from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from utils.data_manager import DataManager
import json
from pathlib import Path

router = APIRouter()

FOLDERS_FILE = Path("/app/backend/data/learned_knowledge/folders.json")

class Folder(BaseModel):
    id: str
    name: str
    parent_id: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    position: Optional[int] = None

class FolderCreate(BaseModel):
    name: str
    parent_id: Optional[str] = None
    color: Optional[str] = "#4CAF50"
    icon: Optional[str] = "📁"

@router.get("/")
async def get_folders():
    """Get all folders"""
    try:
        if FOLDERS_FILE.exists():
            with open(FOLDERS_FILE, 'r') as f:
                data = json.load(f)
            return {"success": True, "folders": data.get("folders", [])}
        else:
            return {"success": True, "folders": []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/")
async def create_folder(folder: FolderCreate):
    """Create new folder"""
    try:
        import uuid
        
        if FOLDERS_FILE.exists():
            with open(FOLDERS_FILE, 'r') as f:
                data = json.load(f)
        else:
            data = {"folders": []}
        
        new_folder = {
            "id": str(uuid.uuid4()),
            "name": folder.name,
            "parent_id": folder.parent_id,
            "color": folder.color,
            "icon": folder.icon,
            "position": len(data["folders"])
        }
        
        data["folders"].append(new_folder)
        
        with open(FOLDERS_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        
        return {"success": True, "folder": new_folder}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/assign")
async def assign_card_to_folder(card_id: str, folder_id: str):
    """Assign knowledge card to folder"""
    try:
        # Load knowledge base
        kb_file = Path("/app/backend/data/learned_knowledge/knowledge_base.json")
        with open(kb_file, 'r') as f:
            kb_data = json.load(f)
        
        # Find card
        entries = kb_data.get("knowledge_entries", [])
        card = next((e for e in entries if e["id"] == card_id), None)
        
        if not card:
            raise HTTPException(status_code=404, detail="Card not found")
        
        # Update cluster
        if "cluster" not in card:
            card["cluster"] = {}
        
        card["cluster"]["folder_id"] = folder_id
        
        # Save
        with open(kb_file, 'w') as f:
            json.dump(kb_data, f, indent=2)
        
        return {"success": True, "message": "Card assigned to folder"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{folder_id}")
async def delete_folder(folder_id: str):
    """Delete folder (cards remain)"""
    try:
        if not FOLDERS_FILE.exists():
            raise HTTPException(status_code=404, detail="No folders found")
        
        with open(FOLDERS_FILE, 'r') as f:
            data = json.load(f)
        
        data["folders"] = [f for f in data["folders"] if f["id"] != folder_id]
        
        with open(FOLDERS_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        
        return {"success": True, "message": "Folder deleted"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
