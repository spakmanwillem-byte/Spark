"""v6_spark_planner_001 — Endpoints voor Gesprekplanner.

Brief (Laag A):
  POST   /api/spark/planner/brief/build       — build brief voor user_id + date
  GET    /api/spark/planner/brief/latest      — meest recente brief van user
  GET    /api/spark/planner/brief/list        — lijst alle briefs van user
  GET    /api/spark/planner/brief/{user_id}/{date}  — specifieke brief

Threads (Laag B):
  GET    /api/spark/planner/threads           — alle threads van user (filter ?status=)
  POST   /api/spark/planner/threads           — nieuwe thread / bump
  PATCH  /api/spark/planner/threads/{id}/status — status wijzigen
  DELETE /api/spark/planner/threads/{id}      — thread verwijderen
  POST   /api/spark/planner/threads/decay     — run decay (open → sluimerend → afgesloten)

Blueprint:
  POST   /api/spark/planner/blueprint/reload  — cache leegmaken
  GET    /api/spark/planner/blueprint         — huidige config bekijken
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

from modules.core.blueprint import load_blueprint_cached, clear_blueprint_cache
from modules.spark_planner import brief_builder, threads_service
from modules.spark_planner.brief_builder import build_daily_brief, latest_brief, list_briefs, _brief_fp
from modules.spark_planner.threads_service import (
    get_threads, add_or_bump_thread, set_status, delete_thread, run_decay,
)
from modules.core.storage import load_json

router = APIRouter(prefix="/spark/planner", tags=["spark-planner"])


# ============================================================
# BRIEF (Laag A)
# ============================================================

class BuildBriefRequest(BaseModel):
    user_id: str
    date: Optional[str] = None  # YYYY-MM-DD, default = gister


@router.post("/brief/build")
async def post_build_brief(body: BuildBriefRequest):
    """Bouw (of herbouw) brief voor user op date (default gister)."""
    if not body.user_id:
        raise HTTPException(400, "user_id verplicht")
    result = await build_daily_brief(body.user_id, body.date)
    return result


@router.get("/brief/latest")
async def get_latest_brief(user_id: str = Query(...)):
    """Pak meest recente brief voor user."""
    b = latest_brief(user_id)
    if not b:
        return {"success": False, "message": "Nog geen brief voor deze user.", "user_id": user_id}
    return {"success": True, "brief": b}


@router.get("/brief/list")
async def get_brief_list(user_id: str = Query(...)):
    """Lijst alle briefs van user (date + samenvatting)."""
    return {"success": True, "user_id": user_id, "briefs": list_briefs(user_id)}


@router.get("/brief/{user_id}/{date}")
async def get_specific_brief(user_id: str, date: str):
    """Specifieke brief op datum YYYY-MM-DD."""
    fp = _brief_fp(user_id, date)
    if not fp.exists():
        raise HTTPException(404, "Brief bestaat niet voor deze user/date")
    return {"success": True, "brief": load_json(fp, default={})}


# ============================================================
# THREADS (Laag B)
# ============================================================

class ThreadCreate(BaseModel):
    user_id: str
    topic: str
    intensity: int = 1
    note: Optional[str] = None


class ThreadStatusUpdate(BaseModel):
    status: str  # open | sluimerend | afgesloten


@router.get("/threads")
async def list_user_threads(
    user_id: str = Query(...),
    status: Optional[str] = Query(None),
):
    """Lijst threads van user (optioneel filter op status)."""
    return {
        "success": True,
        "user_id": user_id,
        "threads": get_threads(user_id, status=status),
    }


@router.post("/threads")
async def create_or_bump_thread(body: ThreadCreate):
    """Voeg thread toe of bump bestaande (case-insensitive op topic)."""
    if not body.topic.strip():
        raise HTTPException(400, "topic mag niet leeg zijn")
    return add_or_bump_thread(body.user_id, body.topic, body.intensity, body.note)


@router.patch("/threads/{thread_id}/status")
async def patch_thread_status(thread_id: str, body: ThreadStatusUpdate,
                                user_id: str = Query(...)):
    """Status wijzigen."""
    res = set_status(user_id, thread_id, body.status)
    if not res.get("success"):
        raise HTTPException(404, res.get("error", "thread niet gevonden"))
    return res


@router.delete("/threads/{thread_id}")
async def delete_thread_route(thread_id: str, user_id: str = Query(...)):
    """Thread verwijderen."""
    res = delete_thread(user_id, thread_id)
    if not res.get("success"):
        raise HTTPException(404, res.get("error", "thread niet gevonden"))
    return res


@router.post("/threads/decay")
async def post_run_decay(user_id: Optional[str] = Query(None)):
    """Loop threads: open→sluimerend na N dagen, →afgesloten na M dagen."""
    return run_decay(user_id)


# ============================================================
# BLUEPRINT
# ============================================================

@router.get("/blueprint")
async def get_blueprint():
    """Bekijk huidige planner-config."""
    return {"success": True, "blueprint": load_blueprint_cached("spark_planner", "planner")}


@router.post("/blueprint/reload")
async def reload_blueprint():
    """Cache leegmaken (na manueel JSON-edit)."""
    clear_blueprint_cache()
    return {"success": True, "msg": "Planner blueprint cache cleared."}
