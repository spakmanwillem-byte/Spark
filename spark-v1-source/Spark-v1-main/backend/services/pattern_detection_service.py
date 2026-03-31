"""
Pattern Detection Service - Detecteert patronen, stopwoorden en bijzonderheden in gesprekken
"""
from typing import Dict, List, Optional
from datetime import datetime
from collections import Counter
import re


class PatternDetectionService:
    """Detecteert patronen in gebruikersgedrag en taalgebruik"""
    
    # Stopwoorden die wijzen op belangrijke dingen
    STOP_WORDS = {
        "belangrijk": 5,
        "cruciaal": 5,
        "essentieel": 5,
        "let op": 4,
        "pas op": 4,
        "onthoud": 4,
        "nooit vergeten": 5,
        "altijd": 3,
        "nooit": 3,
        "moet": 3,
        "absoluut": 4,
        "zeker": 3
    }
    
    # Emotionele woorden
    EMOTIONAL_WORDS = {
        "blij": "positief",
        "gelukkig": "positief",
        "top": "positief",
        "geweldig": "positief",
        "perfect": "positief",
        "verdrietig": "negatief",
        "boos": "negatief",
        "gefrustreerd": "negatief",
        "teleurgesteld": "negatief",
        "bang": "negatief",
        "bezorgd": "negatief",
        "zorgen": "negatief"
    }
    
    @staticmethod
    def analyze_message(message: str, user_data: Optional[Dict] = None) -> Dict:
        """
        Analyseer een bericht voor patronen en bijzonderheden
        
        Returns:
            {
                "has_stop_words": bool,
                "stop_words_found": List[str],
                "importance_score": int (0-10),
                "emotional_tone": str,
                "key_phrases": List[str],
                "topics": List[str],
                "should_remember": bool
            }
        """
        message_lower = message.lower()
        
        # Detect stopwoorden
        stop_words_found = []
        importance_score = 0
        
        for stop_word, score in PatternDetectionService.STOP_WORDS.items():
            if stop_word in message_lower:
                stop_words_found.append(stop_word)
                importance_score += score
        
        # Detect emotionele toon
        emotional_tone = "neutraal"
        emotions_found = []
        
        for emotion_word, tone in PatternDetectionService.EMOTIONAL_WORDS.items():
            if emotion_word in message_lower:
                emotions_found.append(tone)
        
        if emotions_found:
            # Meest voorkomende emotie
            emotion_counter = Counter(emotions_found)
            emotional_tone = emotion_counter.most_common(1)[0][0]
        
        # Extract key phrases (zinnen met "is", "zijn", "moet")
        key_phrases = PatternDetectionService._extract_key_phrases(message)
        
        # Extract topics (belangrijke woorden)
        topics = PatternDetectionService._extract_topics(message)
        
        # Bepaal of dit onthouden moet worden
        should_remember = (
            importance_score >= 4 or
            len(stop_words_found) >= 2 or
            any(word in message_lower for word in ["onthoud", "belangrijk", "nooit vergeten"])
        )
        
        return {
            "has_stop_words": len(stop_words_found) > 0,
            "stop_words_found": stop_words_found,
            "importance_score": min(importance_score, 10),
            "emotional_tone": emotional_tone,
            "key_phrases": key_phrases,
            "topics": topics,
            "should_remember": should_remember,
            "raw_message": message
        }
    
    @staticmethod
    def _extract_key_phrases(message: str) -> List[str]:
        """Extract belangrijke zinnen"""
        # Split op punten en uitroeptekens
        sentences = re.split(r'[.!]+', message)
        
        key_phrases = []
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # Zinnen met "is", "zijn", "moet", "wil", "kan" zijn vaak belangrijk
            if any(word in sentence.lower() for word in [" is ", " zijn ", " moet ", " wil ", " kan ", " heeft ", " hebben "]):
                key_phrases.append(sentence)
        
        return key_phrases[:3]  # Max 3 phrases
    
    @staticmethod
    def _extract_topics(message: str) -> List[str]:
        """Extract belangrijke onderwerpen/woorden"""
        # Remove common woorden
        common_words = {'de', 'het', 'een', 'en', 'van', 'in', 'op', 'is', 'dat', 'die', 'aan', 'voor', 'met', 'als', 'zijn', 'er', 'maar', 'om', 'te', 'ze', 'bij', 'ook', 'naar', 'kan', 'wat', 'niet', 'dit', 'hij', 'heeft', 'was', 'zijn', 'me', 'je', 'we', 'mijn', 'of', 'dan', 'uit'}
        
        # Extract woorden
        words = re.findall(r'\b\w+\b', message.lower())
        
        # Filter en count
        word_counts = Counter([w for w in words if w not in common_words and len(w) > 3])
        
        # Return top 5
        return [word for word, count in word_counts.most_common(5)]
    
    @staticmethod
    def detect_user_patterns(user_id: str, conversation_history: List[Dict]) -> Dict:
        """
        Analyseer gesprekgeschiedenis voor patronen
        
        Args:
            conversation_history: List van {message, response, timestamp}
            
        Returns:
            {
                "frequent_topics": List[str],
                "communication_style": str,
                "interests": List[str],
                "concerns": List[str]
            }
        """
        if not conversation_history:
            return {
                "frequent_topics": [],
                "communication_style": "onbekend",
                "interests": [],
                "concerns": []
            }
        
        all_messages = [conv.get("message", "") for conv in conversation_history]
        combined_text = " ".join(all_messages).lower()
        
        # Frequent topics
        words = re.findall(r'\b\w+\b', combined_text)
        common_words = {'de', 'het', 'een', 'en', 'van', 'in', 'op', 'is', 'dat', 'die', 'aan', 'voor', 'met', 'als', 'zijn', 'er', 'maar', 'om', 'te', 'ze', 'bij', 'ook', 'naar', 'kan', 'wat', 'niet', 'dit', 'hij', 'heeft', 'was', 'zijn', 'me', 'je', 'we', 'mijn', 'of', 'dan', 'uit'}
        
        filtered_words = [w for w in words if w not in common_words and len(w) > 3]
        word_freq = Counter(filtered_words)
        
        frequent_topics = [word for word, count in word_freq.most_common(10) if count >= 2]
        
        # Communication style
        avg_length = sum(len(msg.split()) for msg in all_messages) / len(all_messages) if all_messages else 0
        
        if avg_length < 5:
            comm_style = "kort en bondig"
        elif avg_length < 15:
            comm_style = "normaal"
        else:
            comm_style = "uitgebreid en gedetailleerd"
        
        # Extract interests (woorden die vaak voorkomen met positieve context)
        interests = [topic for topic in frequent_topics[:5]]
        
        # Extract concerns (woorden bij negatieve emoties)
        concerns = []
        for msg in all_messages:
            if any(word in msg for word in ["probleem", "zorgen", "bang", "moeilijk", "help"]):
                # Extract context
                words_in_msg = re.findall(r'\b\w{4,}\b', msg)
                concerns.extend([w for w in words_in_msg if w not in common_words][:2])
        
        return {
            "frequent_topics": frequent_topics[:5],
            "communication_style": comm_style,
            "interests": interests,
            "concerns": list(set(concerns))[:5]
        }
    
    @staticmethod
    def create_insight_note(analysis: Dict, user_name: str) -> Dict:
        """
        Maak een notitie aan op basis van pattern analysis
        
        Returns notitie data voor NotesService
        """
        if not analysis.get("should_remember"):
            return None
        
        # Creëer titel
        if analysis["stop_words_found"]:
            titel = f"Belangrijk: {analysis['stop_words_found'][0]}"
        elif analysis["key_phrases"]:
            titel = analysis["key_phrases"][0][:50]
        else:
            titel = "Bijzonderheid gedetecteerd"
        
        # Creëer inhoud
        inhoud_parts = []
        
        if analysis["key_phrases"]:
            inhoud_parts.append(f"Key phrase: {analysis['key_phrases'][0]}")
        
        if analysis["topics"]:
            inhoud_parts.append(f"Onderwerpen: {', '.join(analysis['topics'])}")
        
        if analysis["emotional_tone"] != "neutraal":
            inhoud_parts.append(f"Emotie: {analysis['emotional_tone']}")
        
        inhoud_parts.append(f"\nOrigineel bericht: {analysis['raw_message']}")
        
        return {
            "titel": titel,
            "inhoud": "\n".join(inhoud_parts),
            "categorie": "Observatie",
            "tags": ["auto-detected", "pattern", user_name],
            "created_by": "Spark AI (automatisch)"
        }
