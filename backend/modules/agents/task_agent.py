"""
task_agent — Brug tussen chat-intent en command_registry.json.

Willem 15-feb 2026 (v13_task_agent_skeleton_001) · gevuld 19-10-2026 (v14_task_agent_basis_001):
    1. `resolve(intent_tags)` → best-matchende live registry-entry via intent_registry.matcher.
    2. `execute(cmd_id, params, user_id)` → gradatie-check + required-params-check, interne
       dispatch via ASGI (geen netwerk), audit-log via spark_logger.

Alleen `commands` (status live) tellen; `placeholders` (wensen zonder route) worden genegeerd.
Nog niet: inhaken in de chat-flow (hybride stap 3 na action_intents en capabilities).
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

_REGISTRY_PATH = Path(__file__).parent.parent.parent / "data" / "system" / "command_registry.json"
_cache = {"mtime": 0.0, "commands": []}


def _load_registry() -> List[Dict]:
    """Lees command_registry.json (alleen live commands), met mtime-cache."""
    try:
        m = _REGISTRY_PATH.stat().st_mtime
        if m != _cache["mtime"]:
            from modules.core.storage import load_json
            data = load_json(_REGISTRY_PATH, default={"commands": []})
            _cache["commands"] = [c for c in data.get("commands", []) if c.get("status", "live") == "live"]
            _cache["mtime"] = m
        return _cache["commands"]
    except Exception as e:  # pragma: no cover
        logger.warning("[task_agent] registry-load faalde: %s", e)
        return []


def list_commands(gradatie_max: Optional[int] = None) -> List[Dict]:
    cmds = _load_registry()
    if gradatie_max is not None:
        cmds = [c for c in cmds if c.get("gradatie_min", 1) <= gradatie_max]
    return cmds


def get_command(cmd_id: str) -> Optional[Dict]:
    return next((c for c in _load_registry() if c.get("id") == cmd_id), None)


_VERB_CONCEPTS = {
    "verwijderen": {"verwijder", "verwijderen", "delete", "wis", "weg", "weghalen", "ruim", "opruimen", "gooi"},
    "aanmaken": {"maak", "maken", "nieuw", "nieuwe", "voeg", "toevoegen", "aanmaken", "noteer", "schrijf", "meld"},
    "wijzigen": {"wijzig", "verander", "pas", "update", "zet", "hernoem", "markeer"},
}
_METHODS_FOR = {"verwijderen": {"DELETE"}, "aanmaken": {"POST"}, "wijzigen": {"PUT", "PATCH", "POST"}}


def resolve(intent_tags: List[str], min_score: float = 0.15, gradatie: Optional[int] = None,
            methods: Optional[set] = None) -> Optional[Dict]:
    """Vind het best-matchende live command op tag-overlap (optioneel beperkt tot HTTP-methods).
    Returns {"cmd", "score", "matched_tags", "needs_disambiguation", "candidates"} of None."""
    if not intent_tags:
        return None
    from modules.intent_registry.matcher import match_capability
    r = match_capability(list(intent_tags), top_n=8, min_score=min_score, gradatie=gradatie)
    cands = [c for c in r.get("candidates", []) if not methods or (c.get("method") or "GET").upper() in methods]
    cands = [c for c in cands if get_command(c["id"])]
    if not cands:
        return None
    best = cands[0]
    disambig = len(cands) >= 2 and best["score"] >= 0.3 and (best["score"] - cands[1]["score"]) <= 0.1
    return {"cmd": get_command(best["id"]), "score": best["score"], "matched_tags": best.get("overlap", []),
            "needs_disambiguation": disambig,
            "candidates": [{"id": c["id"], "score": c["score"]} for c in cands[:3]]}


def resolve_text(text: str, gradatie: Optional[int] = None) -> Optional[Dict]:
    """Zin → tags (extractor + losse woorden + simpele stam) + werkwoord-concept → resolve().
    Zonder actie-werkwoord wordt alleen gelezen (GET)."""
    from modules.intent_registry.extractor import extract_tags
    tags = list(extract_tags(text))
    words = re.findall(r"[\wàáèéëïóöü-]+", (text or "").lower())
    methods: set = set()
    for w in words:
        for concept, verbs in _VERB_CONCEPTS.items():
            if w in verbs:
                methods |= _METHODS_FOR[concept]
                tags.append(concept)
        if len(w) < 3:
            continue
        tags.append(w)
        if w.endswith("s"):
            tags.append(w[:-1])          # notities → notitie
        if w.endswith("en") and len(w) > 5:
            tags.append(w[:-2])          # verbindingen → verbinding
    return resolve(list(dict.fromkeys(tags)), min_score=0.05, gradatie=gradatie, methods=methods or {"GET"})


def _fill_path(path: str, params: Dict) -> (str, Dict, List[str]):
    """Vul {x} in het pad uit params; rest gaat als query/body mee. Returns (pad, rest, ontbrekend)."""
    rest = dict(params)
    missing: List[str] = []

    def sub(m):
        k = m.group(1)
        if k in rest:
            return str(rest.pop(k))
        missing.append(k)
        return m.group(0)
    return re.sub(r"\{([^}]+)\}", sub, path), rest, missing


async def execute(cmd_id: str, params: Optional[Dict] = None, user_id: str = "user-000", admin_mode: bool = False) -> Dict:
    """Voer een live registry-commando intern uit. Returns {ok, status, data|reason, cmd_id}."""
    from modules.core.spark_logger import log_event
    params = dict(params or {})
    cmd = get_command(cmd_id)
    if not cmd:
        return {"ok": False, "reason": "unknown_or_placeholder", "cmd_id": cmd_id}

    from modules.chat.routes_helpers import get_user_gradatie
    grad = get_user_gradatie(user_id)
    need = int(cmd.get("gradatie_min", 1) or 1)
    # Registry-schaal: 1 = iedereen … 5 = beheer. User-schaal: 1 = beheerder … 5 = gast.
    # Omrekening: user mag als user_gradatie <= 6 - gradatie_min; admin_only eist gradatie 1.
    allowed = grad is not None and grad <= (6 - need) and not (cmd.get("admin_only") and grad != 1)
    if admin_mode and grad is not None and grad <= 2:
        allowed = True  # v14_task_agent_bridge_001 — admin-mode aan (admin_capable, frontend-toggle) = beheer-rechten
    if not allowed:
        log_event("task_agent", "execute_denied", intent=cmd_id, detail={"user_id": user_id, "gradatie": grad, "gradatie_min": need})
        return {"ok": False, "reason": "gradatie", "cmd_id": cmd_id, "gradatie": grad, "gradatie_min": need}

    params.setdefault("user_id", user_id)
    path, rest, missing = _fill_path(cmd["path"], params)
    missing += [p for p in (cmd.get("required_params") or []) if p not in params]
    if missing:
        return {"ok": False, "reason": "missing_params", "cmd_id": cmd_id, "missing": sorted(set(missing))}

    import httpx
    from server import app
    method = (cmd.get("method") or "GET").upper()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://task-agent") as client:
        if method in ("GET", "DELETE"):
            resp = await client.request(method, path, params=rest)
        else:
            resp = await client.request(method, path, json=rest)
    try:
        data = resp.json()
    except Exception:
        data = {"text": resp.text[:500]}
    ok = 200 <= resp.status_code < 300
    log_event("task_agent", "execute", intent=cmd_id,
              detail={"user_id": user_id, "method": method, "path": path, "status": resp.status_code, "ok": ok})
    return {"ok": ok, "status": resp.status_code, "cmd_id": cmd_id, "path": path, "data": data}
