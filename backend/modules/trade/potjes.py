"""
Potjes Systeem - 10 onafhankelijke trading pots.

Regels (Willem's design):
- Start: 10 potjes à €5.08
- Groei: winst blijft in potje, max €10/potje
- Als alle potjes €10: voeg nieuwe potjes toe (volume uitbreiding)
- Max 1 potje per monitor cycle mag kopen (staggered entry)
- Elk potje heeft eigen trailing stop + position state
"""
import threading
from functools import wraps
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timezone
from modules.core.storage import load_json, save_json
from modules.core.tracing import trace_call  # v7_function_tracing_001

# v7_potjes_race_fix_001 — Global RLock voor alle read-modify-write cycles.
# Bug voorheen: Spark's bot en Willem's bot konden gelijktijdig _load() → mutate
# → _save() doen. De 2e write overschreef de 1e mutation → pots-teller flipte
# 5↔6 na refresh. Wrap alle mutating functies met @with_lock.
_POTJES_LOCK = threading.RLock()


def with_lock(fn):
    """Decorator: run fn onder global potjes lock (atomair read-modify-write)."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        with _POTJES_LOCK:
            return fn(*args, **kwargs)
    return wrapper


POTJES_FILE = Path(__file__).parent.parent.parent / "data" / "financial" / "user_potjes.json"
ROAR_FILE = Path(__file__).parent.parent.parent / "data" / "roar" / "roar_balances.json"

START_AMOUNT = 10.0  # v6_potje_size_10_001 — starters direct €10 (was €5.08)
DEFAULT_POT_COUNT = 5  # v6_clean_slate_28mei — 5 base potjes van €10 = €50 baseline
SPARK_EXTRA_TRADE_SLOTS = 10  # v6_spark_15slots_001 (28 mei) — Spark krijgt 5 base + 10 trade-slots = 15 totaal
INITIAL_MAX = 50.0  # tier 1: max €50 (5x growth)
LOCKED_POT_INDEX = None  # v6_clean_slate_28mei — geen lock-anker; potjes = trade-posities
BITVAVO_TAKER_FEE = 0.0025
TOKEN_PRICE = 10.00  # v8_price_reset_001: bodemprijs €10 per ROAR token (was €5.08, dynamische prijs via shop.get_dynamic_price)

# v7_spark_fee_rate_001 — Spark's cut van netto trading-winst.
# 0.0 = uit. User's redenering: winst → Bitvavo balance → dynamische token-prijs
# stijgt automatisch → geen extra cut nodig. Constant hier voor makkelijke tuning.
SPARK_FEE_RATE = 0.0


def _mint_spark_bonus_tokens(netto_profit: float, source_pot: str, user_id: str) -> Optional[Dict]:
    """
    v4_token_potje_001 — Spark bonus tokens:
    Bij netto trading-winst > 0: accumuleer in spark_bonus.cumulative_profit_eur.
    Voor elke volle €5.08 (= 1 token-prijs) cumulatieve winst → mint 1 bonus-token
    naar Spark's eigen treasury (user-000 spark_bonus.balance).
    Bestemd voor server-kosten (uitcash later via wallet→bank koppeling).
    """
    if netto_profit <= 0:
        return None
    try:
        roar = load_json(ROAR_FILE, default={})
        bonus = roar.setdefault("spark_bonus", {
            "balance": 0, "cumulative_profit_eur": 0.0,
            "token_price_at_mint": TOKEN_PRICE, "history": []
        })
        prev_cum = float(bonus.get("cumulative_profit_eur", 0.0))
        new_cum = round(prev_cum + netto_profit, 6)
        # Hoeveel volle tokens kunnen we minten?
        prev_tokens = int(prev_cum // TOKEN_PRICE)
        new_tokens = int(new_cum // TOKEN_PRICE)
        minted = new_tokens - prev_tokens
        bonus["cumulative_profit_eur"] = new_cum
        if minted > 0:
            bonus["balance"] = int(bonus.get("balance", 0)) + minted
            bonus.setdefault("history", []).append({
                "ts": datetime.now(timezone.utc).isoformat(),
                "minted": minted,
                "from_pot": source_pot,
                "from_user": user_id,
                "netto_profit_eur": round(netto_profit, 4),
                "cum_profit_eur": new_cum,
                "new_balance": bonus["balance"],
            })
        save_json(ROAR_FILE, roar)
        return {"minted": minted, "balance": bonus["balance"], "cumulative_profit_eur": new_cum}
    except Exception as e:
        # Bonus-mint mag het sluiten van potje NOOIT blokkeren
        try:
            import logging
            logging.getLogger("spark_monitor").warning(f"Spark bonus mint failed: {e}")
        except Exception:
            pass
        return None

# Groei-regel: N potjes → max €N per potje → totaal €N²
# Bij uitbreiding: bestaande potjes groeien mee naar nieuwe maximum


def _max_size_for_count(pot_count: int) -> float:
    """
    Max size per potje op basis van totaal aantal potjes.
    - Tot 10 potjes: €10 per potje (starter tier)
    - 11 potjes: €11 per potje
    - 12 potjes: €12 per potje
    - N potjes: €N per potje
    """
    if pot_count <= DEFAULT_POT_COUNT:
        return INITIAL_MAX
    return float(pot_count)


def _expansion_cost(current_count: int) -> float:
    """
    Kosten om van N naar N+1 potjes te gaan:
    - Groei alle N potjes van €N naar €(N+1): +€1 per potje = N
    - Nieuwe potje #(N+1) = €(N+1)
    - Totaal: N + (N+1) = 2N+1
    """
    if current_count < DEFAULT_POT_COUNT:
        return 0  # Niet mogelijk
    if current_count == DEFAULT_POT_COUNT:
        # Van 10 × €10 naar 11 × €11: +€1 × 10 + €11 = €21
        return 2 * DEFAULT_POT_COUNT + 1  # = 21
    # Van N × €N naar (N+1) × €(N+1): +€1 × N + €(N+1) = 2N+1
    return 2 * current_count + 1


def _load(user_id: str) -> Dict:
    data = load_json(POTJES_FILE, default={"users": {}})
    user = data.get("users", {}).get(user_id, {})
    # v6_potje_per_token_001: alleen Spark (user-000) krijgt automatisch 10 base potjes.
    # Andere users starten met 0 potjes; expansie gebeurt via sync_potjes_to_tokens() bij token-buy.
    is_spark = (user_id == "user-000")
    if not user.get("potjes") and is_spark:
        user = _init_potjes(user_id)
        data.setdefault("users", {})[user_id] = user
        save_json(POTJES_FILE, data)
    elif not user:
        # Non-Spark user — leeg user-record aanmaken, geen base-potjes
        now = datetime.now(timezone.utc).isoformat()
        user = {"user_id": user_id, "market": "BCH-EUR", "potjes": [],
                "last_buy_cycle": None, "overflow_pool": 0.0, "created_at": now}
        data.setdefault("users", {})[user_id] = user
        save_json(POTJES_FILE, data)
    # v5_potjes_repair_001 — als user fewer than 10 potjes heeft (tier 1), reparate door tot 10 aan te vullen
    # v7_anchor_removed_001 — Geen auto-lock meer. Spark heeft 10 unlocked pots (1-op-1 met ROAR-tokens).
    # Auto-fill blijft uit (dead code weg): pot-count wordt beheerd via sync_potjes_to_tokens()
    # en rebalance_from_bitvavo(). Rest-EUR (Bitvavo saldo - som(pots.capital)) is zichtbaar
    # via GET /api/trade/delta (systeem-treasury view).
    # Backfill van staking-anchor lock verwijderd — Spark's eerste pot mag gewoon meehandelen.
    return data


def resize_potjes_to_default(user_id: str) -> Dict:
    """v6_potje_size_10_001 — admin-resize: zet alle potjes van een user op €10 capital.

    Alleen toepasbaar als de user geen open posities heeft (anders crashed P&L).
    Returns dict met before/after status.
    """
    data = _load(user_id)
    user = data["users"][user_id]
    potjes = user.get("potjes", [])
    open_count = sum(1 for p in potjes if p.get("position", {}).get("is_open"))
    if open_count > 0:
        return {
            "success": False,
            "error": f"User heeft {open_count} open posities — sluit eerst alle trades voordat resize.",
            "open_positions": open_count,
        }
    changed = 0
    for p in potjes:
        old = p.get("capital", 0)
        if abs(old - START_AMOUNT) < 0.01:
            continue  # al €10
        p["capital"] = START_AMOUNT
        p["max_size"] = INITIAL_MAX
        changed += 1
    _save(data)
    return {
        "success": True,
        "user_id": user_id,
        "total_potjes": len(potjes),
        "potjes_resized": changed,
        "new_capital_each": START_AMOUNT,
        "total_capital": len(potjes) * START_AMOUNT,
    }


def _save(data: Dict):
    save_json(POTJES_FILE, data)


# v7_pot_revalue_001 — synchroniseer capital van vrije pots met huidige token-prijs.
# Filosofie: elk potje representeert 1 ROAR-token qua waarde. Als Bitvavo groeit
# (door stortingen of trading-winst), stijgt de dynamische token-prijs → pots
# moeten meebewegen. Open pots blijven locked op buy-price want dat is wat er
# in Bitvavo staat als coin.
@with_lock
@trace_call(category="trade.pot.revalue")
def revalue_free_pots(user_id: str, new_capital: float) -> Dict:
    """Zet capital van alle VRIJE pots (position.is_open=False) op new_capital.

    Args:
        user_id: user waarvoor pots geherwaardeerd worden
        new_capital: nieuwe capital-waarde (typisch = current token-prijs)

    Returns:
        dict met before/after telling
    """
    data = _load(user_id)
    user = data["users"][user_id]
    potjes = user.get("potjes", [])
    changed = 0
    unchanged_open = 0
    for p in potjes:
        if p.get("position", {}).get("is_open"):
            unchanged_open += 1
            continue
        old = p.get("capital", 0)
        if abs(old - new_capital) < 0.001:
            continue  # al gelijk
        p["capital"] = round(float(new_capital), 4)
        changed += 1
    if changed:
        _save(data)
    return {
        "success": True,
        "user_id": user_id,
        "new_capital_each": round(float(new_capital), 4),
        "revalued_count": changed,
        "unchanged_open_count": unchanged_open,
        "total_potjes": len(potjes),
    }


@with_lock
def revalue_single_pot(user_id: str, pot_id: str, new_capital: float) -> Dict:
    """Handmatige revalue-knop per pot (admin-actie vanuit UI)."""
    data = _load(user_id)
    user = data["users"][user_id]
    for p in user.get("potjes", []):
        if p.get("id") != pot_id:
            continue
        if p.get("position", {}).get("is_open"):
            return {"success": False, "error": f"Pot {pot_id} heeft open positie — sluit eerst"}
        old = p.get("capital", 0)
        p["capital"] = round(float(new_capital), 4)
        _save(data)
        return {"success": True, "pot_id": pot_id, "old_capital": old, "new_capital": p["capital"]}
    return {"success": False, "error": f"Pot {pot_id} niet gevonden"}


def _markets_for_user(user_id: str) -> List[str]:
    """v6_potje_market_distribution_001 — lees user-specifieke markten uit bots_registry.
    Gebruikt door sync_potjes_to_tokens en redistribute_potjes_across_markets.
    Fallback: ["BCH-EUR"] (legacy default).
    """
    try:
        reg = load_json(POTJES_FILE.parent / "bots_registry_state.json", default={"bots": []})
        bots = reg.get("bots") or []
        for b in bots:
            if b.get("user_id") == user_id:
                mks = b.get("markets") or []
                if mks:
                    return [m for m in mks if isinstance(m, str) and m.strip()]
    except Exception:
        pass
    return ["BCH-EUR"]


def redistribute_potjes_across_markets(user_id: str, markets: Optional[List[str]] = None) -> Dict:
    """v6_potje_market_distribution_001 — herverdeel bestaande potjes round-robin
    over een lijst markten. Slaat potjes met open positions over (die staan al
    vast op een coin). Veilig her-uit te voeren.
    """
    if user_id == "user-000":
        return {"success": False, "error": "Spark heeft custom anchor-distributie; gebruik update_markets() ipv redistribute."}

    target_markets = markets or _markets_for_user(user_id)
    if not target_markets:
        return {"success": False, "error": "Geen markten gevonden om over te verdelen"}

    data = _load(user_id)
    user = data["users"][user_id]
    potjes = user.get("potjes", [])
    if not potjes:
        return {"success": True, "changed": 0, "potjes": []}

    changed = 0
    closed_potjes = [p for p in potjes if not p.get("position", {}).get("is_open")]
    open_potjes = [p for p in potjes if p.get("position", {}).get("is_open")]
    # Open potjes blijven op hun huidige market (positie vastzit).
    # Closed potjes: round-robin verdelen.
    for i, p in enumerate(closed_potjes):
        new_market = target_markets[i % len(target_markets)]
        if p.get("market") != new_market:
            p["market"] = new_market
            p["last_action"] = f"redistribute → {new_market}"
            changed += 1

    user["potjes"] = closed_potjes + open_potjes
    _save(data)
    from collections import Counter
    by_market = dict(Counter(p.get("market") for p in user["potjes"]))
    return {
        "success": True, "changed": changed, "total_potjes": len(potjes),
        "open_positions": len(open_potjes), "markets_used": target_markets,
        "distribution": by_market,
    }


def sync_potjes_to_tokens(user_id: str, n_tokens: int, market: str = "BCH-EUR") -> Dict:
    """v6_potje_per_token_001 — 1 token = 1 potje.

    Regel (Willem 2026-05-28): alleen Spark (user-000) heeft 10 base potjes;
    andere users krijgen 1 potje per ROAR-token dat ze bezitten.

    Deze functie zorgt dat een user EXACT n_tokens potjes heeft. Voegt potjes toe
    bij groei. Verwijdert NIET (open posities of sell_back behandelen we apart).
    Spark (user-000) wordt overgeslagen.
    """
    if user_id == "user-000":
        return {"success": True, "user_id": user_id, "skipped": True, "reason": "Spark heeft base-potjes (10)"}

    data = _load(user_id)
    user = data["users"][user_id]
    potjes = user.get("potjes", [])
    current = len(potjes)
    target = max(0, int(n_tokens))
    if current >= target:
        return {"success": True, "user_id": user_id, "current": current, "target": target, "added": 0,
                "message": "Geen potje-uitbreiding nodig."}

    # v7_anchor_removed_001 — Alle nieuwe potjes zijn unlocked. Geen staking-anker meer.
    # Round-robin market-toewijzing blijft: verdeel over user's bots_registry.markets lijst.
    user_markets = _markets_for_user(user_id) or [market]
    now = datetime.now(timezone.utc).isoformat()
    next_idx = max((p.get("index", i) for i, p in enumerate(potjes)), default=-1) + 1
    added = 0
    while len(potjes) < target:
        # Round-robin: kies market op basis van totaal aantal potjes
        chosen_market = user_markets[len(potjes) % len(user_markets)] if user_markets else market
        potjes.append({
            "id": f"pot-{next_idx+1:03d}",
            "index": next_idx,
            "capital": START_AMOUNT,
            "max_size": INITIAL_MAX,
            "pot_locked": False,
            "lock_reason": None,
            "position": {"is_open": False, "entry_price": None, "highest_price": None,
                         "trailing_active": False, "entry_time": None},
            "market": chosen_market,
            "stats": {"trades": 0, "wins": 0, "losses": 0, "total_pnl": 0.0},
            "created_at": now,
            "last_action": None,
            "source": "token_buy_expansion",
        })
        next_idx += 1
        added += 1
    user["potjes"] = potjes
    _save(data)
    return {
        "success": True,
        "user_id": user_id,
        "current": current,
        "target": target,
        "added": added,
        "message": f"{added} potjes toegevoegd — {len(potjes)} totaal voor user (= {target} tokens).",
    }


def assign_pot_market(user_id: str, pot_id: str, market: str) -> Dict:
    """v6_one_bot_per_pot_001 (28 mei) — Stap 1 van multi-bot:
    Sla per-pot market-toewijzing op (BCH-EUR / BTC-EUR / etc.) zodat elke pot
    onafhankelijk op zijn eigen coin kan handelen. Echte multi-thread bot-instance
    per pot is volgende fase — nu wordt market gerespecteerd door _trade_signals.
    """
    data = _load(user_id)
    user = data["users"][user_id]
    for p in user.get("potjes", []):
        if p.get("id") == pot_id:
            p["assigned_market"] = market
            p["assigned_at"] = datetime.now(timezone.utc).isoformat()
            _save(data)
            return {"success": True, "pot_id": pot_id, "market": market}
    return {"success": False, "error": f"Pot {pot_id} niet gevonden"}


# v7_anchor_removed_001 — ensure_anchors_for_markets() volledig verwijderd.
# Reden: locked anchor-pots deden functioneel niks (werden overal geskipt in open/close),
# maar bloatten de pot-count. Nieuwe regel: Spark heeft altijd exact DEFAULT_POT_COUNT (10)
# unlocked pots die 1-op-1 mappen aan zijn ROAR-tokens. Coins worden verdeeld via
# round-robin market-toewijzing in sync_potjes_to_tokens / rebalance_from_bitvavo.
# Rest-EUR op Bitvavo is zichtbaar via GET /api/trade/delta (systeem-treasury view).
def ensure_anchors_for_markets(user_id: str, markets: List[str]) -> Dict:
    """DEPRECATED — no-op stub gehouden voor backwards-compat met bestaande callers.
    Returned altijd success zonder pots te muteren.
    """
    return {"success": True, "created": [], "skipped": list(markets or []),
            "deprecated": True, "reason": "anchors verwijderd in v7_anchor_removed_001"}


# v6_spark_2pots_per_coin_001 — Spark krijgt 2 trade-potjes per coin (naast anchor)
def ensure_spark_trade_pots(markets: List[str], pots_per_coin: int = 2) -> Dict:
    """Zorg dat Spark `pots_per_coin` vrije trade-potjes per coin heeft (default 2).
    Anchors zijn los hiervan (zie ensure_anchors_for_markets).

    Idempotent: telt bestaande vrije trade-potjes per coin, mint alleen tekorten.
    Skipt open posities (die zijn geclaimd door een actieve trade).
    """
    user_id = "user-000"
    if not markets:
        return {"success": True, "minted": [], "skipped": []}

    clean_markets = sorted({(m or "").strip().upper() for m in markets if m})
    clean_markets = [m for m in clean_markets if m and m != "EUR"]
    if not clean_markets:
        return {"success": True, "minted": [], "skipped": []}

    data = _load(user_id)
    user = data["users"][user_id]
    potjes = user.setdefault("potjes", [])

    # Tel vrije trade-potjes per market (skip locked anchors + open positions)
    from collections import Counter
    free_trade_per_market = Counter()
    for p in potjes:
        if p.get("pot_locked"):
            continue
        if p.get("position", {}).get("is_open"):
            continue
        m = (p.get("market") or "").upper()
        if m and m != "EUR":
            free_trade_per_market[m] += 1

    now = datetime.now(timezone.utc).isoformat()
    next_idx = max((p.get("index", i) for i, p in enumerate(potjes)), default=-1) + 1
    minted = []
    for market in clean_markets:
        cur = free_trade_per_market.get(market, 0)
        needed = pots_per_coin - cur
        for _ in range(max(0, needed)):
            new_pot = {
                "id": f"pot-{next_idx + 1:03d}",
                "index": next_idx,
                "capital": START_AMOUNT,
                "max_size": INITIAL_MAX,
                "pot_locked": False,
                "lock_reason": None,
                "position": {"is_open": False, "entry_price": None, "highest_price": None,
                             "trailing_active": False, "entry_time": None},
                "market": market,
                "stats": {"trades": 0, "wins": 0, "losses": 0, "total_pnl": 0.0},
                "created_at": now,
                "last_action": None,
                "source": "spark_2pots_per_coin",
            }
            potjes.append(new_pot)
            minted.append({"id": new_pot["id"], "market": market})
            next_idx += 1

    if minted:
        user["potjes"] = potjes
        _save(data)

    return {"success": True, "minted": minted, "target_per_coin": pots_per_coin,
            "total_potjes": len(potjes)}


# v6_dynamic_pot_split_001 — Dynamische €10-schijven herbalancering vanaf Bitvavo
def rebalance_from_bitvavo(coins: Optional[List[str]] = None,
                            pot_size: float = 10.0,
                            trader_user_id: str = "user-001",
                            anchor_user_id: str = "user-000",
                            include_eur_liquide: bool = True,
                            target_pot_count: Optional[int] = None,
                            default_market: str = "BCH-EUR") -> Dict:
    """Reset potje-structuur op basis van actuele Bitvavo waarde.

    Twee modi:
      A. Vast pot_size (legacy) — per coin: n = floor(value/pot_size) pots.
         Coins < pot_size geven 0 pots. EUR-saldo genegeerd.

      B. Token-count leidend (aanbevolen, v7):
         set `target_pot_count=N` → exact N pots verdeeld over Bitvavo saldo.
         - pot_size dynamisch = (som(coin_values) + eur_avail) / N
         - Coins met genoeg waarde krijgen hun eigen pots
         - Overige pots worden EUR-only (klaar voor trade-cycle) op default_market
         - Werkt ook als je alleen EUR liquide hebt en 0 coins

    Args:
      include_eur_liquide: als True (v7 default), EUR-saldo telt mee in totale waarde.
      target_pot_count: v7 mode. Als None → legacy per-coin gedrag.
      default_market: markt voor "EUR-only" pots (die krijgen dus geen coin, alleen budget).

    Open posities blijven ongemoeid.
    """
    from modules.trade.monitor import fetch_bitvavo_balance

    # 1) Haal balances (coin + EUR) op via Spark's keys
    bv = fetch_bitvavo_balance(anchor_user_id)
    if not bv.get("success"):
        return {"success": False, "error": f"Bitvavo balance fetch faalde: {bv.get('error')}"}

    target_coins = coins or ["BCH", "BTC", "ETH", "SOL", "ADA", "ATOM"]
    coin_values: Dict[str, float] = {}
    for sym in target_coins:
        m = next((b for b in bv["balances"] if b["symbol"] == sym), None)
        coin_values[sym] = round(m["value_eur"], 2) if m else 0.0

    eur_liquide = 0.0
    if include_eur_liquide:
        eur_entry = next((b for b in bv["balances"] if b["symbol"] == "EUR"), None)
        eur_liquide = float(eur_entry.get("available", 0) if eur_entry else 0)

    # 2) Bouw nieuwe potjes-state
    data = _load(trader_user_id)
    if anchor_user_id != trader_user_id:
        anchor_data = _load(anchor_user_id)
    else:
        anchor_data = data

    # Behoud open-positie potjes van trader (die zijn vastgezet in actieve trade)
    existing_trader = data["users"][trader_user_id].get("potjes", [])
    open_trader_pots = [p for p in existing_trader if p.get("position", {}).get("is_open")]
    open_value_per_coin: Dict[str, float] = {}
    for p in open_trader_pots:
        m = p.get("market") or ""
        sym = m.split("-")[0]
        open_value_per_coin[sym] = open_value_per_coin.get(sym, 0) + (p.get("capital") or 0)

    # Behoud open posities van anchor user
    existing_anchor = anchor_data["users"][anchor_user_id].get("potjes", [])
    open_anchor_pots = [p for p in existing_anchor if p.get("position", {}).get("is_open")]
    for p in open_anchor_pots:
        sym = (p.get("market") or "").split("-")[0]
        open_value_per_coin[sym] = open_value_per_coin.get(sym, 0) + (p.get("capital") or 0)

    now = datetime.now(timezone.utc).isoformat()
    trader_pots: List[Dict] = list(open_trader_pots)  # behoud
    anchor_pots: List[Dict] = list(open_anchor_pots)  # behoud
    t_idx = max((p.get("index", -1) for p in trader_pots), default=-1) + 1
    summary = []

    # =========================================================================
    # MODUS B — Token-count leidend (v7_rebalance_smart_001)
    #
    # Correcte semantiek: pot_size = aankoopprijs per token (default anchor €5,08).
    # NIET total_bitvavo/N — dat zou het hele Bitvavo saldo aan één user toewijzen
    # terwijl dat de systeem-treasury is (visible in /api/trade/delta).
    # =========================================================================
    if target_pot_count is not None and target_pot_count > 0:
        n_existing_open = len(open_trader_pots)
        n_to_create = max(0, target_pot_count - n_existing_open)

        # pot_size default = anchor prijs (€5,08). User kan overschrijven via body.pot_size.
        # Dit is de investering per pot, NIET marktwaarde.
        dyn_pot_size = float(pot_size) if pot_size and pot_size > 0 else 5.08
        total_needed = n_to_create * dyn_pot_size

        # Beschikbaar = coin-values (excl open) + EUR liquide (indien meetellen)
        free_coin_value = sum(
            max(0, coin_values.get(sym, 0) - open_value_per_coin.get(sym, 0))
            for sym in target_coins
        )
        total_available = round(free_coin_value + eur_liquide, 2)

        if total_needed > total_available + 0.01:
            return {
                "success": False,
                "error": (
                    f"Onvoldoende saldo: {n_to_create} pots × €{dyn_pot_size:.2f} = €{total_needed:.2f} nodig, "
                    f"maar Bitvavo heeft slechts €{total_available:.2f} (waarvan coins €{free_coin_value:.2f}, "
                    f"EUR €{eur_liquide:.2f}). Verlaag pot_size of stort meer op Bitvavo."
                ),
                "total_needed": total_needed,
                "total_available": total_available,
            }

        # 1. Coin-gebonden pots: hoeveel per coin krijgen we?
        pots_per_coin: Dict[str, int] = {}
        remaining_slots = n_to_create
        for sym in target_coins:
            free_c = max(0, coin_values.get(sym, 0) - open_value_per_coin.get(sym, 0))
            n = min(int(free_c // dyn_pot_size), remaining_slots)
            if n > 0:
                pots_per_coin[sym] = n
                remaining_slots -= n

        # 2. Maak coin-pots aan
        for sym, n in pots_per_coin.items():
            market = f"{sym}-EUR"
            for _ in range(n):
                trader_pots.append({
                    "id": f"pot-{t_idx+1:03d}", "index": t_idx,
                    "capital": dyn_pot_size, "max_size": max(dyn_pot_size * 5, 50.0),
                    "pot_locked": False, "lock_reason": None,
                    "position": {"is_open": False, "entry_price": None, "highest_price": None,
                                 "trailing_active": False, "entry_time": None},
                    "market": market,
                    "stats": {"trades": 0, "wins": 0, "losses": 0, "total_pnl": 0.0},
                    "created_at": now, "last_action": None,
                    "source": "rebalance_smart_coin",
                })
                t_idx += 1
            summary.append({"coin": sym, "bitvavo_value": coin_values.get(sym, 0),
                            "trade_pots_created": n, "pot_size": dyn_pot_size})

        # 3. Resterende slots → EUR-only pots op default_market
        for _ in range(remaining_slots):
            trader_pots.append({
                "id": f"pot-{t_idx+1:03d}", "index": t_idx,
                "capital": dyn_pot_size, "max_size": max(dyn_pot_size * 5, 50.0),
                "pot_locked": False, "lock_reason": None,
                "position": {"is_open": False, "entry_price": None, "highest_price": None,
                             "trailing_active": False, "entry_time": None},
                "market": default_market,
                "stats": {"trades": 0, "wins": 0, "losses": 0, "total_pnl": 0.0},
                "created_at": now, "last_action": None,
                "source": "rebalance_smart_eur",
            })
            t_idx += 1
        if remaining_slots > 0:
            summary.append({"coin": "EUR", "eur_liquide": eur_liquide,
                            "trade_pots_created": remaining_slots, "pot_size": dyn_pot_size,
                            "market": default_market})

        # 4. Save trader state
        data["users"][trader_user_id]["potjes"] = trader_pots
        _save(data)

        # 5. Rest op Bitvavo = systeem-treasury (zichtbaar via /api/trade/delta)
        treasury_overschot = round(total_available - total_needed, 2)

        return {"success": True, "mode": "smart_token_count",
                "target_pot_count": target_pot_count,
                "existing_open_kept": n_existing_open,
                "new_pots_created": n_to_create,
                "pot_size": dyn_pot_size,
                "total_needed": total_needed,
                "total_available_on_bitvavo": total_available,
                "eur_liquide": eur_liquide,
                "free_coin_value": free_coin_value,
                "treasury_overschot_eur": treasury_overschot,
                "treasury_note": (
                    f"€{treasury_overschot:.2f} blijft op Bitvavo bovenop pot-capital "
                    f"(zichtbaar in /api/trade/delta als 'zweeft'). Dit is systeem-treasury "
                    "of onrealiseerde token-winst."
                ),
                "coins_summary": summary,
                "trader_user_id": trader_user_id}

    # =========================================================================
    # MODUS A — Legacy vast pot_size (behouden voor backwards-compat)
    # =========================================================================
    for sym in target_coins:
        market = f"{sym}-EUR"
        bv_value = coin_values.get(sym, 0)
        already_open = open_value_per_coin.get(sym, 0)
        free_value = max(0, round(bv_value - already_open, 2))
        n_trade = int(free_value // pot_size)
        remainder = round(free_value - n_trade * pot_size, 2)

        for _ in range(n_trade):
            trader_pots.append({
                "id": f"pot-{t_idx+1:03d}", "index": t_idx,
                "capital": pot_size, "max_size": 50.0,
                "pot_locked": False, "lock_reason": None,
                "position": {"is_open": False, "entry_price": None, "highest_price": None,
                             "trailing_active": False, "entry_time": None},
                "market": market,
                "stats": {"trades": 0, "wins": 0, "losses": 0, "total_pnl": 0.0},
                "created_at": now, "last_action": None,
                "source": "rebalance_from_bitvavo",
            })
            t_idx += 1

        # v7_anchor_removed_001 — Anchor met restje wordt niet meer als locked pot aangemaakt.
        # De restant-EUR (< pot_size) blijft op Bitvavo staan en is zichtbaar via
        # GET /api/trade/delta (systeem-treasury view). Geen dode locked pot meer nodig.

        summary.append({
            "coin": sym, "bitvavo_value": bv_value, "already_open": already_open,
            "free_value": free_value, "trade_pots_created": n_trade,
            "remainder_on_bitvavo": remainder,
        })

    # 3) Save
    data["users"][trader_user_id]["potjes"] = trader_pots
    data["users"][trader_user_id]["overflow_pool"] = 0.0
    data["users"][trader_user_id]["last_buy_cycle"] = None
    _save(data)

    if anchor_user_id != trader_user_id:
        anchor_data["users"][anchor_user_id]["potjes"] = anchor_pots
        anchor_data["users"][anchor_user_id]["overflow_pool"] = 0.0
        _save(anchor_data)

    total_trade_eur = sum(p["capital"] for p in trader_pots if not p.get("pot_locked"))
    total_anchor_eur = sum(p["capital"] for p in anchor_pots if p.get("pot_locked"))
    return {
        "success": True,
        "trader_user_id": trader_user_id, "anchor_user_id": anchor_user_id,
        "pot_size_eur": pot_size,
        "bitvavo_total_eur": sum(coin_values.values()),
        "trader_pot_count": len([p for p in trader_pots if not p.get("pot_locked")]),
        "anchor_pot_count": len([p for p in anchor_pots if p.get("pot_locked")]),
        "trader_total_eur": round(total_trade_eur, 2),
        "anchor_total_eur": round(total_anchor_eur, 2),
        "open_positions_preserved": len(open_trader_pots) + len(open_anchor_pots),
        "summary": summary,
    }



def trim_potjes_to_tokens(user_id: str, n_tokens: int) -> Dict:
    """v6_potje_per_token_001 — verminder potjes wanneer user tokens kwijtraakt (sell_back/gift_sent).

    Veiligheid: verwijdert ALLEEN ongebruikte potjes (geen open positie, en niet de lock-anker).
    Returns dict met n_removed.
    """
    if user_id == "user-000":
        return {"success": True, "skipped": True, "reason": "Spark base-potjes"}
    data = _load(user_id)
    user = data["users"][user_id]
    potjes = user.get("potjes", [])
    target = max(0, int(n_tokens))
    if len(potjes) <= target:
        return {"success": True, "removed": 0, "current": len(potjes), "target": target}
    # Sorteer: hoog → laag (verwijder hoogste indexes eerst, behoud lock-anker)
    # Skip: pot_locked OR open position
    removed = 0
    sorted_pots = sorted(potjes, key=lambda p: -(p.get("index") or 0))
    keep_pots = []
    for p in sorted_pots:
        is_open = p.get("position", {}).get("is_open")
        is_locked = p.get("pot_locked")
        if len(potjes) - removed > target and not is_open and not is_locked:
            removed += 1
            continue
        keep_pots.append(p)
    # Behoud originele sorteer-volgorde (op index)
    keep_pots.sort(key=lambda p: p.get("index") or 0)
    user["potjes"] = keep_pots
    _save(data)
    return {"success": True, "removed": removed, "current": len(keep_pots), "target": target}


def _init_potjes(user_id: str) -> Dict:
    """Maak initiële 10 unlocked potjes à €10 voor user (Spark).

    v7_anchor_removed_001: geen locked staking-anker meer. Alle pots handelen mee.
    Elke pot = 1 ROAR-token (1-op-1 mapping).
    """
    now = datetime.now(timezone.utc).isoformat()
    potjes = []
    for i in range(DEFAULT_POT_COUNT):
        potjes.append({
            "id": f"pot-{i+1:03d}",
            "index": i,
            "capital": START_AMOUNT,
            "max_size": INITIAL_MAX,
            "pot_locked": False,
            "lock_reason": None,
            "position": {
                "is_open": False,
                "entry_price": None,
                "highest_price": None,
                "trailing_active": False,
                "entry_time": None,
            },
            "market": "BCH-EUR",
            "stats": {
                "trades": 0,
                "wins": 0,
                "losses": 0,
                "total_pnl": 0.0,
            },
            "created_at": now,
            "last_action": None,
        })
    return {
        "user_id": user_id,
        "market": "BCH-EUR",
        "potjes": potjes,
        "last_buy_cycle": None,
        "overflow_pool": 0.0,
        "created_at": now,
    }


def get_potjes(user_id: str) -> Dict:
    data = _load(user_id)
    user = data["users"][user_id]
    # v6_pot_live_value_per_user_001 — Live Bitvavo lookup zit nu in get_summary()
    # (de stats-endpoint); get_potjes() levert alleen JSON capital + mark-to-market
    # voor open posities. Voorheen werd hier een onused fetch_bitvavo_balance gedaan.

    # v5_potje_mark2market_001 — haal live tickers op voor open posities (mock + live)
    # Bug B4: potje-waarde stijgt niet mee met tokenwaarde. Fix: bereken
    # unrealized P&L per open potje op basis van huidige market-price.
    open_markets = sorted({p.get("market") for p in user["potjes"]
                           if p.get("position", {}).get("is_open") and p.get("market")})
    price_map: Dict[str, float] = {}
    if open_markets:
        try:
            from modules.trade.monitor import fetch_tickers
            symbols = [m.split("-")[0] for m in open_markets]
            tickers = fetch_tickers(symbols)
            for t in tickers:
                sym = t.get("symbol") or t.get("market", "").split("-")[0]
                last = t.get("last") or t.get("price")
                if sym and last is not None:
                    try:
                        price_map[f"{sym}-EUR"] = float(last)
                    except (TypeError, ValueError):
                        pass
        except Exception:
            pass

    # v6_pot_live_value_fix_001 (sessie 14) — voorheen verdeelde live_value de hele
    # Bitvavo balance proportioneel over ALLE potjes via growth-factor. Dat gaf
    # rare bedragen als €43.25 op een €10 anker omdat Bitvavo €222 had (groei-
    # factor 4.32×). Nieuw gedrag:
    #   - LOCKED + VRIJE potjes → live_value = capital (geen growth)
    #   - OPEN posities → mark-to-market via current_price (bestaand, hieronder)
    # Resultaat: anchor blijft €10, trade-potjes met open positie pulseren mee
    # met de actuele coin-prijs.
    for p in user["potjes"]:
        p["live_value"] = p["capital"]

    # v5_potje_mark2market_001 — voor OPEN posities: mark-to-market overschrijft live_value
    # Formule: capital * (1 + (current_price - entry_price)/entry_price) - fees
    for p in user["potjes"]:
        pos = p.get("position") or {}
        if not pos.get("is_open"):
            continue
        entry = pos.get("entry_price")
        market = p.get("market")
        current = price_map.get(market)
        if not entry or not current or entry <= 0:
            continue
        profit_pct = (current - entry) / entry
        bruto = p["capital"] * profit_pct
        fees = p["capital"] * BITVAVO_TAKER_FEE * 2  # buy + sell roundtrip
        netto = bruto - fees
        p["live_value"] = round(p["capital"] + netto, 4)
        p["unrealized_pnl"] = round(netto, 4)
        p["unrealized_pnl_pct"] = round(profit_pct * 100, 3)
        p["current_price"] = current
    return user


def get_available_pot(user_id: str, current_cycle: int, skip_cycle_check: bool = False,
                       prefer_market: Optional[str] = None) -> Optional[Dict]:
    """
    Vind een potje dat mag kopen:
    - is_open = False (niet in positie)
    - last_buy_cycle != current_cycle (nog geen potje in deze cycle gekocht)
    Returns het eerste vrije potje gesorteerd op nummer (1..10), of None.
    v4_potje_sync_001: sorteer op nummer/index zodat UI en backend dezelfde keuze maken.
    v4_potje_quickbuy_002: skip_cycle_check voor user-initiated Quick Buy (user mag meerdere
    potjes openen in dezelfde monitor-cycle).
    v6_pot1_staking_lock_001: skip potjes met `pot_locked=True` (staking-anker).
    v6_pot_market_match_001: als `prefer_market` opgegeven, geef voorrang aan een
    vrij potje dat al voor deze markt is gemarkeerd (voorkomt dat een SOL-potje
    plotseling BCH gaat kopen door round-robin). Fallback: eerste vrije potje.
    """
    user = get_potjes(user_id)
    if not skip_cycle_check and user.get("last_buy_cycle") == current_cycle:
        return None  # Al een potje gekocht in deze cycle (monitor-mode bescherming)
    sorted_potjes = sorted(user["potjes"], key=lambda p: (p.get("nummer") or (p.get("index", 99) + 1)))
    free_potjes = [p for p in sorted_potjes
                   if not p.get("pot_locked") and not p["position"]["is_open"]]
    if prefer_market:
        market_match = [p for p in free_potjes if p.get("market") == prefer_market]
        if market_match:
            return market_match[0]
    return free_potjes[0] if free_potjes else None


def open_pot(user_id: str, pot_id: str, entry_price: float, current_cycle: int,
             trade_id: Optional[str] = None, amount_eur: Optional[float] = None,
             market: Optional[str] = None) -> Dict:
    """Open positie in een potje + log de BUY-trade op het potje zelf.
    v4_potje_sync_001: trade_count + trade_log bijwerken zodat UI tellertje klopt.
    v4_potje_market_001: bewaar welke coin gekocht is per potje (was hardcoded BCH-EUR).
    v6_lock_enforce_002: hard guard tegen openen van een locked potje (defense in depth).
    """
    data = _load(user_id)
    user = data["users"][user_id]
    now = datetime.now(timezone.utc).isoformat()
    for p in user["potjes"]:
        if p["id"] == pot_id:
            # v6_lock_enforce_002 — locked potjes mogen NOOIT geopend worden
            if p.get("pot_locked"):
                print(f"[potjes] BLOCK: open_pot geweigerd voor {pot_id} ({p.get('market')}) — pot_locked=True (reason={p.get('lock_reason','?')})")
                return {}
            p["position"] = {
                "is_open": True,
                "entry_price": entry_price,
                "highest_price": entry_price,
                "trailing_active": False,
                "entry_time": now,
                # v6_potje_amount_in_position_fix_001 — UI moet kunnen tonen hoeveel
                # er in dit potje vastzit. Was alleen in trade_log gezet → "potje
                # wordt niet gevuld"-effect.
                "amount_eur": amount_eur if amount_eur is not None else p.get("capital"),
            }
            # v4_potje_market_001: leg vast WELKE coin in dit potje zit (BTC-EUR / BCH-EUR / ETH-EUR ...)
            if market:
                p["market"] = market
            p["last_action"] = f"BUY @ €{entry_price:.2f}"
            p.setdefault("stats", {"trades": 0, "wins": 0, "losses": 0, "total_pnl": 0.0})
            p["stats"]["trades"] = p["stats"].get("trades", 0) + 1
            p.setdefault("trade_log", []).append({
                "ts": now, "side": "BUY", "price": entry_price,
                "amount_eur": amount_eur, "trade_id": trade_id,
                "market": market or p.get("market"),
            })
            user["last_buy_cycle"] = current_cycle
            _save(data)
            # v4_boekhouder_001: announce trade
            try:
                from modules.boekhouder.service import announce_buy
                announce_buy(user_id, pot_id, market or p.get("market") or "?-EUR",
                             entry_price, amount_eur or p.get("capital", 0))
            except Exception:
                pass
            # v6_accounting_hooks_001 — Trade BUY → expense spark_core (Materiaal)
            try:
                from modules.accounting.hooks import on_bitvavo_coin_buy
                from pathlib import Path as _P
                USERS = _P(__file__).parent.parent.parent / "data" / "system" / "users.json"
                udata = load_json(USERS, default={"users": []})
                ulist = udata.get("users", []) if isinstance(udata, dict) else udata
                naam = next((u.get("naam") for u in ulist if u.get("id") == user_id), user_id)
                on_bitvavo_coin_buy(
                    user_id=user_id, user_naam=naam,
                    market=market or p.get("market") or "?-EUR",
                    amount_eur=amount_eur or p.get("capital", 0),
                    trade_id=trade_id or f"{pot_id}_{now}",
                )
            except Exception as ex:
                print(f"[open_pot] accounting-hook failed (non-blocking): {ex}")
            return p
    return {}


def update_pot_tracking(user_id: str, pot_id: str, current_price: float) -> Dict:
    """Update highest_price en trailing_active voor open positie.

    v6_zerodiv_guard_001 — guard tegen entry_price=0/None (b.v. corrupted anchor
    pots zonder echte BUY-fill). Voorheen crashte de monitor loop met
    ZeroDivisionError → 372 errors in 1 dag log spam.
    """
    data = _load(user_id)
    user = data["users"][user_id]
    for p in user["potjes"]:
        if p["id"] == pot_id and p["position"]["is_open"]:
            pos = p["position"]
            entry = pos.get("entry_price") or 0
            if current_price > (pos.get("highest_price") or 0):
                pos["highest_price"] = current_price
            if entry > 0:
                profit_pct = (current_price - entry) / entry
                if profit_pct >= 0.01:
                    pos["trailing_active"] = True
            # entry_price == 0 → position is open maar zonder fill-prijs; trailing
            # activatie wacht tot een force-close of admin-reconcile dit oplost.
            _save(data)
            return p
    return {}


@with_lock
@trace_call(category="trade.pot.close")
def close_pot(user_id: str, pot_id: str, exit_price: float) -> Dict:
    """Sluit positie, voeg winst toe aan capital (tot max), update stats.
    v6_lock_enforce_002: hard guard — locked potjes mogen niet gesloten worden.
    Dit beschermt staking-ankers als 'is_open' om historische redenen toch True is.
    """
    data = _load(user_id)
    user = data["users"][user_id]
    for p in user["potjes"]:
        if p["id"] == pot_id and p["position"]["is_open"]:
            # v6_lock_enforce_002 — staking-anker blijft staan
            if p.get("pot_locked"):
                print(f"[potjes] BLOCK: close_pot geweigerd voor {pot_id} ({p.get('market')}) — pot_locked=True (reason={p.get('lock_reason','?')})")
                return {}
            entry = p["position"]["entry_price"]
            capital = p["capital"]
            # Bruto P&L
            profit_pct = (exit_price - entry) / entry
            bruto = capital * profit_pct
            fees = capital * BITVAVO_TAKER_FEE * 2  # buy + sell fee
            netto = bruto - fees
            # Update capital (cap at MAX_POT_SIZE, overflow gaat in overflow bucket)
            new_capital = capital + netto
            overflow = 0.0
            pot_max = p.get("max_size", INITIAL_MAX)
            if new_capital > pot_max:
                overflow = new_capital - pot_max
                new_capital = pot_max
            p["capital"] = round(new_capital, 4)
            p["stats"]["trades"] += 1
            if netto > 0:
                p["stats"]["wins"] += 1
            else:
                p["stats"]["losses"] += 1
            p["stats"]["total_pnl"] = round(p["stats"]["total_pnl"] + netto, 4)
            p["position"] = {
                "is_open": False,
                "entry_price": None,
                "highest_price": None,
                "trailing_active": False,
                "entry_time": None,
            }
            p["last_action"] = f"SELL @ €{exit_price:.2f} | netto €{netto:+.3f}"
            # Overflow → gaat naar overflow_pool (voor later expansie)
            user.setdefault("overflow_pool", 0.0)
            user["overflow_pool"] = round(user["overflow_pool"] + overflow, 4)

            # v7_spark_fee_rate_001: SPARK_FEE_RATE (default 0.0) → geen cut meer.
            # Winst gaat volledig naar user's pot capital → Bitvavo balance stijgt →
            # dynamische token-prijs volgt vanzelf. Constant blijft voor toekomstige tuning.
            spark_fee = 0.0
            if SPARK_FEE_RATE > 0 and netto >= 0.10 and user_id != "user-000":
                spark_fee = round(netto * SPARK_FEE_RATE, 4)
                # Trek af van pot capital
                p["capital"] = round(p["capital"] - spark_fee, 4)
                # Voeg toe aan Spark wallet
                try:
                    wallet_file = Path(__file__).parent.parent.parent / "data" / "wallet" / "wallets.json"
                    wal = load_json(wallet_file, default={"wallets": {}})
                    spark_wal = wal.setdefault("wallets", {}).setdefault("user-000", {
                        "wallet_id": "user-000", "balance": 0.0,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    })
                    spark_wal["balance"] = round(float(spark_wal.get("balance", 0)) + spark_fee, 4)
                    spark_wal.setdefault("fee_log", []).append({
                        "ts": datetime.now(timezone.utc).isoformat(),
                        "from_user": user_id, "from_pot": pot_id,
                        "netto_profit": netto, "fee_eur": spark_fee,
                    })
                    save_json(wallet_file, wal)
                except Exception as e:
                    import logging
                    logging.getLogger("spark_fee").warning(f"Spark fee storten faalde: {e}")

            _save(data)
            # v4_token_potje_001: bij positieve winst — mint Spark bonus-tokens (na fee-aftrek)
            bonus_result = _mint_spark_bonus_tokens(netto - spark_fee, p["id"], user_id) if netto > 0 else None
            # v4_boekhouder_001: announce SELL met netto winst en fee
            try:
                from modules.boekhouder.service import announce_sell
                announce_sell(user_id, pot_id, p.get("market") or "?-EUR",
                              exit_price, netto, spark_fee)
            except Exception:
                pass
            # v6_accounting_hooks_001 — Trade SELL resultaat → income/expense Crypto Profit
            try:
                from modules.accounting.hooks import on_trade_result
                USERS = Path(__file__).parent.parent.parent / "data" / "system" / "users.json"
                udata = load_json(USERS, default={"users": []})
                ulist = udata.get("users", []) if isinstance(udata, dict) else udata
                naam = next((u.get("naam") for u in ulist if u.get("id") == user_id), user_id)
                buy_amt = capital  # wat erin ging
                sell_amt = capital + netto  # wat eruit kwam (vóór fee)
                trade_id_local = f"sell_{pot_id}_{datetime.now(timezone.utc).timestamp()}"
                on_trade_result(
                    user_id=user_id, user_naam=naam,
                    market=p.get("market") or "?-EUR",
                    buy_amount=buy_amt, sell_amount=sell_amt,
                    trade_id=trade_id_local,
                )
            except Exception as ex:
                print(f"[close_pot] accounting-hook failed (non-blocking): {ex}")
            # Probeer automatisch te expanderen als mogelijk
            auto_expansion = None
            try:
                # Reload om geupdate overflow te zien
                check_data = _load(user_id)
                check_user = check_data["users"][user_id]
                check_potjes = check_user["potjes"]
                check_count = len(check_potjes)
                check_max = _max_size_for_count(check_count)
                all_max = all(cp["capital"] >= check_max - 0.01 for cp in check_potjes)
                check_cost = _expansion_cost(check_count)
                if all_max and check_user.get("overflow_pool", 0) >= check_cost:
                    auto_expansion = expand_potjes(user_id)
            except Exception:
                pass
            # v6_overflow_auto_mint_instant_001 — direct na trade-sluiting: check of
            # Spark's overflow_pool >= €10 staat, en mint dan onmiddellijk nieuwe
            # trade-potjes. Voorkomt 24h wachttijd van de scheduler. Spark-only.
            # v10_finance_hub_ops_001 — Gebruik finance_hub check_auto_mint_hook zodat
            # nieuwe potjes meteen hybride-revalue krijgen (capital = current token_price).
            auto_mint = None
            if user_id == "user-000":
                try:
                    from modules.boekhouder.finance_ops import check_auto_mint_hook
                    auto_mint = check_auto_mint_hook("user-000")
                    if auto_mint.get("n_minted", 0) > 0:
                        print(f"[close_pot] Auto-mint via finance_hub: {auto_mint['n_minted']} nieuwe potjes @ €{auto_mint.get('token_price_at_mint', '?')}")
                except Exception as ex:
                    print(f"[close_pot] auto-mint failed (non-blocking): {ex}")
            # v6_dynamic_pot_split_001 — DISABLED (sessie 16): auto-rebalance op
            # Bitvavo waarde botst met "1 token = 1 potje"-model. Tokens zijn leidend,
            # niet Bitvavo crypto-waardes (die zijn shared pool). Manual rebalance
            # endpoint blijft beschikbaar voor uitzonderlijke gevallen.
            return {"pot": p, "netto": round(netto, 4), "overflow": overflow,
                    "auto_expansion": auto_expansion, "spark_bonus": bonus_result,
                    "spark_fee_eur": spark_fee, "auto_mint": auto_mint}
    return {}


# =============================================================================
# v7_pot_cluster_001 — Multi-pot clusters om Bitvavo min-order te halen.
#
# Concept: 1 token = 1 pot (boekhoudkundig zuiver, capital = aankoopprijs).
# Maar Bitvavo weigert orders < min-order (€5-7 voor SOL/ADA/etc).
# Oplossing: cluster N pots samen tot Σcapital ≥ min_order, één Bitvavo-order
# voor de hele cluster, alle pots delen dezelfde entry_price + cluster_id.
# Bij SELL: sluit hele cluster tegelijk, netto winst pro-rata over pot.capital.
#
# cluster_id = uuid4-hex. None bij legacy single-pot (backwards-compat).
# =============================================================================
import uuid as _uuid


def get_next_buy_cluster(user_id: str, market: str, min_order_eur: float,
                         prefer_market: bool = True) -> Optional[Dict]:
    """Zoek closed pots die samen >= min_order_eur opleveren.

    Selectie-strategie:
      1. Eerst pots die al voor `market` gemarkeerd zijn
      2. Anders pots met `market="BCH-EUR"` (default) — mogen omgezet
      3. Skip open pots, locked pots
      4. Stop zodra Sigma capital >= min_order_eur

    Returns dict {cluster_id, pot_ids, total_capital, primary_pot_id} of None.
    """
    data = _load(user_id)
    user = data["users"][user_id]
    all_pots = user.get("potjes", [])

    free = [p for p in all_pots
            if not p.get("position", {}).get("is_open")
            and not p.get("pot_locked")]
    if not free:
        return None

    def _sort_key(p):
        m = p.get("market", "")
        if m == market:
            group = 0
        elif m == "BCH-EUR":
            group = 1
        else:
            group = 2
        return (group, float(p.get("capital", 0) or 0), p.get("id", ""))

    if prefer_market:
        free.sort(key=_sort_key)

    accumulated: List[Dict] = []
    total = 0.0
    for p in free:
        accumulated.append(p)
        total += float(p.get("capital", 0) or 0)
        if total >= min_order_eur:
            break

    if total < min_order_eur:
        return None

    cluster_id = _uuid.uuid4().hex[:12]
    return {
        "cluster_id": cluster_id,
        "pot_ids": [p["id"] for p in accumulated],
        "total_capital": round(total, 4),
        "primary_pot_id": accumulated[0]["id"],
        "n_pots": len(accumulated),
    }


@with_lock
@trace_call(category="trade.pot.open")
def open_cluster(user_id: str, pot_ids: List[str], entry_price: float, cluster_id: str,
                 current_cycle: int, trade_id: Optional[str] = None,
                 market: Optional[str] = None) -> Dict:
    """Open alle pots in de cluster gelijktijdig met shared entry + cluster_id."""
    data = _load(user_id)
    user = data["users"][user_id]
    now = datetime.now(timezone.utc).isoformat()
    opened = []
    for p in user["potjes"]:
        if p["id"] in pot_ids and not p.get("pot_locked"):
            p["position"] = {
                "is_open": True,
                "entry_price": entry_price,
                "highest_price": entry_price,
                "trailing_active": False,
                "entry_time": now,
                "amount_eur": p.get("capital"),
                "cluster_id": cluster_id,
                "cluster_size": len(pot_ids),
            }
            if market:
                p["market"] = market
            if trade_id:
                p.setdefault("trade_log", []).append({
                    "ts": now, "action": "BUY", "cluster_id": cluster_id,
                    "trade_id": trade_id, "entry_price": entry_price,
                    "amount_eur": p.get("capital"),
                })
            p["last_action"] = f"BUY cluster {cluster_id[:6]} @ EUR{entry_price:.4f}"
            opened.append(p["id"])
    _save(data)
    return {"success": True, "cluster_id": cluster_id, "opened_pot_ids": opened}


def get_pots_by_cluster(user_id: str, cluster_id: str) -> List[Dict]:
    """Return alle pots die tot deze cluster behoren (open)."""
    data = _load(user_id)
    user = data["users"][user_id]
    return [p for p in user.get("potjes", [])
            if p.get("position", {}).get("cluster_id") == cluster_id
            and p.get("position", {}).get("is_open")]


def close_cluster(user_id: str, cluster_id: str, exit_price: float) -> Dict:
    """Sluit alle pots met matching cluster_id. Netto winst pro-rata over pot.capital."""
    data = _load(user_id)
    user = data["users"][user_id]
    pots_in_cluster = [p for p in user.get("potjes", [])
                       if p.get("position", {}).get("cluster_id") == cluster_id
                       and p.get("position", {}).get("is_open")]
    if not pots_in_cluster:
        return {"success": False, "error": f"Geen open pots met cluster_id {cluster_id}"}

    total_capital = sum(float(p.get("capital", 0) or 0) for p in pots_in_cluster)
    entry_price = pots_in_cluster[0]["position"]["entry_price"]
    profit_pct = (exit_price - entry_price) / entry_price if entry_price else 0
    total_bruto = total_capital * profit_pct
    total_fees = total_capital * BITVAVO_TAKER_FEE * 2
    total_netto = total_bruto - total_fees

    now = datetime.now(timezone.utc).isoformat()
    closed = []
    per_pot_netto = {}
    for p in pots_in_cluster:
        cap = float(p.get("capital", 0) or 0)
        share = cap / total_capital if total_capital > 0 else 0
        pot_netto = round(total_netto * share, 6)
        new_capital = cap + pot_netto
        pot_max = p.get("max_size", INITIAL_MAX)
        overflow = 0.0
        if new_capital > pot_max:
            overflow = new_capital - pot_max
            new_capital = pot_max
        p["capital"] = round(new_capital, 4)
        p["stats"]["trades"] += 1
        if pot_netto > 0:
            p["stats"]["wins"] += 1
        else:
            p["stats"]["losses"] += 1
        p["stats"]["total_pnl"] = round(p["stats"]["total_pnl"] + pot_netto, 4)
        p["position"] = {
            "is_open": False, "entry_price": None, "highest_price": None,
            "trailing_active": False, "entry_time": None,
        }
        p["last_action"] = f"SELL cluster {cluster_id[:6]} @ EUR{exit_price:.4f} | share EUR{pot_netto:+.4f}"
        user.setdefault("overflow_pool", 0.0)
        user["overflow_pool"] = round(user["overflow_pool"] + overflow, 4)
        p.setdefault("trade_log", []).append({
            "ts": now, "action": "SELL", "cluster_id": cluster_id,
            "exit_price": exit_price, "netto": pot_netto, "share_pct": round(share*100, 2),
        })
        closed.append(p["id"])
        per_pot_netto[p["id"]] = pot_netto

    _save(data)
    try:
        from modules.accounting.hooks import on_trade_result
        USERS = Path(__file__).parent.parent.parent / "data" / "system" / "users.json"
        udata = load_json(USERS, default={"users": []})
        ulist = udata.get("users", []) if isinstance(udata, dict) else udata
        naam = next((u.get("naam") for u in ulist if u.get("id") == user_id), user_id)
        on_trade_result(
            user_id=user_id, user_naam=naam,
            market=pots_in_cluster[0].get("market") or "?-EUR",
            buy_amount=total_capital, sell_amount=total_capital + total_netto,
            trade_id=f"cluster_{cluster_id}",
        )
    except Exception:
        pass
    return {
        "success": True, "cluster_id": cluster_id,
        "closed_pot_ids": closed,
        "total_netto": round(total_netto, 4),
        "per_pot_netto": per_pot_netto,
        "exit_price": exit_price,
        "n_pots_closed": len(closed),
    }



def reset_last_buy_cycle(user_id: str):
    """Reset last_buy_cycle zodat volgende cycle weer mag kopen."""
    data = _load(user_id)
    user = data["users"][user_id]
    user["last_buy_cycle"] = None
    _save(data)


def expand_potjes(user_id: str) -> Dict:
    """
    Groeiregel: N potjes → max €N per potje.
    - Check: alle potjes op huidig max?
    - Check: overflow ≥ expansion cost (2N+1)?
    - Expansie: alle bestaande potjes groeien naar €(N+1) (+€1 elk),
                nieuwe potje #(N+1) = €(N+1)
    """
    data = _load(user_id)
    user = data["users"][user_id]
    potjes = user["potjes"]
    current_count = len(potjes)
    current_max = _max_size_for_count(current_count)
    overflow = user.get("overflow_pool", 0.0)

    # Alle potjes op max?
    all_at_max = all(p["capital"] >= current_max - 0.01 for p in potjes)
    if not all_at_max:
        under_max = [p["id"] for p in potjes if p["capital"] < current_max - 0.01]
        return {
            "expanded": 0,
            "reason": f"Niet alle potjes op €{current_max} ({len(under_max)} nog niet vol)",
            "current_count": current_count,
            "current_max": current_max,
        }

    # Genoeg overflow?
    cost = _expansion_cost(current_count)
    if overflow < cost:
        return {
            "expanded": 0,
            "reason": f"Overflow €{overflow:.2f} < benodigd €{cost} voor potje {current_count + 1}",
            "overflow": overflow,
            "cost_needed": cost,
        }

    # Expansie!
    new_count = current_count + 1
    new_max = _max_size_for_count(new_count)
    now = datetime.now(timezone.utc).isoformat()

    # Groei alle bestaande potjes naar new_max
    for p in potjes:
        p["max_size"] = new_max
        # Als er ruimte is: vul op tot new_max (uit overflow)
        needed = new_max - p["capital"]
        if needed > 0:
            p["capital"] = round(p["capital"] + needed, 4)

    # Voeg nieuwe potje toe
    potjes.append({
        "id": f"pot-{new_count:03d}",
        "index": current_count,
        "capital": new_max,
        "max_size": new_max,
        "position": {"is_open": False, "entry_price": None, "highest_price": None, "trailing_active": False, "entry_time": None},
        "market": user.get("market", "BCH-EUR"),
        "stats": {"trades": 0, "wins": 0, "losses": 0, "total_pnl": 0.0},
        "created_at": now,
        "last_action": None,
    })

    user["overflow_pool"] = round(overflow - cost, 4)
    _save(data)
    return {
        "expanded": 1,
        "new_count": new_count,
        "new_max": new_max,
        "cost": cost,
        "overflow_left": user["overflow_pool"],
        "message": f"Potje #{new_count} toegevoegd! Alle {new_count} potjes nu €{new_max}",
    }



# v5_potjes_distribute_001 — Verdeel potjes evenredig over een lijst van markten
def distribute_potjes_over_markets(user_id: str, markets: List[str]) -> Dict:
    """Verdeel alle potjes evenredig over de gekozen markten.
    Voorbeeld: 10 potjes + 5 markets → 2 potjes per market.
    Open posities worden NIET geraakt (alleen `market` van gesloten potjes verandert)."""
    if not markets:
        return {"success": False, "error": "Geen markten opgegeven"}
    markets = [m.strip().upper() for m in markets if m and m.strip()]
    if not markets:
        return {"success": False, "error": "Geen geldige markten"}

    data = _load(user_id)
    user = data["users"][user_id]
    potjes = user["potjes"]
    if not potjes:
        return {"success": False, "error": "Geen potjes om te verdelen"}

    n = len(potjes)
    m = len(markets)
    # Round-robin verdeling
    changed = []
    skipped_open = 0
    skipped_locked = 0
    for i, p in enumerate(potjes):
        target_market = markets[i % m]
        if p.get("position", {}).get("is_open"):
            skipped_open += 1
            continue  # niet aanraken
        # v7_anchor_removed_001 — Geen locked anchor pots meer, dus geen speciale skip.
        if p.get("pot_locked"):
            # Defensive: legacy pot met pot_locked=True nog in state → laat market ongemoeid
            skipped_locked += 1
            continue
        if p.get("market") != target_market:
            p["market"] = target_market
            changed.append({"id": p["id"], "market": target_market})

    # Update user-level primaire market (eerste in lijst)
    user["market"] = markets[0]
    _save(data)

    return {
        "success": True,
        "potjes_count": n,
        "markets_count": m,
        "per_market": n // m,
        "remainder": n % m,
        "changed_count": len(changed),
        "skipped_open_positions": skipped_open,
        "skipped_locked_anchors": skipped_locked,
        "distribution": {mkt: [p["id"] for p in potjes if p.get("market") == mkt] for mkt in markets},
    }


def get_summary(user_id: str) -> Dict:
    user = get_potjes(user_id)
    potjes = user["potjes"]
    total_capital = sum(p["capital"] for p in potjes)
    open_count = sum(1 for p in potjes if p["position"]["is_open"])
    closed_count = len(potjes) - open_count
    total_pnl = sum(p["stats"]["total_pnl"] for p in potjes)
    total_trades = sum(p["stats"]["trades"] for p in potjes)
    total_wins = sum(p["stats"]["wins"] for p in potjes)
    count = len(potjes)
    current_max = _max_size_for_count(count)
    cost_to_next = _expansion_cost(count)
    overflow = user.get("overflow_pool", 0.0)

    # Live Bitvavo balance + baseline P&L
    # v6_bitvavo_proxy_via_spark_001 — non-Spark users delen wel Spark's Bitvavo
    # voor trades, maar hún "balance" tonen we als JSON-capital (= hun aandeel)
    # ipv de gedeelde €345 totaal-pool. Anders zien alle users dezelfde fantasie-balans.
    HAS_REAL_BITVAVO = {"user-000", "user-001"}
    live_balance = None
    live_pnl = None
    baseline = None
    if user_id in HAS_REAL_BITVAVO:
        try:
            baseline_file = Path(__file__).parent.parent.parent / "data" / "trade" / "capital_baseline.json"
            baseline_data = load_json(baseline_file, default={})
            baseline = baseline_data.get(user_id, {}).get("baseline_eur")
            from modules.trade.monitor import fetch_bitvavo_balance
            bv = fetch_bitvavo_balance(user_id)
            if bv.get("success"):
                live_balance = bv.get("total_eur")
                if baseline is not None and live_balance is not None:
                    live_pnl = round(live_balance - baseline, 2)
        except Exception:
            pass
    # Fallback voor non-Spark users OR mislukte Bitvavo call: per-user
    # live_balance = som van JSON capital (gerealiseerd) + mark-to-market open posities.
    if live_balance is None:
        live_balance = round(total_capital, 4)
        baseline = round(START_AMOUNT * count, 4)
        live_pnl = round(live_balance - baseline, 2)

    return {
        "pot_count": count,
        "total_capital": round(total_capital, 2),
        "current_max_per_pot": current_max,
        "open_positions": open_count,
        "closed_positions": closed_count,
        "total_pnl": round(total_pnl, 4),
        "total_trades": total_trades,
        "win_rate": round(total_wins / total_trades * 100, 1) if total_trades else 0,
        "overflow_pool": round(overflow, 4),
        "last_buy_cycle": user.get("last_buy_cycle"),
        "market": user.get("market", "BCH-EUR"),
        # Groei info
        "next_pot_cost": cost_to_next,
        "next_pot_number": count + 1,
        "next_pot_max": _max_size_for_count(count + 1),
        "can_expand": overflow >= cost_to_next and all(p["capital"] >= current_max - 0.01 for p in potjes),
        "expansion_progress_pct": round(min(100, (overflow / cost_to_next) * 100), 1) if cost_to_next else 0,
        # Live metrics
        "live_balance": live_balance,
        "live_pnl": live_pnl,
        "baseline_eur": baseline,
    }
