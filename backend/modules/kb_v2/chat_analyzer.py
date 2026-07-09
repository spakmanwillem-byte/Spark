"""
Chat → KB-suggesties analyzer (v8_kb_chat_suggest_001)

Analyseert recente chat-turns van een user en suggereert nieuwe KB v2-kaarten
voor begrippen die vaak voorkomen maar nog niet in de kennisbank zitten.

Aanpak:
  1. Load laatste N gesprekturns (default 500) uit chat/logs/user-XXX.json
  2. Tokenize alle user_message strings (niet Spark's antwoord — we willen wat USER zegt)
  3. Filter stopwoorden NL + al bekende KB-begrippen (via knowledge_index.json)
  4. Extract candidates: nouns/entities die ≥ threshold keer voorkomen
  5. Return top-20 met mention_count, example_snippets, confidence

Geen LLM-call in deze versie (privacy + snelheid). LLM-enrichment is een P2-optie.
"""
from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import Dict, List, Any

from modules.core.storage import load_json

DATA_ROOT = Path(__file__).parent.parent.parent / "data"
CHAT_LOGS_DIR = DATA_ROOT / "chat" / "logs"
KB_INDEX = DATA_ROOT / "knowledge" / "v2" / "knowledge_index.json"

# NL stopwoorden (uitgebreid)
_STOPWORDS = set("""
de het een en of maar want dus toch ook al niet nog wel niks niets iemand iedereen
je jij jou jouw jullie hem haar hij zij zij we wij ons ze u
ik mijn me mij mezelf zelf
is zijn was waren wordt worden werd
heb hebt heeft hadden gehad hebben
kan kan mag moet moeten mogen kon zou zouden wil wilt wilde wilden
doe doet deed doen gedaan
ga gaat ging gaan
zeg zegt zei zeggen gezegd
wat waar wanneer waarom hoe wie welke welk
ja nee misschien
als dan zoals want omdat terwijl doordat mits tenzij
even nu straks vandaag gisteren morgen later eerder
heel erg zo veel weinig meer minder
zoals bij op in aan uit door om voor na met zonder tegen tussen boven onder achter naast tot van vanaf sinds tijdens rond
die dat deze dit daar hier zo daarna daarvoor daarom hierdoor daaruit erop erin eraan
ben bent
lekker mooi goed slecht groot klein
ok oke prima top
hey hoi hallo dag doei
uh eh mm hm hmm
etc bv bijv zeg maar oa cq
zoiets iemand iets ergens overal nergens elk elke
mn m'n je jouw hun onze
naar ff even ff hè hé hoor
klopt geldt zit gebeurt lukt werkt loopt gaat komt maakt raakt houdt duurt blijft haalt
over overal ergens waarheen waarvoor daarnaast bovendien daarbij
kunnen zullen zullen kunnen willen willen wil wilt wilde
denk denkt dacht denken gedacht vind vindt vond vinden gevonden weet weten wist geweten
ken kent kende kennen gekend hoor hoort hoorde horen gehoord
zie ziet zag zien gezien
maak maakt maakte maken gemaakt
alles alle allemaal beetje wat paar
mee erbij daarbij daarnaast
""".split())

# Interpunctie/getallen regex — behoud alleen woorden met ≥2 letters, geen puur getallen
_WORD_RE = re.compile(r"\b([a-zA-ZÀ-ÿ][a-zA-ZÀ-ÿ0-9\-]{1,29})\b")


def _load_recent_user_messages(user_id: str, max_turns: int = 500) -> List[Dict[str, Any]]:
    """Lees laatste N turns uit chat/logs/user-XXX.json. Return [{text, timestamp}]."""
    path = CHAT_LOGS_DIR / f"{user_id}.json"
    d = load_json(path)
    if not d:
        return []
    convs = d.get("conversations", []) if isinstance(d, dict) else []
    # Alleen user messages
    msgs = []
    for c in convs[-max_turns:]:
        if not isinstance(c, dict):
            continue
        um = c.get("user_message") or ""
        ts = c.get("timestamp") or ""
        if um and isinstance(um, str):
            msgs.append({"text": um, "timestamp": ts})
    return msgs


def _load_known_kb_begrippen() -> set:
    """Alle bekende KB v2-begrippen uit index.json (lowercase)."""
    d = load_json(KB_INDEX, default={"entries": {}}) or {}
    entries = d.get("entries", {}) if isinstance(d, dict) else {}
    return {k.lower() for k in entries.keys()}


def _tokenize(text: str) -> List[str]:
    return [m.group(1).lower() for m in _WORD_RE.finditer(text)]


def analyze_chat_for_kb_suggestions(
    user_id: str,
    max_turns: int = 500,
    min_mentions: int = 3,
    top_n: int = 20,
) -> Dict[str, Any]:
    """Hoofd-entry. Return dict met suggesties en samenvatting."""
    msgs = _load_recent_user_messages(user_id, max_turns=max_turns)
    if not msgs:
        return {
            "success": True,
            "user_id": user_id,
            "turns_analyzed": 0,
            "suggestions": [],
            "note": "Geen chat-turns gevonden voor deze user.",
        }

    known = _load_known_kb_begrippen()
    counter = Counter()
    examples = {}  # begrip → list van snippets

    for m in msgs:
        tokens = _tokenize(m["text"])
        # Skip als message ook meta-commando is
        if len(tokens) < 3:
            continue
        for tok in tokens:
            if tok in _STOPWORDS:
                continue
            if tok in known:
                continue
            if tok.isdigit() or len(tok) < 3:
                continue
            counter[tok] += 1
            if tok not in examples:
                # bewaar 1 voorbeeld-snippet (max 120 chars)
                snip = m["text"][:120].replace("\n", " ")
                examples[tok] = snip

    # Filter op min_mentions
    candidates = [(t, c) for t, c in counter.items() if c >= min_mentions]
    candidates.sort(key=lambda x: -x[1])
    candidates = candidates[:top_n]

    suggestions = []
    for begrip, count in candidates:
        # Confidence: 0-100 op basis van count (log-schaal-ish)
        if count >= 20:
            confidence = 90
        elif count >= 10:
            confidence = 70
        elif count >= 5:
            confidence = 55
        else:
            confidence = 40
        suggestions.append({
            "begrip": begrip,
            "mention_count": count,
            "example_snippet": examples.get(begrip, ""),
            "confidence": confidence,
            "recommendation": (
                "Duidelijk terugkerend concept — direct als kaart aannemen"
                if confidence >= 70
                else "Twijfelgeval — check context voor je hem accepteert"
            ),
        })

    return {
        "success": True,
        "user_id": user_id,
        "turns_analyzed": len(msgs),
        "unique_words_seen": len(counter),
        "known_kb_size": len(known),
        "min_mentions_threshold": min_mentions,
        "suggestions": suggestions,
        "note": "Word-frequency op user_message tekst (niet Spark's antwoord). Stopwoorden + bekende KB-begrippen zijn gefilterd.",
    }
