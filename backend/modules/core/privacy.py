"""Privacy helper: check of viewer toegang mag hebben tot data van target user.

v13d_multi_module_privacy_001 (sessie 55) — Willem: "iedere user een eco-container".
Gebruikt door agenda, dagboek, notes, boekhouder.

Toegangsregels:
- viewer == target → altijd toegang (eigen data)
- viewer is admin/admin_capable → toegang (voor beheer)
- anders → HTTPException 403
"""
from pathlib import Path
from fastapi import HTTPException
from modules.core.storage import load_json

_USERS_FILE = Path(__file__).parent.parent.parent / "data" / "system" / "users.json"


def is_admin(user_id: str) -> bool:
    if not user_id:
        return False
    users = load_json(_USERS_FILE, default={"users": []}).get("users", [])
    for u in users:
        if u.get("id") == user_id:
            return bool(u.get("admin")) or bool(u.get("admin_capable"))
    return False


def require_access(viewer_id: str, target_user_id: str) -> None:
    """Raise 403 als viewer geen toegang mag hebben tot target's data."""
    if not viewer_id:
        raise HTTPException(403, "viewer_id ontbreekt in request")
    if viewer_id == target_user_id:
        return
    if is_admin(viewer_id):
        return
    raise HTTPException(
        403,
        f"Toegang geweigerd: user {viewer_id} mag data van {target_user_id} niet inzien",
    )
