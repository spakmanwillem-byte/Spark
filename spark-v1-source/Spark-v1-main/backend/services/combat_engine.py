"""
COMBAT ENGINE - 2-Layer Rock-Paper-Scissors System
===================================================

Layer 1: BOT ACTION (Individual RPS)
- Attack (🗡️) beats Passief (📜)
- Defend (🛡️) beats Attack (🗡️)
- Passief (📜) beats Defend (🛡️)

Layer 2: FORMATION STANCE (Group Buffs)
- Attack Stance: +2 attack, -1 defend (Archers, Cavalry)
- Defend Stance: +2 defend, -1 attack (Infantry, Shield Wall)
- Passief Stance: +1 all, no penalty (Flanking, Support)

Discipline Bonus:
- High discipline (80-100): +1 to all stats
- Medium discipline (50-79): +0
- Low discipline (0-49): -1 to all stats

Formation Types:
- Infantry: Defend stance, medium discipline
- Archers: Attack stance, low discipline
- Cavalry: Attack stance, high discipline
- Flanking: Passief stance, medium discipline

Supports:
- Single bot combat (individual action)
- Formation combat (group stance + discipline)
- AI behavior (worker flee, soldier fight)
"""

import logging
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)

# ============= CONSTANTS =============

# Action types (Layer 1 - Individual Bot)
ACTION_ATTACK = "attack"
ACTION_DEFEND = "defend"
ACTION_PASSIEF = "passief"

# Stance types (Layer 2 - Formation/Group)
STANCE_ATTACK = "attack"
STANCE_DEFEND = "defend"
STANCE_PASSIEF = "passief"

# Formation types
FORMATION_INFANTRY = "infantry"      # Defend stance, disciplined
FORMATION_ARCHERS = "archers"        # Attack stance, low discipline
FORMATION_CAVALRY = "cavalry"        # Attack stance, high discipline
FORMATION_FLANKING = "flanking"      # Passief stance, flexible

# NIEUW: Formation shapes (visual RPS)
SHAPE_TRIANGLE = "triangle"    # 🔺 Schaar (attack) - offensive wedge
SHAPE_CIRCLE = "circle"        # ⭕ Steen (defend) - shield circle
SHAPE_RECTANGLE = "rectangle"  # ⬜ Papier (passief) - flexible line

# Shape to Stance mapping
SHAPE_TO_STANCE = {
    SHAPE_TRIANGLE: STANCE_ATTACK,   # Triangle = aggressive wedge
    SHAPE_CIRCLE: STANCE_DEFEND,     # Circle = defensive ring
    SHAPE_RECTANGLE: STANCE_PASSIEF  # Rectangle = flexible formation
}

# Formation size limits
MAX_FORMATION_SIZE = 10  # 2 rows of 5
MAX_CIRCLE_SIZE = 12     # For circular formations

# Formation configurations
FORMATION_CONFIGS = {
    FORMATION_INFANTRY: {
        "default_stance": STANCE_DEFEND,
        "default_shape": SHAPE_RECTANGLE,  # Line formation
        "base_discipline": 70,
        "description": "Heavy infantry, defensive formation"
    },
    FORMATION_ARCHERS: {
        "default_stance": STANCE_ATTACK,
        "default_shape": SHAPE_RECTANGLE,  # Firing line
        "base_discipline": 40,
        "description": "Ranged attackers, vulnerable in melee"
    },
    FORMATION_CAVALRY: {
        "default_stance": STANCE_ATTACK,
        "default_shape": SHAPE_TRIANGLE,   # Wedge charge!
        "base_discipline": 85,
        "description": "Fast cavalry, devastating charge"
    },
    FORMATION_FLANKING: {
        "default_stance": STANCE_PASSIEF,
        "default_shape": SHAPE_CIRCLE,     # Encircle
        "base_discipline": 60,
        "description": "Flexible flanking units"
    }
}

# RPS counters (Layer 1)
ACTION_COUNTERS = {
    ACTION_ATTACK: ACTION_DEFEND,   # Defend beats Attack
    ACTION_DEFEND: ACTION_PASSIEF,  # Passief beats Defend
    ACTION_PASSIEF: ACTION_ATTACK   # Attack beats Passief
}

# Stance modifiers (Layer 2)
STANCE_MODIFIERS = {
    STANCE_ATTACK: {"attack": +2, "defend": -1},
    STANCE_DEFEND: {"attack": -1, "defend": +2},
    STANCE_PASSIEF: {"attack": +1, "defend": +1}
}

# Unit types and behaviors
UNIT_BEHAVIORS = {
    "worker": "flee",      # Workers run away
    "soldier": "fight",    # Soldiers fight back
    "archer": "ranged",    # Archers attack from distance
    "cavalry": "charge"    # Cavalry charges
}

# ============= COMBAT CALCULATOR =============

class CombatEngine:
    """2-Layer RPS Combat System"""
    
    @staticmethod
    def calculate_combat(
        attacker: Dict,
        defender: Dict,
        attacker_action: str = ACTION_ATTACK,
        defender_action: str = ACTION_DEFEND,
        attacker_stance: str = STANCE_ATTACK,
        defender_stance: str = STANCE_DEFEND,
        attacker_discipline: int = 50,
        defender_discipline: int = 50
    ) -> Dict:
        """
        Calculate combat result between two units/formations
        
        Args:
            attacker: {
                "units": 5, 
                "type": "soldier", 
                "power": 10,
                "formation_type": "infantry" (optional)
            }
            defender: {
                "units": 3, 
                "type": "worker", 
                "power": 5
            }
            attacker_action: attack/defend/passief (individual bot action)
            defender_action: attack/defend/passief
            attacker_stance: attack/defend/passief (formation stance)
            defender_stance: attack/defend/passief
            attacker_discipline: 0-100 (formation discipline)
            defender_discipline: 0-100
        
        Returns:
            {
                "winner": "attacker" | "defender" | "draw",
                "attacker_losses": 2,
                "defender_losses": 1,
                "damage_dealt": 15,
                "advantage": "attacker" | "defender" | "none"
            }
        """
        
        # Layer 1: Check action RPS advantage (BOT level)
        advantage = CombatEngine._check_action_advantage(attacker_action, defender_action)
        
        # Layer 2: Apply stance modifiers (FORMATION level)
        attacker_power = CombatEngine._apply_stance(
            attacker.get("power", 10),
            attacker_stance,
            attacker_action
        )
        defender_power = CombatEngine._apply_stance(
            defender.get("power", 10),
            defender_stance,
            defender_action
        )
        
        # NIEUW: Layer 3: Apply discipline bonus
        attacker_power = CombatEngine._apply_discipline_bonus(
            attacker_power,
            attacker_discipline
        )
        defender_power = CombatEngine._apply_discipline_bonus(
            defender_power,
            defender_discipline
        )
        
        # Scale by unit count (formation support)
        attacker_total = attacker_power * attacker.get("units", 1)
        defender_total = defender_power * defender.get("units", 1)
        
        # Apply RPS advantage bonus (50% boost)
        if advantage == "attacker":
            attacker_total *= 1.5  # 50% bonus for winning RPS
        elif advantage == "defender":
            defender_total *= 1.5
        
        # Calculate damage and losses
        damage_to_defender = max(0, attacker_total - defender_total * 0.5)
        damage_to_attacker = max(0, defender_total - attacker_total * 0.5)
        
        # Convert damage to unit losses (simplified)
        defender_losses = min(
            defender.get("units", 1),
            int(damage_to_defender / defender.get("power", 10))
        )
        attacker_losses = min(
            attacker.get("units", 1),
            int(damage_to_attacker / attacker.get("power", 10))
        )
        
        # Determine winner
        if attacker_total > defender_total:
            winner = "attacker"
        elif defender_total > attacker_total:
            winner = "defender"
        else:
            winner = "draw"
        
        result = {
            "winner": winner,
            "attacker_losses": attacker_losses,
            "defender_losses": defender_losses,
            "damage_dealt": int(damage_to_defender),
            "damage_received": int(damage_to_attacker),
            "advantage": advantage,
            "attacker_total_power": int(attacker_total),
            "defender_total_power": int(defender_total),
            "attacker_discipline_bonus": CombatEngine._get_discipline_bonus(attacker_discipline),
            "defender_discipline_bonus": CombatEngine._get_discipline_bonus(defender_discipline)
        }
        
        formation_type = attacker.get("formation_type", "unknown")
        logger.info(f"[COMBAT] {formation_type} ({attacker.get('type')}) vs {defender.get('type')} - Winner: {winner} (Advantage: {advantage})")
        
        return result
    
    @staticmethod
    def _check_action_advantage(action1: str, action2: str) -> str:
        """
        Check RPS advantage (Layer 1)
        Returns: "attacker" | "defender" | "none"
        """
        if ACTION_COUNTERS.get(action2) == action1:
            return "attacker"  # action1 beats action2
        elif ACTION_COUNTERS.get(action1) == action2:
            return "defender"  # action2 beats action1
        else:
            return "none"  # Same action or invalid
    
    @staticmethod
    def _apply_stance(base_power: int, stance: str, action: str) -> int:
        """
        Apply stance modifier (Layer 2)
        """
        modifiers = STANCE_MODIFIERS.get(stance, {})
        
        # Get modifier for the action type
        modifier = modifiers.get(action, 0)
        
        return base_power + modifier
    
    @staticmethod
    def _get_discipline_bonus(discipline: int) -> int:
        """
        Get discipline bonus based on discipline value
        
        - High (80-100): +1
        - Medium (50-79): +0
        - Low (0-49): -1
        """
        if discipline >= 80:
            return +1
        elif discipline >= 50:
            return 0
        else:
            return -1
    
    @staticmethod
    def _apply_discipline_bonus(power: int, discipline: int) -> int:
        """
        Apply discipline bonus to power
        """
        bonus = CombatEngine._get_discipline_bonus(discipline)
        return power + bonus
    
    @staticmethod
    def get_formation_positions(shape: str, num_units: int) -> List[Tuple[int, int]]:
        """
        Get visual positions for units in formation shape
        
        Returns list of (x, y) offsets from formation center
        For rendering on canvas later!
        
        Args:
            shape: "triangle", "circle", "rectangle"
            num_units: number of units in formation
        
        Returns:
            [(x1, y1), (x2, y2), ...] - relative positions
        """
        positions = []
        
        if shape == SHAPE_RECTANGLE:
            # 2 rows of 5 (or less)
            row_size = 5
            for i in range(num_units):
                row = i // row_size
                col = i % row_size
                # Center the formation
                x = col - row_size // 2
                y = row - 1
                positions.append((x, y))
        
        elif shape == SHAPE_TRIANGLE:
            # Wedge formation: 1, 2, 3, 4...
            # Example for 6 units:
            #     X
            #    X X
            #   X X X
            row = 0
            units_placed = 0
            while units_placed < num_units:
                units_in_row = min(row + 1, num_units - units_placed)
                for col in range(units_in_row):
                    x = col - units_in_row // 2
                    y = row
                    positions.append((x, y))
                    units_placed += 1
                row += 1
        
        elif shape == SHAPE_CIRCLE:
            # Circular formation
            import math
            radius = 2  # Circle radius
            angle_step = (2 * math.pi) / num_units
            
            for i in range(num_units):
                angle = i * angle_step
                x = int(radius * math.cos(angle))
                y = int(radius * math.sin(angle))
                positions.append((x, y))
        
        return positions
    
    @staticmethod
    def decide_ai_behavior(unit_type: str, situation: Dict) -> Dict:
        """
        Decide AI behavior based on unit type and situation
        
        Args:
            unit_type: "worker", "soldier", etc.
            situation: {
                "enemy_nearby": bool,
                "enemy_strength": int,
                "own_strength": int,
                "is_outnumbered": bool
            }
        
        Returns:
            {
                "behavior": "flee" | "fight" | "defend" | "passief",
                "action": "attack" | "defend" | "passief",
                "stance": "attack" | "defend" | "passief",
                "move_to": (x, y) or None
            }
        """
        behavior = UNIT_BEHAVIORS.get(unit_type, "flee")
        
        # Worker behavior: always flee
        if behavior == "flee":
            return {
                "behavior": "flee",
                "action": ACTION_PASSIEF,
                "stance": STANCE_DEFEND,
                "move_to": "away_from_enemy"
            }
        
        # Soldier behavior: fight or defend based on situation
        elif behavior == "fight":
            if situation.get("is_outnumbered", False):
                # Outnumbered → defensive stance
                return {
                    "behavior": "defend",
                    "action": ACTION_DEFEND,
                    "stance": STANCE_DEFEND,
                    "move_to": None
                }
            else:
                # Not outnumbered → attack
                return {
                    "behavior": "attack",
                    "action": ACTION_ATTACK,
                    "stance": STANCE_ATTACK,
                    "move_to": "towards_enemy"
                }
        
        # Default: passief
        return {
            "behavior": "passief",
            "action": ACTION_PASSIEF,
            "stance": STANCE_PASSIEF,
            "move_to": None
        }
    
    @staticmethod
    def form_formation(units: List[Dict], formation_type: str = FORMATION_INFANTRY, shape: str = None) -> Dict:
        """
        Create formation from individual units with formation type and shape
        
        Args:
            units: [{"type": "soldier", "power": 10}, ...]
            formation_type: "infantry", "archers", "cavalry", "flanking"
            shape: "triangle", "circle", "rectangle" (optional, uses default from type)
        
        Returns:
            {
                "units": 5, 
                "type": "soldier", 
                "power": 10, 
                "total_power": 50,
                "formation_type": "infantry",
                "shape": "rectangle",
                "default_stance": "defend",
                "discipline": 70
            }
        """
        if not units:
            return {"units": 0, "type": "none", "power": 0, "total_power": 0}
        
        # Check formation size limits
        max_size = MAX_CIRCLE_SIZE if shape == SHAPE_CIRCLE else MAX_FORMATION_SIZE
        if len(units) > max_size:
            logger.warning(f"Formation too large! Max {max_size} units, got {len(units)}. Trimming...")
            units = units[:max_size]
        
        # Get formation config
        formation_config = FORMATION_CONFIGS.get(formation_type, FORMATION_CONFIGS[FORMATION_INFANTRY])
        
        # Determine shape (use provided or default from formation type)
        formation_shape = shape if shape else formation_config.get("default_shape", SHAPE_RECTANGLE)
        
        # Shape determines stance!
        shape_stance = SHAPE_TO_STANCE.get(formation_shape, formation_config["default_stance"])
        
        # For simplicity, use most common unit type
        unit_types = [u.get("type", "worker") for u in units]
        most_common = max(set(unit_types), key=unit_types.count)
        
        # Average power
        avg_power = sum(u.get("power", 10) for u in units) / len(units)
        
        formation = {
            "units": len(units),
            "type": most_common,
            "power": int(avg_power),
            "total_power": int(avg_power * len(units)),
            "formation_type": formation_type,
            "shape": formation_shape,
            "default_stance": shape_stance,  # Stance determined by shape!
            "discipline": formation_config["base_discipline"]
        }
        
        logger.info(f"[FORMATION] Created {formation_shape} {formation_type}: {len(units)} {most_common}s (Stance: {shape_stance}, Disc: {formation['discipline']})")
        
        return formation

# ============= COMBAT SCENARIOS (Examples) =============

def example_single_combat():
    """Example: Single bot combat (individual action)"""
    attacker = {"units": 1, "type": "soldier", "power": 10}
    defender = {"units": 1, "type": "worker", "power": 5}
    
    result = CombatEngine.calculate_combat(
        attacker, defender,
        attacker_action=ACTION_ATTACK,  # Bot action
        defender_action=ACTION_DEFEND,  # Bot action (Defend beats Attack!)
        attacker_stance=STANCE_ATTACK,  # No formation, but individual stance
        defender_stance=STANCE_DEFEND,
        attacker_discipline=50,  # Medium discipline
        defender_discipline=30   # Low discipline
    )
    
    print("=== Single Bot Combat ===")
    print(f"Winner: {result['winner']}")
    print(f"Advantage: {result['advantage']}")
    print(f"Attacker power: {result['attacker_total_power']} (discipline: {result['attacker_discipline_bonus']})")
    print(f"Defender power: {result['defender_total_power']} (discipline: {result['defender_discipline_bonus']})")
    return result

def example_formation_combat():
    """Example: Formation combat with stance"""
    # Attacker: Infantry formation (Defend stance, high discipline)
    attacker_units = [
        {"type": "soldier", "power": 10},
        {"type": "soldier", "power": 10},
        {"type": "soldier", "power": 10}
    ]
    attacker_formation = CombatEngine.form_formation(attacker_units, FORMATION_INFANTRY)
    
    # Defender: Archers formation (Attack stance, low discipline)
    defender_units = [
        {"type": "archer", "power": 8},
        {"type": "archer", "power": 8}
    ]
    defender_formation = CombatEngine.form_formation(defender_units, FORMATION_ARCHERS)
    
    result = CombatEngine.calculate_combat(
        attacker_formation,
        defender_formation,
        attacker_action=ACTION_DEFEND,   # Infantry defends
        defender_action=ACTION_ATTACK,   # Archers attack
        attacker_stance=attacker_formation["default_stance"],  # Defend
        defender_stance=defender_formation["default_stance"],  # Attack
        attacker_discipline=attacker_formation["discipline"],  # 70
        defender_discipline=defender_formation["discipline"]   # 40
    )
    
    print("\n=== Formation Combat ===")
    print(f"Infantry (Defend stance, disc 70) vs Archers (Attack stance, disc 40)")
    print(f"Winner: {result['winner']}")
    print(f"Advantage: {result['advantage']} (Action RPS)")
    print(f"Infantry total: {result['attacker_total_power']} (with discipline +{result['attacker_discipline_bonus']})")
    print(f"Archers total: {result['defender_total_power']} (with discipline {result['defender_discipline_bonus']})")
    return result

def example_cavalry_charge():
    """Example: Cavalry charge (high discipline attack)"""
    # Cavalry formation (Attack stance, very high discipline)
    cavalry_units = [
        {"type": "cavalry", "power": 12},
        {"type": "cavalry", "power": 12},
        {"type": "cavalry", "power": 12},
        {"type": "cavalry", "power": 12}
    ]
    cavalry = CombatEngine.form_formation(cavalry_units, FORMATION_CAVALRY)  # Triangle wedge!
    
    # Infantry defender
    infantry_units = [
        {"type": "soldier", "power": 10},
        {"type": "soldier", "power": 10},
        {"type": "soldier", "power": 10}
    ]
    infantry = CombatEngine.form_formation(infantry_units, FORMATION_INFANTRY)  # Rectangle line
    
    result = CombatEngine.calculate_combat(
        cavalry,
        infantry,
        attacker_action=ACTION_ATTACK,
        defender_action=ACTION_DEFEND,
        attacker_stance=cavalry["default_stance"],     # Attack (from triangle)
        defender_stance=infantry["default_stance"],    # Defend (from rectangle)
        attacker_discipline=cavalry["discipline"],     # 85 (high!)
        defender_discipline=infantry["discipline"]     # 70
    )
    
    print("\n=== Cavalry Charge ===")
    print(f"🔺 Cavalry (triangle, 4 units, disc 85) charges ⬜ Infantry (rectangle, 3 units, disc 70)")
    print(f"Winner: {result['winner']}")
    print(f"Cavalry power: {result['attacker_total_power']} (+{result['attacker_discipline_bonus']} discipline)")
    print(f"Infantry power: {result['defender_total_power']} (+{result['defender_discipline_bonus']} discipline)")
    return result

def example_shape_tactics():
    """Example: Different shapes change stance"""
    units = [
        {"type": "soldier", "power": 10},
        {"type": "soldier", "power": 10},
        {"type": "soldier", "power": 10},
        {"type": "soldier", "power": 10},
        {"type": "soldier", "power": 10}
    ]
    
    print("\n=== Formation Shape Tactics ===")
    print("Same 5 soldiers, different shapes:")
    
    # Triangle formation (Attack)
    triangle = CombatEngine.form_formation(units, FORMATION_INFANTRY, shape=SHAPE_TRIANGLE)
    print(f"🔺 Triangle: stance={triangle['default_stance']} (attack)")
    
    # Circle formation (Defend)
    circle = CombatEngine.form_formation(units, FORMATION_INFANTRY, shape=SHAPE_CIRCLE)
    print(f"⭕ Circle: stance={circle['default_stance']} (defend)")
    
    # Rectangle formation (Passief)
    rectangle = CombatEngine.form_formation(units, FORMATION_INFANTRY, shape=SHAPE_RECTANGLE)
    print(f"⬜ Rectangle: stance={rectangle['default_stance']} (passief)")
    
    print("\nShape = Visual RPS! Change shape → change tactics!")
    
    return {"triangle": triangle, "circle": circle, "rectangle": rectangle}

if __name__ == "__main__":
    print("=== COMBAT ENGINE TESTS ===\n")
    example_single_combat()
    example_formation_combat()
    example_cavalry_charge()
    example_shape_tactics()
    
    print("\n=== FORMATION SHAPES ===")
    print(f"🔺 Triangle: Attack stance (offensive wedge) - Max {MAX_FORMATION_SIZE} units")
    print(f"⭕ Circle: Defend stance (shield ring) - Max {MAX_CIRCLE_SIZE} units")
    print(f"⬜ Rectangle: Passief stance (flexible line) - Max {MAX_FORMATION_SIZE} units")
    
    print("\n=== FORMATION CONFIGS ===")
    for name, config in FORMATION_CONFIGS.items():
        print(f"{name}: shape={config['default_shape']}, stance={config['default_stance']}, discipline={config['base_discipline']}")
