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
import json
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


def _get_kracht(user_id: str) -> int:
    """Lees Kracht stat-value (base 10 + spent_points) uit de D&D-character JSON.

    Wordt gebruikt voor de carry-capacity formule (+0.5 kg per +1 Kracht).
    Returnt 10 als character-bestand niet bestaat.
    """
    fp = DATA_ROOT / "dnd" / "characters" / f"{user_id}.json"
    if not fp.exists():
        return 10
    try:
        ch = json.loads(fp.read_text(encoding="utf-8"))
        spent = (ch.get("stat_points_spent") or {}).get("Kracht", 0)
        return 10 + int(spent)
    except (json.JSONDecodeError, OSError, TypeError, ValueError):
        return 10


def _compute_capacity(slots: List[dict], kracht: int = 10) -> dict:
    """Bereken capacity uit slots + Kracht-bonus.

    v6_carry_capacity_001 — +0.5 kg per +1 Kracht boven base 10. Een Kracht-20 speler
    krijgt dus +5 kg, Kracht-100 → +45 kg extra draagkracht.
    """
    cap_bonus = sum(s.get("capacity_bonus", 0) for s in slots)
    weight_bonus = sum(s.get("weight_bonus", 0.0) for s in slots)
    weight_used = sum(s.get("weight", 0.0) for s in slots)
    kracht_bonus_kg = max(0, (kracht - 10)) * 0.5
    return {
        "slots_base": BASE_SLOTS,
        "slots_used": len(slots),
        "slots_total": BASE_SLOTS + cap_bonus,
        "weight_used": round(weight_used, 2),
        "weight_max": round(BASE_WEIGHT_MAX + weight_bonus + kracht_bonus_kg, 2),
        "kracht": kracht,
        "kracht_bonus_kg": round(kracht_bonus_kg, 2),
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
    inv["capacity"] = _compute_capacity(inv.get("slots", []), kracht=_get_kracht(user_id))
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
    """
    Lijst alle bekende items: D&D-kaarten met game_meta.is_item:true (PRIMAIR)
    + hardcoded ITEM_CATALOG (fallback voor items zonder kaart).
    Het D&D-kaart-systeem is dé bron-van-waarheid; deze endpoint unificeert ze.
    """
    items = []
    migrated_ids = set()  # hardcoded item_ids die al naar een D&D-kaart zijn gemigreerd

    # 1. D&D-kaarten met is_item=True (primaire bron)
    try:
        game_file = DATA_ROOT / "cards" / "dnd" / "game.json"
        game_data = load_json(game_file, default={"cards": []})
        for c in game_data.get("cards", []):
            gm = c.get("game_meta") or {}
            if not gm.get("is_item"):
                continue
            img_urls = (c.get("media") or {}).get("image_urls") or []
            items.append({
                "id": c.get("id"),
                "card_id": c.get("id"),
                "naam": c.get("begrip"),
                "kind": gm.get("kind") or "",
                "slot": gm.get("slot") or "",
                "weight": gm.get("weight", 0.0),
                "stats_bonus": gm.get("stats_bonus") or {},
                "combat_bonus": gm.get("combat_bonus") or {},
                "meta": gm.get("meta") or {},
                "value_goud": gm.get("value_goud", 0),
                "rarity": gm.get("rarity") or "common",
                "description": (c.get("lagen") or {}).get("laag1") or "",
                "tags": c.get("tags") or [],
                "image_url": img_urls[0] if img_urls else None,
                "source": "dnd_card",
            })
            # Onthoud welke hardcoded items al een D&D-kaart hebben
            mig_id = (c.get("footnote") or {}).get("item_migrated_from")
            if mig_id:
                migrated_ids.add(mig_id)
    except Exception:
        pass

    # 2. Hardcoded ITEM_CATALOG (fallback, alleen voor items zonder D&D-kaart)
    for k, v in ITEM_CATALOG.items():
        if k in migrated_ids:
            continue  # heeft al een D&D-kaart, dus skip
        items.append({"id": k, **v, "source": "hardcoded"})

    return {"items": items, "total": len(items)}


@router.post("/{user_id}/items")
async def add_item(user_id: str, req: AddItemReq):
    """Voeg item toe aan inventory (uit catalog of custom)."""
    inv = _load_or_init(user_id)
    slots = inv.get("slots", [])
    cap = _compute_capacity(slots, kracht=_get_kracht(user_id))
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



# ============== TRANSFER (v6_transfer_001) ==============
# Item-verplaatsen tussen containers (rugzak ↔ huis-opslag ↔ equipment-slot).
# Thuis-check: alleen wanneer character.locatie_naam == character.dorp.

class TransferReq(BaseModel):
    from_container: str       # "rugzak" | "huis" | "equipment:<slot_key>"
    to_container: str         # idem
    slot_id: Optional[str] = None       # bij rugzak/huis → slot.id
    equip_slot_key: Optional[str] = None # bij equipment → slot_key (hoofd/torso/...)
    item_payload: Optional[Dict] = None  # fallback voor equipment-naar-elders zonder slot_id


def _is_home(user_id: str) -> bool:
    """Check of speler thuis is (locatie_naam == dorp)."""
    char_fp = DATA_ROOT / "dnd" / "characters" / f"{user_id}.json"
    char = load_json(char_fp, default={})
    loc = (char.get("locatie_naam") or "").lower().strip()
    dorp = (char.get("dorp") or "").lower().strip()
    return bool(loc) and bool(dorp) and loc == dorp


@router.get("/{user_id}/is-home")
async def check_home(user_id: str):
    """Geef terug of speler thuis is (kan items verplaatsen tussen containers)."""
    return {"user_id": user_id, "is_home": _is_home(user_id)}


@router.post("/{user_id}/transfer")
async def transfer_item(user_id: str, req: TransferReq):
    """
    Verplaats item tussen containers.
    Restrictie: rugzak ↔ huis vereist 'thuis zijn' (locatie == dorp).
    Equipment ↔ rugzak mag altijd (kleren wisselen on the road).
    """
    fc = (req.from_container or "").lower()
    tc = (req.to_container or "").lower()
    if fc == tc:
        raise HTTPException(400, "from en to zijn gelijk")

    # Thuis-check voor verplaatsing waar 'huis' bij betrokken is
    needs_home = "huis" in fc or "huis" in tc
    if needs_home and not _is_home(user_id):
        raise HTTPException(403, "Niet thuis: ga eerst terug naar je dorp om je huis-opslag te gebruiken.")

    # NB: rugzak + huis delen momenteel hetzelfde inventory.slots (zelfde lijst).
    # Voor MVP: een item zit ofwel in rugzak (carried, telt voor kg) ofwel in huis (storage, geen kg).
    # We onderscheiden via slot.location: "rugzak" | "huis"
    inv = _load_or_init(user_id)
    slots = inv.get("slots", [])

    def _ensure_location(s, default="rugzak"):
        if not s.get("location"):
            s["location"] = default
        return s
    slots = [_ensure_location(s) for s in slots]

    # equipment-naar-rugzak/huis OR rugzak/huis-naar-equipment
    if fc.startswith("equipment:") or tc.startswith("equipment:"):
        char_fp = DATA_ROOT / "dnd" / "characters" / f"{user_id}.json"
        char = load_json(char_fp, default={})
        if not char.get("user_id"):
            raise HTTPException(404, "Character niet gevonden")
        eq = char.setdefault("equipment", {})

        if fc.startswith("equipment:"):
            slot_key = fc.split(":", 1)[1]
            equipped = eq.get(slot_key)
            if not equipped:
                raise HTTPException(400, f"Equipment slot {slot_key} is leeg")
            new_slot = {
                "id": f"slot-{uuid.uuid4().hex[:8]}",
                "item_id": equipped.get("item_id") or "custom",
                "acquired_at": datetime.now(timezone.utc).isoformat(),
                "source": f"unequip:{slot_key}",
                "naam": equipped.get("naam"),
                "icon": equipped.get("icon", ""),
                "image_url": equipped.get("image_url"),
                "weight": equipped.get("weight", 0),
                "value_goud": equipped.get("value_goud", 0),
                "stats_bonus": equipped.get("stats_bonus", {}),
                "combat_bonus": equipped.get("combat_bonus", {}),
                "kind": equipped.get("kind", ""),
                "location": tc,
            }
            slots.append(new_slot)
            eq[slot_key] = None
        else:
            slot_key = tc.split(":", 1)[1]
            slot = next((s for s in slots if s.get("id") == req.slot_id), None)
            if not slot:
                raise HTTPException(404, "Bron-item niet gevonden in inventory")
            eq[slot_key] = {
                "item_id": slot.get("item_id"),
                "naam": slot.get("naam"),
                "icon": slot.get("icon", ""),
                "image_url": slot.get("image_url"),
                "weight": slot.get("weight", 0),
                "value_goud": slot.get("value_goud", 0),
                "stats_bonus": slot.get("stats_bonus", {}),
                "combat_bonus": slot.get("combat_bonus", {}),
                "kind": slot.get("kind", ""),
                "equipped_at": datetime.now(timezone.utc).isoformat(),
            }
            slots = [s for s in slots if s.get("id") != req.slot_id]
        char["equipment"] = eq
        char["updated_at"] = datetime.now(timezone.utc).isoformat()
        save_json(char_fp, char)
    else:
        # Pure container move (rugzak ↔ huis): toggle slot.location
        slot = next((s for s in slots if s.get("id") == req.slot_id), None)
        if not slot:
            raise HTTPException(404, "Item niet in inventory")
        if fc not in {"rugzak", "huis"} or tc not in {"rugzak", "huis"}:
            raise HTTPException(400, "from/to moet 'rugzak' of 'huis' zijn")
        if (slot.get("location") or "rugzak") != fc:
            raise HTTPException(400, f"Item zit niet in {fc}")
        slot["location"] = tc

    fp = _inv_path(user_id)
    save_json(fp, {"user_id": user_id, "slots": slots, "achievements": inv.get("achievements", [])})
    return _load_or_init(user_id)
