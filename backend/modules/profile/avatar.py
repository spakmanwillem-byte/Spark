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

# v4_avatar_fallback_002 — Vraagteken-avatar als default fallback (was Roadkill logo)
ROADKILL_LOGO_ID = "roadkill-logo"  # behouden voor token-logo / shop gebruik
QUESTION_AVATAR_ID = "31c6dc04a2fd"  # "Vraag" avatar uit galerij
QUESTION_AVATAR_URL = f"/api/avatar/gallery/{QUESTION_AVATAR_ID}/image"
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
    # v13c_bots_removed_001 (sessie 54) — alleen Boekhouder + Spark blijven.
    title_to_bot = {
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
async def list_gallery(category: Optional[str] = None):
    """Lijst van systeem-avatars (zichtbaar voor alle users).

    v4_avatar_categories_001: optionele filter op category.
      - 'user'   = persoonlijke avatars (default zichtbaar voor iedereen)
      - 'dnd'    = D&D archief — moet unlocked worden via achievements/XP
      - 'system' = bot-only / Spark-only
    """
    _ensure_gallery_dir()
    idx = load_json(GALLERY_INDEX, default={"avatars": []})
    enriched = []
    for a in idx.get("avatars", []):
        out = dict(a)
        owner = _get_bot_owner(a)
        if owner:
            out["bot_owner"] = owner
            out["locked"] = True
        # Default category als niet gezet
        if "category" not in out:
            out["category"] = "system" if owner else "user"
        if category and out["category"] != category:
            continue
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
    category: Optional[str] = None   # "user" | "dnd" | "system"


@router.patch("/gallery/{avatar_id}")
async def patch_gallery_entry(avatar_id: str, body: GalleryEditBody):
    """Admin past title/tags/bot_owner/category aan."""
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
    if body.category is not None and body.category in ("user", "dnd", "system"):
        entry["category"] = body.category
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
    """User upload eigen profielfoto.
    v6_personal_avatar_archive_001 — Wordt OOK gearchiveerd in user_archive/foto met
    tag 'personal_avatar', zodat user een eigen collectie heeft (alleen voor zichzelf).
    """
    raw = await file.read()
    if len(raw) > 10 * 1024 * 1024:
        raise HTTPException(413, "Bestand te groot (max 10MB)")
    dest = USERS_DIR / user_id / "avatar.jpg"
    info = _resize_and_save(raw, dest)
    _set_user_avatar(user_id, "user")

    # Archiveer als persoonlijke avatar in user_archive (met index)
    try:
        from modules.user_archive.routes import _user_dir, _load_index, _save_index
        from PIL import Image as _PILImage
        import io as _io
        # Bewaar geresizede versie (zoals dest) ook in archive/foto
        archive_dir = _user_dir(user_id) / "foto"
        archive_dir.mkdir(parents=True, exist_ok=True)
        file_id = uuid.uuid4().hex[:12]
        archive_filename = f"avatar_{file_id}.jpg"
        archive_dest = archive_dir / archive_filename
        # Lees bewaarde resize uit dest om identieke bytes te hebben
        archive_dest.write_bytes(dest.read_bytes())
        entry = {
            "id": file_id,
            "filename": archive_filename,
            "original_name": file.filename or "avatar.jpg",
            "category": "foto",
            "extension": ".jpg",
            "mime_type": "image/jpeg",
            "size_bytes": archive_dest.stat().st_size,
            "description": "Persoonlijke avatar",
            "tags": ["personal_avatar", "avatar"],
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
            "uploaded_by": user_id,
            "path": str(archive_dest),
            "source": "personal_avatar_upload",
            "active": True,  # huidige actieve avatar
        }
        files = _load_index(user_id)
        # Markeer eerdere personal avatars als niet-actief
        for f in files:
            if "personal_avatar" in (f.get("tags") or []):
                f["active"] = False
        files.append(entry)
        _save_index(user_id, files)
    except Exception as ex:
        print(f"[avatar] personal archive write failed: {ex}")

    # v5_milestone_unlocks_001: unlock "Eigen Avatar" achievement
    try:
        from modules.achievements.service import unlock_milestone
        unlock_milestone(user_id, "milestone_avatar_uploaded")
        unlock_milestone(user_id, "milestone_avatar_chose")
    except Exception as ex:
        print(f"[avatar] milestone unlock failed: {ex}")

    return {
        "success": True,
        "width": info["w"],
        "height": info["h"],
        "size_bytes": info["size_bytes"],
        "url": f"/api/avatar/user/{user_id}/image?t={int(datetime.now(timezone.utc).timestamp())}",
    }


@router.get("/user/{user_id}/personal-gallery")
async def list_personal_avatars(user_id: str):
    """Lijst alle persoonlijke avatars uit user_archive (alleen zichtbaar voor user zelf).
    Tag 'personal_avatar' bepaalt of het erbij hoort.
    """
    try:
        from modules.user_archive.routes import _load_index
        files = _load_index(user_id)
    except Exception:
        files = []
    out = []
    for f in files:
        if "personal_avatar" in (f.get("tags") or []):
            out.append({
                "id": f["id"],
                "filename": f.get("filename"),
                "uploaded_at": f.get("uploaded_at"),
                "active": f.get("active", False),
                "url": f"/api/archive/{user_id}/file/{f['id']}",
            })
    out.sort(key=lambda x: x.get("uploaded_at", ""), reverse=True)
    return {"avatars": out, "count": len(out)}


@router.post("/user/{user_id}/activate-personal/{avatar_id}")
async def activate_personal_avatar(user_id: str, avatar_id: str):
    """Wissel actieve personal-avatar naar eerdere uit eigen archief."""
    try:
        from modules.user_archive.routes import _load_index, _save_index
        files = _load_index(user_id)
    except Exception:
        raise HTTPException(500, "Archief niet beschikbaar")
    target = None
    for f in files:
        if "personal_avatar" in (f.get("tags") or []):
            f["active"] = (f["id"] == avatar_id)
            if f["id"] == avatar_id:
                target = f
    if not target:
        raise HTTPException(404, "Avatar niet gevonden in jouw archief")
    # Kopieer naar avatar.jpg
    USERS_DIR.mkdir(parents=True, exist_ok=True)
    dest = USERS_DIR / user_id / "avatar.jpg"
    src = Path(target.get("path", ""))
    if not src.exists():
        raise HTTPException(404, "Bestand ontbreekt in archief")
    dest.write_bytes(src.read_bytes())
    _save_index(user_id, files)
    _set_user_avatar(user_id, "user")
    return {"success": True, "url": f"/api/avatar/user/{user_id}/image?t={int(datetime.now(timezone.utc).timestamp())}"}


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
    avatar_title = None
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
        avatar_title = entry.get("title")
    _set_user_avatar(user_id, ref)

    # v5_milestone_unlocks_001: unlock "Ik koos een Avatar" achievement
    if ref:
        try:
            from modules.achievements.service import unlock_milestone
            unlock_milestone(user_id, "milestone_avatar_chose")
        except Exception as ex:
            print(f"[avatar] milestone unlock failed: {ex}")

    # v4_dnd_001: log Spark-observatie zodat hij hem kan benoemen in volgende gesprek
    try:
        from modules.dnd.routes import observe, ObserveBody  # type: ignore
        await observe(ObserveBody(
            user_id=user_id,
            kind="avatar_changed",
            detail={"avatar_ref": ref, "title": avatar_title or (ref or "geen")},
        ))
    except Exception:
        pass  # niet kritiek
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
    # Fallback naar vraagteken-avatar wanneer niets gezet
    fallback_url = QUESTION_AVATAR_URL if (GALLERY_DIR / f"{QUESTION_AVATAR_ID}.jpg").exists() else (
        ROADKILL_LOGO_URL if (GALLERY_DIR / f"{ROADKILL_LOGO_ID}.jpg").exists() else None
    )
    return {
        "success": True,
        "avatar_ref": ref,
        "url": url,
        "fallback_url": fallback_url,
        "is_fallback": url is None,
    }
