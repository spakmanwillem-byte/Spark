"""
User Profile API Routes - CRUD operations for user profiles/personalia
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from services.user_profile_service import UserProfileService

router = APIRouter()


class ProfileUpdate(BaseModel):
    need: Optional[str] = None
    believe: Optional[str] = None
    interesses: Optional[List[str]] = None
    context: Optional[str] = None
    ws5: Optional[dict] = None
    tags: Optional[List[str]] = None
    gradatie: Optional[int] = None


@router.get("/profiles")
async def get_all_profiles():
    """Get all user profiles (admin only)"""
    profiles = UserProfileService.get_all_profiles()
    return {
        "profiles": profiles,
        "total": len(profiles)
    }


@router.get("/profiles/{user_id}")
async def get_user_profile(user_id: str):
    """Get a specific user profile"""
    profile = UserProfileService.get_user_profile(user_id)
    
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"profile": profile}


@router.put("/profiles/{user_id}")
async def update_user_profile(user_id: str, profile_data: ProfileUpdate):
    """Update a user profile"""
    updated = UserProfileService.update_profile(
        user_id=user_id,
        profile_data=profile_data.model_dump(exclude_none=True)
    )
    
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "success": True,
        "profile": updated.get("profile")
    }


@router.get("/profiles/search/need/{keyword}")
async def search_by_need(keyword: str):
    """Search users by need keyword"""
    results = UserProfileService.search_by_need(keyword)
    
    return {
        "results": results,
        "count": len(results),
        "keyword": keyword
    }


@router.get("/profiles/search/believe/{keyword}")
async def search_by_believe(keyword: str):
    """Search users by believe keyword"""
    results = UserProfileService.search_by_believe(keyword)
    
    return {
        "results": results,
        "count": len(results),
        "keyword": keyword
    }
