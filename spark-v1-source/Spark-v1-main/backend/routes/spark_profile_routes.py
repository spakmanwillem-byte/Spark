from fastapi import APIRouter, HTTPException
import json
from pathlib import Path

router = APIRouter()

SPARK_PROFILE_FILE = Path("/app/backend/data/personality/spark_profile.json")

@router.get("/me")
async def get_spark_profile():
    """
    Get Spark's own profile
    When someone asks 'Wie ben jij?' or 'Waarom ben je gemaakt?'
    """
    try:
        if not SPARK_PROFILE_FILE.exists():
            raise HTTPException(status_code=404, detail="Spark profile not found")
        
        with open(SPARK_PROFILE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return {
            "success": True,
            "profile": data.get("spark_profiel", {})
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/about")
async def get_spark_about():
    """
    Get Spark's 'about' info (biografie, waarom gemaakt, etc.)
    Quick endpoint for chat responses
    """
    try:
        if not SPARK_PROFILE_FILE.exists():
            raise HTTPException(status_code=404, detail="Spark profile not found")
        
        with open(SPARK_PROFILE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        profiel = data.get("spark_profiel", {})
        
        return {
            "success": True,
            "naam": profiel.get("basis", {}).get("volledige_naam"),
            "waarom_gemaakt": profiel.get("biografie", {}).get("waarom_gemaakt"),
            "missie": profiel.get("biografie", {}).get("missie"),
            "visie": profiel.get("biografie", {}).get("visie"),
            "sterke_punten": profiel.get("persoonlijkheid", {}).get("sterke_punten"),
            "motto": profiel.get("bijzonderheden", {}).get("motto"),
            "leuke_feiten": profiel.get("bijzonderheden", {}).get("leuke_feiten", [])
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/biography")
async def get_spark_biography():
    """
    Get Spark's full biography
    """
    try:
        if not SPARK_PROFILE_FILE.exists():
            raise HTTPException(status_code=404, detail="Spark profile not found")
        
        with open(SPARK_PROFILE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        profiel = data.get("spark_profiel", {})
        
        return {
            "success": True,
            "biografie": profiel.get("biografie", {}),
            "persoonlijkheid": profiel.get("persoonlijkheid", {}),
            "geschiedenis": profiel.get("biografie", {}).get("geschiedenis")
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
