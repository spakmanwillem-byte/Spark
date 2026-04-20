"""
Spark Core Routes - Identity, Bijbel, Personality
Serves Spark's identity, kernwaarden, normen, doelen, reactie voorbeelden
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Any
from pathlib import Path
from datetime import datetime
import uuid
from modules.core.storage import load_json, save_json

router = APIRouter(prefix="/spark", tags=["spark"])
DATA_DIR = Path(__file__).parent.parent.parent / "data" / "personality"
BIJBEL_FILE = DATA_DIR / "spark_bijbel.json"


@router.get("/identity")
async def get_identity():
    """Spark's core identity"""
    return load_json(DATA_DIR / "spark_identity.json", default={})


@router.get("/bijbel")
async def get_bijbel():
    """Spark Bijbel: kernwaarden, normen, doelen, reactie voorbeelden"""
    return load_json(BIJBEL_FILE, default={})


@router.get("/full")
async def get_full_profile():
    """Combined identity + bijbel for SparkBrainPage"""
    identity = load_json(DATA_DIR / "spark_identity.json", default={})
    bijbel = load_json(BIJBEL_FILE, default={})
    return {
        "identity": identity,
        "bijbel": bijbel,
    }


# ============================================================
# BIJBEL EDIT - kernwaarden / normen / bijbel_items / doelen
# ============================================================

# Velden per sectie
SECTION_SCHEMAS = {
    "kernwaarden": {"id_field": None, "keys": ["waarde", "beschrijving", "voorbeelden"]},
    "normen": {"id_field": "id", "keys": ["norm", "beschrijving", "belangrijkheid", "voorbeelden"]},
    "bijbel_items": {"id_field": "id", "keys": ["naam", "beschrijving", "onderwerp"]},
    "doelen": {"id_field": None, "keys": None},  # list of strings
}


class BijbelItem(BaseModel):
    data: dict = {}
    value: Optional[Any] = None  # voor doelen (plain string)


def _ensure_id(item: dict) -> dict:
    """Voeg id + timestamp toe indien ontbreekt."""
    if "id" not in item:
        item["id"] = uuid.uuid4().hex[:8]
    if "toegevoegd_op" not in item:
        item["toegevoegd_op"] = datetime.now().isoformat()
    return item


@router.post("/bijbel/{section}")
async def add_bijbel_item(section: str, body: BijbelItem):
    """Voeg item toe aan kernwaarden/normen/bijbel_items/doelen."""
    if section not in SECTION_SCHEMAS:
        raise HTTPException(400, f"Onbekende sectie: {section}")
    data = load_json(BIJBEL_FILE, default={})
    items = data.get(section, [])
    schema = SECTION_SCHEMAS[section]

    if section == "doelen":
        new_item = body.value or body.data.get("value", "")
        if not new_item:
            raise HTTPException(400, "Doel mag niet leeg zijn")
        items.append(new_item)
    else:
        item = dict(body.data)
        if schema["id_field"]:
            item = _ensure_id(item)
        items.append(item)

    data[section] = items
    # Update metadata
    data.setdefault("metadata", {})["last_updated"] = datetime.now().isoformat()
    save_json(BIJBEL_FILE, data)
    return {"success": True, "section": section, "total": len(items), "item": items[-1]}


@router.put("/bijbel/{section}/{identifier}")
async def update_bijbel_item(section: str, identifier: str, body: BijbelItem):
    """
    Update een item.
    - Voor kernwaarden/doelen: identifier = index (string representation)
    - Voor normen/bijbel_items: identifier = id
    """
    if section not in SECTION_SCHEMAS:
        raise HTTPException(400, f"Onbekende sectie: {section}")
    data = load_json(BIJBEL_FILE, default={})
    items = data.get(section, [])
    schema = SECTION_SCHEMAS[section]

    found = False
    if schema["id_field"]:
        for i, item in enumerate(items):
            if str(item.get(schema["id_field"])) == identifier:
                items[i] = {**item, **body.data}
                items[i][schema["id_field"]] = identifier  # behoud id
                items[i]["last_updated"] = datetime.now().isoformat()
                found = True
                break
    else:
        try:
            idx = int(identifier)
            if 0 <= idx < len(items):
                if section == "doelen":
                    items[idx] = body.value or body.data.get("value", items[idx])
                else:
                    items[idx] = {**items[idx], **body.data} if isinstance(items[idx], dict) else body.data
                found = True
        except ValueError:
            pass

    if not found:
        raise HTTPException(404, f"Item '{identifier}' niet gevonden in {section}")

    data[section] = items
    data.setdefault("metadata", {})["last_updated"] = datetime.now().isoformat()
    save_json(BIJBEL_FILE, data)
    return {"success": True, "section": section, "identifier": identifier}


@router.delete("/bijbel/{section}/{identifier}")
async def delete_bijbel_item(section: str, identifier: str):
    """Verwijder item uit sectie."""
    if section not in SECTION_SCHEMAS:
        raise HTTPException(400, f"Onbekende sectie: {section}")
    data = load_json(BIJBEL_FILE, default={})
    items = data.get(section, [])
    schema = SECTION_SCHEMAS[section]
    before = len(items)

    if schema["id_field"]:
        items = [i for i in items if str(i.get(schema["id_field"])) != identifier]
    else:
        try:
            idx = int(identifier)
            if 0 <= idx < len(items):
                items.pop(idx)
        except ValueError:
            pass

    if len(items) == before:
        raise HTTPException(404, f"Item '{identifier}' niet gevonden")
    data[section] = items
    data.setdefault("metadata", {})["last_updated"] = datetime.now().isoformat()
    save_json(BIJBEL_FILE, data)
    return {"success": True, "section": section, "remaining": len(items)}
