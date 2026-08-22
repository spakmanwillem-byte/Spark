"""
Trade Routes - Trade history, positions, Bitvavo credentials, monitoring, candles, tickers
"""
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime, timezone
import json
import re
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
# v13_trader_monthly_baseline_001 — Maandelijkse snapshot
# ============================================================

from modules.trade import monthly_baseline as _mb


@router.post("/baseline/monthly-snapshot/{user_id}")
async def monthly_snapshot(user_id: str, current_balance_eur: float):
    """Manuele snapshot voor 1 user (test / handmatig)."""
    snap = _mb.snapshot_user(user_id, current_balance_eur)
    return {"success": True, "snapshot": snap}


@router.get("/baseline/monthly/{user_id}")
async def monthly_history(user_id: str, limit: int = 12):
    return {"success": True, "history": _mb.list_monthly_snapshots(user_id, limit=limit)}


@router.get("/baseline/monthly")
async def monthly_history_all(limit: int = 12):
    return {"success": True, "history": _mb.list_monthly_snapshots(limit=limit)}


@router.post("/baseline/run-scheduled-snapshot")
async def run_scheduled_snapshot():
    """Check-and-run: als het de 1e is en nog niet gedraaid, snapshot alle users."""
    if not _mb.should_run_snapshot():
        return {"success": True, "ran": False, "reason": "Niet de 1e vd maand of al gedaan"}
    dw = load_json(DATA_DIR.parent / "system" / "deposit_watcher_state.json", default={})
    bitvavo_eur = float(dw.get("last_known_eur", 0.0) or dw.get("last_balance_eur", 0.0) or 0.0)
    def _bal(uid: str) -> float:
        return bitvavo_eur if uid == "user-000" else 0.0
    results = _mb.snapshot_all(_bal)
    _mb.mark_snapshot_done()
    return {"success": True, "ran": True, "snapshots": len(results), "results": results}




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

    # v10_deposit_papertrail_001 — Log elke deposit/withdrawal/donation naar
    # boekhouder log-agent (topic="deposit"). Hash-chained paper trail.
    try:
        from modules.boekhouder.agents.log_agent import LogAgent
        log_ev = LogAgent().record(
            topic="deposit",
            event_type=f"{req.type}_registered",
            actor=user_id,
            data={
                "deposit_id": entry["id"],
                "type": req.type,
                "amount_eur": req.amount_eur,
                "source": req.source or "onbekend",
                "description": req.description or "",
            }
        )
        entry["log_event_id"] = log_ev["event_id"]
        data[user_id] = deposits
        save_json(dep_file, data)
    except Exception as _ex:
        print(f"[deposit] papertrail log failed (non-blocking): {_ex}")

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


# ============================================================
# DEPLOY-SAFETY (v10_deploy_safety_001) — voorkom prod/preview race conditions
# Willem's sessie 46-scenario: bot draaide in prod ÉN preview tijdens deploy,
# resultaat: dubbele buy op ETH-EUR. Deze endpoints laten je de bot netjes
# pauzeren VOOR een deploy en herstellen NA de deploy.
# ============================================================

@router.post("/deploy/prepare")
async def deploy_prepare():
    """
    Pre-deploy: pauzeer ALLE actieve bots + snapshot huidige state naar disk.
    Idempotent: veilig meerdere keren aanroepen.

    Retourneert lijst van bots die gepauzeerd zijn en de pre-deploy state-snapshot.
    """
    from .monitor import _registry, _monitor
    from datetime import datetime, timezone
    from pathlib import Path
    import json

    paused = []
    state_snapshot = {
        "prepared_at": datetime.now(timezone.utc).isoformat(),
        "reason": "pre_deploy_safety",
        "bots": [],
    }

    # Legacy singleton (user-001)
    try:
        st = _monitor.get_status() or {}
        was_running = bool(st.get("running")) and not bool(st.get("paused"))
        if was_running and st.get("user_id") != "user-000":
            _monitor.pause()
            paused.append("user-001")
        state_snapshot["bots"].append({
            "user_id": st.get("user_id"),
            "was_running": was_running,
            "was_paused": bool(st.get("paused")),
            "market": st.get("market"),
            "markets": st.get("markets"),
            "position_open": bool((st.get("position") or {}).get("is_open")),
            "cycles": st.get("cycles"),
        })
    except Exception as e:
        state_snapshot["bots"].append({"user_id": "legacy", "error": str(e)})

    # Alle andere per-user bots
    for uid, mon in list(_registry.items()):
        try:
            st = mon.get_status() or {}
            was_running = bool(st.get("running")) and not bool(st.get("paused"))
            if was_running and uid != "user-000":
                mon.pause()
                paused.append(uid)
            state_snapshot["bots"].append({
                "user_id": uid,
                "was_running": was_running,
                "was_paused": bool(st.get("paused")),
                "market": st.get("market"),
                "position_open": bool((st.get("position") or {}).get("is_open")),
                "cycles": st.get("cycles"),
            })
        except Exception as e:
            state_snapshot["bots"].append({"user_id": uid, "error": str(e)})

    # Persist snapshot voor release-hydration
    fp = Path(__file__).parent.parent.parent / "data" / "trade" / "deploy_snapshot.json"
    fp.parent.mkdir(parents=True, exist_ok=True)
    fp.write_text(json.dumps(state_snapshot, indent=2))

    return {
        "success": True,
        "paused_now": paused,
        "total_bots_in_registry": len(_registry) + 1,  # +1 for legacy
        "snapshot": state_snapshot,
        "snapshot_file": str(fp),
        "hint": "Deploy nu safe. Na deploy: POST /api/trade/deploy/release om weer te resumen.",
    }


@router.post("/deploy/release")
async def deploy_release():
    """
    Post-deploy: herstel bots die vóór de deploy draaiden.
    Leest deploy_snapshot.json en resumet elke bot die 'was_running=True' had.
    """
    from .monitor import _registry, _monitor, get_user_monitor
    from pathlib import Path
    import json

    fp = Path(__file__).parent.parent.parent / "data" / "trade" / "deploy_snapshot.json"
    if not fp.exists():
        return {
            "success": False,
            "error": "geen deploy_snapshot.json gevonden — was /deploy/prepare gedraaid?",
        }
    try:
        snap = json.loads(fp.read_text())
    except Exception as e:
        return {"success": False, "error": f"kan snapshot niet parsen: {e}"}

    resumed = []
    skipped = []
    errors = []

    for bot_state in snap.get("bots", []):
        uid = bot_state.get("user_id")
        if not uid:
            continue
        if not bot_state.get("was_running"):
            skipped.append({"user_id": uid, "reason": "was niet running voor deploy"})
            continue
        try:
            mon = _monitor if uid == "user-001" else get_user_monitor(uid)
            # resume_if_was_running is idempotent + no-op als niet in pause-mode
            res = mon.resume_if_was_running()
            resumed.append({"user_id": uid, "result": res})
        except Exception as e:
            errors.append({"user_id": uid, "error": str(e)})

    return {
        "success": True,
        "resumed": resumed,
        "skipped": skipped,
        "errors": errors,
        "snapshot_used": snap.get("prepared_at"),
    }


@router.get("/deploy/status")
async def deploy_status():
    """Toont laatste deploy-snapshot + huidige running-state, handig voor UI-check."""
    from .monitor import _registry, _monitor
    from pathlib import Path
    import json

    fp = Path(__file__).parent.parent.parent / "data" / "trade" / "deploy_snapshot.json"
    snap = None
    if fp.exists():
        try:
            snap = json.loads(fp.read_text())
        except Exception:
            snap = {"error": "snapshot niet parsebaar"}

    current = []
    try:
        st = _monitor.get_status() or {}
        current.append({"user_id": st.get("user_id"), "running": st.get("running"),
                        "paused": st.get("paused")})
    except Exception:
        pass
    for uid, mon in list(_registry.items()):
        try:
            st = mon.get_status() or {}
            current.append({"user_id": uid, "running": st.get("running"),
                            "paused": st.get("paused")})
        except Exception:
            current.append({"user_id": uid, "error": True})

    return {"success": True, "last_snapshot": snap, "current_state": current}


# ============================================================
# ANKER (v10_anker_skeleton_001) — Read-only endpoints (feature flag off).
# ============================================================

@router.get("/anker/{market}")
async def get_anker_endpoint(market: str):
    """Lees anker-cache voor market. Retourneert null als cache leeg is."""
    from .anker_service import get_anker, _load_anker_config
    return {
        "success": True,
        "market": market,
        "anker": get_anker(market),
        "config": _load_anker_config(),
    }


@router.post("/anker/bootstrap/{market}")
async def bootstrap_anker_endpoint(market: str, user_id: str = Query("user-001")):
    """
    Admin-only: seed anker uit Bitvavo 30d candles.
    Werkt ONGEACHT feature-flag (voor zowel dry-run als warm-up).
    """
    from .anker_service import bootstrap_anker_from_bitvavo
    result = bootstrap_anker_from_bitvavo(market, user_id=user_id)
    return {"success": "error" not in result, "market": market, "result": result}


@router.get("/anker/shadow/events")
async def get_anker_shadow_events(days: int = Query(7, ge=1, le=90), market: Optional[str] = None,
                                   limit: int = Query(500, ge=1, le=5000)):
    """
    Read anker-events via `LogAgent` (topic="anker_check").
    Bestaande papertrail-conventie: `data/boekhouder/logs/anker_check/{YYYY-MM}.jsonl`,
    hash-chained, doorzoekbaar via `LogAgent().lookup()`.

    Query params:
      - days: aantal dagen terugkijken (1-90, default 7)
      - market: filter op market (optioneel)
      - limit: max events (default 500, max 5000)

    Retourneert events + aggregate stats.
    """
    from datetime import datetime as _dt, timedelta as _td, timezone as _tz
    from modules.boekhouder.agents.log_agent import LogAgent

    cutoff = _dt.now(_tz.utc) - _td(days=days)
    raw = LogAgent().lookup(topic="anker_check", limit=limit)

    events = []
    for ev in raw:
        # Time filter
        try:
            ev_dt = _dt.fromisoformat(ev.get("timestamp", "").replace("Z", "+00:00"))
            if ev_dt < cutoff:
                continue
        except Exception:
            pass
        # Market filter
        if market and ev.get("data", {}).get("market") != market:
            continue
        events.append(ev)

    # Aggregate
    stats = {
        "total": len(events),
        "would_skip_count": sum(1 for e in events if not e.get("data", {}).get("allow")),
        "above_threshold_count": sum(1 for e in events if e.get("data", {}).get("above_threshold")),
        "allow_count": sum(1 for e in events if e.get("data", {}).get("allow")),
        "markets": sorted({e.get("data", {}).get("market") for e in events if e.get("data", {}).get("market")}),
        "avg_delta_pct": (sum(float(e.get("data", {}).get("delta_pct") or 0) for e in events) / len(events)) if events else 0.0,
    }
    return {"success": True, "days": days, "market_filter": market, "stats": stats, "events": events}


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


# v13u_reconcile_close_sold_001 — close open potjes waarvan coin bijna weg is op Bitvavo
@router.post("/reconcile/close-sold/{user_id}")
async def reconcile_close_sold(user_id: str, dry_run: bool = True):
    """Sync potjes met Bitvavo realiteit: voor elk open potje waar de coin nu ~0 op
    Bitvavo staat (i.p.v. de amount die het potje verwacht), roep `close_pot()` aan
    met de laatst-bekende marktprijs. Zo klopt de potjes-JSON weer met de werkelijkheid.

    Gebruikt door de reconcile-panel-knop "Sync verkopen met Bitvavo".

    Args:
        user_id: user wiens potjes gesynct moeten worden (meestal user-000)
        dry_run: True = alleen tonen wat er zou gebeuren, geen wijziging

    Returns:
        {success, closed: [...], skipped: [...], dry_run}
    """
    from modules.trade.monitor import fetch_bitvavo_balance, fetch_tickers
    from modules.trade import potjes as _p

    bal = fetch_bitvavo_balance(user_id)
    if not bal.get("success"):
        return {"success": False, "error": bal.get("error", "bitvavo balance fetch failed")}
    coin_avail = {b["symbol"]: float(b.get("available", 0)) for b in bal.get("balances", [])}

    data = _p._load(user_id)
    potjes = data.get("users", {}).get(user_id, {}).get("potjes", []) or []

    # Verzamel unieke markten van open potjes en fetch tickers
    open_markets = list({p.get("market") for p in potjes if (p.get("position") or {}).get("is_open") and p.get("market")})
    price_map = {}
    if open_markets:
        symbols = [m.split("-")[0] for m in open_markets]
        for t in fetch_tickers(symbols):
            sym = t.get("symbol") or (t.get("market", "").split("-")[0])
            last = t.get("last") or t.get("price")
            if sym and last:
                price_map[f"{sym}-EUR"] = float(last)

    closed = []
    skipped = []
    THRESHOLD_COIN = 0.05  # <5% van verwachte coin-amount = verkocht

    for pot in potjes:
        pos = pot.get("position") or {}
        if not pos.get("is_open"):
            continue
        if pot.get("pot_locked"):
            skipped.append({"pot_id": pot["id"], "reason": "pot_locked"})
            continue
        market = pot.get("market", "")
        sym = market.split("-")[0] if market else ""
        entry = pos.get("entry_price")
        amt_eur = pos.get("amount_eur") or pot.get("capital", 0)
        if not (sym and entry and amt_eur):
            skipped.append({"pot_id": pot["id"], "reason": "missing market/entry/amount"})
            continue
        expected_coin = amt_eur / entry
        actual_coin = coin_avail.get(sym, 0.0)
        # Coin bijna weg (< 5% van verwacht)? Dan is 'ie op Bitvavo verkocht
        if actual_coin < expected_coin * THRESHOLD_COIN:
            current_price = price_map.get(market)
            if not current_price:
                skipped.append({"pot_id": pot["id"], "reason": "no live price"})
                continue
            action = {
                "pot_id": pot["id"],
                "market": market,
                "entry": entry,
                "amount_eur": amt_eur,
                "expected_coin": round(expected_coin, 8),
                "actual_coin": round(actual_coin, 8),
                "exit_price": current_price,
                "estimated_pnl_pct": round(((current_price - entry) / entry) * 100, 2),
            }
            if not dry_run:
                # v13u_reconcile_close_sold_001 — VEILIGE in-place close (geen finance_hub
                # auto-mint side-effect). close_pot() triggert `check_auto_mint_hook` die
                # de bestaande potjes-capital revalueert → capital=0. Hier alleen JSON-mutatie.
                capital = float(pot.get("capital", 0) or 0)
                profit_pct = (current_price - entry) / entry
                bruto = capital * profit_pct
                fees = capital * 0.0025 * 2  # BITVAVO_TAKER_FEE roundtrip
                netto = round(bruto - fees, 4)
                new_capital = round(capital + netto, 4)
                pot["capital"] = new_capital
                pot["position"] = {
                    "is_open": False,
                    "entry_price": None,
                    "highest_price": None,
                    "trailing_active": False,
                    "entry_time": None,
                }
                stats = pot.setdefault("stats", {"trades": 0, "wins": 0, "losses": 0, "total_pnl": 0.0})
                stats["trades"] = int(stats.get("trades", 0)) + 1
                if netto > 0:
                    stats["wins"] = int(stats.get("wins", 0)) + 1
                else:
                    stats["losses"] = int(stats.get("losses", 0)) + 1
                stats["total_pnl"] = round(float(stats.get("total_pnl", 0)) + netto, 4)
                pot["last_action"] = f"SELL @ €{current_price:.2f} | reconcile | netto €{netto:+.3f}"
                pot.setdefault("reconcile_audit", []).append({
                    "ts": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
                    "type": "reconcile_close_sold",
                    "entry": entry,
                    "exit_price": current_price,
                    "capital_before": capital,
                    "capital_after": new_capital,
                    "netto": netto,
                    "expected_coin": round(expected_coin, 8),
                    "actual_coin": round(actual_coin, 8),
                })
                action["closed"] = True
                action["netto_eur"] = netto
                action["capital_after"] = new_capital
            closed.append(action)
        else:
            skipped.append({
                "pot_id": pot["id"],
                "market": market,
                "reason": "still open on bitvavo",
                "expected_coin": round(expected_coin, 8),
                "actual_coin": round(actual_coin, 8),
            })

    # v13u_reconcile_close_sold_001 — persist mutaties naar disk
    if not dry_run and closed:
        _p._save(data)

    return {
        "success": True,
        "dry_run": dry_run,
        "closed": closed,
        "skipped": skipped,
        "n_closed": len(closed),
        "n_skipped": len(skipped),
    }


# v13u_reconcile_close_sold_all_001 — bulk voor ALLE users met potjes (Spark + Willem + Geiser + ...)
@router.post("/reconcile/close-sold-all")
async def reconcile_close_sold_all(dry_run: bool = True):
    """Draai `reconcile_close_sold` voor elke user die potjes heeft in user_potjes.json.
    Zo werken Spark (user-000), Willem (user-001), Geiser (user-a0ee2d7e) en andere
    trader-users allemaal in 1 klik gesynced met hun eigen Bitvavo-balance.
    """
    from modules.trade import potjes as _p
    from modules.core.storage import load_json as _lj
    from pathlib import Path as _Path
    # Direct de JSON lezen zonder een fake user aan te maken via _load(user_id)
    _fp = _Path(__file__).parent.parent.parent / "data" / "financial" / "user_potjes.json"
    data = _lj(_fp, default={"users": {}}) or {"users": {}}
    users = (data or {}).get("users", {}) or {}
    per_user = {}
    total_closed = 0
    total_skipped = 0
    errors = []
    for uid, u in users.items():
        # Skip meta-keys en de "null" string-key uit oude data
        if not isinstance(u, dict) or uid in (None, "null", "__ignored__"):
            continue
        potjes = u.get("potjes") or []
        # Alleen users die minstens 1 open potje hebben verdienen een sync-poging
        if not any((p.get("position") or {}).get("is_open") for p in potjes):
            per_user[uid] = {"skipped": True, "reason": "no open potjes"}
            continue
        try:
            result = await reconcile_close_sold(uid, dry_run=dry_run)
            per_user[uid] = result
            total_closed += result.get("n_closed", 0)
            total_skipped += result.get("n_skipped", 0)
        except Exception as ex:
            errors.append({"user_id": uid, "error": str(ex)})
            per_user[uid] = {"success": False, "error": str(ex)}
    return {
        "success": True,
        "dry_run": dry_run,
        "n_users_processed": len(per_user),
        "total_closed": total_closed,
        "total_skipped": total_skipped,
        "per_user": per_user,
        "errors": errors,
    }


@router.get("/potjes/{user_id}")
async def get_user_potjes(user_id: str):
    """Haal potjes overzicht op — v10_finance_hub: overlay dynamische capital uit token-prijs.

    Elke pot krijgt `capital_dynamic` = current_token_price, en `live_value` wordt
    aangevuld als hij ontbreekt. Dit zorgt dat Trader-UI en Analytics de hybride
    Willem-regel (1 token = 1 pot @ current_price) live tonen.
    """
    summary = potjes_svc.get_summary(user_id)
    potjes_list = potjes_svc.get_potjes(user_id)["potjes"]

    # Overlay dynamic capital uit finance_hub
    try:
        from modules.boekhouder.finance_hub import get_hub
        price_info = get_hub().get_price()
        dynamic_price = price_info.get("current_price_eur", 0)
        # v10_finance_hub_ui_sync — summary strings updaten
        summary["current_max_per_pot"] = dynamic_price
        summary["next_pot_max"] = price_info.get("base_pot_size_eur", 10.0)
        summary["next_pot_cost"] = price_info.get("next_mint_threshold_eur",
                                                  (len(potjes_list) + 1) * 10.0)
        summary["total_capital_dynamic"] = round(len(potjes_list) * dynamic_price, 2)
        summary["token_price_eur"] = dynamic_price
        for p in potjes_list:
            stored = float(p.get("capital", 0) or 0)
            p["capital_stored"] = stored
            p["capital_dynamic"] = dynamic_price
            # v13_pot_value_consistency_001 — voorheen overschreef deze overlay
            # `live_value` van CLOSED pots met dynamic_price (€10.00) waardoor
            # TraderPage (toont live_value) en AnalyticsPage (toont capital) uit
            # elkaar liepen: €10.00 vs €10.26. Nu geldt semantisch:
            #   • CLOSED pot → live_value = capital (boekwaarde met realized P&L)
            #   • OPEN pot   → live_value = mark-to-market (zie get_potjes())
            # dynamic_price blijft beschikbaar via `capital_dynamic` voor UI's die
            # de token-prijs apart willen laten zien (bv. finance-hub badge).
            position = p.get("position") or {}
            has_open = bool(position.get("is_open"))
            if not has_open:
                # Sync live_value naar boekwaarde (get_potjes() zette dit al zo,
                # maar we bevestigen expliciet voor duidelijkheid).
                p["live_value"] = stored
            elif p.get("live_value") is None:
                # Fallback voor open pots zonder mark-to-market fill.
                p["live_value"] = stored
            p["_hybrid_source"] = "finance_hub_v13"
        # Update summary total_capital naar dynamische som
        if potjes_list:
            summary["total_capital_dynamic"] = round(len(potjes_list) * dynamic_price, 2)
            summary["token_price_eur"] = dynamic_price
    except Exception as ex:
        print(f"[potjes] finance_hub overlay failed (non-blocking): {ex}")

    return {
        "success": True,
        "summary": summary,
        "potjes": potjes_list,
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
        from modules.boekhouder.finance_hub import get_hub
        price = float(get_hub().get_price().get("current_price_eur", 0))
        if price > 0:
            return {"success": True, "price": price}
        # fallback
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


# ============================================================
# v8_honest_pnl_001 — Eerlijke PnL metrics (Willems 100%-check)
# ============================================================

@router.get("/honest-pnl/{user_id}")
async def get_honest_pnl(user_id: str):
    """Eerlijke PnL: gerealiseerd + open drawdown + ECHT netto.

    De 100%-win-rate uit market_stats.json is misleidend omdat verlieslatende
    posities OPEN blijven staan (Willems 'nooit met verlies verkopen'-regel).
    Deze endpoint toont het HELE plaatje.

    Backtest v4 (20260709_213151) bewees: D €+2.63 gerealiseerd, €-15.79 open DD
    = ECHT netto €-13.16. Deze endpoint maakt dat live zichtbaar.
    """
    from modules.trade.bitvavo_client import get_price as _bitvavo_get_price
    try:
        pots = load_json(DATA_DIR / "trade" / "user_potjes.json") or {}
    except Exception:
        pots = {}
    user_pots = pots.get(user_id, [])
    if not isinstance(user_pots, list):
        user_pots = user_pots.get("pots", []) if isinstance(user_pots, dict) else []

    # Realized PnL uit trade history / market_stats
    try:
        stats = load_json(DATA_DIR / "trade" / "market_stats.json") or {}
        user_stats = stats.get("users", {}).get(user_id, {})
        realized_pnl = user_stats.get("total_pnl_eur", 0.0)
        realized_trades = user_stats.get("total_trades", 0)
        realized_wins = user_stats.get("wins", 0)
    except Exception:
        realized_pnl, realized_trades, realized_wins = 0.0, 0, 0

    open_positions = []
    total_open_drawdown = 0.0
    total_open_value = 0.0
    total_open_capital = 0.0
    for pot in user_pots:
        pos = pot.get("position") or {}
        if not pos.get("is_open"):
            continue
        market = pos.get("market") or pot.get("last_market")
        entry_price = pos.get("entry_price")
        size = pos.get("size") or 0
        capital = pot.get("capital", 0)
        if not (market and entry_price and size):
            continue
        current_price = entry_price
        try:
            p = _bitvavo_get_price(market)
            if p:
                current_price = float(p)
        except Exception:
            pass
        current_value = size * current_price
        unrealized = current_value - capital
        total_open_drawdown += unrealized
        total_open_value += current_value
        total_open_capital += capital
        # Time in position
        entry_ts = pos.get("entry_ts")
        held_hours = None
        if entry_ts:
            try:
                et = datetime.fromisoformat(entry_ts.replace("Z", "+00:00"))
                held_hours = round((datetime.now(timezone.utc) - et).total_seconds() / 3600, 1)
            except Exception:
                pass
        open_positions.append({
            "pot_id": pot.get("pot_id") or pot.get("id"),
            "market": market,
            "entry_price": round(entry_price, 4),
            "current_price": round(current_price, 4),
            "capital_eur": round(capital, 2),
            "current_value_eur": round(current_value, 2),
            "unrealized_eur": round(unrealized, 2),
            "unrealized_pct": round((current_value - capital) / capital * 100, 2) if capital else 0,
            "held_hours": held_hours,
        })

    echt_netto = realized_pnl + total_open_drawdown
    honesty_ratio = None
    if realized_pnl > 0:
        honesty_ratio = round(echt_netto / realized_pnl, 2)

    return {
        "success": True,
        "user_id": user_id,
        "as_of": datetime.now(timezone.utc).isoformat(),
        "realized": {
            "pnl_eur": round(realized_pnl, 2),
            "trades": realized_trades,
            "wins": realized_wins,
            "win_rate_pct": round(100 * realized_wins / realized_trades, 1) if realized_trades else 0,
            "_note": "Alleen GESLOTEN trades. Verlieslatende posities blijven open en tellen hier niet mee."
        },
        "open": {
            "positions": len(open_positions),
            "total_capital_eur": round(total_open_capital, 2),
            "total_current_value_eur": round(total_open_value, 2),
            "total_unrealized_eur": round(total_open_drawdown, 2),
            "positions_detail": open_positions,
        },
        "echt_netto_eur": round(echt_netto, 2),
        "honesty_ratio": honesty_ratio,
        "_honesty_ratio_note": (
            "Ratio van ECHT netto vs gerealiseerd. 1.0 = geen verstopte verliezen. "
            "0.5 = helft van 'winst' is illusie (verstopt in open verlies). "
            "Negatief = ECHT netto is verlies terwijl realized winst toont."
        ),
        "backtest_v4_ref": "20260709_213151_v4 — bewijs dat 100% win-rate misleidend was",
    }


# ============================================================
# v8_trader_explained_001 — Publieke uitleg-JSON voor privacyverklaring
# ============================================================

@router.get("/explained")
async def get_trader_explained():
    """Volledig transparante uitleg van Spark Trader voor bezoekers/auditors.

    Publieke leesroute — geen auth, geen user-id. Bedoeld voor:
    - Privacyverklaring "inhoudelijk bekijken"-link
    - Onafhankelijke auditors / journalistiek
    - Users die willen weten wat de bot precies doet

    Bron: backend/data/trade/spark_trader_public.json (single source of truth,
    handmatig onderhouden bij elke wezenlijke strategie-wijziging).
    """
    try:
        pad = TRADE_DIR / "spark_trader_public.json"
        data = load_json(pad) or {}
        return data
    except Exception as e:
        return {"success": False, "error": f"kan uitleg niet laden: {e}"}


# ============================================================
# v8_strategy_confidence_001 — Live confidence score per strategie
# ============================================================

@router.get("/strategy/confidence")
async def get_strategy_confidence(strategy_id: Optional[str] = None):
    """Live confidence-score per strategie op basis van blueprint + huidige data.

    Berekening (max 100):
      backtest_pass    → 30 (heeft ≥180d backtest met positieve gerealiseerd PnL)
      random_seed_pass → 15 (beter dan random-median of laagvariantie)
      bear_pass        → 15 (bear-market PnL > 0)
      honest_pnl_track → 20 (heeft honest_pnl loss-cut mechanisme)
      live_track       → 0-20 (opgebouwd uit live trade history; 0 = geen data)

    Return: dict per strategie of specifiek voor strategy_id.
    """
    try:
        from modules.core.blueprint import load_blueprint_cached
        bp = load_blueprint_cached("trade", "spark_trader") or {}
        strategieën = bp.get("strategieën", {}) or {}
    except Exception as e:
        return {"success": False, "error": f"blueprint niet leesbaar: {e}"}

    def score_one(sid: str, s: dict) -> Dict[str, Any]:
        conf = s.get("confidence", {}) or {}
        based = conf.get("gebaseerd_op", {}) or {}
        props = s.get("properties", []) or []

        # Bereken componenten live
        backtest_pass = 30 if (based.get("gerealiseerd_pnl_180d", 0) > 0 or based.get("gerealiseerd_pnl_360d", 0) > 0) else 10
        random_pass = 15 if based.get("random_seed_validatie") else 0
        bear_pass = 15 if based.get("bear_market_pnl", 0) > 0 else 0
        honest_track = 20 if ("loss_cut_48h_3pct" in props or "honest_pnl" in props) else 0
        # Live: check of er trade_history is voor deze strategie (proxy: is deze strategie actief?)
        live_track = 0
        if s.get("actief"):
            try:
                stats = load_json(TRADE_DIR / "market_stats.json", default={}) or {}
                total_users_trades = sum(u.get("total_trades", 0) for u in stats.get("users", {}).values())
                if total_users_trades > 0:
                    live_track = min(20, total_users_trades // 5)
            except Exception:
                pass

        computed_score = backtest_pass + random_pass + bear_pass + honest_track + live_track
        stored_score = conf.get("score", 0)

        return {
            "strategy_id": sid,
            "display_name": s.get("display_name", sid),
            "actief": bool(s.get("actief")),
            "properties": props,
            "confidence_score_stored": stored_score,
            "confidence_score_computed": min(100, computed_score),
            "breakdown": {
                "backtest_pass": backtest_pass,
                "random_seed_pass": random_pass,
                "bear_market_pass": bear_pass,
                "honest_pnl_track": honest_track,
                "live_track": live_track,
            },
            "hypothese_lineage": s.get("hypothese_lineage", {}),
            "spark_alignment": s.get("spark_alignment", {}),
        }

    if strategy_id:
        s = strategieën.get(strategy_id)
        if not s:
            return {"success": False, "error": f"strategie '{strategy_id}' niet gevonden"}
        return {"success": True, "strategy": score_one(strategy_id, s)}

    # Alle strategieën
    result = {sid: score_one(sid, s) for sid, s in strategieën.items()}
    return {
        "success": True,
        "actieve_strategie": bp.get("actieve_strategie"),
        "strategies": result,
        "_note": "computed = live berekening, stored = handmatig ingesteld in blueprint. Live groeit als trade_history data binnenkomt.",
    }



# ============================================================
# v8_strategy_synthesize_001 — Spark synthetiseert nieuwe strategieën uit properties
# ============================================================

# Property catalog — alle bekende bouwstenen met hun eigenschappen
_PROPERTY_CATALOG = {
    "bollinger_2sigma": {
        "categorie": "signaal",
        "beschrijving": "BUY-signaal wanneer prijs onder Bollinger lower band 2σ zakt (mean-reversion)",
        "conflicts_with": [],
        "requires": [],
    },
    "mean_reversion": {
        "categorie": "filosofie",
        "beschrijving": "Onderneemt kopen bij afwijking van gemiddelde, verwacht terugkeer",
        "conflicts_with": ["trend_following"],
        "requires": [],
    },
    "trend_following": {
        "categorie": "filosofie",
        "beschrijving": "Volgt bestaande momentum-richting (buy-high-sell-higher)",
        "conflicts_with": ["mean_reversion"],
        "requires": [],
    },
    "gap_body_50": {
        "categorie": "confirmatie",
        "beschrijving": "Laatste groene candle moet ≥50% van vorige rode body dekken",
        "conflicts_with": ["gap_body_95"],
        "requires": [],
    },
    "gap_body_95": {
        "categorie": "confirmatie",
        "beschrijving": "Strenge variant: 95% dekking (blokkeerde 100% signalen in backtest — niet aanbevolen)",
        "conflicts_with": ["gap_body_50"],
        "requires": [],
    },
    "n_red_green_pattern": {
        "categorie": "confirmatie",
        "beschrijving": "3 rode candles gevolgd door 1 groene (Neef's variant, extreme oversold)",
        "conflicts_with": [],
        "requires": [],
    },
    "loss_cut_48h_3pct": {
        "categorie": "bescherming",
        "beschrijving": "Forceer SELL na 48u als positie ≤-3% verlies staat (verlies zichtbaar realiseren)",
        "conflicts_with": ["hold_indefinitely"],
        "requires": [],
    },
    "hold_indefinitely": {
        "categorie": "bescherming",
        "beschrijving": "Verkoop nooit met verlies — geeft 100% win-rate maar verbergt drawdown",
        "conflicts_with": ["loss_cut_48h_3pct"],
        "requires": [],
    },
    "event_pause_5pct_24h": {
        "categorie": "bescherming",
        "beschrijving": "Bij daily drop >5% → markt 24u pauze + notificatie",
        "conflicts_with": [],
        "requires": [],
    },
    "trailing_stop": {
        "categorie": "exit",
        "beschrijving": "Activeert bij +0.5% winst, sluit bij -0.4% terugval vanaf top",
        "conflicts_with": [],
        "requires": [],
    },
    "fee_aware_sell": {
        "categorie": "exit",
        "beschrijving": "Weigert SELL als netto na 0.25% Bitvavo-fee < €0.01 winst",
        "conflicts_with": [],
        "requires": [],
    },
    "honest_pnl": {
        "categorie": "meta",
        "beschrijving": "Toont gerealiseerd + open drawdown + ECHT netto + honesty ratio",
        "conflicts_with": [],
        "requires": [],
    },
    "extreme_oversold": {
        "categorie": "signaal",
        "beschrijving": "Alleen kopen bij extreme dips (breed onder mean)",
        "conflicts_with": [],
        "requires": [],
    },
}


class StrategySynthesizeBody(BaseModel):
    display_name: Optional[str] = None
    properties: List[str] = []
    author: Optional[str] = "spark"
    notes: Optional[str] = None


@router.get("/strategy/properties")
async def list_strategy_properties():
    """Property catalog — alle bouwstenen met categorie + beschrijving + conflicts."""
    return {"success": True, "properties": _PROPERTY_CATALOG}


@router.post("/strategy/synthesize")
async def synthesize_strategy(body: StrategySynthesizeBody):
    """Combineer properties tot een nieuwe strategie-blueprint + backtest-plan.

    Valideert conflicts en genereert:
      - strategy_id (kebab_case van display_name)
      - beschrijving (autogenereerd uit properties)
      - spark_alignment (waarom/regels/data/hypothese/zekerheid — placeholder)
      - hypothese_lineage stub (wachtend op backtest)
      - backtest_plan met parameters die getest moeten worden

    Persistent: schrijft naar `spark_trader.json.strategieën[strategy_id]` als draft.
    Backtest zelf wordt niet automatisch gedraaid (dat is een aparte P2-taak).
    """
    props = [p.strip() for p in (body.properties or []) if p.strip()]
    if not props:
        return {"success": False, "error": "properties[] mag niet leeg zijn"}

    # Validate: onbekende properties
    unknown = [p for p in props if p not in _PROPERTY_CATALOG]
    if unknown:
        return {"success": False, "error": f"onbekende properties: {unknown}", "beschikbaar": list(_PROPERTY_CATALOG.keys())}

    # Validate: conflicts
    conflicts_found = []
    for p in props:
        for c in _PROPERTY_CATALOG[p].get("conflicts_with", []):
            if c in props:
                conflicts_found.append((p, c))
    if conflicts_found:
        return {"success": False, "error": "conflicterende properties", "conflicts": conflicts_found}

    # Genereer strategy_id
    disp = body.display_name or " + ".join(props[:3])
    strategy_id = disp.lower().replace(" ", "_").replace("+", "_plus_").replace("-", "_")
    strategy_id = re.sub(r"[^a-z0-9_]", "", strategy_id)[:60]

    # Genereer beschrijving
    signal_props = [p for p in props if _PROPERTY_CATALOG[p]["categorie"] == "signaal"]
    conf_props = [p for p in props if _PROPERTY_CATALOG[p]["categorie"] == "confirmatie"]
    prot_props = [p for p in props if _PROPERTY_CATALOG[p]["categorie"] == "bescherming"]
    exit_props = [p for p in props if _PROPERTY_CATALOG[p]["categorie"] == "exit"]

    beschrijving_parts = []
    if signal_props: beschrijving_parts.append(f"Signaal: {' + '.join(signal_props)}")
    if conf_props: beschrijving_parts.append(f"Confirmatie: {' + '.join(conf_props)}")
    if prot_props: beschrijving_parts.append(f"Bescherming: {' + '.join(prot_props)}")
    if exit_props: beschrijving_parts.append(f"Exit: {' + '.join(exit_props)}")
    beschrijving = ". ".join(beschrijving_parts) + "."

    # Genereer regels lijst
    regels = [_PROPERTY_CATALOG[p]["beschrijving"] for p in props]

    # Backtest plan
    backtest_plan = {
        "test_periode_dagen": 360,
        "vergelijking_met": ["mean_reversion_bollinger (baseline)", "gap_momentum_50 (actieve strategie)"],
        "success_criteria": {
            "echt_netto_pnl_beter_dan_baseline": True,
            "random_seed_check": True,
            "bear_market_pnl_positief": True,
            "honest_pnl_beschikbaar": "loss_cut_48h_3pct" in props,
        },
        "markten": ["BCH-EUR", "BTC-EUR", "ETH-EUR", "SOL-EUR", "ATOM-EUR"],
        "trade_bedrag_eur": 10,
        "bitvavo_fee_pct": 0.25,
    }

    strategy_obj = {
        "display_name": disp,
        "beschrijving": beschrijving,
        "actief": False,
        "status": "draft_synthesized",
        "author": body.author or "spark",
        "synthesized_at": datetime.now(timezone.utc).isoformat(),
        "notes": body.notes or "",
        "properties": props,
        "confidence": {
            "score": 0,
            "berekening": "geen backtest data — draft",
            "gebaseerd_op": {"backtest_dagen": 0, "live_resultaten": "geen"},
            "toelichting": "Nieuwe synthese — backtest nodig voor score",
        },
        "hypothese_lineage": {
            "hypothese": f"De combinatie {' + '.join(props)} presteert beter dan de individuele componenten",
            "backtest_run": "TODO",
            "resultaat": "TODO",
            "conclusie": "TODO",
        },
        "spark_alignment": {
            "waarom": f"Synthese door {body.author or 'spark'} — combineert {len(props)} bouwstenen uit property catalog",
            "regels": regels,
            "data_bronnen": ["property_catalog v1", "voorgaande backtest-runs v2..v5"],
            "onderliggende_hypothese": f"Property-combinatie levert emergent gedrag: {beschrijving}",
            "zekerheid": "0% — draft zonder backtest",
        },
        "backtest_plan": backtest_plan,
    }

    # Persist naar blueprint als draft
    try:
        bp_path = Path(__file__).parent / "blueprints" / "spark_trader.json"
        bp_data = json.loads(bp_path.read_text(encoding="utf-8"))
        strategies = bp_data.setdefault("strategieën", {})
        if strategy_id in strategies and not strategies[strategy_id].get("status", "").startswith("draft"):
            return {"success": False, "error": f"strategy_id '{strategy_id}' bestaat al als niet-draft — kies andere naam"}
        strategies[strategy_id] = strategy_obj
        bp_path.write_text(json.dumps(bp_data, ensure_ascii=False, indent=2), encoding="utf-8")
        # clear cache
        try:
            from modules.core.blueprint import clear_blueprint_cache
            clear_blueprint_cache()
        except Exception:
            pass
    except Exception as e:
        return {"success": False, "error": f"blueprint schrijven mislukt: {e}", "draft": strategy_obj}

    # v9_adaptive_lab_001 — Auto-compare met actieve strategie voor directe feedback
    compared_to_active = None
    try:
        actieve = bp_data.get("actieve_strategie")
        if actieve and actieve != strategy_id:
            compared_to_active = await compare_strategies(a=strategy_id, b=actieve)
    except Exception as _e:
        pass

    return {
        "success": True,
        "message": f"Draft-strategie '{strategy_id}' opgeslagen. Backtest is nodig voor confidence-score.",
        "strategy_id": strategy_id,
        "strategy": strategy_obj,
        "compared_to_active": compared_to_active,
        "spark_feedback": _build_spark_synthesize_feedback(strategy_id, compared_to_active),
    }


def _build_spark_synthesize_feedback(new_id: str, comp: Optional[Dict]) -> str:
    """Genereer Spark's inhoudelijke feedback over een net gesynthetiseerde strategie."""
    if not comp or not comp.get("success"):
        return f"Je nieuwe draft '{new_id}' is opgeslagen. Backtest deze om confidence te bepalen."
    scores = comp.get("score", {})
    winner = comp.get("overall_winner")
    active_name = comp.get("strategies", {}).get("b", {}).get("display_name", "actieve strategie")
    new_name = comp.get("strategies", {}).get("a", {}).get("display_name", new_id)
    a_score = scores.get(new_id, 0)
    if winner == new_id:
        pref = f"🚀 Je nieuwe draft **{new_name}** scoort **{a_score}/5** secties beter dan **{active_name}**"
    elif winner == "tie":
        pref = f"⚖️ **{new_name}** eindigt gelijk met **{active_name}** ({a_score}/5)"
    else:
        pref = f"🤔 **{new_name}** scoort {a_score}/5 secties beter dan **{active_name}** — draft heeft nog werk"
    # Section highlights
    highlights = []
    for name, sec in (comp.get("sections", {}) or {}).items():
        if isinstance(sec, dict) and sec.get("winner") == new_id:
            label = {
                "confidence": "hogere confidence",
                "properties": "meer beschermings-eigenschappen",
                "bear_market_pnl": "beter in bear-markten",
                "honesty": "eerlijker (honesty ratio)",
                "maturity": "afgeronde hypothese",
            }.get(name, name)
            highlights.append(label)
    if highlights:
        pref += f". Sterk op: {', '.join(highlights)}."
    if a_score < 3:
        pref += f" Advies: voeg loss_cut_48h_3pct + event_pause_5pct_24h toe voor honesty."
    else:
        pref += f" Klaar voor backtest — draai backtest_v2.py met deze properties om confidence te valideren."
    return pref



# ============================================================
# v8_strategy_compare_001 — Confidence battle: side-by-side twee strategieën
# ============================================================

@router.get("/strategy/compare")
async def compare_strategies(a: str, b: str):
    """Vergelijk twee strategieën op alle relevante velden en bepaal winnaar per sectie."""
    try:
        from modules.core.blueprint import load_blueprint_cached
        bp = load_blueprint_cached("trade", "spark_trader") or {}
        strategieën = bp.get("strategieën", {}) or {}
    except Exception as e:
        return {"success": False, "error": f"blueprint niet leesbaar: {e}"}

    sa = strategieën.get(a)
    sb = strategieën.get(b)
    if not sa:
        return {"success": False, "error": f"strategie '{a}' niet gevonden"}
    if not sb:
        return {"success": False, "error": f"strategie '{b}' niet gevonden"}

    def _pick(obj, path, default=None):
        cur = obj
        for k in path.split("."):
            if not isinstance(cur, dict):
                return default
            cur = cur.get(k, default)
            if cur is None:
                return default
        return cur

    conf_a = int(_pick(sa, "confidence.score", 0) or 0)
    conf_b = int(_pick(sb, "confidence.score", 0) or 0)
    conf_winner = a if conf_a > conf_b else b if conf_b > conf_a else "tie"

    props_a = set(sa.get("properties", []) or [])
    props_b = set(sb.get("properties", []) or [])
    prot_props = {"loss_cut_48h_3pct", "event_pause_5pct_24h", "honest_pnl", "fee_aware_sell"}
    prot_a = len(props_a & prot_props)
    prot_b = len(props_b & prot_props)
    prot_winner = a if prot_a > prot_b else b if prot_b > prot_a else "tie"

    based_a = _pick(sa, "confidence.gebaseerd_op", {}) or {}
    based_b = _pick(sb, "confidence.gebaseerd_op", {}) or {}
    bear_a = float(based_a.get("bear_market_pnl", 0) or 0)
    bear_b = float(based_b.get("bear_market_pnl", 0) or 0)
    bear_winner = a if bear_a > bear_b else b if bear_b > bear_a else "tie"

    honesty_a = based_a.get("honesty_ratio")
    honesty_b = based_b.get("honesty_ratio")

    def _honesty_score(h):
        if h is None:
            return -999
        return -abs((h or 0) - 1.0) if (h or 0) > 0 else -1000 + (h or 0)

    honesty_winner = (
        a if _honesty_score(honesty_a) > _honesty_score(honesty_b)
        else b if _honesty_score(honesty_b) > _honesty_score(honesty_a)
        else "tie"
    )

    conc_a = bool(_pick(sa, "hypothese_lineage.conclusie") and _pick(sa, "hypothese_lineage.conclusie") != "TODO")
    conc_b = bool(_pick(sb, "hypothese_lineage.conclusie") and _pick(sb, "hypothese_lineage.conclusie") != "TODO")
    maturity_winner = a if conc_a and not conc_b else b if conc_b and not conc_a else "tie"

    winners = [conf_winner, prot_winner, bear_winner, honesty_winner, maturity_winner]
    scores = {a: winners.count(a), b: winners.count(b), "tie": winners.count("tie")}
    if scores[a] > scores[b]:
        overall = a
    elif scores[b] > scores[a]:
        overall = b
    else:
        overall = "tie"

    return {
        "success": True,
        "strategies": {
            "a": {"id": a, "display_name": sa.get("display_name", a), "actief": bool(sa.get("actief"))},
            "b": {"id": b, "display_name": sb.get("display_name", b), "actief": bool(sb.get("actief"))},
        },
        "sections": {
            "confidence": {
                "a_score": conf_a, "b_score": conf_b, "winner": conf_winner,
                "narrative": _narrate_confidence(a, b, conf_a, conf_b, sa, sb),
            },
            "properties": {
                "overlap": sorted(props_a & props_b),
                "unique_a": sorted(props_a - props_b),
                "unique_b": sorted(props_b - props_a),
                "protection_count_a": prot_a,
                "protection_count_b": prot_b,
                "winner": prot_winner,
                "toelichting": "Winnaar = meeste beschermings-eigenschappen (loss_cut, event_pause, honest_pnl, fee_aware_sell)",
                "narrative": _narrate_properties(a, b, props_a, props_b, prot_a, prot_b, sa, sb),
            },
            "bear_market_pnl": {
                "a_eur": bear_a, "b_eur": bear_b, "winner": bear_winner,
                "narrative": _narrate_bear(a, b, bear_a, bear_b, sa, sb),
            },
            "honesty": {
                "a_ratio": honesty_a, "b_ratio": honesty_b, "winner": honesty_winner,
                "toelichting": "Ratio dichter bij 1.0 = eerlijker. Negatief = verstopte verliezen.",
                "narrative": _narrate_honesty(a, b, honesty_a, honesty_b, sa, sb),
            },
            "spark_zekerheid": {
                "a": _pick(sa, "spark_alignment.zekerheid", ""),
                "b": _pick(sb, "spark_alignment.zekerheid", ""),
            },
            "maturity": {
                "a_has_conclusion": conc_a, "b_has_conclusion": conc_b, "winner": maturity_winner,
                "toelichting": "Winnaar = heeft afgeronde hypothese_lineage.conclusie (geen TODO)",
                "narrative": _narrate_maturity(a, b, conc_a, conc_b, sa, sb),
            },
        },
        "score": scores,
        "overall_winner": overall,
        "advies": (
            f"'{sa.get('display_name', a) if overall == a else sb.get('display_name', b)}' scoort beter op {scores.get(overall, 0)}/5 secties."
            if overall != "tie"
            else "Gelijkspel — beide strategieën scoren identiek. Kies op basis van filosofie."
        ),
        "spark_advies": _narrate_overall(a, b, overall, scores, sa, sb),
    }


# ============================================================
# v9_adaptive_lab_001 — Narrative helpers voor Spark's inhoudelijke analyse
# ============================================================

def _narrate_confidence(a, b, ca, cb, sa, sb):
    if ca == cb:
        return f"Beide strategieën scoren identiek ({ca}%). Confidence alleen zegt niet welke beter presteert live."
    winner_name = sa.get("display_name", a) if ca > cb else sb.get("display_name", b)
    diff = abs(ca - cb)
    interp = "significant" if diff >= 20 else "beperkt" if diff >= 10 else "marginaal"
    return f"**{winner_name}** wint met {ca if ca > cb else cb}% vs {min(ca, cb)}%. Verschil van {diff}p is {interp}."


def _narrate_properties(a, b, props_a, props_b, prot_a, prot_b, sa, sb):
    a_name = sa.get("display_name", a)
    b_name = sb.get("display_name", b)
    if prot_a == prot_b:
        return f"Beide hebben {prot_a} beschermings-eigenschappen. Focus op verschillen in signaal-eigenschappen."
    winner_name = a_name if prot_a > prot_b else b_name
    unique_pos = sorted(props_a - props_b) if prot_a > prot_b else sorted(props_b - props_a)
    return (
        f"**{winner_name}** heeft {max(prot_a, prot_b)} beschermings-eigenschappen vs {min(prot_a, prot_b)}. "
        f"Verschilmakers: {', '.join(unique_pos[:4]) if unique_pos else 'geen unieke'}."
    )


def _narrate_bear(a, b, bear_a, bear_b, sa, sb):
    if bear_a == 0 and bear_b == 0:
        return "Geen bear-market data voor beide — draai backtest v3 voor validatie."
    winner_name = sa.get("display_name", a) if bear_a > bear_b else sb.get("display_name", b)
    ratio = round(max(bear_a, bear_b) / max(abs(min(bear_a, bear_b)), 0.001), 1) if min(bear_a, bear_b) != 0 else "∞"
    return f"**{winner_name}** presteert €{max(bear_a, bear_b):.2f} in bear-markten ({ratio}× beter). Advies: gebruik deze bij dalende trend."


def _narrate_honesty(a, b, ha, hb, sa, sb):
    if ha is None and hb is None:
        return "Geen honesty-data voor beide (nog geen open posities in backtest)."
    if ha is None or hb is None:
        available = a if ha is not None else b
        val = ha if ha is not None else hb
        return f"Alleen {sa.get('display_name', a) if available == a else sb.get('display_name', b)} heeft honesty data ({val})."
    a_name = sa.get("display_name", a)
    b_name = sb.get("display_name", b)
    if ha < 0 or hb < 0:
        loser = a_name if ha < hb else b_name
        return f"⚠️ **{loser}** heeft negatieve honesty ratio — verstopte verliezen. Voeg loss_cut toe."
    dist_a = abs(ha - 1.0)
    dist_b = abs(hb - 1.0)
    winner_name = a_name if dist_a < dist_b else b_name
    return f"**{winner_name}** scoort eerlijker (ratio {ha if dist_a < dist_b else hb} — dichter bij 1.0 = geen verstopte verliezen)."


def _narrate_maturity(a, b, ca, cb, sa, sb):
    a_name = sa.get("display_name", a)
    b_name = sb.get("display_name", b)
    if ca and cb:
        return "Beide strategieën hebben afgeronde hypothese_lineage — mature."
    if not ca and not cb:
        return "Beide zijn drafts (geen conclusie). Draai backtest voor validatie."
    mature = a_name if ca else b_name
    draft = b_name if ca else a_name
    return f"**{mature}** is mature (backtest-conclusie aanwezig). **{draft}** is nog draft."


def _narrate_overall(a, b, overall, scores, sa, sb):
    if overall == "tie":
        return "Gelijkspel — kies op basis van filosofie: transparantie (honesty), snelheid (minder cooldowns) of exploratie (nieuwere hypotheses)."
    winner_name = sa.get("display_name", a) if overall == a else sb.get("display_name", b)
    loser_name = sb.get("display_name", b) if overall == a else sa.get("display_name", a)
    s = scores.get(overall, 0)
    if s >= 4:
        return f"🏆 **{winner_name}** wint duidelijk ({s}/5). Aanbevolen om deze actief te zetten via `/api/trade/engine/switch` of blueprint.active_strategy update."
    elif s == 3:
        return f"**{winner_name}** wint knap ({s}/5). {loser_name} blijft een goede backup — hou beide beschikbaar voor A/B."
    return f"**{winner_name}** wint nipt ({s}/5). Verschil is klein — draai nog een backtest-ronde voor zekerheid."


# ============================================================
# v8_engine_switch_001 — A/B decision-engine switch via blueprint config
# ============================================================

@router.get("/engine/status")
async def get_engine_status():
    """Toon actieve decision-engine + welke opties er zijn."""
    try:
        from modules.core.blueprint import load_blueprint_cached
        bp = load_blueprint_cached("trade", "spark_trader") or {}
        active = bp.get("active_decision_engine", "v1")
    except Exception as e:
        return {"success": False, "error": str(e)}

    engines_available = {
        "v1": {
            "module": "strategy_decision",
            "beschrijving": "Bollinger 2σ + gap-body 50% + 48u loss-cut + event-pauze (huidige productie)",
            "status": "productie",
            "backtest_bewezen": True,
        },
        "v2": {
            "module": "strategy_decision_v2",
            "beschrijving": "Pure trend-following stub — koopt bij 3 stijgende candles, verkoopt bij 2 dalende. Experimenteel.",
            "status": "draft",
            "backtest_bewezen": False,
        },
    }

    return {
        "success": True,
        "active_engine": active,
        "engines_available": engines_available,
        "current_module": engines_available.get(active, {}).get("module"),
    }


class EngineSwitchBody(BaseModel):
    engine: str


@router.post("/engine/switch")
async def switch_engine(body: EngineSwitchBody):
    """Wissel actieve decision-engine via blueprint. MonitorService leest bij volgende cycle."""
    if body.engine not in ("v1", "v2"):
        return {"success": False, "error": "engine moet 'v1' of 'v2' zijn"}

    bp_path = Path(__file__).parent / "blueprints" / "spark_trader.json"
    try:
        bp_data = json.loads(bp_path.read_text(encoding="utf-8"))
        bp_data["active_decision_engine"] = body.engine
        # Atomair write via tmp+rename (fix code-review item iter46)
        tmp = bp_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(bp_data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(bp_path)
        try:
            from modules.core.blueprint import clear_blueprint_cache
            clear_blueprint_cache()
        except Exception:
            pass
    except Exception as e:
        return {"success": False, "error": f"blueprint schrijven mislukt: {e}"}

    return {
        "success": True,
        "message": f"Engine geswitcht naar {body.engine}.",
        "active_engine": body.engine,
        "note": "MonitorService leest engine bij volgende cycle (max 5 min wachttijd).",
    }


# ============================================================
# v9_adaptive_lab_002 — Strategy Genome view (DNA-matrix per strategie)
# ============================================================

@router.get("/strategy/genome")
async def get_strategy_genome():
    """Toon alle strategieën als 'genoom' — property-matrix waaruit blijkt welke
    strategie welk gen heeft. Fundament voor Adaptive Strategy Lab v9.

    Return:
      - genes: alle bekende properties uit blueprint + property catalog
      - matrix: {strategy_id: {display_name, actief, confidence, gene_count, genes:{gen:bool}}}
      - inheritance: draft-strategieën met candidate_parents (via property-overlap)
      - stats: gene usage stats, categorieën
    """
    try:
        from modules.core.blueprint import load_blueprint_cached
        bp = load_blueprint_cached("trade", "spark_trader") or {}
        strategieën = bp.get("strategieën", {}) or {}
    except Exception as e:
        return {"success": False, "error": f"blueprint niet leesbaar: {e}"}

    # 1. Verzamel alle unieke genen
    all_genes = set()
    for sid, s in strategieën.items():
        for p in (s.get("properties", []) or []):
            all_genes.add(p)
    for gen in _PROPERTY_CATALOG.keys():
        all_genes.add(gen)
    all_genes = sorted(all_genes)

    # 2. Matrix bouwen
    matrix = {}
    for sid, s in strategieën.items():
        props = set(s.get("properties", []) or [])
        raw_status = s.get("status", "")
        status = raw_status if raw_status.startswith("draft") else "productie"
        matrix[sid] = {
            "display_name": s.get("display_name", sid),
            "actief": bool(s.get("actief")),
            "status": status,
            "confidence": int((s.get("confidence") or {}).get("score", 0)),
            "gene_count": len(props),
            "genes": {gen: (gen in props) for gen in all_genes},
        }

    # 3. Inheritance tracking
    inheritance = {}
    for sid, s in strategieën.items():
        vorige = s.get("vorige_naam")
        if vorige and vorige != sid:
            inheritance[sid] = {
                "vorige_naam": vorige,
                "is_migration": True,
                "beschrijving": "Hernoemd van legacy-code naar semantic name",
            }
        if s.get("status", "").startswith("draft"):
            new_props = set(s.get("properties", []) or [])
            parents = []
            for other_id, other_s in strategieën.items():
                if other_id == sid or other_s.get("status", "").startswith("draft"):
                    continue
                other_props = set(other_s.get("properties", []) or [])
                if other_props and len(new_props & other_props) >= max(2, len(other_props) // 2):
                    overlap = len(new_props & other_props)
                    parents.append({
                        "parent_id": other_id,
                        "parent_name": other_s.get("display_name", other_id),
                        "shared_genes": overlap,
                        "unique_new_genes": sorted(new_props - other_props),
                    })
            if parents:
                inheritance[sid] = {
                    "is_synthesis": True,
                    "candidate_parents": sorted(parents, key=lambda x: -x["shared_genes"])[:3],
                }

    # 4. Stats
    gene_usage = {g: sum(1 for m in matrix.values() if m["genes"].get(g)) for g in all_genes}
    most_common = sorted(gene_usage.items(), key=lambda x: -x[1])[:5]
    unused_genes = [g for g, cnt in gene_usage.items() if cnt == 0]

    genes_by_category = {}
    for gen in all_genes:
        cat = (_PROPERTY_CATALOG.get(gen) or {}).get("categorie", "onbekend")
        genes_by_category.setdefault(cat, []).append(gen)

    return {
        "success": True,
        "total_genes": len(all_genes),
        "total_strategies": len(strategieën),
        "genes_by_category": genes_by_category,
        "matrix": matrix,
        "inheritance": inheritance,
        "stats": {
            "most_common_genes": [{"gene": g, "count": c} for g, c in most_common],
            "unused_genes": unused_genes,
            "protection_gene_count": len([g for g in all_genes if (_PROPERTY_CATALOG.get(g) or {}).get("categorie") == "bescherming"]),
            "signal_gene_count": len([g for g in all_genes if (_PROPERTY_CATALOG.get(g) or {}).get("categorie") == "signaal"]),
        },
        "_note": "Fundament voor Adaptive Strategy Lab v9. Genes = properties. Inheritance detecteert synthesized-drafts en migraties. Gebruik matrix voor UI DNA-heatmap.",
    }

