"""v6_response_composer_001 — Endpoints voor Spark's gespreks-synthesizer.

POST /api/spark/compose  — vraag een gesynthesizeerd antwoord
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from modules.chat.response_composer import compose_response

router = APIRouter(prefix="/spark/compose", tags=["spark-compose"])


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
