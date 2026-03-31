"""
Voice API Routes - Speech-to-Text en Text-to-Speech endpoints
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional
from services.voice_service import get_voice_service

router = APIRouter()

class TTSRequest(BaseModel):
    text: str
    voice: Optional[str] = "nova"  # Default: energetic, upbeat
    speed: Optional[float] = 1.0
    model: Optional[str] = "tts-1"  # tts-1 (snel) of tts-1-hd (HD)
    format: Optional[str] = "audio"  # "audio" of "base64"


@router.post("/stt")
async def speech_to_text(
    audio: UploadFile = File(...),
    language: str = "nl"
):
    """
    Speech-to-Text: Converteer audio naar tekst
    
    Args:
        audio: Audio bestand (mp3, wav, webm, m4a, etc.)
        language: Taal code (nl, en, de, fr, etc.)
    
    Returns:
        {"text": "getranscribeerde tekst"}
    """
    try:
        voice_service = get_voice_service()
        text = await voice_service.speech_to_text(audio, language)
        
        return {
            "text": text,
            "language": language,
            "success": True
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"STT fout: {str(e)}")


@router.post("/tts")
async def text_to_speech(request: TTSRequest):
    """
    Text-to-Speech: Converteer tekst naar audio
    
    Request body:
    {
        "text": "Tekst om uit te spreken",
        "voice": "nova",  // alloy, nova, shimmer, echo, fable, onyx, ash, coral, sage
        "speed": 1.0,     // 0.25 - 4.0
        "model": "tts-1", // tts-1 of tts-1-hd
        "format": "audio" // "audio" (MP3 bytes) of "base64" (base64 string)
    }
    
    Returns:
        Audio file (MP3) of base64 string
    """
    try:
        voice_service = get_voice_service()
        
        if request.format == "base64":
            # Return base64 encoded audio
            audio_base64 = await voice_service.text_to_speech_base64(
                text=request.text,
                voice=request.voice,
                speed=request.speed,
                model=request.model
            )
            return {
                "audio_base64": audio_base64,
                "format": "mp3",
                "success": True
            }
        else:
            # Return audio bytes
            audio_bytes = await voice_service.text_to_speech(
                text=request.text,
                voice=request.voice,
                speed=request.speed,
                model=request.model
            )
            
            return Response(
                content=audio_bytes,
                media_type="audio/mpeg",
                headers={
                    "Content-Disposition": "inline; filename=speech.mp3"
                }
            )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS fout: {str(e)}")


@router.get("/voices")
async def get_available_voices():
    """
    Get lijst van beschikbare stemmen met beschrijvingen
    
    Returns:
        Lijst van voice options
    """
    return {
        "voices": [
            {"id": "alloy", "name": "Alloy", "description": "Neutral, gebalanceerd", "gender": "neutral"},
            {"id": "ash", "name": "Ash", "description": "Helder, duidelijk", "gender": "neutral"},
            {"id": "coral", "name": "Coral", "description": "Warm, vriendelijk", "gender": "female"},
            {"id": "echo", "name": "Echo", "description": "Glad, kalm", "gender": "male"},
            {"id": "fable", "name": "Fable", "description": "Expressief, storytelling", "gender": "neutral"},
            {"id": "nova", "name": "Nova", "description": "Energiek, opgewekt", "gender": "female"},
            {"id": "onyx", "name": "Onyx", "description": "Diep, autoritair", "gender": "male"},
            {"id": "sage", "name": "Sage", "description": "Wijs, gemeten", "gender": "neutral"},
            {"id": "shimmer", "name": "Shimmer", "description": "Helder, vrolijk", "gender": "female"}
        ],
        "default": "nova",
        "recommended_for_spark": "nova"  # Energetic & upbeat past bij Spark
    }


@router.get("/settings")
async def get_voice_settings_defaults():
    """
    Get default voice instellingen
    """
    return {
        "tts": {
            "enabled": False,  # Default uit
            "voice": "nova",
            "speed": 1.0,
            "model": "tts-1",  # Snel model default
            "auto_play": False  # Auto-play responses
        },
        "stt": {
            "enabled": False,  # Default uit
            "language": "nl",
            "push_to_talk": True,  # Push-to-talk vs always listening
            "continuous": False
        }
    }
