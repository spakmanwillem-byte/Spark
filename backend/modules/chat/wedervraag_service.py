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
import secrets
import re
from modules.core.storage import load_json, save_json

KNOWLEDGE_FILE = Path(__file__).parent.parent.parent / "data" / "knowledge" / "learned_knowledge" / "knowledge_base.json"  # V1 legacy
KBV2_DIR = Path(__file__).parent.parent.parent / "data" / "knowledge" / "v2"
KBV2_LADES = ["doen", "weten", "voelen", "spreken"]

# v6_wedervraag_disable_001 — Globale toggle. User vult kaarten zelf sneller in
# dan de vraag-flow biedt; uitgezet om chat-flow niet te verstoren.
# Zet op True om de "Wat houdt X eigenlijk in?" vragen weer aan te zetten.
WEDERVRAAG_ENABLED = False

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

# v6_wedervraag_quiet_001 (28 mei) — heuristieken om te detecteren of user-input
# een NIEUWE vraag/onderwerp is ipv antwoord op de pending wedervraag.
NEW_QUESTION_STARTERS = (
    "wat is", "wat zijn", "hoe ", "waarom ", "wanneer ", "waar ", "wie ",
    "welke ", "kun je", "kan je", "kun jij", "kan jij", "weet je",
    "vertel ", "leg uit", "help me", "help mij", "ik wil", "ik wou",
    "toon ", "geef ", "open ", "ga naar", "start ", "stop ",
)

def looks_like_new_question(text: str) -> bool:
    """v6_wedervraag_quiet_001 — herkent of user een nieuwe vraag stelt ipv
    antwoord geeft op pending W-vraag. Voorkomt dat 'wat is liefde?' getypt
    tijdens een pending 'wanneer was dat?' per ongeluk als antwoord wordt opgeslagen.
    """
    if not text:
        return False
    t = text.lower().strip()
    if t.endswith("?"):
        return True
    if any(t.startswith(s) for s in NEW_QUESTION_STARTERS):
        return True
    # Twee of meer woorden EN bevat een vraagwoord midden in
    words = t.split()
    if len(words) >= 4 and any(qw in words for qw in ("wat", "hoe", "waarom", "wanneer", "waar")):
        return True
    return False


# v6_wedervraag_quiet_001 — interactie-cap: max 1 wedervraag per N chat-beurten
WEDERVRAAG_INTERVAL_INTERACTIONS = 4


def should_throttle(last_wv_at_count: int, current_count: int) -> bool:
    """True = nog te kort geleden, sla nieuwe kick_off over."""
    if not last_wv_at_count:
        return False
    return (current_count - last_wv_at_count) < WEDERVRAAG_INTERVAL_INTERACTIONS


def _load_entries():
    """v6_v2_first_001 — laad alle V2 kaarten (4 lades + inbox) als platte lijst."""
    out = []
    for fname in [f"knowledge_v2_{l}" for l in KBV2_LADES] + ["knowledge_inbox"]:
        d = load_json(KBV2_DIR / f"{fname}.json", default={"kaarten": []})
        out.extend(d.get("kaarten", []) or [])
    return out


def _save_entries(entries):
    """v6_v2_first_001 — schrijf elke entry terug naar de V2 lade die hij claimt.
    Onbekende lade → inbox. V1-stijl entries (snap-*) worden overgeslagen."""
    by_lade = {l: [] for l in KBV2_LADES + ["inbox"]}
    for e in entries:
        eid = e.get("id") or ""
        if eid.startswith("snap-"):
            continue  # V1 is archief
        lade = (e.get("lade") or "").lower().strip()
        if lade not in KBV2_LADES:
            lade = "inbox"
        by_lade[lade].append(e)
    for lade, items in by_lade.items():
        fname = "knowledge_inbox" if lade == "inbox" else f"knowledge_v2_{lade}"
        save_json(KBV2_DIR / f"{fname}.json", {"kaarten": items})


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
    return secrets.choice(templates).replace("{begrip}", begrip[:60])


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

    v6_wedervraag_disable_001 — Globale uitschakeling via WEDERVRAAG_ENABLED.
    User vult kaarten zelf sneller in en de tussenvragen verstoren de flow.
    """
    if not WEDERVRAAG_ENABLED:
        return None
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
    if not WEDERVRAAG_ENABLED:
        return None
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
