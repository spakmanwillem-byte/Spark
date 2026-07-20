"""
Achievement Dispatcher Service (v7 refactor)
============================================
Dispatcher-patroon volgens Spark-modulestijl (zoals trade/monitor.py facade).

De service zelf doet géén achievement-logic meer — die is verplaatst naar
sub-agents in `agents/*.py`. Elke sub-agent handelt één (of meerdere) types af:

    - KBAchievementAgent       → 'words', 'letter_completion'
    - RPSAchievementAgent      → 'rps'
    - MilestoneAchievementAgent→ 'milestones', 'contributions'

Blueprint-koppeling per agent: `blueprints/{name}.json` — admin-editable.

Meta: zie `_meta.json`
Blueprint doc: `/memory/blueprints/achievements.md`
"""
from pathlib import Path
from modules.core.storage import load_json, save_json
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

from .agents import (
    BaseAchievementAgent,
    KBAchievementAgent,
    RPSAchievementAgent,
    MilestoneAchievementAgent,
)

DATA_DIR = Path(__file__).parent.parent.parent / "data"
ACHIEVEMENTS_FILE = DATA_DIR / "achievements.json"
KNOWLEDGE_FILE = DATA_DIR / "knowledge" / "learned_knowledge" / "knowledge_base.json"
KBV2_DIR = DATA_DIR / "knowledge" / "v2"
USERS_FILE = DATA_DIR / "system" / "users.json"


def _load_kbv2_entries():
    """v6_v2_first_001 — V2 kaarten (4 lades + inbox) als platte lijst."""
    out = []
    for fname in ["knowledge_v2_doen", "knowledge_v2_weten",
                  "knowledge_v2_voelen", "knowledge_v2_spreken",
                  "knowledge_inbox"]:
        d = load_json(KBV2_DIR / f"{fname}.json", default={"kaarten": []})
        out.extend(d.get("kaarten", []) or [])
    return out


class AchievementService:
    """
    Dispatcher — delegeert unlock-checks naar de juiste sub-agent per achievement.type.
    """

    def __init__(self):
        # Registry van sub-agents in vaste volgorde (bepaalt check-volgorde)
        self._agents: List[BaseAchievementAgent] = [
            KBAchievementAgent(),
            RPSAchievementAgent(),
            MilestoneAchievementAgent(),
        ]

    # =========== Public API ===========

    def get_all(self):
        """Return all achievements with system stats"""
        achievements = self._get_achievements()
        return {
            "achievements": achievements,
            "total": len(achievements),
            "total_xp_available": sum(a.get("xp_reward", 0) for a in achievements),
            "agents": [{"class": a.__class__.__name__,
                        "handles_types": a.handles_types,
                        "blueprint": a.blueprint_name} for a in self._agents],
        }

    def get_user_progress(self, user_id: str):
        """Retroactive unlock + progress info voor alle achievements."""
        user = self._get_user(user_id)
        if not user:
            return None

        achievements = self._get_achievements()
        context = self._build_context(user_id)

        user_ach = user.get("achievements", {}) or {}
        unlocked = list(user_ach.get("unlocked", []) or [])
        unlocked_ids = [a.get("id") for a in unlocked]
        total_xp = user_ach.get("total_xp_from_achievements", 0)

        # Dispatch: elk achievement naar juiste agent
        newly_unlocked: List[Dict[str, Any]] = []
        for ach in achievements:
            if ach["id"] in unlocked_ids:
                continue
            agent = self._route(ach)
            if agent is None:
                continue
            entry = agent.check_unlock(user, ach, context)
            if entry is not None:
                unlocked.append(entry)
                unlocked_ids.append(entry["id"])
                total_xp += entry.get("xp_reward", 0)
                newly_unlocked.append(entry)

        # Save if new unlocks
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
                            user_id=user_id, amount=reward,
                            reason=f"Achievement: {u.get('name','?')}",
                        )
            except Exception as ex:
                print(f"[achievements] grant_xp failed: {ex}")

        # Volgende milestone (alleen word-based voor preview)
        next_milestone = self._compute_next_milestone(achievements, unlocked_ids, context)

        total_achievements = len(achievements)
        total_unlocked = len(unlocked)
        pct = round((total_unlocked / total_achievements * 100), 1) if total_achievements > 0 else 0

        return {
            "user_naam": user.get("naam", ""),
            "user_gradatie": user.get("gradatie", 1),
            "word_count": context["word_count"],
            "unlocked": unlocked,
            "total_unlocked": total_unlocked,
            "total_achievements": total_achievements,
            "progress_percentage": pct,
            "total_xp_earned": total_xp,
            "next_milestone": next_milestone,
            "newly_unlocked": newly_unlocked,
            "letter_status": context["letter_status"],  # v7 letter progress voor UI
        }

    def unlock_manual(self, user_id: str, achievement_id: str) -> dict:
        """Manual unlock — voor trigger-based (avatar upload, first token, etc.)"""
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

        # Route naar agent voor consistente unlock_entry-opbouw (fallback: default)
        agent = self._route(target)
        entry = agent._build_unlock_entry(target) if agent else {
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
                xp_service.grant_xp(user_id=user_id, amount=reward,
                                    reason=f"Achievement: {target.get('name','?')}")
        except Exception as ex:
            print(f"[achievements] grant_xp failed: {ex}")
        return {"success": True, "already_unlocked": False, "achievement": entry,
                "xp_granted": target.get("xp_reward", 0)}

    def get_blueprints(self) -> Dict[str, Any]:
        """v7_admin_placeholder — return alle sub-agent blueprints (voor admin UI)."""
        out = {}
        for agent in self._agents:
            if agent.blueprint_name:
                out[agent.blueprint_name] = {
                    "agent_class": agent.__class__.__name__,
                    "handles_types": agent.handles_types,
                    "blueprint": agent.blueprint(),
                }
        return out

    # =========== Private ===========

    def _route(self, achievement: Dict[str, Any]) -> Optional[BaseAchievementAgent]:
        """Find the agent that handles this achievement's type."""
        for agent in self._agents:
            if agent.can_handle(achievement):
                return agent
        return None

    def _get_achievements(self):
        data = load_json(ACHIEVEMENTS_FILE, default={"achievements": []})
        return data.get("achievements", [])

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

    def _get_word_count(self, user_id: str = None):
        """Count active knowledge entries (per-user of globaal)."""
        data = load_json(KNOWLEDGE_FILE, default={"knowledge_entries": []})
        entries = data.get("knowledge_entries", [])
        entries = entries + _load_kbv2_entries()
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

    def _get_rps_stats(self, user_id: str) -> dict:
        rps_file = DATA_DIR / "games" / "rps" / "stats.json"
        d = load_json(rps_file, default={"stats": {}})
        return d.get("stats", {}).get(user_id, {"wins": 0, "losses": 0, "ties": 0, "total": 0})

    def _compute_letter_status(self) -> Dict[str, Dict[str, int]]:
        """Compute empty/filled per letter A-Z in één pass."""
        import string as _string, unicodedata as _ud
        out = {c: {"empty": 0, "filled": 0} for c in _string.ascii_uppercase}
        for e in _load_kbv2_entries():
            begrip = (e.get("begrip") or "").strip()
            if not begrip:
                continue
            first = begrip[0].upper()
            first_norm = _ud.normalize("NFKD", first).encode("ascii", "ignore").decode() or first
            if first_norm not in out:
                continue
            lagen = e.get("lagen") or {}
            has_content = bool((lagen.get("laag1") or "").strip())
            if has_content:
                out[first_norm]["filled"] += 1
            else:
                out[first_norm]["empty"] += 1
        return out

    def _build_context(self, user_id: str) -> Dict[str, Any]:
        """Pre-compute alle data die sub-agents nodig hebben — één keer per request."""
        return {
            "word_count": self._get_word_count(user_id),
            "rps_stats": self._get_rps_stats(user_id),
            "letter_status": self._compute_letter_status(),
        }

    def _compute_next_milestone(self, achievements, unlocked_ids, context) -> Optional[Dict[str, Any]]:
        """Preview van volgende woord-milestone (skip letter_completion / rps in preview)."""
        word_ms = [a for a in achievements
                   if isinstance(a.get("milestone"), int)
                   and a.get("type") not in ("rps", "letter_completion")]
        wc = context.get("word_count", 0)
        for ach in sorted(word_ms, key=lambda a: a.get("milestone", 0)):
            if ach["id"] not in unlocked_ids:
                return {
                    **ach,
                    "current_progress": wc,
                    "remaining": max(0, ach.get("milestone", 0) - wc),
                }
        return None


# Module-level singleton
_service_singleton = AchievementService()


def unlock_milestone(user_id: str, achievement_id: str) -> dict:
    """Cross-module hook — voor avatar-upload, first-token, etc."""
    return _service_singleton.unlock_manual(user_id, achievement_id)
