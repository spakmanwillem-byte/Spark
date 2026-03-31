"""
Emotion Service - Manage Spark's Emotional States
Beheert emoties en hun invloed op XP-groei (structuur, later te activeren)
"""
from typing import Dict, List, Optional
from utils.data_manager import DataManager
from datetime import datetime


class EmotionService:
    """Service voor het beheren van Spark's emoties"""
    
    @staticmethod
    def get_current_emotion() -> Dict:
        """Haal de huidige emotie van Spark op"""
        data = DataManager.load_json("emotions/spark_emotions.json")
        return data.get("current_emotion", {
            "state": "neutral",
            "sub_state": None,
            "intensity": 0.5,
            "last_updated": datetime.now().isoformat(),
            "triggered_by": "system"
        })
    
    @staticmethod
    def get_all_emotions() -> Dict:
        """Haal alle beschikbare emoties op"""
        data = DataManager.load_json("emotions/spark_emotions.json")
        return data.get("emotions", {})
    
    @staticmethod
    def get_emotion_details(emotion_state: str) -> Optional[Dict]:
        """
        Haal details op van een specifieke emotie
        
        Args:
            emotion_state: "happy", "sad", "angry", "scared", "neutral"
        """
        emotions = EmotionService.get_all_emotions()
        return emotions.get(emotion_state)
    
    @staticmethod
    def set_emotion(state: str, sub_state: Optional[str] = None, 
                   intensity: float = 0.5, triggered_by: str = "manual",
                   duration_minutes: Optional[int] = None) -> Dict:
        """
        Stel een nieuwe emotie in voor Spark
        
        Args:
            state: Hoofd emotie ("happy", "sad", "angry", "scared", "neutral")
            sub_state: Sub-emotie (bijv. "blijdschap", "vreugde", "euforie")
            intensity: Intensiteit (0.0 - 1.0)
            triggered_by: Wat triggerde deze emotie
            duration_minutes: Hoeveel minuten de emotie duurt (None = permanent)
        
        Returns:
            De nieuwe emotie state
        """
        data = DataManager.load_json("emotions/spark_emotions.json")
        
        # Valideer state
        if state not in data["emotions"]:
            raise ValueError(f"Invalid emotion state: {state}")
        
        # Valideer sub_state als opgegeven
        if sub_state:
            emotion_data = data["emotions"][state]
            if "sub_emotions" in emotion_data:
                if sub_state not in emotion_data["sub_emotions"]:
                    raise ValueError(f"Invalid sub_state '{sub_state}' for emotion '{state}'")
        
        # Clamp intensity tussen 0 en 1
        intensity = max(0.0, min(1.0, intensity))
        
        # Bereken expiry tijd
        expires_at = None
        if duration_minutes:
            from datetime import timedelta
            expires_at = (datetime.now() + timedelta(minutes=duration_minutes)).isoformat()
        
        new_emotion = {
            "state": state,
            "sub_state": sub_state,
            "intensity": intensity,
            "last_updated": datetime.now().isoformat(),
            "triggered_by": triggered_by,
            "expires_at": expires_at,
            "duration_minutes": duration_minutes
        }
        
        data["current_emotion"] = new_emotion
        DataManager.save_json("emotions/spark_emotions.json", data)
        
        return new_emotion
    
    @staticmethod
    def check_and_expire_emotion() -> bool:
        """
        Check of de huidige emotie is verlopen en reset naar neutral
        
        Returns:
            True als emotie is gereset, False als nog geldig
        """
        current = EmotionService.get_current_emotion()
        expires_at = current.get("expires_at")
        
        if not expires_at:
            return False  # Permanent emotion
        
        # Check expiry
        expiry_time = datetime.fromisoformat(expires_at)
        if datetime.now() >= expiry_time:
            # Expired! Reset naar neutral
            EmotionService.reset_to_neutral()
            return True
        
        return False
    
    @staticmethod
    def get_xp_modifier() -> float:
        """
        Haal de huidige XP modifier op gebaseerd op emotie
        
        Returns:
            XP multiplier (0.5 - 2.0)
        """
        current = EmotionService.get_current_emotion()
        state = current.get("state", "neutral")
        sub_state = current.get("sub_state")
        
        data = DataManager.load_json("emotions/spark_emotions.json")
        emotions = data.get("emotions", {})
        
        # Als er een sub_state is, gebruik die modifier
        if sub_state and state in emotions:
            emotion_data = emotions[state]
            if "sub_emotions" in emotion_data:
                sub_emotion = emotion_data["sub_emotions"].get(sub_state, {})
                return sub_emotion.get("xp_modifier", 1.0)
        
        # Anders gebruik de base emotion modifier (of 1.0 voor neutral)
        if state == "neutral":
            return emotions["neutral"].get("xp_modifier", 1.0)
        
        # Default fallback
        return 1.0
    
    @staticmethod
    def get_xp_growth_config() -> Dict:
        """Haal XP-groei configuratie op"""
        data = DataManager.load_json("emotions/spark_emotions.json")
        return data.get("xp_growth_config", {})
    
    @staticmethod
    def get_emotion_stats() -> Dict:
        """
        Haal statistieken op over emoties
        
        Returns:
            Dict met stats over current emotion, available emotions, etc.
        """
        current = EmotionService.get_current_emotion()
        all_emotions = EmotionService.get_all_emotions()
        xp_config = EmotionService.get_xp_growth_config()
        
        # Tel sub-emoties
        total_sub_emotions = 0
        for emotion_key, emotion_data in all_emotions.items():
            if emotion_key != "neutral" and "sub_emotions" in emotion_data:
                total_sub_emotions += len(emotion_data["sub_emotions"])
        
        return {
            "current_emotion": current,
            "total_emotions": len(all_emotions),
            "total_sub_emotions": total_sub_emotions,
            "xp_modifier": EmotionService.get_xp_modifier(),
            "xp_growth_levels": len(xp_config.get("levels", {}))
        }
    
    @staticmethod
    def reset_to_neutral():
        """Reset Spark naar neutrale emotie"""
        return EmotionService.set_emotion(
            state="neutral",
            sub_state=None,
            intensity=0.5,
            triggered_by="manual_reset"
        )
    
    @staticmethod
    def check_inactivity_reset(user_id: str) -> bool:
        """
        Check of user inactief is geweest en reset emotie naar neutral
        
        Inactivity threshold: 1 week (7 dagen)
        
        Args:
            user_id: ID van de gebruiker
            
        Returns:
            True als emotie is gereset door inactiviteit, False anders
        """
        from datetime import timedelta
        
        # Haal gebruiker op
        users = DataManager.load_users()
        user = next((u for u in users if u.get("id") == user_id), None)
        
        if not user:
            return False
        
        last_activity = user.get("last_activity")
        if not last_activity:
            return False
        
        # Parse timestamp
        try:
            last_activity_time = datetime.fromisoformat(last_activity)
        except (ValueError, TypeError):
            return False
        
        # Check of het langer dan 7 dagen geleden is
        inactivity_threshold = timedelta(days=7)
        time_since_activity = datetime.now() - last_activity_time
        
        if time_since_activity >= inactivity_threshold:
            # Check huidige emotie
            current = EmotionService.get_current_emotion()
            current_state = current.get("state", "neutral")
            
            # Als niet al neutral, reset dan
            if current_state != "neutral":
                EmotionService.set_emotion(
                    state="neutral",
                    sub_state=None,
                    intensity=0.5,
                    triggered_by="inactivity_reset_7days"
                )
                return True
        
        return False
    
    @staticmethod
    def get_word_limit() -> int:
        """
        Haal de woordlimiet op voor de huidige emotie
        
        Returns:
            Max aantal woorden dat Spark mag gebruiken in response
        """
        current = EmotionService.get_current_emotion()
        state = current.get("state", "neutral")
        sub_state = current.get("sub_state")
        
        data = DataManager.load_json("emotions/spark_emotions.json")
        emotions = data.get("emotions", {})
        
        # Als er een sub_state is, gebruik die max_words
        if sub_state and state in emotions:
            emotion_data = emotions[state]
            if "sub_emotions" in emotion_data:
                sub_emotion = emotion_data["sub_emotions"].get(sub_state, {})
                return sub_emotion.get("max_words", 150)
        
        # Anders gebruik de base emotion max_words (neutral default)
        if state == "neutral":
            return emotions["neutral"].get("max_words", 150)
        
        # Default fallback
        return 150
