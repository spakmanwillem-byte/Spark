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
