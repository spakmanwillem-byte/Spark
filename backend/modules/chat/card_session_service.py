"""
Card Fill Session Service (v4_008)

Admin-modus om in chat door onbeantwoorde kaarten te lopen en alle 6
W+H velden in te vullen. Per kaart:

1. Spark pakt een kaart met tag 'auto-generated' en lege ws5-velden
2. Vraagt 6 velden in volgorde: what, when, where, who, why, how
3. Skip-woorden ("skip", "weet niet") slaan dat veld over
4. Stop-woorden ("stop", "klaar") beëindigen de hele sessie
5. Na 6 velden: kaart klaar, volgende uit queue, tot queue leeg
6. Tag 'sessie-ingevuld' toegevoegd na elke afronde kaart (admin haalt
   later 'auto-generated' tag eraf voor goedkeuring)

Alleen voor admin (gradatie 1 of 2). Sessie-state in session_state.
"""
from pathlib import Path
from modules.core.storage import load_json, save_json

KNOWLEDGE_FILE = Path(__file__).parent.parent.parent / "data" / "knowledge" / "learned_knowledge" / "knowledge_base.json"

# Vraag-volgorde + sjablonen (vriendelijk, korte vragen)
FIELDS_ORDER = ["wat", "wanneer", "waar", "wie", "waarom", "hoe"]
FIELD_QUESTIONS = {
    "wat": "Wat is **{begrip}** kort gezegd?",
    "wanneer": "Wanneer komt **{begrip}** voor of speelt het?",
    "waar": "Waar hoort **{begrip}** bij — locatie of plek?",
    "wie": "Wie is er bij **{begrip}** betrokken?",
    "waarom": "Waarom is **{begrip}** belangrijk of relevant?",
    "hoe": "Hoe werkt **{begrip}** of hoe ervaar je het?",
}

# Triggers om sessie te starten
START_TRIGGERS = [
    "ik wil kaarten invullen",
    "ik wil een kaart invullen",
    "laten we kaarten invullen",
    "kaarten invullen",
    "kaart invullen",
    "kenniskaarten invullen",
    "kenniskaart invullen",
    "kennis kaarten invullen",
    "kennis kaart invullen",
    "ik wil kenniskaarten invullen",
    "ik wil kennis kaarten invullen",
    "start kaartsessie",
    "start kaart sessie",
    "start kaarten sessie",
    "vul kaarten in",
    "vul kaart in",
    "kaarten doen",
    "kennis invullen",
    "begin met kaarten",
    "begin kaartsessie",
    "spark help me kaarten",
    "wil kaarten invullen",
]

STOP_WORDS = {
    "stop", "klaar", "genoeg", "genoeg voor nu", "laat maar zo",
    "tot later", "pauze", "wacht even", "even niet",
}

SKIP_FIELD = {
    "skip", "weet niet", "geen idee", "overslaan", "passeren", "volgende",
}


def detect_start_command(text: str) -> bool:
    """Detecteer of user kaartsessie wil starten."""
    text_lower = text.lower().strip().rstrip(".!?")
    return any(t in text_lower for t in START_TRIGGERS)


def is_stop(text: str) -> bool:
    text_lower = text.lower().strip().rstrip(".!?")
    return text_lower in STOP_WORDS


def is_skip(text: str) -> bool:
    text_lower = text.lower().strip().rstrip(".!?")
    return text_lower in SKIP_FIELD


def _load_entries():
    return load_json(KNOWLEDGE_FILE, default={"knowledge_entries": []}).get("knowledge_entries", [])


def _save_entries(entries):
    save_json(KNOWLEDGE_FILE, {"knowledge_entries": entries})


def build_queue(max_items: int = 50) -> list:
    """
    Bouw een queue van kaart-ids die nog ingevuld moeten worden.
    Criteria: auto-generated tag AANWEZIG + minstens 1 leeg W+H veld.
    Sortering: nieuwste eerst (omgekeerd lijst-eind), maar zin-snaps achter.
    """
    entries = _load_entries()
    todo = []
    for e in entries:
        tags = e.get("tags") or []
        if "auto-generated" not in tags:
            continue
        ws5 = e.get("ws5") or {}
        empty_fields = [f for f in FIELDS_ORDER if not (ws5.get(f) or "").strip()]
        if not empty_fields:
            continue
        # Zin-snaps achteraan (vaak minder zinvol om uit te leggen)
        is_sentence = "context-zin" in tags or (e.get("metadata") or {}).get("is_sentence")
        todo.append({"id": e["id"], "begrip": e["begrip"], "is_sentence": bool(is_sentence)})
    todo.sort(key=lambda x: (x["is_sentence"], x["begrip"]))
    return [t["id"] for t in todo[:max_items]]


def _find_entry(entry_id):
    for e in _load_entries():
        if e.get("id") == entry_id:
            return e
    return None


def get_next_field(entry: dict) -> str:
    """Volgende lege ws5-veld in vaste volgorde."""
    ws5 = entry.get("ws5") or {}
    for f in FIELDS_ORDER:
        if not (ws5.get(f) or "").strip():
            return f
    return None


def build_question(field: str, begrip: str) -> str:
    return FIELD_QUESTIONS[field].replace("{begrip}", begrip[:60])


def apply_answer(entry_id: str, field: str, answer: str) -> bool:
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
            tags = e.get("tags") or []
            if "sessie-ingevuld" not in tags:
                tags.append("sessie-ingevuld")
            e["tags"] = tags
            updated = True
            break
    if updated:
        _save_entries(entries)
    return updated


def start_session(max_items: int = 50) -> dict:
    """Bouw een nieuwe sessie. Return state-dict."""
    queue = build_queue(max_items)
    if not queue:
        return {"queue": [], "total": 0, "done": True}
    return {
        "queue": queue,
        "total": len(queue),
        "current_index": 0,
        "current_field": None,
        "skipped_fields_for_card": [],
        "done": False,
    }


def next_question(session: dict) -> dict:
    """
    Bepaal volgende vraag binnen de sessie.
    Return {'card_id', 'begrip', 'field', 'question', 'card_progress': (n,total)}
    of {'done': True} als sessie klaar is.
    """
    queue = session.get("queue", [])
    idx = session.get("current_index", 0)
    if idx >= len(queue):
        return {"done": True, "total": session.get("total", 0)}
    card_id = queue[idx]
    entry = _find_entry(card_id)
    if not entry:
        session["current_index"] = idx + 1
        return next_question(session)
    skipped = set(session.get("skipped_fields_for_card", []))
    ws5 = entry.get("ws5") or {}
    next_field = None
    for f in FIELDS_ORDER:
        if f in skipped:
            continue
        if not (ws5.get(f) or "").strip():
            next_field = f
            break
    if next_field is None:
        # Kaart klaar, volgende
        session["current_index"] = idx + 1
        session["skipped_fields_for_card"] = []
        return next_question(session)
    session["current_field"] = next_field
    return {
        "done": False,
        "card_id": card_id,
        "begrip": entry["begrip"],
        "field": next_field,
        "question": build_question(next_field, entry["begrip"]),
        "card_progress": (idx + 1, session["total"]),
    }
