"""v10_bijbel_semantic_layer_001 — Bijbel API routes."""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from . import service

router = APIRouter(prefix="/bijbel", tags=["bijbel"])


class AddEntryRequest(BaseModel):
    tekst: str
    type: str
    gerelateerde_begrippen: Optional[List[str]] = []
    bron: Optional[str] = "Willem"
    tags: Optional[List[str]] = []
    notities: Optional[str] = ""


class UpdateEntryRequest(BaseModel):
    tekst: Optional[str] = None
    type: Optional[str] = None
    gerelateerde_begrippen: Optional[List[str]] = None
    bron: Optional[str] = None
    tags: Optional[List[str]] = None
    notities: Optional[str] = None


@router.get("/list")
async def list_all(type: Optional[str] = None, begrip: Optional[str] = None):
    entries = service.list_entries(entry_type=type, begrip=begrip)
    return {"success": True, "entries": entries, "count": len(entries), "stats": service.stats()}


@router.get("/stats")
async def get_stats():
    return {"success": True, **service.stats()}


@router.get("/search")
async def search(q: str = Query(..., min_length=1), max_results: int = 10):
    return {"success": True, "query": q, "results": service.search_entries(q, max_results=max_results)}


@router.get("/by-begrip/{begrip}")
async def by_begrip(begrip: str):
    """Alle bijbel-entries die aan dit KB-begrip gekoppeld zijn."""
    entries = service.list_entries(begrip=begrip)
    return {"success": True, "begrip": begrip, "count": len(entries), "entries": entries}


@router.get("/{entry_id}")
async def get_one(entry_id: str):
    e = service.get_entry(entry_id)
    if not e:
        raise HTTPException(status_code=404, detail="Entry niet gevonden")
    return {"success": True, "entry": e}


@router.post("/add")
async def add(req: AddEntryRequest):
    result = service.add_entry(
        tekst=req.tekst,
        entry_type=req.type,
        gerelateerde_begrippen=req.gerelateerde_begrippen or [],
        bron=req.bron or "Willem",
        tags=req.tags or [],
        notities=req.notities or "",
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.patch("/{entry_id}")
async def update(entry_id: str, req: UpdateEntryRequest):
    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="Geen velden om te updaten")
    result = service.update_entry(entry_id, updates)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error"))
    return result


@router.delete("/{entry_id}")
async def delete(entry_id: str):
    result = service.delete_entry(entry_id)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error"))
    return result
