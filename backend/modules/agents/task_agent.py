"""
task_agent — Brug tussen chat-intent en command_registry.json.

Willem 15-feb 2026 (v13_task_agent_skeleton_001):
Vandaag doet `capability_handler_service` twee dingen tegelijk: (a) intent
matchen op sleutelwoorden en (b) de bijbehorende endpoint aanroepen. Dat
maakt herbruik lastig — een tweede kanaal (bijv. dashboard-widget of admin-
commando) moet dezelfde matching-logica dupliceren.

task_agent scheidt beide stappen:
    1. `resolve(intent_tags)` → returnt de matchende registry-entry (of None).
    2. `execute(cmd_id, params, user_id)` → voert de call intern uit met
       gradatie-check en logging.

Geen route-registratie hier. De agent leest `command_registry.json` als
single-source-of-truth. Voegt in de KB het inzicht toe: "welk commando hoort
bij welk intent?" — cruciaal voor Spark's zelfuitleg.

TODO:
- resolve(): tag-overlap-score met bestaande matcher-heuristiek.
- execute(): honor gradatie_min + required_params check + audit-log.
- registry-hot-reload watcher (nu wordt bij elke call opnieuw geladen).
- integratie met snap_agent: bij onbekende cmd_id → skeleton in inbox.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

_REGISTRY_PATH = Path(__file__).parent.parent.parent / "data" / "system" / "command_registry.json"


def _load_registry() -> List[Dict]:
    """Lees command_registry.json en returnt de commands-lijst.

    TODO: caching + hot-reload via mtime-check.
    """
    try:
        from modules.core.storage import load_json
        data = load_json(_REGISTRY_PATH, default={"commands": []})
        return data.get("commands", [])
    except Exception as e:  # pragma: no cover
        logger.warning("[task_agent] registry-load faalde: %s", e)
        return []


def resolve(intent_tags: List[str], min_overlap: int = 2) -> Optional[Dict]:
    """Vind de best-matchende registry-entry op basis van intent_tags overlap.

    TODO:
    - Werkelijke scoring (nu placeholder, retourneert None).
    - Tie-break-strategie: hoogste overlap → laagste gradatie_min.
    - Return {"cmd": <entry>, "score": int, "matched_tags": [...]}
    """
    _ = _load_registry()  # placeholder, wordt gebruikt zodra scoring live is
    logger.debug("[task_agent] resolve() nog niet geïmplementeerd — tags=%s", intent_tags)
    return None


def execute(cmd_id: str, params: Optional[Dict] = None, user_id: str = "user-000") -> Dict:
    """Voer een registry-commando uit met gradatie- + params-validatie.

    TODO:
    - Gradatie-check via `modules.spark.gradaties` (huidige user-gradatie
      ≥ entry.gradatie_min?).
    - Required-params-check.
    - Interne dispatch: importeer entry.source (bijv.
      "capability_handler_service._handle_taken_lijst") en roep aan.
    - Audit-log entry naar data/system/audit_log.json.
    """
    logger.debug("[task_agent] execute() nog niet geïmplementeerd — cmd=%s", cmd_id)
    return {"ok": False, "reason": "not_implemented", "cmd_id": cmd_id}


def list_commands(gradatie_max: Optional[int] = None) -> List[Dict]:
    """Return alle bekende commands, optioneel gefilterd op gradatie-limit.

    TODO: filter op behavior_class_hint / intent_tags voor UI-groepering.
    """
    cmds = _load_registry()
    if gradatie_max is not None:
        cmds = [c for c in cmds if c.get("gradatie_min", 1) <= gradatie_max]
    return cmds
