"""
Content Engine - Hub/Orchestrator voor content analyse

Coördineert alle analyzers en produceert een unified ContentAnalysis output.
"""
from datetime import datetime
from typing import Dict, Optional

from .models import ContentAnalysis
from .keyword_analyzer import KeywordAnalyzer
from .intent_detector import IntentDetector
from .compliment_detector import ComplimentDetector
from .language_style_analyzer import LanguageStyleAnalyzer


class ContentEngine:
    """
    Content Engine Hub - Coördineert alle content analyzers.
    
    Flow:
    1. Keyword Analysis (topics, entities)
    2. Intent Detection (wat wil de user?)
    3. Compliment Detection (waardering)
    4. Language Style Analysis (hoe wordt het gezegd?)
    5. Combine results → ContentAnalysis
    
    Usage:
        engine = ContentEngine()
        analysis = engine.analyze("Hey Spark, wat is een auto?", user_data=user)
    """
    
    def __init__(self):
        # Initialize all analyzers
        self.keyword_analyzer = KeywordAnalyzer()
        self.intent_detector = IntentDetector()
        self.compliment_detector = ComplimentDetector()
        self.language_style_analyzer = LanguageStyleAnalyzer()
    
    def analyze(self, text: str, user_data: Optional[Dict] = None) -> ContentAnalysis:
        """
        Main entry point: Analyseer content volledig.
        
        Args:
            text: De input text om te analyseren
            user_data: Optional user data voor context (dict met user info)
        
        Returns:
            ContentAnalysis object met alle analyses
        """
        start_time = datetime.now()
        
        # Run all analyzers
        keywords = self.keyword_analyzer.analyze(text, user_data)
        intent = self.intent_detector.analyze(text)
        compliments = self.compliment_detector.analyze(text)
        language_style = self.language_style_analyzer.analyze(text, compliments, user_data)
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Determine primary topic (first topic from keywords)
        primary_topic = keywords.topics[0] if keywords.topics else None
        
        # Quick access properties
        tone = language_style.tone
        sentiment = language_style.sentiment
        
        # Calculate overall confidence
        confidence = self._calculate_confidence(keywords, intent, language_style)
        
        # Build unified result
        return ContentAnalysis(
            text=text,
            language_style=language_style,
            intent=intent,
            keywords=keywords,
            compliments=compliments,
            primary_topic=primary_topic,
            tone=tone,
            sentiment=sentiment,
            analyzed_at=datetime.now(),
            processing_time_ms=int(processing_time),
            confidence=confidence
        )
    
    def _calculate_confidence(self, keywords, intent, language_style) -> float:
        """
        Bereken overall confidence van de analyse.
        
        Gebaseerd op:
        - Intent confidence
        - Aantal gevonden keywords
        - Duidelijkheid van sentiment
        """
        confidence = 0.0
        
        # Intent confidence (40%)
        confidence += intent.confidence * 0.4
        
        # Keywords (30%)
        if keywords.topics:
            confidence += 0.3
        elif keywords.primary_keywords:
            confidence += 0.15
        
        # Sentiment duidelijkheid (30%)
        if language_style.sentiment in ['positief', 'negatief']:
            confidence += 0.3  # Duidelijk sentiment
        else:
            confidence += 0.15  # Neutraal is minder duidelijk
        
        return min(1.0, confidence)


# Export all public classes
__all__ = [
    'ContentEngine',
    'ContentAnalysis',
    'KeywordAnalyzer',
    'IntentDetector',
    'ComplimentDetector',
    'LanguageStyleAnalyzer'
]
