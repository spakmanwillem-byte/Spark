"""
Agenda Routes - Events CRUD per user
Schema v1: {events: [{id, titel, beschrijving, date, reminder, status, created_at}]}

v13d_multi_module_privacy_001 (sessie 55) — Willem: "iedere user in eco-container".
GET/PATCH/DELETE endpoints eisen nu een `viewer_id` query-param die mag toegang
tot target user_id in de path. Owner en admin mogen; anders 403.
"""
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
from datetime import datetime, timezone
import uuid
from modules.core.storage import load_json, save_json
from modules.core.privacy import require_access

router = APIRouter(prefix="/agenda", tags=["agenda"])
DATA_DIR = Path(__file__).parent.parent.parent / "data" / "agenda"


# v13d_agenda_uren_registratie_001 (sessie 56b) — Willem: "kies privé/zakelijk,
# start/eind tijd, bij zakelijk pauze + opdrachtgever + onderwerp voor
# uren-registratie". Alle nieuwe velden optioneel voor backwards compat.
class EventCreate(BaseModel):
    titel: str
    beschrijving: Optional[str] = None
    date: str  # ISO datetime — geldt als start-tijd
    reminder: bool = False
    # Nieuwe velden (sessie 56b)
    scope: Optional[str] = "prive"  # 'prive' | 'zakelijk'
    end_date: Optional[str] = None  # ISO datetime — eind-tijd
    pauze_minuten: Optional[int] = None  # alleen bij zakelijk
    opdrachtgever: Optional[str] = None  # alleen bij zakelijk
    onderwerp: Optional[str] = None  # alleen bij zakelijk
    product_code: Optional[str] = None  # future-use bij zakelijk


class EventUpdate(BaseModel):
    titel: Optional[str] = None
    beschrijving: Optional[str] = None
    date: Optional[str] = None
    reminder: Optional[bool] = None
    status: Optional[str] = None
    scope: Optional[str] = None
    end_date: Optional[str] = None
    pauze_minuten: Optional[int] = None
    opdrachtgever: Optional[str] = None
    onderwerp: Optional[str] = None
    product_code: Optional[str] = None


def _compute_totaal_uren(start_iso: Optional[str], end_iso: Optional[str], pauze_min: Optional[int]) -> Optional[float]:
    """Bereken gewerkte uren = (end - start) - pauze. Return None als niet mogelijk."""
    if not start_iso or not end_iso:
        return None
    try:
        s = datetime.fromisoformat(start_iso.replace("Z", "+00:00"))
        e = datetime.fromisoformat(end_iso.replace("Z", "+00:00"))
        if e <= s:
            return None
        minuten = (e - s).total_seconds() / 60.0 - (pauze_min or 0)
        if minuten <= 0:
            return 0.0
        return round(minuten / 60.0, 2)
    except (ValueError, TypeError):
        return None


def _get_file(user_id: str) -> Path:
    return DATA_DIR / f"{user_id}.json"


@router.get("/events/{user_id}")
async def get_events(user_id: str, viewer_id: Optional[str] = Query(None)):
    # Backwards-compat: als viewer_id niet meegestuurd is, val terug op user_id
    # (zelfde user opvraag). Nieuwe frontends sturen viewer_id expliciet mee.
    require_access(viewer_id or user_id, user_id)
    data = load_json(_get_file(user_id), default={"events": []})
    return data


@router.post("/events/{user_id}")
async def create_event(user_id: str, event: EventCreate):
    filepath = _get_file(user_id)
    data = load_json(filepath, default={"events": []})
    scope = event.scope if event.scope in ("prive", "zakelijk") else "prive"
    totaal_uren = _compute_totaal_uren(event.date, event.end_date, event.pauze_minuten) if scope == "zakelijk" else None
    new_event = {
        "id": str(uuid.uuid4())[:8],
        "titel": event.titel,
        "beschrijving": event.beschrijving,
        "date": event.date,
        "reminder": event.reminder,
        "status": "upcoming",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "scope": scope,
        "end_date": event.end_date,
        "pauze_minuten": event.pauze_minuten if scope == "zakelijk" else None,
        "opdrachtgever": event.opdrachtgever if scope == "zakelijk" else None,
        "onderwerp": event.onderwerp if scope == "zakelijk" else None,
        "product_code": event.product_code if scope == "zakelijk" else None,
        "totaal_uren": totaal_uren,
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
            # Herbereken totaal_uren wanneer relevante velden zijn aangepast
            if ev.get("scope") == "zakelijk":
                ev["totaal_uren"] = _compute_totaal_uren(
                    ev.get("date"), ev.get("end_date"), ev.get("pauze_minuten")
                )
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



# v13_agenda_monthly_archive_001 (sessie 54) — Willem: op de 1e van elke maand
# oude events archiveren zodat de tab schoon blijft maar Spark de historie behoudt.
from . import archive_service as _archive


@router.get("/archive/{user_id}")
async def list_archive(user_id: str):
    """Lijst alle gearchiveerde maand-bestanden voor deze user. Elk bestand
    bevat de events van één afgelopen maand."""
    from pathlib import Path
    d = Path("/app/backend/data/users") / user_id / "archive" / "agenda_archief"
    if not d.exists():
        return {"user_id": user_id, "months": [], "total_events": 0}
    months = []
    total = 0
    for f in sorted(d.glob("agenda-*.json"), reverse=True):
        data = load_json(f, default={"events": []})
        n = len(data.get("events", []))
        total += n
        months.append({
            "month": data.get("month") or f.stem.replace("agenda-", ""),
            "filename": f.name,
            "event_count": n,
            "archived_at": data.get("archived_at"),
        })
    return {"user_id": user_id, "months": months, "total_events": total}


@router.get("/archive/{user_id}/{month}")
async def get_archived_month(user_id: str, month: str):
    """Alle events van een specifieke maand. `month` = YYYY-MM."""
    from pathlib import Path
    f = Path("/app/backend/data/users") / user_id / "archive" / "agenda_archief" / f"agenda-{month}.json"
    if not f.exists():
        return {"user_id": user_id, "month": month, "events": []}
    return load_json(f, default={"events": []})


@router.post("/archive-now")
async def archive_now_all():
    """Trigger handmatig het maand-archief voor alle users (override state).
    Normaal draait dit automatisch bij server-startup op de 1e van de maand."""
    return _archive.archive_now()


@router.post("/archive-now/{user_id}")
async def archive_now_user(user_id: str):
    """Trigger handmatig het maand-archief voor 1 user."""
    return _archive.archive_now(user_id)
