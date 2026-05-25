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


# v6_kbv2_delete_001 — permanent verwijderen van onbruikbare kaart
class DeleteBody(BaseModel):
    card_id: str
    lade: str  # 'inbox' of een van LADES
    user_id: str = "user-001"
    reason: str = ""


@router.post("/delete")
async def delete_card(body: DeleteBody):
    """Verwijder een KB v2 kaart permanent uit zijn lade (of inbox) + index.
    Reden wordt gelogd in admin_log voor traceability."""
    from modules.core.storage import load_json as _lj, save_json as _sj
    from .service import LADES, _lade_path, _inbox_path, _index_path, _lock
    from modules.core.spark_logger import log_event
    from datetime import datetime, timezone

    target = body.lade
    if target != "inbox" and target not in LADES:
        return {"success": False, "message": f"Onbekende lade: {target}"}

    with _lock:
        path = _inbox_path() if target == "inbox" else _lade_path(target)
        data = _lj(path, default={"kaarten": []})
        before = len(data.get("kaarten", []))
        removed = None
        new_kaarten = []
        for k in data.get("kaarten", []):
            if k.get("id") == body.card_id:
                removed = k
                continue
            new_kaarten.append(k)
        if removed is None:
            return {"success": False, "message": f"Kaart '{body.card_id}' niet gevonden in '{target}'"}
        data["kaarten"] = new_kaarten
        _sj(path, data)

        # Verwijder ook uit knowledge_index
        idx = _lj(_index_path(), default={"entries": {}})
        begrip_key = (removed.get("begrip") or "").lower().strip()
        if begrip_key and begrip_key in idx.get("entries", {}):
            if idx["entries"][begrip_key].get("kaart_id") == body.card_id:
                del idx["entries"][begrip_key]
                _sj(_index_path(), idx)

    log_event("kbv2", "delete_card",
              intent="card-verwijderd",
              detail={
                  "card_id": body.card_id,
                  "lade": target,
                  "begrip": removed.get("begrip"),
                  "user_id": body.user_id,
                  "reason": body.reason or "(geen reden opgegeven)",
                  "before_count": before,
                  "after_count": len(new_kaarten),
                  "ts": datetime.now(timezone.utc).isoformat(),
              })
    return {
        "success": True,
        "message": f"Kaart '{removed.get('begrip')}' verwijderd uit {target}",
        "card_id": body.card_id,
        "begrip": removed.get("begrip"),
        "lade": target,
        "remaining_in_lade": len(new_kaarten),
    }


@router.post("/inbox/add")
async def inbox_add(body: InboxAddBody):
    return service.add_to_inbox(body.begrip, source=body.source, user_id=body.user_id)


# ---------- v6_kbv2_hooks_landing_001: Eenmalige backfill ----------

@router.post("/backfill-hooks")
async def backfill_hooks(limit_per_lade: int = Query(0, ge=0, description="0 = alles")):
    """Eenmalig: alle bestaande KB v2 kaarten door de 5 hooks halen zodat
    vocab/verbanden/lore-koppeling/footnote.hooks_fired retroactief gevuld worden.

    Batch-veilig: 1 save per lade (geen save per kaart).
    Voor grote KB's mag je `limit_per_lade` zetten om in stapjes te draaien.
    """
    from . import hooks as kbv2_hooks
    from modules.core.storage import load_json as _lj, save_json as _sj
    from .service import LADES, _lade_path, _inbox_path

    stats = {"by_lade": {}, "totals": {"cards": 0, "vocab_new": 0, "verbanden_added": 0, "lore_added": 0}}

    # Verwerk lades + inbox
    targets = [(L, _lade_path(L)) for L in LADES] + [("inbox", _inbox_path())]
    for lade, path in targets:
        data = _lj(path, default={"kaarten": []})
        kaarten = data.get("kaarten", [])
        if limit_per_lade > 0:
            kaarten_to_process = kaarten[:limit_per_lade]
        else:
            kaarten_to_process = kaarten

        n_processed = 0
        n_verb = 0
        n_lore = 0
        n_vocab_new = 0
        for k in kaarten_to_process:
            # Hook 1: vocab register
            try:
                is_new = kbv2_hooks.register_in_vocab(k)
                if is_new:
                    n_vocab_new += 1
            except Exception:
                pass
            # Hook 3: verbanden (alleen voor lade-kaarten, niet inbox)
            if lade != "inbox":
                try:
                    verbanden = kbv2_hooks.compute_verbanden(k)
                    if verbanden:
                        k["verbanden"] = verbanden
                        n_verb += 1
                except Exception:
                    pass
            # Hook 4: D&D koppeling (alleen lade)
            if lade != "inbox":
                try:
                    if kbv2_hooks.link_to_dnd(k):
                        n_lore += 1
                except Exception:
                    pass
            n_processed += 1

        # Batch-save 1x per lade
        _sj(path, data)
        stats["by_lade"][lade] = {
            "processed": n_processed,
            "total_in_lade": len(kaarten),
            "verbanden_added": n_verb,
            "lore_added": n_lore,
            "vocab_new": n_vocab_new,
        }
        stats["totals"]["cards"] += n_processed
        stats["totals"]["verbanden_added"] += n_verb
        stats["totals"]["lore_added"] += n_lore
        stats["totals"]["vocab_new"] += n_vocab_new

    return {"success": True, **stats}


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
