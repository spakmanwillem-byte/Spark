from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.game_engine import get_game_instance, update_game, ITEMS, PLACEABLE_ITEMS
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/game", tags=["game"])

# Admin models
class AdminResourcesUpdate(BaseModel):
    wood: int = None
    stone: int = None

class AdminNeedsUpdate(BaseModel):
    hunger: int = None
    thirst: int = None

@router.get("/state")
async def get_game_state():
    """
    Get current game state
    
    Returns:
    - grid_size: Size of the game world
    - spark: Spark entity (position, inventory, needs)
    - trees: Tree resources
    - stones: Stone resources
    - monument: Monument progress
    - game_time: Day/night info
    - stats: Game statistics
    """
    try:
        game = get_game_instance()
        state = game.get_state()
        
        return {
            "success": True,
            "state": state
        }
    except Exception as e:
        logger.error(f"[GAME API] Error getting game state: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/static-data")
async def get_static_data():
    """
    Get static game data (items, buildings)
    This data doesn't change during gameplay and only needs to be fetched once
    
    Returns:
    - items: All item definitions
    - placeable_items: All buildable item definitions
    """
    try:
        return {
            "success": True,
            "data": {
                "items": ITEMS,
                "placeable_items": PLACEABLE_ITEMS
            }
        }
    except Exception as e:
        logger.error(f"[GAME API] Error getting static data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/place-item")
async def place_item_endpoint(data: dict):
    """Place item on grid"""
    try:
        game = get_game_instance()
        result = game.place_item(
            data.get("item_type"),
            data.get("x"),
            data.get("y"),
            data.get("placed_by", "user")
        )
        return result
    except Exception as e:
        logger.error(f"[GAME API] Error placing item: {e}")
        raise HTTPException(status_code=500, detail=str(e))
async def reset_game():
    """
    Reset the game to initial state
    (For testing purposes)
    """
    try:
        from services.game_engine import GameEngine
        
        # Create new game instance
        import services.game_engine as ge
        ge._game_instance = GameEngine()
        
        logger.info("[GAME API] Game reset")
        
        return {
            "success": True,
            "message": "Game reset successfully"
        }
    except Exception as e:
        logger.error(f"[GAME API] Error resetting game: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Admin endpoints
@router.post("/admin/resources")
async def admin_set_resources(update: AdminResourcesUpdate):
    """Admin: Set Spark's resources"""
    try:
        game = get_game_instance()
        game.set_resources(wood=update.wood, stone=update.stone)
        
        return {
            "success": True,
            "message": "Resources updated",
            "inventory": game.spark["inventory"]
        }
    except Exception as e:
        logger.error(f"[GAME API] Error setting resources: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/admin/monument/reset")
async def admin_reset_monument():
    """Admin: Reset monument progress"""
    try:
        game = get_game_instance()
        game.reset_monument()
        
        return {
            "success": True,
            "message": "Monument reset",
            "monument": game.monument
        }
    except Exception as e:
        logger.error(f"[GAME API] Error resetting monument: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/admin/needs")
async def admin_set_needs(update: AdminNeedsUpdate):
    """Admin: Set Spark's hunger/thirst"""
    try:
        game = get_game_instance()
        game.set_needs(hunger=update.hunger, thirst=update.thirst)
        
        return {
            "success": True,
            "message": "Needs updated",
            "hunger": game.spark["hunger"],
            "thirst": game.spark["thirst"]
        }
    except Exception as e:
        logger.error(f"[GAME API] Error setting needs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/toggle-pause")
async def toggle_pause():
    """Toggle game pause/play"""
    try:
        game = get_game_instance()
        result = game.toggle_pause()
        return result
    except Exception as e:
        logger.error(f"[GAME API] Error toggling pause: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/damage")
async def apply_damage(data: dict):
    """Test endpoint: Apply damage to Spark for testing danger/flee system"""
    try:
        game = get_game_instance()
        amount = data.get("amount", 30)
        source_x = data.get("source_x", game.spark["x"])
        source_y = data.get("source_y", game.spark["y"])
        
        game.take_damage(amount, source_x, source_y)
        
        return {
            "success": True,
            "message": f"Applied {amount} damage to Spark",
            "health": game.spark.get("health", 100),
            "is_fleeing": game.spark.get("is_fleeing", False)
        }
    except Exception as e:
        logger.error(f"[GAME API] Error applying damage: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/buildings-overview")
async def get_buildings_overview():
    """
    Get overview of all buildings grouped by faction/Spark
    For UI tabs to show what each faction has built
    """
    try:
        game = get_game_instance()
        
        # Get all placed buildings
        buildings = game.placed_items
        
        # Group by faction (for now all belong to Spark)
        overview = {
            "spark": [],
            "terra": [],
            "aqua": [],
            "ignis": [],
            "ventus": []
        }
        
        # All buildings belong to Spark for now
        overview["spark"] = [
            {
                "type": building.get("type"),
                "icon": PLACEABLE_ITEMS.get(building.get("type"), {}).get("icon", ""),
                "name": PLACEABLE_ITEMS.get(building.get("type"), {}).get("name", ""),
                "x": building.get("x"),
                "y": building.get("y"),
                "id": building.get("id")
            }
            for building in buildings
        ]
        
        # Get resources
        spark_inv = game.spark.get("inventory", {})
        
        # Get workhouse storage totals
        total_storage = {"wood": 0, "stone": 0, "fish": 0, "grain": 0, "flour": 0, "bread": 0, "plank": 0, "water": 0}
        for storage in game.workhouses.values():
            for key in total_storage.keys():
                total_storage[key] += storage.get(key, 0)
        
        return {
            "success": True,
            "overview": overview,
            "spark_inventory": spark_inv,
            "total_storage": total_storage,
            "building_count": len(buildings)
        }
    
    except Exception as e:
        logger.error(f"[GAME API] Error getting buildings overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/combat/history")
async def get_combat_history():
    """Get combat history"""
    try:
        game = get_game_instance()
        return {
            "success": True,
            "combat_history": game.combat_history,
            "total_combats": len(game.combat_history)
        }
    except Exception as e:
        logger.error(f"Failed to get combat history: {e}")
        return {"success": False, "error": str(e)}

@router.post("/combat/test")
async def test_combat():
    """Test combat system with dummy data"""
    try:
        from services.combat_engine import CombatEngine, ACTION_ATTACK, ACTION_DEFEND, STANCE_ATTACK, STANCE_DEFEND
        
        attacker = {"units": 1, "type": "soldier", "power": 10}
        defender = {"units": 1, "type": "worker", "power": 5}
        
        result = CombatEngine.calculate_combat(
            attacker, defender,
            attacker_action=ACTION_ATTACK,
            defender_action=ACTION_DEFEND,
            attacker_stance=STANCE_ATTACK,
            defender_stance=STANCE_DEFEND
        )
        
        return {
            "success": True,
            "combat_result": result
        }
    except Exception as e:
        logger.error(f"Combat test failed: {e}")
        return {"success": False, "error": str(e)}



@router.post("/admin/place-item")
async def admin_place_item(data: dict):
    """
    Admin endpoint to place items directly on grid (dev tool)
    No resource checks, instant placement
    
    Supported types: tree, stone, mountain, water, zombie, animal
    """
    try:
        game = get_game_instance()
        item_type = data.get("type")
        x = data.get("x")
        y = data.get("y")
        
        if not all([item_type, x is not None, y is not None]):
            return {"success": False, "message": "Missing type, x, or y"}
        
        # Place item based on type
        if item_type == "tree":
            tree = {
                "id": f"tree_{len(game.trees)}",
                "x": x,
                "y": y,
                "wood_amount": 3
            }
            game.trees.append(tree)
            game.explored_tiles.add((x, y))
            logger.info(f"[ADMIN] Placed tree at ({x}, {y})")
            
        elif item_type == "stone":
            stone = {
                "id": f"stone_{len(game.stones)}",
                "x": x,
                "y": y,
                "stone_amount": 2
            }
            game.stones.append(stone)
            game.explored_tiles.add((x, y))
            logger.info(f"[ADMIN] Placed stone at ({x}, {y})")
            
        elif item_type == "mountain":
            mountain = {
                "id": f"mountain_{len(game.mountains)}",
                "x": x,
                "y": y
            }
            game.mountains.append(mountain)
            game.explored_tiles.add((x, y))
            logger.info(f"[ADMIN] Placed mountain at ({x}, {y})")
            
        elif item_type == "water":
            game.water_tiles.append((x, y))
            game.explored_tiles.add((x, y))
            logger.info(f"[ADMIN] Placed water at ({x}, {y})")
        
        elif item_type in ["wall", "gate"]:
            # Place defensive structure with health
            structure = {
                "id": f"{item_type}_{len(game.placed_items)}",
                "type": item_type,
                "x": x,
                "y": y,
                "health": 500 if item_type == "wall" else 300,
                "max_health": 500 if item_type == "wall" else 300,
                "icon": "🧱" if item_type == "wall" else "🚪"
            }
            game.placed_items.append(structure)
            game.explored_tiles.add((x, y))
            logger.info(f"[ADMIN] Placed {item_type} ({structure['health']} HP) at ({x}, {y})")
        
        elif item_type in ["warehouse", "house", "lumberjack", "planter", "miner", "fisher", "farm"]:
            # Place building (admin bypass - no resource cost)
            from services.game_engine import PLACEABLE_ITEMS
            
            if item_type not in PLACEABLE_ITEMS:
                return {"success": False, "message": f"Building type {item_type} not found"}
            
            building_def = PLACEABLE_ITEMS[item_type]
            building = {
                "id": f"{item_type}_{len(game.placed_items)}",
                "type": item_type,
                "x": x,
                "y": y,
                "icon": building_def.get("icon", "🏗️"),
                "name": building_def.get("name", item_type),
                "built_day": game.game_time["day"]
            }
            
            # Special init for specific buildings
            if item_type == "planter":
                building["trees_planted"] = 0
            
            game.placed_items.append(building)
            game.explored_tiles.add((x, y))
            logger.info(f"[ADMIN] Placed {item_type} at ({x}, {y})")
            
        elif item_type in ["zombie_barbarian", "wolf", "bear", "deer", "rabbit", "king_gaia", "king_neptune", "king_vulcan", "king_zephyr"]:
            # Use EntityManager to spawn from blueprint
            entity = game.entity_manager.spawn_entity(item_type, x, y)
            if entity:
                entity["spawn_day"] = game.game_time["day"]
                game.explored_tiles.add((x, y))
                
                # Special handling for king bots
                if item_type.startswith("king_"):
                    entity["is_king"] = True
                    entity["inventory"] = {"wood": 0, "stone": 0, "fish": 0, "grain": 0}
                    logger.info(f"[ADMIN] Spawned KING {entity['name']} ({entity['faction']}) at ({x}, {y})")
                else:
                    logger.info(f"[ADMIN] Spawned {entity['name']} at ({x}, {y})")
            else:
                return {"success": False, "message": f"Failed to spawn {item_type}"}
            
        else:
            return {"success": False, "message": f"Unknown type: {item_type}"}
        
        return {
            "success": True,
            "message": f"{item_type.capitalize()} placed at ({x}, {y})"
        }
        
    except Exception as e:
        logger.error(f"[ADMIN] Place item error: {e}", exc_info=True)
        return {"success": False, "message": str(e)}
