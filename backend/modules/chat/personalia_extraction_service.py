"""
v6_personalia_extract_001 — Auto-extract personalia (geboortedatum, woonplaats, beroep, etc.)
uit chat-berichten en koppel ze aan de juiste persoon-kaart in /persons/{user_id}.json.

Patterns:
  "X is [op] DD MAAND YYYY geboren"      → person.geboortedatum
  "X woont in PLAATS"                    → person.woonplaats
  "X werkt als BEROEP"                   → person.beroep
  "X is BEROEP"                          → person.beroep (zwakker signaal)
  "X is N jaar [oud]"                    → person.geboortejaar (afgeleid)
"""
import re
import json
import unicodedata
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime, timezone

from modules.core.storage import load_json, save_json

DATA_DIR = Path(__file__).parent.parent.parent / "data"
PERSONS_DIR = DATA_DIR / "persons"

MAANDEN = {
    "januari": 1, "jan": 1, "februari": 2, "feb": 2, "maart": 3, "mrt": 3,
    "april": 4, "apr": 4, "mei": 5, "juni": 6, "jun": 6, "juli": 7, "jul": 7,
    "augustus": 8, "aug": 8, "september": 9, "sep": 9, "sept": 9,
    "oktober": 10, "okt": 10, "november": 11, "nov": 11, "december": 12, "dec": 12,
}

# Hulp: case-insensitive groep voor maand-namen zonder de hele regex case-blind te maken
_MAAND_RX_PARTS = []
for k in MAANDEN.keys():
    # bv. "februari" → "[fF][eE][bB][rR][uU][aA][rR][iI]"
    _MAAND_RX_PARTS.append("".join(f"[{c}{c.upper()}]" if c.isalpha() else c for c in k))
_MAAND_GROUP = "(" + "|".join(_MAAND_RX_PARTS) + ")"

NAAM_RX = r"([A-Z][a-zà-ÿ]+(?:[\s\-]+[A-Z][a-zà-ÿ]+){0,2})"

PAT_BIRTHDATE_NL = re.compile(
    rf"\b{NAAM_RX}\s+is\s+(?:op\s+)?(\d{{1,2}})\s+{_MAAND_GROUP}\s+(\d{{4}})\s+geboren\b"
)
PAT_BIRTHDATE_ISO = re.compile(
    rf"\b{NAAM_RX}\s+is\s+(?:op\s+)?geboren\s+(?:op\s+)?(\d{{1,2}})[\-/](\d{{1,2}})[\-/](\d{{4}})\b"
)
PAT_AGE = re.compile(
    rf"\b{NAAM_RX}\s+is\s+(\d{{1,3}})\s+jaar(?:\s+oud)?\b"
)
PAT_WOONT = re.compile(
    rf"\b{NAAM_RX}\s+woont\s+(?:in|te)\s+([A-Z][a-zà-ÿ \-]+?)(?:\.|,|$|\n)"
)
PAT_WERKT = re.compile(
    rf"\b{NAAM_RX}\s+(?:werkt|werkte)\s+(?:als|bij)\s+([a-zA-Zà-ÿ \-]+?)(?:\.|,|$|\n)"
)


def _now():
    return datetime.now(timezone.utc).isoformat()


def _strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def _name_key(s: str) -> str:
    """Genormaliseerde naam-sleutel voor matching (lowercase + zonder accenten)."""
    return _strip_accents((s or "").strip().lower())


def _find_persons_by_name(user_id: str, naam: str) -> List[Dict]:
    """Vind alle persoon-kaarten die matchen op naam (exact, voornaam-only, of fuzzy)."""
    pf = PERSONS_DIR / f"{user_id}.json"
    if not pf.exists():
        return []
    pd = load_json(pf, default={"persons": []})
    persons = pd.get("persons", [])
    q = _name_key(naam)
    matches = []
    for p in persons:
        cand = _name_key(p.get("volledige_naam") or p.get("naam") or "")
        if not cand:
            continue
        if cand == q or q in cand.split() or cand.startswith(q + " ") or cand.endswith(" " + q) or q in cand:
            matches.append(p)
    return matches


def extract_personalia(text: str) -> List[Dict]:
    """Vind personalia-mentions. Returns list of dicts:
    {naam, field, value, raw}
    """
    findings: List[Dict] = []
    if not text:
        return findings

    for m in PAT_BIRTHDATE_NL.finditer(text):
        naam = m.group(1).strip()
        d, maand_word, y = m.group(2), m.group(3).lower(), m.group(4)
        maand = MAANDEN.get(maand_word)
        if not maand:
            continue
        try:
            iso = f"{int(y):04d}-{int(maand):02d}-{int(d):02d}"
            datetime.strptime(iso, "%Y-%m-%d")
            findings.append({"naam": naam, "field": "geboortedatum", "value": iso, "raw": m.group(0)})
        except ValueError:
            continue

    for m in PAT_BIRTHDATE_ISO.finditer(text):
        naam = m.group(1).strip()
        d, mo, y = m.group(2), m.group(3), m.group(4)
        try:
            iso = f"{int(y):04d}-{int(mo):02d}-{int(d):02d}"
            datetime.strptime(iso, "%Y-%m-%d")
            findings.append({"naam": naam, "field": "geboortedatum", "value": iso, "raw": m.group(0)})
        except ValueError:
            continue

    for m in PAT_AGE.finditer(text):
        naam = m.group(1).strip()
        leeftijd = int(m.group(2))
        if 0 <= leeftijd <= 130:
            findings.append({"naam": naam, "field": "leeftijd", "value": leeftijd, "raw": m.group(0)})

    for m in PAT_WOONT.finditer(text):
        naam = m.group(1).strip()
        plaats = m.group(2).strip().rstrip(",.;")
        findings.append({"naam": naam, "field": "woonplaats", "value": plaats, "raw": m.group(0)})

    for m in PAT_WERKT.finditer(text):
        naam = m.group(1).strip()
        beroep = m.group(2).strip().rstrip(",.;")
        # Filter te-vage beroepen
        if len(beroep) > 1 and beroep.lower() not in ("daar", "hier", "ze", "hij"):
            findings.append({"naam": naam, "field": "beroep", "value": beroep, "raw": m.group(0)})

    return findings


def save_personalia(user_id: str, findings: List[Dict]) -> List[Dict]:
    """Schrijf gevonden personalia naar de juiste person-card.
    Returns lijst van applied changes."""
    if not user_id or not findings:
        return []
    pf = PERSONS_DIR / f"{user_id}.json"
    if not pf.exists():
        return []
    pd = load_json(pf, default={"persons": []})
    persons = pd.get("persons", [])
    applied = []

    def _local_match(naam_query: str) -> List[Dict]:
        q = _name_key(naam_query)
        out = []
        for pp in persons:
            cand = _name_key(pp.get("volledige_naam") or pp.get("naam") or "")
            if not cand:
                continue
            if cand == q or q in cand.split() or cand.startswith(q + " ") or cand.endswith(" " + q) or q in cand:
                out.append(pp)
        return out

    for f in findings:
        matches = _local_match(f["naam"])
        if not matches:
            continue
        for p in matches:
            field = f["field"]
            value = f["value"]
            current = p.get(field)
            # leeftijd → geboortejaar
            if field == "leeftijd":
                now_y = datetime.now(timezone.utc).year
                geboortejaar = now_y - int(value)
                if p.get("geboortedatum"):
                    # heeft al exacte datum, leeftijd is afgeleid → skip
                    continue
                if p.get("geboortejaar") and p["geboortejaar"] == geboortejaar:
                    continue
                p["geboortejaar"] = geboortejaar
                p["updated_at"] = _now()
                applied.append({"person_id": p.get("id"), "naam": p.get("naam"),
                                "field": "geboortejaar", "value": geboortejaar, "from": "leeftijd"})
            elif field == "geboortedatum":
                if current == value:
                    continue
                p["geboortedatum"] = value
                # geboortejaar voor backward-compat
                try:
                    p["geboortejaar"] = int(value.split("-")[0])
                except (ValueError, IndexError):
                    pass
                p["updated_at"] = _now()
                applied.append({"person_id": p.get("id"), "naam": p.get("naam"),
                                "field": "geboortedatum", "value": value})
            else:
                # generieke string-velden
                if current == value:
                    continue
                p[field] = value
                p["updated_at"] = _now()
                applied.append({"person_id": p.get("id"), "naam": p.get("naam"),
                                "field": field, "value": value})

    if applied:
        pd["persons"] = persons
        pd.setdefault("metadata", {})["last_updated"] = _now()
        save_json(pf, pd)

    return applied


def detect_and_save(user_id: str, text: str) -> List[Dict]:
    findings = extract_personalia(text)
    return save_personalia(user_id, findings)


# v6_personalia_extract_001 — Spark-bekentenis voor de chat
def format_applied_message(applied: List[Dict]) -> str:
    """Vorm een korte Spark-zin: 'Genoteerd: Lotus geboren 2009-02-11.'"""
    if not applied:
        return ""
    parts = []
    for a in applied:
        naam = a.get("naam", "?")
        field = a.get("field", "?")
        val = a.get("value", "?")
        # Format dates nicer
        if field == "geboortedatum":
            try:
                d = datetime.strptime(val, "%Y-%m-%d")
                pretty = d.strftime("%d-%m-%Y")
                parts.append(f"**{naam}** geboren op {pretty}")
            except ValueError:
                parts.append(f"**{naam}** geboren op {val}")
        elif field == "geboortejaar":
            parts.append(f"**{naam}** geboren in {val}")
        elif field == "woonplaats":
            parts.append(f"**{naam}** woont in {val}")
        elif field == "beroep":
            parts.append(f"**{naam}** werkt als {val}")
        else:
            parts.append(f"**{naam}** {field}: {val}")
    return "📝 Genoteerd: " + " · ".join(parts) + "."
