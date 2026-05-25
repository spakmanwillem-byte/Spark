"""
v6_emotion_pipeline_001 — endpoints voor 7-laags emotie-pipeline (dry-run modus).
"""
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from .pipeline import run_pipeline

router = APIRouter(prefix="/emotion-pipeline", tags=["emotion-pipeline"])


class PipelineRunRequest(BaseModel):
    text: str
    user_id: Optional[str] = None


@router.post("/run")
async def run(req: PipelineRunRequest):
    """Dry-run: draait alle 7 lagen en returnt trace + summary.
    Haakt NIET in op chat-flow."""
    return run_pipeline(req.text, user_id=req.user_id)


@router.get("/layers")
async def layers():
    """Documenteer welke 7 lagen bestaan + hun rol (voor UI)."""
    return {
        "success": True,
        "layers": [
            {"n": 1, "name": "Detectie",        "rol": "Emotionele context herkennen",
             "bron": "EmotionDetectionService (bestaand)"},
            {"n": 2, "name": "Weging",          "rol": "Kracht/prioriteit toekennen",
             "bron": "score → bracket (licht/midden/sterk/escalerend)"},
            {"n": 3, "name": "Contextfilter",   "rol": "Emotie kleurt betekenis",
             "bron": "lens per emotie (nieuwsgierig/frustratie/twijfel/...)"},
            {"n": 4, "name": "Identiteitstoets", "rol": "Gespiegeld aan Spark core",
             "bron": "identity_axes (transparantie/autonomie/menselijkheid/rust)"},
            {"n": 5, "name": "Norm/waarden",    "rol": "Passendheidstoets",
             "bron": "spark_bijbel.json (11 kernwaarden + 5 normen)"},
            {"n": 6, "name": "Actierouting",    "rol": "Welke behavior_class activeren",
             "bron": "mapping emotie → begrenzen/vertragen/exploreren/kalmeren"},
            {"n": 7, "name": "Expressie",       "rol": "Tempo/toon/directheid/detail",
             "bron": "presets per behavior_class"},
        ],
    }
