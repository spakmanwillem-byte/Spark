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
from typing import Optional

from dotenv import load_dotenv
from fastapi import APIRouter, UploadFile, File, Form, HTTPException

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
    Tagt automatisch met 'kbv2' + 'kbv2_card_<id>' zodat UI kan filteren."""
    SA_DIR.mkdir(parents=True, exist_ok=True)
    (SA_DIR / category).mkdir(parents=True, exist_ok=True)

    ext = Path(original_name).suffix.lower()
    file_id = uuid.uuid4().hex[:12]
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
        "description": f"Kennis-kaart media voor kaart {card_id}",
        "tags": ["kbv2", f"kbv2_card_{card_id}"],
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "uploaded_by": user_id,
        "path": str(dest),
        # v5_kbv2_media_002 — kennis-kaart link velden
        "linked_card_id": card_id,
        "source": "kbv2_media_upload",
        "scan_status": None,
        "scan_results": None,
    }
    if extra_meta:
        entry.update(extra_meta)

    idx = load_json(SA_INDEX, default={"files": []})
    idx.setdefault("files", []).append(entry)
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
