"""
v14_task_agent_bridge_001 (Willem 20-10) — hybride stap 3: zin → command → uitvoeren in de chat.

Laag 1 (nu): slash-commands. `/tree` toont de mappenboom, `/cmd <zin>` zoekt een live registry-command
via task_agent.resolve_text. Lezen (GET) wordt direct uitgevoerd; schrijven/verwijderen vraagt eerst
"ja/nee" (session_state.last_question, intent `cmd_confirm`). Bewust alleen achter een slash zodat
gewone gesprekken nooit per ongeluk een command raken. Laag 2 (later): zonder slash, met concept-JSON.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

from modules.agents import task_agent
from modules.chat import session_state

_SLASH = re.compile(r"^\s*/(\w+)\s*(.*)$", re.S)
_LEARN_FILE = Path(__file__).parent.parent.parent / "data" / "system" / "command_learning.jsonl"
# laag 2: alleen zinnen met een actie-werkwoord komen in aanmerking (geen gewone gesprekszinnen)
_ACTIE = re.compile(r"\b(verwijder|wis|gooi\s+weg|delete|maak|cre[eë]er|voeg\s+toe|toon|laat\s+(?:me\s+)?zien|open|zet|geef|start|stop|archiveer|exporteer|download|herstel|ruim\s+op|plan|noteer)\b", re.I)
_MIN_SCORE_FREE = 0.25


# v14_task_agent_bridge_003 — ontbrekende gegevens vragen met genummerd lijstje
_PARAM_SPEC = {
    "note_id": {"path": "/api/notes/all", "key": "notes", "label": ("titel", "inhoud"), "naam": "notitie"},
    "task_id": {"path": "/api/notes/tasks", "key": "tasks", "label": ("titel", "title", "inhoud", "text"), "naam": "taak"},
    "event_id": {"path": "/api/agenda/events/{user_id}", "key": "events", "label": ("title", "titel"), "extra": ("date", "datum", "start"), "naam": "afspraak"},
}


async def _lijst(spec: Dict, user_id: str):
    import httpx
    from server import app
    path = spec["path"].replace("{user_id}", user_id)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://task-agent") as client:
        r = await client.get(path, params={"user_id": user_id, "viewer_id": user_id})
    try:
        data = r.json()
    except Exception:
        return []
    items = data.get(spec["key"], []) if isinstance(data, dict) else data
    out = []
    for it in items or []:
        label = next((str(it[k]) for k in spec["label"] if it.get(k)), None) or it.get("id", "?")
        extra = next((str(it[k])[:10] for k in spec.get("extra", ()) if it.get(k)), "")
        out.append({"id": it.get("id"), "label": (label[:60] + (f" ({extra})" if extra else ""))})
    return out


def _ontbrekend(cmd: Dict, params: Dict) -> Optional[str]:
    for p in (cmd.get("required_params") or []):
        if p != "user_id" and p not in params and p in _PARAM_SPEC:
            return p
    return None


async def _vraag_param(user_id: str, cmd: Dict, params: Dict, zin: str, tags, param: str) -> Dict:
    spec = _PARAM_SPEC[param]
    keuzes = await _lijst(spec, user_id)
    if not keuzes:
        _clear(user_id)
        return {"type": "cmd_no_items", "message": f"Je hebt geen {spec['naam']}s om uit te kiezen."}
    keuzes = keuzes[:10]
    session_state.set_state(user_id, pending_cmd={"cmd_id": cmd["id"], "params": params, "zin": zin, "tags": list(tags or []),
                                                   "param": param, "keuzes": keuzes})
    session_state.set_last_question(user_id, f"cmd_param:{param}", intent="cmd_param")
    regels = [f"Welke {spec['naam']} bedoel je?"] + [f"{i + 1}. {k['label']}" for i, k in enumerate(keuzes)] + ["(zeg het nummer, of 'laat maar')"]
    return {"type": "cmd_param", "cmd_id": cmd["id"], "message": "\n".join(regels), "keuzes": keuzes}


# v14_task_agent_bridge_004 — "zet morgen 10 uur tandarts in de agenda" → afspraak-voorstel → ja/nee → POST agenda
_AGENDA_CREATE = re.compile(r"\b(zet|plan|maak|noteer|voeg)\b.*\b(agenda|afspraak)\b|\b(agenda|afspraak)\b.*\b(zetten|plannen|maken|noteren|toevoegen)\b", re.I)
_DAGEN = {"maandag": 0, "dinsdag": 1, "woensdag": 2, "donderdag": 3, "vrijdag": 4, "zaterdag": 5, "zondag": 6}
_TIJD = re.compile(r"\b(?:om\s+)?(\d{1,2})(?:[:.u](\d{2}))?\s*(?:uur)?\b(?!\s*(?:mei|jan|feb|mrt|apr|jun|jul|aug|sep|okt|nov|dec|januari|februari|maart|april|juni|juli|augustus|september|oktober|november|december))", re.I)
_RUIS = re.compile(r"\b(zet|plan|maak|noteer|voeg|toe|in|de|mijn|agenda|afspraak|een|om|uur|morgen|overmorgen|vandaag|op|voor|aan|erin|erbij|graag|even|aub|alsjeblieft|maandag|dinsdag|woensdag|donderdag|vrijdag|zaterdag|zondag|volgende|week|s|ochtends|middags|avonds)\b", re.I)


def _parse_afspraak(t: str):
    from datetime import date, timedelta
    import re as _re
    tl = t.lower()
    vandaag = date.today()
    dag = None
    if "overmorgen" in tl: dag = vandaag + timedelta(days=2)
    elif "morgen" in tl: dag = vandaag + timedelta(days=1)
    elif "vandaag" in tl: dag = vandaag
    else:
        for naam, idx in _DAGEN.items():
            if naam in tl:
                delta = (idx - vandaag.weekday()) % 7 or 7
                if "volgende week" in tl: delta += 7
                dag = vandaag + timedelta(days=delta); break
    m_dat = _re.search(r"\b(\d{1,2})[-/](\d{1,2})(?:[-/](\d{2,4}))?\b", tl)
    if not dag and m_dat:
        jr = int(m_dat.group(3)) if m_dat.group(3) else vandaag.year
        if jr < 100: jr += 2000
        try: dag = date(jr, int(m_dat.group(2)), int(m_dat.group(1)))
        except ValueError: dag = None
    if not dag:
        return None
    uur, minuut = 9, 0
    rest = tl if not m_dat else tl.replace(m_dat.group(0), " ")
    m_t = _TIJD.search(rest)
    if m_t and 0 <= int(m_t.group(1)) <= 23:
        uur = int(m_t.group(1)); minuut = int(m_t.group(2) or 0)
        if uur < 7 and ("middag" in tl or "avond" in tl): uur += 12
        rest = rest.replace(m_t.group(0), " ")
    titel = _RUIS.sub(" ", rest)
    titel = _re.sub(r"[^\wà-ÿ\s-]", " ", titel)
    titel = " ".join(titel.split()).strip() or "Afspraak"
    return {"titel": titel[:1].upper() + titel[1:], "date": f"{dag.isoformat()}T{uur:02d}:{minuut:02d}:00", "dag": dag, "uur": uur, "minuut": minuut}


def try_agenda_create(text: str, user_id: Optional[str]) -> Optional[Dict]:
    t = (text or "").strip()
    if not user_id or "?" in t or not _AGENDA_CREATE.search(t):
        return None
    p = _parse_afspraak(t)
    if not p:
        return {"type": "cmd_need_date", "message": "Wanneer moet dat zijn? Zeg bv. 'morgen 10 uur' of 'vrijdag 14:30'."}
    dagnaam = ["ma", "di", "wo", "do", "vr", "za", "zo"][p["dag"].weekday()]
    session_state.set_state(user_id, pending_cmd={"cmd_id": "cap_agenda_event_create", "params": {"titel": p["titel"], "date": p["date"], "scope": "prive"},
                                                   "zin": t, "tags": ["agenda", "aanmaken"], "label": f"{p['titel']} {dagnaam} {p['dag'].strftime('%d-%m')} {p['uur']:02d}:{p['minuut']:02d}"})
    session_state.set_last_question(user_id, "cmd_confirm:cap_agenda_event_create", intent="cmd_confirm")
    return {"type": "cmd_confirm", "cmd_id": "cap_agenda_event_create",
            "message": f"📅 Afspraak '{p['titel']}' op {dagnaam} {p['dag'].strftime('%d-%m-%Y')} om {p['uur']:02d}:{p['minuut']:02d} in je agenda zetten? (ja/nee)"}


def _leer_bias(zin: str, tags) -> Dict[str, Dict[str, int]]:
    """Per cmd_id: hoe vaak ja/nee op precies deze zin of dezelfde tag-set."""
    out: Dict[str, Dict[str, int]] = {}
    if not _LEARN_FILE.exists():
        return out
    z = zin.strip().lower()
    tagset = set(tags or [])
    try:
        for regel in _LEARN_FILE.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(regel)
            except Exception:
                continue
            if r.get("zin", "").strip().lower() == z or (tagset and set(r.get("tags") or []) == tagset):
                d = out.setdefault(r.get("cmd_id", ""), {"ja": 0, "nee": 0})
                d[r.get("besluit", "nee")] = d.get(r.get("besluit", "nee"), 0) + 1
    except Exception as e:
        print(f"[task-agent-bridge] leer-bias lezen mislukt: {e}")
    return out


def _leer(user_id: str, zin: str, cmd_id: str, tags, besluit: str):
    """Elke ja/nee op een vrije zin → regel in command_learning.jsonl (zin → command → besluit)."""
    try:
        _LEARN_FILE.parent.mkdir(parents=True, exist_ok=True)
        with _LEARN_FILE.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"ts": datetime.now(timezone.utc).isoformat(), "user_id": user_id, "zin": zin,
                                 "cmd_id": cmd_id, "tags": list(tags or []), "besluit": besluit}, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"[task-agent-bridge] leren mislukt: {e}")
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

    lq = session_state.get_last_question(user_id)
    pending = session_state.get_state(user_id).get("pending_cmd")
    vers = lq.get("age_sec") is None or lq["age_sec"] < 300

    # 0) antwoord op "welke notitie?" (nummer of tekst)
    if lq.get("intent") == "cmd_param" and pending and vers:
        if re.search(r"\b(laat maar|nee|stop|annuleer|geen)\b", t.lower()):
            _clear(user_id)
            return {"type": "cmd_cancelled", "message": "Oké, laat maar."}
        keuzes = pending.get("keuzes") or []
        keuze = None
        m_nr = re.search(r"\d+", t)
        if m_nr and 1 <= int(m_nr.group(0)) <= len(keuzes):
            keuze = keuzes[int(m_nr.group(0)) - 1]
        else:
            keuze = next((k for k in keuzes if t.lower() in k["label"].lower() or k["label"].lower() in t.lower()), None)
        if not keuze:
            return {"type": "cmd_param", "message": f"Dat nummer ken ik niet — kies 1 t/m {len(keuzes)} of zeg 'laat maar'."}
        params = dict(pending.get("params") or {})
        params[pending["param"]] = keuze["id"]
        cmd = task_agent.get_command(pending["cmd_id"]) or {}
        method = (cmd.get("method") or "GET").upper()
        actie = {"DELETE": "verwijderen", "POST": "aanmaken", "PUT": "wijzigen", "PATCH": "wijzigen"}.get(method, "tonen")
        session_state.set_state(user_id, pending_cmd={**pending, "params": params, "label": keuze["label"]})
        session_state.set_last_question(user_id, f"cmd_confirm:{pending['cmd_id']}", intent="cmd_confirm")
        return {"type": "cmd_confirm", "cmd_id": pending["cmd_id"],
                "message": f"'{keuze['label']}' {actie} via `{pending['cmd_id']}`. Zeker weten? (ja/nee)"}

    # 1) antwoord op bevestigingsvraag
    if lq.get("intent") == "cmd_confirm" and pending and vers:
        from modules.chat.smart_intents_service import is_yes, is_no
        if is_yes(t):
            _clear(user_id)
            if pending.get("zin"):
                _leer(user_id, pending["zin"], pending["cmd_id"], pending.get("tags"), "ja")
            cmd = task_agent.get_command(pending["cmd_id"]) or {}
            ontbr = _ontbrekend(cmd, pending.get("params") or {})
            if ontbr:  # eerst nog kiezen, daarna opnieuw bevestigen
                return await _vraag_param(user_id, cmd, pending.get("params") or {}, pending.get("zin", ""), pending.get("tags"), ontbr)
            res = await task_agent.execute(pending["cmd_id"], pending.get("params"), user_id=user_id, admin_mode=admin_mode)
            out = _antwoord(res)
            if res.get("ok") and pending.get("label"):
                out["message"] = f"✅ '{pending['label']}' — gedaan via `{pending['cmd_id']}`."
            return out
        if is_no(t):
            _clear(user_id)
            if pending.get("zin"):
                _leer(user_id, pending["zin"], pending["cmd_id"], pending.get("tags"), "nee")
            return {"type": "cmd_cancelled", "message": "Oké, niet uitgevoerd. Dat onthoud ik: die zin hoort niet bij dat commando."}
        _clear(user_id)

    m = _SLASH.match(t)
    if not m:
        return try_agenda_create(t, user_id)
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
        ontbr = _ontbrekend(cmd, {})
        if ontbr:
            return await _vraag_param(user_id, cmd, {}, rest, hit.get("matched_tags"), ontbr)
        if method == "GET":
            return _antwoord(await task_agent.execute(cmd["id"], {}, user_id=user_id, admin_mode=admin_mode))
        session_state.set_state(user_id, pending_cmd={"cmd_id": cmd["id"], "params": {}})
        session_state.set_last_question(user_id, f"cmd_confirm:{cmd['id']}", intent="cmd_confirm")
        actie = {"DELETE": "verwijderen", "POST": "aanmaken/uitvoeren", "PUT": "wijzigen", "PATCH": "wijzigen"}.get(method, method)
        return {"type": "cmd_confirm", "cmd_id": cmd["id"],
                "message": f"Dit is {actie} via `{cmd['id']}` ({method} {cmd.get('path')}). Zal ik het doen? (ja/nee)"}
    return None


def try_resolve_free(text: str, user_id: Optional[str], admin_mode: bool = False) -> Optional[Dict]:
    """Laag 2 (v14_task_agent_bridge_002): zin zonder slash → tags → concept → command, altijd eerst ja/nee.
    Wordt pas aangeroepen als geen andere intent de zin oppakte."""
    if not user_id:
        return None
    t = (text or "").strip()
    if len(t) < 6 or t.startswith("/") or "?" in t or not _ACTIE.search(t):
        return None
    hit = task_agent.resolve_text(t)
    if not hit or not hit.get("cmd"):
        return None
    # v14_task_agent_bridge_003 — leren van ja/nee: vaak-ja → hogere zekerheid (en lagere drempel), 2× nee → ander command
    bias = _leer_bias(t, hit.get("matched_tags"))
    score = float(hit.get("score", 0))
    cmd = hit["cmd"]
    b = bias.get(cmd["id"], {})
    if b.get("nee", 0) >= 2 and b.get("nee", 0) > b.get("ja", 0):
        alt = next((c for c in (hit.get("candidates") or [])[1:] if bias.get(c["id"], {}).get("nee", 0) < 2), None)
        if not alt:
            return None
        cmd = task_agent.get_command(alt["id"]) or cmd
        score = float(alt.get("score", score))
        b = bias.get(cmd["id"], {})
    score = min(0.99, score + 0.15 * b.get("ja", 0) - 0.1 * b.get("nee", 0))
    geleerd = b.get("ja", 0) > 0
    if score < _MIN_SCORE_FREE and not geleerd:
        return None
    hit = {**hit, "score": score}
    method = (cmd.get("method") or "GET").upper()
    concept = {"DELETE": "verwijderen", "POST": "aanmaken/uitvoeren", "PUT": "wijzigen", "PATCH": "wijzigen"}.get(method, "lezen")
    tags = hit.get("matched_tags") or []
    session_state.set_state(user_id, pending_cmd={"cmd_id": cmd["id"], "params": {}, "zin": t, "tags": tags})
    session_state.set_last_question(user_id, f"cmd_confirm:{cmd['id']}", intent="cmd_confirm")
    alt = ""
    if hit.get("needs_disambiguation") and len(hit.get("candidates") or []) > 1:
        alt = f" (twijfel met `{hit['candidates'][1]['id']}`)"
    leer_txt = f", {b['ja']}× eerder ja" if geleerd else ""
    return {"type": "cmd_confirm", "cmd_id": cmd["id"], "score": score,
            "message": (f"Ik lees: tags [{', '.join(tags) or '—'}] → {concept} → `{cmd['id']}` "
                        f"({method} {cmd.get('path')}, zekerheid {round(score * 100)}%{leer_txt}){alt}. Zal ik het doen? (ja/nee)")}
