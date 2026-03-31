"""
Language Style Analyzer - Analyseert toon, sentiment en stijl
"""
from typing import Dict
from services.nlp_service import NLPService
from services.pattern_detection_service import PatternDetectionService
from .models import LanguageStyle, ComplimentAnalysis
from .helpers import (
    count_words,
    calculate_avg_word_length,
    count_questions,
    has_emoji,
    has_capitals_emphasis,
    has_punctuation_emphasis,
    calculate_formality,
    calculate_emotional_intensity
)


class LanguageStyleAnalyzer:
    """
    Analyseert de taalstijl: toon, sentiment, formaliteit, emotionele intensiteit.
    Hergebruikt NLPService en PatternDetectionService.
    """
    
    def __init__(self):
        self.nlp_service = NLPService()
        self.pattern_service = PatternDetectionService()
    
    def analyze(
        self,
        text: str,
        compliment_analysis: ComplimentAnalysis,
        user_data: Dict = None
    ) -> LanguageStyle:
        """
        Analyseer taalstijl van text
        
        Args:
            text: Input text
            compliment_analysis: Compliment analyse (voor style context)
            user_data: Optional user data
        
        Returns:
            LanguageStyle object
        """
        # Hergebruik NLPService voor sentiment
        sentiment = self.nlp_service.detect_sentiment(text)
        
        # Hergebruik PatternDetectionService voor emotional tone
        patterns = self.pattern_service.analyze_message(text, user_data)
        emotional_tone = patterns.get('emotional_tone', 'neutraal')
        
        # Map emotional_tone naar tone
        tone = self._determine_tone(text, sentiment, emotional_tone, compliment_analysis)
        
        # Calculate metrics
        formality = calculate_formality(text)
        emotional_intensity = calculate_emotional_intensity(text, sentiment)
        
        # Style markers
        uses_emoji = has_emoji(text)
        uses_capitals = has_capitals_emphasis(text)
        uses_punctuation = has_punctuation_emphasis(text)
        
        # Word metrics
        word_count = count_words(text)
        avg_word_length = calculate_avg_word_length(text)
        question_count = count_questions(text)
        
        # Compliment info
        contains_compliments = compliment_analysis.has_compliment
        compliment_targets = compliment_analysis.targets
        
        return LanguageStyle(
            tone=tone,
            sentiment=sentiment,
            formality_level=formality,
            emotional_intensity=emotional_intensity,
            uses_emoji=uses_emoji,
            uses_capitals=uses_capitals,
            uses_punctuation_emphasis=uses_punctuation,
            contains_compliments=contains_compliments,
            compliment_targets=compliment_targets,
            word_count=word_count,
            avg_word_length=avg_word_length,
            question_count=question_count
        )
    
    def _determine_tone(self, text: str, sentiment: str, emotional_tone: str, compliment: ComplimentAnalysis) -> str:
        """
        Bepaal de algemene toon van het bericht
        
        Returns:
            "friendly", "formal", "casual", "urgent", "playful", "neutral"
        """
        text_lower = text.lower()
        
        # Urgent markers
        if any(word in text_lower for word in ['help', 'snel', 'dringend', 'nu']):
            if has_punctuation_emphasis(text):
                return 'urgent'
        
        # Playful markers
        if has_emoji(text) or any(word in text_lower for word in ['haha', 'lol', 'leuk']):
            return 'playful'
        
        # Friendly markers
        if compliment.has_compliment or sentiment == 'positief':
            return 'friendly'
        
        # Formal markers
        formality = calculate_formality(text)
        if formality > 0.7:
            return 'formal'
        
        # Casual markers
        if formality < 0.3:
            return 'casual'
        
        # Default
        return 'neutral'
