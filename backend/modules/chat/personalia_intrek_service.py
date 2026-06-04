"""
v6_fact_intrek_001 — Intrek/wijzig facts over personen.

Patterns:
  "vergeet dat Gerben een hond heeft"
  "wis Gerben heeft hond"
  "Gerben heeft geen hond"
  "Gerben heeft geen werk"  → wist beroep
  "Gerben houdt niet van vissen"

v6_shadow_verification_001 — Bij intrek/wijzig wordt een shadow-question voor de
target-user (als die linked is) in de queue gezet.
"""
import re
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime, timezone

from modules.core.storage import load_json, save_json

DATA_DIR = Path(__file__).parent.parent.parent / "data"
PERSONS_DIR = DATA_DIR / "persons"
SHADOW_Q_DIR = DATA_DIR / "persons" / "shadow_questions"
SHADOW_Q_DIR.mkdir(parents=True, exist_ok=True)

NAAM_RX = r"([A-Z][a-zà-ÿ]+(?:[\s\-]+[A-Z][a-zà-ÿ]+){0,2})"

# v6_fact_intrek_001 — intrek-patronen
PAT_VERGEET_BEZIT = re.compile(
    rf"\b(?i:vergeet|wis|verwijder)(?:\s+dat)?\s+{NAAM_RX}\s+(?i:heeft|bezit)\s+(?i:een|de|het)?\s*([a-zà-ÿ][\w\-]*(?:\s+[a-zà-ÿ][\w\-]*){{0,2}}?)\s*(?:\.|,|;|$|\n)"
)
PAT_GEEN_BEZIT = re.compile(
    rf"\b{NAAM_RX}\s+(?i:heeft\s+geen|bezit\s+geen)\s+([a-zà-ÿ][\w\-]*(?:\s+[a-zà-ÿ][\w\-]*){{0,2}}?)\s*(?:\.|,|;|$|\n)"
)
PAT_NIET_HOUDT = re.compile(
    rf"\b{NAAM_RX}\s+(?i:houdt\s+niet\s+van|is\s+niet\s+gek\s+op|is\s+niet\s+dol\s+op)\s+([a-zà-ÿ][\w\-]*(?:\s+[a-zà-ÿ][\w\-]*){{0,2}}?)\s*(?:\.|,|;|$|\n)"
)
PAT_GEEN_WERK = re.compile(
    rf"\b{NAAM_RX}\s+(?i:heeft\s+(?:op\s+(?:het|dit)\s+moment\s+)?geen\s+werk|werkt\s+(?:nu\s+)?niet|is\s+werkloos)\b"
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _find_persons_by_name(user_id: str, naam: str) -> List[Dict]:
    q = (naam or "").strip().lower()
    if not q:
        return []
    pf = PERSONS_DIR / f"{user_id}.json"
    if not pf.exists():
        return []
    pd = load_json(pf, default={"persons": []})
    out = []
    for p in pd.get("persons", []):
        cand = (p.get("volledige_naam") or p.get("naam") or "").lower()
        if cand == q or q in cand.split() or q in cand:
            out.append(p)
    return out


def _queue_shadow_question(target_user_id: str, asker_id: str, person_naam: str,
                           field: str, value, action: str):
    """Plaats een shadow-vraag voor target-user die hij/zij beantwoordt bij volgende chat.
    action: 'verify' (klopt deze info?) of 'denied' (asker zei dat niet)
    """
    if not target_user_id:
        return
    fp = SHADOW_Q_DIR / f"{target_user_id}.json"
    q = load_json(fp, default={"questions": []})
    q.setdefault("questions", []).append({
        "id": f"sq-{int(datetime.now().timestamp()*1000)}",
        "asker": asker_id,
        "asker_naam": _user_naam(asker_id),
        "subject_person": person_naam,
        "field": field,
        "value": value,
        "action": action,
        "asked_at": _now(),
        "answered": False,
    })
    save_json(fp, q)


def _user_naam(user_id: str) -> str:
    USERS = DATA_DIR / "system" / "users.json"
    u = load_json(USERS, default={"users": []})
    users = u.get("users", []) if isinstance(u, dict) else u
    for x in users:
        if x.get("id") == user_id:
            return x.get("naam") or x.get("name") or user_id
    return user_id


def _remove_from_list(person: Dict, field: str, value: str) -> bool:
    """Verwijder value uit list-veld. Returns True bij wijziging."""
    lst = person.get(field) or []
    if not isinstance(lst, list):
        return False
    value_lc = value.lower().strip()
    new_lst = [x for x in lst if x.lower().strip() != value_lc]
    if len(new_lst) == len(lst):
        return False
    if new_lst:
        person[field] = new_lst
    else:
        person.pop(field, None)
    # Source ook opruimen
    src = (person.get("_fact_sources") or {}).get(field)
    if isinstance(src, dict):
        for k in list(src.keys()):
            if k.lower().strip() == value_lc:
                src.pop(k, None)
        if not src:
            (person.get("_fact_sources") or {}).pop(field, None)
    return True


def detect_and_apply_intrek(user_id: str, text: str) -> Optional[Dict]:
    """Returns dict met action-info, of None als geen intrek-statement gedetecteerd."""
    if not text or not user_id:
        return None
    actions: List[Dict] = []

    # Laad één keer en muteer in-place
    pf = PERSONS_DIR / f"{user_id}.json"
    if not pf.exists():
        return None
    pd = load_json(pf, default={"persons": []})
    all_persons = pd.get("persons", [])

    def _match(naam_q: str) -> List[Dict]:
        q = (naam_q or "").strip().lower()
        if not q:
            return []
        out = []
        for p in all_persons:
            cand = (p.get("volledige_naam") or p.get("naam") or "").lower()
            if cand == q or q in cand.split() or q in cand:
                out.append(p)
        return out

    # 1. "vergeet dat X heeft Y"
    for m in PAT_VERGEET_BEZIT.finditer(text):
        naam_q, ding = m.group(1).strip(), m.group(2).strip().lower()
        if not naam_q or not ding:
            continue
        for p in _match(naam_q):
            removed = _remove_from_list(p, "bezittingen", ding) or _remove_from_list(p, "interesses", ding)
            if removed:
                p["updated_at"] = _now()
                actions.append({"naam": p.get("naam"), "field": "bezittingen/interesses",
                                "value": ding, "removed": True})

    # 2. "X heeft geen Y"
    for m in PAT_GEEN_BEZIT.finditer(text):
        naam_q, ding = m.group(1).strip(), m.group(2).strip().lower()
        if not naam_q or not ding:
            continue
        for p in _match(naam_q):
            removed = _remove_from_list(p, "bezittingen", ding)
            if removed:
                p["updated_at"] = _now()
                actions.append({"naam": p.get("naam"), "field": "bezittingen",
                                "value": ding, "removed": True})
                if p.get("linked_user_id"):
                    _queue_shadow_question(p["linked_user_id"], user_id,
                                           p.get("naam") or naam_q, "bezittingen", ding, "denied")

    # 3. "X houdt niet van Y"
    for m in PAT_NIET_HOUDT.finditer(text):
        naam_q, ding = m.group(1).strip(), m.group(2).strip().lower()
        for p in _match(naam_q):
            removed = _remove_from_list(p, "interesses", ding)
            if removed:
                p["updated_at"] = _now()
                actions.append({"naam": p.get("naam"), "field": "interesses",
                                "value": ding, "removed": True})

    # 4. "X heeft geen werk"
    for m in PAT_GEEN_WERK.finditer(text):
        naam_q = m.group(1).strip()
        for p in _match(naam_q):
            if p.get("beroep"):
                old = p.pop("beroep")
                # Source ook
                src = (p.get("_fact_sources") or {})
                src.pop("beroep", None)
                p["updated_at"] = _now()
                actions.append({"naam": p.get("naam"), "field": "beroep",
                                "value": old, "removed": True})

    if not actions:
        return None

    save_json(pf, pd)

    bits = []
    for a in actions:
        bits.append(f"**{a['naam']}**: {a['field']}={a['value']} ✗")
    return {
        "type": "personalia_intrek",
        "message": "🗑️ Vergeten: " + ", ".join(bits) + ".",
        "actions": actions,
    }
