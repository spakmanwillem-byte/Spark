"""
Achievements Routes
"""
from fastapi import APIRouter, HTTPException
from pathlib import Path
from .service import AchievementService
from modules.core.storage import load_json

router = APIRouter(prefix="/achievements", tags=["achievements"])
service = AchievementService()


@router.get("/all")
async def get_all_achievements():
    """Get all available achievements"""
    return service.get_all()


# v7_achievement_agents_001 — Blueprint uitlezen voor admin UI (later editable)
@router.get("/admin/blueprints")
async def get_blueprints():
    """Return alle sub-agent blueprints (XP-waarden, texts, thresholds) voor admin UI."""
    return {"success": True, "blueprints": service.get_blueprints()}


@router.get("/progress/{user_id}")
async def get_user_progress(user_id: str):
    """Get user's achievement progress (auto-unlocks retroactively)"""
    result = service.get_user_progress(user_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Gebruiker niet gevonden")
    return result


# v4_leaderboard_001 — Echte data uit user-progress (ipv frontend mock)
@router.get("/leaderboard")
async def get_leaderboard(period: str = "alltime", limit: int = 25):
    """
    Ranglijst van alle users op basis van XP / unlocks / word_count.
    period: 'alltime' (default), 'week', 'month' (laatste twee gebaseerd op recente unlocks).
    """
    users_file = Path(__file__).parent.parent.parent / "data" / "system" / "users.json"
    users_data = load_json(users_file, default={"users": []})
    results = []
    for u in users_data.get("users", []):
        uid = u.get("id")
        if not uid:
            continue
        try:
            prog = service.get_user_progress(uid)
        except Exception:
            prog = None
        if not prog:
            continue
        xp = prog.get("total_xp_earned", 0)
        unlocked_list = prog.get("unlocked", []) or []
        # Period filter
        if period in ("week", "month"):
            from datetime import datetime, timezone, timedelta
            cutoff = datetime.now(timezone.utc) - (timedelta(days=7) if period == "week" else timedelta(days=30))
            recent_unlocks = []
            recent_xp = 0
            for a in unlocked_list:
                ts = a.get("unlocked_at")
                if not ts:
                    continue
                try:
                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    if dt >= cutoff:
                        recent_unlocks.append(a)
                        recent_xp += a.get("xp_reward", 0)
                except Exception:
                    continue
            xp = recent_xp
            achievements_count = len(recent_unlocks)
        else:
            achievements_count = len(unlocked_list)
        results.append({
            "user_id": uid,
            "naam": prog.get("user_naam") or u.get("naam") or uid,
            "gradatie": prog.get("user_gradatie") or u.get("gradatie", 7),
            "gradatie_titel": u.get("rol") or "",
            "rang": u.get("rang"),
            "avatar_ref": u.get("avatar"),  # v4_avatar_leaderboard_001
            "xp": int(xp),
            "level": int(xp // 100) if xp else 0,
            "achievements": achievements_count,
            "words": prog.get("word_count", 0),
            "is_bot": uid.startswith("bot-"),
        })
    # Sort op XP desc
    results.sort(key=lambda r: r["xp"], reverse=True)
    # Rank toevoegen
    for i, r in enumerate(results[:limit], start=1):
        r["rank"] = i
    return {"period": period, "leaderboard": results[:limit], "total_users": len(results)}



# v6_achievements_admin_edit_001 — Admin: titel + icon bewerken
from fastapi import UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional
from modules.admin.admin_service import is_admin
from modules.core.storage import save_json


class AchievementPatch(BaseModel):
    name: Optional[str] = None
    icon: Optional[str] = None  # emoji of URL-pad


ACHIEVEMENTS_FILE = Path(__file__).parent.parent.parent / "data" / "achievements.json"


@router.patch("/admin/{achievement_id}")
async def admin_patch_achievement(achievement_id: str, body: AchievementPatch, by_user: str):
    """Admin: pas naam en/of icon van een achievement aan."""
    if not is_admin(by_user):
        raise HTTPException(403, "Alleen admins mogen achievements bewerken.")
    data = load_json(ACHIEVEMENTS_FILE, default={"achievements": []})
    achs = data.get("achievements", [])
    target = next((a for a in achs if a.get("id") == achievement_id), None)
    if not target:
        raise HTTPException(404, f"Achievement '{achievement_id}' niet gevonden")
    updated = []
    if body.name is not None and body.name.strip():
        target["name"] = body.name.strip()
        updated.append("name")
    if body.icon is not None:
        target["icon"] = body.icon
        updated.append("icon")
    save_json(ACHIEVEMENTS_FILE, data)
    return {"success": True, "updated": updated, "achievement": target}


@router.post("/admin/{achievement_id}/icon-upload")
async def admin_upload_achievement_icon(
    achievement_id: str,
    by_user: str = Form(...),
    file: UploadFile = File(...),
):
    """Admin: upload afbeelding als icon — slaat op via system-archive."""
    if not is_admin(by_user):
        raise HTTPException(403, "Alleen admins mogen achievement-iconen wijzigen.")
    # Inline opslaan in system-archive (zelfde struct als /api/system-archive/upload)
    import uuid
    from datetime import datetime, timezone as _tz
    from modules.system_archive.routes import (
        ARCHIVE_DIR, _ensure_dirs, _detect_category, _load_index, _save_index, MAX_SIZE_BYTES,
    )
    _ensure_dirs()
    raw = await file.read()
    if len(raw) > MAX_SIZE_BYTES:
        raise HTTPException(413, "Icon te groot")
    if len(raw) == 0:
        raise HTTPException(400, "Leeg bestand")
    original = file.filename or "icon.png"
    cat = _detect_category(original)
    ext = Path(original).suffix.lower() or ".png"
    file_id = uuid.uuid4().hex[:12]
    safe = f"{file_id}{ext}"
    from modules.local_storage import persist_upload_bytes
    dest = persist_upload_bytes(ARCHIVE_DIR / cat / safe, raw)
    entry = {
        "id": file_id, "filename": safe, "original_name": original,
        "category": cat, "extension": ext,
        "mime_type": file.content_type or "image/png",
        "size_bytes": len(raw),
        "description": f"achievement-icon:{achievement_id}",
        "tags": ["achievement-icon"],
        "uploaded_at": datetime.now(_tz.utc).isoformat(),
        "uploaded_by": by_user, "path": str(dest),
        "scan_status": None, "scan_results": None,
    }
    idx = _load_index()
    idx.append(entry)
    _save_index(idx)
    icon_url = f"/api/system-archive/file/{file_id}"
    data = load_json(ACHIEVEMENTS_FILE, default={"achievements": []})
    target = next((a for a in data.get("achievements", []) if a.get("id") == achievement_id), None)
    if not target:
        raise HTTPException(404, f"Achievement '{achievement_id}' niet gevonden")
    target["icon"] = icon_url
    save_json(ACHIEVEMENTS_FILE, data)
    return {"success": True, "icon": icon_url, "archive_id": file_id}
