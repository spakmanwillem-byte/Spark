"""
Personal Context API Routes - Fase 1 MVP
Simple endpoints for entity extraction and management
WITH source/about tracking for privacy/scheiding
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import logging

from services.personal_context_service import PersonalContextService
from services.achievement_service import AchievementService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/context", tags=["Personal Context"])

# Initialize service
context_service = PersonalContextService()

# Request/Response Models
class AnalyzeTextRequest(BaseModel):
    user_id: str
    text: str

class AnalyzeTextResponse(BaseModel):
    success: bool
    extracted_entities: List[Dict]
    updated_profile: Dict

class GetEntitiesResponse(BaseModel):
    success: bool
    user_id: str
    entities: List[Dict]

class DeleteEntityRequest(BaseModel):
    user_id: str
    entity_id: str


@router.post("/analyze", response_model=AnalyzeTextResponse)
async def analyze_conversation(request: AnalyzeTextRequest):
    """
    Analyze conversation text and extract persons + relations
    Auto-updates user profile with source/about tracking
    
    Example 1 (no name):
    {
        "user_id": "willem",
        "text": "Mijn moeder belde gisteren"
    }
    → source: "willem", about: null, relation: "parent"
    
    Example 2 (with name):
    {
        "user_id": "willem",
        "text": "Lotus is mijn ex"
    }
    → source: "willem", about: "Lotus", relation: "ex_partner"
    """
    try:
        # Extract entities from text (includes source/about)
        extracted = context_service.analyze_text(request.text, request.user_id)
        
        # Update user profile (merge/deduplicate)
        updated_profile = context_service.update_user_context(request.user_id, extracted)
        
        # Award XP for context creation (if entities were added)
        if extracted and len(extracted) > 0:
            xp_result = AchievementService.award_xp_for_event(request.user_id, "context_created")
            logger.info(f"[API] Awarded {xp_result.get('xp_awarded', 0)} XP for context creation")
        
        logger.info(f"[API] Analyzed text for user {request.user_id}: {len(extracted)} entities found")
        
        return {
            "success": True,
            "extracted_entities": extracted,
            "updated_profile": updated_profile
        }
    
    except Exception as e:
        logger.error(f"[API] Error analyzing text: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/entities/{user_id}", response_model=GetEntitiesResponse)
async def get_user_entities(user_id: str):
    """
    Get all entities for a user
    """
    try:
        entities = context_service.get_user_entities(user_id)
        
        return {
            "success": True,
            "user_id": user_id,
            "entities": entities
        }
    
    except Exception as e:
        logger.error(f"[API] Error getting entities: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/entity/{user_id}/{role}")
async def get_entity_by_role(user_id: str, role: str):
    """
    Get specific entity by role (or alias)
    
    Example: GET /api/context/entity/user_001/moeder
    """
    try:
        entity = context_service.get_entity_by_role(user_id, role)
        
        if not entity:
            raise HTTPException(status_code=404, detail=f"Entity '{role}' not found for user {user_id}")
        
        return {
            "success": True,
            "entity": entity
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Error getting entity: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/entity")
async def delete_entity(request: DeleteEntityRequest):
    """
    Delete an entity from user profile
    """
    try:
        success = context_service.delete_entity(request.user_id, request.entity_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Entity not found")
        
        return {
            "success": True,
            "message": f"Entity {request.entity_id} deleted"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Error deleting entity: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear/{user_id}")
async def clear_user_context(user_id: str):
    """
    Clear all entities for a user (for testing/reset)
    """
    try:
        success = context_service.clear_user_context(user_id)
        
        return {
            "success": success,
            "message": f"Cleared context for user {user_id}"
        }
    
    except Exception as e:
        logger.error(f"[API] Error clearing context: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
