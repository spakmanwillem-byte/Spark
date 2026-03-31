from fastapi import APIRouter
import json
from pathlib import Path

router = APIRouter(prefix="/factions", tags=["factions"])

FACTIONS_FILE = Path("/app/backend/data/factions.json")

def load_factions():
    if FACTIONS_FILE.exists():
        with open(FACTIONS_FILE, 'r') as f:
            return json.load(f)
    return {"factions": []}

def save_factions(data):
    with open(FACTIONS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

@router.get("/list")
async def get_factions():
    """Get all factions"""
    data = load_factions()
    return {"success": True, "factions": data["factions"]}

@router.get("/{faction_id}")
async def get_faction(faction_id: str):
    """Get single faction"""
    data = load_factions()
    faction = next((f for f in data["factions"] if f["id"] == faction_id), None)
    if not faction:
        return {"success": False, "message": "Faction not found"}
    return {"success": True, "faction": faction}

@router.put("/{faction_id}/warehouse")
async def update_warehouse(faction_id: str, updates: dict):
    """Update faction warehouse (admin)"""
    data = load_factions()
    faction = next((f for f in data["factions"] if f["id"] == faction_id), None)
    
    if not faction:
        return {"success": False, "message": "Faction not found"}
    
    # Update warehouse
    for key, value in updates.items():
        if key in faction["warehouse"]:
            faction["warehouse"][key] = value
    
    save_factions(data)
    return {"success": True, "faction": faction}
