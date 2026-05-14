"""
Agenda Intent Service (v3_303 - Event Extraction, v4_024 polish)

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
# v4_024: dagdeel-woorden met default-tijd én day-offset (0 = vandaag)
DAGDELEN = {
    "vanochtend":  (0, 9, 0),
    "vanmorgen":   (0, 9, 0),
    "vanmiddag":   (0, 14, 0),
    "vanavond":    (0, 19, 0),
    "vannacht":    (0, 22, 0),
    "straks":      (0, None, None),  # tijd: now + 2h
    "later":       (0, None, None),
}

# v4_024: extra activity-woorden die NIET in calendar_triggers staan maar wel
# duidelijke event-titels zijn. Volgorde: specifiek → algemener.
EXTRA_ACTIVITIES = [
    "etentje", "feestje", "borrel", "borreltje", "uitje", "klusje", "tripje",
    "rondje", "wandelingetje", "fietstochtje", "dagje uit", "avondje uit",
    "afspraak", "afspraakje", "date", "verjaardagsfeest", "verjaardagje",
    "vakantie", "weekendje", "vakantietje", "reisje", "concertje",
]


def _load_calendar_triggers():
    return load_json(DATA_DIR / "triggers" / "calendar_triggers.json", default={})


def _load_keywords():
    return load_json(DATA_DIR / "keywords.json", default={})


# ---- Tijd-extractie ----

def extract_datetime(text: str):
    """
    Return (date_str ISO, raw_phrase, dag_woord, tijd_woord) of (None, None, None, None).
    Splitst output zodat de message-bouwer 'morgen' en '14:00' apart kan gebruiken.
    """
    text_lower = text.lower()
    base_date = None
    dag_woord = ""
    tijd_woord = ""
    default_hour, default_minute = 9, 0

    # v4_024: Dagdeel-woorden hebben ingebouwde default-tijd
    for w, (offset, h, m) in DAGDELEN.items():
        if re.search(rf"\b{w}\b", text_lower):
            base_date = (datetime.now() + timedelta(days=offset)).date()
            dag_woord = w
            if w in ("straks", "later"):
                later = datetime.now() + timedelta(hours=2)
                default_hour, default_minute = later.hour, later.minute
            else:
                default_hour, default_minute = h, m
            break

    # Relatieve dag (vandaag/morgen)
    if base_date is None:
        for w, offset in RELATIVE.items():
            if re.search(rf"\b{w}\b", text_lower):
                base_date = (datetime.now() + timedelta(days=offset)).date()
                dag_woord = w
                break

    # Vaste weekdag
    if base_date is None:
        today_wd = datetime.now().weekday()
        for w, wd in DAGEN.items():
            if re.search(rf"\b{w}\b", text_lower):
                days_ahead = (wd - today_wd) % 7
                if days_ahead == 0:
                    days_ahead = 7
                base_date = (datetime.now() + timedelta(days=days_ahead)).date()
                dag_woord = w
                break

    if base_date is None:
        return None, None, None, None

    # Tijd: 12:30 / 12.30 / 12 uur / 14u — overschrijft default
    hour, minute = default_hour, default_minute
    m = re.search(r"\b(\d{1,2})[:.](\d{2})\b", text_lower)
    if m:
        hour = int(m.group(1))
        minute = int(m.group(2))
        tijd_woord = f"{hour:02d}:{minute:02d}"
    else:
        m = re.search(r"\b(\d{1,2})\s*(?:uur|u\b)", text_lower)
        if m:
            hour = int(m.group(1))
            minute = 0
            tijd_woord = m.group(0).strip()

    # v4_024: Dagdeel-modifier ('s avonds, 's ochtends, 's middags, 's nachts)
    # converteert 12-uurs uitspraak naar 24-uurs klok.
    # Regel: standaard is 24h. Maar als 'savonds/avonds/'s middags wordt gezegd
    # bij een uur 1-11 → +12. 'ochtends' laat 1-11 staan.
    # OOK: dagdeel-woord (vanavond/vannacht) impliceert 's avonds bij uur 1-11.
    has_avond = bool(re.search(r"\b(?:'?s?\s*avonds|s avonds|vanavond)\b", text_lower))
    has_middag = bool(re.search(r"\b(?:'?s?\s*middags|s middags|in de middag|vanmiddag)\b", text_lower))
    has_nacht = bool(re.search(r"\b(?:'?s?\s*nachts|s nachts|vannacht)\b", text_lower))
    # 'ochtend' wordt momenteel niet gebruikt voor +12, maar is detect-vriendelijk
    # voor toekomstige gebruik (default-tijd verfijnen).

    if 1 <= hour <= 11:
        if has_avond or has_nacht:
            hour += 12
        elif has_middag and hour <= 5:
            hour += 12
    elif hour == 12 and has_nacht:
        hour = 0

    if 0 <= hour <= 23 and 0 <= minute <= 59:
        # Update tijd_woord met definitieve 24h-versie (na 's avonds-conversie)
        if tijd_woord and minute == 0 and "uur" in tijd_woord:
            tijd_woord = f"{hour} uur"
        elif tijd_woord:
            tijd_woord = f"{hour:02d}:{minute:02d}"
        dt = datetime.combine(base_date, datetime.min.time()).replace(hour=hour, minute=minute)
        return dt.isoformat(), f"{dag_woord} {tijd_woord}".strip(), dag_woord, tijd_woord
    return None, None, None, None


# ---- Activiteit-extractie ----

def extract_what(text: str) -> str:
    """
    Vind het 'wat' — activiteit of zelfstandig naamwoord.
    Volgorde:
      1) calendar_triggers categorieën (behalve time/action_verbs)
      2) EXTRA_ACTIVITIES lijst (etentje/borrel/uitje/etc.)
      3) leeg
    """
    text_lower = text.lower()
    cal = _load_calendar_triggers().get("triggers", {})

    # Pass 1: calendar triggers — domeinspecifieke woorden (tandarts, vergadering, ...)
    for cat, words in cal.items():
        if cat in ("time_indicators", "action_verbs"):
            continue
        if not isinstance(words, list):
            continue
        for w in words:
            if re.search(rf"\b{re.escape(w)}\b", text_lower):
                return w

    # Pass 2: extra activiteit-woorden (etentje, borrel, uitje)
    for w in EXTRA_ACTIVITIES:
        if re.search(rf"\b{re.escape(w)}\b", text_lower):
            return w

    return ""


def extract_what_category(text: str) -> str:
    """v4_024: bepaal categorie van de activiteit voor nettere zinsbouw."""
    text_lower = text.lower()
    cal = _load_calendar_triggers().get("triggers", {})
    for cat, words in cal.items():
        if cat in ("time_indicators", "action_verbs"):
            continue
        if not isinstance(words, list):
            continue
        for w in words:
            if re.search(rf"\b{re.escape(w)}\b", text_lower):
                return cat
    return ""


# ---- Locatie-extractie ----

LOC_PREPS = ["in", "bij", "op", "naar", "te"]
# v4_024: lowercase plaats-hints (bv. "bij oma", "op kantoor", "naar de kapper")
LOWER_PLACES = {
    "oma", "opa", "mama", "papa", "moeder", "vader", "broer", "zus",
    "kantoor", "thuis", "huis", "werk", "school", "kerk", "stad",
    "park", "strand", "supermarkt", "tandarts", "dokter", "kapper", "fysio",
}


def extract_where(text: str) -> str:
    """
    Zoek 'in/bij/op/naar/te <Plek>'. Plek = woord met hoofdletter,
    OF expliciete lowercase plek-marker (oma, kantoor, thuis, ...).
    """
    for prep in LOC_PREPS:
        # 1) Hoofdletter-plaatsnaam (Groningen, Marian, ...)
        m = re.search(
            rf"\b{prep}\s+(?:de\s+|het\s+|een\s+)?([A-Z][a-zéèêëïüöà]+(?:\s+[A-Z][a-zéèêëïüöà]+)?)",
            text,
        )
        if m:
            return m.group(1).strip()
        # 2) Lowercase persoonlijke/gewone plek (oma, kantoor, school)
        m = re.search(
            rf"\b{prep}\s+(?:de\s+|het\s+|een\s+)?({'|'.join(LOWER_PLACES)})\b",
            text.lower(),
        )
        if m:
            return m.group(1).strip()
    return ""


# ---- Intent-detectie ----

def detect_agenda_intent(text: str) -> dict:
    """
    Return dict {has_intent, dag, tijd, raw_time, wat, waar, datetime_iso, categorie}
    of {has_intent: False}.

    Een agenda-intentie vereist:
    - tijd-aanduiding IN DE TOEKOMST
    - EN een action_verb, activiteit, of locatie
    """
    when_iso, raw_time, dag, tijd = extract_datetime(text)
    if not when_iso:
        return {"has_intent": False}

    try:
        target = datetime.fromisoformat(when_iso)
        if target < datetime.now():
            return {"has_intent": False}
    except Exception:
        return {"has_intent": False}

    wat = extract_what(text)
    waar = extract_where(text)
    categorie = extract_what_category(text)

    if not (wat or waar):
        return {"has_intent": False}

    # v4_024: voorkom duplicaat (waar==wat bij 'naar de kapper' → kapper × 2)
    if waar and waar.lower() == (wat or "").lower():
        waar = ""

    return {
        "has_intent": True,
        "datetime_iso": when_iso,
        "raw_time": raw_time,
        "dag": dag,
        "tijd": tijd,
        "wat": wat,
        "waar": waar,
        "categorie": categorie,
    }


# v4_024: Werkwoord-mapping per activiteit voor natuurlijke zinsbouw.
# Twee categorieën:
#  GAAT_X = "gaat <wat>" (werkwoorden zoals wandelen/sporten/bellen)
#  HEEFT_X = "hebt een <wat>" (zelfstandige naamwoorden zoals vergadering/etentje)
GAAT_WERKWOORDEN = {
    "wandelen", "bellen", "appen", "lunchen", "dineren", "eten",
    "koffiedrinken", "koffie drinken", "borrelen", "ontmoeten",
    "praten", "bijpraten", "opruimen", "schoonmaken", "tuinieren",
    "klussen", "wassen", "stofzuigen", "strijken", "shoppen",
    "winkelen", "kopen", "sporten", "zwemmen", "hardlopen", "fietsen",
    "fitness", "lezen", "gamen", "kijken",
    "boodschappen", "boodschappen doen",
}
HEEFT_NAAMWOORDEN = {
    "feestje", "verjaardag", "etentje", "borrel", "uitje", "klusje",
    "tripje", "rondje", "wandelingetje", "fietstochtje", "afspraak",
    "afspraakje", "date", "verjaardagsfeest", "verjaardagje",
    "vakantie", "weekendje", "reisje", "concertje", "concert", "theater",
    "vergadering", "meeting", "presentatie", "deadline", "overleg",
    "interview", "training", "yoga", "gesprek", "evenement",
    "tandarts", "dokter", "fysio", "kapper", "huisarts", "controle",
    "voetbal", "hockey", "tennis", "voetbaltraining",
}

# Mooiere rendering van losse wat-woorden (multi-word → 1 woord)
WAT_RENDER = {
    "koffie drinken": "koffiedrinken",
    "boodschappen doen": "boodschappen doen",
}


def format_event_title(pending: dict) -> str:
    """Maak een nette titel voor het agenda-event (Hoofdletter, evt. + waar)."""
    wat_raw = (pending.get("wat") or "").lower()
    wat = WAT_RENDER.get(wat_raw, wat_raw)
    waar = pending.get("waar") or ""
    if wat and waar:
        return f"{wat.capitalize()} bij {waar}" if waar[:1].isupper() else f"{wat.capitalize()}"
    if wat:
        return wat.capitalize()
    if waar:
        return f"Bij {waar}"
    return "Afspraak"


def _location_phrase(waar: str) -> str:
    """Bouw correcte 'voorzetsel + locatie' fragment."""
    if not waar:
        return ""
    plek = waar.lower().strip()
    # Hoofdletter = persoon of plaats
    if waar[0].isupper():
        # Plaatsnamen (stad/dorp/land) → 'in', persoonsnamen → 'bij'
        # Heuristiek: 1 woord met hoofdletter en lengte > 4 = vaak plaats
        # Voor mensennamen vaak korter en gangbaarder. Niet perfect, gebruikt 'bij' als default.
        # Specifieke override: bekende plaatsen via in.
        if plek in {"groningen", "amsterdam", "rotterdam", "utrecht", "den haag",
                    "eindhoven", "tilburg", "almere", "breda", "nijmegen", "haarlem",
                    "arnhem", "zwolle", "leiden", "leeuwarden", "assen", "emmen"}:
            return f"in {waar}"
        return f"bij {waar}"
    # Lowercase plekken
    if plek in {"kantoor", "werk", "school", "stad"}:
        return f"op {plek}"
    if plek in {"thuis"}:
        return plek  # 'morgen thuis stofzuigen' → 'thuis'
    if plek in {"tandarts", "dokter", "kapper", "fysio", "huisarts",
                "supermarkt", "park", "strand"}:
        return f"naar de {plek}"
    # Personen lowercase (oma, opa, moeder, ...)
    return f"bij {plek}"


def build_proposal_message(intent: dict, has_conflict: bool = False) -> str:
    """Bouw vriendelijk voorstel met correcte NL-zinsbouw."""
    dag = intent.get("dag", "")
    tijd = intent.get("tijd", "")
    wat_raw = (intent.get("wat") or "").lower()
    wat = WAT_RENDER.get(wat_raw, wat_raw)
    waar = intent.get("waar", "")

    # Tijd-zin: 'om 14:00' / 'om 9 uur' / '' (geen tijd)
    tijd_zin = f"om {tijd}" if tijd else ""

    # Locatie-zin
    loc_zin = _location_phrase(waar)

    # Werkwoord-keuze
    if wat in GAAT_WERKWOORDEN:
        # 'morgen om 14:00 gaat wandelen bij oma'
        delen = [dag, tijd_zin, f"gaat {wat}", loc_zin]
    elif wat in HEEFT_NAAMWOORDEN:
        # 'morgen om 14:00 een vergadering bij Marian hebt' → herordenen
        # NL: '...morgen om 14:00 een vergadering hebt' / '... morgen tandarts hebt'
        article = "" if wat in {"tandarts", "dokter", "fysio", "kapper", "huisarts",
                                "yoga", "fitness", "vakantie", "training"} else "een"
        delen = [dag, tijd_zin, f"{article} {wat}".strip(), loc_zin, "hebt"]
    elif wat:
        # Onbekende activiteit
        delen = [dag, tijd_zin, f"iets met {wat}", loc_zin, "hebt"]
    else:
        # Alleen locatie
        delen = [dag, tijd_zin, loc_zin, "iets hebt"]

    core = " ".join(x for x in delen if x)
    sentence = f"Ik hoorde dat je {core}."
    # Dubbele spaties opruimen
    sentence = re.sub(r"\s+", " ", sentence)

    if has_conflict:
        return f"{sentence} Je agenda zit op die tijd al vol. Toch noteren?"
    return f"{sentence} Zal ik het noteren?"


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
