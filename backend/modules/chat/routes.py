"""
Chat Routes - Spark AI chat met Snap/NLP knowledge lookup
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from .snap_service import SnapNLPService

router = APIRouter(prefix="/chat", tags=["chat"])
snap = SnapNLPService()


class ChatMessage(BaseModel):
    message: str
    user_naam: Optional[str] = "Gebruiker"
    user_id: Optional[str] = None


class SnapRequest(BaseModel):
    concept: str
    context: Optional[str] = ""
    user_naam: Optional[str] = "Gebruiker"
    is_sentence: bool = False


@router.post("/message")
async def process_message(req: ChatMessage):
    """
    Verwerk een chat bericht:
    1. Check triggers (begroeting, bedankt, hoe gaat het)
    2. Zoek begrippen in knowledge base
    3. Geef antwoord op basis van lagen
    4. Detecteer onbekende woorden (voor snap suggesties)
    """
    text = req.message.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Leeg bericht")

    response = {
        "type": "response",
        "message": "",
        "knowledge_matches": [],
        "sentiment": snap.detect_sentiment(text),
        "unknown_words": [],
        "snap_suggestions": [],
    }

    # 1. Trigger checks
    if snap.detect_greeting(text):
        resp = snap.get_trigger_response("greeting")
        response["type"] = "greeting"
        response["message"] = resp or f"Hallo {req.user_naam}! Hoe kan ik je helpen?"
        return response

    if snap.detect_thanks(text):
        resp = snap.get_trigger_response("thanks")
        response["type"] = "thanks"
        response["message"] = resp or "Graag gedaan!"
        return response

    if snap.detect_how_are_you(text):
        resp = snap.get_trigger_response("how_are_you")
        response["type"] = "how_are_you"
        response["message"] = resp or "Goed! Ik ben bezig om te leren en groeien."
        return response

    if snap.detect_goodbye(text):
        resp = snap.get_trigger_response("goodbye")
        response["type"] = "goodbye"
        response["message"] = resp or f"Tot ziens {req.user_naam}!"
        return response

    # 2. Knowledge lookup - zoek alle begrippen in de zin
    matches = snap.multi_lookup(text)

    if matches:
        response["knowledge_matches"] = matches
        # Gebruik het beste match voor het antwoord
        best = matches[0]
        laag1 = best.get("laag1", "")
        if laag1:
            if len(matches) == 1:
                response["message"] = f"**{best['begrip']}**: {laag1}"
            else:
                parts = [f"**{m['begrip']}**: {m['laag1']}" for m in matches if m.get('laag1')]
                response["message"] = "\n\n".join(parts) if parts else f"Ik ken '{best['begrip']}' maar heb nog geen uitleg."
        else:
            response["message"] = f"Ik ken '{best['begrip']}' maar heb nog geen uitleg. Wil je het invullen in de Kennisbank?"
        response["type"] = "knowledge"
    else:
        # 3. Geen match - detecteer onbekende woorden voor snap suggesties
        meaningful = snap._extract_meaningful_words(text)
        index = snap._get_index()
        unknown = [w for w in meaningful if w not in index]

        if unknown:
            response["unknown_words"] = unknown
            response["snap_suggestions"] = unknown[:5]
            response["message"] = f"Hmm, ik ken deze woorden nog niet: {', '.join(unknown)}. Zal ik ze opslaan als nieuwe kaarten?"
            response["type"] = "unknown"
        else:
            # Gewoon antwoord als er niks te matchen valt
            if snap.is_question(text):
                response["message"] = "Goede vraag! Daar heb ik helaas nog geen antwoord op. Wil je het toevoegen aan de Kennisbank?"
                response["type"] = "question"
            else:
                response["message"] = "Ik begrijp je, maar kan daar nog niet specifiek op reageren. Mijn kennis groeit elke dag!"
                response["type"] = "general"

    return response


@router.post("/snap")
async def create_snap(req: SnapRequest):
    """Maak een knowledge snap (woord of zin)"""
    if req.is_sentence:
        result = snap.create_sentence_snap(req.concept, req.context, req.user_naam)
    else:
        result = snap.create_word_snap(req.concept, req.context, req.user_naam)

    if result is None:
        return {"success": False, "message": "Kon geen snap aanmaken (bestaat al of is een stopwoord)"}

    return {
        "success": True,
        "message": f"Snap '{result['begrip']}' aangemaakt!",
        "entry": {
            "id": result["id"],
            "begrip": result["begrip"],
            "status": result["status"],
        }
    }


@router.get("/lookup/{query}")
async def lookup_knowledge(query: str):
    """Direct knowledge lookup op een begrip"""
    result = snap.lookup(query)
    if not result:
        return {"found": False, "query": query}
    return {"found": True, "query": query, "result": result}
