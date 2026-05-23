"""
v6_capabilities_admin_001 — Admin overzicht van alle Spark capabilities.

Endpoints:
  GET  /api/admin/capabilities        — alle caps met live/placeholder/handler status
  POST /api/admin/capabilities/test   — test een specifieke capability met sample text
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from modules.chat import intent_matcher_service, capability_handler_service

router = APIRouter(prefix="/admin/capabilities", tags=["admin-capabilities"])


class TestRequest(BaseModel):
    text: str
    user_id: Optional[str] = "user-001"


@router.get("")
async def list_capabilities():
    caps = intent_matcher_service.all_capabilities()
    handlers = set(capability_handler_service._HANDLERS.keys())
    enriched = []
    for c in caps:
        enriched.append({
            **c,
            "has_handler": c.get("id") in handlers,
            "effective_status": (
                "executable" if c.get("id") in handlers
                else c.get("status", "idea")
            ),
        })
    return {
        "total": len(enriched),
        "executable": sum(1 for c in enriched if c["has_handler"]),
        "live_no_handler": sum(1 for c in enriched if c.get("status") == "live" and not c["has_handler"]),
        "placeholder": sum(1 for c in enriched if c.get("status") == "placeholder"),
        "idea": sum(1 for c in enriched if c.get("status") == "idea"),
        "capabilities": enriched,
    }


@router.post("/test")
async def test_capability(req: TestRequest):
    match = intent_matcher_service.match_capability(req.text)
    if not match:
        return {"matched": False, "message": "Geen capability gematched op die zin."}
    resp = capability_handler_service.route_capability(req.text, req.user_id)
    return {
        "matched": True,
        "match": match,
        "execution": resp,
    }
