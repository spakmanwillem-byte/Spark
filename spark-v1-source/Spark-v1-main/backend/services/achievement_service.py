"""
Achievement Service - Simple word-based achievement system

Trigger: words_added → achievement → XP

Tracks:
- Number of words user has taught Spark
- Unlocks achievements at milestones
- Awards XP per achievement
- Retroactive unlock support
"""
from typing import Dict, List, Optional, Tuple
from utils.data_manager import DataManager
from datetime import datetime


class AchievementService:
    """Service voor achievement tracking en unlocking"""
    
    @staticmethod
    def get_all_achievements() -> List[Dict]:
        """Get all available achievements"""
        data = DataManager.load_json("system/achievements.json")
        return data.get("achievements", [])
    
    @staticmethod
    def get_user_word_count(user_id: str) -> int:
        """
        Get number of words (active knowledge entries) user has added
        
        Counts knowledge entries where:
        - created_by matches user_id OR detected_by matches user name (current or previous)
        - status = "active"
        """
        knowledge_data = DataManager.load_json("learned_knowledge/knowledge_base.json")
        entries = knowledge_data.get("knowledge_entries", [])
        
        # Get user data to match name
        users = DataManager.load_users()
        user = next((u for u in users if u.get("id") == user_id), None)
        
        if not user:
            return 0
        
        # Get current and previous names
        user_name = user.get("naam")
        previous_names = user.get("previous_names", [])
        all_names = [user_name] + previous_names if user_name else previous_names
        
        # Count active entries by this user
        count = 0
        for entry in entries:
            if entry.get("status") != "active":
                continue
            
            # Check if user created this
            created_by = entry.get("created_by")  # Legacy field
            created_by_user_id = entry.get("created_by_user_id")  # Current field
            detected_by = entry.get("detected_by")
            
            # Match by user_id (created_by_user_id or created_by) 
            # or by name (detected_by matching current or previous names)
            if created_by_user_id == user_id or created_by == user_id:
                count += 1
            elif detected_by and detected_by in all_names:
                count += 1
        
        return count
    
    @staticmethod
    def get_user_context_count(user_id: str) -> int:
        """
        Get number of context cards user has added
        
        Counts context entries in user's personal context file
        """
        try:
            context_data = DataManager.load_data(f"users/{user_id}/context.json")
            entries = context_data.get("entries", [])
            return len(entries)
        except:
            return 0
    
    @staticmethod
    def get_user_total_contributions(user_id: str) -> int:
        """
        Get total contributions (knowledge + context cards)
        """
        knowledge_count = AchievementService.get_user_word_count(user_id)
        context_count = AchievementService.get_user_context_count(user_id)
        return knowledge_count + context_count
    
    @staticmethod
    def check_achievements(user_id: str, word_count: Optional[int] = None) -> List[Dict]:
        """
        Check which achievements user has unlocked
        
        Uses total contributions (knowledge + context cards)
        
        Returns:
            List of newly unlocked achievements
        """
        # Get user data
        users = DataManager.load_users()
        user = next((u for u in users if u.get("id") == user_id), None)
        if not user:
            return []
        
        # Get current contribution count (knowledge + context)
        if word_count is None:
            word_count = AchievementService.get_user_total_contributions(user_id)
        
        # Get achievements
        all_achievements = AchievementService.get_all_achievements()
        
        # Get already unlocked achievements
        unlocked = user.get("achievements", {}).get("unlocked", [])
        unlocked_ids = [a.get("id") for a in unlocked]
        
        # Check for new unlocks
        newly_unlocked = []
        
        for achievement in all_achievements:
            ach_id = achievement.get("id")
            milestone = achievement.get("milestone", 0)
            
            # Skip if already unlocked
            if ach_id in unlocked_ids:
                continue
            
            # Check if milestone reached
            if word_count >= milestone:
                newly_unlocked.append({
                    "id": ach_id,
                    "name": achievement.get("name"),
                    "description": achievement.get("description"),
                    "milestone": milestone,
                    "xp_reward": achievement.get("xp_reward", 0),
                    "icon": achievement.get("icon", "🏆"),
                    "rarity": achievement.get("rarity", "common"),
                    "unlocked_at": datetime.now().isoformat()
                })
        
        return newly_unlocked
    
    @staticmethod
    def unlock_achievement(user_id: str, achievement_id: str) -> Tuple[bool, str, int]:
        """
        Unlock a specific achievement for user
        
        Returns:
            (success: bool, message: str, xp_awarded: int)
        """
        # Get user data
        users = DataManager.load_users()
        user_index = next((i for i, u in enumerate(users) if u.get("id") == user_id), None)
        
        if user_index is None:
            return False, "User not found", 0
        
        user = users[user_index]
        
        # Get achievement
        all_achievements = AchievementService.get_all_achievements()
        achievement = next((a for a in all_achievements if a.get("id") == achievement_id), None)
        
        if not achievement:
            return False, f"Achievement {achievement_id} not found", 0
        
        # Check if already unlocked
        unlocked = user.get("achievements", {}).get("unlocked", [])
        if any(a.get("id") == achievement_id for a in unlocked):
            return False, "Achievement already unlocked", 0
        
        # Unlock achievement
        xp_reward = achievement.get("xp_reward", 0)
        
        new_unlock = {
            "id": achievement_id,
            "name": achievement.get("name"),
            "description": achievement.get("description"),
            "milestone": achievement.get("milestone"),
            "xp_reward": xp_reward,
            "icon": achievement.get("icon", "🏆"),
            "rarity": achievement.get("rarity", "common"),
            "unlocked_at": datetime.now().isoformat()
        }
        
        # Initialize achievements structure if needed
        if "achievements" not in user:
            user["achievements"] = {
                "unlocked": [],
                "total_xp_from_achievements": 0
            }
        
        # Add to unlocked
        user["achievements"]["unlocked"].append(new_unlock)
        user["achievements"]["total_xp_from_achievements"] = user["achievements"].get("total_xp_from_achievements", 0) + xp_reward
        
        # Add XP to user total
        user["xp"] = user.get("xp", 0) + xp_reward
        
        # Save users
        users[user_index] = user
        DataManager.save_users(users)
        
        return True, f"🎉 Achievement unlocked: {achievement.get('name')}!", xp_reward
    
    @staticmethod
    def unlock_all_eligible(user_id: str) -> List[Dict]:
        """
        Check and unlock all eligible achievements for user
        
        Returns:
            List of newly unlocked achievements with XP
        """
        newly_unlocked = AchievementService.check_achievements(user_id)
        
        results = []
        for achievement in newly_unlocked:
            success, message, xp = AchievementService.unlock_achievement(user_id, achievement["id"])
            if success:
                results.append({
                    **achievement,
                    "xp_awarded": xp
                })
        
        return results
    
    @staticmethod
    def get_user_achievements(user_id: str) -> Dict:
        """
        Get user's achievement progress
        
        Returns:
            {
                "unlocked": List[Dict],
                "total_unlocked": int,
                "total_achievements": int,
                "progress_percentage": float,
                "total_xp_earned": int,
                "next_milestone": Dict or None,
                "knowledge_count": int,
                "context_count": int,
                "total_contributions": int
            }
        """
        users = DataManager.load_users()
        user = next((u for u in users if u.get("id") == user_id), None)
        
        if not user:
            return {
                "unlocked": [],
                "total_unlocked": 0,
                "total_achievements": 0,
                "progress_percentage": 0,
                "total_xp_earned": 0,
                "next_milestone": None,
                "knowledge_count": 0,
                "context_count": 0,
                "total_contributions": 0
            }
        
        # Get unlocked achievements
        unlocked = user.get("achievements", {}).get("unlocked", [])
        total_xp = user.get("achievements", {}).get("total_xp_from_achievements", 0)
        
        # Get all achievements
        all_achievements = AchievementService.get_all_achievements()
        
        # Calculate progress
        total_unlocked = len(unlocked)
        total_achievements = len(all_achievements)
        progress = (total_unlocked / total_achievements * 100) if total_achievements > 0 else 0
        
        # Get contribution counts
        knowledge_count = AchievementService.get_user_word_count(user_id)
        context_count = AchievementService.get_user_context_count(user_id)
        total_contributions = knowledge_count + context_count
        
        # Find next milestone
        unlocked_ids = [a.get("id") for a in unlocked]
        
        next_milestone = None
        for achievement in sorted(all_achievements, key=lambda a: a.get("milestone", 0)):
            if achievement.get("id") not in unlocked_ids:
                next_milestone = {
                    **achievement,
                    "current_progress": total_contributions,
                    "remaining": max(0, achievement.get("milestone", 0) - total_contributions)
                }
                break
        
        return {
            "unlocked": unlocked,
            "total_unlocked": total_unlocked,
            "total_achievements": total_achievements,
            "progress_percentage": round(progress, 1),
            "total_xp_earned": total_xp,
            "next_milestone": next_milestone,
            "knowledge_count": knowledge_count,
            "context_count": context_count,
            "total_contributions": total_contributions
        }
    
    @staticmethod
    def retroactive_unlock(user_id: str) -> Tuple[int, int]:
        """
        Retroactively unlock all eligible achievements based on current word count
        
        Returns:
            (achievements_unlocked: int, total_xp_awarded: int)
        """
        newly_unlocked = AchievementService.unlock_all_eligible(user_id)
        
        total_xp = sum(a.get("xp_awarded", 0) for a in newly_unlocked)
        
        return len(newly_unlocked), total_xp
    
    @staticmethod
    def get_user_id_by_name(user_name: str) -> Optional[str]:
        """Helper: Get user_id from naam"""
        users = DataManager.load_users()
        user = next((u for u in users if u.get("naam") == user_name), None)
        return user.get("id") if user else None
    
    @staticmethod
    def award_xp_for_event(user_id: str, event_type: str) -> Dict:
        """
        Award XP for an event (e.g. snap_to_knowledge, context_created)
        Also checks for achievement unlocks
        
        Returns:
            {
                "success": bool,
                "xp_awarded": int,
                "total_xp": int,
                "new_level": int,
                "level_up": bool,
                "achievements_unlocked": List[Dict]
            }
        """
        # XP amounts per event type
        xp_amounts = {
            "snap_to_knowledge": 10,
            "knowledge_created": 5,
            "context_created": 8,  # NEW: Context card XP
            "bug_report": 15
        }
        
        xp_amount = xp_amounts.get(event_type, 5)
        
        # Get users
        users = DataManager.load_users()
        user_index = next((i for i, u in enumerate(users) if u.get("id") == user_id), None)
        
        if user_index is None:
            return {"success": False, "error": "User not found"}
        
        user = users[user_index]
        
        # Award XP
        old_xp = user.get("xp", 0)
        new_xp = old_xp + xp_amount
        user["xp"] = new_xp
        
        # Calculate level (simple: 100 XP per level)
        old_level = old_xp // 100
        new_level = new_xp // 100
        level_up = new_level > old_level
        
        # Save user
        users[user_index] = user
        DataManager.save_users(users)
        
        # Check for achievement unlocks
        achievements_unlocked = AchievementService.unlock_all_eligible(user_id)
        
        return {
            "success": True,
            "xp_awarded": xp_amount,
            "total_xp": new_xp,
            "new_level": new_level,
            "level_up": level_up,
            "achievements_unlocked": achievements_unlocked
        }
