"""
KB v2 Routes (v5_kbv2_001)
==========================
GET  /api/kb/v2/stats                     overzicht aantallen per lade + inbox
GET  /api/kb/v2/lade/{lade}               kaarten in 1 lade (paged + search)
GET  /api/kb/v2/inbox                     kaarten in inbox (paged + filter op reden)
GET  /api/kb/v2/find?begrip=...           direct lookup via index
GET  /api/kb/v2/fallback?begrip=...       #DeWillem graceful fallback
GET  /api/kb/v2/audit                     self-audit van v2 kennis
POST /api/kb/v2/classify                  inbox → lade (met optionele edits)
POST /api/kb/v2/edit                      bewerk kaart in een lade
POST /api/kb/v2/inbox/add                 nieuwe kaart in inbox
"""
from typing import Optional, Dict, List
from fastapi import APIRouter, Query
from pydantic import BaseModel

from . import service

router = APIRouter(prefix="/kb/v2", tags=["kb-v2"])


# ---------- Models ----------

class ClassifyBody(BaseModel):
    card_id: str
    lade: str
    updates: Optional[Dict] = None
    user_id: Optional[str] = "user-000"


class EditBody(BaseModel):
    card_id: str
    lade: str
    updates: Dict
    user_id: Optional[str] = "user-000"


class InboxAddBody(BaseModel):
    begrip: str
    source: Optional[str] = "user"
    user_id: Optional[str] = "user-000"


# ---------- Read ----------

@router.get("/stats")
async def get_stats():
    return {"success": True, **service.get_stats()}


@router.get("/lade/{lade}")
async def get_lade(lade: str,
                   limit: int = Query(50, ge=1, le=500),
                   offset: int = Query(0, ge=0),
                   search: str = ""):
    r = service.list_lade(lade, limit=limit, offset=offset, search=search)
    r["success"] = "error" not in r
    return r


@router.get("/inbox")
async def get_inbox(limit: int = Query(50, ge=1, le=500),
                    offset: int = Query(0, ge=0),
                    reason: str = "",
                    search: str = ""):
    return {"success": True, **service.list_inbox(limit=limit, offset=offset, reason=reason, search=search)}


@router.get("/find")
async def find_begrip(begrip: str = Query(..., min_length=1)):
    r = service.find_by_begrip(begrip)
    if r is None:
        return {"success": False, "found": False}
    return {"success": True, "found": True, **r}


@router.get("/fallback")
async def get_fallback(begrip: str = Query(..., min_length=1)):
    """#DeWillem graceful fallback: direct hit OR neighbor OR None."""
    r = service.graceful_fallback(begrip)
    if r is None:
        return {"success": True, "found": False, "type": "none"}
    return {"success": True, "found": True, **r}


@router.get("/audit")
async def get_audit():
    return {"success": True, **service.audit()}


# ---------- Write ----------

@router.post("/classify")
async def classify(body: ClassifyBody):
    return service.classify_card(body.card_id, body.lade, updates=body.updates, user_id=body.user_id)


@router.post("/edit")
async def edit(body: EditBody):
    return service.edit_card(body.card_id, body.lade, updates=body.updates, user_id=body.user_id)


@router.post("/inbox/add")
async def inbox_add(body: InboxAddBody):
    return service.add_to_inbox(body.begrip, source=body.source, user_id=body.user_id)


# ---------- Herzien-flow (v6_kbv2_herzien_001) ----------
# Trekt 1 KB v1 kaart die nog niet gemigreerd is en presenteert hem voor
# herziening + promotion naar KB v2 lade.
import random as _random
from pathlib import Path as _Path
import json as _json
from datetime import datetime as _dt, timezone as _tz

_KB_V1_FILE = _Path(__file__).parent.parent.parent / "data" / "knowledge" / "learned_knowledge" / "knowledge_base.json"


def _load_kb_v1() -> dict:
    if not _KB_V1_FILE.exists():
        return {"knowledge_entries": []}
    return _json.loads(_KB_V1_FILE.read_text(encoding="utf-8"))


def _save_kb_v1(data: dict) -> None:
    _KB_V1_FILE.write_text(_json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


@router.get("/herzien/next")
async def herzien_next(strategy: str = "random"):
    """Trek 1 KB v1 kaart die nog niet naar v2 is gemigreerd.
    strategy: 'random' (default), 'oldest', 'unanswered_first'."""
    data = _load_kb_v1()
    all_entries = data.get("knowledge_entries") or data.get("entries") or []
    entries = [e for e in all_entries if not (e.get("migrated_to_v2") or e.get("_v2_migrated"))]
    if not entries:
        return {"success": True, "entry": None, "remaining": 0}
    if strategy == "oldest":
        entries.sort(key=lambda e: (e.get("metadata") or {}).get("created_at") or "")
    elif strategy == "unanswered_first":
        entries.sort(key=lambda e: (
            0 if not ((e.get("lagen") or {}).get("laag1") or "").strip() else 1,
            (e.get("metadata") or {}).get("created_at") or "",
        ))
    else:
        _random.shuffle(entries)
    entry = entries[0]
    return {"success": True, "entry": entry, "remaining": len(entries)}


class HerzienPromoteBody(BaseModel):
    v1_id: str
    begrip: str
    lagen: Optional[Dict] = None
    ws5: Optional[Dict] = None
    tags: Optional[List[str]] = None
    topic: Optional[str] = None
    target_lade: Optional[str] = None     # 'voelen' | 'spreken' | 'weten' | 'doen' | None=auto
    user_id: Optional[str] = "user-001"


# Topic + tags → KB v2 lade mapping (auto-classify)
_TOPIC_LADE_MAP = {
    # voelen
    "emotie": "voelen", "voelen": "voelen", "gevoel": "voelen", "relatie": "voelen",
    "verbinding": "voelen", "empathie": "voelen", "compassie": "voelen",
    # spreken
    "taal": "spreken", "communicatie": "spreken", "gesprek": "spreken",
    "schrijven": "spreken", "spreken": "spreken", "praten": "spreken",
    # weten
    "kennis": "weten", "systeem": "weten", "feit": "weten", "logica": "weten",
    "definitie": "weten", "concept": "weten", "model": "weten", "theorie": "weten",
    "weten": "weten", "geheugen": "weten",
    # doen
    "gedrag": "doen", "actie": "doen", "praktijk": "doen", "doen": "doen",
    "uitvoeren": "doen", "stap": "doen", "methode": "doen", "proces": "doen",
}


def _auto_lade(topic: Optional[str], tags: Optional[List[str]]) -> str:
    pool = []
    if topic: pool.append(str(topic).lower())
    pool.extend([str(t).lower() for t in (tags or [])])
    for token in pool:
        for key, lade in _TOPIC_LADE_MAP.items():
            if key in token:
                return lade
    return "weten"  # safe default


@router.post("/herzien/promote")
async def herzien_promote(body: HerzienPromoteBody):
    """Maak een nieuwe v2-kaart uit de herziene v1-kaart, classify naar lade,
    en markeer v1 als gemigreerd."""
    begrip = (body.begrip or "").strip()
    if not begrip:
        return {"success": False, "message": "Begrip mag niet leeg zijn"}
    # 1. Inbox-kaart aanmaken
    r = service.add_to_inbox(begrip, source="kb_v1_migration", user_id=body.user_id)
    if not (r and r.get("kaart")):
        return {"success": False, "message": "Inbox-add mislukt", "raw": r}
    card_id = r["kaart"]["id"]
    # 2. Updates toepassen
    updates = {}
    if body.lagen: updates["lagen"] = body.lagen
    if body.ws5:   updates["ws5"]   = body.ws5
    if body.tags:  updates["tags"]  = body.tags
    if updates:
        service.edit_card(card_id, "inbox", updates=updates, user_id=body.user_id)
    # 3. Classify naar lade
    target = body.target_lade or _auto_lade(body.topic, body.tags)
    if target not in ("voelen", "spreken", "weten", "doen"):
        target = "weten"
    cl = service.classify_card(card_id, target, updates=None, user_id=body.user_id)
    # 4. Mark v1 als gemigreerd
    data = _load_kb_v1()
    entries_list = data.get("knowledge_entries") or data.get("entries") or []
    for e in entries_list:
        if e.get("id") == body.v1_id:
            e["migrated_to_v2"] = True
            e["v2_card_id"] = card_id
            e["v2_lade"] = target
            e["migrated_at"] = _dt.now(_tz.utc).isoformat()
            break
    _save_kb_v1(data)
    return {
        "success": True,
        "v1_id": body.v1_id,
        "v2_card_id": card_id,
        "lade": target,
        "auto_classified": body.target_lade is None,
        "kaart": cl.get("kaart") if cl else None,
    }


@router.post("/herzien/skip")
async def herzien_skip():
    """Skip (alleen marker, geen mutatie nodig — herzien/next picks willekeurig)."""
    return {"success": True, "skipped": True}
