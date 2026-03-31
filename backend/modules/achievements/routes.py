"""
Achievements Routes
"""
from fastapi import APIRouter, HTTPException
from .service import AchievementService

router = APIRouter(prefix="/achievements", tags=["achievements"])
service = AchievementService()


@router.get("/all")
async def get_all_achievements():
    """Get all available achievements"""
    return service.get_all()


@router.get("/progress/{user_id}")
async def get_user_progress(user_id: str):
    """Get user's achievement progress (auto-unlocks retroactively)"""
    result = service.get_user_progress(user_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Gebruiker niet gevonden")
    return result
