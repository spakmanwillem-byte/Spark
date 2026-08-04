"""v6_admin_role_001 — Admin als losstaande rol los van gradatie.

Helper-functies + grant/revoke/verify logic.

Datamodel:
  users.json per user heeft nu (optioneel) `admin: bool` flag.
  Migratie zet `admin=True` alleen voor user-001 (Willem) en user-000 (Spark).
  Andere users (incl. gradatie 2 familie) starten met admin=False.

Toekenning: alleen via /api/admin/grant met admin-wachtwoord uit ADMIN_PASSWORD env.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime, timezone

from modules.core.storage import load_json, save_json

USERS_FILE = Path(__file__).parent.parent.parent / "data" / "system" / "users.json"

# Initiale admins bij migratie (eerste run). Latere admin-grants gaan via /grant.
SEED_ADMIN_USER_IDS = {"user-001", "user-000"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_users() -> Dict:
    return load_json(USERS_FILE, default={"users": []})


def _save_users(data: Dict) -> None:
    save_json(USERS_FILE, data)


def get_user(user_id: str) -> Optional[Dict]:
    data = _load_users()
    return next((u for u in data.get("users", []) if u.get("id") == user_id), None)


def is_admin(user_id: Optional[str]) -> bool:
    """v6_admin_role_001 — Centrale admin-check.

    Returnt True alleen als user.admin == True.
    Negeert gradatie volledig — gradatie blijft puur sociaal.
    """
    if not user_id:
        return False
    u = get_user(user_id)
    return bool(u and u.get("admin") is True)


def is_admin_or_legacy_grad12(user_id: Optional[str]) -> bool:
    """Backwards-compat helper voor modules die nog niet gemigreerd zijn.

    Returnt True als user.admin==True OF gradatie ≤ 2 (oude gedrag).
    Gebruik dit ALLEEN voor sociale/visuele features (helptekst, UI-toggles).
    Voor gevoelige operaties (geld/data) → gebruik strict `is_admin()`.
    """
    if not user_id:
        return False
    u = get_user(user_id)
    if not u:
        return False
    if u.get("admin") is True:
        return True
    return (u.get("gradatie", 99) or 99) <= 2


def ensure_seed_admins() -> Dict:
    """Idempotent: zorg dat SEED_ADMIN_USER_IDS admin=True hebben.
    Verwijdert geen bestaande admins (additive).
    Wordt aangeroepen bij backend startup."""
    data = _load_users()
    changed = []
    for u in data.get("users", []):
        if u.get("id") in SEED_ADMIN_USER_IDS and u.get("admin") is not True:
            u["admin"] = True
            u["admin_granted_at"] = _now_iso()
            u["admin_granted_by"] = "system-seed"
            changed.append(u["id"])
    if changed:
        _save_users(data)
    return {"seeded": changed, "total_admins": sum(1 for u in data.get("users", []) if u.get("admin") is True)}


def verify_admin_password(password: str) -> bool:
    """Check meegegeven wachtwoord tegen ADMIN_PASSWORD env-var.
    Returnt False als env-var leeg/ontbreekt (= admin grant niet mogelijk).
    """
    expected = os.environ.get("ADMIN_PASSWORD", "").strip()
    if not expected:
        return False
    return password.strip() == expected


def grant_admin(target_user_id: str, granted_by: str, password: str, admin_type: str = "full") -> Dict:
    """Geef admin-rol aan een user.

    Vereisten:
      - granted_by MOET zelf admin zijn
      - password moet matchen met ADMIN_PASSWORD env-var
      - admin_type moet bestaan in /data/system/admin_types.json (default 'full')
    """
    if not is_admin(granted_by):
        return {"success": False, "error": "Alleen bestaande admin mag admin-rechten verlenen."}
    if not verify_admin_password(password):
        return {"success": False, "error": "Admin-wachtwoord onjuist.", "bark_kaart": "Toegang geweigerd"}

    # v12_admin_type_001 — Valideer type
    valid_ids = {t["id"] for t in list_admin_types()}
    if admin_type not in valid_ids:
        return {"success": False, "error": f"Onbekend admin-type '{admin_type}'. Kies uit: {sorted(valid_ids)}"}

    data = _load_users()
    target = next((u for u in data.get("users", []) if u.get("id") == target_user_id), None)
    if not target:
        return {"success": False, "error": f"Gebruiker {target_user_id} niet gevonden."}
    if target.get("admin") is True and target.get("admin_type") == admin_type:
        return {"success": True, "already": True, "user_id": target_user_id, "admin_type": admin_type,
                "bark_kaart": "Admin geactiveerd"}

    target["admin"] = True
    target["admin_type"] = admin_type
    target["admin_granted_at"] = _now_iso()
    target["admin_granted_by"] = granted_by
    _save_users(data)
    return {
        "success": True,
        "user_id": target_user_id,
        "naam": target.get("naam"),
        "admin_type": admin_type,
        "granted_by": granted_by,
        "bark_kaart": "Admin geactiveerd",
        "message": f"{target.get('naam', target_user_id)} is nu {admin_type}-admin.",
    }


# v12_admin_type_001 — Config-loader voor admin-types.
def list_admin_types() -> list:
    """Return alle vaste admin-types uit /data/system/admin_types.json."""
    import json as _json
    from pathlib import Path as _P
    p = _P(__file__).parent.parent.parent / "data" / "system" / "admin_types.json"
    if not p.exists():
        return [{"id": "full", "naam": "Beheerder", "scopes": ["*"], "is_default": True}]
    try:
        return _json.loads(p.read_text()).get("types", [])
    except Exception:
        return [{"id": "full", "naam": "Beheerder", "scopes": ["*"], "is_default": True}]


def revoke_admin(target_user_id: str, revoked_by: str) -> Dict:
    """Trek admin-rol in. Alleen door bestaande admin. Kan jezelf niet revoken
    als je de laatste admin bent (anti-lockout)."""
    if not is_admin(revoked_by):
        return {"success": False, "error": "Alleen bestaande admin mag admin-rechten intrekken."}

    data = _load_users()
    target = next((u for u in data.get("users", []) if u.get("id") == target_user_id), None)
    if not target:
        return {"success": False, "error": f"Gebruiker {target_user_id} niet gevonden."}
    if not target.get("admin"):
        return {"success": True, "already": True, "user_id": target_user_id}

    # Anti-lockout: niet de laatste admin laten verdwijnen
    admin_count = sum(1 for u in data.get("users", []) if u.get("admin") is True)
    if admin_count <= 1 and target.get("admin"):
        return {"success": False, "error": "Kan laatste admin niet intrekken (lockout-bescherming)."}

    target["admin"] = False
    target["admin_revoked_at"] = _now_iso()
    target["admin_revoked_by"] = revoked_by
    _save_users(data)
    return {
        "success": True,
        "user_id": target_user_id,
        "naam": target.get("naam"),
        "revoked_by": revoked_by,
        "bark_kaart": "Admin gedeactiveerd",
        "message": f"Admin-rol ingetrokken voor {target.get('naam', target_user_id)}.",
    }


def get_bark_image_for_concept(begrip: str) -> Optional[str]:
    """v6_admin_role_001 — Zoek een doen-kaart op begrip en geef eerste image_url.

    Gebruikt door bark-system om visueel commando-feedback te tonen
    (b.v. "Admin geactiveerd" → groen vinkje-image).

    Returnt None als geen kaart of geen image gevonden.
    """
    base = Path(__file__).parent.parent.parent / "data" / "knowledge" / "v2"
    target = (begrip or "").strip().lower()
    if not target:
        return None
    for lade in ("doen", "spreken", "voelen", "weten"):
        data = load_json(base / f"knowledge_v2_{lade}.json", default={"kaarten": []})
        for k in data.get("kaarten", []):
            if (k.get("begrip", "") or "").strip().lower() == target:
                imgs = (k.get("media", {}) or {}).get("image_urls") or []
                if imgs:
                    return imgs[0]
                return None
    return None


def list_admins() -> Dict:
    """Lijst van huidige admins."""
    data = _load_users()
    admins = [
        {"id": u.get("id"), "naam": u.get("naam"), "gradatie": u.get("gradatie"),
         "admin_type": u.get("admin_type") or "full",
         "admin_granted_at": u.get("admin_granted_at"), "admin_granted_by": u.get("admin_granted_by")}
        for u in data.get("users", []) if u.get("admin") is True
    ]
    return {"admins": admins, "count": len(admins)}
