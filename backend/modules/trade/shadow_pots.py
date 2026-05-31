"""
Shadow-potjes systeem (v6_shadow_pot_001) — Willem's idee, 2026-05-31

Concept:
  Elk potje kan een SHADOW twin krijgen. Bij een dump (verlies > threshold):
    - Origineel potje BLIJFT OPEN (geen gerealiseerd verlies)
    - Shadow potje doet RE-ENTRY BUY op de lage prijs
    - Bij recovery → origineel trail-SELT op winst, shadow trail-SELT op winst
    → 2 winst-kansen i.p.v. 1 verlies

Community-pool (later, na MVP):
  User met 0 vrije shadow-potjes → leen er één uit collectieve pool
  Voorkeur: shadow van user met minste winst (solidariteit)
  Winst-deling 50/50 of via algoritme

Storage:
  data/trade/shadow_pots.json
  {
    "shadows": [
      {
        "shadow_id": "shadow-001",
        "original_pot_id": "pot-001",
        "owner_user_id": "user-001",      # eigenaar shadow (kan != origineel-owner zijn bij community lending)
        "original_owner_id": "user-001",  # eigenaar origineel potje
        "market": "BTC-EUR",
        "capital": 10.0,
        "status": "idle|active|closed",
        "activated_at": null,
        "entry_price": null,
        "exit_price": null,
        "trigger_drop_pct": null,
        "profit": null,
        "borrowed_from": null,            # set bij community-lending
        "created_at": ISO,
        "closed_at": null
      }
    ]
  }

Activatie-regel:
  Triggert bij profit_pct ≤ SHADOW_TRIGGER_PCT (-3%, ruimer dan stop-loss zou zijn)
  Voorkomt dat shadows op kleine swings activeren

Idempotency:
  Per origineel-pot is er maximaal 1 actieve shadow.
"""
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from ..core.storage import load_json, save_json

DATA_ROOT = Path(__file__).parent.parent.parent / "data"
SHADOW_FILE = DATA_ROOT / "trade" / "shadow_pots.json"
POTJES_FILE = DATA_ROOT / "financial" / "user_potjes.json"

# Configuratie
SHADOW_TRIGGER_PCT = -0.03   # -3% verlies → activeer shadow
MAX_SHADOWS_PER_POT = 1      # geen oneindig stapelen


def _load() -> dict:
    SHADOW_FILE.parent.mkdir(parents=True, exist_ok=True)
    return load_json(SHADOW_FILE, default={"shadows": []})


def _save(data: dict) -> None:
    save_json(SHADOW_FILE, data)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_shadows_for_pot(pot_id: str) -> List[dict]:
    """Alle shadows (idle/active/closed) gekoppeld aan een origineel potje."""
    data = _load()
    return [s for s in data.get("shadows", []) if s.get("original_pot_id") == pot_id]


def get_active_shadow(pot_id: str) -> Optional[dict]:
    """De actieve shadow voor een origineel potje, indien aanwezig."""
    for s in get_shadows_for_pot(pot_id):
        if s.get("status") == "active":
            return s
    return None


def create_shadow_for_pot(pot_id: str, user_id: str, market: str, capital: float = 10.0) -> dict:
    """
    Maak een idle shadow voor een origineel potje. Idempotent: als al een
    actieve/idle shadow bestaat → return die.
    """
    data = _load()
    existing = next(
        (s for s in data["shadows"]
         if s.get("original_pot_id") == pot_id and s.get("status") in ("idle", "active")),
        None,
    )
    if existing:
        return {"success": True, "shadow": existing, "created": False}

    next_idx = len(data["shadows"]) + 1
    shadow = {
        "shadow_id": f"shadow-{next_idx:03d}",
        "original_pot_id": pot_id,
        "owner_user_id": user_id,
        "original_owner_id": user_id,
        "market": market,
        "capital": float(capital),
        "status": "idle",
        "activated_at": None,
        "entry_price": None,
        "exit_price": None,
        "trigger_drop_pct": None,
        "profit": None,
        "borrowed_from": None,
        "created_at": _now_iso(),
        "closed_at": None,
    }
    data["shadows"].append(shadow)
    _save(data)
    return {"success": True, "shadow": shadow, "created": True}


def activate_shadow(pot_id: str, entry_price: float, drop_pct: float, trade_id: Optional[str] = None) -> dict:
    """Activeer de shadow voor een origineel potje (= shadow doet BUY op lage prijs)."""
    data = _load()
    idle = next(
        (s for s in data["shadows"]
         if s.get("original_pot_id") == pot_id and s.get("status") == "idle"),
        None,
    )
    if not idle:
        return {"success": False, "error": f"Geen idle shadow voor {pot_id}"}

    idle["status"] = "active"
    idle["activated_at"] = _now_iso()
    idle["entry_price"] = float(entry_price)
    idle["trigger_drop_pct"] = float(drop_pct)
    idle["trade_id"] = trade_id
    _save(data)
    return {"success": True, "shadow": idle}


def close_shadow(shadow_id: str, exit_price: float, profit: float) -> dict:
    """Sluit een actieve shadow (= shadow doet SELL bij recovery/winst)."""
    data = _load()
    sh = next((s for s in data["shadows"] if s.get("shadow_id") == shadow_id), None)
    if not sh:
        return {"success": False, "error": f"Shadow {shadow_id} niet gevonden"}
    if sh.get("status") != "active":
        return {"success": False, "error": f"Shadow {shadow_id} niet actief (status={sh.get('status')})"}

    sh["status"] = "closed"
    sh["exit_price"] = float(exit_price)
    sh["profit"] = float(profit)
    sh["closed_at"] = _now_iso()
    _save(data)
    return {"success": True, "shadow": sh}


def auto_ensure_shadows_for_user(user_id: str) -> dict:
    """
    Maak shadows voor ALLE potjes van een user die er nog geen hebben.
    Wordt aangeroepen bij pot-creatie + na auto-provision.
    """
    pots_data = load_json(POTJES_FILE, default={"users": {}})
    u = pots_data.get("users", {}).get(user_id, {})
    pots = u.get("potjes", []) or u.get("pots", [])
    created = []
    for p in pots:
        pot_id = p.get("id")
        if not pot_id:
            continue
        # Anchors (locked) krijgen geen shadow — die zijn statische staking-anchors
        if p.get("pot_locked"):
            continue
        result = create_shadow_for_pot(
            pot_id=pot_id,
            user_id=user_id,
            market=p.get("market", "BCH-EUR"),
            capital=float(p.get("capital", 10.0)),
        )
        if result.get("created"):
            created.append(result["shadow"]["shadow_id"])
    return {"success": True, "user_id": user_id, "created": created, "total_created": len(created)}


def list_shadows_for_user(user_id: str) -> List[dict]:
    """Alle shadows die deze user bezit (eigenaar van de shadow)."""
    data = _load()
    return [s for s in data.get("shadows", []) if s.get("owner_user_id") == user_id]


def stats() -> dict:
    """Aggregate stats voor admin dashboard."""
    data = _load()
    shadows = data.get("shadows", [])
    by_status = {"idle": 0, "active": 0, "closed": 0}
    total_profit = 0.0
    for s in shadows:
        st = s.get("status", "idle")
        by_status[st] = by_status.get(st, 0) + 1
        if s.get("profit"):
            total_profit += float(s.get("profit", 0))
    return {
        "total": len(shadows),
        "by_status": by_status,
        "total_profit_realized": round(total_profit, 4),
    }
