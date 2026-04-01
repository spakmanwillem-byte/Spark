"""
Notes & Tasks Routes - CRUD
Notes schema v1: {notes: [{id, titel, inhoud, categorie, tags[], datum, created_by, updated_at}]}
Tasks schema v1: {tasks: [{id, task, priority, status, created_at, completed_at}]}
"""
from fastapi import APIRouter
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


class NoteUpdate(BaseModel):
    titel: Optional[str] = None
    inhoud: Optional[str] = None
    categorie: Optional[str] = None
    tags: Optional[List[str]] = None
    priority: Optional[str] = None


class TaskCreate(BaseModel):
    task: str
    priority: str = "medium"


class TaskUpdate(BaseModel):
    task: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None


# ============== NOTES ==============

@router.get("/all")
async def get_notes():
    data = load_json(NOTES_FILE, default={"notes": []})
    return data


@router.post("/create")
async def create_note(note: NoteCreate):
    data = load_json(NOTES_FILE, default={"notes": []})
    new_note = {
        "id": str(uuid.uuid4()),
        "titel": note.titel,
        "inhoud": note.inhoud,
        "categorie": note.categorie,
        "tags": note.tags,
        "priority": note.priority,
        "datum": datetime.now(timezone.utc).isoformat(),
        "created_by": "Willem",
        "updated_at": None,
    }
    data["notes"].insert(0, new_note)
    save_json(NOTES_FILE, data)
    return {"success": True, "note": new_note}


@router.put("/update/{note_id}")
async def update_note(note_id: str, updates: NoteUpdate):
    data = load_json(NOTES_FILE, default={"notes": []})
    for n in data["notes"]:
        if n["id"] == note_id:
            for k, v in updates.model_dump(exclude_none=True).items():
                n[k] = v
            n["updated_at"] = datetime.now(timezone.utc).isoformat()
            save_json(NOTES_FILE, data)
            return {"success": True, "note": n}
    return {"success": False, "message": "Notitie niet gevonden"}


@router.delete("/delete/{note_id}")
async def delete_note(note_id: str):
    data = load_json(NOTES_FILE, default={"notes": []})
    before = len(data["notes"])
    data["notes"] = [n for n in data["notes"] if n["id"] != note_id]
    if len(data["notes"]) < before:
        save_json(NOTES_FILE, data)
        return {"success": True}
    return {"success": False, "message": "Notitie niet gevonden"}


# ============== TASKS ==============

@router.get("/tasks")
async def get_tasks():
    data = load_json(TASKS_FILE, default={"tasks": []})
    return data


@router.post("/tasks/create")
async def create_task(task: TaskCreate):
    data = load_json(TASKS_FILE, default={"tasks": []})
    new_task = {
        "id": str(uuid.uuid4()),
        "task": task.task,
        "priority": task.priority,
        "status": "todo",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None,
    }
    data["tasks"].append(new_task)
    save_json(TASKS_FILE, data)
    return {"success": True, "task": new_task}


@router.put("/tasks/update/{task_id}")
async def update_task(task_id: str, updates: TaskUpdate):
    data = load_json(TASKS_FILE, default={"tasks": []})
    for t in data["tasks"]:
        if t["id"] == task_id:
            for k, v in updates.model_dump(exclude_none=True).items():
                t[k] = v
            if updates.status == "done" and not t.get("completed_at"):
                t["completed_at"] = datetime.now(timezone.utc).isoformat()
            save_json(TASKS_FILE, data)
            return {"success": True, "task": t}
    return {"success": False, "message": "Taak niet gevonden"}


@router.delete("/tasks/delete/{task_id}")
async def delete_task(task_id: str):
    data = load_json(TASKS_FILE, default={"tasks": []})
    before = len(data["tasks"])
    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
    if len(data["tasks"]) < before:
        save_json(TASKS_FILE, data)
        return {"success": True}
    return {"success": False, "message": "Taak niet gevonden"}
