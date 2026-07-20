"""
BaseAchievementAgent
====================
Abstracte basis voor alle achievement sub-agents.
Elke sub-agent handelt één achievement-type af (bv. 'letter_completion', 'rps', 'words').

Blueprint-koppeling:
- Runtime-config (XP-waarden, banner-texts, thresholds) leeft in JSON blueprints.
- Blueprint pad: `backend/modules/achievements/blueprints/{name}.json`
- Admin kan later via UI dit aanpassen zonder code-wijziging.
"""
from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Optional
from modules.core.storage import load_json
from datetime import datetime, timezone


BLUEPRINTS_DIR = Path(__file__).parent.parent / "blueprints"


class BaseAchievementAgent:
    """Abstracte base — sub-agents overschrijven `handles_type` en `check_unlock`."""

    # Types dit agent kan handelen (bv. ['words'] of ['letter_completion'])
    handles_types: List[str] = []
    blueprint_name: Optional[str] = None  # naam van JSON in blueprints/

    def __init__(self):
        self._blueprint_cache: Optional[Dict[str, Any]] = None

    def blueprint(self) -> Dict[str, Any]:
        """Lees blueprint JSON (cached per agent-instance)."""
        if self._blueprint_cache is not None:
            return self._blueprint_cache
        if not self.blueprint_name:
            self._blueprint_cache = {}
            return {}
        path = BLUEPRINTS_DIR / f"{self.blueprint_name}.json"
        self._blueprint_cache = load_json(path, default={}) or {}
        return self._blueprint_cache

    def can_handle(self, achievement: Dict[str, Any]) -> bool:
        """Return True als deze agent het achievement-type kan afhandelen."""
        return achievement.get("type") in self.handles_types

    # ----- Uit te breiden door sub-agents -----

    def check_unlock(self, user: Dict[str, Any], achievement: Dict[str, Any],
                     context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Check of user achievement mag unlocken.
        `context` bevat pre-computed data (word_count, rps_stats, letter_status, etc.).
        Returns: unlock_entry dict OF None.
        """
        raise NotImplementedError

    def progress(self, user: Dict[str, Any], achievement: Dict[str, Any],
                 context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Return progress-info voor UI (bv. {'current': 289, 'target': 300, 'pct': 96}).
        Default: leeg.
        """
        return {}

    # ----- Helpers -----

    def _build_unlock_entry(self, achievement: Dict[str, Any], **extra) -> Dict[str, Any]:
        entry = {
            "id": achievement["id"],
            "name": achievement["name"],
            "description": achievement["description"],
            "milestone": achievement.get("milestone"),
            "xp_reward": achievement.get("xp_reward", 0),
            "icon": achievement.get("icon", ""),
            "rarity": achievement.get("rarity", "common"),
            "type": achievement.get("type", "words"),
            "unlocked_at": datetime.now(timezone.utc).isoformat(),
        }
        entry.update(extra)
        return entry
