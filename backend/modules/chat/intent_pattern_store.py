"""
Intent Pattern Store (v13d_intent_patterns_json_001, sessie 55)
================================================================

Centrale registry voor alle regex-patronen die chat-intents matchen.

**Doel** (Willem, sessie 55):
- Alle hardcoded intent-patronen migreren naar JSON zodat Triggers-tab de bron
  van waarheid wordt.
- Nieuwe patronen kunnen live via UI worden toegevoegd zonder redeploy.
- Bestaande code blijft werken via BASELINE: als JSON leeg is, fallback op
  hardcoded lijst.

**Werking**:
1. Modules registreren een `BASELINE` dict (intent_key → list[regex-str]).
2. Runtime pattern-lookup = BASELINE + JSON-additions (`intent_patterns.json`).
3. Cache met mtime-check zodat live edits direct doorwerken.

**JSON-schema** (`/data/triggers/intent_patterns.json`):
```json
{
  "_meta": { ... },
  "agenda_read":   ["\\bwat staat\\b.*\\bagenda\\b", ...],
  "agenda_delete": ["\\bhaal\\b.*\\buit (de|mijn) agenda\\b", ...]
}
```

De UI schrijft naar deze file via `/api/triggers/edit/intent/{key}/{op}`.
"""
from __future__ import annotations

import re
import threading
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Pattern

from modules.core.storage import load_json, save_json

_DATA_DIR = Path(__file__).parent.parent.parent / "data"
_JSON_PATH = _DATA_DIR / "triggers" / "intent_patterns.json"

# ─────────────────────────────────────────────────────────────────────────────
# BASELINE — hardcoded patronen die ALTIJD werken (fallback bij lege JSON)
# ─────────────────────────────────────────────────────────────────────────────
#
# Deze dict is de single source of truth voor het BASISgedrag van Spark.
# JSON kan patronen TOEVOEGEN maar niet weghalen — dat is bewust: de basis
# moet nooit stuk gaan doordat iemand per ongeluk iets in de UI wist.
#
BASELINE: Dict[str, List[str]] = {
    # AGENDA
    "agenda_read": [
        r"\bwat staat\b.*\b(agenda|planning|gepland)\b",
        r"\bwat staat (er|op (de )?planning)\b",
        r"\bwat (staat|heb ik) (er )?(vandaag|morgen|overmorgen|deze week)\b",
        r"\bwat staat er\b.*\b(maandag|dinsdag|woensdag|donderdag|vrijdag|zaterdag|zondag)\b",
        r"\bafspraak\b.*\b(maandag|dinsdag|woensdag|donderdag|vrijdag|zaterdag|zondag)\b",
        r"\b(uit )?(mijn )?agenda\b.*\b(maandag|dinsdag|woensdag|donderdag|vrijdag|zaterdag|zondag)\b",
        r"\b(uit|in|van)\s+(de|mijn)\s+agenda\b.*\b(halen|lezen|kijken|zien|checken)\b",
        r"\b(afspraak|afspraken)\b.*\b(van|voor|op)\b.*\b(maandag|dinsdag|woensdag|donderdag|vrijdag|zaterdag|zondag|vandaag|morgen|overmorgen)\b",
        r"\b(heb|hebben) ik\b.*\b(afspraken|afspraak|in (de )?agenda)\b",
        r"\b(heb|hebben) ik\s+(vandaag|morgen|overmorgen)\b.*\b(afspraken|afspraak|wat te doen|iets te doen)\b",
        r"\b(heb|hebben) ik\s+(vandaag|morgen|overmorgen|deze week)\b.*\b(te doen|iets|wat)",
        r"\bagenda\b.*\b(vandaag|morgen|overmorgen|deze week)\b",
        r"\bkijk\s+(?:in|naar)?\s*(?:de\s+|mijn\s+)?(agenda|planning)\b",
        r"\bwelke afspraken\b",
        r"\b(mijn |de )?planning\b.*\b(vandaag|morgen)\b",
    ],
    "agenda_delete": [
        # v13d_agenda_delete_001 — Willem: "haal aanstaande dinsdag uit de agenda"
        # Spark antwoordde eerder "doe dat via de agenda-tab" i.p.v. te executeren.
        # Match op: verwijder/haal/schrap/annuleer + agenda/afspraak.
        r"\b(haal|verwijder|schrap|wis|annuleer|cancel|gooi\s+weg|delete)\b.*\b(uit|van)\s+(de|mijn)\s+agenda\b",
        r"\b(haal|verwijder|schrap|wis|annuleer|cancel|delete)\b.*\bafspraak\b",
        r"\b(afspraak|afspraken)\s+(op|van|voor)\s+.+\s+(verwijder|weghalen|annuleer|schrap)",
        r"\bagenda\b.*\b(leegmaken|opschonen|opruimen)\b",
        r"\b(verwijder|haal weg|schrap)\s+(?:het\s+|de\s+|mijn\s+)?(evenement|event|afspraak)\b",
    ],

    # NOTES / BUGS
    "note_create": [
        r"^\s*(?:maak|voeg|schrijf|zet|noteer|onthoud|leg)\s+(?:eens\s+)?(?:een|de|mijn|nieuwe|deze)?\s*(?:nieuwe\s+)?(?:notitie|note|memo|aantekening)\s*(?:aan|toe|op|vast)?\s*[:\-]\s*(.+)$",
        r"^\s*(?:nieuwe\s+)?(?:notitie|note|memo|aantekening)\s*[:\-]\s*(.+)$",
        r"^\s*(?:noteer|onthoud|schrijf\s+op|leg\s+vast)\s*[:\-]?\s*(.+)$",
    ],
    "bug_report": [
        r"^\s*(?:meld|rapporteer|voeg\s+toe)?\s*(?:een\s+|de\s+)?(?:nieuwe\s+)?(?:bug|foutmelding|issue)\s*(?:rapport)?\s*[:\-]\s*(.+)$",
        r"^\s*(?:er\s+is\s+(?:een\s+)?(?:bug|fout|probleem)|er\s+gaat\s+iets\s+mis)\s*[:\-]?\s*(.+)$",
    ],

    # HELP / SUGGEST / TOPIC
    "help_overview": [
        r"\bwat kan je\b",
        r"\bwat kun je\b",
        r"\bhoe werk je\b",
        r"^\s*/?help[\s.!?]*$",
        r"\bwelke (commands|opdrachten|functies)\b",
        r"\bwat zijn je (mogelijkheden|capaciteiten)\b",
        r"\b(open|toon|laat zien|geef|opent?)\s+(de\s+|het\s+)?help(\s+(kader|overzicht|menu|popup|venster|paneel))?\b",
        r"\bhelp(\s+(kader|overzicht|menu|popup|venster|paneel))\b",
        r"\bik wil de? help\b",
        r"\bhelp\s+nodig\b",
    ],
    "suggest_action": [
        r"\bwat zullen we\b",
        r"\bwat (kunnen|gaan) we (gaan )?doen\b",
        r"\b(geef me|heb je) (een )?(idee|voorstel|suggestie)\b",
        r"\bwaar (moet|zou) ik aan werken\b",
        r"\bwat is (er )?(belangrijk|urgent)\b",
    ],
    "topic_overview": [
        r"\bvertel (me |mij )?(eens )?over\s+(.+)$",
        r"\bwat heb je (allemaal )?over\s+(.+)\?",
        r"\balles over\s+(.+)$",
        r"\bwat weet je over\s+(.+)\?",
        r"\boverzicht\s+(van )?(.+)$",
    ],

    # ACCOUNT / CLARIFY / RECAP / DND
    "account_delete": [
        r"\b(verwijder|wis|delete|sluit|stop)\s+(mijn|m'n|me)\s+account\b",
        r"\b(ik wil|wil)\s+mijn\s+account\s+(verwijder|wissen|opzeggen|deleten|kwijt|weg)",
        r"\bmijn\s+account\s+(verwijder|wissen|deleten|opzeggen)",
        r"\b(deactiveer|opheffen|opzeggen)\s+(mijn|m'n|me)\s+account\b",
        r"\baccount\s+(verwijder|opzeggen|sluiten)\b",
    ],
    "clarify": [
        r"\bnee\b.*\b(bedoel|bedoelde)\b",
        r"\b(bedoel|bedoelde) ik niet\b",
        r"\bdat (bedoel|bedoelde) ik niet\b",
        r"\b(verkeerd|fout)\b.*(begrepen|begrip|woord)\b",
    ],
    "community_recap": [
        r"\bwat (is|was|werd) (er )?(gisteren|vandaag|eergisteren).{0,40}(besproken|gezegd|gepraat|gepost)\b",
        r"\bwat (is|was) er (gisteren|vandaag|eergisteren).{0,30}(community|chat)\b",
        r"\bcommunity (recap|samenvatting|overzicht)\b",
        r"\b(samenvatting|recap) (van )?(de )?community\b",
        r"\bwat heeft (de )?community (gisteren|vandaag|eergisteren) (gezegd|besproken)\b",
        r"\bwat (is|was) er (gisteren|vandaag|eergisteren) (besproken|gezegd|gepraat)\b",
    ],
    "dnd_help": [
        r"\bd\&?d (help|uitleg|wat is)\b",
        r"\bhelp.{0,10}d\&?d\b",
        r"\bwat (is|zijn) d\&?d\b",
        r"\bhoe werkt d\&?d\b",
        r"\bspark world (uitleg|help)\b",
        r"\bbase line (uitleg|wat)\b",
        r"\bpersoonskaart (help|uitleg)\b",
        r"\brugzak (help|uitleg)\b",
        r"\binventory (help|uitleg)\b",
        r"\bbark (help|uitleg|wat is)\b",
    ],

    # ACTION INTENTS (STT/TTS/AMBIENT)
    "stt_on": [
        r"\(\s*s[ts]t\s+aan\s*\)",
        r"\(\s*spraak\s+naar\s+te?xt\s+aan\s*\)",
        r"\(\s*spraak\s+naar\s+tekst\s+aan\s*\)",
        r"\bspeech[-\s]?to[-\s]?text\s+(aan|aanzetten|activeren|start|aan zetten|aanzettten)\b",
        r"\bs[ts]t\s+(aan|aanzetten|activeren|start)\b",
        r"\bspraak\s+naar\s+te?xt\s+aan\b",
        r"\bspraak\s+naar\s+tekst\s+aan\b",
        r"\b(zet|doe)\s+(de\s+)?(speech[-\s]?to[-\s]?text|s[ts]t|microfoon|micro|mic)\s+aan\b",
        r"\b(start|activeer)\s+(de\s+)?(speech[-\s]?to[-\s]?text|s[ts]t|microfoon|micro|mic|spraak|spraakherkenning)\b",
        r"\bik\s+wil\s+(praten|spreken|inspreken)\b",
        r"\bmicrofoon\s+aan\b",
        r"\b(luister|hoor)\s+(naar\s+)?(me|mij)\b",
    ],
    "stt_off": [
        r"\(\s*s[ts]t\s+uit\s*\)",
        r"\(\s*spraak\s+naar\s+te?xt\s+uit\s*\)",
        r"\(\s*spraak\s+naar\s+tekst\s+uit\s*\)",
        r"\bspeech[-\s]?to[-\s]?text\s+(uit|uitzetten|stoppen|stop|deactiveren|uit zetten)\b",
        r"\bs[ts]t\s+(uit|uitzetten|stoppen|stop|deactiveren)\b",
        r"\bspraak\s+naar\s+te?xt\s+uit\b",
        r"\bspraak\s+naar\s+tekst\s+uit\b",
        r"\b(zet|doe)\s+(de\s+)?(speech[-\s]?to[-\s]?text|s[ts]t|microfoon|micro|mic)\s+uit\b",
        r"\b(stop|deactiveer)\s+(de\s+)?(speech[-\s]?to[-\s]?text|s[ts]t|microfoon|micro|mic|spraak|spraakherkenning)\b",
        r"\b(ik\s+wil\s+)?(weer\s+)?typen\b",
        r"\bmicrofoon\s+uit\b",
    ],
    "tts_on": [
        r"\(\s*t[ts]s\s+aan\s*\)",
        r"\(\s*te?xt\s+naar\s+spraak\s+aan\s*\)",
        r"\btext[-\s]?to[-\s]?speech\s+(aan|aanzetten|activeren|start)\b",
        r"\bt[ts]s\s+(aan|aanzetten|activeren|start)\b",
        r"\bte?xt\s+naar\s+spraak\s+aan\b",
        r"\b(zet|doe)\s+(de\s+)?(t[ts]s|text[-\s]?to[-\s]?speech|stem|spraak\s*output)\s+aan\b",
        r"\bik\s+wil\s+(je|spark|hem)\s+horen\b",
        r"\b(spreek|praat)\s+(tegen\s+)?(me|mij|tegen)\b",
        r"\b(stem|spraak)\s+aan\b",
        r"\b(zet|doe)\s+(je\s+)?stem\s+aan\b",
    ],
    "tts_off": [
        r"\(\s*t[ts]s\s+uit\s*\)",
        r"\(\s*te?xt\s+naar\s+spraak\s+uit\s*\)",
        r"\btext[-\s]?to[-\s]?speech\s+(uit|uitzetten|stoppen|stop|deactiveren)\b",
        r"\bt[ts]s\s+(uit|uitzetten|stoppen|stop|deactiveren)\b",
        r"\bte?xt\s+naar\s+spraak\s+uit\b",
        r"\b(zet|doe)\s+(de\s+)?(t[ts]s|text[-\s]?to[-\s]?speech|stem|spraak\s*output)\s+uit\b",
        r"\b(stop|hou\s+op)\s+(met\s+)?(praten|spreken)\b",
        r"\b(wees|ben)\s+(stil|stilletjes)\b",
        r"\b(stem|spraak)\s+uit\b",
    ],
    "ambient_off": [
        r"^\s*(stilte|stil)[\s.!?]*$",
        r"\b(even|nu|zet)\s+(stilte|het\s+stil)\b",
        r"\bambient\s*\d*\s*(uit|stop|af|weg)\b",
        r"\b(stop|zet)\s+(de\s+)?(muziek|geluid|loop|ambient|achtergrondgeluid|natuur|vogels|vogeltjes)\s*(uit|af|stop)?\b",
        r"\b(muziek|geluid|loop|ambient|achtergrondgeluid|natuur|vogels|vogeltjes)\s+(uit|stop|weg)\b",
        r"\b(geen|niks)\s+geluid\s*(meer)?\b",
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
# Cache met mtime-invalidation
# ─────────────────────────────────────────────────────────────────────────────
_lock = threading.RLock()
_cache_mtime: Optional[float] = None
_cache_compiled: Dict[str, List[Pattern]] = {}
_cache_raw: Dict[str, List[str]] = {}


def _read_json_patterns() -> Dict[str, List[str]]:
    """Lees intent_patterns.json en normaliseer naar {intent_key: [patronen]}."""
    if not _JSON_PATH.exists():
        return {}
    data = load_json(_JSON_PATH, default={})
    if not isinstance(data, dict):
        return {}
    out: Dict[str, List[str]] = {}
    for key, val in data.items():
        if key.startswith("_"):
            continue
        if isinstance(val, list):
            out[key] = [str(p) for p in val if isinstance(p, str) and p.strip()]
    return out


def _rebuild_cache() -> None:
    """Herbouw compiled cache uit BASELINE + JSON. Non-fatale compile errors worden geskipt."""
    raw: Dict[str, List[str]] = {}
    for k, lst in BASELINE.items():
        raw[k] = list(lst)
    for k, lst in _read_json_patterns().items():
        raw.setdefault(k, [])
        # Voeg toe zonder duplicates (case-sensitive vergelijking op regex-string)
        seen = set(raw[k])
        for p in lst:
            if p not in seen:
                raw[k].append(p)
                seen.add(p)

    compiled: Dict[str, List[Pattern]] = {}
    for k, lst in raw.items():
        pats = []
        for p in lst:
            try:
                pats.append(re.compile(p, re.IGNORECASE))
            except re.error:
                # Ongeldige regex uit JSON — sla over, laat baseline werken
                continue
        compiled[k] = pats

    global _cache_compiled, _cache_raw
    _cache_compiled = compiled
    _cache_raw = raw


def _ensure_fresh() -> None:
    """Reload cache als JSON is gewijzigd (mtime check)."""
    global _cache_mtime
    with _lock:
        try:
            mt = _JSON_PATH.stat().st_mtime if _JSON_PATH.exists() else 0.0
        except OSError:
            mt = 0.0
        if _cache_mtime is None or mt != _cache_mtime or not _cache_compiled:
            _cache_mtime = mt
            _rebuild_cache()


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def get_patterns(intent_key: str) -> List[Pattern]:
    """Return gecombineerde compiled patronen (baseline + JSON) voor een intent."""
    _ensure_fresh()
    return _cache_compiled.get(intent_key, [])


def get_raw_patterns(intent_key: str) -> List[str]:
    """Return gecombineerde raw regex-strings voor een intent."""
    _ensure_fresh()
    return list(_cache_raw.get(intent_key, []))


def get_baseline(intent_key: str) -> List[str]:
    """Return uitsluitend hardcoded baseline (niet-verwijderbaar)."""
    return list(BASELINE.get(intent_key, []))


def get_json_additions(intent_key: str) -> List[str]:
    """Return alleen patronen uit JSON (extra bovenop baseline)."""
    return list(_read_json_patterns().get(intent_key, []))


def match_any(intent_key: str, text: str) -> bool:
    """True als ≥1 patroon (baseline of JSON) matcht op de tekst."""
    if not text:
        return False
    for p in get_patterns(intent_key):
        if p.search(text):
            return True
    return False


def find_first(intent_key: str, text: str) -> Optional[re.Match]:
    """Return eerste re.Match of None."""
    if not text:
        return None
    for p in get_patterns(intent_key):
        m = p.search(text)
        if m:
            return m
    return None


def list_intent_keys() -> List[str]:
    """Alle bekende intent-sleutels (baseline ∪ JSON)."""
    _ensure_fresh()
    return sorted(_cache_raw.keys())


# ─────────────────────────────────────────────────────────────────────────────
# Editors (worden aangeroepen door /api/triggers/edit/intent/...)
# ─────────────────────────────────────────────────────────────────────────────

def _load_all_json() -> dict:
    if not _JSON_PATH.exists():
        return {"_meta": {"purpose": "Live-editable intent patronen naast BASELINE"}}
    return load_json(_JSON_PATH, default={}) or {}


def _save_all_json(data: dict) -> None:
    _JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    save_json(_JSON_PATH, data)
    # Force cache refresh op volgende call
    global _cache_mtime
    with _lock:
        _cache_mtime = None


def add_pattern(intent_key: str, pattern: str) -> bool:
    """Voeg regex-patroon toe aan JSON-additions. Return True bij succes."""
    pattern = (pattern or "").strip()
    if not pattern:
        return False
    # Validatie: moet compilen
    try:
        re.compile(pattern)
    except re.error:
        return False
    data = _load_all_json()
    lst = data.get(intent_key)
    if not isinstance(lst, list):
        lst = []
    if pattern in lst:
        return True  # idempotent
    # Ook niet toevoegen als het al in BASELINE staat (redundant)
    if pattern in BASELINE.get(intent_key, []):
        return True
    lst.append(pattern)
    data[intent_key] = lst
    _save_all_json(data)
    return True


def remove_pattern(intent_key: str, pattern: str) -> bool:
    """Verwijder patroon uit JSON-additions. BASELINE kan NIET worden verwijderd
    (dat is opzettelijk — de basis moet altijd blijven werken)."""
    data = _load_all_json()
    lst = data.get(intent_key)
    if not isinstance(lst, list) or pattern not in lst:
        return False
    lst.remove(pattern)
    if lst:
        data[intent_key] = lst
    else:
        data.pop(intent_key, None)
    _save_all_json(data)
    return True


def bootstrap_json_if_empty() -> None:
    """Zet de JSON-file klaar met een leeg schema als hij niet bestaat.
    Zo weet de Triggers-UI meteen welke intent-keys editable zijn."""
    if _JSON_PATH.exists():
        return
    stub = {
        "_meta": {
            "purpose": "Live-editable intent patronen. Voeg regex-strings toe om patronen aan te vullen naast BASELINE.",
            "note": "BASELINE staat in intent_pattern_store.py en is niet-verwijderbaar.",
            "known_keys": sorted(BASELINE.keys()),
        }
    }
    for k in BASELINE.keys():
        stub[k] = []
    _save_all_json(stub)


# Auto-bootstrap bij import zodat UI meteen de sleutels toont
try:
    bootstrap_json_if_empty()
except Exception:
    pass
