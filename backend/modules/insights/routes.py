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
    "omdat", "doordat", "zodat", "tijdens", "terwijl", "totdat", "nadat", "voordat",
    "ondanks", "behalve", "volgens", "binnen", "buiten", "boven", "beneden",
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


def _collect_vocab_and_triggers_only() -> Set[str]:
    """Verzamel woorden uit vocab + triggers (NIET uit knowledge — die willen we juist mineren)."""
    known: Set[str] = set()
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
    for fname in ("conversation_triggers.json", "emotion_triggers.json",
                  "calendar_triggers.json", "admin_commands.json"):
        fp = TRIGGERS_DIR / fname
        if fp.exists():
            _walk(load_json(fp, default={}))
    return known


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


# ===== v4_vocab_growth_001 — Vocab from Knowledge =====
# Spark groeit door: kaarten die jij maakt bevatten vaak begrippen die nog niet in zijn
# vocab/triggers zitten. Dit endpoint mineert kandidaat-woorden uit alle KB-velden
# (begrip, topic, tags, ws5 wat/waarom/wanneer/wie/waar, lagen 1-4) en filtert
# vocab/triggers eruit. Resultaat: woorden die Spark zou kunnen leren.

# Velden in een kennis-entry die tekstinhoud bevatten
_KB_TEXT_FIELDS = ("begrip", "topic", "wat", "waarom", "wanneer", "wie", "waar",
                   "laag_1", "laag_2", "laag_3", "laag_4", "beschrijving", "context", "notitie")


def _walk_kb_entry_text(entry: dict) -> List[str]:
    """Verzamel alle teksttokens uit één kennis-entry."""
    tokens: List[str] = []
    for f in _KB_TEXT_FIELDS:
        v = entry.get(f)
        if isinstance(v, str):
            tokens.extend(_tokenize(v))
        elif isinstance(v, dict):
            # ws5 kan dict zijn ({wat: "...", waarom: "..."})
            for sv in v.values():
                if isinstance(sv, str):
                    tokens.extend(_tokenize(sv))
    # tags = list of strings
    for tag in entry.get("tags", []) or []:
        if isinstance(tag, str):
            tokens.extend(_tokenize(tag))
    # ws5 als sub-object
    ws5 = entry.get("ws5") or entry.get("5w") or {}
    if isinstance(ws5, dict):
        for sv in ws5.values():
            if isinstance(sv, str):
                tokens.extend(_tokenize(sv))
    # lagen als list
    lagen = entry.get("lagen") or entry.get("layers") or []
    if isinstance(lagen, list):
        for layer in lagen:
            if isinstance(layer, str):
                tokens.extend(_tokenize(layer))
            elif isinstance(layer, dict):
                for sv in layer.values():
                    if isinstance(sv, str):
                        tokens.extend(_tokenize(sv))
    return tokens


@router.get("/vocab-from-knowledge")
async def vocab_from_knowledge(
    min_count: int = Query(1, ge=1, description="Min keer voorkomen in kaarten"),
    limit: int = Query(100, ge=1, le=500, description="Max kandidaten"),
):
    """
    Scan alle knowledge cards en geef kandidaat-woorden terug die niet in
    vocab/triggers zitten. Spark kan deze leren om zijn taal te laten groeien.
    """
    kb = load_json(KB_FILE, default={})
    entries = kb.get("knowledge_entries", []) or []
    if not entries:
        return {
            "entries_scanned": 0,
            "candidates": [],
            "summary": "Geen kenniskaarten gevonden.",
        }

    known = _collect_vocab_and_triggers_only()
    counter: Counter = Counter()
    sources: Dict[str, List[str]] = {}  # word → list of card-begrippen waar gevonden

    for entry in entries:
        begrip = entry.get("begrip", "")
        toks = _walk_kb_entry_text(entry)
        seen_in_entry: Set[str] = set()
        for tok in toks:
            if len(tok) < 3 or tok.isdigit():
                continue
            if tok in STOPWORDS or tok in TIME_TOKENS:
                continue
            if tok in known:
                continue
            if tok in seen_in_entry:
                continue
            seen_in_entry.add(tok)
            counter[tok] += 1
            if tok not in sources:
                sources[tok] = []
            if begrip and begrip not in sources[tok] and len(sources[tok]) < 3:
                sources[tok].append(begrip)

    candidates = []
    for word, count in counter.most_common(limit * 2):
        if count < min_count:
            break
        candidates.append({
            "word": word,
            "count": count,
            "source_cards": sources.get(word, []),
        })
        if len(candidates) >= limit:
            break

    return {
        "entries_scanned": len(entries),
        "unique_candidates": len(counter),
        "min_count": min_count,
        "candidates": candidates,
        "summary": f"{len(candidates)} woorden uit jouw kennisbank zijn nog niet in Spark's vocab/triggers — kandidaten om hem te laten groeien.",
    }



@router.get("/tags-without-card")
async def tags_without_card(min_count: int = Query(1, ge=1), limit: int = Query(200, ge=1, le=2000)):
    """Welke tags worden gebruikt in de KB maar hebben GEEN eigen begrip-kaart?"""
    kb = load_json(KB_FILE, default={})
    entries = kb.get("knowledge_entries", []) or []
    if not entries:
        return {"entries_scanned": 0, "candidates": [], "summary": "Geen kaarten gevonden."}

    begrips: Set[str] = set()
    for e in entries:
        b = (e.get("begrip", "") or "").strip().lower()
        if b:
            begrips.add(b)

    tag_counter: Counter = Counter()
    tag_sources: Dict[str, List[str]] = {}
    for e in entries:
        tags = e.get("tags") or []
        begrip = e.get("begrip", "") or ""
        for t in tags:
            if not isinstance(t, str):
                continue
            tt = t.strip().lower()
            if not tt or len(tt) < 2:
                continue
            tag_counter[tt] += 1
            if tt not in tag_sources:
                tag_sources[tt] = []
            if begrip and begrip not in tag_sources[tt] and len(tag_sources[tt]) < 5:
                tag_sources[tt].append(begrip)

    candidates = []
    covered = 0
    for tag, count in tag_counter.most_common():
        if tag in begrips:
            covered += 1
            continue
        if count < min_count:
            continue
        candidates.append({
            "tag": tag,
            "count": count,
            "source_cards": tag_sources.get(tag, []),
        })
        if len(candidates) >= limit:
            break

    return {
        "entries_scanned": len(entries),
        "total_unique_tags": len(tag_counter),
        "tags_with_card": covered,
        "candidates": candidates,
        "summary": f"{len(candidates)} tags hebben nog geen eigen kaart (van {len(tag_counter)} unieke tags totaal, {covered} hebben al een kaart).",
    }
