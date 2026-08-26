"""
Notes & Tasks Routes - CRUD
v4_notes_002 — user-bound: notitie/taak hoort bij user_id (default user-001 voor legacy).
Notes schema: {notes: [{id, user_id, titel, inhoud, categorie, tags[], datum, created_by, updated_at}]}
Tasks schema: {tasks: [{id, user_id, task, priority, status, created_at, completed_at}]}
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from pathlib import Path
from datetime import datetime, timezone
import uuid
from modules.core.storage import load_json, save_json

router = APIRouter(prefix="/notes", tags=["notes"])
DATA_DIR = Path(__file__).parent.parent.parent / "data" / "notes"
NOTES_FILE = DATA_DIR / "notes.json"
TASKS_FILE = DATA_DIR / "tasks.json"


class NoteCreate(BaseModel):
    titel: str
    inhoud: str = ""
    categorie: str = "Observatie"
    tags: List[str] = []
    priority: str = "medium"
    user_id: str  # verplicht (geen anonieme notes meer)
    # v13d_notes_scope_001 (sessie 56b) — Willem: scope-label prive/zakelijk/admin
    # zodat layout weer klopt en admin-notities apart in Kladblok kunnen.
    scope: Optional[str] = "prive"  # 'prive' | 'zakelijk' | 'admin'


class NoteUpdate(BaseModel):
    titel: Optional[str] = None
    inhoud: Optional[str] = None
    categorie: Optional[str] = None
    tags: Optional[List[str]] = None
    priority: Optional[str] = None
    scope: Optional[str] = None


class TaskCreate(BaseModel):
    task: str
    priority: str = "medium"
    user_id: str  # verplicht
    scope: Optional[str] = "prive"


class TaskUpdate(BaseModel):
    task: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None


def _filter_by_user(items: list, user_id: str) -> list:
    """Filter items op user_id. Items zonder user_id worden behandeld als legacy van user-001."""
    return [it for it in items if (it.get("user_id") or "user-001") == user_id]


def _user_naam(user_id: str) -> str:
    """Lookup user naam voor created_by veld."""
    try:
        users = load_json(Path(__file__).parent.parent.parent / "data" / "system" / "users.json", default={"users": []})
        for u in users.get("users", []):
            if u.get("id") == user_id:
                return u.get("naam") or user_id
    except Exception:
        pass
    return user_id


# ============== NOTES ==============

@router.get("/all")
async def get_notes(user_id: str, viewer_id: Optional[str] = None):
    """Notes van DEZE user. user_id is verplicht.

    v13d_multi_module_privacy_001 (sessie 55) — als viewer_id opgegeven én
    verschilt van user_id én viewer is geen admin → 403. Zonder viewer_id
    (backwards-compat) valt terug op user_id."""
    if not user_id:
        raise HTTPException(400, "user_id is verplicht")
    from modules.core.privacy import require_access
    require_access(viewer_id or user_id, user_id)
    data = load_json(NOTES_FILE, default={"notes": []})
    return {"notes": _filter_by_user(data.get("notes", []), user_id)}


@router.post("/create")
async def create_note(note: NoteCreate):
    if not note.user_id:
        raise HTTPException(400, "user_id is verplicht")
    data = load_json(NOTES_FILE, default={"notes": []})
    new_note = {
        "id": str(uuid.uuid4()),
        "user_id": note.user_id,
        "titel": note.titel,
        "inhoud": note.inhoud,
        "categorie": note.categorie,
        "tags": note.tags,
        "priority": note.priority,
        "scope": note.scope if note.scope in ("prive", "zakelijk", "admin") else "prive",
        "datum": datetime.now(timezone.utc).isoformat(),
        "created_by": _user_naam(note.user_id),
        "updated_at": None,
    }
    data["notes"].insert(0, new_note)
    save_json(NOTES_FILE, data)
    return {"success": True, "note": new_note}


@router.put("/update/{note_id}")
async def update_note(note_id: str, updates: NoteUpdate, user_id: str):
    """Update notitie. user_id moet overeenkomen met owner."""
    data = load_json(NOTES_FILE, default={"notes": []})
    for n in data["notes"]:
        if n["id"] == note_id:
            if (n.get("user_id") or "user-001") != user_id:
                raise HTTPException(403, "Niet jouw notitie")
            for k, v in updates.model_dump(exclude_none=True).items():
                n[k] = v
            n["updated_at"] = datetime.now(timezone.utc).isoformat()
            save_json(NOTES_FILE, data)
            return {"success": True, "note": n}
    return {"success": False, "message": "Notitie niet gevonden"}


@router.delete("/delete/{note_id}")
async def delete_note(note_id: str, user_id: str):
    data = load_json(NOTES_FILE, default={"notes": []})
    target = None
    for n in data["notes"]:
        if n["id"] == note_id:
            target = n
            break
    if not target:
        return {"success": False, "message": "Notitie niet gevonden"}
    if (target.get("user_id") or "user-001") != user_id:
        raise HTTPException(403, "Niet jouw notitie")
    data["notes"] = [n for n in data["notes"] if n["id"] != note_id]
    save_json(NOTES_FILE, data)
    return {"success": True}


# ============== TASKS ==============

@router.get("/tasks")
async def get_tasks(user_id: str, viewer_id: Optional[str] = None):
    if not user_id:
        raise HTTPException(400, "user_id is verplicht")
    from modules.core.privacy import require_access
    require_access(viewer_id or user_id, user_id)
    data = load_json(TASKS_FILE, default={"tasks": []})
    return {"tasks": _filter_by_user(data.get("tasks", []), user_id)}


@router.post("/tasks/create")
async def create_task(task: TaskCreate):
    if not task.user_id:
        raise HTTPException(400, "user_id is verplicht")
    data = load_json(TASKS_FILE, default={"tasks": []})
    new_task = {
        "id": str(uuid.uuid4()),
        "user_id": task.user_id,
        "task": task.task,
        "priority": task.priority,
        "scope": task.scope if task.scope in ("prive", "zakelijk", "admin") else "prive",
        "status": "todo",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None,
    }
    data["tasks"].append(new_task)
    save_json(TASKS_FILE, data)
    return {"success": True, "task": new_task}


@router.put("/tasks/update/{task_id}")
async def update_task(task_id: str, updates: TaskUpdate, user_id: str):
    data = load_json(TASKS_FILE, default={"tasks": []})
    for t in data["tasks"]:
        if t["id"] == task_id:
            if (t.get("user_id") or "user-001") != user_id:
                raise HTTPException(403, "Niet jouw taak")
            for k, v in updates.model_dump(exclude_none=True).items():
                t[k] = v
            if updates.status == "done" and not t.get("completed_at"):
                t["completed_at"] = datetime.now(timezone.utc).isoformat()
            save_json(TASKS_FILE, data)
            return {"success": True, "task": t}
    return {"success": False, "message": "Taak niet gevonden"}


@router.delete("/tasks/delete/{task_id}")
async def delete_task(task_id: str, user_id: str):
    data = load_json(TASKS_FILE, default={"tasks": []})
    target = None
    for t in data["tasks"]:
        if t["id"] == task_id:
            target = t
            break
    if not target:
        return {"success": False, "message": "Taak niet gevonden"}
    if (target.get("user_id") or "user-001") != user_id:
        raise HTTPException(403, "Niet jouw taak")
    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
    save_json(TASKS_FILE, data)
    return {"success": True}
