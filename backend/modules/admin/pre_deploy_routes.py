"""
v6_pre_deploy_reset_001 — Admin endpoint voor pre/post-deploy schoonmaak.

Eén knop die:
  1. Shadow-cascade UIT zet (data/trade/shadow_flag.json)
  2. ROAR balances reset naar door admin opgegeven map

Vereist: admin-rol (user.admin == True).
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional
from pathlib import Path
from datetime import datetime, timezone
from modules.core.storage import load_json, save_json
from modules.admin.admin_service import is_admin

router = APIRouter(prefix="/admin/system", tags=["admin-system"])

ROAR_FILE = Path(__file__).parent.parent.parent / "data" / "roar" / "roar_balances.json"
SHADOW_FLAG_FILE = Path(__file__).parent.parent.parent / "data" / "trade" / "shadow_flag.json"


class ResetBody(BaseModel):
    by_user: str  # admin user_id die de actie uitvoert
    balances: Optional[Dict[str, int]] = None  # {user_id: nieuwe_balance}
    disable_shadow: bool = True


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@router.post("/pre-deploy-reset")
def pre_deploy_reset(body: ResetBody):
    """
    Pre/post-deploy schoonmaak:
      - balances: optionele dict {user_id: nieuw_saldo} → vervangt ALLE balances
      - disable_shadow: True (default) → zet shadow-cascade UIT

    Retourneert wat er is gewijzigd. Admin-only.
    """
    if not is_admin(body.by_user):
        raise HTTPException(403, "Alleen admins mogen pre-deploy reset uitvoeren.")

    result = {"success": True, "ts": _now(), "by": body.by_user}

    # 1. Shadow flag UIT
    if body.disable_shadow:
        sf = load_json(SHADOW_FLAG_FILE, default={})
        prev = sf.get("enabled")
        sf.update({
            "enabled": False,
            "updated_at": _now(),
            "updated_by": body.by_user,
            "note": "pre_deploy_reset endpoint",
        })
        save_json(SHADOW_FLAG_FILE, sf)
        result["shadow_flag"] = {"was": prev, "now": False}

    # 2. ROAR balances reset
    if body.balances is not None:
        roar = load_json(ROAR_FILE, default={"balances": {}})
        prev_balances = dict(roar.get("balances", {}))
        # Valideer ints
        new_balances = {k: int(v) for k, v in body.balances.items()}
        roar["balances"] = new_balances
        roar.setdefault("admin_log", []).append({
            "ts": _now(),
            "action": "pre_deploy_reset_balances",
            "by": body.by_user,
            "previous": prev_balances,
            "new": new_balances,
        })
        save_json(ROAR_FILE, roar)
        result["balances"] = {"previous": prev_balances, "new": new_balances}

    return result


@router.get("/health-status")
def health_status():
    """Snelle check: huidige shadow-flag + ROAR-balances voor admin-UI."""
    sf = load_json(SHADOW_FLAG_FILE, default={"enabled": False})
    roar = load_json(ROAR_FILE, default={"balances": {}})
    return {
        "shadow_enabled": bool(sf.get("enabled")),
        "shadow_updated_at": sf.get("updated_at"),
        "roar_balances": roar.get("balances", {}),
    }
