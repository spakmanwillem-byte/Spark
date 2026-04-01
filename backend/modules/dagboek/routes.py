"""
Dagboek Routes - Diary entries CRUD per user
Schema v1: {entries: [{id, content, mood, tags[], created_at, word_count}]}
Extended v1 also has: {id, datum, tijd, titel, inhoud, mood, tags[], created_at, word_count}
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List
from pathlib import Path
from datetime import datetime, timezone
import uuid
from modules.core.storage import load_json, save_json

router = APIRouter(prefix="/dagboek", tags=["dagboek"])
DATA_DIR = Path(__file__).parent.parent.parent / "data" / "dagboek"


class EntryCreate(BaseModel):
    content: str
    mood: str = "neutraal"
    tags: List[str] = []


class EntryUpdate(BaseModel):
    content: Optional[str] = None
    mood: Optional[str] = None
    tags: Optional[List[str]] = None


def _get_file(user_id: str) -> Path:
    return DATA_DIR / f"{user_id}.json"


@router.get("/entries/{user_id}")
async def get_entries(user_id: str):
    data = load_json(_get_file(user_id), default={"entries": []})
    return data


@router.post("/entries/{user_id}")
async def create_entry(user_id: str, entry: EntryCreate):
    filepath = _get_file(user_id)
    data = load_json(filepath, default={"entries": []})
    new_entry = {
        "id": str(uuid.uuid4())[:8],
        "content": entry.content,
        "mood": entry.mood,
        "tags": entry.tags,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "word_count": len(entry.content.strip().split()),
    }
    data["entries"].insert(0, new_entry)
    save_json(filepath, data)
    return {"success": True, "entry": new_entry}


@router.put("/entries/{user_id}/{entry_id}")
async def update_entry(user_id: str, entry_id: str, updates: EntryUpdate):
    filepath = _get_file(user_id)
    data = load_json(filepath, default={"entries": []})
    for e in data["entries"]:
        if e["id"] == entry_id:
            for k, v in updates.model_dump(exclude_none=True).items():
                e[k] = v
            if updates.content:
                e["word_count"] = len(updates.content.strip().split())
            save_json(filepath, data)
            return {"success": True, "entry": e}
    return {"success": False, "message": "Entry niet gevonden"}


@router.delete("/entries/{user_id}/{entry_id}")
async def delete_entry(user_id: str, entry_id: str):
    filepath = _get_file(user_id)
    data = load_json(filepath, default={"entries": []})
    before = len(data["entries"])
    data["entries"] = [e for e in data["entries"] if e["id"] != entry_id]
    if len(data["entries"]) < before:
        save_json(filepath, data)
        return {"success": True}
    return {"success": False, "message": "Entry niet gevonden"}
