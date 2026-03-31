"""
Knowledge-Game Integration Routes
Koppelt kennisbank aan Spark World voor unlock mechanics
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/knowledge-game", tags=["knowledge-game"])

class UnlockCheckRequest(BaseModel):
    user_id: str
    item_type: str  # e.g., "sawmill", "baker", "toolsmith"

class UnlockableItem(BaseModel):
    item_type: str
    name: str
    required_concepts: List[str]  # Knowledge card topics needed
    is_unlocked: bool
    icon: str

@router.get("/unlockable-items/{user_id}")
async def get_unlockable_items(user_id: str):
    """
    Get all items that can be unlocked via knowledge
    
    PLACEHOLDER: Returns static data for now
    TODO: Check user's knowledge cards and determine unlocks
    """
    try:
        # PLACEHOLDER DATA
        items = [
            {
                "item_type": "sawmill",
                "name": "Houtzagerij",
                "icon": "🪚",
                "required_concepts": ["houtbewerking", "gereedschap", "productie"],
                "is_unlocked": False,  # TODO: Check if user has these concepts
                "unlock_message": "Leer over houtbewerking om dit te ontgrendelen!"
            },
            {
                "item_type": "toolsmith",
                "name": "Gereedschapsmaker",
                "icon": "🔨",
                "required_concepts": ["metaalbewerking", "gereedschap", "ambacht"],
                "is_unlocked": False,
                "unlock_message": "Leer over metaalbewerking!"
            },
            {
                "item_type": "library",
                "name": "Bibliotheek",
                "icon": "📚",
                "required_concepts": ["kennis", "onderwijs", "leren"],
                "is_unlocked": False,
                "unlock_message": "Leer over kennisoverdracht!"
            },
            {
                "item_type": "school",
                "name": "School",
                "icon": "🏫",
                "required_concepts": ["onderwijs", "leren", "groep"],
                "is_unlocked": False,
                "unlock_message": "Leer over onderwijs!"
            }
        ]
        
        logger.info(f"[KNOWLEDGE-GAME] Fetched {len(items)} unlockable items for {user_id} (PLACEHOLDER)")
        
        return {
            "success": True,
            "items": items,
            "message": "PLACEHOLDER: Real knowledge integration coming soon!"
        }
        
    except Exception as e:
        logger.error(f"[KNOWLEDGE-GAME] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/check-unlock")
async def check_unlock(request: UnlockCheckRequest):
    """
    Check if user has unlocked specific item via knowledge
    
    PLACEHOLDER: Always returns false for now
    TODO: Query user's knowledge cards and check if required concepts exist
    """
    try:
        # PLACEHOLDER LOGIC
        # TODO: 
        # 1. Get user's knowledge cards
        # 2. Extract topics from cards
        # 3. Check if required_concepts ⊆ user_topics
        # 4. Return unlock status
        
        is_unlocked = False  # PLACEHOLDER
        
        logger.info(f"[KNOWLEDGE-GAME] Unlock check for {request.item_type}: {is_unlocked} (PLACEHOLDER)")
        
        return {
            "success": True,
            "is_unlocked": is_unlocked,
            "item_type": request.item_type,
            "message": "PLACEHOLDER: Real unlock logic coming soon!"
        }
        
    except Exception as e:
        logger.error(f"[KNOWLEDGE-GAME] Error checking unlock: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/knowledge-progress/{user_id}")
async def get_knowledge_progress(user_id: str):
    """
    Get user's knowledge progress for game unlocks
    
    PLACEHOLDER: Returns mock data
    TODO: Real integration with knowledge base
    """
    try:
        # PLACEHOLDER DATA
        progress = {
            "total_concepts_learned": 0,  # TODO: Count unique topics in knowledge cards
            "unlocked_items_count": 0,
            "locked_items_count": 4,
            "next_unlock": {
                "item": "Houtzagerij",
                "concepts_needed": ["houtbewerking", "gereedschap"],
                "concepts_missing": 2
            }
        }
        
        return {
            "success": True,
            "progress": progress,
            "message": "PLACEHOLDER: Connect to real knowledge base"
        }
        
    except Exception as e:
        logger.error(f"[KNOWLEDGE-GAME] Error getting progress: {e}")
        raise HTTPException(status_code=500, detail=str(e))
