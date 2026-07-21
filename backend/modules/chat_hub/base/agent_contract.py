"""AgentContract — typed base voor Leaf-agents in ChatHub.

meta: elke leaf beschrijft z'n eigen naam/klasse/triggers zodat de hub
weet wanneer hem aan te roepen. Zelf-uitlegbaar via .to_manifest().
footnote: {generated_by: v10_chat_hub_fase1, created: 2026-07-21}
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import re


class AgentContract(BaseModel):
    """Basis-contract voor elke leaf-agent."""

    naam: str
    klasse: str  # info_lookup | computation | mutation | decision | notify | guardrail
    doel: str
    rol: str = "leaf"
    parent: str = "chat_hub_master"
    triggers: List[str] = Field(default_factory=list)  # regex patterns
    gradatie_min: int = 3
    kost_ms_estimate: int = 50
    footnote: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True

    def matches(self, text: str, viewer_gradatie: int = 3) -> bool:
        """Check of deze agent de vraag zou willen beantwoorden."""
        if viewer_gradatie > self.gradatie_min:
            # hogere getallen = minder rechten in ons systeem (grad 1 = admin)
            # dus als viewer_gradatie > min → geen toegang
            return False
        low = (text or "").lower()
        for pat in self.triggers:
            try:
                if re.search(pat, low, re.IGNORECASE):
                    return True
            except re.error:
                continue
        return False

    def run(self, text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Override in subclass — retourneer gestructureerde output."""
        raise NotImplementedError(f"{self.naam}.run() niet geïmplementeerd")

    def to_manifest(self) -> Dict[str, Any]:
        return {
            "naam": self.naam, "klasse": self.klasse, "rol": self.rol,
            "doel": self.doel, "parent": self.parent,
            "gradatie_min": self.gradatie_min,
            "trigger_count": len(self.triggers),
        }
