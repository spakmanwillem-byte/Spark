"""
Avatar Module — Profielfoto's
  • Systeem-galerij: admin uploadt voorbeeld-avatars (alle users kunnen kiezen)
    → /app/backend/data/system/avatars/_index.json
    → /app/backend/data/system/avatars/{avatar_id}.jpg
  • User-portret: user uploadt eigen foto (alleen voor eigen profiel)
    → /app/backend/data/users/{user_id}/avatar.jpg
  • Selectie: users.json[id].avatar = "gallery:{id}" | "user" | null

Max formaat 512×512 (Pillow resize), JPEG kwaliteit 85.
"""
import io
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
from PIL import Image

from modules.core.storage import load_json, save_json

router = APIRouter(prefix="/avatar", tags=["avatar"])

DATA_DIR = Path(__file__).parent.parent.parent / "data"
GALLERY_DIR = DATA_DIR / "system" / "avatars"
GALLERY_INDEX = GALLERY_DIR / "_index.json"
USERS_DIR = DATA_DIR / "users"
USERS_FILE = DATA_DIR / "system" / "users.json"

MAX_DIM = 512  # max width/height
QUALITY = 85
ADMIN_GRAD = 2  # gradatie ≤ 2 mag galerij beheren

# v4_avatar_fallback_001 — Roadkill logo als default fallback wanneer geen avatar gezet is
ROADKILL_LOGO_ID = "roadkill-logo"
ROADKILL_LOGO_URL = f"/api/avatar/gallery/{ROADKILL_LOGO_ID}/image"

# v4_avatar_bot_lock_001 — Avatars geclaimd door specifieke bots (title-based, exclusief voor die bot)
# Maakt het visueel duidelijk (locket-stempel) + voorkomt dat ze door normale users gekozen worden
def _get_bot_owner(entry: dict) -> Optional[str]:
    """Return owner user-id als deze avatar exclusief geclaimd is (bot of Spark).

    Priority:
      1. Expliciete `bot_owner` veld (admin-managed via PATCH /gallery/{id})
      2. Title-match met bekende bots (fallback voor seed-data)
    """
    if not entry:
        return None
    explicit = (entry.get("bot_owner") or "").strip()
    if explicit:
        return explicit
    title = (entry.get("title") or "").strip().lower()
    title_to_bot = {
        "harry klokkenmaker": "bot-harry",
        "madelief stouten": "bot-madelief",
        "mr smith": "bot-smith",
        "de boekhouder": "bot-boekhouder",
        "spark": "user-000",
    }
    return title_to_bot.get(title)


def _ensure_gallery_dir():
    GALLERY_DIR.mkdir(parents=True, exist_ok=True)


def _resize_and_save(img_bytes: bytes, dest: Path) -> dict:
    """Resize naar max 512x512 en sla op als JPEG. Return {w,h,size_bytes}."""
    img = Image.open(io.BytesIO(img_bytes))
    if img.mode in ("RGBA", "LA", "P"):
        bg = Image.new("RGB", img.size, (15, 23, 42))  # slate-900
        if img.mode == "P":
            img = img.convert("RGBA")
        bg.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
        img = bg
    elif img.mode != "RGB":
        img = img.convert("RGB")
    img.thumbnail((MAX_DIM, MAX_DIM), Image.LANCZOS)
    dest.parent.mkdir(parents=True, exist_ok=True)
    img.save(dest, "JPEG", quality=QUALITY, optimize=True)
    return {"w": img.width, "h": img.height, "size_bytes": dest.stat().st_size}


def _is_admin(user_id: str) -> bool:
    users = load_json(USERS_FILE, default={}).get("users", [])
    me = next((u for u in users if u.get("id") == user_id), None)
    return bool(me) and (me.get("gradatie", 99) <= ADMIN_GRAD)


# ============================================================
# GALERIJ (admin)
# ============================================================

@router.get("/gallery")
async def list_gallery():
    """Lijst van systeem-avatars (zichtbaar voor alle users)."""
    _ensure_gallery_dir()
    idx = load_json(GALLERY_INDEX, default={"avatars": []})
    # Verrijk met bot_owner zodat frontend locket-stempel kan tonen
    enriched = []
    for a in idx.get("avatars", []):
        out = dict(a)
        owner = _get_bot_owner(a)
        if owner:
            out["bot_owner"] = owner
            out["locked"] = True
        enriched.append(out)
    return {"success": True, "avatars": enriched}


@router.post("/gallery")
async def upload_to_gallery(
    file: UploadFile = File(...),
    title: str = Form(...),
    tags: str = Form(""),
    uploader_id: str = Form(...),
):
    """Admin upload een avatar naar de systeem-galerij."""
    if not _is_admin(uploader_id):
        raise HTTPException(403, "Alleen admins kunnen de galerij beheren")
    if not title.strip():
        raise HTTPException(400, "Titel is verplicht")

    raw = await file.read()
    if len(raw) > 10 * 1024 * 1024:
        raise HTTPException(413, "Bestand te groot (max 10MB)")

    avatar_id = uuid.uuid4().hex[:12]
    dest = GALLERY_DIR / f"{avatar_id}.jpg"
    info = _resize_and_save(raw, dest)

    _ensure_gallery_dir()
    idx = load_json(GALLERY_INDEX, default={"avatars": []})
    entry = {
        "id": avatar_id,
        "title": title.strip(),
        "tags": [t.strip() for t in tags.split(",") if t.strip()],
        "original_name": file.filename or "",
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "uploaded_by": uploader_id,
        "width": info["w"],
        "height": info["h"],
        "size_bytes": info["size_bytes"],
    }
    idx.setdefault("avatars", []).append(entry)
    save_json(GALLERY_INDEX, idx)
    return {"success": True, "avatar": entry}


@router.delete("/gallery/{avatar_id}")
async def delete_from_gallery(avatar_id: str, viewer_id: str):
    if not _is_admin(viewer_id):
        raise HTTPException(403, "Alleen admins kunnen verwijderen")
    idx = load_json(GALLERY_INDEX, default={"avatars": []})
    before = len(idx.get("avatars", []))
    idx["avatars"] = [a for a in idx.get("avatars", []) if a.get("id") != avatar_id]
    save_json(GALLERY_INDEX, idx)
    f = GALLERY_DIR / f"{avatar_id}.jpg"
    if f.exists():
        f.unlink()
    return {"success": True, "removed": before - len(idx["avatars"])}


# v4_avatar_gallery_edit_001 — Admin kan title/tags/bot_owner van bestaande gallery-avatar wijzigen
class GalleryEditBody(BaseModel):
    viewer_id: str
    title: Optional[str] = None
    tags: Optional[List[str]] = None
    bot_owner: Optional[str] = None  # "bot-xxx" of "" om te wissen


@router.patch("/gallery/{avatar_id}")
async def patch_gallery_entry(avatar_id: str, body: GalleryEditBody):
    """Admin past title/tags/bot_owner aan voor bestaande gallery avatar.

    Voor de bot_owner-claim: gebruik "bot-harry"/"bot-smith"/"bot-madelief"/"bot-boekhouder"/"user-000" (Spark).
    Lege string of None verwijdert de claim (avatar wordt weer vrij te kiezen).
    """
    if not _is_admin(body.viewer_id):
        raise HTTPException(403, "Alleen admins kunnen avatars bewerken")
    idx = load_json(GALLERY_INDEX, default={"avatars": []})
    entry = next((a for a in idx.get("avatars", []) if a.get("id") == avatar_id), None)
    if not entry:
        raise HTTPException(404, "Avatar niet gevonden")
    if body.title is not None and body.title.strip():
        entry["title"] = body.title.strip()
    if body.tags is not None:
        entry["tags"] = [t.strip() for t in body.tags if t and t.strip()]
    if body.bot_owner is not None:
        owner = body.bot_owner.strip()
        if owner == "":
            entry.pop("bot_owner", None)
        else:
            entry["bot_owner"] = owner
    entry["updated_at"] = datetime.now(timezone.utc).isoformat()
    save_json(GALLERY_INDEX, idx)
    return {"success": True, "avatar": entry}


@router.get("/gallery/{avatar_id}/image")
async def get_gallery_image(avatar_id: str):
    f = GALLERY_DIR / f"{avatar_id}.jpg"
    if not f.exists():
        raise HTTPException(404, "Avatar niet gevonden")
    return FileResponse(str(f), media_type="image/jpeg")


# ============================================================
# USER PORTRET
# ============================================================

@router.post("/user/{user_id}")
async def upload_user_portrait(user_id: str, file: UploadFile = File(...)):
    """User upload eigen profielfoto (alleen voor eigen profiel)."""
    raw = await file.read()
    if len(raw) > 10 * 1024 * 1024:
        raise HTTPException(413, "Bestand te groot (max 10MB)")
    dest = USERS_DIR / user_id / "avatar.jpg"
    info = _resize_and_save(raw, dest)
    _set_user_avatar(user_id, "user")
    return {
        "success": True,
        "width": info["w"],
        "height": info["h"],
        "size_bytes": info["size_bytes"],
        "url": f"/api/avatar/user/{user_id}/image?t={int(datetime.now(timezone.utc).timestamp())}",
    }


@router.get("/user/{user_id}/image")
async def get_user_portrait(user_id: str):
    f = USERS_DIR / user_id / "avatar.jpg"
    if not f.exists():
        raise HTTPException(404, "Geen profielfoto")
    return FileResponse(str(f), media_type="image/jpeg")


@router.delete("/user/{user_id}")
async def remove_user_portrait(user_id: str):
    f = USERS_DIR / user_id / "avatar.jpg"
    if f.exists():
        f.unlink()
    _set_user_avatar(user_id, None)
    return {"success": True}


# ============================================================
# SELECTIE
# ============================================================

class AvatarSelect(BaseModel):
    avatar_ref: Optional[str] = None  # "gallery:{id}" | "user" | null


def _set_user_avatar(user_id: str, ref: Optional[str]):
    data = load_json(USERS_FILE, default={"users": []})
    for u in data.get("users", []):
        if u.get("id") == user_id:
            if ref:
                u["avatar"] = ref
            else:
                u.pop("avatar", None)
            break
    save_json(USERS_FILE, data)


@router.put("/select/{user_id}")
async def select_avatar(user_id: str, body: AvatarSelect):
    """Stel huidige avatar in: "gallery:{id}", "user", of null."""
    ref = body.avatar_ref
    if ref and not (ref == "user" or ref.startswith("gallery:")):
        raise HTTPException(400, "Ongeldige avatar_ref")
    if ref and ref.startswith("gallery:"):
        gid = ref.split(":", 1)[1]
        idx = load_json(GALLERY_INDEX, default={"avatars": []})
        entry = next((a for a in idx.get("avatars", []) if a.get("id") == gid), None)
        if not entry:
            raise HTTPException(404, "Galerij-avatar niet gevonden")
        # v4_avatar_bot_lock_001: bot-claimed avatar mag alleen door die bot of admin worden gekozen
        owner = _get_bot_owner(entry)
        if owner and owner != user_id and not _is_admin(user_id):
            raise HTTPException(403, f"Deze avatar is exclusief voor {owner}")
    _set_user_avatar(user_id, ref)
    return {"success": True, "avatar_ref": ref}


@router.get("/current/{user_id}")
async def get_current_avatar(user_id: str):
    """Geef huidige avatar_ref + resolved URL terug.

    v4_avatar_fallback_001: als geen avatar gezet → roadkill logo als fallback URL
    (frontend kan zelf kiezen om de letter-fallback te gebruiken via avatar_ref==null).
    """
    data = load_json(USERS_FILE, default={"users": []})
    me = next((u for u in data.get("users", []) if u.get("id") == user_id), None)
    if not me:
        raise HTTPException(404, "User niet gevonden")
    ref = me.get("avatar")
    url = None
    if ref == "user" and (USERS_DIR / user_id / "avatar.jpg").exists():
        url = f"/api/avatar/user/{user_id}/image"
    elif ref and ref.startswith("gallery:"):
        gid = ref.split(":", 1)[1]
        if (GALLERY_DIR / f"{gid}.jpg").exists():
            url = f"/api/avatar/gallery/{gid}/image"
    # Fallback naar Roadkill logo wanneer niets gezet
    fallback_url = ROADKILL_LOGO_URL if (GALLERY_DIR / f"{ROADKILL_LOGO_ID}.jpg").exists() else None
    return {
        "success": True,
        "avatar_ref": ref,
        "url": url,
        "fallback_url": fallback_url,
        "is_fallback": url is None,
    }
