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
import uuid
from modules.core.storage import load_json, save_json

POTJES_FILE = Path(__file__).parent.parent.parent / "data" / "financial" / "user_potjes.json"

START_AMOUNT = 5.08
MAX_POT_SIZE = 10.0
DEFAULT_POT_COUNT = 10
BITVAVO_TAKER_FEE = 0.0025

# Niet-lineaire expansie: bij €108 (tier 1 compleet + 8% buffer)
# start tier 2 met grotere potjes. Elke tier verdubbelt pot-grootte.
TIER_TRIGGER_MULTIPLIER = 1.08  # 8% buffer over tier-capaciteit
TIER_GROWTH_FACTOR = 2.0  # pot-grootte verdubbelt per tier
POTJES_PER_TIER = 5  # aantal nieuwe potjes per tier


def _tier_config(tier: int) -> Dict:
    """
    Tier 1: 10 potjes, start €5.08, max €10
    Tier 2: +5 potjes, start €10, max €20 (trigger bij €108 totaal)
    Tier 3: +5 potjes, start €20, max €40 (trigger bij €216 totaal)
    Tier N: +5 potjes, start = €5.08 * 2^(N-1), max = €10 * 2^(N-1)
    """
    if tier == 1:
        return {"count": DEFAULT_POT_COUNT, "start": START_AMOUNT, "max": MAX_POT_SIZE}
    factor = TIER_GROWTH_FACTOR ** (tier - 1)
    return {"count": POTJES_PER_TIER, "start": round(START_AMOUNT * factor, 2), "max": round(MAX_POT_SIZE * factor, 2)}


def _current_tier(potjes: List[Dict]) -> int:
    """Bepaal huidige tier op basis van hoogste potje max."""
    if not potjes:
        return 1
    max_size = max(p.get("max_size", MAX_POT_SIZE) for p in potjes)
    tier = 1
    while MAX_POT_SIZE * (TIER_GROWTH_FACTOR ** (tier - 1)) < max_size:
        tier += 1
    return tier


def _tier_trigger_threshold(tier: int) -> float:
    """Totaal capital waarop volgende tier moet starten."""
    # Som van alle tiers tot en met `tier`:
    total = 0.0
    for t in range(1, tier + 1):
        cfg = _tier_config(t)
        total += cfg["count"] * cfg["max"]
    return round(total * TIER_TRIGGER_MULTIPLIER, 2)


def _load(user_id: str) -> Dict:
    data = load_json(POTJES_FILE, default={"users": {}})
    user = data.get("users", {}).get(user_id, {})
    if not user.get("potjes"):
        user = _init_potjes(user_id)
        data.setdefault("users", {})[user_id] = user
        save_json(POTJES_FILE, data)
    return data


def _save(data: Dict):
    save_json(POTJES_FILE, data)


def _init_potjes(user_id: str) -> Dict:
    """Maak initiële 10 potjes à €5.08 voor user."""
    now = datetime.now(timezone.utc).isoformat()
    cfg = _tier_config(1)
    potjes = []
    for i in range(cfg["count"]):
        potjes.append({
            "id": f"pot-{i+1:03d}",
            "index": i,
            "tier": 1,
            "capital": cfg["start"],
            "max_size": cfg["max"],
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
        "current_tier": 1,
        "created_at": now,
    }


def get_potjes(user_id: str) -> Dict:
    data = _load(user_id)
    return data["users"][user_id]


def get_available_pot(user_id: str, current_cycle: int) -> Optional[Dict]:
    """
    Vind een potje dat mag kopen:
    - is_open = False (niet in positie)
    - last_buy_cycle != current_cycle (nog geen potje in deze cycle gekocht)
    Returns het eerste vrije potje, of None.
    """
    user = get_potjes(user_id)
    if user.get("last_buy_cycle") == current_cycle:
        return None  # Al een potje gekocht in deze cycle
    for p in user["potjes"]:
        if not p["position"]["is_open"]:
            return p
    return None


def open_pot(user_id: str, pot_id: str, entry_price: float, current_cycle: int) -> Dict:
    """Open positie in een potje."""
    data = _load(user_id)
    user = data["users"][user_id]
    now = datetime.now(timezone.utc).isoformat()
    for p in user["potjes"]:
        if p["id"] == pot_id:
            p["position"] = {
                "is_open": True,
                "entry_price": entry_price,
                "highest_price": entry_price,
                "trailing_active": False,
                "entry_time": now,
            }
            p["last_action"] = f"BUY @ €{entry_price:.2f}"
            user["last_buy_cycle"] = current_cycle
            _save(data)
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
    """Sluit positie, voeg winst toe aan capital (tot max), update stats."""
    data = _load(user_id)
    user = data["users"][user_id]
    for p in user["potjes"]:
        if p["id"] == pot_id and p["position"]["is_open"]:
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
            pot_max = p.get("max_size", MAX_POT_SIZE)
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
            _save(data)
            return {"pot": p, "netto": round(netto, 4), "overflow": overflow}
    return {}


def reset_last_buy_cycle(user_id: str):
    """Reset last_buy_cycle zodat volgende cycle weer mag kopen."""
    data = _load(user_id)
    user = data["users"][user_id]
    user["last_buy_cycle"] = None
    _save(data)


def expand_potjes(user_id: str) -> Dict:
    """
    Niet-lineaire expansie via tier-systeem:
    - Tier 1: 10 potjes × €10 max (€100 cap)
    - Tier 2 trigger: totaal capital ≥ €108 → +5 potjes × €20 max
    - Tier 3 trigger: totaal capital ≥ €216 → +5 potjes × €40 max
    - Elke tier verdubbelt pot-grootte (volume-gedreven)
    """
    data = _load(user_id)
    user = data["users"][user_id]
    potjes = user["potjes"]
    current_tier = user.get("current_tier", _current_tier(potjes))
    total_capital = sum(p["capital"] for p in potjes) + user.get("overflow_pool", 0.0)
    threshold = _tier_trigger_threshold(current_tier)

    if total_capital < threshold:
        return {
            "expanded": 0,
            "reason": f"Tier {current_tier+1} vereist €{threshold:.2f} (huidig: €{total_capital:.2f})",
            "current_tier": current_tier,
            "next_tier_threshold": threshold,
        }

    # Expand naar volgende tier
    next_tier = current_tier + 1
    cfg = _tier_config(next_tier)

    # Hoeveel nieuwe potjes kunnen we financieren uit huidige capital?
    overflow = user.get("overflow_pool", 0.0)
    pots_affordable = int(overflow / cfg["start"])
    if pots_affordable == 0:
        return {
            "expanded": 0,
            "reason": f"Overflow pool €{overflow:.2f} te klein voor tier {next_tier} potje (€{cfg['start']:.2f})",
        }

    now = datetime.now(timezone.utc).isoformat()
    start_idx = len(potjes)
    added = 0
    for i in range(min(cfg["count"], pots_affordable)):
        potjes.append({
            "id": f"pot-{start_idx + i + 1:03d}",
            "index": start_idx + i,
            "tier": next_tier,
            "capital": cfg["start"],
            "max_size": cfg["max"],
            "position": {"is_open": False, "entry_price": None, "highest_price": None, "trailing_active": False, "entry_time": None},
            "market": user.get("market", "BCH-EUR"),
            "stats": {"trades": 0, "wins": 0, "losses": 0, "total_pnl": 0.0},
            "created_at": now,
            "last_action": None,
        })
        added += 1

    user["overflow_pool"] = round(overflow - (added * cfg["start"]), 4)
    user["current_tier"] = next_tier
    _save(data)
    return {
        "expanded": added,
        "new_tier": next_tier,
        "new_pot_size": cfg["max"],
        "overflow_left": user["overflow_pool"],
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
    current_tier = user.get("current_tier", _current_tier(potjes))
    next_threshold = _tier_trigger_threshold(current_tier)
    return {
        "pot_count": len(potjes),
        "total_capital": round(total_capital, 2),
        "open_positions": open_count,
        "closed_positions": closed_count,
        "total_pnl": round(total_pnl, 4),
        "total_trades": total_trades,
        "win_rate": round(total_wins / total_trades * 100, 1) if total_trades else 0,
        "overflow_pool": round(user.get("overflow_pool", 0.0), 4),
        "last_buy_cycle": user.get("last_buy_cycle"),
        "market": user.get("market", "BCH-EUR"),
        "current_tier": current_tier,
        "next_tier_threshold": next_threshold,
        "progress_to_next_tier": round((total_capital + user.get("overflow_pool", 0.0)) / next_threshold * 100, 1) if next_threshold else 0,
    }
