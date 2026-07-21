"""ChatHubMaster — root-dispatcher voor alle chat_hub agents.

meta: master (rol=master). Doet zelf geen werk, alleen routing + mergen.
Groeit door leaves toe te voegen. Bij >4 children op één master → promotie.
"""
from __future__ import annotations
from typing import Any, Dict, List
from pathlib import Path
import json
from .base.master_contract import MasterContract
from .agents.papertrail_agent import PapertrailAgent
from .agents.module_meta_agent import ModuleMetaAgent
from .agents.module_info_agent import ModuleInfoAgent
from .agents.heal_agent import HealAgent

HUB_DIR = Path(__file__).parent


class ChatHubMaster(MasterContract):
    """Root van de chat-agent-tree."""

    def __init__(self, **data):
        super().__init__(
            naam="chat_hub_master",
            doel="Root dispatcher — routeert user-vragen naar juiste leaf-agent en merged output.",
            rol="master",
            parent="",
            children=[
                PapertrailAgent(),
                ModuleMetaAgent(),
                ModuleInfoAgent(),
                HealAgent(),
            ],
            footnote={
                "generated_by": "v10_chat_hub_fase1",
                "created": "2026-07-21",
                "philosophy": "Master doet geen werk, alleen routing. Leaves doen taken. Quad-tree principe.",
            },
            **data
        )

    def manifest(self) -> Dict[str, Any]:
        """Retourneer volledige tree als manifest (voor UI/admin/spark-self-awareness)."""
        return {
            "master": self.to_manifest(),
            "children_detail": [c.to_manifest() for c in self.children],
            "split_check": self._split_check(),
        }

    def _split_check(self) -> Dict[str, Any]:
        """Check of we tegen split-drempels aan lopen."""
        rules = self.split_rules
        child_count = len(self.children)
        needs_split = child_count > rules.get("master_max_children", 4)
        return {
            "current_children": child_count,
            "max_children": rules.get("master_max_children", 4),
            "needs_promotion": needs_split,
            "note": "Als children > 4 → promoot 1 leaf naar sub-master met eigen children."
                    if needs_split else "OK, binnen limits.",
        }


# Singleton
_hub = ChatHubMaster()


def get_hub() -> ChatHubMaster:
    return _hub
