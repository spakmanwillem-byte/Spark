"""v6_response_composer_001 — Endpoints voor Spark's gespreks-synthesizer.

POST /api/spark/compose                  — vraag een gesynthesizeerd antwoord
GET  /api/spark/compose/blueprint        — lees huidige blueprint config
POST /api/spark/compose/blueprint/reload — clear cache (na handmatige edit)
"""
import json
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from modules.chat.response_composer import compose_response
from modules.core.blueprint import load_blueprint, clear_blueprint_cache

router = APIRouter(prefix="/spark/compose", tags=["spark-compose"])

BP_FP = Path(__file__).parent / "blueprints" / "response_composer.json"


class ComposeRequest(BaseModel):
    text: str
    user_id: Optional[str] = "user-001"
    session_id: Optional[str] = None
    emotion: Optional[str] = None
    active_tab: Optional[str] = None  # v6_tab_context_001 — welke tab user nu bekijkt


@router.post("")
async def compose(req: ComposeRequest):
    """Synthesizeer een gespreks-antwoord vanuit KB + bijbel + turns."""
    if not (req.text or "").strip():
        return {"success": False, "error": "empty text"}
    result = await compose_response(
        user_text=req.text,
        user_id=req.user_id or "user-001",
        session_id=req.session_id,
        emotion=req.emotion,
        active_tab=req.active_tab,
    )
    return result


@router.get("/blueprint")
async def get_blueprint():
    """Toon de huidige Response Composer blueprint config (read-only voorbeeld)."""
    try:
        bp = load_blueprint("chat", "response_composer")
        return {"success": True, "blueprint": bp, "path": str(BP_FP)}
    except FileNotFoundError as ex:
        raise HTTPException(404, str(ex))


@router.post("/blueprint/reload")
async def reload_blueprint():
    """Clear blueprint-cache na handmatige edit van het JSON-bestand."""
    clear_blueprint_cache()
    return {"success": True, "msg": "Blueprint cache cleared. Volgende /compose-call gebruikt verse JSON."}


# v6_trigger_learner_001 — admin endpoints voor learned triggers
@router.get("/learned-triggers")
async def list_learned_triggers(limit: int = 50, status: Optional[str] = None):
    """Lijst van LLM-voorgestelde triggers wachtend op admin-review."""
    try:
        from modules.chat.trigger_learner import _load_learned
        data = _load_learned()
        voorstellen = data.get("voorstellen", [])
        if status:
            voorstellen = [v for v in voorstellen if v.get("status") == status]
        # Nieuwste eerst
        return {
            "success": True,
            "totaal": len(voorstellen),
            "voorstellen": voorstellen[-limit:][::-1],
            "statistieken": data.get("statistieken", {}),
        }
    except Exception as ex:
        raise HTTPException(500, str(ex))


@router.post("/learned-triggers/{voorstel_id}/approve")
async def approve_trigger(voorstel_id: str):
    from modules.chat.trigger_learner import approve
    ok = approve(voorstel_id)
    if not ok:
        raise HTTPException(404, f"Voorstel {voorstel_id} niet gevonden")
    return {"success": True, "voorstel_id": voorstel_id, "status": "approved"}


@router.post("/learned-triggers/{voorstel_id}/reject")
async def reject_trigger(voorstel_id: str):
    from modules.chat.trigger_learner import reject
    ok = reject(voorstel_id)
    if not ok:
        raise HTTPException(404, f"Voorstel {voorstel_id} niet gevonden")
    return {"success": True, "voorstel_id": voorstel_id, "status": "rejected"}
