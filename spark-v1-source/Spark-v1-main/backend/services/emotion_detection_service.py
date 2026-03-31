"""
Emotion Detection Service - Detecteert emoties in berichten via trigger woorden

HYBRIDE SYSTEEM:
1. STATIC: Hard-coded triggers in emotion_triggers.json (basis)
2. DYNAMIC: Leert van knowledge cards met #emotie-* tags (groeit mee)

4 Basis Emoties:
- Blij (positief)
- Boos (negatief - woede)
- Bang (negatief - angst)
- Bedroefd (negatief - verdriet)

Anti-misbruik: Elk woord max 3x per bericht

DYNAMISCH LEREN:
- Willem vult knowledge cards in met #emotie-boos, #emotie-blij, etc.
- Systeem leest deze tags en gebruikt ze als triggers
- Complexe emoties mogelijk: "oorlog" kan #emotie-boos + #emotie-bedroefd hebben
- Context emoties: "opbouw" kan #emotie-blij + #emotie-bang hebben
"""
from typing import Dict, List, Optional, Tuple
from utils.data_manager import DataManager
from collections import Counter
import random


class EmotionDetectionService:
    """Service voor het detecteren van emoties in berichten"""
    
    _triggers_cache = None
    _learned_triggers_cache = None
    
    @staticmethod
    def _load_triggers() -> Dict:
        """Load emotion triggers from JSON (cached)"""
        if EmotionDetectionService._triggers_cache is None:
            EmotionDetectionService._triggers_cache = DataManager.load_json("triggers/emotion_triggers.json")
        return EmotionDetectionService._triggers_cache
    
    @staticmethod
    def _load_learned_triggers() -> Dict:
        """
        Load LEARNED emotion triggers from knowledge cards with #emotie-* tags
        
        Returns:
            {
                "blij": {"woord1": 3, "woord2": 2, ...},
                "boos": {...},
                "bang": {...},
                "bedroefd": {...}
            }
        """
        # Cache for 60 seconds (so Willem's edits are picked up quickly)
        import time
        current_time = time.time()
        
        if (EmotionDetectionService._learned_triggers_cache and 
            current_time - EmotionDetectionService._learned_triggers_cache.get('cached_at', 0) < 60):
            return EmotionDetectionService._learned_triggers_cache['data']
        
        # Load knowledge base
        knowledge_data = DataManager.load_json("learned_knowledge/knowledge_base.json")
        entries = knowledge_data.get("knowledge_entries", [])
        
        # Build learned triggers from tags
        learned = {
            "blij": {},
            "boos": {},
            "bang": {},
            "bedroefd": {}
        }
        
        for entry in entries:
            # Only active cards (niet draft)
            if entry.get("status") != "active":
                continue
            
            begrip = entry.get("begrip", "").lower()
            tags = entry.get("tags", [])
            
            # Check for #emotie-* tags
            for tag in tags:
                tag_lower = tag.lower().strip()
                
                # Support both #emotie-blij and emotie-blij formats
                if tag_lower == "#emotie-blij" or tag_lower == "emotie-blij":
                    learned["blij"][begrip] = 3  # Score 3 (standaard)
                elif tag_lower == "#emotie-boos" or tag_lower == "emotie-boos":
                    learned["boos"][begrip] = 3
                elif tag_lower == "#emotie-bang" or tag_lower == "emotie-bang":
                    learned["bang"][begrip] = 3
                elif tag_lower == "#emotie-bedroefd" or tag_lower == "emotie-bedroefd":
                    learned["bedroefd"][begrip] = 3
        
        # Cache result
        EmotionDetectionService._learned_triggers_cache = {
            'data': learned,
            'cached_at': current_time
        }
        
        return learned
    
    @staticmethod
    def detect_emotion(message: str) -> Optional[Dict]:
        """
        Detecteer emotie in een bericht
        
        HYBRIDE: Gebruikt ZOWEL hard-coded triggers ALS learned triggers (van tags)
        
        Returns:
            {
                "emotion": "blij" | "boos" | "bang" | "bedroefd",
                "score": int (totaal aantal punten),
                "intensity": float (0.0 - 1.0),
                "triggered_words": List[str] (welke woorden triggerde),
                "source": "static" | "learned" | "both",
                "emoji": str,
                "empathic_response": str
            }
            
            Of None als geen emotie gedetecteerd
        """
        triggers_data = EmotionDetectionService._load_triggers()
        learned_triggers = EmotionDetectionService._load_learned_triggers()
        
        emotions = triggers_data.get("emotions", {})
        meta = triggers_data.get("meta", {})
        
        max_word_count = meta.get("max_word_count", 3)
        min_score = meta.get("min_score_for_detection", 3)
        
        # Normalize message
        message_lower = message.lower()
        
        # Count words in message (for anti-misbruik)
        words_in_message = message_lower.split()
        word_frequency = Counter(words_in_message)
        
        # Score each emotion - COMBINE static + learned
        emotion_scores = {}
        
        for emotion_name, emotion_data in emotions.items():
            score = 0
            triggered_words = []
            sources = set()
            
            # 1. STATIC triggers (hard-coded)
            trigger_dict = emotion_data.get("triggers", {})
            
            for trigger_word, points in trigger_dict.items():
                if trigger_word in message_lower:
                    occurrences = min(word_frequency.get(trigger_word, 0), max_word_count)
                    
                    if occurrences > 0:
                        score += points * occurrences
                        triggered_words.append(trigger_word)
                        sources.add("static")
            
            # 2. LEARNED triggers (from knowledge cards tags)
            learned_emotion_triggers = learned_triggers.get(emotion_name, {})
            
            for trigger_word, points in learned_emotion_triggers.items():
                if trigger_word in message_lower:
                    occurrences = min(word_frequency.get(trigger_word, 0), max_word_count)
                    
                    if occurrences > 0:
                        score += points * occurrences
                        if trigger_word not in triggered_words:
                            triggered_words.append(f"{trigger_word} (learned)")
                        sources.add("learned")
            
            if score > 0:
                # Determine source
                if len(sources) == 2:
                    source = "both"
                elif "learned" in sources:
                    source = "learned"
                else:
                    source = "static"
                
                emotion_scores[emotion_name] = {
                    "score": score,
                    "triggered_words": triggered_words,
                    "source": source,
                    "emoji": emotion_data.get("emoji", ""),
                    "color": emotion_data.get("color", "")
                }
        
        # No emotion detected
        if not emotion_scores:
            return None
        
        # Find dominant emotion
        dominant_emotion = max(emotion_scores.items(), key=lambda x: x[1]["score"])
        emotion_name = dominant_emotion[0]
        emotion_info = dominant_emotion[1]
        
        # Check if score meets minimum threshold
        if emotion_info["score"] < min_score:
            return None
        
        # Calculate intensity (0.0 - 1.0)
        score = emotion_info["score"]
        if score <= 5:
            intensity = 0.3 + (score / 5) * 0.2
        elif score <= 10:
            intensity = 0.5 + ((score - 5) / 5) * 0.2
        else:
            intensity = min(0.7 + ((score - 10) / 10) * 0.3, 1.0)
        
        # Get empathic response
        empathic_responses = triggers_data.get("empathic_responses", {}).get(emotion_name, [])
        empathic_response = random.choice(empathic_responses) if empathic_responses else None
        
        return {
            "emotion": emotion_name,
            "score": score,
            "intensity": round(intensity, 2),
            "triggered_words": emotion_info["triggered_words"],
            "source": emotion_info["source"],
            "emoji": emotion_info["emoji"],
            "color": emotion_info["color"],
            "empathic_response": empathic_response
        }
    
    @staticmethod
    def get_all_triggers() -> Dict:
        """Get all emotion triggers (for admin/debug)"""
        return EmotionDetectionService._load_triggers()
    
    @staticmethod
    def should_respond_empathically(emotion_detection: Optional[Dict]) -> bool:
        """
        Check if we should give an empathic response
        
        Criteria:
        - Negative emotions (boos, bang, bedroefd) always get empathic response
        - Positive emotions (blij) only if intensity > 0.5
        """
        if not emotion_detection:
            return False
        
        emotion = emotion_detection.get("emotion")
        intensity = emotion_detection.get("intensity", 0)
        
        # Always respond to negative emotions
        if emotion in ["boos", "bang", "bedroefd"]:
            return True
        
        # Respond to strong positive emotions
        if emotion == "blij" and intensity > 0.5:
            return True
        
        return False
    
    @staticmethod
    def format_emotion_debug_info(emotion_detection: Dict) -> str:
        """Format emotion detection info for admin debugging"""
        if not emotion_detection:
            return "Geen emotie gedetecteerd"
        
        emotion = emotion_detection.get("emotion")
        score = emotion_detection.get("score")
        intensity = emotion_detection.get("intensity")
        source = emotion_detection.get("source", "unknown")
        triggered = ", ".join(emotion_detection.get("triggered_words", []))
        emoji = emotion_detection.get("emoji", "")
        
        source_emoji = "📚" if source == "static" else "🧠" if source == "learned" else "🔀"
        
        return (
            f"{emoji} **Emotie: {emotion.upper()}** {source_emoji}\n"
            f"Score: {score} | Intensiteit: {intensity} | Bron: {source}\n"
            f"Triggered: {triggered}"
        )
    
    @staticmethod
    def get_learned_emotions_count() -> Dict:
        """Get count of learned emotions per type (for admin dashboard)"""
        learned = EmotionDetectionService._load_learned_triggers()
        return {
            emotion: len(triggers)
            for emotion, triggers in learned.items()
        }
