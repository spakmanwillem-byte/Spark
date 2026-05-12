"""
Compositional Reasoning Service (v4_006)

Spark gebruikt bestaande kaarten om nieuwe samengestelde woorden te begrijpen.
Voorbeeld: 'suikerspin' onbekend → split in 'suiker' (voeding) + 'spin' (dier)
→ tegenstrijdige topics → vraag user voor duidelijkheid.

Strategie:
1. Probeer alle 2-deel splits van het woord (min 3 chars per deel)
2. Voor elk paar: zoek bestaande snaps op
3. Vergelijk tags/topic per kant
4. Conflict (verschillende topics) → vraag user wat het is
5. Geen conflict → erfde tags als suggestie, maak snap met decomposed_from metadata
"""
from typing import Optional


# Algemene admin-tags die we niet meetellen voor topic-inheritance
ADMIN_TAGS = {
    "knowledge-snap", "auto-generated", "scan-discovered",
    "user-verrijkt", "context-zin", "homonym_variant",
}


def try_decompose(word: str, lookup_fn) -> list:
    """
    Probeer woord te splitsen in 2 bekende delen.
    lookup_fn(word) -> entry dict of None.
    Returns lijst van candidates, gesorteerd op meest waarschijnlijke split.
    """
    word = (word or "").lower().strip()
    if len(word) < 6:  # te kort om zinvol te splitsen
        return []
    candidates = []
    for i in range(3, len(word) - 2):  # min 3 chars per deel
        left, right = word[:i], word[i:]
        left_entry = lookup_fn(left)
        right_entry = lookup_fn(right)
        if not (left_entry and right_entry):
            continue
        candidates.append({
            "left": left,
            "right": right,
            "left_entry": left_entry,
            "right_entry": right_entry,
        })
    # Sort: voorkeur voor evenwichtige splits met langere delen
    candidates.sort(
        key=lambda c: (
            -min(len(c["left"]), len(c["right"])),
            -(len(c["left"]) + len(c["right"]))
        )
    )
    return candidates


def analyze_decomposition(candidate: dict) -> dict:
    """Vergelijk topics/tags van beide delen, detecteer conflict."""
    left_e = candidate["left_entry"]
    right_e = candidate["right_entry"]
    left_topic = (left_e.get("topic") or "").strip().lower()
    right_topic = (right_e.get("topic") or "").strip().lower()
    left_tags = set(t.lower() for t in (left_e.get("tags") or []) if t) - ADMIN_TAGS
    right_tags = set(t.lower() for t in (right_e.get("tags") or []) if t) - ADMIN_TAGS

    topic_conflict = bool(left_topic and right_topic and left_topic != right_topic)
    common_tags = left_tags & right_tags
    has_overlap = bool(common_tags)

    return {
        "left_topic": left_topic,
        "right_topic": right_topic,
        "left_tags": sorted(left_tags),
        "right_tags": sorted(right_tags),
        "common_tags": sorted(common_tags),
        "topic_conflict": topic_conflict,
        "has_overlap": has_overlap,
        # Suggestie: erfbare tags = common_tags, of fallback alleen left als geen overlap
        "suggested_tags": sorted(common_tags) if common_tags else sorted(left_tags | right_tags)[:4],
    }


def build_decomposition_message(word: str, candidate: dict, analysis: dict) -> str:
    """Vriendelijke uitleg + vraag voor user."""
    left = candidate["left"]
    right = candidate["right"]
    lt = analysis["left_topic"]
    rt = analysis["right_topic"]
    lt_str = f" ({lt})" if lt else ""
    rt_str = f" ({rt})" if rt else ""

    if analysis["topic_conflict"]:
        return (
            f"Ik ken '{word}' niet, maar ik herken er '{left}'{lt_str} en '{right}'{rt_str} in. "
            f"Dat klinkt tegenstrijdig — wat is een '{word}' eigenlijk?"
        )
    if analysis["has_overlap"]:
        common = ", ".join(analysis["common_tags"][:3])
        return (
            f"Ik ken '{word}' niet, maar het lijkt te maken te hebben met '{left}' en '{right}' "
            f"(beide rond: {common}). Klopt dat?"
        )
    # Geen overlap, geen conflict (één topic onbekend)
    known_part = left if lt else right
    known_topic = lt or rt
    if known_topic:
        return (
            f"Ik ken '{word}' niet, maar herken '{known_part}' ({known_topic}). "
            f"Heeft '{word}' daarmee te maken?"
        )
    return f"Ik ken '{word}' niet, maar herken '{left}' en '{right}' los. Wat is een '{word}'?"


def find_best_decomposition(word: str, lookup_fn) -> Optional[dict]:
    """Hoofdfunctie: vind de beste split met analyse. None als niks bruikbaar."""
    candidates = try_decompose(word, lookup_fn)
    if not candidates:
        return None
    best = candidates[0]
    analysis = analyze_decomposition(best)
    return {
        "candidate": best,
        "analysis": analysis,
        "message": build_decomposition_message(word, best, analysis),
    }
