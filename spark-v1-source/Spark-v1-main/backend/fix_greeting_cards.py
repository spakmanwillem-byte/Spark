"""
Fix Greeting Cards - Add Response Field
========================================
Voegt 'response' en 'type' toe aan greeting cards
ZONDER bestaande lagen aan te passen
"""

import json
from datetime import datetime

KB_PATH = "/app/backend/data/learned_knowledge/knowledge_base.json"

# Greeting cards met responses
GREETING_UPDATES = [
    {
        "begrip": "Hallo Spark",
        "type": "greeting",
        "response": {
            "text": [
                "Hallo! Fijn dat je er bent.",
                "Hey! Hoe kan ik je helpen?",
                "Hallo daar! Wat kan ik voor je doen?"
            ],
            "trigger_words": ["hallo"],
            "trigger_pattern": "^hallo\\s*spark"
        }
    },
    {
        "begrip": "Hey Spark",
        "type": "greeting",
        "response": {
            "text": [
                "Hey! Wat kan ik voor je doen?",
                "Hallo! Hoe gaat het?",
                "Hey daar!"
            ],
            "trigger_words": ["hey"],
            "trigger_pattern": "^hey\\s*spark"
        }
    },
    {
        "begrip": "Goedemorgen Spark",
        "type": "greeting",
        "response": {
            "text": [
                "Goedemorgen! Klaar voor een nieuwe dag?",
                "Goedemorgen! Hoe kan ik je helpen?",
                "Goedemorgen! Fijn je te zien."
            ],
            "trigger_words": ["goedemorgen"],
            "trigger_pattern": "^goedemorgen\\s*spark"
        }
    },
    {
        "begrip": "Hi Spark",
        "type": "greeting",
        "response": {
            "text": [
                "Hi! Hoe gaat het?",
                "Hey! Wat kan ik voor je doen?",
                "Hi daar!"
            ],
            "trigger_words": ["hi"],
            "trigger_pattern": "^hi\\s*spark"
        }
    },
    {
        "begrip": "Goedemiddag Spark",
        "type": "greeting",
        "response": {
            "text": [
                "Goedemiddag! Hoe gaat het?",
                "Middag! Wat kan ik voor je doen?"
            ],
            "trigger_words": ["goedemiddag", "middag"],
            "trigger_pattern": "^(goedemiddag|middag)\\s*spark"
        }
    },
    {
        "begrip": "Goedenavond Spark",
        "type": "greeting",
        "response": {
            "text": [
                "Goedenavond! Hoe was je dag?",
                "Avond! Wat kan ik voor je doen?"
            ],
            "trigger_words": ["goedenavond", "avond"],
            "trigger_pattern": "^(goedenavond|avond)\\s*spark"
        }
    }
]


def update_greeting_cards():
    """Update greeting cards met response field"""
    
    print("=" * 60)
    print("GREETING CARDS UPDATEN")
    print("=" * 60)
    
    # Load KB
    with open(KB_PATH, 'r', encoding='utf-8') as f:
        kb = json.load(f)
    
    entries = kb.get('knowledge_entries', [])
    updated_count = 0
    created_count = 0
    
    for update in GREETING_UPDATES:
        begrip = update['begrip']
        
        # Zoek bestaande card
        found = False
        for card in entries:
            if card.get('begrip') == begrip:
                # Card bestaat - update
                print(f"\n✏️  UPDATE: {begrip}")
                
                # Voeg type toe (overschrijf als het 'unknown' was)
                old_type = card.get('type', 'unknown')
                card['type'] = update['type']
                print(f"   Type: {old_type} → {update['type']}")
                
                # Voeg response toe
                card['response'] = update['response']
                print(f"   Response templates: {len(update['response']['text'])}")
                print(f"   Trigger words: {update['response']['trigger_words']}")
                
                # Lagen blijven ONGEWIJZIGD
                print(f"   Lagen: ONGEWIJZIGD ✓")
                
                updated_count += 1
                found = True
                break
        
        if not found:
            # Card bestaat niet - maak nieuwe aan
            print(f"\n➕ CREATE: {begrip}")
            new_card = {
                "id": str(uuid4()),
                "begrip": begrip,
                "type": update['type'],
                "lagen": {
                    "laag1": f"Een begroeting gericht aan Spark."
                },
                "response": update['response'],
                "tags": ["begroeting", "communicatie"],
                "metadata": {
                    "created_date": datetime.now().isoformat(),
                    "bron": "system_greeting"
                },
                "context_5wh": {
                    "wie": "",
                    "wat": "Begroeting",
                    "waar": "",
                    "wanneer": "",
                    "waarom": "Contact maken met Spark",
                    "hoe": ""
                },
                "usage_count": 0,
                "voorgestelde_verbanden": [],
                "bevestigde_verbanden": []
            }
            entries.append(new_card)
            created_count += 1
    
    # Save
    kb['knowledge_entries'] = entries
    with open(KB_PATH, 'w', encoding='utf-8') as f:
        json.dump(kb, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 60)
    print("📊 RESULTAAT")
    print("=" * 60)
    print(f"  Updated: {updated_count} cards")
    print(f"  Created: {created_count} cards")
    print(f"  Total greeting cards: {updated_count + created_count}")
    print("\n✅ Greeting cards klaar!\n")


if __name__ == "__main__":
    from uuid import uuid4
    update_greeting_cards()
