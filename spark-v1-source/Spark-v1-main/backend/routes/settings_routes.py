from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import json
from pathlib import Path
from utils.paths import get_user_path

router = APIRouter()


class SettingsRequest(BaseModel):
    user_id: str
    key: str
    value: Any


class SettingsUpdate(BaseModel):
    user_id: str
    settings: Dict[str, Any]


@router.post("/get")
async def get_setting(request: SettingsRequest):
    """
    Get specific setting for user
    """
    try:
        settings_file = get_user_path(request.user_id, "settings.json")
        
        if not settings_file.exists():
            return {"success": False, "error": "Settings file not found"}
        
        with open(settings_file, 'r') as f:
            settings = json.load(f)
        
        value = settings.get(request.key)
        return {
            "success": True,
            "key": request.key,
            "value": value
        }
    
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/all/{user_id}")
async def get_all_settings(user_id: str):
    """
    Get all settings for user
    """
    try:
        settings_file = get_user_path(user_id, "settings.json")
        
        if not settings_file.exists():
            # Return empty settings if file doesn't exist
            return {"success": True, "settings": {}}
        
        with open(settings_file, 'r') as f:
            settings = json.load(f)
        
        return {
            "success": True,
            "settings": settings
        }
    
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/set")
async def set_setting(request: SettingsRequest):
    """
    Set specific setting for user
    """
    try:
        settings_file = get_user_path(request.user_id, "settings.json")
        settings_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing settings
        if settings_file.exists():
            with open(settings_file, 'r') as f:
                settings = json.load(f)
        else:
            settings = {}
        
        # Update setting
        settings[request.key] = request.value
        
        # Save
        with open(settings_file, 'w') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
        
        return {"success": True, "key": request.key}
    
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/update")
async def update_settings(request: SettingsUpdate):
    """
    Bulk update settings for user
    """
    try:
        settings_file = get_user_path(request.user_id, "settings.json")
        settings_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing settings
        if settings_file.exists():
            with open(settings_file, 'r') as f:
                settings = json.load(f)
        else:
            settings = {}
        
        # Update all provided settings
        settings.update(request.settings)
        
        # Save
        with open(settings_file, 'w') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
        
        return {"success": True, "updated_keys": list(request.settings.keys())}
    
    except Exception as e:
        return {"success": False, "error": str(e)}
