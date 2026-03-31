"""
Agenda Service - Enhanced with Profile Integration
Manages: personal events, family birthdays, recurring events, pending items
"""
from typing import Dict, List, Optional
from datetime import datetime
from utils.data_manager import DataManager
import uuid


class AgendaService:
    """Enhanced agenda service with profile integration"""
    
    @staticmethod
    def _get_user_from_system(user_id: str) -> Optional[Dict]:
        """Get user from system/users.json"""
        try:
            users_data = DataManager.load_json("system/users.json")
            users = users_data.get("users", [])
            return next((u for u in users if u["id"] == user_id), None)
        except:
            return None
    
    @staticmethod
    def _save_user_to_system(user: Dict) -> bool:
        """Save user back to system/users.json"""
        try:
            users_data = DataManager.load_json("system/users.json")
            users = users_data.get("users", [])
            
            # Update user in list
            for i, u in enumerate(users):
                if u["id"] == user["id"]:
                    users[i] = user
                    break
            
            DataManager.save_json("system/users.json", users_data)
            return True
        except Exception as e:
            print(f"[AGENDA ERROR] Save failed: {e}")
            return False
    
    @staticmethod
    def _get_user_agenda_path(user_id: str) -> str:
        return f"users/{user_id}/agenda.json"
    
    @staticmethod
    def get_events(user_id: str, upcoming_only: bool = False) -> List[Dict]:
        """Get user's agenda events"""
        try:
            data = DataManager.load_data(AgendaService._get_user_agenda_path(user_id))
            events = data.get("events", [])
            
            if upcoming_only:
                now = datetime.now().isoformat()
                events = [e for e in events if e.get("date", "") >= now]
            
            # Sort by date
            events.sort(key=lambda x: x.get("date", ""))
            
            return events
        except Exception:
            return []
    
    @staticmethod
    def add_event(user_id: str, titel: str, date: str, beschrijving: Optional[str] = None, 
                  reminder: bool = False) -> Dict:
        """Add new agenda event"""
        try:
            data = DataManager.load_data(AgendaService._get_user_agenda_path(user_id))
            if "events" not in data:
                data["events"] = []
        except Exception:
            # Create new agenda file
            data = {
                "user_id": user_id,
                "events": [],
                "created_at": datetime.now().isoformat()
            }
        
        # Create event
        event_id = str(uuid.uuid4())
        event = {
            "id": event_id,
            "titel": titel,
            "date": date,
            "beschrijving": beschrijving,
            "reminder": reminder,
            "created_at": datetime.now().isoformat()
        }
        
        data["events"].append(event)
        DataManager.save_data(AgendaService._get_user_agenda_path(user_id), data)
        
        return event
    
    # NEW: Enhanced methods for v3.3 Profile & Agenda system
    
    @staticmethod
    def add_personal_event(user_id: str, event_data: Dict) -> Optional[str]:
        """
        Add event to user's personal agenda (in profile)
        """
        try:
            user = AgendaService._get_user_from_system(user_id)
            if not user:
                return None
            
            # Ensure agenda structure
            if "agenda" not in user:
                user["agenda"] = {"events": [], "family_birthdays": [], "recurring_events": []}
            if "events" not in user["agenda"]:
                user["agenda"]["events"] = []
            
            # Create event
            event_id = str(uuid.uuid4())
            event = {
                "id": event_id,
                "title": event_data.get("title", "Untitled"),
                "date": event_data.get("date"),
                "time": event_data.get("time"),
                "type": event_data.get("type", "other"),
                "notes": event_data.get("notes", ""),
                "created_at": datetime.now().isoformat(),
                "auto_detected": event_data.get("auto_detected", False)
            }
            
            user["agenda"]["events"].append(event)
            AgendaService._save_user_to_system(user)
            return event_id
        except Exception as e:
            print(f"[AGENDA ERROR] Add event failed: {e}")
            return None
    
    @staticmethod
    def add_family_birthday(user_id: str, birthday_data: Dict) -> Optional[str]:
        """Add family/friend birthday"""
        try:
            user = AgendaService._get_user_from_system(user_id)
            if not user:
                return None
            
            if "agenda" not in user:
                user["agenda"] = {"events": [], "family_birthdays": [], "recurring_events": []}
            if "family_birthdays" not in user["agenda"]:
                user["agenda"]["family_birthdays"] = []
            
            birthday_id = str(uuid.uuid4())
            birthday = {
                "id": birthday_id,
                "naam": birthday_data.get("naam"),
                "relatie": birthday_data.get("relatie", ""),
                "datum": birthday_data.get("datum"),
                "jaar": birthday_data.get("jaar"),
                "herinnering": birthday_data.get("herinnering", "1_week_voor"),
                "created_at": datetime.now().isoformat(),
                "auto_detected": birthday_data.get("auto_detected", False)
            }
            
            user["agenda"]["family_birthdays"].append(birthday)
            AgendaService._save_user_to_system(user)
            return birthday_id
        except Exception as e:
            print(f"[AGENDA ERROR] Add birthday failed: {e}")
            return None
    
    @staticmethod
    def get_full_agenda(user_id: str) -> Optional[Dict]:
        """Get complete agenda (events + birthdays + recurring)"""
        try:
            user = AgendaService._get_user_from_system(user_id)
            if not user:
                return None
            
            return user.get("agenda", {
                "events": [],
                "family_birthdays": [],
                "recurring_events": []
            })
        except Exception:
            return None
    
    @staticmethod
    def add_pending_agenda_item(user_id: str, detected_event) -> bool:
        """Add detected event to pending (needs approval)"""
        try:
            user = AgendaService._get_user_from_system(user_id)
            if not user:
                return False
            
            if "pending_agenda_items" not in user:
                user["pending_agenda_items"] = []
            
            pending = {
                "id": str(uuid.uuid4()),
                "type": detected_event.type,
                "title": detected_event.title,
                "date_str": detected_event.date_str,
                "parsed_date": detected_event.parsed_date,
                "confidence": detected_event.confidence,
                "original_text": detected_event.original_text,
                "notes": detected_event.notes,
                "detected_at": datetime.now().isoformat(),
                "status": "pending"
            }
            
            user["pending_agenda_items"].append(pending)
            AgendaService._save_user_to_system(user)
            return True
        except Exception as e:
            print(f"[AGENDA ERROR] Add pending failed: {e}")
            return False
    
    @staticmethod
    def approve_pending_item(user_id: str, pending_id: str) -> bool:
        """Approve and move pending item to agenda"""
        try:
            user = AgendaService._get_user_from_system(user_id)
            if not user:
                return False
            
            pending_items = user.get("pending_agenda_items", [])
            pending = next((p for p in pending_items if p["id"] == pending_id), None)
            if not pending:
                return False
            
            # Add to appropriate category
            if pending["type"] == "birthday":
                AgendaService.add_family_birthday(user_id, {
                    "naam": pending["title"].replace("Verjaardag ", ""),
                    "datum": pending["parsed_date"] or pending["date_str"],
                    "auto_detected": True
                })
            else:
                AgendaService.add_personal_event(user_id, {
                    "title": pending["title"],
                    "date": pending["parsed_date"],
                    "type": pending["type"],
                    "notes": pending["notes"],
                    "auto_detected": True
                })
            
            # Remove from pending
            user["pending_agenda_items"] = [p for p in pending_items if p["id"] != pending_id]
            AgendaService._save_user_to_system(user)
            return True
        except Exception as e:
            print(f"[AGENDA ERROR] Approve failed: {e}")
            return False
    
    @staticmethod
    def reject_pending_item(user_id: str, pending_id: str) -> bool:
        """Reject pending item"""
        try:
            user = AgendaService._get_user_from_system(user_id)
            if not user:
                return False
            
            pending_items = user.get("pending_agenda_items", [])
            user["pending_agenda_items"] = [p for p in pending_items if p["id"] != pending_id]
            AgendaService._save_user_to_system(user)
            return True
        except Exception:
            return False

            data = {
                "user_id": user_id,
                "events": [],
                "created_at": datetime.now().isoformat()
            }
        
        # Create event
        event = {
            "id": str(uuid.uuid4())[:8],
            "titel": titel,
            "beschrijving": beschrijving,
            "date": date,
            "reminder": reminder,
            "status": "upcoming",
            "created_at": datetime.now().isoformat()
        }
        
        # Add to events
        data["events"].append(event)
        
        # Save
        DataManager.save_data(AgendaService._get_user_agenda_path(user_id), data)
        
        return event
    
    @staticmethod
    def get_upcoming(user_id: str, limit: int = 5) -> List[Dict]:
        """Get upcoming events"""
        events = AgendaService.get_events(user_id, upcoming_only=True)
        return events[:limit]
