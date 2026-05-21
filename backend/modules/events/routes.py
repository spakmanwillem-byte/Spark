"""
v5_event_overlay_001 — Event-overlay engine.

KB-kaart kan tijdelijk als overlay getoond worden in een chat-kanaal.
Polling-based: frontend vraagt elke X sec actieve events op per kanaal.
"""
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, Query
from pydantic import BaseModel

from modules.core.storage import load_json, save_json

router = APIRouter(prefix="/events", tags=["events"])

DATA = Path(__file__).parent.parent.parent / "data"
EVENTS_FILE = DATA / "system" / "active_events.json"
KB_FILE = DATA / "knowledge" / "learned_knowledge" / "knowledge_base.json"

VALID_TARGETS = {"community", "spark_feed", "spark_prive", "test"}


class TriggerEventRequest(BaseModel):
    card_id: str
    target: str = "community"   # community / spark_feed / spark_prive
    duration_ms: int = 8000     # standaard 8 sec
    fade_ms: int = 600
    triggered_by: Optional[str] = None
    note: Optional[str] = None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _now_ms() -> int:
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def _get_card(card_id: str) -> Optional[dict]:
    data = load_json(KB_FILE, default={"knowledge_entries": []})
    entries = data.get("knowledge_entries", [])
    return next((e for e in entries if e.get("id") == card_id), None)


@router.post("/trigger")
async def trigger_event(req: TriggerEventRequest):
    """Activeer een KB-kaart als overlay in een kanaal."""
    if req.target not in VALID_TARGETS:
        return {"success": False, "error": f"Target moet zijn: {sorted(VALID_TARGETS)}"}
    card = _get_card(req.card_id)
    if not card:
        return {"success": False, "error": f"Kaart {req.card_id} niet gevonden"}

    now_ms = _now_ms()
    event = {
        "id": f"evt-{uuid.uuid4().hex[:10]}",
        "card_id": req.card_id,
        "begrip": card.get("begrip"),
        "media": card.get("media") or {},
        "lagen_preview": card.get("lagen", {}).get("laag1", "")[:200],
        "target": req.target,
        "duration_ms": req.duration_ms,
        "fade_ms": req.fade_ms,
        "triggered_by": req.triggered_by,
        "note": req.note,
        "started_at_ms": now_ms,
        "expires_at_ms": now_ms + req.duration_ms,
        "created_at": _now(),
    }
    data = load_json(EVENTS_FILE, default={"events": []})
    data.setdefault("events", []).append(event)
    # Prune oud (> 1 uur)
    cutoff = now_ms - 3_600_000
    data["events"] = [e for e in data["events"] if e.get("expires_at_ms", 0) > cutoff]
    save_json(EVENTS_FILE, data)
    return {"success": True, "event": event}


@router.get("/active")
async def get_active_events(target: str = Query("community")):
    """Geef alle nog-niet-verlopen events terug voor een target."""
    if target not in VALID_TARGETS:
        return {"success": False, "error": "Invalid target"}
    data = load_json(EVENTS_FILE, default={"events": []})
    now_ms = _now_ms()
    active = [e for e in data.get("events", [])
              if e.get("target") == target and e.get("expires_at_ms", 0) > now_ms]
    return {"success": True, "events": active, "now_ms": now_ms}


@router.post("/clear")
async def clear_events(target: Optional[str] = None):
    """Admin: ruim alle (of per target) events op."""
    data = load_json(EVENTS_FILE, default={"events": []})
    before = len(data.get("events", []))
    if target:
        data["events"] = [e for e in data.get("events", []) if e.get("target") != target]
    else:
        data["events"] = []
    save_json(EVENTS_FILE, data)
    return {"success": True, "cleared": before - len(data["events"])}


@router.get("/sensory-cards")
async def list_sensory_cards():
    """Lijst alle KB-kaarten met media (voor event-trigger UI)."""
    data = load_json(KB_FILE, default={"knowledge_entries": []})
    rows = []
    for e in data.get("knowledge_entries", []):
        media = e.get("media")
        if media and (media.get("image_url") or media.get("sound_url")):
            rows.append({
                "id": e.get("id"),
                "begrip": e.get("begrip"),
                "preview": e.get("lagen", {}).get("laag1", "")[:120],
                "has_image": bool(media.get("image_url")),
                "has_sound": bool(media.get("sound_url")),
                "media": media,
            })
    return {"success": True, "cards": rows}
