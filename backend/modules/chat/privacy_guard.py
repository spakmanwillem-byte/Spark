"""v13_privacy_guard_001 — Attente Spark v13 privacy-matrix.

Zorgt dat gevoelige data van hoge-gradatie users NIET in LLM-context landt
voor lage-gradatie requesters.

Regels per gradatie via /app/backend/data/system/privacy_defaults.json:
  gradatie 1-2: alles zichtbaar
  gradatie 3-4: blokkeer financieel/gezondheid/familie
  gradatie 5+:  blokkeer ook privé/persoonlijk + persoonsnamen

Toepassing (in response_composer):
  1. filter_kb_cards(cards, gradatie) → weer kaarten met verboden tags
  2. filter_identity_facts(facts, gradatie) → strip about_user/about_relationship voor 5+
  3. strip_person_names(text, gradatie) → maskeer namen in eind-prompt
  4. should_include_relations(gradatie) → False voor 5+

@traced-decorator niet gebruikt want zuiver-synchrone helpers.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional, Any

from modules.core.storage import load_json

_DATA = Path(__file__).parent.parent.parent / "data"
_DEFAULTS_FP = _DATA / "system" / "privacy_defaults.json"

# Cache (blueprint-style, in-memory)
_CACHE: Dict[str, Any] = {"defaults": None, "extra_names": None}


def _defaults() -> Dict:
    if _CACHE["defaults"] is None:
        _CACHE["defaults"] = load_json(_DEFAULTS_FP, default={
            "regels_per_gradatie": {},
            "blokkeer_ook_person_names": [],
        }) or {}
    return _CACHE["defaults"]


def _extra_names_from_admin_relations() -> List[str]:
    """Namen uit admin's relationships (user-001) — auto-strip voor grad >= 5."""
    if _CACHE["extra_names"] is not None:
        return _CACHE["extra_names"]
    names: List[str] = []
    try:
        rel_fp = _DATA / "persons" / "user-001_relationships.json"
        d = load_json(rel_fp, default={"relationships": []}) or {}
        for r in (d.get("relationships") or []):
            rt = (r.get("relation_type") or "").lower()
            # alleen familie/privé, geen bots/vrienden-collega's
            if "familie" in rt or any(w in rt for w in (
                "moeder", "vader", "zus", "broer", "dochter", "zoon",
                "oma", "opa", "tante", "oom", "neef", "nicht", "partner", "vrouw", "man"
            )):
                pn = (r.get("person_name") or "").strip()
                if pn and len(pn) >= 2:
                    names.append(pn)
    except Exception:
        pass
    _CACHE["extra_names"] = names
    return names


def _rules_for(gradatie: Optional[int]) -> Dict:
    """Return {'blokkeer_tags': [...], 'beschrijving': ...} voor deze gradatie."""
    defs = _defaults()
    grad = int(gradatie) if gradatie else 7  # veiligst: onbekend = strengst
    key = str(max(1, min(7, grad)))
    return (defs.get("regels_per_gradatie") or {}).get(key, {
        "blokkeer_tags": ["financieel", "gezondheid", "familie", "privé", "persoonlijk", "relaties"],
    })


def should_include_relations(gradatie: Optional[int]) -> bool:
    """False voor gradatie 5+ (kennis/onbekend/vreemde)."""
    grad = int(gradatie) if gradatie else 7
    return grad <= 4


def should_strip_person_names(gradatie: Optional[int]) -> bool:
    """True voor gradatie 5+ (namen worden gemaskeerd tot 'iemand')."""
    grad = int(gradatie) if gradatie else 7
    return grad >= 5


def filter_kb_cards(cards: List[Dict], gradatie: Optional[int]) -> List[Dict]:
    """Verwijder KB-kaarten met tags die deze gradatie NIET mag zien.

    Match op tags[], lade, ws5.wie/waar (soft-scan op familie-namen).
    Behoudt kaarten die 0 blocked_tags hebben.
    """
    rules = _rules_for(gradatie)
    blocked = set((t or "").lower() for t in (rules.get("blokkeer_tags") or []))
    if not blocked:
        return cards

    grad = int(gradatie) if gradatie else 7
    extra_names_lc = set(n.lower() for n in _defaults().get("blokkeer_ook_person_names", []))
    extra_names_lc |= set(n.lower() for n in _extra_names_from_admin_relations())

    out = []
    for c in cards:
        tags = set((t or "").lower() for t in (c.get("tags") or []))
        if tags & blocked:
            continue
        # v13: ook lade-check (persoonlijke lade doen/voelen zonder tags kan lekken)
        lade = (c.get("lade") or c.get("_lade") or "").lower()
        if grad >= 5 and lade in ("privé", "prive", "persoonlijk"):
            continue
        # v13: bij grad 5+ ook familie-namen in laag1/ws5 filteren
        if grad >= 5 and extra_names_lc:
            haystack_parts = [
                str((c.get("lagen") or {}).get("laag1", "")),
                str((c.get("lagen") or {}).get("laag2", "")),
                " ".join(str(v) for v in (c.get("ws5") or {}).values() if v),
                str(c.get("begrip", "")),
            ]
            haystack = " ".join(haystack_parts).lower()
            if any(n in haystack for n in extra_names_lc):
                continue
        out.append(c)
    return out


def filter_identity_facts(facts: Dict, gradatie: Optional[int]) -> Dict:
    """Voor grad >= 5: strip about_user + about_relationship (persoonlijk).
    about_spark blijft — dat is Spark's zelfperceptie, geen user-PII.
    """
    grad = int(gradatie) if gradatie else 7
    if grad <= 4:
        return facts or {}
    return {
        "about_user": [],
        "about_relationship": [],
        "about_spark": (facts or {}).get("about_spark", []),
    }


def strip_person_names(text: str, gradatie: Optional[int]) -> str:
    """Vervang privacy-gevoelige persoonsnamen door 'iemand'.

    Alleen actief voor gradatie 5+. Behoudt requester's eigen naam
    door callers die die apart doorgeven (niet in deze helper — hier
    strippen we alleen namen uit de matrix + admin-familie).
    """
    if not text or not should_strip_person_names(gradatie):
        return text
    defs = _defaults()
    names = list(defs.get("blokkeer_ook_person_names") or [])
    names += _extra_names_from_admin_relations()
    if not names:
        return text
    # Sort langste eerst → 'Willie' vóór 'Wil'
    names_sorted = sorted(set(names), key=lambda n: -len(n))
    out = text
    for n in names_sorted:
        if not n or len(n) < 2:
            continue
        # Word-boundary vervanging, case-insensitive
        pattern = r"\b" + re.escape(n) + r"\b"
        out = re.sub(pattern, "iemand", out, flags=re.IGNORECASE)
    return out


def reset_cache() -> None:
    """Voor tests / na settings-update."""
    _CACHE["defaults"] = None
    _CACHE["extra_names"] = None
