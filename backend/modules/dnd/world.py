"""
Spark World Fracties & Provincies (v6_dnd_fracties_001)

9 fracties met element-alignment, en mapping op de 12 NL-provincies.

JSON: /app/backend/data/dnd/fracties.json (statisch, baseline)
JSON: /app/backend/data/dnd/provincies.json (provincie → fractie binding, editable)
"""
from pathlib import Path
from typing import Optional, List
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..core.storage import load_json, save_json

router = APIRouter(prefix="/dnd/world", tags=["dnd-world"])

DATA_ROOT = Path(__file__).parent.parent.parent / "data"
FRACTIES_FILE = DATA_ROOT / "dnd" / "fracties.json"
PROVINCIES_FILE = DATA_ROOT / "dnd" / "provincies.json"
USERS_FILE = DATA_ROOT / "system" / "users.json"

# v6_dnd_fracties_001 — 9 fracties, kleur + element + alignment
FRACTIES_BASELINE = [
    {"id": "spark",    "naam": "Spark",     "kleur": "#f59e0b", "element": "spark",   "alignment": "neutraal", "leider": "Spark",         "is_main": True,  "beschrijving": "De centrale fractie. Hoofdstad: Stormhaven."},
    {"id": "licht",    "naam": "Licht",     "kleur": "#fde68a", "element": "licht",   "alignment": "licht",    "leider": "—",             "is_main": False, "beschrijving": "Hoofd-fractie van het licht."},
    {"id": "schaduw",  "naam": "Schaduw",   "kleur": "#7c3aed", "element": "schaduw", "alignment": "schaduw",  "leider": "—",             "is_main": False, "beschrijving": "Hoofd-fractie van de schaduw."},
    {"id": "vuur",     "naam": "Vuur",      "kleur": "#dc2626", "element": "vuur",    "alignment": "licht",    "leider": "—",             "is_main": False, "beschrijving": "Element Vuur (Licht-aligned)."},
    {"id": "lucht",    "naam": "Lucht",     "kleur": "#06b6d4", "element": "lucht",   "alignment": "licht",    "leider": "—",             "is_main": False, "beschrijving": "Element Lucht (Licht-aligned)."},
    {"id": "water",    "naam": "Water",     "kleur": "#3b82f6", "element": "water",   "alignment": "schaduw",  "leider": "—",             "is_main": False, "beschrijving": "Element Water (Schaduw-aligned)."},
    {"id": "aarde",    "naam": "Aarde",     "kleur": "#78350f", "element": "aarde",   "alignment": "schaduw",  "leider": "—",             "is_main": False, "beschrijving": "Element Aarde (Schaduw-aligned)."},
    {"id": "natuur",   "naam": "Natuur",    "kleur": "#22c55e", "element": "natuur",  "alignment": "licht",    "leider": "—",             "is_main": False, "beschrijving": "Natuur (Licht-aligned, niet-element). Tegenpool van Barbaren."},
    {"id": "barbaren", "naam": "Barbaren",  "kleur": "#991b1b", "element": "barbaren","alignment": "schaduw",  "leider": "—",             "is_main": False, "beschrijving": "Barbaren (Schaduw-aligned, niet-element). Tegenpool van Natuur."},
    {"id": "neutraal", "naam": "Neutraal",  "kleur": "#94a3b8", "element": "—",       "alignment": "—",        "leider": "—",             "is_main": False, "beschrijving": "Veroverbare regio. Nog geen fractie geclaimd."},
]

# v6_dnd_provincies_001 — 12 provincies met default-mapping op fracties
# Groningen = Stormhaven = Spark (hoofdstad)
# Andere wijs ik symbolisch toe; admin kan herzien via drag-edit + fractie-pick
PROVINCIES_BASELINE = [
    {"id": "groningen",     "naam": "Groningen",     "hoofdstad": "Stormhaven",       "fractie_id": "spark",    "x_pct": 78, "y_pct": 18},
    {"id": "friesland",     "naam": "Friesland",     "hoofdstad": "Leeuwarden",       "fractie_id": "lucht",    "x_pct": 60, "y_pct": 22},
    {"id": "drenthe",       "naam": "Drenthe",       "hoofdstad": "Assen",            "fractie_id": "aarde",    "x_pct": 76, "y_pct": 32},
    {"id": "overijssel",    "naam": "Overijssel",    "hoofdstad": "Zwolle",           "fractie_id": "natuur",   "x_pct": 72, "y_pct": 44},
    {"id": "flevoland",     "naam": "Flevoland",     "hoofdstad": "Lelystad",         "fractie_id": "water",    "x_pct": 58, "y_pct": 42},
    {"id": "gelderland",    "naam": "Gelderland",    "hoofdstad": "Arnhem",           "fractie_id": "vuur",     "x_pct": 68, "y_pct": 55},
    {"id": "utrecht",       "naam": "Utrecht",       "hoofdstad": "Utrecht",          "fractie_id": "licht",    "x_pct": 55, "y_pct": 55},
    {"id": "noord-holland", "naam": "Noord-Holland", "hoofdstad": "Haarlem",          "fractie_id": "neutraal", "x_pct": 44, "y_pct": 40},
    {"id": "zuid-holland",  "naam": "Zuid-Holland",  "hoofdstad": "Den Haag",         "fractie_id": "neutraal", "x_pct": 42, "y_pct": 58},
    {"id": "zeeland",       "naam": "Zeeland",       "hoofdstad": "Middelburg",       "fractie_id": "neutraal", "x_pct": 38, "y_pct": 74},
    {"id": "noord-brabant", "naam": "Noord-Brabant", "hoofdstad": "'s-Hertogenbosch", "fractie_id": "schaduw",  "x_pct": 56, "y_pct": 76},
    {"id": "limburg",       "naam": "Limburg",       "hoofdstad": "Maastricht",       "fractie_id": "barbaren", "x_pct": 70, "y_pct": 88},
]

# v6_dnd_rarity_001 — WoW-style 5 rarity-tiers
RARITY_TIERS = [
    {"id": "common",    "naam": "Common",    "kleur": "#9ca3af", "spawn_pct": 60, "glow": "0 0 6px rgba(156,163,175,0.4)"},
    {"id": "uncommon",  "naam": "Uncommon",  "kleur": "#22c55e", "spawn_pct": 25, "glow": "0 0 8px rgba(34,197,94,0.5)"},
    {"id": "rare",      "naam": "Rare",      "kleur": "#3b82f6", "spawn_pct": 10, "glow": "0 0 10px rgba(59,130,246,0.6)"},
    {"id": "epic",      "naam": "Epic",      "kleur": "#a855f7", "spawn_pct": 4,  "glow": "0 0 14px rgba(168,85,247,0.7)"},
    {"id": "legendary", "naam": "Legendary", "kleur": "#f59e0b", "spawn_pct": 1,  "glow": "0 0 18px rgba(245,158,11,0.85)"},
]


def _is_admin(user_id: Optional[str]) -> bool:
    if not user_id:
        return False
    users = load_json(USERS_FILE, default={"users": []}).get("users", [])
    u = next((x for x in users if x.get("id") == user_id), None)
    return bool(u and (u.get("gradatie", 99) <= 2))


def _load_fracties() -> List[dict]:
    FRACTIES_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = load_json(FRACTIES_FILE, default={})
    if not data or "fracties" not in data:
        data = {"fracties": [dict(f) for f in FRACTIES_BASELINE]}
        save_json(FRACTIES_FILE, data)
    return data.get("fracties", [])


def _load_provincies() -> List[dict]:
    PROVINCIES_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = load_json(PROVINCIES_FILE, default={})
    if not data or "provincies" not in data:
        data = {"provincies": [dict(p) for p in PROVINCIES_BASELINE], "updated_at": None}
        save_json(PROVINCIES_FILE, data)
    return data.get("provincies", [])


# ===== MODELS =====
class ProvincieUpdate(BaseModel):
    id: str
    fractie_id: Optional[str] = None
    hoofdstad: Optional[str] = None
    x_pct: Optional[float] = None
    y_pct: Optional[float] = None


class ProvinciesPatch(BaseModel):
    user_id: str
    updates: List[ProvincieUpdate]


# ===== ROUTES =====
@router.get("/rarities")
async def get_rarities():
    return {"rarities": RARITY_TIERS}


@router.get("/fracties")
async def get_fracties():
    return {"fracties": _load_fracties()}


@router.get("/provincies")
async def get_provincies():
    return {"provincies": _load_provincies(), "fracties": _load_fracties()}


@router.patch("/provincies")
async def patch_provincies(req: ProvinciesPatch):
    """Admin: update fractie/coördinaten van één of meer provincies."""
    if not _is_admin(req.user_id):
        raise HTTPException(403, "Alleen admin kan provincies wijzigen")
    provincies = _load_provincies()
    by_id = {p["id"]: p for p in provincies}
    for upd in req.updates:
        if upd.id not in by_id:
            continue
        p = by_id[upd.id]
        if upd.fractie_id is not None:
            p["fractie_id"] = upd.fractie_id
        if upd.hoofdstad is not None:
            p["hoofdstad"] = upd.hoofdstad
        if upd.x_pct is not None:
            p["x_pct"] = float(upd.x_pct)
        if upd.y_pct is not None:
            p["y_pct"] = float(upd.y_pct)
    data = {
        "provincies": list(by_id.values()),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "updated_by": req.user_id,
    }
    save_json(PROVINCIES_FILE, data)
    return data


@router.post("/provincies/reset")
async def reset_provincies(req: dict):
    if not _is_admin(req.get("user_id")):
        raise HTTPException(403, "Alleen admin")
    data = {
        "provincies": [dict(p) for p in PROVINCIES_BASELINE],
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "updated_by": req.get("user_id"),
    }
    save_json(PROVINCIES_FILE, data)
    return data
