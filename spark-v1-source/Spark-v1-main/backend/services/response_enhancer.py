"""
Response Enhancer - Gebruikt ContextualAnalysis om responses te verbeteren

Enhancement strategies:
- Style adjustment (brief, detailed, empathetic, playful)
- Phase-appropriate responses (greeting, ongoing, closing)
- User pattern responses (frustration, enthusiasm, curiosity)
- Topic personalization (long-term interests)

Performance: < 50ms overhead (rule-based, no LLM calls)
"""
from typing import Optional
from services.context_layer import ContextualAnalysis
import random


class ResponseEnhancer:
    """
    Lightweight response enhancement using contextual analysis.
    
    Fast, rule-based enhancement without heavy processing.
    """
    
    def __init__(self):
        # Enhancement templates
        self.empathy_phrases = [
            "Ik snap dat dit vervelend kan zijn. ",
            "Dat klinkt frustrerend. ",
            "Ik begrijp je zorgen. ",
            "Laat me je helpen. "
        ]
        
        self.encouragement_phrases = [
            "Wat goed om te horen! ",
            "Geweldig! ",
            "Super dat je dat vraagt! ",
            "Dat is interessant! "
        ]
        
        self.playful_additions = [
            " 😊",
            " ✨",
            "!",
            " 🎉"
        ]
        
        self.closing_phrases = [
            "\n\nIs er nog iets anders waar ik je mee kan helpen?",
            "\n\nWas dit nuttig?",
            "\n\nZit je nog ergens mee?",
            "\n\nNog andere vragen?"
        ]
    
    def enhance(
        self,
        base_response: str,
        contextual_analysis: Optional[ContextualAnalysis],
        user_name: Optional[str] = None
    ) -> str:
        """
        Enhance response based on contextual analysis.
        
        Args:
            base_response: Original response
            contextual_analysis: Rich context from Context Layer
            user_name: User's name for personalization
        
        Returns:
            Enhanced response
        """
        
        if not contextual_analysis:
            return base_response
        
        enhanced = base_response
        
        # 1. Handle conversation phase
        enhanced = self._apply_phase_enhancement(
            enhanced,
            contextual_analysis.conversation_phase,
            user_name
        )
        
        # 2. Respond to user patterns
        enhanced = self._apply_pattern_response(
            enhanced,
            contextual_analysis
        )
        
        # 3. Apply response style
        enhanced = self._apply_style(
            enhanced,
            contextual_analysis.suggested_response_style
        )
        
        # 4. Add topic personalization (if appropriate)
        enhanced = self._add_topic_reference(
            enhanced,
            contextual_analysis
        )
        
        return enhanced
    
    def _apply_phase_enhancement(
        self,
        response: str,
        phase: str,
        user_name: Optional[str]
    ) -> str:
        """Apply phase-appropriate enhancements"""
        
        if phase == "greeting":
            # Add warm greeting
            if user_name:
                return f"Hey {user_name}! {response}"
            else:
                return f"Hey! {response}"
        
        elif phase == "closing":
            # Add closing phrase if not already present
            if not any(phrase in response.lower() for phrase in ["nog iets", "verder", "anders"]):
                closing = random.choice(self.closing_phrases)
                return response + closing
        
        return response
    
    def _apply_pattern_response(
        self,
        response: str,
        context: ContextualAnalysis
    ) -> str:
        """Respond to detected user patterns"""
        
        # Frustration → Empathy
        if context.user_shows_frustration:
            empathy = random.choice(self.empathy_phrases)
            return empathy + response
        
        # Enthusiasm → Encouragement
        if context.user_shows_enthusiasm:
            encouragement = random.choice(self.encouragement_phrases)
            return encouragement + response
        
        # Curiosity → Keep it detailed (no change needed, just acknowledge)
        if context.user_shows_curiosity and context.conversation.is_deep_inquiry:
            # Already handled by style suggestion
            pass
        
        return response
    
    def _apply_style(
        self,
        response: str,
        style: str
    ) -> str:
        """Apply suggested response style"""
        
        if style == "brief":
            # Shorten if too long
            if len(response) > 150:
                # Take first sentence or paragraph
                sentences = response.split('. ')
                if sentences:
                    return sentences[0] + '.'
        
        elif style == "empathetic":
            # Add empathetic tone (already done in pattern_response usually)
            # Ensure response is supportive
            pass
        
        elif style == "playful":
            # Add playful element if not present
            if not any(emoji in response for emoji in ['😊', '✨', '🎉', '!']):
                addition = random.choice(self.playful_additions)
                return response + addition
        
        elif style == "detailed":
            # Keep full response (no truncation)
            # Could add "Wil je meer details?" if very short
            if len(response) < 50:
                return response + "\n\nZal ik verder uitleggen?"
        
        # "informative" = default, no changes needed
        
        return response
    
    def _add_topic_reference(
        self,
        response: str,
        context: ContextualAnalysis
    ) -> str:
        """Add personalized topic reference if relevant"""
        
        # Check if we're continuing a topic
        if context.is_topic_continuation and context.previous_topic:
            # Topic is already being discussed, no need to reference
            pass
        
        # Check long-term interests (from summaries)
        long_term_topics = context.conversation.long_term_topics
        current_topic = context.content.primary_topic
        
        # If current topic matches long-term interest, acknowledge it
        if current_topic and long_term_topics:
            if current_topic in long_term_topics:
                # Subtle acknowledgment
                # Don't add if response is already short
                if len(response) > 100:
                    addition = f"\n\n_Ik zie dat {current_topic} je al langer interesseert!_"
                    return response + addition
        
        return response
    
    def add_word_limit_truncation(self, response: str, word_limit: int) -> str:
        """
        Apply word limit truncation (from emotion system).
        
        This is separate from style enhancement.
        
        Args:
            response: Response text
            word_limit: Maximum words
        
        Returns:
            Truncated response if needed
        """
        words = response.split()
        
        if len(words) <= word_limit:
            return response
        
        # Truncate and add indicator
        truncated = ' '.join(words[:word_limit])
        return truncated + "..."
    
    def adjust_tone(self, response: str, target_tone: str) -> str:
        """
        Adjust response tone to match user's tone.
        
        Args:
            response: Response text
            target_tone: Desired tone (from content analysis)
        
        Returns:
            Tone-adjusted response
        """
        
        # This is a placeholder for more sophisticated tone matching
        # For now, we use style suggestions
        
        if target_tone == "urgent":
            # Add urgency/directness
            # Remove fluff, keep it direct
            pass
        
        elif target_tone == "casual":
            # Make more casual
            # Could replace formal words with casual ones
            pass
        
        elif target_tone == "friendly":
            # Already handled by enthusiasm detection
            pass
        
        return response


# Singleton instance
_response_enhancer = None

def get_response_enhancer() -> ResponseEnhancer:
    """Get singleton response enhancer"""
    global _response_enhancer
    if _response_enhancer is None:
        _response_enhancer = ResponseEnhancer()
    return _response_enhancer
