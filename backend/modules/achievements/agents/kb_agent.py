"""
KBAchievementAgent
==================
Handelt kennisbank-gebaseerde achievements af:
  - `type: "words"`       — milestone op basis van totaal aantal (user-bijdragen)
  - `type: "letter_completion"` — unlock als alle inbox-skeletons voor een letter gevuld zijn

Blueprint: `blueprints/kb_achievements.json`
Bevat XP-waarden, texts, min_filled threshold voor letter_completion.
"""
from __future__ import annotations
from typing import Any, Dict, Optional
from .base_agent import BaseAchievementAgent


class KBAchievementAgent(BaseAchievementAgent):
    handles_types = ["words", "letter_completion"]
    blueprint_name = "kb_achievements"

    def check_unlock(self, user, achievement, context) -> Optional[Dict[str, Any]]:
        atype = achievement.get("type")
        if atype == "words":
            return self._check_words(user, achievement, context)
        if atype == "letter_completion":
            return self._check_letter(user, achievement, context)
        return None

    def progress(self, user, achievement, context) -> Dict[str, Any]:
        atype = achievement.get("type")
        if atype == "words":
            wc = context.get("word_count", 0)
            target = achievement.get("milestone", 0) or 0
            return {"current": wc, "target": target,
                    "pct": min(100, round(wc / target * 100)) if target else 0}
        if atype == "letter_completion":
            letter = (achievement.get("letter") or "").upper()[:1]
            ls = (context.get("letter_status") or {}).get(letter, {"empty": 0, "filled": 0})
            total = ls["empty"] + ls["filled"]
            return {
                "letter": letter,
                "filled": ls["filled"], "empty": ls["empty"], "total": total,
                "pct": round(ls["filled"] / total * 100) if total else 0,
            }
        return {}

    # ----- private -----

    def _check_words(self, user, achievement, context):
        milestone = achievement.get("milestone")
        if not isinstance(milestone, int):
            return None
        if context.get("word_count", 0) < milestone:
            return None
        return self._build_unlock_entry(achievement)

    def _check_letter(self, user, achievement, context):
        letter = (achievement.get("letter") or "").upper()[:1]
        if not letter:
            return None
        letter_status = context.get("letter_status") or {}
        status = letter_status.get(letter, {"empty": 0, "filled": 0})
        bp = self.blueprint()
        min_filled = bp.get("letter_completion", {}).get("min_filled_to_unlock", 1)
        if status["empty"] == 0 and status["filled"] >= min_filled:
            return self._build_unlock_entry(achievement, letter=letter)
        return None
