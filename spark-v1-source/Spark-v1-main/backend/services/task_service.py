"""
Task Service - CRUD operations voor taken
Simpel, geen over-engineering
"""

import json
import os
from datetime import datetime, timezone
from uuid import uuid4
from typing import List, Dict, Optional

TASKS_FILE = "/app/backend/data/tasks.json"


def _load_tasks() -> Dict:
    """Laad tasks van JSON file"""
    if not os.path.exists(TASKS_FILE):
        return {"tasks": []}
    
    with open(TASKS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def _save_tasks(data: Dict) -> None:
    """Sla tasks op naar JSON file"""
    with open(TASKS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_all_tasks() -> List[Dict]:
    """Haal alle tasks op"""
    data = _load_tasks()
    return data.get("tasks", [])


def get_task_by_id(task_id: str) -> Optional[Dict]:
    """Haal specifieke task op"""
    data = _load_tasks()
    for task in data.get("tasks", []):
        if task["id"] == task_id:
            return task
    return None


def create_task(task_text: str, priority: str = "medium", note_id: Optional[str] = None) -> Dict:
    """
    Maak nieuwe task aan
    
    Args:
        task_text: Task beschrijving
        priority: low, medium, high
        note_id: Optioneel - link naar notitie (voor context)
    """
    data = _load_tasks()
    
    new_task = {
        "id": str(uuid4()),
        "task": task_text,
        "priority": priority,  # low, medium, high
        "status": "todo",  # todo, done
        "created_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None,
        "note_id": note_id  # Link naar notitie (optioneel)
    }
    
    data["tasks"].append(new_task)
    _save_tasks(data)
    
    return new_task


def update_task_status(task_id: str, status: str) -> Optional[Dict]:
    """Update task status (todo/done)"""
    data = _load_tasks()
    
    for task in data["tasks"]:
        if task["id"] == task_id:
            task["status"] = status
            
            if status == "done":
                task["completed_at"] = datetime.now(timezone.utc).isoformat()
            else:
                task["completed_at"] = None
            
            _save_tasks(data)
            return task
    
    return None


def update_task(task_id: str, updates: Dict) -> Optional[Dict]:
    """Update task fields (task, priority, status)"""
    data = _load_tasks()
    
    for task in data["tasks"]:
        if task["id"] == task_id:
            # Update toegestane velden
            if "task" in updates:
                task["task"] = updates["task"]
            if "priority" in updates:
                task["priority"] = updates["priority"]
            if "status" in updates:
                task["status"] = updates["status"]
                if updates["status"] == "done":
                    task["completed_at"] = datetime.now(timezone.utc).isoformat()
                else:
                    task["completed_at"] = None
            
            _save_tasks(data)
            return task
    
    return None


def delete_task(task_id: str) -> bool:
    """Verwijder task"""
    data = _load_tasks()
    
    original_count = len(data["tasks"])
    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
    
    if len(data["tasks"]) < original_count:
        _save_tasks(data)
        return True
    
    return False


def get_tasks_by_status(status: str) -> List[Dict]:
    """Filter tasks op status"""
    data = _load_tasks()
    return [t for t in data.get("tasks", []) if t["status"] == status]
