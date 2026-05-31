"""
Shadow-potjes API routes (v6_shadow_pot_001)
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from . import shadow_pots as shadow_svc

router = APIRouter(prefix="/trade/shadow", tags=["trade-shadow"])


@router.get("/list/{user_id}")
async def list_for_user(user_id: str):
    return {"shadows": shadow_svc.list_shadows_for_user(user_id)}


@router.get("/pot/{pot_id}")
async def get_for_pot(pot_id: str):
    return {"shadows": shadow_svc.get_shadows_for_pot(pot_id)}


@router.post("/auto-ensure/{user_id}")
async def auto_ensure(user_id: str):
    """Maak shadow potjes voor alle non-anchor potjes van een user."""
    return shadow_svc.auto_ensure_shadows_for_user(user_id)


class CreateShadowReq(BaseModel):
    pot_id: str
    user_id: str
    market: str
    capital: Optional[float] = 10.0


@router.post("/create")
async def create(req: CreateShadowReq):
    return shadow_svc.create_shadow_for_pot(req.pot_id, req.user_id, req.market, req.capital)


@router.get("/stats")
async def get_stats():
    return shadow_svc.stats()
