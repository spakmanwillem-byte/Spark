"""
Compliment Detector - Detecteert complimenten en waardering
"""
from typing import List, Tuple
from .models import ComplimentAnalysis


class ComplimentDetector:
    """
    Detecteert complimenten, waardering en dankbaarheid in berichten.
    """
    
    def __init__(self):
        # Compliment patterns (Nederlands)
        self.direct_compliments = [
            'geweldig', 'super', 'top', 'goed gedaan', 'knap', 'slim',
            'mooi', 'perfect', 'uitstekend', 'fantastisch', 'prachtig',
            'geweldig werk', 'goed bezig', 'leuk', 'cool', 'vet'
        ]
        
        self.gratitude_phrases = [
            'bedankt', 'dank je', 'dank u', 'dankjewel', 'dankuwel',
            'thanks', 'thx', 'merci', 'top bedankt'
        ]
        
        self.praise_phrases = [
            'je bent', 'jij bent', 'dat is', 'dit is',
            'je doet het', 'je helpt', 'spark is'
        ]
    
    def analyze(self, text: str) -> ComplimentAnalysis:
        """
        Analyseer text voor complimenten
        
        Args:
            text: Input text
        
        Returns:
            ComplimentAnalysis object
        """
        text_lower = text.lower()
        
        # Detect compliment type
        compliment_type = None
        compliment_phrases = []
        targets = []
        intensity = 0.0
        
        # Check voor directe complimenten
        direct_found = [word for word in self.direct_compliments if word in text_lower]
        if direct_found:
            compliment_type = 'direct'
            compliment_phrases.extend(direct_found)
            intensity += 0.7
            targets = self._extract_targets(text_lower, 'direct')
        
        # Check voor dankbaarheid
        gratitude_found = [phrase for phrase in self.gratitude_phrases if phrase in text_lower]
        if gratitude_found:
            if compliment_type is None:
                compliment_type = 'gratitude'
            compliment_phrases.extend(gratitude_found)
            intensity += 0.6
            targets = self._extract_targets(text_lower, 'gratitude')
        
        # Check voor indirecte praise
        if not compliment_type:
            for phrase in self.praise_phrases:
                if phrase in text_lower:
                    # Check if followed by positive word
                    if any(pos in text_lower for pos in self.direct_compliments):
                        compliment_type = 'indirect'
                        intensity += 0.5
                        targets = self._extract_targets(text_lower, 'indirect')
                        break
        
        # Calculate final intensity
        if compliment_type:
            # Boost voor meerdere complimenten
            intensity = min(1.0, intensity + (len(compliment_phrases) - 1) * 0.1)
        
        has_compliment = compliment_type is not None
        
        return ComplimentAnalysis(
            has_compliment=has_compliment,
            compliment_type=compliment_type,
            compliment_intensity=intensity,
            targets=targets,
            compliment_phrases=compliment_phrases
        )
    
    def _extract_targets(self, text: str, compliment_type: str) -> List[str]:
        """
        Probeer te detecteren wie/wat geprezen wordt
        
        Returns:
            List van targets (bijv. ["spark", "system"])
        """
        targets = []
        
        # Check voor expliciete targets
        if 'spark' in text or 'jij' in text or 'je' in text:
            targets.append('spark')
        
        if any(word in text for word in ['systeem', 'platform', 'app', 'website']):
            targets.append('system')
        
        if 'dit' in text or 'dat' in text:
            targets.append('feature')
        
        # Default target als geen specifieke gevonden
        if not targets:
            targets.append('general')
        
        return targets
