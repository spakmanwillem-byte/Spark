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


@router.get("/status/{user_id}")
async def status_for_user(user_id: str):
    """
    Per-pot shadow-status voor UI. Returnt voor elk potje van de user:
      pot_id, market, shadow_status (idle/active/none), shadow_id, entry_price, trigger_drop_pct
    """
    from pathlib import Path
    from ..core.storage import load_json
    DATA_ROOT = Path(__file__).parent.parent.parent / "data"
    pots_data = load_json(DATA_ROOT / "financial" / "user_potjes.json", default={"users": {}})
    u = pots_data.get("users", {}).get(user_id, {})
    pots = u.get("potjes", []) or u.get("pots", [])

    shadows = shadow_svc.list_shadows_for_user(user_id)
    by_pot = {}
    for s in shadows:
        # Laatste status wint (idle/active overschreven door closed alleen als geen actieve)
        cur = by_pot.get(s.get("original_pot_id"))
        if cur is None or cur.get("status") == "closed":
            by_pot[s.get("original_pot_id")] = s

    result = []
    for p in pots:
        if p.get("pot_locked"):
            continue
        sh = by_pot.get(p.get("id"))
        result.append({
            "pot_id": p.get("id"),
            "market": p.get("market"),
            "shadow_status": (sh.get("status") if sh else "none"),
            "shadow_id": (sh.get("shadow_id") if sh else None),
            "entry_price": (sh.get("entry_price") if sh else None),
            "trigger_drop_pct": (sh.get("trigger_drop_pct") if sh else None),
            "profit": (sh.get("profit") if sh else None),
            "activated_at": (sh.get("activated_at") if sh else None),
            "closed_at": (sh.get("closed_at") if sh else None),
        })
    by_status = {"idle": 0, "active": 0, "closed": 0, "none": 0}
    for r in result:
        by_status[r["shadow_status"]] = by_status.get(r["shadow_status"], 0) + 1
    return {"user_id": user_id, "pots": result, "summary": by_status}


@router.get("/stats")
async def get_stats():
    return shadow_svc.stats()
