"""
Profile Service
Manages extended user profiles with personal information
"""
from typing import Optional, Dict, Any
from datetime import datetime
from utils.data_manager import DataManager


class ProfileService:
    """Service for managing user profiles"""
    
    @staticmethod
    def get_empty_profile_structure() -> Dict[str, Any]:
        """
        Get empty profile structure (for new users or migration)
        """
        return {
            "personal_info": {
                "voornaam": "",
                "achternaam": "",
                "geboortedatum": None,  # ISO format: "1990-05-15"
                "sterrenbeeld": "",  # Auto-calculated from geboortedatum
                "geslacht": "",
                
                "contact": {
                    "email": "",
                    "telefoon": "",
                    "secondary_email": None,
                    "secondary_phone": None
                },
                
                "adres": {
                    "straat": "",
                    "huisnummer": "",
                    "postcode": "",
                    "plaats": "",
                    "land": "Nederland"
                },
                
                "werk": {
                    "beroep": "",
                    "bedrijf": "",
                    "sector": "",
                    "sinds": None  # ISO format date
                },
                
                "interesses": {
                    "hobbies": [],  # Hierarchisch: {"naam": "gamen", "detail": ["shooters"], "games": ["Call of Duty"]}
                    "sporten": [],
                    "muziek_genres": [],
                    "favoriete_boeken": [],
                    "favoriete_films": [],
                    "favoriete_eten": [],  # NEW: ["pizza", "pasta", "sushi"]
                    "favoriete_drinken": []  # NEW: ["koffie", "bier", "thee"]
                },
                
                "persoonlijkheid": {  # NEW SECTION
                    "introvert_extrovert": 5,  # Schaal 1-10 (1=introvert, 10=extrovert)
                    "meest_gebruikt_woord": "",  # Auto-detect uit gesprekken
                    "gespreksstijl": "",  # "direct", "uitgebreid", "kort"
                    "humor_type": ""  # "droog", "sarcastisch", "speels"
                },
                
                "life_events": [],  # NEW: [{"type": "loss", "description": "Vader overleden aan kanker", "when": "jaren geleden"}]
                
                "relaties": {
                    "partner": {
                        "naam": "",
                        "sinds": None
                    },
                    "kinderen": [],  # [{"naam": "...", "geboortedatum": "..."}]
                    "huisdieren": []  # [{"naam": "...", "type": "...", "ras": "..."}]
                },
                
                "belangrijke_data": {
                    "verjaardag_partner": None,
                    "trouwdag": None,
                    "custom": []  # [{"naam": "...", "datum": "..."}]
                }
            },
            
            "agenda": {
                "events": [],  # Personal events
                "family_birthdays": [],  # Family/friends birthdays
                "recurring_events": []  # Weekly/monthly recurring
            },
            
            "pending_profile_updates": [],  # Auto-extracted profile info awaiting approval
            "pending_agenda_items": []  # Auto-extracted events awaiting approval
        }
    
    @staticmethod
    def calculate_zodiac_sign(birthdate: str) -> str:
        """
        Calculate zodiac sign (sterrenbeeld) from birthdate
        
        Args:
            birthdate: ISO format date string "YYYY-MM-DD"
        
        Returns:
            Dutch zodiac sign name
        """
        try:
            date = datetime.fromisoformat(birthdate)
            month = date.month
            day = date.day
            
            # Zodiac sign dates (Dutch names)
            if (month == 3 and day >= 21) or (month == 4 and day <= 19):
                return "Ram"
            elif (month == 4 and day >= 20) or (month == 5 and day <= 20):
                return "Stier"
            elif (month == 5 and day >= 21) or (month == 6 and day <= 20):
                return "Tweelingen"
            elif (month == 6 and day >= 21) or (month == 7 and day <= 22):
                return "Kreeft"
            elif (month == 7 and day >= 23) or (month == 8 and day <= 22):
                return "Leeuw"
            elif (month == 8 and day >= 23) or (month == 9 and day <= 22):
                return "Maagd"
            elif (month == 9 and day >= 23) or (month == 10 and day <= 22):
                return "Weegschaal"
            elif (month == 10 and day >= 23) or (month == 11 and day <= 21):
                return "Schorpioen"
            elif (month == 11 and day >= 22) or (month == 12 and day <= 21):
                return "Boogschutter"
            elif (month == 12 and day >= 22) or (month == 1 and day <= 19):
                return "Steenbok"
            elif (month == 1 and day >= 20) or (month == 2 and day <= 18):
                return "Waterman"
            else:  # (month == 2 and day >= 19) or (month == 3 and day <= 20)
                return "Vissen"
        except:
            return ""
    
    @staticmethod
    def ensure_profile_structure(user_data: Dict) -> Dict:
        """
        Ensure user has complete profile structure (migration helper)
        Adds missing fields without overwriting existing data
        """
        empty_structure = ProfileService.get_empty_profile_structure()
        
        # Add missing top-level keys
        for key in empty_structure:
            if key not in user_data:
                user_data[key] = empty_structure[key]
        
        # Ensure nested structures exist
        if "personal_info" not in user_data or not isinstance(user_data["personal_info"], dict):
            user_data["personal_info"] = empty_structure["personal_info"]
        
        # Add missing nested keys in personal_info
        for key in empty_structure["personal_info"]:
            if key not in user_data["personal_info"]:
                user_data["personal_info"][key] = empty_structure["personal_info"][key]
        
        # Auto-calculate zodiac if birthdate exists but zodiac doesn't
        if user_data["personal_info"].get("geboortedatum") and not user_data["personal_info"].get("sterrenbeeld"):
            user_data["personal_info"]["sterrenbeeld"] = ProfileService.calculate_zodiac_sign(
                user_data["personal_info"]["geboortedatum"]
            )
        
        return user_data
    
    @staticmethod
    def update_profile_field(user_id: str, field_path: str, value: Any) -> bool:
        """
        Update a specific profile field
        
        Args:
            user_id: User ID
            field_path: Dot notation path (e.g., "personal_info.contact.email")
            value: New value
        
        Returns:
            Success boolean
        """
        try:
            # Load user
            users_data = DataManager.load_json("system/users.json")
            users = users_data.get("users", [])
            
            user = next((u for u in users if u["id"] == user_id), None)
            if not user:
                return False
            
            # Ensure profile structure
            user = ProfileService.ensure_profile_structure(user)
            
            # Navigate to field using dot notation
            keys = field_path.split(".")
            target = user
            for key in keys[:-1]:
                if key not in target:
                    target[key] = {}
                target = target[key]
            
            # Set value
            target[keys[-1]] = value
            
            # Special: Auto-update zodiac if birthdate changed
            if field_path == "personal_info.geboortedatum" and value:
                user["personal_info"]["sterrenbeeld"] = ProfileService.calculate_zodiac_sign(value)
            
            # Save
            DataManager.save_json("system/users.json", users_data)
            return True
            
        except Exception as e:
            print(f"[PROFILE ERROR] Failed to update {field_path}: {e}")
            return False
    
    @staticmethod
    def get_profile(user_id: str) -> Optional[Dict]:
        """
        Get user's complete profile
        """
        try:
            users_data = DataManager.load_json("system/users.json")
            users = users_data.get("users", [])
            
            user = next((u for u in users if u["id"] == user_id), None)
            if not user:
                return None
            
            # Ensure structure
            user = ProfileService.ensure_profile_structure(user)
            
            return {
                "personal_info": user.get("personal_info", {}),
                "agenda": user.get("agenda", {}),
                "pending_profile_updates": user.get("pending_profile_updates", []),
                "pending_agenda_items": user.get("pending_agenda_items", [])
            }
        except Exception as e:
            print(f"[PROFILE ERROR] Failed to get profile: {e}")
            return None
