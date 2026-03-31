"""
Roadmap API Routes
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Dict, Any
from services.roadmap_service import RoadmapService

router = APIRouter(tags=["roadmap"])


class RoadmapItemCreate(BaseModel):
    titel: str
    priority: Optional[str] = "medium"
    assigned_to: Optional[str] = None
    notes: Optional[str] = None


class RoadmapItemUpdate(BaseModel):
    status: Optional[str] = None
    progress: Optional[int] = None
    notes: Optional[str] = None
    priority: Optional[str] = None


@router.get("/")
async def get_full_roadmap():
    """Get complete roadmap"""
    return RoadmapService.get_roadmap()


@router.get("/summary")
async def get_roadmap_summary():
    """Get roadmap summary"""
    return RoadmapService.get_summary()


@router.get("/version/{version}")
async def get_version_roadmap(version: str):
    """Get specific version roadmap"""
    result = RoadmapService.get_version(version)
    if result:
        return result
    return {"error": "Version not found"}


@router.post("/item/{version}")
async def add_roadmap_item(version: str, item: RoadmapItemCreate):
    """Add new roadmap item"""
    return RoadmapService.add_item(version, item.dict())


@router.put("/item/{item_id}")
async def update_roadmap_item(item_id: str, updates: RoadmapItemUpdate):
    """Update roadmap item"""
    return RoadmapService.update_item(item_id, updates.dict(exclude_unset=True))
