"""
Trade Routes - Trade history, positions, Bitvavo credentials, monitoring, candles, tickers
"""
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional, List, Dict
from pathlib import Path
from datetime import datetime, timezone
import json
from modules.core.storage import load_json, save_json
from modules.core.spark_logger import traced
from .monitor import (
    get_monitor, fetch_candles, fetch_tickers,
    execute_mock_trade, execute_real_trade, WATCHLIST_COINS,
    fetch_bitvavo_balance, sync_bitvavo_orders,
)
from . import potjes as potjes_svc
from . import context_service

router = APIRouter(prefix="/trade", tags=["trade"])
DATA_DIR = Path(__file__).parent.parent.parent / "data" / "wallet"
SETTINGS_DIR = Path(__file__).parent.parent.parent / "data" / "users"
TRADE_DIR = Path(__file__).parent.parent.parent / "data" / "trade"


# v6_mock_safety_001 — Hard safety: als bot-config use_mock=True → handmatige real trade is geblokkeerd
def _bot_uses_mock(user_id: str) -> Optional[bool]:
    """Return True/False als user een bot-config heeft, anders None (geen config)."""
    reg = load_json(TRADE_DIR / "bots_registry_state.json", default={"bots": []})
    for b in reg.get("bots", []) if isinstance(reg.get("bots"), list) else []:
        if b.get("user_id") == user_id:
            return bool(b.get("use_mock", True))
    return None


def _enforce_mock_safety(user_id: str, requested_use_mock: bool) -> tuple[bool, Optional[str]]:
    """
    Returns (effective_use_mock, blocker_error_or_None).
    Regel: als bot zegt mock=True maar user vraagt real → BLOCK met duidelijke error.
    Als bot zegt mock=False → user mag beide (admin kan altijd kiezen).
    Geen bot-config → respecteer user's keuze (backward compat).
    """
    bot_mock = _bot_uses_mock(user_id)
    if bot_mock is True and not requested_use_mock:
        return (True, f"Bot-config voor {user_id} staat op MOCK. Handmatige real trade geblokkeerd. "
                       "Zet eerst use_mock=False in de bot-config via /api/trade/bot/start/{user_id}.")
    return (requested_use_mock, None)


class BitvavoCredentials(BaseModel):
    api_key: str
    api_secret: str


# v7_defaults_align_001 — helper voor dynamische trade_amount default
def _default_trade_amount() -> float:
    """Huidige token-prijs of bodemprijs fallback. Vermijdt hardcoded €5/€10 defaults."""
    try:
        from modules.shop.routes import get_dynamic_price
        p = float(get_dynamic_price())
        return p if p > 0 else 5.08
    except Exception:
        return 5.08


class TraderSettings(BaseModel):
    trade_amount: Optional[float] = None  # None = dynamisch (token-prijs)
    market: Optional[str] = "BCH-EUR"
    # v6_mock_default_off_001 — new users default naar REAL, niet mock
    use_mock: Optional[bool] = False
    auto_trade: Optional[bool] = False


class MonitorStartRequest(BaseModel):
    interval: Optional[int] = 300  # v7: minimum 5 min (was 60s = ruis)
    market: Optional[str] = "BCH-EUR"
    markets: Optional[List[str]] = None   # v4_multi_market_001: lijst van coins ipv enkele
    candle_interval: Optional[str] = "15m"  # v7: was "1h" = te traag voor 5min-tick
    user_id: Optional[str] = "user-001"
    auto_trade: Optional[bool] = False
    trade_amount: Optional[float] = None  # None = dynamisch
    use_mock: Optional[bool] = False
    use_potjes: Optional[bool] = False


class QuickTradeRequest(BaseModel):
    market: str = "BCH-EUR"
    side: str = "buy"
    amount: float = 5.0
    use_mock: bool = False


@router.get("/history/{user_id}")
async def get_trade_history(user_id: str, limit: int = Query(50, ge=1, le=500), market: Optional[str] = None):
    data = load_json(DATA_DIR / "trade_history" / f"{user_id}.json", default={"trades": []})
    trades = data.get("trades", [])
    if market:
        trades = [t for t in trades if t.get("market") == market]
    trades.sort(key=lambda t: t.get("timestamp", ""), reverse=True)
    total = len(trades)
    return {"trades": trades[:limit], "total": total}


@router.get("/stats/{user_id}")
async def get_trade_stats(user_id: str):
    data = load_json(DATA_DIR / "trade_history" / f"{user_id}.json", default={"trades": []})
    all_trades = data.get("trades", [])

    # v7_stats_since_baseline_001 — filter trades op baseline.set_at zodat de stats
    # tellen vanaf het moment van baseline-reset (test-data vóór reset wordt uitgesloten).
    baseline_data = load_json(DATA_DIR.parent / "trade" / "capital_baseline.json", default={})
    user_baseline_raw = baseline_data.get(user_id, {})
    if isinstance(user_baseline_raw, (int, float)):
        user_baseline = {"baseline_eur": float(user_baseline_raw), "set_at": None, "note": "legacy-float"}
    elif isinstance(user_baseline_raw, dict):
        user_baseline = user_baseline_raw
    else:
        user_baseline = {}
    baseline_since = user_baseline.get("set_at")

    if baseline_since:
        trades = [t for t in all_trades if (t.get("timestamp") or "") >= baseline_since]
    else:
        trades = all_trades

    buys = [t for t in trades if t.get("action") == "BUY" and t.get("success")]
    sells = [t for t in trades if t.get("action") == "SELL" and t.get("success")]
    markets = list(set(t.get("market", "?") for t in trades))
    total_buy_eur = sum(t.get("amount", 0) for t in buys)
    total_sell_eur = sum(t.get("amount", 0) for t in sells)
    avg_buy_price = sum(t.get("price", 0) for t in buys) / max(len(buys), 1)
    avg_sell_price = sum(t.get("price", 0) for t in sells) / max(len(sells), 1)
    # Fee-aware profit calculation
    total_fees = sum(float(t.get("fee", 0) or 0) for t in trades if (t.get("fee_currency") or "EUR") == "EUR")
    bruto_pnl = total_sell_eur - total_buy_eur
    netto_pnl = bruto_pnl - total_fees

    baseline_eur = user_baseline.get("baseline_eur")
    live_pnl = None
    live_balance = None
    if baseline_eur is not None:
        try:
            from modules.trade.monitor import fetch_bitvavo_balance
            bv = fetch_bitvavo_balance(user_id)
            if bv.get("success"):
                live_balance = bv.get("total_eur")
                live_pnl = round(live_balance - baseline_eur, 2)
        except Exception:
            pass

    return {
        # v4_meetpunt_003: 1 BUY + 1 SELL = 1 round-trip trade (geen 2)
        "total_trades": max(len(buys), len(sells)),
        "buys": len(buys),
        "sells": len(sells),
        "markets": markets,
        "total_buy_eur": round(total_buy_eur, 2),
        "total_sell_eur": round(total_sell_eur, 2),
        "avg_buy_price": round(avg_buy_price, 2),
        "avg_sell_price": round(avg_sell_price, 2),
        "total_fees_eur": round(total_fees, 2),
        "bruto_pnl": round(bruto_pnl, 2),
        "profit_loss": round(netto_pnl, 2),
        "netto_pnl": round(netto_pnl, 2),
        "mock_trades": sum(1 for t in trades if t.get("mock")),
        "real_trades": sum(1 for t in trades if not t.get("mock")),
        # v7_user_view_stats_001 — user's OWN view (buys×sells zonder mock, admin-info verborgen bij front)
        "user_trades": max(len([t for t in buys if not t.get("mock")]), len([t for t in sells if not t.get("mock")])),
        "user_pnl": round(netto_pnl, 2),  # per user is dit dezelfde P&L (per user_id file)
        # Nieuwe velden
        "baseline_eur": baseline_eur,
        "live_balance": live_balance,
        "live_pnl": live_pnl,
        "baseline_set_at": user_baseline.get("set_at"),
        # v7_stats_since_baseline_001 — extra info: hoeveel trades vóór baseline
        "lifetime_trades": max(
            len([t for t in all_trades if t.get("action") == "BUY" and t.get("success")]),
            len([t for t in all_trades if t.get("action") == "SELL" and t.get("success")]),
        ),
        "trades_before_baseline": len(all_trades) - len(trades) if baseline_since else 0,
    }


@router.get("/baseline/{user_id}")
async def get_baseline(user_id: str):
    data = load_json(DATA_DIR.parent / "trade" / "capital_baseline.json", default={})
    return {"success": True, "baseline": data.get(user_id)}


class BaselineSetRequest(BaseModel):
    baseline_eur: float
    note: Optional[str] = None


@router.post("/baseline/{user_id}")
async def set_baseline(user_id: str, req: BaselineSetRequest):
    """Zet/update startkapitaal baseline. Live P&L = Bitvavo balance - baseline."""
    baseline_file = DATA_DIR.parent / "trade" / "capital_baseline.json"
    baseline_file.parent.mkdir(parents=True, exist_ok=True)
    data = load_json(baseline_file, default={})
    data[user_id] = {
        "baseline_eur": req.baseline_eur,
        "set_at": datetime.now(timezone.utc).isoformat(),
        "note": req.note or "Manueel ingesteld",
    }
    save_json(baseline_file, data)
    return {"success": True, "baseline": data[user_id]}


# ============================================================
# DEPOSITS / DONATIES — Externe geldtoevoegingen (niet trading)
# ============================================================

class DepositRequest(BaseModel):
    amount_eur: float
    type: str  # "donation", "deposit", "withdrawal"
    source: Optional[str] = None  # Bv. "Harry", "eigen rekening"
    description: Optional[str] = None
    timestamp: Optional[str] = None


@router.get("/deposits/{user_id}")
async def get_deposits(user_id: str):
    """Lijst alle donaties/deposits/withdrawals voor user."""
    dep_file = DATA_DIR.parent / "trade" / "deposits.json"
    data = load_json(dep_file, default={})
    user_deps = data.get(user_id, [])
    totals = {
        "donations": sum(d["amount_eur"] for d in user_deps if d["type"] == "donation"),
        "deposits": sum(d["amount_eur"] for d in user_deps if d["type"] == "deposit"),
        "withdrawals": sum(d["amount_eur"] for d in user_deps if d["type"] == "withdrawal"),
    }
    totals["net_external"] = round(totals["donations"] + totals["deposits"] - totals["withdrawals"], 2)
    return {"success": True, "deposits": user_deps, "totals": totals}


@router.post("/deposits/{user_id}")
async def add_deposit(user_id: str, req: DepositRequest):
    """
    Registreer een externe geldtoevoeging (donatie, deposit, withdrawal).
    Effect: baseline wordt automatisch bijgewerkt zodat P&L niet scheef trekt.

    Voorbeeld: Harry doneert €10
      -> baseline gaat van €50.80 naar €60.80
      -> live_pnl (balance - baseline) blijft correct (alleen trading-winst)
    """
    dep_file = DATA_DIR.parent / "trade" / "deposits.json"
    dep_file.parent.mkdir(parents=True, exist_ok=True)
    data = load_json(dep_file, default={})
    deposits = data.get(user_id, [])

    if req.type not in ("donation", "deposit", "withdrawal"):
        return {"success": False, "error": "Type moet: donation, deposit of withdrawal"}

    entry = {
        "id": f"dep-{len(deposits) + 1:04d}",
        "timestamp": req.timestamp or datetime.now(timezone.utc).isoformat(),
        "type": req.type,
        "amount_eur": req.amount_eur,
        "source": req.source or "onbekend",
        "description": req.description or "",
    }
    deposits.append(entry)
    data[user_id] = deposits
    save_json(dep_file, data)

    # Update baseline: +donation/deposit, -withdrawal
    baseline_file = DATA_DIR.parent / "trade" / "capital_baseline.json"
    baseline_data = load_json(baseline_file, default={})
    current_baseline = baseline_data.get(user_id, {}).get("baseline_eur", 0.0)
    if req.type == "withdrawal":
        new_baseline = round(current_baseline - req.amount_eur, 2)
    else:
        new_baseline = round(current_baseline + req.amount_eur, 2)
    baseline_data[user_id] = {
        "baseline_eur": new_baseline,
        "set_at": datetime.now(timezone.utc).isoformat(),
        "note": f"Auto-update via {req.type}: {req.description or req.source or 'geen beschrijving'}",
    }
    save_json(baseline_file, baseline_data)

    return {
        "success": True,
        "deposit": entry,
        "baseline_updated": {
            "old": current_baseline,
            "new": new_baseline,
            "delta": round(new_baseline - current_baseline, 2),
        },
    }


@router.delete("/deposits/{user_id}/{deposit_id}")
async def delete_deposit(user_id: str, deposit_id: str):
    """Verwijder een deposit entry (en corrigeer baseline)."""
    dep_file = DATA_DIR.parent / "trade" / "deposits.json"
    data = load_json(dep_file, default={})
    deposits = data.get(user_id, [])
    entry = next((d for d in deposits if d["id"] == deposit_id), None)
    if not entry:
        return {"success": False, "error": "Niet gevonden"}
    deposits = [d for d in deposits if d["id"] != deposit_id]
    data[user_id] = deposits
    save_json(dep_file, data)
    # Correct baseline in reverse
    baseline_file = DATA_DIR.parent / "trade" / "capital_baseline.json"
    baseline_data = load_json(baseline_file, default={})
    current = baseline_data.get(user_id, {}).get("baseline_eur", 0.0)
    if entry["type"] == "withdrawal":
        new_baseline = round(current + entry["amount_eur"], 2)
    else:
        new_baseline = round(current - entry["amount_eur"], 2)
    baseline_data[user_id] = {
        "baseline_eur": new_baseline,
        "set_at": datetime.now(timezone.utc).isoformat(),
        "note": f"Correctie door verwijderen {entry['type']} #{deposit_id}",
    }
    save_json(baseline_file, baseline_data)
    return {"success": True, "removed": entry, "new_baseline": new_baseline}


@router.get("/markets/{user_id}")
async def get_available_markets(user_id: str):
    data = load_json(DATA_DIR / "trade_history" / f"{user_id}.json", default={"trades": []})
    trades = data.get("trades", [])
    markets = {}
    for t in trades:
        m = t.get("market", "?")
        if m not in markets:
            markets[m] = {"total": 0, "buys": 0, "sells": 0}
        markets[m]["total"] += 1
        if t.get("action") == "BUY":
            markets[m]["buys"] += 1
        elif t.get("action") == "SELL":
            markets[m]["sells"] += 1
    return {"markets": markets}


@router.post("/bitvavo/credentials/{user_id}")
async def save_bitvavo_credentials(user_id: str, creds: BitvavoCredentials):
    settings_file = SETTINGS_DIR / user_id / "settings.json"
    settings = load_json(settings_file, default={"user_id": user_id, "integrations": {}})
    if "integrations" not in settings:
        settings["integrations"] = {}
    settings["integrations"]["bitvavo"] = {
        "api_key": creds.api_key,
        "api_secret": creds.api_secret,
        "connected_at": datetime.now(timezone.utc).isoformat(),
    }
    settings_file.parent.mkdir(parents=True, exist_ok=True)
    save_json(settings_file, settings)
    return {"success": True, "message": "Bitvavo credentials opgeslagen"}


@router.get("/bitvavo/status/{user_id}")
async def get_bitvavo_status(user_id: str):
    settings_file = SETTINGS_DIR / user_id / "settings.json"
    settings = load_json(settings_file, default={})
    bitvavo = settings.get("integrations", {}).get("bitvavo", {})
    api_key = bitvavo.get("api_key", "")
    return {
        "connected": bool(api_key) and not api_key.startswith("TEST_"),
        "placeholder": api_key.startswith("TEST_"),
        "connected_at": bitvavo.get("connected_at"),
    }


@router.get("/bitvavo/balance/{user_id}")
async def get_bitvavo_balance(user_id: str):
    """Live Bitvavo account balances (all coins + EUR) with current EUR values."""
    return fetch_bitvavo_balance(user_id)


@router.post("/bitvavo/sync/{user_id}")
async def sync_bitvavo(user_id: str, market: Optional[str] = None):
    """Importeer trade history vanuit Bitvavo naar lokale trade_history."""
    return sync_bitvavo_orders(user_id, market)


# v7_treasury_delta_002 — Systeem-treasury delta view (gebruikt bestaand dynamic-price systeem).
# Toont zowel de INVESTERING (som pot-capital = aankoopprijzen) als de MARKTWAARDE
# (circulating tokens × live dynamic price, zoals bepaald in shop/routes.py:get_dynamic_price).
#
# Bestaande regel (zie shop/routes.py):
#   - 1 ROAR token = 1 tradeable pot (Spark 10, Willem 10, Gijs 2, etc.)
#   - Pot.capital = aankoopprijs op moment van kopen (bevroren investering)
#   - Live token-waarde = get_spark_core_value() / circulating (dynamisch)
#   - Bitvavo groeit door trading → dynamic price groeit → token waarde groeit
#     → daardoor stijgt de MARKTWAARDE van elke pot mee (ook al blijft capital vast)
#
# Delta interpretatie:
#   marktwaarde > investering → onrealiseerde winst (tokens meer waard geworden)
#   marktwaarde ≈ investering → break-even
#   marktwaarde < investering → onrealiseerd verlies
@router.get("/delta")
async def get_treasury_delta():
    """Systeem-treasury delta: investering (pot-capital) vs live marktwaarde (dynamic price × tokens).

    Response:
      pots_capital_eur     — som van alle capital-velden (aankoopprijzen, bevroren)
      spark_core_value_eur — live Bitvavo + kasboek (canonical waarde-bron)
      dynamic_price_eur    — huidige prijs per ROAR-token (spark_core / circulating)
      circulating_tokens   — som ROAR-balances alle users
      market_value_eur     — circulating × dynamic_price (= wat alle pots samen waard zijn NU)
      delta_eur            — market_value - pots_capital (onrealiseerd P&L)
      per_user             — pot_count, capital_eur (investering), market_value_eur (huidig)
      spark_kasboek        — Spark's boekhoudkundige totalen
    """
    # 1. Som alle pots per user (aankoopprijzen)
    potjes_data = load_json(
        Path(__file__).parent.parent.parent / "data" / "financial" / "user_potjes.json",
        default={"users": {}},
    )
    # 2. ROAR balances (voor pot ↔ token consistentie check)
    roar_data = load_json(
        Path(__file__).parent.parent.parent / "data" / "roar" / "roar_balances.json",
        default={"balances": {}},
    )
    roar_balances = roar_data.get("balances", {})

    # 3. Live dynamic price + spark core value (uit bestaand shop-systeem)
    try:
        from modules.shop.routes import (
            get_dynamic_price, get_spark_core_value, get_circulating,
        )
        dynamic_price = float(get_dynamic_price() or 0)
        spark_core_value = float(get_spark_core_value() or 0)
        circulating = int(get_circulating() or 0)
    except Exception:
        dynamic_price = 0.0
        spark_core_value = 0.0
        circulating = sum(int(v) for v in roar_balances.values())

    per_user = {}
    total_pots_capital = 0.0
    total_market_value = 0.0
    for uid, info in potjes_data.get("users", {}).items():
        pots = info.get("potjes", [])
        cap = round(sum(float(p.get("capital", 0) or 0) for p in pots), 4)
        open_positions = sum(1 for p in pots if p.get("position", {}).get("is_open"))
        tokens = int(roar_balances.get(uid, 0))
        market_value = round(tokens * dynamic_price, 4)
        per_user[uid] = {
            "pot_count": len(pots),
            "roar_tokens": tokens,
            "capital_eur": cap,           # aankoopprijs (investering)
            "market_value_eur": market_value,  # huidige waarde
            "unrealized_pnl_eur": round(market_value - cap, 4),
            "open_positions": open_positions,
            "pots_match_tokens": (len(pots) == tokens),  # regel-check: 1 token = 1 pot
        }
        total_pots_capital += cap
        total_market_value += market_value

    total_pots_capital = round(total_pots_capital, 4)
    total_market_value = round(total_market_value, 4)
    delta = round(total_market_value - total_pots_capital, 4)

    # 4. Spark boekhouding totalen
    kb = load_json(
        Path(__file__).parent.parent.parent / "data" / "system" / "spark_kasboek.json",
        default={"totals": {}},
    )
    kb_totals = kb.get("totals", {})

    # 5. Categoriseer delta
    if abs(delta) < 0.01:
        status = "break_even"
        toelichting = "Marktwaarde gelijk aan investering — geen onrealiseerde winst of verlies."
    elif delta > 0:
        status = "winst"
        toelichting = (
            f"€{delta:.2f} onrealiseerde winst: tokens zijn meer waard geworden dan "
            f"toen ze gekocht werden (dynamic price €{dynamic_price:.2f} > aankoopgemiddelde)."
        )
    else:
        status = "verlies"
        toelichting = (
            f"€{abs(delta):.2f} onrealiseerd verlies: tokens zijn minder waard dan "
            f"toen ze gekocht werden (dynamic price €{dynamic_price:.2f}). "
            "Kan komen door trader-drawdown."
        )

    # 6. Consistency check: som pots == circulating tokens?
    total_pots = sum(u["pot_count"] for u in per_user.values())
    total_tokens = sum(u["roar_tokens"] for u in per_user.values())
    consistency_ok = (total_pots == total_tokens == circulating)

    return {
        "success": True,
        # Investering vs marktwaarde
        "pots_capital_eur": total_pots_capital,
        "market_value_eur": total_market_value,
        "delta_eur": delta,
        "status": status,
        "toelichting": toelichting,
        # Achterliggende waarden
        "spark_core_value_eur": round(spark_core_value, 4),
        "dynamic_price_eur": round(dynamic_price, 4),
        "circulating_tokens": circulating,
        # Consistency
        "total_pots": total_pots,
        "total_roar_tokens": total_tokens,
        "consistency_ok": consistency_ok,
        # Per user + kasboek
        "per_user": per_user,
        "spark_kasboek": kb_totals,
        "as_of": datetime.now(timezone.utc).isoformat(),
    }



@router.get("/settings/{user_id}")
async def get_trader_settings(user_id: str):
    settings_file = SETTINGS_DIR / user_id / "settings.json"
    settings = load_json(settings_file, default={})
    trader = settings.get("trader", {
        "trade_amount": _default_trade_amount(),  # v7: dynamisch = token-prijs
        "market": "BCH-EUR",
        "use_mock": False,   # v6_mock_default_off_001 — default REAL voor nieuwe users
        "auto_trade": False,
    })
    return {"settings": trader}


@router.put("/settings/{user_id}")
async def update_trader_settings(user_id: str, updates: TraderSettings):
    settings_file = SETTINGS_DIR / user_id / "settings.json"
    settings = load_json(settings_file, default={"user_id": user_id})
    if "trader" not in settings:
        settings["trader"] = {}
    for k, v in updates.model_dump(exclude_none=True).items():
        settings["trader"][k] = v
    settings_file.parent.mkdir(parents=True, exist_ok=True)
    save_json(settings_file, settings)
    return {"success": True, "settings": settings["trader"]}


# ============================================================
# CANDLES & TICKERS (Bitvavo Public API - no auth needed)
# ============================================================

@router.get("/candles")
async def get_candles(
    market: str = Query("BCH-EUR"),
    interval: str = Query("1h"),
    limit: int = Query(30, ge=1, le=200),
):
    candles = fetch_candles(market, interval, limit)
    return {"success": len(candles) > 0, "market": market, "interval": interval, "candles": candles}


@router.get("/tickers")
async def get_tickers(coins: str = Query(None)):
    coin_list = coins.split(",") if coins else WATCHLIST_COINS
    tickers = fetch_tickers(coin_list)
    return {"success": len(tickers) > 0, "tickers": tickers}


# ============================================================
# QUICK TRADE (Execute buy/sell)
# ============================================================

@router.post("/execute/{user_id}")
async def execute_trade(user_id: str, req: QuickTradeRequest):
    # v6_mock_safety_001 — block real-trade als bot-config op mock staat
    eff_mock, err = _enforce_mock_safety(user_id, req.use_mock)
    if err:
        return {"success": False, "error": err, "blocked_by": "bot_mock_safety"}
    if eff_mock:
        result = execute_mock_trade(user_id, req.market, req.side, req.amount)
    else:
        result = execute_real_trade(user_id, req.market, req.side, req.amount)
    return result


# ============================================================
# SNELHANDEL MET POTJE — Spark pakt vrij potje + start monitor auto (v4_quickpot_001)
# ============================================================

class QuickBuyPotjeRequest(BaseModel):
    market: str = "BCH-EUR"
    use_mock: bool = False   # v6_mock_default_off_001
    candle_interval: Optional[str] = "1h"


@router.post("/quick-buy-potje/{user_id}")
@traced(intent="quick-buy: pak eerste vrije potje + start monitor", module="trade")
async def quick_buy_potje(user_id: str, req: QuickBuyPotjeRequest):
    """
    Spark-assisted buy: pakt eerste vrije potje, voert buy uit, start monitor in potjes-mode.
    Monitor neemt over voor automatische verkoop op trailing-stop winst-moment.

    v4_token_gate_001: alleen gradatie ≤ 1 (admin) mag handmatig quick-buy.
    Lagere gradaties mogen alleen via auto-bot werken wanneer ze tokens bezitten.
    """
    # Token-gate + admin-lock
    users_data = load_json(Path(__file__).parent.parent.parent / "data" / "system" / "users.json", default={})
    users_list = users_data.get("users", []) if isinstance(users_data, dict) else []
    user_entry = next((u for u in users_list if (u.get("id") or u.get("user_id")) == user_id), None)
    gradatie = (user_entry or {}).get("gradatie", 7)
    if gradatie > 1:
        return {"success": False, "error": "Handmatig potje kopen kan alleen door beheerder (gradatie 1). Jouw bot start automatisch zodra je tokens hebt."}

    monitor = get_monitor()

    # 1) Vind vrij potje (v4_potje_quickbuy_002: skip cycle-check, user-initiated mag meerdere)
    # v6_pot_market_match_001 — voorkeur voor potje dat al deze market heeft
    current_cycle = monitor._cycles if hasattr(monitor, "_cycles") else 0
    pot = potjes_svc.get_available_pot(user_id, current_cycle, skip_cycle_check=True,
                                        prefer_market=getattr(req, "market", None))
    if not pot:
        # Tel hoeveel er open zijn voor een betere foutmelding
        user_data = potjes_svc.get_potjes(user_id)
        open_count = sum(1 for p in user_data.get("potjes", []) if p.get("position", {}).get("is_open"))
        total = len(user_data.get("potjes", []))
        return {
            "success": False,
            "error": f"Geen vrij potje beschikbaar — {open_count}/{total} potjes hebben al een open positie. Wacht tot een potje verkoopt of breid het aantal potjes uit."
        }

    # 2) Huidige prijs ophalen (met mock-fallback bij API down in preview)
    tickers = fetch_tickers([req.market])
    price = None
    if tickers and tickers[0].get("last"):
        price = float(tickers[0]["last"])
    elif req.use_mock:
        # Preview/test fallback: gebruik laatste bekende prijs uit potje of dummy
        price = float(pot.get("position", {}).get("entry_price") or 300.0)
    if not price:
        return {"success": False, "error": f"Kon prijs niet ophalen voor {req.market}"}

    # 3) Buy uitvoeren met potje's eigen entry amount
    # v6_potje_size_10_fix_001 — primaire bron is `capital` (v6-systeem schrijft daar
    # de actuele potje-grootte naartoe). `current_size`/`starting_size` zijn legacy
    # velden die in moderne potjes niet meer gezet worden, vandaar dat de oude
    # fallback `5.08` ten onrechte sloeg. Nu: capital → current_size → starting_size → 10.0.
    entry_amount = float(
        pot.get("capital")
        or pot.get("current_size")
        or pot.get("starting_size")
        or 10.0
    )
    if req.use_mock:
        trade_result = execute_mock_trade(user_id, req.market, "buy", entry_amount)
    else:
        # v6_mock_safety_001 — block real-trade als bot-config op mock staat
        eff_mock, err = _enforce_mock_safety(user_id, req.use_mock)
        if err:
            return {"success": False, "error": err, "blocked_by": "bot_mock_safety"}
        trade_result = execute_real_trade(user_id, req.market, "buy", entry_amount)

    if not trade_result.get("success"):
        return {"success": False, "error": f"Buy mislukt: {trade_result.get('error', 'onbekend')}", "trade": trade_result}

    # 4) Markeer potje als open (v4_potje_market_001: incl. market + trade ref)
    pot_opened = potjes_svc.open_pot(
        user_id, pot["id"], price, current_cycle,
        trade_id=trade_result.get("trade", {}).get("trade_id"),
        amount_eur=entry_amount,
        market=req.market,
    )

    # 5) Start monitor in potjes-mode als hij nog niet draait
    monitor_started = False
    if not monitor._running:
        monitor.start(
            interval=300,
            market=req.market,
            candle_interval=req.candle_interval or "15m",
            user_id=user_id,
            auto_trade=True,
            trade_amount=entry_amount,
            use_mock=req.use_mock,
            use_potjes=True,
        )
        monitor_started = True

    return {
        "success": True,
        "message": f"Potje #{pot.get('nummer', '?')} geopend @ €{price:.2f}. Spark neemt over en verkoopt automatisch op winst.",
        "pot": pot_opened,
        "entry_price": price,
        "entry_amount": entry_amount,
        "monitor_started": monitor_started,
        "monitor_status": monitor.get_status(),
        "trade": trade_result,
    }


# ============================================================
# MONITOR (Start/Stop/Pause background trading monitor)
# ============================================================

@router.post("/monitor/start")
async def monitor_start(req: MonitorStartRequest = MonitorStartRequest()):
    """
    Legacy singleton monitor. Alleen toegankelijk voor admin (gradatie ≤ 1)
    of Spark (user-000). Andere users moeten via `/api/trade/bot/start/{user_id}`.
    """
    # v4_monitor_auth_001: admin/Spark-only check
    uid = req.user_id
    if uid and uid != "user-000":
        users_data = load_json(Path(__file__).parent.parent.parent / "data" / "system" / "users.json", default={})
        users_list = users_data.get("users", []) if isinstance(users_data, dict) else []
        user_entry = next((u for u in users_list if (u.get("id") or u.get("user_id")) == uid), None)
        gradatie = (user_entry or {}).get("gradatie", 7)
        if gradatie > 1:
            return {"success": False, "error": "Legacy monitor is admin-only. Gebruik /api/trade/bot/start/{user_id}."}
    monitor = get_monitor()
    return monitor.start(
        interval=req.interval,
        market=req.market,
        markets=req.markets,
        candle_interval=req.candle_interval,
        user_id=req.user_id,
        auto_trade=req.auto_trade,
        trade_amount=req.trade_amount,
        use_mock=req.use_mock,
        use_potjes=req.use_potjes,
    )


@router.post("/monitor/stop")
async def monitor_stop():
    # v4_spark_unstoppable_001: bescherm Spark's legacy monitor
    mon = get_monitor()
    try:
        st = mon.get_status() or {}
        if st.get("user_id") == "user-000":
            return {"success": False, "error": "Spark's eigen bot is onstopbaar. Gebruik /api/trade/bot/stop voor andere users."}
    except Exception:
        pass
    return mon.stop()


@router.post("/monitor/pause")
async def monitor_pause():
    mon = get_monitor()
    try:
        st = mon.get_status() or {}
        if st.get("user_id") == "user-000":
            return {"success": False, "error": "Spark's eigen bot kan niet gepauzeerd worden."}
    except Exception:
        pass
    return mon.pause()


@router.get("/monitor/status")
async def monitor_status():
    return {"success": True, "status": get_monitor().get_status()}


@router.get("/monitor/decisions")
async def monitor_decisions(limit: int = Query(50)):
    return {"success": True, "decisions": get_monitor().get_decisions(limit)}


# v5_hot_market_swap_001 — markets hot-aanpassen tijdens running zonder bot te stoppen
class UpdateMarketsBody(BaseModel):
    markets: List[str]


@router.post("/monitor/markets/{user_id}")
async def update_monitor_markets(user_id: str, body: UpdateMarketsBody):
    """Wissel de markten van een (lopende of stilstaande) bot zonder hem te stoppen."""
    from .monitor import get_user_monitor
    monitor = get_user_monitor(user_id)
    return monitor.update_markets(body.markets)


# v6_potje_market_distribution_001 — herverdeel bestaande potjes over user's markten
@router.post("/potjes/redistribute/{user_id}")
async def redistribute_potjes(user_id: str, body: UpdateMarketsBody = None):
    """Verdeel alle gesloten potjes round-robin over user's markets.
    Open posities blijven op hun huidige market staan (kan niet hot-swappen).
    Als `markets` in body ontbreekt, wordt user's bots_registry markets gebruikt.
    """
    from .potjes import redistribute_potjes_across_markets
    target = (body.markets if body else None)
    return redistribute_potjes_across_markets(user_id, target)


# v6_dynamic_pot_split_001 — Rebalance potjes vanaf actuele Bitvavo balance
# v7_rebalance_smart_001 — Extended met token-count leidend + EUR-liquide meetellen
class RebalanceBody(BaseModel):
    coins: Optional[List[str]] = None       # default: alle 6 watchlist coins
    pot_size: float = 10.0                  # legacy vaste schijf (modus A)
    trader_user_id: str = "user-001"        # krijgt de trade-pots
    anchor_user_id: str = "user-000"        # legacy — niet meer gebruikt voor anchors (v7)
    # v7 smart mode
    target_pot_count: Optional[int] = None  # als gezet → smart mode: exact N pots
    include_eur_liquide: bool = True        # EUR-saldo op Bitvavo meetellen
    default_market: str = "BCH-EUR"         # markt voor EUR-only pots in smart mode


@router.post("/potjes/rebalance-from-bitvavo")
async def rebalance_from_bitvavo_endpoint(body: RebalanceBody = RebalanceBody()):
    """Herbalanceer potjes vanaf actuele Bitvavo balance.

    Twee modi:
      A. Legacy (pot_size vast, target_pot_count=None):
         Per coin → floor(value/pot_size) pots. EUR wordt genegeerd.
         Coins <€pot_size geven 0 pots.

      B. Smart v7 (target_pot_count=N):
         Exact N pots aangemaakt. pot_size = (som(coins) + eur) / N.
         Coins met genoeg waarde krijgen coin-pots, rest wordt EUR-only op default_market.
         Werkt ook als je alleen EUR liquide hebt.

    Aanbevolen: token-count leidend → `target_pot_count = aantal ROAR tokens`.
    Open posities blijven ongemoeid.
    """
    from .potjes import rebalance_from_bitvavo
    return rebalance_from_bitvavo(
        coins=body.coins, pot_size=body.pot_size,
        trader_user_id=body.trader_user_id, anchor_user_id=body.anchor_user_id,
        include_eur_liquide=body.include_eur_liquide,
        target_pot_count=body.target_pot_count,
        default_market=body.default_market,
    )


# v5_candle_hotswap_001 — wissel candle-interval (cycle) zonder restart
class UpdateCandleBody(BaseModel):
    candle_interval: str


@router.post("/monitor/candle/{user_id}")
async def update_monitor_candle(user_id: str, body: UpdateCandleBody):
    """Wissel candle_interval (15m / 1h / 4h / 1d) van een bot zonder restart."""
    from .monitor import get_user_monitor
    monitor = get_user_monitor(user_id)
    return monitor.update_candle_interval(body.candle_interval)


# v5_autotrade_hotswap_001 — toggle auto_trade aan/uit zonder restart
class UpdateAutoTradeBody(BaseModel):
    auto_trade: bool


@router.post("/bot/auto-trade/{user_id}")
async def update_bot_auto_trade(user_id: str, body: UpdateAutoTradeBody):
    """Zet auto_trade aan/uit voor user's bot. Persisteert direct naar registry zodat
    de waarde een backend-restart overleeft (bug B1 fix)."""
    from .monitor import get_user_monitor
    monitor = get_user_monitor(user_id)
    return monitor.update_auto_trade(body.auto_trade)




# ============================================================
# v4_per_user_bot_001 — Per-user bot endpoints
# ============================================================
@router.post("/bot/start/{user_id}")
@traced(intent="trade-bot starten voor specifieke user", module="trade")
async def bot_start(user_id: str, req: MonitorStartRequest = MonitorStartRequest()):
    """Start trade-bot voor specifieke user. Token-gate: user moet ≥ 1 token hebben.
    Spark (user-000) en admin (gradatie 1) zijn uitgezonderd van token-gate."""
    from .monitor import get_user_monitor
    users_data = load_json(Path(__file__).parent.parent.parent / "data" / "system" / "users.json", default={})
    users_list = users_data.get("users", []) if isinstance(users_data, dict) else []
    user_entry = next((u for u in users_list if (u.get("id") or u.get("user_id")) == user_id), None)
    gradatie = (user_entry or {}).get("gradatie", 7)
    if gradatie > 1 and user_id != "user-000":
        roar = load_json(Path(__file__).parent.parent.parent / "data" / "roar" / "roar_balances.json", default={})
        tokens = int(roar.get("balances", {}).get(user_id, 0))
        if tokens < 1:
            return {"success": False, "error": "Je hebt 0 tokens — bot kan niet starten. 1 token = 1 potje slot."}
    mon = get_user_monitor(user_id)
    # v7_min_interval_300s_001 — clamp interval naar minimum 5 min
    _interval = max(300, int(req.interval or 300))
    # v7_force_dynamic_trade_amount_001 — negeer UI-input; ALTIJD huidige token-prijs
    # Reden: UI stuurt vaak legacy 5.0 mee → wordt geaccepteerd → willem koopt met €5 ipv €6.31.
    _amt = _default_trade_amount()
    return mon.start(
        interval=_interval,
        market=req.market,
        markets=req.markets,
        candle_interval=req.candle_interval or "15m",
        user_id=user_id,
        auto_trade=req.auto_trade,
        trade_amount=_amt,
        use_mock=req.use_mock,
        use_potjes=req.use_potjes,
    )


@router.post("/bot/stop/{user_id}")
@traced(intent="trade-bot stoppen voor specifieke user", module="trade")
async def bot_stop(user_id: str):
    from .monitor import get_user_monitor
    # v5_spark_stoppable_001 — Spark stop is weer toegestaan (bugs van v4_spark_unstoppable_001 zijn opgelost)
    return get_user_monitor(user_id).stop()


@router.post("/bot/pause/{user_id}")
async def bot_pause(user_id: str):
    """v5_per_user_endpoints_001 — pauzeer een specifieke user's bot zonder andere bots te raken."""
    from .monitor import get_user_monitor
    return get_user_monitor(user_id).pause()


@router.get("/bot/status/{user_id}")
async def bot_status(user_id: str):
    from .monitor import get_user_monitor
    return {"success": True, "status": get_user_monitor(user_id).get_status()}


@router.get("/bot/decisions/{user_id}")
async def bot_decisions(user_id: str, limit: int = Query(50)):
    from .monitor import get_user_monitor
    return {"success": True, "decisions": get_user_monitor(user_id).get_decisions(limit)}


@router.get("/admin/bots")
async def admin_list_bots():
    """v4_trade_analytics_001: alle user-bots voor admin overzicht.

    v5_lazy_slot_001: elke menselijke user krijgt automatisch een idle bot-slot
    (zelfs als hij nog niet gestart heeft). bot-* user_ids (AI personae) worden
    overgeslagen — die hebben geen trader-bot.
    'Draaien als ik offline ben' checkbox regelt persistentie, niet zichtbaarheid.
    """
    from .monitor import list_running_bots, _load_registered_users, _read_pot_count
    # Echte users uit system/users.json (geen AI bots)
    users_fp = Path(__file__).parent.parent.parent / "data" / "system" / "users.json"
    users_data = load_json(users_fp, default={"users": []})
    all_users = users_data.get("users", []) if isinstance(users_data, dict) else []
    registered = set(_load_registered_users())

    # v5_shadow_cleanup_001 — ROAR balances voor token-gate
    roar_fp = Path(__file__).parent.parent.parent / "data" / "roar" / "roar_balances.json"
    roar_data = load_json(roar_fp, default={})
    roar_balances = roar_data.get("balances", {}) if isinstance(roar_data, dict) else {}

    # Bestaande bots ophalen
    bots = list_running_bots()
    # v6_potje_per_token_001 — toevoegen actual pot_count uit user_potjes.json (niet hardcoded 10)
    # v6_admin_bots_potcount_fix_001 (sessie 16) — ALTIJD pot_count zetten, niet alleen
    # als use_potjes=True. Potjes bestaan los van de bot-instance flag, en de UI
    # toont anders `null` voor Spark/Willem wat verwarrend is.
    for b in bots:
        if b.get("user_id"):
            b["pot_count"] = _read_pot_count(b["user_id"])
    bots_by_uid = {b.get("user_id"): b for b in bots if b.get("user_id")}

    # Voor elke menselijke user: zorg dat er een entry is.
    # v5_shadow_cleanup_001 — alleen lazy-slot tonen als user ≥1 ROAR token heeft,
    # proactief geregistreerd is, óf een running/paused bot heeft. Voorkomt
    # "schaduw-traders" zoals Gijs/Nick die ooit een token hadden maar nu 0.
    for u in all_users:
        uid = u.get("id") or u.get("user_id")
        if not uid or uid.startswith("bot-"):
            continue
        if uid in bots_by_uid:
            continue
        tokens = int(roar_balances.get(uid, 0) or 0)
        gradatie = u.get("gradatie", 7)
        # Skip lazy-slot als geen token, niet proactief geregistreerd, en geen admin
        if tokens < 1 and uid not in registered and gradatie > 1 and uid != "user-000":
            continue
        bots_by_uid[uid] = {
            "user_id": uid,
            "user_naam": u.get("naam") or u.get("name") or uid,
            "gradatie": gradatie,
            "running": False,
            "paused": False,
            "cycles": 0,
            "interval": 300,  # v7: 5 min minimum
            "candle_interval": "15m",  # v7
            "market": "BCH-EUR",
            "markets": [f"{c}-EUR" for c in ["BCH", "BTC", "ETH", "SOL", "ADA", "ATOM"]],
            "auto_trade": False,
            "trade_amount": _default_trade_amount(),  # v7: dynamisch
            "use_mock": False,
            "use_potjes": True,
            "pot_count": _read_pot_count(uid),
            "uptime_seconds": 0,
            "lazy_slot": True,
            "tokens": tokens,
        }

    # Verrijk bestaande bot-entries met user-naam en gradatie
    name_lookup = {(u.get("id") or u.get("user_id")): (u.get("naam") or u.get("name")) for u in all_users}
    grad_lookup = {(u.get("id") or u.get("user_id")): u.get("gradatie") for u in all_users}
    # v5_display_fix_001 — CORRECTIE: user-000 = Spark, user-001 = De Willem.
    # Eerdere "swap" was een bug die verwarring veroorzaakte. Data was altijd correct,
    # display nu ook gelijkgetrokken met user's mental model.
    name_lookup["user-000"] = "Spark"
    name_lookup["user-001"] = "De Willem"
    # v6_admin_bots_markets_fix_001 (sessie 16) — overlay markets uit bots_registry_state
    # voor entries die stale default ['BCH-EUR'] tonen. Registry is source-of-truth voor
    # multi-coin keuzes.
    registry_fp = Path(__file__).parent.parent.parent / "data" / "trade" / "bots_registry_state.json"
    registry_data = load_json(registry_fp, default={"bots": []})
    registry_markets = {br.get("user_id"): br.get("markets") for br in registry_data.get("bots", []) if br.get("user_id")}
    for uid, b in bots_by_uid.items():
        b.setdefault("user_naam", name_lookup.get(uid, uid))
        if uid in ("user-000", "user-001"):
            b["user_naam"] = name_lookup[uid]
        b.setdefault("gradatie", grad_lookup.get(uid))
        b["proactively_registered"] = uid in registered
        # Overlay markets als registry een betere (langere) lijst heeft
        reg_mkts = registry_markets.get(uid)
        if reg_mkts and len(reg_mkts) > len(b.get("markets", [])):
            b["markets"] = reg_mkts
            b["market"] = reg_mkts[0]

    # Sorteer: Spark eerst, dan running, dan rest alfabetisch op naam
    def _sort_key(b):
        if b["user_id"] == "user-000":
            return (0, "")
        if b.get("running"):
            return (1, (b.get("user_naam") or b["user_id"]).lower())
        return (2, (b.get("user_naam") or b["user_id"]).lower())

    out = sorted(bots_by_uid.values(), key=_sort_key)
    return {"success": True, "bots": out, "total_unfiltered": len(bots)}


@router.get("/community/trade-feed")
async def get_trade_feed(limit: int = Query(50)):
    """v4_boekhouder_001: laatste community trade-feed berichten."""
    feed_file = Path(__file__).parent.parent.parent / "data" / "chat" / "community" / "trade-feed.json"
    data = load_json(feed_file, default={"messages": []})
    msgs = data.get("messages", [])
    return {"success": True, "messages": list(reversed(msgs[-limit:])), "channel_info": {"title": data.get("title", "Trade-feed"), "description": data.get("description", "")}}


@router.get("/admin/audit-log")
async def get_audit_log(limit: int = Query(100)):
    """v4_audit_001: alle geld/token-bewegingen audit-trail."""
    audit_file = Path(__file__).parent.parent.parent / "data" / "system" / "audit_log.json"
    data = load_json(audit_file, default={"entries": []})
    return {"success": True, "entries": list(reversed(data.get("entries", [])[-limit:]))}


# ============================================================
# POTJES SYSTEEM (10 onafhankelijke potjes)
# ============================================================

@router.get("/potjes/{user_id}")
async def get_user_potjes(user_id: str):
    """Haal potjes overzicht op"""
    return {
        "success": True,
        "summary": potjes_svc.get_summary(user_id),
        "potjes": potjes_svc.get_potjes(user_id)["potjes"],
    }


@router.post("/potjes/{user_id}/expand")
async def expand_user_potjes(user_id: str):
    """Breid potjes uit vanuit overflow pool (wanneer alle potjes op max staan)"""
    return potjes_svc.expand_potjes(user_id)


@router.post("/potjes/{user_id}/reset-cycle")
async def reset_potjes_cycle(user_id: str):
    """Reset last_buy_cycle marker (handmatig, voor debugging)"""
    potjes_svc.reset_last_buy_cycle(user_id)
    return {"success": True, "message": "Buy cycle gereset"}


# v6_potje_size_10_001 — admin: zet alle potjes op €10 (nieuwe default)
@router.post("/potjes/{user_id}/resize-to-default")
async def resize_potjes(user_id: str):
    """Zet alle potjes van een user naar de DEFAULT capital (€10).
    Faalt als user open posities heeft."""
    return potjes_svc.resize_potjes_to_default(user_id)


# v6_potje_per_token_001 — sync 1 token = 1 potje voor alle non-Spark users
@router.post("/potjes/sync-all-to-tokens")
async def sync_all_potjes_to_tokens(viewer_id: str):
    """Backfill: synchroniseert alle non-Spark users' potje-count naar hun ROAR balance.
    Admin-only (gradatie ≤ 2). Verwijdert ongebruikte potjes als user te veel heeft.
    """
    from fastapi import HTTPException
    USERS = Path(__file__).parent.parent.parent / "data" / "system" / "users.json"
    ROAR = Path(__file__).parent.parent.parent / "data" / "roar" / "roar_balances.json"
    users = load_json(USERS, default={"users": []})
    ulist = users.get("users", []) if isinstance(users, dict) else users
    viewer = next((u for u in ulist if u.get("id") == viewer_id), None)
    if not viewer or int(viewer.get("gradatie", 7) or 7) > 2:
        raise HTTPException(403, "Alleen admin (gradatie ≤ 2) mag bulk-sync uitvoeren.")
    roar = load_json(ROAR, default={"balances": {}})
    balances = roar.get("balances", {})
    results = []
    for uid, n in balances.items():
        if uid == "user-000":
            continue
        try:
            n = int(n)
        except (TypeError, ValueError):
            continue
        # Probeer eerst expand, dan trim
        add_r = potjes_svc.sync_potjes_to_tokens(uid, n)
        trim_r = potjes_svc.trim_potjes_to_tokens(uid, n)
        results.append({
            "user_id": uid,
            "tokens": n,
            "added": add_r.get("added", 0),
            "removed": trim_r.get("removed", 0),
            "final_count": trim_r.get("current", add_r.get("target", n)),
        })
    return {"success": True, "synced_users": len(results), "results": results}


@router.post("/potjes/{user_id}/{pot_id}/assign-market")
async def assign_pot_market(user_id: str, pot_id: str, market: str):
    """v6_one_bot_per_pot_001 — assign coin-market per pot (fase 1 van multi-bot)."""
    return potjes_svc.assign_pot_market(user_id, pot_id, market)


# v6_pot1_staking_lock_001 — toggle pot-lock (admin / Pot 1 wijzigen)
class TogglePotLockBody(BaseModel):
    pot_id: str
    locked: bool
    lock_reason: Optional[str] = "staking_anchor"


@router.post("/potjes/{user_id}/toggle-lock")
async def toggle_pot_lock(user_id: str, body: TogglePotLockBody):
    """Zet `pot_locked` op een specifiek potje aan/uit."""
    data = potjes_svc._load(user_id)
    user = data["users"].get(user_id, {})
    pot = next((p for p in user.get("potjes", []) if p.get("id") == body.pot_id), None)
    if not pot:
        return {"success": False, "error": f"Potje {body.pot_id} niet gevonden"}
    if pot.get("position", {}).get("is_open") and body.locked:
        return {"success": False, "error": "Potje heeft open positie — sluit eerst voor je het lockt."}
    pot["pot_locked"] = body.locked
    pot["lock_reason"] = body.lock_reason if body.locked else None
    potjes_svc._save(data)
    return {"success": True, "pot": pot}


# v5_potjes_distribute_001 — Verdeel potjes over markten (5x2, 10x1 etc.)
class DistributeBody(BaseModel):
    markets: List[str]


@router.post("/potjes/{user_id}/distribute")
async def distribute_potjes(user_id: str, body: DistributeBody):
    """Verdeel alle potjes evenredig over de gekozen markten (round-robin).
    Open posities blijven onaangeraakt op hun huidige market."""
    return potjes_svc.distribute_potjes_over_markets(user_id, body.markets)


# ============================================================
# v5_bot_proactive_register_001 — User opt-in zichtbaarheid in Analytics
# ============================================================
class RegisterBody(BaseModel):
    viewer_id: str


@router.post("/bot/register/{user_id}")
async def register_bot(user_id: str, body: RegisterBody):
    """Proactief: laat bot-slot van user zichtbaar zijn in Analytics zonder dat hij draait.
    Alleen de user zelf (of admin) mag dit doen."""
    from .monitor import register_user_bot
    if body.viewer_id != user_id and (body.viewer_id not in ("user-001",)):
        # Niet-admin mag alleen zichzelf registreren
        users_data = load_json(Path(__file__).parent.parent.parent / "data" / "system" / "users.json", default={})
        users_list = users_data.get("users", []) if isinstance(users_data, dict) else []
        viewer = next((u for u in users_list if (u.get("id") or u.get("user_id")) == body.viewer_id), None)
        if not viewer or viewer.get("gradatie", 99) > 1:
            return {"success": False, "error": "Mag alleen jezelf registreren"}
    return register_user_bot(user_id)


@router.post("/bot/unregister/{user_id}")
async def unregister_bot(user_id: str, body: RegisterBody):
    from .monitor import unregister_user_bot
    if body.viewer_id != user_id:
        users_data = load_json(Path(__file__).parent.parent.parent / "data" / "system" / "users.json", default={})
        users_list = users_data.get("users", []) if isinstance(users_data, dict) else []
        viewer = next((u for u in users_list if (u.get("id") or u.get("user_id")) == body.viewer_id), None)
        if not viewer or viewer.get("gradatie", 99) > 1:
            return {"success": False, "error": "Mag alleen jezelf afmelden"}
    return unregister_user_bot(user_id)


@router.get("/bot/register-status/{user_id}")
async def register_status(user_id: str):
    from .monitor import is_registered
    return {"user_id": user_id, "registered": is_registered(user_id)}


# ============================================================
# v5_admin_force_sell_001 — Admin force-sell van een specifiek potje
# ============================================================
class ForceSellBody(BaseModel):
    viewer_id: str
    reason: Optional[str] = None


# ============================================================
# v7_pot_revalue_001 — Handmatige "Herwaardeer" knop per pot en globaal
# ============================================================
class RevalueBody(BaseModel):
    viewer_id: str


def _get_token_price_and_check_admin(viewer_id: str) -> Dict:
    """Helper: valideer admin + fetch huidige dynamische token-prijs."""
    users_data = load_json(Path(__file__).parent.parent.parent / "data" / "system" / "users.json", default={})
    users_list = users_data.get("users", []) if isinstance(users_data, dict) else []
    viewer = next((u for u in users_list if (u.get("id") or u.get("user_id")) == viewer_id), None)
    if not viewer or viewer.get("gradatie", 99) > 1:
        return {"success": False, "error": "Alleen admins (gradatie ≤ 1) mogen herwaarderen"}
    try:
        from modules.shop.routes import get_dynamic_price
        return {"success": True, "price": float(get_dynamic_price())}
    except Exception as e:
        return {"success": False, "error": f"Kon token-prijs niet ophalen: {e}"}


@router.post("/potjes/{user_id}/revalue-all")
async def revalue_all_pots(user_id: str, body: RevalueBody):
    """Zet capital van alle VRIJE pots op de huidige dynamische token-prijs.

    Open pots blijven ongewijzigd. Dit gebeurt automatisch elke monitor-tick,
    maar dit endpoint is voor de handmatige knop in het trader-kader.
    """
    chk = _get_token_price_and_check_admin(body.viewer_id)
    if not chk["success"]:
        return chk
    result = potjes_svc.revalue_free_pots(user_id, chk["price"])
    result["token_price_used"] = chk["price"]
    return result


@router.post("/potjes/{user_id}/{pot_id}/revalue")
async def revalue_single_pot_endpoint(user_id: str, pot_id: str, body: RevalueBody):
    """Handmatig 1 pot op huidige token-prijs zetten (admin-knop naast force-sell)."""
    chk = _get_token_price_and_check_admin(body.viewer_id)
    if not chk["success"]:
        return chk
    result = potjes_svc.revalue_single_pot(user_id, pot_id, chk["price"])
    result["token_price_used"] = chk["price"]
    return result


@router.post("/potjes/{user_id}/{pot_id}/force-sell")
async def force_sell_pot(user_id: str, pot_id: str, body: ForceSellBody):
    """Admin-only: sluit een specifiek potje op huidige marktprijs.
    LET OP: dit kan verlies geven → tokens devalueren. Audit-trail wordt bijgehouden."""
    # Admin-check
    users_data = load_json(Path(__file__).parent.parent.parent / "data" / "system" / "users.json", default={})
    users_list = users_data.get("users", []) if isinstance(users_data, dict) else []
    viewer = next((u for u in users_list if (u.get("id") or u.get("user_id")) == body.viewer_id), None)
    if not viewer or viewer.get("gradatie", 99) > 1:
        return {"success": False, "error": "Alleen admins (gradatie ≤ 1) mogen force-sell"}

    # Vind potje
    user_data = potjes_svc.get_potjes(user_id)
    pot = next((p for p in user_data.get("potjes", []) if p.get("id") == pot_id), None)
    if not pot:
        return {"success": False, "error": f"Potje {pot_id} niet gevonden voor {user_id}"}
    if not pot.get("position", {}).get("is_open"):
        return {"success": False, "error": "Potje is niet open — niets om te verkopen"}

    # Live prijs ophalen
    market = pot.get("market") or "BCH-EUR"
    tickers = fetch_tickers()
    ticker = next((t for t in tickers if t.get("market") == market), None)
    if not ticker:
        return {"success": False, "error": f"Geen live prijs voor {market}"}
    exit_price = float(ticker.get("last") or ticker.get("price") or 0)
    if exit_price <= 0:
        return {"success": False, "error": "Ongeldige live prijs"}

    # v6_force_sell_real_001 (sessie 16) — voer echte Bitvavo SELL uit voordat
    # we administratief sluiten. Anders blijft de coin op Bitvavo en raken JSON
    # en realiteit uit sync. execute_real_trade gebruikt Spark's keys via proxy.
    # v7_force_sell_atomic_001 — Bail out BEFORE close_pot als Bitvavo weigerde.
    # Voorheen: pot werd gesloten + PnL toegekend + Spark-bonus geactiveerd ook
    # als Bitvavo error 212/429 gaf → interne state raakte uit sync met Bitvavo.
    from .monitor import execute_real_trade
    # v7_dynamic_capital_fallback_001 — geen hardcode €10 meer. Als pot.capital
    # ontbreekt → val terug op huidige dynamische token-prijs.
    _cap = pot.get("capital")
    if not _cap:
        try:
            from modules.shop.routes import get_dynamic_price
            _cap = float(get_dynamic_price())
        except Exception:
            _cap = 5.08  # ultieme fallback = bodemprijs
    sell_result = execute_real_trade(user_id, market, "SELL", _cap)

    if not sell_result.get("success", False):
        # Bitvavo weigerde de sell — pot blijft OPEN, geen PnL, geen bonus.
        # Log toch in audit voor traceerbaarheid.
        try:
            audit_file = Path(__file__).parent.parent.parent / "data" / "trade" / "force_sell_audit.json"
            audit_file.parent.mkdir(parents=True, exist_ok=True)
            audit = load_json(audit_file, default={"entries": []})
            audit["entries"].append({
                "id": f"fs-{len(audit['entries']) + 1:04d}",
                "ts": datetime.now(timezone.utc).isoformat(),
                "type": "force_sell_rejected",
                "user_id": user_id,
                "pot_id": pot_id,
                "market": market,
                "exit_price": exit_price,
                "by_admin": body.viewer_id,
                "reason": body.reason or "geen opgegeven",
                "bitvavo_sell": sell_result,
                "note": "Pot NIET gesloten — Bitvavo weigerde de order. Geen PnL/bonus toegekend.",
            })
            save_json(audit_file, audit)
        except Exception:
            pass
        return {
            "success": False,
            "error": f"Bitvavo weigerde force-sell: {sell_result.get('error', 'onbekende fout')}",
            "bitvavo_error_code": sell_result.get("error_code"),
            "bitvavo_response": sell_result,
            "market": market,
            "pot_id": pot_id,
            "hint": "Pot blijft open. Als coin niet meer op Bitvavo staat (out-of-sync), gebruik /api/trade/reconcile/potjes/{user_id}/sync-with-bitvavo om restwaarde-pots op te ruimen zonder PnL.",
        }

    real_exit_price = (sell_result.get("trade") or {}).get("price") or exit_price

    # Close het potje (administratief) met echte fill-prijs — alleen als Bitvavo succes
    result = potjes_svc.close_pot(user_id, pot_id, real_exit_price)
    result["bitvavo_sell"] = sell_result

    # Audit-trail
    try:
        audit_file = Path(__file__).parent.parent.parent / "data" / "trade" / "force_sell_audit.json"
        audit_file.parent.mkdir(parents=True, exist_ok=True)
        audit = load_json(audit_file, default={"entries": []})
        audit["entries"].append({
            "id": f"fs-{len(audit['entries']) + 1:04d}",
            "ts": datetime.now(timezone.utc).isoformat(),
            "type": "force_sell",
            "user_id": user_id,
            "pot_id": pot_id,
            "market": market,
            "exit_price": exit_price,
            "by_admin": body.viewer_id,
            "reason": body.reason or "geen opgegeven",
            "result": result,
        })
        save_json(audit_file, audit)
    except Exception as e:
        result["audit_error"] = str(e)

    return {"success": True, "force_sell": result, "exit_price": exit_price, "market": market}


# ============================================================
# LEERMODULE - Trading Context (S/R, market state, patterns)
# ============================================================

@router.get("/context/{market}")
async def get_context(market: str, refresh: bool = False):
    """Haal context op voor market (uit cache of regenereer)."""
    if not refresh:
        cached = context_service.get_cached(market)
        if cached:
            return {"success": True, "context": cached, "from_cache": True}
    # Regenereer: 2 jaar 1h candles
    candles = fetch_candles(market, interval="1h", limit=1000)
    if not candles:
        return {"success": False, "error": "Geen candle data beschikbaar"}
    context = context_service.analyze(candles, market=market)
    context_service.save_cache(market, context)
    return {"success": True, "context": context, "from_cache": False}


@router.post("/context/refresh-all")
async def refresh_all_contexts():
    """Regenereer context voor alle leer-coins (BCH, BTC, ETH, SOL, ADA)."""
    results = {}
    for market in context_service.LEARNING_COINS:
        try:
            candles = fetch_candles(market, interval="1h", limit=1000)
            if not candles:
                results[market] = {"success": False, "error": "Geen data"}
                continue
            context = context_service.analyze(candles, market=market)
            context_service.save_cache(market, context)
            results[market] = {
                "success": True,
                "supports": len(context.get("support_levels", [])),
                "resistances": len(context.get("resistance_levels", [])),
                "trend": context.get("market_state", {}).get("trend"),
            }
        except Exception as e:
            results[market] = {"success": False, "error": str(e)}
    return {"success": True, "results": results}



# ============================================================
# v6_auto_provision_001 — Migratie: alle ROAR-token-holders zonder bot
# ============================================================
@router.post("/admin/migrate-token-holders")
async def migrate_token_holders():
    """
    Voor alle users met >0 ROAR-tokens die nog geen monitor-bot hebben:
    - register_user_bot
    - bot-config aanmaken (auto_trade=True, use_mock=False)
    - sync_potjes_to_tokens
    Idempotent: doet niks voor users die al een bot hebben.
    """
    from modules.trade.monitor import auto_provision_bot_for_token_holder
    from modules.trade.potjes import sync_potjes_to_tokens

    roar = load_json(DATA_DIR.parent / "roar" / "roar_balances.json", default={"balances": {}})
    balances = roar.get("balances", {})

    registry = load_json(TRADE_DIR / "bots_registry_state.json", default={"bots": []})
    existing_bot_users = {b.get("user_id") for b in registry.get("bots", []) if isinstance(b, dict)}

    results = []
    for uid, tokens in balances.items():
        try:
            t = int(tokens) if tokens else 0
        except Exception:
            t = 0
        if t <= 0:
            continue
        if uid == "user-000":  # Spark heeft eigen base-potjes
            continue
        already = uid in existing_bot_users
        try:
            sync_potjes_to_tokens(uid, t)
        except Exception as e:
            results.append({"user_id": uid, "tokens": t, "status": "potje-sync-failed", "error": str(e)})
            continue
        try:
            r = auto_provision_bot_for_token_holder(uid, use_mock=False, auto_trade=True, autostart=False)
            results.append({
                "user_id": uid, "tokens": t,
                "status": "already_had_bot" if already else "newly_provisioned",
                "running": r.get("running"),
            })
        except Exception as e:
            results.append({"user_id": uid, "tokens": t, "status": "provision-failed", "error": str(e)})

    return {"success": True, "total_users": len(results), "results": results}



# ============================================================
# v7_admin_start_all_bots_001 — Admin bulk-start voor alle geregistreerde bots
# ============================================================
class StartAllBotsBody(BaseModel):
    viewer_id: str


@router.post("/admin/start-all-bots")
async def admin_start_all_bots(body: StartAllBotsBody):
    """Admin-actie: start alle geregistreerde bots (Spark, Geiser, Willem, ...) in één klik.

    Idempotent: bots die al draaien worden overgeslagen. Non-admin krijgt error.
    """
    # Admin check
    users_data = load_json(Path(__file__).parent.parent.parent / "data" / "system" / "users.json", default={})
    users_list = users_data.get("users", []) if isinstance(users_data, dict) else []
    viewer = next((u for u in users_list if (u.get("id") or u.get("user_id")) == body.viewer_id), None)
    if not viewer or viewer.get("gradatie", 99) > 1:
        return {"success": False, "error": "Alleen admins (gradatie ≤ 1) mogen alle bots starten"}

    from modules.trade.monitor import get_monitor, get_user_monitor, _load_registered_users
    results = []

    # 1. Legacy Willem monitor
    try:
        m = get_monitor()
        if not m._running:
            m.start()
            results.append({"user_id": "user-001", "action": "started", "running": True})
        else:
            results.append({"user_id": "user-001", "action": "already_running", "running": True})
    except Exception as e:
        results.append({"user_id": "user-001", "action": "failed", "error": str(e)})

    # 2. Alle registry bots
    for uid in _load_registered_users():
        if uid == "user-001":
            continue
        try:
            m = get_user_monitor(uid)
            if not m._running:
                m.start()
                results.append({"user_id": uid, "action": "started", "running": True})
            else:
                results.append({"user_id": uid, "action": "already_running", "running": True})
        except Exception as e:
            results.append({"user_id": uid, "action": "failed", "error": str(e)})

    started = sum(1 for r in results if r.get("action") == "started")
    return {"success": True, "started_count": started, "total_bots": len(results), "results": results}


@router.post("/admin/stop-all-bots")
async def admin_stop_all_bots(body: StartAllBotsBody):
    """Admin-actie: stop alle draaiende bots in één klik."""
    users_data = load_json(Path(__file__).parent.parent.parent / "data" / "system" / "users.json", default={})
    users_list = users_data.get("users", []) if isinstance(users_data, dict) else []
    viewer = next((u for u in users_list if (u.get("id") or u.get("user_id")) == body.viewer_id), None)
    if not viewer or viewer.get("gradatie", 99) > 1:
        return {"success": False, "error": "Alleen admins (gradatie ≤ 1) mogen alle bots stoppen"}

    from modules.trade.monitor import get_monitor, get_user_monitor, _load_registered_users
    results = []
    try:
        m = get_monitor()
        if m._running:
            m.stop()
            results.append({"user_id": "user-001", "action": "stopped"})
    except Exception as e:
        results.append({"user_id": "user-001", "action": "failed", "error": str(e)})
    for uid in _load_registered_users():
        if uid == "user-001":
            continue
        try:
            m = get_user_monitor(uid)
            if m._running:
                m.stop()
                results.append({"user_id": uid, "action": "stopped"})
        except Exception as e:
            results.append({"user_id": uid, "action": "failed", "error": str(e)})
    stopped = sum(1 for r in results if r.get("action") == "stopped")
    return {"success": True, "stopped_count": stopped, "results": results}


# ============================================================
# v8_event_protection_001 — Event notifications endpoint
# ============================================================

@router.get("/events/notifications")
async def get_event_notifications(user_id: Optional[str] = None, limit: int = 50):
    """Recente shock-event notificaties (data-driven bot-pauzes).
    Filter op user_id indien opgegeven, anders alle users."""
    from pathlib import Path as _P
    notif_file = _P(__file__).parent.parent.parent / "data" / "trade" / "event_notifications.json"
    if not notif_file.exists():
        return {"success": True, "count": 0, "notifications": []}
    try:
        all_notifs = json.loads(notif_file.read_text())
    except Exception as e:
        return {"success": False, "error": str(e)}
    if user_id:
        all_notifs = [n for n in all_notifs if n.get("user_id") == user_id]
    all_notifs = sorted(all_notifs, key=lambda n: n.get("ts", ""), reverse=True)[:limit]
    return {"success": True, "count": len(all_notifs), "notifications": all_notifs}


@router.get("/backtests")
async def list_backtests():
    """Overzicht van alle backtest-runs (voor Spark's introspectie + admin UI)."""
    from pathlib import Path as _P
    idx_file = _P(__file__).parent.parent.parent / "data" / "trade" / "backtests" / "_meta.json"
    if not idx_file.exists():
        return {"success": True, "runs": []}
    try:
        idx = json.loads(idx_file.read_text())
        return {"success": True, "runs": idx.get("runs", []), "count": len(idx.get("runs", []))}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/backtests/{run_id}")
async def get_backtest(run_id: str):
    """Specifieke backtest-run: aggregate + meta (voor Spark om over te vertellen)."""
    from pathlib import Path as _P
    run_dir = _P(__file__).parent.parent.parent / "data" / "trade" / "backtests" / run_id
    if not run_dir.exists():
        # Try with _v3 suffix
        run_dir_v3 = _P(__file__).parent.parent.parent / "data" / "trade" / "backtests" / f"{run_id}_v3"
        if run_dir_v3.exists():
            run_dir = run_dir_v3
        else:
            return {"success": False, "error": "Backtest niet gevonden"}
    result = {"success": True, "run_id": run_id}
    for name in ("_meta", "aggregate"):
        f = run_dir / f"{name}.json"
        if f.exists():
            result[name] = json.loads(f.read_text())
    return result
