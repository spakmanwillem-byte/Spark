"""
Body Layout — sleepbare slot-posities over de lijf-avatar (v6_dnd_body_layout_001)

Per-slot x/y % posities die admin kan bewerken via drag-and-drop.
Shared layout (1× voor alle users); JSON: /app/backend/data/dnd/body_layout.json

Default-posities corresponderen ongeveer met de huidige 3-koloms layout
geprojecteerd op een 100×140 vlak met de goud-silhouet in het midden.
"""
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..core.storage import load_json, save_json

router = APIRouter(prefix="/dnd/body-layout", tags=["dnd-body-layout"])

DATA_ROOT = Path(__file__).parent.parent.parent / "data"
LAYOUT_FILE = DATA_ROOT / "dnd" / "body_layout.json"
USERS_FILE = DATA_ROOT / "system" / "users.json"

# Default-posities (x,y in %) tegen de body-avatar achtergrond.
# Linker-kolom (admin POV = rechts van de avatar) → 12..22%
# Rechter-kolom (admin POV = links van de avatar) → 78..88%
# Boven head: y ≈ 6%, voeten: y ≈ 94%
BODY_SLOTS_DEFAULT = [
    # Hoofd
    {"key": "hoofd",       "x": 50, "y": 8,  "label": "HOOFD",       "fallback": "Hoofdband"},
    # Linker-kolom (links op scherm)
    {"key": "linkerhand",  "x": 18, "y": 18, "label": "LINKERHAND",  "fallback": "Schild"},
    {"key": "offhand",     "x": 18, "y": 30, "label": "OFFHAND",     "fallback": "Lantaarn"},
    {"key": "pijl_boog",   "x": 18, "y": 42, "label": "PIJL & BOOG", "fallback": "Pijl en Boog"},
    {"key": "rugzak",      "x": 18, "y": 54, "label": "RUGZAK",      "fallback": "Rugzak"},
    {"key": "ring_l",      "x": 18, "y": 66, "label": "RING (L)",    "fallback": "Ring"},
    {"key": "riem",        "x": 18, "y": 78, "label": "RIEM",        "fallback": "Riem"},
    # Rechter-kolom (rechts op scherm)
    {"key": "nek",         "x": 82, "y": 18, "label": "NEK",         "fallback": "Ketting"},
    {"key": "schouders",   "x": 82, "y": 30, "label": "SCHOUDERS",   "fallback": "Schouderbeschermer"},
    {"key": "armen",       "x": 82, "y": 42, "label": "ARMEN",       "fallback": "Armband"},
    {"key": "trinket",     "x": 82, "y": 54, "label": "TRINKET",     "fallback": "Medaillon"},
    {"key": "sjaal",       "x": 82, "y": 66, "label": "SJAAL",       "fallback": "Sjaal"},
    {"key": "ring_r",      "x": 82, "y": 78, "label": "RING (R)",    "fallback": "Ring"},
    # Centrum (onder hoofd op silhouet)
    {"key": "torso",       "x": 50, "y": 36, "label": "TORSO",       "fallback": "T-shirt"},
    {"key": "handen",      "x": 50, "y": 52, "label": "HANDEN",      "fallback": "Handschoenen"},
    {"key": "broek",       "x": 50, "y": 66, "label": "BROEK",       "fallback": "Broek"},
    {"key": "rechterhand", "x": 35, "y": 60, "label": "RECHTERHAND", "fallback": "Klein Zwaard"},
    {"key": "voeten",      "x": 50, "y": 88, "label": "VOETEN",      "fallback": "Schoenen"},
]


def _is_admin(user_id: Optional[str]) -> bool:
    if not user_id:
        return False
    users = load_json(USERS_FILE, default={"users": []}).get("users", [])
    u = next((x for x in users if x.get("id") == user_id), None)
    return bool(u and (u.get("gradatie", 99) <= 2))


def _load() -> dict:
    LAYOUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = load_json(LAYOUT_FILE, default={})
    if not data or "slots" not in data:
        data = {"slots": [dict(s) for s in BODY_SLOTS_DEFAULT]}
        save_json(LAYOUT_FILE, data)
    return data


class SlotPos(BaseModel):
    key: str
    x: float
    y: float
    label: Optional[str] = None
    fallback: Optional[str] = None


class LayoutUpdate(BaseModel):
    user_id: str
    slots: List[SlotPos]


@router.get("")
async def get_layout():
    return _load()


@router.put("")
async def put_layout(req: LayoutUpdate):
    if not _is_admin(req.user_id):
        raise HTTPException(403, "Alleen admin (gradatie ≤ 2) kan body layout bewerken")
    current = _load().get("slots", [])
    by_key = {s["key"]: dict(s) for s in current}
    for s in req.slots:
        if s.key in by_key:
            by_key[s.key]["x"] = float(s.x)
            by_key[s.key]["y"] = float(s.y)
            if s.label is not None:
                by_key[s.key]["label"] = s.label
            if s.fallback is not None:
                by_key[s.key]["fallback"] = s.fallback
    data = {
        "slots": list(by_key.values()),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "updated_by": req.user_id,
    }
    save_json(LAYOUT_FILE, data)
    return data


@router.post("/reset")
async def reset_layout(req: dict):
    if not _is_admin(req.get("user_id")):
        raise HTTPException(403, "Alleen admin")
    data = {
        "slots": [dict(s) for s in BODY_SLOTS_DEFAULT],
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "updated_by": req.get("user_id"),
    }
    save_json(LAYOUT_FILE, data)
    return data
