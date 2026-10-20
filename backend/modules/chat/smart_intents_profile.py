"""v6_smart_intents_split_001 — Profile/Relation/Age lookup intents.

Uit smart_intents_service.py geëxtraheerd om dat bestand onder ~800 regels te krijgen.
Bevat: my_relation_lookup, age_lookup, profile_lookup.

Backwards-compat: smart_intents_service.py re-exporteert alle public funcs.
"""
import re
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional

from modules.core.storage import load_json

DATA_ROOT = Path(__file__).parent.parent.parent / "data"


# ============== PROFILE LOOKUP INTENT (v6_profile_lookup_001 - 28 mei) ==============
# ============== v6_my_relation_lookup_001 — "Wie is/zijn mijn X" ==============
# Vragen als "Wie is mijn zus?", "Wie zijn mijn dochters?", "Wie is mijn vader"
# Antwoorden direct vanuit /persons/{user_id}_relationships.json — geen KB-cards.

from .relation_extraction_service import REL_TYPES as _REL_TYPES, REL_KEYS_SORTED as _REL_KEYS

# Plural forms → singular relation key. NB: REL_TYPES heeft o.a. "zus", "broer", "neef" etc.
_REL_PLURALS = {
    "zussen": "zus", "broers": "broer", "broertjes": "broer", "zusjes": "zus",
    "moeders": "moeder", "vaders": "vader",
    "dochters": "dochter", "zonen": "zoon", "kinderen": "kind",
    "vrienden": "vriend", "vriendinnen": "vriendin",
    "collegas": "collega", "collega's": "collega",
    "neven": "neef", "nichten": "nicht", "neefjes": "neef", "nichtjes": "nicht",
    "tantes": "tante", "ooms": "oom",
    "schoonzussen": "schoonzus", "schoonbroers": "schoonbroer",
    "schoonzonen": "schoonzoon", "schoondochters": "schoondochter",
    "oma's": "oma", "opa's": "opa", "omas": "oma", "opas": "opa",
}

# Alle herkende termen (singular + plural)
_ALL_REL_TERMS = sorted(
    list(_REL_KEYS) + list(_REL_PLURALS.keys()),
    key=len, reverse=True
)
_MY_REL_PATTERN = re.compile(
    rf"\bwie\s+(?:is|zijn)\s+mijn\s+({'|'.join(re.escape(k) for k in _ALL_REL_TERMS)})\b",
    re.IGNORECASE,
)


def detect_my_relation_lookup(text: str) -> Optional[str]:
    """Returnt de relatie-term (genormaliseerd, lowercase, singular) als 'Wie is mijn X' matcht."""
    if not text:
        return None
    m = _MY_REL_PATTERN.search(text)
    if not m:
        return None
    term = m.group(1).lower()
    # Normalize plurals
    return _REL_PLURALS.get(term, term)


def handle_my_relation_lookup(user_id: str, rel_term: str) -> Dict:
    """Vraagt persons-graaf op en geeft alle personen terug die op deze relatie matchen."""
    rel_type = _REL_TYPES.get(rel_term, rel_term)
    # rel_type kan bv. "familie/zus" zijn
    base_type = rel_type.split("/")[-1]  # "zus", "moeder", etc.

    REL_FILE = DATA_ROOT / "persons" / f"{user_id}_relationships.json"
    if not REL_FILE.exists():
        return {
            "type": "my_relation_lookup",
            "message": f"Ik heb geen relaties van jou opgeslagen. Vertel me eens over je {rel_term}? Dan onthoud ik het.",
            "matched_rel": rel_term,
            "found": [],
        }

    rel_data = load_json(REL_FILE, default={"relationships": []})
    rels = rel_data.get("relationships", []) if isinstance(rel_data, dict) else rel_data

    matches = []
    for r in rels:
        rt = (r.get("relation_type") or "").lower()
        # Match: exact "familie/zus" of suffix-match (laatste deel = "zus")
        if rt == rel_type.lower() or rt.endswith(f"/{base_type}") or rt == base_type:
            matches.append(r)

    if not matches:
        return {
            "type": "my_relation_lookup",
            "message": f"Ik weet (nog) niet wie jouw {rel_term} is. Vertel het me — bv. '\\<naam\\> is mijn {rel_term}' — dan onthoud ik het.",
            "matched_rel": rel_term,
            "found": [],
        }

    namen = [r.get("person_name") for r in matches if r.get("person_name")]
    # Mooie taal
    if len(namen) == 1:
        n = namen[0]
        notes = (matches[0].get("notes") or "").strip()
        extra = f"\n\n_{notes}_" if notes and not notes.startswith("Auto-detected") else ""
        msg = f"Jouw **{rel_term}** is **{n}**.{extra}"
    else:
        bulleted = "\n".join(f"- **{n}**" for n in namen)
        msg = f"Jouw **{rel_term}**:\n{bulleted}"
    return {
        "type": "my_relation_lookup",
        "message": msg,
        "matched_rel": rel_term,
        "found": namen,
    }


# ============== v6_age_lookup_001 — "Hoe oud is X" ==============
# Twee patronen: naam OF "mijn relatie"
_REL_REF_AGE = "(?:mijn\\s+(?:moeder|vader|ma|mama|pa|papa|zus|zusje|broer|broertje|oma|opa|"
_REL_REF_AGE += "dochter|zoon|man|vrouw|partner|tante|oom|neef|nicht|nichtje|neefje|"
_REL_REF_AGE += "schoonmoeder|schoonvader|schoonzus|schoonbroer))"
_AGE_PATTERN = re.compile(
    rf"\bhoe\s+oud\s+is\s+(?:([A-Z][a-zà-ÿ]+(?:[\s\-]+[A-Z][a-zà-ÿ]+){{0,2}})|({_REL_REF_AGE}))\b",
    re.IGNORECASE,
)


def detect_age_lookup(text: str, user_id: str) -> Optional[Dict]:
    """Returns response dict als 'Hoe oud is X' kan worden beantwoord via persons-card."""
    if not text:
        return None
    m = _AGE_PATTERN.search(text)
    if not m:
        return None
    naam_direct = m.group(1)
    rel_ref = m.group(2)
    # v6 fix: re.IGNORECASE laat [A-Z] ook lowercase matchen, dus "mijn moeder" kan in
    # de naam-slot belanden. Detecteer dit en map terug naar rel_ref.
    if naam_direct and naam_direct.lower().startswith("mijn "):
        rel_ref = naam_direct
        naam_direct = None
    # Resolve "mijn moeder" → echte naam
    if rel_ref and not naam_direct:
        try:
            from .personalia_extraction_service import _resolve_relation_ref
            naam_query = _resolve_relation_ref(user_id, rel_ref)
            if not naam_query:
                return {
                    "type": "age_lookup",
                    "message": f"Ik weet (nog) niet wie jouw {rel_ref.replace('mijn ','')} is. Vertel het me eerst.",
                }
        except Exception:
            naam_query = rel_ref
    else:
        naam_query = (naam_direct or "").strip()
    if not naam_query:
        return None
    pf = DATA_ROOT / "persons" / f"{user_id}.json"
    if not pf.exists():
        return {
            "type": "age_lookup",
            "message": f"Ik weet niet wie {naam_query} is — vertel eerst hoe je hem/haar kent.",
        }
    pd = load_json(pf, default={"persons": []})
    persons = pd.get("persons", [])
    q = naam_query.lower()
    matches = []
    for p in persons:
        cand = (p.get("volledige_naam") or p.get("naam") or "").lower()
        if not cand:
            continue
        if cand == q or q in cand.split() or q in cand:
            matches.append(p)
    if not matches:
        return {
            "type": "age_lookup",
            "message": f"Ik ken **{naam_query}** nog niet als persoon. Vertel hoe je elkaar kent of wanneer hij/zij geboren is.",
        }
    # Take best match (highest gradatie / first)
    p = matches[0]
    gd = p.get("geboortedatum")
    gj = p.get("geboortejaar")
    g_dag = p.get("geboortedag")
    g_maand = p.get("geboortemaand")
    # Compose ISO datum als alle 3 delen aanwezig (auto-fill)
    if not gd and gj and g_maand and g_dag:
        gd = f"{int(gj):04d}-{int(g_maand):02d}-{int(g_dag):02d}"
    if gd:
        try:
            d = datetime.strptime(gd, "%Y-%m-%d")
            today = datetime.now()
            age = today.year - d.year - ((today.month, today.day) < (d.month, d.day))
            verjaardag = d.strftime("%d %B").replace("January", "januari").replace("February", "februari").replace("March", "maart").replace("April", "april").replace("May", "mei").replace("June", "juni").replace("July", "juli").replace("August", "augustus").replace("September", "september").replace("October", "oktober").replace("November", "november").replace("December", "december")
            return {
                "type": "age_lookup",
                "message": f"**{p.get('naam') or naam_query}** is **{age} jaar** (geboren op {verjaardag} {d.year}).",
            }
        except ValueError:
            pass
    if gj:
        approx = datetime.now().year - int(gj)
        extra = ""
        if g_dag and g_maand:
            # Toon ook verjaardag-datum zonder jaar
            mnd_namen = ["", "januari","februari","maart","april","mei","juni","juli","augustus","september","oktober","november","december"]
            extra = f" Verjaardag op **{int(g_dag)} {mnd_namen[int(g_maand)]}**."
        elif g_dag or g_maand:
            extra = " (geboortedatum nog niet compleet)"
        return {
            "type": "age_lookup",
            "message": f"**{p.get('naam') or naam_query}** is ongeveer **{approx} jaar** (geboren in {gj}).{extra}",
        }
    if g_dag and g_maand:
        mnd_namen = ["", "januari","februari","maart","april","mei","juni","juli","augustus","september","oktober","november","december"]
        return {
            "type": "age_lookup",
            "message": f"**{p.get('naam') or naam_query}** is jarig op **{int(g_dag)} {mnd_namen[int(g_maand)]}**, maar het geboortejaar heb ik nog niet — vertel eens?",
        }
    return {
        "type": "age_lookup",
        "message": f"Ik ken **{p.get('naam') or naam_query}**, maar geen geboortedatum. Vertel eens — bv. '{p.get('naam')} is 11 februari 2009 geboren'.",
    }


# Spark beantwoordt vragen over personen: "wie is Marieke?", "wat is Willems achternaam?"
# Privacy-gate: alleen users in vriendelijke graaf van vrager, óf publieke users (gradatie ≤ 4).

_PROFILE_PATTERNS = [
    r"\bwie is\s+([A-ZÀ-ŸÄ-Üa-zà-ÿä-ü][\w\- ']{1,30})\??",
    # v13c_wie_is_natural_001 (sessie 54) — Willem: "weet jij wie Emmy is" leidde
    # tot LLM-hallucinatie omdat pattern alleen 'wie is X' snapt, niet
    # 'weet jij wie X is' (X staat vóór 'is' i.p.v. erna).
    r"\bweet\s+(?:jij|je|spark)\s+wie\s+([A-ZÀ-ŸÄ-Üa-zà-ÿä-ü][\w\- ']{1,30})\s+is\??",
    r"\b(?:weet|kent)\s+(?:jij|je|spark)\s+([A-ZÀ-ŸÄ-Üa-zà-ÿä-ü][\w\- ']{1,30})\??\s*$",
    # v6_profile_wat_weet_001 — "wat weet jij/je over X"
    r"\bwat\s+weet\s+(?:jij|je)\s+over\s+([A-ZÀ-ŸÄ-Üa-zà-ÿä-ü][\w\- ']{1,30})\??",
    r"\bwat\s+weet\s+ik\s+over\s+([A-ZÀ-ŸÄ-Üa-zà-ÿä-ü][\w\- ']{1,30})\??",
    # "wat is X achternaam" / "wat is Willems achternaam"
    r"\b(wat|hoe)(\s+is)?\s+([A-ZÀ-Ÿa-zà-ÿ][\w\- ']{1,30})['\u2019]?s?\s+(achternaam|email|telefoon|leeftijd|geboortedatum|rang|gradatie)\??",
    # "wat is de achternaam van X"
    r"\b(wat|hoe)(\s+is)?(\s+(?:de\s+|haar\s+|zijn\s+))?(achternaam|email|telefoon|leeftijd|geboortedatum|rang|gradatie)\s+van\s+([A-ZÀ-Ÿa-zà-ÿ][\w\- ']{1,30})\??",
    r"\bvertel\s+(eens\s+)?over\s+([A-ZÀ-Ÿa-zà-ÿ][\w\- ']{1,30})\b",
    r"\bken\s+je\s+([A-ZÀ-Ÿa-zà-ÿ][\w\- ']{1,30})\??",
]


def _users_data():
    USERS_FILE = DATA_ROOT / "system" / "users.json"
    d = load_json(USERS_FILE, default={"users": []})
    return d.get("users", []) if isinstance(d, dict) else d


def _resolve_person(name_query: str, viewer_id: str):
    """Find person by name. Privacy-rules:
    - Owner profielen (gradatie ≤ 2) altijd zichtbaar
    - Viewer's eigen profiel altijd zichtbaar
    - Andere users alleen als ze in viewer's relationships staan
    - v6_persons_card_lookup_001 — Persons cards (alleen in viewer's eigen graaf)
      worden óók doorzocht zodat "Wie is Lotus" met Lotus uit relaties werkt.
    """
    q = (name_query or "").strip().lower()
    if not q:
        return None, "no_name"

    # 1. Zoek in system users
    users = _users_data()
    matches = []
    for u in users:
        if not isinstance(u, dict):
            continue
        full = (u.get("naam") or u.get("name") or "").lower()
        if not full:
            continue
        if q == full or q in full.split() or q in full:
            matches.append(u)

    # 2. v6_persons_card_lookup_001 — Persons cards van viewer (eigen relatie-graaf)
    if viewer_id:
        pf = DATA_ROOT / "persons" / f"{viewer_id}.json"
        if pf.exists():
            pd = load_json(pf, default={"persons": []})
            for p in pd.get("persons", []):
                full = (p.get("volledige_naam") or p.get("naam") or "").lower()
                if not full:
                    continue
                if q == full or q in full.split() or q in full:
                    # Wrap als pseudo-user met _source marker
                    matches.append({
                        "id": p.get("id"),
                        "naam": p.get("naam"),
                        "volledige_naam": p.get("volledige_naam"),
                        "gradatie": p.get("gradatie", 5),
                        "_persons_card": p,
                        "_source": "persons_card",
                    })

    if not matches:
        return None, "not_found"
    if len(matches) > 1:
        # v6_persons_card_lookup_001 — dedup: persons_card heeft voorrang als de naam
        # uniek matcht binnen viewer's eigen graaf, want viewer kent zijn eigen persoon-kaart.
        # Selecteer de meest-complete persons_card (met meeste velden ingevuld).
        own_cards = [m for m in matches if m.get("_source") == "persons_card"]
        # v14_rel_dedupe_001 (Willem 20-10: "Joy, Joy, Joy Spakman") — "Joy" en "Joy Spakman" met dezelfde relatie
        # zijn één persoon: houd de volledigste naam.
        def _nm(m): return ((m.get("volledige_naam") or m.get("naam") or "")).strip().lower()
        def _rel(m): return ((m.get("_persons_card") or {}).get("relatie") or "").lower()
        samengevoegd = []
        for m in sorted(own_cards, key=lambda x: -len(_nm(x))):
            if any(_nm(m) and _nm(m) != _nm(o) and _nm(o).startswith(_nm(m).split()[0]) and _rel(m) == _rel(o) for o in samengevoegd):
                continue
            if any(_nm(m) == _nm(o) for o in samengevoegd):
                continue
            samengevoegd.append(m)
        own_cards = samengevoegd
        if own_cards:
            # Score op aantal info-velden
            def _score(m):
                pc = m.get("_persons_card", {}) or {}
                fields = ("geboortedatum","geboortejaar","woonplaats","beroep","bezittingen","interesses","relatie")
                return sum(1 for f in fields if pc.get(f))
            own_cards.sort(key=_score, reverse=True)
            # Kies de top als er een duidelijke winnaar is
            if len(own_cards) == 1 or _score(own_cards[0]) > _score(own_cards[1]):
                return own_cards[0], "ok"
        return matches, "ambiguous"
    person = matches[0]
    # Persons-cards uit user's eigen graaf zijn ALTIJD toegankelijk voor die user
    if person.get("_source") == "persons_card":
        return person, "ok"
    # v13c_admin_profile_bypass_001 (sessie 54) — admins (grad 1) mogen alle
    # user-profielen zien. Anders zegt Spark 'Emmy staat niet in jouw graaf'
    # tegen zijn eigen maker.
    try:
        viewer = next((u for u in _users_data()
                       if isinstance(u, dict) and u.get("id") == viewer_id), None)
        if viewer and int(viewer.get("gradatie", 7) or 7) == 1:
            return person, "ok"
    except Exception:
        pass
    grad = int(person.get("gradatie", 7) or 7)
    if grad <= 2 or person.get("id") == viewer_id:
        return person, "ok"
    REL_FILE = DATA_ROOT / "persons" / f"{viewer_id}_relationships.json"
    if REL_FILE.exists():
        rel_data = load_json(REL_FILE, default={"relationships": []})
        rels = rel_data.get("relationships", []) if isinstance(rel_data, dict) else rel_data
        for r in rels:
            if r.get("user_id") == person.get("id") or r.get("naam","").lower() == (person.get("naam") or "").lower():
                return person, "ok"
    return person, "no_access"


def detect_profile_lookup(text: str, viewer_id: str = "") -> Optional[Dict]:
    """Detecteert vragen als 'wie is Marieke?' of 'wat is Willems achternaam?'.
    Returns dict {type, message, person?} of None.
    """
    if not text or len(text) < 6:
        return None
    t = text.strip()
    name_query = None
    field = None
    for pat in _PROFILE_PATTERNS:
        m = re.search(pat, t, re.IGNORECASE)
        if not m:
            continue
        groups = m.groups()
        # Patroon "wat is Willems achternaam" → groups = (wat, is, willems, achternaam)
        if len(groups) == 4 and groups[3] and groups[3].lower() in ("achternaam","email","telefoon","leeftijd","geboortedatum","rang","gradatie"):
            name_query = (groups[2] or "").strip().rstrip("'\u2019s")
            field = groups[3].lower()
        # Patroon "wat is de achternaam van X" (5 groups)
        elif len(groups) >= 5 and groups[3] and groups[4]:
            field = (groups[3] or "").strip().lower()
            name_query = (groups[4] or "").strip()
        else:
            name_query = (groups[-1] or "").strip()
        break
    if not name_query:
        return None

    # Cleanup: remove trailing ?, leading "een/de"
    name_query = re.sub(r"^(een|de|het|die|dat)\s+", "", name_query, flags=re.I).strip("?., ")
    if not name_query or name_query.lower() in ("dat", "die", "het", "ik", "jij", "je"):
        return None

    person, status = _resolve_person(name_query, viewer_id)
    if status == "not_found":
        return {"type": "profile_lookup", "message": f"Ik ken geen '{name_query}' in mijn registers. Ben je zeker van de naam?"}
    if status == "ambiguous":
        names = ", ".join(p.get("naam") or p.get("name") or "?" for p in person[:5])
        return {"type": "profile_lookup_ambiguous", "message": f"Welke '{name_query}' bedoel je? Ik vind: {names}."}
    if status == "no_access":
        return {"type": "profile_lookup_denied", "message": f"Ik weet wel wie {person.get('naam', name_query)} is, maar deze persoon staat niet in jouw vrienden-graaf. Ik deel hun info alleen met vrienden."}

    # status == ok → bouw antwoord
    # v6_persons_card_lookup_001 — Als persons-card hit, gebruik die info
    if person.get("_source") == "persons_card":
        pc = person.get("_persons_card", {})
        naam = pc.get("volledige_naam") or pc.get("naam") or "?"
        rel = pc.get("relatie") or "—"
        sources = pc.get("_fact_sources") or {}

        def _marker(field: str, val=None):
            """Geef ' (?)' terug als fact niet bevestigd is door target-user zelf."""
            if val is not None:
                s = (sources.get(field) or {}).get(val) if isinstance(sources.get(field), dict) and val in (sources.get(field) or {}) else None
            else:
                s = sources.get(field)
            if s and isinstance(s, dict) and not s.get("verified"):
                return " ⚠️"
            return ""

        parts = [f"**{naam}**"]
        if rel and rel != "—":
            parts.append(f"jouw **{rel}**")
        info_bits = []
        if pc.get("geboortedatum"):
            try:
                from datetime import datetime
                d = datetime.strptime(pc["geboortedatum"], "%Y-%m-%d")
                today = datetime.now()
                age = today.year - d.year - ((today.month, today.day) < (d.month, d.day))
                info_bits.append(f"{age} jaar{_marker('geboortedatum')}")
            except ValueError:
                pass
        elif pc.get("geboortejaar"):
            try:
                from datetime import datetime
                age = datetime.now().year - int(pc["geboortejaar"])
                info_bits.append(f"~{age} jaar{_marker('geboortejaar')}")
            except (ValueError, TypeError):
                pass
        if pc.get("woonplaats"):
            info_bits.append(f"woont in {pc['woonplaats']}{_marker('woonplaats')}")
        if pc.get("beroep"):
            info_bits.append(f"werkt als {pc['beroep']}{_marker('beroep')}")
        bezit = pc.get("bezittingen") or []
        if bezit:
            shown = []
            for b in bezit[:5]:
                shown.append(f"{b}{_marker('bezittingen', b)}")
            info_bits.append(f"heeft: {', '.join(shown)}")
        interesses = pc.get("interesses") or []
        if interesses:
            shown = []
            for i in interesses[:5]:
                shown.append(f"{i}{_marker('interesses', i)}")
            info_bits.append(f"interesses: {', '.join(shown)}")
        msg = " is ".join(parts) + ("." if not info_bits else " — " + " · ".join(info_bits) + ".")
        # Verificatie-disclaimer als er ⚠️ in zit
        if "⚠️" in msg:
            msg += "\n\n_⚠️ = nog niet door {naam} zelf bevestigd. Spark kan het hem/haar later vragen._".replace("{naam}", naam.split()[0])
        return {
            "type": "profile_lookup",
            "person_id": pc.get("id"),
            "message": msg,
        }

    naam = person.get("naam") or person.get("name") or "?"
    rang = person.get("rang") or person.get("rank") or "—"
    grad = person.get("gradatie", "?")
    if field:
        # Specifiek veld vragen
        value = None
        if field in ("achternaam",):
            parts = naam.split()
            value = parts[-1] if len(parts) > 1 else "(alleen voornaam bekend)"
        elif field in ("email",):
            value = person.get("email") or "(niet ingevuld)"
        elif field in ("telefoon",):
            value = person.get("telefoon") or person.get("phone") or "(niet ingevuld)"
        elif field in ("leeftijd", "geboortedatum"):
            value = person.get("geboortedatum") or person.get("leeftijd") or "(niet ingevuld)"
        else:
            value = person.get(field) or "(niet ingevuld)"
        return {
            "type": "profile_lookup",
            "person_id": person.get("id"),
            "message": f"**{naam}** — {field}: {value}",
        }

    # Algemeen profiel
    return {
        "type": "profile_lookup",
        "person_id": person.get("id"),
        "message": (
            f"**{naam}** (gradatie {grad}, rang {rang}). "
            f"{'Admin / oprichter.' if int(grad)<=2 else 'Lid van het Spark Core platform.'}"
        ),
    }

