#!/usr/bin/env python3
"""
Knowledge Base Cleanup Script
Doel: Verwijder alleen 4 lege entries + 13 duplicaten (behoud beste versie)
"""

import json
from datetime import datetime

KB_PATH = '/app/backend/data/learned_knowledge/knowledge_base.json'

def load_kb():
    with open(KB_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_kb(data):
    with open(KB_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def make_backup(data):
    backup_path = f"{KB_PATH}.cleanup_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"💾 Backup aangemaakt: {backup_path}")
    return backup_path

def remove_empty_entries(entries):
    """Verwijder 4 volledig lege entries"""
    
    print("\n" + "="*70)
    print("🗑️  STAP 1: VERWIJDER LEGE ENTRIES")
    print("="*70)
    
    # IDs van de 4 lege entries
    empty_ids = [
        "snap-80c5366f",  # "ik ga naar bed"
        "snap-c8b02ee0",  # "slaaplekker"
        "snap-f2515914",  # "Test bericht 1"
        "snap-6d15dc63"   # "Test bericht 2"
    ]
    
    removed = []
    kept_entries = []
    
    for entry in entries:
        if entry.get('id') in empty_ids:
            removed.append(entry.get('begrip', 'N/A'))
        else:
            kept_entries.append(entry)
    
    print(f"\n✅ Verwijderd: {len(removed)} lege entries")
    for begrip in removed:
        print(f"   • '{begrip}'")
    
    return kept_entries

def remove_duplicates(entries):
    """Verwijder duplicaten, behoud versie met meeste inhoud"""
    
    print("\n" + "="*70)
    print("🗑️  STAP 2: VERWIJDER DUPLICATEN")
    print("="*70)
    
    # Duplicaat mapping: begrip -> lijst van (index, keep=True/False)
    # Behoud versie met meeste content
    duplicates_to_remove = {
        'balken': {'keep_index': 660, 'remove_indices': [757]},
        'blauwdruk': {'keep_index': 905, 'remove_indices': [380]},
        'duiken': {'keep_index': 1018, 'remove_indices': [1073]},
        'lam': {'keep_index': 1120, 'remove_indices': [1114]},
        'medaillon': {'keep_index': 668, 'remove_indices': [761]},
        'mollen': {'keep_index': 722, 'remove_indices': [769]},
        'nacht': {'keep_index': 113, 'remove_indices': [1062]},
        'nevenschade': {'keep_index': 495, 'remove_indices': [1068]},
        'onthoud dit': {'keep_index': 153, 'remove_indices': [1601]},
        'onthouden': {'keep_index': 996, 'remove_indices': [1261]},
        'planken': {'keep_index': 756, 'remove_indices': [659]},
        'tijdige communicatie vanuit de meldkamer kan levens redden.': {'keep_index': 1739, 'remove_indices': [1740]},
        'tip': {'keep_index': 755, 'remove_indices': [654]},
        'wat is een fiets': {'keep_index': 1652, 'remove_indices': [1655]}
    }
    
    # Collect all indices to remove
    indices_to_remove = set()
    for dup_info in duplicates_to_remove.values():
        indices_to_remove.update(dup_info['remove_indices'])
    
    # Build new entry list
    kept_entries = []
    removed_count = 0
    
    for idx, entry in enumerate(entries):
        if idx in indices_to_remove:
            removed_count += 1
            print(f"   ❌ Verwijderd: '{entry.get('begrip', 'N/A')}' (index {idx})")
        else:
            kept_entries.append(entry)
    
    print(f"\n✅ Verwijderd: {removed_count} duplicaat entries")
    print(f"✅ Behouden: {len(kept_entries)} entries")
    
    return kept_entries

def validate_structure(data):
    """Valideer KB structuur na cleanup"""
    
    print("\n" + "="*70)
    print("🧪 VALIDATIE")
    print("="*70)
    
    entries = data.get('knowledge_entries', [])
    
    # Check 1: Totaal klopt
    if data['total_entries'] != len(entries):
        print(f"   ⚠️  Metadata update nodig: {data['total_entries']} → {len(entries)}")
        data['total_entries'] = len(entries)
    else:
        print(f"   ✅ Total entries klopt: {len(entries)}")
    
    # Check 2: Unique IDs
    ids = [e.get('id') for e in entries]
    unique_ids = set(ids)
    if len(ids) != len(unique_ids):
        print(f"   ❌ Duplicate IDs gevonden: {len(ids) - len(unique_ids)}")
    else:
        print(f"   ✅ Alle IDs zijn uniek")
    
    # Check 3: Begrippen lowercase check
    from collections import defaultdict
    begrippen_map = defaultdict(list)
    for entry in entries:
        begrip = entry.get('begrip', '').lower()
        begrippen_map[begrip].append(entry.get('id'))
    
    duplicates = {k: v for k, v in begrippen_map.items() if len(v) > 1}
    if duplicates:
        print(f"   ⚠️  Nog {len(duplicates)} duplicaat begrippen (na cleanup)")
    else:
        print(f"   ✅ Geen duplicaat begrippen meer")
    
    # Check 4: JSON serializable
    try:
        json.dumps(data)
        print(f"   ✅ Data is valid JSON")
    except Exception as e:
        print(f"   ❌ JSON error: {e}")
    
    return data

def main():
    print("🧹 Knowledge Base Cleanup gestart...")
    print(f"📁 Bestand: {KB_PATH}\n")
    
    # Load data
    data = load_kb()
    original_count = len(data['knowledge_entries'])
    print(f"📊 Origineel aantal entries: {original_count}")
    
    # Backup
    backup_path = make_backup(data)
    
    # Step 1: Remove empty entries
    entries = remove_empty_entries(data['knowledge_entries'])
    
    # Step 2: Remove duplicates
    entries = remove_duplicates(entries)
    
    # Update data
    data['knowledge_entries'] = entries
    data['total_entries'] = len(entries)
    
    # Update metadata
    if 'metadata' not in data:
        data['metadata'] = {}
    data['metadata']['last_updated'] = datetime.now().isoformat()
    data['metadata']['last_cleanup'] = datetime.now().isoformat()
    data['metadata']['cleanup_removed'] = original_count - len(entries)
    
    # Validate
    data = validate_structure(data)
    
    # Save
    print(f"\n💾 Schrijf opgeschoonde data...")
    save_kb(data)
    
    # Final report
    print("\n" + "="*70)
    print("✅ CLEANUP VOLTOOID!")
    print("="*70)
    print(f"   • Origineel: {original_count} entries")
    print(f"   • Verwijderd: {original_count - len(entries)} entries (4 lege + 13 duplicaten)")
    print(f"   • Nieuw totaal: {len(entries)} entries")
    print(f"   • Backup: {backup_path}")
    print("="*70)

if __name__ == '__main__':
    main()
