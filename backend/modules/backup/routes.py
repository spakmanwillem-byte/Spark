"""
Spark Backup Module
-------------------
Standalone backup/restore systeem voor Spark data (offline-first filosofie).

Endpoints:
  POST /api/backup/mark-deployed     - Zet "laatste deploy" marker op huidige timestamp
  GET  /api/backup/status            - Toon marker timestamp + lijst gewijzigde bestanden
  GET  /api/backup/download/full     - Download complete ZIP (alle data + memory)
  GET  /api/backup/download/changes  - Download ZIP met alleen gewijzigde bestanden sinds marker
  POST /api/backup/restore/preview   - Upload ZIP en zie wat er gemerged zou worden (geen schrijven)
  POST /api/backup/restore           - Upload ZIP en merge daadwerkelijk (alleen overschrijven, niets verwijderen)

Scope:
  /app/backend/data/   (knowledge, personality, triggers, etc.)
  /app/memory/         (PRD, roadmap, notes)
"""
import io
import json
import zipfile
import tempfile
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any

from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import StreamingResponse, FileResponse

router = APIRouter(prefix="/backup", tags=["backup"])

# ============== PATHS ==============
APP_ROOT = Path("/app")
DATA_ROOT = APP_ROOT / "backend" / "data"
MEMORY_ROOT = APP_ROOT / "memory"
MARKER_FILE = DATA_ROOT / "system" / ".deploy_marker.json"

# Folders/files we never want to ship in a backup
EXCLUDE_NAMES = {".deploy_marker.json", "__pycache__", ".DS_Store"}

# Roots that are included in backups (relative to APP_ROOT)
BACKUP_SOURCES = [
    ("backend/data", DATA_ROOT),
    ("memory", MEMORY_ROOT),
]


# ============== HELPERS ==============
def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_marker() -> Dict[str, Any]:
    if not MARKER_FILE.exists():
        return {"marked_at": None, "marked_at_epoch": 0.0}
    try:
        return json.loads(MARKER_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"marked_at": None, "marked_at_epoch": 0.0}


def _write_marker() -> Dict[str, Any]:
    MARKER_FILE.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    payload = {
        "marked_at": now.isoformat(),
        "marked_at_epoch": now.timestamp(),
        "note": "Markeert moment van laatste deploy. Bestanden gewijzigd na deze tijd zitten in een 'wijzigingen-backup'.",
    }
    MARKER_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def _iter_files(root: Path):
    """Yield (absolute_path, relative_path_to_root) for every file under root, skipping excludes."""
    if not root.exists():
        return
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in EXCLUDE_NAMES for part in path.parts):
            continue
        yield path


def _collect_files(since_epoch: float = 0.0) -> List[Dict[str, Any]]:
    """Collect files from all backup sources, optionally filtered by mtime > since_epoch."""
    items = []
    for prefix, root in BACKUP_SOURCES:
        for fpath in _iter_files(root):
            mtime = fpath.stat().st_mtime
            if mtime <= since_epoch:
                continue
            try:
                rel = fpath.relative_to(APP_ROOT)
            except ValueError:
                continue
            items.append({
                "abs": str(fpath),
                "rel": str(rel),  # bv "backend/data/knowledge/knowledge_base.json"
                "size": fpath.stat().st_size,
                "mtime": mtime,
                "mtime_iso": datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat(),
            })
    return items


def _make_zip_file(files: List[Dict[str, Any]], meta: Dict[str, Any]) -> Path:
    """v4_backup_stream_001 — schrijf ZIP naar disk-tempfile (NIET in RAM).

    Voor grote backups (16MB+) voorkomt dit dat alles eerst in RAM moet zitten
    en de browser timeout omdat de response pas begint na alle compressie.
    """
    tmp = Path(tempfile.mkstemp(prefix="spark_backup_", suffix=".zip")[1])
    with zipfile.ZipFile(str(tmp), "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        zf.writestr("spark_backup_manifest.json", json.dumps(meta, indent=2))
        for item in files:
            try:
                zf.write(item["abs"], arcname=item["rel"])
            except (OSError, ValueError):
                continue
    # Sanity test (cheap: just open, niet testzip op alles → testzip is duur bij grote files)
    try:
        with zipfile.ZipFile(str(tmp)) as test_zf:
            _ = test_zf.namelist()  # alleen index parsen, geen CRC check
    except zipfile.BadZipFile as e:
        try:
            tmp.unlink()
        except OSError:
            pass
        raise RuntimeError(f"Backup ZIP validatie faalde: {e}")
    return tmp


def _make_zip(files: List[Dict[str, Any]], meta: Dict[str, Any]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # Manifest first
        zf.writestr("spark_backup_manifest.json", json.dumps(meta, indent=2))
        for item in files:
            try:
                zf.write(item["abs"], arcname=item["rel"])
            except (OSError, ValueError):
                # Skip onleesbare files, log naar manifest later
                continue
    data = buf.getvalue()
    # v4_backup_integrity_001 — validate zip before returning
    if data[-22:].find(b"PK\x05\x06") == -1:
        # EOCD niet aan einde gevonden → probeer ergens in de laatste 64KB
        if data.rfind(b"PK\x05\x06") == -1:
            raise RuntimeError("Backup ZIP heeft geen EOCD — corrupt (interne fout)")
    # Sanity test: open in zipfile
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as test_zf:
            bad = test_zf.testzip()
            if bad is not None:
                raise RuntimeError(f"Backup ZIP corrupt entry: {bad}")
    except zipfile.BadZipFile as e:
        raise RuntimeError(f"Backup ZIP validatie faalde: {e}")
    return data


def _safe_target_from_rel(rel: str) -> Path:
    """Convert a manifest-relative path (e.g. 'backend/data/.../foo.json') to absolute /app/... and refuse escapes."""
    # Strip leading slashes and 'app/' if present
    rel = rel.lstrip("/").replace("\\", "/")
    if rel.startswith("app/"):
        rel = rel[4:]
    target = (APP_ROOT / rel).resolve()
    # Must be under either DATA_ROOT or MEMORY_ROOT
    allowed_roots = [DATA_ROOT.resolve(), MEMORY_ROOT.resolve()]
    if not any(str(target).startswith(str(r)) for r in allowed_roots):
        raise ValueError(f"Pad buiten toegestane scope: {rel}")
    return target


# ============== ROUTES ==============
def _cleanup_task(path: Path):
    """Background task die tempfile verwijdert nadat FileResponse klaar is."""
    from starlette.background import BackgroundTask

    def _do():
        try:
            if path.exists():
                path.unlink()
        except OSError:
            pass
    return BackgroundTask(_do)


@router.post("/mark-deployed")
async def mark_deployed():
    """Zet de 'laatste deploy' marker op nu. Roep dit aan direct NA een succesvolle deploy."""
    payload = _write_marker()
    return {"ok": True, "marker": payload}


@router.get("/status")
async def status():
    """Toon status: marker timestamp + aantal/lijst bestanden gewijzigd sinds marker."""
    marker = _read_marker()
    since = float(marker.get("marked_at_epoch") or 0.0)

    changed = _collect_files(since_epoch=since)
    all_files = _collect_files(since_epoch=0.0)

    # Lichte preview: alleen rel + size + mtime_iso
    def _light(item):
        return {"path": item["rel"], "size": item["size"], "mtime": item["mtime_iso"]}

    return {
        "marker": marker,
        "total_files": len(all_files),
        "changed_files_count": len(changed),
        "changed_files": [_light(x) for x in sorted(changed, key=lambda i: -i["mtime"])][:500],
        "sources": [str(r) for _, r in BACKUP_SOURCES],
        "now": _iso_now(),
    }


@router.post("/anchor")
async def anchor_download():
    """v4_mr_smith_001: log download als 'anchor' event (Spark's geheugen verplaatst naar zip)."""
    anchor_file = Path(__file__).parent.parent.parent / "data" / "system" / "backup_anchors.json"
    anchor_file.parent.mkdir(parents=True, exist_ok=True)
    data = {}
    if anchor_file.exists():
        try:
            data = json.loads(anchor_file.read_text())
        except Exception:
            data = {}
    data.setdefault("anchors", []).append({
        "ts": _iso_now(),
        "note": "User downloaded backup zip. Mr Smith warning shown and accepted.",
    })
    anchor_file.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    return {"ok": True, "total_anchors": len(data["anchors"])}


@router.get("/download/full")
async def download_full():
    """Volledige backup: alle bestanden onder /app/backend/data + /app/memory."""
    files = _collect_files(since_epoch=0.0)
    meta = {
        "type": "full",
        "created_at": _iso_now(),
        "file_count": len(files),
        "sources": [str(r) for _, r in BACKUP_SOURCES],
        "files": [{"path": f["rel"], "size": f["size"], "mtime": f["mtime_iso"]} for f in files],
    }
    # v4_backup_stream_001 — schrijf naar disk en stream als FileResponse
    zip_path = _make_zip_file(files, meta)
    size = zip_path.stat().st_size
    fname = f"spark_backup_full_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.zip"
    return FileResponse(
        str(zip_path),
        media_type="application/zip",
        filename=fname,
        headers={
            "Content-Length": str(size),
            "X-Backup-Bytes": str(size),
            "X-Backup-Files": str(len(files)),
            "Cache-Control": "no-store",
        },
        background=_cleanup_task(zip_path),
    )


@router.get("/download/changes")
async def download_changes():
    """Backup met alleen bestanden gewijzigd na laatste deploy-marker."""
    marker = _read_marker()
    since = float(marker.get("marked_at_epoch") or 0.0)
    files = _collect_files(since_epoch=since)
    meta = {
        "type": "changes_since_deploy",
        "created_at": _iso_now(),
        "marker": marker,
        "file_count": len(files),
        "sources": [str(r) for _, r in BACKUP_SOURCES],
        "files": [{"path": f["rel"], "size": f["size"], "mtime": f["mtime_iso"]} for f in files],
    }
    zip_path = _make_zip_file(files, meta)
    size = zip_path.stat().st_size
    label = "changes" if since > 0 else "no_marker_full_like"
    fname = f"spark_backup_{label}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.zip"
    return FileResponse(
        str(zip_path),
        media_type="application/zip",
        filename=fname,
        headers={
            "Content-Length": str(size),
            "X-Backup-Bytes": str(size),
            "X-Backup-Files": str(len(files)),
            "Cache-Control": "no-store",
        },
        background=_cleanup_task(zip_path),
    )


def _analyze_zip(content: bytes) -> Dict[str, Any]:
    """Open ZIP in-memory en classificeer entries als (nieuw / wijzig / skip)."""
    try:
        zf = zipfile.ZipFile(io.BytesIO(content))
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="Ongeldige ZIP file")

    results = {"new": [], "modified": [], "identical": [], "skipped": [], "manifest": None}
    for name in zf.namelist():
        if name.endswith("/"):
            continue
        if name == "spark_backup_manifest.json":
            try:
                results["manifest"] = json.loads(zf.read(name).decode("utf-8"))
            except Exception:
                results["manifest"] = {"error": "kon manifest niet lezen"}
            continue
        try:
            target = _safe_target_from_rel(name)
        except ValueError as e:
            results["skipped"].append({"path": name, "reason": str(e)})
            continue

        incoming_bytes = zf.read(name)
        if not target.exists():
            results["new"].append({"path": name, "size": len(incoming_bytes)})
        else:
            try:
                current = target.read_bytes()
            except Exception:
                current = b""
            if current == incoming_bytes:
                results["identical"].append({"path": name, "size": len(incoming_bytes)})
            else:
                results["modified"].append({
                    "path": name,
                    "incoming_size": len(incoming_bytes),
                    "current_size": len(current),
                })
    return results


@router.post("/restore/preview")
async def restore_preview(file: UploadFile = File(...)):
    """Upload ZIP en krijg een dry-run analyse. Geen bestanden worden gewijzigd."""
    content = await file.read()
    analysis = _analyze_zip(content)
    summary = {
        "filename": file.filename,
        "size_bytes": len(content),
        "new_count": len(analysis["new"]),
        "modified_count": len(analysis["modified"]),
        "identical_count": len(analysis["identical"]),
        "skipped_count": len(analysis["skipped"]),
        "manifest": analysis["manifest"],
    }
    return {"summary": summary, "details": analysis}


@router.post("/restore")
async def restore(file: UploadFile = File(...), confirm: str = Form("false")):
    """
    Voer de daadwerkelijke restore uit. MERGE-only:
      - Nieuwe bestanden worden toegevoegd
      - Bestaande bestanden worden overschreven met de versie uit de ZIP
      - Bestanden die WEL lokaal bestaan maar NIET in de ZIP zitten blijven onaangetast
    """
    if str(confirm).lower() not in ("true", "1", "yes", "ja"):
        raise HTTPException(status_code=400, detail="Bevestiging ontbreekt. Stuur 'confirm=true'.")

    content = await file.read()
    try:
        zf = zipfile.ZipFile(io.BytesIO(content))
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="Ongeldige ZIP file")

    written, created, skipped, errors = [], [], [], []
    for name in zf.namelist():
        if name.endswith("/"):
            continue
        if name == "spark_backup_manifest.json":
            continue
        try:
            target = _safe_target_from_rel(name)
        except ValueError as e:
            skipped.append({"path": name, "reason": str(e)})
            continue
        try:
            data = zf.read(name)
            existed = target.exists()
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            if existed:
                written.append(name)
            else:
                created.append(name)
        except Exception as e:
            errors.append({"path": name, "error": str(e)})

    # v4_storage_cache_001: invalideer alle cache na restore (extern geschreven files)
    try:
        from modules.core.storage import clear_cache
        clear_cache()
    except Exception:
        pass

    return {
        "ok": True,
        "created_count": len(created),
        "overwritten_count": len(written),
        "skipped_count": len(skipped),
        "error_count": len(errors),
        "created": created[:200],
        "overwritten": written[:200],
        "skipped": skipped,
        "errors": errors,
        "restored_at": _iso_now(),
    }
