"""
Spark Core Routes - Identity, Bijbel, Personality
Serves Spark's identity, kernwaarden, normen, doelen, reactie voorbeelden
"""
from fastapi import APIRouter
from pathlib import Path
from modules.core.storage import load_json

router = APIRouter(prefix="/spark", tags=["spark"])
DATA_DIR = Path(__file__).parent.parent.parent / "data" / "personality"


@router.get("/identity")
async def get_identity():
    """Spark's core identity"""
    return load_json(DATA_DIR / "spark_identity.json", default={})


@router.get("/bijbel")
async def get_bijbel():
    """Spark Bijbel: kernwaarden, normen, doelen, reactie voorbeelden"""
    return load_json(DATA_DIR / "spark_bijbel.json", default={})


@router.get("/full")
async def get_full_profile():
    """Combined identity + bijbel for SparkBrainPage"""
    identity = load_json(DATA_DIR / "spark_identity.json", default={})
    bijbel = load_json(DATA_DIR / "spark_bijbel.json", default={})
    return {
        "identity": identity,
        "bijbel": bijbel,
    }
