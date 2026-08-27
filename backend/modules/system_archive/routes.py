"""
System Archive Routes — admin-only systeem opslag
Categorieën: bestanden | foto | geluiden | filmpjes | dialogen
Storage: /app/backend/data/system_archive/{category}/
Index:   /app/backend/data/system_archive/_index.json

Verschillen met user_archive:
- Geen quota
- Bedoeld voor systeem-resources (geluiden, dialogen voor Spark leer-materiaal)
- 'dialogen' is een unieke categorie met tags voor gespreks-types
"""
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel

from modules.core.storage import load_json, save_json

router = APIRouter(prefix="/system-archive", tags=["system-archive"])

ARCHIVE_DIR = Path(__file__).parent.parent.parent / "data" / "system_archive"
MAX_SIZE_BYTES = 100 * 1024 * 1024  # 100MB per file (groter voor systeem)

EXT_MAP = {
    "foto": {".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic", ".bmp", ".svg"},
    "geluiden": {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac", ".opus"},
    "filmpjes": {".mp4", ".webm", ".mov", ".avi", ".mkv", ".m4v"},
    "dialogen": {".txt", ".md", ".json", ".srt", ".vtt", ".rtf"},
}

CATEGORIES = ["bestanden", "foto", "geluiden", "filmpjes", "dialogen"]

# Pre-defined dialoog-tags (later in UI als suggesties)
DIALOG_TAGS = [
    "algemeen", "rauw", "afscheid", "vreugde", "delen",
    "verdrietig", "boos", "humor", "conflict", "vriendschap",
    "familie", "liefde", "professioneel", "informeel", "filosofisch",
    "kort", "lang", "monoloog", "tweegesprek", "groepsgesprek"
]


def _detect_category(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    for cat, exts in EXT_MAP.items():
        if ext in exts:
            return cat
    return "bestanden"


def _ensure_dirs():
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    for cat in CATEGORIES:
        (ARCHIVE_DIR / cat).mkdir(exist_ok=True)
    return ARCHIVE_DIR


def _index_file() -> Path:
    return _ensure_dirs() / "_index.json"


def _load_index() -> List[dict]:
    data = load_json(_index_file(), default={"files": []})
    return data.get("files", [])


def _save_index(files: List[dict]):
    save_json(_index_file(), {
        "files": files,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    })


def _public_entry(e: dict) -> dict:
    pub = {k: v for k, v in e.items() if k != "path"}
    pub["download_url"] = f"/api/system-archive/file/{e['id']}"
    return pub


# ============================================================
# UPLOAD
# ============================================================

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    category: Optional[str] = Form(None),  # forceer categorie (anders auto)
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    uploaded_by: Optional[str] = Form(None),  # admin user-id
):
    _ensure_dirs()
    content = await file.read()
    if len(content) > MAX_SIZE_BYTES:
        raise HTTPException(413, f"Bestand te groot (max {MAX_SIZE_BYTES // 1024 // 1024}MB)")
    if len(content) == 0:
        raise HTTPException(400, "Leeg bestand")

    original_name = file.filename or "untitled"
    cat = category if category in CATEGORIES else _detect_category(original_name)
    ext = Path(original_name).suffix.lower()
    file_id = uuid.uuid4().hex[:12]
    safe_name = f"{file_id}{ext}"
    from modules.local_storage import persist_upload_bytes
    dest = persist_upload_bytes(ARCHIVE_DIR / cat / safe_name, content)

    entry = {
        "id": file_id,
        "filename": safe_name,
        "original_name": original_name,
        "category": cat,
        "extension": ext,
        "mime_type": file.content_type or "application/octet-stream",
        "size_bytes": len(content),
        "description": description or "",
        "tags": [t.strip() for t in (tags or "").split(",") if t.strip()],
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "uploaded_by": uploaded_by or "system",
        "path": str(dest),
        # Dialoog-specifieke velden
        "scan_status": "pending" if cat == "dialogen" else None,
        "scan_results": None,
    }

    files = _load_index()
    files.append(entry)
    _save_index(files)
    return {"success": True, "file": _public_entry(entry)}


# ============================================================
# LIST + SEARCH
# ============================================================

@router.get("")
async def list_files(
    category: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
):
    _ensure_dirs()
    files = _load_index()

    if category:
        if category not in CATEGORIES:
            raise HTTPException(400, f"Onbekende categorie: {category}")
        files = [f for f in files if f.get("category") == category]
    if tag:
        files = [f for f in files if tag.lower() in [t.lower() for t in (f.get("tags") or [])]]
    if q:
        ql = q.lower().strip()
        files = [
            f for f in files
            if ql in (f.get("original_name", "") or "").lower()
            or ql in (f.get("description", "") or "").lower()
            or any(ql in t.lower() for t in (f.get("tags") or []))
        ]
    files = sorted(files, key=lambda x: x.get("uploaded_at", ""), reverse=True)

    # Stats
    all_files = _load_index()
    counts = {cat: 0 for cat in CATEGORIES}
    total_bytes = 0
    for f in all_files:
        cat = f.get("category", "bestanden")
        if cat in counts:
            counts[cat] += 1
        total_bytes += f.get("size_bytes", 0)

    return {
        "files": [_public_entry(f) for f in files],
        "total": len(files),
        "stats": {
            "counts": counts,
            "total_files": len(all_files),
            "total_size_bytes": total_bytes,
        },
        "available_tags": DIALOG_TAGS,
    }


@router.get("/stats")
async def get_stats():
    _ensure_dirs()
    files = _load_index()
    counts = {cat: 0 for cat in CATEGORIES}
    total_bytes = 0
    for f in files:
        cat = f.get("category", "bestanden")
        if cat in counts:
            counts[cat] += 1
        total_bytes += f.get("size_bytes", 0)
    return {
        "total_files": len(files),
        "total_size_bytes": total_bytes,
        "counts": counts,
        "categories": CATEGORIES,
        "available_tags": DIALOG_TAGS,
    }


# ============================================================
# DOWNLOAD
# ============================================================

@router.get("/file/{file_id}")
async def download_file(file_id: str):
    files = _load_index()
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


@router.put("/{file_id}")
async def update_metadata(file_id: str, body: UpdateMeta):
    files = _load_index()
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
    _save_index(files)
    return {"success": True}


# ============================================================
# DELETE
# ============================================================

@router.delete("/{file_id}")
async def delete_file(file_id: str):
    files = _load_index()
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
    _save_index(files)
    return {"success": True}


# ============================================================
# PUBLIC: Geluiden alias (gebruikt door Instellingen > Geluid)
# Toont alleen audio-bestanden uit systeem-archief
# ============================================================

@router.get("/sounds")
async def list_sounds():
    """Snel-overzicht voor de sound-mapping UI in Instellingen."""
    _ensure_dirs()
    files = _load_index()
    sounds = [_public_entry(f) for f in files if f.get("category") == "geluiden"]
    sounds.sort(key=lambda x: x.get("uploaded_at", ""), reverse=True)
    return {"sounds": sounds, "total": len(sounds)}
