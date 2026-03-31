"""
Dagboek & Agenda API Routes
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List
from services.dagboek_service import DagboekService
from services.agenda_service import AgendaService

router = APIRouter(tags=["personal"])


# Dagboek Models
class DagboekEntryCreate(BaseModel):
    user_id: str
    content: str
    mood: Optional[str] = None
    tags: Optional[List[str]] = None


class DagboekEntryUpdate(BaseModel):
    content: str
    mood: Optional[str] = None
    tags: Optional[List[str]] = None


# Agenda Models
class AgendaEventCreate(BaseModel):
    user_id: str
    titel: str
    date: str
    beschrijving: Optional[str] = None
    reminder: Optional[bool] = False


# Dagboek Routes
@router.post("/dagboek")
async def add_dagboek_entry(entry: DagboekEntryCreate):
    """Add dagboek entry"""
    result = DagboekService.add_entry(
        entry.user_id, 
        entry.content, 
        entry.mood, 
        entry.tags
    )
    return {"success": True, "entry": result}


@router.get("/dagboek/{user_id}")
async def get_dagboek_entries(
    user_id: str, 
    limit: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Get user's dagboek entries with optional filters"""
    entries = DagboekService.get_entries(user_id, limit, start_date, end_date)
    stats = DagboekService.get_stats(user_id)
    return {"entries": entries, "stats": stats}


@router.put("/dagboek/{entry_id}")
async def update_dagboek_entry(entry_id: str, user_id: str, update: DagboekEntryUpdate):
    """Update dagboek entry"""
    result = DagboekService.update_entry(
        user_id,
        entry_id,
        update.content,
        update.mood,
        update.tags
    )
    if result:
        return {"success": True, "entry": result}
    return {"success": False, "message": "Entry niet gevonden"}


@router.delete("/dagboek/{entry_id}")
async def delete_dagboek_entry(entry_id: str, user_id: str):
    """Delete dagboek entry"""
    success = DagboekService.delete_entry(user_id, entry_id)
    if success:
        return {"success": True, "message": "Entry verwijderd"}
    return {"success": False, "message": "Entry niet gevonden"}


@router.get("/dagboek/{user_id}/export")
async def export_dagboek(
    user_id: str,
    format: str = "txt",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Export dagboek entries as text or markdown"""
    content = DagboekService.export_entries(user_id, format, start_date, end_date)
    return {
        "success": True,
        "content": content,
        "format": format
    }


# Agenda Routes
@router.post("/agenda")
async def add_agenda_event(event: AgendaEventCreate):
    """Add agenda event"""
    result = AgendaService.add_event(
        event.user_id,
        event.titel,
        event.date,
        event.beschrijving,
        event.reminder
    )
    return {"success": True, "event": result}


@router.get("/agenda/{user_id}")
async def get_agenda_events(user_id: str, upcoming_only: bool = False):
    """Get user's agenda events"""
    events = AgendaService.get_events(user_id, upcoming_only)
    return {"events": events}


@router.get("/agenda/{user_id}/upcoming")
async def get_upcoming_events(user_id: str, limit: int = 5):
    """Get upcoming events"""
    events = AgendaService.get_upcoming(user_id, limit)
    return {"upcoming": events}




# NEW v3.3: Extended Profile & Agenda Routes
from services.profile_service import ProfileService

class ExtendedProfileUpdate(BaseModel):
    field_path: str  # e.g., "personal_info.contact.email"
    value: str


@router.get("/profile/extended/{user_id}")
async def get_extended_profile(user_id: str):
    """Get user's extended profile (v3.3)"""
    profile = ProfileService.get_profile(user_id)
    if not profile:
        return {"profile": ProfileService.get_empty_profile_structure()}
    return {"profile": profile}


@router.put("/profile/extended/{user_id}")
async def update_extended_profile(user_id: str, update: ExtendedProfileUpdate):
    """Update specific profile field"""
    success = ProfileService.update_profile_field(
        user_id,
        update.field_path,
        update.value
    )
    return {"success": success}


@router.get("/agenda/full/{user_id}")
async def get_full_agenda(user_id: str):
    """Get complete agenda (events + birthdays + recurring)"""
    agenda = AgendaService.get_full_agenda(user_id)
    if not agenda:
        return {"agenda": {"events": [], "family_birthdays": [], "recurring_events": []}}
    return {"agenda": agenda}


class EventCreate(BaseModel):
    title: str
    date: Optional[str] = None
    time: Optional[str] = None
    type: str = "other"
    notes: str = ""


class BirthdayCreate(BaseModel):
    naam: str
    relatie: str = ""
    datum: str  # "MM-DD" or "YYYY-MM-DD"
    jaar: Optional[int] = None
    herinnering: str = "1_week_voor"


@router.post("/agenda/{user_id}/event")
async def create_personal_agenda_event(user_id: str, event: EventCreate):
    """Add personal event to agenda"""
    event_id = AgendaService.add_personal_event(user_id, event.model_dump())
    return {"success": event_id is not None, "event_id": event_id}


@router.post("/agenda/{user_id}/birthday")
async def add_agenda_birthday(user_id: str, birthday: BirthdayCreate):
    """Add family birthday to agenda"""
    birthday_id = AgendaService.add_family_birthday(user_id, birthday.model_dump())
    return {"success": birthday_id is not None, "birthday_id": birthday_id}


@router.get("/agenda/{user_id}/pending")
async def get_pending_agenda_items(user_id: str):
    """Get pending agenda items (auto-detected, awaiting approval)"""
    from utils.data_manager import DataManager
    users_data = DataManager.load_json("system/users.json")
    users = users_data.get("users", [])
    user = next((u for u in users if u["id"] == user_id), None)
    
    if not user:
        return {"pending": []}
    
    return {"pending": user.get("pending_agenda_items", [])}


@router.post("/agenda/{user_id}/pending/{pending_id}/approve")
async def approve_pending_agenda_item(user_id: str, pending_id: str):
    """Approve pending agenda item"""
    success = AgendaService.approve_pending_item(user_id, pending_id)
    return {"success": success}


@router.delete("/agenda/{user_id}/pending/{pending_id}")
async def reject_pending_agenda_item(user_id: str, pending_id: str):
    """Reject/delete pending agenda item"""
    success = AgendaService.reject_pending_item(user_id, pending_id)
    return {"success": success}
