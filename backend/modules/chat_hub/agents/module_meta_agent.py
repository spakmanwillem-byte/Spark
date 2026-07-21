"""ModuleMetaAgent — leest _meta.json van elke module (doel + footnote + endpoints).

meta: leaf, info_lookup. Reader voor de metadata die sessie 40d heeft ingevuld.
footnote: retourneert doel/footnote/endpoints per module-naam.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from pathlib import Path
import json
from ..base.agent_contract import AgentContract

BACKEND = Path(__file__).resolve().parent.parent.parent.parent  # /app/backend
MODULES_DIR = BACKEND / "modules"


class ModuleMetaAgent(AgentContract):
    naam: str = "module_meta"
    klasse: str = "info_lookup"
    rol: str = "leaf"
    parent: str = "chat_hub_master"
    doel: str = "Leest _meta.json van elke module (doel, footnote, endpoints)."
    gradatie_min: int = 3
    kost_ms_estimate: int = 15
    triggers: List[str] = [
        r"\bwat\s+doet\s+(de\s+)?module\s+(\w+)",
        r"\bmodule[- ]?meta\b",
        r"\bmeta\s+van\s+(\w+)",
        r"\bhoe\s+werkt\s+(de\s+)?module\s+(\w+)",
    ]
    footnote: Dict[str, Any] = {
        "generated_by": "v10_chat_hub_fase1", "created": "2026-07-21",
        "meta_pass_source": "v9_meta_enrich_001 (sessie 40d)",
    }

    def run(self, text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        module_name = _extract_module_name(text)
        if not module_name:
            return {"error": "geen module-naam gedetecteerd", "hint": "probeer 'wat doet module trade'"}
        return self.read_module_meta(module_name)

    def read_module_meta(self, module_name: str) -> Dict[str, Any]:
        mod_dir = MODULES_DIR / module_name
        if not mod_dir.exists():
            # Case-insensitive fallback
            match = next((p for p in MODULES_DIR.iterdir()
                          if p.is_dir() and p.name.lower() == module_name.lower()), None)
            if not match:
                return {"error": f"module '{module_name}' niet gevonden",
                        "beschikbaar": sorted([p.name for p in MODULES_DIR.iterdir() if p.is_dir() and not p.name.startswith("_")])[:20]}
            mod_dir = match

        meta_fp = mod_dir / "_meta.json"
        if not meta_fp.exists():
            return {"module": mod_dir.name, "error": "geen _meta.json aanwezig"}

        try:
            meta = json.load(open(meta_fp))
            return {
                "module": mod_dir.name,
                "doel": meta.get("doel"),
                "footnote": meta.get("footnote"),
                "endpoints": meta.get("endpoints", []),
                "last_touched": meta.get("last_touched"),
                "has_blueprint": (mod_dir / "blueprints").exists() or bool(meta.get("blueprint")),
                "sub_agents": [p.name for p in (mod_dir / "agents").iterdir()
                               if p.is_file() and p.suffix == ".py" and not p.name.startswith("_")]
                              if (mod_dir / "agents").exists() else [],
            }
        except Exception as e:
            return {"module": mod_dir.name, "error": f"kan _meta.json niet lezen: {e}"}


def _extract_module_name(text: str) -> Optional[str]:
    """Vind module-naam in vraag."""
    import re
    low = (text or "").lower()
    # Patterns: "module X", "meta van X", "hoe werkt X", "wat doet X"
    for pat in [
        r"module\s+(\w+)", r"meta\s+van\s+(\w+)",
        r"hoe\s+werkt\s+(?:de\s+)?(?:module\s+)?(\w+)",
        r"wat\s+doet\s+(?:de\s+)?(?:module\s+)?(\w+)",
    ]:
        m = re.search(pat, low)
        if m:
            name = m.group(1)
            if name not in ("de", "je", "de", "een"):  # false positives
                return name
    return None
