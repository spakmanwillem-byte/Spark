"""
admin_command_agent — Wrapper rond admin-only capability-endpoints.

Willem 15-feb 2026 (v13_admin_command_agent_skeleton_001):
Sommige commando's uit `command_registry.json` (reconciles, dedupe-runs,
seed-cards, gebruikers-capable-toggle) zijn admin-only. Vandaag zit die
gate verspreid: soms `require_admin` decorator op de route, soms een
handmatige check binnen de handler.

admin_command_agent centraliseert de admin-toegangscheck en biedt een
enkel entrypoint voor "voer admin-commando X uit als user Y". Voor Spark
betekent dit: één plek om te leren welke admin-acties bestaan en één plek
om audit-trails naar toe te schrijven.

TODO:
- Admin-check via `modules.auth.deps.require_admin_capable` hergebruiken.
- Whitelist admin-cmd_ids (subset van command_registry).
- Zware admin-acties (reconcile-all, seed-full-KB) achter dubbele bevestiging.
- Sync met eco-container: admin-actie in container A mag geen data in B raken.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# TODO: uitbreiden zodra elke admin-cmd geregistreerd is in de registry.
_ADMIN_CMD_WHITELIST: List[str] = [
    "cap_kb_normalize_apostrophes",  # v13c_apostrophe_normalizer_001 — eerste live admin-cmd
    # "cap_reconcile_potjes",
    # "cap_seed_self_awareness_cards",
    # "cap_toggle_admin_capable",
]


def is_admin_command(cmd_id: str) -> bool:
    """Return True als cmd_id een admin-only actie is.

    TODO: leest whitelist. Later: `admin_only=True` veld in registry-entry.
    """
    return cmd_id in _ADMIN_CMD_WHITELIST


def execute_as_admin(cmd_id: str, user_id: str, params: Optional[Dict] = None) -> Dict:
    """Voer een admin-commando uit met dubbele check.

    Stappen:
        1. Is user admin-capable? (via auth-deps)
        2. Staat cmd_id op de whitelist?
        3. Delegeer naar task_agent.execute() met audit-flag.

    TODO:
    - Import cyclus vermijden: task_agent lazy-importeren.
    - Structured audit log ("admin_action" event type).
    """
    logger.debug("[admin_command_agent] execute_as_admin() nog niet geïmplementeerd — cmd=%s user=%s", cmd_id, user_id)
    return {"ok": False, "reason": "not_implemented", "cmd_id": cmd_id}


def list_admin_commands() -> List[Dict]:
    """Return alle admin-only commands uit de registry.

    TODO: intersect _ADMIN_CMD_WHITELIST met task_agent.list_commands().
    """
    return []
