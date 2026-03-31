from fastapi import APIRouter
import json
from pathlib import Path

router = APIRouter(prefix="/actors", tags=["actors"])

ACTORS_FILE = Path("/app/backend/data/actors.json")

def load_actors():
    if ACTORS_FILE.exists():
        with open(ACTORS_FILE, 'r') as f:
            return json.load(f)
    return {"actors": []}

def save_actors(data):
    with open(ACTORS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

@router.get("/list")
async def get_actors():
    """Get all actors"""
    data = load_actors()
    return {"success": True, "actors": data["actors"]}

@router.get("/{actor_id}")
async def get_actor(actor_id: str):
    """Get single actor"""
    data = load_actors()
    actor = next((a for a in data["actors"] if a["id"] == actor_id), None)
    if not actor:
        return {"success": False, "message": "Actor not found"}
    return {"success": True, "actor": actor}

@router.put("/{actor_id}")
async def update_actor(actor_id: str, updates: dict):
    """Update actor (admin)"""
    data = load_actors()
    actor = next((a for a in data["actors"] if a["id"] == actor_id), None)
    
    if not actor:
        return {"success": False, "message": "Actor not found"}
    
    # Update fields
    for key, value in updates.items():
        if key in actor:
            actor[key] = value
    
    save_actors(data)
    return {"success": True, "actor": actor}

@router.put("/{actor_id}/stats")
async def update_actor_stats(actor_id: str, stats: dict):
    """Update actor stats (admin)"""
    data = load_actors()
    actor = next((a for a in data["actors"] if a["id"] == actor_id), None)
    
    if not actor:
        return {"success": False, "message": "Actor not found"}
    
    # Update stats
    for key, value in stats.items():
        if key in actor["stats"]:
            actor["stats"][key] = value
    
    save_actors(data)
    return {"success": True, "actor": actor}
