"""
KB v2 Media Routes (v5_kbv2_media_002 — refactored to use System Archive)
==========================================================================
Media van kennis-kaarten (voice + image) wordt opgeslagen in het centrale
System Archive (Beheer → Instellingen → Archief → Foto/Geluiden) met de
tag `kbv2` + `kbv2_card_<id>` + veld `linked_card_id`.

Voordeel: 1 centrale media-store, sub-tabs in Archive tonen kennis-kaart
gebonden items naast losse uploads. Geen duplicate-storage.

POST /api/kb/v2/media/voice    multipart: audio + card_id + lade
                               → opslaan in system_archive/geluiden + transcribeer
POST /api/kb/v2/media/image    multipart: image + card_id + lade
                               → opslaan in system_archive/foto + linken aan kaart
"""
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, List

from dotenv import load_dotenv
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel

from modules.core.spark_logger import traced
from modules.core.storage import load_json, save_json
from . import service

load_dotenv()

# System archive paden (delen met /api/system-archive)
SA_DIR = Path(__file__).parent.parent.parent / "data" / "system_archive"
SA_INDEX = SA_DIR / "_index.json"

ALLOWED_AUDIO = {".webm", ".mp3", ".wav", ".m4a", ".mp4", ".mpga", ".mpeg", ".ogg", ".opus"}
ALLOWED_IMAGE = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}
MAX_AUDIO_MB = 24
MAX_IMAGE_MB = 8

router = APIRouter(prefix="/kb/v2/media", tags=["kb-v2-media"])


# ---------------------------------------------------------------------------
# Helpers — schrijf naar system_archive met kbv2-tag
# ---------------------------------------------------------------------------

def _save_to_system_archive(
    content: bytes, original_name: str, category: str,
    card_id: str, user_id: str, mime_type: str = "application/octet-stream",
    extra_meta: Optional[dict] = None,
) -> dict:
    """Schrijf bytes naar system_archive/{category}/ + voeg index-entry toe.
    Tagt automatisch met 'kbv2' + 'kbv2_card_<id>' zodat UI kan filteren.

    v7_media_dedup_001 — Content-hash dedup:
    Als exact dezelfde bytes al bestaan (md5 match), hergebruik dan de bestaande
    file + entry. We voegen alleen `linked_card_id` extra tag toe zodat het
    _index.json weet dat meerdere kaarten deze afbeelding delen.
    """
    import hashlib as _hashlib
    SA_DIR.mkdir(parents=True, exist_ok=True)
    (SA_DIR / category).mkdir(parents=True, exist_ok=True)

    content_hash = _hashlib.md5(content).hexdigest()
    idx = load_json(SA_INDEX, default={"files": []})
    files_list = idx.setdefault("files", [])

    # Zoek bestaande file met dezelfde content-hash
    existing = None
    for f in files_list:
        if f.get("content_md5") == content_hash and f.get("category") == category:
            # Verifieer file bestaat nog op disk
            if f.get("path") and Path(f["path"]).exists():
                existing = f
                break

    if existing:
        # Hergebruik: link deze kaart aan bestaande entry
        card_tag = f"kbv2_card_{card_id}"
        tags = existing.setdefault("tags", [])
        if card_tag not in tags:
            tags.append(card_tag)
        linked_cards = existing.setdefault("linked_card_ids", [])
        if existing.get("linked_card_id") and existing["linked_card_id"] not in linked_cards:
            linked_cards.append(existing["linked_card_id"])
        if card_id not in linked_cards:
            linked_cards.append(card_id)
        existing["last_reused_at"] = datetime.now(timezone.utc).isoformat()
        existing.setdefault("reuse_count", 0)
        existing["reuse_count"] += 1
        idx["updated_at"] = datetime.now(timezone.utc).isoformat()
        save_json(SA_INDEX, idx)
        return existing

    # Nieuwe file: opslaan met hash-gebaseerde naam
    ext = Path(original_name).suffix.lower()
    file_id = content_hash[:12]  # kortere hash als file_id
    safe_name = f"{file_id}{ext}"
    dest = SA_DIR / category / safe_name
    dest.write_bytes(content)

    entry = {
        "id": file_id,
        "filename": safe_name,
        "original_name": original_name,
        "category": category,
        "extension": ext,
        "mime_type": mime_type,
        "size_bytes": len(content),
        "content_md5": content_hash,
        "description": f"Kennis-kaart media voor kaart {card_id}",
        "tags": ["kbv2", f"kbv2_card_{card_id}"],
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "uploaded_by": user_id,
        "path": str(dest),
        "linked_card_id": card_id,
        "linked_card_ids": [card_id],
        "source": "kbv2_media_upload",
        "scan_status": None,
        "scan_results": None,
        "reuse_count": 0,
    }
    if extra_meta:
        entry.update(extra_meta)

    files_list.append(entry)
    idx["updated_at"] = datetime.now(timezone.utc).isoformat()
    save_json(SA_INDEX, idx)

    return entry


def _system_archive_url(file_id: str) -> str:
    """Bestaande system-archive download endpoint."""
    return f"/api/system-archive/file/{file_id}"


def _resolve_lade(card_id: str) -> Optional[str]:
    """Vind lade van kaart via index."""
    idx = load_json(service._index_path(), default={"entries": {}})
    for begrip, e in (idx.get("entries") or {}).items():
        if e.get("kaart_id") == card_id:
            return e.get("lade")
    return None


def _patch_card_media(card_id: str, lade: Optional[str], media_update: dict, user_id: str):
    """Update media-velden op kaart in lade OF inbox."""
    if lade and lade in service.LADES:
        service.edit_card(card_id, lade, {"media": media_update}, user_id=user_id)
        return
    # Inbox-direct patch
    ip = service._inbox_path()
    inbox = load_json(ip, default={"kaarten": []})
    for k in inbox.get("kaarten", []):
        if k.get("id") == card_id:
            m = k.setdefault("media", {"voice_url": None, "voice_transcript": None, "image_urls": []})
            for key, val in media_update.items():
                if key == "image_urls" and isinstance(val, list):
                    m.setdefault("image_urls", []).extend(val)
                else:
                    m[key] = val
            # Auto-fill laag1 met transcript indien leeg
            if media_update.get("voice_transcript") and not (k.get("lagen", {}).get("laag1") or "").strip():
                k.setdefault("lagen", {})["laag1"] = media_update["voice_transcript"]
            k["needs"] = service._compute_needs(k)
            save_json(ip, inbox)
            return


# ---------------------------------------------------------------------------
# Voice (Whisper)
# ---------------------------------------------------------------------------

@router.post("/voice")
@traced(intent="audio voor kaart transcriberen + opslaan in system archive", module="kbv2", log_args=False)
async def upload_voice(
    audio: UploadFile = File(...),
    card_id: str = Form(...),
    lade: Optional[str] = Form(None),
    user_id: str = Form("user-000"),
):
    ext = Path(audio.filename or "audio.webm").suffix.lower()
    if ext not in ALLOWED_AUDIO:
        raise HTTPException(status_code=400, detail=f"Audio-type '{ext}' niet toegestaan")
    data = await audio.read()
    if len(data) > MAX_AUDIO_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"Audio te groot (>{MAX_AUDIO_MB}MB)")

    # Eerst opslaan in system_archive zodat we URL hebben (transcriptie kan falen)
    entry = _save_to_system_archive(
        content=data,
        original_name=audio.filename or f"inspraak_{card_id}.webm",
        category="geluiden",
        card_id=card_id,
        user_id=user_id,
        mime_type=audio.content_type or "audio/webm",
    )
    voice_url = _system_archive_url(entry["id"])

    # Whisper transcriptie
    transcript = ""
    try:
        from emergentintegrations.llm.openai import OpenAISpeechToText
        api_key = os.getenv("EMERGENT_LLM_KEY")
        if not api_key:
            raise RuntimeError("EMERGENT_LLM_KEY ontbreekt")
        stt = OpenAISpeechToText(api_key=api_key)
        with open(entry["path"], "rb") as f:
            resp = await stt.transcribe(
                file=f, model="whisper-1", response_format="json",
                language="nl",
                prompt="Spark Core kennis-kaart Nederlandse uitleg",
                temperature=0.0,
            )
        transcript = (getattr(resp, "text", None) or "").strip()
    except Exception as e:
        # Bestand bewaard, alleen transcriptie mislukt
        _patch_card_media(card_id, lade or _resolve_lade(card_id),
                          {"voice_url": voice_url, "voice_transcript": ""}, user_id)
        return {
            "success": False,
            "error": f"Transcriptie mislukt: {e}",
            "voice_url": voice_url,
            "voice_transcript": "",
            "archive_id": entry["id"],
        }

    # Update transcript-metadata in archive-entry zelf
    idx = load_json(SA_INDEX, default={"files": []})
    for f in idx.get("files", []):
        if f.get("id") == entry["id"]:
            f["scan_status"] = "transcribed"
            f["scan_results"] = {"transcript": transcript, "language": "nl"}
            f["description"] = (transcript[:120] + "...") if len(transcript) > 120 else transcript
            break
    save_json(SA_INDEX, idx)

    _patch_card_media(card_id, lade or _resolve_lade(card_id),
                      {"voice_url": voice_url, "voice_transcript": transcript}, user_id)

    # v6_kbv2_hooks_landing_001 — Hook 5: bewaar transcript ook als dialoog-snippet
    try:
        from . import hooks as kbv2_hooks
        kbv2_hooks.save_voice_snippet(transcript, card_id, user_id, voice_url=voice_url)
    except Exception:
        pass

    return {
        "success": True,
        "voice_url": voice_url,
        "voice_transcript": transcript,
        "archive_id": entry["id"],
        "size_bytes": len(data),
    }


# ---------------------------------------------------------------------------
# Image
# ---------------------------------------------------------------------------

@router.post("/image")
@traced(intent="foto voor kaart opslaan in system archive", module="kbv2", log_args=False)
async def upload_image(
    image: UploadFile = File(...),
    card_id: str = Form(...),
    lade: Optional[str] = Form(None),
    user_id: str = Form("user-000"),
):
    ext = Path(image.filename or "img.png").suffix.lower()
    if ext not in ALLOWED_IMAGE:
        raise HTTPException(status_code=400, detail=f"Image-type '{ext}' niet toegestaan")
    data = await image.read()
    if len(data) > MAX_IMAGE_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"Image te groot (>{MAX_IMAGE_MB}MB)")

    entry = _save_to_system_archive(
        content=data,
        original_name=image.filename or f"foto_{card_id}.png",
        category="foto",
        card_id=card_id,
        user_id=user_id,
        mime_type=image.content_type or "image/png",
    )
    image_url = _system_archive_url(entry["id"])

    # Update kaart: append aan image_urls
    target_lade = lade or _resolve_lade(card_id)
    if target_lade and target_lade in service.LADES:
        # Read current to avoid overwriting
        cur = load_json(service._lade_path(target_lade), default={"kaarten": []})
        for k in cur.get("kaarten", []):
            if k.get("id") == card_id:
                images = (k.get("media") or {}).get("image_urls") or []
                images.append(image_url)
                service.edit_card(card_id, target_lade, {"media": {"image_urls": images}}, user_id=user_id)
                break
    else:
        _patch_card_media(card_id, None, {"image_urls": [image_url]}, user_id)

    return {"success": True, "image_url": image_url, "archive_id": entry["id"], "size_bytes": len(data)}


# ---------------------------------------------------------------------------
# v6_kbv2_media_delete_001 — Delete media (voice OR specific image)
# ---------------------------------------------------------------------------

@router.delete("/voice/{card_id}")
@traced(intent="voice + transcript verwijderen van kaart", module="kbv2", log_args=False)
async def delete_voice(card_id: str, lade: Optional[str] = None, user_id: str = "user-000"):
    """Verwijder voice_url + transcript van kaart. Bestand blijft in archive."""
    target = lade or _resolve_lade(card_id)
    _patch_card_media(card_id, target, {"voice_url": None, "voice_transcript": None}, user_id)
    return {"success": True}


@router.delete("/image/{card_id}")
@traced(intent="één foto verwijderen van kaart", module="kbv2", log_args=False)
async def delete_image(card_id: str, image_url: str, lade: Optional[str] = None, user_id: str = "user-000"):
    """Verwijder één specifieke foto-URL uit kaart.media.image_urls.
    Bestand blijft bestaan in system_archive (alleen kaart-link verwijderd).
    """
    target_lade = lade or _resolve_lade(card_id)
    if target_lade and target_lade in service.LADES:
        cur = load_json(service._lade_path(target_lade), default={"kaarten": []})
        for k in cur.get("kaarten", []):
            if k.get("id") == card_id:
                images = (k.get("media") or {}).get("image_urls") or []
                images = [u for u in images if u != image_url]
                service.edit_card(card_id, target_lade, {"media": {"image_urls": images}}, user_id=user_id)
                return {"success": True, "remaining": len(images)}
    # Inbox-direct
    ip = service._inbox_path()
    inbox = load_json(ip, default={"kaarten": []})
    for k in inbox.get("kaarten", []):
        if k.get("id") == card_id:
            m = k.setdefault("media", {})
            m["image_urls"] = [u for u in (m.get("image_urls") or []) if u != image_url]
            k["needs"] = service._compute_needs(k)
            save_json(ip, inbox)
            return {"success": True, "remaining": len(m["image_urls"])}
    raise HTTPException(404, "Kaart niet gevonden")


# ---------------------------------------------------------------------------
# v6_kbv2_media_audio2_001 — 2e audio (spraak transcript) NAAST de hoofd-voice
# ---------------------------------------------------------------------------

@router.post("/voice/secondary")
@traced(intent="extra audio (spraak of geluid) opslaan bij kaart", module="kbv2", log_args=False)
async def upload_secondary_audio(
    audio: UploadFile = File(...),
    card_id: str = Form(...),
    lade: Optional[str] = Form(None),
    user_id: str = Form("user-000"),
    audio_kind: str = Form("spraak"),  # "spraak" of "geluid"
    transcribe: bool = Form(True),
):
    """Voeg 2e audio-track toe aan kaart.media.extra_audio[].
    Bij audio_kind=spraak en transcribe=True wordt ook Whisper aangeroepen.
    """
    ext = Path(audio.filename or "audio.webm").suffix.lower()
    if ext not in ALLOWED_AUDIO:
        raise HTTPException(status_code=400, detail=f"Audio-type '{ext}' niet toegestaan")
    data = await audio.read()
    if len(data) > MAX_AUDIO_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"Audio te groot (>{MAX_AUDIO_MB}MB)")

    entry = _save_to_system_archive(
        content=data,
        original_name=audio.filename or f"audio2_{card_id}.webm",
        category="geluiden",
        card_id=card_id,
        user_id=user_id,
        mime_type=audio.content_type or "audio/webm",
        extra_meta={"audio_kind": audio_kind},
    )
    url = _system_archive_url(entry["id"])

    transcript = ""
    if audio_kind == "spraak" and transcribe:
        try:
            from emergentintegrations.llm.openai import OpenAISpeechToText
            api_key = os.getenv("EMERGENT_LLM_KEY")
            if api_key:
                stt = OpenAISpeechToText(api_key=api_key)
                with open(entry["path"], "rb") as f:
                    resp = await stt.transcribe(file=f, model="whisper-1", response_format="json", language="nl", temperature=0.0)
                transcript = (getattr(resp, "text", None) or "").strip()
                idx = load_json(SA_INDEX, default={"files": []})
                for f2 in idx.get("files", []):
                    if f2.get("id") == entry["id"]:
                        f2["scan_status"] = "transcribed"
                        f2["scan_results"] = {"transcript": transcript, "language": "nl"}
                        break
                save_json(SA_INDEX, idx)
        except Exception as e:
            print(f"[kbv2 audio2] transcriptie skip: {e}")

    # Voeg toe aan extra_audio list
    item = {"url": url, "kind": audio_kind, "transcript": transcript, "archive_id": entry["id"],
            "added_at": datetime.now(timezone.utc).isoformat()}
    target_lade = lade or _resolve_lade(card_id)
    if target_lade and target_lade in service.LADES:
        cur = load_json(service._lade_path(target_lade), default={"kaarten": []})
        for k in cur.get("kaarten", []):
            if k.get("id") == card_id:
                extras = (k.get("media") or {}).get("extra_audio") or []
                extras.append(item)
                service.edit_card(card_id, target_lade, {"media": {"extra_audio": extras}}, user_id=user_id)
                break
    else:
        ip = service._inbox_path()
        inbox = load_json(ip, default={"kaarten": []})
        for k in inbox.get("kaarten", []):
            if k.get("id") == card_id:
                m = k.setdefault("media", {})
                m.setdefault("extra_audio", []).append(item)
                k["needs"] = service._compute_needs(k)
                save_json(ip, inbox)
                break

    # v6_kbv2_hooks_landing_001 — Hook 5: bewaar transcript van 2e spraak-audio ook als snippet
    if transcript:
        try:
            from . import hooks as kbv2_hooks
            kbv2_hooks.save_voice_snippet(transcript, card_id, user_id, voice_url=url)
        except Exception:
            pass

    return {"success": True, "item": item}


@router.delete("/voice/secondary/{card_id}")
@traced(intent="extra audio verwijderen van kaart", module="kbv2", log_args=False)
async def delete_secondary_audio(card_id: str, archive_id: str, lade: Optional[str] = None, user_id: str = "user-000"):
    target_lade = lade or _resolve_lade(card_id)
    if target_lade and target_lade in service.LADES:
        cur = load_json(service._lade_path(target_lade), default={"kaarten": []})
        for k in cur.get("kaarten", []):
            if k.get("id") == card_id:
                extras = (k.get("media") or {}).get("extra_audio") or []
                extras = [x for x in extras if x.get("archive_id") != archive_id]
                service.edit_card(card_id, target_lade, {"media": {"extra_audio": extras}}, user_id=user_id)
                return {"success": True, "remaining": len(extras)}
    ip = service._inbox_path()
    inbox = load_json(ip, default={"kaarten": []})
    for k in inbox.get("kaarten", []):
        if k.get("id") == card_id:
            m = k.setdefault("media", {})
            m["extra_audio"] = [x for x in (m.get("extra_audio") or []) if x.get("archive_id") != archive_id]
            k["needs"] = service._compute_needs(k)
            save_json(ip, inbox)
            return {"success": True, "remaining": len(m["extra_audio"])}
    raise HTTPException(404, "Kaart niet gevonden")


# ---------------------------------------------------------------------------
# v6_kbv2_audio_kind_001 — Toggle audio-kind (spraak ↔ geluid)
# ---------------------------------------------------------------------------

def _normalize_kind(kind: str) -> str:
    k = (kind or "").lower().strip()
    return "geluid" if k in ("geluid", "sound", "sfx") else "spraak"


@router.patch("/voice/kind/{card_id}")
@traced(intent="toggle primaire voice-kind (spraak/geluid)", module="kbv2", log_args=False)
async def def_primary_voice_kind(
    card_id: str,
    kind: str,
    lade: Optional[str] = None,
    user_id: str = "user-000",
):
    """Zet kaart.media.voice_kind = 'spraak' | 'geluid'. Voor backwards-compat is default 'spraak'."""
    kind = _normalize_kind(kind)
    target = lade or _resolve_lade(card_id)
    _patch_card_media(card_id, target, {"voice_kind": kind}, user_id)
    return {"success": True, "voice_kind": kind}


@router.patch("/voice/secondary/kind/{card_id}")
@traced(intent="toggle extra-audio-kind (spraak/geluid)", module="kbv2", log_args=False)
async def def_secondary_voice_kind(
    card_id: str,
    archive_id: str,
    kind: str,
    lade: Optional[str] = None,
    user_id: str = "user-000",
):
    """Update extra_audio[archive_id].kind in lade OF inbox."""
    kind = _normalize_kind(kind)
    target_lade = lade or _resolve_lade(card_id)
    if target_lade and target_lade in service.LADES:
        cur = load_json(service._lade_path(target_lade), default={"kaarten": []})
        for k in cur.get("kaarten", []):
            if k.get("id") == card_id:
                extras = (k.get("media") or {}).get("extra_audio") or []
                hit = False
                for x in extras:
                    if x.get("archive_id") == archive_id:
                        x["kind"] = kind
                        hit = True
                if not hit:
                    raise HTTPException(404, f"Extra audio '{archive_id}' niet gevonden")
                service.edit_card(card_id, target_lade, {"media": {"extra_audio": extras}}, user_id=user_id)
                return {"success": True, "kind": kind, "archive_id": archive_id}
    ip = service._inbox_path()
    inbox = load_json(ip, default={"kaarten": []})
    for k in inbox.get("kaarten", []):
        if k.get("id") == card_id:
            extras = (k.get("media") or {}).get("extra_audio") or []
            hit = False
            for x in extras:
                if x.get("archive_id") == archive_id:
                    x["kind"] = kind
                    hit = True
            if not hit:
                raise HTTPException(404, f"Extra audio '{archive_id}' niet gevonden")
            k.setdefault("media", {})["extra_audio"] = extras
            save_json(ip, inbox)
            return {"success": True, "kind": kind, "archive_id": archive_id}
    raise HTTPException(404, "Kaart niet gevonden")



# ---------------------------------------------------------------------------
# v6_kbv2_media_legacy_001 — Legacy file-serve route
# ---------------------------------------------------------------------------
# Oude kaarten (pre-v5_kbv2_media_002) hebben URLs als
#   /api/kb/v2/media/image/file/{filename}
#   /api/kb/v2/media/voice/file/{filename}
# Die files staan nog in /data/knowledge/v2/media/{image,voice}/
# maar de route was verdwenen → 404. Deze route herstelt backwards-compat.
# ---------------------------------------------------------------------------

from fastapi.responses import FileResponse

_LEGACY_MEDIA_DIR = Path(__file__).parent.parent.parent / "data" / "knowledge" / "v2" / "media"

_MIME_BY_EXT = {
    ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
    ".webp": "image/webp", ".gif": "image/gif", ".bmp": "image/bmp",
    ".webm": "audio/webm", ".mp3": "audio/mpeg", ".wav": "audio/wav",
    ".m4a": "audio/mp4", ".mp4": "audio/mp4", ".ogg": "audio/ogg",
    ".opus": "audio/ogg",
}


def _serve_legacy_media(kind: str, filename: str):
    if kind not in ("image", "voice"):
        raise HTTPException(404, "Onbekend media-type")
    # Basic path-traversal guard
    safe_name = os.path.basename(filename)
    if not safe_name or safe_name != filename:
        raise HTTPException(400, "Ongeldige bestandsnaam")
    fp = _LEGACY_MEDIA_DIR / kind / safe_name
    if not fp.exists() or not fp.is_file():
        raise HTTPException(404, "Bestand niet gevonden")
    ext = fp.suffix.lower()
    media_type = _MIME_BY_EXT.get(ext, "application/octet-stream")
    return FileResponse(path=str(fp), media_type=media_type, filename=safe_name)


@router.get("/image/file/{filename}")
async def legacy_image_file(filename: str):
    """Backwards-compat: serve image van pre-v5_kbv2_media_002 kaarten."""
    return _serve_legacy_media("image", filename)


@router.get("/voice/file/{filename}")
async def legacy_voice_file(filename: str):
    """Backwards-compat: serve voice van pre-v5_kbv2_media_002 kaarten."""
    return _serve_legacy_media("voice", filename)



# =============================================================================
# v7_media_dedup_001 — Archive dedup + picker endpoints
# =============================================================================

@router.get("/archive/list")
async def list_archive_images(category: str = "foto", limit: int = 200):
    """Lijst van beschikbare afbeeldingen in system archive voor UI-picker.

    Response: {items: [{id, url, size_bytes, original_name, reuse_count, linked_cards}]}
    Sorteert op reuse_count DESC (populair eerst) dan uploaded_at DESC.
    """
    idx = load_json(SA_INDEX, default={"files": []})
    items = []
    for f in idx.get("files", []):
        if f.get("category") != category:
            continue
        if not f.get("path") or not Path(f["path"]).exists():
            continue  # skip weesbestanden
        items.append({
            "id": f.get("id"),
            "url": _system_archive_url(f.get("id")),
            "original_name": f.get("original_name"),
            "size_bytes": f.get("size_bytes", 0),
            "extension": f.get("extension"),
            "uploaded_at": f.get("uploaded_at"),
            "reuse_count": f.get("reuse_count", 0),
            "linked_cards": f.get("linked_card_ids") or ([f.get("linked_card_id")] if f.get("linked_card_id") else []),
        })
    items.sort(key=lambda x: (-(x["reuse_count"] or 0), x.get("uploaded_at") or ""), reverse=False)
    items.sort(key=lambda x: -(x["reuse_count"] or 0))  # populair eerst
    return {"success": True, "category": category, "count": len(items), "items": items[:limit]}


class LinkExistingImageRequest(BaseModel):
    card_id: str
    archive_id: str
    lade: Optional[str] = None
    user_id: str = "user-000"


@router.post("/image/link-existing")
async def link_existing_image(req: LinkExistingImageRequest):
    """Koppel een bestaande archive-afbeelding aan een kaart (geen re-upload).

    Voor UI-picker: user kiest een bestaande foto → kaart krijgt URL naar die file.
    """
    idx = load_json(SA_INDEX, default={"files": []})
    entry = next((f for f in idx.get("files", []) if f.get("id") == req.archive_id), None)
    if not entry:
        raise HTTPException(404, f"Archive-id {req.archive_id} niet gevonden")
    if not Path(entry.get("path", "")).exists():
        raise HTTPException(404, f"Bestand voor {req.archive_id} ontbreekt op disk")

    # Update index: kaart-tag + linked_card_ids
    card_tag = f"kbv2_card_{req.card_id}"
    tags = entry.setdefault("tags", [])
    if card_tag not in tags:
        tags.append(card_tag)
    linked = entry.setdefault("linked_card_ids", [])
    if entry.get("linked_card_id") and entry["linked_card_id"] not in linked:
        linked.append(entry["linked_card_id"])
    if req.card_id not in linked:
        linked.append(req.card_id)
    entry.setdefault("reuse_count", 0)
    entry["reuse_count"] += 1
    entry["last_reused_at"] = datetime.now(timezone.utc).isoformat()
    save_json(SA_INDEX, idx)

    # Update kaart: append URL aan image_urls (inbox OF lade)
    image_url = _system_archive_url(entry["id"])
    target_lade = req.lade or _resolve_lade(req.card_id)

    if target_lade and target_lade in service.LADES:
        # Lade-kaart: lees huidige images, append nieuwe, schrijf complete lijst
        cur = load_json(service._lade_path(target_lade), default={"kaarten": []})
        for k in cur.get("kaarten", []):
            if k.get("id") == req.card_id:
                images = list((k.get("media") or {}).get("image_urls") or [])
                if image_url not in images:
                    images.append(image_url)
                    service.edit_card(req.card_id, target_lade, {"media": {"image_urls": images}}, user_id=req.user_id)
                break
    else:
        # Inbox-kaart: helper doet extend()
        _patch_card_media(req.card_id, None, {"image_urls": [image_url]}, user_id=req.user_id)

    return {"success": True, "image_url": image_url, "archive_id": entry["id"],
            "reuse_count": entry["reuse_count"], "linked_cards": linked}


@router.post("/archive/dedup")
async def dedup_archive(execute: bool = False, category: str = "foto"):
    """Scan archief op bit-identieke duplicaten en merge ze.

    Dry-run default. Set execute=true om echt te dedupliceren.

    Effect: voor elke groep files met dezelfde md5:
      - Kies canonical (oudste)
      - Verwijder overige files van disk
      - Update _index.json: verwijder duplicate entries
      - Update kaarten die naar oude URLs verwezen → nieuwe canonical URL
    """
    import hashlib as _hashlib
    idx = load_json(SA_INDEX, default={"files": []})
    files_list = idx.get("files", [])

    # Bereken md5 per file en groepeer
    by_hash: Dict[str, List[dict]] = {}
    for f in files_list:
        if f.get("category") != category:
            continue
        p = f.get("path")
        if not p or not Path(p).exists():
            continue
        h = f.get("content_md5")
        if not h:
            # Legacy files zonder md5 → bereken nu
            try:
                h = _hashlib.md5(Path(p).read_bytes()).hexdigest()
                f["content_md5"] = h
            except Exception:
                continue
        by_hash.setdefault(h, []).append(f)

    duplicate_groups = {h: fs for h, fs in by_hash.items() if len(fs) > 1}
    total_dup_bytes = sum(
        sum(f.get("size_bytes", 0) for f in fs[1:])
        for fs in duplicate_groups.values()
    )

    if not execute:
        return {
            "success": True, "mode": "DRY_RUN",
            "duplicate_groups": len(duplicate_groups),
            "total_files_scanned": sum(1 for f in files_list if f.get("category") == category),
            "would_delete_bytes": total_dup_bytes,
            "would_delete_mb": round(total_dup_bytes / 1024 / 1024, 2),
            "sample_groups": [
                {"hash": h, "canonical": fs[0].get("id"),
                 "duplicates": [dup.get("id") for dup in fs[1:]],
                 "size_bytes": fs[0].get("size_bytes")}
                for h, fs in list(duplicate_groups.items())[:5]
            ],
        }

    # Execute mode
    deleted_files = []
    updated_cards = 0
    for h, fs in duplicate_groups.items():
        canonical = sorted(fs, key=lambda f: f.get("uploaded_at") or "")[0]
        canonical_url = _system_archive_url(canonical["id"])
        canonical_linked = set(canonical.setdefault("linked_card_ids", []))
        if canonical.get("linked_card_id"):
            canonical_linked.add(canonical["linked_card_id"])

        for dup in fs:
            if dup["id"] == canonical["id"]:
                continue
            dup_url = _system_archive_url(dup["id"])
            # Merge linked_card_ids
            for cid in (dup.get("linked_card_ids") or []):
                canonical_linked.add(cid)
            if dup.get("linked_card_id"):
                canonical_linked.add(dup["linked_card_id"])

            # Update alle kaarten die naar dup_url wezen
            for lade in service.LADES:
                lp = service._lade_path(lade)
                if not lp.exists():
                    continue
                cur = load_json(lp, default={"kaarten": []})
                changed = False
                for k in cur.get("kaarten", []):
                    imgs = (k.get("media") or {}).get("image_urls") or []
                    if dup_url in imgs:
                        new_imgs = [canonical_url if u == dup_url else u for u in imgs]
                        new_imgs = list(dict.fromkeys(new_imgs))  # dedup
                        k.setdefault("media", {})["image_urls"] = new_imgs
                        changed = True
                        updated_cards += 1
                if changed:
                    save_json(lp, cur)

            # Verwijder dup file + index-entry
            try:
                Path(dup["path"]).unlink()
                deleted_files.append({"id": dup["id"], "path": dup["path"], "size": dup.get("size_bytes")})
            except Exception:
                pass

        canonical["linked_card_ids"] = sorted(canonical_linked)
        canonical["reuse_count"] = len(canonical_linked)

    # Filter dups uit files_list
    keep_ids = {fs[0]["id"] for fs in [sorted(g, key=lambda f: f.get("uploaded_at") or "") for g in duplicate_groups.values()]}
    remove_ids = {dup["id"] for h, fs in duplicate_groups.items() for dup in fs if dup["id"] not in keep_ids}
    idx["files"] = [f for f in files_list if f.get("id") not in remove_ids]
    idx["updated_at"] = datetime.now(timezone.utc).isoformat()
    save_json(SA_INDEX, idx)

    return {
        "success": True, "mode": "EXECUTED",
        "duplicate_groups_processed": len(duplicate_groups),
        "files_deleted": len(deleted_files),
        "bytes_saved": sum(f.get("size", 0) or 0 for f in deleted_files),
        "mb_saved": round(sum(f.get("size", 0) or 0 for f in deleted_files) / 1024 / 1024, 2),
        "cards_updated": updated_cards,
    }
