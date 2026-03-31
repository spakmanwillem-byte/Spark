#!/usr/bin/env python3
"""
Snap Creation Test Tool
Voor Willem om verschillende snap scenario's te testen
"""

import sys
sys.path.insert(0, '/app/backend')

from services.knowledge_service import KnowledgeService
from datetime import datetime

def test_snap_scenarios():
    """Test verschillende snap scenario's"""
    
    print("="*80)
    print("🧪 SNAP CREATION TEST TOOL")
    print("="*80)
    print("Test verschillende scenario's en zie direct de logging\n")
    
    test_cases = [
        {
            "name": "1. Lege string (moet geweigerd worden)",
            "concept": "",
            "context": "test context",
            "expected": "REJECTED"
        },
        {
            "name": "2. Alleen spaties (moet geweigerd worden)",
            "concept": "    ",
            "context": "test context",
            "expected": "REJECTED"
        },
        {
            "name": "3. Stopword 'de' (moet geweigerd worden)",
            "concept": "de",
            "context": "test context",
            "expected": "REJECTED"
        },
        {
            "name": "4. Bestaand begrip 'bewustzijn' (moet geweigerd worden - duplicate)",
            "concept": "bewustzijn",
            "context": "test context",
            "expected": "REJECTED"
        },
        {
            "name": "5. Nieuw geldig concept (moet aangemaakt worden)",
            "concept": f"TestConcept{datetime.now().strftime('%H%M%S')}",
            "context": "Dit is een test voor een nieuw concept",
            "expected": "CREATED"
        },
        {
            "name": "6. Geldige zinsnap (moet aangemaakt worden)",
            "concept": f"Dit is een test zin {datetime.now().strftime('%H%M%S')}",
            "context": "Testing zinsnap",
            "is_sentence": True,
            "expected": "CREATED"
        },
        {
            "name": "7. Lege zinsnap (moet geweigerd worden)",
            "concept": "",
            "context": "test",
            "is_sentence": True,
            "expected": "REJECTED"
        },
        {
            "name": "8. Te korte zinsnap - 1 char (moet geweigerd worden)",
            "concept": "x",
            "context": "test",
            "is_sentence": True,
            "expected": "REJECTED"
        }
    ]
    
    print("Let op: Alle logging verschijnt ook in de backend logs")
    print("Draai 'python3 scripts/monitor_snaps.py' in een andere terminal voor real-time monitoring\n")
    print("-"*80)
    
    passed = 0
    failed = 0
    created_ids = []
    
    for test in test_cases:
        print(f"\n🧪 {test['name']}")
        print(f"   Input: '{test['concept']}'")
        print(f"   Expected: {test['expected']}")
        
        try:
            result = KnowledgeService.create_knowledge_snap(
                concept=test['concept'],
                context=test['context'],
                user_naam="Willem (TEST)",
                user_id="user-001",
                is_sentence_snap=test.get('is_sentence', False)
            )
            
            if test['expected'] == 'REJECTED':
                if result is None:
                    print(f"   ✅ PASS: Correct geweigerd")
                    passed += 1
                else:
                    print(f"   ❌ FAIL: Werd aangemaakt maar had geweigerd moeten worden")
                    print(f"      Created ID: {result.get('id')}")
                    created_ids.append(result.get('id'))
                    failed += 1
            else:  # CREATED
                if result is not None:
                    print(f"   ✅ PASS: Correct aangemaakt")
                    print(f"      ID: {result.get('id')}")
                    print(f"      Begrip: {result.get('begrip')}")
                    print(f"      Status: {result.get('status')}")
                    created_ids.append(result.get('id'))
                    passed += 1
                else:
                    print(f"   ❌ FAIL: Werd geweigerd maar had aangemaakt moeten worden")
                    failed += 1
        
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
            failed += 1
    
    # Samenvatting
    print("\n" + "="*80)
    print("📊 TEST RESULTATEN")
    print("="*80)
    print(f"Geslaagd: {passed}/{len(test_cases)}")
    print(f"Gefaald:  {failed}/{len(test_cases)}")
    
    if created_ids:
        print(f"\n📝 Aangemaakte test entries (IDs): {len([id for id in created_ids if 'Test' in str(id)])}")
        print("   Deze kun je later verwijderen als je wilt")
    
    # Cleanup optie
    if created_ids:
        print("\n⚠️  Test entries zijn aangemaakt in de knowledge base")
        cleanup = input("Wil je de test entries verwijderen? (j/n): ").lower()
        
        if cleanup == 'j':
            from utils.data_manager import DataManager
            data = DataManager.load_json("learned_knowledge/knowledge_base.json")
            original_count = len(data.get("knowledge_entries", []))
            
            # Verwijder test entries
            data["knowledge_entries"] = [
                e for e in data["knowledge_entries"] 
                if e.get("id") not in created_ids
            ]
            
            DataManager.save_json("learned_knowledge/knowledge_base.json", data)
            new_count = len(data.get("knowledge_entries", []))
            print(f"✅ {original_count - new_count} test entries verwijderd")
    
    print("\n✅ Testing compleet!")
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(test_snap_scenarios())
