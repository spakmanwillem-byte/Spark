"""
Spark Auth Module - Service Layer
All authentication logic in one place
"""
import os
from typing import Optional, Tuple, List, Dict
from datetime import datetime, timedelta
from pathlib import Path

from modules.core.storage import load_json, save_json
from config.settings import USERS_FILE, GRADATIES_FILE, SESSION_TIMEOUT_MINUTES
from .models import User, UserCreate


def _get_masterkey() -> str:
    """Load masterkey from env at call-time (allows hot-swap in dev)."""
    return (os.environ.get("SPARK_MASTERKEY") or "").strip().upper()


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
        
        # Check masterkey first (loaded from env — SPARK_MASTERKEY)
        env_mk = _get_masterkey()
        if masterkey and env_mk and masterkey.strip().upper() == env_mk:
            for user in matching_users:
                user_mk = (user.get("masterkey") or "").strip().upper()
                if user_mk and user_mk == env_mk:
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
                # Credits bonus multiplier (v4_dank_004) — users in bedank-lijst krijgen sneller trust
                mult = user.get("credits_multiplier", 1.0) or 1.0
                # +1 base, multiplied by credits_multiplier (rounded — but keep float carry)
                user["_trust_carry"] = (user.get("_trust_carry", 0) or 0) + mult
                gain = int(user["_trust_carry"])
                user["_trust_carry"] = user["_trust_carry"] - gain
                user["trust_score"] = min(user.get("trust_score", 0) + gain, 100)
                return AuthService._save_users(users)
        
        return False
    
    # ============== USER MANAGEMENT ==============
    
    @staticmethod
    def create_user(user_data: UserCreate, admin_override: bool = False) -> Tuple[Optional[dict], str]:
        """
        Create new user
        
        Args:
          user_data: UserCreate object
          admin_override: indien True, slaat collisie-check en lengte-eisen over
                          (voor admin-gemaakte accounts met gedeeld default sleutelwoord)

        Returns:
            Tuple of (user_dict, error_message)
        """
        sleutel = (user_data.sleutelwoord or "").strip()

        if not admin_override:
            # v4_025c: minimale eisen aan sleutelwoord voor self-registration
            if len(sleutel) < 4:
                return None, "Kies een sleutelwoord met minstens 4 tekens."

            users = AuthService.get_all_users()
            # Generieke collisie-melding (verraadt bestaan niet)
            for u in users:
                if (u.get("naam", "").lower() == user_data.naam.lower() and
                    u.get("sleutelwoord", "").lower() == sleutel.lower()):
                    return None, "Kies een ander sleutelwoord, of kies een sleutelwoord met meer tekens."
        else:
            users = AuthService.get_all_users()
        
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
            print(f"[AUTH] New user: {user_data.naam} (admin_override={admin_override})")
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
        Delete user + alle gekoppelde persoonlijke data.
        Bescherming: user-001 (admin/Willem) kan niet verwijderd worden.

        Cascade-delete:
        - data/chat/logs/{user_id}.json (gesprekslogs)
        - data/users/{user_id}/         (persoonlijk archief + quota)
        """
        if user_id == "user-001":
            return False

        users = AuthService.get_all_users()
        original_len = len(users)
        users = [u for u in users if u.get("id") != user_id]

        if len(users) >= original_len:
            return False

        if not AuthService._save_users(users):
            return False

        # Cascade-delete persoonlijke data
        import shutil
        BASE = Path(__file__).parent.parent.parent / "data"

        # 1. Chat-logs
        chat_log = BASE / "chat" / "logs" / f"{user_id}.json"
        if chat_log.exists():
            try:
                chat_log.unlink()
                print(f"[AUTH] Cascade: chat log gewist voor {user_id}")
            except OSError as e:
                print(f"[AUTH] Kon chat log niet verwijderen: {e}")

        # 2. Archief + quota + bestanden
        archive_dir = BASE / "users" / user_id
        if archive_dir.exists():
            try:
                shutil.rmtree(archive_dir)
                print(f"[AUTH] Cascade: archief gewist voor {user_id}")
            except OSError as e:
                print(f"[AUTH] Kon archief niet verwijderen: {e}")

        return True

    @staticmethod
    def reset_password(user_id: str, new_sleutelwoord: str = "Welkom01") -> Optional[str]:
        """
        Reset sleutelwoord van een gebruiker.
        Standaard wordt het op 'Welkom01' gezet (voor reset-verzoeken).
        Returns het nieuwe sleutelwoord bij succes, None bij falen.
        """
        users = AuthService.get_all_users()
        for user in users:
            if user.get("id") == user_id:
                user["sleutelwoord"] = new_sleutelwoord
                user["sleutelwoord_reset_op"] = datetime.utcnow().isoformat()
                if AuthService._save_users(users):
                    print(f"[AUTH] Password reset: {user.get('naam')} -> {new_sleutelwoord}")
                    return new_sleutelwoord
        return None

    @staticmethod
    def change_password(user_id: str, current_sleutelwoord: str, new_sleutelwoord: str) -> Tuple[bool, str]:
        """
        Self-service change: verifieer huidig sleutelwoord en zet nieuwe.
        Returns (success, message).
        v5_self_password_001: gebruiker kan eigen sleutelwoord wijzigen zonder admin.
        """
        if not current_sleutelwoord or not new_sleutelwoord:
            return False, "Geef huidig én nieuw sleutelwoord op"
        if len(new_sleutelwoord) < 4:
            return False, "Nieuw sleutelwoord moet minstens 4 tekens hebben"
        if current_sleutelwoord == new_sleutelwoord:
            return False, "Nieuw sleutelwoord is gelijk aan het huidige"
        users = AuthService.get_all_users()
        for user in users:
            if user.get("id") == user_id:
                if (user.get("sleutelwoord") or "") != current_sleutelwoord:
                    return False, "Huidig sleutelwoord klopt niet"
                user["sleutelwoord"] = new_sleutelwoord
                user["sleutelwoord_changed_op"] = datetime.utcnow().isoformat()
                if AuthService._save_users(users):
                    print(f"[AUTH] Password self-change: {user.get('naam')}")
                    return True, "Sleutelwoord gewijzigd"
                return False, "Opslaan mislukt"
        return False, "Gebruiker niet gevonden"

    
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
    def _profile_completeness(user: dict) -> float:
        """v4_grad_growth_002: Bereken hoe volledig een user-profiel is (0.0-1.0).

        Velden die meetellen voor 7→6 upgrade:
        - volledige_naam (basis-naam), geboortedatum, locatie/plaats
        - adres (straat), postcode, land, telefoon, nationaliteit
        - noodcontact (naam + telefoon)
        - geslacht
        """
        check_fields = [
            "volledige_naam", "geboortedatum", "plaats", "straat", "postcode",
            "land", "telefoon", "nationaliteit", "geslacht",
        ]
        filled = 0
        for f in check_fields:
            v = user.get(f) or (user.get("profiel") or {}).get(f) or (user.get("adres") or {}).get(f)
            if isinstance(v, str) and v.strip():
                filled += 1
            elif v and not isinstance(v, str):
                filled += 1
        # Noodcontact telt als 1 als naam+telefoon gevuld
        nc = user.get("noodcontact") or {}
        if isinstance(nc, dict) and (nc.get("naam") and nc.get("telefoon")):
            filled += 1
            total = len(check_fields) + 1
        else:
            total = len(check_fields) + 1  # noodcontact telt mee in noemer
        return filled / total if total else 0.0

    @staticmethod
    def check_auto_gradatie_growth(user: dict) -> Optional[int]:
        """
        v4_grad_growth_002: Auto-upgrade pad
          7 → 6: profiel ≥ 80% gevuld (Spark "kent" jou) — geen tijd/gesprek-eis
          6 → 5: 15 gesprekken + 30 dagen + trust ≥ 60 (gedrag bewezen)
          5 → 4: token bezit ≥ 1 (Roarr-token, mechaniek v4_token_potje_001)
          4 → 3: handmatig door admin (persoonlijke kring); Spark mag suggereren
          3 → 2 → 1: admin-only, geen auto-groei
        """
        current = user.get("gradatie", 7)
        gesprekken = user.get("gesprekken_count", 0)
        trust = user.get("trust_score", 0)

        try:
            registered = datetime.fromisoformat(user.get("registered_date", datetime.utcnow().isoformat()))
            days_active = (datetime.utcnow() - registered).days
        except Exception:
            days_active = 0

        # 7 → 6: profielvolledigheid (jouw nieuwe regel — Spark weet basis-info)
        if current == 7:
            completeness = AuthService._profile_completeness(user)
            if completeness >= 0.80:
                return 6

        # 6 → 5: behavior-based (oude regel — onveranderd)
        if current == 6 and gesprekken >= 15 and days_active >= 30 and trust >= 60:
            return 5

        # 5 → 4: token bezit ≥ 1 (Roarr-token mechaniek, v4_token_potje_001)
        # Token systeem bestaat nog niet — fallback: skip tot mechaniek af is.
        if current == 5:
            tokens = user.get("tokens", 0) or len(user.get("token_ids", []) or [])
            if tokens >= 1:
                return 4

        # 4 → 3 en hoger: admin-only (returneert None)
        return None

    @staticmethod
    def suggest_gradatie_promotion(user: dict) -> Optional[Dict]:
        """v4_grad_suggest_001: Spark mag voorstellen aan admin om user te promoten.
        Vooral voor 4 → 3 (persoonlijke kring) — beslissing blijft bij admin.
        """
        current = user.get("gradatie", 7)
        if current != 4:
            return None
        gesprekken = user.get("gesprekken_count", 0)
        trust = user.get("trust_score", 0)
        # Heuristiek: veel positieve interactie + hoge trust
        if gesprekken >= 50 and trust >= 80:
            return {
                "from": 4, "to": 3,
                "reden": f"{user.get('naam')} heeft {gesprekken} gesprekken en trust {trust}. Misschien je persoonlijke kring waardig?",
                "admin_action_required": True,
            }
        return None
