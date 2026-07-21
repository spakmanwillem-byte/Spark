"""ModuleInfoAgent — "vertel over X" waar X = module.

Onderscheid van ModuleMetaAgent: dit is een user-facing "leg uit" intent.
ModuleMetaAgent geeft ruwe meta; ModuleInfoAgent bouwt vriendelijke prose.

meta: leaf, info_lookup. Vangt de fantoom-vraag "vertel over spark trader".
"""
from __future__ import annotations
from typing import Any, Dict, List
import re
from ..base.agent_contract import AgentContract
from .module_meta_agent import ModuleMetaAgent


# Alias-map: user zegt niet altijd de exacte module-naam
_ALIASES = {
    "spark trader": "trade", "trader": "trade", "trade bot": "trade",
    "kennisbank": "kb_v2", "kb": "kb_v2",
    "boekhouder": "boekhouder", "boekhouding": "boekhouder", "boekhoud": "boekhouder",
    "agenda": "agenda", "achievements": "achievements",
    "shop": "shop", "winkel": "shop",
    "wallet": "wallet", "portemonnee": "wallet",
    "notities": "notes", "notes": "notes",
    "help": "help", "spark hulp": "help",
    "dnd": "dnd", "spark world": "dnd",
    "analytics": "analytics",
    "graph": "graph", "grafiek": "graph",
    "monitor": "trade", "spark monitor": "trade",
}


class ModuleInfoAgent(AgentContract):
    naam: str = "module_info"
    klasse: str = "info_lookup"
    rol: str = "leaf"
    parent: str = "chat_hub_master"
    doel: str = "Beantwoordt 'vertel over X' waar X een module is (trade, kb, boekhouder, ...)."
    gradatie_min: int = 3
    kost_ms_estimate: int = 20
    triggers: List[str] = [
        # "vertel over TRADER" (met trailing module-woord)
        r"\bvertel\s+(eens\s+)?over\s+(spark\s+)?(trader|trade|kb|kennisbank|boekhouder|boekhouding|agenda|achievements?|shop|winkel|wallet|portemonnee|notities|help|dnd|analytics|graph|monitor)\b",
        r"\bleg\s+(de\s+)?(trader|trade|kb|kennisbank|boekhouder|agenda|shop|wallet|help|dnd)\s+uit\b",
        r"\bwat\s+is\s+(de\s+)?spark[- ]?(trader|monitor|world)\b",
        r"\bhoe\s+werkt\s+(de\s+)?(spark\s+)?(trader|kb|kennisbank|boekhouder|shop|wallet|agenda)\b",
    ]
    footnote: Dict[str, Any] = {
        "generated_by": "v10_chat_hub_fase1", "created": "2026-07-21",
    }

    def run(self, text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        # 1. Detecteer welke module
        module_key = self._detect_module(text)
        if not module_key:
            return {"error": "geen bekende module in vraag gevonden",
                    "aliases": sorted(set(_ALIASES.keys()))}

        # 2. Roep meta-agent aan
        meta = ModuleMetaAgent().read_module_meta(module_key)
        if meta.get("error"):
            return meta

        # 3. Bouw prose-antwoord
        parts = [f"**Module `{meta['module']}`**"]
        if meta.get("doel"):
            parts.append(f"\n🎯 Doel: {meta['doel']}")
        if meta.get("sub_agents"):
            parts.append(f"\n🧩 Sub-agents: {', '.join(meta['sub_agents'][:6])}")
        if meta.get("has_blueprint"):
            parts.append("\n📘 Heeft blueprint(s) → admin-editable regels")
        endp = meta.get("endpoints", []) or []
        if endp:
            names = [e if isinstance(e, str) else (e.get("path") or str(e)) for e in endp[:5]]
            parts.append(f"\n🔌 Endpoints: {', '.join(names)}")
        fn = meta.get("footnote", {})
        if isinstance(fn, dict) and fn.get("spark_note"):
            parts.append(f"\n💬 Spark's eigen note: _{fn['spark_note'][:200]}_")

        return {
            "module": meta["module"],
            "prose": "".join(parts),
            "raw_meta": meta,
        }

    def _detect_module(self, text: str) -> str:
        low = (text or "").lower()
        # Match multi-word aliases first (spark trader → trade)
        for alias in sorted(_ALIASES.keys(), key=lambda x: -len(x)):
            if alias in low:
                return _ALIASES[alias]
        return ""
