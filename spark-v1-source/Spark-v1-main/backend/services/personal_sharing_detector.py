"""
Personal Sharing Detector
Detecteert wanneer user persoonlijke info deelt en stelt follow-up vragen
"""
import re
from typing import Optional, Dict, Tuple


class PersonalSharingDetector:
    """
    Detecteert personal sharing patterns en genereert follow-up vragen
    """
    
    @staticmethod
    def detect_hobby_sharing(text: str) -> Optional[Dict]:
        """
        Detect: "Mijn hobby is [X]" / "Ik hou van [X]" / "Ik ben gek op [X]"
        
        Returns:
            {
                "type": "hobby",
                "value": "gamen",
                "follow_up": "Welke games vind jij leuk?",
                "profile_field": "personal_info.interesses.hobbies"
            }
        """
        text_lower = text.lower()
        
        # Pattern 1: "Mijn hobby is X"
        if "mijn hobby is" in text_lower or "mijn hobbies zijn" in text_lower:
            # Extract word(s) after "is/zijn"
            parts = text_lower.split("mijn hobby is" if "mijn hobby is" in text_lower else "mijn hobbies zijn")
            if len(parts) > 1:
                hobby = parts[1].strip().split()[0] if parts[1].strip() else ""
                if hobby:
                    return {
                        "type": "hobby",
                        "value": hobby,
                        "follow_up": PersonalSharingDetector._generate_hobby_followup(hobby),
                        "profile_field": "personal_info.interesses.hobbies"
                    }
        
        # Pattern 2: "Ik hou van X"
        match = re.search(r"ik hou van ([\wëïéèàáüöôâ\s]+?)(?:\.|,|$)", text_lower)
        if match:
            hobby = match.group(1).strip()
            # Filter out common false positives
            if hobby not in ["je", "hem", "haar", "dit", "dat"]:
                return {
                    "type": "hobby",
                    "value": hobby,
                    "follow_up": PersonalSharingDetector._generate_hobby_followup(hobby),
                    "profile_field": "personal_info.interesses.hobbies"
                }
        
        # Pattern 3: "Ik ben gek op X"
        match = re.search(r"ik ben gek op ([\wëïéèàáüöôâ\s]+?)(?:\.|,|$)", text_lower)
        if match:
            hobby = match.group(1).strip()
            return {
                "type": "hobby",
                "value": hobby,
                "follow_up": PersonalSharingDetector._generate_hobby_followup(hobby),
                "profile_field": "personal_info.interesses.hobbies"
            }
        
        return None
    
    @staticmethod
    def _generate_hobby_followup(hobby: str) -> str:
        """
        Generate contextual follow-up question based on hobby type
        """
        hobby_lower = hobby.lower()
        
        # Specific follow-ups per hobby type
        if "gam" in hobby_lower:
            return "Welke games vind jij leuk? 🎮"
        elif "sport" in hobby_lower or "fit" in hobby_lower:
            return "Welke sporten doe je graag?"
        elif "lezen" in hobby_lower or "boek" in hobby_lower:
            return "Wat voor boeken lees je graag?"
        elif "muziek" in hobby_lower:
            return "Welke muziek luister je graag?"
        elif "kook" in hobby_lower or "bak" in hobby_lower:
            return "Wat maak je graag?"
        elif "rij" in hobby_lower or "auto" in hobby_lower or "motor" in hobby_lower:
            return "Wat voor rijden vind je leuk?"
        else:
            # Generic follow-up
            return f"Leuk! Vertel me meer over {hobby}?"
    
    @staticmethod
    def detect_food_preference(text: str) -> Optional[Dict]:
        """
        Detect: "Ik hou van [eten/drinken]"
        
        Returns: Similar dict structure
        """
        text_lower = text.lower()
        
        # Food indicators
        food_keywords = ["eet", "eten", "kook", "maak", "recept", "gerecht"]
        drink_keywords = ["drink", "drinken", "koffie", "thee", "bier", "wijn"]
        
        # Pattern: "Ik eet graag X" / "Ik drink graag X"
        if any(kw in text_lower for kw in food_keywords):
            match = re.search(r"(?:eet|hou van|lust) graag ([a-zëïéèàáüöôâ\s]+)", text_lower)
            if match:
                food = match.group(1).strip()
                return {
                    "type": "food_preference",
                    "value": food,
                    "follow_up": "Lekker! Maak je dat zelf of eet je het ergens?",
                    "profile_field": "personal_info.interesses.favoriete_eten"
                }
        
        if any(kw in text_lower for kw in drink_keywords):
            match = re.search(r"(?:drink|hou van) graag ([a-zëïéèàáüöôâ\s]+)", text_lower)
            if match:
                drink = match.group(1).strip()
                return {
                    "type": "drink_preference",
                    "value": drink,
                    "follow_up": f"Ah, {drink}! Hoe drink je dat het liefst?",
                    "profile_field": "personal_info.interesses.favoriete_drinken"
                }
        
        return None
    
    @staticmethod
    def detect_life_event(text: str) -> Optional[Dict]:
        """
        Detect: "Mijn [persoon] is overleden" / "Ik heb [event]"
        
        Returns: Similar dict structure
        """
        text_lower = text.lower()
        
        # Loss patterns
        loss_keywords = ["overleden", "gestorven", "verloren", "doodgegaan"]
        family_members = ["vader", "moeder", "broer", "zus", "oma", "opa", "partner", "vriend", "vriendin"]
        
        if any(kw in text_lower for kw in loss_keywords):
            # Find family member
            for member in family_members:
                if member in text_lower:
                    return {
                        "type": "life_event_loss",
                        "value": f"{member} overleden",
                        "follow_up": "Dat spijt me om te horen. 💙 Wanneer is dit gebeurd?",
                        "profile_field": "personal_info.life_events",
                        "sensitive": True  # Mark as sensitive
                    }
        
        return None
    
    @staticmethod
    def detect_any_sharing(text: str) -> Optional[Dict]:
        """
        Main detection function - checks all patterns
        
        Returns:
            First matched pattern or None
        """
        # Priority order (most specific first)
        detectors = [
            PersonalSharingDetector.detect_life_event,
            PersonalSharingDetector.detect_hobby_sharing,
            PersonalSharingDetector.detect_food_preference,
        ]
        
        for detector in detectors:
            result = detector(text)
            if result:
                print(f"[PERSONAL_SHARING] Detected {result['type']}: {result['value']}")
                return result
        
        return None
