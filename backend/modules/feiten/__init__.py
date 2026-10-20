"""
v14_feiten_archief_001 (Willem 20-10) — Feiten-archief in KB-kaart-formaat.

Vier soorten: `mening` (persoonlijk, nooit waar/onwaar), `waarde` (normen & waarden), `overtuiging` (geloof /
levensbeschouwing — "hun bijbel", iets anders dan normen & waarden; Willem 20-10) en `feit` (toetsbaar: ongetoetst →
getoetst / verworpen door admin). Per user in users/{uid}/feiten.json; algemene Spark-feiten (wijsheid) in data/feiten/spark.json.
Alleen admin ziet het (Beheer → Instellingen → Feiten) — "soms willen mensen dingen niet weten over zichzelf".
Feit wint van LLM: "wat weet je van mij / wat vind ik van X" → antwoord uit kaarten, met bron.
Geen W-vervolgvraag (Willem: "kan niet altijd natuurlijk, laat maar weg").
"""
from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from modules.core.storage import load_json, save_json

router = APIRouter(prefix="/feiten", tags=["feiten"])
DATA_DIR = Path(__file__).parent.parent.parent / "data"
SPARK_FILE = DATA_DIR / "feiten" / "spark.json"

# identity_facts-triggers → soort
MENING_TRIGGERS = {"i_love", "my_hobby", "user_calls_spark", "user_views_spark_as", "spark_is_to_user", "we_are_together",
                   "spark_carries", "spark_feels_like", "spark_part_of", "user_proposes_spark", "user_worldview", "user_creates_spark"}
TRIGGER_BEGRIP = {"i_am": "ik ben", "i_work_as": "werk", "i_have": "ik heb", "i_love": "houdt van", "my_hobby": "hobby",
                  "i_live_in": "woonplaats", "my_name": "naam", "user_calls_spark": "Spark is voor mij",
                  "user_views_spark_as": "ik zie Spark als", "spark_is_to_user": "Spark is voor mij", "we_are_together": "wij zijn",
                  "user_worldview": "wereldbeeld"}

# Extra patronen (meningen/gevoelens + droge feiten) bovenop identity_facts
_MENING = [
    (r"\bik\s+vind\s+(?:dat\s+)?([^\.,!?\n]{3,80})", "ik vind"),
    (r"\bik\s+(?:geloof|denk)\s+(?:dat\s+)?([^\.,!?\n]{3,80})", "ik geloof"),
    (r"\bik\s+(?:haat|verafschuw)\s+([^\.,!?\n]{3,60})", "ik haat"),
    (r"\bmijn\s+favoriete\s+([^\.,!?\n]{3,60})", "favoriet"),
    (r"\bik\s+ben\s+(?:gek|dol)\s+op\s+([^\.,!?\n]{3,60})", "gek op"),
]
# Overtuiging — geloof / levensbeschouwing. "ik geloof in X" is overtuiging als X levensbeschouwelijk is, anders waarde.
_LEVENSBESCHOUWING = re.compile(r"\b(god|allah|jezus|christus|bijbel|koran|thora|kerk|moskee|synagoge|boeddha|hemel|hel|karma|re[ïi]ncarnatie|wedergeboorte|universum|energie[ëe]n?|ziel|zielen|geesten?|engelen?|spiritu\w*|atheïst|atheist|humanist|gelovig|christen|christelijk|moslim|islam\w*|joods|jood|hindoe\w*|boeddhis\w*|heiden\w*|wicca|natuur\s*geloof|het\s+lot|voorbestemd|schepper|leven\s+na\s+de\s+dood|hogere\s+macht|gebed|bidden|bid)\b", re.I)
_OVERTUIGING = [
    (r"\bik\s+geloof\s+(?:niet\s+)?in\s+([^\.,!?\n]{3,60})", "ik geloof in"),
    (r"\bik\s+ben\s+((?:niet\s+)?(?:gelovig|christen|christelijk|moslim|joods|hindoe|boeddhist|atheïst|atheist|humanist|spiritueel|heidens|katholiek|protestant|gereformeerd)[^\.,!?\n]{0,40})", "levensbeschouwing"),
    (r"\b(?:volgens|in)\s+(?:mijn\s+geloof|de\s+bijbel|de\s+koran|mijn\s+religie)\s*,?\s*([^\.,!?\n]{3,80})", "volgens mijn geloof"),
    (r"\bmijn\s+(?:geloof|religie|levensbeschouwing|overtuiging)\s+is\s+([^\.,!?\n]{3,60})", "levensbeschouwing"),
    (r"\bik\s+bid\s+([^\.,!?\n]{3,60})", "gebed"),
]

# Normen & waarden — wat iemand belangrijk vindt / waar iemand voor staat
_WAARDE = [
    (r"\bik\s+vind\s+(?:het\s+)?belangrijk\s+(?:dat\s+)?([^\.,!?\n]{3,80})", "belangrijk"),
    (r"\b(?:voor\s+mij\s+is|is\s+voor\s+mij)\s+([^\.,!?\n]{3,60})\s+(?:heel\s+|erg\s+)?belangrijk", "belangrijk"),
    (r"\b([a-zà-ÿ]{4,30})\s+(?:is|vind\s+ik)\s+(?:heel\s+|erg\s+|het\s+)?(?:belangrijk|heilig|essentieel)\b", "waarde"),
    (r"\bik\s+(?:sta|ga)\s+voor\s+([^\.,!?\n]{3,60})", "ik sta voor"),
    (r"\bik\s+geloof\s+in\s+([^\.,!?\n]{3,60})", "ik geloof in"),
    (r"\bje\s+(?:moet|hoort)\s+(?:altijd|nooit)\s+([^\.,!?\n]{3,80})", "norm"),
    (r"\bik\s+(?:doe|zeg|lieg|steel)\s+nooit\s+([^\.,!?\n]{3,60})", "norm"),
    (r"\bik\s+(?:respecteer|waardeer)\s+([^\.,!?\n]{3,60})", "respect"),
]
_FEIT = [
    (r"\bik\s+woon\s+(?:in|op|te)\s+([^\.,!?\n]{2,40})", "woonplaats"),
    (r"\bik\s+heet\s+([A-Za-zÀ-ÿ][^\.,!?\n]{1,40})", "naam"),
    (r"\bik\s+ben\s+(\d{1,3})\s+jaar", "leeftijd"),
    (r"\bik\s+heb\s+(\d+|een|twee|drie|vier)\s+(kinderen|kind|zoons?|dochters?|honden?|katten?|broers?|zussen?)\b", "gezin"),
]
_NEG = re.compile(r"\b(niet|nooit|geen)\b")


def _file(scope: str, user_id: Optional[str]) -> Path:
    return SPARK_FILE if scope == "spark" else DATA_DIR / "users" / str(user_id) / "feiten.json"


def _load(scope: str, user_id: Optional[str]) -> Dict:
    d = load_json(_file(scope, user_id), default={})
    d.setdefault("feiten", [])
    d.setdefault("_doel", "Feiten-archief in KB-kaart-formaat (v14_feiten_archief_001): mening = persoonlijk, feit = toetsbaar")
    return d


def _save(scope: str, user_id: Optional[str], d: Dict):
    save_json(_file(scope, user_id), d)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _kaart(kind: str, scope: str, user_id: Optional[str], begrip: str, wat: str, context: str, bron_type: str,
           session_id: Optional[str] = None, tags: Optional[List[str]] = None, trigger: Optional[str] = None) -> Dict:
    return {
        "id": f"feit-{uuid.uuid4().hex[:8]}", "kind": kind, "scope": scope, "user_id": user_id,
        "begrip": begrip.strip()[:60], "lagen": {"wat": wat.strip()[:200], "waarom": "", "context": context.strip()[:300]},
        "tags": sorted(set((tags or []) + [kind, begrip.lower().split()[0] if begrip else kind])),
        "status": "ongetoetst" if kind == "feit" else "bevestigd",   # mening/waarde zijn per definitie van de user zelf
        "vertrouwen": 0.5 if kind == "feit" else 0.6, "trigger": trigger,
        "bron": {"type": bron_type, "session_id": session_id, "datum": _now()},
        "created_at": _now(), "updated_at": _now(), "keer_gehoord": 1,
    }


def _dedupe_add(d: Dict, k: Dict) -> bool:
    wat_lc = k["lagen"]["wat"].lower()
    for f in d["feiten"]:
        fw = f["lagen"]["wat"].lower()
        if f["kind"] == k["kind"] and (fw == wat_lc or (len(wat_lc) > 8 and (wat_lc in fw or fw in wat_lc))):
            f["keer_gehoord"] = f.get("keer_gehoord", 1) + 1
            f["updated_at"] = _now()
            return False
    d["feiten"].append(k)
    return True


def extract_and_save(user_id: str, text: str, session_id: Optional[str] = None) -> List[Dict]:
    """Passief: haalt meningen/feiten uit een zin en slaat ze als kaart op bij de user."""
    t = (text or "").strip()
    if len(t) < 8 or user_id in (None, "", "user-000"):
        return []
    d = _load("user", user_id)
    nieuw: List[Dict] = []
    for patronen, kind in ((_OVERTUIGING, "overtuiging"), (_WAARDE, "waarde"), (_MENING, "mening"), (_FEIT, "feit")):
        for pat, begrip in patronen:
            for m in re.finditer(pat, t, re.I):
                waarde = m.group(0) if kind == "feit" and begrip == "gezin" else m.group(1)
                if kind == "overtuiging":
                    if "spark" in t.lower() and "bijbel" in t.lower():
                        continue  # Spark Bijbel = app-begrip, geen geloof
                    if begrip == "ik geloof in" and not _LEVENSBESCHOUWING.search(waarde):
                        continue  # "ik geloof in tweede kansen" → waarde
                    if "niet" in m.group(0).lower():
                        waarde = m.group(0).split(None, 1)[1] if begrip == "levensbeschouwing" else f"niet in {waarde}"
                elif _NEG.search(t[max(0, m.start() - 12):m.start()]) or len(waarde.strip()) < 2:
                    continue
                if kind == "waarde" and begrip == "ik geloof in" and _LEVENSBESCHOUWING.search(waarde):
                    continue  # al als overtuiging gepakt
                if kind == "mening" and any(n["kind"] in ("waarde", "overtuiging") and n["lagen"]["context"] == t.strip()[:300] for n in nieuw):
                    continue  # "ik vind het belangrijk dat …" / "ik geloof dat God…" is al waarde/overtuiging
                k = _kaart(kind, "user", user_id, begrip, waarde, t, "chat", session_id)
                if _dedupe_add(d, k):
                    nieuw.append(k)
    # identity_facts (bestaand) → ook als kaart, zodat het archief één plek is
    try:
        from modules.chat import identity_facts
        for f in identity_facts.extract_and_save(user_id, t, session_id=session_id):
            trig = f.get("trigger", "")
            kind = "mening" if trig in MENING_TRIGGERS else "feit"
            if any(n["kind"] == "feit" and n["lagen"]["wat"].lower() in (f.get("value") or "").lower() for n in nieuw):
                continue  # specifieker patroon (leeftijd/woonplaats) heeft dit al
            k = _kaart(kind, "user", user_id, TRIGGER_BEGRIP.get(trig, trig.replace("_", " ")), f.get("value", ""), t, "chat",
                       session_id, trigger=trig)
            if _dedupe_add(d, k):
                nieuw.append(k)
    except Exception as e:
        print(f"[feiten] identity_facts koppeling faalde: {e}")
    if nieuw or d.get("_touched"):
        _save("user", user_id, d)
    return nieuw


# ---- Feit wint van LLM --------------------------------------------------------------------------
_VRAAG_ALLES = re.compile(r"\bwat\s+weet\s+je\s+(?:allemaal\s+)?(?:van|over)\s+(?:mij|me)\b|\bwat\s+heb\s+ik\s+(?:je\s+)?(?:allemaal\s+)?verteld\b", re.I)
_VRAAG_MENING = re.compile(r"\bwat\s+vind\s+ik\s+(?:van\s+)?([^\?\.\n]{2,60})|\bwaar\s+hou(?:d)?\s+ik\s+van\b|\bwat\s+(?:vind|vond)\s+ik\s+belangrijk\b|\bwat\s+zijn\s+mijn\s+(?:normen|waarden|normen\s+en\s+waarden)\b|\bwat\s+(?:is\s+mijn\s+geloof|geloof\s+ik)\b", re.I)
_VRAAG_FEIT = re.compile(r"\b(?:wat\s+is|hoe\s+heet|waar\s+is|wie\s+is)\s+mijn\s+([^\?\.\n]{2,40})|\bweet\s+je\s+nog\s+(?:wat\s+ik\s+(?:over\s+)?)?([^\?\.\n]{2,60})\s+(?:zei|vertelde)", re.I)


def _fmt(f: Dict) -> str:
    st = "" if f["status"] in ("bevestigd", "getoetst") else " (nog niet getoetst)"
    return f"• {f['begrip']}: {f['lagen']['wat']}{st}"


def vind_antwoord(user_id: str, text: str) -> Optional[Dict]:
    t = (text or "").strip()
    if not user_id or len(t) < 8:
        return None
    feiten = [f for f in _load("user", user_id)["feiten"] if f["status"] != "verworpen"]
    if _VRAAG_ALLES.search(t):
        if not feiten:
            return {"type": "feiten_antwoord", "message": "Ik heb nog niets over je vastgelegd. Vertel gerust — wat je deelt, onthoud ik als jouw mening of als feit."}
        men = [f for f in feiten if f["kind"] == "mening"][:8]
        fei = [f for f in feiten if f["kind"] == "feit"][:8]
        waa = [f for f in feiten if f["kind"] == "waarde"][:8]
        ove = [f for f in feiten if f["kind"] == "overtuiging"][:8]
        regels = ["Dit heb ik van je onthouden:"]
        if fei: regels += ["Feiten:"] + [_fmt(f) for f in fei]
        if ove: regels += ["Jouw overtuiging:"] + [_fmt(f) for f in ove]
        if waa: regels += ["Wat jij belangrijk vindt:"] + [_fmt(f) for f in waa]
        if men: regels += ["Jouw meningen:"] + [_fmt(f) for f in men]
        regels.append(f"({len(feiten)} kaarten in totaal — uit onze gesprekken, geen LLM-gok)")
        return {"type": "feiten_antwoord", "message": "\n".join(regels), "feiten_ids": [f["id"] for f in fei + ove + waa + men]}
    m = _VRAAG_MENING.search(t) or _VRAAG_FEIT.search(t)
    if not m:
        return None
    onderwerp = next((g for g in m.groups() if g), "").strip().lower()
    woorden = {w for w in re.findall(r"[a-zà-ÿ]{3,}", onderwerp)} - {"van", "over", "mijn", "het", "een", "dat", "die"}
    hits = [f for f in feiten if woorden and (any(w in (f["lagen"]["wat"] + " " + f["begrip"] + " " + f["lagen"]["context"]).lower() for w in woorden))]
    if not hits and re.search(r"\bhou(?:d)?\s+ik\s+van", t, re.I):
        hits = [f for f in feiten if f["begrip"] in ("houdt van", "gek op", "favoriet", "hobby")]
    if not hits and re.search(r"belangrijk|normen|waarden", t, re.I):
        hits = [f for f in feiten if f["kind"] == "waarde"]
    if not hits and re.search(r"geloof|overtuiging|religie", t, re.I):
        hits = [f for f in feiten if f["kind"] == "overtuiging"]
    if not hits:
        return None
    return {"type": "feiten_antwoord", "message": "Uit wat je me eerder vertelde:\n" + "\n".join(_fmt(f) for f in hits[:5]),
            "feiten_ids": [f["id"] for f in hits[:5]]}


# ---- Admin API ----------------------------------------------------------------------------------
def _require_admin(viewer_id: str):
    from modules.core.privacy import is_admin
    if not is_admin(viewer_id):
        raise HTTPException(403, "Alleen admins")


def _alle_users() -> List[str]:
    return sorted(p.parent.name for p in (DATA_DIR / "users").glob("*/feiten.json"))


@router.get("")
async def lijst(viewer_id: str, scope: str = "user", user_id: Optional[str] = None, kind: Optional[str] = None,
                status: Optional[str] = None, q: Optional[str] = None):
    _require_admin(viewer_id)
    if scope == "spark":
        feiten = _load("spark", None)["feiten"]
    else:
        uids = [user_id] if user_id else _alle_users()
        feiten = [f for u in uids for f in _load("user", u)["feiten"]]
    if kind: feiten = [f for f in feiten if f["kind"] == kind]
    if status: feiten = [f for f in feiten if f["status"] == status]
    if q:
        ql = q.lower()
        feiten = [f for f in feiten if ql in (f["begrip"] + " " + f["lagen"]["wat"] + " " + f["lagen"]["context"] + " " + " ".join(f["tags"])).lower()]
    feiten.sort(key=lambda f: f.get("updated_at", ""), reverse=True)
    return {"success": True, "feiten": feiten, "total": len(feiten), "users": _alle_users()}


@router.get("/stats")
async def stats(viewer_id: str):
    _require_admin(viewer_id)
    per_user = {}
    tel = {"mening": 0, "waarde": 0, "overtuiging": 0, "feit": 0, "ongetoetst": 0, "getoetst": 0, "verworpen": 0, "bevestigd": 0}
    for u in _alle_users():
        fs = _load("user", u)["feiten"]
        per_user[u] = len(fs)
        for f in fs:
            tel[f["kind"]] = tel.get(f["kind"], 0) + 1
            tel[f["status"]] = tel.get(f["status"], 0) + 1
    sp = len(_load("spark", None)["feiten"])
    return {"success": True, "per_user": per_user, "spark": sp, "tellers": tel, "totaal": sum(per_user.values()) + sp}


class FeitUpdate(BaseModel):
    viewer_id: str
    scope: str = "user"
    user_id: Optional[str] = None
    status: Optional[str] = None
    wat: Optional[str] = None
    waarom: Optional[str] = None
    begrip: Optional[str] = None
    kind: Optional[str] = None
    tags: Optional[List[str]] = None


@router.put("/{feit_id}")
async def update(feit_id: str, body: FeitUpdate):
    _require_admin(body.viewer_id)
    d = _load(body.scope, body.user_id)
    f = next((x for x in d["feiten"] if x["id"] == feit_id), None)
    if not f:
        raise HTTPException(404, "Feit niet gevonden")
    if body.status:
        if body.status not in ("ongetoetst", "getoetst", "verworpen", "bevestigd"):
            raise HTTPException(400, "Onbekende status")
        f["status"] = body.status
        f["getoetst_door"] = body.viewer_id
        f["vertrouwen"] = {"getoetst": 0.9, "bevestigd": 0.8, "verworpen": 0.0}.get(body.status, 0.5)
    for k in ("wat", "waarom"):
        v = getattr(body, k)
        if v is not None: f["lagen"][k] = v.strip()[:300]
    if body.begrip is not None: f["begrip"] = body.begrip.strip()[:60]
    if body.kind in ("mening", "feit", "waarde", "overtuiging"): f["kind"] = body.kind
    if body.tags is not None: f["tags"] = sorted(set(t.strip().lower() for t in body.tags if t.strip()))
    f["updated_at"] = _now()
    _save(body.scope, body.user_id, d)
    return {"success": True, "feit": f}


class FeitCreate(BaseModel):
    viewer_id: str
    scope: str = "spark"
    user_id: Optional[str] = None
    kind: str = "feit"
    begrip: str
    wat: str
    waarom: Optional[str] = ""
    tags: Optional[List[str]] = None


@router.post("")
async def maak(body: FeitCreate):
    _require_admin(body.viewer_id)
    if body.scope == "user" and not body.user_id:
        raise HTTPException(400, "user_id nodig voor scope user")
    d = _load(body.scope, body.user_id)
    k = _kaart(body.kind, body.scope, body.user_id, body.begrip, body.wat, "", "admin", tags=body.tags)
    k["lagen"]["waarom"] = (body.waarom or "")[:300]
    k["status"] = "getoetst" if body.kind == "feit" else "bevestigd"
    k["getoetst_door"] = body.viewer_id
    d["feiten"].append(k)
    _save(body.scope, body.user_id, d)
    return {"success": True, "feit": k}


@router.delete("/{feit_id}")
async def verwijder(feit_id: str, viewer_id: str, scope: str = "user", user_id: Optional[str] = None):
    _require_admin(viewer_id)
    d = _load(scope, user_id)
    n = len(d["feiten"])
    d["feiten"] = [x for x in d["feiten"] if x["id"] != feit_id]
    if len(d["feiten"]) == n:
        raise HTTPException(404, "Feit niet gevonden")
    _save(scope, user_id, d)
    return {"success": True}


class MigreerBody(BaseModel):
    viewer_id: str


@router.post("/migreer")
async def migreer(body: MigreerBody):
    """identity_facts.json (about_user/about_spark) → feit-kaarten per user. Idempotent (dedupe op wat)."""
    _require_admin(body.viewer_id)
    stats = {"users": 0, "nieuw": 0}
    for p in (DATA_DIR / "users").glob("*/identity_facts.json"):
        uid = p.parent.name
        src = load_json(p, default={})
        d = _load("user", uid)
        stats["users"] += 1
        for key in ("about_user", "about_spark", "about_relationship"):
            for f in src.get(key, []) or []:
                trig = f.get("trigger", "")
                kind = "mening" if trig in MENING_TRIGGERS else "feit"
                k = _kaart(kind, "user", uid, TRIGGER_BEGRIP.get(trig, trig.replace("_", " ")), f.get("value", ""),
                           f.get("context", ""), "migratie_identity_facts", f.get("session_id"), trigger=trig)
                k["created_at"] = f.get("first_seen") or k["created_at"]
                k["keer_gehoord"] = f.get("count", 1)
                if _dedupe_add(d, k):
                    stats["nieuw"] += 1
        _save("user", uid, d)
    return {"success": True, "stats": stats}
