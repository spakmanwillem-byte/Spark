"""
Spark Auth Module - Service Layer
All authentication logic in one place
"""
from typing import Optional, Tuple, List
from datetime import datetime, timedelta
from pathlib import Path

from modules.core.storage import load_json, save_json
from config.settings import USERS_FILE, GRADATIES_FILE, SESSION_TIMEOUT_MINUTES
from .models import User, UserCreate


class AuthService:
    """
    Authentication Service
    Handles login, sessions, user management, and gradaties
    """
    
    # ============== USER LOADING ==============
    
    @staticmethod
    def get_all_users() -> List[dict]:
        """Load all users from storage"""
        data = load_json(USERS_FILE, default=[])
        # Support both list format and {"users": [...]} format
        if isinstance(data, dict) and "users" in data:
            return data["users"]
        return data if isinstance(data, list) else []
    
    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[dict]:
        """Get user by ID"""
        users = AuthService.get_all_users()
        return next((u for u in users if u.get("id") == user_id), None)
    
    @staticmethod
    def _save_users(users: List[dict]) -> bool:
        """Save users to storage"""
        # Check original format
        original = load_json(USERS_FILE, default=[])
        if isinstance(original, dict) and "users" in original:
            # Preserve object format
            original["users"] = users
            return save_json(USERS_FILE, original)
        return save_json(USERS_FILE, users)
    
    # ============== AUTHENTICATION ==============
    
    @staticmethod
    def authenticate(naam: str, sleutelwoord: Optional[str] = None, masterkey: Optional[str] = None) -> Tuple[Optional[dict], bool]:
        """
        Authenticate user with sleutelwoord or masterkey
        
        Args:
            naam: User name (partial or full)
            sleutelwoord: User password
            masterkey: Admin masterkey
            
        Returns:
            Tuple of (user_data, is_masterkey_used)
        """
        users = AuthService.get_all_users()
        
        # Find matching users
        matching_users = []
        naam_lower = naam.lower().strip()
        
        for u in users:
            user_naam = u.get("naam", "").lower()
            
            # Exact match
            if user_naam == naam_lower:
                matching_users.append(u)
            # Partial match (e.g., "Maurice" matches "Maurice Maas")
            elif naam_lower in user_naam or user_naam.split()[0] == naam_lower:
                matching_users.append(u)
        
        if not matching_users:
            return None, False
        
        # Check masterkey first
        if masterkey and masterkey.upper() == "SAMEN":
            for user in matching_users:
                if user.get("masterkey") == "SAMEN":
                    print(f"[AUTH] Masterkey login: {user.get('naam')}")
                    return user, True
            return None, False
        
        # Check sleutelwoord
        if sleutelwoord:
            sleutel_lower = sleutelwoord.lower().strip()
            for user in matching_users:
                user_sleutel = user.get("sleutelwoord", "").lower().strip()
                if user_sleutel == sleutel_lower:
                    print(f"[AUTH] Login: {user.get('naam')}")
                    return user, False
        
        return None, False
    
    # ============== SESSION MANAGEMENT ==============
    
    @staticmethod
    def validate_session(user_id: str) -> bool:
        """
        Check if user session is still active
        
        Args:
            user_id: User ID
            
        Returns:
            True if session is valid
        """
        user = AuthService.get_user_by_id(user_id)
        if not user:
            return False
        
        last_active_str = user.get("last_active")
        if not last_active_str:
            return True  # No timestamp yet, allow
        
        try:
            last_active = datetime.fromisoformat(last_active_str)
            now = datetime.utcnow()
            
            if now - last_active > timedelta(minutes=SESSION_TIMEOUT_MINUTES):
                print(f"[SESSION] Expired: {user.get('naam')}")
                return False
            
            return True
        except Exception as e:
            print(f"[SESSION ERROR] {e}")
            return True
    
    @staticmethod
    def heartbeat(user_id: str) -> dict:
        """
        Update session heartbeat
        
        Args:
            user_id: User ID
            
        Returns:
            Session status dict
        """
        users = AuthService.get_all_users()
        user = next((u for u in users if u.get("id") == user_id), None)
        
        if not user:
            return {"status": "invalid", "message": "User not found"}
        
        # Update last_active
        now = datetime.utcnow()
        user["last_active"] = now.isoformat()
        AuthService._save_users(users)
        
        return {
            "status": "active",
            "user_id": user_id,
            "naam": user.get("naam"),
            "gradatie": user.get("gradatie"),
            "expires_in": SESSION_TIMEOUT_MINUTES * 60,
            "last_active": now.isoformat()
        }
    
    @staticmethod
    def update_activity(user_id: str) -> bool:
        """
        Update user activity (gesprekken_count, trust_score, last_active)
        
        Args:
            user_id: User ID
            
        Returns:
            True if updated
        """
        users = AuthService.get_all_users()
        
        for user in users:
            if user.get("id") == user_id:
                user["last_active"] = datetime.utcnow().isoformat()
                user["gesprekken_count"] = user.get("gesprekken_count", 0) + 1
                user["trust_score"] = min(user.get("trust_score", 0) + 1, 100)
                return AuthService._save_users(users)
        
        return False
    
    # ============== USER MANAGEMENT ==============
    
    @staticmethod
    def create_user(user_data: UserCreate) -> Tuple[Optional[dict], str]:
        """
        Create new user
        
        Args:
            user_data: User creation data
            
        Returns:
            Tuple of (user_dict, error_message)
        """
        users = AuthService.get_all_users()
        
        # Check if exists
        for u in users:
            if (u.get("naam", "").lower() == user_data.naam.lower() and 
                u.get("sleutelwoord", "").lower() == user_data.sleutelwoord.lower()):
                return None, f"Gebruiker {user_data.naam} met dit sleutelwoord bestaat al"
        
        # Create new user
        new_user = User(
            naam=user_data.naam,
            volledige_naam=user_data.volledige_naam or user_data.naam,
            sleutelwoord=user_data.sleutelwoord,
            gradatie=7,
            rol="Onbekende"
        )
        
        user_dict = new_user.model_dump()
        users.append(user_dict)
        
        if AuthService._save_users(users):
            print(f"[AUTH] New user: {user_data.naam}")
            return user_dict, ""
        
        return None, "Kon gebruiker niet opslaan"
    
    @staticmethod
    def update_user(user_id: str, updates: dict) -> bool:
        """
        Update user fields
        
        Args:
            user_id: User ID
            updates: Dict of fields to update
            
        Returns:
            True if updated
        """
        users = AuthService.get_all_users()
        
        for user in users:
            if user.get("id") == user_id:
                user.update(updates)
                return AuthService._save_users(users)
        
        return False
    
    @staticmethod
    def delete_user(user_id: str) -> bool:
        """
        Delete user
        
        Args:
            user_id: User ID
            
        Returns:
            True if deleted
        """
        users = AuthService.get_all_users()
        original_len = len(users)
        users = [u for u in users if u.get("id") != user_id]
        
        if len(users) < original_len:
            return AuthService._save_users(users)
        
        return False
    
    # ============== GRADATIE SYSTEM ==============
    
    @staticmethod
    def get_gradaties() -> List[dict]:
        """Get all gradatie definitions"""
        data = load_json(GRADATIES_FILE, default={"gradaties": []})
        return data.get("gradaties", [])
    
    @staticmethod
    def get_gradatie_info(niveau: int) -> Optional[dict]:
        """Get gradatie info by niveau"""
        gradaties = AuthService.get_gradaties()
        return next((g for g in gradaties if g.get("niveau") == niveau), None)
    
    @staticmethod
    def update_gradatie(user_id: str, new_gradatie: int, reden: str = "") -> bool:
        """
        Update user gradatie
        
        Args:
            user_id: User ID
            new_gradatie: New gradatie level (1-7)
            reden: Reason for change
            
        Returns:
            True if updated
        """
        users = AuthService.get_all_users()
        gradatie_info = AuthService.get_gradatie_info(new_gradatie)
        
        for user in users:
            if user.get("id") == user_id:
                old_gradatie = user.get("gradatie", 7)
                user["gradatie"] = new_gradatie
                
                if gradatie_info:
                    user["rol"] = gradatie_info.get("titel", "Onbekende")
                
                print(f"[AUTH] Gradatie change: {user.get('naam')} {old_gradatie} -> {new_gradatie} ({reden})")
                return AuthService._save_users(users)
        
        return False
    
    @staticmethod
    def check_auto_gradatie_growth(user: dict) -> Optional[int]:
        """
        Check if user should auto-grow in gradatie
        
        Args:
            user: User dict
            
        Returns:
            New gradatie if should change, None otherwise
        """
        current = user.get("gradatie", 7)
        gesprekken = user.get("gesprekken_count", 0)
        trust = user.get("trust_score", 0)
        
        try:
            registered = datetime.fromisoformat(user.get("registered_date", datetime.utcnow().isoformat()))
            days_active = (datetime.utcnow() - registered).days
        except:
            days_active = 0
        
        # Gradatie 7 -> 6
        if current == 7 and gesprekken >= 5 and days_active >= 7 and trust >= 30:
            return 6
        
        # Gradatie 6 -> 5
        if current == 6 and gesprekken >= 15 and days_active >= 30 and trust >= 60:
            return 5
        
        return None
