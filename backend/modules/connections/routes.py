from typing import Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from modules.auth.service import AuthService
from . import service

router = APIRouter(prefix="/connections", tags=["connections"])

ADMIN_MAX_GRAD = 2


class SaveBody(BaseModel):
    viewer_id: str
    values: Dict[str, str]


def _require_admin(viewer_id: str) -> None:
    u = AuthService.get_user_by_id(viewer_id) or {}
    if not (u.get("admin_capable") or (u.get("gradatie") or 99) <= ADMIN_MAX_GRAD):
        raise HTTPException(403, "Alleen admin mag verbindingen zien of wijzigen")


@router.get("")
async def list_connections(viewer_id: str):
    _require_admin(viewer_id)
    return {"success": True, "connections": service.list_connections()}


@router.put("/{conn_id}")
async def save_connection(conn_id: str, body: SaveBody):
    _require_admin(body.viewer_id)
    try:
        cur = service.save_values(conn_id, body.values, body.viewer_id)
    except KeyError:
        raise HTTPException(404, f"Onbekende verbinding '{conn_id}'")
    return {"success": True, "conn_id": conn_id, "updated_at": cur.get("_updated_at")}


@router.post("/{conn_id}/test")
async def test_connection(conn_id: str, viewer_id: str):
    _require_admin(viewer_id)
    try:
        return {"success": True, "conn_id": conn_id, **service.test_connection(conn_id, user_id=viewer_id)}
    except KeyError:
        raise HTTPException(404, f"Onbekende verbinding '{conn_id}'")
