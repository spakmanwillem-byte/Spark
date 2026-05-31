"""
Inventory Module (v4_inventory_001)

Stats + Inventory per user (incl. bots) — basis voor D&D laag.

JSON Schema (/app/backend/data/users/{user_id}/inventory.json):
{
  "user_id": "user-001",
  "slots": [
    {"id": "slot-xxx", "item_id": "backpack-basic", "naam": "Basis Rugzak", "kind": "carry", "weight": 1.0, "capacity_bonus": 5, "weight_bonus": 10.0, "acquired_at": "ISO"}
  ],
  "stats": {
    "level": 277,       # afgeleid van XP // 100
    "xp": 27720,
    "rang": "Generaal",
    "gradatie": 4,
    "trust": 0,
    "achievements": []
  },
  "capacity": {
    "slots_base": 4,
    "slots_used": 1,
    "slots_total": 9,     # base + sum(capacity_bonus)
    "weight_used": 1.0,
    "weight_max": 20.0,   # base 10 + sum(weight_bonus)
  }
}
"""
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timezone
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..core.storage import load_json, save_json

router = APIRouter(prefix="/inventory", tags=["inventory"])

DATA_ROOT = Path(__file__).parent.parent.parent / "data"
USERS_FILE = DATA_ROOT / "system" / "users.json"
USERS_DIR = DATA_ROOT / "users"

BASE_SLOTS = 4         # ieder krijgt standaard 4 slots
BASE_WEIGHT_MAX = 10.0  # 10kg basis-tilcapaciteit

# Built-in item-catalogus (uitbreidbaar via KB later)
ITEM_CATALOG = {
    "backpack-basic": {
        "naam": "Basis Rugzak",
        "kind": "carry",
        "weight": 1.0,
        "capacity_bonus": 5,
        "weight_bonus": 10.0,
        "description": "Een eenvoudige stoffen rugzak. +5 slots, +10kg draagkracht. Weegt zelf 1kg.",
        "icon": "🎒",
        "rarity": "common",
    },
    "backpack-large": {
        "naam": "Grote Trekrugzak",
        "kind": "carry",
        "weight": 2.5,
        "capacity_bonus": 10,
        "weight_bonus": 25.0,
        "description": "Stevige trekrugzak met meerdere vakken. +10 slots, +25kg. Weegt 2.5kg.",
        "icon": "🎒",
        "rarity": "uncommon",
    },
    "achievement-token": {
        "naam": "Achievement Penning",
        "kind": "trophy",
        "weight": 0.05,
        "description": "Symbool van een afgeronde achievement.",
        "icon": "🏅",
        "rarity": "common",
    },
    "auto-bark-pup": {
        "naam": "Auto-Bark Welp",
        "kind": "pet",
        "weight": 0.5,
        "description": "Een mini-Bark die automatisch reageert in community-chat (1x per dag).",
        "icon": "🐶",
        "rarity": "rare",
    },
    # === v6_food_items_001 — Voedsel & basis-loot (gemaakt thuis, mee op pad) ===
    "brood": {
        "naam": "Brood",
        "kind": "food",
        "weight": 0.4,
        "description": "Vers brood van de bakker. Herstelt 20 conditie. Bederft over tijd.",
        "icon": "🍞",
        "rarity": "common",
        "tags": ["brood", "voedsel", "bakker"],
        "value_goud": 2,
    },
    "vlees": {
        "naam": "Stuk Vlees",
        "kind": "food",
        "weight": 0.6,
        "description": "Rauw stuk vlees. Bak het thuis voor een sterke maaltijd. Herstelt 35 conditie.",
        "icon": "🥩",
        "rarity": "common",
        "tags": ["vlees", "voedsel", "slager"],
        "value_goud": 4,
    },
    "water": {
        "naam": "Veldfles Water",
        "kind": "drink",
        "weight": 0.8,
        "description": "Schoon drinkwater. Onmisbaar onderweg.",
        "icon": "💧",
        "rarity": "common",
        "tags": ["water", "drank"],
        "value_goud": 1,
    },
    "kaas": {
        "naam": "Boerenkaas",
        "kind": "food",
        "weight": 0.3,
        "description": "Stuk gerijpte kaas. Lichte snack. Herstelt 15 conditie.",
        "icon": "🧀",
        "rarity": "common",
        "tags": ["kaas", "voedsel"],
        "value_goud": 3,
    },
    "appel": {
        "naam": "Appel",
        "kind": "food",
        "weight": 0.15,
        "description": "Verse rode appel. Herstelt 8 conditie. Licht in het dragen.",
        "icon": "🍎",
        "rarity": "common",
        "tags": ["appel", "fruit", "voedsel"],
        "value_goud": 1,
    },
    "ei": {
        "naam": "Ei",
        "kind": "food",
        "weight": 0.08,
        "description": "Vers boerenei. Mengsel-basis voor maaltijden.",
        "icon": "🥚",
        "rarity": "common",
        "tags": ["ei", "voedsel"],
        "value_goud": 1,
    },
    "fakkel": {
        "naam": "Fakkel",
        "kind": "tool",
        "weight": 0.5,
        "description": "Brandende fakkel. Verlicht donkere plekken. 30 min brandtijd.",
        "icon": "🔥",
        "rarity": "common",
        "tags": ["fakkel", "licht"],
        "value_goud": 2,
    },
    "munt-goud": {
        "naam": "Goudstuk",
        "kind": "currency",
        "weight": 0.01,
        "description": "Eén glanzend goudstuk. Universeel ruilmiddel in Spark World.",
        "icon": "🪙",
        "rarity": "common",
        "tags": ["goud", "munt", "valuta"],
        "value_goud": 1,
    },
    # === v6_combat_items_001 — Wapens & kleding met stat-bonussen (common, overal te vinden) ===
    # Schema-uitbreiding:
    #   stats_bonus:  {kracht, behendigheid, intelligentie, conditie, wilskracht, geluk}
    #   combat_bonus: {aanvalskracht, verdediging, magie, crit_kans, beweging, initiatief}
    #   meta:         {klasse, beroep, fractie, locatie}   ← fractie="" = overal te vinden (common loot)
    "zwaard-klein": {
        "naam": "Klein Zwaard",
        "kind": "weapon",
        "weight": 1.5,
        "description": "Eenvoudig kort zwaard. Stevig, balanceert goed, ideaal voor beginners.",
        "icon": "⚔",
        "rarity": "common",
        "tags": ["zwaard", "wapen", "rechterhand"],
        "value_goud": 12,
        "slot": "rechterhand",
        "stats_bonus": {"kracht": 1},
        "combat_bonus": {"aanvalskracht": 5, "crit_kans": 2},
        "meta": {"klasse": "Strijder", "beroep": "", "fractie": "", "locatie": "Overal"},
    },
    "schild-basis": {
        "naam": "Basis Schild",
        "kind": "shield",
        "weight": 2.2,
        "description": "Houten schild met ijzeren rand. Blokt simpele aanvallen.",
        "icon": "🛡",
        "rarity": "common",
        "tags": ["schild", "linkerhand"],
        "value_goud": 10,
        "slot": "linkerhand",
        "stats_bonus": {"conditie": 1},
        "combat_bonus": {"verdediging": 6, "beweging": -2},
        "meta": {"klasse": "Strijder", "beroep": "", "fractie": "", "locatie": "Overal"},
    },
    "linnen-shirt": {
        "naam": "Linnen Shirt",
        "kind": "armor",
        "weight": 0.6,
        "description": "Eenvoudig wit linnen shirt. Licht en luchtig. Biedt minimale bescherming.",
        "icon": "👕",
        "rarity": "common",
        "tags": ["torso", "shirt", "linnen", "kleding"],
        "value_goud": 6,
        "slot": "torso",
        "stats_bonus": {"behendigheid": 1},
        "combat_bonus": {"verdediging": 1, "beweging": 1},
        "meta": {"klasse": "", "beroep": "", "fractie": "", "locatie": "Overal"},
    },
    "linnen-broek": {
        "naam": "Linnen Broek",
        "kind": "armor",
        "weight": 0.7,
        "description": "Versleten maar comfortabele broek. Standaard reizigersuitrusting.",
        "icon": "👖",
        "rarity": "common",
        "tags": ["broek", "linnen", "kleding"],
        "value_goud": 6,
        "slot": "broek",
        "stats_bonus": {},
        "combat_bonus": {"verdediging": 1, "beweging": 1},
        "meta": {"klasse": "", "beroep": "", "fractie": "", "locatie": "Overal"},
    },
    "lederen-helm": {
        "naam": "Lederen Helm",
        "kind": "armor",
        "weight": 0.5,
        "description": "Gehard lederen kapje. Beschermt het hoofd tegen klappen.",
        "icon": "🪖",
        "rarity": "common",
        "tags": ["hoofd", "helm", "leer"],
        "value_goud": 8,
        "slot": "hoofd",
        "stats_bonus": {"wilskracht": 1},
        "combat_bonus": {"verdediging": 2},
        "meta": {"klasse": "Strijder", "beroep": "", "fractie": "", "locatie": "Overal"},
    },
    "leren-laarzen": {
        "naam": "Leren Laarzen",
        "kind": "armor",
        "weight": 0.9,
        "description": "Stevige leren laarzen. Comfortabel op lange tochten.",
        "icon": "🥾",
        "rarity": "common",
        "tags": ["voeten", "schoenen", "laarzen", "leer"],
        "value_goud": 7,
        "slot": "voeten",
        "stats_bonus": {"conditie": 1},
        "combat_bonus": {"verdediging": 1, "beweging": 3},
        "meta": {"klasse": "", "beroep": "Reiziger", "fractie": "", "locatie": "Overal"},
    },
}


# ============== HELPERS ==============
def _inv_path(user_id: str) -> Path:
    d = USERS_DIR / user_id
    d.mkdir(parents=True, exist_ok=True)
    return d / "inventory.json"


def _get_user(user_id: str) -> Optional[dict]:
    data = load_json(USERS_FILE, default={"users": []})
    return next((u for u in data.get("users", []) if u.get("id") == user_id), None)


def _compute_capacity(slots: List[dict]) -> dict:
    """Bereken capacity uit slots."""
    cap_bonus = sum(s.get("capacity_bonus", 0) for s in slots)
    weight_bonus = sum(s.get("weight_bonus", 0.0) for s in slots)
    weight_used = sum(s.get("weight", 0.0) for s in slots)
    return {
        "slots_base": BASE_SLOTS,
        "slots_used": len(slots),
        "slots_total": BASE_SLOTS + cap_bonus,
        "weight_used": round(weight_used, 2),
        "weight_max": round(BASE_WEIGHT_MAX + weight_bonus, 2),
    }


def _load_or_init(user_id: str) -> dict:
    u = _get_user(user_id)
    if not u:
        raise HTTPException(404, "User niet gevonden")
    fp = _inv_path(user_id)
    inv = load_json(fp, default={})
    # storage.load_json returns {} when file not exists (zelfs met default=None)
    # → check op "slots" key, niet inv is None
    if not inv or "slots" not in inv:
        # First-time init: geef iedereen een Basis Rugzak gratis
        slot_id = f"slot-{uuid.uuid4().hex[:8]}"
        item = dict(ITEM_CATALOG["backpack-basic"])
        slot = {
            "id": slot_id,
            "item_id": "backpack-basic",
            "acquired_at": datetime.now(timezone.utc).isoformat(),
            "source": "starter_pack",
            **item,
        }
        inv = {
            "user_id": user_id,
            "slots": [slot],
            "achievements": [],
        }
        save_json(fp, inv)

    # Refresh stats from users.json (live)
    xp = u.get("xp", 0)
    inv["stats"] = {
        "level": xp // 100,
        "xp": xp,
        "rang": u.get("rang", "Burger"),
        "gradatie": u.get("gradatie", 7),
        "trust": u.get("trust", 0),
        "naam": u.get("naam"),
        "achievements": inv.get("achievements", []),
        "is_bot": (user_id or "").startswith("bot-") or u.get("type") == "bot",
    }
    inv["capacity"] = _compute_capacity(inv.get("slots", []))
    return inv


# ============== MODELS ==============
class AddItemReq(BaseModel):
    item_id: str
    source: Optional[str] = "manual"
    naam: Optional[str] = None
    weight: Optional[float] = None
    capacity_bonus: Optional[int] = None
    weight_bonus: Optional[float] = None
    description: Optional[str] = None
    icon: Optional[str] = None


# ============== ROUTES ==============
@router.get("/{user_id}")
async def get_inventory(user_id: str):
    """Haal inventory + stats op voor user/bot."""
    return _load_or_init(user_id)


@router.get("/catalog/all")
async def get_catalog():
    """Lijst alle bekende items (ITEM_CATALOG)."""
    return {"items": [{"id": k, **v} for k, v in ITEM_CATALOG.items()]}


@router.post("/{user_id}/items")
async def add_item(user_id: str, req: AddItemReq):
    """Voeg item toe aan inventory (uit catalog of custom)."""
    inv = _load_or_init(user_id)
    slots = inv.get("slots", [])
    cap = _compute_capacity(slots)
    if cap["slots_used"] >= cap["slots_total"]:
        raise HTTPException(400, f"Inventory vol: {cap['slots_used']}/{cap['slots_total']} slots gebruikt")

    base = dict(ITEM_CATALOG.get(req.item_id, {}))
    if not base and not req.naam:
        raise HTTPException(404, f"Item '{req.item_id}' niet in catalog (geef custom naam mee)")
    # Custom overrides
    if req.naam:
        base["naam"] = req.naam
    if req.weight is not None:
        base["weight"] = req.weight
    if req.capacity_bonus is not None:
        base["capacity_bonus"] = req.capacity_bonus
    if req.weight_bonus is not None:
        base["weight_bonus"] = req.weight_bonus
    if req.description:
        base["description"] = req.description
    if req.icon:
        base["icon"] = req.icon

    proposed_weight = sum(s.get("weight", 0) for s in slots) + (base.get("weight") or 0)
    if proposed_weight > cap["weight_max"]:
        raise HTTPException(400, f"Te zwaar: {proposed_weight:.1f}kg > {cap['weight_max']:.1f}kg")

    slot = {
        "id": f"slot-{uuid.uuid4().hex[:8]}",
        "item_id": req.item_id,
        "acquired_at": datetime.now(timezone.utc).isoformat(),
        "source": req.source or "manual",
        **base,
    }
    slots.append(slot)
    inv["slots"] = slots
    fp = _inv_path(user_id)
    save_json(fp, {"user_id": user_id, "slots": slots, "achievements": inv.get("achievements", [])})
    return _load_or_init(user_id)


@router.delete("/{user_id}/items/{slot_id}")
async def remove_item(user_id: str, slot_id: str):
    """Verwijder slot."""
    inv = _load_or_init(user_id)
    slots = [s for s in inv.get("slots", []) if s.get("id") != slot_id]
    if len(slots) == len(inv.get("slots", [])):
        raise HTTPException(404, "Slot niet gevonden")
    fp = _inv_path(user_id)
    save_json(fp, {"user_id": user_id, "slots": slots, "achievements": inv.get("achievements", [])})
    return _load_or_init(user_id)


@router.post("/{user_id}/achievement")
async def add_achievement(user_id: str, body: dict):
    """v4_inventory_achievement_001 — registreer achievement + automatisch trofee in inventory."""
    code = (body.get("code") or "").strip()
    naam = (body.get("naam") or "").strip() or code
    if not code:
        raise HTTPException(400, "code is verplicht")
    inv = _load_or_init(user_id)
    achs = inv.get("achievements", [])
    if any(a.get("code") == code for a in achs):
        return {"ok": True, "already": True, "inventory": inv}
    ach = {
        "code": code,
        "naam": naam,
        "earned_at": datetime.now(timezone.utc).isoformat(),
        "source": body.get("source", "manual"),
    }
    achs.append(ach)
    fp = _inv_path(user_id)
    save_json(fp, {"user_id": user_id, "slots": inv.get("slots", []), "achievements": achs})
    return _load_or_init(user_id)
