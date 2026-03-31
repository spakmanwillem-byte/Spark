"""
5W+H Verbanden Routes (Light Version)
======================================
API endpoints voor verbanden management

FOCUS:
- Simpel
- Debugbaar
- Handmatige controle
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import sys
sys.path.append('/app/backend')

from services.verbanden_service import VerbanenService

router = APIRouter(prefix="/verbanden", tags=["verbanden"])


# ============== REQUEST MODELS ==============

class UpdateContextRequest(BaseModel):
    """Update 5W+H context voor een card"""
    card_id: str
    field: str  # wie, wat, waar, wanneer, waarom, hoe
    value: str


class BevestigVerbandRequest(BaseModel):
    """Bevestig een voorgesteld verband"""
    card_id: str
    target_id: str


# ============== ROUTES ==============

@router.post("/suggest/{card_id}")
async def suggest_verbanden(card_id: str, max_suggestions: int = 10):
    """
    🔍 Zoek verbanden voor één card (handmatige trigger)
    
    Light versie:
    - Simpele overlap detectie
    - Max 10 voorstellen
    - Uitgebreide logging in console
    
    Returns:
        - suggestions: List van voorgestelde verbanden
        - count: Aantal voorstellen
    """
    try:
        service = VerbanenService()
        suggestions = service.suggest_verbanden(card_id, max_suggestions)
        
        card = service.get_card(card_id)
        begrip = card.get('begrip', 'Unknown') if card else 'Unknown'
        
        return {
            "success": True,
            "card_id": card_id,
            "card_begrip": begrip,
            "suggestions": suggestions,
            "count": len(suggestions),
            "message": f"Found {len(suggestions)} voorstellen voor '{begrip}'"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bevestig")
async def bevestig_verband(req: BevestigVerbandRequest):
    """
    ✅ Bevestig een voorgesteld verband (handmatig door Willem)
    
    Verplaatst verband van 'voorgesteld' naar 'bevestigd'
    """
    try:
        service = VerbanenService()
        success = service.bevestig_verband(req.card_id, req.target_id)
        
        if success:
            source = service.get_card(req.card_id)
            target = service.get_card(req.target_id)
            
            return {
                "success": True,
                "message": f"Verband bevestigd: {source.get('begrip')} ↔ {target.get('begrip')}"
            }
        else:
            raise HTTPException(status_code=400, detail="Kon verband niet bevestigen")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/verwijder")
async def verwijder_verband(card_id: str, target_id: str):
    """
    🗑️ Verwijder een bevestigd verband
    """
    try:
        service = VerbanenService()
        success = service.verwijder_verband(card_id, target_id)
        
        if success:
            return {
                "success": True,
                "message": "Verband verwijderd"
            }
        else:
            raise HTTPException(status_code=404, detail="Verband niet gevonden")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-context")
async def update_context(req: UpdateContextRequest):
    """
    ✏️ Update 5W+H context field voor een card
    
    Willem vult handmatig de 5W+H velden in via frontend
    """
    try:
        service = VerbanenService()
        card = service.get_card(req.card_id)
        
        if not card:
            raise HTTPException(status_code=404, detail="Card niet gevonden")
        
        # Update context field
        if 'context_5wh' not in card:
            card['context_5wh'] = {}
        
        valid_fields = ['wie', 'wat', 'waar', 'wanneer', 'waarom', 'hoe']
        if req.field not in valid_fields:
            raise HTTPException(status_code=400, detail=f"Ongeldig veld: {req.field}")
        
        old_value = card['context_5wh'].get(req.field, '')
        card['context_5wh'][req.field] = req.value
        service._save_kb()
        
        return {
            "success": True,
            "message": f"Context veld '{req.field}' updated",
            "card_id": req.card_id,
            "card_begrip": card.get('begrip'),
            "field": req.field,
            "old_value": old_value,
            "new_value": req.value
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def verbanden_stats():
    """
    📊 Get statistieken over verbanden in hele knowledge base
    
    Handig om te zien hoeveel cards voorstellen/verbanden hebben
    """
    try:
        service = VerbanenService()
        stats = service.get_statistics()
        
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/card/{card_id}")
async def get_card_verbanden(card_id: str):
    """
    📋 Get alle verbanden info voor één card
    
    Inclusief:
    - 5W+H context
    - Voorgestelde verbanden
    - Bevestigde verbanden
    - Usage count
    """
    try:
        service = VerbanenService()
        card = service.get_card(card_id)
        
        if not card:
            raise HTTPException(status_code=404, detail="Card niet gevonden")
        
        # Get details van bevestigde verbanden
        bevestigde_details = []
        for target_id in card.get('bevestigde_verbanden', []):
            target = service.get_card(target_id)
            if target:
                bevestigde_details.append({
                    'card_id': target_id,
                    'card_begrip': target.get('begrip'),
                    'context_5wh': target.get('context_5wh', {})
                })
        
        return {
            "success": True,
            "card_id": card_id,
            "begrip": card.get('begrip'),
            "context_5wh": card.get('context_5wh', {}),
            "voorgestelde_verbanden": card.get('voorgestelde_verbanden', []),
            "bevestigde_verbanden": bevestigde_details,
            "bevestigde_count": len(card.get('bevestigde_verbanden', [])),
            "voorgestelde_count": len(card.get('voorgestelde_verbanden', [])),
            "usage_count": card.get('usage_count', 0)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
