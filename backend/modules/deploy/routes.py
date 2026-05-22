"""
Update Bark + Anker Systeem (v4_update_bark_001)

Workflow:
  1. Admin klikt "Anker huidige versie" → versie wordt vastgelegd in /app/backend/data/system/version_anchor.json
  2. Bij volgende login per user: check welke anker-barks nog niet "gezien" zijn
  3. Frontend toont sensory-overlay barks (1 per anker, queued)
  4. Privacy-bark is een ingebouwde anker (id=privacy_v1) die ELKE user 1x ziet

Schema /data/system/version_anchor.json:
{
  "barks": [
    {
      "id": "v0.6.4",                 # versie tag of "privacy_v1"
      "kind": "deploy" | "privacy" | "feature",
      "anchored_at": "ISO",
      "anchored_by": "user-001",
      "title": "Spark Core v0.6.4",
      "message": "...",                # body tekst
      "icon": "🚀",                    # of emoji
      "roadmap_ref": "phase-5",        # optionele link naar roadmap
      "audience": "all" | "admins"
    }
  ],
  "current": "v0.6.4"
}

Per-user "seen barks" wordt opgeslagen in /data/users/{user_id}/seen_barks.json:
{
  "seen": ["privacy_v1", "v0.6.4"],
  "last_check": "ISO"
}
"""
from pathlib import Path
from typing import Optional, List
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..core.storage import load_json, save_json

router = APIRouter(prefix="/deploy", tags=["deploy"])

DATA_ROOT = Path(__file__).parent.parent.parent / "data"
USERS_FILE = DATA_ROOT / "system" / "users.json"
ANCHOR_FILE = DATA_ROOT / "system" / "version_anchor.json"
USERS_DIR = DATA_ROOT / "users"

DEFAULT_PRIVACY_BARK = {
    "id": "privacy_v1",
    "kind": "privacy",
    "anchored_at": "2026-05-22T00:00:00+00:00",
    "anchored_by": "system",
    "title": "Privacy & Voorwaarden",
    "message": (
        "Welkom in Spark Core 2.0. Even kort:\n\n"
        "• Wij volgen je niet en gebruiken geen tracking-cookies.\n"
        "• Alle data blijft lokaal in JSON-bestanden op deze server (geen MongoDB, geen externe analytics).\n"
        "• Je gesprekken met Spark AI, je inventory en je avatar zijn alleen voor jou en de admins (gradatie 1-2).\n"
        "• Bij elke deploy zie je 1x een update-bark met wat er is veranderd.\n\n"
        "Door door te gaan ga je akkoord met deze voorwaarden."
    ),
    "icon": "🔒",
    "roadmap_ref": None,
    "audience": "all",
}


def _is_admin(user_id: str) -> bool:
    users = load_json(USERS_FILE, default={"users": []}).get("users", [])
    me = next((u for u in users if u.get("id") == user_id), None)
    return bool(me) and (me.get("gradatie", 99) <= 2)


def _load_anchors() -> dict:
    data = load_json(ANCHOR_FILE, default={})
    if not data or "barks" not in data:
        # Bootstrap: voeg privacy bark toe
        data = {"barks": [dict(DEFAULT_PRIVACY_BARK)], "current": None}
        save_json(ANCHOR_FILE, data)
    return data


def _seen_path(user_id: str) -> Path:
    d = USERS_DIR / user_id
    d.mkdir(parents=True, exist_ok=True)
    return d / "seen_barks.json"


def _seen(user_id: str) -> dict:
    return load_json(_seen_path(user_id), default={"seen": [], "last_check": None})


def _read_changelog_excerpt() -> str:
    """Probeer laatste sectie uit /app/memory/CHANGELOG.md te halen voor auto-generated message."""
    cl = Path(__file__).parent.parent.parent.parent / "memory" / "CHANGELOG.md"
    if not cl.exists():
        return ""
    try:
        text = cl.read_text(encoding="utf-8")
        # Pak eerste sectie tot de tweede ## (of einde)
        lines = text.split("\n")
        out: List[str] = []
        section_count = 0
        for ln in lines:
            if ln.startswith("## "):
                section_count += 1
                if section_count > 1:
                    break
            if section_count >= 1:
                out.append(ln)
        return "\n".join(out).strip()[:1200]
    except OSError:
        return ""


# ============== ROUTES ==============
class AnchorBody(BaseModel):
    version: str            # bv. "v0.6.4"
    title: Optional[str] = None
    message: Optional[str] = None
    icon: Optional[str] = None
    roadmap_ref: Optional[str] = None
    audience: str = "all"   # "all" | "admins"
    viewer_id: str


@router.get("/anchors")
async def list_anchors(viewer_id: Optional[str] = None):
    """Lijst alle ankers (admin ziet alles, anders alleen 'all')."""
    data = _load_anchors()
    barks = data.get("barks", [])
    is_admin = bool(viewer_id and _is_admin(viewer_id))
    if not is_admin:
        barks = [b for b in barks if (b.get("audience") or "all") == "all"]
    return {"barks": barks, "current": data.get("current"), "total": len(barks)}


@router.post("/anchor")
async def create_anchor(body: AnchorBody):
    """Admin verankert nieuwe versie → wordt automatisch bark voor iedereen op volgende login."""
    if not _is_admin(body.viewer_id):
        raise HTTPException(403, "Alleen admins (gradatie ≤ 2) mogen verankeren")
    if not body.version.strip():
        raise HTTPException(400, "Version is verplicht")

    data = _load_anchors()
    # Geen duplicaten
    if any(b.get("id") == body.version for b in data.get("barks", [])):
        raise HTTPException(400, f"Versie '{body.version}' is al verankerd")

    excerpt = _read_changelog_excerpt() if not body.message else ""
    bark = {
        "id": body.version.strip(),
        "kind": "deploy",
        "anchored_at": datetime.now(timezone.utc).isoformat(),
        "anchored_by": body.viewer_id,
        "title": body.title or f"Spark Core {body.version}",
        "message": body.message or excerpt or f"Nieuwe versie {body.version} is gedeployed.",
        "icon": body.icon or "🚀",
        "roadmap_ref": body.roadmap_ref,
        "audience": body.audience,
    }
    data["barks"] = data.get("barks", []) + [bark]
    data["current"] = body.version
    save_json(ANCHOR_FILE, data)
    return {"success": True, "bark": bark}


@router.delete("/anchor/{anchor_id}")
async def delete_anchor(anchor_id: str, viewer_id: str):
    if not _is_admin(viewer_id):
        raise HTTPException(403, "Alleen admins mogen verwijderen")
    if anchor_id == "privacy_v1":
        raise HTTPException(400, "Privacy bark is niet te verwijderen")
    data = _load_anchors()
    before = len(data.get("barks", []))
    data["barks"] = [b for b in data.get("barks", []) if b.get("id") != anchor_id]
    if data.get("current") == anchor_id:
        # Reset current naar laatste deploy bark
        deploys = [b for b in data["barks"] if b.get("kind") == "deploy"]
        data["current"] = deploys[-1]["id"] if deploys else None
    save_json(ANCHOR_FILE, data)
    return {"success": True, "removed": before - len(data["barks"])}


@router.get("/pending/{user_id}")
async def pending_barks(user_id: str):
    """Welke anker-barks heeft deze user nog niet gezien? (gebruikt door frontend bij login)."""
    data = _load_anchors()
    barks = data.get("barks", [])
    seen = _seen(user_id).get("seen", [])
    is_admin = _is_admin(user_id)
    pending: List[dict] = []
    for b in barks:
        if b.get("id") in seen:
            continue
        if (b.get("audience") or "all") == "admins" and not is_admin:
            continue
        pending.append(b)
    # Privacy-bark eerst, dan chronologisch
    pending.sort(key=lambda x: (x.get("kind") != "privacy", x.get("anchored_at") or ""))
    return {"pending": pending, "count": len(pending)}


class SeenBody(BaseModel):
    user_id: str
    bark_id: str


@router.post("/seen")
async def mark_seen(body: SeenBody):
    """User markeert een anker-bark als gezien."""
    fp = _seen_path(body.user_id)
    data = _seen(body.user_id)
    if body.bark_id not in data.get("seen", []):
        data["seen"] = data.get("seen", []) + [body.bark_id]
    data["last_check"] = datetime.now(timezone.utc).isoformat()
    save_json(fp, data)
    return {"success": True, "seen_count": len(data["seen"])}


@router.post("/reset-seen/{user_id}")
async def reset_seen(user_id: str, viewer_id: str):
    """Admin reset 'seen' lijst voor een user (debug / re-show)."""
    if not _is_admin(viewer_id):
        raise HTTPException(403, "Alleen admins")
    fp = _seen_path(user_id)
    save_json(fp, {"seen": [], "last_check": None})
    return {"success": True}
