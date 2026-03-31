"""
Test 5W+H Verbanden System
===========================
Vul handmatig 5W+H in bij 5 test cards en test suggest_verbanden
"""

import json
import requests

KB_PATH = "/app/backend/data/learned_knowledge/knowledge_base.json"
API = "http://localhost:8001/api/verbanden"

# Load KB
with open(KB_PATH, 'r') as f:
    kb = json.load(f)

entries = kb.get('knowledge_entries', [])[:10]  # Eerste 10 cards

print("=" * 60)
print("🧪 5W+H VERBANDEN TEST")
print("=" * 60)
print(f"\nGevonden {len(entries)} cards om mee te testen\n")

# Handmatig 5W+H invullen voor test
test_cards = [
    {
        "id": entries[0]['id'],
        "begrip": entries[0].get('begrip'),
        "context": {
            "wie": "Willem, Gamers, Community",
            "wat": "Gaming community beweging",
            "waar": "Online, Roadkill Shop",
            "wanneer": "Sinds MSX tijd",
            "waarom": "Verbinding en positiviteit",
            "hoe": "Merchandise, Zorgboerderij"
        }
    },
    {
        "id": entries[1]['id'],
        "begrip": entries[1].get('begrip'),
        "context": {
            "wie": "Willem, Community supporters",
            "wat": "Merchandise winkel",
            "waar": "roadkillshop.com",
            "wanneer": "Nu actief",
            "waarom": "Financi financiering Spark Your Life",
            "hoe": "Verkoop kleding en items"
        }
    },
    {
        "id": entries[2]['id'],
        "begrip": entries[2].get('begrip'),
        "context": {
            "wie": "Willem, Supporters, Cliënten",
            "wat": "Community van helpers",
            "waar": "Online en fysiek",
            "wanneer": "Groeiend",
            "waarom": "Zorgboerderij steunen",
            "hoe": "Merchandise kopen, meedoen"
        }
    },
    {
        "id": entries[3]['id'],
        "begrip": entries[3].get('begrip'),
        "context": {
            "wie": "Bitcoin traders",
            "wat": "Cryptocurrency trading",
            "waar": "Bitvavo exchange",
            "wanneer": "2024+",
            "waarom": "Winst maken",
            "hoe": "Buy low sell high"
        }
    },
    {
        "id": entries[4]['id'],
        "begrip": entries[4].get('begrip'),
        "context": {
            "wie": "Crypto investors",
            "wat": "Digital currency",
            "waar": "Online exchanges",
            "wanneer": "Sinds 2009",
            "waarom": "Decentralisatie",
            "hoe": "Blockchain technologie"
        }
    }
]

# Update 5W+H via KB direct (sneller dan API calls)
print("📝 Vulling 5W+H in voor 5 test cards...")
for i, test in enumerate(test_cards):
    for entry in kb['knowledge_entries']:
        if entry['id'] == test['id']:
            entry['context_5wh'] = test['context']
            print(f"  ✅ {i+1}. {test['begrip']}")
            break

# Save
with open(KB_PATH, 'w') as f:
    json.dump(kb, f, indent=2, ensure_ascii=False)

print("\n💾 Knowledge base updated\n")

# Test suggest_verbanden via API
print("=" * 60)
print("🔍 TEST: suggest_verbanden")
print("=" * 60)

test_id = test_cards[0]['id']
test_begrip = test_cards[0]['begrip']

print(f"\nZoek verbanden voor: {test_begrip}")
print(f"Context: {test_cards[0]['context']}\n")

try:
    response = requests.post(
        f"{API}/suggest/{test_id}",
        params={"max_suggestions": 10},
        timeout=30
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ API Response Success!")
        print(f"\nAantal voorstellen: {data.get('count')}")
        
        for i, suggestion in enumerate(data.get('suggestions', []), 1):
            print(f"\n{i}. {suggestion.get('card_begrip')}")
            print(f"   Overlap: {', '.join(suggestion.get('overlap', []))}")
            print(f"   Card ID: {suggestion.get('card_id')}")
        
        print(f"\n{'='*60}")
        print(f"📊 CHECK BACKEND LOGS voor details!")
        print(f"{'='*60}")
        
    else:
        print(f"❌ API Error: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"❌ Error: {e}")

print("\n✅ Test complete!")
print("\nVOLGENDE STAP:")
print("  1. Check backend logs: tail -n 100 /var/log/supervisor/backend.out.log")
print("  2. Check waarom verbanden gelinkt worden (logging)")
print("  3. Test bevestig_verband via API\n")
