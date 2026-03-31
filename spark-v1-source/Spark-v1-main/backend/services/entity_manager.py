"""
ENTITY MANAGER - Bot Blueprint System
======================================

Manages all entities (animals, NPCs, enemies) in the game world.
Supports:
- Spawning from blueprints
- AI behavior (passive/aggressive)
- Combat integration
- Resource drops on death
- Vision & detection ranges
"""

import json
import uuid
import random
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

BLUEPRINTS_FILE = "/app/backend/data/bot_blueprints.json"

class EntityManager:
    """Manages all entities in the game world"""
    
    def __init__(self):
        self.blueprints = self._load_blueprints()
        self.entities = []  # Active entities in world
        self.next_entity_id = 0
    
    def _load_blueprints(self) -> Dict:
        """Load bot blueprints from JSON"""
        try:
            with open(BLUEPRINTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Blueprints file not found: {BLUEPRINTS_FILE}")
            return {"bot_blueprints": [], "resource_drops": []}
    
    def get_blueprint(self, blueprint_id: str) -> Optional[Dict]:
        """Get blueprint by ID"""
        for bp in self.blueprints.get("bot_blueprints", []):
            if bp["id"] == blueprint_id:
                return bp.copy()
        return None
    
    def spawn_entity(self, blueprint_id: str, x: int, y: int) -> Optional[Dict]:
        """
        Spawn entity from blueprint at position
        
        Returns entity dict with unique ID
        """
        blueprint = self.get_blueprint(blueprint_id)
        if not blueprint:
            logger.error(f"Blueprint not found: {blueprint_id}")
            return None
        
        # Create entity instance with unique ID
        entity = {
            "id": str(uuid.uuid4()),  # Unique ID
            "blueprint_id": blueprint_id,
            "name": blueprint["name"],
            "icon": blueprint["icon"],
            "x": x,
            "y": y,
            "faction": blueprint["faction"],
            "type": blueprint["type"],
            "behavior": blueprint["behavior"],
            "combat_type": blueprint["combat_type"],
            "vision_radius": blueprint["vision_radius"],
            "health": blueprint["health"],
            "max_health": blueprint["health"],
            "power": blueprint["power"],
            "speed": blueprint["speed"],
            "is_aggressive": blueprint["is_aggressive"],
            "drop_resource": blueprint.get("drop_resource"),
            "is_alive": True,
            "current_action": "idle",
            "target": None,
            "spawn_day": 0  # Will be set by game engine
        }
        
        self.entities.append(entity)
        logger.info(f"[ENTITY] Spawned {blueprint['name']} at ({x}, {y}) - ID: {entity['id'][:8]}")
        
        return entity
    
    def remove_entity(self, entity_id: str) -> Optional[Dict]:
        """Remove entity and return drops"""
        entity = self.get_entity(entity_id)
        if not entity:
            return None
        
        # Get drop before removing
        drops = None
        if entity.get("drop_resource"):
            drop_config = entity["drop_resource"]
            amount = random.randint(
                drop_config.get("amount_min", 1),
                drop_config.get("amount_max", 1)
            )
            drops = {
                "resource": drop_config["type"],
                "amount": amount,
                "x": entity["x"],
                "y": entity["y"]
            }
        
        # Remove from list
        self.entities = [e for e in self.entities if e["id"] != entity_id]
        
        logger.info(f"[ENTITY] Removed {entity['name']} - Drops: {drops}")
        
        return drops
    
    def get_entity(self, entity_id: str) -> Optional[Dict]:
        """Get entity by ID"""
        for entity in self.entities:
            if entity["id"] == entity_id:
                return entity
        return None
    
    def get_entities_in_radius(self, x: int, y: int, radius: int) -> List[Dict]:
        """Get all entities within radius of position"""
        nearby = []
        for entity in self.entities:
            if not entity.get("is_alive", True):
                continue
            
            distance = abs(entity["x"] - x) + abs(entity["y"] - y)
            if distance <= radius:
                nearby.append(entity)
        
        return nearby
    
    def update_entity_ai(self, entity: Dict, player_pos: Tuple[int, int], game_time: Dict) -> Dict:
        """
        Update entity AI behavior
        
        Returns: {
            "action": "move" | "attack" | "flee" | "idle",
            "target": (x, y) or entity_id,
            "new_position": (x, y)
        }
        """
        ex, ey = entity["x"], entity["y"]
        px, py = player_pos
        distance_to_player = abs(ex - px) + abs(ey - py)
        
        # Check if player is in vision range
        in_vision = distance_to_player <= entity["vision_radius"]
        
        # Aggressive behavior
        if entity["is_aggressive"] and in_vision:
            if distance_to_player <= 1:
                # Adjacent → attack!
                return {
                    "action": "attack",
                    "target": "player",
                    "new_position": (ex, ey)
                }
            else:
                # Move towards player
                dx = 1 if px > ex else (-1 if px < ex else 0)
                dy = 1 if py > ey else (-1 if py < ey else 0)
                
                return {
                    "action": "move",
                    "target": player_pos,
                    "new_position": (ex + dx, ey + dy)
                }
        
        # Passive behavior
        elif not entity["is_aggressive"] and in_vision:
            # Flee from player
            dx = -1 if px > ex else (1 if px < ex else 0)
            dy = -1 if py > ey else (1 if py < ey else 0)
            
            return {
                "action": "flee",
                "target": None,
                "new_position": (ex + dx, ey + dy)
            }
        
        # No player nearby → wander
        else:
            # Random movement (10% chance)
            if random.random() < 0.1:
                dx = random.choice([-1, 0, 1])
                dy = random.choice([-1, 0, 1])
                return {
                    "action": "wander",
                    "target": None,
                    "new_position": (ex + dx, ey + dy)
                }
            else:
                return {
                    "action": "idle",
                    "target": None,
                    "new_position": (ex, ey)
                }
    
    def damage_entity(self, entity_id: str, damage: int) -> Dict:
        """
        Deal damage to entity
        
        Returns: {
            "is_alive": bool,
            "current_health": int,
            "drops": {...} or None
        }
        """
        entity = self.get_entity(entity_id)
        if not entity:
            return {"is_alive": False, "current_health": 0, "drops": None}
        
        entity["health"] = max(0, entity["health"] - damage)
        
        if entity["health"] <= 0:
            entity["is_alive"] = False
            drops = self.remove_entity(entity_id)
            
            return {
                "is_alive": False,
                "current_health": 0,
                "drops": drops
            }
        
        return {
            "is_alive": True,
            "current_health": entity["health"],
            "drops": None
        }
    
    def get_all_entities(self) -> List[Dict]:
        """Get all active entities"""
        return [e for e in self.entities if e.get("is_alive", True)]
    
    def get_entity_count_by_type(self, blueprint_id: str) -> int:
        """Count entities of specific type"""
        return sum(1 for e in self.entities if e["blueprint_id"] == blueprint_id and e.get("is_alive", True))

# ============= TESTING =============

if __name__ == "__main__":
    print("=== ENTITY MANAGER TEST ===\n")
    
    manager = EntityManager()
    
    # Spawn some entities
    rabbit = manager.spawn_entity("rabbit", 10, 10)
    wolf = manager.spawn_entity("wolf", 15, 15)
    
    print(f"Spawned: {rabbit['name']} (ID: {rabbit['id'][:8]})")
    print(f"Spawned: {wolf['name']} (ID: {wolf['id'][:8]})")
    
    # Test AI
    ai_decision = manager.update_entity_ai(wolf, (12, 12), {"day": 1})
    print(f"\nWolf AI Decision: {ai_decision}")
    
    # Test damage
    result = manager.damage_entity(rabbit["id"], 10)
    print(f"\nRabbit damaged: {result}")
    
    print(f"\nActive entities: {len(manager.get_all_entities())}")
