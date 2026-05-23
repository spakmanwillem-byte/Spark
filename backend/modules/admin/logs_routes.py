"""
Admin Logs Routes (v5_spark_logger_001)
========================================
Endpoints om logs te indexeren, bekijken en opschonen via UI.

Routes:
  GET  /api/admin/logs/index                     → boom YYYY/MM/DD → [modules]
  GET  /api/admin/logs/read?date=&module=&limit= → laatste N records
  POST /api/admin/logs/purge                     → handmatige opschoning
"""
from typing import Optional
from fastapi import APIRouter, Query

from modules.core.spark_logger import index_tree, read_logs, purge_old_logs, RETENTION_DAYS

router = APIRouter(prefix="/admin/logs", tags=["admin-logs"])


@router.get("/index")
async def get_index():
    """Boom van beschikbare logs: {YYYY: {MM: {DD: [module, ...]}}}."""
    return {"success": True, "tree": index_tree(), "retention_days": RETENTION_DAYS}


@router.get("/read")
async def read(
    date: str = Query(..., description="YYYY-MM-DD"),
    module: str = Query(..., description="module name, e.g. 'bots' of 'auth'"),
    limit: int = Query(200, ge=1, le=2000),
    phase: Optional[str] = Query(None, description="filter op pre/post/error/event"),
):
    """Lees laatste `limit` log-records voor module op die datum."""
    result = read_logs(date, module, limit=limit, phase=phase)
    result["success"] = "error" not in result
    return result


@router.post("/purge")
async def purge(retention_days: int = Query(RETENTION_DAYS, ge=1, le=365)):
    """Verwijder logs ouder dan `retention_days` dagen."""
    return {"success": True, **purge_old_logs(retention_days)}
