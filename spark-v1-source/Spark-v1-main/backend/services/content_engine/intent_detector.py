"""
Intent Detector - Detecteert de intentie van het bericht
"""
from typing import Dict, Optional, Tuple
from services.nlp_service import NLPService
from .models import IntentAnalysis
from .helpers import count_questions, detect_question_type


class IntentDetector:
    """
    Detecteert primaire intentie: vraag, statement, commando, begroeting, etc.
    Hergebruikt NLPService voor command detection.
    """
    
    def __init__(self):
        self.nlp_service = NLPService()
    
    def analyze(self, text: str) -> IntentAnalysis:
        """
        Analyseer intentie van text
        
        Args:
            text: Input text
        
        Returns:
            IntentAnalysis object
        """
        text_lower = text.lower().strip()
        
        # Check voor commands (hergebruik NLPService)
        command_result = self.nlp_service.detect_command(text)
        is_command = command_result is not None
        command_type = command_result[0] if command_result else None
        command_content = command_result[1] if command_result else None
        
        # Check voor vraag
        is_question = '?' in text or count_questions(text) > 0
        question_type = detect_question_type(text) if is_question else None
        
        # Check voor teaching signal
        is_teaching, teaching_signal = self._detect_teaching(text_lower)
        
        # Bepaal primary intent
        primary_intent, confidence = self._determine_primary_intent(
            text_lower,
            is_command,
            is_question,
            is_teaching
        )
        
        return IntentAnalysis(
            primary_intent=primary_intent,
            confidence=confidence,
            is_command=is_command,
            command_type=command_type,
            command_content=command_content,
            is_question=is_question,
            question_type=question_type,
            is_teaching=is_teaching,
            teaching_signal=teaching_signal
        )
    
    def _detect_teaching(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        Detecteer of user iets wil leren/onderwijzen
        
        Returns:
            (is_teaching, signal)
        """
        teaching_signals = [
            'leer jezelf',
            'onthoud',
            'onthoud dit',
            'dit is belangrijk',
            'weet dat',
            'je moet weten',
            'ik vertel je'
        ]
        
        for signal in teaching_signals:
            if signal in text:
                return True, signal
        
        return False, None
    
    def _determine_primary_intent(
        self,
        text: str,
        is_command: bool,
        is_question: bool,
        is_teaching: bool
    ) -> Tuple[str, float]:
        """
        Bepaal de primaire intentie met confidence
        
        Returns:
            (intent, confidence)
        """
        # Priority order: command > teaching > question > greeting > statement
        
        if is_command:
            return 'command', 0.9
        
        if is_teaching:
            return 'teaching', 0.85
        
        if is_question:
            return 'question', 0.9
        
        # Check voor begroeting
        greetings = ['hoi', 'hey', 'hallo', 'goedemorgen', 'goedemiddag', 'goedenavond']
        if any(greeting in text for greeting in greetings):
            return 'greeting', 0.8
        
        # Default: statement
        return 'statement', 0.7
