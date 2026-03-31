"""
Keyword Analyzer - Extraheert keywords, topics en belangrijke woorden
"""
from typing import Dict, List
from services.pattern_detection_service import PatternDetectionService
from .models import KeywordAnalysis
from .helpers import extract_keywords


class KeywordAnalyzer:
    """
    Analyseert keywords, topics en stop woorden.
    Hergebruikt PatternDetectionService voor pattern detectie.
    """
    
    def __init__(self):
        self.pattern_service = PatternDetectionService()
    
    def analyze(self, text: str, user_data: Dict = None) -> KeywordAnalysis:
        """
        Analyseer text voor keywords en topics
        
        Args:
            text: Input text
            user_data: Optional user data voor context
        
        Returns:
            KeywordAnalysis object
        """
        # Hergebruik PatternDetectionService voor pattern analyse
        patterns = self.pattern_service.analyze_message(text, user_data)
        
        # Extract keywords (basic)
        keywords = extract_keywords(text, limit=5)
        
        # Get topics from pattern service
        topics = patterns.get('topics', [])
        
        # Stop woorden (belangrijke signaalwoorden)
        has_stop_words = patterns.get('has_stop_words', False)
        stop_words_found = patterns.get('stop_words_found', [])
        importance_score = patterns.get('importance_score', 0)
        
        # Named entities (TODO: implement proper NER later)
        entities = self._extract_basic_entities(text)
        
        return KeywordAnalysis(
            primary_keywords=keywords,
            topics=topics,
            entities=entities,
            has_stop_words=has_stop_words,
            stop_words_found=stop_words_found,
            importance_score=importance_score
        )
    
    def _extract_basic_entities(self, text: str) -> List[str]:
        """
        Basic entity extraction (capitalized words)
        Later kunnen we dit uitbreiden met spaCy NER
        """
        import re
        # Find capitalized words (potential names/places)
        entities = re.findall(r'\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)*\b', text)
        # Remove common false positives
        entities = [e for e in entities if e.lower() not in ['ik', 'spark', 'wat']]
        return list(set(entities))[:5]  # Max 5, unique
