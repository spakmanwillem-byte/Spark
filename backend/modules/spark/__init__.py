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
    """Spark Bijbel: kernwaarden, normen, doelen, reactie voorbeelden.
    Auto-migratie: items zonder id krijgen een id zodat CRUD werkt."""
    data = load_json(BIJBEL_FILE, default={})
    changed = False
    for section in ("kernwaarden", "normen", "bijbel_items"):
        for item in data.get(section, []):
            if isinstance(item, dict) and not item.get("id"):
                item["id"] = uuid.uuid4().hex[:8]
                changed = True
    if changed:
        save_json(BIJBEL_FILE, data)
    return data


@router.get("/full")
async def get_full_profile():
    """Combined identity + bijbel for SparkBrainPage"""
    identity = load_json(DATA_DIR / "spark_identity.json", default={})
    bijbel = await get_bijbel()
    return {
        "identity": identity,
        "bijbel": bijbel,
    }


# ============================================================
# BIJBEL EDIT - kernwaarden / normen / bijbel_items / doelen
# ============================================================

# Velden per sectie (v4_011: ws5/lagen/tags/sterren toegevoegd voor chat-integratie)
SECTION_SCHEMAS = {
    "kernwaarden": {
        "id_field": "id",
        "keys": ["waarde", "beschrijving", "voorbeelden", "belangrijkheid", "ws5", "lagen", "tags"],
    },
    "normen": {
        "id_field": "id",
        "keys": ["norm", "beschrijving", "belangrijkheid", "voorbeelden", "ws5", "lagen", "tags"],
    },
    "bijbel_items": {
        "id_field": "id",
        "keys": ["naam", "beschrijving", "onderwerp", "belangrijkheid", "voorbeelden", "ws5", "lagen", "tags"],
    },
    "doelen": {"id_field": None, "keys": None},  # list of strings
}


_DEFAULT_WS5 = {"wie": "", "wat": "", "wanneer": "", "waar": "", "waarom": "", "hoe": ""}
_DEFAULT_LAGEN = {"laag1": "", "laag2": "", "laag3": "", "laag4": ""}


def _ensure_defaults(item: dict, schema_keys) -> dict:
    """Vul ws5/lagen/tags/belangrijkheid/voorbeelden defaults in als velden in schema."""
    if "ws5" in schema_keys and "ws5" not in item:
        item["ws5"] = dict(_DEFAULT_WS5)
    elif "ws5" in item and isinstance(item["ws5"], dict):
        # Merge zodat alle 6 keys bestaan
        item["ws5"] = {**_DEFAULT_WS5, **item["ws5"]}
    if "lagen" in schema_keys and "lagen" not in item:
        item["lagen"] = dict(_DEFAULT_LAGEN)
    elif "lagen" in item and isinstance(item["lagen"], dict):
        item["lagen"] = {**_DEFAULT_LAGEN, **item["lagen"]}
    if "tags" in schema_keys and "tags" not in item:
        item["tags"] = []
    if "voorbeelden" in schema_keys and "voorbeelden" not in item:
        item["voorbeelden"] = []
    if "belangrijkheid" in schema_keys and "belangrijkheid" not in item:
        item["belangrijkheid"] = 3
    return item


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
        item = _ensure_defaults(item, schema.get("keys") or [])
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
