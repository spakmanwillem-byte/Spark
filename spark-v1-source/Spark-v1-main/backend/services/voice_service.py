"""
Voice Service - Text-to-Speech and Speech-to-Text
Gebruikt OpenAI Whisper (STT) en OpenAI TTS voor voice interface
"""
import os
from typing import Optional
from fastapi import UploadFile
from dotenv import load_dotenv

load_dotenv()

class VoiceService:
    """Service voor voice conversie (STT & TTS)"""
    
    def __init__(self):
        self.api_key = os.getenv("EMERGENT_LLM_KEY")
        if not self.api_key:
            raise ValueError("EMERGENT_LLM_KEY niet gevonden in .env")
    
    async def speech_to_text(self, audio_file: UploadFile, language: str = "nl") -> str:
        """
        Converteer audio naar tekst met OpenAI Whisper
        
        Args:
            audio_file: Uploaded audio file (mp3, wav, webm, etc.)
            language: Taal code (nl, en, etc.)
            
        Returns:
            Getranscribeerde tekst
        """
        try:
            from emergentintegrations.llm.openai import OpenAISpeechToText
            
            stt = OpenAISpeechToText(api_key=self.api_key)
            
            # Read file content
            audio_content = await audio_file.read()
            
            # Create a file-like object from bytes
            from io import BytesIO
            audio_bytes = BytesIO(audio_content)
            audio_bytes.name = audio_file.filename or "audio.webm"
            
            # Transcribe
            response = await stt.transcribe(
                file=audio_bytes,
                model="whisper-1",
                response_format="json",
                language=language,
                temperature=0.0  # Meest deterministische resultaat
            )
            
            return response.text
            
        except Exception as e:
            raise Exception(f"Speech-to-Text fout: {str(e)}")
    
    async def text_to_speech(
        self, 
        text: str, 
        voice: str = "nova",
        speed: float = 1.0,
        model: str = "tts-1"
    ) -> bytes:
        """
        Converteer tekst naar audio met OpenAI TTS
        
        Args:
            text: Tekst om uit te spreken
            voice: Stem keuze (alloy, nova, shimmer, echo, fable, onyx, ash, coral, sage)
            speed: Snelheid (0.25 - 4.0, default 1.0)
            model: tts-1 (snel) of tts-1-hd (HD kwaliteit)
            
        Returns:
            Audio bytes (MP3 format)
        """
        try:
            from emergentintegrations.llm.openai import OpenAITextToSpeech
            
            # Limiet: 4096 characters
            if len(text) > 4096:
                text = text[:4096]
            
            tts = OpenAITextToSpeech(api_key=self.api_key)
            
            audio_bytes = await tts.generate_speech(
                text=text,
                model=model,
                voice=voice,
                speed=speed,
                response_format="mp3"
            )
            
            return audio_bytes
            
        except Exception as e:
            raise Exception(f"Text-to-Speech fout: {str(e)}")
    
    async def text_to_speech_base64(
        self,
        text: str,
        voice: str = "nova",
        speed: float = 1.0,
        model: str = "tts-1"
    ) -> str:
        """
        Converteer tekst naar base64 audio (voor direct in frontend gebruik)
        
        Returns:
            Base64 encoded audio string
        """
        try:
            from emergentintegrations.llm.openai import OpenAITextToSpeech
            
            if len(text) > 4096:
                text = text[:4096]
            
            tts = OpenAITextToSpeech(api_key=self.api_key)
            
            audio_base64 = await tts.generate_speech_base64(
                text=text,
                model=model,
                voice=voice,
                speed=speed,
                response_format="mp3"
            )
            
            return audio_base64
            
        except Exception as e:
            raise Exception(f"Text-to-Speech Base64 fout: {str(e)}")


# Singleton instance
_voice_service = None

def get_voice_service() -> VoiceService:
    """Get or create VoiceService singleton"""
    global _voice_service
    if _voice_service is None:
        _voice_service = VoiceService()
    return _voice_service
