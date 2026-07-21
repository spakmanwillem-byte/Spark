"""MasterContract — typed base voor Master-agents (routers).

Master doet ZELF geen werk. Alleen: routing, mergen, cross-cutting (logging, timing).
Als een leaf te groot wordt → promotie naar Master (rol=master, krijgt children).
"""
from __future__ import annotations
from typing import Any, Dict, List
from pydantic import BaseModel, Field
from .agent_contract import AgentContract


class MasterContract(BaseModel):
    """Routing-only contract. Business-logic hoort in leaves."""

    naam: str
    doel: str
    rol: str = "master"
    parent: str = ""
    children: List[AgentContract] = Field(default_factory=list)
    split_rules: Dict[str, int] = Field(default_factory=lambda: {
        "leaf_max_lines": 400, "master_max_children": 4, "max_depth": 3,
    })
    footnote: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        arbitrary_types_allowed = True

    def route(self, text: str, viewer_gradatie: int = 3) -> List[AgentContract]:
        """Vind alle children die deze vraag claimen."""
        return [c for c in self.children if c.matches(text, viewer_gradatie)]

    def dispatch(self, text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Router: run alle matchende children, merge output."""
        vg = int((context or {}).get("viewer_gradatie", 3) or 3)
        matched = self.route(text, viewer_gradatie=vg)
        if not matched:
            return {"matched": [], "results": [], "message": None}

        results = []
        for agent in matched:
            try:
                out = agent.run(text, context)
                results.append({
                    "agent": agent.naam, "klasse": agent.klasse, "output": out,
                })
            except Exception as e:
                results.append({
                    "agent": agent.naam, "error": str(e),
                })
        return {
            "matched": [a.naam for a in matched],
            "results": results,
        }

    def to_manifest(self) -> Dict[str, Any]:
        return {
            "naam": self.naam, "rol": self.rol, "doel": self.doel,
            "children": [c.naam for c in self.children],
            "child_count": len(self.children),
            "split_rules": self.split_rules,
        }
