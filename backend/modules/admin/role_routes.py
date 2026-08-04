"""v6_admin_role_001 — Endpoints voor admin grant/revoke/verify + bark-image lookup."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from . import admin_service as svc

router = APIRouter(prefix="/admin", tags=["admin-role"])


class GrantRequest(BaseModel):
    target_user_id: str
    granted_by: str
    password: str
    admin_type: Optional[str] = "full"  # v12_admin_type_001


@router.post("/grant")
async def grant_admin(req: GrantRequest):
    """Verleen admin-rol aan een user. Alleen door bestaande admin met geldig
    ADMIN_PASSWORD wachtwoord (env-var). admin_type default 'full'."""
    result = svc.grant_admin(req.target_user_id, req.granted_by, req.password, req.admin_type or "full")
    # Verrijk met bark-image
    if result.get("bark_kaart"):
        result["bark_image_url"] = svc.get_bark_image_for_concept(result["bark_kaart"])
    return result


# v12_admin_type_001 — Vaste admin-type-config voor RBAC light.
@router.get("/types")
async def get_admin_types():
    """Return de vaste admin-types (full / community / user_admin). Bevat naam,
    beschrijving, kleur en scope-array. Frontend gebruikt dit voor de dropdown
    in 'Maak admin' bark en voor toekomstige scope-gates."""
    return {"types": svc.list_admin_types()}


class RevokeRequest(BaseModel):
    target_user_id: str
    revoked_by: str


@router.post("/revoke")
async def revoke_admin(req: RevokeRequest):
    """Trek admin-rol in. Alleen door bestaande admin. Anti-lockout: laatste
    admin kan niet ge-revoked worden."""
    result = svc.revoke_admin(req.target_user_id, req.revoked_by)
    if result.get("bark_kaart"):
        result["bark_image_url"] = svc.get_bark_image_for_concept(result["bark_kaart"])
    return result


class VerifyRequest(BaseModel):
    password: str


@router.post("/verify")
async def verify_password(req: VerifyRequest):
    """Test of meegegeven wachtwoord matcht. Voor frontend admin-popup."""
    ok = svc.verify_admin_password(req.password)
    if ok:
        return {"success": True, "bark_kaart": "Toegang verleend",
                "bark_image_url": svc.get_bark_image_for_concept("Toegang verleend")}
    return {"success": False, "bark_kaart": "Toegang geweigerd",
            "bark_image_url": svc.get_bark_image_for_concept("Toegang geweigerd")}


class ChangePasswordRequest(BaseModel):
    user_id: str
    old_password: str
    new_password: str


@router.post("/password/reset")
async def reset_admin_password(req: ChangePasswordRequest):
    """v6_admin_role_001 — Reset admin-wachtwoord. Alleen door admin zelf
    met het huidige wachtwoord.

    Note: wachtwoord wordt opgeslagen in `data/system/admin_password.json`
    omdat .env in productie niet runtime-writable is. Bij eerste reset wordt
    het env-var-wachtwoord vervangen door de nieuwe versie in het JSON-bestand.
    """
    import os
    import json
    from pathlib import Path
    if not svc.is_admin(req.user_id):
        raise HTTPException(403, "Alleen admin mag wachtwoord wijzigen.")
    if not svc.verify_admin_password(req.old_password):
        return {"success": False, "error": "Oud wachtwoord onjuist.",
                "bark_kaart": "Toegang geweigerd",
                "bark_image_url": svc.get_bark_image_for_concept("Toegang geweigerd")}
    if not req.new_password or len(req.new_password) < 6:
        return {"success": False, "error": "Nieuw wachtwoord moet minimaal 6 tekens zijn."}

    pw_file = Path(__file__).parent.parent.parent / "data" / "system" / "admin_password.json"
    pw_file.parent.mkdir(parents=True, exist_ok=True)
    pw_file.write_text(json.dumps({
        "password": req.new_password,
        "changed_at": svc._now_iso(),
        "changed_by": req.user_id,
    }))
    # Update env voor lopende process
    os.environ["ADMIN_PASSWORD"] = req.new_password
    return {"success": True, "bark_kaart": "Admin geactiveerd",
            "bark_image_url": svc.get_bark_image_for_concept("Admin geactiveerd"),
            "message": "Admin-wachtwoord gewijzigd."}


@router.get("/list")
async def list_admins(viewer_id: Optional[str] = None):
    """Lijst van huidige admins. Alleen voor admins."""
    if not svc.is_admin(viewer_id):
        raise HTTPException(403, "Alleen admin mag admin-lijst zien.")
    return svc.list_admins()


@router.get("/is-admin/{user_id}")
async def check_is_admin(user_id: str):
    """Public: check of een user admin is. Voor frontend UI-state."""
    return {"user_id": user_id, "is_admin": svc.is_admin(user_id)}


@router.get("/bark-image")
async def get_bark_image(begrip: str):
    """Public: krijg image_url voor een bark-concept (begrip in lade)."""
    url = svc.get_bark_image_for_concept(begrip)
    return {"begrip": begrip, "image_url": url}


@router.post("/help-bark")
async def get_help_bark(viewer_id: Optional[str] = None, scope: str = "general"):
    """Krijg de juiste help-bark voor de viewer. scope='general' (Help) of
    'admin' (Help Admin). Frontend kiest welke help getoond moet worden."""
    bark_begrip = "Help Admin" if scope == "admin" else "Help"
    img = svc.get_bark_image_for_concept(bark_begrip)
    # Help-tekst per gradatie (helpgradatie blijft sociaal)
    u = svc.get_user(viewer_id) if viewer_id else None
    gradatie = (u or {}).get("gradatie", 7) if u else 7
    return {
        "scope": scope,
        "bark_image_url": img,
        "begrip": bark_begrip,
        "gradatie": gradatie,
        "is_admin": svc.is_admin(viewer_id) if viewer_id else False,
    }
