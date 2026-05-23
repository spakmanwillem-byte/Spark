"""v5_closing_flow_001 — Boekhouder closing-flow routes.

POST /api/boekhouder/close-cycle/{user_id}  — rollup + DM + audit
GET  /api/boekhouder/closings               — lijst (admin/user)
"""
from fastapi import APIRouter, HTTPException, Body
from typing import Optional
from . import service as boekhouder

router = APIRouter(prefix="/boekhouder", tags=["boekhouder"])


def _is_admin(user_id: str) -> bool:
    """Lazy admin check zonder cross-module gradatie-call (Willem of Spark)."""
    from pathlib import Path
    from modules.core.storage import load_json
    p = Path(__file__).parent.parent.parent / "data" / "system" / "users.json"
    data = load_json(p, default={"users": []})
    for u in data.get("users", []):
        if u.get("id") == user_id and (u.get("gradatie") or 7) <= 2:
            return True
    return False


@router.post("/close-cycle/{user_id}")
async def close_cycle(user_id: str, payload: Optional[dict] = Body(None)):
    """Sluit een trade-cyclus af voor user_id (terlens-terug-boek).

    Body (optioneel): {"viewer_id": "user-001", "note": "...optionele toelichting..."}
    Alleen admin (gradatie ≤ 2) mag closings triggeren.
    """
    viewer_id = (payload or {}).get("viewer_id")
    if not viewer_id or not _is_admin(viewer_id):
        raise HTTPException(status_code=403, detail="Alleen admin kan boekhouder afsluiten")
    note = (payload or {}).get("note", "")
    rollup = boekhouder.close_cycle(user_id, note=note)
    return {"success": True, "rollup": rollup}


@router.get("/closings")
async def list_closings(user_id: Optional[str] = None, limit: int = 20):
    return boekhouder.list_closings(user_id=user_id, limit=limit)
