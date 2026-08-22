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
from typing import Optional
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


# ═══════════════════════════════════════════════════════════════════
# v11_kb_fill_offer_001 — "Kan ik wat voor je doen"-flow
#
# Willems idee: als user proactief vraagt "kan ik wat voor je doen",
# Spark kiest zelf een random KBv2 kaart met een leeg ws5-veld en biedt
# aan die te laten invullen. Multi-turn:
#   1. User: "kan ik wat voor je doen"
#      → Spark: "Ja graag — op de kaart 'X' mist het veld 'wie'. Wil je die invullen?"
#      state: kb_fill_offer {entry_id, field}
#   2. User: "ja" → Spark stelt de vraag: "Wie is er bij 'X' betrokken?"
#      state: kb_fill_awaiting_answer {entry_id, field, begrip}
#   3. User: <antwoord>
#      → Spark: "Dus '{begrip}' — {field}: '{antwoord}'. Klopt dit?"
#      state: kb_fill_awaiting_confirm {entry_id, field, begrip, answer}
#   4. User: "ja" → apply_answer + save; "nee" → vraag om herformulering
# ═══════════════════════════════════════════════════════════════════
KAN_IK_HELPEN_PATTERNS = [
    r"\bkan\s+ik\s+(iets|wat)\s+(voor\s+(je|jou)\s+)?doen\b",
    r"\bwat\s+kan\s+ik\s+(voor\s+(je|jou)\s+)?doen\b",
    r"\bwaarmee\s+kan\s+ik\s+(je|jou)\s+helpen\b",
    r"\bhelp\s+je\s+een\s+handje\b",
    r"\biets\s+voor\s+(je|jou)\s+doen\b",
    r"\bwil\s+je\s+dat\s+ik\s+iets\s+(voor\s+(je|jou)\s+)?doe\b",
]

AFFIRMATIVE_PATTERNS = [
    r"^\s*(ja|jazeker|jep|yes|yep|klopt|correct|goed\s+zo|prima|okee?|oké|zeker|natuurlijk)\b",
    r"^\s*(doe\s+maar|graag|akkoord)\b",
]

NEGATIVE_PATTERNS = [
    r"^\s*(nee|nope|nah|niet\s+juist|niet\s+goed|klopt\s+niet|onjuist)\b",
    r"^\s*(laat\s+maar|later|skip|stop|geen\s+zin)\b",
]


def _match_any(text: str, patterns: list) -> bool:
    t = (text or "").strip().lower()
    for p in patterns:
        if re.search(p, t):
            return True
    return False


def wants_to_help(text: str) -> bool:
    """Detecteer of user proactief helpen aanbiedt."""
    return _match_any(text, KAN_IK_HELPEN_PATTERNS)


def is_affirmative(text: str) -> bool:
    return _match_any(text, AFFIRMATIVE_PATTERNS)


def is_negative(text: str) -> bool:
    return _match_any(text, NEGATIVE_PATTERNS)


def pick_random_kbv2_card_with_gap(exclude_ids: Optional[list] = None) -> Optional[dict]:
    """Zoek random KBv2-kaart met minstens 1 leeg ws5-veld.

    Returns dict {entry_id, begrip, field, lade, question} of None als alles gevuld is.
    Prefereert kaarten met MEER lege velden (grotere winst).
    """
    exclude_set = set(exclude_ids or [])
    all_entries = _load_entries()
    candidates = []
    for e in all_entries:
        eid = e.get("id") or ""
        if not eid or eid in exclude_set or eid.startswith("snap-"):
            continue
        begrip = (e.get("begrip") or "").strip()
        if not begrip:
            continue
        ws = e.get("ws5") or {}
        if not isinstance(ws, dict):
            continue
        empty_fields = [f for f in FIELD_PRIORITY if not str(ws.get(f) or "").strip()]
        if not empty_fields:
            continue
        candidates.append({
            "entry_id": eid,
            "begrip": begrip,
            "empty_fields": empty_fields,
            "lade": e.get("lade") or "",
        })
    if not candidates:
        return None
    # Bias: kaarten met meer lege velden hoger gewogen
    candidates.sort(key=lambda c: -len(c["empty_fields"]))
    # Neem top-30% en pick random
    top_n = max(1, len(candidates) // 3)
    pick = secrets.choice(candidates[:top_n])
    field = pick["empty_fields"][0]  # kies eerste-prioriteit
    return {
        "entry_id": pick["entry_id"],
        "begrip": pick["begrip"],
        "field": field,
        "lade": pick["lade"],
        "question": build_question(field, pick["begrip"]),
    }


def format_offer(offer: dict) -> str:
    """Bouw Spark's aanbod-tekst: 'Op de kaart X mist Y. Wil je die invullen?'"""
    field_label = {
        "wat": "Wat", "wanneer": "Wanneer", "waar": "Waar",
        "wie": "Wie", "waarom": "Waarom", "hoe": "Hoe",
    }.get(offer["field"], offer["field"])
    return (
        f"Ja graag — op de kaart '**{offer['begrip']}**' "
        f"mist het veld '{field_label}'. Wil jij die aanvullen?"
    )


def build_offer_from_card(card: dict) -> Optional[dict]:
    """v13_semantic_lookup_gap_offer_001 — bouw kb_fill_pending offer uit een
    kaart die door semantic_lookup als ws5-gap gemarkeerd is.

    Verschil met pick_random_kbv2_card_with_gap:
      - Die pakt een willekeurige kaart bij "kan ik wat voor je doen"-trigger
      - Deze pakt een SPECIFIEKE kaart die net in het gesprek relevant was
        (dus veel relevanter voor Willem om te beantwoorden)

    Returns offer-dict met dezelfde vorm als pick_random_kbv2_card_with_gap.
    """
    eid = card.get("id") or ""
    begrip = (card.get("begrip") or "").strip()
    if not eid or not begrip:
        return None
    ws = card.get("ws5") or {}
    if not isinstance(ws, dict):
        return None
    empty_fields = [f for f in FIELD_PRIORITY if not str(ws.get(f) or "").strip()]
    if not empty_fields:
        return None
    field = empty_fields[0]
    return {
        "entry_id": eid,
        "begrip": begrip,
        "field": field,
        "lade": card.get("lade") or card.get("_lade") or "",
        "question": build_question(field, begrip),
        "source": "semantic_lookup_gap",  # onderscheid met random-pick
    }


def format_paraphrase(begrip: str, field: str, answer: str) -> str:
    """Bouw parafrase voor bevestiging."""
    field_label = {
        "wat": "Wat", "wanneer": "Wanneer", "waar": "Waar",
        "wie": "Wie", "waarom": "Waarom", "hoe": "Hoe",
    }.get(field, field)
    return (
        f"Dus voor '**{begrip}**' — {field_label}: _{answer.strip()[:280]}_.\n\n"
        f"Klopt dit? (ja / nee)"
    )
