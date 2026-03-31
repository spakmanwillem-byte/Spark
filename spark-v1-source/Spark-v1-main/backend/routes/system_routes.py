from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional, List, Dict
import json
import os
from datetime import datetime
from utils.paths import PATHS, get_data_path

router = APIRouter()

# Cross-platform paths
SETTINGS_FILE = PATHS["settings"]
LOGS_FILE = PATHS["logs"]
BUG_REPORTS_FILE = PATHS["bug_reports"]
SOUNDS_DIR = PATHS["sounds_dir"]
SOUNDS_MAPPING_FILE = get_data_path("system", "sound_mappings.json")
TRIGGERS_DIR = get_data_path("triggers")

# Ensure directories exist
SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
LOGS_FILE.parent.mkdir(parents=True, exist_ok=True)
SOUNDS_DIR.mkdir(parents=True, exist_ok=True)

class SettingsUpdate(BaseModel):
    settings: Dict

class BugReport(BaseModel):
    user_id: Optional[str] = None
    user_name: str
    title: str
    description: str
    severity: str
    timestamp: str

# ==================== SETTINGS ENDPOINTS ====================

@router.get("/settings")
async def get_settings():
    """Get system settings"""
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r') as f:
                settings = json.load(f)
        else:
            # Default settings
            settings = {
                "heartbeat_interval": 30,
                "session_timeout": 5,
                "debug_mode": False,
                "auto_save": True,
                "notification_sound": True
            }
        return {"settings": settings}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/settings")
async def update_settings(data: SettingsUpdate):
    """Update system settings"""
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(data.settings, f, indent=2)
        return {"success": True, "message": "Settings saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== LOGS ENDPOINTS ====================

@router.get("/logs")
async def get_logs(limit: int = 100):
    """Get system logs"""
    try:
        if os.path.exists(LOGS_FILE):
            with open(LOGS_FILE, 'r') as f:
                logs = json.load(f)
        else:
            logs = []
        
        # Return most recent logs
        return {"logs": logs[-limit:] if len(logs) > limit else logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/bugs/report")
async def report_bug(bug: BugReport):
    """Submit a bug report"""
    try:
        # Load existing reports
        if os.path.exists(BUG_REPORTS_FILE):
            with open(BUG_REPORTS_FILE, 'r') as f:
                reports = json.load(f)
        else:
            reports = []
        
        # Add new report
        bug_dict = bug.dict()
        bug_dict['id'] = f"bug_{len(reports) + 1}"
        reports.append(bug_dict)
        
        # Save
        with open(BUG_REPORTS_FILE, 'w') as f:
            json.dump(reports, f, indent=2)
        
        # Also add to logs
        log_entry = {
            "level": "warning",
            "message": f"Bug reported: {bug.title}",
            "timestamp": bug.timestamp,
            "details": f"{bug.description} (Severity: {bug.severity})"
        }
        
        if os.path.exists(LOGS_FILE):
            with open(LOGS_FILE, 'r') as f:
                logs = json.load(f)
        else:
            logs = []
        
        logs.append(log_entry)
        
        with open(LOGS_FILE, 'w') as f:
            json.dump(logs, f, indent=2)
        
        return {"success": True, "message": "Bug report submitted", "bug_id": bug_dict['id']}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== SOUNDS ENDPOINTS ====================

@router.get("/sounds/mappings")
async def get_sound_mappings(user_id: Optional[str] = None):
    """
    Get sound mappings filtered by visibility rules:
    - Own private sounds (user_id matches)
    - Shared sounds from others (visibility = 'shared')
    - Global system sounds (user_id = 'user-000' or visibility = 'global')
    """
    try:
        if os.path.exists(SOUNDS_MAPPING_FILE):
            with open(SOUNDS_MAPPING_FILE, 'r') as f:
                data = json.load(f)
                all_mappings = data.get('mappings', [])
                
                # If no user_id provided, return all (backwards compatibility)
                if not user_id:
                    return {"mappings": all_mappings}
                
                # Filter based on visibility rules
                filtered = []
                for mapping in all_mappings:
                    # Own sounds
                    if mapping.get('user_id') == user_id:
                        filtered.append(mapping)
                    # Shared sounds
                    elif mapping.get('visibility') == 'shared':
                        filtered.append(mapping)
                    # Global system sounds
                    elif mapping.get('visibility') == 'global' or mapping.get('user_id') == 'user-000':
                        filtered.append(mapping)
                
                return {"mappings": filtered}
        return {"mappings": []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sounds/mapping")
async def add_sound_mapping(
    audio: UploadFile = File(...),
    word: str = None,
    frequency: str = None,
    user_id: str = None,
    display_name: str = None,
    visibility: str = 'private',  # NEW: private, shared, global
    sound_type: str = 'user'  # NEW: user, system, button, command
):
    """Add a new sound mapping with visibility control"""
    try:
        if not word or not frequency or not user_id:
            raise HTTPException(status_code=400, detail="Missing required fields: word, frequency, user_id")
        
        # Use display_name or default to word
        if not display_name:
            display_name = word.capitalize()
        
        # Save audio file
        filename = f"{word}_{datetime.now().timestamp()}.{audio.filename.split('.')[-1]}"
        filepath = os.path.join(SOUNDS_DIR, filename)
        
        with open(filepath, 'wb') as f:
            content = await audio.read()
            f.write(content)
        
        # Load existing mappings
        if os.path.exists(SOUNDS_MAPPING_FILE):
            with open(SOUNDS_MAPPING_FILE, 'r') as f:
                data = json.load(f)
                mappings = data.get('mappings', [])
        else:
            mappings = []
        
        # Add new mapping
        new_mapping = {
            "id": f"sound_{len(mappings) + 1}",
            "word": word.lower(),
            "display_name": display_name,
            "frequency": frequency,
            "file": filename,
            "filepath": filepath,
            "user_id": user_id,
            "visibility": visibility,  # NEW
            "type": sound_type,  # NEW
            "created_at": datetime.now().isoformat(),
            "play_count": 0
        }
        mappings.append(new_mapping)
        
        # Save
        with open(SOUNDS_MAPPING_FILE, 'w') as f:
            json.dump({"mappings": mappings}, f, indent=2)
        
        return {"success": True, "message": "Sound mapping added", "mapping": new_mapping}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sounds/play/{mapping_id}")
async def play_sound(mapping_id: str):
    """Get sound file URL"""
    try:
        if os.path.exists(SOUNDS_MAPPING_FILE):
            with open(SOUNDS_MAPPING_FILE, 'r') as f:
                data = json.load(f)
                mappings = data.get('mappings', [])
                
            mapping = next((m for m in mappings if m['id'] == mapping_id), None)
            if mapping:
                # Increment play count
                mapping['play_count'] = mapping.get('play_count', 0) + 1
                with open(SOUNDS_MAPPING_FILE, 'w') as f:
                    json.dump({"mappings": mappings}, f, indent=2)
                
                return {"url": f"/media/sounds/{mapping['file']}"}
        
        raise HTTPException(status_code=404, detail="Sound not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sounds/stream/{filename}")
async def stream_sound(filename: str):
    """Stream audio file"""
    from fastapi.responses import FileResponse
    
    filepath = os.path.join(SOUNDS_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Sound file not found")
    
    # Detect media type from extension
    media_type = "audio/mpeg"
    if filename.endswith('.wav'):
        media_type = "audio/wav"
    elif filename.endswith('.ogg'):
        media_type = "audio/ogg"
    
    return FileResponse(filepath, media_type=media_type)


@router.put("/sounds/mapping/{mapping_id}")
async def update_sound_mapping(
    mapping_id: str,
    word: str = None,
    display_name: str = None,
    frequency: str = None
):
    """Update sound mapping properties"""
    try:
        if not os.path.exists(SOUNDS_MAPPING_FILE):
            raise HTTPException(status_code=404, detail="No mappings found")
        
        with open(SOUNDS_MAPPING_FILE, 'r') as f:
            data = json.load(f)
            mappings = data.get('mappings', [])
        
        mapping = next((m for m in mappings if m['id'] == mapping_id), None)
        if not mapping:
            raise HTTPException(status_code=404, detail="Mapping not found")
        
        # Update fields
        if word:
            mapping['word'] = word.lower()
        if display_name:
            mapping['display_name'] = display_name
        if frequency:
            mapping['frequency'] = frequency
        
        mapping['updated_at'] = datetime.now().isoformat()
        
        # Save
        with open(SOUNDS_MAPPING_FILE, 'w') as f:
            json.dump({"mappings": mappings}, f, indent=2)
        
        return {"success": True, "message": "Mapping updated", "mapping": mapping}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/sounds/mapping/{mapping_id}")
async def delete_sound_mapping(mapping_id: str):
    """Delete a sound mapping"""
    try:
        if os.path.exists(SOUNDS_MAPPING_FILE):
            with open(SOUNDS_MAPPING_FILE, 'r') as f:
                data = json.load(f)
                mappings = data.get('mappings', [])
            
            # Find and remove mapping
            mapping = next((m for m in mappings if m['id'] == mapping_id), None)
            if mapping:
                # Delete file
                if os.path.exists(mapping['filepath']):
                    os.remove(mapping['filepath'])
                
                # Remove from list
                mappings = [m for m in mappings if m['id'] != mapping_id]
                
                # Save
                with open(SOUNDS_MAPPING_FILE, 'w') as f:
                    json.dump({"mappings": mappings}, f, indent=2)
                
                return {"success": True, "message": "Sound mapping deleted"}
        
        raise HTTPException(status_code=404, detail="Sound not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== TRIGGERS ENDPOINTS ====================

@router.get("/triggers/all")
async def get_all_triggers():
    """Get all trigger lists"""
    try:
        # Load emotion triggers
        emotion_file = os.path.join(TRIGGERS_DIR, "emotion_triggers.json")
        with open(emotion_file, 'r') as f:
            emotion_data = json.load(f)
        
        # Load conversation triggers
        conversation_file = os.path.join(TRIGGERS_DIR, "conversation_triggers.json")
        with open(conversation_file, 'r') as f:
            conversation_data = json.load(f)
        
        # Load calendar triggers
        calendar_file = os.path.join(TRIGGERS_DIR, "calendar_triggers.json")
        with open(calendar_file, 'r') as f:
            calendar_data = json.load(f)
        
        return {
            "emotions": emotion_data.get('emotions', {}),
            "conversation": conversation_data.get('triggers', {}),
            "calendar": calendar_data.get('triggers', {})
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/triggers/add")
async def add_trigger_word(request: dict):
    """Add a word to a trigger list"""
    try:
        category = request.get("category")
        subcategory = request.get("subcategory")
        word = request.get("word")
        
        if not all([category, subcategory, word]):
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        # Determine file
        if category == "emotions":
            filepath = os.path.join(TRIGGERS_DIR, "emotion_triggers.json")
            key = "emotions"
        elif category == "conversation":
            filepath = os.path.join(TRIGGERS_DIR, "conversation_triggers.json")
            key = "triggers"
        elif category == "calendar":
            filepath = os.path.join(TRIGGERS_DIR, "calendar_triggers.json")
            key = "triggers"
        else:
            raise HTTPException(status_code=400, detail="Invalid category")
        
        # Load file
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Add word based on structure
        if category == "emotions":
            # Emotion triggers use {subcategory: {triggers: {word: score}}} format
            if subcategory not in data[key]:
                data[key][subcategory] = {"triggers": {}}
            if "triggers" not in data[key][subcategory]:
                data[key][subcategory]["triggers"] = {}
            # Add word with default score
            if word not in data[key][subcategory]["triggers"]:
                data[key][subcategory]["triggers"][word] = 0.8
        else:
            # Conversation and calendar use array format
            if subcategory in data[key]:
                if word not in data[key][subcategory]:
                    data[key][subcategory].append(word)
            else:
                data[key][subcategory] = [word]
        
        # Save
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return {"success": True, "message": f"Added '{word}' to {category}/{subcategory}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/triggers/remove")
async def remove_trigger_word(category: str, subcategory: str, word: str):
    """Remove a word from a trigger list"""
    try:
        # Determine file
        if category == "emotions":
            filepath = os.path.join(TRIGGERS_DIR, "emotion_triggers.json")
            key = "emotions"
        elif category == "conversation":
            filepath = os.path.join(TRIGGERS_DIR, "conversation_triggers.json")
            key = "triggers"
        elif category == "calendar":
            filepath = os.path.join(TRIGGERS_DIR, "calendar_triggers.json")
            key = "triggers"
        else:
            raise HTTPException(status_code=400, detail="Invalid category")
        
        # Load file
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Remove word
        if category == "emotions":
            # Emotion triggers use dict format
            if subcategory in data[key] and "triggers" in data[key][subcategory]:
                if word in data[key][subcategory]["triggers"]:
                    del data[key][subcategory]["triggers"][word]
        else:
            # Conversation/calendar use array format
            if subcategory in data[key] and word in data[key][subcategory]:
                data[key][subcategory].remove(word)
        
        # Save
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return {"success": True, "message": f"Removed '{word}' from {category}/{subcategory}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
