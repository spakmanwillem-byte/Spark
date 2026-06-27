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
