"""
Knowledge → Game Integration Service
Koppelt bestaande knowledge base aan game resources en buildings
"""
import json
import os
import logging

logger = logging.getLogger(__name__)

KNOWLEDGE_BASE_PATH = "/app/backend/data/learned_knowledge/knowledge_base.json"

# RESOURCE MAPPING: Knowledge begrip → Game resource
RESOURCE_MAPPING = {
    "boom": "wood",      # boom knowledge → hout verzamelen
    "berg": "stone",     # berg knowledge → steen verzamelen
    "water": "water",    # water knowledge → water verzamelen
}

# BUILDING UNLOCKS: Knowledge begrip → Gebouwen
BUILDING_UNLOCKS = {
    "hout": ["lumberjack", "sawmill", "house"],          # hout → houthakker, zagerij, huis
    "steen": ["quarry", "house", "monument", "storage"], # steen → steengroeve, huis, monument, opslag
    "boom": ["forester", "planter"],                     # boom → boswachter, planter
}

def load_user_knowledge():
    """
    Laad alle knowledge entries van user
    Returns: List van begrippen die user kent
    """
    try:
        if not os.path.exists(KNOWLEDGE_BASE_PATH):
            logger.warning(f"[KNOWLEDGE] No knowledge base found at {KNOWLEDGE_BASE_PATH}")
            return []
        
        with open(KNOWLEDGE_BASE_PATH, 'r') as f:
            data = json.load(f)
            entries = data.get('knowledge_entries', [])
            
            # Extract begrippen (concepten)
            begrippen = [e.get('begrip', '').lower() for e in entries if e.get('begrip')]
            
            logger.info(f"[KNOWLEDGE] Loaded {len(begrippen)} unique concepts")
            return begrippen
            
    except Exception as e:
        logger.error(f"[KNOWLEDGE] Error loading knowledge: {e}")
        return []

def can_collect_resource(resource_type: str) -> bool:
    """
    Check of user resource mag verzamelen op basis van knowledge
    
    Args:
        resource_type: "wood", "stone", "water"
    
    Returns:
        True als user de benodigde knowledge heeft
    """
    user_knowledge = load_user_knowledge()
    
    # Zoek welk begrip nodig is voor deze resource
    for begrip, game_resource in RESOURCE_MAPPING.items():
        if game_resource == resource_type:
            # Check of user dit begrip kent
            has_knowledge = any(begrip in concept for concept in user_knowledge)
            logger.info(f"[KNOWLEDGE] Resource '{resource_type}' requires '{begrip}': {has_knowledge}")
            return has_knowledge
    
    # Default: altijd toestaan (fallback voor backwards compatibility)
    return True

def get_unlocked_buildings() -> list:
    """
    Haal alle gebouwen op die user kan bouwen op basis van knowledge
    
    Returns:
        List van building types die unlocked zijn
    """
    user_knowledge = load_user_knowledge()
    unlocked = []
    
    for begrip, buildings in BUILDING_UNLOCKS.items():
        # Check of user dit begrip kent
        if any(begrip in concept for concept in user_knowledge):
            unlocked.extend(buildings)
            logger.info(f"[KNOWLEDGE] Unlocked buildings via '{begrip}': {buildings}")
    
    # Remove duplicates
    return list(set(unlocked))

def check_knowledge_for_concept(concept: str) -> bool:
    """
    Check of user specifiek concept kent
    
    Args:
        concept: Begrip om te checken (bijv. "boom", "hout")
    
    Returns:
        True als user dit concept kent
    """
    user_knowledge = load_user_knowledge()
    return any(concept.lower() in knowledge_concept for knowledge_concept in user_knowledge)

def get_knowledge_stats() -> dict:
    """
    Haal statistics op over user's knowledge
    """
    user_knowledge = load_user_knowledge()
    unlocked_buildings = get_unlocked_buildings()
    
    return {
        "total_concepts": len(user_knowledge),
        "unlocked_buildings": unlocked_buildings,
        "can_collect_wood": can_collect_resource("wood"),
        "can_collect_stone": can_collect_resource("stone"),
        "knowledge_concepts": user_knowledge[:20]  # Sample
    }
