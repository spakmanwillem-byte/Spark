"""
Blueprint API - Custom Buildings, Resources & Actions Management
"""
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional, Dict
import json
import os
from datetime import datetime
import shutil

router = APIRouter(prefix="/api/blueprints", tags=["blueprints"])

# Data file paths
BUILDINGS_FILE = "/app/backend/data/custom_buildings.json"
RESOURCES_FILE = "/app/backend/data/custom_resources.json"
ACTIONS_FILE = "/app/backend/data/task_actions.json"
BOTS_FILE = "/app/backend/data/bot_blueprints.json"
UPLOAD_DIR = "/app/backend/static/uploaded_icons"

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ============= PYDANTIC MODELS =============

class ResourceAmount(BaseModel):
    resource: str
    amount: int

class CustomBuilding(BaseModel):
    id: Optional[str] = None
    name: str
    type: str  # production, storage, housing, defense, etc.
    faction: str  # spark, terra, aqua, ignis, ventus
    icon: str  # emoji or URL
    description: str
    input_resources: List[ResourceAmount] = []
    output_resources: List[ResourceAmount] = []
    build_cost: Dict[str, int]

class CustomResource(BaseModel):
    id: Optional[str] = None
    name: str
    icon: str
    weight: float  # kg per unit
    volume: float  # cubic units
    description: str
    is_default: bool = False

class TaskAction(BaseModel):
    id: str
    name: str
    icon: str
    description: str

class BotBlueprint(BaseModel):
    id: Optional[str] = None
    name: str
    icon: str
    faction: str  # neutral, friend, enemy, spark
    type: str  # animal, humanoid, worker, soldier
    behavior: str  # passief, agressief, gather, transport, attack
    combat_type: str  # worker, soldier
    vision_radius: int
    health: int
    power: int
    speed: float
    carry_capacity: Optional[int] = 0  # For workers
    role: Optional[str] = None  # warehouse_runner, gatherer, etc.
    linked_building: Optional[str] = None  # Building ID if worker is linked
    drop_resource: Optional[Dict] = None
    spawn_biome: List[str] = []
    is_aggressive: bool = False

# ============= HELPER FUNCTIONS =============

def load_json(file_path: str) -> dict:
    """Load JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"buildings": []} if "buildings" in file_path else {"resources": []} if "resources" in file_path else {"actions": []}

def save_json(file_path: str, data: dict):
    """Save JSON file"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def generate_id(prefix: str) -> str:
    """Generate unique ID"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"{prefix}_{timestamp}"

# ============= BUILDINGS API =============

@router.get("/buildings")
async def get_buildings():
    """Get all custom buildings"""
    data = load_json(BUILDINGS_FILE)
    return {"success": True, "buildings": data.get("buildings", [])}

@router.post("/buildings")
async def create_building(building: CustomBuilding):
    """Create new custom building"""
    data = load_json(BUILDINGS_FILE)
    
    # Generate ID if not provided
    if not building.id:
        building.id = generate_id("building")
    
    # Add timestamps
    building_dict = building.dict()
    building_dict["created_at"] = datetime.now().isoformat()
    building_dict["updated_at"] = datetime.now().isoformat()
    
    # Add to list
    data["buildings"].append(building_dict)
    save_json(BUILDINGS_FILE, data)
    
    return {"success": True, "building": building_dict}

@router.put("/buildings/{building_id}")
async def update_building(building_id: str, building: CustomBuilding):
    """Update existing building"""
    data = load_json(BUILDINGS_FILE)
    
    # Find building
    for i, b in enumerate(data["buildings"]):
        if b["id"] == building_id:
            building_dict = building.dict()
            building_dict["id"] = building_id
            building_dict["created_at"] = b.get("created_at", datetime.now().isoformat())
            building_dict["updated_at"] = datetime.now().isoformat()
            data["buildings"][i] = building_dict
            save_json(BUILDINGS_FILE, data)
            return {"success": True, "building": building_dict}
    
    raise HTTPException(status_code=404, detail="Building not found")

@router.delete("/buildings/{building_id}")
async def delete_building(building_id: str):
    """Delete building"""
    data = load_json(BUILDINGS_FILE)
    
    # Filter out building
    original_count = len(data["buildings"])
    data["buildings"] = [b for b in data["buildings"] if b["id"] != building_id]
    
    if len(data["buildings"]) == original_count:
        raise HTTPException(status_code=404, detail="Building not found")
    
    save_json(BUILDINGS_FILE, data)
    return {"success": True, "message": "Building deleted"}

# ============= RESOURCES API =============

@router.get("/resources")
async def get_resources():
    """Get all resources"""
    data = load_json(RESOURCES_FILE)
    return {"success": True, "resources": data.get("resources", [])}

@router.post("/resources")
async def create_resource(resource: CustomResource):
    """Create new custom resource"""
    data = load_json(RESOURCES_FILE)
    
    # Generate ID if not provided
    if not resource.id:
        resource.id = generate_id("resource")
    
    resource_dict = resource.dict()
    data["resources"].append(resource_dict)
    save_json(RESOURCES_FILE, data)
    
    return {"success": True, "resource": resource_dict}

@router.put("/resources/{resource_id}")
async def update_resource(resource_id: str, resource: CustomResource):
    """Update existing resource"""
    data = load_json(RESOURCES_FILE)
    
    for i, r in enumerate(data["resources"]):
        if r["id"] == resource_id:
            resource_dict = resource.dict()
            resource_dict["id"] = resource_id
            data["resources"][i] = resource_dict
            save_json(RESOURCES_FILE, data)
            return {"success": True, "resource": resource_dict}
    
    raise HTTPException(status_code=404, detail="Resource not found")

@router.delete("/resources/{resource_id}")
async def delete_resource(resource_id: str):
    """Delete resource (only if not default)"""
    data = load_json(RESOURCES_FILE)
    
    # Find resource and check if default
    for r in data["resources"]:
        if r["id"] == resource_id and r.get("is_default", False):
            raise HTTPException(status_code=400, detail="Cannot delete default resource")
    
    original_count = len(data["resources"])
    data["resources"] = [r for r in data["resources"] if r["id"] != resource_id]
    
    if len(data["resources"]) == original_count:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    save_json(RESOURCES_FILE, data)
    return {"success": True, "message": "Resource deleted"}

# ============= ACTIONS API =============

@router.get("/actions")
async def get_actions():
    """Get all task actions"""
    data = load_json(ACTIONS_FILE)
    return {"success": True, "actions": data.get("actions", [])}

@router.post("/actions")
async def create_action(action: TaskAction):
    """Create new task action"""
    data = load_json(ACTIONS_FILE)
    
    action_dict = action.dict()
    data["actions"].append(action_dict)
    save_json(ACTIONS_FILE, data)
    
    return {"success": True, "action": action_dict}

# ============= BOT BLUEPRINT API =============

@router.get("/bots")
async def get_bots():
    """Get all bot blueprints"""
    data = load_json(BOTS_FILE)
    return {"bots": data.get("bot_blueprints", [])}

@router.get("/bots/{bot_id}")
async def get_bot(bot_id: str):
    """Get specific bot blueprint"""
    data = load_json(BOTS_FILE)
    bots = data.get("bot_blueprints", [])
    
    bot = next((b for b in bots if b["id"] == bot_id), None)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    return {"bot": bot}

@router.post("/bots")
async def create_bot(bot: BotBlueprint):
    """Create new bot blueprint"""
    data = load_json(BOTS_FILE)
    
    # Generate ID if not provided
    if not bot.id:
        bot.id = bot.name.lower().replace(" ", "_")
    
    bot_dict = bot.dict()
    data.setdefault("bot_blueprints", []).append(bot_dict)
    save_json(BOTS_FILE, data)
    
    return {"success": True, "bot": bot_dict}

@router.put("/bots/{bot_id}")
async def update_bot(bot_id: str, bot: BotBlueprint):
    """Update bot blueprint"""
    data = load_json(BOTS_FILE)
    bots = data.get("bot_blueprints", [])
    
    bot_index = next((i for i, b in enumerate(bots) if b["id"] == bot_id), None)
    if bot_index is None:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    bot_dict = bot.dict()
    bot_dict["id"] = bot_id  # Preserve ID
    bots[bot_index] = bot_dict
    save_json(BOTS_FILE, data)
    
    return {"success": True, "bot": bot_dict}

@router.delete("/bots/{bot_id}")
async def delete_bot(bot_id: str):
    """Delete bot blueprint"""
    data = load_json(BOTS_FILE)
    bots = data.get("bot_blueprints", [])
    
    original_count = len(bots)
    data["bot_blueprints"] = [b for b in bots if b["id"] != bot_id]
    
    if len(data["bot_blueprints"]) == original_count:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    save_json(BOTS_FILE, data)
    return {"success": True}

# ============= ICON UPLOAD API =============

@router.post("/upload-icon")
async def upload_icon(file: UploadFile = File(...)):
    """Upload custom icon"""
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    extension = file.filename.split(".")[-1]
    filename = f"icon_{timestamp}.{extension}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Return URL
    icon_url = f"/static/uploaded_icons/{filename}"
    return {"success": True, "icon_url": icon_url}
