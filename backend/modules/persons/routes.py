"""
Persons Routes - Persoonskaarten (relatiebeheer)
Schema v1: {persons: [{id, naam, volledige_naam, relatie, gradatie, is_user, linked_user_id, tags[], notes, created_by, conversation_refs[], knowledge_refs[], created_at, updated_at}]}
Relationships: {user_id, relationships: [{person_name, user_id, relation_type, knows_about_me, i_know_about, notes}]}
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List
from pathlib import Path
from datetime import datetime, timezone
import uuid
from modules.core.storage import load_json, save_json

router = APIRouter(prefix="/persons", tags=["persons"])
DATA_DIR = Path(__file__).parent.parent.parent / "data" / "persons"


class PersonCreate(BaseModel):
    naam: str
    volledige_naam: Optional[str] = None
    relatie: Optional[str] = None
    gradatie: int = 5
    is_user: bool = False
    linked_user_id: Optional[str] = None
    tags: List[str] = []
    notes: str = ""


class PersonUpdate(BaseModel):
    naam: Optional[str] = None
    volledige_naam: Optional[str] = None
    relatie: Optional[str] = None
    gradatie: Optional[int] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None


# v6_body_slots_001 — D&D-style inventory voor persoonskaart
# 8 slots, geïnspireerd door D&D armor/inventory maar privacy-vriendelijk:
#   head / shoulders / chest / hands / waist / feet / aura / pocket
class BodySlotItem(BaseModel):
    label: str                              # bv. "Roadkill Cap"
    color: Optional[str] = None             # hex kleur voor visualisatie
    icon: Optional[str] = None              # emoji of lucide-naam
    note: Optional[str] = None              # vrije notitie


class BodySlotsUpdate(BaseModel):
    slots: dict  # {slot_id: BodySlotItem | None}  — None = leegmaken


VALID_SLOTS = {
    "head":      {"label": "Hoofd",     "icon": "🎩", "x": 50, "y": 8,  "desc": "Pet, helm, gedachten"},
    "shoulders": {"label": "Schouders", "icon": "🧥", "x": 50, "y": 22, "desc": "Jas, cape, last"},
    "chest":     {"label": "Borst",     "icon": "❤️", "x": 50, "y": 38, "desc": "Hart, drager"},
    "hands":     {"label": "Handen",    "icon": "🤲", "x": 18, "y": 50, "desc": "Tools, magie, sieraad"},
    "waist":     {"label": "Heupen",    "icon": "🔑", "x": 50, "y": 58, "desc": "Riem, sleutels"},
    "feet":      {"label": "Voeten",    "icon": "👟", "x": 50, "y": 90, "desc": "Schoenen, pad"},
    "aura":      {"label": "Aura",      "icon": "✨", "x": 82, "y": 50, "desc": "Energie, stemming"},
    "pocket":    {"label": "Zak",       "icon": "💼", "x": 50, "y": 72, "desc": "Geheim, draag-item"},
}


def _get_file(user_id: str) -> Path:
    return DATA_DIR / f"{user_id}.json"


def _get_rel_file(user_id: str) -> Path:
    return DATA_DIR / f"{user_id}_relationships.json"


@router.get("/cards/{user_id}")
async def get_person_cards(user_id: str, viewer_id: Optional[str] = None):
    # v13d_multi_module_privacy_001 — Persons/relaties per user beveiligd.
    from modules.core.privacy import require_access
    require_access(viewer_id or user_id, user_id)
    data = load_json(_get_file(user_id), default={"persons": [], "metadata": {}})
    return data


@router.post("/cards/{user_id}")
async def create_person(user_id: str, person: PersonCreate):
    filepath = _get_file(user_id)
    data = load_json(filepath, default={"persons": [], "metadata": {"user_id": user_id, "total_persons": 0}})
    now = datetime.now(timezone.utc).isoformat()
    new_person = {
        "id": f"person-{uuid.uuid4().hex[:8]}",
        "naam": person.naam,
        "volledige_naam": person.volledige_naam or person.naam,
        "relatie": person.relatie,
        "gradatie": person.gradatie,
        "is_user": person.is_user,
        "linked_user_id": person.linked_user_id,
        "tags": person.tags,
        "notes": person.notes,
        "created_by": user_id,
        "conversation_refs": [],
        "knowledge_refs": [],
        "created_at": now,
        "updated_at": now,
    }
    data["persons"].append(new_person)
    data["metadata"]["total_persons"] = len(data["persons"])
    data["metadata"]["last_updated"] = now
    save_json(filepath, data)
    return {"success": True, "person": new_person}


@router.put("/cards/{user_id}/{person_id}")
async def update_person(user_id: str, person_id: str, updates: PersonUpdate):
    filepath = _get_file(user_id)
    data = load_json(filepath, default={"persons": []})
    for p in data["persons"]:
        if p["id"] == person_id:
            for k, v in updates.model_dump(exclude_none=True).items():
                p[k] = v
            p["updated_at"] = datetime.now(timezone.utc).isoformat()
            save_json(filepath, data)
            return {"success": True, "person": p}
    return {"success": False, "message": "Persoon niet gevonden"}


@router.delete("/cards/{user_id}/{person_id}")
async def delete_person(user_id: str, person_id: str):
    filepath = _get_file(user_id)
    data = load_json(filepath, default={"persons": []})
    before = len(data["persons"])
    data["persons"] = [p for p in data["persons"] if p["id"] != person_id]
    if len(data["persons"]) < before:
        data["metadata"]["total_persons"] = len(data["persons"])
        data["metadata"]["last_updated"] = datetime.now(timezone.utc).isoformat()
        save_json(filepath, data)
        return {"success": True}
    return {"success": False, "message": "Persoon niet gevonden"}


@router.get("/relationships/{user_id}")
async def get_relationships(user_id: str):
    return load_json(_get_rel_file(user_id), default={"user_id": user_id, "relationships": []})


# v6_body_slots_001 — D&D-style body-slot inventaris per persoonskaart
@router.get("/body-slots/config")
async def get_body_slot_config():
    """Lijst van geldige slot-IDs met hun positie + label voor de UI."""
    return {"slots": VALID_SLOTS}


@router.put("/cards/{user_id}/{person_id}/body-slots")
async def update_body_slots(user_id: str, person_id: str, body: BodySlotsUpdate):
    """Vervang volledige body_slots map. Items=None verwijderen het slot."""
    filepath = _get_file(user_id)
    data = load_json(filepath, default={"persons": []})
    for p in data["persons"]:
        if p["id"] != person_id:
            continue
        cur = p.get("body_slots") or {}
        for slot_id, item in (body.slots or {}).items():
            if slot_id not in VALID_SLOTS:
                continue  # negeer onbekende slots
            if item is None:
                cur.pop(slot_id, None)
            else:
                # Sanitize: alleen velden uit BodySlotItem opslaan
                cur[slot_id] = {
                    "label": (item.get("label") or "").strip(),
                    "color": item.get("color"),
                    "icon": item.get("icon"),
                    "note": (item.get("note") or "").strip() or None,
                    "ts": datetime.now(timezone.utc).isoformat(),
                }
        p["body_slots"] = cur
        p["updated_at"] = datetime.now(timezone.utc).isoformat()
        save_json(filepath, data)
        return {"success": True, "body_slots": cur}
    return {"success": False, "message": "Persoon niet gevonden"}


@router.delete("/cards/{user_id}/{person_id}/body-slots/{slot_id}")
async def clear_body_slot(user_id: str, person_id: str, slot_id: str):
    """Maak één specifiek slot leeg."""
    if slot_id not in VALID_SLOTS:
        return {"success": False, "message": f"Onbekend slot: {slot_id}"}
    filepath = _get_file(user_id)
    data = load_json(filepath, default={"persons": []})
    for p in data["persons"]:
        if p["id"] != person_id:
            continue
        slots = p.get("body_slots") or {}
        if slot_id in slots:
            del slots[slot_id]
            p["body_slots"] = slots
            p["updated_at"] = datetime.now(timezone.utc).isoformat()
            save_json(filepath, data)
            return {"success": True, "body_slots": slots}
        return {"success": True, "body_slots": slots, "noop": True}
    return {"success": False, "message": "Persoon niet gevonden"}
