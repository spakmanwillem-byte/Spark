"""
Verbanden Service - Light Version
==================================
Simpele overlap detectie voor 5W+H context

FOCUS:
- Simpel (exact match + substring)
- Debugbaar (uitgebreide logging)
- Max 10 voorstellen per card
"""

import json
import logging
from typing import List, Dict, Optional
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

KB_PATH = Path("/app/backend/data/learned_knowledge/knowledge_base.json")


class VerbanenService:
    """Light versie van verbanden detectie"""
    
    def __init__(self):
        self.kb_data = self._load_kb()
    
    def _load_kb(self) -> dict:
        """Load knowledge base"""
        with open(KB_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _save_kb(self):
        """Save knowledge base"""
        with open(KB_PATH, 'w', encoding='utf-8') as f:
            json.dump(self.kb_data, f, indent=2, ensure_ascii=False)
        logger.info("💾 Knowledge base saved")
    
    def get_card(self, card_id: str) -> Optional[dict]:
        """Get single card by ID"""
        for card in self.kb_data.get('knowledge_entries', []):
            if card.get('id') == card_id:
                return card
        return None
    
    def _check_overlap(self, value1: str, value2: str) -> bool:
        """
        Versoepelde overlap check - WOORDNIVEAU
        
        Normalisatie:
        - Lowercase
        - Split op spaties en komma's
        - Minimaal 3 chars per woord
        
        Match als minimaal 1 woord overlapt
        """
        if not value1 or not value2:
            return False
        
        # Normaliseer: lowercase, replace komma's, split op spaties
        def normalize_to_words(text):
            words = set()
            # Replace komma's en split
            for word in text.lower().replace(',', ' ').split():
                word = word.strip()
                # Minimaal 3 chars (skip "de", "en", "is", etc.)
                if len(word) >= 3:
                    words.add(word)
            return words
        
        words1 = normalize_to_words(value1)
        words2 = normalize_to_words(value2)
        
        # Check overlap (set intersection)
        overlap_words = words1 & words2
        
        # Minimaal 1 woord overlap = match
        if len(overlap_words) > 0:
            logger.debug(f"      Word overlap: {overlap_words}")
            return True
        
        return False
    
    def suggest_verbanden(self, card_id: str, max_suggestions: int = 10) -> List[Dict]:
        """
        Light verbanden detector
        
        Returns:
            List van voorgestelde verbanden met logging
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"🔍 SUGGEST VERBANDEN voor card: {card_id}")
        logger.info(f"{'='*60}")
        
        source_card = self.get_card(card_id)
        if not source_card:
            logger.error(f"❌ Card niet gevonden: {card_id}")
            return []
        
        source_context = source_card.get('context_5wh', {})
        source_begrip = source_card.get('begrip', 'Unknown')
        
        logger.info(f"📋 Source card: {source_begrip}")
        logger.info(f"   Context: {source_context}")
        
        suggestions = []
        checked_count = 0
        
        # Loop door alle cards
        for target_card in self.kb_data.get('knowledge_entries', []):
            target_id = target_card.get('id')
            
            # Skip zelfde card
            if target_id == card_id:
                continue
            
            # Skip al bevestigde verbanden
            bevestigd = source_card.get('bevestigde_verbanden', [])
            if target_id in bevestigd:
                continue
            
            checked_count += 1
            
            target_context = target_card.get('context_5wh', {})
            target_begrip = target_card.get('begrip', 'Unknown')
            
            # Check overlap per veld
            overlap_fields = []
            overlap_details = []
            
            for field in ['wie', 'wat', 'waar', 'wanneer', 'waarom', 'hoe']:
                source_val = source_context.get(field, '')
                target_val = target_context.get(field, '')
                
                if self._check_overlap(source_val, target_val):
                    overlap_fields.append(field)
                    overlap_details.append(f"{field}: '{source_val}' ↔ '{target_val}'")
            
            # Minimaal 1 veld overlap = voorstel (versoepeld voor testing)
            if len(overlap_fields) >= 1:
                suggestion = {
                    'card_id': target_id,
                    'card_begrip': target_begrip,
                    'overlap': overlap_fields,
                    'overlap_count': len(overlap_fields),
                    'status': 'pending'
                }
                suggestions.append(suggestion)
                
                # Log details
                logger.info(f"\n✅ MATCH GEVONDEN:")
                logger.info(f"   Target: {target_begrip}")
                logger.info(f"   Overlap ({len(overlap_fields)} velden): {', '.join(overlap_fields)}")
                for detail in overlap_details:
                    logger.info(f"      - {detail}")
                
                # Stop bij max suggestions
                if len(suggestions) >= max_suggestions:
                    logger.info(f"\n⚠️  Max {max_suggestions} suggestions bereikt, stop zoeken")
                    break
        
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 RESULTAAT:")
        logger.info(f"   - Checked: {checked_count} cards")
        logger.info(f"   - Found: {len(suggestions)} voorstellen")
        logger.info(f"{'='*60}\n")
        
        # Save suggestions to source card
        source_card['voorgestelde_verbanden'] = suggestions
        self._save_kb()
        
        return suggestions
    
    def bevestig_verband(self, card_id: str, target_id: str) -> bool:
        """
        Bevestig een voorgesteld verband (handmatig door Willem)
        
        Returns:
            True als succesvol
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"✅ BEVESTIG VERBAND")
        logger.info(f"{'='*60}")
        
        source_card = self.get_card(card_id)
        target_card = self.get_card(target_id)
        
        if not source_card or not target_card:
            logger.error(f"❌ Card(s) niet gevonden")
            return False
        
        source_begrip = source_card.get('begrip', 'Unknown')
        target_begrip = target_card.get('begrip', 'Unknown')
        
        logger.info(f"   Source: {source_begrip}")
        logger.info(f"   Target: {target_begrip}")
        
        # Voeg toe aan bevestigde verbanden
        if 'bevestigde_verbanden' not in source_card:
            source_card['bevestigde_verbanden'] = []
        
        if target_id not in source_card['bevestigde_verbanden']:
            source_card['bevestigde_verbanden'].append(target_id)
            logger.info(f"   ✅ Verband toegevoegd")
        else:
            logger.info(f"   ⚠️  Verband bestond al")
        
        # Verwijder uit voorstellen
        voorstellen = source_card.get('voorgestelde_verbanden', [])
        source_card['voorgestelde_verbanden'] = [
            v for v in voorstellen if v.get('card_id') != target_id
        ]
        logger.info(f"   🗑️  Verwijderd uit voorstellen")
        
        self._save_kb()
        
        logger.info(f"{'='*60}\n")
        return True
    
    def verwijder_verband(self, card_id: str, target_id: str) -> bool:
        """Verwijder een bevestigd verband"""
        logger.info(f"🗑️  Verwijder verband: {card_id} ↔ {target_id}")
        
        source_card = self.get_card(card_id)
        if not source_card:
            return False
        
        verbanden = source_card.get('bevestigde_verbanden', [])
        if target_id in verbanden:
            verbanden.remove(target_id)
            source_card['bevestigde_verbanden'] = verbanden
            self._save_kb()
            logger.info(f"   ✅ Verband verwijderd")
            return True
        
        return False
    
    def get_statistics(self) -> dict:
        """Get verbanden statistieken"""
        entries = self.kb_data.get('knowledge_entries', [])
        
        total_cards = len(entries)
        cards_with_suggestions = sum(1 for e in entries if len(e.get('voorgestelde_verbanden', [])) > 0)
        cards_with_verbanden = sum(1 for e in entries if len(e.get('bevestigde_verbanden', [])) > 0)
        
        total_suggestions = sum(len(e.get('voorgestelde_verbanden', [])) for e in entries)
        total_verbanden = sum(len(e.get('bevestigde_verbanden', [])) for e in entries)
        
        return {
            'total_cards': total_cards,
            'cards_with_suggestions': cards_with_suggestions,
            'cards_with_verbanden': cards_with_verbanden,
            'total_suggestions': total_suggestions,
            'total_verbanden': total_verbanden
        }


# Quick test function
if __name__ == "__main__":
    print("🧪 Testing VerbanenService...\n")
    
    service = VerbanenService()
    
    # Get eerste card
    entries = service.kb_data.get('knowledge_entries', [])
    if entries:
        test_card = entries[0]
        card_id = test_card['id']
        
        print(f"Testing with card: {test_card.get('begrip')}")
        print(f"Context: {test_card.get('context_5wh')}\n")
        
        # Test suggest
        suggestions = service.suggest_verbanden(card_id, max_suggestions=5)
        
        print(f"\n📊 Found {len(suggestions)} suggestions")
        
        # Stats
        stats = service.get_statistics()
        print(f"\n📈 Statistics:")
        for key, value in stats.items():
            print(f"   {key}: {value}")
