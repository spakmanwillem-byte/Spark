"""
v6_kb_tag_normalizer_001 (2026-05-28) — Fundering voor #kb-tag-singular + #kb-verb-stem.

Doel: Nederlandse tags normaliseren naar canonieke vorm zodat "emoties"=="emotie"
en "bakken"=="bakt"=="bakker" tot dezelfde stam herleiden. Voedt later
#kb-similarity en #cmd-disambiguation.

Heuristieken (no ML, gewoon regels — NL morfologie is genoeg consistent):
  - Pluralia: -en, -s, -eren, -es → strip
  - Werkwoord-vervoeging: -t, -en, -de, -te, -tte, -de → strip naar stam
  - Diakritiek normaliseren via lowercase + strip
  - Lengte-guard: stam ≥ 3 chars (anders wordt "is" → "")

Niet-doel:
  - Onregelmatige werkwoorden (zijn/was/zijn) — out-of-scope, later via lookup-table
  - Engels — alleen NL
"""
from typing import List, Set
import re

# Onregelmatige plurale die strip-regels missen — kleine seed-list
_IRREGULAR_PLURAL = {
    "kinderen": "kind", "eieren": "ei", "liederen": "lied",
    "broers": "broer", "vaders": "vader", "moeders": "moeder",
    "mensen": "mens", "leden": "lid", "schepen": "schip",
    "steden": "stad", "dagen": "dag", "wegen": "weg",
}

# Nouns die eindigen op "-t" achter consonant maar GEEN verb zijn.
# Zonder deze list zou "plant" → "plan" worden (false positive).
_NOUN_T_EXCEPTIONS = {
    "plant", "kant", "punt", "front", "tent", "want", "ent",
    "kunst", "lust", "rust", "wist", "kust", "vest", "best",
    "feest", "geest", "geest", "leest", "moest", "vast",
    "markt", "kracht", "vacht", "macht", "nacht", "wacht", "lucht",
    "vlucht", "klucht", "drift", "lift", "gift", "schrift",
    "groot", "noot", "boot", "voet", "moet", "stoet",
    "post", "lijst", "kist", "vist", "twist",
    "borst", "dorst", "vorst", "korst", "barst", "haast",
}

# Korte stopwoorden die we NIET normaliseren (zou stam < 3 maken)
_KEEP_AS_IS = {"ik", "jij", "wij", "zij", "hij", "het", "een", "de", "en", "of",
               "in", "op", "om", "te", "ze", "is", "ai", "tv", "pc"}

# Suffixen in volgorde van specificiteit (langer eerst).
# Conservatief: "-es" weggelaten (raakt "emotie"-achtige woorden), "-ies" Engels.
_PLURAL_SUFFIX = ["eren", "en", "s"]
# Verb-stripping alleen voor 3e-persoon-enkelvoud "-t" achter consonant
# (werkt→werk, loopt→loop) — onveilig voor "boot/moet/voet" (vowel+t).
# Andere verb-vormen ("lopen", "werkende") laten we voor #kb-verb-stem-v2.
_VOWELS = set("aeiou")


def _strip_suffix(word: str, suffixes: List[str], min_stem: int = 3) -> str:
    """Strip eerste matchende suffix mits resulterende stam ≥ min_stem chars."""
    for suf in suffixes:
        if word.endswith(suf) and len(word) - len(suf) >= min_stem:
            return word[: -len(suf)]
    return word


def normalize_tag(tag: str) -> str:
    """Normaliseer 1 tag naar canonieke stam.

    Voorbeelden:
      "Emoties" → "emotie"   (plural -s)
      "vrienden" → "vriend"  (plural -en)
      "bakken" → "bak"       (plural -en + dubbele-consonant-fix)
      "werkt"  → "werk"      (verb -t achter consonant)
      "vriend" → "vriend"    (ongewijzigd, geen verb)
      "boot"   → "boot"      (-t achter klinker → niet gestripped)
      "kinderen" → "kind"    (irregulier)
    """
    if not tag or not isinstance(tag, str):
        return ""
    t = tag.strip().lower()
    if not t:
        return ""
    if t in _KEEP_AS_IS:
        return t
    if t in _IRREGULAR_PLURAL:
        return _IRREGULAR_PLURAL[t]
    if t in _NOUN_T_EXCEPTIONS:
        return t
    # Probeer plural-strip eerst
    stem_p = _strip_suffix(t, _PLURAL_SUFFIX)
    if stem_p != t:
        stem = stem_p
    elif len(t) >= 5 and t[-1] == "t" and t[-2] not in _VOWELS:
        # Verb 3e-persoon: werkt→werk, loopt→loop. Niet voor boot/moet/voet.
        stem = t[:-1]
    else:
        stem = t
    # Dubbele consonant-fix: "bakk" → "bak", "lopp" → "lop"
    if len(stem) >= 4 and stem[-1] == stem[-2] and stem[-1] in "bdfgklmnprstvz":
        stem = stem[:-1]
    return stem


def normalize_tags(tags: List[str]) -> List[str]:
    """Normaliseer een lijst tags, dedupe met behoud van volgorde."""
    if not tags:
        return []
    seen: Set[str] = set()
    out: List[str] = []
    for t in tags:
        n = normalize_tag(t)
        if n and n not in seen:
            seen.add(n)
            out.append(n)
    return out


def tags_similar(tag_a: str, tag_b: str) -> bool:
    """True als beide tags na normalisatie dezelfde stam hebben."""
    return normalize_tag(tag_a) == normalize_tag(tag_b) and normalize_tag(tag_a) != ""


def overlap_score(tags_a: List[str], tags_b: List[str]) -> float:
    """Jaccard-score op genormaliseerde tags (0.0 - 1.0).

    Voorbeeld:
      ["emoties","blij"] vs ["emotie","verdrietig"] → na norm: {"emotie","blij"} vs {"emotie","verdrietig"}
      → intersect=1, union=3 → 0.333
    """
    if not tags_a or not tags_b:
        return 0.0
    a = set(normalize_tags(tags_a))
    b = set(normalize_tags(tags_b))
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)
