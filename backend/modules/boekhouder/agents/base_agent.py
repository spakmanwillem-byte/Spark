"""
BaseFinanceAgent — abstract base voor alle boekhouder sub-agents.
Blueprint: `../blueprints/finance_hub.json` (sectie `sub_agents[topic]`)
"""
from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, Optional
from modules.core.storage import load_json

BLUEPRINT_FP = Path(__file__).parent.parent / "blueprints" / "finance_hub.json"
DATA = Path(__file__).parent.parent.parent.parent / "data"


class BaseFinanceAgent:
    topic: str = "unknown"
    _cache: Optional[Dict[str, Any]] = None

    def blueprint(self) -> Dict[str, Any]:
        d = load_json(BLUEPRINT_FP, default={}) or {}
        return d.get("sub_agents", {}).get(self.topic, {})

    def full_blueprint(self) -> Dict[str, Any]:
        return load_json(BLUEPRINT_FP, default={}) or {}

    def snapshot(self, user_id: str) -> Dict[str, Any]:
        """Elke agent overschrijft dit — return zijn deel van het financiële beeld."""
        return {}
