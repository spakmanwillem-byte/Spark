"""
RPSAchievementAgent
===================
Handelt Rock-Paper-Scissors achievements af.
Type: "rps" — milestone tegen `stat_field` in rps_stats (wins/losses/total).

Blueprint: `blueprints/rps_achievements.json`
"""
from __future__ import annotations
from typing import Any, Dict, Optional
from .base_agent import BaseAchievementAgent


class RPSAchievementAgent(BaseAchievementAgent):
    handles_types = ["rps"]
    blueprint_name = "rps_achievements"

    def check_unlock(self, user, achievement, context) -> Optional[Dict[str, Any]]:
        rps_stats = context.get("rps_stats") or {}
        stat_field = achievement.get("stat_field", "wins")
        milestone = achievement.get("milestone")
        if not isinstance(milestone, int):
            return None
        current = rps_stats.get(stat_field, 0)
        if current < milestone:
            return None
        return self._build_unlock_entry(achievement, stat_field=stat_field, current=current)

    def progress(self, user, achievement, context) -> Dict[str, Any]:
        rps_stats = context.get("rps_stats") or {}
        stat_field = achievement.get("stat_field", "wins")
        current = rps_stats.get(stat_field, 0)
        target = achievement.get("milestone", 0) or 0
        return {
            "stat_field": stat_field, "current": current, "target": target,
            "pct": min(100, round(current / target * 100)) if target else 0,
        }
