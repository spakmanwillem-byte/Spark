"""
Knowledge Routes - Public endpoints for feedback
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.knowledge_service_v2 import KnowledgeServiceV2

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


class FeedbackRequest(BaseModel):
    helpful: bool


@router.post("/{knowledge_id}/feedback")
async def record_feedback(knowledge_id: str, feedback: FeedbackRequest):
    """
    Record user feedback (public endpoint - no auth required)
    
    Args:
        knowledge_id: ID of knowledge entry
        feedback.helpful: True if helpful, False if not
    """
    success = KnowledgeServiceV2.record_feedback(knowledge_id, feedback.helpful)
    
    if not success:
        raise HTTPException(status_code=404, detail="Knowledge entry not found")
    
    return {
        "success": True,
        "message": "Bedankt voor je feedback!",
        "knowledge_id": knowledge_id
    }


@router.get("/{knowledge_id}/stats")
async def get_stats(knowledge_id: str):
    """
    Get usage statistics for a knowledge entry
    Includes rank_score
    """
    stats = KnowledgeServiceV2.get_entry_stats(knowledge_id)
    
    if not stats:
        raise HTTPException(status_code=404, detail="Knowledge entry not found")
    
    return {
        "success": True,
        "stats": stats
    }
