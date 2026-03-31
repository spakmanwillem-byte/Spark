"""
Task Routes - API endpoints voor task module (Core)
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from services.task_service import (
    get_all_tasks,
    get_task_by_id,
    create_task,
    update_task_status,
    update_task,
    delete_task,
    get_tasks_by_status
)

router = APIRouter(prefix="/tasks", tags=["tasks"])


class TaskCreate(BaseModel):
    task: str
    priority: Optional[str] = "medium"
    note_id: Optional[str] = None  # Link naar notitie


class TaskUpdate(BaseModel):
    task: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None


@router.get("")
async def list_tasks(status: Optional[str] = None):
    """Haal alle tasks op (optioneel gefilterd op status)"""
    if status:
        tasks = get_tasks_by_status(status)
    else:
        tasks = get_all_tasks()
    
    return {
        "success": True,
        "count": len(tasks),
        "tasks": tasks
    }


@router.get("/{task_id}")
async def get_task(task_id: str):
    """Haal specifieke task op"""
    task = get_task_by_id(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task niet gevonden")
    
    return {
        "success": True,
        "task": task
    }


@router.post("")
async def add_task(data: TaskCreate):
    """Maak nieuwe task aan"""
    if not data.task.strip():
        raise HTTPException(status_code=400, detail="Task mag niet leeg zijn")
    
    task = create_task(data.task, data.priority, data.note_id)
    
    return {
        "success": True,
        "message": "Task aangemaakt",
        "task": task
    }


@router.put("/{task_id}")
async def modify_task(task_id: str, data: TaskUpdate):
    """Update task"""
    updates = data.dict(exclude_unset=True)
    
    if not updates:
        raise HTTPException(status_code=400, detail="Geen updates opgegeven")
    
    task = update_task(task_id, updates)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task niet gevonden")
    
    return {
        "success": True,
        "message": "Task bijgewerkt",
        "task": task
    }


@router.patch("/{task_id}/status")
async def toggle_task_status(task_id: str, status: str):
    """Toggle task status (todo/done)"""
    if status not in ["todo", "done"]:
        raise HTTPException(status_code=400, detail="Status moet 'todo' of 'done' zijn")
    
    task = update_task_status(task_id, status)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task niet gevonden")
    
    return {
        "success": True,
        "message": f"Task status: {status}",
        "task": task
    }


@router.delete("/{task_id}")
async def remove_task(task_id: str):
    """Verwijder task"""
    success = delete_task(task_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Task niet gevonden")
    
    return {
        "success": True,
        "message": "Task verwijderd"
    }
