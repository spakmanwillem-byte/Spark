"""
Shadow-potjes API routes (v6_shadow_cascade_002)
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from pathlib import Path

from . import shadow_pots as shadow_svc
from ..core.storage import load_json

router = APIRouter(prefix="/trade/shadow", tags=["trade-shadow"])

DATA_ROOT = Path(__file__).parent.parent.parent / "data"
POTJES_FILE = DATA_ROOT / "financial" / "user_potjes.json"
USERS_FILE = DATA_ROOT / "system" / "users.json"


def _is_admin(user_id: Optional[str]) -> bool:
    """v6_shadow_safety_001 — admin-guard helper, matcht patroon van dnd/world.py."""
    if not user_id:
        return False
    users = load_json(USERS_FILE, default={"users": []}).get("users", [])
    u = next((x for x in users if x.get("id") == user_id), None)
    return bool(u and (u.get("gradatie", 99) <= 2))


@router.get("/list/{user_id}")
async def list_for_user(user_id: str):
    return {"shadows": shadow_svc.list_shadows_for_user(user_id)}


@router.get("/pot/{pot_id}")
async def get_for_pot(pot_id: str, user_id: Optional[str] = None):
    return {"shadows": shadow_svc.get_shadows_for_pot(pot_id, owner_user_id=user_id)}


@router.post("/auto-ensure/{user_id}")
async def auto_ensure(user_id: str):
    """Maak voor alle non-anchor potjes van een user 3 idle shadow-slots."""
    return shadow_svc.auto_ensure_shadows_for_user(user_id)


class CreateShadowReq(BaseModel):
    pot_id: str
    user_id: str
    market: str
    capital: Optional[float] = 10.0
    slot: Optional[int] = None


@router.post("/create")
async def create(req: CreateShadowReq):
    return shadow_svc.create_shadow_for_pot(
        req.pot_id, req.user_id, req.market, req.capital, slot=req.slot
    )


@router.get("/status/{user_id}")
async def status_for_user(user_id: str):
    """
    Per-pot shadow-status voor UI. Toont voor elk potje:
      pot_id, market, capacity {idle, active, closed, slots: {1,2,3 → status}},
      active_shadows: [{shadow_id, slot, entry_price, drop_pct}],
      cycle (huidige recycle-cyclus, start 1)
    """
    pots_data = load_json(POTJES_FILE, default={"users": {}})
    u = pots_data.get("users", {}).get(user_id, {})
    pots = u.get("potjes", []) or u.get("pots", [])

    summary = {"idle": 0, "active": 0, "closed": 0, "archived": 0, "none": 0}
    result = []
    for p in pots:
        if p.get("pot_locked"):
            continue
        cap = shadow_svc.shadow_capacity(p["id"], user_id)
        actives = shadow_svc.get_active_shadows(p["id"], owner_user_id=user_id)
        all_shadows = shadow_svc.get_shadows_for_pot(p["id"], owner_user_id=user_id)
        cycle = max((int(s.get("cycle", 1)) for s in all_shadows), default=1)
        result.append({
            "pot_id": p["id"],
            "market": p.get("market"),
            "capacity": cap,
            "active_shadows": [
                {
                    "shadow_id": s["shadow_id"],
                    "slot": s.get("slot", 1),
                    "entry_price": s.get("entry_price"),
                    "trigger_drop_pct": s.get("trigger_drop_pct"),
                    "trigger_reason": s.get("trigger_reason"),
                    "activated_at": s.get("activated_at"),
                }
                for s in actives
            ],
            "cycle": cycle,
        })
        if cap["have"] == 0:
            summary["none"] += 1
        else:
            summary["idle"] += cap["idle"]
            summary["active"] += cap["active"]
            summary["closed"] += cap["closed"]
    return {"user_id": user_id, "pots": result, "summary": summary, "max_per_pot": shadow_svc.MAX_SHADOWS_PER_POT}


@router.get("/stats")
async def get_stats():
    return shadow_svc.stats()


class SimulateStabReq(BaseModel):
    pot_id: str
    user_id: str
    entry_price: float
    current_price: float
    candles: list  # list of {high, low, close}


@router.post("/simulate-stabilization")
async def simulate_stabilization(req: SimulateStabReq):
    """
    Test helper: gegeven een entry_price en candles, zou de bodemdetector triggeren?
    Voor offline analyse (backtest van historische bot-logs).
    """
    return shadow_svc.is_stabilizing_after_drop(
        candles=req.candles,
        entry_price=req.entry_price,
        current_price=req.current_price,
    )


# v6_shadow_safety_001 — admin endpoints voor master-flag + corrupt cleanup
@router.get("/flag")
async def get_shadow_flag():
    """Lees huidige SHADOW_ENABLED state. Public-read (informatief)."""
    return {"enabled": shadow_svc.is_shadow_enabled()}


class ShadowFlagReq(BaseModel):
    enabled: bool
    by_user: Optional[str] = "admin"


@router.post("/flag")
async def set_shadow_flag(req: ShadowFlagReq):
    """Toggle de master-flag. Wanneer False slaat de bot alle shadow-BUYs over.
    Admin-only (gradatie ≤ 2)."""
    if not _is_admin(req.by_user):
        raise HTTPException(403, "Alleen admin (gradatie ≤ 2) kan de shadow-flag wijzigen")
    return shadow_svc.set_shadow_enabled(req.enabled, by_user=req.by_user or "admin")


class CleanupReq(BaseModel):
    viewer_id: Optional[str] = None


@router.post("/cleanup-corrupt")
async def cleanup_corrupt_shadows(req: Optional[CleanupReq] = None):
    """v6_shadow_safety_001 — markeer actieve shadows met market/entry-mismatch
    als `archived_corrupt`. Detectie:
      - shadow.market != pot.market (mismatch)
      - shadow.entry_price niet binnen 50% van pot.position.entry_price
    Vrij idle slot creëren NIET — eerst handmatig beoordelen.
    Admin-only (gradatie ≤ 2).
    """
    viewer_id = req.viewer_id if req else None
    if not _is_admin(viewer_id):
        raise HTTPException(403, "Alleen admin (gradatie ≤ 2) kan corrupt shadows opruimen")
    return shadow_svc.cleanup_corrupt_active_shadows()
