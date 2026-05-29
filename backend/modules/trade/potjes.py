"""
Potjes Systeem - 10 onafhankelijke trading pots.

Regels (Willem's design):
- Start: 10 potjes à €5.08
- Groei: winst blijft in potje, max €10/potje
- Als alle potjes €10: voeg nieuwe potjes toe (volume uitbreiding)
- Max 1 potje per monitor cycle mag kopen (staggered entry)
- Elk potje heeft eigen trailing stop + position state
"""
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timezone
from modules.core.storage import load_json, save_json

POTJES_FILE = Path(__file__).parent.parent.parent / "data" / "financial" / "user_potjes.json"
ROAR_FILE = Path(__file__).parent.parent.parent / "data" / "roar" / "roar_balances.json"

START_AMOUNT = 10.0  # v6_potje_size_10_001 — starters direct €10 (was €5.08)
DEFAULT_POT_COUNT = 5  # v6_clean_slate_28mei — 5 base potjes van €10 = €50 baseline
SPARK_EXTRA_TRADE_SLOTS = 10  # v6_spark_15slots_001 (28 mei) — Spark krijgt 5 base + 10 trade-slots = 15 totaal
INITIAL_MAX = 50.0  # tier 1: max €50 (5x growth)
LOCKED_POT_INDEX = None  # v6_clean_slate_28mei — geen lock-anker; potjes = trade-posities
BITVAVO_TAKER_FEE = 0.0025
TOKEN_PRICE = 5.08  # vaste prijs per ROAR token (= 1 bonus token bij €5.08 winst)


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
    # Voorkomt edge cases waar legacy data slechts 1-2 potjes had
    # v6_pot1_staking_lock_001: zorg dat pot-001 (index 0) altijd `pot_locked=True` heeft
    # v6_spark_15slots_001 — Spark krijgt 5 base + 10 trade-slots = 15 totaal
    target_count = DEFAULT_POT_COUNT + SPARK_EXTRA_TRADE_SLOTS if is_spark else DEFAULT_POT_COUNT
    if is_spark and len(user.get("potjes", [])) < target_count:
        existing = user["potjes"]
        next_idx = max((p.get("index", i) for i, p in enumerate(existing)), default=-1) + 1
        now = datetime.now(timezone.utc).isoformat()
        while len(existing) < target_count:
            is_locked = (next_idx == LOCKED_POT_INDEX)
            existing.append({
                "id": f"pot-{next_idx+1:03d}",
                "index": next_idx,
                "capital": START_AMOUNT,
                "max_size": INITIAL_MAX,
                "pot_locked": is_locked,
                "lock_reason": "staking_anchor" if is_locked else None,
                "position": {
                    "is_open": False, "entry_price": None, "highest_price": None,
                    "trailing_active": False, "entry_time": None,
                },
                "market": existing[0].get("market", "BCH-EUR") if existing else "BCH-EUR",
                "stats": {"trades": 0, "wins": 0, "losses": 0, "total_pnl": 0.0},
                "created_at": now,
                "last_action": None,
            })
            next_idx += 1
        user["potjes"] = existing
        data["users"][user_id] = user
        save_json(POTJES_FILE, data)
    # v6_pot1_staking_lock_only_spark_fix_001 (sessie 14) — backfill van staking-anchor
    # mag ALLEEN bij Spark (user-000). Non-Spark users hebben "1 token = 1 potje" en
    # géén anchors. Eerder werd ook bij Willem/Gijs pot-001 telkens auto-gelocked.
    potjes_list = user.get("potjes", [])
    if is_spark and potjes_list:
        # Vind het 'eerste' potje: liefst index==0, anders nummer==1, anders gewoon eerste in lijst
        def _pot_sort_key(p):
            return (p.get("index") if p.get("index") is not None else 999,
                    p.get("nummer") if p.get("nummer") is not None else 999,
                    p.get("id", "zzz"))
        first_pot = sorted(potjes_list, key=_pot_sort_key)[0]
        if not first_pot.get("pot_locked"):
            first_pot["pot_locked"] = True
            first_pot["lock_reason"] = "staking_anchor"
            data["users"][user_id] = user
            save_json(POTJES_FILE, data)
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

    # Voeg potjes toe tot target. Eerste potje (index 0) blijft staking-anker.
    now = datetime.now(timezone.utc).isoformat()
    next_idx = max((p.get("index", i) for i, p in enumerate(potjes)), default=-1) + 1
    added = 0
    while len(potjes) < target:
        is_locked = (next_idx == LOCKED_POT_INDEX)
        potjes.append({
            "id": f"pot-{next_idx+1:03d}",
            "index": next_idx,
            "capital": START_AMOUNT,
            "max_size": INITIAL_MAX,
            "pot_locked": is_locked,
            "lock_reason": "staking_anchor" if is_locked else None,
            "position": {"is_open": False, "entry_price": None, "highest_price": None,
                         "trailing_active": False, "entry_time": None},
            "market": market,
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
    """Maak initiële 10 potjes à €10 voor user. Pot 1 (index 0) = staking-lock.

    v6_potje_size_10_001: nieuwe potjes starten direct op €10 (was €5.08).
    v6_pot1_staking_lock_001: pot-001 krijgt `pot_locked=True` — wordt geskipt door
    de trade-bot en quick-buy. Dient als ROAR-token staking-anker.
    """
    now = datetime.now(timezone.utc).isoformat()
    potjes = []
    for i in range(DEFAULT_POT_COUNT):
        is_locked = (i == LOCKED_POT_INDEX)
        potjes.append({
            "id": f"pot-{i+1:03d}",
            "index": i,
            "capital": START_AMOUNT,
            "max_size": INITIAL_MAX,
            "pot_locked": is_locked,  # v6_pot1_staking_lock_001
            "lock_reason": "staking_anchor" if is_locked else None,
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
    # Verrijk elk potje met live_value: als gesloten → aandeel in live balance
    try:
        baseline_file = Path(__file__).parent.parent.parent / "data" / "trade" / "capital_baseline.json"
        baseline_data = load_json(baseline_file, default={})
        baseline = baseline_data.get(user_id, {}).get("baseline_eur")
        from modules.trade.monitor import fetch_bitvavo_balance
        bv = fetch_bitvavo_balance(user_id)
        live_balance = bv.get("total_eur") if bv.get("success") else None
    except Exception:
        live_balance = None
        baseline = None

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


def get_available_pot(user_id: str, current_cycle: int, skip_cycle_check: bool = False) -> Optional[Dict]:
    """
    Vind een potje dat mag kopen:
    - is_open = False (niet in positie)
    - last_buy_cycle != current_cycle (nog geen potje in deze cycle gekocht)
    Returns het eerste vrije potje gesorteerd op nummer (1..10), of None.
    v4_potje_sync_001: sorteer op nummer/index zodat UI en backend dezelfde keuze maken.
    v4_potje_quickbuy_002: skip_cycle_check voor user-initiated Quick Buy (user mag meerdere
    potjes openen in dezelfde monitor-cycle).
    v6_pot1_staking_lock_001: skip potjes met `pot_locked=True` (staking-anker).
    """
    user = get_potjes(user_id)
    if not skip_cycle_check and user.get("last_buy_cycle") == current_cycle:
        return None  # Al een potje gekocht in deze cycle (monitor-mode bescherming)
    sorted_potjes = sorted(user["potjes"], key=lambda p: (p.get("nummer") or (p.get("index", 99) + 1)))
    for p in sorted_potjes:
        if p.get("pot_locked"):
            continue  # v6_pot1_staking_lock_001 — staking-anker overslaan
        if not p["position"]["is_open"]:
            return p
    return None


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
    """Update highest_price en trailing_active voor open positie."""
    data = _load(user_id)
    user = data["users"][user_id]
    for p in user["potjes"]:
        if p["id"] == pot_id and p["position"]["is_open"]:
            pos = p["position"]
            if current_price > pos["highest_price"]:
                pos["highest_price"] = current_price
            profit_pct = (current_price - pos["entry_price"]) / pos["entry_price"]
            if profit_pct >= 0.01:
                pos["trailing_active"] = True
            _save(data)
            return p
    return {}


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

            # v4_spark_fee_001: 5% van netto winst (≥ €0.10) → naar Spark wallet (user-000)
            # Eigenaarschap-check: Spark's eigen bot (user-000) betaalt geen fee aan zichzelf
            spark_fee = 0.0
            if netto >= 0.10 and user_id != "user-000":
                spark_fee = round(netto * 0.05, 4)
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
            return {"pot": p, "netto": round(netto, 4), "overflow": overflow, "auto_expansion": auto_expansion, "spark_bonus": bonus_result, "spark_fee_eur": spark_fee}
    return {}


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
        # v6_distribute_respect_lock_001 (sessie 14) — locked staking-ankers houden
        # hun coin-koppeling. Zonder deze guard zou een coin-herverdeling de
        # 5 anchor-potjes door elkaar gooien (bv. ADA-anker → BCH-anker).
        if p.get("pot_locked"):
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
    live_balance = None
    live_pnl = None
    baseline = None
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
