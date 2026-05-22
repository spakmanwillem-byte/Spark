"""
Bugs Module (v4_bugs_001) — Bug-meldingen door iedereen, beheerd door admins (gradatie ≤ 2).

Iedereen mag een bug aanmaken (anoniem of ingelogd).
Lijst + status wijzigen is alleen zichtbaar voor gradatie ≤ 2.

Bij aanmaken: stuurt automatisch een privé-bericht naar de melder van bot "Spark AI" (user-000)
zodat de melder een bevestiging ziet in zijn Privé-chat.

Storage: /data/bugs/bugs.json
"""
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from modules.core.storage import load_json, save_json

router = APIRouter(prefix="/bugs", tags=["bugs"])

DATA_ROOT = Path(__file__).parent.parent.parent / "data"
BUGS_FILE = DATA_ROOT / "bugs" / "bugs.json"
USERS_FILE = DATA_ROOT / "system" / "users.json"
PRIVE_DIR = DATA_ROOT / "chat" / "prive"
BUGS_FILE.parent.mkdir(parents=True, exist_ok=True)
PRIVE_DIR.mkdir(parents=True, exist_ok=True)

ADMIN_GRADATIE_MAX = 2  # tijdelijke MVP: gradatie 1+2 zien bugs (later splitsen fam vs admin)
ALLOWED_STATUS = {"nieuw", "in_behandeling", "opgelost", "afgewezen"}
SPARK_BOT_ID = "user-000"  # Spark AI assistant


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_user(user_id: str) -> Optional[dict]:
    if not user_id:
        return None
    data = load_json(USERS_FILE, default={"users": []})
    for u in data.get("users", []):
        if u.get("id") == user_id:
            return u
    return None


def _is_admin_viewer(user_id: Optional[str]) -> bool:
    """Gradatie 1-2 mag bugs zien."""
    u = _get_user(user_id) if user_id else None
    if not u:
        return False
    grad = u.get("gradatie", 7) or 7
    return grad <= ADMIN_GRADATIE_MAX


def _send_confirmation_pm(bug: dict) -> None:
    """Stuur een privé-bericht aan de melder vanuit Spark AI (user-000)."""
    melder_id = bug.get("created_by_id")
    if not melder_id or melder_id == SPARK_BOT_ID:
        return  # anoniem of door Spark zelf, geen PM
    pair = sorted([SPARK_BOT_ID, melder_id])
    fp = PRIVE_DIR / f"{pair[0]}__{pair[1]}.json"
    data = load_json(fp, default={"messages": []})
    when = bug.get("when") or "onbekend tijdstip"
    page = bug.get("page")
    desc = (bug.get("description") or "").strip()
    snippet = desc[:140] + ("…" if len(desc) > 140 else "")
    ref = f"#{bug['id'][:8]}"
    lines = [
        f"Bedankt — je bugmelding {ref} is binnen.",
        "",
        f"📝 \"{snippet}\"",
        f"🕒 Wanneer: {when}",
    ]
    if page:
        lines.append(f"📍 Waar: {page}")
    lines.append("")
    lines.append("We bekijken het zo snel mogelijk en houden je hier op de hoogte.")
    msg = {
        "id": f"pm-{uuid.uuid4().hex[:8]}",
        "from_user_id": SPARK_BOT_ID,
        "from_naam": "Spark AI",
        "to_user_id": melder_id,
        "text": "\n".join(lines),
        "ts": _now_iso(),
        "unread_by": [melder_id],
        "system": True,
        "kind": "bug_confirmation",
        "bug_id": bug["id"],
        "bug_ref": ref,
    }
    data["messages"] = data.get("messages", []) + [msg]
    save_json(fp, data)


def _send_status_pm(bug: dict, new_status: str, note: Optional[str]) -> None:
    """Stuur een privé-bericht aan de melder bij status-wijziging."""
    melder_id = bug.get("created_by_id")
    if not melder_id or melder_id == SPARK_BOT_ID:
        return
    pair = sorted([SPARK_BOT_ID, melder_id])
    fp = PRIVE_DIR / f"{pair[0]}__{pair[1]}.json"
    data = load_json(fp, default={"messages": []})
    ref = f"#{bug['id'][:8]}"
    status_labels = {
        "in_behandeling": "wordt nu onderzocht 🔎",
        "opgelost": "is opgelost ✅",
        "afgewezen": "is afgewezen ⛔",
        "nieuw": "is heropend 🔄",
    }
    label = status_labels.get(new_status, new_status)
    lines = [f"Update over je bugmelding {ref}: {label}."]
    if note:
        lines.append("")
        lines.append(f"💬 {note}")
    msg = {
        "id": f"pm-{uuid.uuid4().hex[:8]}",
        "from_user_id": SPARK_BOT_ID,
        "from_naam": "Spark AI",
        "to_user_id": melder_id,
        "text": "\n".join(lines),
        "ts": _now_iso(),
        "unread_by": [melder_id],
        "system": True,
        "kind": "bug_status_update",
        "bug_id": bug["id"],
        "bug_ref": ref,
    }
    data["messages"] = data.get("messages", []) + [msg]
    save_json(fp, data)


# ============== MODELS ==============
class CreateBug(BaseModel):
    description: str
    when: Optional[str] = None  # vrije tekst: "vanmiddag 14u", "16-05 11:30", etc.
    page: Optional[str] = None  # waar deed het zich voor (optioneel)
    created_by_id: Optional[str] = None  # leeg = anoniem
    created_by_naam: Optional[str] = None  # display name


class UpdateStatus(BaseModel):
    status: str
    note: Optional[str] = None
    viewer_id: str  # wie wijzigt (moet admin zijn)


# ============== ROUTES ==============
@router.post("/create")
async def create_bug(req: CreateBug):
    """Iedereen mag een bug aanmaken — anoniem of ingelogd."""
    if not req.description.strip():
        raise HTTPException(status_code=400, detail="Omschrijving is verplicht")

    data = load_json(BUGS_FILE, default={"bugs": []})
    bug = {
        "id": str(uuid.uuid4()),
        "description": req.description.strip(),
        "when": (req.when or "").strip() or None,
        "page": (req.page or "").strip() or None,
        "status": "nieuw",
        "created_at": _now_iso(),
        "created_by_id": req.created_by_id or None,
        "created_by_naam": (req.created_by_naam or "").strip() or "Anoniem",
        "history": [{"status": "nieuw", "at": _now_iso(), "by": req.created_by_id, "note": None}],
    }
    data["bugs"] = [bug] + data.get("bugs", [])
    save_json(BUGS_FILE, data)

    _send_confirmation_pm(bug)

    return {"success": True, "bug": bug}


@router.get("/list")
async def list_bugs(viewer_id: str, status: Optional[str] = None):
    """Alleen gradatie ≤ 2 mag de lijst zien."""
    if not _is_admin_viewer(viewer_id):
        raise HTTPException(status_code=403, detail="Niet toegestaan — alleen admins (gradatie ≤ 2)")
    data = load_json(BUGS_FILE, default={"bugs": []})
    bugs: List[dict] = data.get("bugs", [])
    if status:
        bugs = [b for b in bugs if b.get("status") == status]
    # nieuwste eerst
    bugs.sort(key=lambda b: b.get("created_at", ""), reverse=True)
    counts = {s: 0 for s in ALLOWED_STATUS}
    for b in data.get("bugs", []):
        s = b.get("status") or "nieuw"
        counts[s] = counts.get(s, 0) + 1
    return {"bugs": bugs, "total": len(bugs), "counts": counts}


# v4_roadmap_user_ideas_001 — eigen tickets ophalen (zonder admin-rechten)
@router.get("/mine")
async def my_bugs(user_id: str):
    """Toon alleen bug-tickets aangemaakt door de huidige user."""
    data = load_json(BUGS_FILE, default={"bugs": []})
    mine = [b for b in data.get("bugs", []) if b.get("created_by_id") == user_id]
    mine.sort(key=lambda b: b.get("created_at", ""), reverse=True)
    return {"bugs": mine, "total": len(mine)}


@router.patch("/{bug_id}/status")
async def update_status(bug_id: str, req: UpdateStatus):
    if not _is_admin_viewer(req.viewer_id):
        raise HTTPException(status_code=403, detail="Niet toegestaan — alleen admins (gradatie ≤ 2)")
    if req.status not in ALLOWED_STATUS:
        raise HTTPException(status_code=400, detail=f"Ongeldige status. Toegestaan: {sorted(ALLOWED_STATUS)}")
    data = load_json(BUGS_FILE, default={"bugs": []})
    for b in data.get("bugs", []):
        if b.get("id") == bug_id:
            b["status"] = req.status
            b.setdefault("history", []).append({
                "status": req.status,
                "at": _now_iso(),
                "by": req.viewer_id,
                "note": req.note,
            })
            save_json(BUGS_FILE, data)
            _send_status_pm(b, req.status, req.note)
            return {"success": True, "bug": b}
    raise HTTPException(status_code=404, detail="Bug niet gevonden")


@router.delete("/{bug_id}")
async def delete_bug(bug_id: str, viewer_id: str):
    if not _is_admin_viewer(viewer_id):
        raise HTTPException(status_code=403, detail="Niet toegestaan — alleen admins (gradatie ≤ 2)")
    data = load_json(BUGS_FILE, default={"bugs": []})
    before = len(data.get("bugs", []))
    data["bugs"] = [b for b in data.get("bugs", []) if b.get("id") != bug_id]
    if len(data["bugs"]) == before:
        raise HTTPException(status_code=404, detail="Bug niet gevonden")
    save_json(BUGS_FILE, data)
    return {"success": True}
