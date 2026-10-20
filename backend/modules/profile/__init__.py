"""
Spark Profile, Willem Personality, Roadmap, Notifications, Extended Profile
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime, timezone
import uuid
from modules.core.storage import load_json, save_json

router = APIRouter(tags=["profile"])
DATA_DIR = Path(__file__).parent.parent.parent / "data"
PERSONALITY_DIR = DATA_DIR / "personality"
SYSTEM_DIR = DATA_DIR / "system"
NOTIF_FILE = DATA_DIR / "notifications" / "notifications.json"
USERS_DIR = DATA_DIR / "users"


# ============================================================
# SPARK PROFIEL
# ============================================================

@router.get("/spark/profile")
async def get_spark_profile():
    data = load_json(PERSONALITY_DIR / "spark_profile.json", default={})
    return {"success": True, "profile": data.get("spark_profiel", {})}


@router.get("/spark/about")
async def get_spark_about():
    data = load_json(PERSONALITY_DIR / "spark_profile.json", default={})
    profiel = data.get("spark_profiel", {})
    return {
        "success": True,
        "naam": profiel.get("basis", {}).get("naam", "Spark"),
        "biografie": profiel.get("biografie", {}),
        "identiteit": profiel.get("identiteit", {}),
        "filosofie": profiel.get("filosofie", {}),
        "kernwaarden": profiel.get("biografie", {}).get("kernwaarden", []),
    }


# ============================================================
# WILLEM PERSONALITY
# ============================================================

@router.get("/personality/{user_id}")
async def get_user_personality(user_id: str):
    data = load_json(PERSONALITY_DIR / "willem_personality.json", default={})
    return {"success": True, "user_id": user_id, "personality": data}


@router.put("/personality/{user_id}")
async def update_user_personality(user_id: str, updates: Dict[str, Any]):
    data = load_json(PERSONALITY_DIR / "willem_personality.json", default={})
    for k, v in updates.items():
        data[k] = v
    data.setdefault("metadata", {})["last_updated"] = datetime.now(timezone.utc).isoformat()
    save_json(PERSONALITY_DIR / "willem_personality.json", data)
    return {"success": True, "personality": data}


# ============================================================
# ROADMAP API
# ============================================================

@router.get("/roadmap")
async def get_roadmap():
    data = load_json(SYSTEM_DIR / "roadmap.json", default={})
    return {"success": True, "roadmap": data}


@router.get("/roadmap/summary")
async def get_roadmap_summary():
    data = load_json(SYSTEM_DIR / "roadmap.json", default={})
    summary = data.get("summary", {})
    versions = {}
    for key in data:
        if key.startswith("v") and key[1:2].isdigit():
            v = data[key]
            if isinstance(v, dict):
                items = v.get("items", v.get("features", []))
                if isinstance(items, list):
                    done = sum(1 for i in items if isinstance(i, dict) and i.get("status") in ("done", "completed", "klaar"))
                    versions[key] = {"total": len(items), "done": done, "title": v.get("title", v.get("naam", key))}
                else:
                    versions[key] = {"title": v.get("title", v.get("naam", key))}
    return {"success": True, "summary": summary, "versions": versions}


@router.get("/roadmap/version/{version}")
async def get_roadmap_version(version: str):
    data = load_json(SYSTEM_DIR / "roadmap.json", default={})
    v = data.get(version) or data.get(f"v{version}")
    if not v:
        return {"success": False, "error": f"Versie {version} niet gevonden"}
    return {"success": True, "version": version, "data": v}


class RoadmapItemCreate(BaseModel):
    titel: str
    versie: str = "v6.0"
    priority: Optional[str] = "medium"
    notes: Optional[str] = None


@router.post("/roadmap/add")
async def add_roadmap_item(item: RoadmapItemCreate):
    data = load_json(SYSTEM_DIR / "roadmap.json", default={})
    if item.versie not in data:
        data[item.versie] = {"items": []}
    v = data[item.versie]
    items = v.get("items", [])
    new = {
        "id": str(uuid.uuid4())[:8],
        "titel": item.titel,
        "status": "todo",
        "priority": item.priority,
        "notes": item.notes,
        "added": datetime.now(timezone.utc).isoformat(),
    }
    items.append(new)
    v["items"] = items
    data[item.versie] = v
    save_json(SYSTEM_DIR / "roadmap.json", data)
    return {"success": True, "item": new}


# ============================================================
# NOTIFICATIONS
# ============================================================

@router.get("/notifications/{user_id}")
async def get_notifications(user_id: str, unread_only: bool = False):
    data = load_json(NOTIF_FILE, default={"notifications": []})
    notifs = [n for n in data.get("notifications", []) if n.get("user_id") == user_id or n.get("user_id") == "all"]
    if unread_only:
        notifs = [n for n in notifs if not n.get("read")]
    notifs.sort(key=lambda n: n.get("timestamp", ""), reverse=True)
    unread = sum(1 for n in data.get("notifications", []) if (n.get("user_id") == user_id or n.get("user_id") == "all") and not n.get("read"))
    return {"success": True, "notifications": notifs, "unread_count": unread}


@router.post("/notifications/{user_id}/read/{notif_id}")
async def mark_notification_read(user_id: str, notif_id: str):
    data = load_json(NOTIF_FILE, default={"notifications": []})
    for n in data.get("notifications", []):
        if n.get("id") == notif_id:
            n["read"] = True
            break
    save_json(NOTIF_FILE, data)
    return {"success": True}


@router.post("/notifications/{user_id}/read-all")
async def mark_all_read(user_id: str):
    data = load_json(NOTIF_FILE, default={"notifications": []})
    for n in data.get("notifications", []):
        if n.get("user_id") == user_id or n.get("user_id") == "all":
            n["read"] = True
    save_json(NOTIF_FILE, data)
    return {"success": True}


class NotificationCreate(BaseModel):
    user_id: str = "all"
    title: str = ""
    message: str = ""
    type: str = "info"


@router.post("/notifications/create")
async def create_notification(notif: NotificationCreate):
    data = load_json(NOTIF_FILE, default={"notifications": []})
    new = {
        "id": str(uuid.uuid4()),
        "user_id": notif.user_id,
        "title": notif.title,
        "message": notif.message,
        "type": notif.type,
        "read": False,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    data["notifications"].append(new)
    save_json(NOTIF_FILE, data)
    return {"success": True, "notification": new}


# ============================================================
# EXTENDED PROFILE
# ============================================================

class ProfileExtended(BaseModel):
    volledige_naam: Optional[str] = None
    roepnaam: Optional[str] = None
    achternaam: Optional[str] = None
    email: Optional[str] = None
    telefoon: Optional[str] = None
    noodcontact_naam: Optional[str] = None
    noodcontact_telefoon: Optional[str] = None
    geboortedatum: Optional[str] = None
    geboorteplaats: Optional[str] = None
    geslacht: Optional[str] = None
    nationaliteit: Optional[str] = None
    burgerlijke_staat: Optional[str] = None
    straat: Optional[str] = None
    huisnummer: Optional[str] = None
    postcode: Optional[str] = None
    plaats: Optional[str] = None
    land: Optional[str] = None
    bio: Optional[str] = None
    iban: Optional[str] = None
    bank_provider: Optional[str] = None
    # v14_contacten_klapper_001 — zakelijk (voor leveranciersmail/factuur; e-mail pas gebruiken als ingevuld)
    zakelijke_email: Optional[str] = None
    bedrijfsnaam: Optional[str] = None
    kvk: Optional[str] = None
    btw_nummer: Optional[str] = None


@router.get("/profile/extended/{user_id}")
async def get_extended_profile(user_id: str):
    profile_file = USERS_DIR / user_id / "profile.json"
    data = load_json(profile_file, default={"user_id": user_id})
    return {"success": True, "profile": data}


@router.put("/profile/extended/{user_id}")
async def update_extended_profile(user_id: str, updates: ProfileExtended):
    profile_file = USERS_DIR / user_id / "profile.json"
    profile_file.parent.mkdir(parents=True, exist_ok=True)
    data = load_json(profile_file, default={"user_id": user_id})
    for k, v in updates.model_dump(exclude_none=True).items():
        data[k] = v
    data["last_updated"] = datetime.now(timezone.utc).isoformat()
    save_json(profile_file, data)
    return {"success": True, "profile": data}


# ============================================================
# UI VOORKEUREN (v5_ui_prefs_001) — per-user beeld/geluid/connecties
# Schema:
#   glow_base_color: hex (#f59e0b default amber)
#   glow_intensity: 0..1 (toekomstig)
#   sound_enabled: bool (toekomstig, default True)
#   auto_bark_enabled: bool (toekomstig, default False)
# Live-apply: frontend zet CSS var --glow-base op document root.
# ============================================================

class UIPreferences(BaseModel):
    glow_base_color: Optional[str] = None
    glow_intensity: Optional[float] = None
    sound_enabled: Optional[bool] = None
    auto_bark_enabled: Optional[bool] = None
    tts_enabled: Optional[bool] = None
    # v12_chat_visibility_001 — per-user zichtbaarheid van chat-modules
    community_chat_enabled: Optional[bool] = None  # default False; alleen gradatie ≤ 5
    private_chats_enabled: Optional[bool] = None   # default True; alle gradaties
    # v13_call_devices_001 — mic/cam device-keuze voor privé-bellen
    audio_input_device_id: Optional[str] = None    # browser mediaDevice deviceId of "default"
    video_input_device_id: Optional[str] = None
    audio_input_label: Optional[str] = None        # menselijk leesbare naam voor UI
    video_input_label: Optional[str] = None
    use_default_devices: Optional[bool] = None     # true = systeem-default, negeer bovenstaande
    # v13o_announce_prefs_001 — welke auto-boekingen wil user via boekhouder-bot horen?
    announce_shop_sale: Optional[bool] = None      # verkoop → DM
    announce_sepa_import: Optional[bool] = None    # camt053/mt940 → DM
    announce_migration: Optional[bool] = None      # migration → DM
    announce_spark_fee: Optional[bool] = None      # spark_fee_inlossen → DM


DEFAULT_UI_PREFS = {
    "glow_base_color": "#f59e0b",
    "glow_intensity": 0.5,
    "sound_enabled": True,
    "auto_bark_enabled": False,
    "tts_enabled": True,
    # v12_chat_visibility_001
    "community_chat_enabled": False,
    "private_chats_enabled": True,
    # v13_call_devices_001
    "audio_input_device_id": "default",
    "video_input_device_id": "default",
    "audio_input_label": "Systeem-standaard microfoon",
    "video_input_label": "Systeem-standaard camera",
    "use_default_devices": True,
    # v13o_announce_prefs_001 — defaults: alles aan
    "announce_shop_sale": True,
    "announce_sepa_import": True,
    "announce_migration": True,
    "announce_spark_fee": True,
}


@router.get("/profile/ui-preferences/{user_id}")
async def get_ui_preferences(user_id: str):
    prefs_file = USERS_DIR / user_id / "ui_preferences.json"
    data = load_json(prefs_file, default={"user_id": user_id, **DEFAULT_UI_PREFS})
    # Vul ontbrekende defaults aan (forward-compat)
    merged = {**DEFAULT_UI_PREFS, **data, "user_id": user_id}
    return {"success": True, "preferences": merged}


@router.put("/profile/ui-preferences/{user_id}")
async def update_ui_preferences(user_id: str, updates: UIPreferences):
    prefs_file = USERS_DIR / user_id / "ui_preferences.json"
    prefs_file.parent.mkdir(parents=True, exist_ok=True)
    data = load_json(prefs_file, default={"user_id": user_id, **DEFAULT_UI_PREFS})
    payload = updates.model_dump(exclude_none=True)
    # Valideer hex-kleur indien meegegeven
    color = payload.get("glow_base_color")
    if color is not None:
        c = color.strip()
        if not (c.startswith("#") and len(c) in (4, 7)):
            return {"success": False, "error": "glow_base_color moet hex zijn (bv #f59e0b)"}
        payload["glow_base_color"] = c
    for k, v in payload.items():
        data[k] = v
    data["user_id"] = user_id
    data["last_updated"] = datetime.now(timezone.utc).isoformat()
    save_json(prefs_file, data)
    merged = {**DEFAULT_UI_PREFS, **data}
    return {"success": True, "preferences": merged}


# ============================================================
# CHAT-HISTORIE (eigen log van user, schoon)
# ============================================================

CHAT_LOG_DIR = DATA_DIR / "chat" / "logs"


def _strip_meta(text: str) -> str:
    """Verwijder debug payload / system markers uit chat-tekst."""
    if not text:
        return ""
    t = text.strip()
    # filter pure system messages
    if t.startswith("[system:") and t.endswith("]"):
        return ""
    return t


@router.get("/profile/chat-history/{user_id}")
async def get_chat_history(user_id: str, limit: int = 500, channel: Optional[str] = "spark"):
    """Geef de eigen Spark-chathistorie van een user, schoon en gegroepeerd op jaar→maand→dag.
    Default channel='spark' om community-berichten niet te tonen in eigen chat-historie."""
    log_file = CHAT_LOG_DIR / f"{user_id}.json"
    data = load_json(log_file, default={"conversations": []})
    convs = data.get("conversations", []) or []
    if channel:
        convs = [c for c in convs if c.get("channel", "spark") == channel]

    grouped: Dict[str, Dict[str, Dict[str, list]]] = {}
    total = 0
    for c in convs[-limit:]:
        ts = c.get("timestamp", "")
        if not ts or len(ts) < 10:
            continue
        year, month, day = ts[0:4], ts[5:7], ts[8:10]
        user_msg = _strip_meta(c.get("user_message", ""))
        spark_msg = _strip_meta(c.get("spark_response", ""))
        if not user_msg and not spark_msg:
            continue
        entry = {
            "id": c.get("id"),
            "time": ts[11:16] if len(ts) >= 16 else "",
            "ts": ts,
            "user_message": user_msg,
            "spark_response": spark_msg,
        }
        grouped.setdefault(year, {}).setdefault(month, {}).setdefault(day, []).append(entry)
        total += 1

    # sorteer aflopend (nieuwste eerst)
    tree = []
    for y in sorted(grouped.keys(), reverse=True):
        months = []
        for m in sorted(grouped[y].keys(), reverse=True):
            days = []
            for d in sorted(grouped[y][m].keys(), reverse=True):
                items = sorted(grouped[y][m][d], key=lambda x: x["ts"], reverse=True)
                days.append({"day": d, "count": len(items), "items": items})
            months.append({"month": m, "count": sum(d["count"] for d in days), "days": days})
        tree.append({"year": y, "count": sum(mo["count"] for mo in months), "months": months})

    return {"success": True, "user_id": user_id, "total": total, "years": tree}


# v4_storage_cache_001 — Cache diagnostics endpoint
@router.get("/admin/storage-cache")
async def storage_cache_stats():
    """Toont welke files in-memory gecached zijn (alleen >50KB worden gecached)."""
    from modules.core.storage import get_cache_stats
    return get_cache_stats()


@router.post("/admin/storage-cache/clear")
async def storage_cache_clear():
    """Forceer cache leeg (debug/recovery)."""
    from modules.core.storage import clear_cache
    clear_cache()
    return {"success": True, "message": "Cache leeggemaakt"}


# v4_dank_004 — Credits bonus sync (admin)
@router.get("/admin/credits-bonus")
async def credits_bonus_status():
    """Status van credits-bonus per user."""
    from modules.chat.dank_service import sync_credits_bonus
    from modules.core.storage import load_json as _lj
    from pathlib import Path as _P
    users = _lj(_P("/app/backend/data/system/users.json"), default={"users": []}).get("users", [])
    bonused = [
        {
            "id": u.get("id"), "naam": u.get("naam"),
            "volledige_naam": u.get("volledige_naam"),
            "gradatie": u.get("gradatie"),
            "trust_score": u.get("trust_score"),
            "multiplier": u.get("credits_multiplier"),
            "applied_at": u.get("credits_bonus_applied_at"),
        }
        for u in users if u.get("credits_bonus")
    ]
    return {"success": True, "bonused_users": bonused, "count": len(bonused)}


@router.post("/admin/credits-bonus/sync")
async def credits_bonus_sync():
    """Re-run de match: nieuwe namen → users met gradatie ≤ 4 krijgen bonus."""
    from modules.chat.dank_service import sync_credits_bonus
    result = sync_credits_bonus()
    return {"success": True, **result}


# v4_roadmap_archeo_001 — Detecteer orphan vX_xxx refs in code (niet in roadmap)
@router.get("/admin/roadmap-archeology")
async def roadmap_archeology():
    """Scan code voor vX_xxx refs en vergelijk met roadmap items."""
    import re as _re, subprocess as _sp
    from pathlib import Path as _P
    result = _sp.run(
        ["grep", "-rho", "-E", "v[0-9]+_[a-z_0-9]{3,40}", "/app/backend/modules"],
        capture_output=True, text=True, timeout=30,
    )
    code_refs = set()
    for line in result.stdout.split("\n"):
        m = _re.match(r"v\d+_[a-z_0-9]+", line.strip())
        if m and 4 < len(m.group(0)) < 35:
            code_refs.add(m.group(0))
    roadmap = load_json(_P("/app/backend/data/system/roadmap.json"), default={})
    rm_ids = set()
    for v_data in roadmap.values():
        if isinstance(v_data, dict):
            for it in v_data.get("items", []) or []:
                if isinstance(it, dict) and it.get("id"):
                    rm_ids.add(it["id"])
    orphans = sorted(code_refs - rm_ids)
    unused = sorted(rm_ids - code_refs)
    return {
        "success": True,
        "code_refs_count": len(code_refs),
        "roadmap_ids_count": len(rm_ids),
        "orphans_in_code_not_in_roadmap": orphans,
        "in_roadmap_not_in_code": unused[:30],
        "sync_percentage": round(100 * len(code_refs & rm_ids) / max(1, len(code_refs)), 1),
    }
@router.get("/admin/architecture")
async def admin_architecture():
    """Scan /app/backend/modules en geef live overzicht van lagen + modules terug."""
    from pathlib import Path as _P
    modules_dir = _P("/app/backend/modules")
    modules = []
    for d in sorted(modules_dir.iterdir()):
        if not d.is_dir() or d.name.startswith("_"):
            continue
        py_files = list(d.rglob("*.py"))
        routes_file = d / "routes.py"
        init_file = d / "__init__.py"
        # Count route definitions (rough)
        route_count = 0
        for f in (routes_file, init_file):
            if f.exists():
                try:
                    txt = f.read_text(encoding="utf-8", errors="ignore")
                    route_count += txt.count("@router.")
                except Exception:
                    pass
        modules.append({
            "name": d.name,
            "files": len([f for f in py_files if "__pycache__" not in str(f)]),
            "routes": route_count,
            "size_kb": round(sum(f.stat().st_size for f in py_files if f.exists()) / 1024, 1),
        })

    # Tel frontend componenten als snelle inventaris
    fe_dir = _P("/app/frontend/src/components")
    fe_groups = []
    if fe_dir.exists():
        for d in sorted(fe_dir.iterdir()):
            if d.is_dir():
                js_files = [f for f in d.rglob("*.js") if f.is_file()]
                fe_groups.append({"group": d.name, "components": len(js_files)})

    return {
        "success": True,
        "layers": [
            {"name": "Presentatie Laag", "tech": "React 19 + TailwindCSS",
             "description": "Frontend UI Components",
             "metrics": {"groups": len(fe_groups), "total_components": sum(g["components"] for g in fe_groups)}},
            {"name": "API Laag", "tech": "FastAPI + Pydantic",
             "description": "REST endpoints onder /api/*",
             "metrics": {"modules": len(modules), "total_routes": sum(m["routes"] for m in modules)}},
            {"name": "Service Laag", "tech": "Python services",
             "description": "Business logic (auth, snap, NLP, chat-intents)",
             "metrics": {"total_files": sum(m["files"] for m in modules)}},
            {"name": "Data Laag", "tech": "Lokaal JSON (geen MongoDB)",
             "description": "JSON files in /app/backend/data/",
             "metrics": {"total_kb": round(sum(m["size_kb"] for m in modules), 1)}},
        ],
        "modules": modules,
        "frontend_groups": fe_groups,
    }


# v4_personal_docs_001 — Persoonlijke documenten (testament, survivalgids, etc.)
@router.get("/personal-docs/{user_id}")
async def list_personal_docs(user_id: str):
    """Geef lijst van persoonlijke documenten van user (testament/survivalgids/etc)."""
    from modules.chat.personal_docs_service import list_user_docs, DOC_TYPES
    docs = list_user_docs(user_id)
    return {
        "success": True,
        "documents": docs,
        "available_types": [
            {"type": k, "label": v["label"], "emoji": v["emoji"]}
            for k, v in DOC_TYPES.items()
        ],
    }


@router.get("/personal-docs/{user_id}/{doc_type}")
async def get_personal_doc(user_id: str, doc_type: str):
    """Geef de volledige inhoud van een persoonlijk document."""
    from modules.chat.personal_docs_service import _doc_file, DOC_TYPES
    if doc_type not in DOC_TYPES:
        return {"success": False, "error": f"Onbekend type: {doc_type}"}
    fp = _doc_file(user_id, doc_type)
    if not fp.exists():
        return {"success": False, "error": "Niet gevonden"}
    return {"success": True, "document": load_json(fp, default={})}
