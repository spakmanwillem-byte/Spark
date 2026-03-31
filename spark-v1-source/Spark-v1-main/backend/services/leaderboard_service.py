"""
Leaderboard Service - Track top contributors
"""
from typing import List, Dict
from utils.data_manager import DataManager


class LeaderboardService:
    """Service voor leaderboard rankings"""
    
    @staticmethod
    def get_top_contributors(limit: int = 10) -> List[Dict]:
        """
        Get top users by words contributed to Spark
        
        Returns list of users sorted by word count
        Includes matching on previous_names for users who changed their name
        """
        # Get all users
        users = DataManager.load_users()
        
        # Build name-to-user mapping (including previous names)
        name_to_user = {}
        for user in users:
            user_id = user.get("id")
            current_name = user.get("naam")
            previous_names = user.get("previous_names", [])
            
            # Map current name
            if current_name:
                name_to_user[current_name] = user_id
            
            # Map all previous names
            for prev_name in previous_names:
                name_to_user[prev_name] = user_id
        
        # Get knowledge base
        knowledge_data = DataManager.load_json("learned_knowledge/knowledge_base.json")
        entries = knowledge_data.get("knowledge_entries", [])
        
        # Count words per user
        user_word_counts = {}
        
        for entry in entries:
            if entry.get("status") != "active":
                continue
            
            created_by_user_id = entry.get("created_by_user_id")
            created_by = entry.get("created_by")
            detected_by = entry.get("detected_by")
            
            # Try to find user ID
            user_id = created_by_user_id or created_by
            
            if user_id:
                if user_id not in user_word_counts:
                    user_word_counts[user_id] = 0
                user_word_counts[user_id] += 1
            elif detected_by:
                # Find user by name (current or previous)
                user_id = name_to_user.get(detected_by)
                if user_id:
                    if user_id not in user_word_counts:
                        user_word_counts[user_id] = 0
                    user_word_counts[user_id] += 1
        
        # Build leaderboard
        leaderboard = []
        for user in users:
            user_id = user.get("id")
            word_count = user_word_counts.get(user_id, 0)
            
            if word_count > 0:
                # Calculate leven (level) and rank
                # XP determines leven
                xp = user.get("xp", 0)
                leven = xp // 100  # Every 100 XP = 1 level
                rank = leven // 100  # Every 100 levels = 1 rank
                
                leaderboard.append({
                    "rank": 0,  # Will be set after sorting (position in leaderboard)
                    "user_id": user_id,
                    "naam": user.get("naam"),
                    "word_count": word_count,
                    "gradatie": user.get("gradatie"),
                    "xp": xp,
                    "leven": leven,
                    "user_rank": rank,
                    "achievements_count": len(user.get("achievements", {}).get("unlocked", []))
                })
        
        # Sort by word count
        leaderboard.sort(key=lambda x: x["word_count"], reverse=True)
        
        # Set ranks
        for idx, entry in enumerate(leaderboard):
            entry["rank"] = idx + 1
        
        return leaderboard[:limit]
    
    @staticmethod
    def get_user_rank(user_id: str) -> Dict:
        """Get specific user's rank"""
        leaderboard = LeaderboardService.get_top_contributors(limit=1000)
        
        user_entry = next((e for e in leaderboard if e["user_id"] == user_id), None)
        
        if user_entry:
            return {
                "rank": user_entry["rank"],
                "total_users": len(leaderboard),
                "word_count": user_entry["word_count"],
                "percentile": round((1 - (user_entry["rank"] / len(leaderboard))) * 100, 1)
            }
        
        return {
            "rank": None,
            "total_users": len(leaderboard),
            "word_count": 0,
            "percentile": 0
        }
