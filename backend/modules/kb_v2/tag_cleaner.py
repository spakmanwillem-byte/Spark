"""v12_tag_cleaner_001 — Junk-filter + lemma-dedupe + cap voor kaart-tags.

Doel: GPT genereert vaak 100+ tags per kaart met veel bloat (tijden, cijfers,
enkelvoud+meervoud dubbel, werkwoord-vervoegingen). Dit script normaliseert
naar max 15 signaal-tags per kaart.

Regels:
1. JUNK filter — verwijder pure cijfers, tijden ("08:00"), datums, single-letters,
   tags >40 chars of <2 chars, en tags die alleen leestekens bevatten.
2. LEMMA dedupe — Nederlands lichtgewicht stemming: 'audit'/'audits'/'auditen'
   worden 1 tag (kortste variant blijft). Volgt de Infinitief-Regel: als een
   verb-variant erbij zit, wint de kortste stem.
3. CAP — max 15 tags per kaart. Bij overflow: behoud korte, unieke, canonieke
   tags (kortste variant per stem, alfabetische tiebreak).
"""
from __future__ import annotations

import re
from typing import List, Tuple, Dict

MAX_TAGS_PER_CARD = 15
MIN_TAG_LEN = 2
MAX_TAG_LEN = 40

# Suffixen in volgorde van 'lange match eerst', zodat 'controleren' eerst 'eren'
# eraf gooit (→ 'control') i.p.v. alleen 'en' (→ 'controler').
_DUTCH_SUFFIXES = [
    "eerden", "eerde", "eerdt", "erden", "erend", "erende",
    "eren", "eert", "ende",
    "nde", "ing",
    "en", "es", "er", "et",
    "e", "t", "s",
]

# Junk-detectie patronen
_TIME_RE = re.compile(r"^\d{1,2}[:.]\d{2}(?::\d{2})?$")           # 08:00 / 8.30
_DATE_RE = re.compile(r"^\d{1,4}[-/.]\d{1,2}([-/.]\d{1,4})?$")     # 2026-08-04
_PURE_NUM_RE = re.compile(r"^-?\d+([.,]\d+)?$")                   # 42 / 3.14
_ONLY_PUNCT_RE = re.compile(r"^[\s\W_]+$")                         # !!! / ---


def _stem(word: str) -> str:
    """Lichtgewicht Nederlandse stemmer. Verwijdert iteratief achtervoegsels tot
    er niks meer af kan. Zo mergen 'audit' → 'audi' en 'audits' → 'audit' → 'audi'
    naar dezelfde stem. Minimum resulterende lengte: 3 chars."""
    w = (word or "").lower().strip()
    if len(w) < 4:
        return w
    changed = True
    while changed and len(w) >= 4:
        changed = False
        for suf in _DUTCH_SUFFIXES:
            if len(w) - len(suf) < 3:
                continue
            if w.endswith(suf):
                stem = w[: -len(suf)]
                # Undo verdubbeling: 'stoppen' → 'stopp' → 'stop'
                if len(stem) >= 3 and stem[-1] == stem[-2] and stem[-1] in "bdfglmnprst":
                    stem = stem[:-1]
                w = stem
                changed = True
                break
    return w


def is_junk(tag: str) -> Tuple[bool, str]:
    """Return (is_junk, reason). reason='' als geen junk."""
    if tag is None:
        return True, "none"
    t = str(tag).strip()
    if len(t) < MIN_TAG_LEN:
        return True, "too_short"
    if len(t) > MAX_TAG_LEN:
        return True, "too_long"
    if _ONLY_PUNCT_RE.match(t):
        return True, "only_punct"
    if _TIME_RE.match(t):
        return True, "time_literal"
    if _DATE_RE.match(t):
        return True, "date_literal"
    if _PURE_NUM_RE.match(t):
        return True, "pure_number"
    return False, ""


def clean_tags(tags: List[str], max_tags: int = MAX_TAGS_PER_CARD) -> Tuple[List[str], Dict]:
    """Reinig een tag-lijst. Retourneert (schone_tags, rapport).

    rapport: {
      'before': n, 'after': n,
      'removed_junk': [(tag, reden), ...],
      'merged_lemmas': [(canoniek, [varianten]), ...],
      'trimmed_by_cap': [weggegooide_tags]
    }
    """
    report = {
        "before": len(tags or []),
        "after": 0,
        "removed_junk": [],
        "merged_lemmas": [],
        "trimmed_by_cap": [],
    }

    # 1. JUNK-filter + lowercase + dedupe op exact string
    seen_exact = set()
    kept = []
    for raw in tags or []:
        t = str(raw).strip()
        low = t.lower()
        if low in seen_exact:
            continue
        seen_exact.add(low)
        junk, reason = is_junk(low)
        if junk:
            report["removed_junk"].append((t, reason))
            continue
        kept.append(low)

    # 2. LEMMA-dedupe: groepeer op stem, behoud kortste variant als canoniek
    by_stem: Dict[str, List[str]] = {}
    for t in kept:
        s = _stem(t)
        by_stem.setdefault(s, []).append(t)

    canonical = []
    for stem, variants in by_stem.items():
        # Kortste variant wint (dichtst bij de basis-vorm)
        variants_sorted = sorted(set(variants), key=lambda x: (len(x), x))
        canoniek = variants_sorted[0]
        canonical.append(canoniek)
        if len(variants_sorted) > 1:
            report["merged_lemmas"].append((canoniek, [v for v in variants_sorted if v != canoniek]))

    # 3. CAP: max_tags. Sorteer op (lengte oplopend, alfabetisch) — atomair wint.
    canonical.sort(key=lambda x: (len(x), x))
    if len(canonical) > max_tags:
        report["trimmed_by_cap"] = canonical[max_tags:]
        canonical = canonical[:max_tags]

    # Definitieve output alfabetisch voor stabiele opslag
    canonical.sort()
    report["after"] = len(canonical)
    return canonical, report


def clean_tags_simple(tags: List[str], max_tags: int = MAX_TAGS_PER_CARD) -> List[str]:
    """Convenience-wrapper: alleen schone tags zonder rapport."""
    out, _ = clean_tags(tags, max_tags=max_tags)
    return out
