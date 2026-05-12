"""
Agenda Intent Service (v3_303 - Event Extraction)

Doel: detecteer of een chat-bericht een agenda-intentie bevat,
extract velden {wanneer, wat, waar} en bouw bevestigingsvraag.

Strategie:
- Hergebruikt bestaande calendar_triggers.json (action_verbs + time_indicators)
- Hergebruikt keywords.tijd voor dag/tijd-woorden
- Regex voor concrete tijden (12 uur, 12:30, 14u)
- Locatie-detectie via 'in/bij/op' + hoofdletterwoord
- Resulteert in voorstel-object dat in session_state wacht op ja/nee
"""
from pathlib import Path
import re
from datetime import datetime, timedelta
from modules.core.storage import load_json

DATA_DIR = Path(__file__).parent.parent.parent / "data"

# Dag-mapping voor parsing (NL → relatief)
DAGEN = {
    "maandag": 0, "dinsdag": 1, "woensdag": 2, "donderdag": 3,
    "vrijdag": 4, "zaterdag": 5, "zondag": 6,
}
RELATIVE = {
    "vandaag": 0, "morgen": 1, "overmorgen": 2,
    "gisteren": -1, "eergisteren": -2,
}


def _load_calendar_triggers():
    return load_json(DATA_DIR / "triggers" / "calendar_triggers.json", default={})


def _load_keywords():
    return load_json(DATA_DIR / "keywords.json", default={})


# ---- Tijd-extractie ----

def extract_datetime(text: str):
    """
    Return (date_str ISO, raw_phrase) of (None, None).
    Combineert dag-woord + tijd ("maandag 12 uur" / "morgen om 14:30").
    """
    text_lower = text.lower()
    base_date = None
    raw_parts = []

    # Relatieve dag (vandaag/morgen)
    for w, offset in RELATIVE.items():
        if re.search(rf"\b{w}\b", text_lower):
            base_date = (datetime.now() + timedelta(days=offset)).date()
            raw_parts.append(w)
            break

    # Vaste weekdag
    if base_date is None:
        today_wd = datetime.now().weekday()
        for w, wd in DAGEN.items():
            if re.search(rf"\b{w}\b", text_lower):
                # Eerstvolgende voorkomen van deze weekdag
                days_ahead = (wd - today_wd) % 7
                if days_ahead == 0:
                    days_ahead = 7  # volgende week
                base_date = (datetime.now() + timedelta(days=days_ahead)).date()
                raw_parts.append(w)
                break

    if base_date is None:
        return None, None

    # Tijd: 12:30 / 12.30 / 12 uur / 14u
    hour, minute = 9, 0  # default 09:00
    m = re.search(r"\b(\d{1,2})[:.](\d{2})\b", text_lower)
    if m:
        hour = int(m.group(1))
        minute = int(m.group(2))
        raw_parts.append(m.group(0))
    else:
        m = re.search(r"\b(\d{1,2})\s*(?:uur|u\b)", text_lower)
        if m:
            hour = int(m.group(1))
            minute = 0
            raw_parts.append(m.group(0))

    if 0 <= hour <= 23 and 0 <= minute <= 59:
        dt = datetime.combine(base_date, datetime.min.time()).replace(hour=hour, minute=minute)
        return dt.isoformat(), " ".join(raw_parts)
    return None, None


# ---- Activiteit-extractie ----

def extract_what(text: str) -> str:
    """
    Vind het 'wat' — activiteit of zelfstandig naamwoord na een action_verb of in calendar-categorie.
    Fallback: het langste zinvol woord dat niet tijd/locatie is.
    """
    text_lower = text.lower()
    cal = _load_calendar_triggers().get("triggers", {})

    # Loop door alle categorieën behalve time_indicators
    for cat, words in cal.items():
        if cat in ("time_indicators",):
            continue
        if not isinstance(words, list):
            continue
        for w in words:
            if re.search(rf"\b{re.escape(w)}\b", text_lower):
                return w
    return ""


# ---- Locatie-extractie ----

LOC_PREPS = ["in", "bij", "op", "naar", "te"]


def extract_where(text: str) -> str:
    """
    Zoek 'in <Plek>', 'bij <Persoon>', 'op <Plek>'. Plek = woord met hoofdletter
    of expliciete plek-marker.
    """
    # Sla originele case op voor hoofdletter-detectie
    # 'in Groningen' -> Groningen
    for prep in LOC_PREPS:
        m = re.search(rf"\b{prep}\s+(?:de\s+|het\s+|een\s+)?([A-Z][a-zéèêëïüöà]+(?:\s+[A-Z][a-zéèêëïüöà]+)?)", text)
        if m:
            return m.group(1).strip()
    return ""


# ---- Intent-detectie ----

def detect_agenda_intent(text: str) -> dict:
    """
    Return dict {has_intent, wanneer, wat, waar, raw_time, datetime_iso}
    of {has_intent: False}.

    Een agenda-intentie vereist:
    - tijd-aanduiding IN DE TOEKOMST
    - EN een action_verb of locatie
    """
    when_iso, raw_time = extract_datetime(text)
    if not when_iso:
        return {"has_intent": False}

    # Alleen toekomst — verleden tijd ('gisteren', 'eergisteren') is geen agenda-intent
    try:
        target = datetime.fromisoformat(when_iso)
        if target < datetime.now():
            return {"has_intent": False}
    except Exception:
        return {"has_intent": False}

    wat = extract_what(text)
    waar = extract_where(text)

    # Heuristiek: tijd + (wat of waar) → intentie
    if not (wat or waar):
        return {"has_intent": False}

    return {
        "has_intent": True,
        "datetime_iso": when_iso,
        "raw_time": raw_time,
        "wat": wat,
        "waar": waar,
    }


def build_proposal_message(intent: dict, has_conflict: bool = False) -> str:
    """Bouw vriendelijk voorstel om agenda te noteren."""
    when = intent.get("raw_time", "?")
    wat = intent.get("wat") or "afspraak"
    waar = intent.get("waar")

    parts = [f"Ik hoorde dat je een **{wat}**"]
    if waar:
        parts.append(f"in {waar}")
    parts.append(f"hebt ({when}).")
    base = " ".join(parts)

    if has_conflict:
        return f"{base} Je agenda zit op die tijd al vol. Toch noteren?"
    return f"{base} Er staat niks in je agenda. Zal ik het noteren?"


def has_agenda_conflict(user_id: str, dt_iso: str) -> bool:
    """Check of er al een event is op die dag (zelfde uur range)."""
    if not user_id or not dt_iso:
        return False
    try:
        target = datetime.fromisoformat(dt_iso)
    except Exception:
        return False
    path = DATA_DIR / "agenda" / f"{user_id}.json"
    data = load_json(path, default={"events": []})
    for ev in data.get("events", []):
        try:
            existing = datetime.fromisoformat(ev.get("date", ""))
            if existing.date() == target.date() and abs((existing - target).total_seconds()) < 3600:
                return True
        except Exception:
            continue
    return False
