from typing import Optional, Dict, Tuple
from utils.data_manager import DataManager
from utils.logger import SparkLogger
from models.user import User, UserCreate

class AuthService:
    @staticmethod
    def authenticate_user(naam: str, sleutelwoord: Optional[str] = None, masterkey: Optional[str] = None) -> Tuple[Optional[Dict], bool]:
        """
        Authenticate user with sleutelwoord or masterkey
        Returns: (user_data, is_masterkey_used)
        """
        users = DataManager.load_users()
        
        # Find user by naam (exact match or first name match)
        matching_users = []
        for u in users:
            # Exact match (full name)
            if u["naam"].lower() == naam.lower():
                matching_users.append(u)
            # Partial match (e.g., "Maurice" matches "Maurice Maas")
            elif naam.lower() in u["naam"].lower():
                matching_users.append(u)
            # First name match (e.g., "Willem" matches "Willem Spakman")
            elif u["naam"].split()[0].lower() == naam.lower():
                matching_users.append(u)
        
        if not matching_users:
            return None, False
        
        # Check for masterkey first
        if masterkey and masterkey.upper() == "SAMEN":
            # Find user with masterkey privilege (gradatie 1)
            for user in matching_users:
                if user.get("masterkey") == "SAMEN":
                    SparkLogger.log_masterkey_attempt(user["naam"], user.get("sleutelwoord"), True)
                    return user, True
            
            # Masterkey attempt failed
            SparkLogger.log_masterkey_attempt(naam, sleutelwoord, False)
            return None, False
        
        # Check sleutelwoord
        if sleutelwoord:
            for user in matching_users:
                # Match sleutelwoord (case-insensitive, flexible matching)
                user_keyword = user.get("sleutelwoord", "").lower().strip()
                input_keyword = sleutelwoord.lower().strip()
                
                if user_keyword == input_keyword:
                    return user, False
        
        # If multiple users with same naam, need sleutelwoord
        if len(matching_users) > 1:
            return None, False
        
        # Single user found but no sleutelwoord provided
        return None, False
    
    @staticmethod
    def register_user(user_create: UserCreate) -> User:
        """
        Register new user with default gradatie 7
        """
        users = DataManager.load_users()
        
        # Check if naam + sleutelwoord combo already exists
        existing = [u for u in users if u["naam"] == user_create.naam and u["sleutelwoord"] == user_create.sleutelwoord]
        if existing:
            raise ValueError(f"Gebruiker {user_create.naam} met sleutelwoord {user_create.sleutelwoord} bestaat al")
        
        # Create new user
        new_user = User(
            naam=user_create.naam,
            volledige_naam=user_create.volledige_naam or user_create.naam,
            sleutelwoord=user_create.sleutelwoord,
            gradatie=7,
            rol="Onbekende"
        )
        
        # Add to database
        users.append(new_user.model_dump())
        DataManager.save_users(users)
        
        # Log
        SparkLogger.log_new_user(new_user.naam, new_user.sleutelwoord, new_user.gradatie)
        
        return new_user
    
    @staticmethod
    def update_user_activity(user_id: str):
        """
        Update user's last_active, gesprekken_count, and trust_score
        """
        from datetime import datetime
        users = DataManager.load_users()
        
        for user in users:
            if user["id"] == user_id:
                user["last_active"] = datetime.utcnow().isoformat()
                user["gesprekken_count"] = user.get("gesprekken_count", 0) + 1
                
                # Update trust_score: +1 per bericht (max 100)
                current_trust = user.get("trust_score", 0)
                user["trust_score"] = min(current_trust + 1, 100)
                
                break
        
        DataManager.save_users(users)
    
    @staticmethod
    def check_auto_gradatie_growth(user: Dict) -> Optional[int]:
        """
        Check if user should auto-grow in gradatie
        Returns new gradatie if changed, None otherwise
        """
        from datetime import datetime, timedelta
        
        current_gradatie = user.get("gradatie", 7)
        gesprekken = user.get("gesprekken_count", 0)
        trust_score = user.get("trust_score", 0)
        
        # Parse registered_date
        try:
            registered = datetime.fromisoformat(user.get("registered_date", datetime.utcnow().isoformat()))
            days_active = (datetime.utcnow() - registered).days
        except:
            days_active = 0
        
        # Gradatie 7 -> 6
        if current_gradatie == 7 and gesprekken >= 5 and days_active >= 7 and trust_score >= 30:
            return 6
        
        # Gradatie 6 -> 5
        if current_gradatie == 6 and gesprekken >= 15 and days_active >= 30 and trust_score >= 60:
            return 5
        
        return None
    
    @staticmethod
    def update_gradatie(user_id: str, new_gradatie: int, reden: str, handmatig: bool = False):
        """
        Update user gradatie
        """
        users = DataManager.load_users()
        
        for user in users:
            if user["id"] == user_id:
                old_gradatie = user.get("gradatie", 7)
                user["gradatie"] = new_gradatie
                
                # Update rol based on gradatie
                gradaties_data = DataManager.load_json("system/gradaties.json")
                for g in gradaties_data.get("gradaties", []):
                    if g["niveau"] == new_gradatie:
                        user["rol"] = g["titel"]
                        break
                
                # Log
                SparkLogger.log_gradatie_change(
                    user["naam"],
                    user["sleutelwoord"],
                    old_gradatie,
                    new_gradatie,
                    reden,
                    handmatig
                )
                
                break
        
        DataManager.save_users(users)
    
    @staticmethod
    def validate_session(user_id: str) -> bool:
        """
        Validate if user session is still active
        Returns: True if session valid, False if expired
        """
        from datetime import datetime, timedelta
        
        users = DataManager.load_users()
        user = next((u for u in users if u["id"] == user_id), None)
        
        if not user:
            return False
        
        # Check last_active timestamp
        last_active_str = user.get("last_active")
        if not last_active_str:
            return True  # No timestamp yet, allow
        
        try:
            last_active = datetime.fromisoformat(last_active_str)
            now = datetime.utcnow()
            
            # Session expires after 5 minutes of inactivity
            if now - last_active > timedelta(minutes=5):
                print(f"[SESSION] User {user['naam']} session expired (inactive for {(now - last_active).seconds}s)")
                return False
            
            return True
        except Exception as e:
            print(f"[SESSION ERROR] Could not parse last_active: {e}")
            return True  # Fail-safe: allow if timestamp is malformed
    
    @staticmethod
    def heartbeat(user_id: str) -> Dict:
        """
        Update user's last_active timestamp (heartbeat)
        Returns: Session status
        """
        from datetime import datetime, timedelta
        
        users = DataManager.load_users()
        user = next((u for u in users if u["id"] == user_id), None)
        
        if not user:
            return {"status": "invalid", "message": "User not found"}
        
        # Update last_active
        now = datetime.utcnow()
        user["last_active"] = now.isoformat()
        DataManager.save_users(users)
        
        # Calculate time until expiry (5 minutes from now)
        expires_at = now + timedelta(minutes=5)
        seconds_until_expiry = 300  # 5 minutes
        
        return {
            "status": "active",
            "user_id": user_id,
            "naam": user["naam"],
            "gradatie": user["gradatie"],
            "expires_in": seconds_until_expiry,
            "last_active": now.isoformat()
        }
    
    @staticmethod
    def delete_user(user_id: str, sleutelwoord: str) -> bool:
        """
        Delete user (with backup)
        """
        users = DataManager.load_users()
        
        for i, user in enumerate(users):
            if user["id"] == user_id and user["sleutelwoord"] == sleutelwoord:
                # Create backup
                backup_file = DataManager.backup_user(user)
                
                # Log
                stats = {
                    "gesprekken": user.get("gesprekken_count", 0),
                    "dagboek": 0  # TODO: count diary entries
                }
                SparkLogger.log_deleted_user(user["naam"], user["sleutelwoord"], backup_file, stats)
                
                # Remove from list
                users.pop(i)
                DataManager.save_users(users)
                
                return True
        
        return False
