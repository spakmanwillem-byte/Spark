import random
import json
import os
import csv
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime, timedelta
import heapq  # For A* pathfinding priority queue

# Knowledge integration
from services.knowledge_game_service import (
    can_collect_resource, 
    get_unlocked_buildings,
    check_knowledge_for_concept
)

# NIEUW: Combat Engine
from services.combat_engine import (
    CombatEngine, 
    ACTION_ATTACK, ACTION_DEFEND, ACTION_PASSIEF,
    STANCE_ATTACK, STANCE_DEFEND, STANCE_PASSIEF
)

# NIEUW: Entity Manager (Bot System)
from services.entity_manager import EntityManager

logger = logging.getLogger(__name__)

# Game configuration
GRID_SIZE = 200  # UPGRADED: 200x200 wereld (4x groter voor Anno-stijl gameplay)
UPDATE_INTERVAL = 5  # seconds between updates

# ECONOMY CONFIGURATION
SPARK_INVENTORY_MAX = 50  # Max resources Spark can carry
MONUMENT_BUFFER_WOOD = 20  # Always keep this much wood
MONUMENT_BUFFER_STONE = 20  # Always keep this much stone
MONUMENT_STORAGE_THRESHOLD = 0.5  # Only contribute if storage > 50% full

# TIME SCALE CONFIGURATION
# Target: 1 ingame day = 10-20 minutes real time
# With 5-second updates: 120-240 updates per day
# Solution: 1440 minutes/day ÷ 120 updates = 12 min/update (fast)
#           1440 minutes/day ÷ 240 updates = 6 min/update (slow)
TIME_SCALE_MINUTES_PER_UPDATE = 5  # 1 update = 5 minuten game time (~1 dag per uur realtime)
MINUTES_PER_DAY = 1440  # Standard 24-hour day

SAVE_FILE = "/app/backend/data/world_save.json"

# Directions for movement
DIRECTIONS = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # right, down, left, up

# Items
ITEMS = {
    "fishing_rod": {"name": "Hengel", "icon": "🎣", "type": "tool"},
    "water_bottle": {"name": "Waterfles", "icon": "🍶", "type": "consumable"},
    "fish": {"name": "Vis", "icon": "🐟", "type": "food"},
    "grain": {"name": "Graan", "icon": "🌾", "type": "resource"},
    "flour": {"name": "Meel", "icon": "🥖", "type": "resource"},
    "bread": {"name": "Brood", "icon": "🍞", "type": "food"},
    "plank": {"name": "Plank", "icon": "🪵", "type": "material"}
}

# Placeable items (voor building)
PLACEABLE_ITEMS = {
    "tree": {"name": "Boom", "icon": "🌳", "type": "resource", "cost": 0},
    "stone": {"name": "Steen", "icon": "🪨", "type": "resource", "cost": 0},
    "water": {"name": "Water", "icon": "💧", "type": "terrain", "cost": 0},
    "wooden_bridge": {"name": "Houten Brug", "icon": "🌉", "type": "bridge", "cost": {"wood": 2}, "walkable": True},
    "stone_bridge": {"name": "Stenen Brug", "icon": "🌉", "type": "bridge", "cost": {"wood": 1, "stone": 2}, "walkable": True},
    "house": {"name": "Huis", "icon": "🏠", "type": "building", "cost": {"wood": 2, "stone": 2}, "storage_capacity": 50},
    "warehouse": {"name": "Warehouse", "icon": "🏭", "type": "building", "cost": {"wood": 10, "stone": 10}, "storage_capacity": 1000},
    "workshop": {"name": "Workshop", "icon": "🔧", "type": "profession", "cost": {"wood": 5, "stone": 2}, "workers": 1, "storage_capacity": 100, "process": {"input": "wood", "output": "water_bottle", "rate": 1}},
    "wall": {"name": "Muur", "icon": "🧱", "type": "defensive", "cost": {"stone": 2}, "health": 500, "max_health": 500, "blocks_enemy": True},
    "gate": {"name": "Poort", "icon": "🚪", "type": "defensive", "cost": {"wood": 3, "stone": 1}, "health": 300, "max_health": 300, "walkable_ally": True},
    "farm": {"name": "Boerderij", "icon": "🌾", "type": "building", "cost": {"wood": 5, "stone": 3}},
    "lumberjack": {"name": "Houthakker", "icon": "🪓", "type": "profession", "cost": {"wood": 10}, "workers": 1, "storage_capacity": 100},
    "planter": {"name": "Planter", "icon": "🌱", "type": "profession", "cost": {"wood": 10}, "workers": 1, "max_trees": 10, "plant_rate": 1},
    "miner": {"name": "Miner", "icon": "⛏️", "type": "profession", "cost": {"stone": 10}, "workers": 1, "storage_capacity": 100},
    "fisher": {"name": "Visser", "icon": "🎣", "type": "profession", "cost": {"wood": 5}, "workers": 1, "requires": "water", "storage_capacity": 100},
    "farmer": {"name": "Boer", "icon": "👨‍🌾", "type": "profession", "cost": {"wood": 8}, "workers": 1, "max_cropfields": 10, "storage_capacity": 100},
    "runner": {"name": "Loopjongen", "icon": "🏃", "type": "profession", "cost": {"wood": 3}, "workers": 1, "carry_capacity": 20},
    "miller": {"name": "Molenaar", "icon": "🌾", "type": "profession", "cost": {"wood": 15, "stone": 5}, "workers": 1, "storage_capacity": 100, "process": {"input": "grain", "output": "flour", "rate": 2, "water": 2}},
    "baker": {"name": "Bakker", "icon": "🍞", "type": "profession", "cost": {"wood": 12, "stone": 8}, "workers": 1, "storage_capacity": 100, "process": {"input": "flour", "output": "bread", "rate": 1, "water": 1}},
    "sawmill": {"name": "Houtzagerij", "icon": "🪚", "type": "profession", "cost": {"wood": 20, "stone": 10}, "workers": 1, "storage_capacity": 100, "process": {"input": "wood", "output": "plank", "rate": 1}},
    "well": {"name": "Waterput", "icon": "💧", "type": "building", "cost": {"stone": 5}, "production": "water"},
    "cropfield": {"name": "Akkerveld", "icon": "🌾", "type": "terrain", "cost": {"wood": 2}, "walkable": True, "speed_penalty": 0.1},
    "mine": {"name": "Mine", "icon": "🕳️", "type": "building", "cost": {"stone": 20}, "requires": "mountain"},
    "barracks": {"name": "Barracks", "icon": "⚔️", "type": "military", "cost": {"wood": 50, "stone": 30}, "train_capacity": 5, "can_train": ["soldier"]},
    "tower": {"name": "Tower", "icon": "🗼", "type": "defensive", "cost": {"wood": 30, "stone": 40}, "attack_range": 10, "damage": 15, "health": 200, "max_health": 200}
}

# Growth stages
TREE_GROWTH_STAGES = {
    "seedling": {"icon": "🌱", "days": 2, "harvestable": False},
    "young": {"icon": "🌳", "days": 2, "harvestable": False},
    "mature": {"icon": "🌲", "days": 999, "harvestable": True, "wood_amount": 3}
}

CROP_GROWTH_STAGES = {
    "planted": {"icon": "🟫", "days": 1, "harvestable": False},
    "growing": {"icon": "🌱", "days": 2, "harvestable": False},
    "harvestable": {"icon": "🌾", "days": 999, "harvestable": True, "food_amount": 1}
}

class GameEngine:
    """
    Spark AI Mini Survival Game - Fase 2 (Simpel)
    
    Features:
    - 20x20 grid wereld
    - Spark entiteit die automatisch beweegt
    - Resources: bomen (hout) en stenen
    - Monument in het midden (doel: 1000 hout + 1000 steen)
    - Basis behoeften: eten en drinken
    - Tijd systeem: 1 uur = 1 dag
    - Dag/nacht cyclus (visueel)
    """
    
    def __init__(self):
        self.grid_size = GRID_SIZE
        
        # Try to load saved world first
        if self._load_world():
            logger.info("[GAME] Loaded saved world from file!")
            
            # BUGFIX: Check if koning bots exist, if not spawn them
            entities = self.entity_manager.get_all_entities()
            kings = [e for e in entities if e.get('type') == 'king']
            if len(kings) == 0:
                logger.warning("[GAME] No koning bots in save, spawning them...")
                for king_type, x, y in [("king_gaia", 50, 150), ("king_neptune", 150, 150), ("king_vulcan", 150, 50), ("king_zephyr", 50, 50)]:
                    try:
                        self.entity_manager.spawn_entity(king_type, x, y)
                        logger.info(f"[GAME] ✅ Spawned {king_type}")
                    except: pass
            return
        
        # Otherwise generate new world
        logger.info("[GAME] Generating new world...")
        self._initialize_new_world()
    
    def _initialize_new_world(self):
        """Initialize a brand new world"""
        self.start_time = datetime.now()
        self.is_paused = False  # START RUNNING (active world)
        
        # Time system FIRST (needed by _update_exploration)
        self.game_time = {
            "day": 1,
            "hour": 6,
            "minute": 0,
            "time_of_day": 6.0,  # 0-24 hours
            "is_day": True,  # Day or night
            "minutes_elapsed": 0,
            "minutes_per_update": TIME_SCALE_MINUTES_PER_UPDATE  # Configureerbare time scale
        }
        
        # Spark's build plan (auto-build progression)
        self.build_plan = {
            "house_built": False,
            "storage_built": False,
            "monument_contributing": False
        }
        
        # Spark entiteit
        self.spark = {
            "x": GRID_SIZE // 2,
            "y": GRID_SIZE // 2,
            "inventory": {
                "wood": 0,   # START MET 0 - krijgt starter box
                "stone": 0,  # START MET 0 - krijgt starter box
                "fish": 0,   # START MET 0 - krijgt starter box
                "water_bottle": 0
            },
            "items": ["fishing_rod"],
            "direction": "right",
            "hunger": 100,
            "thirst": 100,
            "energy": 100,
            "is_sleeping": False,
            "health": 500,  # UPGRADED: Spark special (was 100)
            "max_health": 500,
            "attack": 20,  # NIEUW: Combat damage
            "defense": 10,  # NIEUW: Damage reduction
            "faction": "spark",  # NIEUW: Faction identifier
            "is_fleeing": False,
            "vision_radius": 6,
            "current_action": "idle",
            "action_target": None,
            "action_progress": 0,
            "resource_memory": {
                "wood": [],
                "stone": [],
                "water": []
            }
        }
        
        # NIEUW: STARTER BOX (1-time resource boost)
        self.starter_box = {
            "x": GRID_SIZE // 2,
            "y": GRID_SIZE // 2,
            "contents": {
                "wood": 50,
                "stone": 50,
                "fish": 10  # food
            },
            "is_active": True,
            "icon": "📦"
        }
        
        # Danger memory - Spark leert gevaarlijke locaties
        self.danger_memory = []  # [{x, y, timestamp, type: "danger"}]
        
        # Explored tiles (fog of war) - initialize empty, update AFTER resources are generated
        self.explored_tiles = set()
        
        # NIEUW: FRACTIE RELATIE SYSTEEM
        self.faction_relations = {
            "spark": {
                "terra": "neutral",    # friend, neutral, enemy
                "aqua": "neutral",
                "ignis": "neutral",
                "ventus": "neutral"
            },
            "terra": {
                "spark": "neutral",
                "aqua": "neutral",
                "ignis": "neutral",
                "ventus": "neutral"
            },
            "aqua": {
                "spark": "neutral",
                "terra": "neutral",
                "ignis": "neutral",
                "ventus": "neutral"
            },
            "ignis": {
                "spark": "neutral",
                "terra": "neutral",
                "aqua": "neutral",
                "ventus": "neutral"
            },
            "ventus": {
                "spark": "neutral",
                "terra": "neutral",
                "aqua": "neutral",
                "ignis": "neutral"
            }
        }
        
        # NIEUW: FRACTIE ENCOUNTER MEMORY
        # Spark onthoudt waar hij welke fractie is tegengekomen
        self.faction_encounters = []  # [{"x": x, "y": y, "faction": "terra", "type": "building", "day": day}, ...]
        
        # NIEUW: COMBAT SYSTEM
        self.combat_history = []  # Geschiedenis van gevechten
        self.active_combats = []  # Actieve gevechten
        
        # Initialize resources - LOAD FROM CSV MAP
        csv_path = "/app/backend/data/emergent_map_200x200.csv"
        if os.path.exists(csv_path):
            logger.info(f"[WORLD] Loading map from CSV: {csv_path}")
            self.trees, self.stones, self.water_tiles = self._load_map_from_csv(csv_path)
        else:
            logger.warning(f"[WORLD] CSV not found, using procedural generation")
            self.trees = self._generate_trees(count=1000)
            self.stones = self._generate_stones(count=320)
            self.water_tiles = self._generate_rivers(num_rivers=5)
        
        self.stumps = []  # NEW: Tree stumps after chopping
        
        # NO MOUNTAINS OR RIVERS from CSV - use your custom map design!
        self.mountains = []  # Empty - your CSV has no mountains
        # water_tiles already loaded from CSV (if any)
        
        # NIEUW: BUILD PHASE SYSTEM
        self.build_phases = {
            "current_phase": "phase_1_basics",
            "phase_1_basics": {
                "required": ["warehouse"],  # Put is optional, warehouse is must
                "completed": False
            },
            "phase_2_producers": {
                "required": ["planter", "lumberjack"],
                "warehouse_threshold": 50,  # Need 50% warehouse fill
                "completed": False
            },
            "phase_3_mining": {
                "required": ["miner"],  # On mountain
                "warehouse_threshold": 50,
                "completed": False
            },
            "phase_4_advanced": {
                "required": ["sawmill", "mill"],
                "warehouse_threshold": 75,
                "completed": False
            }
        }
        
        # NIEUW: BOT/ENTITY SYSTEM
        self.entity_manager = EntityManager()
        self.worker_bots = []  # Active worker bots (warehouse runners, etc.)
        logger.info("[GAME] Entity Manager initialized")
        
        # Player placed items
        self.placed_items = []
        self.cropfields = []
        self.managed_trees = []
        
        # Bewoners (residents/workers)
        self.residents = []
        
        # Production tracking
        self.workhouses = {}
        self.wells = []
        
        # Stats (needed by save function)
        self.stats = {
            "updates": 0,
            "wood_collected": 0,
            "stone_collected": 0,
            "distance_traveled": 0,
            "monument_contributions": 0,
            "steps_since_save": 0
        }
        
        # NOW safe to update exploration (after ALL dependencies exist)
        self._update_exploration()  # Initial exploration
        
        # Monumenten (5 stuks) - ZELFDE SIZE ALS HUIS (1 tile)
        center = GRID_SIZE // 2
        edge_offset = 8
        
        self.monuments = [
            {
                "id": "spark_core",
                "name": "Spark Core",
                "faction_id": None,
                "x": center,  # MIDDEN (1 tile)
                "y": center,
                "size": 1,  # ZELFDE ALS HUIS
                "color": "#FFD700",
                "icon": "⚡",
                "wood_contributed": 0,
                "stone_contributed": 0,
                "plank_contributed": 0,  # NEW: Planks needed
                "wood_needed": 10,  # VERLAAGD: was 1000
                "stone_needed": 10,  # VERLAAGD: was 1000
                "plank_needed": 5,  # VERLAAGD: was 500
                "progress": 0.0
            },
            {
                "id": "terra_monument",
                "name": "Terra Monument",
                "faction_id": "earth_builders",
                "x": edge_offset,
                "y": edge_offset,
                "size": 1,  # ZELFDE ALS HUIS
                "color": "#8B4513",
                "icon": "🌍",
                "wood_contributed": 0,
                "stone_contributed": 0,
                "plank_contributed": 0,
                "wood_needed": 10,  # VERLAAGD: was 1000
                "stone_needed": 10,  # VERLAAGD: was 1000
                "plank_needed": 5,  # VERLAAGD: was 500
                "progress": 0.0
            },
            {
                "id": "aqua_monument",
                "name": "Aqua Monument",
                "faction_id": "water_traders",
                "x": GRID_SIZE - edge_offset - 1,  # -1 voor 1 tile
                "y": edge_offset,
                "size": 1,  # ZELFDE ALS HUIS
                "color": "#2196F3",
                "icon": "💧",
                "wood_contributed": 0,
                "stone_contributed": 0,
                "plank_contributed": 0,
                "wood_needed": 10,  # VERLAAGD: was 1000
                "stone_needed": 10,  # VERLAAGD: was 1000
                "plank_needed": 5,  # VERLAAGD: was 500
                "progress": 0.0
            },
            {
                "id": "ignis_monument",
                "name": "Ignis Monument",
                "faction_id": "fire_crafters",
                "x": edge_offset,
                "y": GRID_SIZE - edge_offset - 1,  # -1 voor 1 tile
                "size": 1,  # ZELFDE ALS HUIS
                "color": "#F44336",
                "icon": "🔥",
                "wood_contributed": 0,
                "stone_contributed": 0,
                "plank_contributed": 0,
                "wood_needed": 10,  # VERLAAGD: was 1000
                "stone_needed": 10,  # VERLAAGD: was 1000
                "plank_needed": 5,  # VERLAAGD: was 500
                "progress": 0.0
            },
            {
                "id": "ventus_monument",
                "name": "Ventus Monument",
                "faction_id": "air_explorers",
                "x": GRID_SIZE - edge_offset - 1,  # -1 voor 1 tile
                "y": GRID_SIZE - edge_offset - 1,  # -1 voor 1 tile
                "size": 1,  # ZELFDE ALS HUIS
                "color": "#9E9E9E",
                "icon": "💨",
                "wood_contributed": 0,
                "stone_contributed": 0,
                "plank_contributed": 0,
                "wood_needed": 10,  # VERLAAGD: was 1000
                "stone_needed": 10,  # VERLAAGD: was 1000
                "plank_needed": 5,  # VERLAAGD: was 500
                "progress": 0.0
            }
        ]
        
        logger.info(f"[GAME] New world generated - Grid: {GRID_SIZE}x{GRID_SIZE}")
        
        # AUTO-SPAWN KONING BOTS bij nieuwe wereld (safe positions - geen bergen/water)
        logger.info("[GAME] Spawning koning bots...")
        try:
            # Find safe spawn positions (no mountains/water)
            def find_safe_pos(target_x, target_y, search_radius=10):
                for offset in range(search_radius):
                    for dx, dy in [(0,0), (offset,0), (-offset,0), (0,offset), (0,-offset)]:
                        test_x, test_y = target_x + dx, target_y + dy
                        if 0 <= test_x < GRID_SIZE and 0 <= test_y < GRID_SIZE:
                            # Check no mountain
                            if not any(m['x'] == test_x and m['y'] == test_y for m in self.mountains):
                                # Check no water
                                if not self._is_water(test_x, test_y):
                                    return (test_x, test_y)
                return (target_x, target_y)  # Fallback
            
            # Spawn 4 koning bots op veilige posities
            koning_targets = [
                ("king_gaia", 50, 150),      # SW - Terra
                ("king_neptune", 150, 150),  # SE - Aqua
                ("king_vulcan", 150, 50),    # NE - Ignis
                ("king_zephyr", 50, 50)      # NW - Ventus
            ]
            
            for king_type, target_x, target_y in koning_targets:
                safe_x, safe_y = find_safe_pos(target_x, target_y)
                self.entity_manager.spawn_entity(king_type, safe_x, safe_y)
                logger.info(f"[GAME] ✅ Spawned {king_type} at ({safe_x}, {safe_y})")
        except Exception as e:
            logger.error(f"[GAME] ❌ Error spawning koning bots: {e}")
        
        self._save_world()  # Save initial state
        
        logger.info(f"[GAME] Game initialized - Grid: {GRID_SIZE}x{GRID_SIZE}, Trees: {len(self.trees)}, Mountains: {len(self.mountains)}, Water: {len(self.water_tiles)} tiles")
    
    def _load_map_from_csv(self, csv_path: str) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """
        Load map from CSV file
        Returns: (trees, stones, water_tiles)
        
        CSV Format:
        - 0 = grass (gras)
        - 1 = water (water)
        - 2 = mountain (berg) - stored in self.mountains directly
        - 3 = tree (boom)
        """
        trees = []
        stones = []
        water_tiles = []
        mountains = []
        
        logger.info(f"[MAP LOADER] Reading CSV from: {csv_path}")
        
        try:
            with open(csv_path, 'r') as f:
                reader = csv.reader(f)
                grid_data = list(reader)
            
            # Validate grid size
            if len(grid_data) != self.grid_size:
                logger.warning(f"[MAP LOADER] CSV rows ({len(grid_data)}) != grid_size ({self.grid_size})")
            
            # Parse CSV and extract resources
            tree_count = 0
            water_count = 0
            mountain_count = 0
            grass_tiles = []  # We'll place stones on these
            
            for y, row in enumerate(grid_data):
                if len(row) != self.grid_size:
                    logger.warning(f"[MAP LOADER] Row {y} has {len(row)} columns (expected {self.grid_size})")
                    continue
                
                for x, cell_value in enumerate(row):
                    cell_type = int(cell_value.strip())
                    
                    if cell_type == 3:  # Tree
                        trees.append({
                            "id": f"tree_{tree_count}",
                            "x": x,
                            "y": y,
                            "wood_amount": random.randint(1, 3),
                            "type": "tree",
                            "stage": "mature",
                            "planted_day": 0
                        })
                        tree_count += 1
                    elif cell_type == 1:  # Water
                        water_tiles.append({"x": x, "y": y})
                        water_count += 1
                    elif cell_type == 2:  # Mountain
                        mountains.append({
                            "id": f"mountain_{mountain_count}",
                            "x": x,
                            "y": y,
                            "type": "mountain"
                        })
                        mountain_count += 1
                    elif cell_type == 0:  # Grass - candidate for stone placement
                        grass_tiles.append((x, y))
            
            # Add stones randomly to grass tiles (~400 stones = 1% of grass)
            num_stones = min(400, len(grass_tiles) // 100)
            if len(grass_tiles) > 0:
                stone_positions = random.sample(grass_tiles, min(num_stones, len(grass_tiles)))
                
                for idx, (x, y) in enumerate(stone_positions):
                    stones.append({
                        "id": f"stone_{idx}",
                        "x": x,
                        "y": y,
                        "stone_amount": random.randint(1, 3),
                        "type": "stone"
                    })
            
            # Store mountains in self (side effect, but needed)
            self.mountains = mountains
            
            logger.info(f"[MAP LOADER] ✅ Loaded {len(trees)} trees from CSV")
            logger.info(f"[MAP LOADER] ✅ Loaded {len(water_tiles)} water tiles from CSV")
            logger.info(f"[MAP LOADER] ✅ Loaded {len(mountains)} mountains from CSV")
            logger.info(f"[MAP LOADER] ✅ Added {len(stones)} random stones to map")
            logger.info(f"[MAP LOADER] ✅ Map size: {len(grid_data)}x{len(grid_data[0])}")
            
        except Exception as e:
            logger.error(f"[MAP LOADER] ❌ Error loading CSV: {e}")
            # Fallback to empty lists
            logger.warning("[MAP LOADER] Using empty map as fallback")
        
        return trees, stones, water_tiles
    
    def _generate_trees(self, count: int = 120) -> List[Dict]:  # Was 5 (!!) → Nu 120
        """Generate random tree positions - VEEL MEER voor groen landschap"""
        trees = []
        center_x, center_y = self.grid_size // 2, self.grid_size // 2
        
        for i in range(count):
            # Try to find good spot (max 10 attempts to avoid infinite loop)
            for attempt in range(10):
                x = random.randint(1, self.grid_size - 2)
                y = random.randint(1, self.grid_size - 2)
                
                # Not on center (where Spark starts)
                if not (x == center_x and y == center_y):
                    # Not too close to other trees (min 2 tiles spacing)
                    if not any(abs(t["x"] - x) < 2 and abs(t["y"] - y) < 2 for t in trees):
                        break
            
            trees.append({
                "id": f"tree_{i}",
                "x": x,
                "y": y,
                "wood_amount": random.randint(1, 3),
                "type": "tree",
                "stage": "mature",
                "planted_day": 0
            })
        
        return trees

    def _generate_mountain_ranges(self, num_ranges: int = 5) -> List[Dict]:
        """Generate mountain RANGES (ketens) instead of random mountains"""
        mountains = []
        center_x, center_y = self.grid_size // 2, self.grid_size // 2
        
        for range_id in range(num_ranges):
            # Random start position (not in center)
            start_x = random.randint(10, self.grid_size - 10)
            start_y = random.randint(10, self.grid_size - 10)
            
            # Avoid center
            while abs(start_x - center_x) < 30 and abs(start_y - center_y) < 30:
                start_x = random.randint(10, self.grid_size - 10)
                start_y = random.randint(10, self.grid_size - 10)
            
            # Generate a chain of mountains (20-40 mountains per range)
            range_length = random.randint(20, 40)
            direction_x = random.choice([-1, 0, 1])
            direction_y = random.choice([-1, 0, 1])
            
            current_x, current_y = start_x, start_y
            
            for i in range(range_length):
                mountains.append({
                    "id": f"mountain_range{range_id}_{i}",
                    "x": current_x,
                    "y": current_y,
                    "type": "mountain",
                    "range_id": range_id
                })
                
                # Move in general direction with some randomness
                current_x += direction_x + random.choice([-1, 0, 1])
                current_y += direction_y + random.choice([-1, 0, 1])
                
                # Keep within bounds
                current_x = max(5, min(self.grid_size - 5, current_x))
                current_y = max(5, min(self.grid_size - 5, current_y))
                
                # Sometimes change direction slightly
                if random.random() < 0.2:
                    direction_x = random.choice([-1, 0, 1])
                    direction_y = random.choice([-1, 0, 1])
        
        logger.info(f"[WORLD] Generated {num_ranges} mountain ranges with {len(mountains)} total mountains")
        return mountains
    
    def _generate_rivers(self, num_rivers: int = 3) -> List[Dict]:
        """Generate RIVERS (water stromen) instead of random lakes"""
        water_tiles = []
        
        for river_id in range(num_rivers):
            # Rivers start from one edge and flow to another
            if random.random() < 0.5:
                # Horizontal river
                start_y = random.randint(20, self.grid_size - 20)
                current_x, current_y = 0, start_y
                target_x = self.grid_size - 1
                
                while current_x < target_x:
                    # Add water tiles (3-5 tiles wide)
                    width = random.randint(3, 5)
                    for w in range(width):
                        water_tiles.append({
                            "x": current_x,
                            "y": current_y + w - width // 2,
                            "type": "river",
                            "river_id": river_id
                        })
                    
                    # Move forward with slight meandering
                    current_x += 1
                    current_y += random.choice([-1, 0, 0, 0, 1])  # Mostly straight
                    current_y = max(5, min(self.grid_size - 5, current_y))
            else:
                # Vertical river
                start_x = random.randint(20, self.grid_size - 20)
                current_x, current_y = start_x, 0
                target_y = self.grid_size - 1
                
                while current_y < target_y:
                    # Add water tiles (3-5 tiles wide)
                    width = random.randint(3, 5)
                    for w in range(width):
                        water_tiles.append({
                            "x": current_x + w - width // 2,
                            "y": current_y,
                            "type": "river",
                            "river_id": river_id
                        })
                    
                    # Move forward with slight meandering
                    current_y += 1
                    current_x += random.choice([-1, 0, 0, 0, 1])
                    current_x = max(5, min(self.grid_size - 5, current_x))
        
        logger.info(f"[WORLD] Generated {num_rivers} rivers with {len(water_tiles)} water tiles")
        return water_tiles
    
    def _save_world(self):
        """Save complete world state to file"""
        try:
            state = {
                "grid_size": self.grid_size,
                "spark": self.spark,
                "explored_tiles": list(self.explored_tiles),
                "trees": self.trees,
                "stumps": self.stumps,
                "stones": self.stones,
                "mountains": self.mountains,
                "water_tiles": self.water_tiles,
                "monuments": self.monuments,
                "placed_items": self.placed_items,
                "cropfields": self.cropfields,
                "managed_trees": self.managed_trees,
                "residents": self.residents,
                "workhouses": self.workhouses,
                "wells": self.wells,
                "game_time": self.game_time,
                "stats": self.stats,
                "is_paused": getattr(self, 'is_paused', True),
                "build_plan": getattr(self, 'build_plan', {"house_built": False, "storage_built": False, "monument_contributing": False}),
                "danger_memory": getattr(self, 'danger_memory', []),
                "faction_relations": getattr(self, 'faction_relations', {}),  # NIEUW: Save fractie relaties
                "faction_encounters": getattr(self, 'faction_encounters', []),  # NIEUW: Save fractie encounters
                "combat_history": getattr(self, 'combat_history', []),  # NIEUW: Save combat history
                "starter_box": getattr(self, 'starter_box', {"is_active": False, "contents": {}}),  # Save starter box state
                "build_phases": getattr(self, 'build_phases', {}),  # Save build phases
                "worker_bots": getattr(self, 'worker_bots', []),  # NIEUW: Save worker bots
                "saved_at": datetime.now().isoformat()
            }
            
            os.makedirs(os.path.dirname(SAVE_FILE), exist_ok=True)
            with open(SAVE_FILE, 'w') as f:
                json.dump(state, f, indent=2)
            
            logger.info(f"[SAVE] World saved! Steps: {self.stats.get('distance_traveled', 0)}")
            return True
        except Exception as e:
            logger.error(f"[SAVE] Failed to save world: {e}")
            return False
    
    def _load_world(self) -> bool:
        """Load world state from file"""
        try:
            if not os.path.exists(SAVE_FILE):
                logger.info("[LOAD] No save file found, will generate new world")
                return False
            
            with open(SAVE_FILE, 'r') as f:
                content = f.read().strip()
                # Safety check: if file is empty or corrupt, regenerate
                if not content:
                    logger.warning("[LOAD] Save file is empty, will generate new world")
                    return False
                state = json.loads(content)
            
            # Restore all state
            self.grid_size = state["grid_size"]
            self.spark = state["spark"]
            self.explored_tiles = set(tuple(t) for t in state["explored_tiles"])
            self.trees = state["trees"]
            self.stumps = state.get("stumps", [])  # NEW: Load stumps
            self.stones = state["stones"]
            self.mountains = state["mountains"]
            self.water_tiles = state["water_tiles"]
            self.monuments = state["monuments"]
            self.placed_items = state["placed_items"]
            self.cropfields = state["cropfields"]
            self.managed_trees = state.get("managed_trees", [])
            self.residents = state.get("residents", [])
            self.workhouses = state.get("workhouses", {})
            self.wells = state.get("wells", [])
            self.game_time = state["game_time"]
            self.stats = state["stats"]
            self.is_paused = state.get("is_paused", False)
            self.build_plan = state.get("build_plan", {"house_built": False, "storage_built": False, "monument_contributing": False})
            self.danger_memory = state.get("danger_memory", [])
            self.faction_relations = state.get("faction_relations", {})  # NIEUW: Load fractie relaties
            self.faction_encounters = state.get("faction_encounters", [])  # NIEUW: Load fractie encounters
            self.combat_history = state.get("combat_history", [])  # NIEUW: Load combat history
            self.start_time = datetime.now()  # Reset start time on load
            
            # CRITICAL: Load starter_box (if missing, set as inactive/collected)
            self.starter_box = state.get("starter_box", {
                "x": GRID_SIZE // 2,
                "y": GRID_SIZE // 2,
                "contents": {},
                "is_active": False,  # Already collected if not in save
                "icon": "📦"
            })
            
            # CRITICAL: Load build_phases (initialize defaults if missing)
            self.build_phases = state.get("build_phases", {
                "current_phase": "phase_1_basics",
                "phase_1_basics": {"required": ["warehouse"], "completed": False},
                "phase_2_producers": {"required": ["planter", "lumberjack"], "warehouse_threshold": 50, "completed": False},
                "phase_3_mining": {"required": ["miner"], "warehouse_threshold": 50, "completed": False},
                "phase_4_advanced": {"required": ["sawmill", "mill"], "warehouse_threshold": 75, "completed": False}
            })
            
            # NIEUW: BOT/ENTITY SYSTEM (initialize even if not in save)
            self.entity_manager = EntityManager()
            self.worker_bots = state.get("worker_bots", [])
            logger.info(f"[LOAD] Loaded {len(self.worker_bots)} worker bots")
            
            logger.info(f"[LOAD] World loaded! Day {self.game_time['day']}, Spark at ({self.spark['x']}, {self.spark['y']})")
            return True
        except json.JSONDecodeError as e:
            logger.error(f"[LOAD] Corrupt save file (JSONDecodeError): {e}. Will generate new world")
            return False
        except Exception as e:
            logger.error(f"[LOAD] Failed to load world: {e}", exc_info=True)
            return False
    
    def _generate_stones(self, count: int = 5) -> List[Dict]:
        """Generate random stone positions on the grid"""
        stones = []
        center_x, center_y = self.grid_size // 2, self.grid_size // 2
        
        for i in range(count):
            while True:
                x = random.randint(1, self.grid_size - 2)
                y = random.randint(1, self.grid_size - 2)
                
                # Not on center
                if not (x == center_x and y == center_y):
                    # Not too close to other stones or trees
                    if not any(abs(s["x"] - x) < 2 and abs(s["y"] - y) < 2 for s in stones):
                        if not any(abs(t["x"] - x) < 2 and abs(t["y"] - y) < 2 for t in self.trees):
                            break
            
            stones.append({
                "id": f"stone_{i}",
                "x": x,
                "y": y,
                "stone_amount": random.randint(1, 3),
                "type": "stone"
            })
        
        return stones
    
    def _generate_mountains(self, count: int = 3) -> List[Dict]:
        """Generate mountains for mining"""
        mountains = []
        center_x, center_y = self.grid_size // 2, self.grid_size // 2
        
        for i in range(count):
            while True:
                x = random.randint(5, self.grid_size - 5)
                y = random.randint(5, self.grid_size - 5)
                
                # Not on center, not too close to other features
                if abs(x - center_x) > 15 and abs(y - center_y) > 15:
                    # Not too close to other mountains
                    if not any(abs(m["x"] - x) < 8 and abs(m["y"] - y) < 8 for m in mountains):
                        break
            
            mountains.append({
                "id": f"mountain_{i}",
                "x": x,
                "y": y,
                "type": "mountain"
            })
        
        return mountains
    
    def _generate_water(self) -> List[Dict]:
        """Generate water area (lake)"""
        water_tiles = []
        
        # Pick a random location for lake (not too close to center)
        while True:
            lake_center_x = random.randint(10, self.grid_size - 10)
            lake_center_y = random.randint(10, self.grid_size - 10)
            
            # Not too close to monument
            if abs(lake_center_x - self.grid_size // 2) > 10 or abs(lake_center_y - self.grid_size // 2) > 10:
                break
        
        # Create lake (3x3 area)
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                water_tiles.append({
                    "x": lake_center_x + dx,
                    "y": lake_center_y + dy,
                    "type": "water"
                })
        
        logger.info(f"[GAME] 💧 Lake generated at ({lake_center_x}, {lake_center_y})")
        return water_tiles
    
    def _check_and_build_bridges(self):
        """
        AUTO-BUILD BRIDGES wanneer Spark water moet oversteken
        
        Checkt:
        1. Is er een target (huis, monument, resources) aan de andere kant van water?
        2. Zo ja → bouw brug over kortste waterroute
        
        Bridge types:
        - Wooden bridge: 2 wood per tile (goedkoper)
        - Stone bridge: 1 wood + 2 stone per tile (duurzamer)
        """
        spark_x, spark_y = self.spark["x"], self.spark["y"]
        inv = self.spark["inventory"]
        
        # Find important targets
        targets = []
        
        # 1. House (most important - to sleep)
        house = next((item for item in self.placed_items if item.get("type") == "house"), None)
        if house:
            targets.append(("house", house["x"], house["y"]))
        
        # 2. Monuments (for contribution)
        for monument in self.monuments:
            targets.append(("monument", monument["x"], monument["y"]))
        
        # Check if any target is blocked by water
        for target_type, target_x, target_y in targets:
            # Simple pathfinding: check if there's water between Spark and target
            water_in_path = self._find_water_in_path(spark_x, spark_y, target_x, target_y)
            
            if water_in_path:
                # Build bridge over first water tile in path
                wx, wy = water_in_path[0]  # First water tile
                
                # Choose bridge type based on inventory
                if inv.get("wood", 0) >= 2:
                    # Build wooden bridge
                    logger.info(f"[BRIDGE] 🌉 Building wooden bridge at ({wx}, {wy}) to reach {target_type}")
                    self.place_item("wooden_bridge", wx, wy, placed_by="spark_auto")
                    inv["wood"] -= 2
                    return True  # Built one bridge, check again next cycle
                elif inv.get("wood", 0) >= 1 and inv.get("stone", 0) >= 2:
                    # Build stone bridge
                    logger.info(f"[BRIDGE] 🌉 Building stone bridge at ({wx}, {wy}) to reach {target_type}")
                    self.place_item("stone_bridge", wx, wy, placed_by="spark_auto")
                    inv["wood"] -= 1
                    inv["stone"] -= 2
                    return True
        
        return False
    
    def _find_water_in_path(self, x1: int, y1: int, x2: int, y2: int) -> list:
        """
        Find water tiles in straight-line path from (x1,y1) to (x2,y2)
        Returns list of (x, y) water coordinates
        """
        water_tiles = []
        
        # Simple line algorithm (Bresenham-ish)
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        
        x, y = x1, y1
        steps = max(dx, dy)
        
        for _ in range(steps):
            if self._is_water(x, y):
                # Check if there's already a bridge here
                has_bridge = any(
                    item.get("x") == x and item.get("y") == y 
                    and item.get("type") in ["wooden_bridge", "stone_bridge"]
                    for item in self.placed_items
                )
                if not has_bridge:
                    water_tiles.append((x, y))
            
            # Move towards target
            if dx > dy:
                if x != x2:
                    x += sx
            else:
                if y != y2:
                    y += sy
        
        return water_tiles
    
    def _is_water(self, x: int, y: int) -> bool:
        """Check if position is water (bridges make water walkable)"""
        # Check if there's a bridge here
        bridge = next((item for item in self.placed_items 
                      if item.get("x") == x and item.get("y") == y 
                      and item.get("type") in ["wooden_bridge", "stone_bridge"]), None)
        if bridge:
            return False  # Bridge = walkable
        
        return any(w["x"] == x and w["y"] == y for w in self.water_tiles)
    
    def update(self) -> Dict:
        """
        Update game state - called every UPDATE_INTERVAL seconds
        
        1. Update time (day counter, day/night)
        2. Decrease hunger/thirst
        3. Move Spark
        4. Collect resources
        5. Contribute to monument if at center
        6. Update stats
        """
        # If paused, just return current state without updates
        if getattr(self, 'is_paused', False):
            return self.get_state()
        
        self.stats["updates"] += 1
        
        # Reset action to exploring/idle at start of each update
        self.spark["current_action"] = "exploring"
        self.spark["action_target"] = None
        
        # 1. Update time system
        self._update_time()
        
        # 2. Check starter box (1-time resource boost at start)
        self._check_starter_box()
        
        # 2.5 Auto-build logic (NOW WITH BUILD PHASES!)
        self._spark_auto_build()
        
        # 2.7 CHECK AND BUILD BRIDGES (if water blocks path to important targets)
        if self.stats["updates"] % 20 == 0:  # Check every ~100 seconds
            self._check_and_build_bridges()
        
        # 3. Decrease hunger, thirst, energy, and health (slowly)
        self.spark["hunger"] = max(0, self.spark["hunger"] - 0.5)
        self.spark["thirst"] = max(0, self.spark["thirst"] - 0.8)
        self.spark["energy"] = max(0, self.spark.get("energy", 100) - 0.3)
        # Health regenerates slowly when safe
        if self.spark.get("health", 100) < 100:
            self.spark["health"] = min(100, self.spark.get("health", 100) + 0.2)
        
        # 4. DANGER CHECK - highest priority!
        self._check_danger_escape()
        
        # 4.5 NIEUW: COMBAT CHECK - check for hostile encounters
        if not self.spark.get("is_fleeing", False):
            self._check_combat_encounters()
        
        # 4.6 SPARK AUTO-FIGHT - Fight back when under attack!
        self._spark_auto_combat()
        
        # 5. Check sleep need (if not fleeing)
        if not self.spark.get("is_fleeing", False):
            self._check_sleep_need()
        
        # 6. Move Spark (unless sleeping or fleeing handled by danger check)
        old_x, old_y = self.spark["x"], self.spark["y"]
        if not self.spark.get("is_sleeping", False) and not self.spark.get("is_fleeing", False):
            self._move_spark()
        
        # Track distance
        if (old_x, old_y) != (self.spark["x"], self.spark["y"]):
            self.stats["distance_traveled"] += 1
            self.stats["steps_since_save"] += 1
            self._update_exploration()
            
            # Auto-save every 10 steps
            if self.stats["steps_since_save"] >= 10:
                self._save_world()
                self.stats["steps_since_save"] = 0
                logger.info("[AUTO-SAVE] World saved after 10 steps!")
        
        # 4. Check for resource collection (will update action if collecting)
        self._check_resource_collection()
        
        # 5. Try fishing if near water (will update action if fishing)
        self._try_fishing()
        
        # 6. Auto-consume food/water if needed
        self._auto_consume()
        
        # 7. AUTO-CONTRIBUTE SURPLUS TO MONUMENT (passive, automatic)
        # This runs every few updates to contribute excess resources above buffer
        if self.stats["updates"] % 10 == 0:  # Every ~50 seconds
            self._auto_contribute_surplus()
        
        # 8. (OLD) Contribute to monuments if on monument - KEPT for manual contributions
        # Now mainly for when Spark physically stands on monument
        # self._check_monument_contribution()  # DISABLED - surplus auto-contributes now
        
        # 9. Update growth stages (trees, crops) - ✅ SAFE
        self._update_growth()
        
        # 10. Workers auto-produce resources - ✅ SAFE
        self._workers_produce()
        
        # 11. Runners transport resources - ✅ SAFE
        self._runners_transport()
        
        # 12. Wells produce water - TEST 4 (FINAL)
        self._wells_produce()
        
        # 13. NIEUW: Update worker bots (warehouse runners, etc.)
        self._update_worker_bots()
        
        # 14. COMBAT AI: Update zombies and towers
        self._update_zombies()
        self._update_towers()
        
        logger.debug(f"[UPDATE] Completed update {self.stats['updates']}")
        
        return self.get_state()
    
    def _move_spark(self):
        """
        Move Spark with SMART AI:
        - If > 60% explored → move towards CENTER (50, 50) for building
        - Else → random exploration
        """
        current_x, current_y = self.spark["x"], self.spark["y"]
        
        # Check if on cropfield (10% chance to NOT move = slower)
        on_cropfield = any(
            p["x"] == current_x and p["y"] == current_y and p["type"] == "cropfield"
            for p in self.placed_items
        )
        
        if on_cropfield and random.random() < 0.1:
            # 10% chance to skip movement (= slower)
            return
        
        # NEW: Check if should focus on center
        focus_center = self._should_focus_on_center_building()
        
        if focus_center:
            # Move towards center (50, 50)
            center_x, center_y = self.grid_size // 2, self.grid_size // 2
            
            # Calculate direction to center
            dx = 0 if center_x == current_x else (1 if center_x > current_x else -1)
            dy = 0 if center_y == current_y else (1 if center_y > current_y else -1)
            
            new_x = current_x + dx
            new_y = current_y + dy
            
            # Try to move towards center
            if self._is_valid_move(new_x, new_y):
                self.spark["x"] = new_x
                self.spark["y"] = new_y
                self.stats["distance_traveled"] += 1
                self._update_exploration()
                
                # Log occasionally
                if self.stats["updates"] % 20 == 0:
                    exploration_pct = self._calculate_exploration_percentage()
                    logger.info(f"[AI] 🏗️ Spark focus op centrum ({exploration_pct:.1f}% verkend) - afstand tot centrum: {abs(center_x-new_x)+abs(center_y-new_y)}")
                return
            else:
                # If blocked, fall back to random movement
                pass
        
        # Random exploration (original behavior)
        attempts = 0
        moved = False
        
        while attempts < 4 and not moved:
            dx, dy = random.choice(DIRECTIONS)
            new_x = current_x + dx
            new_y = current_y + dy
            
            # Check boundaries and water
            if 0 <= new_x < self.grid_size and 0 <= new_y < self.grid_size and not self._is_water(new_x, new_y):
                # Check collision with trees
                tree_blocking = any(t["x"] == new_x and t["y"] == new_y for t in self.trees)
                # Check collision with stones
                stone_blocking = any(s["x"] == new_x and s["y"] == new_y for s in self.stones)
                # Check collision with mountains
                mountain_blocking = any(m["x"] == new_x and m["y"] == new_y for m in self.mountains)
                # Check collision with buildings (but not walls and cropfields)
                building_blocking = any(
                    p["x"] == new_x and p["y"] == new_y 
                    for p in self.placed_items 
                    if p["type"] not in ["tree", "stone", "wall", "cropfield"]
                )
                
                if not (tree_blocking or stone_blocking or mountain_blocking or building_blocking):
                    # Move is valid
                    self.spark["x"] = new_x
                    self.spark["y"] = new_y
                    moved = True
                    
                    # Update direction for visual
                    if dx > 0:
                        self.spark["direction"] = "right"
                    elif dx < 0:
                        self.spark["direction"] = "left"
                    elif dy > 0:
                        self.spark["direction"] = "down"
                    elif dy < 0:
                        self.spark["direction"] = "up"
            
            attempts += 1
        
        # If couldn't move after 4 attempts, stay in place (blocked)
    
    def _check_resource_collection(self):
        """
        Check if Spark is adjacent to resources and collect them
        
        NEW LOGIC:
        - Collect to inventory (max 50)
        - If inventory full -> transfer overflow to storage
        """
        spark_x, spark_y = self.spark["x"], self.spark["y"]
        
        # Check trees (wood)
        for tree in self.trees[:]:
            tree_x, tree_y = tree["x"], tree["y"]
            
            if abs(tree_x - spark_x) <= 1 and abs(tree_y - spark_y) <= 1:
                # Set action status
                self.spark["current_action"] = "gathering"
                self.spark["action_target"] = {"type": "tree", "x": tree_x, "y": tree_y}
                
                wood_amount = tree["wood_amount"]
                self.spark["inventory"]["wood"] += wood_amount
                self.stats["wood_collected"] += wood_amount
                
                # Restore hunger when collecting
                self.spark["hunger"] = min(100, self.spark["hunger"] + 10)
                
                logger.info(f"[GAME] 🌳 Collected {wood_amount} wood from tree at ({tree_x}, {tree_y})")
                
                # Check inventory overflow
                self._handle_inventory_overflow()
                
                # NEW: Forget this tree from memory (is verzameld)
                self._forget_collected_resource(tree_x, tree_y, "wood")
                
                # NEW: Leave stump behind instead of removing tree completely
                self.stumps.append({
                    "id": f"stump_{tree['id']}",
                    "x": tree_x,
                    "y": tree_y,
                    "wood_remaining": 1  # Can be dug up for 1 extra wood
                })
                
                self.trees.remove(tree)
                # Don't auto-generate new tree - let Planter do that
                return  # Only one resource per update
        
        # NEW: Check stumps (can dig up for 1 wood with shovel)
        for stump in self.stumps[:]:
            stump_x, stump_y = stump["x"], stump["y"]
            
            if abs(stump_x - spark_x) <= 1 and abs(stump_y - spark_y) <= 1:
                # Set action status
                self.spark["current_action"] = "gathering"
                self.spark["action_target"] = {"type": "stump", "x": stump_x, "y": stump_y}
                
                wood_amount = stump["wood_remaining"]
                self.spark["inventory"]["wood"] += wood_amount
                self.stats["wood_collected"] += wood_amount
                
                logger.info(f"[GAME] 🪵 Dug up stump for {wood_amount} wood at ({stump_x}, {stump_y})")
                
                # Check inventory overflow
                self._handle_inventory_overflow()
                
                self.stumps.remove(stump)
                return  # Only one resource per update
        
        # Check stones
        for stone in self.stones[:]:
            stone_x, stone_y = stone["x"], stone["y"]
            
            if abs(stone_x - spark_x) <= 1 and abs(stone_y - spark_y) <= 1:
                # Set action status
                self.spark["current_action"] = "gathering"
                self.spark["action_target"] = {"type": "stone", "x": stone_x, "y": stone_y}
                
                stone_amount = stone["stone_amount"]
                self.spark["inventory"]["stone"] += stone_amount
                self.stats["stone_collected"] += stone_amount
                
                # Restore thirst when collecting
                self.spark["thirst"] = min(100, self.spark["thirst"] + 10)
                
                logger.info(f"[GAME] 🪨 Collected {stone_amount} stone at ({stone_x}, {stone_y})")
                
                # Check inventory overflow
                self._handle_inventory_overflow()
                
                # NEW: Forget this stone from memory (is verzameld)
                self._forget_collected_resource(stone_x, stone_y, "stone")
                
                self.stones.remove(stone)
                self.stones.append(self._generate_stones(1)[0])
                return  # Only one resource per update
    
    def _handle_inventory_overflow(self):
        """
        Handle inventory overflow when Spark inventory > max (50)
        Transfer overflow to nearest storage:
        Priority: warehouse > production buildings > house
        """
        inv = self.spark["inventory"]
        total_inventory = inv.get("wood", 0) + inv.get("stone", 0) + inv.get("fish", 0)
        
        if total_inventory <= SPARK_INVENTORY_MAX:
            return  # No overflow
        
        overflow = total_inventory - SPARK_INVENTORY_MAX
        logger.info(f"[STORAGE] Inventory overflow: {total_inventory}/{SPARK_INVENTORY_MAX} (overflow: {overflow})")
        
        # Find nearest storage (warehouse > production > house)
        spark_x, spark_y = self.spark["x"], self.spark["y"]
        
        # Priority 1: Warehouse (1000 capacity)
        warehouse = next((item for item in self.placed_items if item.get("type") == "warehouse"), None)
        if warehouse:
            transferred = self._transfer_to_storage(warehouse, overflow)
            if transferred > 0:
                logger.info(f"[STORAGE] ✅ Transferred {transferred} resources to Warehouse")
                return
        
        # Priority 2: Production buildings with storage (100 capacity)
        production_buildings = [
            item for item in self.placed_items 
            if item.get("type") in ["lumberjack", "miner", "fisher", "farmer", "miller", "baker", "sawmill"]
        ]
        
        if production_buildings:
            # Find nearest production building
            nearest = min(production_buildings, key=lambda b: abs(b["x"] - spark_x) + abs(b["y"] - spark_y))
            transferred = self._transfer_to_storage(nearest, overflow)
            if transferred > 0:
                logger.info(f"[STORAGE] ✅ Transferred {transferred} resources to {nearest.get('type')}")
                return
        
        # Priority 3: House (50 capacity)
        house = next((item for item in self.placed_items if item.get("type") == "house"), None)
        if house:
            transferred = self._transfer_to_storage(house, overflow)
            if transferred > 0:
                logger.info(f"[STORAGE] ✅ Transferred {transferred} resources to House")
                return
        
        # No storage available - trigger warehouse build
        logger.warning(f"[STORAGE] ⚠️ No storage available! Inventory overflow: {overflow}")
        # Note: Warehouse will be built automatically by need-driven system
    
    def _transfer_to_storage(self, building: Dict, amount_needed: int) -> int:
        """
        Transfer resources from Spark inventory to building storage
        Returns: amount actually transferred
        """
        building_id = building.get("id")
        building_type = building.get("type")
        
        # Get or initialize storage
        if building_type == "warehouse":
            if "storage" not in building:
                building["storage"] = {"wood": 0, "stone": 0, "fish": 0, "food": 0, "grain": 0, "flour": 0, "bread": 0, "plank": 0, "water": 0}
            storage = building["storage"]
            capacity = PLACEABLE_ITEMS["warehouse"]["storage_capacity"]
        else:
            # Production building or house
            if building_id not in self.workhouses:
                self.workhouses[building_id] = {"wood": 0, "stone": 0, "fish": 0, "food": 0}
            storage = self.workhouses[building_id]
            capacity = PLACEABLE_ITEMS.get(building_type, {}).get("storage_capacity", 0)
        
        # Calculate current storage usage
        current_storage = sum(storage.values())
        available_space = max(0, capacity - current_storage)
        
        if available_space == 0:
            return 0  # Storage full
        
        # Transfer resources (priority: wood > stone > fish)
        inv = self.spark["inventory"]
        transferred = 0
        
        # Transfer wood
        if inv.get("wood", 0) > 0 and transferred < amount_needed and transferred < available_space:
            to_transfer = min(inv["wood"], amount_needed - transferred, available_space - transferred)
            inv["wood"] -= to_transfer
            storage["wood"] = storage.get("wood", 0) + to_transfer
            transferred += to_transfer
        
        # Transfer stone
        if inv.get("stone", 0) > 0 and transferred < amount_needed and transferred < available_space:
            to_transfer = min(inv["stone"], amount_needed - transferred, available_space - transferred)
            inv["stone"] -= to_transfer
            storage["stone"] = storage.get("stone", 0) + to_transfer
            transferred += to_transfer
        
        # Transfer fish
        if inv.get("fish", 0) > 0 and transferred < amount_needed and transferred < available_space:
            to_transfer = min(inv["fish"], amount_needed - transferred, available_space - transferred)
            inv["fish"] -= to_transfer
            storage["fish"] = storage.get("fish", 0) + to_transfer
            transferred += to_transfer
        
        return transferred
    
    def _update_exploration(self):
        """Update explored tiles based on Spark's vision AND scan for resources"""
        spark_x, spark_y = self.spark["x"], self.spark["y"]
        radius = self.spark["vision_radius"]
        current_day = self.game_time["day"]
        
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                x = spark_x + dx
                y = spark_y + dy
                
                if 0 <= x < self.grid_size and 0 <= y < self.grid_size:
                    self.explored_tiles.add((x, y))
                    
                    # NEW: Scan en onthoud resources in zicht!
                    self._scan_and_remember_resources(x, y, current_day)
    
    def _scan_and_remember_resources(self, x, y, current_day):
        """Spark onthoudt waar resources zijn die hij ziet + FRACTIE ENCOUNTERS"""
        memory = self.spark["resource_memory"]
        
        # Check voor bomen (wood)
        for tree in self.trees:
            if tree["x"] == x and tree["y"] == y:
                # Alleen toevoegen als nog niet in memory
                if not any(m[0] == x and m[1] == y for m in memory["wood"]):
                    memory["wood"].append((x, y, current_day))
                    logger.info(f"[MEMORY] 🧠 Spark onthoudt boom op ({x}, {y})")
        
        # Check voor stenen (stone)
        for stone in self.stones:
            if stone["x"] == x and stone["y"] == y:
                if not any(m[0] == x and m[1] == y for m in memory["stone"]):
                    memory["stone"].append((x, y, current_day))
                    logger.info(f"[MEMORY] 🧠 Spark onthoudt steen op ({x}, {y})")
        
        # Check voor water (water)
        for water in self.water_tiles:
            if water["x"] == x and water["y"] == y:
                if not any(m[0] == x and m[1] == y for m in memory["water"]):
                    memory["water"].append((x, y, current_day))
                    # Niet loggen (te veel water tiles)
        
        # NIEUW: Check voor gebouwen van andere fracties
        for building in self.placed_items:
            if building["x"] == x and building["y"] == y:
                faction = building.get("placed_by", "unknown")
                
                # Alleen andere fracties onthouden (niet eigen gebouwen)
                if faction != "spark" and faction != "spark_auto":
                    # Check of al in encounters
                    already_known = any(
                        e["x"] == x and e["y"] == y and e["faction"] == faction 
                        for e in self.faction_encounters
                    )
                    
                    if not already_known:
                        encounter = {
                            "x": x,
                            "y": y,
                            "faction": faction,
                            "type": "building",
                            "building_type": building.get("type", "unknown"),
                            "day": current_day
                        }
                        self.faction_encounters.append(encounter)
                        
                        relation = self.faction_relations.get("spark", {}).get(faction, "neutral")
                        logger.info(f"[FRACTIE] 🏰 Spark ontdekt {faction} gebouw ({building['type']}) op ({x}, {y}) - Relatie: {relation}")
    
    def _forget_collected_resource(self, x, y, resource_type):
        """Verwijder resource uit memory als het is verzameld"""
        memory = self.spark["resource_memory"]
        
        if resource_type in memory:
            # Filter out the collected resource
            memory[resource_type] = [(mx, my, day) for mx, my, day in memory[resource_type] 
                                     if not (mx == x and my == y)]
            logger.info(f"[MEMORY] 🧠 Spark vergeet {resource_type} op ({x}, {y}) (verzameld)")
    
    def _should_fetch_remembered_resource(self):
        """
        Check if Spark should go to remembered resource location
        Returns True if pathfinding to remembered resource
        """
        inv = self.spark["inventory"]
        memory = self.spark["resource_memory"]
        spark_x, spark_y = self.spark["x"], self.spark["y"]
        
        # Bepaal welke resource het meest nodig is
        needed_resource = None
        
        if inv.get("wood", 0) < 10 and len(memory["wood"]) > 0:
            needed_resource = "wood"
        elif inv.get("stone", 0) < 10 and len(memory["stone"]) > 0:
            needed_resource = "stone"
        
        if not needed_resource:
            return False  # Geen resources nodig of geen memory
        
        # Vind de dichtstbijzijnde resource in memory
        closest_resource = None
        closest_distance = float('inf')
        
        for rx, ry, seen_day in memory[needed_resource]:
            distance = abs(rx - spark_x) + abs(ry - spark_y)  # Manhattan distance
            if distance < closest_distance:
                closest_distance = distance
                closest_resource = (rx, ry)
        
        if closest_resource and closest_distance > 1:  # Not adjacent
            target_x, target_y = closest_resource
            
            # Move towards remembered resource
            dx = 0 if target_x == spark_x else (1 if target_x > spark_x else -1)
            dy = 0 if target_y == spark_y else (1 if target_y > spark_y else -1)
            
            new_x = spark_x + dx
            new_y = spark_y + dy
            
            # Check if move is valid
            if self._is_valid_move(new_x, new_y):
                self.spark["x"] = new_x
                self.spark["y"] = new_y
                self.stats["distance_traveled"] += 1
                self._update_exploration()
                
                logger.info(f"[MEMORY] 🧠 Spark gaat naar onthouden {needed_resource} op ({target_x}, {target_y}) - nog {closest_distance} tiles")
                return True
        
        return False
    
    def _calculate_exploration_percentage(self):
        """Bereken hoeveel % van de wereld is verkend"""
        total_tiles = self.grid_size * self.grid_size
        explored_count = len(self.explored_tiles)
        percentage = (explored_count / total_tiles) * 100
        return percentage
    
    def _should_focus_on_center_building(self):
        """
        Check if Spark should focus on building near center instead of exploring
        Returns True if > 60% explored
        """
        exploration_pct = self._calculate_exploration_percentage()
        
        # Als meer dan 60% verkend → focus op centrum bouwen
        if exploration_pct > 60:
            return True
        
        return False
    
    # ============= COMBAT SYSTEM =============
    
    def _check_combat_encounters(self):
        """
        Check for hostile units/buildings nearby and initiate combat
        Uses 2-layer RPS combat system
        """
        spark_x, spark_y = self.spark["x"], self.spark["y"]
        vision = self.spark.get("vision_radius", 6)
        
        # Check for nearby enemy buildings/units
        for encounter in self.faction_encounters:
            ex, ey = encounter["x"], encounter["y"]
            distance = abs(ex - spark_x) + abs(ey - spark_y)
            
            if distance <= 2:  # Very close → combat!
                enemy_faction = encounter["faction"]
                relation = self.faction_relations.get("spark", {}).get(enemy_faction, "neutral")
                
                # Only fight if enemy
                if relation == "enemy":
                    self._initiate_combat(encounter)
                    break
    
    def _initiate_combat(self, enemy_encounter: Dict):
        """
        Start combat with enemy unit/building
        """
        spark_x, spark_y = self.spark["x"], self.spark["y"]
        
        # Define Spark as unit
        spark_unit = {
            "units": 1,
            "type": "spark",  # Spark is unique!
            "power": 15,  # Spark is stronger than worker
            "x": spark_x,
            "y": spark_y
        }
        
        # Define enemy (simplified - based on building type)
        enemy_building_type = enemy_encounter.get("building_type", "house")
        enemy_power = 5 if "house" in enemy_building_type else 10
        
        enemy_unit = {
            "units": 1,
            "type": "defender",
            "power": enemy_power,
            "x": enemy_encounter["x"],
            "y": enemy_encounter["y"]
        }
        
        # AI decides action/stance for Spark (always attacks)
        spark_behavior = CombatEngine.decide_ai_behavior("soldier", {
            "enemy_nearby": True,
            "enemy_strength": enemy_power,
            "own_strength": 15,
            "is_outnumbered": False
        })
        
        # Enemy defends
        enemy_action = ACTION_DEFEND
        enemy_stance = STANCE_DEFEND
        
        # Calculate combat
        result = CombatEngine.calculate_combat(
            spark_unit,
            enemy_unit,
            attacker_action=spark_behavior["action"],
            defender_action=enemy_action,
            attacker_stance=spark_behavior["stance"],
            defender_stance=enemy_stance
        )
        
        # Apply results
        if result["winner"] == "attacker":
            # Spark wins! Destroy enemy building
            logger.info(f"[COMBAT] ⚔️ Spark defeats {enemy_encounter['faction']} at ({enemy_encounter['x']}, {enemy_encounter['y']})")
            
            # Remove building if it exists
            self.placed_items = [
                item for item in self.placed_items 
                if not (item["x"] == enemy_encounter["x"] and item["y"] == enemy_encounter["y"])
            ]
            
            # Remove from encounters
            self.faction_encounters = [
                e for e in self.faction_encounters
                if not (e["x"] == enemy_encounter["x"] and e["y"] == enemy_encounter["y"])
            ]
            
            # Update relation to enemy (if wasn't already)
            if self.faction_relations.get("spark", {}).get(enemy_encounter["faction"]) != "enemy":
                self.faction_relations["spark"][enemy_encounter["faction"]] = "enemy"
                logger.info(f"[FRACTIE] Spark is now ENEMY with {enemy_encounter['faction']}")
        
        elif result["winner"] == "defender":
            # Spark loses! Take damage
            damage = result["damage_received"]
            self.spark["health"] = max(0, self.spark.get("health", 100) - damage)
            
            logger.info(f"[COMBAT] 💔 Spark takes {damage} damage! Health: {self.spark['health']}")
            
            # Flee if low health
            if self.spark["health"] < 30:
                self.spark["is_fleeing"] = True
                logger.info("[COMBAT] 🏃 Spark is fleeing!")
        
        # Save combat history
        combat_record = {
            "day": self.game_time["day"],
            "spark_health": self.spark.get("health", 100),
            "enemy_faction": enemy_encounter["faction"],
            "winner": result["winner"],
            "location": (enemy_encounter["x"], enemy_encounter["y"])
        }
        self.combat_history.append(combat_record)
        
        # Set action
        self.spark["current_action"] = "fighting"
        self.spark["action_target"] = {
            "type": "combat",
            "enemy": enemy_encounter["faction"],
            "location": (enemy_encounter["x"], enemy_encounter["y"])
        }
    
    def _try_fishing(self):
        """Try to catch fish if near water and has fishing rod"""
        if "fishing_rod" not in self.spark["items"]:
            return
        
        # STOP FISHING IF INVENTORY FULL (fish > 20)
        if self.spark["inventory"].get("fish", 0) >= 20:
            return  # Stop fishing, let other actions happen
        
        spark_x, spark_y = self.spark["x"], self.spark["y"]
        
        # Check if near water
        near_water = False
        water_pos = None
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if self._is_water(spark_x + dx, spark_y + dy):
                    near_water = True
                    water_pos = (spark_x + dx, spark_y + dy)
                    break
        
        if near_water:
            # Set action status
            self.spark["current_action"] = "fishing"
            self.spark["action_target"] = {"type": "water", "x": water_pos[0], "y": water_pos[1]} if water_pos else None
            
            # 20% chance to catch fish
            if random.random() < 0.2:
                self.spark["inventory"]["fish"] += 1
                logger.info("[GAME] 🎣 Caught a fish!")
    
    def _auto_consume(self):
        """Auto-consume food/water when needed"""
        # Eat fish if hungry
        if self.spark["hunger"] < 30 and self.spark["inventory"]["fish"] > 0:
            self.spark["inventory"]["fish"] -= 1
            self.spark["hunger"] = 100
            logger.info("[GAME] 🍴 Ate fish! Hunger restored")
        
        # Drink water if thirsty
        if self.spark["thirst"] < 30 and self.spark["inventory"]["water_bottle"] > 0:
            self.spark["inventory"]["water_bottle"] -= 1
            self.spark["thirst"] = 100
            logger.info("[GAME] 💧 Drank water! Thirst restored")
    
    def _update_time(self):
        """Update 24-hour time + dag/nacht cyclus - CONFIGUREERBARE TIME SCALE"""
        try:
            # Time progression (configureerbaar via TIME_SCALE_MINUTES_PER_UPDATE)
            minutes_to_add = self.game_time.get("minutes_per_update", TIME_SCALE_MINUTES_PER_UPDATE)
            self.game_time["minutes_elapsed"] = self.game_time.get("minutes_elapsed", 0) + minutes_to_add
            
            # Update 24-hour clock
            time_of_day = self.game_time.get("time_of_day", 6.0)
            time_of_day = (time_of_day + (minutes_to_add / 60.0)) % 24
            self.game_time["time_of_day"] = time_of_day
            
            # Hour & minute for display
            total_minutes = int(time_of_day * 60)
            self.game_time["hour"] = total_minutes // 60
            self.game_time["minute"] = total_minutes % 60
            
            # Day/night (6:00-18:00 = day)
            self.game_time["is_day"] = 6 <= self.game_time["hour"] < 18
            
            # New day check
            if self.game_time["minutes_elapsed"] >= MINUTES_PER_DAY:
                self.game_time["day"] += 1
                self.game_time["minutes_elapsed"] = 0
                updates_per_day = MINUTES_PER_DAY // minutes_to_add
                real_minutes_per_day = (updates_per_day * UPDATE_INTERVAL) / 60
                logger.info(f"[TIME] ☀️ Dag {self.game_time['day']}! (Scale: +{minutes_to_add}min/update = ~{real_minutes_per_day:.1f} real min/dag)")
        except Exception as e:
            logger.error(f"[TIME] Error: {e}", exc_info=True)

    def _update_growth(self):
        """Update growth stages for trees and crops (placeholder for future implementation)"""
        pass

    def _check_sleep_need(self):
        """Check sleep - TWEE TRIGGERS: NACHT (22:00-06:00) + LOW ENERGY (< 20)"""
        try:
            energy = self.spark.get("energy", 100)
            hour = self.game_time.get("hour", 6)
            is_night = (hour >= 22 or hour < 6)  # 22:00 - 06:00
            
            # Find huis
            house = next((item for item in self.placed_items if item.get("type") == "house"), None)
            
            # TRIGGER 1: NACHT or TRIGGER 2: LOW ENERGY
            should_sleep = is_night or energy < 20
            
            if should_sleep and house:
                spark_x, spark_y = self.spark["x"], self.spark["y"]
                house_x, house_y = house["x"], house["y"]
                distance = abs(spark_x - house_x) + abs(spark_y - house_y)
                
                if distance <= 2:
                    # IN HUIS - SLAPEN
                    self.spark["is_sleeping"] = True
                    self.spark["current_action"] = "sleeping"
                    self.spark["action_target"] = {"type": "house", "x": house_x, "y": house_y}
                    
                    # SNELLERE REGEN tijdens sleep
                    energy_regen = 2.0 if is_night else 1.5
                    self.spark["energy"] = min(100, energy + energy_regen)
                    
                    if self.stats["updates"] % 20 == 0:
                        reason = "🌙 Nacht" if is_night else "⚡ Low energy"
                        logger.info(f"[SLEEP] 😴 Spark slaapt ({reason}, energy: {self.spark['energy']:.1f})")
                else:
                    # NAAR HUIS - Walking home
                    self.spark["is_sleeping"] = False
                    self.spark["current_action"] = "walking_home"
                    self.spark["action_target"] = {"type": "house", "x": house_x, "y": house_y}
                    
                    if spark_x < house_x:
                        self.spark["x"] += 1
                    elif spark_x > house_x:
                        self.spark["x"] -= 1
                    elif spark_y < house_y:
                        self.spark["y"] += 1
                    elif spark_y > house_y:
                        self.spark["y"] -= 1
            
            elif should_sleep and not house:
                # Wil slapen maar GEEN huis
                self.spark["is_sleeping"] = False
                if self.stats["updates"] % 50 == 0:
                    reason = "Nacht" if is_night else "Uitgeput"
                    logger.warning(f"[SLEEP] ⚠️ {reason} maar geen huis!")
            
            else:
                # Geen sleep nodig - DAG + genoeg energy
                if self.spark.get("is_sleeping"):
                    # Was sleeping, nu wakker
                    logger.info(f"[SLEEP] ☀️ Spark wordt wakker! (Energy: {energy:.1f}, {hour:02d}:00)")
                self.spark["is_sleeping"] = False
        
        except Exception as e:
            logger.error(f"[SLEEP] Error: {e}", exc_info=True)

    def _check_danger_escape(self):
        """
        DANGER SYSTEM - Spark vlucht bij laag health
        - Health < 20 → Vlucht naar huis (of weg van gevaar)
        - Onthoudt gevaarlijke locaties
        - Vermijdt deze locaties tijdelijk (cooldown)
        - Met knowledge ("speer", "verdediging") mag hij terug
        """
        try:
            health = self.spark.get("health", 100)
            spark_x, spark_y = self.spark["x"], self.spark["y"]
            is_fleeing = self.spark.get("is_fleeing", False)
            
            # Check if can fight (knowledge based)
            can_fight = (
                check_knowledge_for_concept("speer") or 
                check_knowledge_for_concept("verdediging") or
                check_knowledge_for_concept("weapon")
            )
            
            # CRITICAL HEALTH - VLUCHT!
            if health < 20:
                self.spark["is_fleeing"] = True
                self.spark["current_action"] = "fleeing"
                
                # Find house
                house = next((item for item in self.placed_items if item.get("type") == "house"), None)
                
                if house:
                    # Vlucht naar huis
                    house_x, house_y = house["x"], house["y"]
                    distance = abs(spark_x - house_x) + abs(spark_y - house_y)
                    self.spark["action_target"] = {"type": "house", "x": house_x, "y": house_y}
                    
                    if distance == 0:
                        # Bij huis - herstel health
                        self.spark["health"] = min(100, health + 3.0)
                        if self.spark["health"] >= 50:
                            self.spark["is_fleeing"] = False
                            self.spark["current_action"] = "idle"
                            logger.info(f"[DANGER] ✅ Spark is veilig! Health: {self.spark['health']:.1f}%")
                    else:
                        # Loop naar huis (snelst pad)
                        if spark_x < house_x:
                            self.spark["x"] += 1
                        elif spark_x > house_x:
                            self.spark["x"] -= 1
                        elif spark_y < house_y:
                            self.spark["y"] += 1
                        elif spark_y > house_y:
                            self.spark["y"] -= 1
                        logger.debug(f"[DANGER] 🏃 Vlucht naar huis! Health: {health:.1f}%")
                else:
                    # Geen huis - vlucht random veilige richting
                    safe_moves = []
                    for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]:
                        new_x, new_y = spark_x + dx, spark_y + dy
                        # Check niet in danger memory
                        is_safe = not any(
                            d["x"] == new_x and d["y"] == new_y 
                            for d in self.danger_memory
                        )
                        if is_safe and 0 <= new_x < self.grid_size and 0 <= new_y < self.grid_size:
                            safe_moves.append((new_x, new_y))
                    
                    if safe_moves:
                        new_x, new_y = random.choice(safe_moves)
                        self.spark["x"] = new_x
                        self.spark["y"] = new_y
                        logger.debug(f"[DANGER] 🏃 Vlucht! (geen huis) Health: {health:.1f}%")
                
                return  # Skip normal movement
            
            elif is_fleeing and health >= 50:
                # Health recovered - stop fleeing
                self.spark["is_fleeing"] = False
                logger.info(f"[DANGER] ✅ Niet meer gevaarlijk. Health: {health:.1f}%")
            
            # DANGER AVOIDANCE - vermijd gevaarlijke locaties (tenzij can_fight)
            if not can_fight:
                current_time = datetime.now()
                DANGER_COOLDOWN = 300  # 5 minuten
                
                # Clean oude danger entries
                self.danger_memory = [
                    d for d in self.danger_memory 
                    if (current_time - d["timestamp"]).total_seconds() < DANGER_COOLDOWN
                ]
                
                # Check if current location is dangerous
                for danger in self.danger_memory:
                    if danger["x"] == spark_x and danger["y"] == spark_y:
                        # Op gevaarlijke plek - beweeg weg!
                        safe_moves = []
                        for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]:
                            new_x, new_y = spark_x + dx, spark_y + dy
                            is_safe = not any(d["x"] == new_x and d["y"] == new_y for d in self.danger_memory)
                            if is_safe and 0 <= new_x < self.grid_size and 0 <= new_y < self.grid_size:
                                safe_moves.append((new_x, new_y))
                        
                        if safe_moves:
                            new_x, new_y = random.choice(safe_moves)
                            self.spark["x"] = new_x
                            self.spark["y"] = new_y
                            logger.debug(f"[DANGER] ⚠️ Vermijd gevaarlijke locatie ({danger['x']}, {danger['y']})")
                        break
        
        except Exception as e:
            logger.error(f"[DANGER] Error: {e}", exc_info=True)
    
    def take_damage(self, amount: float, source_x: int = None, source_y: int = None):
        """
        Spark neemt damage - gebruikt voor danger learning
        
        Args:
            amount: Damage amount (health reduction)
            source_x, source_y: Locatie van gevaar (optioneel)
        """
        try:
            self.spark["health"] = max(0, self.spark.get("health", 100) - amount)
            
            logger.warning(f"[DANGER] ⚡ Spark nam {amount} damage! Health: {self.spark['health']:.1f}%")
            
            # Voeg locatie toe aan danger memory
            if source_x is not None and source_y is not None:
                self.danger_memory.append({
                    "x": source_x,
                    "y": source_y,
                    "timestamp": datetime.now(),
                    "type": "danger"
                })
                logger.info(f"[DANGER] 📍 Gevaarlijke locatie opgeslagen: ({source_x}, {source_y})")
        
        except Exception as e:
            logger.error(f"[DANGER] Error taking damage: {e}", exc_info=True)

    def _workers_produce(self):
        """
        Production buildings automatisch laten werken
        INCLUDES PROCESSING: Sawmill, Miller, Baker, Workshop, Planter
        """
        try:
            # Production rate: elke 10 updates = ~50 seconden
            if self.stats["updates"] % 10 != 0:
                return
            
            # Loop door alle geplaatste buildings
            for item in self.placed_items:
                item_type = item.get("type")
                building_id = item.get("id")
                building_x, building_y = item["x"], item["y"]
                
                # Get or init storage for this building
                if building_id not in self.workhouses:
                    self.workhouses[building_id] = {"wood": 0, "stone": 0, "fish": 0, "food": 0, "grain": 0, "flour": 0, "bread": 0, "plank": 0, "water": 0}
                storage = self.workhouses[building_id]
                
                # === BASIC PRODUCERS ===
                
                # LUMBERJACK: verzamelt wood van nearby trees
                if item_type == "lumberjack":
                    nearby_trees = [
                        tree for tree in self.trees
                        if abs(tree["x"] - building_x) <= 10 and abs(tree["y"] - building_y) <= 10
                    ]
                    
                    if nearby_trees and random.random() < 0.5:  # 50% success rate
                        wood_gained = 2
                        storage["wood"] += wood_gained
                        logger.info(f"[LUMBERJACK] 🪓 +{wood_gained} wood at ({building_x}, {building_y})")
                
                # MINER: verzamelt stone van nearby mountains
                elif item_type == "miner":
                    nearby_mountains = [
                        mtn for mtn in self.mountains
                        if abs(mtn["x"] - building_x) <= 10 and abs(mtn["y"] - building_y) <= 10
                    ]
                    
                    if nearby_mountains and random.random() < 0.5:
                        stone_gained = 2
                        storage["stone"] += stone_gained
                        logger.info(f"[MINER] ⛏️ +{stone_gained} stone at ({building_x}, {building_y})")
                
                # FISHER: produceert fish als bij water
                elif item_type == "fisher":
                    # Check if near water (within 5 tiles)
                    near_water = any(
                        abs(int(wx) - building_x) <= 5 and abs(int(wy) - building_y) <= 5
                        for wx, wy in self.water_tiles[:100]
                    )
                    
                    if near_water and random.random() < 0.6:  # 60% success rate
                        fish_gained = 1
                        storage["fish"] += fish_gained
                        logger.info(f"[FISHER] 🎣 +{fish_gained} fish at ({building_x}, {building_y})")
                
                # WELL: water production
                elif item_type == "well":
                    water_gained = 2
                    storage["water"] += water_gained
                    logger.debug(f"[WELL] 💧 +{water_gained} water at ({building_x}, {building_y})")
                
                # === PROCESSING BUILDINGS ===
                
                # SAWMILL: wood → plank (1:1)
                elif item_type == "sawmill":
                    if storage.get("wood", 0) >= 1:
                        storage["wood"] -= 1
                        storage["plank"] = storage.get("plank", 0) + 1
                        logger.info(f"[SAWMILL] 🪚 Processed 1 wood → 1 plank at ({building_x}, {building_y})")
                
                # WORKSHOP: wood → water_bottle (1:1)
                elif item_type == "workshop":
                    if storage.get("wood", 0) >= 1:
                        storage["wood"] -= 1
                        storage["water"] = storage.get("water", 0) + 1  # water_bottle stored as "water"
                        logger.info(f"[WORKSHOP] 🔧 Crafted 1 wood → 1 bottle at ({building_x}, {building_y})")
                
                # MILLER: 1 grain + 2 water → 2 flour
                elif item_type == "miller":
                    if storage.get("grain", 0) >= 1 and storage.get("water", 0) >= 2:
                        storage["grain"] -= 1
                        storage["water"] -= 2
                        storage["flour"] = storage.get("flour", 0) + 2
                        logger.info(f"[MILLER] 🌾 Milled 1 grain + 2 water → 2 flour at ({building_x}, {building_y})")
                
                # BAKER: 1 flour + 1 water → 1 bread
                elif item_type == "baker":
                    if storage.get("flour", 0) >= 1 and storage.get("water", 0) >= 1:
                        storage["flour"] -= 1
                        storage["water"] -= 1
                        storage["bread"] = storage.get("bread", 0) + 1
                        logger.info(f"[BAKER] 🍞 Baked 1 flour + 1 water → 1 bread at ({building_x}, {building_y})")
                
                # PLANTER: Plants 1 tree per day (max 10 trees TOTAAL)
                elif item_type == "planter":
                    # Check if it's a new day and max trees not reached
                    if not hasattr(item, 'last_plant_day'):
                        item['last_plant_day'] = 0
                        item['trees_planted'] = 0
                    
                    current_day = self.game_time.get("day", 1)
                    
                    # FIXED: Max 10 trees TOTAAL per planter
                    MAX_TREES_PER_PLANTER = 10
                    if item['last_plant_day'] < current_day and item.get('trees_planted', 0) < MAX_TREES_PER_PLANTER:
                        # Find empty spot nearby
                        for offset_x in range(-5, 6):
                            for offset_y in range(-5, 6):
                                new_x = building_x + offset_x
                                new_y = building_y + offset_y
                                
                                # Check if spot is valid (not water, not occupied)
                                if (0 <= new_x < GRID_SIZE and 0 <= new_y < GRID_SIZE and
                                    not self._is_water(new_x, new_y) and
                                    not any(t['x'] == new_x and t['y'] == new_y for t in self.trees)):
                                    
                                    # Plant tree
                                    new_tree = self._generate_trees(1)[0]
                                    new_tree['x'] = new_x
                                    new_tree['y'] = new_y
                                    self.trees.append(new_tree)
                                    
                                    item['trees_planted'] = item.get('trees_planted', 0) + 1
                                    item['last_plant_day'] = current_day
                                    
                                    logger.info(f"[PLANTER] 🌱 Planted tree #{item['trees_planted']}/{MAX_TREES_PER_PLANTER} at ({new_x}, {new_y})")
                                    break
                
                # FARMER: Plants 10 cropfields → produce grain
                elif item_type == "farmer":
                    # Check if it's a new day and max cropfields not reached
                    if not hasattr(item, 'last_plant_day'):
                        item['last_plant_day'] = 0
                        item['cropfields_planted'] = 0
                    
                    current_day = self.game_time.get("day", 1)
                    
                    # Plant 1 cropfield per day (max 10)
                    if item['last_plant_day'] < current_day and item.get('cropfields_planted', 0) < 10:
                        # Find empty spot nearby
                        for offset_x in range(-5, 6):
                            for offset_y in range(-5, 6):
                                new_x = building_x + offset_x
                                new_y = building_y + offset_y
                                
                                # Check if spot is valid
                                if (0 <= new_x < GRID_SIZE and 0 <= new_y < GRID_SIZE and
                                    not self._is_water(new_x, new_y) and
                                    not any(c['x'] == new_x and c['y'] == new_y for c in self.cropfields) and
                                    not any(t['x'] == new_x and t['y'] == new_y for t in self.trees)):
                                    
                                    # Plant cropfield
                                    new_cropfield = {
                                        "x": new_x,
                                        "y": new_y,
                                        "growth_stage": "planted",
                                        "planted_day": current_day,
                                        "farmer_id": building_id
                                    }
                                    self.cropfields.append(new_cropfield)
                                    
                                    item['cropfields_planted'] = item.get('cropfields_planted', 0) + 1
                                    item['last_plant_day'] = current_day
                                    
                                    logger.info(f"[FARMER] 👨‍🌾 Planted cropfield #{item['cropfields_planted']} at ({new_x}, {new_y})")
                                    break
                    
                    # Harvest mature cropfields (3 days old)
                    for cropfield in self.cropfields[:]:
                        if cropfield.get('farmer_id') == building_id:
                            planted_day = cropfield.get('planted_day', 0)
                            if current_day - planted_day >= 3:  # 3 days to grow
                                # Harvest grain
                                storage["grain"] = storage.get("grain", 0) + 2
                                logger.info(f"[FARMER] 👨‍🌾 Harvested 2 grain from cropfield at ({cropfield['x']}, {cropfield['y']})")
                                
                                # Remove cropfield (replant next day)
                                self.cropfields.remove(cropfield)
                                item['cropfields_planted'] -= 1
        
        except Exception as e:
            logger.error(f"[PRODUCTION] Error: {e}", exc_info=True)
    
    def _runners_transport(self):
        """Runners transport resources from workhouses to warehouse"""
        # Find all runners
        runners = [r for r in self.residents if r["profession"] == "runner" and r["status"] == "ready_to_work"]
        
        if not runners:
            return
        
        # Find warehouse
        warehouse = next((p for p in self.placed_items if p["type"] == "warehouse"), None)
        if not warehouse:
            return
        
        # Initialize warehouse storage
        if "storage" not in warehouse:
            warehouse["storage"] = {"wood": 0, "stone": 0, "fish": 0, "food": 0}
        
        for runner in runners:
            # Each runner picks up from all workhouses
            carry_capacity = PLACEABLE_ITEMS["runner"].get("carry_capacity", 20)
            carried = {"wood": 0, "stone": 0, "fish": 0, "food": 0}
            
            # Collect from each workhouse
            for building_id, storage in self.workhouses.items():
                for resource in ["wood", "stone", "fish", "food"]:
                    available = storage.get(resource, 0)
                    space_left = carry_capacity - sum(carried.values())
                    
                    if available > 0 and space_left > 0:
                        amount = min(available, space_left)
                        carried[resource] += amount
                        storage[resource] -= amount
            
            # Deposit to warehouse
            if sum(carried.values()) > 0:
                for resource, amount in carried.items():
                    warehouse["storage"][resource] += amount
                
                logger.info(f"[RUNNER] Transported to warehouse: {carried}")

    def _wells_produce(self):
        """Wells produce water to warehouse"""
        if not self.wells:
            return
        
        warehouse = next((p for p in self.placed_items if p["type"] == "warehouse"), None)
        if not warehouse:
            return
        
        if "storage" not in warehouse:
            warehouse["storage"] = {"wood": 0, "stone": 0, "fish": 0, "food": 0, "grain": 0, "flour": 0, "bread": 0, "plank": 0, "water": 0}
        
        # Each well produces 2 water per update
        water_produced = len(self.wells) * 2
        warehouse["storage"]["water"] += water_produced
        
        if water_produced > 0:
            logger.info(f"[WELLS] Produced {water_produced} water → warehouse")
    
    def _auto_contribute_surplus(self):
        """
        NEW PRIORITY SYSTEM:
        1. FIRST: Fill warehouse to 50% (for Phase 2 unlock)
        2. THEN: Contribute surplus to monuments (passive progress)
        
        This ensures build phases can progress while still building monuments
        """
        inv = self.spark["inventory"]
        wood = inv.get("wood", 0)
        stone = inv.get("stone", 0)
        
        # Get warehouse info
        warehouse = next((item for item in self.placed_items if item.get("type") == "warehouse"), None)
        warehouse_fill = self._get_warehouse_fill_percentage()
        
        # PRIORITY 1: Fill warehouse to 50% FIRST (for Phase 2 unlock)
        if warehouse and warehouse_fill < 50.0:
            # Deposit surplus resources into warehouse
            target_amount = int(1000 * 0.50)  # 50% of 1000 = 500 resources
            current_total = sum(warehouse.get("storage", {}).values())
            space_needed = target_amount - current_total
            
            if space_needed > 0:
                # Transfer wood
                if wood > 30:  # Keep some for building
                    deposit_wood = min(wood - 30, space_needed)
                    if "storage" not in warehouse:
                        warehouse["storage"] = {}
                    warehouse["storage"]["wood"] = warehouse["storage"].get("wood", 0) + deposit_wood
                    inv["wood"] -= deposit_wood
                    space_needed -= deposit_wood
                    logger.info(f"[WAREHOUSE] 📦 Deposited {deposit_wood} wood → {self._get_warehouse_fill_percentage():.1f}% fill")
                
                # Transfer stone
                if stone > 30 and space_needed > 0:  # Keep some for building
                    deposit_stone = min(stone - 30, space_needed)
                    warehouse["storage"]["stone"] = warehouse["storage"].get("stone", 0) + deposit_stone
                    inv["stone"] -= deposit_stone
                    logger.info(f"[WAREHOUSE] 📦 Deposited {deposit_stone} stone → {self._get_warehouse_fill_percentage():.1f}% fill")
            
            return  # Skip monument contribution until warehouse is 50%
        
        # PRIORITY 2: Contribute surplus to monuments (after warehouse ≥50%)
        # Get planks from warehouse storage
        planks = 0
        if warehouse and "storage" in warehouse:
            planks = warehouse["storage"].get("plank", 0)
        
        # Check surplus above buffer
        wood_surplus = max(0, wood - MONUMENT_BUFFER_WOOD)
        stone_surplus = max(0, stone - MONUMENT_BUFFER_STONE)
        plank_surplus = planks  # All planks can be contributed (no buffer needed)
        
        if wood_surplus == 0 and stone_surplus == 0 and plank_surplus == 0:
            return  # No surplus to contribute
        
        # Find nearest monument
        spark_x, spark_y = self.spark["x"], self.spark["y"]
        nearest_monument = min(
            self.monuments,
            key=lambda m: abs(m["x"] - spark_x) + abs(m["y"] - spark_y),
            default=None
        )
        
        if not nearest_monument:
            return
        
        # Contribute wood surplus
        if wood_surplus > 0:
            wood_needed = nearest_monument["wood_needed"] - nearest_monument["wood_contributed"]
            wood_to_contribute = min(wood_surplus, wood_needed)
            
            if wood_to_contribute > 0:
                inv["wood"] -= wood_to_contribute
                nearest_monument["wood_contributed"] += wood_to_contribute
                self.stats["monument_contributions"] += 1
                logger.info(f"[AUTO-CONTRIBUTE] 🏛️ +{wood_to_contribute} wood to {nearest_monument['name']} (surplus above buffer)")
        
        # Contribute stone surplus
        if stone_surplus > 0:
            stone_needed = nearest_monument["stone_needed"] - nearest_monument["stone_contributed"]
            stone_to_contribute = min(stone_surplus, stone_needed)
            
            if stone_to_contribute > 0:
                inv["stone"] -= stone_to_contribute
                nearest_monument["stone_contributed"] += stone_to_contribute
                self.stats["monument_contributions"] += 1
                logger.info(f"[AUTO-CONTRIBUTE] 🏛️ +{stone_to_contribute} stone to {nearest_monument['name']} (surplus above buffer)")
        
        # Contribute plank surplus (from warehouse)
        if plank_surplus > 0 and warehouse:
            plank_needed = nearest_monument.get("plank_needed", 0) - nearest_monument.get("plank_contributed", 0)
            plank_to_contribute = min(plank_surplus, plank_needed)
            
            if plank_to_contribute > 0:
                warehouse["storage"]["plank"] -= plank_to_contribute
                nearest_monument["plank_contributed"] = nearest_monument.get("plank_contributed", 0) + plank_to_contribute
                self.stats["monument_contributions"] += 1
                logger.info(f"[AUTO-CONTRIBUTE] 🏛️ +{plank_to_contribute} planks to {nearest_monument['name']} (from warehouse)")
        
        # Update progress (wood + stone + planks)
        total_contributed = (nearest_monument["wood_contributed"] + 
                            nearest_monument["stone_contributed"] + 
                            nearest_monument.get("plank_contributed", 0))
        total_needed = (nearest_monument["wood_needed"] + 
                       nearest_monument["stone_needed"] + 
                       nearest_monument.get("plank_needed", 0))
        nearest_monument["progress"] = (total_contributed / total_needed) * 100
    
    def _check_monument_contribution(self):
        """
        Check if Spark is at any monument and contribute resources
        
        NEW ECONOMY RULES:
        1. Keep buffer (20 wood, 20 stone) - never contribute below buffer
        2. Only contribute if total storage > 50% full
        3. Priority: Survival > Buildings > Storage > Monument (last)
        """
        spark_x, spark_y = self.spark["x"], self.spark["y"]
        
        # Calculate total storage capacity and current resources
        total_storage_capacity = self._calculate_total_storage_capacity()
        total_resources = self._calculate_total_resources()
        
        # Check storage threshold (must be > 50% full)
        if total_storage_capacity > 0:
            storage_percentage = total_resources / total_storage_capacity
            if storage_percentage < MONUMENT_STORAGE_THRESHOLD:
                # Storage not full enough - don't contribute yet
                return
        
        for monument in self.monuments:
            mx, my = monument["x"], monument["y"]
            size = monument["size"]
            
            # Check if Spark is within monument area
            if mx <= spark_x < mx + size and my <= spark_y < my + size:
                # Contribute wood (only surplus above buffer)
                wood_available = self.spark["inventory"]["wood"]
                wood_surplus = max(0, wood_available - MONUMENT_BUFFER_WOOD)
                
                if wood_surplus > 0:
                    wood_to_contribute = min(
                        wood_surplus,
                        monument["wood_needed"] - monument["wood_contributed"]
                    )
                    
                    if wood_to_contribute > 0:
                        self.spark["inventory"]["wood"] -= wood_to_contribute
                        monument["wood_contributed"] += wood_to_contribute
                        self.stats["monument_contributions"] += 1
                        logger.info(f"[MONUMENT] 🏛️ Contributed {wood_to_contribute} wood to {monument['name']} (kept {MONUMENT_BUFFER_WOOD} buffer)")
                
                # Contribute stone (only surplus above buffer)
                stone_available = self.spark["inventory"]["stone"]
                stone_surplus = max(0, stone_available - MONUMENT_BUFFER_STONE)
                
                if stone_surplus > 0:
                    stone_to_contribute = min(
                        stone_surplus,
                        monument["stone_needed"] - monument["stone_contributed"]
                    )
                    
                    if stone_to_contribute > 0:
                        self.spark["inventory"]["stone"] -= stone_to_contribute
                        monument["stone_contributed"] += stone_to_contribute
                        self.stats["monument_contributions"] += 1
                        logger.info(f"[MONUMENT] 🏛️ Contributed {stone_to_contribute} stone to {monument['name']} (kept {MONUMENT_BUFFER_STONE} buffer)")
                
                # Update progress
                total_contributed = monument["wood_contributed"] + monument["stone_contributed"]
                total_needed = monument["wood_needed"] + monument["stone_needed"]
                monument["progress"] = (total_contributed / total_needed) * 100
                
                break  # Only contribute to one monument at a time
    
    def _calculate_total_storage_capacity(self) -> int:
        """Calculate total storage capacity from all buildings"""
        total = 0
        
        for item in self.placed_items:
            item_type = item.get("type")
            if item_type in PLACEABLE_ITEMS:
                capacity = PLACEABLE_ITEMS[item_type].get("storage_capacity", 0)
                total += capacity
        
        return total
    
    def _calculate_total_resources(self) -> int:
        """Calculate total resources (Spark inventory + all storage)"""
        total = 0
        
        # Spark inventory
        inv = self.spark["inventory"]
        total += inv.get("wood", 0) + inv.get("stone", 0) + inv.get("fish", 0)
        
        # All workhouse storage
        for storage in self.workhouses.values():
            total += storage.get("wood", 0) + storage.get("stone", 0) + storage.get("fish", 0)
        
        # Warehouse storage (if exists)
        warehouse = next((item for item in self.placed_items if item.get("type") == "warehouse"), None)
        if warehouse and "storage" in warehouse:
            storage = warehouse["storage"]
            total += storage.get("wood", 0) + storage.get("stone", 0) + storage.get("fish", 0)
        
        return total
    
    def get_state(self) -> Dict:
        """Get current game state for frontend"""
        exploration_pct = self._calculate_exploration_percentage()
        
        return {
            "grid_size": self.grid_size,
            "spark": self.spark,
            "trees": self.trees,
            "stumps": self.stumps,
            "stones": self.stones,
            "water_tiles": self.water_tiles,
            "mountains": self.mountains,
            "monuments": self.monuments,
            "placed_items": self.placed_items,
            "cropfields": self.cropfields,
            "managed_trees": self.managed_trees,
            "residents": self.residents,
            "workhouses": self.workhouses,
            "game_time": self.game_time,
            "stats": self.stats,
            "explored_tiles": list(self.explored_tiles),
            "exploration_percentage": exploration_pct,  # NIEUW: % verkend
            "faction_relations": self.faction_relations,  # NIEUW: Fractie relaties
            "faction_encounters": self.faction_encounters,  # NIEUW: Ontmoette fracties
            "combat_history": getattr(self, 'combat_history', []),  # NIEUW: Combat geschiedenis
            "worker_bots": getattr(self, 'worker_bots', []),  # NIEUW: Worker bots voor frontend
            "entities": self.entity_manager.get_all_entities(),  # NIEUW: Alle entities (inclusief koning bots)
            "timestamp": self.stats["updates"]
        }
    
    # Admin methods
    def set_resources(self, wood: int = None, stone: int = None):
        """Admin: Set Spark's resources"""
        if wood is not None:
            self.spark["inventory"]["wood"] = max(0, wood)
        if stone is not None:
            self.spark["inventory"]["stone"] = max(0, stone)
        logger.info(f"[GAME ADMIN] Resources set - Wood: {self.spark['inventory']['wood']}, Stone: {self.spark['inventory']['stone']}")
    
    def reset_monument(self):
        """Admin: Reset all monuments progress"""
        for monument in self.monuments:
            monument["wood_contributed"] = 0
            monument["stone_contributed"] = 0
            monument["progress"] = 0.0
        logger.info("[GAME ADMIN] All monuments reset")
    
    def set_needs(self, hunger: int = None, thirst: int = None):
        """Admin: Set Spark's needs"""
        if hunger is not None:
            self.spark["hunger"] = max(0, min(100, hunger))
        if thirst is not None:
            self.spark["thirst"] = max(0, min(100, thirst))
        logger.info(f"[GAME ADMIN] Needs set - Hunger: {self.spark['hunger']}, Thirst: {self.spark['thirst']}")
    
    def place_item(self, item_type: str, x: int, y: int, placed_by: str = "player"):
        """Place a buildable item on the grid"""
        # Validate coordinates
        if not (0 <= x < self.grid_size and 0 <= y < self.grid_size):
            return {"success": False, "message": "Positie buiten de kaart"}
        
        # Check if item exists in PLACEABLE_ITEMS
        if item_type not in PLACEABLE_ITEMS:
            return {"success": False, "message": "Onbekend item type"}
        
        item_config = PLACEABLE_ITEMS[item_type]
        cost = item_config.get("cost", {})

        # Special validation for water-dependent buildings (fisher)
        if item_config.get("requires") == "water":
            # Check if adjacent to water
            adjacent_to_water = False
            for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                check_x, check_y = x + dx, y + dy
                if any(w["x"] == check_x and w["y"] == check_y for w in self.water_tiles):
                    adjacent_to_water = True
                    break
            
            if not adjacent_to_water:
                return {"success": False, "message": f"{item_config['name']} moet naast water geplaatst worden! 💧"}
        
        # Special validation for mountain-dependent buildings (mine)
        if item_config.get("requires") == "mountain":
            # Must be placed ON a mountain
            on_mountain = any(m["x"] == x and m["y"] == y for m in self.mountains)
            if not on_mountain:
                return {"success": False, "message": f"{item_config['name']} moet op een berg geplaatst worden! ⛰️"}
        
        # Check if player has enough resources
        inv = self.spark["inventory"]
        if cost.get("wood", 0) > inv.get("wood", 0):
            return {"success": False, "message": f"Niet genoeg hout (nodig: {cost.get('wood', 0)})"}
        if cost.get("stone", 0) > inv.get("stone", 0):
            return {"success": False, "message": f"Niet genoeg steen (nodig: {cost.get('stone', 0)})"}
        
        # Check if tile is empty (no tree, stone, water, or other placed item)
        for tree in self.trees:
            if tree["x"] == x and tree["y"] == y:
                return {"success": False, "message": "Er staat al een boom op deze plek"}
        
        for stone in self.stones:
            if stone["x"] == x and stone["y"] == y:
                return {"success": False, "message": "Er ligt al een steen op deze plek"}
        
        for water in self.water_tiles:
            if water["x"] == x and water["y"] == y:
                return {"success": False, "message": "Je kunt niet op water bouwen"}
        
        for placed in self.placed_items:
            if placed["x"] == x and placed["y"] == y:
                return {"success": False, "message": "Er staat al een gebouw op deze plek"}
        
        # Deduct resources
        inv["wood"] -= cost.get("wood", 0)
        inv["stone"] -= cost.get("stone", 0)
        
        # Place the item
        placed_item = {
            "type": item_type,
            "x": x,
            "y": y,
            "placed_by": placed_by,
            "icon": item_config["icon"],
            "name": item_config["name"],
            "id": f"{item_type}_{len(self.placed_items)}"
        }
        self.placed_items.append(placed_item)
        
        # Track cropfields separately for food production
        if item_type == "cropfield":
            self.cropfields.append({
                "id": placed_item["id"],
                "x": x,
                "y": y,
                "stage": "planted",
                "planted_day": self.game_time["day"],
                "food_produced_today": 0,
                "last_harvest_day": 0
            })
        
        # Track wells for water production
        if item_type == "well":
            self.wells.append({
                "id": placed_item["id"],
                "x": x,
                "y": y
            })
            # Wells produce water to warehouse automatically
            warehouse = next((p for p in self.placed_items if p["type"] == "warehouse"), None)
            if warehouse:
                if "storage" not in warehouse:
                    warehouse["storage"] = {"wood": 0, "stone": 0, "fish": 0, "food": 0, "grain": 0, "flour": 0, "bread": 0, "plank": 0, "water": 0}
                warehouse["storage"]["water"] += 10  # Initial water bonus
                logger.info("[BUILD] Well created! +10 water to warehouse")
        
        # If it's a profession building, create workers
        if item_config.get("type") == "profession":
            workers_needed = item_config.get("workers", 1)
            
            # Initialize workhouse storage for production buildings
            if item_config.get("storage_capacity"):
                self.workhouses[placed_item["id"]] = {"wood": 0, "stone": 0, "fish": 0, "food": 0}
            
            for i in range(workers_needed):
                resident = {
                    "id": f"resident_{len(self.residents)}",
                    "name": f"Bewoner {len(self.residents) + 1}",
                    "house_id": None,  # Needs a house!
                    "profession_building_id": placed_item["id"],
                    "profession": item_type,
                    "faction_id": None,  # Later koppelen aan factie
                    "hunger": 100,
                    "thirst": 100,
                    "x": x,  # Start at profession building
                    "y": y,
                    "status": "waiting_for_house"  # Need house before working
                }
                self.residents.append(resident)
                logger.info(f"[BUILD] Created resident {resident['name']} for {item_type}")
        
        # If it's a house, try to assign homeless residents
        if item_type == "house":
            homeless = [r for r in self.residents if r["house_id"] is None]
            if homeless:
                resident = homeless[0]
                resident["house_id"] = placed_item["id"]
                resident["status"] = "ready_to_work"
                logger.info(f"[BUILD] Assigned {resident['name']} to house {placed_item['id']}")
        
        logger.info(f"[BUILD] {placed_by} placed {item_type} at ({x}, {y})")
        
        return {
            "success": True,
            "message": f"{item_config['name']} geplaatst!",
            "item": placed_item,
            "inventory": inv,
            "new_residents": [r for r in self.residents if r["profession_building_id"] == placed_item["id"]] if item_config.get("type") == "profession" else []
        }

    def _check_starter_box(self):
        """
        Check if Spark is near starter box and transfer contents
        Starter box disappears after emptied (1-time boost)
        """
        if not self.starter_box.get("is_active", False):
            return  # Already collected
        
        spark_x, spark_y = self.spark["x"], self.spark["y"]
        box_x, box_y = self.starter_box["x"], self.starter_box["y"]
        
        # Check if adjacent to starter box
        distance = abs(spark_x - box_x) + abs(spark_y - box_y)
        
        if distance <= 1:  # Adjacent or on top
            # Transfer all contents to Spark's inventory
            contents = self.starter_box.get("contents", {})
            
            for resource, amount in contents.items():
                if resource in self.spark["inventory"]:
                    self.spark["inventory"][resource] += amount
                else:
                    self.spark["inventory"][resource] = amount
            
            # Log transfer
            logger.info(f"[STARTER] 📦 Spark collected starter box: {contents}")
            
            # Deactivate starter box (disappears)
            self.starter_box["is_active"] = False
            self.starter_box["contents"] = {}
            
            # Set action
            self.spark["current_action"] = "collecting_starter_box"
            self.spark["action_target"] = {"type": "starter_box", "x": box_x, "y": box_y}
    
    def _get_warehouse_fill_percentage(self) -> float:
        """
        Calculate warehouse fill percentage (0-100)
        Returns 0 if no warehouse exists
        """
        warehouse = next((item for item in self.placed_items if item.get("type") == "warehouse"), None)
        
        if not warehouse:
            return 0.0
        
        # Get warehouse storage
        storage = warehouse.get("storage", {})
        capacity = PLACEABLE_ITEMS["warehouse"]["storage_capacity"]  # 1000
        
        # Calculate total stored
        total_stored = sum(storage.values())
        
        # Calculate percentage
        fill_percentage = (total_stored / capacity) * 100 if capacity > 0 else 0
        
        return fill_percentage
    
    def _get_current_build_phase(self) -> str:
        """
        Determine current build phase based on warehouse fill % and completed requirements
        
        Returns: "phase_1_basics", "phase_2_producers", "phase_3_mining", "phase_4_advanced"
        """
        warehouse_fill = self._get_warehouse_fill_percentage()
        
        # Phase 1: Basics (warehouse must be built)
        phase_1 = self.build_phases["phase_1_basics"]
        has_warehouse = any(item.get("type") == "warehouse" for item in self.placed_items)
        
        if not has_warehouse:
            return "phase_1_basics"  # Still in phase 1
        
        # Phase 1 completed when warehouse exists
        if not phase_1["completed"]:
            phase_1["completed"] = True
            logger.info("[BUILD PHASE] ✅ Phase 1 Complete: Basics (warehouse built)")
        
        # Phase 2: Producers (requires 50% warehouse fill)
        phase_2 = self.build_phases["phase_2_producers"]
        phase_2_threshold = phase_2["warehouse_threshold"]
        
        if warehouse_fill < phase_2_threshold:
            return "phase_1_basics"  # Not enough resources for phase 2
        
        # Check if phase 2 requirements met
        has_planter = any(item.get("type") == "planter" for item in self.placed_items)
        has_lumberjack = any(item.get("type") == "lumberjack" for item in self.placed_items)
        
        if not (has_planter and has_lumberjack):
            return "phase_2_producers"  # Working on phase 2
        
        # Phase 2 completed
        if not phase_2["completed"]:
            phase_2["completed"] = True
            logger.info("[BUILD PHASE] ✅ Phase 2 Complete: Producers (planter + lumberjack)")
        
        # Phase 3: Mining (requires 50% warehouse fill + mountain nearby)
        phase_3 = self.build_phases["phase_3_mining"]
        phase_3_threshold = phase_3["warehouse_threshold"]
        
        if warehouse_fill < phase_3_threshold:
            return "phase_2_producers"  # Not enough resources for phase 3
        
        has_miner = any(item.get("type") == "miner" for item in self.placed_items)
        
        if not has_miner:
            return "phase_3_mining"  # Working on phase 3
        
        # Phase 3 completed
        if not phase_3["completed"]:
            phase_3["completed"] = True
            logger.info("[BUILD PHASE] ✅ Phase 3 Complete: Mining (miner built)")
        
        # Phase 4: Advanced (requires 75% warehouse fill)
        phase_4 = self.build_phases["phase_4_advanced"]
        phase_4_threshold = phase_4["warehouse_threshold"]
        
        if warehouse_fill < phase_4_threshold:
            return "phase_3_mining"  # Not enough resources for phase 4
        
        has_sawmill = any(item.get("type") == "sawmill" for item in self.placed_items)
        has_mill = any(item.get("type") == "miller" for item in self.placed_items)
        
        if not (has_sawmill and has_mill):
            return "phase_4_advanced"  # Working on phase 4
        
        # Phase 4 completed
        if not phase_4["completed"]:
            phase_4["completed"] = True
            logger.info("[BUILD PHASE] ✅ Phase 4 Complete: Advanced (sawmill + mill)")
        
        return "phase_4_advanced"  # All phases complete
    
    def _spark_auto_build(self):
        """
        PHASE-DRIVEN BUILD LOGIC
        NEW RULES:
        1. Phase 1: Build warehouse (required before anything else)
        2. Phase 2: Producers (planter + lumberjack) when warehouse 50% full
        3. Phase 3: Mining (miner on mountain) when warehouse 50% full
        4. Phase 4: Advanced (sawmill + mill) when warehouse 75% full
        5. Houses built as needed for workers (1 house per production building)
        """
        try:
            # Build more frequently - every 10 updates (~50 seconds)
            if self.stats["updates"] % 10 != 0:
                return
            
            inv = self.spark["inventory"]
            wood, stone = inv.get("wood", 0), inv.get("stone", 0)
            spark_x, spark_y = self.spark["x"], self.spark["y"]
            
            # Get current build phase and warehouse fill
            current_phase = self._get_current_build_phase()
            warehouse_fill = self._get_warehouse_fill_percentage()
            
            # Log phase info occasionally
            if self.stats["updates"] % 100 == 0:
                logger.info(f"[BUILD PHASE] Current: {current_phase}, Warehouse: {warehouse_fill:.1f}%")
            
            # Count buildings
            house_count = sum(1 for item in self.placed_items if item.get("type") == "house")
            # production_count used in priority system helper methods
            
            # ALWAYS PRIORITY: Survival needs (house, well, fisher)
            has_well = any(item.get("type") == "well" for item in self.placed_items)
            has_fisher = any(item.get("type") == "fisher" for item in self.placed_items)
            thirst = self.spark.get("thirst", 100)
            hunger = self.spark.get("hunger", 100)
            
            # Emergency: First house (survival)
            if house_count == 0 and wood >= 2 and stone >= 2:
                logger.info("[AUTO-BUILD] 🏠 Bouw eerste huis (survival)")
                self.spark["current_action"] = "building"
                self.spark["action_target"] = {"type": "house", "x": spark_x, "y": spark_y}
                self.place_item("house", spark_x, spark_y, placed_by="spark_auto")
                return
            
            # Emergency: Thirst → Well
            if thirst < 40 and not has_well and stone >= 5:
                logger.info(f"[AUTO-BUILD] 💧 Bouw well (thirst: {thirst:.0f})")
                self.spark["current_action"] = "building"
                self.spark["action_target"] = {"type": "well", "x": spark_x + 2, "y": spark_y}
                self.place_item("well", spark_x + 2, spark_y, placed_by="spark_auto")
                return
            
            # Emergency: Hunger → Fisher (if near water)
            if hunger < 40 and not has_fisher and wood >= 5:
                near_water = any(
                    abs(int(wx) - spark_x) <= 8 and abs(int(wy) - spark_y) <= 8
                    for wx, wy in self.water_tiles[:50]
                )
                if near_water:
                    logger.info(f"[AUTO-BUILD] 🎣 Bouw fisher (hunger: {hunger:.0f})")
                    self.spark["current_action"] = "building"
                    self.spark["action_target"] = {"type": "fisher", "x": spark_x + 3, "y": spark_y}
                    self.place_item("fisher", spark_x + 3, spark_y, placed_by="spark_auto")
                    return
            
            # === PHASE-DRIVEN BUILDING ===
            
            # PHASE 1: Build Warehouse (priority!)
            if current_phase == "phase_1_basics":
                has_warehouse = any(item.get("type") == "warehouse" for item in self.placed_items)
                
                if not has_warehouse and wood >= 10 and stone >= 10:
                    logger.info(f"[AUTO-BUILD] 🏭 Phase 1: Bouw warehouse (resources: {wood}W + {stone}S)")
                    self.spark["current_action"] = "building"
                    self.spark["action_target"] = {"type": "warehouse", "x": spark_x + 5, "y": spark_y}
                    self.place_item("warehouse", spark_x + 5, spark_y, placed_by="spark_auto")
                    return
            
            # PHASE 2: Build Producers (planter + lumberjack)
            elif current_phase == "phase_2_producers":
                has_planter = any(item.get("type") == "planter" for item in self.placed_items)
                has_lumberjack = any(item.get("type") == "lumberjack" for item in self.placed_items)
                
                if not has_planter and wood >= 10:
                    logger.info(f"[AUTO-BUILD] 🌱 Phase 2: Bouw planter (warehouse: {warehouse_fill:.1f}%)")
                    self.spark["current_action"] = "building"
                    self.spark["action_target"] = {"type": "planter", "x": spark_x - 3, "y": spark_y}
                    self.place_item("planter", spark_x - 3, spark_y, placed_by="spark_auto")
                    return
                
                if not has_lumberjack and wood >= 10:
                    logger.info(f"[AUTO-BUILD] 🪓 Phase 2: Bouw lumberjack (warehouse: {warehouse_fill:.1f}%)")
                    self.spark["current_action"] = "building"
                    self.spark["action_target"] = {"type": "lumberjack", "x": spark_x - 5, "y": spark_y}
                    self.place_item("lumberjack", spark_x - 5, spark_y, placed_by="spark_auto")
                    return
            
            # PHASE 3: Build Miner (on mountain)
            elif current_phase == "phase_3_mining":
                has_miner = any(item.get("type") == "miner" for item in self.placed_items)
                
                if not has_miner and stone >= 10:
                    # Find nearest mountain
                    nearest_mountain = None
                    min_dist = float('inf')
                    
                    for mtn in self.mountains[:20]:  # Check first 20 mountains
                        dist = abs(mtn["x"] - spark_x) + abs(mtn["y"] - spark_y)
                        if dist < min_dist:
                            min_dist = dist
                            nearest_mountain = mtn
                    
                    if nearest_mountain:
                        # Place miner near mountain (not on it)
                        miner_x = nearest_mountain["x"] + 1
                        miner_y = nearest_mountain["y"]
                        
                        logger.info(f"[AUTO-BUILD] ⛏️ Phase 3: Bouw miner near mountain ({miner_x}, {miner_y})")
                        self.spark["current_action"] = "building"
                        self.spark["action_target"] = {"type": "miner", "x": miner_x, "y": miner_y}
                        self.place_item("miner", miner_x, miner_y, placed_by="spark_auto")
                        return
            
            # PHASE 4: Build Advanced (sawmill + mill)
            elif current_phase == "phase_4_advanced":
                has_sawmill = any(item.get("type") == "sawmill" for item in self.placed_items)
                has_mill = any(item.get("type") == "miller" for item in self.placed_items)
                
                if not has_sawmill and wood >= 20 and stone >= 10:
                    logger.info(f"[AUTO-BUILD] 🪚 Phase 4: Bouw sawmill (warehouse: {warehouse_fill:.1f}%)")
                    self.spark["current_action"] = "building"
                    self.spark["action_target"] = {"type": "sawmill", "x": spark_x + 7, "y": spark_y}
                    self.place_item("sawmill", spark_x + 7, spark_y, placed_by="spark_auto")
                    return
                
                if not has_mill and wood >= 15 and stone >= 5:
                    logger.info(f"[AUTO-BUILD] 🌾 Phase 4: Bouw mill (warehouse: {warehouse_fill:.1f}%)")
                    self.spark["current_action"] = "building"
                    self.spark["action_target"] = {"type": "miller", "x": spark_x + 9, "y": spark_y}
                    self.place_item("miller", spark_x + 9, spark_y, placed_by="spark_auto")
                    return
            
            # ALWAYS: Worker housing (1 house per production building)
            # UPGRADED: Use priority system
            decision = self._decide_next_build()
            
            # Log decision (for debugging)
            if self.stats["updates"] % 20 == 0:  # Every ~100 seconds
                logger.info(f"[PRIORITY] {decision['priority']}: {decision['action']} - {decision['reason']}")
            
            # Execute based on priority
            if decision["action"] in ["build_house", "build_worker_house", "urgent_shelter"]:
                if wood >= 2 and stone >= 2:
                    logger.info(f"[AUTO-BUILD] 🏠 {decision['priority']}: {decision['reason']}")
                    self.spark["current_action"] = "building"
                    offset = house_count * 2
                    self.spark["action_target"] = {"type": "house", "x": spark_x + offset, "y": spark_y + offset}
                    self.place_item("house", spark_x + offset, spark_y + offset, placed_by="spark_auto")
                    return
            
            # Monument ONLY if warehouse > 50% (NIEUW RULE)
            monuments_count = len(self.monuments)
            if decision["action"] == "build_monument" and monuments_count == 0:
                if warehouse_fill >= 50 and wood >= 50 and stone >= 50:
                    logger.info(f"[AUTO-BUILD] 🏛️ LUXURY: Build monument (warehouse {warehouse_fill:.0f}% filled)")
                    # Monument placement logic (use existing code if available)
                    self.spark["current_action"] = "building"
                    self.spark["action_target"] = {"type": "monument", "x": spark_x, "y": spark_y - 10}
                    # TODO: Actual monument build (if not implemented yet)
                    return
        
        except Exception as e:
            logger.error(f"[AUTO-BUILD] Error: {e}", exc_info=True)
    
    def toggle_pause(self) -> Dict:
        """Toggle game pause state"""
        self.is_paused = not getattr(self, 'is_paused', False)
        status = "PAUSED" if self.is_paused else "RUNNING"
        logger.info(f"[GAME] Game {status}")
        return {
            "success": True,
            "is_paused": self.is_paused,
            "message": f"Game {status}"
        }
    
    # ============= PRIORITY SYSTEM HELPERS =============
    
    def _count_homeless_residents(self) -> int:
        """Count residents without a house"""
        resident_count = len(self.residents)
        house_count = len([item for item in self.placed_items if item.get("type") == "house"])
        homeless = max(0, resident_count - house_count)
        return homeless
    
    def _count_homeless_workers(self) -> int:
        """Count workers without housing"""
        # Workers = production buildings (lumberjack, planter, miner, etc.)
        production_buildings = ["lumberjack", "planter", "miner", "fisher", "farmer"]
        worker_count = len([item for item in self.placed_items if item.get("type") in production_buildings])
        house_count = len([item for item in self.placed_items if item.get("type") == "house"])
        homeless_workers = max(0, worker_count - house_count)
        return homeless_workers
    
    def _get_warehouse_fill_percentage(self) -> float:
        """Calculate warehouse fill percentage (0-100)"""
        warehouses = [item for item in self.placed_items if item.get("type") == "warehouse"]
        if not warehouses:
            return 0.0
        
        warehouse = warehouses[0]
        storage = warehouse.get("storage", {})
        capacity = warehouse.get("capacity", 100)
        
        # Calculate total items
        total_items = sum(storage.values())
        fill_percent = (total_items / capacity) * 100 if capacity > 0 else 0
        
        return fill_percent
    
    def _decide_next_build(self) -> Dict:
        """
        Smart build decision based on priorities
        
        Returns: {"action": str, "priority": str, "reason": str}
        """
        # Get current state
        homeless = self._count_homeless_residents()
        homeless_workers = self._count_homeless_workers()
        warehouse_fill = self._get_warehouse_fill_percentage()
        spark_hp_percent = (self.spark.get("health", 500) / self.spark.get("max_health", 500)) * 100
        
        # CRITICAL PRIORITY
        if homeless > 0:
            return {
                "action": "build_house",
                "priority": "CRITICAL",
                "reason": f"{homeless} residents homeless"
            }
        
        if spark_hp_percent < 50:
            return {
                "action": "find_shelter",
                "priority": "CRITICAL",
                "reason": f"Spark HP low ({spark_hp_percent:.0f}%)"
            }
        
        # IMPORTANT PRIORITY
        if homeless_workers > 0:
            return {
                "action": "build_worker_house",
                "priority": "IMPORTANT",
                "reason": f"{homeless_workers} workers need housing"
            }
        
        if warehouse_fill < 50:
            return {
                "action": "gather_resources",
                "priority": "IMPORTANT",
                "reason": f"Warehouse only {warehouse_fill:.0f}% filled"
            }
        
        # Check night time
        if not self.game_time.get("is_day", True):
            if homeless + homeless_workers > 0:
                return {
                    "action": "urgent_shelter",
                    "priority": "IMPORTANT",
                    "reason": "Night time, people need shelter"
                }
        
        # LUXURY PRIORITY
        if warehouse_fill >= 50:
            return {
                "action": "build_monument",
                "priority": "LUXURY",
                "reason": f"Warehouse {warehouse_fill:.0f}% filled, monument allowed"
            }
        
        # DEFAULT: Keep gathering
        return {
            "action": "gather_resources",
            "priority": "DEFAULT",
            "reason": "No urgent needs"
        }
    
    # ============= BOT SYSTEM =============
    
    def _update_worker_bots(self):
        """
        Update all worker bots (warehouse runners) + koning entities
        
        State machine:
        - idle: Looking for work
        - move_to_resource: Moving to nearest resource
        - gathering: Picking up resource
        - move_to_dropoff: Moving to warehouse
        - delivering: Dropping off resource
        """
        # Check if we need to spawn worker bots
        self._check_bot_spawning()
        
        # Update each worker bot
        for bot in self.worker_bots:
            self._update_single_bot(bot)
        
        # NIEUW: Update koning entities from entity_manager
        entities = self.entity_manager.get_all_entities()
        for entity in entities:
            if entity.get('type') == 'king':
                self._update_single_bot(entity)
    
    def _check_bot_spawning(self):
        """
        Check if we should spawn worker bots
        
        Rules:
        - 1 warehouse runner per warehouse
        - Only spawn if warehouse exists and no runner assigned
        """
        # Find all warehouses
        warehouses = [item for item in self.placed_items if item["type"] == "warehouse"]
        
        # Debug: log warehouse count
        if self.stats["updates"] % 20 == 0 and len(warehouses) > 0:  # Every ~100 seconds
            logger.info(f"[BOT DEBUG] Checking spawn: {len(warehouses)} warehouses, {len(self.worker_bots)} bots")
        
        for warehouse in warehouses:
            # Check if this warehouse already has a runner
            has_runner = any(
                bot.get("linked_building_id") == warehouse["id"] 
                for bot in self.worker_bots
            )
            
            if not has_runner:
                # Spawn a warehouse runner
                bot = {
                    "id": f"bot_{len(self.worker_bots)}",
                    "name": f"Runner {len(self.worker_bots) + 1}",
                    "blueprint_id": "warehouse_runner",
                    "icon": "🏃",
                    "x": warehouse["x"],
                    "y": warehouse["y"],
                    "linked_building_id": warehouse["id"],
                    "linked_building_type": "warehouse",
                    "state": "idle",
                    "target": None,
                    "carry": {},
                    "carry_capacity": 20,
                    "speed": 1.5,
                    "retry_count": 0
                }
                self.worker_bots.append(bot)
                logger.info(f"[BOT] 🏃 Spawned warehouse runner for {warehouse['id']} at ({warehouse['x']}, {warehouse['y']})")
    
    def _update_single_bot(self, bot: Dict):
        """
        Update single bot behavior
        
        State machine with fail-safes
        """
        # Check bot type - different behavior
        bot_type = bot.get("type", "worker")
        faction = bot.get("faction", "neutral")
        
        if bot_type == "king":
            # King bot (autonomous leader) - like Spark
            self._update_king_bot(bot)
        elif faction == "hostile":
            # Zombie/hostile entity AI
            self._update_hostile_bot(bot)
        elif faction == "neutral":
            # Animal/neutral entity AI
            self._update_neutral_bot(bot)
        else:
            # Worker bot (warehouse runner, etc.)
            self._update_worker_bot(bot)
    
    def _update_worker_bot(self, bot: Dict):
        """Worker bot logic (warehouse runner)"""
        state = bot.get("state", "idle")
        
        # Get linked building (warehouse)
        warehouse = self._get_building_by_id(bot.get("linked_building_id"))
        if not warehouse:
            # [BOT TODO] Handle missing warehouse (deleted?)
            logger.warning(f"[BOT TODO] {bot['name']} - Warehouse {bot.get('linked_building_id')} not found! Resetting to idle")
            bot["state"] = "idle"
            bot["target"] = None
            bot["carry"] = {}
            return
        
        # STATE MACHINE
        if state == "idle":
            self._bot_state_idle(bot, warehouse)
        elif state == "move_to_resource":
            self._bot_state_move_to_resource(bot, warehouse)
        elif state == "gathering":
            self._bot_state_gathering(bot, warehouse)
        elif state == "move_to_dropoff":
            self._bot_state_move_to_dropoff(bot, warehouse)
        elif state == "delivering":
            self._bot_state_delivering(bot, warehouse)
        elif state == "move_to_home":
            self._bot_state_move_to_home(bot, warehouse)
        elif state == "waiting_at_home":
            self._bot_state_waiting_at_home(bot, warehouse)
        elif state == "move_to_warehouse_wait":
            self._bot_state_move_to_warehouse_wait(bot, warehouse)
        elif state == "waiting_at_warehouse":
            self._bot_state_waiting_at_warehouse(bot, warehouse)
        else:
            logger.error(f"[BOT] {bot['name']} - Unknown state: {state}")
            bot["state"] = "idle"
    
    def _update_hostile_bot(self, bot: Dict):
        """
        Hostile bot AI (Zombie)
        
        Distance-based behavior:
        - 5-6 blocks: detect only
        - 3-4 blocks: approach & attack
        - 1 block: combat
        """
        # Find nearest target (Spark or friendly entities)
        spark_dist = abs(bot["x"] - self.spark["x"]) + abs(bot["y"] - self.spark["y"])
        
        logger.info(f"[ZOMBIE DEBUG] {bot['name']} at ({bot['x']},{bot['y']}) | distance to Spark: {spark_dist} | health: {bot.get('health', 100)}/{bot.get('max_health', 100)}")
        
        if spark_dist >= 5:
            # Detect only - no action
            bot["state"] = "detected"
            bot["target"] = {"x": self.spark["x"], "y": self.spark["y"], "type": "spark"}
            
        elif spark_dist >= 3:
            # Approach & attack mode
            bot["state"] = "approach_attack"
            bot["target"] = {"x": self.spark["x"], "y": self.spark["y"], "type": "spark"}
            
            # Move towards Spark
            moved = self._move_bot_towards(bot, self.spark["x"], self.spark["y"])
            if not moved:
                logger.warning(f"[ZOMBIE] {bot['name']} blocked at ({bot['x']},{bot['y']})")
                
        elif spark_dist == 1:
            # Adjacent - COMBAT!
            bot["state"] = "combat"
            bot["target"] = {"x": self.spark["x"], "y": self.spark["y"], "type": "spark"}
            
            # Deal damage to Spark
            damage = bot.get("attack", 10)
            self.spark["health"] = max(0, self.spark["health"] - damage)
            
            logger.info(f"[COMBAT] 🧟 {bot['name']} attacks Spark! Damage: {damage} | Spark HP: {self.spark['health']}/{self.spark['max_health']}")
            
            # Spark counter-attack
            spark_damage = self.spark.get("attack", 20) - bot.get("defense", 0)
            spark_damage = max(1, spark_damage)  # Minimum 1 damage
            bot["health"] = max(0, bot.get("health", 100) - spark_damage)
            
            logger.info(f"[COMBAT] ⚡ Spark counter-attacks! Damage: {spark_damage} | Zombie HP: {bot['health']}/{bot.get('max_health', 100)}")
            
            # Check if zombie dead
            if bot["health"] <= 0:
                logger.info(f"[COMBAT] 💀 {bot['name']} defeated!")
                self.worker_bots.remove(bot)
                return
                
        else:
            # Close proximity - continue approach
            bot["state"] = "chase"
            moved = self._move_bot_towards(bot, self.spark["x"], self.spark["y"])
    
    def _update_neutral_bot(self, bot: Dict):
        """
        Neutral bot AI (Animals)
        
        Distance-based behavior:
        - 5-6 blocks: idle, grazing
        - 3-4 blocks: flee if approached
        - 1 block: panic flee
        """
        spark_dist = abs(bot["x"] - self.spark["x"]) + abs(bot["y"] - self.spark["y"])
        
        if spark_dist >= 5:
            # Safe distance - idle/grazing
            bot["state"] = "idle"
            
            # Random movement (10% chance)
            if self.stats["updates"] % 10 == 0 and random.random() < 0.1:
                directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
                dx, dy = random.choice(directions)
                new_x = bot["x"] + dx
                new_y = bot["y"] + dy
                
                if self._is_valid_bot_move(new_x, new_y):
                    bot["x"] = new_x
                    bot["y"] = new_y
                    
        elif spark_dist >= 3:
            # Flee mode
            bot["state"] = "flee"
            
            # Move away from Spark
            dx = 1 if bot["x"] < self.spark["x"] else -1
            dy = 1 if bot["y"] < self.spark["y"] else -1
            
            # Try to move away
            if self._is_valid_bot_move(bot["x"] - dx, bot["y"]):
                bot["x"] -= dx
            elif self._is_valid_bot_move(bot["x"], bot["y"] - dy):
                bot["y"] -= dy
                
        else:
            # Panic - fast flee
            bot["state"] = "panic"
            # Double flee distance
            for _ in range(2):
                dx = 1 if bot["x"] < self.spark["x"] else -1
                dy = 1 if bot["y"] < self.spark["y"] else -1
                
                if self._is_valid_bot_move(bot["x"] - dx, bot["y"]):
                    bot["x"] -= dx
                    break
    
    def _update_king_bot(self, bot: Dict):
        """
        King Bot AI (Autonomous Leader) - SAME AS SPARK
        
        🤴 Koning = Mini-Spark voor eigen fractie:
        - Verzamelt resources
        - Plaatst gebouwen (voor eigen fractie)
        - Reageert op combat dreigingen
        - Autonoom zoals Spark
        
        Faction strategieën:
        - Gaia (Terra): Farming & defense
        - Neptune (Aqua): Fishing & expansion
        - Vulcan (Ignis): Mining & aggression
        - Zephyr (Ventus): Exploration & trade
        """
        faction = bot.get("faction", "neutral")
        
        # KONING = MINI-SPARK!
        # Koningen gebruiken dezelfde logica als Spark maar voor hun eigen fractie
        
        # 1. CHECK FOR COMBAT THREATS (hoogste prioriteit)
        nearby_hostiles = self._find_nearby_hostiles(bot["x"], bot["y"], radius=20)
        if nearby_hostiles:
            bot["current_action"] = "fleeing"
            # Vlucht van hostiles (zoals Spark)
            hostile_x, hostile_y = nearby_hostiles[0]['x'], nearby_hostiles[0]['y']
            
            # Flee away from hostile
            flee_dx = -1 if hostile_x > bot['x'] else 1 if hostile_x < bot['x'] else 0
            flee_dy = -1 if hostile_y > bot['y'] else 1 if hostile_y < bot['y'] else 0
            
            new_x = bot['x'] + flee_dx
            new_y = bot['y'] + flee_dy
            
            if self._is_valid_bot_move(new_x, new_y):
                bot['x'] = new_x
                bot['y'] = new_y
                logger.info(f"[KING] 🏃 {bot['name']} ({faction}) - Fleeing from hostile!")
            return
        
        # 2. RESOURCE GATHERING (zoals Spark)
        # Check if koning needs resources
        inventory = bot.get("inventory", {})
        wood = inventory.get("wood", 0)
        stone = inventory.get("stone", 0)
        
        # If low on resources, gather
        if wood < 20 or stone < 10:
            # Find nearest resource
            nearest_tree = None
            nearest_stone = None
            min_tree_dist = 999
            min_stone_dist = 999
            
            # Search nearby area
            for dx in range(-15, 15):
                for dy in range(-15, 15):
                    check_x = bot['x'] + dx
                    check_y = bot['y'] + dy
                    
                    if not (0 <= check_x < 200 and 0 <= check_y < 200):
                        continue
                    
                    # Check for trees
                    if wood < 20:
                        for tree in self.trees:
                            if tree['x'] == check_x and tree['y'] == check_y:
                                dist = abs(dx) + abs(dy)
                                if dist < min_tree_dist:
                                    min_tree_dist = dist
                                    nearest_tree = tree
                    
                    # Check for stones
                    if stone < 10:
                        for s in self.stones:
                            if s['x'] == check_x and s['y'] == check_y:
                                dist = abs(dx) + abs(dy)
                                if dist < min_stone_dist:
                                    min_stone_dist = dist
                                    nearest_stone = s
            
            # Move towards resource
            target = nearest_tree if (wood < 20 and nearest_tree) else nearest_stone
            
            if target:
                bot["current_action"] = "gathering"
                
                # Check if at resource
                if bot['x'] == target['x'] and bot['y'] == target['y']:
                    # Gather resource!
                    resource_type = "wood" if target in self.trees else "stone"
                    amount = 3 if resource_type == "wood" else 2
                    
                    if resource_type not in inventory:
                        inventory[resource_type] = 0
                    inventory[resource_type] += amount
                    bot["inventory"] = inventory
                    
                    # Remove resource
                    if resource_type == "wood":
                        self.trees = [t for t in self.trees if not (t['x'] == target['x'] and t['y'] == target['y'])]
                    else:
                        self.stones = [s for s in self.stones if not (s['x'] == target['x'] and s['y'] == target['y'])]
                    
                    logger.info(f"[KING] 🪵 {bot['name']} gathered {amount} {resource_type}! Total: {inventory.get(resource_type, 0)}")
                else:
                    # Move towards target
                    dx = 1 if target['x'] > bot['x'] else -1 if target['x'] < bot['x'] else 0
                    dy = 1 if target['y'] > bot['y'] else -1 if target['y'] < bot['y'] else 0
                    new_x = bot['x'] + dx
                    new_y = bot['y'] + dy
                    
                    if self._is_valid_bot_move(new_x, new_y):
                        bot['x'] = new_x
                        bot['y'] = new_y
                
                return
        
        # 3. BUILDING PLACEMENT (zoals Spark)
        # Check if koning should build
        gaps = self._detect_production_gaps_for_faction(bot)
        
        if gaps and wood >= 15 and stone >= 10:
            bot["current_action"] = "building"
            
            # Place first missing building
            building_type = gaps[0]
            
            # Find placement near koning
            placed = False
            for offset in range(1, 10):
                for dx, dy in [(offset, 0), (-offset, 0), (0, offset), (0, -offset)]:
                    place_x = bot['x'] + dx
                    place_y = bot['y'] + dy
                    
                    if self._is_valid_building_spot(place_x, place_y):
                        # Place building!
                        building = {
                            "id": f"{building_type}_{faction}_{len(self.placed_items)}",
                            "type": building_type,
                            "x": place_x,
                            "y": place_y,
                            "faction": faction,
                            "owner": bot['name']
                        }
                        self.placed_items.append(building)
                        
                        # Deduct resources
                        inventory["wood"] -= 15
                        inventory["stone"] -= 10
                        bot["inventory"] = inventory
                        
                        logger.info(f"[KING] 🏗️ {bot['name']} ({faction}) - Built {building_type} at ({place_x}, {place_y})!")
                        placed = True
                        break
                if placed:
                    break
            
            return
        
        # 4. EXPLORATION (zoals Spark)
        bot["current_action"] = "exploring"
        
        # Move randomly (30% chance)
        if random.random() < 0.3:
            directions = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]
            dx, dy = random.choice(directions)
            new_x = bot["x"] + dx
            new_y = bot["y"] + dy
            
            if self._is_valid_bot_move(new_x, new_y):
                bot["x"] = new_x
                bot["y"] = new_y
                self.explored_tiles.add((new_x, new_y))
    
    def _detect_production_gaps_for_faction(self, king: Dict) -> list:
        """Detect missing buildings for specific faction"""
        gaps = []
        faction = king.get("faction", "neutral")
        
        # Check for essential buildings FOR THIS FACTION
        faction_buildings = [item for item in self.placed_items if item.get("faction") == faction]
        
        has_warehouse = any(b.get("type") == "warehouse" for b in faction_buildings)
        has_lumberjack = any(b.get("type") == "lumberjack" for b in faction_buildings)
        has_house = any(b.get("type") == "house" for b in faction_buildings)
        
        # Prioritized needs
        if not has_warehouse:
            gaps.append("warehouse")
        if not has_lumberjack:
            gaps.append("lumberjack")
        if not has_house:
            gaps.append("house")
        
        return gaps
    
    def _is_valid_building_spot(self, x: int, y: int) -> bool:
        """Check if location is valid for building placement"""
        # Check bounds
        if not (0 <= x < 200 and 0 <= y < 200):
            return False
        
        # Check terrain
        terrain = self.grid[y][x]
        if terrain in [1, 2]:  # Water or mountains
            return False
        
        # Check for existing buildings/trees
        if any(item['x'] == x and item['y'] == y for item in self.placed_items):
            return False
        if any(tree['x'] == x and tree['y'] == y for tree in self.trees):
            return False
        
        return True
    
    def _find_nearby_hostiles(self, x: int, y: int, radius: int) -> list:
        """Find hostile entities near position"""
        hostiles = []
        entities = self.entity_manager.get_all_entities()
        
        for entity in entities:
            # Check if hostile
            is_hostile = (
                entity.get('is_aggressive', False) or 
                entity.get('type') == 'undead' or 
                entity.get('faction') == 'enemy'
            )
            
            if is_hostile:
                dist = abs(entity['x'] - x) + abs(entity['y'] - y)
                if dist <= radius:
                    hostiles.append(entity)
        
        return hostiles
    
    def _detect_production_gaps(self, king: Dict) -> list:
        """
        Detect missing buildings/workers in production chain
        Returns list of needed buildings
        """
        gaps = []
        faction = king.get("faction", "neutral")
        
        # Check for essential buildings
        has_warehouse = any(item.get("type") == "warehouse" for item in self.placed_items)
        has_lumberjack = any(item.get("type") == "lumberjack" for item in self.placed_items)
        has_miner = any(item.get("type") == "miner" for item in self.placed_items)
        
        # Prioritized needs
        if not has_warehouse:
            gaps.append("warehouse")
        if not has_lumberjack:
            gaps.append("lumberjack")
        if not has_miner:
            gaps.append("miner")
        
        return gaps
    
    def _bot_state_idle(self, bot: Dict, warehouse: Dict):
        """
        IDLE STATE: Look for nearest resource to collect
        If no work: Go wait at home (or warehouse if no home)
        """
        # If carrying something, go deliver first
        if bot.get("carry"):
            logger.info(f"[BOT] {bot['name']} - Carrying items, switching to delivery")
            bot["state"] = "move_to_dropoff"
            bot["target"] = {"x": warehouse["x"], "y": warehouse["y"], "type": "warehouse"}
            return
        
        # Find nearest resource (wood or stone) within radius
        nearest = self._find_nearest_resource(bot["x"], bot["y"], radius=30)
        
        if nearest:
            bot["state"] = "move_to_resource"
            bot["target"] = nearest
            bot["retry_count"] = 0
            logger.info(f"[BOT DEBUG] {bot['name']} - state=move_to_resource | target={nearest['type']}@({nearest['x']},{nearest['y']}) | carry={self._format_carry(bot['carry'])} | pos=({bot['x']},{bot['y']})")
        else:
            # No resources found - GO WAIT AT HOME OR WAREHOUSE
            bot["retry_count"] = bot.get("retry_count", 0) + 1
            
            # Find assigned home for this worker
            assigned_home = self._find_worker_home(bot)
            
            if assigned_home:
                # Worker has a home - go wait there
                if bot["x"] == assigned_home["x"] and bot["y"] == assigned_home["y"]:
                    # Already at home - waiting
                    bot["state"] = "waiting_at_home"
                    if self.stats["updates"] % 50 == 0:  # Log occasionally
                        logger.info(f"[WORKER] {bot['name']} - Waiting at home ({assigned_home['x']}, {assigned_home['y']})")
                else:
                    # Move to home
                    bot["state"] = "move_to_home"
                    bot["target"] = {"x": assigned_home["x"], "y": assigned_home["y"], "type": "home"}
                    logger.info(f"[WORKER] {bot['name']} - No work, going home at ({assigned_home['x']}, {assigned_home['y']})")
            else:
                # No home - go wait at warehouse
                if bot["x"] == warehouse["x"] and bot["y"] == warehouse["y"]:
                    # Already at warehouse - waiting
                    bot["state"] = "waiting_at_warehouse"
                    if self.stats["updates"] % 50 == 0:
                        logger.info(f"[WORKER] {bot['name']} - Waiting at warehouse (no home)")
                else:
                    # Move to warehouse
                    bot["state"] = "move_to_warehouse_wait"
                    bot["target"] = {"x": warehouse["x"], "y": warehouse["y"], "type": "warehouse"}
                    logger.info(f"[WORKER] {bot['name']} - No work and no home, going to warehouse")
            
            if self.stats["updates"] % 20 == 0:  # Log every ~100 seconds
                logger.info(f"[BOT DEBUG] {bot['name']} - state=idle | target=None | carry=empty | pos=({bot['x']},{bot['y']}) | reason=no_resources_in_radius")
            
            # [BOT TODO] After many retries, expand search radius or change strategy
            if bot["retry_count"] > 50:
                logger.warning(f"[BOT TODO] {bot['name']} - Idle for {bot['retry_count']} updates, may need expanded search")
    
    def _find_worker_home(self, bot: Dict) -> Optional[Dict]:
        """
        Find assigned home for this worker
        For now: Find nearest empty house
        Future: Track home_building_id per worker
        """
        # Find all houses
        houses = [b for b in self.buildings if b.get("type") == "house"]
        
        if not houses:
            return None
        
        # Find nearest house (simple assignment for now)
        nearest_house = None
        min_dist = float('inf')
        
        for house in houses:
            dist = abs(house["x"] - bot["x"]) + abs(house["y"] - bot["y"])
            if dist < min_dist:
                min_dist = dist
                nearest_house = house
        
        return nearest_house
    
    def _bot_state_move_to_home(self, bot: Dict, warehouse: Dict):
        """
        Move to assigned home to wait
        """
        target = bot.get("target")
        if not target:
            bot["state"] = "idle"
            return
        
        # Move towards home
        moved = self._move_bot_towards(bot, target["x"], target["y"])
        
        # Check if arrived at home
        if bot["x"] == target["x"] and bot["y"] == target["y"]:
            bot["state"] = "waiting_at_home"
            bot["target"] = None
            logger.info(f"[WORKER] {bot['name']} - Arrived at home, waiting for work")
    
    def _bot_state_move_to_warehouse_wait(self, bot: Dict, warehouse: Dict):
        """
        Move to warehouse to wait (no home available)
        """
        target = bot.get("target")
        if not target:
            bot["state"] = "idle"
            return
        
        # Move towards warehouse
        moved = self._move_bot_towards(bot, target["x"], target["y"])
        
        # Check if arrived at warehouse
        if bot["x"] == target["x"] and bot["y"] == target["y"]:
            bot["state"] = "waiting_at_warehouse"
            bot["target"] = None
            logger.info(f"[WORKER] {bot['name']} - Arrived at warehouse, waiting for work")
    
    def _bot_state_waiting_at_home(self, bot: Dict, warehouse: Dict):
        """
        Waiting at home - check if new work available
        """
        # Check for new work
        nearest = self._find_nearest_resource(bot["x"], bot["y"], radius=50)  # Larger radius when waiting
        
        if nearest:
            # New work found! Leave home and start working
            bot["state"] = "move_to_resource"
            bot["target"] = nearest
            bot["retry_count"] = 0
            logger.info(f"[WORKER] {bot['name']} - New work found! Leaving home to gather {nearest['type']}")
    
    def _bot_state_waiting_at_warehouse(self, bot: Dict, warehouse: Dict):
        """
        Waiting at warehouse - check if new work available
        """
        # Check for new work
        nearest = self._find_nearest_resource(bot["x"], bot["y"], radius=50)  # Larger radius when waiting
        
        if nearest:
            # New work found! Leave warehouse and start working
            bot["state"] = "move_to_resource"
            bot["target"] = nearest
            bot["retry_count"] = 0
            logger.info(f"[WORKER] {bot['name']} - New work found! Leaving warehouse to gather {nearest['type']}")
    
    def _bot_state_move_to_resource(self, bot: Dict, warehouse: Dict):
        """
        MOVE_TO_RESOURCE STATE: Move towards target resource
        """
        target = bot.get("target")
        if not target:
            logger.warning(f"[BOT] {bot['name']} - No target in move_to_resource, resetting to idle")
            bot["state"] = "idle"
            return
        
        # Check if resource still exists
        resource = self._get_resource_at(target["x"], target["y"], target["type"])
        if not resource:
            logger.info(f"[BOT DEBUG] {bot['name']} - state=move_to_resource | target=GONE | carry={self._format_carry(bot['carry'])} | reason=resource_collected_by_other")
            bot["state"] = "idle"
            bot["target"] = None
            return
        
        # Check if adjacent to resource
        distance = abs(bot["x"] - target["x"]) + abs(bot["y"] - target["y"])
        if distance <= 1:
            # Adjacent! Start gathering
            bot["state"] = "gathering"
            logger.info(f"[BOT DEBUG] {bot['name']} - state=gathering | target={target['type']}@({target['x']},{target['y']}) | carry={self._format_carry(bot['carry'])}")
            return
        
        # Move towards resource
        moved = self._move_bot_towards(bot, target["x"], target["y"])
        if not moved:
            # Blocked or unreachable
            logger.warning(f"[BOT TODO] {bot['name']} - Cannot reach resource at ({target['x']},{target['y']}), resetting")
            bot["state"] = "idle"
            bot["target"] = None
            return
        
        # Log movement progress occasionally
        if self.stats["updates"] % 10 == 0:
            logger.info(f"[BOT DEBUG] {bot['name']} - state=move_to_resource | target={target['type']}@({target['x']},{target['y']}) | carry={self._format_carry(bot['carry'])} | pos=({bot['x']},{bot['y']}) | distance={distance}")
    
    def _bot_state_gathering(self, bot: Dict, warehouse: Dict):
        """
        GATHERING STATE: Pick up resource
        """
        target = bot.get("target")
        if not target:
            bot["state"] = "idle"
            return
        
        # Get resource
        resource = self._get_resource_at(target["x"], target["y"], target["type"])
        if not resource:
            logger.info(f"[BOT] {bot['name']} - Resource disappeared during gathering")
            bot["state"] = "idle"
            bot["target"] = None
            return
        
        # Calculate how much to pick up (respect carry capacity)
        resource_type = target["type"]
        if resource_type == "tree":
            amount = resource.get("wood_amount", 3)
            carry_key = "wood"
        elif resource_type == "stone":
            amount = resource.get("stone_amount", 2)
            carry_key = "stone"
        else:
            logger.error(f"[BOT] {bot['name']} - Unknown resource type: {resource_type}")
            bot["state"] = "idle"
            return
        
        # Check carry capacity
        current_carry = sum(bot["carry"].values())
        space_left = bot["carry_capacity"] - current_carry
        
        if space_left <= 0:
            # Full! Go deliver
            logger.info(f"[BOT DEBUG] {bot['name']} - state=move_to_dropoff | target=warehouse | carry={self._format_carry(bot['carry'])} | reason=capacity_full")
            bot["state"] = "move_to_dropoff"
            bot["target"] = {"x": warehouse["x"], "y": warehouse["y"], "type": "warehouse"}
            return
        
        # Pick up (partial if needed)
        pickup_amount = min(amount, space_left)
        bot["carry"][carry_key] = bot["carry"].get(carry_key, 0) + pickup_amount
        
        logger.info(f"[BOT DEBUG] {bot['name']} - state=gathering | target={resource_type} | carry={self._format_carry(bot['carry'])} | picked_up={pickup_amount}")
        
        # Remove resource from world
        if resource_type == "tree":
            self.trees.remove(resource)
            # Leave stump
            self.stumps.append({
                "id": f"stump_{resource['id']}",
                "x": resource["x"],
                "y": resource["y"],
                "wood_remaining": 1
            })
        elif resource_type == "stone":
            self.stones.remove(resource)
            # Regenerate stone elsewhere
            self.stones.append(self._generate_stones(1)[0])
        
        # Now go deliver
        bot["state"] = "move_to_dropoff"
        bot["target"] = {"x": warehouse["x"], "y": warehouse["y"], "type": "warehouse"}
    
    def _bot_state_move_to_dropoff(self, bot: Dict, warehouse: Dict):
        """
        MOVE_TO_DROPOFF STATE: Move to warehouse
        """
        # Check if at warehouse
        distance = abs(bot["x"] - warehouse["x"]) + abs(bot["y"] - warehouse["y"])
        if distance <= 1:
            # At warehouse! Deliver
            bot["state"] = "delivering"
            logger.info(f"[BOT DEBUG] {bot['name']} - state=delivering | target=warehouse | carry={self._format_carry(bot['carry'])}")
            return
        
        # Move towards warehouse
        moved = self._move_bot_towards(bot, warehouse["x"], warehouse["y"])
        if not moved:
            # Blocked - this is critical!
            logger.error(f"[BOT TODO] {bot['name']} - Cannot reach warehouse! Stuck at ({bot['x']},{bot['y']})")
            # For now, reset to idle (better than infinite loop)
            bot["state"] = "idle"
            bot["target"] = None
            return
        
        # Log occasionally
        if self.stats["updates"] % 10 == 0:
            logger.info(f"[BOT DEBUG] {bot['name']} - state=move_to_dropoff | target=warehouse@({warehouse['x']},{warehouse['y']}) | carry={self._format_carry(bot['carry'])} | pos=({bot['x']},{bot['y']}) | distance={distance}")
    
    def _bot_state_delivering(self, bot: Dict, warehouse: Dict):
        """
        DELIVERING STATE: Drop off resources at warehouse
        """
        if not bot.get("carry"):
            # Nothing to deliver
            bot["state"] = "idle"
            return
        
        # Transfer carry to warehouse storage
        if "storage" not in warehouse:
            warehouse["storage"] = {"wood": 0, "stone": 0, "fish": 0, "food": 0, "grain": 0, "flour": 0, "bread": 0, "plank": 0, "water": 0}
        
        for resource_type, amount in bot["carry"].items():
            warehouse["storage"][resource_type] = warehouse["storage"].get(resource_type, 0) + amount
        
        logger.info(f"[BOT DEBUG] {bot['name']} - state=delivering | target=warehouse | delivered={self._format_carry(bot['carry'])} | warehouse_total={self._format_carry(warehouse['storage'])}")
        
        # Clear carry
        bot["carry"] = {}
        
        # Back to idle to find next resource
        bot["state"] = "idle"
        bot["target"] = None
    
    # ============= BOT HELPER FUNCTIONS =============
    
    def _find_nearest_resource(self, x: int, y: int, radius: int = 30) -> Optional[Dict]:
        """
        Find nearest resource (tree or stone) within radius
        
        Performance: Only search within radius, not full grid
        """
        nearest = None
        min_distance = float('inf')
        
        # Search trees within radius
        for tree in self.trees:
            dx = abs(tree["x"] - x)
            dy = abs(tree["y"] - y)
            distance = dx + dy
            
            if distance <= radius and distance < min_distance:
                nearest = {"x": tree["x"], "y": tree["y"], "type": "tree"}
                min_distance = distance
        
        # Search stones within radius
        for stone in self.stones:
            dx = abs(stone["x"] - x)
            dy = abs(stone["y"] - y)
            distance = dx + dy
            
            if distance <= radius and distance < min_distance:
                nearest = {"x": stone["x"], "y": stone["y"], "type": "stone"}
                min_distance = distance
        
        return nearest
    
    def _get_resource_at(self, x: int, y: int, resource_type: str) -> Optional[Dict]:
        """Get resource at specific position"""
        if resource_type == "tree":
            for tree in self.trees:
                if tree["x"] == x and tree["y"] == y:
                    return tree
        elif resource_type == "stone":
            for stone in self.stones:
                if stone["x"] == x and stone["y"] == y:
                    return stone
        return None
    
    def _get_building_by_id(self, building_id: str) -> Optional[Dict]:
        """Get building by ID"""
        for item in self.placed_items:
            if item.get("id") == building_id:
                return item
        return None
    
    def _a_star_pathfinding(self, start_x: int, start_y: int, goal_x: int, goal_y: int, max_nodes: int = 500) -> Optional[List[Tuple[int, int]]]:
        """
        A* pathfinding algorithm to find shortest path avoiding obstacles
        
        Returns: List of (x, y) coordinates from start to goal, or None if no path found
        """
        # Early exit if start or goal is invalid
        if not self._is_valid_bot_move(goal_x, goal_y):
            return None
        
        if start_x == goal_x and start_y == goal_y:
            return [(start_x, start_y)]
        
        # Heuristic: Manhattan distance
        def heuristic(x, y):
            return abs(x - goal_x) + abs(y - goal_y)
        
        # Priority queue: (f_score, counter, (x, y), path)
        counter = 0
        open_set = [(heuristic(start_x, start_y), counter, (start_x, start_y), [])]
        closed_set = set()
        
        while open_set and counter < max_nodes:
            f_score, _, current, path = heapq.heappop(open_set)
            current_x, current_y = current
            
            # Goal reached
            if current_x == goal_x and current_y == goal_y:
                return path + [current]
            
            # Skip if already visited
            if current in closed_set:
                continue
            
            closed_set.add(current)
            
            # Explore neighbors (4 directions)
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                next_x, next_y = current_x + dx, current_y + dy
                next_pos = (next_x, next_y)
                
                # Skip if invalid or already visited
                if next_pos in closed_set:
                    continue
                
                if not self._is_valid_bot_move(next_x, next_y):
                    continue
                
                # Calculate scores
                g_score = len(path) + 1
                h_score = heuristic(next_x, next_y)
                f_score = g_score + h_score
                
                counter += 1
                heapq.heappush(open_set, (f_score, counter, next_pos, path + [current]))
        
        # No path found
        return None
    
    def _move_bot_towards(self, bot: Dict, target_x: int, target_y: int) -> bool:
        """
        Move bot one step towards target using A* pathfinding
        
        Returns: True if moved, False if blocked/no path
        """
        current_x, current_y = bot["x"], bot["y"]
        
        # Calculate path using A* (cache path in bot data for efficiency)
        if "cached_path" not in bot or not bot["cached_path"]:
            path = self._a_star_pathfinding(current_x, current_y, target_x, target_y)
            
            if not path:
                # No path found - try simple fallback
                logger.warning(f"[PATHFINDING] {bot.get('name', 'Bot')} - No A* path from ({current_x},{current_y}) to ({target_x},{target_y})")
                return self._simple_move_fallback(bot, target_x, target_y)
            
            # Store path (skip first element as it's current position)
            bot["cached_path"] = path[1:] if len(path) > 1 else []
            logger.debug(f"[PATHFINDING] {bot.get('name', 'Bot')} - Calculated path: {len(path)} steps")
        
        # Follow cached path
        if bot["cached_path"]:
            next_step = bot["cached_path"][0]
            next_x, next_y = next_step
            
            # Verify step is still valid (terrain may have changed)
            if self._is_valid_bot_move(next_x, next_y):
                bot["x"] = next_x
                bot["y"] = next_y
                bot["cached_path"].pop(0)  # Remove completed step
                
                # Clear cache if destination reached or destination changed
                if (next_x == target_x and next_y == target_y) or \
                   (bot["cached_path"] and bot["cached_path"][-1] != (target_x, target_y)):
                    bot["cached_path"] = []
                
                return True
            else:
                # Path blocked - recalculate next update
                logger.debug(f"[PATHFINDING] {bot.get('name', 'Bot')} - Path blocked, will recalculate")
                bot["cached_path"] = []
                return False
        
        return False
    
    def _simple_move_fallback(self, bot: Dict, target_x: int, target_y: int) -> bool:
        """
        Simple directional movement as fallback when A* fails
        (Original logic from before A* implementation)
        """
        current_x, current_y = bot["x"], bot["y"]
        
        # Calculate direction
        dx = 0 if target_x == current_x else (1 if target_x > current_x else -1)
        dy = 0 if target_y == current_y else (1 if target_y > current_y else -1)
        
        # Try to move diagonally first
        new_x = current_x + dx
        new_y = current_y + dy
        
        if self._is_valid_bot_move(new_x, new_y):
            bot["x"] = new_x
            bot["y"] = new_y
            return True
        
        # Try horizontal
        if dx != 0 and self._is_valid_bot_move(current_x + dx, current_y):
            bot["x"] = current_x + dx
            return True
        
        # Try vertical
        if dy != 0 and self._is_valid_bot_move(current_x, current_y + dy):
            bot["y"] = current_y + dy
            return True
        
        # Completely blocked
        return False
    
    def _is_valid_bot_move(self, x: int, y: int) -> bool:
        """Check if bot can move to this position"""
        # Check boundaries
        if not (0 <= x < self.grid_size and 0 <= y < self.grid_size):
            return False
        
        # NIEUW: Bots kunnen nu OVER water (water crossing enabled!)
        # Water is nu geldig terrein (geen return False meer)
        
        # Check trees (bots can't walk through trees)
        if any(t["x"] == x and t["y"] == y for t in self.trees):
            return False
        
        # Check mountains
        if any(m["x"] == x and m["y"] == y for m in self.mountains):
            return False
        
        # Check buildings (except warehouses and small items)
        if any(
            p["x"] == x and p["y"] == y 
            for p in self.placed_items 
            if p["type"] not in ["cropfield", "wall"]
        ):
            return False
        
        return True
    
    def _format_carry(self, carry: Dict) -> str:
        """Format carry dict for logging"""
        if not carry:
            return "empty"
        parts = [f"{k}:{v}" for k, v in carry.items()]
        return " ".join(parts)
    
    def _spark_auto_combat(self):
        """
        Spark automatically fights back when under attack
        """
        # Find nearby hostiles
        entities = self.entity_manager.get_all_entities()
        hostiles = []
        
        for entity in entities:
            # Check if hostile
            is_hostile = (
                entity.get('is_aggressive', False) or 
                entity.get('type') == 'undead' or 
                entity.get('faction') == 'enemy'
            )
            
            if is_hostile:
                dist = abs(entity['x'] - self.spark['x']) + abs(entity['y'] - self.spark['y'])
                if dist <= 2:  # Attack range (slightly larger than zombie range)
                    hostiles.append((entity, dist))
        
        if hostiles:
            # Fight closest hostile
            hostiles.sort(key=lambda x: x[1])
            target, dist = hostiles[0]
            
            # SPARK FIGHTS BACK!
            spark_damage = self.spark.get('attack', 20)  # Spark attack power
            target['health'] = max(0, target.get('health', 100) - spark_damage)
            
            self.spark['current_action'] = 'fighting'
            
            logger.info(f"[COMBAT] ⚔️ Spark fights back! Attacks {target.get('name', 'hostile')} for {spark_damage} damage! HP: {target['health']}")
            
            # Check if target died
            if target['health'] <= 0:
                self.entity_manager.remove_entity(target['id'])
                logger.info(f"[COMBAT] 💀 Spark killed {target.get('name', 'hostile')}!")
                
                # Reset Spark action
                self.spark['current_action'] = 'exploring'
        else:
            # No hostiles nearby - reset combat action
            if self.spark.get('current_action') == 'fighting':
                self.spark['current_action'] = 'exploring'
    
    def _update_zombies(self):
        """Zombie roaming + attack AI"""
        entities = self.entity_manager.get_all_entities()
        # Find all hostile entities (zombies, enemies) - check is_aggressive flag OR undead type
        zombies = [e for e in entities if (
            e.get('is_aggressive', False) or 
            e.get('type') == 'undead' or 
            'zombie' in e.get('name', '').lower()
        )]
        
        for zombie in zombies:
            # Find nearby targets (Spark, bots, kings)
            targets = []
            
            # Spark as target
            spark_dist = abs(zombie['x'] - self.spark['x']) + abs(zombie['y'] - self.spark['y'])
            if spark_dist < 15:
                targets.append(('spark', self.spark, spark_dist))
            
            # All entities as targets (exclude other hostiles)
            for entity in entities:
                # Don't target other zombies/hostiles
                is_hostile = (
                    entity.get('is_aggressive', False) or 
                    entity.get('type') == 'undead' or 
                    entity.get('faction') == 'enemy'
                )
                
                if entity['id'] != zombie['id'] and not is_hostile:
                    dist = abs(zombie['x'] - entity['x']) + abs(zombie['y'] - entity['y'])
                    if dist < 15:
                        targets.append(('entity', entity, dist))
            
            if targets:
                # Attack closest target
                targets.sort(key=lambda t: t[2])
                target_type, target, dist = targets[0]
                
                if dist <= 1.5:  # Attack range
                    # ATTACK!
                    damage = zombie.get('power', zombie.get('damage', 5))
                    target['health'] = max(0, target.get('health', 100) - damage)
                    
                    # Set combat status
                    zombie['current_action'] = 'fighting'
                    if target_type == 'spark':
                        self.spark['current_action'] = 'fighting'
                    else:
                        target['current_action'] = 'fighting'
                    
                    logger.info(f"[ZOMBIE] 🧟 {zombie['name']} attacks {target.get('name', 'target')} for {damage} damage! HP: {target['health']}")
                    
                    # Remove if dead
                    if target['health'] <= 0:
                        if target_type == 'spark':
                            logger.warning(f"[COMBAT] ⚠️ Spark died!")
                        else:
                            self.entity_manager.remove_entity(target['id'])
                            logger.info(f"[COMBAT] 💀 {target.get('name')} died!")
                else:
                    # Move toward target
                    zombie['current_action'] = 'chasing'
                    dx = 1 if target['x'] > zombie['x'] else -1 if target['x'] < zombie['x'] else 0
                    dy = 1 if target['y'] > zombie['y'] else -1 if target['y'] < zombie['y'] else 0
                    new_x = zombie['x'] + dx
                    new_y = zombie['y'] + dy
                    
                    if self._is_valid_bot_move(new_x, new_y):
                        zombie['x'] = new_x
                        zombie['y'] = new_y
            else:
                # Random roam
                zombie['current_action'] = 'roaming'
                import random
                dx = random.choice([-1, 0, 1])
                dy = random.choice([-1, 0, 1])
                new_x = zombie['x'] + dx
                new_y = zombie['y'] + dy
                
                if self._is_valid_bot_move(new_x, new_y):
                    zombie['x'] = new_x
                    zombie['y'] = new_y
    
    def _update_towers(self):
        """Tower auto-attack nearby hostiles"""
        towers = [item for item in self.placed_items if item.get('type') == 'tower']
        entities = self.entity_manager.get_all_entities()
        # Find all hostile entities (zombies, enemies) - check is_aggressive flag OR undead type
        hostiles = [e for e in entities if (
            e.get('is_aggressive', False) or 
            e.get('type') == 'undead' or 
            e.get('faction') == 'enemy'
        )]
        
        for tower in towers:
            tower_range = 10
            tower_damage = 15
            
            # Find nearest hostile
            nearest = None
            nearest_dist = 999
            
            for hostile in hostiles:
                dist = abs(tower['x'] - hostile['x']) + abs(tower['y'] - hostile['y'])
                if dist <= tower_range and dist < nearest_dist:
                    nearest = hostile
                    nearest_dist = dist
            
            if nearest:
                # Attack!
                nearest['health'] = max(0, nearest.get('health', 100) - tower_damage)
                logger.info(f"[TOWER] 🗼 Tower at ({tower['x']}, {tower['y']}) attacks {nearest.get('name', 'hostile')} for {tower_damage} damage! HP: {nearest['health']}")
                
                # Remove if dead
                if nearest['health'] <= 0:
                    self.entity_manager.remove_entity(nearest['id'])
                    logger.info(f"[TOWER] 💀 {nearest.get('name')} eliminated!")

# Global game instance
_game_instance = None

def get_game_instance() -> GameEngine:
    """Get or create the global game instance"""
    global _game_instance
    if _game_instance is None:
        _game_instance = GameEngine()
    return _game_instance

def update_game() -> Dict:
    """Update the game and return new state - CRASH-SAFE wrapper"""
    try:
        game = get_game_instance()
        return game.update()
    except Exception as e:
        logger.error(f"[CRITICAL] Game update crashed: {e}", exc_info=True)
        # Return minimal safe state to prevent frontend crash
        return {
            "error": "Game update failed",
            "message": str(e),
            "spark": {"x": 50, "y": 50, "inventory": {}, "health": 100, "energy": 100},
            "trees": [],
            "stones": [],
            "grid_size": 200
        }
