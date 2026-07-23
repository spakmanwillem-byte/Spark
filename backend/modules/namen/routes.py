"""v6_namen_001 — Namen-lade API routes."""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from . import service

router = APIRouter(prefix="/namen", tags=["namen"])


class AddNameRequest(BaseModel):
    naam: str
    categorie: str
    bron: Optional[str] = "manueel"
    notities: Optional[str] = ""


class ClassifyRequest(BaseModel):
    naam: str
    auto_add: Optional[bool] = False


@router.get("/list")
async def list_all(categorie: Optional[str] = None):
    """Lijst alle namen, optioneel gefilterd."""
    return {"success": True, "namen": service.list_names(categorie=categorie), "stats": service.stats()}


@router.get("/stats")
async def get_stats():
    return {"success": True, **service.stats()}


@router.get("/search")
async def search(q: str = Query(..., min_length=1), max_results: int = 10):
    return {"success": True, "query": q, "results": service.search_names(q, max_results=max_results)}


@router.get("/{naam}")
async def get_one(naam: str):
    n = service.get_name(naam)
    if not n:
        raise HTTPException(status_code=404, detail=f"Naam '{naam}' niet gevonden")
    return {"success": True, "naam": n}


@router.post("/add")
async def add(req: AddNameRequest):
    result = service.add_name(req.naam, req.categorie, bron=req.bron or "manueel", notities=req.notities or "")
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@router.post("/classify")
async def classify(req: ClassifyRequest):
    """LLM-classify een naam. Optioneel auto_add=true om meteen op te slaan."""
    result = service.classify_via_llm(req.naam)
    if result.get("success") and req.auto_add:
        add_result = service.add_name(req.naam, result["categorie"], bron="llm_classify")
        result["opgeslagen"] = add_result
    return result


@router.delete("/{naam}")
async def delete(naam: str):
    result = service.delete_name(naam)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error"))
    return result
