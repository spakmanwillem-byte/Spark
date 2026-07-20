"""
Achievement Sub-Agents
======================
Elke sub-agent handelt een specifieke achievement-categorie af.
De dispatcher (`service.AchievementService`) delegeert unlock-checks
naar de juiste agent op basis van `achievement.type`.

Ontwerp:
- Elke agent erft van `BaseAchievementAgent`
- Agent leest zijn eigen blueprint uit `../blueprints/*.json`
- Agent implementeert `check_unlock(user, achievement) -> Optional[unlock_entry]`
- Agent implementeert `progress(user, achievement) -> dict` voor UI-preview
"""
from .base_agent import BaseAchievementAgent
from .kb_agent import KBAchievementAgent
from .rps_agent import RPSAchievementAgent
from .milestone_agent import MilestoneAchievementAgent

__all__ = [
    "BaseAchievementAgent",
    "KBAchievementAgent",
    "RPSAchievementAgent",
    "MilestoneAchievementAgent",
]
