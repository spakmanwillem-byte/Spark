"""
Personal Info Extractor Service
Extraheert persoonlijke informatie uit chatberichten voor auto-fill profiel
"""
import re
from typing import Dict, Optional, List
from datetime import datetime


class PersonalInfoExtractor:
    """Extract personal information from natural language"""
    
    # Patterns voor verschillende velden
    PATTERNS = {
        'beroep': [
            r'(?:ik werk als|mijn baan is|ik ben\s+(?:een\s+)?)([\w\s]+?)(?:\s+bij|\s+voor|\s+en|\.|\,|$)',
            r'(?:werk als|werken als|werkzaam als)\s+([\w\s]+?)(?:\s+bij|\s+voor|\.|$)',
            r'(?:beroep|job|functie):\s*([\w\s]+?)(?:\.|$)',
        ],
        'naam': [
            r'(?:mijn naam is|ik heet|noem me|naam:)\s+([A-Z][a-zéèêëïöü]+(?:\s+[A-Z][a-zéèêëïöü]+)?)(?=\s+(?:en|maar|en ik|,|\.)|\s*$)',
            r'^([A-Z][a-zéèêëïöü]+)\s+hier',
        ],
        'opleiding': [
            r'(?:gestudeerd|studie|diploma|afgestudeerd)\s+(?:in\s+)?([^\.]+?)(?:\s+aan|\.|$)',
            r'(?:opleiding|school|universiteit):\s*([^\.]+?)(?:\.|$)',
        ],
        'hobbies': [
            r'(?:hobby\'?s?|interesseer me voor|hou van|doe graag)\s*:?\s*([^\.]+?)(?:\.|$)',
            r'(?:vrije tijd|hobby)\s+(?:doe ik|is)\s+([^\.]+?)(?:\.|$)',
        ],
        'muziek_voorkeur': [
            r'(?:luister naar|muziek|genre|favoriet)\s*:?\s*(?:is\s+)?([^\.]+?)(?:\s+muziek|\.|$)',
            r'(?:hou van|fan van)\s+([\w\s]+?)\s+muziek',
        ],
        'film_voorkeur': [
            r'(?:films?|movies?|kijk graag)\s*:?\s*([^\.]+?)(?:\.|$)',
            r'(?:favoriete\s+(?:film|genre))\s*:?\s*([^\.]+?)(?:\.|$)',
        ],
        'game_voorkeur': [
            r'(?:games?|gaming|speel graag)\s*:?\s*([^\.]+?)(?:\.|$)',
            r'(?:favoriet spel|game)\s*:?\s*([^\.]+?)(?:\.|$)',
        ],
        'email': [
            r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
        ],
        'telefoon': [
            r'(?:telefoon|tel|mobiel|nummer)\s*:?\s*([\d\s\-\+\(\)]{8,})',
            r'(\+?\d{1,3}[\s\-]?\(?\d{1,4}\)?[\s\-]?\d{1,4}[\s\-]?\d{1,4}[\s\-]?\d{1,9})',
        ],
        'geboortedatum': [
            r'(?:geboren|geboortedatum|verjaardag)\s*:?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
        ],
        'adres': [
            r'(?:woon|adres|straat)\s*:?\s*([^,\.]+?)(?:\s+\d+[a-z]?)(?:\.|,|$)',
        ],
        'postcode': [
            r'\b(\d{4}\s*[A-Z]{2})\b',
        ],
        'plaats': [
            r'(?:woonplaats|plaats|stad|in)\s+([A-Z][a-zéèêëïöü]+(?:\s+[A-Z][a-zéèêëïöü]+)*)(?:\s+woon|\.|,|$)',
        ],
    }
    
    @staticmethod
    def extract_from_message(message: str) -> Dict[str, str]:
        """
        Extract persoonlijke info uit een enkel bericht
        
        Args:
            message: Chat bericht
            
        Returns:
            Dict met gevonden velden: {field_name: value}
        """
        extracted = {}
        message_lower = message.lower()
        
        for field, patterns in PersonalInfoExtractor.PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    value = match.group(1).strip()
                    # Clean up value
                    value = value.strip('.,!?;:')
                    if len(value) > 2:  # Minimale lengte
                        extracted[field] = value
                        break  # First match wins
        
        return extracted
    
    @staticmethod
    def extract_from_conversation(messages: List[Dict]) -> Dict[str, str]:
        """
        Extract info uit hele conversatie geschiedenis
        
        Args:
            messages: List van {content: str, isUser: bool, timestamp: str}
            
        Returns:
            Dict met alle gevonden persoonlijke info
        """
        all_extracted = {}
        
        for msg in messages:
            if msg.get('isUser', False):  # Alleen user berichten
                content = msg.get('content', '')
                extracted = PersonalInfoExtractor.extract_from_message(content)
                
                # Merge, maar overschrijf niet bestaande waarden
                for key, value in extracted.items():
                    if key not in all_extracted:
                        all_extracted[key] = value
        
        return all_extracted
    
    @staticmethod
    def get_empty_fields(user_profile: Dict) -> List[str]:
        """
        Check welke profiel velden leeg zijn
        
        Args:
            user_profile: User data dict
            
        Returns:
            List van lege veld namen
        """
        empty_fields = []
        
        # Check top-level fields
        if not user_profile.get('naam'):
            empty_fields.append('naam')
        if not user_profile.get('volledige_naam'):
            empty_fields.append('volledige_naam')
        
        # Check persoonlijke_info nested fields
        personal_info = user_profile.get('persoonlijke_info', {})
        
        fields_to_check = [
            'email', 'telefoon', 'geboortedatum', 'adres', 
            'postcode', 'plaats', 'beroep', 'opleiding', 
            'hobbies', 'muziek_voorkeur', 'film_voorkeur', 
            'game_voorkeur', 'over_mij'
        ]
        
        for field in fields_to_check:
            if not personal_info.get(field):
                empty_fields.append(field)
        
        return empty_fields
    
    @staticmethod
    def auto_fill_profile(user_profile: Dict, conversation_history: List[Dict]) -> Dict:
        """
        Auto-fill lege profiel velden uit conversatie
        
        Args:
            user_profile: Huidige user profile
            conversation_history: Alle chat berichten
            
        Returns:
            Dict met updates: {field: value, ...}
            + metadata: {updated_fields: [...], timestamp: ...}
        """
        # 1. Check welke velden leeg zijn
        empty_fields = PersonalInfoExtractor.get_empty_fields(user_profile)
        
        if not empty_fields:
            return {
                'updates': {},
                'metadata': {
                    'updated_fields': [],
                    'message': 'Geen lege velden gevonden',
                    'timestamp': datetime.now().isoformat()
                }
            }
        
        # 2. Extract info uit conversatie
        extracted_info = PersonalInfoExtractor.extract_from_conversation(conversation_history)
        
        # 3. Match extracted info met lege velden
        updates = {}
        for field in empty_fields:
            if field in extracted_info:
                updates[field] = extracted_info[field]
        
        return {
            'updates': updates,
            'metadata': {
                'updated_fields': list(updates.keys()),
                'empty_fields_checked': empty_fields,
                'extraction_count': len(extracted_info),
                'timestamp': datetime.now().isoformat()
            }
        }
    
    @staticmethod
    def should_auto_fill(user_profile: Dict) -> bool:
        """
        Check of auto-fill moet worden uitgevoerd
        
        Returns:
            True als er lege velden zijn
        """
        empty_fields = PersonalInfoExtractor.get_empty_fields(user_profile)
        return len(empty_fields) > 0
