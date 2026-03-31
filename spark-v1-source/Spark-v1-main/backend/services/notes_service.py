"""
Notes Service - Manages user's notes, ideas and observations
"""
from typing import List, Dict, Optional
from datetime import datetime
from utils.data_manager import DataManager
import uuid


class NotesService:
    """Service for managing notes per user"""
    
    @staticmethod
    def _get_user_notes_path(user_id: str) -> str:
        return f"users/{user_id}/notes.json"
    
    @staticmethod
    def get_all_notes(user_id: str, filter_category: Optional[str] = None) -> List[Dict]:
        """Get all notes for a user, optionally filtered by category"""
        try:
            data = DataManager.load_data(NotesService._get_user_notes_path(user_id))
            notes = data.get("notes", [])
        except:
            return []
        
        if filter_category:
            notes = [n for n in notes if n.get("categorie") == filter_category]
        
        # Sort by date, newest first
        notes.sort(key=lambda x: x.get("datum", ""), reverse=True)
        return notes
    
    @staticmethod
    def get_note_by_id(user_id: str, note_id: str) -> Optional[Dict]:
        """Get a specific note by ID"""
        try:
            data = DataManager.load_data(NotesService._get_user_notes_path(user_id))
            notes = data.get("notes", [])
            
            for note in notes:
                if note.get("id") == note_id:
                    return note
        except:
            pass
        return None
    
    @staticmethod
    def add_note(user_id: str, titel: str, inhoud: str, categorie: str = "Algemeen", 
                 tags: List[str] = None, created_by: str = "User") -> Dict:
        """Add a new note"""
        try:
            data = DataManager.load_data(NotesService._get_user_notes_path(user_id))
        except:
            # Create new notes file for user
            data = {
                "user_id": user_id,
                "notes": [],
                "created_at": datetime.now().isoformat()
            }
        
        if "notes" not in data:
            data["notes"] = []
        
        new_note = {
            "id": str(uuid.uuid4())[:8],
            "titel": titel,
            "inhoud": inhoud,
            "categorie": categorie,
            "tags": tags or [],
            "datum": datetime.now().isoformat(),
            "created_by": created_by,
            "updated_at": None
        }
        
        data["notes"].append(new_note)
        DataManager.save_data(NotesService._get_user_notes_path(user_id), data)
        
        return new_note
    
    @staticmethod
    def update_note(user_id: str, note_id: str, titel: Optional[str] = None, 
                   inhoud: Optional[str] = None, categorie: Optional[str] = None,
                   tags: Optional[List[str]] = None) -> Optional[Dict]:
        """Update an existing note"""
        try:
            data = DataManager.load_data(NotesService._get_user_notes_path(user_id))
            notes = data.get("notes", [])
            
            for note in notes:
                if note.get("id") == note_id:
                    if titel is not None:
                        note["titel"] = titel
                    if inhoud is not None:
                        note["inhoud"] = inhoud
                    if categorie is not None:
                        note["categorie"] = categorie
                    if tags is not None:
                        note["tags"] = tags
                    
                    note["updated_at"] = datetime.now().isoformat()
                    
                    DataManager.save_data(NotesService._get_user_notes_path(user_id), data)
                    return note
        except:
            pass
        
        return None
    
    @staticmethod
    def delete_note(user_id: str, note_id: str) -> bool:
        """Delete a note permanently"""
        try:
            data = DataManager.load_data(NotesService._get_user_notes_path(user_id))
            notes = data.get("notes", [])
            
            initial_count = len(notes)
            data["notes"] = [n for n in notes if n.get("id") != note_id]
            
            if len(data["notes"]) < initial_count:
                DataManager.save_data(NotesService._get_user_notes_path(user_id), data)
                return True
        except:
            pass
        
        return False
    
    @staticmethod
    def search_notes(user_id: str, query: str) -> List[Dict]:
        """Search notes by titel or inhoud"""
        try:
            data = DataManager.load_data(NotesService._get_user_notes_path(user_id))
            notes = data.get("notes", [])
            query_lower = query.lower()
            
            results = [
                note for note in notes
                if query_lower in note.get("titel", "").lower() or
                   query_lower in note.get("inhoud", "").lower()
            ]
            
            return results
        except:
            return []
    
    @staticmethod
    def get_categories_stats(user_id: str) -> Dict:
        """Get statistics per category for a user"""
        try:
            data = DataManager.load_data(NotesService._get_user_notes_path(user_id))
            notes = data.get("notes", [])
        except:
            notes = []
        
        stats = {
            "Inzicht": 0,
            "Patroon": 0,
            "Observatie": 0,
            "TODO": 0,
            "Algemeen": 0
        }
        
        for note in notes:
            cat = note.get("categorie", "Algemeen")
            if cat in stats:
                stats[cat] += 1
            else:
                stats["Algemeen"] += 1
        
        return stats
