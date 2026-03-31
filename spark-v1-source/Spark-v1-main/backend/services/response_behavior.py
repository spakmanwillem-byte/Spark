"""
Response Behavior System - Gedragsregels per type zin
Detecteert type input en bepaalt passend gedrag voor Spark
"""
from typing import Dict, Optional, Tuple
from enum import Enum
import re


class MessageType(Enum):
    """Type van de user message"""
    EMOTION = "emotion"      # "ik ben blij", "ik voel me verdrietig"
    ACTION = "action"        # "ik ga slapen", "ik werk nu"
    QUESTION = "question"    # "wat is X", "hoe werkt Y"
    STATUS = "status"        # "er is een bestelling", "de taak is klaar"
    UNKNOWN = "unknown"


class ResponseBehavior:
    """Bepaalt gedrag per type zin"""
    
    # Emotie woorden
    EMOTION_PATTERNS = [
        r'\b(ben|voel|voelt)\s+(blij|verdrietig|boos|bang|moe|enthousiast|gespannen|rustig|gefrustreerd|teleurgesteld)',
        r'\bik\s+(voel|ben)\s+me\s+',
        r'\b(blij|verdrietig|boos|bang|moe|down|happy|sad)',
    ]
    
    # Actie woorden (werkwoorden in eerste persoon)
    ACTION_PATTERNS = [
        r'^ik\s+(ga|loop|werk|maak|doe|eet|drink|slaap|kom|blijf|help|probeer|begin|stop)',
        r'\bik\s+(moet|wil|kan|zou)\s+\w+',  # Flexibeler: "ik moet [any word]"
        r'\bik\s+(moet|wil|kan|zou)\s+\w+\s+\w+',  # "ik moet een [word]"
        # Fase 1 module specifieke acties
        r'\b(registreren|vastleggen|noteren|opschrijven|bijhouden)\b',
        r'\b(uitgave|uitgegeven|betaald|gekost|kwijt)\b',
        r'\b(inkomsten|verdiend|ontvangen|binnen|gekregen)\b',
        r'\b(dagboek|schrijven|entry|reflectie)\b',
    ]
    
    # Vraag patronen
    QUESTION_PATTERNS = [
        r'^(wat|wie|waar|wanneer|waarom|hoe|welke|welk)\s+',
        r'\?$',  # Eindigt met vraagteken
    ]
    
    # Status patronen (externe updates)
    STATUS_PATTERNS = [
        r'^(er\s+is|er\s+zijn)\s+',
        r'\b(is\s+klaar|is\s+af|is\s+gedaan|is\s+voltooid)',
        r'\b(nieuwe|update|melding|notificatie)',
    ]
    
    @staticmethod
    def detect_message_type(message: str) -> Tuple[MessageType, float]:
        """
        Detecteer het type message
        
        Returns:
            (MessageType, confidence_score)
        """
        message_lower = message.lower().strip()
        
        # Check vraag EERST (hoogste prioriteit)
        for pattern in ResponseBehavior.QUESTION_PATTERNS:
            if re.search(pattern, message_lower):
                return (MessageType.QUESTION, 0.95)
        
        # Check actie TWEEDE (voor emotie!)
        for pattern in ResponseBehavior.ACTION_PATTERNS:
            if re.search(pattern, message_lower):
                return (MessageType.ACTION, 0.85)
        
        # Check emotie
        for pattern in ResponseBehavior.EMOTION_PATTERNS:
            if re.search(pattern, message_lower):
                return (MessageType.EMOTION, 0.9)
        
        # Check status
        for pattern in ResponseBehavior.STATUS_PATTERNS:
            if re.search(pattern, message_lower):
                return (MessageType.STATUS, 0.8)
        
        return (MessageType.UNKNOWN, 0.5)
    
    @staticmethod
    def get_behavior_rules(message_type: MessageType) -> Dict:
        """
        Haal gedragsregels op voor een type
        
        Returns:
            {
                "approach": "empathisch/informatief/bevestigend",
                "max_words": int,
                "should_ask_followup": bool,
                "tone": "warm/neutral/direct"
            }
        """
        rules = {
            MessageType.EMOTION: {
                "approach": "empathisch",
                "max_words": 15,  # Kort houden
                "should_ask_followup": True,  # "Wil je erover praten?"
                "tone": "warm",
                "templates": [
                    "Begrijpelijk.",
                    "Dat snap ik.",
                    "Herkenbaar.",
                ]
            },
            MessageType.ACTION: {
                "approach": "bevestigend",
                "max_words": 10,  # Heel kort
                "should_ask_followup": False,
                "tone": "neutral",
                "templates": [
                    "Begrepen.",
                    "Duidelijk.",
                    "Genoteerd.",
                ]
            },
            MessageType.QUESTION: {
                "approach": "informatief",
                "max_words": 50,  # Meer ruimte voor uitleg
                "should_ask_followup": False,
                "tone": "direct",
                "templates": []  # Gebruik kenniskaart content
            },
            MessageType.STATUS: {
                "approach": "bevestigend",
                "max_words": 20,
                "should_ask_followup": True,  # "Zal ik dit verwerken?"
                "tone": "direct",
                "templates": [
                    "Ontvangen.",
                    "Genoteerd.",
                    "Begrepen.",
                ]
            },
            MessageType.UNKNOWN: {
                "approach": "open",
                "max_words": 20,
                "should_ask_followup": True,
                "tone": "neutral",
                "templates": [
                    "Vertel me meer.",
                    "Ik luister.",
                ]
            }
        }
        
        return rules.get(message_type, rules[MessageType.UNKNOWN])
    
    @staticmethod
    def format_response(
        message_type: MessageType,
        content: str,
        card_context: Optional[Dict] = None
    ) -> str:
        """
        Formatteer response volgens gedragsregels
        
        Args:
            message_type: Type van de input
            content: De content (laag1 of generator output)
            card_context: Optionele card info voor extra context
        
        Returns:
            Geformatteerde response (kort en menselijk)
        """
        import random
        
        rules = ResponseBehavior.get_behavior_rules(message_type)
        
        # Voor EMOTIE: kort empathisch
        if message_type == MessageType.EMOTION:
            if content and len(content) > 50:
                # Te lang, gebruik template
                return random.choice(rules["templates"])
            return content or random.choice(rules["templates"])
        
        # Voor ACTIE: zeer kort, soms met context
        elif message_type == MessageType.ACTION:
            # 80% kort, 20% met content
            if random.random() < 0.8:
                return random.choice(rules["templates"])
            else:
                # Kort met context
                if content and len(content) < 30:
                    return content
                return random.choice(rules["templates"])
        
        # Voor VRAAG: gebruik volledige content (informatief)
        elif message_type == MessageType.QUESTION:
            return content or "Ik weet hier nog geen antwoord op."
        
        # Voor STATUS: bevestig + optioneel actie
        elif message_type == MessageType.STATUS:
            template = random.choice(rules["templates"])
            # Voeg actie toe als card context beschikbaar is
            if card_context and random.random() < 0.5:
                return f"{template} {content[:30]}" if content else template
            return template
        
        # UNKNOWN: open response
        else:
            return content or random.choice(rules["templates"])
