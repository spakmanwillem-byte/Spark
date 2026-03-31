"""
Knowledge Fallback Service
Implements graceful degradation for knowledge lookup:
- When specific answer not found, fall back to general concept definition
- "Stap terug" strategy: provide context instead of "I don't know"
- Uses system_fallback.json for response templates
"""
from typing import Optional, Dict, List
from utils.data_manager import DataManager
import random


class KnowledgeFallbackService:
    """Graceful fallback for knowledge lookup"""
    
    _fallback_triggers = None
    
    @staticmethod
    def _get_fallback_triggers() -> Dict:
        """Load fallback triggers from JSON (cached)"""
        if KnowledgeFallbackService._fallback_triggers is None:
            KnowledgeFallbackService._fallback_triggers = DataManager.load_json("triggers/system_fallback.json")
        return KnowledgeFallbackService._fallback_triggers
    
    @staticmethod
    def get_no_understanding_response() -> str:
        """
        Get a random 'no understanding' response from triggers (NEW)
        """
        triggers = KnowledgeFallbackService._get_fallback_triggers()
        responses = triggers.get("no_understanding", [])
        if responses:
            return random.choice(responses)
        return "Ik begrijp het niet helemaal. Kun je het anders zeggen?"
    
    @staticmethod
    def get_topic_not_found_response() -> str:
        """
        Get a random 'topic not found' response from triggers (NEW)
        """
        triggers = KnowledgeFallbackService._get_fallback_triggers()
        responses = triggers.get("topic_not_found", [])
        if responses:
            return random.choice(responses)
        return "Dat is een goede vraag! Ik weet het antwoord nog niet."
    
    @staticmethod
    def find_related_by_tags(search_term: str, max_results: int = 3) -> List[Dict]:
        """
        Find related knowledge entries by shared tags
        Used for fallback when exact match not found
        """
        data = DataManager.load_json("learned_knowledge/knowledge_base.json")
        entries = data.get("knowledge_entries", [])
        
        search_lower = search_term.lower()
        related = []
        
        for entry in entries:
            # Skip if this IS the search term
            if entry.get("begrip", "").lower() == search_lower:
                continue
            
            # Check if search term appears in tags
            tags = entry.get("tags", [])
            if any(search_lower in tag.lower() or tag.lower() in search_lower for tag in tags):
                related.append(entry)
        
        return related[:max_results]
    
    @staticmethod
    def get_general_definition(concept: str) -> Optional[str]:
        """
        Get the basic definition (laag1) of a concept
        Used for fallback: step back to general explanation
        """
        data = DataManager.load_json("learned_knowledge/knowledge_base.json")
        entries = data.get("knowledge_entries", [])
        
        concept_lower = concept.lower()
        
        # Try exact match first
        for entry in entries:
            if entry.get("begrip", "").lower() == concept_lower:
                lagen = entry.get("lagen", {})
                if isinstance(lagen, dict) and "laag1" in lagen:
                    return lagen["laag1"].get("antwoord", "")
        
        # Try partial match in tags
        for entry in entries:
            tags = entry.get("tags", [])
            if concept_lower in [t.lower() for t in tags]:
                lagen = entry.get("lagen", {})
                if isinstance(lagen, dict) and "laag1" in lagen:
                    return lagen["laag1"].get("antwoord", "")
        
        return None
    
    @staticmethod
    def create_fallback_response(query: str, detected_concept: str) -> Optional[str]:
        """
        Create a fallback response when specific answer not found
        Strategy: Step back to general definition + offer to learn
        
        Example:
        Query: "Wat eten we vanavond?"
        Detected: "eten"
        Fallback: "Ik ken nog geen specifieke gerechten, maar eten is voeding tot je nemen om energie te krijgen."
        """
        # Get general definition of detected concept
        definition = KnowledgeFallbackService.get_general_definition(detected_concept)
        
        if definition:
            # Create helpful fallback response
            response = f"Ik ken nog geen specifieke {_get_plural(detected_concept)}, maar "
            response += definition.lower() if definition[0].isupper() else definition
            response += " Wil je dat ik hier meer over leer?"
            return response
        
        # Try to find related concepts
        related = KnowledgeFallbackService.find_related_by_tags(detected_concept, max_results=2)
        if related:
            related_names = [e.get("begrip") for e in related]
            return f"Ik weet niet precies over '{detected_concept}', maar ik ken wel: {', '.join(related_names)}. Wil je daar meer over weten?"
        
        return None


def _get_plural(word: str) -> str:
    """Simple Dutch plural helper"""
    plurals = {
        "eten": "gerechten",
        "gerecht": "gerechten",
        "recept": "recepten",
        "voedsel": "voedingsmiddelen",
        "dier": "dieren",
        "plant": "planten",
        "boom": "bomen",
        "auto": "auto's",
        "fiets": "fietsen",
    }
    return plurals.get(word.lower(), f"{word}en")
