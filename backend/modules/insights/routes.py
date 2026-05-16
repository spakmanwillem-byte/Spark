"""
Insights Module (v4_016) — Analyser voor Shadow Observer data.

Read-only API die patronen in chat-gedrag analyseert en suggesties teruggeeft.
Geen wijzigingen op vocab/triggers/bijbel — alleen inzicht.

Eerste laag (deze sessie):
  GET /api/spark/insights/unused-vocab
    → Woorden die user/chat vaak gebruikt maar die NIET in vocab/triggers/knowledge zitten.
       Suggestie: kandidaat-vocab toevoegen.

Toekomstige lagen (later):
  GET /api/spark/insights/trigger-overlap   → Triggers die op dezelfde zinnen reageerden
  GET /api/spark/insights/bijbel-unused     → Bijbel categorieën nooit gebruikt
"""
import json
import re
from collections import Counter
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Set, List, Dict

from fastapi import APIRouter, Query

from modules.core.storage import load_json

router = APIRouter(prefix="/spark/insights", tags=["insights"])

DATA_ROOT = Path(__file__).parent.parent.parent / "data"
SHADOW_EVENTS_DIR = DATA_ROOT / "shadow" / "events"
VOCAB_FILE = DATA_ROOT / "personality" / "spark_vocab.json"
KB_FILE = DATA_ROOT / "knowledge" / "learned_knowledge" / "knowledge_base.json"
TRIGGERS_DIR = DATA_ROOT / "triggers"

# Stopwoorden — frequent maar niet zinvol als vocab-kandidaat
STOPWORDS = {
    # lidwoorden / voornaamwoorden
    "de", "het", "een", "ik", "je", "jij", "u", "we", "wij", "ze", "zij", "hij", "men",
    "mij", "jou", "ons", "hen", "hun", "hem", "haar", "z'n", "m'n", "mn", "zn",
    # werkwoorden algemeen
    "ben", "bent", "is", "zijn", "was", "waren", "had", "heb", "heeft", "hebben",
    "ga", "gaat", "ging", "gaan", "kan", "kun", "kunt", "kunnen", "moet", "moeten",
    "wil", "wilt", "willen", "doe", "doet", "doen", "zal", "zou", "zullen",
    "word", "wordt", "worden", "kom", "komt", "komen", "zie", "ziet", "zien",
    "weet", "weten", "denk", "denkt", "denken", "vind", "vindt", "vinden",
    # voorzetsels / voegwoorden
    "en", "of", "maar", "want", "dus", "als", "dan", "toch", "ook", "nog", "wel", "niet",
    "in", "op", "aan", "uit", "om", "tot", "te", "voor", "na", "bij", "van", "met", "naar",
    "over", "onder", "door", "tussen", "tegen", "zonder", "tegenover", "rond", "vanuit",
    # vraagwoorden / bijwoorden
    "wat", "wie", "waar", "wanneer", "hoe", "waarom", "welke", "welk",
    "hier", "daar", "ergens", "nergens", "overal", "nu", "toen", "straks", "eerst",
    "altijd", "nooit", "soms", "vaak", "meestal", "even", "iets", "niets", "alles",
    "veel", "weinig", "meer", "minder", "heel", "zeer", "erg", "best", "vrij", "tamelijk",
    # bezittelijke / aanwijzende
    "deze", "die", "dit", "dat", "zo", "zoals", "dezelfde", "andere", "anders",
    # mini / tussenwerpsels
    "ja", "nee", "oh", "ah", "hm", "hmm", "oké", "okay", "ok", "ja's", "nee's",
    "even", "echt", "gewoon", "misschien", "vast",
    # tijdsindicatoren
    "vandaag", "gisteren", "morgen", "vanmorgen", "vanmiddag", "vanavond",
    # leestekens helpers
    "ff", "ofzo", "ofzoiets", "iets",
}

# Tijd-indicatoren die we expliciet uitsluiten (al gedekt door agenda intents)
TIME_TOKENS = {"uur", "minuut", "minuten", "seconde", "seconden", "dag", "dagen", "week",
               "weken", "maand", "maanden", "jaar", "jaren"}

# NOTE voor toekomst: woorden zoals "appeflap" zijn user-placeholders (workaround
# voor snap-bug — user typt placeholder, edit dan naar echt onderwerp). NIET uitsluiten,
# user wil ze gewoon zien. Als snap-bug ooit gefixt is, dan kan dit verdwijnen.

WORD_RE = re.compile(r"[a-zA-ZàâäéèêëîïôöùûüçÀÂÄÉÈÊËÎÏÔÖÙÛÜÇ']+")


def _tokenize(text: str) -> List[str]:
    if not text:
        return []
    return [m.group(0).lower().strip("'") for m in WORD_RE.finditer(text)]


def _collect_vocab_words() -> Set[str]:
    """Verzamel alle woorden die al in vocab/triggers/knowledge zitten."""
    known: Set[str] = set()

    # 1) Spark vocab
    vocab = load_json(VOCAB_FILE, default={})
    def _walk(obj):
        if isinstance(obj, list):
            for x in obj:
                _walk(x)
        elif isinstance(obj, dict):
            for v in obj.values():
                _walk(v)
        elif isinstance(obj, str):
            for tok in _tokenize(obj):
                known.add(tok)
    _walk(vocab.get("emoties", {}))
    _walk(vocab.get("algemeen", {}))

    # 2) Knowledge base: begrip + tags + topic
    kb = load_json(KB_FILE, default={})
    for entry in kb.get("knowledge_entries", []):
        for tok in _tokenize(entry.get("begrip", "")):
            known.add(tok)
        for tag in entry.get("tags", []) or []:
            for tok in _tokenize(tag):
                known.add(tok)
        topic = entry.get("topic", "")
        for tok in _tokenize(topic):
            known.add(tok)

    # 3) Trigger patterns (woorden uit triggers)
    for fname in ("conversation_triggers.json", "emotion_triggers.json",
                  "calendar_triggers.json", "admin_commands.json"):
        fp = TRIGGERS_DIR / fname
        if fp.exists():
            data = load_json(fp, default={})
            _walk(data)

    return known


def _read_shadow_events(days: int) -> List[dict]:
    """Lees shadow events van de laatste N dagen."""
    if not SHADOW_EVENTS_DIR.exists():
        return []
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    events: List[dict] = []
    for f in sorted(SHADOW_EVENTS_DIR.glob("*.jsonl")):
        # Filename = YYYY-MM-DD.jsonl
        try:
            file_date = datetime.strptime(f.stem, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        if file_date < cutoff - timedelta(days=1):
            continue
        try:
            with f.open() as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        except OSError:
            continue
    return events


@router.get("/unused-vocab")
async def unused_vocab(
    days: int = Query(14, ge=1, le=90, description="Hoeveel dagen terug analyseren"),
    min_count: int = Query(2, ge=1, description="Minimaal aantal keer voorgekomen"),
    limit: int = Query(50, ge=1, le=500, description="Max aantal woorden terug"),
):
    """
    Lees shadow events van laatste N dagen, tokeniseer user_msg,
    geef woorden terug die ≥ min_count voorkwamen maar NIET in vocab/triggers/knowledge zitten.

    Kandidaten voor toevoeging aan vocab.
    """
    events = _read_shadow_events(days)
    if not events:
        return {
            "days": days,
            "min_count": min_count,
            "events_analyzed": 0,
            "candidates": [],
            "summary": "Geen shadow events gevonden in deze periode.",
        }

    known = _collect_vocab_words()
    counter: Counter = Counter()
    sample_msgs: Dict[str, str] = {}  # eerste zin waar dit woord voorkwam

    for ev in events:
        msg = ev.get("user_msg") or ""
        if not msg or msg.startswith("[system:"):
            continue
        for tok in _tokenize(msg):
            if len(tok) < 3:
                continue
            if tok in STOPWORDS or tok in TIME_TOKENS:
                continue
            if tok in known:
                continue
            if tok.isdigit():
                continue
            counter[tok] += 1
            if tok not in sample_msgs:
                sample_msgs[tok] = msg[:120]

    candidates = []
    for word, count in counter.most_common(limit * 3):  # ruim ophalen, dan filter
        if count < min_count:
            break
        candidates.append({
            "word": word,
            "count": count,
            "sample": sample_msgs.get(word, ""),
        })
        if len(candidates) >= limit:
            break

    return {
        "days": days,
        "min_count": min_count,
        "events_analyzed": len(events),
        "unique_unknown_words": len(counter),
        "candidates": candidates,
        "summary": f"{len(candidates)} kandidaat-woorden gevonden ({len(counter)} unieke onbekende woorden in {len(events)} events).",
    }
