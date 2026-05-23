"""
Spark Auth Module - API Routes
All auth endpoints in one place
"""
from fastapi import APIRouter, HTTPException
from typing import Optional
from pydantic import BaseModel

from .service import AuthService
from .models import LoginRequest, LoginResponse, SessionStatus, UserCreate
from modules.core.storage import load_json, save_json

router = APIRouter(prefix="/auth", tags=["auth"])


# ============== LOGIN / LOGOUT ==============

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Login with naam + sleutelwoord
    
    Returns user data if successful
    """
    user, is_masterkey = AuthService.authenticate(
        naam=request.naam,
        sleutelwoord=request.sleutelwoord,
        masterkey=request.masterkey
    )
    
    if not user:
        return LoginResponse(
            success=False,
            message="Ongeldige inloggegevens",
            user=None,
            is_masterkey=False
        )
    
    # Update activity
    AuthService.heartbeat(user.get("id"))

    # v5_barks_001 — F1: Mr Smith login-counter bark (3/4/5 → bark, 6 → reset)
    try:
        from modules.bots.proactive_barks import handle_login_bark
        handle_login_bark(user.get("id"), user.get("naam") or user.get("name") or "")
    except Exception:
        pass

    # v5_welcome_001 — Spark stuurt persoonlijke welkom bij eerste login (idempotent per WELCOME_VERSION)
    try:
        from modules.bots.spark_welcome_service import maybe_send_welcome
        maybe_send_welcome(user)
    except Exception:
        pass

    # v4_grad_titel_001: voeg gradatie_titel toe voor warme weergave in UI
    try:
        ginfo = AuthService.get_gradatie_info(user.get("gradatie", 7))
        if ginfo:
            user["gradatie_titel"] = ginfo.get("titel", "")
    except Exception:
        pass

    return LoginResponse(
        success=True,
        message="Welkom terug!" if not is_masterkey else "Masterkey toegang",
        user=user,
        is_masterkey=is_masterkey
    )


@router.post("/logout")
async def logout(user_id: str):
    """
    Logout user (clear session state om stale pending_* flows te voorkomen).
    Anders zit een gebruiker bij eerste bericht na opnieuw inloggen vast in
    een oude wedervraag/card_session.
    """
    try:
        from modules.chat import session_state
        session_state.clear_state(user_id)
    except Exception as e:
        print(f"[logout] clear_state failed (niet fataal): {e}")
    return {"success": True, "message": "Uitgelogd"}


# ============== SESSION ==============

@router.post("/session/heartbeat", response_model=SessionStatus)
async def heartbeat(user_id: str):
    """
    Session heartbeat - keeps session alive
    
    Should be called every 30 seconds from frontend
    """
    result = AuthService.heartbeat(user_id)
    
    if result.get("status") == "invalid":
        raise HTTPException(status_code=401, detail="Sessie ongeldig")
    
    return SessionStatus(**result)


@router.get("/session/validate")
async def validate_session(user_id: str):
    """
    Check if session is still valid
    """
    is_valid = AuthService.validate_session(user_id)
    
    if not is_valid:
        return {"valid": False, "message": "Sessie verlopen"}
    
    user = AuthService.get_user_by_id(user_id)
    return {
        "valid": True,
        "user": user
    }


# ============== USER MANAGEMENT ==============

@router.get("/users")
async def get_users():
    """
    Get all users (admin only in production)
    """
    users = AuthService.get_all_users()
    # Remove sensitive fields
    safe_users = []
    for u in users:
        safe_user = {k: v for k, v in u.items() if k not in ["masterkey"]}
        safe_users.append(safe_user)
    return {"users": safe_users, "count": len(safe_users)}


@router.get("/users/{user_id}")
async def get_user(user_id: str):
    """
    Get user by ID
    """
    user = AuthService.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Gebruiker niet gevonden")
    return user


@router.post("/users")
async def create_user(user_data: UserCreate, admin_id: Optional[str] = None):
    """
    Create new user.

    - Self-registration (admin_id=None): collisie-check + minstens 4 tekens.
    - Admin override (?admin_id=<gradatie 1/2 user>): collisie-check + lengte-eis
      overgeslagen. Hiermee kan admin meerdere accounts maken met gedeeld
      default-sleutelwoord (bv. 'Welkom01').
    """
    admin_override = False
    if admin_id:
        admin_user = AuthService.get_user_by_id(admin_id)
        if not admin_user or admin_user.get("gradatie", 99) > 2:
            raise HTTPException(status_code=403, detail="Alleen admin (gradatie 1 of 2) mag override gebruiken.")
        admin_override = True

    user, error = AuthService.create_user(user_data, admin_override=admin_override)
    
    if error:
        raise HTTPException(status_code=400, detail=error)
    
    return {"success": True, "user": user, "admin_override": admin_override}


@router.put("/users/{user_id}")
async def update_user(user_id: str, updates: dict):
    """
    Update user fields
    """
    # Protect sensitive fields
    protected = ["id", "masterkey", "registered_date"]
    updates = {k: v for k, v in updates.items() if k not in protected}
    
    if not AuthService.update_user(user_id, updates):
        raise HTTPException(status_code=404, detail="Gebruiker niet gevonden")
    
    return {"success": True}


@router.delete("/users/{user_id}")
async def delete_user(user_id: str):
    """
    Delete user. user-001 (admin) kan niet verwijderd worden.
    """
    if user_id == "user-001":
        raise HTTPException(status_code=403, detail="Admin gebruiker kan niet verwijderd worden")

    if not AuthService.delete_user(user_id):
        raise HTTPException(status_code=404, detail="Gebruiker niet gevonden")

    return {"success": True}


# v4_self_delete_001 — User wist zijn EIGEN account, met 30-dagen backup
@router.delete("/self-delete/{user_id}")
async def self_delete_account(user_id: str, confirm: bool = False):
    """User verwijdert zijn EIGEN account.
    Maakt backup naar /data/_deleted_users/{user_id}_{ISO}.json (30 dagen bewaard).
    """
    if not confirm:
        raise HTTPException(400, "confirm=true vereist")
    if user_id == "user-001":
        raise HTTPException(403, "Admin gebruiker kan niet verwijderd worden")
    user = AuthService.get_user_by_id(user_id) if hasattr(AuthService, "get_user_by_id") else None
    if not user:
        # Fallback: zoek manueel
        from pathlib import Path as _P
        users_data = load_json(_P(__file__).parent.parent.parent / "data" / "system" / "users.json", default={"users": []})
        user = next((u for u in users_data.get("users", []) if u.get("id") == user_id), None)
    if not user:
        raise HTTPException(404, "Gebruiker niet gevonden")

    # 1) Backup naar _deleted_users dir
    from pathlib import Path as _P
    from datetime import datetime as _dt, timezone as _tz
    base = _P(__file__).parent.parent.parent / "data"
    bkp_dir = base / "_deleted_users"
    bkp_dir.mkdir(parents=True, exist_ok=True)
    stamp = _dt.now(_tz.utc).strftime("%Y%m%d_%H%M%S")
    bkp_path = bkp_dir / f"{user_id}_{stamp}.json"
    # Verzamel alle user-bound data
    payload = {
        "user_id": user_id,
        "deleted_at": _dt.now(_tz.utc).isoformat(),
        "user_record": user,
        "files": {},
    }
    # Bekende user-gebonden files (best effort)
    candidates = [
        f"persons/{user_id}.json",
        f"persons/{user_id}_relationships.json",
        f"agenda/{user_id}.json",
        f"chat/logs/{user_id}.json",
        f"chat/sessions/{user_id}.json",
        f"dagboek/{user_id}.json",
        f"settings/user_{user_id}.json",
        f"urgent/acks_{user_id}.json",
        f"users/{user_id}/profile.json",
        f"users/{user_id}/settings.json",
    ]
    for rel in candidates:
        fp = base / rel
        if fp.exists():
            try:
                payload["files"][rel] = load_json(fp, default=None)
            except Exception:
                pass
    save_json(bkp_path, payload)

    # 2) Auto-cleanup oude backups (>30 dagen)
    cutoff = _dt.now(_tz.utc).timestamp() - 30 * 86400
    cleaned = 0
    for f in bkp_dir.iterdir():
        try:
            if f.is_file() and f.stat().st_mtime < cutoff:
                f.unlink()
                cleaned += 1
        except OSError:
            pass

    # 3) Verwijder echte user record (data files blijven, mocht een admin willen herstellen
    #    binnen 30 dagen via backup file)
    AuthService.delete_user(user_id)

    return {
        "success": True,
        "message": "Account verwijderd. Backup bewaard voor 30 dagen.",
        "backup_file": bkp_path.name,
        "old_backups_cleaned": cleaned,
    }


@router.post("/users/{user_id}/reset-password")
async def reset_password(user_id: str, new_sleutelwoord: Optional[str] = None):
    """
    Reset sleutelwoord van gebruiker. Default: 'Welkom01'.
    Gebruik query-param ?new_sleutelwoord=... voor custom.
    """
    nw = new_sleutelwoord or "Welkom01"
    result = AuthService.reset_password(user_id, nw)
    if not result:
        raise HTTPException(status_code=404, detail="Gebruiker niet gevonden")
    return {"success": True, "sleutelwoord": result, "message": f"Sleutelwoord gereset naar '{result}'"}


# v5_self_password_001 — user kan eigen sleutelwoord wijzigen vanuit Mijn Profiel → Instellingen
class ChangePasswordRequest(BaseModel):
    current_sleutelwoord: str
    new_sleutelwoord: str


@router.post("/users/{user_id}/change-password")
async def change_password(user_id: str, req: ChangePasswordRequest):
    """
    Self-service sleutelwoord wijzigen. Vereist huidig sleutelwoord.
    Gebruik nieuw_sleutelwoord='Welkom01' voor een reset-naar-default.
    """
    ok, msg = AuthService.change_password(user_id, req.current_sleutelwoord, req.new_sleutelwoord)
    if not ok:
        return {"success": False, "error": msg}
    return {"success": True, "message": msg}


@router.get("/users/{user_id}/time-awareness")
async def get_time_awareness(user_id: str):
    """v4_025: Wat denkt Spark dat de tijd is voor deze user?
    Toont timezone-source, lokale tijd, weekdag en dagdeel."""
    user = AuthService.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Gebruiker niet gevonden")
    try:
        from modules.chat.user_time_service import time_awareness_block
        return time_awareness_block(user)
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Fout: {ex}")


# ============== GRADATIE ==============

@router.get("/gradaties")
async def get_gradaties():
    """
    Get all gradatie definitions
    """
    return {"gradaties": AuthService.get_gradaties()}


@router.put("/users/{user_id}/gradatie")
async def update_gradatie(user_id: str, gradatie: int, reden: str = ""):
    """
    Update user gradatie
    """
    if gradatie < 1 or gradatie > 7:
        raise HTTPException(status_code=400, detail="Gradatie moet tussen 1 en 7 zijn")
    
    if not AuthService.update_gradatie(user_id, gradatie, reden):
        raise HTTPException(status_code=404, detail="Gebruiker niet gevonden")
    
    return {"success": True}



# v5_bot_settings_tab_001 — Bot-specifieke settings update (alleen voor is_bot users)
class BotSettingsPatch(BaseModel):
    personality: Optional[str] = None
    rol: Optional[str] = None
    channels: Optional[list] = None
    avatar_lock: Optional[bool] = None
    bark_template: Optional[str] = None
    # v5_bot_stt_tts_001 — voorbereiding voor stemkoppeling
    stt_enabled: Optional[bool] = None
    tts_enabled: Optional[bool] = None
    tts_voice: Optional[str] = None


@router.patch("/admin/bots/{bot_id}/settings")
async def patch_bot_settings(bot_id: str, body: BotSettingsPatch):
    """Update bot-persona velden. Werkt alleen op users met is_bot=true."""
    users = AuthService.get_all_users()
    target = next((u for u in users if (u.get("id") or u.get("user_id")) == bot_id), None)
    if not target:
        raise HTTPException(404, f"Bot {bot_id} niet gevonden")
    if not target.get("is_bot"):
        raise HTTPException(400, f"{bot_id} is geen bot — gebruik /users/{bot_id} voor gewone users")
    updates = {k: v for k, v in body.dict(exclude_unset=True).items() if v is not None}
    if not updates:
        return {"success": True, "updated": [], "message": "Niets te updaten"}
    AuthService.update_user(bot_id, updates)
    return {"success": True, "updated": list(updates.keys()), "bot_id": bot_id}
