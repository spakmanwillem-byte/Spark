"""
Relation Extraction Service (v4_rel_001) — Auto-extract relaties uit chat-berichten.

Patterns:
  "mijn moeder/vader/zusje/broer/vriend/oma/opa/dochter/zoon/man/vrouw/partner [Naam]"
  "[Naam] is mijn moeder/vader/..."
  "[Naam], mijn moeder/..."

Voegt nieuwe relaties toe aan /data/persons/{user_id}_relationships.json
(append-only, dedup op person_name + relation_type, geen overschrijving).
"""
import re
import json
from pathlib import Path
from typing import List, Dict
from datetime import datetime, timezone

from modules.core.storage import load_json, save_json

DATA_DIR = Path(__file__).parent.parent.parent / "data"
PERSONS_DIR = DATA_DIR / "persons"
PERSONS_DIR.mkdir(parents=True, exist_ok=True)

# Relatie-types die we herkennen (Nederlands, lowercase)
REL_TYPES = {
    "moeder": "familie/moeder",
    "ma": "familie/moeder",
    "mama": "familie/moeder",
    "vader": "familie/vader",
    "pa": "familie/vader",
    "papa": "familie/vader",
    "zus": "familie/zus",
    "zusje": "familie/zus",
    "broer": "familie/broer",
    "broertje": "familie/broer",
    "oma": "familie/oma",
    "opa": "familie/opa",
    "dochter": "familie/dochter",
    "zoon": "familie/zoon",
    "kind": "familie/kind",
    "man": "familie/partner",
    "vrouw": "familie/partner",
    "partner": "familie/partner",
    "vriend": "vriend",
    "vriendin": "vriend",
    "goede vriend": "vriend/goed",
    "beste vriend": "vriend/beste",
    "collega": "collega",
    "buurman": "buur",
    "buurvrouw": "buur",
    "nicht": "familie/nicht",
    "neef": "familie/neef",
    "tante": "familie/tante",
    "oom": "familie/oom",
    "schoonmoeder": "familie/schoonmoeder",
    "schoonvader": "familie/schoonvader",
}

# Sorteer langste eerst zodat "goede vriend" matched vóór "vriend"
REL_KEYS_SORTED = sorted(REL_TYPES.keys(), key=len, reverse=True)
REL_REGEX = "|".join(re.escape(k) for k in REL_KEYS_SORTED)

# Patterns
NAAM_REGEX = r"([A-Z][a-zà-ÿ]+(?:[\s\-]+[A-Z][a-zà-ÿ]+){0,2})"  # bv. "Anneke" of "Anne Marie"

# NB: alleen "mijn" mag case-insensitive zijn, naam-regex MOET hoofdletter eisen.
# Anders worden "heeft", "werkt" etc. ook als naam-vervolg gezien.
PATTERN_MIJN_REL_NAAM = re.compile(
    rf"\b[Mm]ijn\s+({REL_REGEX})\s+{NAAM_REGEX}\b"
)
PATTERN_NAAM_IS_MIJN = re.compile(
    rf"\b{NAAM_REGEX}\s+is\s+[Mm]ijn\s+({REL_REGEX})\b"
)
PATTERN_NAAM_KOMMA = re.compile(
    rf"\b{NAAM_REGEX}\s*,\s*[Mm]ijn\s+({REL_REGEX})(?:\s|,|\.|$)"
)

# Negatieve woorden die we niet als naam willen
NAME_BLACKLIST = {"De", "Het", "Een", "Wat", "Hoe", "Hij", "Zij", "Mijn", "Jouw"}


def _rel_file(user_id: str) -> Path:
    return PERSONS_DIR / f"{user_id}_relationships.json"


def _normalize(name: str) -> str:
    return name.strip()


def extract(text: str) -> List[Dict]:
    """Vind relatie-mentions in tekst."""
    if not text:
        return []
    findings: List[Dict] = []
    seen = set()

    def add(naam: str, rel_word: str):
        naam = _normalize(naam)
        if not naam or naam in NAME_BLACKLIST:
            return
        key = (naam.lower(), rel_word.lower())
        if key in seen:
            return
        seen.add(key)
        findings.append({
            "person_name": naam,
            "relation_type": REL_TYPES.get(rel_word.lower(), rel_word.lower()),
            "raw_relation_word": rel_word.lower(),
        })

    for m in PATTERN_MIJN_REL_NAAM.finditer(text):
        rel_word, naam = m.group(1), m.group(2)
        add(naam, rel_word)
    for m in PATTERN_NAAM_IS_MIJN.finditer(text):
        naam, rel_word = m.group(1), m.group(2)
        add(naam, rel_word)
    for m in PATTERN_NAAM_KOMMA.finditer(text):
        naam, rel_word = m.group(1), m.group(2)
        add(naam, rel_word)

    return findings


def add_relations(user_id: str, findings: List[Dict]) -> List[Dict]:
    """Append nieuwe relaties (dedup op person_name + relation_type)."""
    if not findings or not user_id:
        return []
    fp = _rel_file(user_id)
    data = load_json(fp, default={"user_id": user_id, "relationships": []})
    existing = data.get("relationships", [])
    existing_keys = {(r.get("person_name","").lower(), r.get("relation_type","").lower()) for r in existing}
    new_entries = []
    for f in findings:
        k = (f["person_name"].lower(), f["relation_type"].lower())
        if k in existing_keys:
            continue
        entry = {
            "person_name": f["person_name"],
            "relation_type": f["relation_type"],
            "knows_about_me": True,
            "i_know_about": True,
            "notes": f"Auto-detected uit chat ({datetime.now(timezone.utc).strftime('%Y-%m-%d')})",
            "auto_detected": True,
            "detected_at": datetime.now(timezone.utc).isoformat(),
        }
        existing.append(entry)
        existing_keys.add(k)
        new_entries.append(entry)
    if new_entries:
        data["relationships"] = existing
        save_json(fp, data)
    return new_entries


def detect_and_save(user_id: str, text: str) -> List[Dict]:
    """Combined: extract + save. Returns lijst van NIEUW toegevoegde relaties."""
    findings = extract(text)
    return add_relations(user_id, findings)
