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
from modules.core.spark_logger import traced

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


@router.get("/priority/missing-laag1")
async def get_priority_missing_laag1(limit: int = Query(50, ge=1, le=200)):
    """
    v6_kbv2_priority_001 — Top N inbox-kaarten zonder laag1, gesorteerd op
    'belangrijkheid' = aantal verbanden + tag-richness + topic-aanwezigheid.

    Doel: De Willem ziet welke kaarten het meeste effect hebben als hij ze invult,
    i.p.v. door 2112 inbox-kaarten te scrollen.

    Returnt: {cards: [{id, begrip, lade, score, reasons[], tags_count, verbanden_count, has_topic}]}
    """
    return {"success": True, **service.list_priority_missing_laag1(limit=limit)}


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
@traced(intent="KB v2 kaart classificeren (inbox → lade)", module="kb_v2")
async def classify(body: ClassifyBody):
    return service.classify_card(body.card_id, body.lade, updates=body.updates, user_id=body.user_id)


@router.post("/edit")
@traced(intent="KB v2 kaart bewerken", module="kb_v2")
async def edit(body: EditBody):
    return service.edit_card(body.card_id, body.lade, updates=body.updates, user_id=body.user_id)


# v6_kbv2_autoresolve_001 — bulk auto-classify van inbox-kaarten via topic+tags
class AutoResolveBody(BaseModel):
    reasons: Optional[List[str]] = None  # ['tag_tie', 'no_match'] — default beide
    dry_run: bool = True
    limit: Optional[int] = None  # max kaarten in 1 call (None = alles)
    viewer_id: str = "user-001"


@router.post("/inbox/auto-resolve")
@traced(intent="Auto-classify inbox kaarten via topic+tags → lade", module="kb_v2")
async def auto_resolve_inbox(body: AutoResolveBody):
    """v6_kbv2_autoresolve_001 — Bulk auto-classify van inbox-kaarten.

    Gebruikt `_auto_lade(topic, tags)` om kaarten met tag_tie/no_match-reden
    naar de juiste lade te promoteren. Default dry_run=True (preview) zodat
    je eerst kunt zien wat er ZOU gebeuren.

    Filter:
      reasons=['tag_tie'] of ['no_match'] of beide (default).
      Kaarten zonder topic EN zonder tags → skipped (geen signaal).

    Returns: {success, planned, executed, by_lade, skipped, examples}
    Admin-only (gradatie ≤ 2).
    """
    from modules.core.storage import load_json
    from .service import _inbox_path
    # Admin-guard
    from modules.dnd.world import _is_admin as _check_admin
    if not _check_admin(body.viewer_id):
        return {"success": False, "error": "Alleen admin (gradatie ≤ 2) mag inbox bulk-classifyen."}

    reasons = set(body.reasons or ["tag_tie", "no_match"])
    inbox = load_json(_inbox_path(), default={"kaarten": []})
    kaarten = inbox.get("kaarten", [])

    planned = []   # kaarten die we kunnen promoten
    skipped = []   # geen topic + geen tags
    for k in kaarten:
        if k.get("_inbox_reason") not in reasons:
            continue
        # Skip als al laag1 gevuld (zou niet moeten kunnen voor deze reasons, maar safety)
        topic = (k.get("topic") or "").strip()
        tags = k.get("tags") or []
        if not topic and not tags:
            skipped.append({"id": k.get("id"), "begrip": k.get("begrip"), "reason": "geen topic en geen tags"})
            continue
        target_lade = _auto_lade(topic, tags)
        # v6_kbv2_autoresolve_001 — alleen committen als _auto_lade een ECHTE match
        # had (anders zou alles 'weten' worden via default). Word-boundary check
        # (zelfde regex-grens als _auto_lade nu gebruikt).
        import re as _re
        matched = False
        pool = [topic.lower()] if topic else []
        pool.extend([str(t).lower() for t in tags])
        for token in pool:
            if any(_re.search(rf"(?:^|[\s\-_/]){_re.escape(key)}(?:$|[\s\-_/])", token)
                   for key in _TOPIC_LADE_MAP.keys()):
                matched = True
                break
        if not matched:
            skipped.append({"id": k.get("id"), "begrip": k.get("begrip"), "reason": "topic/tags niet in lade-map"})
            continue
        planned.append({
            "id": k.get("id"),
            "begrip": k.get("begrip"),
            "topic": topic or "-",
            "tags_count": len(tags),
            "reason": k.get("_inbox_reason"),
            "→ lade": target_lade,
        })

    # Limit
    if body.limit:
        planned = planned[:body.limit]

    by_lade: Dict[str, int] = {}
    for p in planned:
        by_lade[p["→ lade"]] = by_lade.get(p["→ lade"], 0) + 1

    result = {
        "success": True,
        "dry_run": body.dry_run,
        "planned_count": len(planned),
        "by_lade": by_lade,
        "skipped_count": len(skipped),
        "examples": planned[:10],
        "skipped_examples": skipped[:5],
    }

    if not body.dry_run:
        executed = 0
        failures = []
        for p in planned:
            try:
                r = service.classify_card(p["id"], p["→ lade"], updates=None, user_id=body.viewer_id)
                if r and r.get("success"):
                    executed += 1
                else:
                    failures.append({"id": p["id"], "error": r.get("message") if r else "no result"})
            except Exception as e:
                failures.append({"id": p["id"], "error": str(e)[:80]})
        result["executed"] = executed
        result["failure_count"] = len(failures)
        result["failures"] = failures[:5]

    return result


# v6_kbv2_vocab_sync_001 — herstel vocab-gaten (kaarten in lade maar niet in vocab)
class VocabSyncBody(BaseModel):
    dry_run: bool = True
    viewer_id: str = "user-001"


@router.post("/vocab/sync")
@traced(intent="Sync vocab register met lade-kaarten", module="kb_v2")
async def sync_vocab(body: VocabSyncBody):
    """v6_kbv2_vocab_sync_001 — Herstel ontbrekende vocab-entries.

    Probleem: kaarten die via legacy paden of mislukte hooks in de lades zijn beland,
    staan WEL in de lade maar NIET in spark_vocab → Spark gebruikt het woord niet
    actief in zijn taal. Geaccepteerd was zo'n geval.

    Fix: loop door alle lade-kaarten, check vocab, en run `register_in_vocab()` voor
    elke kaart die mist. Idempotent — kaarten die al in vocab staan worden niet
    aangeraakt (behalve `last_seen`-update door bestaande hook-logica).

    Admin-only (gradatie ≤ 2).
    """
    from modules.core.storage import load_json
    from .service import _lade_path
    from . import hooks as kbv2_hooks
    from modules.dnd.world import _is_admin as _check_admin
    from pathlib import Path
    if not _check_admin(body.viewer_id):
        return {"success": False, "error": "Alleen admin (gradatie ≤ 2) mag vocab syncen."}

    base = Path(__file__).parent.parent.parent / "data"
    vdata = load_json(base / "personality" / "spark_vocab.json", default={"vocab": {}})
    vocab_keys = {k.lower() for k in vdata.get("vocab", {}).keys()}

    missing = []
    for lade in ["voelen", "spreken", "weten", "doen"]:
        ldata = load_json(_lade_path(lade), default={"kaarten": []})
        for k in ldata.get("kaarten", []):
            begrip = (k.get("begrip") or "").strip()
            if not begrip:
                continue
            if begrip.lower() not in vocab_keys:
                missing.append({"id": k.get("id"), "begrip": begrip, "lade": lade})

    result = {
        "success": True,
        "dry_run": body.dry_run,
        "missing_count": len(missing),
        "by_lade": {},
        "examples": missing[:15],
    }
    for m in missing:
        result["by_lade"][m["lade"]] = result["by_lade"].get(m["lade"], 0) + 1

    if not body.dry_run:
        registered = 0
        for m in missing:
            # Vind kaart en run register_in_vocab
            ldata = load_json(_lade_path(m["lade"]), default={"kaarten": []})
            card = next((k for k in ldata.get("kaarten", []) if k.get("id") == m["id"]), None)
            if card:
                try:
                    kbv2_hooks.register_in_vocab(card)
                    registered += 1
                except Exception:
                    pass
        result["registered"] = registered

    return result


# v6_kbv2_delete_001 — permanent verwijderen van onbruikbare kaart
class DeleteBody(BaseModel):
    card_id: str
    lade: str  # 'inbox' of een van LADES
    user_id: str = "user-001"
    reason: str = ""


@router.post("/delete")
@traced(intent="KB v2 kaart verwijderen", module="kb_v2")
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
    """v6_kbv2_autoresolve_001 — Map topic+tags naar lade via WORD-boundary.
    Voorheen werd `if key in token` substring-match gebruikt → false positives
    zoals 'taal' in 'metaal' (Nikkel → spreken). Nu: woord-grens regex zodat
    enkel hele tokens of door spatie/streepje gescheiden delen matchen.
    """
    import re as _re
    pool = []
    if topic: pool.append(str(topic).lower())
    pool.extend([str(t).lower() for t in (tags or [])])
    for token in pool:
        for key, lade in _TOPIC_LADE_MAP.items():
            if _re.search(rf"(?:^|[\s\-_/]){_re.escape(key)}(?:$|[\s\-_/])", token):
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



# ---------------------------------------------------------------------------
# v6_kb_tag_normalizer_001 — Tag-normalisatie + dry-run scan
# ---------------------------------------------------------------------------
# Fundering voor #kb-tag-singular + #kb-verb-stem. Geen mutaties — alleen
# inspectie zodat Willem in volgende sessie een "1-klik dedupe" UI kan
# bouwen bovenop deze data.
# ---------------------------------------------------------------------------

from .tag_normalizer import normalize_tag, normalize_tags, overlap_score


@router.get("/tags/normalize")
async def tag_normalize_one(tag: str):
    """Test 1 tag: 'Emoties' → 'emotie'."""
    return {"input": tag, "normalized": normalize_tag(tag)}


@router.post("/tags/normalize-batch")
async def tag_normalize_batch(body: dict):
    """Normaliseer een lijst tags (dedupe behoudt volgorde)."""
    tags = body.get("tags") or []
    if not isinstance(tags, list):
        return {"success": False, "error": "tags moet een lijst zijn"}
    return {"input": tags, "normalized": normalize_tags(tags)}


@router.get("/tags/scan")
async def tag_scan(limit: int = 50):
    """Scan alle KB v2 kaarten en groepeer tags op canonieke stam.
    Toont waar dedupe kansen liggen (bv. 'emoties' + 'emotie' + 'Emoties' → 1 stam).
    Read-only.
    """
    from collections import defaultdict
    from modules.core.storage import load_json
    lades = ["voelen", "spreken", "weten", "doen"]
    stem_to_variants: dict = defaultdict(set)
    stem_to_count: dict = defaultdict(int)
    total_tags = 0
    for lade in lades:
        try:
            d = load_json(service._lade_path(lade), default={"kaarten": []})
        except Exception:
            continue
        for k in d.get("kaarten", []):
            for t in k.get("tags") or []:
                if not isinstance(t, str) or not t.strip():
                    continue
                stem = normalize_tag(t)
                if not stem:
                    continue
                stem_to_variants[stem].add(t.strip().lower())
                stem_to_count[stem] += 1
                total_tags += 1
    # Filter: alleen stammen met ≥2 verschillende varianten (dedupe-kansen)
    duplicates = [
        {
            "stem": stem,
            "variants": sorted(variants),
            "variant_count": len(variants),
            "total_occurrences": stem_to_count[stem],
        }
        for stem, variants in stem_to_variants.items()
        if len(variants) >= 2
    ]
    duplicates.sort(key=lambda x: (-x["total_occurrences"], -x["variant_count"]))
    return {
        "success": True,
        "total_tags_scanned": total_tags,
        "unique_stems": len(stem_to_variants),
        "stems_with_duplicates": len(duplicates),
        "top_duplicates": duplicates[:limit],
    }


@router.get("/tags/similarity")
async def tag_similarity(a: str, b: str):
    """Vergelijk 2 tag-lijsten (kommagescheiden) via genormaliseerde Jaccard.
    Voorbeeld: ?a=emoties,blij&b=emotie,verdrietig → 0.333
    """
    list_a = [s.strip() for s in a.split(",") if s.strip()]
    list_b = [s.strip() for s in b.split(",") if s.strip()]
    return {
        "tags_a": list_a,
        "tags_b": list_b,
        "normalized_a": normalize_tags(list_a),
        "normalized_b": normalize_tags(list_b),
        "jaccard_score": round(overlap_score(list_a, list_b), 4),
    }


class TagMergeBody(BaseModel):
    stem: str  # canonieke stam waar we naar mergen
    keep_variant: str  # welke variant we behouden (bv. "emotie", niet "emoties")
    viewer_id: str  # admin gradatie ≤ 2 vereist


@router.post("/tags/merge")
async def tag_merge(body: TagMergeBody):
    """Vervang ALLE varianten met dezelfde stam door `keep_variant` in alle KB v2 kaarten.

    Voorbeeld: stem='emotie', keep_variant='emotie' → 'Emoties', 'emoties', 'EMOTIE' worden
    allemaal 'emotie' in elke kaart-tags lijst.

    Admin-only (gradatie ≤ 2). Geeft per lade aantal gemuteerde kaarten terug.
    """
    from pathlib import Path
    from modules.core.storage import load_json, save_json

    # Admin check
    USERS = Path(__file__).parent.parent.parent / "data" / "system" / "users.json"
    users = load_json(USERS, default={"users": []})
    ulist = users.get("users", []) if isinstance(users, dict) else users
    viewer = next((u for u in ulist if u.get("id") == body.viewer_id), None)
    if not viewer or int(viewer.get("gradatie", 7) or 7) > 2:
        return {"success": False, "error": "Alleen admin (gradatie ≤ 2) mag tags mergen"}

    target_stem = normalize_tag(body.stem)
    keep = body.keep_variant.strip()
    if not target_stem or not keep:
        return {"success": False, "error": "stem en keep_variant mogen niet leeg zijn"}

    lades = ["voelen", "spreken", "weten", "doen"]
    stats = {lade: {"cards_touched": 0, "tags_replaced": 0} for lade in lades}

    for lade in lades:
        path = service._lade_path(lade)
        d = load_json(path, default={"kaarten": []})
        changed = False
        for k in d.get("kaarten", []):
            old_tags = k.get("tags") or []
            if not old_tags:
                continue
            new_tags = []
            seen = set()
            card_changed = False
            for t in old_tags:
                if not isinstance(t, str):
                    new_tags.append(t)
                    continue
                if normalize_tag(t) == target_stem and t != keep:
                    if keep not in seen:
                        new_tags.append(keep)
                        seen.add(keep)
                    stats[lade]["tags_replaced"] += 1
                    card_changed = True
                else:
                    if t not in seen:
                        new_tags.append(t)
                        seen.add(t)
            if card_changed:
                k["tags"] = new_tags
                stats[lade]["cards_touched"] += 1
                changed = True
        if changed:
            save_json(path, d)

    total_cards = sum(s["cards_touched"] for s in stats.values())
    total_replaced = sum(s["tags_replaced"] for s in stats.values())
    return {
        "success": True,
        "stem": target_stem,
        "keep_variant": keep,
        "cards_touched": total_cards,
        "tags_replaced": total_replaced,
        "per_lade": stats,
        "by": body.viewer_id,
    }

