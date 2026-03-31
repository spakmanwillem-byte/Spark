"""
Audit Service - Self-Check Tooling
===================================
Spark kan zichzelf auditen: wat ontbreekt, wat is leeg, wat moet verbeterd?

GEEN AI, GEEN NLP - gewoon JSON filteren en rapporteren
"""

import json
from pathlib import Path
from typing import List, Dict

KB_PATH = Path("/app/backend/data/learned_knowledge/knowledge_base.json")


class AuditService:
    """Self-check tooling voor Spark"""
    
    def __init__(self):
        self.kb_data = self._load_kb()
    
    def _load_kb(self) -> dict:
        """Load knowledge base"""
        with open(KB_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    # ============== SCAN 1: LEGE ACTIES (PLACEHOLDERS) ==============
    
    def scan_placeholder_actions(self) -> List[Dict]:
        """
        Vind alle action cards die nog placeholders zijn
        
        PRIORITY: HIGH (features die nog gebouwd moeten worden)
        
        Returns:
            List van {begrip, type, future_module, notes, priority}
        """
        placeholders = []
        
        for card in self.kb_data.get('knowledge_entries', []):
            card_type = card.get('type', '')
            
            # Check of het een action card is
            if card_type == 'action':
                # Check of er een action field is met type=placeholder
                action = card.get('action', {})
                if action.get('type') == 'placeholder':
                    placeholders.append({
                        'begrip': card.get('begrip'),
                        'type': card_type,
                        'future_module': action.get('future_module', 'Unknown'),
                        'notes': action.get('notes', ''),
                        'card_id': card.get('id'),
                        'priority': 'HIGH'  # Placeholder actions = HIGH priority
                    })
        
        return placeholders
    
    # ============== SCAN 2: TRIGGERS ZONDER GOEDE RESPONSE ==============
    
    def scan_weak_triggers(self) -> List[Dict]:
        """
        Vind triggers (greeting/action) met lege of te simpele responses
        
        PRIORITY: MEDIUM (belangrijk voor UX maar niet kritiek)
        
        Criteria:
        - type = greeting/farewell/action
        - response field bestaat NIET OF
        - response.text is leeg OF
        - response.text heeft < 10 characters (te simpel)
        
        Returns:
            List van {begrip, type, issue, suggestion, priority}
        """
        weak_triggers = []
        
        trigger_types = ['greeting', 'farewell', 'action']
        
        for card in self.kb_data.get('knowledge_entries', []):
            card_type = card.get('type', '')
            
            if card_type in trigger_types:
                begrip = card.get('begrip')
                response = card.get('response', {})
                
                issue = None
                suggestion = None
                
                # Check 1: Geen response field
                if not response:
                    issue = "Geen response field"
                    suggestion = "Voeg response toe met trigger_words en text"
                
                # Check 2: Response.text is leeg
                elif not response.get('text'):
                    issue = "Response.text is leeg"
                    suggestion = "Voeg text array toe met responses"
                
                # Check 3: Response.text te kort (< 10 chars)
                else:
                    text = response.get('text', '')
                    if isinstance(text, list):
                        # Check eerste item
                        if text and len(text[0]) < 10:
                            issue = f"Response te kort: '{text[0]}'"
                            suggestion = "Maak response uitgebreider en vriendelijker"
                    elif isinstance(text, str) and len(text) < 10:
                        issue = f"Response te kort: '{text}'"
                        suggestion = "Maak response uitgebreider en vriendelijker"
                
                if issue:
                    weak_triggers.append({
                        'begrip': begrip,
                        'type': card_type,
                        'issue': issue,
                        'suggestion': suggestion,
                        'card_id': card.get('id'),
                        'priority': 'MEDIUM'  # Weak triggers = MEDIUM priority
                    })
        
        return weak_triggers
    
    # ============== SCAN 3: ZWAKKE VERBANDEN (OPTIONEEL) ==============
    
    def scan_weak_verbanden(self, min_overlap: int = 2) -> List[Dict]:
        """
        Vind cards met zwakke verbanden (te weinig overlap)
        
        PRIORITY: LOW (nice to have, helpt bij threshold tuning)
        
        FILTER: Alleen greeting/action/farewell cards (geen knowledge)
        
        Ruis = 1 veld overlap → kan false positive zijn
        Sterk = 2+ velden overlap → waarschijnlijk relevant
        
        Args:
            min_overlap: Minimaal aantal velden (default 2)
        
        Returns:
            List van {source_begrip, weak_verbanden_count, voorbeelden, priority}
        """
        weak_verbanden_cards = []
        
        # Alleen relevante types (geen knowledge)
        relevant_types = ['greeting', 'farewell', 'action']
        
        for card in self.kb_data.get('knowledge_entries', []):
            card_type = card.get('type', '')
            
            # Skip knowledge cards
            if card_type not in relevant_types:
                continue
            
            begrip = card.get('begrip')
            
            # Check voorgestelde verbanden
            voorgestelde = card.get('voorgestelde_verbanden', [])
            
            # Filter op overlap count < min_overlap
            weak = [
                v for v in voorgestelde 
                if v.get('overlap_count', 0) < min_overlap
            ]
            
            if weak:
                # Neem max 3 voorbeelden
                voorbeelden = [
                    {
                        'target': v.get('card_begrip'),
                        'overlap': v.get('overlap'),
                        'overlap_count': v.get('overlap_count')
                    }
                    for v in weak[:3]
                ]
                
                weak_verbanden_cards.append({
                    'source_begrip': begrip,
                    'weak_count': len(weak),
                    'voorbeelden': voorbeelden,
                    'card_id': card.get('id'),
                    'priority': 'LOW'  # Weak verbanden = LOW priority
                })
        
        # Sort by weak_count (meeste eerst)
        weak_verbanden_cards.sort(key=lambda x: -x['weak_count'])
        
        return weak_verbanden_cards
    
    # ============== SCAN 4: CARDS ZONDER 5W+H ==============
    
    def scan_missing_5wh(self) -> List[Dict]:
        """
        Vind cards waar 5W+H nog niet ingevuld is
        (alle velden leeg)
        
        PRIORITY: LOW (nice to have voor toekomstige verbanden)
        
        FILTER: Alleen greeting/action/farewell cards (geen knowledge)
        
        Returns:
            List van {begrip, type, card_id, priority}
        """
        missing_5wh = []
        
        # Alleen relevante types (geen knowledge)
        relevant_types = ['greeting', 'farewell', 'action']
        
        for card in self.kb_data.get('knowledge_entries', []):
            card_type = card.get('type', '')
            
            # Skip knowledge cards
            if card_type not in relevant_types:
                continue
            
            context_5wh = card.get('context_5wh', {})
            
            # Check of alle velden leeg zijn
            all_empty = all(
                not context_5wh.get(field, '').strip()
                for field in ['wie', 'wat', 'waar', 'wanneer', 'waarom', 'hoe']
            )
            
            if all_empty:
                missing_5wh.append({
                    'begrip': card.get('begrip'),
                    'type': card_type,
                    'card_id': card.get('id'),
                    'priority': 'LOW'  # Missing 5W+H = LOW priority
                })
        
        return missing_5wh
    
    # ============== COMPREHENSIVE AUDIT ==============
    
    def run_full_audit(self) -> Dict:
        """
        Run alle scans en geef complete overzicht
        
        Returns:
            {
                'by_priority': {
                    'HIGH': [...],
                    'MEDIUM': [...],
                    'LOW': [...]
                },
                'placeholder_actions': [...],
                'weak_triggers': [...],
                'weak_verbanden': [...],
                'missing_5wh_count': int,
                'summary': {...}
            }
        """
        placeholders = self.scan_placeholder_actions()
        weak_triggers = self.scan_weak_triggers()
        weak_verbanden = self.scan_weak_verbanden(min_overlap=2)
        missing_5wh = self.scan_missing_5wh()
        
        total_cards = len(self.kb_data.get('knowledge_entries', []))
        
        # Group by priority
        by_priority = {
            'HIGH': placeholders,
            'MEDIUM': weak_triggers,
            'LOW': weak_verbanden[:10] + [
                {
                    'category': 'missing_5wh',
                    'count': len(missing_5wh),
                    'priority': 'LOW'
                }
            ]
        }
        
        return {
            'by_priority': by_priority,
            'placeholder_actions': placeholders,
            'weak_triggers': weak_triggers,
            'weak_verbanden': weak_verbanden[:10],  # Top 10 alleen
            'missing_5wh_count': len(missing_5wh),
            'missing_5wh_sample': missing_5wh[:5],  # Sample van 5
            'summary': {
                'total_cards': total_cards,
                'high_priority_count': len(placeholders),
                'medium_priority_count': len(weak_triggers),
                'low_priority_count': len(weak_verbanden) + len(missing_5wh),
                'placeholder_actions_count': len(placeholders),
                'weak_triggers_count': len(weak_triggers),
                'weak_verbanden_count': len(weak_verbanden),
                'missing_5wh_count': len(missing_5wh),
                'completion_percentage': round(
                    ((total_cards - len(missing_5wh)) / total_cards * 100), 1
                ) if total_cards > 0 else 0
            }
        }


# Quick test
if __name__ == "__main__":
    print("=" * 60)
    print("🔍 AUDIT SERVICE TEST")
    print("=" * 60)
    
    service = AuditService()
    
    # Test scan 1
    print("\n📋 PLACEHOLDER ACTIONS:")
    placeholders = service.scan_placeholder_actions()
    print(f"   Found: {len(placeholders)}")
    for p in placeholders[:3]:
        print(f"   - {p['begrip']} (future: {p['future_module']})")
    
    # Test scan 2
    print("\n⚠️  WEAK TRIGGERS:")
    weak = service.scan_weak_triggers()
    print(f"   Found: {len(weak)}")
    for w in weak[:3]:
        print(f"   - {w['begrip']}: {w['issue']}")
    
    # Test scan 3
    print("\n🔗 WEAK VERBANDEN (sample):")
    weak_verb = service.scan_weak_verbanden(min_overlap=2)
    print(f"   Found: {len(weak_verb)} cards met zwakke verbanden")
    if weak_verb:
        sample = weak_verb[0]
        print(f"   Example: {sample['source_begrip']} heeft {sample['weak_count']} zwakke verbanden")
    
    # Test scan 4
    print("\n📝 MISSING 5W+H:")
    missing = service.scan_missing_5wh()
    print(f"   Found: {len(missing)} cards zonder 5W+H")
    
    print("\n" + "=" * 60)
