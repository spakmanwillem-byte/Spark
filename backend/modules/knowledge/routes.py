"""
Knowledge Routes - API endpoints voor kennisbank
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from .service import KnowledgeService

router = APIRouter(prefix="/knowledge", tags=["knowledge"])
service = KnowledgeService()


@router.get("/all")
async def get_all_knowledge(
    search: Optional[str] = Query(None),
    status_filter: Optional[str] = Query("all"),
    sort_by: Optional[str] = Query("recent"),
    importance: Optional[str] = Query("all"),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
):
    """Get all knowledge entries with search, filter, sort and pagination"""
    result = service.get_all(
        search=search,
        status_filter=status_filter,
        sort_by=sort_by,
        importance=importance,
        page=page,
        per_page=per_page,
    )
    return result


@router.get("/stats")
async def get_knowledge_stats():
    """Get knowledge base statistics"""
    return service.get_stats()


@router.get("/tags")
async def get_all_tags():
    """Get all unique tags"""
    return {"tags": service.get_all_tags()}


@router.get("/review/next")
async def get_next_review_entry(after_id: Optional[str] = Query(None)):
    """v4_019: pak volgende kaart voor de Review-flow.
    Nooit-gereviewd eerst, daarna langst-niet-gereviewd."""
    entry = service.get_next_review(after_id=after_id)
    if not entry:
        return {"entry": None, "message": "Geen kaarten meer om te reviewen."}
    return {"entry": entry}


@router.get("/exists")
async def check_begrip_exists(begrip: str = Query(..., min_length=1)):
    """v4_kb_create_001: exact-match check op begrip (case-insensitive).
    Retourneert {exists: bool, match: {id, begrip, topic} | null}."""
    match = service.exists_begrip(begrip)
    return {"exists": bool(match), "match": match}


@router.post("/create")
async def create_knowledge_entry(data: dict):
    """v4_kb_create_001: maak een nieuwe knowledge kaart aan.
    Body: {begrip (verplicht), topic, tags, lagen, ws5, belangrijkheid, kaart_type}.
    Faalt met 409 als begrip al bestaat."""
    entry, err = service.create_entry(data)
    if err == "begrip_required":
        raise HTTPException(status_code=400, detail="'begrip' is verplicht")
    if err == "duplicate":
        existing = service.exists_begrip(data.get("begrip"))
        raise HTTPException(
            status_code=409,
            detail={"message": "Begrip bestaat al", "match": existing},
        )
    return {"status": "ok", "entry": entry}


@router.get("/{entry_id}")
async def get_knowledge_entry(entry_id: str):
    """Get single knowledge entry by ID"""
    entry = service.get_by_id(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry niet gevonden")
    return entry


@router.put("/{entry_id}")
async def update_knowledge_entry(entry_id: str, data: dict):
    """Update a knowledge entry"""
    updated = service.update_entry(entry_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Entry niet gevonden")
    return {"status": "ok", "message": "Entry bijgewerkt"}


@router.delete("/{entry_id}")
async def delete_knowledge_entry(entry_id: str):
    """Delete a knowledge entry permanently"""
    deleted = service.delete_entry(entry_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Entry niet gevonden")
    return {"status": "ok", "message": "Entry verwijderd"}


@router.post("/{entry_id}/review")
async def mark_entry_reviewed(entry_id: str):
    """v4_019: registreer een review (zet reviewed_at + verhoog review_count)."""
    entry = service.mark_reviewed(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry niet gevonden")
    return {
        "status": "ok",
        "reviewed_at": (entry.get("metadata") or {}).get("reviewed_at"),
        "review_count": (entry.get("metadata") or {}).get("review_count"),
    }