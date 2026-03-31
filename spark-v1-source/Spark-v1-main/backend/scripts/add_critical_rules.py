#!/usr/bin/env python3
"""
Identity System - Add Auth/Display/System Separation
Doel: Update identity files met 3-laags scheiding voor data integriteit
"""

import json
from pathlib import Path
from datetime import datetime

IDENTITIES_ROOT = Path('/app/backend/data/identities')

def update_willem_identity():
    """Update Willem identity met Auth/Display/System scheiding"""
    
    print("👤 Updating Willem identity...")
    
    filepath = IDENTITIES_ROOT / 'willem' / 'core.json'
    
    with open(filepath, 'r') as f:
        identity = json.load(f)
    
    # Add 3-layer separation
    identity['auth_layer'] = {
        "description": "Technische laag - voor login, database, achievements, highscores",
        "user_id": "user-001",
        "auth_name": "Willem Spakman",
        "password_keyword": "appelsap",
        "critical_rule": "ALTIJD op user_id matchen, NOOIT op naam"
    }
    
    identity['display_layer'] = {
        "description": "Weergave laag - voor AI-output, UI, representatie",
        "display_name": "De Willem",
        "visual_identity": "De Willem",
        "usage": "Frontend display, chat interface, AI responses"
    }
    
    identity['system_layer'] = {
        "description": "Data-koppeling laag - intern systeem ID",
        "system_id": "user-001",
        "critical_rule": "Alle achievements, highscores, en data ALTIJD via system_id",
        "never_match_on": ["auth_name", "display_name"],
        "always_match_on": "system_id"
    }
    
    # Add critical notes
    identity['_CRITICAL_RULES'] = {
        "rule_1": "naam ≠ identiteit ≠ data-koppeling",
        "rule_2": "Achievements/highscores → ALTIJD op user_id",
        "rule_3": "display_name ('De Willem') is alleen visueel",
        "rule_4": "'Willem Spakman' blijft intern voor auth",
        "rule_5": "NOOIT matchen op naam, ALTIJD op user_id"
    }
    
    # Update metadata
    identity['metadata']['last_updated'] = datetime.now().isoformat()
    identity['metadata']['version'] = "1.1"
    identity['metadata']['added_layers'] = "auth/display/system separation for data integrity"
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(identity, f, indent=2, ensure_ascii=False)
    
    print(f"   ✅ Updated with 3-layer separation")
    return identity

def create_identity_system_rules():
    """Create system-wide rules document"""
    
    print("\n📋 Creating identity_system_rules.json...")
    
    rules = {
        "title": "Identity System - Critical Rules",
        "version": "1.0",
        "created_at": datetime.now().isoformat(),
        "philosophy": "Structuur geven aan organische groei - niet opschonen",
        
        "layer_separation": {
            "description": "Drie kritieke lagen die GESCHEIDEN moeten blijven",
            "layers": {
                "auth_layer": {
                    "purpose": "Login, database, achievements, highscores",
                    "example": {
                        "name": "Willem Spakman",
                        "keyword": "appelsap",
                        "usage": "Backend authentication only"
                    }
                },
                "display_layer": {
                    "purpose": "AI-output, UI, representatie",
                    "example": {
                        "name": "De Willem",
                        "usage": "Frontend display, chat messages, UI labels"
                    }
                },
                "system_layer": {
                    "purpose": "Data-koppeling, referenties",
                    "example": {
                        "id": "user-001",
                        "usage": "Database queries, relationships, tracking"
                    }
                }
            }
        },
        
        "critical_rules": [
            {
                "id": "CR-001",
                "rule": "naam ≠ identiteit ≠ data-koppeling",
                "explanation": "Deze 3 concepten zijn NIET uitwisselbaar",
                "severity": "CRITICAL"
            },
            {
                "id": "CR-002",
                "rule": "ALTIJD op user_id matchen, NOOIT op naam",
                "explanation": "Namen kunnen veranderen, IDs niet. Gebruik system_id voor alle data-koppelingen",
                "severity": "CRITICAL"
            },
            {
                "id": "CR-003",
                "rule": "display_name is alleen visueel",
                "explanation": "'De Willem' is voor UI/UX, gebruik niet voor queries of matching",
                "severity": "HIGH"
            },
            {
                "id": "CR-004",
                "rule": "Achievements en highscores → user_id",
                "explanation": "Gebruik ALTIJD user_id voor tracking, niet naam",
                "severity": "CRITICAL"
            },
            {
                "id": "CR-005",
                "rule": "Organische groei is waardevol",
                "explanation": "Incomplete metadata, variatie in data, inferred values zijn acceptabel - het is geen vervuiling maar groei",
                "severity": "MEDIUM"
            }
        ],
        
        "examples": {
            "correct_user_lookup": {
                "description": "Hoe een gebruiker ophalen",
                "code": "user = db.users.find_one({'id': user_id}, {'_id': 0})",
                "never_do": "user = db.users.find_one({'naam': 'De Willem'})"
            },
            "correct_achievement_save": {
                "description": "Hoe achievement opslaan",
                "code": "achievement = {'user_id': user_id, 'type': 'xp', 'value': 100}",
                "never_do": "achievement = {'naam': 'De Willem', 'type': 'xp'}"
            },
            "correct_display": {
                "description": "Hoe naam tonen in UI",
                "code": "display_name = user_data['display_layer']['display_name']",
                "result": "De Willem"
            }
        },
        
        "migration_notes": {
            "existing_code": "Check alle queries op naam-matching",
            "refactor_needed": "Replace naam-matching met user_id-matching",
            "backwards_compat": "Temporarily support beide, maar log warnings"
        },
        
        "testing_checklist": [
            "✓ Login werkt met auth_name (Willem Spakman)",
            "✓ Display toont display_name (De Willem)",
            "✓ Achievements linken naar user_id (user-001)",
            "✓ Highscores gebruiken user_id, niet naam",
            "✓ KB entries linken naar user_id indien relevant"
        ]
    }
    
    filepath = IDENTITIES_ROOT / '_schema' / 'identity_system_rules.json'
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(rules, f, indent=2, ensure_ascii=False)
    
    print(f"   ✅ Saved: _schema/identity_system_rules.json")
    return rules

def update_readme_with_rules():
    """Update README met critical rules"""
    
    print("\n📄 Updating README...")
    
    readme_addition = """

---

## ⚠️ CRITICAL RULES - DATA INTEGRITY

### **3-Laags Scheiding**

**BELANGRIJK:** naam ≠ identiteit ≠ data-koppeling

#### **1. Auth Layer (Technisch)**
- **Doel:** Login, database, authentication
- **Voorbeeld:** "Willem Spakman" + "appelsap"
- **Gebruik:** Backend authentication ONLY

#### **2. Display Layer (Weergave)**
- **Doel:** AI-output, UI, representatie
- **Voorbeeld:** "De Willem"
- **Gebruik:** Frontend display, chat messages, UI labels

#### **3. System Layer (Data-koppeling)**
- **Doel:** Database queries, relationships, tracking
- **Voorbeeld:** `user-001`
- **Gebruik:** **ALTIJD** voor achievements, highscores, data linking

---

### **Kritieke Regels**

```
CR-001: naam ≠ identiteit ≠ data-koppeling
CR-002: ALTIJD op user_id matchen, NOOIT op naam
CR-003: display_name is alleen visueel
CR-004: Achievements en highscores → user_id
CR-005: Organische groei is waardevol (geen vervuiling)
```

### **Code Voorbeelden**

✅ **CORRECT:**
```python
# User lookup
user = db.users.find_one({'id': user_id}, {'_id': 0})

# Achievement save
achievement = {'user_id': user_id, 'type': 'xp', 'value': 100}

# Display in UI
display_name = user_data['display_layer']['display_name']  # "De Willem"
```

❌ **FOUT:**
```python
# NEVER do this
user = db.users.find_one({'naam': 'De Willem'})
achievement = {'naam': 'De Willem', 'type': 'xp'}
```

---

### **Waarom Dit Belangrijk Is**

- Namen kunnen veranderen (display preferences)
- IDs zijn persistent en uniek
- Matching op naam breekt bij typos, varianten, updates
- Data-integriteit hangt af van correcte ID-linking

**Zie ook:** `_schema/identity_system_rules.json` voor volledige documentatie

"""
    
    readme_path = IDENTITIES_ROOT / '_schema' / 'README.md'
    
    with open(readme_path, 'r') as f:
        current_readme = f.read()
    
    # Append new section
    updated_readme = current_readme + readme_addition
    
    with open(readme_path, 'w') as f:
        f.write(updated_readme)
    
    print(f"   ✅ README updated with critical rules")

def main():
    print("🔧 CRITICAL UPDATE: Auth/Display/System Separation")
    print("="*70)
    print("Filosofie: naam ≠ identiteit ≠ data-koppeling")
    print("="*70)
    
    # Update Willem (exemplar for 3-layer separation)
    update_willem_identity()
    
    # Create system-wide rules
    create_identity_system_rules()
    
    # Update README
    update_readme_with_rules()
    
    print("\n" + "="*70)
    print("✅ CRITICAL RULES GEÏMPLEMENTEERD")
    print("="*70)
    print("\n🎯 Key Updates:")
    print("   • Willem identity: 3-layer separation toegevoegd")
    print("   • System rules: identity_system_rules.json created")
    print("   • README: Critical rules section added")
    print("\n⚠️  BELANGRIJK:")
    print("   • Alle code moet user_id gebruiken")
    print("   • NOOIT matchen op naam")
    print("   • display_name is alleen visueel")
    print("="*70)

if __name__ == '__main__':
    main()
