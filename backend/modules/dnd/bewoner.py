"""
v6_bewoner_001 — NPC Bewoners in Spark World

Elke "Bewoner" is een NPC die in een gebouw woont/werkt in een stad.
Heeft eigen avatar (D&D-kaart), wallet, 8 inventory-slots (te koop), beroep, fractie.

Speler kan op bewoner-locatie:
- 8 vakjes zien wat HIJ verkoopt
- 8 vakjes hebben om JIJ erin te slepen (verkopen aan bewoner)

Opslag: /app/backend/data/dnd/bewoners/{bewoner_id}.json
Index:  /app/backend/data/dnd/bewoners/_index.json
"""
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..core.storage import load_json, save_json

router = APIRouter(prefix="/dnd/bewoners", tags=["dnd-bewoners"])

DATA_ROOT = Path(__file__).parent.parent.parent / "data"
BEWONERS_DIR = DATA_ROOT / "dnd" / "bewoners"
INDEX_FILE = BEWONERS_DIR / "_index.json"

BEWONER_INVENTORY_SLOTS = 8     # vaste 8 vakjes per bewoner
PLACEHOLDER_AVATAR_URL = "/api/avatar/gallery/31c6dc04a2fd/image"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_index() -> Dict[str, Any]:
    return load_json(INDEX_FILE, default={"bewoners": []})


def _save_index(data: Dict[str, Any]) -> None:
    BEWONERS_DIR.mkdir(parents=True, exist_ok=True)
    save_json(INDEX_FILE, data)


def _bewoner_path(bewoner_id: str) -> Path:
    BEWONERS_DIR.mkdir(parents=True, exist_ok=True)
    return BEWONERS_DIR / f"{bewoner_id}.json"


# ============== MODELS ==============
class BewonerCreate(BaseModel):
    naam: str
    beroep: str
    fractie_id: str = "spark"
    provincie_id: str = "groningen"
    hoofdstad: str = "Stormhaven"
    avatar_card_id: Optional[str] = None     # D&D-kaart van persoon (image)
    gebouw_card_id: Optional[str] = None     # D&D-kaart van gebouw (image)
    beschrijving: Optional[str] = ""
    start_goud: int = 50
    rang: Optional[str] = "Burger"


class BewonerPatch(BaseModel):
    naam: Optional[str] = None
    beroep: Optional[str] = None
    fractie_id: Optional[str] = None
    provincie_id: Optional[str] = None
    hoofdstad: Optional[str] = None
    avatar_card_id: Optional[str] = None
    gebouw_card_id: Optional[str] = None
    beschrijving: Optional[str] = None
    rang: Optional[str] = None
    wallet_goud: Optional[int] = None


class BewonerTradeReq(BaseModel):
    """Speler koopt slot N van bewoner OF verkoopt eigen slot aan bewoner."""
    user_id: str
    bewoner_slot_index: Optional[int] = None    # bij kopen
    user_slot_id: Optional[str] = None          # bij verkopen
    user_item_id: Optional[str] = None          # bij verkopen (fallback)


# ============== HELPERS ==============
def _load_bewoner(bewoner_id: str) -> Dict[str, Any]:
    fp = _bewoner_path(bewoner_id)
    b = load_json(fp, default={})
    if not b or "id" not in b:
        raise HTTPException(404, f"Bewoner {bewoner_id} niet gevonden")
    # Forward compat — zorg dat slots-array bestaat met juiste lengte
    slots = b.get("inventory_slots", [])
    while len(slots) < BEWONER_INVENTORY_SLOTS:
        slots.append(None)
    b["inventory_slots"] = slots[:BEWONER_INVENTORY_SLOTS]
    return b


def _save_bewoner(b: Dict[str, Any]) -> None:
    b["updated_at"] = _now()
    save_json(_bewoner_path(b["id"]), b)


def _index_upsert(b: Dict[str, Any]) -> None:
    """Bewaar minimale ref in index voor list-queries."""
    idx = _load_index()
    refs = idx.get("bewoners", [])
    ref = {
        "id": b["id"], "naam": b["naam"], "beroep": b.get("beroep"),
        "fractie_id": b.get("fractie_id"), "provincie_id": b.get("provincie_id"),
        "hoofdstad": b.get("hoofdstad"),
        "avatar_card_id": b.get("avatar_card_id"),
    }
    found = next((r for r in refs if r["id"] == b["id"]), None)
    if found:
        found.update(ref)
    else:
        refs.append(ref)
    idx["bewoners"] = refs
    _save_index(idx)


def _resolve_card_image(card_id: Optional[str]) -> Optional[str]:
    """Haal eerste image_url uit een D&D-kaart."""
    if not card_id:
        return None
    game_file = DATA_ROOT / "cards" / "dnd" / "game.json"
    data = load_json(game_file, default={"cards": []})
    for c in data.get("cards", []):
        if c.get("id") == card_id:
            imgs = (c.get("media") or {}).get("image_urls") or []
            return imgs[0] if imgs else None
    return None


# ============== ROUTES ==============
@router.get("/")
async def list_bewoners(
    provincie_id: Optional[str] = None,
    fractie_id: Optional[str] = None,
    hoofdstad: Optional[str] = None,
):
    """Lijst alle bewoners (uit index). Filters: provincie/fractie/stad."""
    idx = _load_index()
    refs = idx.get("bewoners", [])
    if provincie_id:
        refs = [r for r in refs if r.get("provincie_id") == provincie_id]
    if fractie_id:
        refs = [r for r in refs if r.get("fractie_id") == fractie_id]
    if hoofdstad:
        refs = [r for r in refs if (r.get("hoofdstad") or "").lower() == hoofdstad.lower()]
    # Verrijk met avatar-image
    for r in refs:
        r["avatar_url"] = _resolve_card_image(r.get("avatar_card_id")) or PLACEHOLDER_AVATAR_URL
    return {"success": True, "total": len(refs), "bewoners": refs}


@router.get("/{bewoner_id}")
async def get_bewoner(bewoner_id: str):
    """Haal volledige bewoner op (incl. inventory_slots + wallet)."""
    b = _load_bewoner(bewoner_id)
    b["avatar_url"] = _resolve_card_image(b.get("avatar_card_id")) or PLACEHOLDER_AVATAR_URL
    b["gebouw_url"] = _resolve_card_image(b.get("gebouw_card_id"))
    return b


@router.post("/")
async def create_bewoner(req: BewonerCreate):
    """Maak een nieuwe bewoner aan."""
    bid = f"bewoner-{uuid.uuid4().hex[:8]}"
    b = {
        "id": bid,
        "naam": req.naam,
        "beroep": req.beroep,
        "fractie_id": req.fractie_id,
        "provincie_id": req.provincie_id,
        "hoofdstad": req.hoofdstad,
        "avatar_card_id": req.avatar_card_id,
        "gebouw_card_id": req.gebouw_card_id,
        "beschrijving": req.beschrijving or "",
        "rang": req.rang or "Burger",
        "wallet": {"goud": int(req.start_goud), "gems": 0},
        "inventory_slots": [None] * BEWONER_INVENTORY_SLOTS,
        "created_at": _now(),
        "updated_at": _now(),
    }
    _save_bewoner(b)
    _index_upsert(b)
    return {"success": True, "bewoner": b}


@router.patch("/{bewoner_id}")
async def patch_bewoner(bewoner_id: str, req: BewonerPatch):
    b = _load_bewoner(bewoner_id)
    data = req.dict(exclude_none=True)
    if "wallet_goud" in data:
        b.setdefault("wallet", {"goud": 0, "gems": 0})
        b["wallet"]["goud"] = int(data.pop("wallet_goud"))
    b.update(data)
    _save_bewoner(b)
    _index_upsert(b)
    return b


@router.put("/{bewoner_id}/slot/{slot_index}")
async def set_bewoner_slot(bewoner_id: str, slot_index: int, item: Dict[str, Any]):
    """Plaats/wissel een item in slot N (admin/seed). item={item_id, naam, image_url, weight, value_goud, ...}"""
    if not (0 <= slot_index < BEWONER_INVENTORY_SLOTS):
        raise HTTPException(400, f"slot_index moet 0..{BEWONER_INVENTORY_SLOTS - 1}")
    b = _load_bewoner(bewoner_id)
    slots = b["inventory_slots"]
    slots[slot_index] = item if item else None
    b["inventory_slots"] = slots
    _save_bewoner(b)
    return b


@router.delete("/{bewoner_id}/slot/{slot_index}")
async def clear_bewoner_slot(bewoner_id: str, slot_index: int):
    if not (0 <= slot_index < BEWONER_INVENTORY_SLOTS):
        raise HTTPException(400, "slot_index out of range")
    b = _load_bewoner(bewoner_id)
    b["inventory_slots"][slot_index] = None
    _save_bewoner(b)
    return b


@router.delete("/{bewoner_id}")
async def delete_bewoner(bewoner_id: str):
    fp = _bewoner_path(bewoner_id)
    if fp.exists():
        fp.unlink()
    idx = _load_index()
    idx["bewoners"] = [r for r in idx.get("bewoners", []) if r.get("id") != bewoner_id]
    _save_index(idx)
    return {"success": True, "deleted": bewoner_id}


# ============== SEED ==============
@router.post("/seed")
async def seed_bewoners(user_id: str = "user-001"):
    """Seed minimale set bewoners gekoppeld aan bestaande persoon/gebouw D&D-kaarten."""
    game_file = DATA_ROOT / "cards" / "dnd" / "game.json"
    game_data = load_json(game_file, default={"cards": []})
    cards = game_data.get("cards", [])

    def _find_card(*keywords) -> Optional[str]:
        for kw in keywords:
            lkw = kw.lower()
            for c in cards:
                if (c.get("begrip") or "").lower().strip() == lkw:
                    return c.get("id")
            for c in cards:
                if lkw in (c.get("begrip") or "").lower():
                    return c.get("id")
        return None

    SEED = [
        {
            "naam": "Hans de Bakker", "beroep": "Bakker", "fractie_id": "spark",
            "provincie_id": "groningen", "hoofdstad": "Stormhaven",
            "avatar_hint": ["Bakker persoon"], "gebouw_hint": ["Bakker gebouw"],
            "beschrijving": "Verse broden uit de oven, elke morgen. Spreekt veel maar handelt eerlijk.",
            "start_goud": 80, "rang": "Burger",
        },
        {
            "naam": "Greta de Slager", "beroep": "Slager", "fractie_id": "spark",
            "provincie_id": "groningen", "hoofdstad": "Stormhaven",
            "avatar_hint": ["Slager"], "gebouw_hint": ["Slager gebouw"],
            "beschrijving": "Houdt van haar dieren maar weet wat het kost. Stevige vrouw, eerlijke prijzen.",
            "start_goud": 100, "rang": "Burger",
        },
        {
            "naam": "Oude Mira", "beroep": "Kruidenvrouw", "fractie_id": "natuur",
            "provincie_id": "groningen", "hoofdstad": "Stormhaven",
            "avatar_hint": ["The fortune teller", "fortune"], "gebouw_hint": ["Waterput"],
            "beschrijving": "Verkoopt kruiden, drankjes en raadgevingen. Soms juist wat je niet wilt horen.",
            "start_goud": 60, "rang": "Wijze",
        },
    ]

    idx = _load_index()
    existing_names = {r.get("naam", "").lower() for r in idx.get("bewoners", [])}
    created = []
    skipped = []
    for s in SEED:
        if s["naam"].lower() in existing_names:
            skipped.append(s["naam"])
            continue
        bid = f"bewoner-{uuid.uuid4().hex[:8]}"
        avatar_card = _find_card(*s["avatar_hint"])
        gebouw_card = _find_card(*s["gebouw_hint"])
        b = {
            "id": bid,
            "naam": s["naam"],
            "beroep": s["beroep"],
            "fractie_id": s["fractie_id"],
            "provincie_id": s["provincie_id"],
            "hoofdstad": s["hoofdstad"],
            "avatar_card_id": avatar_card,
            "gebouw_card_id": gebouw_card,
            "beschrijving": s["beschrijving"],
            "rang": s["rang"],
            "wallet": {"goud": s["start_goud"], "gems": 0},
            "inventory_slots": [None] * BEWONER_INVENTORY_SLOTS,
            "created_at": _now(),
            "updated_at": _now(),
        }
        _save_bewoner(b)
        _index_upsert(b)
        created.append({"id": bid, "naam": s["naam"], "avatar_card": avatar_card, "gebouw_card": gebouw_card})

    return {"success": True, "created_count": len(created), "skipped_count": len(skipped),
            "created": created, "skipped": skipped}


# ============== TRADE (eenvoudig) ==============
@router.post("/{bewoner_id}/buy")
async def buy_from_bewoner(bewoner_id: str, req: BewonerTradeReq):
    """Speler koopt slot N van de bewoner. Goud-transfer + item-move."""
    if req.bewoner_slot_index is None:
        raise HTTPException(400, "bewoner_slot_index verplicht")
    b = _load_bewoner(bewoner_id)
    if not (0 <= req.bewoner_slot_index < BEWONER_INVENTORY_SLOTS):
        raise HTTPException(400, "slot_index out of range")
    item = b["inventory_slots"][req.bewoner_slot_index]
    if not item:
        raise HTTPException(400, "Slot is leeg")
    price = int(item.get("value_goud", 0))

    # Update bewoner-wallet en slot
    b.setdefault("wallet", {"goud": 0, "gems": 0})
    b["wallet"]["goud"] = int(b["wallet"].get("goud", 0)) + price
    b["inventory_slots"][req.bewoner_slot_index] = None
    _save_bewoner(b)

    # Speler-character: aftrekken goud + voeg item toe in inventory
    char_file = DATA_ROOT / "dnd" / "characters" / f"{req.user_id}.json"
    char = load_json(char_file, default={})
    if not char.get("user_id"):
        raise HTTPException(404, "Speler-character niet gevonden")
    char.setdefault("currency", {"goud": 0, "gems": 0, "ziel": 0})
    char["currency"]["goud"] = int(char["currency"].get("goud", 0)) - price
    save_json(char_file, char)

    # Voeg item toe aan player inventory
    inv_file = DATA_ROOT / "users" / req.user_id / "inventory.json"
    inv = load_json(inv_file, default={"user_id": req.user_id, "slots": [], "achievements": []})
    slot = {
        "id": f"slot-{uuid.uuid4().hex[:8]}",
        "item_id": item.get("item_id"),
        "acquired_at": _now(),
        "source": f"buy:{bewoner_id}",
        "naam": item.get("naam"),
        "weight": item.get("weight", 0),
        "icon": item.get("icon", ""),
        "image_url": item.get("image_url"),
        "value_goud": item.get("value_goud", 0),
        "stats_bonus": item.get("stats_bonus", {}),
        "combat_bonus": item.get("combat_bonus", {}),
        "kind": item.get("kind", ""),
    }
    inv.setdefault("slots", []).append(slot)
    save_json(inv_file, inv)

    return {"success": True, "bought": item, "price": price, "buyer_goud_left": char["currency"]["goud"]}


@router.post("/{bewoner_id}/sell")
async def sell_to_bewoner(bewoner_id: str, req: BewonerTradeReq):
    """Speler verkoopt item uit eigen inventory aan bewoner. 50% van value_goud."""
    if not req.user_slot_id:
        raise HTTPException(400, "user_slot_id verplicht")
    inv_file = DATA_ROOT / "users" / req.user_id / "inventory.json"
    inv = load_json(inv_file, default={"user_id": req.user_id, "slots": [], "achievements": []})
    slots = inv.get("slots", [])
    slot = next((s for s in slots if s.get("id") == req.user_slot_id), None)
    if not slot:
        raise HTTPException(404, "Item niet in inventory")

    b = _load_bewoner(bewoner_id)
    # Vind eerste lege bewoner-slot
    free_idx = next((i for i, x in enumerate(b["inventory_slots"]) if x is None), None)
    if free_idx is None:
        raise HTTPException(400, f"{b['naam']} heeft geen plek meer (8/8 slots vol)")

    price = max(1, int(slot.get("value_goud", 0)) // 2)  # bewoner betaalt 50%
    b.setdefault("wallet", {"goud": 0, "gems": 0})
    if int(b["wallet"].get("goud", 0)) < price:
        raise HTTPException(400, f"{b['naam']} heeft niet genoeg goud ({b['wallet']['goud']}/{price})")

    # Move item
    bewoner_item = {
        "item_id": slot.get("item_id"),
        "naam": slot.get("naam"),
        "weight": slot.get("weight", 0),
        "icon": slot.get("icon", ""),
        "image_url": slot.get("image_url"),
        "value_goud": int(slot.get("value_goud", 0)),
        "stats_bonus": slot.get("stats_bonus", {}),
        "combat_bonus": slot.get("combat_bonus", {}),
        "kind": slot.get("kind", ""),
    }
    b["inventory_slots"][free_idx] = bewoner_item
    b["wallet"]["goud"] = int(b["wallet"]["goud"]) - price
    _save_bewoner(b)

    # Remove from player
    inv["slots"] = [s for s in slots if s.get("id") != req.user_slot_id]
    save_json(inv_file, inv)

    # Add goud to player
    char_file = DATA_ROOT / "dnd" / "characters" / f"{req.user_id}.json"
    char = load_json(char_file, default={})
    char.setdefault("currency", {"goud": 0, "gems": 0, "ziel": 0})
    char["currency"]["goud"] = int(char["currency"].get("goud", 0)) + price
    save_json(char_file, char)

    return {"success": True, "sold": bewoner_item, "price": price, "seller_goud": char["currency"]["goud"]}
