"""ChatHub API routes."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from pathlib import Path
import json
from .chat_hub_master import get_hub

router = APIRouter(prefix="/chat_hub", tags=["chat_hub"])
HUB_DIR = Path(__file__).parent


class DispatchBody(BaseModel):
    text: str
    viewer_id: Optional[str] = "user-001"
    viewer_gradatie: Optional[int] = None


@router.get("/manifest")
async def get_manifest():
    """Volledige tree + split-check + blueprint-registry."""
    hub = get_hub()
    return {
        "success": True,
        "hub": hub.manifest(),
        "structure_manifest_file": str(HUB_DIR / "structure_manifest.json"),
    }


@router.get("/health")
async def health_check():
    """Roept HealAgent.health_check() aan (systematische status)."""
    from .agents.heal_agent import HealAgent
    return {"success": True, **HealAgent().health_check()}


@router.post("/dispatch")
async def dispatch(body: DispatchBody):
    """Route een query naar matchende leaf-agents. Retourneer resultaten."""
    # Gradatie: gebruik meegegeven, anders lookup
    vg = body.viewer_gradatie
    if vg is None:
        try:
            users = json.load(open(HUB_DIR.parent.parent / "data" / "system" / "users.json"))
            u = next((x for x in users.get("users", []) if x.get("id") == body.viewer_id), None)
            vg = int(u.get("gradatie", 3)) if u else 3
        except Exception:
            vg = 3

    hub = get_hub()
    context = {"viewer_id": body.viewer_id, "viewer_gradatie": vg}
    result = hub.dispatch(body.text, context)
    return {"success": True, "viewer_gradatie": vg, **result}


@router.get("/blueprint/{agent_name}")
async def get_blueprint(agent_name: str):
    """Lees de blueprint van een specifieke agent."""
    bp_fp = HUB_DIR / "blueprints" / f"{agent_name}_blauwdruk.json"
    if not bp_fp.exists():
        raise HTTPException(status_code=404, detail=f"blueprint '{agent_name}' niet gevonden")
    return {"success": True, "blueprint": json.load(open(bp_fp))}


@router.get("/agents")
async def list_agents():
    """Lijst alle agents met basis-manifest."""
    hub = get_hub()
    return {
        "success": True,
        "count": len(hub.children),
        "agents": [c.to_manifest() for c in hub.children],
    }
