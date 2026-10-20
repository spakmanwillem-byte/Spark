"""
v14_task_agent_bridge_001 (Willem 20-10) — hybride stap 3: zin → command → uitvoeren in de chat.

Laag 1 (nu): slash-commands. `/tree` toont de mappenboom, `/cmd <zin>` zoekt een live registry-command
via task_agent.resolve_text. Lezen (GET) wordt direct uitgevoerd; schrijven/verwijderen vraagt eerst
"ja/nee" (session_state.last_question, intent `cmd_confirm`). Bewust alleen achter een slash zodat
gewone gesprekken nooit per ongeluk een command raken. Laag 2 (later): zonder slash, met concept-JSON.
"""
from __future__ import annotations

import re
from collections import Counter
from typing import Dict, Optional

from modules.agents import task_agent
from modules.chat import session_state

_SLASH = re.compile(r"^\s*/(\w+)\s*(.*)$", re.S)
_ALIASES = {"tree": "cap_files_tree", "boom": "cap_files_tree", "mappen": "cap_files_tree"}


def _fmt_tree(data: Dict) -> str:
    regels = ["🗂️ Mappenboom (alleen lezen):"]
    for base in data.get("tree", []):
        per_map = Counter((f.get("directory") or ".").split("/")[0] for f in base.get("files", []))
        regels.append(f"📁 {base['name']} — {len(base.get('files', []))} bestanden")
        for m, n in sorted(per_map.items(), key=lambda x: -x[1])[:12]:
            regels.append(f"   └ {m}/ ({n})")
        if len(per_map) > 12:
            regels.append(f"   └ … nog {len(per_map) - 12} mappen")
    regels.append(f"Totaal {data.get('total_files', 0)} bestanden. Zeg `/cmd <wat je wilt>` voor andere commando's.")
    return "\n".join(regels)


_FORMATTERS = {"cap_files_tree": _fmt_tree}


def _fmt_generic(cmd_id: str, data) -> str:
    if isinstance(data, dict):
        lijst = next((v for v in data.values() if isinstance(v, list)), None)
        if lijst is not None:
            return f"✅ `{cmd_id}` uitgevoerd — {len(lijst)} items."
        keys = ", ".join(list(data.keys())[:8])
        return f"✅ `{cmd_id}` uitgevoerd. Velden: {keys}."
    return f"✅ `{cmd_id}` uitgevoerd."


def _antwoord(result: Dict) -> Dict:
    cmd_id = result.get("cmd_id", "?")
    if not result.get("ok"):
        reden = result.get("reason") or f"status {result.get('status')}"
        uitleg = {"gradatie": "daar heb je geen rechten voor", "missing_params": f"er ontbreekt iets: {', '.join(result.get('missing', []))}",
                  "unknown_or_placeholder": "dat commando bestaat nog niet (placeholder)"}.get(reden, reden)
        return {"type": "cmd_failed", "message": f"⚠️ `{cmd_id}` niet uitgevoerd — {uitleg}.", "cmd_id": cmd_id}
    fmt = _FORMATTERS.get(cmd_id)
    msg = fmt(result.get("data") or {}) if fmt else _fmt_generic(cmd_id, result.get("data"))
    return {"type": "cmd_executed", "message": msg, "cmd_id": cmd_id}


def _clear(user_id: str):
    session_state.set_state(user_id, last_question=None, last_question_intent=None, pending_cmd=None)


async def try_execute(text: str, user_id: Optional[str], admin_mode: bool = False) -> Optional[Dict]:
    """Return response-dict of None als dit geen command is."""
    if not user_id:
        return None
    t = (text or "").strip()

    # 1) antwoord op bevestigingsvraag
    lq = session_state.get_last_question(user_id)
    pending = session_state.get_state(user_id).get("pending_cmd")
    if lq.get("intent") == "cmd_confirm" and pending and (lq.get("age_sec") is None or lq["age_sec"] < 300):
        from modules.chat.smart_intents_service import is_yes, is_no
        if is_yes(t):
            _clear(user_id)
            return _antwoord(await task_agent.execute(pending["cmd_id"], pending.get("params"), user_id=user_id, admin_mode=admin_mode))
        if is_no(t):
            _clear(user_id)
            return {"type": "cmd_cancelled", "message": "Oké, niet uitgevoerd."}
        _clear(user_id)

    m = _SLASH.match(t)
    if not m:
        return None
    naam, rest = m.group(1).lower(), m.group(2).strip()
    if naam in ("help",):
        return None  # help heeft z'n eigen route

    if naam in _ALIASES:
        return _antwoord(await task_agent.execute(_ALIASES[naam], {}, user_id=user_id, admin_mode=admin_mode))

    if naam in ("cmd", "doe", "command"):
        if not rest:
            return {"type": "cmd_usage", "message": "Gebruik: `/cmd <wat je wilt>`, bv. `/cmd toon mijn taken` of `/tree`."}
        hit = task_agent.resolve_text(rest)
        if not hit or not hit.get("cmd"):
            return {"type": "cmd_none", "message": f"Ik ken nog geen commando voor \"{rest}\". Zeg `wat kan je` voor een overzicht."}
        cmd = hit["cmd"]
        method = (cmd.get("method") or "GET").upper()
        if method == "GET":
            return _antwoord(await task_agent.execute(cmd["id"], {}, user_id=user_id, admin_mode=admin_mode))
        session_state.set_state(user_id, pending_cmd={"cmd_id": cmd["id"], "params": {}})
        session_state.set_last_question(user_id, f"cmd_confirm:{cmd['id']}", intent="cmd_confirm")
        actie = {"DELETE": "verwijderen", "POST": "aanmaken/uitvoeren", "PUT": "wijzigen", "PATCH": "wijzigen"}.get(method, method)
        return {"type": "cmd_confirm", "cmd_id": cmd["id"],
                "message": f"Dit is {actie} via `{cmd['id']}` ({method} {cmd.get('path')}). Zal ik het doen? (ja/nee)"}
    return None
