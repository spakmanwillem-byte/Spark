"""
LLM Output Scanner (v9_llm_self_learn_001)
==========================================
Scant Spark's eigen LLM-antwoorden op concepten die (a) NIET in KB v2 staan
en (b) NIET in user's vraag stonden. Voedt lite_card_factory met kandidaten.

Filosofie (Willem-regel): Spark leert van zichzelf, niet alleen van users.
Metadata (source, herkomst_turn_id, llm_confidence) via footnote-systeem.

Klein en pure — geen side-effects, alleen scan+return.
"""
from __future__ import annotations
import re
from collections import Counter
from pathlib import Path
from typing import Dict, List, Any

from modules.core.storage import load_json

_KB_INDEX = Path(__file__).parent.parent.parent / "data" / "knowledge" / "v2" / "knowledge_index.json"

# Herbruik stopwoorden uit kb_v2 analyzer (single source of truth)
try:
    from modules.kb_v2.chat_analyzer import _STOPWORDS as _KB_STOPWORDS  # type: ignore
except Exception:
    _KB_STOPWORDS = set()

# Extra stopwoorden specifiek voor Spark's antwoord-taal (frequent zonder KB-waarde)
_SPARK_STOPWORDS = set("""
willem spark bot user users hij zij het dat dit deze die daarbij overigens
uitleg overigens misschien overigens verder inderdaad prima dank
""".split())

_STOPWORDS = _KB_STOPWORDS | _SPARK_STOPWORDS
_WORD_RE = re.compile(r"\b([a-zA-ZÀ-ÿ][a-zA-ZÀ-ÿ0-9\-]{2,29})\b")


def _load_known_kb_begrippen() -> set:
    d = load_json(_KB_INDEX, default={"entries": {}}) or {}
    entries = d.get("entries", {}) if isinstance(d, dict) else {}
    return {k.lower() for k in entries.keys()}


def scan_spark_response(spark_response: str, user_text: str = "",
                        min_len: int = 4, top_n: int = 8) -> List[Dict[str, Any]]:
    """Return kandidaat-concepten uit spark_response die niet in KB en niet in user_text zitten.

    Args:
        spark_response: Spark's LLM antwoord tekst.
        user_text: Willems vraag — filter deze woorden weg zodat we enkel Spark-nieuws krijgen.
        min_len: min woordlengte om te tellen (default 4, filtert "een/dat/etc").
        top_n: max kandidaten (default 8, houdt inbox schoon).

    Returns:
        [{"begrip": str, "count_in_spark": int, "context_snippet": str}]
        Gesorteerd op count desc.
    """
    if not spark_response or len(spark_response) < 30:
        return []
    known = _load_known_kb_begrippen()
    user_words = {w.lower() for w in _WORD_RE.findall(user_text or "")}

    counter: Counter = Counter()
    snippets: Dict[str, str] = {}
    for m in _WORD_RE.finditer(spark_response):
        tok = m.group(1).lower()
        if len(tok) < min_len:
            continue
        if tok in _STOPWORDS or tok.isdigit():
            continue
        if tok in known:
            continue
        if tok in user_words:  # niet Spark-nieuws maar gewoon echo van user
            continue
        counter[tok] += 1
        if tok not in snippets:
            start = max(0, m.start() - 40)
            end = min(len(spark_response), m.end() + 60)
            snippets[tok] = spark_response[start:end].replace("\n", " ").strip()

    return [
        {"begrip": tok, "count_in_spark": cnt, "context_snippet": snippets.get(tok, "")}
        for tok, cnt in counter.most_common(top_n)
        if cnt >= 1
    ]
