#!/usr/bin/env python3
"""
End-to-End test: Simuleer realistische chat scenario's
"""

import sys
sys.path.insert(0, '/app/backend')

from services.knowledge_service import KnowledgeService
from utils.data_manager import DataManager

def cleanup_test_concepts():
    """Verwijder test concepten"""
    data = DataManager.load_json('learned_knowledge/knowledge_base.json')
    entries = data.get('knowledge_entries', [])
    
    test_concepts = ['Kwantumcomputing', 'Meditatie', 'Permacultuur']
    entries = [e for e in entries if e.get('begrip') not in test_concepts]
    
    data['knowledge_entries'] = entries
    DataManager.save_json('learned_knowledge/knowledge_base.json', data)

# Cleanup
cleanup_test_concepts()

print("=" * 70)
print("🧪 END-TO-END TEST: Realistische Chat Scenario's")
print("=" * 70)
print()

# Scenario 1: Gebruiker stelt een vraag
print("Scenario 1: Gebruiker vraagt 'Wat is kwantumcomputing?'")
result = KnowledgeService.create_knowledge_snap(
    concept="Wat is kwantumcomputing?",
    context="Gebruiker wil leren over technologie",
    user_naam="Willem"
)
if result:
    print(f"  ✅ Snap aangemaakt: '{result['begrip']}'")
    print(f"  📋 Status: {result['status']}")
    print(f"  🏷️  Tags: {', '.join(result['tags'])}")
else:
    print("  ❌ Snap afgewezen")
print()

# Scenario 2: Gebruiker vraagt om uitleg
print("Scenario 2: Gebruiker vraagt 'Vertel me meer over meditatie'")
result = KnowledgeService.create_knowledge_snap(
    concept="Vertel me meer over meditatie",
    context="Gebruiker is geïnteresseerd in mindfulness",
    user_naam="Willem"
)
if result:
    print(f"  ✅ Snap aangemaakt: '{result['begrip']}'")
    print(f"  📋 Status: {result['status']}")
else:
    print("  ❌ Snap afgewezen")
print()

# Scenario 3: Gebruiker noemt een concept zonder vraagwoord
print("Scenario 3: Gebruiker noemt 'Hoe werkt permacultuur precies?'")
result = KnowledgeService.create_knowledge_snap(
    concept="Hoe werkt permacultuur precies?",
    context="Gesprek over duurzaamheid",
    user_naam="Willem"
)
if result:
    print(f"  ✅ Snap aangemaakt: '{result['begrip']}'")
    print(f"  📋 Status: {result['status']}")
else:
    print("  ❌ Snap afgewezen")
print()

# Scenario 4: Ruis - moet worden afgewezen
print("Scenario 4: Ruis 'nou ja het is gewoon zo'")
result = KnowledgeService.create_knowledge_snap(
    concept="nou ja het is gewoon zo",
    context="Random zin",
    user_naam="Willem"
)
if result:
    print(f"  ❌ FOUT: Snap aangemaakt: '{result['begrip']}' (zou afgewezen moeten worden)")
else:
    print("  ✅ Correct afgewezen")
print()

# Verificatie: Check database
print("=" * 70)
print("📊 VERIFICATIE: Controleer database")
print("=" * 70)
data = DataManager.load_json('learned_knowledge/knowledge_base.json')
entries = data.get('knowledge_entries', [])

test_concepts = ['Kwantumcomputing', 'Meditatie', 'Permacultuur']
found = [e for e in entries if e.get('begrip') in test_concepts]

print(f"\nGevonden entries: {len(found)}/3")
for entry in found:
    print(f"  • {entry['begrip']}")
    print(f"    - ID: {entry['id']}")
    print(f"    - Status: {entry['status']}")
    print(f"    - Created via: {entry.get('created_via', 'N/A')}")

print()

# Cleanup
print("🧹 Opruimen test data...")
cleanup_test_concepts()

print("\n✅ END-TO-END TEST VOLTOOID")
