"""
User Profile Service - Manages user personalia (needs, believes, interests, context)
"""
from typing import Dict, Optional, List
from datetime import datetime
from utils.data_manager import DataManager


class UserProfileService:
    """Service for managing user profiles and personalia"""
    
    @staticmethod
    def get_user_profile(user_id: str) -> Optional[Dict]:
        """Get complete profile for a user"""
        users = DataManager.load_users()
        
        for user in users:
            if user.get("id") == user_id:
                # Return user with profile, create default if not exists
                if "profile" not in user:
                    user["profile"] = UserProfileService._create_default_profile()
                return user
        
        return None
    
    @staticmethod
    def get_all_profiles() -> List[Dict]:
        """Get all user profiles (admin only)"""
        users = DataManager.load_users()
        
        profiles = []
        for user in users:
            if "profile" not in user:
                user["profile"] = UserProfileService._create_default_profile()
            
            # Return FULL user object with all fields
            profiles.append(user)
        
        return profiles
    
    @staticmethod
    def update_profile(user_id: str, profile_data: Dict) -> Optional[Dict]:
        """Update user profile"""
        users = DataManager.load_users()
        
        for user in users:
            if user.get("id") == user_id:
                # Initialize profile if not exists
                if "profile" not in user:
                    user["profile"] = UserProfileService._create_default_profile()
                
                # Update fields
                if "need" in profile_data:
                    user["profile"]["need"] = profile_data["need"]
                if "believe" in profile_data:
                    user["profile"]["believe"] = profile_data["believe"]
                if "interesses" in profile_data:
                    user["profile"]["interesses"] = profile_data["interesses"]
                if "context" in profile_data:
                    user["profile"]["context"] = profile_data["context"]
                if "ws5" in profile_data:
                    user["profile"]["ws5"] = profile_data["ws5"]
                if "tags" in profile_data:
                    user["profile"]["tags"] = profile_data["tags"]
                
                # Update gradatie (admin only feature)
                if "gradatie" in profile_data:
                    user["gradatie"] = profile_data["gradatie"]
                
                user["profile"]["updated_at"] = datetime.now().isoformat()
                
                # Save
                DataManager.save_users(users)
                return user
        
        return None
    
    @staticmethod
    def _create_default_profile() -> Dict:
        """Create default empty profile"""
        return {
            "need": "",
            "believe": "",
            "interesses": [],
            "context": "",
            "ws5": {
                "who": "",
                "what": "",
                "when": "",
                "where": "",
                "why": "",
                "how": ""
            },
            "tags": [],
            "updated_at": None
        }
    
    @staticmethod
    def search_by_need(need_keyword: str) -> List[Dict]:
        """Search users by need keyword"""
        users = DataManager.load_users()
        results = []
        
        for user in users:
            profile = user.get("profile", {})
            need = profile.get("need", "").lower()
            
            if need_keyword.lower() in need:
                results.append({
                    "id": user.get("id"),
                    "naam": user.get("naam"),
                    "need": profile.get("need"),
                    "believe": profile.get("believe")
                })
        
        return results
    
    @staticmethod
    def search_by_believe(believe_keyword: str) -> List[Dict]:
        """Search users by believe keyword"""
        users = DataManager.load_users()
        results = []
        
        for user in users:
            profile = user.get("profile", {})
            believe = profile.get("believe", "").lower()
            
            if believe_keyword.lower() in believe:
                results.append({
                    "id": user.get("id"),
                    "naam": user.get("naam"),
                    "need": profile.get("need"),
                    "believe": profile.get("believe")
                })
        
        return results
