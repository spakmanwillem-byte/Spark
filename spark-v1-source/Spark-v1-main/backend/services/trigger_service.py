"""
Trigger Service (Simple)
=========================
Check voor directe triggers (greetings, farewells)
VOOR NLP/knowledge search

Simpel:
- Geen orchestrator
- Geen multi-intent
- Gewoon: trigger gevonden? → direct response
"""

import json
import random
import re
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

KB_PATH = Path("/app/backend/data/learned_knowledge/knowledge_base.json")


class TriggerService:
    """Simpele trigger detector - greetings, farewells, etc."""
    
    def __init__(self):
        self.kb_data = self._load_kb()
        self.trigger_cards = self._load_trigger_cards()
        logger.info(f"✅ Trigger service loaded: {len(self.trigger_cards)} trigger cards")
    
    def _load_kb(self) -> dict:
        """Load knowledge base"""
        with open(KB_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _load_trigger_cards(self) -> list:
        """
        Load alleen cards met type greeting/farewell en een response field
        """
        trigger_types = ['greeting', 'farewell', 'action']
        cards = []
        
        for card in self.kb_data.get('knowledge_entries', []):
            card_type = card.get('type')
            if card_type in trigger_types and 'response' in card:
                cards.append(card)
        
        return cards
    
    def check_trigger(self, user_input: str) -> dict:
        """
        Check of user input een trigger matcht
        
        Returns:
            {
                "triggered": bool,
                "response": str,
                "card_begrip": str,
                "card_type": str,
                "action": str (optional - alleen bij type="action"),
                "response_config": dict (optional - bij action triggers),
                "user_input": str (original input - voor action handler)
            }
        """
        user_lower = user_input.lower().strip()
        
        logger.info(f"🔍 Checking triggers voor: '{user_input}'")
        
        for card in self.trigger_cards:
            response_config = card.get('response', {})
            card_type = card.get('type')
            
            # Check trigger pattern (regex) eerst
            trigger_pattern = response_config.get('trigger_pattern')
            if trigger_pattern:
                if re.match(trigger_pattern, user_lower, re.IGNORECASE):
                    # Bij action type: return action info
                    if card_type == 'action':
                        action = response_config.get('action')
                        logger.info(f"✅ ACTION TRIGGER MATCH (pattern): {card.get('begrip')}")
                        logger.info(f"   Action: {action}")
                        return {
                            "triggered": True,
                            "response": None,  # Will be set by action handler
                            "card_begrip": card.get('begrip'),
                            "card_type": card_type,
                            "action": action,
                            "response_config": response_config,
                            "user_input": user_input
                        }
                    
                    # Bij response type: return text response
                    response = self._get_response(response_config)
                    logger.info(f"✅ TRIGGER MATCH (pattern): {card.get('begrip')}")
                    logger.info(f"   Response: {response}")
                    return {
                        "triggered": True,
                        "response": response,
                        "card_begrip": card.get('begrip'),
                        "card_type": card_type,
                        "action": None,
                        "response_config": None,
                        "user_input": user_input
                    }
            
            # Fallback: check trigger words
            trigger_words = response_config.get('trigger_words', [])
            for word in trigger_words:
                # Simpel: woord in input (case insensitive)
                if word.lower() in user_lower:
                    # Bij action type: return action info
                    if card_type == 'action':
                        action = response_config.get('action')
                        logger.info(f"✅ ACTION TRIGGER MATCH (word): {card.get('begrip')} (word: {word})")
                        logger.info(f"   Action: {action}")
                        return {
                            "triggered": True,
                            "response": None,
                            "card_begrip": card.get('begrip'),
                            "card_type": card_type,
                            "action": action,
                            "response_config": response_config,
                            "user_input": user_input
                        }
                    
                    # Bij response type: return text response
                    response = self._get_response(response_config)
                    logger.info(f"✅ TRIGGER MATCH (word): {card.get('begrip')} (word: {word})")
                    logger.info(f"   Response: {response}")
                    return {
                        "triggered": True,
                        "response": response,
                        "card_begrip": card.get('begrip'),
                        "card_type": card_type,
                        "action": None,
                        "response_config": None,
                        "user_input": user_input
                    }
        
        logger.info("❌ Geen trigger match")
        return {
            "triggered": False,
            "response": None,
            "card_begrip": None,
            "card_type": None,
            "action": None,
            "response_config": None,
            "user_input": user_input
        }
    
    def _get_response(self, response_config: dict) -> str:
        """
        Haal response text uit config
        - Als list: kies random
        - Als string: direct
        """
        response_text = response_config.get('text', '')
        
        if isinstance(response_text, list):
            return random.choice(response_text)
        
        return response_text
    
    def reload(self):
        """Reload trigger cards (voor live updates)"""
        self.kb_data = self._load_kb()
        self.trigger_cards = self._load_trigger_cards()
        logger.info(f"🔄 Triggers reloaded: {len(self.trigger_cards)} cards")


# Singleton instance
_trigger_service = None

def get_trigger_service():
    """Get singleton trigger service"""
    global _trigger_service
    if _trigger_service is None:
        _trigger_service = TriggerService()
    return _trigger_service


# Quick test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    service = TriggerService()
    
    print("=" * 60)
    print("🧪 TEST TRIGGER SERVICE")
    print("=" * 60)
    
    test_inputs = [
        "Hallo Spark",
        "hey spark hoe gaat het",
        "Goedemorgen Spark",
        "wat is bitcoin",  # Geen trigger
        "Hi Spark!",
        "goedenavond spark"
    ]
    
    for test_input in test_inputs:
        print(f"\n📝 Input: '{test_input}'")
        result = service.check_trigger(test_input)
        
        if result['triggered']:
            print(f"   ✅ TRIGGER: {result['card_begrip']}")
            print(f"   Response: {result['response']}")
        else:
            print("   ❌ Geen trigger")
    
    print("\n" + "=" * 60)
    print(f"📊 Total trigger cards loaded: {len(service.trigger_cards)}")
    print("=" * 60)
