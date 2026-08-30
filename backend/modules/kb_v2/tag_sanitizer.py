"""v13c_tag_sanitizer_001 — Centrale tag-sanitizer.

Voorkomt LLM-lek in tags/lagen. Elke plek waar LLM-output → tags gaat
MOET door `sanitize_tag()` of `sanitize_tag_list()`.

Regels:
  1. Alleen strings, geen dict/list/None
  2. Split op newline — pak alleen eerste regel (LLM-lek fix)
  3. Strip emoji's (metadata is text, geen icoontjes)
  4. Trim whitespace + collapse dubbele spaties
  5. Length-cap: 60 chars max (echte tags zijn korter, langer = corrupt)
  6. Dedupe (case-insensitive) bij list-versie
  7. Empty strings weggegooid
"""
from __future__ import annotations

import re
from typing import List

_EMOJI_RE = re.compile(
    r"["
    r"\U0001F300-\U0001F5FF"
    r"\U0001F600-\U0001F64F"
    r"\U0001F680-\U0001F6FF"
    r"\U0001F700-\U0001F77F"
    r"\U0001F780-\U0001F7FF"
    r"\U0001F800-\U0001F8FF"
    r"\U0001F900-\U0001F9FF"
    r"\U0001FA00-\U0001FA6F"
    r"\U0001FA70-\U0001FAFF"
    r"\U00002600-\U000026FF"
    r"\U00002700-\U000027BF"
    r"\U0001F1E6-\U0001F1FF"
    r"]+", flags=re.UNICODE
)

MAX_TAG_LEN = 60

# v13c_tag_sanitizer_apostrof — unicode-apostrofen / smart-quotes normaliseren
# naar rechte ASCII-apostrof zodat "foto’s" en "foto's" nooit meer als 2 tags
# door de KB kunnen komen. Zie ROADMAP Principe #8 + ghost-preventie.
_APO_MAP = str.maketrans({
    "\u2019": "'",  # ’ RIGHT SINGLE QUOTATION MARK
    "\u2018": "'",  # ‘ LEFT SINGLE QUOTATION MARK
    "\u02BC": "'",  # ʼ MODIFIER LETTER APOSTROPHE
    "\u00B4": "'",  # ´ ACUTE ACCENT (soms gebruikt als apostrof)
    "\u0060": "'",  # ` GRAVE ACCENT
    "\u201B": "'",  # ‛ SINGLE HIGH-REVERSED-9 QUOTATION MARK
})


def _normalize_apostrophes(s: str) -> str:
    """Vervang alle unicode-apostrof-varianten door de rechte ASCII-apostrof."""
    return s.translate(_APO_MAP) if s else s


def sanitize_tag(t) -> str:
    """Return schone tag-string, of leeg als input onbruikbaar was.

    Idempotent — herhaald aanroepen wijzigt niks meer.
    """
    if not isinstance(t, str):
        return ""
    # Pak alleen eerste regel — LLM-multi-line-lek stopt hier
    first = t.split("\n")[0]
    # Emoji weg
    stripped = _EMOJI_RE.sub("", first).strip()
    # Dubbele whitespace normaliseren
    stripped = re.sub(r"\s+", " ", stripped)
    # Unicode-apostrofen → rechte apostrof (voorkomt "foto’s"-ghosts)
    stripped = _normalize_apostrophes(stripped)
    # Length-cap
    if len(stripped) > MAX_TAG_LEN:
        stripped = stripped[:MAX_TAG_LEN].strip()
    return stripped


def sanitize_tag_list(tags) -> List[str]:
    """Sanitize + dedupe (case-insensitive) een lijst tags.
    Non-list input → lege lijst."""
    if not isinstance(tags, (list, tuple)):
        return []
    out: List[str] = []
    seen = set()
    for t in tags:
        cleaned = sanitize_tag(t)
        if not cleaned:
            continue
        key = cleaned.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(cleaned)
    return out


def merge_tags(existing, incoming) -> List[str]:
    """Merge nieuwe (LLM-)tags in bestaande. Beide worden gesanitized.
    Behoudt volgorde van existing, appendt nieuwe niet-duplicaat items.
    """
    existing_clean = sanitize_tag_list(existing)
    incoming_clean = sanitize_tag_list(incoming)
    seen = {t.lower() for t in existing_clean}
    out = list(existing_clean)
    for t in incoming_clean:
        if t.lower() not in seen:
            out.append(t)
            seen.add(t.lower())
    return out
