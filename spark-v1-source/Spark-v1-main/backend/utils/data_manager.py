import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

DATA_DIR = Path(__file__).parent.parent / "data"

class DataManager:
    @staticmethod
    def load_json(filepath: str) -> Dict[str, Any]:
        """Load JSON file"""
        full_path = DATA_DIR / filepath
        if not full_path.exists():
            return {}
        with open(full_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @staticmethod
    def save_json(filepath: str, data: Dict[str, Any]):
        """Save JSON file"""
        full_path = DATA_DIR / filepath
        full_path.parent.mkdir(parents=True, exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    @staticmethod
    def load_users() -> List[Dict[str, Any]]:
        """Load all users"""
        data = DataManager.load_json("system/users.json")
        return data.get("users", [])
    
    @staticmethod
    def save_users(users: List[Dict[str, Any]]):
        """Save users"""
        data = {
            "users": users,
            "metadata": {
                "purpose": "Gebruikersdatabase met gradaties en authenticatie",
                "creator": "System",
                "last_updated": datetime.utcnow().isoformat()
            }
        }
        DataManager.save_json("system/users.json", data)
    
    @staticmethod
    def update_user(user_data: Dict[str, Any]):
        """Update a single user in the users list"""
        users = DataManager.load_users()
        
        # Find and update the user
        for i, user in enumerate(users):
            if user.get("id") == user_data.get("id"):
                users[i] = user_data
                DataManager.save_users(users)
                return True
        
        # User not found
        return False
    
    @staticmethod
    def load_knowledge() -> List[Dict[str, Any]]:
        """Load knowledge base"""
        data = DataManager.load_json("learned_knowledge/knowledge_base.json")
        return data.get("knowledge_entries", [])
    
    @staticmethod
    def save_knowledge(entries: List[Dict[str, Any]]):
        """Save knowledge base"""
        data = {
            "knowledge_entries": entries,
            "total_entries": len(entries),
            "metadata": {
                "purpose": "Geleerde kennis van Spark door gesprekken",
                "creator": "System",
                "last_updated": datetime.utcnow().isoformat()
            }
        }
        DataManager.save_json("learned_knowledge/knowledge_base.json", data)
    
    @staticmethod
    def load_diary(user_id: str, sleutelwoord: str) -> List[Dict[str, Any]]:
        """Load user's personal diary"""
        filename = f"memories/{user_id}_{sleutelwoord}_diary.json"
        data = DataManager.load_json(filename)
        return data.get("entries", [])
    
    @staticmethod
    def save_diary(user_id: str, sleutelwoord: str, entries: List[Dict[str, Any]]):
        """Save user's personal diary"""
        filename = f"memories/{user_id}_{sleutelwoord}_diary.json"
        data = {
            "owner": user_id,
            "sleutelwoord": sleutelwoord,
            "entries": entries,
            "metadata": {
                "purpose": "Persoonlijk dagboek",
                "last_updated": datetime.utcnow().isoformat()
            }
        }
        DataManager.save_json(filename, data)
    
    @staticmethod
    def backup_user(user: Dict[str, Any]):
        """Create backup of user data before deletion"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"backups/{user['naam']}_{user['sleutelwoord']}_backup_{timestamp}.json"
        DataManager.save_json(filename, user)
        return filename


    @staticmethod
    def load_data(filepath: str) -> Dict[str, Any]:
        """Alias for load_json"""
        return DataManager.load_json(filepath)
    
    @staticmethod
    def save_data(filepath: str, data: Dict[str, Any]):
        """Alias for save_json"""
        DataManager.save_json(filepath, data)
