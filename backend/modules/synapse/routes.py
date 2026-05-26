"""
Synapse — FastAPI routes (v6_synapse_001)
==========================================
Endpoints:
  GET  /api/synapse/scan          : trigger full scan + rebuild aggregator
  GET  /api/synapse/tree          : returnt SYNAPSE.json
  GET  /api/synapse/search?q=...  : zoek in alle meta-records
  POST /api/synapse/tag           : tag een container (status update)
  POST /api/synapse/touch         : handmatig touch
"""
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from modules.core.storage import load_json, save_json

from .aggregator import build_synapse, SYNAPSE_FILE
from .schema import VALID_STATUSES, now_iso
from .touch import touch_path

router = APIRouter(prefix="/synapse", tags=["synapse"])


# ============================================================
# SCAN + TREE
# ============================================================
@router.get("/scan")
async def trigger_scan():
    """Doe een volledige scan + rebuild SYNAPSE.json."""
    doc = build_synapse()
    return {
        "success": True,
        "generated_at": doc.get("generated_at"),
        "summary": doc.get("summary"),
    }


@router.get("/tree")
async def get_tree(group: Optional[str] = None):
    """Returnt SYNAPSE.json. Optioneel: ?group=backend_modules|frontend_components|backend_data"""
    if not SYNAPSE_FILE.exists():
        # On-demand build als nog niet bestaat
        build_synapse()
    doc = load_json(SYNAPSE_FILE, default={})
    if group:
        tree = doc.get("tree", {})
        if group not in tree:
            raise HTTPException(404, f"Onbekende group: {group}")
        return {
            "generated_at": doc.get("generated_at"),
            "group": group,
            "items": tree.get(group, {}),
        }
    return doc


# ============================================================
# SEARCH
# ============================================================
@router.get("/search")
async def search(q: str, group: Optional[str] = None):
    """Zoek in naam/doel/footnote/tags/endpoints."""
    if not q or not q.strip():
        raise HTTPException(400, "Query 'q' verplicht")
    if not SYNAPSE_FILE.exists():
        build_synapse()
    doc = load_json(SYNAPSE_FILE, default={})
    needle = q.lower().strip()
    hits: List[Dict[str, Any]] = []
    for grp, items in doc.get("tree", {}).items():
        if group and grp != group:
            continue
        for path, meta in items.items():
            haystack_parts = [
                meta.get("naam", ""),
                meta.get("doel", ""),
                meta.get("footnote", ""),
                meta.get("blueprint_ref", "") or "",
                " ".join(meta.get("tags", []) or []),
                " ".join(meta.get("endpoints", []) or []),
            ]
            haystack = " ".join(haystack_parts).lower()
            if needle in haystack:
                hits.append({
                    "path": path,
                    "group": grp,
                    "naam": meta.get("naam"),
                    "doel": meta.get("doel"),
                    "status": meta.get("status"),
                    "container_type": meta.get("container_type"),
                    "endpoints_count": len(meta.get("endpoints") or []),
                    "footnote": meta.get("footnote") or "",
                    "blueprint_ref": meta.get("blueprint_ref"),
                    "last_touched": meta.get("last_touched"),
                })
    return {"q": q, "count": len(hits), "hits": hits[:50]}


# ============================================================
# TAG (status update)
# ============================================================
class TagBody(BaseModel):
    container_path: str  # bv. "/app/backend/modules/winkelstraat" of relative
    status: Optional[str] = None
    footnote: Optional[str] = None
    blueprint_ref: Optional[str] = None
    tags: Optional[List[str]] = None
    doel: Optional[str] = None
    viewer_id: Optional[str] = None  # admin guard later


@router.post("/tag")
async def tag_container(body: TagBody):
    """Update status/footnote/blueprint/tags/doel van een container's _meta.json."""
    # Resolve path
    raw = body.container_path
    p = Path(raw) if raw.startswith("/") else Path("/app") / raw
    if not p.exists() or not p.is_dir():
        raise HTTPException(404, f"Map niet gevonden: {raw}")
    meta_path = p / "_meta.json"
    if not meta_path.exists():
        raise HTTPException(404, f"Geen _meta.json in {raw} — scan eerst /api/synapse/scan")
    meta = load_json(meta_path, default={})
    if body.status is not None:
        if body.status not in VALID_STATUSES:
            raise HTTPException(400, f"Ongeldige status. Gebruik: {sorted(VALID_STATUSES)}")
        meta["status"] = body.status
    if body.footnote is not None:
        meta["footnote"] = body.footnote
    if body.blueprint_ref is not None:
        meta["blueprint_ref"] = body.blueprint_ref or None
    if body.tags is not None:
        meta["tags"] = body.tags
    if body.doel is not None and body.doel.strip():
        meta["doel"] = body.doel.strip()
    meta["last_touched"] = now_iso()
    save_json(meta_path, meta)
    return {"success": True, "meta": meta}


# ============================================================
# TOUCH (handmatig)
# ============================================================
class TouchBody(BaseModel):
    file_path: str


@router.post("/touch")
async def manual_touch(body: TouchBody):
    ok = touch_path(body.file_path)
    return {"success": ok, "file_path": body.file_path}


# ============================================================
# Summary (snelle helper voor Spark chat)
# ============================================================
@router.get("/summary")
async def get_summary():
    """Returnt alleen de high-level summary (lichtgewicht)."""
    if not SYNAPSE_FILE.exists():
        build_synapse()
    doc = load_json(SYNAPSE_FILE, default={})
    summary = doc.get("summary", {})
    # Voeg top-status-categorieën toe
    return {
        "generated_at": doc.get("generated_at"),
        **summary,
    }
