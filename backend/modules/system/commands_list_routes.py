"""v13_commands_list_001 — Spark's 'welke commando's ken je?'-endpoint.

Route: GET /api/commands/list
Wrapper rond task_agent.list_commands() met filters zodat:
- de chat-laag een 'bekijk command lijst'-intent kan afhandelen;
- admin-console een gefilterde tabel kan tonen;
- Spark introspectief kan uitleggen wat ie kan.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query

from modules.agents import task_agent

router = APIRouter(prefix="/commands", tags=["commands"])


@router.get("/list")
async def list_commands(
    module: Optional[str] = Query(None, description="Filter op module-prefix uit path, bv 'agenda' of 'kb/v2'"),
    admin_only: Optional[bool] = Query(None, description="True=alleen admin-cmd, False=alleen non-admin, None=beide"),
    gradatie_max: Optional[int] = Query(None, ge=1, le=6, description="Alleen cmd's met gradatie_min ≤ dit"),
    q: Optional[str] = Query(None, description="Zoekterm in id, path, intent_tags of source"),
):
    """Return alle geregistreerde commando's, optioneel gefilterd.

    Non-mutating; leest command_registry.json via task_agent.list_commands().
    """
    cmds = task_agent.list_commands(gradatie_max=gradatie_max)

    if module:
        needle = module.strip("/").lower()
        cmds = [c for c in cmds if needle in (c.get("path", "").lower())]

    if admin_only is True:
        cmds = [c for c in cmds if c.get("admin_only") is True]
    elif admin_only is False:
        cmds = [c for c in cmds if not c.get("admin_only")]

    if q:
        needle = q.lower().strip()
        def match(c: dict) -> bool:
            if needle in (c.get("id") or "").lower():
                return True
            if needle in (c.get("path") or "").lower():
                return True
            if needle in (c.get("source") or "").lower():
                return True
            for t in c.get("intent_tags", []) or []:
                if needle in (t or "").lower():
                    return True
            return False
        cmds = [c for c in cmds if match(c)]

    # Kort samenvattingsformaat + volledige entries
    return {
        "count": len(cmds),
        "filters": {
            "module": module,
            "admin_only": admin_only,
            "gradatie_max": gradatie_max,
            "q": q,
        },
        "commands": cmds,
    }
