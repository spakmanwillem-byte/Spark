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

# v6_personalia_pronoun_001 — Herken "mijn moeder/vader/zus/etc." als persoon-verwijzing.
# Wordt opgelost door _resolve_relation_ref() naar de naam uit relationships.json.
_REL_REF_WORDS = [
    "moeder", "vader", "zus", "zusje", "broer", "broertje", "oma", "opa",
    "dochter", "zoon", "man", "vrouw", "partner", "tante", "oom", "neef", "nicht",
    "nichtje", "neefje", "schoonmoeder", "schoonvader", "schoonzus", "schoonbroer",
]

NAAM_RX = r"([A-Z][a-zà-ÿ]+(?:[\s\-]+[A-Z][a-zà-ÿ]+){0,2})"

PAT_BIRTHDATE_NL = re.compile(
    rf"\b{NAAM_RX}\s+(?i:is)\s+(?i:op\s+)?(\d{{1,2}})\s+{_MAAND_GROUP}\s+(\d{{4}})\s+(?i:geboren)\b"
)
PAT_BIRTHDATE_ISO = re.compile(
    rf"\b{NAAM_RX}\s+(?i:is)\s+(?i:op\s+)?(?i:geboren)\s+(?i:op\s+)?(\d{{1,2}})[\-/](\d{{1,2}})[\-/](\d{{4}})\b"
)
PAT_AGE = re.compile(
    rf"\b{NAAM_RX}\s+(?i:is)\s+(\d{{1,3}})\s+(?i:jaar)(?:\s+(?i:oud))?\b"
)
PAT_WOONT = re.compile(
    rf"\b{NAAM_RX}\s+(?i:woont)\s+(?i:in|te)\s+([A-Z][a-zà-ÿ \-]+?)(?:\.|,|$|\n)"
)
PAT_WERKT = re.compile(
    rf"\b{NAAM_RX}\s+(?i:werkt|werkte)\s+(?i:als|bij)\s+([a-zA-Zà-ÿ \-]+?)(?:\.|,|$|\n)"
)

# v6_personalia_birthday_002 — "[Naam/mijn relatie] is jarig op DD MAAND"
PAT_JARIG_OP = re.compile(
    rf"\b(?:{NAAM_RX}|((?i:mijn)\s+(?i:{'|'.join(_REL_REF_WORDS)})))\s+(?i:is)\s+(?i:jarig)\s+(?i:op\s+)?(\d{{1,2}})\s+{_MAAND_GROUP}\b",
)
# "DD MAAND is [Naam/mijn relatie] jarig" — andersom
PAT_OP_JARIG = re.compile(
    rf"\b(\d{{1,2}})\s+{_MAAND_GROUP}\s+(?i:is)\s+(?:{NAAM_RX}|((?i:mijn)\s+(?i:{'|'.join(_REL_REF_WORDS)})))\s+(?i:jarig)\b",
)
# v6_personalia_pronoun_001 — "mijn [relatie] is N jaar [oud]"
PAT_REL_AGE = re.compile(
    rf"\b((?i:mijn)\s+(?i:{'|'.join(_REL_REF_WORDS)}))\s+(?i:is)\s+(\d{{1,3}})\s+(?i:jaar)(?:\s+(?i:oud))?\b",
)
PAT_PRONOUN_AGE = re.compile(
    r"\b(?i:zij|hij|ze)\s+(?i:is)\s+(\d{1,3})(?:\s+(?i:jaar))?\b",
)
# "mijn [relatie] is op DD MAAND YYYY geboren"
PAT_REL_BIRTHDATE = re.compile(
    rf"\b((?i:mijn)\s+(?i:{'|'.join(_REL_REF_WORDS)}))\s+(?i:is)\s+(?i:op\s+)?(\d{{1,2}})\s+{_MAAND_GROUP}\s+(\d{{4}})\s+(?i:geboren)\b",
)
# "mijn [relatie] woont in PLAATS"
PAT_REL_WOONT = re.compile(
    rf"\b((?i:mijn)\s+(?i:{'|'.join(_REL_REF_WORDS)}))\s+(?i:woont)\s+(?i:in|te)\s+([A-Z][a-zà-ÿ \-]+?)(?:\.|,|$|\n)",
)

# v6_personalia_bezittingen_001 — "X heeft een Y" / "X bezit een Y"
PAT_BEZIT = re.compile(
    rf"\b{NAAM_RX}\s+(?i:heeft|bezit)\s+(?i:een|de|het)?\s*([a-zà-ÿ][\w\-]*(?:\s+[a-zà-ÿ][\w\-]*){{0,2}}?)\s*(?:\.|,|;|\s+en\b|\s+maar\b|\s+ook\b|$|\n)"
)
PAT_REL_BEZIT = re.compile(
    rf"\b((?i:mijn)\s+(?i:{'|'.join(_REL_REF_WORDS)}))\s+(?i:heeft|bezit)\s+(?i:een|de|het)?\s*([a-zà-ÿ][\w\-]*(?:\s+[a-zà-ÿ][\w\-]*){{0,2}}?)\s*(?:\.|,|;|\s+en\b|\s+maar\b|\s+ook\b|$|\n)"
)
PAT_INTEREST = re.compile(
    rf"\b{NAAM_RX}\s+(?i:houdt\s+van|is\s+gek\s+op|is\s+dol\s+op)\s+([a-zà-ÿ][\w\-]*(?:\s+[a-zà-ÿ][\w\-]*){{0,2}}?)\s*(?:\.|,|;|\s+en\b|\s+maar\b|$|\n)"
)
PAT_REL_INTEREST = re.compile(
    rf"\b((?i:mijn)\s+(?i:{'|'.join(_REL_REF_WORDS)}))\s+(?i:houdt\s+van|is\s+gek\s+op|is\s+dol\s+op)\s+([a-zà-ÿ][\w\-]*(?:\s+[a-zà-ÿ][\w\-]*){{0,2}}?)\s*(?:\.|,|;|\s+en\b|\s+maar\b|$|\n)"
)
# v6_personalia_continuation_001 — "... en is gek op Y" / "... en heeft Y" (subject overerving)
# Matches alleen als er een eerder onderwerp was, gebruikt context.
PAT_AND_BEZIT = re.compile(
    r"\s+en\s+(?i:heeft|bezit)\s+(?i:een|de|het)?\s*([a-zà-ÿ][\w\-]*(?:\s+[a-zà-ÿ][\w\-]*){0,2}?)\s*(?:\.|,|;|\s+en\b|\s+maar\b|$|\n)"
)
PAT_AND_INTEREST = re.compile(
    r"\s+en\s+(?i:houdt\s+van|is\s+gek\s+op|is\s+dol\s+op)\s+([a-zà-ÿ][\w\-]*(?:\s+[a-zà-ÿ][\w\-]*){0,2}?)\s*(?:\.|,|;|\s+en\b|\s+maar\b|$|\n)"
)
# Filter woorden die geen "echt bezit" zijn
_BEZIT_BLACKLIST = {"zin", "tijd", "honger", "dorst", "haast", "spijt", "gelijk", "ongelijk",
                    "geluk", "pech", "last", "moeite", "plezier", "lol", "respect", "begrip",
                    "iets", "niets", "alles", "geen", "veel", "weinig", "wat", "dat", "dit"}


def _resolve_relation_ref(user_id: str, ref: str) -> Optional[str]:
    """'mijn moeder' → echte naam uit relationships.json. Returns naam of None."""
    if not ref or not user_id:
        return None
    # extract rel-word
    parts = ref.strip().lower().split()
    if len(parts) < 2 or parts[0] != "mijn":
        return None
    rel_word = " ".join(parts[1:])
    # Map plural/diminutive → singular like in smart_intents
    rel_word_norm = rel_word
    plurals = {"zusje": "zus", "broertje": "broer", "nichtje": "nicht", "neefje": "neef",
               "ma": "moeder", "mama": "moeder", "pa": "vader", "papa": "vader"}
    rel_word_norm = plurals.get(rel_word, rel_word)
    # Map naar relation_type uit relationships
    rel_file = DATA_DIR / "persons" / f"{user_id}_relationships.json"
    if not rel_file.exists():
        return None
    rd = load_json(rel_file, default={"relationships": []})
    rels = rd.get("relationships", []) if isinstance(rd, dict) else rd
    base = rel_word_norm.lower()
    matches = []
    for r in rels:
        rt = (r.get("relation_type") or "").lower()
        if rt.endswith(f"/{base}") or rt == base:
            matches.append(r.get("person_name"))
    if not matches:
        return None
    # Voorkeur: niet-auto-detected (hand-getypt door user, dus zeker)
    primaries = [r for r in rels if r.get("person_name") in matches and not r.get("auto_detected")]
    if primaries:
        return primaries[0].get("person_name")
    return matches[0]


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


def extract_personalia(text: str, user_id: Optional[str] = None) -> List[Dict]:
    """Vind personalia-mentions. Returns list of dicts:
    {naam, field, value, raw}

    v6_personalia_pronoun_001 — Resolves "mijn moeder/vader/etc." en pronomen "zij/hij"
    via user_id's relationships + last-mention in zelfde zin.
    """
    findings: List[Dict] = []
    if not text:
        return findings

    # === bestaande directe naam-patterns ===
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
        if len(beroep) > 1 and beroep.lower() not in ("daar", "hier", "ze", "hij"):
            findings.append({"naam": naam, "field": "beroep", "value": beroep, "raw": m.group(0)})

    # === v6_personalia_birthday_002 — verjaardag DAG+MAAND (zonder jaar) ===
    # PAT_JARIG_OP: groups = (naam_directe, mijn_relatie_ref, dag, maand_word)
    last_subject_naam: Optional[str] = None  # voor pronoun-resolutie
    for m in PAT_JARIG_OP.finditer(text):
        naam_direct = m.group(1)
        rel_ref = m.group(2)
        d, maand_word = m.group(3), m.group(4).lower()
        maand = MAANDEN.get(maand_word)
        if not maand:
            continue
        naam = naam_direct or (_resolve_relation_ref(user_id, rel_ref) if rel_ref else None)
        if not naam:
            continue
        last_subject_naam = naam
        findings.append({"naam": naam, "field": "geboortedag", "value": int(d), "raw": m.group(0)})
        findings.append({"naam": naam, "field": "geboortemaand", "value": int(maand), "raw": m.group(0)})

    for m in PAT_OP_JARIG.finditer(text):
        d, maand_word = m.group(1), m.group(2).lower()
        naam_direct = m.group(3)
        rel_ref = m.group(4)
        maand = MAANDEN.get(maand_word)
        if not maand:
            continue
        naam = naam_direct or (_resolve_relation_ref(user_id, rel_ref) if rel_ref else None)
        if not naam:
            continue
        last_subject_naam = naam
        findings.append({"naam": naam, "field": "geboortedag", "value": int(d), "raw": m.group(0)})
        findings.append({"naam": naam, "field": "geboortemaand", "value": int(maand), "raw": m.group(0)})

    # "mijn [relatie] is op DD MAAND YYYY geboren"
    for m in PAT_REL_BIRTHDATE.finditer(text):
        rel_ref = m.group(1)
        d, maand_word, y = m.group(2), m.group(3).lower(), m.group(4)
        maand = MAANDEN.get(maand_word)
        if not maand:
            continue
        naam = _resolve_relation_ref(user_id, rel_ref) if rel_ref else None
        if not naam:
            continue
        try:
            iso = f"{int(y):04d}-{int(maand):02d}-{int(d):02d}"
            datetime.strptime(iso, "%Y-%m-%d")
            last_subject_naam = naam
            findings.append({"naam": naam, "field": "geboortedatum", "value": iso, "raw": m.group(0)})
        except ValueError:
            continue

    # "mijn [relatie] is N jaar"
    for m in PAT_REL_AGE.finditer(text):
        rel_ref = m.group(1)
        leeftijd = int(m.group(2))
        naam = _resolve_relation_ref(user_id, rel_ref) if rel_ref else None
        if naam and 0 <= leeftijd <= 130:
            last_subject_naam = naam
            findings.append({"naam": naam, "field": "leeftijd", "value": leeftijd, "raw": m.group(0)})

    # "mijn [relatie] woont in PLAATS"
    for m in PAT_REL_WOONT.finditer(text):
        rel_ref = m.group(1)
        plaats = m.group(2).strip().rstrip(",.;")
        naam = _resolve_relation_ref(user_id, rel_ref) if rel_ref else None
        if naam:
            last_subject_naam = naam
            findings.append({"naam": naam, "field": "woonplaats", "value": plaats, "raw": m.group(0)})

    # === Pronoun "zij/hij is N" — refereert naar last_subject_naam ===
    for m in PAT_PRONOUN_AGE.finditer(text):
        leeftijd = int(m.group(1))
        if last_subject_naam and 0 <= leeftijd <= 130:
            findings.append({"naam": last_subject_naam, "field": "leeftijd",
                             "value": leeftijd, "raw": m.group(0),
                             "resolved_from_pronoun": True})

    # === v6_personalia_bezittingen_001 — bezittingen ===
    for m in PAT_BEZIT.finditer(text):
        naam = m.group(1).strip()
        ding = m.group(2).strip().lower()
        if ding and ding not in _BEZIT_BLACKLIST and len(ding) >= 3:
            findings.append({"naam": naam, "field": "bezittingen", "value": ding,
                             "raw": m.group(0), "list_append": True})
            last_subject_naam = naam

    for m in PAT_REL_BEZIT.finditer(text):
        rel_ref = m.group(1)
        ding = m.group(2).strip().lower()
        if not ding or ding in _BEZIT_BLACKLIST or len(ding) < 3:
            continue
        naam = _resolve_relation_ref(user_id, rel_ref) if rel_ref else None
        if naam:
            findings.append({"naam": naam, "field": "bezittingen", "value": ding,
                             "raw": m.group(0), "list_append": True})
            last_subject_naam = naam

    # === v6_personalia_interest_001 — interesses ===
    for m in PAT_INTEREST.finditer(text):
        naam = m.group(1).strip()
        ding = m.group(2).strip().lower()
        if ding and len(ding) >= 3:
            findings.append({"naam": naam, "field": "interesses", "value": ding,
                             "raw": m.group(0), "list_append": True})
            last_subject_naam = naam

    for m in PAT_REL_INTEREST.finditer(text):
        rel_ref = m.group(1)
        ding = m.group(2).strip().lower()
        if not ding or len(ding) < 3:
            continue
        naam = _resolve_relation_ref(user_id, rel_ref) if rel_ref else None
        if naam:
            findings.append({"naam": naam, "field": "interesses", "value": ding,
                             "raw": m.group(0), "list_append": True})
            last_subject_naam = naam

    # v6_personalia_continuation_001 — Match "... en heeft Y" / "... en is gek op Y"
    # waarbij subject impliciet de voorgaande naam is.
    if last_subject_naam:
        for m in PAT_AND_BEZIT.finditer(text):
            ding = m.group(1).strip().lower()
            if ding and ding not in _BEZIT_BLACKLIST and len(ding) >= 3:
                findings.append({"naam": last_subject_naam, "field": "bezittingen", "value": ding,
                                 "raw": m.group(0), "list_append": True, "resolved_from_pronoun": True})
        for m in PAT_AND_INTEREST.finditer(text):
            ding = m.group(1).strip().lower()
            if ding and len(ding) >= 3:
                findings.append({"naam": last_subject_naam, "field": "interesses", "value": ding,
                                 "raw": m.group(0), "list_append": True, "resolved_from_pronoun": True})

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
                    parts = value.split("-")
                    p["geboortejaar"] = int(parts[0])
                    p["geboortemaand"] = int(parts[1])
                    p["geboortedag"] = int(parts[2])
                except (ValueError, IndexError):
                    pass
                p["updated_at"] = _now()
                applied.append({"person_id": p.get("id"), "naam": p.get("naam"),
                                "field": "geboortedatum", "value": value})
            elif field in ("geboortedag", "geboortemaand"):
                if current == value:
                    continue
                p[field] = int(value)
                p["updated_at"] = _now()
                applied.append({"person_id": p.get("id"), "naam": p.get("naam"),
                                "field": field, "value": value})
            else:
                # generieke string-velden + list-velden (bezittingen/interesses)
                is_list = f.get("list_append")
                if is_list:
                    cur_list = p.get(field) or []
                    if not isinstance(cur_list, list):
                        cur_list = [cur_list] if cur_list else []
                    if value in cur_list:
                        continue
                    cur_list.append(value)
                    p[field] = cur_list
                    p["updated_at"] = _now()
                    applied.append({"person_id": p.get("id"), "naam": p.get("naam"),
                                    "field": field, "value": value, "appended": True})
                else:
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
    findings = extract_personalia(text, user_id=user_id)
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
        elif field == "bezittingen":
            parts.append(f"**{naam}** heeft een {val}")
        elif field == "interesses":
            parts.append(f"**{naam}** houdt van {val}")
        elif field == "geboortedag":
            parts.append(f"**{naam}** jarig op dag {val}")
        elif field == "geboortemaand":
            mnd = ["", "jan","feb","mrt","apr","mei","jun","jul","aug","sep","okt","nov","dec"]
            parts.append(f"**{naam}** maand {mnd[int(val)] if 1<=int(val)<=12 else val}")
        else:
            parts.append(f"**{naam}** {field}: {val}")
    return "📝 Genoteerd: " + " · ".join(parts) + "."
