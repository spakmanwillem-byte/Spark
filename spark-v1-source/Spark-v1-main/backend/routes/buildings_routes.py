from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/buildings", tags=["buildings"])

# Import PLACEABLE_ITEMS from game_engine
from services.game_engine import PLACEABLE_ITEMS

class BuildingUpdate(BaseModel):
    item_type: str
    updates: Dict[str, Any]

@router.get("/list")
async def get_buildings():
    """
    Get all available buildings with their properties
    """
    try:
        # Convert PLACEABLE_ITEMS to a more structured format
        buildings = []
        
        for item_type, config in PLACEABLE_ITEMS.items():
            building = {
                "id": item_type,
                "name": config.get("name", item_type),
                "icon": config.get("icon", "📦"),
                "type": config.get("type", "building"),
                "cost": config.get("cost", {}),
                "production": None,
                "unlocks": [],
                "properties": {}
            }
            
            # Production info
            if "process" in config:
                process = config["process"]
                building["production"] = {
                    "input": process.get("input"),
                    "output": process.get("output"),
                    "rate": process.get("rate", 1)
                }
            
            # Special properties
            if "workers" in config:
                building["properties"]["workers"] = config["workers"]
            if "storage_capacity" in config:
                building["properties"]["storage_capacity"] = config["storage_capacity"]
            if "requires" in config:
                building["properties"]["requires"] = config["requires"]
            if "production" in config:
                building["properties"]["auto_production"] = config["production"]
            
            buildings.append(building)
        
        # Group by type
        grouped = {
            "buildings": [b for b in buildings if b["type"] == "building"],
            "professions": [b for b in buildings if b["type"] == "profession"],
            "terrain": [b for b in buildings if b["type"] in ["terrain", "resource"]],
            "tools": [b for b in buildings if b["type"] == "tool"]
        }
        
        return {
            "success": True,
            "buildings": buildings,
            "grouped": grouped,
            "total": len(buildings)
        }
    except Exception as e:
        logger.error(f"[BUILDINGS API] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tree")
async def get_buildings_tree():
    """
    Get buildings in a tree structure for blueprint view
    """
    try:
        tree = {
            "name": "All Buildings",
            "children": []
        }
        
        # Group by category
        categories = {
            "🏗️ Basic Buildings": ["house", "warehouse", "wall", "farm"],
            "⚒️ Production": ["lumberjack", "miner", "fisher", "farmer", "sawmill", "miller", "baker"],
            "🌱 Nature": ["planter", "cropfield", "well"],
            "🏃 Support": ["runner"]
        }
        
        for category_name, item_types in categories.items():
            category_node = {
                "name": category_name,
                "type": "category",
                "children": []
            }
            
            for item_type in item_types:
                if item_type in PLACEABLE_ITEMS:
                    config = PLACEABLE_ITEMS[item_type]
                    
                    building_node = {
                        "id": item_type,
                        "name": config.get("name", item_type),
                        "icon": config.get("icon", "📦"),
                        "cost": config.get("cost", {}),
                        "type": config.get("type", "building"),
                        "properties": {
                            k: v for k, v in config.items() 
                            if k not in ["name", "icon", "cost", "type"]
                        }
                    }
                    
                    category_node["children"].append(building_node)
            
            if category_node["children"]:
                tree["children"].append(category_node)
        
        return {
            "success": True,
            "tree": tree
        }
    except Exception as e:
        logger.error(f"[BUILDINGS TREE] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update")
async def update_building(update: BuildingUpdate):
    """
    Update building properties (admin only in production)
    Note: This updates runtime only - restart required for persistence
    """
    try:
        item_type = update.item_type
        
        if item_type not in PLACEABLE_ITEMS:
            raise HTTPException(status_code=404, detail=f"Building {item_type} not found")
        
        # Update the building config
        for key, value in update.updates.items():
            PLACEABLE_ITEMS[item_type][key] = value
        
        logger.info(f"[BUILDINGS] Updated {item_type}: {update.updates}")
        
        return {
            "success": True,
            "message": f"Building {item_type} updated",
            "building": PLACEABLE_ITEMS[item_type]
        }
    except Exception as e:
        logger.error(f"[BUILDINGS UPDATE] Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
