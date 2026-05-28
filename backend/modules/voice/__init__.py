"""
Voice Routes - Speech-to-Text (Whisper) en Text-to-Speech (OpenAI TTS)
"""
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional
import os
import tempfile
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/voice", tags=["voice"])

VOICES = [
    {"id": "alloy", "name": "Alloy", "description": "Neutraal, gebalanceerd"},
    {"id": "ash", "name": "Ash", "description": "Helder, duidelijk"},
    {"id": "coral", "name": "Coral", "description": "Warm, vriendelijk"},
    {"id": "echo", "name": "Echo", "description": "Glad, kalm"},
    {"id": "fable", "name": "Fable", "description": "Expressief, storytelling"},
    {"id": "nova", "name": "Nova", "description": "Energiek, opgewekt"},
    {"id": "onyx", "name": "Onyx", "description": "Diep, autoritair"},
    {"id": "sage", "name": "Sage", "description": "Wijs, gemeten"},
    {"id": "shimmer", "name": "Shimmer", "description": "Helder, vrolijk"},
]


class TTSRequest(BaseModel):
    text: str
    voice: Optional[str] = "nova"
    speed: Optional[float] = 1.0
    model: Optional[str] = "tts-1"
    format: Optional[str] = "base64"


@router.post("/stt")
async def speech_to_text(audio: UploadFile = File(...), language: str = "nl",
                          card_id: Optional[str] = None, user_id: Optional[str] = None):
    """Speech-to-Text via OpenAI Whisper.

    v6_voice_kbv2_link_001 — als card_id meegegeven wordt, slaan we het transcript
    op als dialoog-snippet via kbv2.save_voice_snippet (Spark's stem-stijl groei).
    """
    try:
        from emergentintegrations.llm.openai import OpenAISpeechToText
        stt = OpenAISpeechToText(api_key=os.getenv("EMERGENT_LLM_KEY"))

        # Save upload to temp file
        suffix = "." + (audio.filename.split(".")[-1] if audio.filename else "webm")
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await audio.read()
            tmp.write(content)
            tmp_path = tmp.name

        with open(tmp_path, "rb") as f:
            response = await stt.transcribe(file=f, model="whisper-1", language=language, response_format="json")

        os.unlink(tmp_path)

        transcript_text = response.text or ""

        # v6_voice_kbv2_link_001 — Kennis-kaart link → snippet opslaan
        snippet_saved = False
        if card_id and user_id and transcript_text.strip():
            try:
                from modules.kb_v2.hooks import save_voice_snippet
                snippet_saved = save_voice_snippet(transcript_text, card_id, user_id)
            except Exception as _ex:
                print(f"[voice] save_voice_snippet failed: {_ex}")

        return {
            "success": True,
            "text": transcript_text,
            "language": language,
            "snippet_saved": snippet_saved,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/tts")
async def text_to_speech(req: TTSRequest):
    """Text-to-Speech via OpenAI TTS"""
    try:
        from emergentintegrations.llm.openai import OpenAITextToSpeech
        tts = OpenAITextToSpeech(api_key=os.getenv("EMERGENT_LLM_KEY"))

        if req.format == "base64":
            audio_b64 = await tts.generate_speech_base64(
                text=req.text, model=req.model, voice=req.voice, speed=req.speed,
            )
            return {"success": True, "audio_base64": audio_b64, "format": "mp3"}
        else:
            audio_bytes = await tts.generate_speech(
                text=req.text, model=req.model, voice=req.voice, speed=req.speed,
            )
            return Response(content=audio_bytes, media_type="audio/mpeg",
                            headers={"Content-Disposition": "inline; filename=speech.mp3"})
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/voices")
async def get_voices():
    return {"voices": VOICES, "default": "nova"}
