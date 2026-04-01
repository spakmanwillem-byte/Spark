"""
Agenda Routes - Events CRUD per user
Schema v1: {events: [{id, titel, beschrijving, date, reminder, status, created_at}]}
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
from datetime import datetime, timezone
import uuid
from modules.core.storage import load_json, save_json

router = APIRouter(prefix="/agenda", tags=["agenda"])
DATA_DIR = Path(__file__).parent.parent.parent / "data" / "agenda"


class EventCreate(BaseModel):
    titel: str
    beschrijving: Optional[str] = None
    date: str
    reminder: bool = False


class EventUpdate(BaseModel):
    titel: Optional[str] = None
    beschrijving: Optional[str] = None
    date: Optional[str] = None
    reminder: Optional[bool] = None
    status: Optional[str] = None


def _get_file(user_id: str) -> Path:
    return DATA_DIR / f"{user_id}.json"


@router.get("/events/{user_id}")
async def get_events(user_id: str):
    data = load_json(_get_file(user_id), default={"events": []})
    return data


@router.post("/events/{user_id}")
async def create_event(user_id: str, event: EventCreate):
    filepath = _get_file(user_id)
    data = load_json(filepath, default={"events": []})
    new_event = {
        "id": str(uuid.uuid4())[:8],
        "titel": event.titel,
        "beschrijving": event.beschrijving,
        "date": event.date,
        "reminder": event.reminder,
        "status": "upcoming",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    data["events"].append(new_event)
    save_json(filepath, data)
    return {"success": True, "event": new_event}


@router.put("/events/{user_id}/{event_id}")
async def update_event(user_id: str, event_id: str, updates: EventUpdate):
    filepath = _get_file(user_id)
    data = load_json(filepath, default={"events": []})
    for ev in data["events"]:
        if ev["id"] == event_id:
            for k, v in updates.model_dump(exclude_none=True).items():
                ev[k] = v
            save_json(filepath, data)
            return {"success": True, "event": ev}
    return {"success": False, "message": "Event niet gevonden"}


@router.delete("/events/{user_id}/{event_id}")
async def delete_event(user_id: str, event_id: str):
    filepath = _get_file(user_id)
    data = load_json(filepath, default={"events": []})
    before = len(data["events"])
    data["events"] = [e for e in data["events"] if e["id"] != event_id]
    if len(data["events"]) < before:
        save_json(filepath, data)
        return {"success": True}
    return {"success": False, "message": "Event niet gevonden"}
