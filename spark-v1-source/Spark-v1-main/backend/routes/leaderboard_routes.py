"""
Leaderboard API Routes
"""
from fastapi import APIRouter, HTTPException
from services.leaderboard_service import LeaderboardService

router = APIRouter()

@router.get("/leaderboard/top")
async def get_top_contributors(limit: int = 10):
    """Get top contributors leaderboard"""
    try:
        leaderboard = LeaderboardService.get_top_contributors(limit)
        return {
            "success": True,
            "leaderboard": leaderboard,
            "count": len(leaderboard)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/leaderboard/rank/{user_id}")
async def get_user_rank(user_id: str):
    """Get user's rank on leaderboard"""
    try:
        rank = LeaderboardService.get_user_rank(user_id)
        return {
            "success": True,
            **rank
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
