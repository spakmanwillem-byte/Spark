#!/usr/bin/env python3
"""
Test script voor concept normalisatie in knowledge snaps
Test verschillende input types:
- Vragen ("Wat is X?")
- Concepten ("blockchain", "AUTO")
- Ruis ("en", "de", "het")
"""

import sys
import os
sys.path.insert(0, '/app/backend')

from services.knowledge_service import KnowledgeService
from utils.data_manager import DataManager
import json

# Test cases
TEST_CASES = [
    # Format: (input, verwacht_begrip_of_none, beschrijving)
    ("Wat is een auto?", "Auto", "Vraag met lidwoord"),
    ("Wat is liefde?", "Liefde", "Vraag zonder lidwoord"),
    ("Hoe werkt blockchain?", "Blockchain", "Hoe-vraag"),
    ("Vertel over fotosynthese", "Fotosynthese", "Vertel-statement"),
    ("Wie is tijd", "Tijd", "Wie-vraag (filosofisch)"),
    
    # Concepten direct
    ("blockchain", "Blockchain", "Lowercase concept"),
    ("AUTO", "AUTO", "Uppercase concept (blijft uppercase)"),
    ("Respect", "Respect", "Correct gekapitaliseerd concept"),
    
    # Ruis (moet worden afgewezen)
    ("en", None, "Voegwoord"),
    ("de", None, "Lidwoord"),
    ("het", None, "Lidwoord"),
    ("is", None, "Hulpwerkwoord"),
    ("wat is", None, "Grammaticaal patroon"),
    ("nou ja", None, "Opvulwoord"),
    
    # Edge cases
    ("de appel", "Appel", "Concept met lidwoord"),
    ("een hond", "Hond", "Concept met onbepaald lidwoord"),
    ("ik loop", None, "Zin met voornaamwoord"),
]

def clear_test_snaps():
    """Verwijder alle test snaps uit de database"""
    data = DataManager.load_json("learned_knowledge/knowledge_base.json")
    entries = data.get("knowledge_entries", [])
    
    # Bewaar aantal voor rapportage
    original_count = len(entries)
    
    # Filter test snaps eruit
    test_concepts = [case[1] for case in TEST_CASES if case[1] is not None]
    test_concepts_lower = [c.lower() for c in test_concepts]
    
    entries = [
        e for e in entries 
        if e.get("begrip", "").lower() not in test_concepts_lower
    ]
    
    removed = original_count - len(entries)
    if removed > 0:
        data["knowledge_entries"] = entries
        DataManager.save_json("learned_knowledge/knowledge_base.json", data)
        print(f"🧹 Opgeruimd: {removed} test entries verwijderd\n")
    
    return removed

def run_tests():
    """Voer alle tests uit"""
    print("=" * 70)
    print("🧪 TEST: Concept Normalisatie in Knowledge Snaps")
    print("=" * 70)
    print()
    
    # Cleanup eerst
    clear_test_snaps()
    
    results = {
        "passed": 0,
        "failed": 0,
        "details": []
    }
    
    print("Running tests...\n")
    
    for i, (input_text, expected_begrip, description) in enumerate(TEST_CASES, 1):
        print(f"Test {i}/{len(TEST_CASES)}: {description}")
        print(f"  Input: '{input_text}'")
        print(f"  Verwacht: {expected_begrip if expected_begrip else 'REJECT'}")
        
        # Voer test uit
        result = KnowledgeService.create_knowledge_snap(
            concept=input_text,
            context=f"Test context for: {input_text}",
            user_naam="TestUser"
        )
        
        # Evalueer resultaat
        if expected_begrip is None:
            # We verwachten None (rejection)
            if result is None:
                print(f"  ✅ PASS: Correct afgewezen")
                results["passed"] += 1
                results["details"].append({
                    "test": description,
                    "status": "PASS",
                    "input": input_text,
                    "expected": "REJECT",
                    "actual": "REJECT"
                })
            else:
                actual_begrip = result.get("begrip", "?")
                print(f"  ❌ FAIL: Werd opgeslagen als '{actual_begrip}' (zou afgewezen moeten worden)")
                results["failed"] += 1
                results["details"].append({
                    "test": description,
                    "status": "FAIL",
                    "input": input_text,
                    "expected": "REJECT",
                    "actual": actual_begrip
                })
        else:
            # We verwachten een begrip
            if result is None:
                print(f"  ❌ FAIL: Werd afgewezen (verwachtte '{expected_begrip}')")
                results["failed"] += 1
                results["details"].append({
                    "test": description,
                    "status": "FAIL",
                    "input": input_text,
                    "expected": expected_begrip,
                    "actual": "REJECT"
                })
            else:
                actual_begrip = result.get("begrip", "")
                if actual_begrip == expected_begrip:
                    print(f"  ✅ PASS: '{actual_begrip}'")
                    results["passed"] += 1
                    results["details"].append({
                        "test": description,
                        "status": "PASS",
                        "input": input_text,
                        "expected": expected_begrip,
                        "actual": actual_begrip
                    })
                else:
                    print(f"  ❌ FAIL: '{actual_begrip}' (verwachtte '{expected_begrip}')")
                    results["failed"] += 1
                    results["details"].append({
                        "test": description,
                        "status": "FAIL",
                        "input": input_text,
                        "expected": expected_begrip,
                        "actual": actual_begrip
                    })
        
        print()
    
    # Cleanup na tests
    print("\n🧹 Opruimen test data...")
    removed = clear_test_snaps()
    
    # Samenvatting
    print("\n" + "=" * 70)
    print("📊 TEST RESULTATEN")
    print("=" * 70)
    print(f"✅ Geslaagd: {results['passed']}/{len(TEST_CASES)}")
    print(f"❌ Gefaald:  {results['failed']}/{len(TEST_CASES)}")
    print(f"📈 Slagingspercentage: {(results['passed']/len(TEST_CASES)*100):.1f}%")
    print()
    
    if results["failed"] > 0:
        print("❌ Gefaalde tests:")
        for detail in results["details"]:
            if detail["status"] == "FAIL":
                print(f"  • {detail['test']}")
                print(f"    Input: '{detail['input']}'")
                print(f"    Verwacht: {detail['expected']}, Gekregen: {detail['actual']}")
        print()
    
    # Export resultaten
    with open("/app/test_concept_normalization_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"📄 Volledige resultaten: /app/test_concept_normalization_results.json")
    print()
    
    return results["failed"] == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
