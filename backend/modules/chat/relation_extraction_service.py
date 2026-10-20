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
    # v13_roles_array_001 (sessie 53) — professionele rollen voor Zorgboerderij dossiers
    # Een persoon kan meerdere rollen tegelijk hebben (bv. vriend + cliënt).
    "cliënt": "professioneel/cliënt",
    "client": "professioneel/cliënt",
    "klant": "professioneel/klant",
    "medewerker": "professioneel/medewerker",
    "werkgever": "professioneel/werkgever",
    "begeleider": "professioneel/begeleider",
}

# Sorteer langste eerst zodat "goede vriend" matched vóór "vriend"
REL_KEYS_SORTED = sorted(REL_TYPES.keys(), key=len, reverse=True)
REL_REGEX = "|".join(re.escape(k) for k in REL_KEYS_SORTED)

# Patterns
NAAM_REGEX = r"([A-Z][a-zà-ÿ]+(?:[\s\-]+[A-Z][a-zà-ÿ]+){0,2})"  # bv. "Anneke" of "Anne Marie"

# NB: alleen "mijn" mag case-insensitive zijn, naam-regex MOET hoofdletter eisen.
# Anders worden "heeft", "werkt" etc. ook als naam-vervolg gezien.
# v13_roles_array_001: optionele adverbia ("ook", "nu", "tegenwoordig", "sinds kort")
# tussen "is" en "mijn" zodat "X is ook mijn cliënt" wél matcht (voor dual-role).
_ADV = r"(?:ook|nu|tegenwoordig|sinds\s+kort|inmiddels|ook\s+nog)?"
PATTERN_MIJN_REL_NAAM = re.compile(
    rf"\b[Mm]ijn\s+({REL_REGEX})\s+{NAAM_REGEX}\b"
)
PATTERN_NAAM_IS_MIJN = re.compile(
    rf"\b{NAAM_REGEX}\s+is\s+{_ADV}\s*[Mm]ijn\s+({REL_REGEX})\b"
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
# v6_rel_005 — "mijn [andere/tweede/derde] X heet Y" / "mijn X heet Y"
PATTERN_MIJN_REL_HEET = re.compile(
    rf"\b[Mm]ijn\s+(?:andere|tweede|derde|vierde|jongere|oudere|kleine|grote)?\s*({REL_REGEX})\s+heet\s+{NAAM_REGEX}\b"
)
# "een/m'n andere X is Y"
PATTERN_MIJN_REL_IS_NAAM = re.compile(
    rf"\b[Mm]ijn\s+(?:andere|tweede|derde|vierde|jongere|oudere|kleine|grote)?\s*({REL_REGEX})\s+is\s+{NAAM_REGEX}\b"
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
NAME_BLACKLIST = {"De", "Het", "Een", "Wat", "Hoe", "Hij", "Zij", "Mijn", "Jouw",
                  # v14_rel_dedupe_001 — toestanden zijn geen namen ("mijn moeder is Jarig")
                  "Jarig", "Ziek", "Thuis", "Weg", "Blij", "Moe", "Boos", "Druk", "Dood", "Overleden", "Oud", "Klaar",
                  "Weer", "Ook", "Nog", "Vandaag", "Morgen", "Gisteren", "Lief", "Aardig", "Er", "Hier", "Daar"}


def _rel_file(user_id: str) -> Path:
    return PERSONS_DIR / f"{user_id}_relationships.json"


def _normalize(name: str) -> str:
    return name.strip()


# v14_rel_alle_users_001 (Willem 20-10: "als ik inlog als mijn zusje worden relaties niet onthouden").
# Oorzaak: naam moest met hoofdletter én er moest een naam zijn. Nu: (a) kleine letter mag als het
# een bekende naam is (users, contacten, bel-contacten, eigen relaties), (b) relatie zonder naam
# wordt onthouden als "(naam onbekend)" en krijgt later de naam via "mijn broer heet Willem".
NAAM_ONBEKEND = "(naam onbekend)"
_LC_WOORD = r"([a-zà-ÿ][a-zà-ÿ\-]{1,})"
PATTERN_MIJN_REL_LC = re.compile(rf"\b[Mm]ijn\s+({REL_REGEX})\s+{_LC_WOORD}\b")
PATTERN_MIJN_REL_NAAMLOOS = re.compile(rf"\b[Mm]ijn\s+({REL_REGEX})\b(?!\s+(?:heet|is\s+[A-Z]|[A-Z]))")
_STOP_NA_REL = {"heeft", "is", "was", "wordt", "komt", "gaat", "zei", "heet", "en", "of", "die", "dat", "ook", "nog",
                "hier", "daar", "al", "niet", "wel", "van", "met", "bij", "in", "op", "aan", "voor", "naar", "toe"}


def _bekende_namen(user_id: Optional[str]) -> Dict[str, str]:
    """lowercase → nette schrijfwijze, uit users.json, contacten, bel-contacten en eigen relaties."""
    namen: Dict[str, str] = {}
    def put(n):
        n = (n or "").strip()
        if len(n) >= 2:
            for deel in [n] + n.split():
                namen.setdefault(deel.lower(), deel[0].upper() + deel[1:])
    try:
        for u in load_json(DATA_DIR / "system" / "users.json", default={"users": []}).get("users", []):
            put(u.get("naam"))
    except Exception:
        pass
    if user_id:
        for rel, key in ((f"users/{user_id}/contacten.json", "contacten"), (f"users/{user_id}/bel_contacts.json", "contacts")):
            try:
                d = load_json(DATA_DIR / rel, default={})
                items = d.get(key) if isinstance(d, dict) else d
                for c in items or []:
                    put(c.get("naam") or c.get("name"))
            except Exception:
                pass
        try:
            for r in load_json(_rel_file(user_id), default={"relationships": []}).get("relationships", []):
                put(r.get("person_name"))
        except Exception:
            pass
    return namen


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

    # v6_rel_005 — "mijn [andere/tweede] X heet Y" / "mijn X is Y"
    for pat in (PATTERN_MIJN_REL_HEET, PATTERN_MIJN_REL_IS_NAAM):
        for m in pat.finditer(text):
            rel_word, naam = m.group(1), m.group(2)
            add(naam, rel_word)

    # v14_rel_alle_users_001 — kleine-letter-naam alleen als bekende naam ("mijn broertje willem")
    bekend = _bekende_namen(user_id)
    for m in PATTERN_MIJN_REL_LC.finditer(text):
        rel_word, woord = m.group(1), m.group(2)
        if woord.lower() in bekend and woord.lower() not in _STOP_NA_REL:
            add(bekend[woord.lower()], rel_word)
    # relatie zonder naam ("mijn broer heeft een winkel") → placeholder, alleen als die relatie nog geen naam heeft
    gevonden_rels = {f["relation_type"] for f in findings}
    for m in PATTERN_MIJN_REL_NAAMLOOS.finditer(text):
        rel_word = m.group(1)
        rel_type = REL_TYPES.get(rel_word.lower(), rel_word.lower())
        if rel_type in gevonden_rels or rel_word.lower() in ("vriend", "vriendin", "bekende", "collega", "buurman", "buurvrouw"):
            continue
        key = (NAAM_ONBEKEND.lower(), rel_type)
        if key not in seen:
            seen.add(key)
            findings.append({"person_name": NAAM_ONBEKEND, "relation_type": rel_type,
                             "raw_relation_word": rel_word.lower(), "naam_onbekend": True})

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
    zodat de Persoonkaarten UI de relatie direct toont.

    v13_roles_array_001 (sessie 53): elke entry krijgt/behoudt een `roles: []` array.
    Als een persoon al bestaat maar met een andere role → nieuwe role wordt toegevoegd
    aan bestaande entry (i.p.v. dubbel entry). Foundation voor Zorgboerderij-dossiers
    waar iemand tegelijk vriend én cliënt kan zijn.
    """
    if not findings or not user_id:
        return []
    fp = _rel_file(user_id)
    data = load_json(fp, default={"user_id": user_id, "relationships": []})
    existing = data.get("relationships", [])

    # Migratie: zorg dat elke bestaande entry een roles-array heeft (backwards-compat)
    for r in existing:
        if "roles" not in r or not isinstance(r.get("roles"), list):
            rt = r.get("relation_type") or ""
            r["roles"] = [rt] if rt else []

    # Index op persoonsnaam (lowercase) voor role-merge
    by_name: Dict[str, Dict] = {}
    for r in existing:
        nm = (r.get("person_name") or "").strip().lower()
        if nm and nm not in by_name:
            by_name[nm] = r

    new_entries: List[Dict] = []
    role_added_entries: List[Dict] = []

    for f in findings:
        naam = f["person_name"]
        rtype = f["relation_type"]
        nm_lc = naam.strip().lower()

        # v14_rel_alle_users_001 — placeholder-logica
        placeholder = next((r for r in existing if r.get("naam_onbekend") and rtype in (r.get("roles") or [r.get("relation_type")])), None)
        if f.get("naam_onbekend"):
            if placeholder or any(rtype in (r.get("roles") or [r.get("relation_type")]) for r in existing):
                continue  # al een (naamloze of echte) relatie van dit type
        elif placeholder:
            # echte naam voor een eerder naamloze relatie → placeholder invullen
            placeholder.update({"person_name": naam, "naam_onbekend": False,
                                "updated_at": datetime.now(timezone.utc).isoformat()})
            by_name[nm_lc] = placeholder
            new_entries.append(placeholder)
            continue

        # Persoon bestaat al → check of role nieuw is
        if nm_lc in by_name:
            entry = by_name[nm_lc]
            roles = entry.setdefault("roles", [])
            if rtype in roles:
                continue  # role al bekend, skip
            roles.append(rtype)
            entry["updated_at"] = datetime.now(timezone.utc).isoformat()
            role_added_entries.append({
                "person_name": entry["person_name"],
                "added_role": rtype,
                "all_roles": list(roles),
            })
            continue

        # Nieuwe persoon
        entry = {
            "person_name": naam,
            "relation_type": rtype,
            "roles": [rtype],
            "knows_about_me": True,
            "i_know_about": True,
            "notes": f"Auto-detected uit chat ({datetime.now(timezone.utc).strftime('%Y-%m-%d')})",
            "auto_detected": True,
            "detected_at": datetime.now(timezone.utc).isoformat(),
        }
        if f.get("naam_onbekend"):
            entry["naam_onbekend"] = True
            entry["notes"] = "Relatie genoemd zonder naam — zeg bv. 'mijn broer heet …' om de naam aan te vullen"
        existing.append(entry)
        by_name[nm_lc] = entry
        new_entries.append(entry)

    if new_entries or role_added_entries:
        data["relationships"] = existing
        save_json(fp, data)
        # Sync naar persons cards file zodat UI Persoonkaarten ze toont
        try:
            _sync_persons_cards(user_id, new_entries)
        except Exception as e:
            print(f"[rel-extract] persons-card sync failed: {e}")
    return new_entries + role_added_entries


def get_roles(user_id: str, person_name: str) -> List[str]:
    """Return alle rollen die deze persoon voor de user vervult (leeg = geen relatie)."""
    if not user_id or not person_name:
        return []
    data = load_json(_rel_file(user_id), default={"relationships": []})
    nm_lc = person_name.strip().lower()
    for r in data.get("relationships", []):
        if (r.get("person_name") or "").strip().lower() == nm_lc:
            roles = r.get("roles")
            if isinstance(roles, list) and roles:
                return list(roles)
            # Fallback naar relation_type voor oude entries zonder migratie
            rt = r.get("relation_type")
            return [rt] if rt else []
    return []


def has_role(user_id: str, person_name: str, role: str) -> bool:
    """Check of een persoon een specifieke rol heeft. Role kan het volledige rel_type
    (bv. 'professioneel/cliënt') of het korte woord (bv. 'cliënt') zijn."""
    if not role:
        return False
    all_roles = get_roles(user_id, person_name)
    role_lc = role.lower().strip()
    for r in all_roles:
        if r.lower() == role_lc:
            return True
        # Match op laatste segment: 'cliënt' matcht 'professioneel/cliënt'
        tail = r.split("/")[-1].lower() if "/" in r else r.lower()
        if tail == role_lc:
            return True
    return False


def add_role(user_id: str, person_name: str, role: str) -> bool:
    """Voeg handmatig een rol toe aan een bestaande persoon. Returns True als toegevoegd,
    False als de persoon niet bestaat of de rol al aanwezig was."""
    if not (user_id and person_name and role):
        return False
    fp = _rel_file(user_id)
    data = load_json(fp, default={"relationships": []})
    nm_lc = person_name.strip().lower()
    for r in data.get("relationships", []):
        if (r.get("person_name") or "").strip().lower() == nm_lc:
            if "roles" not in r or not isinstance(r.get("roles"), list):
                rt = r.get("relation_type") or ""
                r["roles"] = [rt] if rt else []
            # Normaliseer role via REL_TYPES als het een kort woord is
            rtype = REL_TYPES.get(role.lower(), role)
            if rtype in r["roles"]:
                return False
            r["roles"].append(rtype)
            r["updated_at"] = datetime.now(timezone.utc).isoformat()
            save_json(fp, data)
            return True
    return False


def migrate_all_to_roles_array() -> Dict[str, int]:
    """One-shot migratie: voeg `roles: [relation_type]` toe aan elke entry in élk
    /persons/{uid}_relationships.json bestand dat nog geen roles-array heeft.
    Idempotent — kan meermaals veilig gedraaid worden."""
    stats = {"files": 0, "entries_migrated": 0, "entries_ok": 0}
    if not PERSONS_DIR.exists():
        return stats
    for fp in PERSONS_DIR.glob("*_relationships.json"):
        try:
            data = load_json(fp, default={"relationships": []})
        except Exception:
            continue
        rels = data.get("relationships", [])
        changed = False
        for r in rels:
            if isinstance(r.get("roles"), list) and r["roles"]:
                stats["entries_ok"] += 1
                continue
            rt = r.get("relation_type") or ""
            r["roles"] = [rt] if rt else []
            stats["entries_migrated"] += 1
            changed = True
        if changed:
            save_json(fp, data)
        stats["files"] += 1
    return stats


def _sync_persons_cards(user_id: str, new_relations: List[Dict]):
    """Maak/update person-cards in /data/persons/{user_id}.json voor elke nieuwe relatie."""
    import uuid
    new_relations = [r for r in new_relations if not r.get("naam_onbekend")]  # geen persoonskaart zonder naam
    if not new_relations:
        return
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
