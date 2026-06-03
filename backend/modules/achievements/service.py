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

    def _get_word_count(self, user_id: str = None):
        """Count active knowledge entries.

        v4_leaderboard_002: filter op user_id wanneer beschikbaar zodat elke user
        zijn eigen bijdrage telt. KB-entries gebruiken `detected_by` met NAAM, dus we
        matchen ook op user.naam / user.volledige_naam.
        Fallback zonder user_id: globaal (legacy / admin context).
        """
        data = load_json(KNOWLEDGE_FILE, default={"knowledge_entries": []})
        entries = data.get("knowledge_entries", [])
        active = [e for e in entries if e.get("status", "active") in ("active", "draft")]
        if not user_id:
            return len(active)
        user = self._get_user(user_id)
        if not user:
            return 0
        identifiers = {
            user_id.lower(),
            (user.get("naam") or "").lower(),
            (user.get("volledige_naam") or "").lower(),
        } - {""}
        own = 0
        for e in active:
            cb = (e.get("created_by") or "").lower()
            db = (e.get("detected_by") or "").lower()
            meta_cb = ((e.get("metadata", {}) or {}).get("created_by") or "").lower()
            if cb in identifiers or db in identifiers or meta_cb in identifiers:
                own += 1
        return own

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

    # v5_milestone_unlocks_001 — handmatig unlock voor non-milestone achievements (avatar, tokens, etc.)
    def unlock_manual(self, user_id: str, achievement_id: str) -> dict:
        """Unlock een specifieke achievement voor een user (indien nog niet unlocked).
        Returns: {success, already_unlocked, xp_granted, achievement|None}
        """
        user = self._get_user(user_id)
        if not user:
            return {"success": False, "error": "Gebruiker niet gevonden"}
        achievements = self._get_achievements()
        target = next((a for a in achievements if a.get("id") == achievement_id), None)
        if not target:
            return {"success": False, "error": f"Achievement {achievement_id} bestaat niet"}
        user_ach = user.get("achievements", {}) or {}
        unlocked = list(user_ach.get("unlocked", []))
        if any(u.get("id") == achievement_id for u in unlocked):
            return {"success": True, "already_unlocked": True, "achievement": target}
        entry = {
            "id": target["id"], "name": target["name"], "description": target["description"],
            "milestone": target.get("milestone", 0), "xp_reward": target.get("xp_reward", 0),
            "icon": target.get("icon", ""), "rarity": target.get("rarity", "common"),
            "unlocked_at": datetime.now(timezone.utc).isoformat(),
        }
        unlocked.append(entry)
        total_xp = user_ach.get("total_xp_from_achievements", 0) + target.get("xp_reward", 0)
        self._save_user(user_id, {
            "achievements": {"unlocked": unlocked, "total_xp_from_achievements": total_xp},
        })
        try:
            from modules.chat import xp_service
            reward = target.get("xp_reward", 0)
            if reward > 0:
                xp_service.grant_xp(user_id=user_id, amount=reward, reason=f"Achievement: {target.get('name','?')}")
        except Exception as ex:
            print(f"[achievements] grant_xp failed: {ex}")
        return {"success": True, "already_unlocked": False, "achievement": entry, "xp_granted": target.get("xp_reward", 0)}

    def _get_rps_stats(self, user_id: str) -> dict:
        """v6_achievements_rps_001 — Lees RPS lifetime stats voor user."""
        rps_file = DATA_DIR / "games" / "rps" / "stats.json"
        d = load_json(rps_file, default={"stats": {}})
        return d.get("stats", {}).get(user_id, {"wins": 0, "losses": 0, "ties": 0, "total": 0})

    def get_user_progress(self, user_id):
        """Calculate user's achievement progress based on knowledge count + rps stats"""
        user = self._get_user(user_id)
        if not user:
            return None

        achievements = self._get_achievements()
        word_count = self._get_word_count(user_id)
        rps_stats = self._get_rps_stats(user_id)

        # Get unlocked from user data
        user_ach = user.get("achievements", {})
        unlocked = user_ach.get("unlocked", [])
        unlocked_ids = [a.get("id") for a in unlocked]
        total_xp = user_ach.get("total_xp_from_achievements", 0)

        # Check retroactive: auto-unlock any milestone die de progress al gepasseerd is.
        # v5_milestone_unlocks_001: skip trigger-based milestones (geen "milestone" int veld)
        # v6_achievements_rps_001: voor type='rps' gebruik stat_field tegen rps_stats
        newly_unlocked = []
        milestone_achs = [a for a in achievements if isinstance(a.get("milestone"), int)]
        for ach in sorted(milestone_achs, key=lambda a: a.get("milestone", 0)):
            if ach["id"] in unlocked_ids:
                continue
            if ach.get("type") == "rps":
                # RPS-achievement: vergelijk milestone tegen rps_stats[stat_field]
                stat_field = ach.get("stat_field", "wins")
                current = rps_stats.get(stat_field, 0)
                if current < ach.get("milestone", 0):
                    continue
            else:
                # Default: word-based
                if word_count < ach.get("milestone", 0):
                    continue
            unlock_entry = {
                "id": ach["id"], "name": ach["name"], "description": ach["description"],
                "milestone": ach["milestone"], "xp_reward": ach.get("xp_reward", 0),
                "icon": ach.get("icon", ""), "rarity": ach.get("rarity", "common"),
                "type": ach.get("type", "words"),
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

        # Find next milestone (alleen word-based: skip rps voor "volgende mijlpaal" preview)
        word_milestones = [a for a in milestone_achs if a.get("type") != "rps"]
        next_milestone = None
        for ach in sorted(word_milestones, key=lambda a: a.get("milestone", 0)):
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


# Module-level convenience (v5_milestone_unlocks_001)
_service_singleton = AchievementService()


def unlock_milestone(user_id: str, achievement_id: str) -> dict:
    """Cross-module hook: unlock een mijlpaal-achievement (avatar, first token, etc.)."""
    return _service_singleton.unlock_manual(user_id, achievement_id)

