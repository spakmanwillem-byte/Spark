"""
MilestoneAchievementAgent
=========================
Handelt trigger-based milestone achievements af (avatar-upload, first-token, etc.).
Deze worden NIET automatisch unlockt door retroactive check —
ze worden vanuit andere modules aangeroepen via `service.unlock_milestone(user_id, achievement_id)`.

Type: "milestones" (of "contributions" of andere zonder milestone-int)

Blueprint: `blueprints/milestone_achievements.json`
"""
from __future__ import annotations
from typing import Any, Dict, Optional
from .base_agent import BaseAchievementAgent


class MilestoneAchievementAgent(BaseAchievementAgent):
    handles_types = ["milestones", "contributions"]
    blueprint_name = "milestone_achievements"

    def check_unlock(self, user, achievement, context) -> Optional[Dict[str, Any]]:
        """
        Trigger-based achievements worden alleen handmatig unlockt via
        `service.unlock_manual`. Retroactive check doet niks tenzij
        achievement een `milestone` int heeft (dan gedraagt het zich als word-achievement).
        """
        milestone = achievement.get("milestone")
        if isinstance(milestone, int) and milestone > 0:
            # Fallback: word_count based
            if context.get("word_count", 0) < milestone:
                return None
            return self._build_unlock_entry(achievement)
        return None  # niks doen — wacht op manual unlock
