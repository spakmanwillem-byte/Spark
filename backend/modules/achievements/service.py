"""
Achievement Service - Word-based achievement system
Berekent voortgang op basis van kennisbank entries
"""
from pathlib import Path
from modules.core.storage import load_json, save_json
from datetime import datetime, timezone

DATA_DIR = Path(__file__).parent.parent.parent / "data"
ACHIEVEMENTS_FILE = DATA_DIR / "achievements.json"
KNOWLEDGE_FILE = DATA_DIR / "knowledge" / "learned_knowledge" / "knowledge_base.json"
USERS_FILE = DATA_DIR / "system" / "users.json"


class AchievementService:

    def _get_achievements(self):
        data = load_json(ACHIEVEMENTS_FILE, default={"achievements": []})
        return data.get("achievements", [])

    def _get_word_count(self):
        """Count active knowledge entries as word count"""
        data = load_json(KNOWLEDGE_FILE, default={"knowledge_entries": []})
        entries = data.get("knowledge_entries", [])
        return len([e for e in entries if e.get("status", "active") == "active"])

    def _get_user(self, user_id):
        data = load_json(USERS_FILE, default={"users": []})
        for u in data.get("users", []):
            if u.get("id") == user_id:
                return u
        return None

    def _save_user(self, user_id, updates):
        data = load_json(USERS_FILE, default={"users": []})
        for i, u in enumerate(data["users"]):
            if u.get("id") == user_id:
                data["users"][i].update(updates)
                save_json(USERS_FILE, data)
                return True
        return False

    def get_all(self):
        """Return all achievements with system stats"""
        achievements = self._get_achievements()
        return {
            "achievements": achievements,
            "total": len(achievements),
            "total_xp_available": sum(a.get("xp_reward", 0) for a in achievements),
        }

    def get_user_progress(self, user_id):
        """Calculate user's achievement progress based on knowledge count"""
        user = self._get_user(user_id)
        if not user:
            return None

        achievements = self._get_achievements()
        word_count = self._get_word_count()

        # Get unlocked from user data
        user_ach = user.get("achievements", {})
        unlocked = user_ach.get("unlocked", [])
        unlocked_ids = [a.get("id") for a in unlocked]
        total_xp = user_ach.get("total_xp_from_achievements", 0)

        # Check retroactive: auto-unlock any milestone that word_count already passed
        newly_unlocked = []
        for ach in sorted(achievements, key=lambda a: a.get("milestone", 0)):
            if ach["id"] not in unlocked_ids and word_count >= ach.get("milestone", 0):
                unlock_entry = {
                    "id": ach["id"], "name": ach["name"], "description": ach["description"],
                    "milestone": ach["milestone"], "xp_reward": ach.get("xp_reward", 0),
                    "icon": ach.get("icon", ""), "rarity": ach.get("rarity", "common"),
                    "unlocked_at": datetime.now(timezone.utc).isoformat(),
                }
                unlocked.append(unlock_entry)
                unlocked_ids.append(ach["id"])
                total_xp += ach.get("xp_reward", 0)
                newly_unlocked.append(unlock_entry)

        # Save if new unlocks
        # ⚠ FIX 2026-05-19: voorheen overschreef "xp": total_xp de totale user.xp,
        # waardoor bijdragen-XP (van xp_service.grant_xp) verloren ging. Nu: alleen
        # achievement-list opslaan en per nieuwe unlock grant_xp aanroepen (optellend + audit log).
        if newly_unlocked:
            self._save_user(user_id, {
                "achievements": {"unlocked": unlocked, "total_xp_from_achievements": total_xp},
            })
            try:
                from modules.chat import xp_service
                for u in newly_unlocked:
                    reward = u.get("xp_reward", 0)
                    if reward > 0:
                        xp_service.grant_xp(
                            user_id=user_id,
                            amount=reward,
                            reason=f"Achievement: {u.get('name','?')}",
                        )
            except Exception as ex:
                print(f"[achievements] grant_xp failed: {ex}")

        # Find next milestone
        next_milestone = None
        for ach in sorted(achievements, key=lambda a: a.get("milestone", 0)):
            if ach["id"] not in unlocked_ids:
                next_milestone = {
                    **ach,
                    "current_progress": word_count,
                    "remaining": max(0, ach.get("milestone", 0) - word_count),
                }
                break

        total_achievements = len(achievements)
        total_unlocked = len(unlocked)
        pct = round((total_unlocked / total_achievements * 100), 1) if total_achievements > 0 else 0

        return {
            "user_naam": user.get("naam", ""),
            "user_gradatie": user.get("gradatie", 1),
            "word_count": word_count,
            "unlocked": unlocked,
            "total_unlocked": total_unlocked,
            "total_achievements": total_achievements,
            "progress_percentage": pct,
            "total_xp_earned": total_xp,
            "next_milestone": next_milestone,
            "newly_unlocked": newly_unlocked,
        }
