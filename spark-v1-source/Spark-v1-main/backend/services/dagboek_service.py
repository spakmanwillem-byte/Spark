"""
Dagboek Service - Persoonlijke dagboek entries
"""
from typing import Dict, List, Optional
from datetime import datetime
from utils.data_manager import DataManager
import uuid


class DagboekService:
    
    @staticmethod
    def _get_user_dagboek_path(user_id: str) -> str:
        return f"users/{user_id}/dagboek.json"
    
    @staticmethod
    def get_entries(user_id: str, limit: Optional[int] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict]:
        """Get user's dagboek entries with optional date filtering"""
        try:
            data = DataManager.load_data(DagboekService._get_user_dagboek_path(user_id))
            entries = data.get("entries", [])
            
            # Apply date filters if provided
            if start_date or end_date:
                filtered = []
                for entry in entries:
                    entry_date = entry.get("created_at", "")[:10]  # YYYY-MM-DD
                    if start_date and entry_date < start_date:
                        continue
                    if end_date and entry_date > end_date:
                        continue
                    filtered.append(entry)
                entries = filtered
            
            # Sort by date (newest first)
            entries.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            
            if limit:
                return entries[:limit]
            return entries
        except:
            return []
    
    @staticmethod
    def add_entry(user_id: str, content: str, mood: Optional[str] = None, tags: Optional[List[str]] = None) -> Dict:
        """Add new dagboek entry"""
        try:
            data = DataManager.load_data(DagboekService._get_user_dagboek_path(user_id))
            if "entries" not in data:
                data["entries"] = []
        except:
            # Create new dagboek file
            data = {
                "user_id": user_id,
                "entries": [],
                "created_at": datetime.now().isoformat()
            }
        
        # Create entry
        entry = {
            "id": str(uuid.uuid4())[:8],
            "content": content,
            "mood": mood,
            "tags": tags or [],
            "created_at": datetime.now().isoformat(),
            "word_count": len(content.split())
        }
        
        # Add to entries
        data["entries"].append(entry)
        
        # Save
        DataManager.save_data(DagboekService._get_user_dagboek_path(user_id), data)
        
        return entry
    
    @staticmethod
    def update_entry(user_id: str, entry_id: str, content: str, mood: Optional[str] = None, tags: Optional[List[str]] = None) -> Optional[Dict]:
        """Update existing dagboek entry"""
        try:
            data = DataManager.load_data(DagboekService._get_user_dagboek_path(user_id))
            entries = data.get("entries", [])
            
            for entry in entries:
                if entry.get("id") == entry_id:
                    entry["content"] = content
                    entry["mood"] = mood
                    entry["tags"] = tags or []
                    entry["word_count"] = len(content.split())
                    entry["updated_at"] = datetime.now().isoformat()
                    
                    DataManager.save_data(DagboekService._get_user_dagboek_path(user_id), data)
                    return entry
            
            return None
        except:
            return None
    
    @staticmethod
    def delete_entry(user_id: str, entry_id: str) -> bool:
        """Delete dagboek entry"""
        try:
            data = DataManager.load_data(DagboekService._get_user_dagboek_path(user_id))
            entries = data.get("entries", [])
            
            original_count = len(entries)
            data["entries"] = [e for e in entries if e.get("id") != entry_id]
            
            if len(data["entries"]) < original_count:
                DataManager.save_data(DagboekService._get_user_dagboek_path(user_id), data)
                return True
            
            return False
        except:
            return False
    
    @staticmethod
    def get_stats(user_id: str) -> Dict:
        """Get dagboek statistics"""
        entries = DagboekService.get_entries(user_id)
        
        if not entries:
            return {
                "total_entries": 0,
                "total_words": 0,
                "latest_entry": None
            }
        
        total_words = sum(e.get("word_count", 0) for e in entries)
        
        return {
            "total_entries": len(entries),
            "total_words": total_words,
            "latest_entry": entries[0].get("created_at") if entries else None,
            "avg_words_per_entry": total_words // len(entries) if entries else 0
        }
    
    @staticmethod
    def export_entries(user_id: str, format: str = "txt", start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
        """Export dagboek entries as text or markdown"""
        entries = DagboekService.get_entries(user_id, start_date=start_date, end_date=end_date)
        
        if format == "markdown":
            content = "# Dagboek Export\n\n"
            content += f"*Geëxporteerd op {datetime.now().strftime('%d-%m-%Y om %H:%M')}*\n\n"
            content += f"**Totaal aantal entries:** {len(entries)}\n\n---\n\n"
            
            for entry in reversed(entries):  # Oldest first for reading
                date = datetime.fromisoformat(entry.get("created_at", "")).strftime('%d-%m-%Y om %H:%M')
                content += f"## {date}\n\n"
                
                if entry.get("mood"):
                    content += f"**Stemming:** {entry.get('mood')}\n\n"
                
                if entry.get("tags"):
                    tags = ", ".join([f"#{tag}" for tag in entry.get("tags", [])])
                    content += f"**Tags:** {tags}\n\n"
                
                content += f"{entry.get('content', '')}\n\n"
                content += f"*{entry.get('word_count', 0)} woorden*\n\n---\n\n"
        else:
            # Plain text format
            content = "DAGBOEK EXPORT\n"
            content += f"Geëxporteerd op {datetime.now().strftime('%d-%m-%Y om %H:%M')}\n"
            content += f"Totaal aantal entries: {len(entries)}\n\n"
            content += "=" * 60 + "\n\n"
            
            for entry in reversed(entries):  # Oldest first for reading
                date = datetime.fromisoformat(entry.get("created_at", "")).strftime('%d-%m-%Y om %H:%M')
                content += f"{date}\n"
                
                if entry.get("mood"):
                    content += f"Stemming: {entry.get('mood')}\n"
                
                if entry.get("tags"):
                    tags = ", ".join([f"#{tag}" for tag in entry.get("tags", [])])
                    content += f"Tags: {tags}\n"
                
                content += "\n" + entry.get('content', '') + "\n"
                content += f"\n({entry.get('word_count', 0)} woorden)\n"
                content += "\n" + "-" * 60 + "\n\n"
        
        return content
