"""
Card Factory Routes (v5_card_factory_001)

POST   /api/cards/{type}                    create
GET    /api/cards/{type}                    list
GET    /api/cards/{type}/{card_id}          get
POST   /api/cards/{type}/{card_id}          update (triggert hook-chain bij draft→active)
DELETE /api/cards/{type}/{card_id}          delete + cascade media
POST   /api/cards/{type}/{card_id}/media    upload image/audio (delegeert naar system_archive)
"""
from typing import Optional, Dict, List
from pathlib import Path
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel

from modules.core.storage import load_json, save_json
from . import service

router = APIRouter(prefix="/cards", tags=["cards"])


class CreateBody(BaseModel):
    titel: str
    vraag: Optional[str] = None
    antwoord: Optional[str] = None
    user_id: Optional[str] = "user-000"
    extra: Optional[Dict] = None


class UpdateBody(BaseModel):
    updates: Dict
    user_id: Optional[str] = "user-000"


# ---------- Read ----------

@router.get("/{card_type}")
async def list_(card_type: str, status: Optional[str] = None):
    cards = service.list_cards(card_type, status=status)
    return {"success": True, "type": card_type, "count": len(cards), "cards": cards}


@router.get("/{card_type}/{card_id}")
async def get(card_type: str, card_id: str):
    c = service.get_card(card_type, card_id)
    if not c:
        raise HTTPException(404, "Kaart niet gevonden")
    return {"success": True, "card": c}


# ---------- Write ----------

@router.post("/{card_type}")
async def create(card_type: str, body: CreateBody):
    return service.create_card(card_type, body.titel, user_id=body.user_id,
                                vraag=body.vraag, antwoord=body.antwoord, extra=body.extra)


@router.post("/{card_type}/{card_id}")
async def update(card_type: str, card_id: str, body: UpdateBody):
    return service.update_card(card_type, card_id, body.updates, user_id=body.user_id)


@router.delete("/{card_type}/{card_id}")
async def delete(card_type: str, card_id: str):
    return service.delete_card(card_type, card_id)


# ---------- Media upload (delegate naar system_archive) ----------

ALLOWED_AUDIO = {".webm", ".mp3", ".wav", ".m4a", ".ogg"}
ALLOWED_IMAGE = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
MAX_AUDIO_MB = 24
MAX_IMAGE_MB = 8

SA_DIR = Path(__file__).parent.parent.parent / "data" / "system_archive"
SA_INDEX = SA_DIR / "_index.json"


def _save_to_system_archive(content: bytes, original_name: str, category: str,
                            card_id: str, card_type: str, user_id: str,
                            mime_type: str = "application/octet-stream") -> dict:
    """Schrijf bytes naar system_archive met card-tag + linked_card_id."""
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
        "description": f"Game-kaart media voor kaart {card_id} ({card_type})",
        "tags": [f"card_{card_type}", "card_factory"],
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "uploaded_by": user_id,
        "path": str(dest),
        "linked_card_id": card_id,
        "source": "card_factory_media_upload",
    }
    idx = load_json(SA_INDEX, default={"files": []})
    idx.setdefault("files", []).append(entry)
    idx["updated_at"] = datetime.now(timezone.utc).isoformat()
    save_json(SA_INDEX, idx)
    return entry


@router.post("/{card_type}/{card_id}/media")
async def upload_media(
    card_type: str,
    card_id: str,
    file: UploadFile = File(...),
    kind: str = Form(...),   # "image" of "audio"
    user_id: str = Form("user-000"),
):
    if kind not in ("image", "audio"):
        raise HTTPException(400, "kind moet 'image' of 'audio' zijn")
    ext = Path(file.filename or "").suffix.lower()
    if kind == "image":
        if ext not in ALLOWED_IMAGE:
            raise HTTPException(400, f"Image-type '{ext}' niet toegestaan")
        max_mb = MAX_IMAGE_MB
        category = "foto"
    else:
        if ext not in ALLOWED_AUDIO:
            raise HTTPException(400, f"Audio-type '{ext}' niet toegestaan")
        max_mb = MAX_AUDIO_MB
        category = "geluiden"

    data = await file.read()
    if len(data) > max_mb * 1024 * 1024:
        raise HTTPException(413, f"File te groot (>{max_mb}MB)")

    entry = _save_to_system_archive(
        data, file.filename or f"card_{card_id}{ext}", category,
        card_id, card_type, user_id,
        mime_type=file.content_type or "application/octet-stream"
    )
    url = f"/api/system-archive/file/{entry['id']}"
    media_field = "image_url" if kind == "image" else "audio_url"
    service.update_card(card_type, card_id, {"media": {media_field: url}}, user_id=user_id)
    return {"success": True, "url": url, "archive_id": entry["id"]}
