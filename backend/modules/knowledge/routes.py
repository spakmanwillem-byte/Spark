"""
Knowledge Routes - API endpoints voor kennisbank
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from .service import KnowledgeService

router = APIRouter(prefix="/knowledge", tags=["knowledge"])
service = KnowledgeService()


@router.get("/all")
async def get_all_knowledge(
    search: Optional[str] = Query(None),
    status_filter: Optional[str] = Query("all"),
    sort_by: Optional[str] = Query("recent"),
    importance: Optional[str] = Query("all"),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
):
    """Get all knowledge entries with search, filter, sort and pagination"""
    result = service.get_all(
        search=search,
        status_filter=status_filter,
        sort_by=sort_by,
        importance=importance,
        page=page,
        per_page=per_page,
    )
    return result


@router.get("/stats")
async def get_knowledge_stats():
    """Get knowledge base statistics"""
    return service.get_stats()


@router.get("/tags")
async def get_all_tags():
    """Get all unique tags"""
    return {"tags": service.get_all_tags()}


@router.get("/review/next")
async def get_next_review_entry(after_id: Optional[str] = Query(None)):
    """v4_019: pak volgende kaart voor de Review-flow.
    Nooit-gereviewd eerst, daarna langst-niet-gereviewd."""
    entry = service.get_next_review(after_id=after_id)
    if not entry:
        return {"entry": None, "message": "Geen kaarten meer om te reviewen."}
    return {"entry": entry}


@router.get("/exists")
async def check_begrip_exists(begrip: str = Query(..., min_length=1)):
    """v4_kb_create_001: exact-match check op begrip (case-insensitive).
    Retourneert {exists: bool, match: {id, begrip, topic} | null}."""
    match = service.exists_begrip(begrip)
    return {"exists": bool(match), "match": match}


@router.post("/create")
async def create_knowledge_entry(data: dict):
    """v4_kb_create_001: maak een nieuwe knowledge kaart aan.
    Body: {begrip (verplicht), topic, tags, lagen, ws5, belangrijkheid, kaart_type}.
    Faalt met 409 als begrip al bestaat."""
    entry, err = service.create_entry(data)
    if err == "begrip_required":
        raise HTTPException(status_code=400, detail="'begrip' is verplicht")
    if err == "duplicate":
        existing = service.exists_begrip(data.get("begrip"))
        raise HTTPException(
            status_code=409,
            detail={"message": "Begrip bestaat al", "match": existing},
        )
    # v4_dnd_001 — Behavior: kennis-creatie versterkt The Story Teller
    try:
        from modules.behavior_tracker import track
        creator = data.get("created_by") or data.get("detected_by")
        if creator:
            track(creator, "kb_create", 1)
            track(creator, "story_share", 1)
            # v13c_dnd_sloop_001 (sessie 54) — DnD observe-hook verwijderd.
    except Exception:
        pass
    return {"status": "ok", "entry": entry}


@router.get("/{entry_id}")
async def get_knowledge_entry(entry_id: str):
    """Get single knowledge entry by ID"""
    entry = service.get_by_id(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry niet gevonden")
    return entry


@router.put("/{entry_id}")
async def update_knowledge_entry(entry_id: str, data: dict):
    """Update a knowledge entry"""
    updated = service.update_entry(entry_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Entry niet gevonden")
    return {"status": "ok", "message": "Entry bijgewerkt"}


@router.delete("/{entry_id}")
async def delete_knowledge_entry(entry_id: str):
    """Delete a knowledge entry permanently"""
    deleted = service.delete_entry(entry_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Entry niet gevonden")
    return {"status": "ok", "message": "Entry verwijderd"}


@router.post("/{entry_id}/review")
async def mark_entry_reviewed(entry_id: str):
    """v4_019: registreer een review (zet reviewed_at + verhoog review_count)."""
    entry = service.mark_reviewed(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry niet gevonden")
    return {
        "status": "ok",
        "reviewed_at": (entry.get("metadata") or {}).get("reviewed_at"),
        "review_count": (entry.get("metadata") or {}).get("review_count"),
    }


# v5_kb_diff_export_001 — Import een KB-diff bestand (van productie naar preview)
from fastapi import UploadFile, File
from pathlib import Path as _Path
import json as _json
from datetime import datetime as _dt, timezone as _tz
from modules.core.storage import load_json as _load, save_json as _save

_KB = _Path(__file__).parent.parent.parent / "data" / "knowledge" / "learned_knowledge" / "knowledge_base.json"


@router.post("/import-diff")
async def import_kb_diff(file: UploadFile = File(...)):
    """Merge een kb_diff bestand (van /api/backup/kb-changed-since-deploy) in deze KB.
    Veiligheid: maakt eerst een backup van de huidige KB. Match by id of begrip.
    """
    try:
        raw = await file.read()
        payload = _json.loads(raw)
    except Exception as e:
        raise HTTPException(400, f"Geen geldig JSON-bestand: {e}")

    if not isinstance(payload, dict) or "knowledge_entries" not in payload:
        raise HTTPException(400, "Bestand mist 'knowledge_entries' veld")

    diff_entries = payload.get("knowledge_entries") or []
    if not diff_entries:
        return {"success": True, "merged_existing": 0, "new_added": 0, "message": "Geen kaarten in diff-bestand"}

    # v6_v2_first_001 — schrijf nu naar V2 lade-bestanden (niet meer V1)
    v2_dir = _Path(__file__).parent.parent.parent / "data" / "knowledge" / "v2"
    KBV2_LADES = ["doen", "weten", "voelen", "spreken"]

    # 1. Laad alle V2 kaarten verdeeld per lade-bestand
    lade_data = {}
    for lade in KBV2_LADES + ["inbox"]:
        fname = "knowledge_inbox" if lade == "inbox" else f"knowledge_v2_{lade}"
        fp = v2_dir / f"{fname}.json"
        lade_data[lade] = {
            "fp": fp,
            "data": _load(fp, default={"kaarten": []}),
        }

    # Backup elk V2 lade-bestand
    backup_ts = _dt.now(_tz.utc).strftime("%Y%m%d_%H%M%S")
    for lade, info in lade_data.items():
        fname = info["fp"].name
        backup = info["fp"].with_suffix(f".backup_pre_diff_import_{backup_ts}.json")
        try:
            backup.write_text(info["fp"].read_text(encoding="utf-8"), encoding="utf-8")
        except Exception:
            pass

    # Bouw lookup over ALLE V2 kaarten (kan in elke lade staan)
    by_id = {}
    by_begrip = {}
    location = {}  # id → lade
    for lade, info in lade_data.items():
        for k in info["data"].get("kaarten", []):
            kid = k.get("id")
            if kid:
                by_id[kid] = k
                location[kid] = lade
            b = (k.get("begrip") or "").strip().lower()
            if b:
                by_begrip.setdefault(b, (k, lade))

    merged_existing = 0
    new_added = 0
    now_iso = _dt.now(_tz.utc).isoformat()

    for d in diff_entries:
        # Skip V1 ghosts in import payload
        did = d.get("id") or ""
        if did.startswith("snap-"):
            continue
        dbegrip = (d.get("begrip") or "").strip().lower()
        target = by_id.get(did)
        if target is None and dbegrip in by_begrip:
            target, _ = by_begrip[dbegrip]
        if target is not None:
            for key in ("lagen", "ws5", "tags", "belangrijkheid", "topic", "lade", "footnote"):
                if key in d and d[key] is not None:
                    target[key] = d[key]
            md = target.setdefault("metadata", {})
            d_md = d.get("metadata") or {}
            if d_md.get("updated_at"):
                md["updated_at"] = d_md["updated_at"]
            md["last_diff_import_at"] = now_iso
            merged_existing += 1
        else:
            # Nieuwe kaart — voeg toe aan juiste lade (uit kaart.lade, anders inbox)
            new_lade = (d.get("lade") or "").lower().strip()
            if new_lade not in KBV2_LADES:
                new_lade = "inbox"
            lade_data[new_lade]["data"].setdefault("kaarten", []).append(d)
            new_added += 1

    # Schrijf alle lade-bestanden
    total_after = 0
    for lade, info in lade_data.items():
        _save(info["fp"], info["data"])
        total_after += len(info["data"].get("kaarten", []))

    return {
        "success": True,
        "schema": "v2",
        "merged_existing": merged_existing,
        "new_added": new_added,
        "total_after": total_after,
        "backup_ts": backup_ts,
    }
