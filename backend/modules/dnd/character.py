"""
D&D Character Sheet (v6_dnd_character_sheet_001)

Stormhaven-stijl character sheet voor Spark World D&D-laag.

JSON Storage: /app/backend/data/dnd/characters/{user_id}.json
Per user 1 character. Idempotent first-load.

Schema:
{
  "user_id": "user-001",
  "titel": "De Nachtwacht",
  "ondertitel": "Zoeker van Waarheid",
  "rang_titel": "Kapitein",
  "rang_progress_pct": 68,
  "klasse": "",
  "beroep": "",
  "fractie": "",
  "locatie_naam": "Stormhaven",
  "dorp": "Stormhaven",
  "dorp_level": 2,
  "fog_of_war_pct": 32,
  "bio": "Een reiziger tussen werelden...",
  "currency": {"goud": 0, "gems": 0, "ziel": 0},
  "equipment": {                # slot_key -> {item_id, naam, icon, ...} of leeg
      "hoofd": null, "nek": null, "schouders": null, "armen": null,
      "trinket": null, "torso": null, "broek": null, "voeten": null,
      "sjaal": null, "riem": null, "handen": null, "ring_l": null,
      "ring_r": null, "rugzak": null, "linkerhand": null, "rechterhand": null,
      "offhand": null, "pijl_boog": null
  },
  "event_feed": [               # ringbuffer max 50
      {"ts": ISO, "kind": "SYSTEEM|WERELD|GUILD|VERHAAL|HANDEL", "text": "..."}
  ],
  "updated_at": ISO
}
"""
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..core.storage import load_json, save_json

router = APIRouter(prefix="/dnd/character", tags=["dnd-character"])

DATA_ROOT = Path(__file__).parent.parent.parent / "data"
CHARS_DIR = DATA_ROOT / "dnd" / "characters"
USERS_FILE = DATA_ROOT / "system" / "users.json"
EVENT_BUFFER_MAX = 50

SLOT_KEYS = [
    "hoofd", "nek", "schouders", "armen", "trinket", "torso", "broek",
    "voeten", "sjaal", "riem", "handen", "ring_l", "ring_r", "rugzak",
    "linkerhand", "rechterhand", "offhand", "pijl_boog",
]

SLOT_LABELS = {
    "hoofd": ("HOOFD", "Hoofdband"),
    "nek": ("NEK", "Ketting"),
    "schouders": ("SCHOUDERS", "Schouderbeschermer"),
    "armen": ("ARMEN", "Armband"),
    "trinket": ("TRINKET", "Medaillon"),
    "torso": ("TORSO", "T-shirt"),
    "broek": ("BROEK", "Broek"),
    "voeten": ("VOETEN", "Schoenen"),
    "sjaal": ("SJAAL", "Sjaal"),
    "riem": ("RIEM", "Riem"),
    "handen": ("HANDEN", "Handschoenen"),
    "ring_l": ("RING (L)", "Ring"),
    "ring_r": ("RING (R)", "Ring"),
    "rugzak": ("RUGZAK", "Rugzak"),
    "linkerhand": ("LINKERHAND", "Schild"),
    "rechterhand": ("RECHTERHAND", "Klein Zwaard"),
    "offhand": ("OFFHAND", "Lantaarn"),
    "pijl_boog": ("PIJL & BOOG", "Pijl en Boog"),
}

DEFAULT_CHARACTER = {
    "titel": "Naamloos",
    "ondertitel": "Zoeker",
    "rang_titel": "Burger",
    "rang_progress_pct": 0,
    "klasse": "",
    "beroep": "",
    "fractie": "",
    "locatie_naam": "Stormhaven",
    "dorp": "Stormhaven",
    "dorp_level": 1,
    "fog_of_war_pct": 0,
    "bio": "",
    "currency": {"goud": 0, "gems": 0, "ziel": 0},
}


# ============== HELPERS ==============
def _char_path(user_id: str) -> Path:
    CHARS_DIR.mkdir(parents=True, exist_ok=True)
    return CHARS_DIR / f"{user_id}.json"


def _get_user(user_id: str) -> Optional[dict]:
    data = load_json(USERS_FILE, default={"users": []})
    return next((u for u in data.get("users", []) if u.get("id") == user_id), None)


def _empty_equipment() -> Dict[str, Any]:
    return {k: None for k in SLOT_KEYS}


def _load_or_init(user_id: str) -> dict:
    u = _get_user(user_id)
    if not u:
        raise HTTPException(404, "User niet gevonden")
    fp = _char_path(user_id)
    ch = load_json(fp, default={})
    if not ch or "user_id" not in ch:
        ch = {
            "user_id": user_id,
            **DEFAULT_CHARACTER,
            "titel": u.get("naam") or "Naamloos",
            "ondertitel": "Zoeker",
            "rang_titel": u.get("rang") or "Burger",
            "equipment": _empty_equipment(),
            "event_feed": [
                {
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "kind": "SYSTEEM",
                    "text": f"Welkom in Spark Emergent, {u.get('naam') or 'reiziger'}!",
                }
            ],
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        save_json(fp, ch)

    # Ensure equipment schema complete (forward compat als slots toegevoegd worden)
    eq = ch.get("equipment") or {}
    for k in SLOT_KEYS:
        eq.setdefault(k, None)
    ch["equipment"] = eq

    # Derive stats live uit users.json + inventory
    xp = u.get("xp", 0) or 0
    level = xp // 100
    ch["derived"] = {
        "level": level,
        "xp": xp,
        "xp_in_level": xp % 100,
        "xp_per_level": 100,
        "rang": u.get("rang") or "Burger",
        "gradatie": u.get("gradatie", 7),
        "trust": u.get("trust", 0),
    }

    # Default placeholder stat-block (basis 10, kan later gemodificeerd worden)
    ch["statistieken"] = {
        "Kracht": 10, "Behendigheid": 10, "Intelligentie": 10,
        "Conditie": 10, "Wilskracht": 10, "Geluk": 10,
    }
    ch["aanval_verdediging"] = {
        "Aanvalskracht": 0, "Verdediging": 0, "Magie Kracht": 0,
        "Crit. Kans": 5, "Beweging": 100, "Initiatief": 0,
    }
    return ch


# ============== MODELS ==============
class CharacterPatch(BaseModel):
    titel: Optional[str] = None
    ondertitel: Optional[str] = None
    rang_titel: Optional[str] = None
    rang_progress_pct: Optional[int] = None
    klasse: Optional[str] = None
    beroep: Optional[str] = None
    fractie: Optional[str] = None
    locatie_naam: Optional[str] = None
    dorp: Optional[str] = None
    dorp_level: Optional[int] = None
    fog_of_war_pct: Optional[int] = None
    bio: Optional[str] = None
    currency: Optional[Dict[str, int]] = None


class EquipReq(BaseModel):
    slot_key: str
    item_id: Optional[str] = None
    naam: Optional[str] = None
    icon: Optional[str] = None


class EventReq(BaseModel):
    kind: str
    text: str


# ============== ROUTES ==============
@router.get("/slots/config")
async def get_slot_config():
    """Lijst van slot-keys + labels (voor UI rendering)."""
    return {
        "slots": [
            {"key": k, "label": SLOT_LABELS[k][0], "default_naam": SLOT_LABELS[k][1]}
            for k in SLOT_KEYS
        ]
    }


@router.get("/{user_id}")
async def get_character(user_id: str):
    """Haal het character sheet op."""
    return _load_or_init(user_id)


@router.patch("/{user_id}")
async def patch_character(user_id: str, patch: CharacterPatch):
    """Update meta velden (titel/rang/klasse/locatie/currency/bio)."""
    ch = _load_or_init(user_id)
    payload = patch.dict(exclude_none=True)
    # Currency merge
    if "currency" in payload:
        ch.setdefault("currency", {"goud": 0, "gems": 0, "ziel": 0})
        for k, v in (payload.pop("currency") or {}).items():
            ch["currency"][k] = int(v)
    ch.update(payload)
    ch["updated_at"] = datetime.now(timezone.utc).isoformat()
    save_json(_char_path(user_id), _strip_derived(ch))
    return _load_or_init(user_id)


@router.post("/{user_id}/equip")
async def equip_slot(user_id: str, req: EquipReq):
    """Equip een item in een specifiek slot (of leegmaken met item_id=null)."""
    if req.slot_key not in SLOT_KEYS:
        raise HTTPException(400, f"Onbekend slot: {req.slot_key}")
    ch = _load_or_init(user_id)
    eq = ch.get("equipment") or _empty_equipment()
    if not req.item_id and not req.naam:
        eq[req.slot_key] = None
    else:
        eq[req.slot_key] = {
            "item_id": req.item_id,
            "naam": req.naam or SLOT_LABELS[req.slot_key][1],
            "icon": req.icon or "",
            "equipped_at": datetime.now(timezone.utc).isoformat(),
        }
    ch["equipment"] = eq
    ch["updated_at"] = datetime.now(timezone.utc).isoformat()
    save_json(_char_path(user_id), _strip_derived(ch))
    return _load_or_init(user_id)


@router.post("/{user_id}/event")
async def push_event(user_id: str, req: EventReq):
    """Voeg een event toe aan de feed (ringbuffer max 50)."""
    valid_kinds = {"SYSTEEM", "WERELD", "GUILD", "VERHAAL", "HANDEL"}
    kind = (req.kind or "SYSTEEM").upper()
    if kind not in valid_kinds:
        raise HTTPException(400, f"Onbekende kind: {kind}")
    ch = _load_or_init(user_id)
    feed: List[dict] = ch.get("event_feed") or []
    feed.insert(0, {
        "ts": datetime.now(timezone.utc).isoformat(),
        "kind": kind,
        "text": (req.text or "").strip()[:300],
    })
    ch["event_feed"] = feed[:EVENT_BUFFER_MAX]
    ch["updated_at"] = datetime.now(timezone.utc).isoformat()
    save_json(_char_path(user_id), _strip_derived(ch))
    return _load_or_init(user_id)


def _strip_derived(ch: dict) -> dict:
    """Verwijder runtime-derived velden voor we naar disk schrijven."""
    out = dict(ch)
    out.pop("derived", None)
    out.pop("statistieken", None)
    out.pop("aanval_verdediging", None)
    return out
