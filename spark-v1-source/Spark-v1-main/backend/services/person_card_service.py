"""
Person Card Service - Beheer van persoonlijke contacten/relaties

Person Cards = Profielen van mensen in het leven van een user
- Met Spark account (is_user=True, heeft user_id)
- Zonder Spark account (is_user=False)

Gekoppeld aan:
- Gesprekken (conversation_refs)
- Kenniskaarten (knowledge_refs)
- User Gradatie systeem
"""
from typing import List, Dict, Optional
from datetime import datetime
from uuid import uuid4
import os
import json
from utils.data_manager import DataManager


class PersonCardService:
    """Service voor Person Card management"""
    
    PERSONS_DIR = "/app/backend/data/persons"
    
    @staticmethod
    def _ensure_dir():
        """Ensure persons directory exists"""
        os.makedirs(PersonCardService.PERSONS_DIR, exist_ok=True)
    
    @staticmethod
    def _get_person_cards_file(user_id: str) -> str:
        """Get person cards file path for user"""
        PersonCardService._ensure_dir()
        return os.path.join(PersonCardService.PERSONS_DIR, f"{user_id}_person_cards.json")
    
    @staticmethod
    def load_person_cards(user_id: str) -> List[Dict]:
        """
        Load all person cards for a user
        
        Args:
            user_id: Owner of the person cards
            
        Returns:
            List of person card dicts
        """
        filepath = PersonCardService._get_person_cards_file(user_id)
        
        if not os.path.exists(filepath):
            return []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return data.get('persons', [])
    
    @staticmethod
    def save_person_cards(user_id: str, person_cards: List[Dict]) -> bool:
        """
        Save person cards for a user
        
        Args:
            user_id: Owner
            person_cards: List of person cards
            
        Returns:
            Success boolean
        """
        filepath = PersonCardService._get_person_cards_file(user_id)
        
        data = {
            'persons': person_cards,
            'metadata': {
                'user_id': user_id,
                'total_persons': len(person_cards),
                'last_updated': datetime.now().isoformat()
            }
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return True
    
    @staticmethod
    def get_person_card(user_id: str, person_id: str) -> Optional[Dict]:
        """Get a specific person card"""
        person_cards = PersonCardService.load_person_cards(user_id)
        return next((p for p in person_cards if p.get('id') == person_id), None)
    
    @staticmethod
    def create_person_card(
        user_id: str,
        naam: str,
        volledige_naam: Optional[str] = None,
        relatie: Optional[str] = None,
        gradatie: Optional[int] = None,
        is_user: bool = False,
        linked_user_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        notes: Optional[str] = None
    ) -> Dict:
        """
        Create a new person card
        
        Args:
            user_id: Owner (creator)
            naam: First name or short name
            volledige_naam: Full name
            relatie: Relationship (dochter, vriend, collega, etc.)
            gradatie: Access level 1-7
            is_user: Does this person have a Spark account?
            linked_user_id: If is_user=True, their user_id
            tags: Tags (familie, werk, etc.)
            notes: Free text notes
            
        Returns:
            Created person card dict
        """
        person_cards = PersonCardService.load_person_cards(user_id)
        
        # Check if person already exists (by name)
        existing = next((p for p in person_cards if p.get('naam', '').lower() == naam.lower()), None)
        if existing:
            return existing  # Return existing instead of duplicate
        
        person_id = f"person-{uuid4().hex[:8]}"
        
        person_card = {
            'id': person_id,
            'naam': naam,
            'volledige_naam': volledige_naam or naam,
            'relatie': relatie,
            'gradatie': gradatie,
            'is_user': is_user,
            'linked_user_id': linked_user_id,
            'tags': tags or [],
            'notes': notes or '',
            'created_by': user_id,
            'conversation_refs': [],  # List of conversation IDs or message IDs
            'knowledge_refs': [],  # List of knowledge card IDs
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        person_cards.append(person_card)
        PersonCardService.save_person_cards(user_id, person_cards)
        
        return person_card
    
    @staticmethod
    def update_person_card(
        user_id: str,
        person_id: str,
        updates: Dict
    ) -> Optional[Dict]:
        """
        Update a person card
        
        Args:
            user_id: Owner
            person_id: Person card ID
            updates: Dict with fields to update
            
        Returns:
            Updated person card or None
        """
        person_cards = PersonCardService.load_person_cards(user_id)
        person = next((p for p in person_cards if p.get('id') == person_id), None)
        
        if not person:
            return None
        
        # Update fields
        for key, value in updates.items():
            if key not in ['id', 'created_by', 'created_at']:  # Protect immutable fields
                person[key] = value
        
        person['updated_at'] = datetime.now().isoformat()
        
        PersonCardService.save_person_cards(user_id, person_cards)
        
        return person
    
    @staticmethod
    def delete_person_card(user_id: str, person_id: str) -> bool:
        """Delete a person card"""
        person_cards = PersonCardService.load_person_cards(user_id)
        person_cards = [p for p in person_cards if p.get('id') != person_id]
        PersonCardService.save_person_cards(user_id, person_cards)
        return True
    
    @staticmethod
    def add_conversation_ref(user_id: str, person_id: str, conversation_ref: str) -> bool:
        """Add a conversation reference to a person card"""
        person = PersonCardService.get_person_card(user_id, person_id)
        if not person:
            return False
        
        if conversation_ref not in person.get('conversation_refs', []):
            person['conversation_refs'].append(conversation_ref)
            PersonCardService.update_person_card(user_id, person_id, person)
        
        return True
    
    @staticmethod
    def add_knowledge_ref(user_id: str, person_id: str, knowledge_id: str) -> bool:
        """Add a knowledge card reference to a person card"""
        person = PersonCardService.get_person_card(user_id, person_id)
        if not person:
            return False
        
        if knowledge_id not in person.get('knowledge_refs', []):
            person['knowledge_refs'].append(knowledge_id)
            PersonCardService.update_person_card(user_id, person_id, person)
        
        return True
    
    @staticmethod
    def search_person_cards(user_id: str, query: str) -> List[Dict]:
        """
        Search person cards by name, relatie, tags
        
        Args:
            user_id: Owner
            query: Search term
            
        Returns:
            Matching person cards
        """
        person_cards = PersonCardService.load_person_cards(user_id)
        query_lower = query.lower()
        
        results = []
        for person in person_cards:
            # Search in name, relatie, tags, notes
            if (query_lower in person.get('naam', '').lower() or
                query_lower in person.get('volledige_naam', '').lower() or
                query_lower in person.get('relatie', '').lower() or
                any(query_lower in tag.lower() for tag in person.get('tags', [])) or
                query_lower in person.get('notes', '').lower()):
                results.append(person)
        
        return results
    
    @staticmethod
    def migrate_from_users(user_id: str) -> List[Dict]:
        """
        Migrate existing users to Person Cards
        
        For Willem: creates Person Cards for Lotus, Maurice, etc.
        
        Args:
            user_id: User creating the Person Cards (e.g., "user-001")
            
        Returns:
            List of created Person Cards
        """
        users = DataManager.load_users()
        current_user = next((u for u in users if u.get('id') == user_id), None)
        
        if not current_user:
            return []
        
        created_cards = []
        
        # Check persoonlijke_info for dochter, partner, etc.
        pers_info = current_user.get('persoonlijke_info', {})
        
        # Dochter
        if pers_info.get('dochter'):
            # Find user with this name
            dochter_name = pers_info.get('dochter')
            dochter_user = next((u for u in users if u.get('naam') == dochter_name), None)
            
            card = PersonCardService.create_person_card(
                user_id=user_id,
                naam=dochter_name,
                volledige_naam=dochter_user.get('volledige_naam') if dochter_user else dochter_name,
                relatie='dochter',
                gradatie=dochter_user.get('gradatie') if dochter_user else 2,
                is_user=bool(dochter_user),
                linked_user_id=dochter_user.get('id') if dochter_user else None,
                tags=['familie', 'dochter']
            )
            created_cards.append(card)
        
        # Check other users and create Person Cards
        for user in users:
            if user.get('id') == user_id:
                continue  # Skip self
            
            # Skip if already created (like dochter)
            naam = user.get('naam')
            if any(c.get('naam') == naam for c in created_cards):
                continue
            
            # Determine relatie from user data
            relatie = user.get('rol', 'kennis')
            if 'collega' in relatie.lower():
                relatie = 'collega'
            elif 'vriend' in relatie.lower():
                relatie = 'vriend'
            elif 'familie' in relatie.lower():
                relatie = 'familie'
            
            card = PersonCardService.create_person_card(
                user_id=user_id,
                naam=naam,
                volledige_naam=user.get('volledige_naam', naam),
                relatie=relatie,
                gradatie=user.get('gradatie', 5),
                is_user=True,
                linked_user_id=user.get('id'),
                tags=[relatie] if relatie else []
            )
            created_cards.append(card)
        
        return created_cards
