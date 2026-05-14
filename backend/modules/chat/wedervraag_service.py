"""
Wedervraag Service (v4_001b - Conversational Depth)

Implementeert multi-turn 5W+H verrijking:
1. Bij nieuwe snap (woord of zin) → Spark kiest 1 leeg ws5-veld
2. Spark stelt gerichte vraag: "Wanneer was dat?", "Wie was erbij?"
3. session_state onthoudt {entry_id, awaiting_field}
4. Volgend bericht is antwoord → wordt opgeslagen in ws5[field]
5. Spark bevestigt + vraagt evt. volgende veld (max 2 per snap, anders te vermoeiend)

Skip-woorden ("laat maar", "skip", "weet niet") laten de flow stoppen.
"""
from pathlib import Path
import random
import re
from modules.core.storage import load_json, save_json

KNOWLEDGE_FILE = Path(__file__).parent.parent.parent / "data" / "knowledge" / "learned_knowledge" / "knowledge_base.json"

# Prioriteit-volgorde: welke velden vragen we eerst?
# (Wat/Wanneer/Waar zijn meest concreet, Wie/Waarom/Hoe meer reflectief)
FIELD_PRIORITY = ["wat", "wanneer", "waar", "wie", "waarom", "hoe"]

# Vraagsjablonen per veld (NL, vriendelijke toon)
QUESTION_TEMPLATES = {
    "wat": [
        "Kan je in het kort uitleggen wat '{begrip}' precies is?",
        "Wat houdt '{begrip}' eigenlijk in?",
        "Wat betekent '{begrip}' voor jou?",
    ],
    "wanneer": [
        "Wanneer kwam '{begrip}' ter sprake?",
        "Wanneer was dat met '{begrip}'?",
        "Wanneer speelt '{begrip}' een rol?",
    ],
    "waar": [
        "Waar speelt '{begrip}' zich af?",
        "Op welke plek hoort '{begrip}' bij?",
        "Waar komt '{begrip}' meestal voor?",
    ],
    "wie": [
        "Wie is er bij '{begrip}' betrokken?",
        "Met wie heeft '{begrip}' te maken?",
        "Over wie gaat '{begrip}'?",
    ],
    "waarom": [
        "Waarom == '{begrip}' belangrijk?",
        "Waarom noem je '{begrip}'?",
        "Wat maakt '{begrip}' relevant voor jou?",
    ],
    "hoe": [
        "Hoe werkt '{begrip}' precies?",
        "Hoe pak je '{begrip}' aan?",
        "Hoe ervaar je '{begrip}'?",
    ],
}

# Skip-zinnen — user wil niet verder verrijken
SKIP_PATTERNS = [
    "skip", "laat maar", "weet niet", "geen idee", "later", "hou maar op",
    "stop", "niet nu", "geen tijd", "passeren", "overslaan",
]


def _load_entries():
    return load_json(KNOWLEDGE_FILE, default={"knowledge_entries": []}).get("knowledge_entries", [])


def _save_entries(entries):
    save_json(KNOWLEDGE_FILE, {"knowledge_entries": entries})


def _find_entry(entry_id):
    for e in _load_entries():
        if e.get("id") == entry_id:
            return e
    return None


def is_skip(text: str) -> bool:
    text_lower = text.lower().strip()
    return any(p in text_lower for p in SKIP_PATTERNS)


def pick_next_field(entry: dict) -> str:
    """
    Kies eerste lege ws5-veld in prioriteitsvolgorde.
    Returns field-naam ('what','when',...) of None als alles ingevuld.
    """
    ws5 = entry.get("ws5") or {}
    for field in FIELD_PRIORITY:
        if not (ws5.get(field) or "").strip():
            return field
    return None


def build_question(field: str, begrip: str) -> str:
    """Bouw vriendelijke 5W+H vraag voor begrip + leeg veld."""
    templates = QUESTION_TEMPLATES.get(field, [f"Kan je iets meer vertellen over '{begrip}'?"])
    return random.choice(templates).replace("{begrip}", begrip[:60])


def apply_answer(entry_id: str, field: str, answer: str) -> bool:
    """Sla user-antwoord op in ws5[field] van entry. Returns True als opgeslagen."""
    answer = (answer or "").strip()
    if not answer:
        return False
    entries = _load_entries()
    updated = False
    for e in entries:
        if e.get("id") == entry_id:
            ws5 = e.get("ws5") or {}
            ws5[field] = answer[:300]
            e["ws5"] = ws5
            # Update status: kaart krijgt iets terug
            tags = e.get("tags") or []
            if "user-verrijkt" not in tags:
                tags.append("user-verrijkt")
            e["tags"] = tags
            updated = True
            break
    if updated:
        _save_entries(entries)
    return updated


def kick_off(entry: dict, max_questions: int = 2) -> dict:
    """
    Genereer eerste wedervraag voor een nieuwe snap.
    Returns {field, question, asked_count: 1} of None als niks te vragen.
    """
    field = pick_next_field(entry)
    if not field:
        return None
    return {
        "entry_id": entry["id"],
        "field": field,
        "question": build_question(field, entry.get("begrip", "")),
        "asked_count": 1,
        "max_questions": max_questions,
    }


def continue_flow(pending: dict) -> dict:
    """
    Na ontvangen antwoord: kies volgend veld (of stop).
    pending = vorige state {entry_id, field, asked_count, max_questions}
    Returns next state of None.
    """
    entry = _find_entry(pending.get("entry_id"))
    if not entry:
        return None
    if pending.get("asked_count", 0) >= pending.get("max_questions", 2):
        return None
    next_field = pick_next_field(entry)
    if not next_field:
        return None
    return {
        "entry_id": entry["id"],
        "field": next_field,
        "question": build_question(next_field, entry.get("begrip", "")),
        "asked_count": pending.get("asked_count", 0) + 1,
        "max_questions": pending.get("max_questions", 2),
    }
