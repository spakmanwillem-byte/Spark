"""
Notes API Routes - CRUD operations for user notes
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from services.notes_service import NotesService

router = APIRouter()


class NoteCreate(BaseModel):
    titel: str
    inhoud: str
    categorie: Optional[str] = "Algemeen"
    tags: Optional[List[str]] = []
    created_by: Optional[str] = "User"


class NoteUpdate(BaseModel):
    titel: Optional[str] = None
    inhoud: Optional[str] = None
    categorie: Optional[str] = None
    tags: Optional[List[str]] = None


@router.get("/notes")
async def get_all_notes(user_id: str, categorie: Optional[str] = None):
    """Get all notes for a user, optionally filtered by category"""
    notes = NotesService.get_all_notes(user_id, filter_category=categorie)
    stats = NotesService.get_categories_stats(user_id)
    
    return {
        "notes": notes,
        "total": len(notes),
        "stats": stats
    }


@router.get("/notes/{note_id}")
async def get_note(user_id: str, note_id: str):
    """Get a specific note"""
    note = NotesService.get_note_by_id(user_id, note_id)
    
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    return {"note": note}


@router.post("/notes")
async def create_note(user_id: str, note: NoteCreate):
    """Create a new note"""
    new_note = NotesService.add_note(
        user_id=user_id,
        titel=note.titel,
        inhoud=note.inhoud,
        categorie=note.categorie,
        tags=note.tags,
        created_by=note.created_by
    )
    
    return {"success": True, "note": new_note}


@router.put("/notes/{note_id}")
async def update_note(user_id: str, note_id: str, note: NoteUpdate):
    """Update an existing note"""
    updated = NotesService.update_note(
        user_id=user_id,
        note_id=note_id,
        titel=note.titel,
        inhoud=note.inhoud,
        categorie=note.categorie,
        tags=note.tags
    )
    
    if not updated:
        raise HTTPException(status_code=404, detail="Note not found")
    
    return {"success": True, "note": updated}


@router.delete("/notes/{note_id}")
async def delete_note(user_id: str, note_id: str):
    """Delete a note"""
    success = NotesService.delete_note(user_id, note_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Note not found")
    
    return {"success": True, "message": "Note deleted"}


@router.get("/notes/search/{query}")
async def search_notes(user_id: str, query: str):
    """Search notes"""
    results = NotesService.search_notes(user_id, query)
    
    return {
        "results": results,
        "count": len(results)
    }
