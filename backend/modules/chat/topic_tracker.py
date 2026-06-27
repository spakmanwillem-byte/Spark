"""v6_topic_tracker_001 — Bewaak gespreks-onderwerp over meerdere turns.

GEEN nieuwe opslag — leest bestaande turn-files uit chat/logs.
Detecteert dominant onderwerp uit recente user-berichten zodat Spark
weet "we zijn in een filosofie-modus" of "we praten over de kennisbank".

Output: 1-3 woord topic string die in compose system_prompt geïnject wordt.
"""
from __future__ import annotations

import json
from pathlib import Path
from collections import Counter
from typing import List, Optional

DATA = Path(__file__).parent.parent.parent / "data"
TURNS_DIR = DATA / "chat" / "logs"
KBV2_DIR = DATA / "knowledge" / "v2"

# Stop-woorden voor topic-extractie
STOP = {
    "ik", "je", "jij", "we", "wij", "het", "de", "een", "en", "of", "als",
    "is", "ben", "bent", "zijn", "was", "waren", "zou", "moet", "heeft",
    "ja", "nee", "ook", "niet", "naar", "maar", "met", "van", "voor", "die",
    "dat", "waar", "hoe", "wat", "wie", "wanneer", "waarom", "even",
    "kan", "wil", "wilde", "nu", "weer", "soms", "dan", "spark", "denk",
    "vind", "vond", "vraag", "vragen", "zeg", "zei", "ergens", "iets",
    "alles", "niks", "nog", "al", "ook", "echt", "wel", "geen", "even",
}


def _load_kbv2_begripen_set() -> set:
    """Verzamel alle begrippen uit KB v2 (lowercase) — voor topic-validatie."""
    out = set()
    for fname in ["knowledge_v2_doen", "knowledge_v2_weten",
                  "knowledge_v2_voelen", "knowledge_v2_spreken"]:
        fp = KBV2_DIR / f"{fname}.json"
        if not fp.exists():
            continue
        try:
            d = json.loads(fp.read_text(encoding="utf-8"))
            for k in d.get("kaarten", []):
                b = (k.get("begrip") or "").lower().strip()
                if b and len(b) >= 4:
                    out.add(b)
        except Exception:
            continue
    return out


# Lazy-cache: build only once per process
_BEGRIPPEN_CACHE: Optional[set] = None


def _get_begrippen() -> set:
    global _BEGRIPPEN_CACHE
    if _BEGRIPPEN_CACHE is None:
        _BEGRIPPEN_CACHE = _load_kbv2_begripen_set()
    return _BEGRIPPEN_CACHE


def detect_topic(session_id: str, max_turns: int = 6) -> Optional[str]:
    """Lees laatste N user-turns, vind dominant onderwerp dat overeenkomt met een KB-begrip."""
    if not session_id:
        return None
    fp = TURNS_DIR / f"{session_id}.json"
    if not fp.exists():
        return None
    try:
        d = json.loads(fp.read_text(encoding="utf-8"))
        msgs = d.get("messages", [])[-max_turns:]
    except Exception:
        return None

    if not msgs:
        return None

    begripen = _get_begrippen()
    counter: Counter = Counter()
    for m in msgs:
        if m.get("role") != "user":
            continue
        text = (m.get("text") or m.get("message") or "").lower()
        # Eerst exacte KB-begrip matches (krijgen 3x gewicht)
        for b in begripen:
            if b in text:
                counter[b] += 3
        # Plus losse woorden (1x gewicht)
        for w in text.split():
            w = w.strip(".,?!:;'\"()").lower()
            if len(w) >= 5 and w not in STOP and not w.isdigit():
                counter[w] += 1

    if not counter:
        return None
    top, score = counter.most_common(1)[0]
    if score < 2:
        return None
    return top
