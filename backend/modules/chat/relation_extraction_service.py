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
from typing import List, Dict, Optional
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
    "omaatje": "familie/oma",
    "opa": "familie/opa",
    "opaatje": "familie/opa",
    "dochter": "familie/dochter",
    "dochtertje": "familie/dochter",
    "zoon": "familie/zoon",
    "zoontje": "familie/zoon",
    "kind": "familie/kind",
    "man": "familie/partner",
    "vrouw": "familie/partner",
    "partner": "familie/partner",
    "vriend": "vriend",
    "vriendin": "vriend",
    "vriendje": "vriend",
    "goede vriend": "vriend/goed",
    "beste vriend": "vriend/beste",
    "collega": "collega",
    "buurman": "buur",
    "buurvrouw": "buur",
    "nicht": "familie/nicht",
    "nichtje": "familie/nicht",
    "neef": "familie/neef",
    "neefje": "familie/neef",
    "tante": "familie/tante",
    "oom": "familie/oom",
    "schoonmoeder": "familie/schoonmoeder",
    "schoonvader": "familie/schoonvader",
    "schoonzus": "familie/schoonzus",
    "schoonbroer": "familie/schoonbroer",
    "zwager": "familie/schoonbroer",
    "schoonzoon": "familie/schoonzoon",
    "schoondochter": "familie/schoondochter",
    "bekende": "bekende",
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
# v4_rel_003 — "ik ken X" / "X ken ik" → relatie "bekende" (zwakke link, user kan upgraden)
PATTERN_KEN_NAAM = re.compile(
    rf"\b[Ii]k\s+ken\s+{NAAM_REGEX}\b"
)
PATTERN_NAAM_KEN_IK = re.compile(
    rf"\b{NAAM_REGEX}\s+ken\s+ik\b"
)
# v6_rel_004 — Transitieve relatie: "X is de Y van Z" (bv. "Joy is de dochter van Maaike")
# Wordt gemapt naar een impliciete user-relatie als Z al bekend is.
PATTERN_NAAM_IS_REL_VAN = re.compile(
    rf"\b{NAAM_REGEX}\s+is\s+(?:de|het|een)\s+({REL_REGEX})\s+van\s+{NAAM_REGEX}\b"
)

# Welke combinaties geven welke transitieve relatie?
# (Z_rel_to_user, X_rel_to_Z) → X_rel_to_user
TRANSITIVE_REL = {
    # zus/broer's kind = nichtje/neefje
    ("familie/zus", "familie/dochter"): "familie/nicht",
    ("familie/zus", "familie/zoon"): "familie/neef",
    ("familie/broer", "familie/dochter"): "familie/nicht",
    ("familie/broer", "familie/zoon"): "familie/neef",
    # moeder/vader's kind = zus/broer (al bekend) — skip om dubbele detectie te voorkomen
    # oma/opa's kind = ouder (al bekend)
    # ouders van ouders → grootouders
    ("familie/moeder", "familie/moeder"): "familie/oma",
    ("familie/moeder", "familie/vader"): "familie/opa",
    ("familie/vader", "familie/moeder"): "familie/oma",
    ("familie/vader", "familie/vader"): "familie/opa",
    # partners van familie → schoonfamilie
    ("familie/zus", "familie/partner"): "familie/schoonbroer",
    ("familie/broer", "familie/partner"): "familie/schoonzus",
    ("familie/dochter", "familie/partner"): "familie/schoonzoon",
    ("familie/zoon", "familie/partner"): "familie/schoondochter",
    # kind van mijn kind = kleinkind
    ("familie/dochter", "familie/dochter"): "familie/kleindochter",
    ("familie/dochter", "familie/zoon"): "familie/kleinzoon",
    ("familie/zoon", "familie/dochter"): "familie/kleindochter",
    ("familie/zoon", "familie/zoon"): "familie/kleinzoon",
}

# Negatieve woorden die we niet als naam willen
NAME_BLACKLIST = {"De", "Het", "Een", "Wat", "Hoe", "Hij", "Zij", "Mijn", "Jouw"}


def _rel_file(user_id: str) -> Path:
    return PERSONS_DIR / f"{user_id}_relationships.json"


def _normalize(name: str) -> str:
    return name.strip()


def extract(text: str, user_id: Optional[str] = None) -> List[Dict]:
    """Vind relatie-mentions in tekst.

    v6_rel_004 — Als `user_id` meegegeven is, doet ook transitieve relatie-detectie
    ("X is de Y van Z") door bestaande relaties van de user op te zoeken.
    """
    if not text:
        return []
    findings: List[Dict] = []
    seen = set()

    def add(naam: str, rel_word: str, note: str = ""):
        naam = _normalize(naam)
        if not naam or naam in NAME_BLACKLIST:
            return
        # rel_word kan al een volledig rel_type zijn (bv. "familie/nicht") via transitive
        if rel_word in REL_TYPES:
            rel_type = REL_TYPES[rel_word]
        elif "/" in rel_word:
            rel_type = rel_word
        else:
            rel_type = rel_word.lower()
        key = (naam.lower(), rel_type.lower())
        if key in seen:
            return
        seen.add(key)
        f = {
            "person_name": naam,
            "relation_type": rel_type,
            "raw_relation_word": rel_word.lower(),
        }
        if note:
            f["transitive_note"] = note
        findings.append(f)

    for m in PATTERN_MIJN_REL_NAAM.finditer(text):
        rel_word, naam = m.group(1), m.group(2)
        add(naam, rel_word)
    for m in PATTERN_NAAM_IS_MIJN.finditer(text):
        naam, rel_word = m.group(1), m.group(2)
        add(naam, rel_word)
    for m in PATTERN_NAAM_KOMMA.finditer(text):
        naam, rel_word = m.group(1), m.group(2)
        add(naam, rel_word)
    # v4_rel_003: "ik ken X" / "X ken ik" → impliciete relatie "bekende"
    for pat in (PATTERN_KEN_NAAM, PATTERN_NAAM_KEN_IK):
        for m in pat.finditer(text):
            naam = m.group(1)
            add(naam, "bekende")

    # v6_rel_004 — Transitieve relatie via bestaande relatie van user
    if user_id:
        try:
            existing_data = load_json(_rel_file(user_id), default={"relationships": []})
            existing_rels = existing_data.get("relationships", [])
            # Map naam → rel_type van bekende relaties
            known = {}
            for r in existing_rels:
                nm = (r.get("person_name") or "").strip().lower()
                rt = r.get("relation_type") or ""
                if nm and rt and nm not in known:
                    known[nm] = rt
            for m in PATTERN_NAAM_IS_REL_VAN.finditer(text):
                x_naam = m.group(1)
                rel_word = m.group(2)
                z_naam = m.group(3)
                # Eerst de directe relatie tussen X en Z toevoegen (niet user-relatie, maar info)
                # Z is bekend? Dan kan transitive afgeleid worden:
                z_rel_user = known.get(z_naam.lower().strip())
                xz_rel = REL_TYPES.get(rel_word.lower(), f"familie/{rel_word.lower()}")
                if z_rel_user:
                    transitive = TRANSITIVE_REL.get((z_rel_user, xz_rel))
                    if transitive:
                        add(x_naam, transitive, note=f"afgeleid: {rel_word} van {z_naam}")
        except Exception as e:
            print(f"[rel-extract] transitive lookup failed: {e}")

    return findings


def add_relations(user_id: str, findings: List[Dict]) -> List[Dict]:
    """Append nieuwe relaties (dedup op person_name + relation_type).
    v4_rel_002: synchroniseert óók de persons cards file (/persons/{user_id}.json)
    zodat de Persoonkaarten UI de relatie direct toont."""
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
        # Sync naar persons cards file zodat UI Persoonkaarten ze toont
        try:
            _sync_persons_cards(user_id, new_entries)
        except Exception as e:
            print(f"[rel-extract] persons-card sync failed: {e}")
    return new_entries


def _sync_persons_cards(user_id: str, new_relations: List[Dict]):
    """Maak/update person-cards in /data/persons/{user_id}.json voor elke nieuwe relatie."""
    import uuid
    pf = PERSONS_DIR / f"{user_id}.json"
    pd = load_json(pf, default={"persons": [], "metadata": {"user_id": user_id, "total_persons": 0}})
    persons = pd.get("persons", [])

    # Index op naam (lowercase) voor lookup/update
    by_name = {(p.get("volledige_naam") or p.get("naam") or "").strip().lower(): p for p in persons}

    # Map relation_type → kort relatie-veld + gradatie
    REL_TO_FIELD = {
        "familie/moeder": ("moeder", 2),
        "familie/vader": ("vader", 2),
        "familie/zoon": ("zoon", 2),
        "familie/dochter": ("dochter", 2),
        "familie/broer": ("broer", 2),
        "familie/zus": ("zus", 2),
        "familie/opa": ("opa", 3),
        "familie/oma": ("oma", 3),
        "familie/partner": ("partner", 1),
        "familie/man": ("partner", 1),
        "familie/vrouw": ("partner", 1),
        "vriend/jeugdvriend": ("jeugdvriend", 3),
        "vriend/vriend": ("vriend", 3),
        "vriend/oud-collega": ("oud-collega", 4),
        "collega/collega": ("collega", 4),
        "kennis/kennis": ("kennis", 5),
    }

    now = datetime.now(timezone.utc).isoformat()
    changed = False
    for rel in new_relations:
        name = rel.get("person_name", "").strip()
        rtype = rel.get("relation_type", "")
        if not name:
            continue
        short_rel, grad = REL_TO_FIELD.get(rtype, (rtype.split("/")[-1] if "/" in rtype else rtype, 5))
        existing_p = by_name.get(name.lower())
        if existing_p:
            # Alleen aanvullen als velden leeg zijn
            if not existing_p.get("relatie"):
                existing_p["relatie"] = short_rel
                existing_p["gradatie"] = min(existing_p.get("gradatie", 5), grad)
                existing_p["updated_at"] = now
                tags = set(existing_p.get("tags") or [])
                cat = rtype.split("/")[0] if "/" in rtype else "kennis"
                tags.update([cat, short_rel])
                existing_p["tags"] = sorted(tags)
                changed = True
        else:
            cat = rtype.split("/")[0] if "/" in rtype else "kennis"
            entry = {
                "id": f"person-{uuid.uuid4().hex[:8]}",
                "naam": name,
                "volledige_naam": name,
                "relatie": short_rel,
                "gradatie": grad,
                "is_user": False,
                "linked_user_id": None,
                "tags": sorted({cat, short_rel}),
                "notes": rel.get("notes", ""),
                "created_by": user_id,
                "conversation_refs": [],
                "knowledge_refs": [],
                "auto_detected": True,
                "created_at": now,
                "updated_at": now,
            }
            persons.append(entry)
            by_name[name.lower()] = entry
            changed = True
    if changed:
        pd["persons"] = persons
        pd.setdefault("metadata", {})
        pd["metadata"]["total_persons"] = len(persons)
        pd["metadata"]["last_updated"] = now
        save_json(pf, pd)


def detect_and_save(user_id: str, text: str) -> List[Dict]:
    """Combined: extract + save. Returns lijst van NIEUW toegevoegde relaties."""
    findings = extract(text, user_id=user_id)
    return add_relations(user_id, findings)
