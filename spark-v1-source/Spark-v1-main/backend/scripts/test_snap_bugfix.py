#!/usr/bin/env python3
"""
Test script voor knowledge snap bug fix
Test of lege snaps worden geweigerd
"""

import sys
import os
sys.path.insert(0, '/app/backend')

from services.knowledge_service import KnowledgeService
from utils.data_manager import DataManager
import json

def test_empty_snap_rejection():
    """Test of lege snaps worden geweigerd"""
    print("="*70)
    print("🧪 TEST: Lege Snap Rejection")
    print("="*70)
    
    # Tel huidige entries
    data = DataManager.load_json("learned_knowledge/knowledge_base.json")
    start_count = len(data.get("knowledge_entries", []))
    print(f"\n📊 Start count: {start_count} entries")
    
    tests = [
        {
            "name": "Leeg concept (empty string)",
            "concept": "",
            "context": "test context",
            "should_reject": True
        },
        {
            "name": "Alleen spaties",
            "concept": "   ",
            "context": "test context",
            "should_reject": True
        },
        {
            "name": "Zinsnap: leeg",
            "concept": "",
            "context": "test",
            "is_sentence": True,
            "should_reject": True
        },
        {
            "name": "Zinsnap: te kort (1 char)",
            "concept": "a",
            "context": "test",
            "is_sentence": True,
            "should_reject": True
        },
        {
            "name": "Valid concept",
            "concept": "TestConcept123",
            "context": "Dit is een test",
            "should_reject": False
        },
        {
            "name": "Valid zinsnap",
            "concept": "Dit is een test zin voor snap",
            "context": "Testing",
            "is_sentence": True,
            "should_reject": False
        }
    ]
    
    print("\n🧪 Running tests...")
    passed = 0
    failed = 0
    
    for i, test in enumerate(tests, 1):
        print(f"\n  Test {i}: {test['name']}")
        
        result = KnowledgeService.create_knowledge_snap(
            concept=test['concept'],
            context=test['context'],
            user_naam="TestUser",
            user_id="test-001",
            is_sentence_snap=test.get('is_sentence', False)
        )
        
        if test['should_reject']:
            if result is None:
                print(f"    ✅ PASS: Snap werd correct geweigerd")
                passed += 1
            else:
                print(f"    ❌ FAIL: Snap werd NIET geweigerd (maar had dat wel moeten zijn)")
                failed += 1
        else:
            if result is not None:
                print(f"    ✅ PASS: Snap werd correct aangemaakt")
                # Verwijder de test entry weer
                data = DataManager.load_json("learned_knowledge/knowledge_base.json")
                data["knowledge_entries"] = [e for e in data["knowledge_entries"] if e.get("id") != result.get("id")]
                DataManager.save_json("learned_knowledge/knowledge_base.json", data)
                passed += 1
            else:
                print(f"    ❌ FAIL: Snap werd NIET aangemaakt (maar had dat wel moeten zijn)")
                failed += 1
    
    # Verificatie: entry count moet hetzelfde zijn
    data = DataManager.load_json("learned_knowledge/knowledge_base.json")
    end_count = len(data.get("knowledge_entries", []))
    
    print("\n" + "="*70)
    print("📊 RESULTATEN")
    print("="*70)
    print(f"Start entries: {start_count}")
    print(f"End entries:   {end_count}")
    print(f"Tests passed:  {passed}/{len(tests)}")
    print(f"Tests failed:  {failed}/{len(tests)}")
    
    if failed == 0 and start_count == end_count:
        print("\n✅ ALLE TESTS GESLAAGD! Bug fix werkt correct.")
        return 0
    else:
        print("\n❌ SOMMIGE TESTS GEFAALD")
        return 1

if __name__ == "__main__":
    sys.exit(test_empty_snap_rejection())
