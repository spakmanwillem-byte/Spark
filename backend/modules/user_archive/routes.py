"""
User Archive Routes - per-user persoonlijke opslag
Categorieën: bestanden | foto | geluiden | filmpjes (auto-detect via extensie)
Storage: /app/backend/data/users/{user_id}/archive/{category}/
Index:   /app/backend/data/users/{user_id}/archive/_index.json
"""
import os
import uuid
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel

from modules.core.storage import load_json, save_json

router = APIRouter(prefix="/archive", tags=["user-archive"])

BASE_DIR = Path(__file__).parent.parent.parent / "data" / "users"
MAX_SIZE_BYTES = 50 * 1024 * 1024  # 50MB per file

# Categorie detectie op basis van extensie
EXT_MAP = {
    "foto": {".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic", ".bmp", ".svg"},
    "geluiden": {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac", ".opus"},
    "filmpjes": {".mp4", ".webm", ".mov", ".avi", ".mkv", ".m4v"},
}
ALL_MEDIA_EXTS = set().union(*EXT_MAP.values())

CATEGORIES = ["bestanden", "foto", "geluiden", "filmpjes"]


def _detect_category(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    for cat, exts in EXT_MAP.items():
        if ext in exts:
            return cat
    return "bestanden"


def _user_dir(user_id: str) -> Path:
    if not user_id or "/" in user_id or ".." in user_id:
        raise HTTPException(400, "Ongeldig user_id")
    d = BASE_DIR / user_id / "archive"
    d.mkdir(parents=True, exist_ok=True)
    for cat in CATEGORIES:
        (d / cat).mkdir(exist_ok=True)
    return d


def _index_file(user_id: str) -> Path:
    return _user_dir(user_id) / "_index.json"


def _load_index(user_id: str) -> List[dict]:
    data = load_json(_index_file(user_id), default={"files": []})
    return data.get("files", [])


def _save_index(user_id: str, files: List[dict]):
    save_json(_index_file(user_id), {
        "user_id": user_id,
        "files": files,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    })


# ============================================================
# UPLOAD
# ============================================================

@router.post("/{user_id}/upload")
async def upload_file(
    user_id: str,
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),  # komma-gescheiden
):
    """Upload een bestand naar het persoonlijke archief van de user."""
    user_dir = _user_dir(user_id)

    # Lees inhoud + size check
    content = await file.read()
    if len(content) > MAX_SIZE_BYTES:
        raise HTTPException(413, f"Bestand te groot (max {MAX_SIZE_BYTES // 1024 // 1024}MB)")
    if len(content) == 0:
        raise HTTPException(400, "Leeg bestand")

    original_name = file.filename or "untitled"
    category = _detect_category(original_name)
    ext = Path(original_name).suffix.lower()

    file_id = uuid.uuid4().hex[:12]
    safe_name = f"{file_id}{ext}"
    dest = user_dir / category / safe_name

    with open(dest, "wb") as f:
        f.write(content)

    entry = {
        "id": file_id,
        "filename": safe_name,
        "original_name": original_name,
        "category": category,
        "extension": ext,
        "mime_type": file.content_type or "application/octet-stream",
        "size_bytes": len(content),
        "description": description or "",
        "tags": [t.strip() for t in (tags or "").split(",") if t.strip()],
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "uploaded_by": user_id,
        "path": str(dest),
    }

    files = _load_index(user_id)
    files.append(entry)
    _save_index(user_id, files)

    return {"success": True, "file": _public_entry(entry)}


def _public_entry(e: dict) -> dict:
    """Strip absolute path; expose download URL."""
    pub = {k: v for k, v in e.items() if k != "path"}
    pub["download_url"] = f"/api/archive/{e['uploaded_by']}/file/{e['id']}"
    return pub


# ============================================================
# LIST + SEARCH
# ============================================================

@router.get("/{user_id}")
async def list_files(
    user_id: str,
    category: Optional[str] = Query(None, description="bestanden|foto|geluiden|filmpjes"),
    q: Optional[str] = Query(None, description="zoekterm in naam/desc/tags"),
):
    """Lijst alle archief-bestanden van user, optioneel gefilterd op categorie + zoek."""
    _user_dir(user_id)  # ensure dirs exist
    files = _load_index(user_id)

    if category:
        if category not in CATEGORIES:
            raise HTTPException(400, f"Onbekende categorie: {category}")
        files = [f for f in files if f.get("category") == category]

    if q:
        q_low = q.lower().strip()
        files = [
            f for f in files
            if q_low in (f.get("original_name", "") or "").lower()
            or q_low in (f.get("description", "") or "").lower()
            or any(q_low in t.lower() for t in (f.get("tags") or []))
        ]

    # Sorteer op nieuwste eerst
    files = sorted(files, key=lambda x: x.get("uploaded_at", ""), reverse=True)

    # Statistieken per categorie
    all_files = _load_index(user_id)
    stats = {cat: 0 for cat in CATEGORIES}
    total_bytes = 0
    for f in all_files:
        cat = f.get("category", "bestanden")
        if cat in stats:
            stats[cat] += 1
        total_bytes += f.get("size_bytes", 0)

    return {
        "user_id": user_id,
        "files": [_public_entry(f) for f in files],
        "total": len(files),
        "stats": {
            "counts": stats,
            "total_files": len(all_files),
            "total_size_bytes": total_bytes,
        },
    }


# ============================================================
# DOWNLOAD
# ============================================================

@router.get("/{user_id}/file/{file_id}")
async def download_file(user_id: str, file_id: str):
    """Download/stream een bestand."""
    files = _load_index(user_id)
    entry = next((f for f in files if f.get("id") == file_id), None)
    if not entry:
        raise HTTPException(404, "Bestand niet gevonden")
    path = Path(entry.get("path", ""))
    if not path.exists():
        raise HTTPException(404, "Bestand bestaat niet meer op disk")
    return FileResponse(
        path=str(path),
        media_type=entry.get("mime_type", "application/octet-stream"),
        filename=entry.get("original_name", "download"),
    )


# ============================================================
# UPDATE METADATA
# ============================================================

class UpdateMeta(BaseModel):
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    original_name: Optional[str] = None


@router.put("/{user_id}/{file_id}")
async def update_metadata(user_id: str, file_id: str, body: UpdateMeta):
    """Update beschrijving, tags of weergave-naam."""
    files = _load_index(user_id)
    found = False
    for f in files:
        if f.get("id") == file_id:
            if body.description is not None:
                f["description"] = body.description
            if body.tags is not None:
                f["tags"] = body.tags
            if body.original_name:
                f["original_name"] = body.original_name
            f["updated_at"] = datetime.now(timezone.utc).isoformat()
            found = True
            break
    if not found:
        raise HTTPException(404, "Bestand niet gevonden")
    _save_index(user_id, files)
    return {"success": True}


# ============================================================
# DELETE
# ============================================================

@router.delete("/{user_id}/{file_id}")
async def delete_file(user_id: str, file_id: str):
    """Verwijder bestand + index entry."""
    files = _load_index(user_id)
    entry = next((f for f in files if f.get("id") == file_id), None)
    if not entry:
        raise HTTPException(404, "Bestand niet gevonden")
    path = Path(entry.get("path", ""))
    if path.exists():
        try:
            path.unlink()
        except OSError:
            pass
    files = [f for f in files if f.get("id") != file_id]
    _save_index(user_id, files)
    return {"success": True}


# ============================================================
# STATS (los endpoint voor dashboard)
# ============================================================

@router.get("/{user_id}/stats")
async def get_stats(user_id: str):
    """Quick stats voor user archief."""
    _user_dir(user_id)
    files = _load_index(user_id)
    counts = {cat: 0 for cat in CATEGORIES}
    total_bytes = 0
    for f in files:
        cat = f.get("category", "bestanden")
        if cat in counts:
            counts[cat] += 1
        total_bytes += f.get("size_bytes", 0)
    return {
        "user_id": user_id,
        "total_files": len(files),
        "total_size_bytes": total_bytes,
        "counts": counts,
        "categories": CATEGORIES,
    }
