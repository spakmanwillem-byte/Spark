from typing import Dict, List, Optional
from utils.data_manager import DataManager
import re

class ClassificationService:
    def __init__(self):
        self.classes = DataManager.load_json("classifications/classes.json").get("classes", {})
        self.labels = DataManager.load_json("classifications/labels.json").get("labels", {})
    
    def classify_topic(self, text: str, entities: Dict) -> Dict:
        """
        Classify the main topic of text
        Returns: {
            "klasse": str,
            "sub_klasse": str,
            "confidence": float,
            "labels": {}
        }
        """
        text_lower = text.lower()
        
        scores = {}
        for klasse, info in self.classes.items():
            score = 0
            
            # Check keywords related to class
            if klasse == "Personen":
                if entities.get("personen"):
                    score += 10
                if any(w in text_lower for w in ["iemand", "persoon", "mensen", "vriend", "familie"]):
                    score += 5
            
            elif klasse == "Activiteiten":
                activity_words = ["deed", "ging", "ben geweest", "gedaan", "bezig", "spelen", "werken"]
                if any(w in text_lower for w in activity_words):
                    score += 8
            
            elif klasse == "Locaties":
                if entities.get("locaties"):
                    score += 10
                if any(w in text_lower for w in ["naar", "in", "bij", "plaats"]):
                    score += 3
            
            elif klasse == "Events":
                event_words = ["verjaardag", "feest", "evenement", "bijzonder", "speciaal"]
                if any(w in text_lower for w in event_words):
                    score += 10
            
            elif klasse == "Concepten":
                concept_words = ["denk", "vind", "mening", "idee", "gevoel", "voel"]
                if any(w in text_lower for w in concept_words):
                    score += 8
            
            elif klasse == "Objecten":
                object_words = ["eten", "drinken", "product", "ding", "spullen"]
                if any(w in text_lower for w in object_words):
                    score += 7
            
            elif klasse == "Werk":
                work_words = ["werk", "project", "klant", "meeting", "taak", "bedrijf"]
                if any(w in text_lower for w in work_words):
                    score += 9
            
            elif klasse == "Kennis":
                knowledge_words = ["leren", "weten", "begrijpen", "uitleg", "betekent"]
                if any(w in text_lower for w in knowledge_words):
                    score += 8
            
            scores[klasse] = score
        
        # Get best match
        if not scores or max(scores.values()) == 0:
            return {
                "klasse": "Algemeen",
                "sub_klasse": "Onbekend",
                "confidence": 0.0,
                "labels": {}
            }
        
        best_klasse = max(scores, key=scores.get)
        confidence = min(scores[best_klasse] / 10.0, 1.0)
        
        # Determine sub-class (simple matching)
        sub_klasse = self._determine_sub_class(best_klasse, text_lower, entities)
        
        # Apply labels
        applied_labels = self._apply_labels(text_lower, entities)
        
        return {
            "klasse": best_klasse,
            "sub_klasse": sub_klasse,
            "confidence": confidence,
            "labels": applied_labels
        }
    
    def _determine_sub_class(self, klasse: str, text_lower: str, entities: Dict) -> str:
        """Determine sub-class within a class"""
        sub_classes = self.classes.get(klasse, {}).get("sub_classes", [])
        
        if not sub_classes:
            return "Algemeen"
        
        # Simple keyword matching
        for sub_class in sub_classes:
            if sub_class.lower() in text_lower:
                return sub_class
        
        # Default to first sub-class
        return sub_classes[0] if sub_classes else "Algemeen"
    
    def _apply_labels(self, text_lower: str, entities: Dict) -> Dict:
        """Apply labels based on text analysis"""
        labels = {}
        
        # Context
        if any(w in text_lower for w in ["werk", "project", "klant"]):
            labels["context"] = "werk"
        elif any(w in text_lower for w in ["familie", "dochter", "zoon", "ouders"]):
            labels["context"] = "familie"
        elif any(w in text_lower for w in ["vriend", "vrienden"]):
            labels["context"] = "vrienden"
        else:
            labels["context"] = "prive"
        
        # Frequentie
        if any(w in text_lower for w in ["altijd", "elke dag", "dagelijks"]):
            labels["frequentie"] = "dagelijks"
        elif any(w in text_lower for w in ["vaak", "regelmatig", "wekelijks"]):
            labels["frequentie"] = "wekelijks"
        elif any(w in text_lower for w in ["soms", "af en toe"]):
            labels["frequentie"] = "maandelijks"
        else:
            labels["frequentie"] = "eenmalig"
        
        # Urgentie
        if any(w in text_lower for w in ["urgent", "snel", "nu", "direct", "meteen"]):
            labels["urgentie"] = "direct"
        elif any(w in text_lower for w in ["spoedig", "binnenkort"]):
            labels["urgentie"] = "spoedig"
        else:
            labels["urgentie"] = "binnenkort"
        
        return labels
