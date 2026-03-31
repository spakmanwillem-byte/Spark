"""
Person Detection Service
Detecteert nieuwe namen in gesprekken en stelt Person Card creatie voor
"""
import re
from typing import List, Dict, Optional
from services.person_card_service import PersonCardService
from utils.data_manager import DataManager


class PersonDetectionService:
    """Service voor automatische persoon detectie"""
    
    # Blacklist: woorden die GEEN namen zijn
    NAME_BLACKLIST = [
        'ik', 'je', 'jij', 'hij', 'zij', 'het', 'we', 'jullie', 'ze',
        'dit', 'dat', 'deze', 'die',
        'ja', 'nee', 'ok', 'oké', 'okay',
        'dag', 'hallo', 'hoi', 'hey',
        'spark', 'ai', 'bot', 'assistant',
        'wie', 'wat', 'waar', 'wanneer', 'waarom', 'hoe',
        'god', 'jezus', 'allah', 'boeddha',  # Religieuze figuren
        'jan', 'piet', 'klaas',  # Te algemeen
    ]
    
    # Context woorden die aangeven dat een naam genoemd wordt
    NAME_CONTEXT_WORDS = [
        'heet', 'ik ben', 'naam is', 'genoemd', 'ken je',
        'ontmoet', 'gesproken met', 'gezien', 'contact met',
        'vriendschap met', 'gewerkt met', 'samen met',
        'koffie met', 'lunch met', 'date met',
        'mijn vriend', 'mijn vriendin', 'mijn collega', 'mijn baas',
        'mijn dochter', 'mijn zoon', 'mijn vader', 'mijn moeder',
        'mijn broer', 'mijn zus', 'mijn opa', 'mijn oma'
    ]
    
    @staticmethod
    def detect_names_in_text(text: str) -> List[str]:
        """
        Detecteer mogelijke namen in tekst (hoofdletters)
        
        Args:
            text: Input text
            
        Returns:
            List of detected names
        """
        # Regex: woorden die met hoofdletter beginnen
        potential_names = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b', text)
        
        # Filter blacklist
        names = [
            name for name in potential_names
            if name.lower() not in PersonDetectionService.NAME_BLACKLIST
        ]
        
        return list(set(names))  # Unique names
    
    @staticmethod
    def detect_new_persons(
        text: str,
        user_id: str,
        require_context: bool = True
    ) -> List[Dict]:
        """
        Detecteer NIEUWE personen in tekst (nog geen Person Card)
        
        Args:
            text: Input text
            user_id: Current user
            require_context: Require naam context woorden (default True)
            
        Returns:
            List of new person suggestions with confidence
        """
        # Detecteer namen
        detected_names = PersonDetectionService.detect_names_in_text(text)
        
        if not detected_names:
            return []
        
        # Check context (optioneel)
        has_context = False
        if require_context:
            text_lower = text.lower()
            has_context = any(
                context in text_lower
                for context in PersonDetectionService.NAME_CONTEXT_WORDS
            )
            
            if not has_context:
                return []  # Geen context, geen suggestie
        
        # Load existing Person Cards
        existing_cards = PersonCardService.load_person_cards(user_id)
        existing_names = [p.get('naam', '').lower() for p in existing_cards]
        
        # Load existing users
        users = DataManager.load_users()
        user_names = [u.get('naam', '').lower() for u in users]
        
        # Filter: alleen NIEUWE namen (geen existing card, geen existing user)
        new_persons = []
        for name in detected_names:
            name_lower = name.lower()
            
            # Skip if already has Person Card
            if name_lower in existing_names:
                continue
            
            # Skip if is existing user (but suggest linking)
            is_user = name_lower in user_names
            
            # Determine confidence
            confidence = 0.7
            if has_context:
                confidence = 0.9
            
            # Try to extract relatie from context
            relatie = PersonDetectionService._extract_relatie_from_context(text, name)
            
            new_persons.append({
                'naam': name,
                'is_user': is_user,
                'suggested_relatie': relatie,
                'confidence': confidence,
                'context_snippet': text[:100]  # First 100 chars for context
            })
        
        return new_persons
    
    @staticmethod
    def _extract_relatie_from_context(text: str, name: str) -> Optional[str]:
        """
        Probeer relatie te extraheren uit context
        
        Bijv: "Ik heb met mijn vriend Sarah gesproken" → relatie = "vriend"
        """
        text_lower = text.lower()
        name_lower = name.lower()
        
        # Relatie mapping
        relatie_patterns = {
            'vriend': ['mijn vriend', 'goede vriend', 'oude vriend', 'beste vriend'],
            'vriendin': ['mijn vriendin', 'goede vriendin'],
            'collega': ['mijn collega', 'collega van'],
            'baas': ['mijn baas', 'de baas'],
            'dochter': ['mijn dochter', 'dochter van'],
            'zoon': ['mijn zoon', 'zoon van'],
            'vader': ['mijn vader', 'vader van'],
            'moeder': ['mijn moeder', 'moeder van'],
            'broer': ['mijn broer', 'broer van'],
            'zus': ['mijn zus', 'zus van'],
            'opa': ['mijn opa', 'opa van'],
            'oma': ['mijn oma', 'oma van'],
            'partner': ['mijn partner', 'mijn lief'],
        }
        
        # Check patterns
        for relatie, patterns in relatie_patterns.items():
            for pattern in patterns:
                if pattern in text_lower:
                    # Check if name is nearby (within 50 chars)
                    pattern_idx = text_lower.index(pattern)
                    name_idx = text_lower.find(name_lower, pattern_idx)
                    
                    if name_idx != -1 and (name_idx - pattern_idx) < 50:
                        return relatie
        
        return None
    
    @staticmethod
    def suggest_gradatie_from_relatie(relatie: Optional[str]) -> int:
        """
        Stel gradatie voor op basis van relatie
        
        Args:
            relatie: Detected relatie
            
        Returns:
            Suggested gradatie (1-7)
        """
        if not relatie:
            return 5  # Default: kennis
        
        relatie_lower = relatie.lower()
        
        # Gradatie mapping (op basis van Willem's systeem)
        if relatie_lower in ['dochter', 'zoon', 'partner', 'vader', 'moeder']:
            return 2  # Directe familie
        elif relatie_lower in ['broer', 'zus', 'opa', 'oma']:
            return 3  # Uitgebreide familie
        elif relatie_lower in ['vriend', 'vriendin', 'beste vriend']:
            return 3  # Goede vrienden
        elif relatie_lower in ['collega', 'baas']:
            return 4  # Werk relaties
        elif relatie_lower in ['kennis', 'bekende']:
            return 5  # Kennissen
        else:
            return 5  # Default
