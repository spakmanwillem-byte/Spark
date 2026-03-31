#!/usr/bin/env python3
"""
Knowledge Base Repair Script
Doel: Repareer knowledge_base.json voor validiteit en stabiliteit
- Update entry counts in metadata
- Valideer structuur van entries
- Rapporteer inconsistenties (zonder aan te passen)
"""

import json
import sys
from datetime import datetime, timezone
from collections import defaultdict

KB_PATH = '/app/backend/data/learned_knowledge/knowledge_base.json'

def load_knowledge_base():
    """Laad de knowledge base"""
    try:
        with open(KB_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Fout bij laden: {e}")
        sys.exit(1)

def analyze_inconsistencies(entries):
    """Analyseer inconsistenties zonder aan te passen"""
    report = {
        'hoofdlettergebruik': defaultdict(list),
        'mogelijke_duplicaten': [],
        'structuur_problemen': [],
        'id_duplicaten': defaultdict(list)
    }
    
    # Verzamel begrippen voor hoofdletter analyse
    begrippen_map = defaultdict(list)
    seen_ids = defaultdict(list)
    
    for idx, entry in enumerate(entries):
        begrip = entry.get('begrip', '')
        entry_id = entry.get('id', '')
        
        # Check ID duplicaten
        if entry_id:
            seen_ids[entry_id].append(idx)
        
        # Hoofdletteranalyse
        begrip_lower = begrip.lower()
        begrippen_map[begrip_lower].append({
            'index': idx,
            'origineel': begrip,
            'id': entry_id
        })
        
        # Structuurvalidatie - check vereiste velden
        required_fields = ['id', 'begrip', 'lagen', 'metadata', 'status']
        missing_fields = [field for field in required_fields if field not in entry]
        
        if missing_fields:
            report['structuur_problemen'].append({
                'index': idx,
                'begrip': begrip,
                'missing_fields': missing_fields
            })
    
    # Identificeer hoofdlettervariaties
    for begrip_lower, occurrences in begrippen_map.items():
        if len(occurrences) > 1:
            # Check of er verschillende schrijfwijzen zijn
            unique_writings = set(occ['origineel'] for occ in occurrences)
            if len(unique_writings) > 1:
                report['hoofdlettergebruik'][begrip_lower] = list(unique_writings)
        
        # Check mogelijke duplicaten (zelfde begrip)
        if len(occurrences) > 1:
            report['mogelijke_duplicaten'].append({
                'begrip': begrip_lower,
                'aantal': len(occurrences),
                'indices': [occ['index'] for occ in occurrences],
                'schrijfwijzen': [occ['origineel'] for occ in occurrences]
            })
    
    # ID duplicaten
    for entry_id, indices in seen_ids.items():
        if len(indices) > 1:
            report['id_duplicaten'][entry_id] = indices
    
    return report

def repair_knowledge_base():
    """Hoofdfunctie: repareer KB"""
    print("🔧 Knowledge Base Repair gestart...")
    print(f"📁 Bestand: {KB_PATH}\n")
    
    # 1. Laad data
    data = load_knowledge_base()
    print("✅ Bestand succesvol geladen")
    
    # 2. Tel entries
    entries = data.get('knowledge_entries', [])
    actual_count = len(entries)
    old_count = data.get('total_entries', 0)
    
    print(f"📊 Oude count: {old_count}")
    print(f"📊 Werkelijke count: {actual_count}")
    print(f"📊 Verschil: {actual_count - old_count}\n")
    
    # 3. Analyseer inconsistenties
    print("🔍 Analyseer inconsistenties...")
    report = analyze_inconsistencies(entries)
    
    # 4. Print rapport
    print("\n" + "="*60)
    print("📋 INCONSISTENTIE RAPPORT")
    print("="*60)
    
    # Hoofdlettergebruik
    if report['hoofdlettergebruik']:
        print(f"\n⚠️  HOOFDLETTERGEBRUIK ({len(report['hoofdlettergebruik'])} gevonden):")
        for begrip_lower, variaties in list(report['hoofdlettergebruik'].items())[:10]:
            print(f"  • '{begrip_lower}' heeft variaties: {', '.join(variaties)}")
        if len(report['hoofdlettergebruik']) > 10:
            print(f"  ... en nog {len(report['hoofdlettergebruik']) - 10} andere")
    else:
        print("\n✅ Geen hoofdlettervariaties gevonden")
    
    # Mogelijke duplicaten
    if report['mogelijke_duplicaten']:
        print(f"\n⚠️  MOGELIJKE DUPLICATEN ({len(report['mogelijke_duplicaten'])} gevonden):")
        for dup in report['mogelijke_duplicaten'][:10]:
            print(f"  • '{dup['begrip']}' komt {dup['aantal']}x voor")
            print(f"    Indices: {dup['indices']}")
        if len(report['mogelijke_duplicaten']) > 10:
            print(f"  ... en nog {len(report['mogelijke_duplicaten']) - 10} andere")
    else:
        print("\n✅ Geen duplicaten gevonden")
    
    # ID duplicaten
    if report['id_duplicaten']:
        print(f"\n❌ ID DUPLICATEN ({len(report['id_duplicaten'])} gevonden):")
        for entry_id, indices in list(report['id_duplicaten'].items())[:5]:
            print(f"  • ID {entry_id} komt voor op indices: {indices}")
    else:
        print("\n✅ Geen ID duplicaten gevonden")
    
    # Structuurproblemen
    if report['structuur_problemen']:
        print(f"\n❌ STRUCTUURPROBLEMEN ({len(report['structuur_problemen'])} gevonden):")
        for prob in report['structuur_problemen'][:5]:
            print(f"  • Index {prob['index']} ('{prob['begrip']}'): Missing {prob['missing_fields']}")
        if len(report['structuur_problemen']) > 5:
            print(f"  ... en nog {len(report['structuur_problemen']) - 5} andere")
    else:
        print("\n✅ Alle entries hebben de vereiste velden")
    
    print("\n" + "="*60)
    
    # 5. Update counts
    print("\n🔧 Update metadata...")
    data['total_entries'] = actual_count
    
    # Update metadata timestamp
    if 'metadata' not in data:
        data['metadata'] = {}
    
    data['metadata']['last_updated'] = datetime.now(timezone.utc).isoformat()
    data['metadata']['last_repair'] = datetime.now(timezone.utc).isoformat()
    data['metadata']['repaired_count_from'] = old_count
    data['metadata']['repaired_count_to'] = actual_count
    
    # 6. Maak backup
    backup_path = f"{KB_PATH}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"💾 Maak backup: {backup_path}")
    
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # 7. Schrijf gerepareerd bestand terug
    print(f"💾 Schrijf gerepareerd bestand...")
    
    with open(KB_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print("\n✅ REPARATIE VOLTOOID!")
    print(f"   • Entry count gecorrigeerd: {old_count} → {actual_count}")
    print(f"   • Metadata updated")
    print(f"   • Backup aangemaakt")
    print(f"   • Alle data behouden")
    
    # 8. Valideer resultaat
    print("\n🧪 Valideer gerepareerd bestand...")
    with open(KB_PATH, 'r', encoding='utf-8') as f:
        validated = json.load(f)
    
    assert validated['total_entries'] == len(validated['knowledge_entries']), "Count mismatch na reparatie!"
    print("✅ Validatie geslaagd!")
    
    return True

if __name__ == '__main__':
    try:
        repair_knowledge_base()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ FOUT: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
