"""
Settings Module (v4_settings_001) — System + User instellingen met gradatie-gating.

Architectuur:
  - /data/settings/system.json     → system defaults (alle users zien dit)
  - /data/settings/user_<id>.json  → per-user override (alleen voor scope='user' settings)

Resolutie: bij effective: system overlay user. User leegmaken = reset naar default.

Gradatie-gating:
  - System-scope settings: alleen gradatie ≤ SYSTEM_EDIT_GRAD wijzigbaar
  - User-scope settings: user zelf OF admin (≤ SYSTEM_EDIT_GRAD)
"""
from pathlib import Path
from typing import Optional, Any, Dict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from modules.core.storage import load_json, save_json

router = APIRouter(prefix="/settings", tags=["settings"])

DATA_ROOT = Path(__file__).parent.parent.parent / "data"
SETTINGS_DIR = DATA_ROOT / "settings"
SYSTEM_FILE = SETTINGS_DIR / "system.json"
USERS_FILE = DATA_ROOT / "system" / "users.json"
SETTINGS_DIR.mkdir(parents=True, exist_ok=True)

SYSTEM_EDIT_GRAD = 1  # alleen gradatie 1 mag system-settings wijzigen (later: ook 2-admin)

# Schema: type + scope + (optioneel) min/max/options/min_gradatie
SCHEMA: Dict[str, Dict[str, Any]] = {
    # System-scope (alleen admin)
    "heartbeat_interval": {"type": "int", "scope": "system", "min": 10, "max": 300},
    "session_timeout": {"type": "int", "scope": "system", "min": 1, "max": 60},
    "debug_mode": {"type": "bool", "scope": "system"},
    "auto_save": {"type": "bool", "scope": "system"},
    # v5_admin_color_scheme_001 — app-wide kleurenschema (admin only)
    "app_primary_accent": {"type": "str", "scope": "system"},   # hex bv #f59e0b
    "app_secondary_accent": {"type": "str", "scope": "system"}, # hex bv #06b6d4
    "app_background_tint": {"type": "str", "scope": "system"},  # hex bv #0f172a
    # v13s_login_glow_config_001 — login-scherm glow + logo (systeem, admin only)
    # Zie Beheer → Instellingen → Beeld → "Login Glow & Spark-logo"
    "login_dots_count": {"type": "int", "scope": "system", "min": 4, "max": 24},        # aantal glow-puntjes (default 8)
    "login_dots_contrast": {"type": "float", "scope": "system", "min": 0.1, "max": 1.0},# opacity/contrast (default 0.6)
    "login_dots_size": {"type": "float", "scope": "system", "min": 0.5, "max": 3.0},    # grootte-multiplier (default 1.0)
    "login_corner_glow_enabled": {"type": "bool", "scope": "system"},                    # aan/uit vinkje (default true)
    "login_corner_glow_color_a": {"type": "str", "scope": "system"},                     # linksboven hex (default primary)
    "login_corner_glow_color_b": {"type": "str", "scope": "system"},                     # rechtsonder hex (default secondary)
    "spark_logo_url": {"type": "str", "scope": "system"},                                # URL/path naar Spark-logo (default null → fallback Sparkles icon)
    # v5_bot_color_scheme_001 — per-bot accent kleur (admin) — gebruikt door GesprekkenPage / CommunityPage bubbles
    "bot_color_madelief": {"type": "str", "scope": "system"},   # default #ec4899
    "bot_color_harry":    {"type": "str", "scope": "system"},   # default #06b6d4
    "bot_color_smith":    {"type": "str", "scope": "system"},   # default #10b981
    "bot_color_boekhouder": {"type": "str", "scope": "system"}, # default #f59e0b
    "bot_color_dood":     {"type": "str", "scope": "system"},   # default #a855f7
    # User-scope (iedereen voor zichzelf)
    "theme": {"type": "str", "scope": "user", "options": ["dark", "light"]},
    "mood_colors": {"type": "bool", "scope": "user"},
    "notification_sound": {"type": "bool", "scope": "user"},
    "master_volume": {"type": "int", "scope": "user", "min": 0, "max": 100},
    "enable_user_sounds": {"type": "bool", "scope": "user"},
    "tts_enabled": {"type": "bool", "scope": "user"},
    "tts_voice": {"type": "str", "scope": "user", "options": ["nova", "alloy", "echo", "fable", "onyx", "shimmer"]},
    "tts_speed": {"type": "float", "scope": "user", "min": 0.5, "max": 2.0},
    "tts_auto_play": {"type": "bool", "scope": "user"},
    "stt_enabled": {"type": "bool", "scope": "user"},
    "stt_language": {"type": "str", "scope": "user", "options": ["nl", "en", "de"]},
    "stt_push_to_talk": {"type": "bool", "scope": "user"},
    "stt_silence_sec": {"type": "float", "scope": "user", "min": 0.5, "max": 5.0},
    # v6_kb_sound_001 — Speel KB-kaart geluid af wanneer Spark een begrip noemt dat een 'geluid'-audio heeft
    "kb_sound_enabled": {"type": "bool", "scope": "user"},
    "ambient_default_volume": {"type": "float", "scope": "user", "min": 0.0, "max": 1.0},
    "ambient_duck_volume": {"type": "float", "scope": "user", "min": 0.0, "max": 1.0},
}


# ============== HELPERS ==============
def _user_file(user_id: str) -> Path:
    return SETTINGS_DIR / f"user_{user_id}.json"


def _get_user_gradatie(user_id: str) -> Optional[int]:
    if not user_id:
        return None
    data = load_json(USERS_FILE, default={"users": []})
    for u in data.get("users", []):
        if u.get("id") == user_id:
            return u.get("gradatie")
    return None


def _validate(key: str, value: Any) -> Any:
    if key not in SCHEMA:
        raise HTTPException(status_code=400, detail=f"Onbekende setting '{key}'")
    schema = SCHEMA[key]
    t = schema["type"]
    try:
        if t == "bool":
            value = bool(value) if isinstance(value, bool) else str(value).lower() in ("true", "1", "yes", "aan")
        elif t == "int":
            value = int(value)
        elif t == "float":
            value = float(value)
        elif t == "str":
            value = str(value)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail=f"Ongeldige waarde voor '{key}': verwacht {t}")
    if "options" in schema and value not in schema["options"]:
        raise HTTPException(status_code=400, detail=f"Waarde voor '{key}' moet zijn: {schema['options']}")
    if "min" in schema and value < schema["min"]:
        raise HTTPException(status_code=400, detail=f"'{key}' moet ≥ {schema['min']}")
    if "max" in schema and value > schema["max"]:
        raise HTTPException(status_code=400, detail=f"'{key}' moet ≤ {schema['max']}")
    return value


# ============== MODELS ==============
class SetValue(BaseModel):
    value: Any
    viewer_id: str  # wie wijzigt (voor gradatie-check)


# ============== ROUTES ==============
@router.get("/schema")
async def get_schema():
    """Alle keys + types + opties (voor UI rendering)."""
    return {"schema": SCHEMA, "system_edit_gradatie_max": SYSTEM_EDIT_GRAD}


@router.get("/system")
async def get_system_settings():
    """Alle system defaults."""
    data = load_json(SYSTEM_FILE, default={})
    data.pop("_meta", None)
    return {"settings": data}


@router.get("/user/{user_id}")
async def get_user_overrides(user_id: str):
    """Alleen de overrides die user expliciet heeft gezet."""
    data = load_json(_user_file(user_id), default={})
    return {"user_id": user_id, "overrides": data}


@router.get("/effective/{user_id}")
async def get_effective(user_id: str):
    """System defaults + user overrides (= wat de UI moet tonen)."""
    sys_data = load_json(SYSTEM_FILE, default={})
    sys_data.pop("_meta", None)
    user_data = load_json(_user_file(user_id), default={})
    effective = {**sys_data, **user_data}
    return {"user_id": user_id, "effective": effective, "overridden_keys": list(user_data.keys())}


@router.put("/system/{key}")
async def set_system(key: str, req: SetValue):
    if key not in SCHEMA:
        raise HTTPException(status_code=400, detail=f"Onbekende setting '{key}'")
    if SCHEMA[key]["scope"] != "system":
        raise HTTPException(status_code=400, detail=f"'{key}' is een user-scope setting, gebruik /user endpoint")
    grad = _get_user_gradatie(req.viewer_id)
    if grad is None or grad > SYSTEM_EDIT_GRAD:
        raise HTTPException(status_code=403, detail=f"Alleen gradatie ≤ {SYSTEM_EDIT_GRAD} mag system-settings wijzigen")
    value = _validate(key, req.value)
    data = load_json(SYSTEM_FILE, default={})
    data[key] = value
    save_json(SYSTEM_FILE, data)
    return {"success": True, "key": key, "value": value, "scope": "system"}


@router.put("/user/{user_id}/{key}")
async def set_user(user_id: str, key: str, req: SetValue):
    if key not in SCHEMA:
        raise HTTPException(status_code=400, detail=f"Onbekende setting '{key}'")
    if SCHEMA[key]["scope"] != "user":
        raise HTTPException(status_code=400, detail=f"'{key}' is een system-scope setting, gebruik /system endpoint")
    # Permissie: user zelf OF admin (grad ≤ SYSTEM_EDIT_GRAD)
    viewer_grad = _get_user_gradatie(req.viewer_id)
    if req.viewer_id != user_id and (viewer_grad is None or viewer_grad > SYSTEM_EDIT_GRAD):
        raise HTTPException(status_code=403, detail="Alleen voor jezelf of admin")
    value = _validate(key, req.value)
    fp = _user_file(user_id)
    data = load_json(fp, default={})
    data[key] = value
    save_json(fp, data)
    return {"success": True, "key": key, "value": value, "scope": "user", "user_id": user_id}


@router.delete("/user/{user_id}/{key}")
async def reset_user(user_id: str, key: str, viewer_id: str):
    """Verwijder user-override → val terug op system default."""
    viewer_grad = _get_user_gradatie(viewer_id)
    if viewer_id != user_id and (viewer_grad is None or viewer_grad > SYSTEM_EDIT_GRAD):
        raise HTTPException(status_code=403, detail="Alleen voor jezelf of admin")
    fp = _user_file(user_id)
    data = load_json(fp, default={})
    if key in data:
        del data[key]
        save_json(fp, data)
    return {"success": True, "key": key, "reset_to_default": True}


# ============================================================
# v13s_login_glow_config_001 — Spark-logo upload endpoint
# ============================================================
from fastapi import UploadFile, File, Form
from fastapi.responses import FileResponse

LOGO_DIR = DATA_ROOT / "system" / "branding"
LOGO_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_LOGO_EXT = {".png", ".jpg", ".jpeg", ".webp", ".svg"}


@router.post("/system/spark-logo")
async def upload_spark_logo(viewer_id: str = Form(...), file: UploadFile = File(...)):
    """Upload Spark's systeem-logo. Bewaart in /data/system/branding/spark_logo.{ext}
    en zet `spark_logo_url` in system settings naar de public serve URL.
    Alleen gradatie ≤ SYSTEM_EDIT_GRAD (admin) mag dit.
    """
    grad = _get_user_gradatie(viewer_id)
    if grad is None or grad > SYSTEM_EDIT_GRAD:
        raise HTTPException(status_code=403, detail=f"Alleen gradatie ≤ {SYSTEM_EDIT_GRAD} mag Spark-logo uploaden")

    filename = file.filename or ""
    ext = "." + filename.split(".")[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_LOGO_EXT:
        raise HTTPException(status_code=400, detail=f"Bestandstype '{ext}' niet toegestaan. Kies: {sorted(ALLOWED_LOGO_EXT)}")

    # Overschrijf altijd naar consistente naam met huidige extensie
    for existing in LOGO_DIR.glob("spark_logo.*"):
        existing.unlink(missing_ok=True)
    target = LOGO_DIR / f"spark_logo{ext}"
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:  # 5 MB cap
        raise HTTPException(status_code=413, detail="Logo mag max 5 MB zijn")
    target.write_bytes(content)

    # Update system setting met de public serve URL (via /api/settings/spark-logo/serve)
    from datetime import datetime, timezone
    data = load_json(SYSTEM_FILE, default={})
    # Cache-buster via timestamp zodat browser niet oude versie toont
    ts = int(datetime.now(timezone.utc).timestamp())
    data["spark_logo_url"] = f"/api/settings/spark-logo/serve?v={ts}"
    save_json(SYSTEM_FILE, data)

    return {"success": True, "url": data["spark_logo_url"], "size_bytes": len(content), "ext": ext}


@router.get("/spark-logo/serve")
async def serve_spark_logo():
    """Publieke serve endpoint voor het Spark-logo (bereikbaar vanaf login-scherm zonder auth)."""
    for existing in LOGO_DIR.glob("spark_logo.*"):
        return FileResponse(existing, media_type=f"image/{existing.suffix[1:]}")
    raise HTTPException(status_code=404, detail="Nog geen Spark-logo geupload")


@router.delete("/system/spark-logo")
async def delete_spark_logo(viewer_id: str):
    """Verwijder Spark-logo → fallback naar Sparkles icon."""
    grad = _get_user_gradatie(viewer_id)
    if grad is None or grad > SYSTEM_EDIT_GRAD:
        raise HTTPException(status_code=403, detail=f"Alleen gradatie ≤ {SYSTEM_EDIT_GRAD} mag Spark-logo verwijderen")
    for existing in LOGO_DIR.glob("spark_logo.*"):
        existing.unlink(missing_ok=True)
    data = load_json(SYSTEM_FILE, default={})
    data.pop("spark_logo_url", None)
    save_json(SYSTEM_FILE, data)
    return {"success": True, "reset_to_default": True}
