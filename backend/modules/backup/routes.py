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
# v7_persistent_marker_001 — /app/backend/data/ wordt bij server-reset gewist,
# waardoor de marker verdwijnt en "alleen gewijzigd" backup het HELE systeem inpakt.
# /app/memory/ overleeft resets (bevat PRD/CHANGELOG). Marker eerst daar lezen/schrijven,
# fallback naar oude locatie voor backwards-compat.
MARKER_FILE_PERSISTENT = Path("/app/memory") / ".deploy_marker.json"

# Folders/files we never want to ship in a backup
EXCLUDE_NAMES = {".deploy_marker.json", "__pycache__", ".DS_Store"}

# v13c_backup_exclude_prefixes_001 — Backup-in-backup-inception voorkomen.
# Deze paden (relatief aan APP_ROOT) worden nooit meegenomen in geen enkele
# backup-slice. Waarom: `_backup_*` en `_backups/` bevatten oude backup-ZIPs
# en pre-merge-snapshots die anders elke volgende backup ~500-700MB opblazen.
EXCLUDE_REL_PREFIXES = (
    "backend/data/_backup_",           # backup_before_prod_merge_YYYYMMDD, backup_pre_prod_merge_*
    "backend/data/_backups/",          # verzamelmap voor rolling backups
    "backend/data/_archive/",          # oude archief-map
    "backend/data/_deleted_containers/",
    "backend/data/_deleted_users/",
)

# Roots that are included in backups (relative to APP_ROOT)
BACKUP_SOURCES = [
    ("backend/data", DATA_ROOT),
    ("memory", MEMORY_ROOT),
]


# ============== HELPERS ==============
def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_marker() -> Dict[str, Any]:
    # v7_persistent_marker_001 — probeer persistent locatie eerst
    for candidate in (MARKER_FILE_PERSISTENT, MARKER_FILE):
        if candidate.exists():
            try:
                return json.loads(candidate.read_text(encoding="utf-8"))
            except Exception:
                continue
    return {"marked_at": None, "marked_at_epoch": 0.0}


def _write_marker() -> Dict[str, Any]:
    # v7_persistent_marker_001 — schrijf naar BEIDE locaties zodat we backwards-compat
    # blijven én de marker een server-reset overleeft.
    MARKER_FILE_PERSISTENT.parent.mkdir(parents=True, exist_ok=True)
    MARKER_FILE.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    payload = {
        "marked_at": now.isoformat(),
        "marked_at_epoch": now.timestamp(),
        "note": "Markeert moment van laatste deploy. Bestanden gewijzigd na deze tijd zitten in een 'wijzigingen-backup'.",
        "written_to": ["persistent (/app/memory/)", "legacy (backend/data/system/)"],
    }
    text = json.dumps(payload, indent=2)
    MARKER_FILE_PERSISTENT.write_text(text, encoding="utf-8")
    try:
        MARKER_FILE.write_text(text, encoding="utf-8")
    except Exception:
        pass  # legacy locatie is best-effort
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
    """Collect files from all backup sources, optionally filtered by mtime > since_epoch.

    v13c_backup_exclude_prefixes_001 — filtert oude backup-dirs (`_backup_*`,
    `_backups/`, `_archive/`, `_deleted_*`) uit zodat backup-in-backup-inception
    stopt. Deze paden groeien elke deploy-cyclus en blazen anders elke volgende
    'alleen wijzigingen'-download honderden MB's op.
    """
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
            rel_str = str(rel).replace("\\", "/")
            if any(rel_str.startswith(p) for p in EXCLUDE_REL_PREFIXES):
                continue
            items.append({
                "abs": str(fpath),
                "rel": rel_str,
                "size": fpath.stat().st_size,
                "mtime": mtime,
                "mtime_iso": datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat(),
            })
    return items


# v13c_backup_split_001 — Split "alleen wijzigingen" in 3 stukken zodat de
# zip niet te groot wordt bij intensief chat/trade-gebruik. Elk pad-prefix
# (relatief aan APP_ROOT) valt in exact één slice.
CHAT_PREFIXES = (
    "backend/data/chat/",
    "backend/data/chat_analytics/",
    "backend/data/dialogen/",
    "backend/data/dagboek/",
)
CHAT_EXACT_FILES = (
    "backend/data/chat_sessions.json",
    "backend/data/conversation_triggers.json",
)
TRADER_PREFIXES = (
    "backend/data/trade/",
    "backend/data/financial/",
    "backend/data/bitvavo/",
)


def _slice_of(rel: str) -> str:
    """Return 'chat', 'trader' of 'rest' voor een backup-relatief pad."""
    rel_norm = rel.replace("\\", "/")
    if rel_norm in CHAT_EXACT_FILES:
        return "chat"
    for p in CHAT_PREFIXES:
        if rel_norm.startswith(p):
            return "chat"
    for p in TRADER_PREFIXES:
        if rel_norm.startswith(p):
            return "trader"
    return "rest"


def _collect_files_sliced(since_epoch: float, slice_name: str) -> List[Dict[str, Any]]:
    """Zelfde als _collect_files maar filtert op één slice ('chat'/'trader'/'rest')."""
    files = _collect_files(since_epoch=since_epoch)
    return [f for f in files if _slice_of(f["rel"]) == slice_name]


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


@router.get("/kb-changed-since-deploy")
async def kb_changed_since_deploy():
    """v5_kb_diff_export_001 — Export kennis-kaarten gewijzigd na laatste deploy.
    v6_v2_first_001 — Leest nu V2 (4 lades + inbox), niet meer V1.
    Detecteert wijziging via updated_at (top-level of metadata) vs deploy-marker.
    """
    marker = _read_marker()
    marker_iso = marker.get("marked_at") or "1970-01-01T00:00:00+00:00"

    v2_dir = DATA_ROOT / "knowledge" / "v2"
    all_entries = []
    for fname in ["knowledge_v2_doen", "knowledge_v2_weten",
                  "knowledge_v2_voelen", "knowledge_v2_spreken",
                  "knowledge_inbox"]:
        fp = v2_dir / f"{fname}.json"
        if not fp.exists():
            continue
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
        except Exception:
            continue
        all_entries.extend(data.get("kaarten", []) or [])

    if not all_entries:
        raise HTTPException(404, "Geen V2 kaarten gevonden")

    changed = []
    for e in all_entries:
        upd = e.get("updated_at") or (e.get("metadata") or {}).get("updated_at") or ""
        created = e.get("created_at") or (e.get("metadata") or {}).get("created_at") or ""
        if (upd and upd > marker_iso) or (created and created > marker_iso):
            changed.append(e)

    payload = {
        "type": "kb_diff_since_deploy",
        "schema": "v2",
        "exported_at": _iso_now(),
        "deploy_marker": marker_iso,
        "total_entries_in_kb": len(all_entries),
        "changed_count": len(changed),
        "note": "V2 kaarten met updated_at OF created_at NA deploy. Merge in preview via /api/knowledge/import-diff.",
        "knowledge_entries": changed,
    }

    # Stream als file zodat browser-download netjes triggered
    fname = f"spark_kb_diff_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    body = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
    from fastapi.responses import Response
    return Response(
        content=body,
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="{fname}"',
            "X-KB-Changed-Count": str(len(changed)),
            "X-KB-Total": str(len(all_entries)),
            "Cache-Control": "no-store",
        },
    )




@router.get("/download/changes")
async def download_changes(fallback_hours: int = 24):
    """Backup met alleen bestanden gewijzigd na laatste deploy-marker.

    Als er geen marker is (bijv. na server-reset waar de marker-file uit
    /app/backend/data verloren ging), val terug op `fallback_hours` (default 24u)
    zodat de zip niet stiekem het hele systeem inpakt.
    """
    marker = _read_marker()
    since = float(marker.get("marked_at_epoch") or 0.0)
    marker_missing = since <= 0.0
    if marker_missing:
        # v7_persistent_marker_002 — fallback zodat we niet per ongeluk 300MB opsturen
        fallback_epoch = datetime.now(timezone.utc).timestamp() - (fallback_hours * 3600)
        since = fallback_epoch
    files = _collect_files(since_epoch=since)
    meta = {
        "type": "changes_since_deploy",
        "created_at": _iso_now(),
        "marker": marker,
        "marker_missing": marker_missing,
        "fallback_used_hours": fallback_hours if marker_missing else None,
        "file_count": len(files),
        "sources": [str(r) for _, r in BACKUP_SOURCES],
        "files": [{"path": f["rel"], "size": f["size"], "mtime": f["mtime_iso"]} for f in files],
    }
    zip_path = _make_zip_file(files, meta)
    size = zip_path.stat().st_size
    label = "changes" if not marker_missing else f"changes_fallback_{fallback_hours}h"
    fname = f"spark_backup_{label}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.zip"
    return FileResponse(
        str(zip_path),
        media_type="application/zip",
        filename=fname,
        headers={
            "Content-Length": str(size),
            "X-Backup-Bytes": str(size),
            "X-Backup-Files": str(len(files)),
            "X-Marker-Missing": "1" if marker_missing else "0",
            "X-Fallback-Hours": str(fallback_hours) if marker_missing else "0",
            "Cache-Control": "no-store",
        },
        background=_cleanup_task(zip_path),
    )


# v13c_backup_split_001 — Drie aparte "alleen wijzigingen"-endpoints per slice
# zodat een intensieve chat- of trade-sessie geen 300MB-ZIP oplevert waar
# een KB-wijziging in verdrinkt.

def _download_changes_slice(slice_name: str, fallback_hours: int) -> FileResponse:
    """Gedeelde helper voor de drie slice-endpoints."""
    if slice_name not in ("chat", "trader", "rest"):
        raise HTTPException(status_code=400, detail=f"Onbekende slice: {slice_name}")
    marker = _read_marker()
    since = float(marker.get("marked_at_epoch") or 0.0)
    marker_missing = since <= 0.0
    if marker_missing:
        since = datetime.now(timezone.utc).timestamp() - (fallback_hours * 3600)
    files = _collect_files_sliced(since_epoch=since, slice_name=slice_name)
    meta = {
        "type": f"changes_since_deploy_{slice_name}",
        "slice": slice_name,
        "created_at": _iso_now(),
        "marker": marker,
        "marker_missing": marker_missing,
        "fallback_used_hours": fallback_hours if marker_missing else None,
        "file_count": len(files),
        "sources": [str(r) for _, r in BACKUP_SOURCES],
        "slice_prefixes": {
            "chat": {"prefixes": list(CHAT_PREFIXES), "exact_files": list(CHAT_EXACT_FILES)},
            "trader": {"prefixes": list(TRADER_PREFIXES), "exact_files": []},
            "rest": {"description": "alles wat niet onder chat/trader valt"},
        }[slice_name],
        "files": [{"path": f["rel"], "size": f["size"], "mtime": f["mtime_iso"]} for f in files],
    }
    zip_path = _make_zip_file(files, meta)
    size = zip_path.stat().st_size
    label = f"changes_{slice_name}" if not marker_missing else f"changes_{slice_name}_fallback_{fallback_hours}h"
    fname = f"spark_backup_{label}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.zip"
    return FileResponse(
        str(zip_path),
        media_type="application/zip",
        filename=fname,
        headers={
            "Content-Length": str(size),
            "X-Backup-Bytes": str(size),
            "X-Backup-Files": str(len(files)),
            "X-Backup-Slice": slice_name,
            "X-Marker-Missing": "1" if marker_missing else "0",
            "X-Fallback-Hours": str(fallback_hours) if marker_missing else "0",
            "Cache-Control": "no-store",
        },
        background=_cleanup_task(zip_path),
    )


@router.get("/download/changes/chat")
async def download_changes_chat(fallback_hours: int = 24):
    """Backup met alleen gesprek-log wijzigingen: data/chat, data/chat_analytics,
    data/dagboek, data/dialogen + chat_sessions.json + conversation_triggers.json."""
    return _download_changes_slice("chat", fallback_hours)


@router.get("/download/changes/trader")
async def download_changes_trader(fallback_hours: int = 24):
    """Backup met alleen trader-wijzigingen: data/trade, data/financial, data/bitvavo."""
    return _download_changes_slice("trader", fallback_hours)


@router.get("/download/changes/rest")
async def download_changes_rest(fallback_hours: int = 24):
    """Backup met alle overige wijzigingen sinds laatste deploy — dus zonder
    chat-slice en zonder trader-slice. Voor kleine, snel-mergebare exports
    van KB / config / notes / persons / achievements / etc."""
    return _download_changes_slice("rest", fallback_hours)


@router.get("/download/changes/sizes")
async def download_changes_sizes(fallback_hours: int = 24):
    """Voorbereidings-endpoint: geeft aantal bestanden + totale bytes per slice
    terug zodat de UI weet hoe groot elke download wordt vóór klikken."""
    marker = _read_marker()
    since = float(marker.get("marked_at_epoch") or 0.0)
    marker_missing = since <= 0.0
    if marker_missing:
        since = datetime.now(timezone.utc).timestamp() - (fallback_hours * 3600)
    all_files = _collect_files(since_epoch=since)
    summary = {"chat": {"files": 0, "bytes": 0},
               "trader": {"files": 0, "bytes": 0},
               "rest": {"files": 0, "bytes": 0},
               "total": {"files": len(all_files), "bytes": sum(f["size"] for f in all_files)}}
    for f in all_files:
        s = _slice_of(f["rel"])
        summary[s]["files"] += 1
        summary[s]["bytes"] += f["size"]
    return {
        "marker": marker,
        "marker_missing": marker_missing,
        "fallback_used_hours": fallback_hours if marker_missing else None,
        "sizes": summary,
    }


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

    v13_pre_merge_scan_001 (sessie 54): tip Willem's ATOM-KB-incident van 23 aug —
    dubbele check via `POST /backup/pre-scan` VÓÓR restore om te zien welke files
    de ZIP kleiner maakt dan wat er nu staat (dataverlies-risico).
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
            from modules.local_storage import persist_upload_bytes
            persist_upload_bytes(target, data)
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



# v13_pre_merge_scan_001 (sessie 54) — Scan een ZIP vóór merge zodat gebruiker
# kan zien welke files zouden krimpen / veranderen. Geen writes.
@router.post("/pre-scan")
async def pre_merge_scan(file: UploadFile = File(...)):
    """Scan ZIP en vergelijk met huidige /data.

    Return:
      - summary: telling per verdict
      - risks: files die kleiner worden of anders zijn (potentieel dataverlies)
      - safe_count: aantal files die veilig zijn (NEW, IDENTICAL, ZIP_LARGER)

    Willem's use-case: check vóór merge of hij preview-werk niet overschrijft
    met een productie-ZIP die achterloopt.
    """
    import io as _io
    import tempfile as _tempfile

    content = await file.read()
    # Schrijf tijdelijk naar disk voor pre_merge_scan
    with _tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        from .pre_merge_scan import scan_zip_vs_current
        result = scan_zip_vs_current(tmp_path)
        result["filename"] = file.filename
        result["size_bytes"] = len(content)
        return result
    finally:
        try:
            import os as _os
            _os.unlink(tmp_path)
        except Exception:
            pass
