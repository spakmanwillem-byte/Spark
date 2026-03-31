"""
Person Card API Routes
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from services.person_card_service import PersonCardService

router = APIRouter()


class PersonCardCreate(BaseModel):
    naam: str
    volledige_naam: Optional[str] = None
    relatie: Optional[str] = None
    gradatie: Optional[int] = None
    is_user: bool = False
    linked_user_id: Optional[str] = None
    tags: Optional[List[str]] = []
    notes: Optional[str] = None


class PersonCardUpdate(BaseModel):
    naam: Optional[str] = None
    volledige_naam: Optional[str] = None
    relatie: Optional[str] = None
    gradatie: Optional[int] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None


@router.get("/persons/{user_id}")
async def get_person_cards(user_id: str):
    """Get all person cards for a user"""
    person_cards = PersonCardService.load_person_cards(user_id)
    return {
        'person_cards': person_cards,
        'total': len(person_cards)
    }


@router.get("/persons/{user_id}/search")
async def search_person_cards(user_id: str, q: str):
    """Search person cards - MUST be before /{person_id} to avoid route conflict"""
    results = PersonCardService.search_person_cards(user_id, q)
    return {
        'results': results,
        'total': len(results)
    }


@router.get("/persons/{user_id}/{person_id}")
async def get_person_card(user_id: str, person_id: str):
    """Get a specific person card"""
    person = PersonCardService.get_person_card(user_id, person_id)
    
    if not person:
        raise HTTPException(status_code=404, detail="Person card not found")
    
    return person


@router.post("/persons/{user_id}")
async def create_person_card(user_id: str, person: PersonCardCreate):
    """Create a new person card"""
    try:
        card = PersonCardService.create_person_card(
            user_id=user_id,
            naam=person.naam,
            volledige_naam=person.volledige_naam,
            relatie=person.relatie,
            gradatie=person.gradatie,
            is_user=person.is_user,
            linked_user_id=person.linked_user_id,
            tags=person.tags,
            notes=person.notes
        )
        return {
            'success': True,
            'person_card': card
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/persons/{user_id}/{person_id}")
async def update_person_card(user_id: str, person_id: str, updates: PersonCardUpdate):
    """Update a person card"""
    # Convert to dict, remove None values
    update_dict = {k: v for k, v in updates.dict().items() if v is not None}
    
    person = PersonCardService.update_person_card(user_id, person_id, update_dict)
    
    if not person:
        raise HTTPException(status_code=404, detail="Person card not found")
    
    return {
        'success': True,
        'person_card': person
    }


@router.delete("/persons/{user_id}/{person_id}")
async def delete_person_card(user_id: str, person_id: str):
    """Delete a person card"""
    success = PersonCardService.delete_person_card(user_id, person_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Person card not found")
    
    return {'success': True}


@router.post("/persons/{user_id}/migrate")
async def migrate_users_to_person_cards(user_id: str):
    """
    Migrate existing users to Person Cards
    Creates Person Cards for Lotus, Maurice, etc.
    """
    try:
        created = PersonCardService.migrate_from_users(user_id)
        return {
            'success': True,
            'created_cards': created,
            'total': len(created)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/persons/{user_id}/{person_id}/conversation")
async def add_conversation_ref(user_id: str, person_id: str, conversation_ref: str):
    """Add conversation reference to person card"""
    success = PersonCardService.add_conversation_ref(user_id, person_id, conversation_ref)
    
    if not success:
        raise HTTPException(status_code=404, detail="Person card not found")
    
    return {'success': True}


@router.post("/persons/{user_id}/{person_id}/knowledge")
async def add_knowledge_ref(user_id: str, person_id: str, knowledge_id: str):
    """Add knowledge card reference to person card"""
    success = PersonCardService.add_knowledge_ref(user_id, person_id, knowledge_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Person card not found")
    
    return {'success': True}
