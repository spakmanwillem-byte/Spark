from typing import List, Dict, Optional
from utils.data_manager import DataManager
from models.diary import DiaryEntry, DiaryCreate

class DiaryService:
    @staticmethod
    def add_diary_entry(user_id: str, sleutelwoord: str, diary_create: DiaryCreate) -> DiaryEntry:
        """
        Add diary entry for user
        """
        entries = DataManager.load_diary(user_id, sleutelwoord)
        
        # Create new entry
        new_entry = DiaryEntry(
            user_id=user_id,
            content=diary_create.content,
            mood=diary_create.mood
        )
        
        entries.append(new_entry.model_dump())
        DataManager.save_diary(user_id, sleutelwoord, entries)
        
        return new_entry
    
    @staticmethod
    def get_diary_entries(user_id: str, sleutelwoord: str, limit: Optional[int] = None) -> List[Dict]:
        """
        Get diary entries for user
        """
        entries = DataManager.load_diary(user_id, sleutelwoord)
        
        # Sort by timestamp (newest first)
        entries.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        if limit:
            return entries[:limit]
        
        return entries
