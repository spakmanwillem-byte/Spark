"""
KB v2 Media Routes (v5_kbv2_media_001)
=======================================
Upload routes voor voice (Whisper STT) + image bij kennis-kaarten.

POST /api/kb/v2/media/voice         multipart: audio + card_id + lade → transcribeert + slaat op
POST /api/kb/v2/media/image         multipart: image + card_id + lade → slaat op + linkt aan kaart
"""
import os
import uuid
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse

from modules.core.spark_logger import traced
from . import service

load_dotenv()

# Media storage onder data/knowledge/v2/media/
MEDIA_DIR = Path(__file__).parent.parent.parent / "data" / "knowledge" / "v2" / "media"
VOICE_DIR = MEDIA_DIR / "voice"
IMAGE_DIR = MEDIA_DIR / "image"
VOICE_DIR.mkdir(parents=True, exist_ok=True)
IMAGE_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_AUDIO = {".webm", ".mp3", ".wav", ".m4a", ".mp4", ".mpga", ".mpeg"}
ALLOWED_IMAGE = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
MAX_AUDIO_MB = 24    # OpenAI Whisper limit is 25 MB
MAX_IMAGE_MB = 8

router = APIRouter(prefix="/kb/v2/media", tags=["kb-v2-media"])


# ----------------------------- Voice (Whisper) -----------------------------

@router.post("/voice")
@traced(intent="audio voor kaart transcriberen + opslaan", module="kbv2", log_args=False)
async def upload_voice(
    audio: UploadFile = File(...),
    card_id: str = Form(...),
    lade: Optional[str] = Form(None),
    user_id: str = Form("user-000"),
):
    ext = Path(audio.filename or "audio.webm").suffix.lower()
    if ext not in ALLOWED_AUDIO:
        raise HTTPException(status_code=400, detail=f"Audio-type '{ext}' niet toegestaan. Gebruik: {sorted(ALLOWED_AUDIO)}")
    data = await audio.read()
    if len(data) > MAX_AUDIO_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"Audio te groot (>{MAX_AUDIO_MB}MB)")

    fname = f"{card_id}_{uuid.uuid4().hex[:6]}{ext}"
    fpath = VOICE_DIR / fname
    fpath.write_bytes(data)

    # Whisper transcribeer
    transcript = ""
    try:
        from emergentintegrations.llm.openai import OpenAISpeechToText
        api_key = os.getenv("EMERGENT_LLM_KEY")
        if not api_key:
            raise RuntimeError("EMERGENT_LLM_KEY ontbreekt in .env")
        stt = OpenAISpeechToText(api_key=api_key)
        with fpath.open("rb") as f:
            resp = await stt.transcribe(
                file=f, model="whisper-1", response_format="json",
                language="nl",
                prompt="Spark Core kennis-kaart Nederlandse uitleg",
                temperature=0.0,
            )
        transcript = (getattr(resp, "text", None) or "").strip()
    except Exception as e:
        # Bestand bewaard, maar transcriptie mislukt
        return {
            "success": False,
            "error": f"Transcriptie mislukt: {e}",
            "voice_url": f"/api/kb/v2/media/voice/file/{fname}",
            "voice_transcript": "",
        }

    # Update kaart met voice_url + transcript
    updates = {
        "media": {
            "voice_url": f"/api/kb/v2/media/voice/file/{fname}",
            "voice_transcript": transcript,
        }
    }
    # Probeer lade te vinden als niet meegegeven
    if not lade:
        # Quick lookup via index
        from modules.core.storage import load_json
        idx = load_json(service._index_path(), default={"entries": {}})
        for begrip, e in (idx.get("entries") or {}).items():
            if e.get("kaart_id") == card_id:
                lade = e.get("lade")
                break

    if lade and lade in service.LADES:
        service.edit_card(card_id, lade, updates, user_id=user_id)
    else:
        # Inbox-card: patch direct in inbox-file
        from modules.core.storage import load_json, save_json
        ip = service._inbox_path()
        inbox = load_json(ip, default={"kaarten": []})
        for k in inbox.get("kaarten", []):
            if k.get("id") == card_id:
                k.setdefault("media", {})["voice_url"] = updates["media"]["voice_url"]
                k["media"]["voice_transcript"] = transcript
                k["needs"] = service._compute_needs(k)
                # Auto-fill laag1 als die nog leeg is en we transcript hebben
                if transcript and not (k.get("lagen", {}).get("laag1") or "").strip():
                    k.setdefault("lagen", {})["laag1"] = transcript
                    k["needs"] = service._compute_needs(k)
                save_json(ip, inbox)
                break

    return {
        "success": True,
        "voice_url": updates["media"]["voice_url"],
        "voice_transcript": transcript,
        "size_bytes": len(data),
    }


@router.get("/voice/file/{fname}")
async def get_voice_file(fname: str):
    """Serveer audio-bestand."""
    fp = VOICE_DIR / fname
    if not fp.exists() or ".." in fname:
        raise HTTPException(status_code=404, detail="Audio niet gevonden")
    return FileResponse(fp)


# ----------------------------- Image -----------------------------

@router.post("/image")
@traced(intent="foto voor kaart opslaan", module="kbv2", log_args=False)
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

    fname = f"{card_id}_{uuid.uuid4().hex[:6]}{ext}"
    fpath = IMAGE_DIR / fname
    fpath.write_bytes(data)
    image_url = f"/api/kb/v2/media/image/file/{fname}"

    # Append aan kaart's image_urls (lade of inbox)
    if not lade:
        from modules.core.storage import load_json
        idx = load_json(service._index_path(), default={"entries": {}})
        for begrip, e in (idx.get("entries") or {}).items():
            if e.get("kaart_id") == card_id:
                lade = e.get("lade")
                break

    if lade and lade in service.LADES:
        # Read current images, append, save
        from modules.core.storage import load_json
        cur = load_json(service._lade_path(lade), default={"kaarten": []})
        for k in cur.get("kaarten", []):
            if k.get("id") == card_id:
                images = (k.get("media") or {}).get("image_urls") or []
                images.append(image_url)
                service.edit_card(card_id, lade, {"media": {"image_urls": images}}, user_id=user_id)
                break
    else:
        from modules.core.storage import load_json, save_json
        ip = service._inbox_path()
        inbox = load_json(ip, default={"kaarten": []})
        for k in inbox.get("kaarten", []):
            if k.get("id") == card_id:
                m = k.setdefault("media", {"voice_url": None, "voice_transcript": None, "image_urls": []})
                m.setdefault("image_urls", []).append(image_url)
                k["needs"] = service._compute_needs(k)
                save_json(ip, inbox)
                break

    return {"success": True, "image_url": image_url, "size_bytes": len(data)}


@router.get("/image/file/{fname}")
async def get_image_file(fname: str):
    fp = IMAGE_DIR / fname
    if not fp.exists() or ".." in fname:
        raise HTTPException(status_code=404, detail="Image niet gevonden")
    return FileResponse(fp)
