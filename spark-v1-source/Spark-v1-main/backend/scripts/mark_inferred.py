#!/usr/bin/env python3
"""
Mark Inferred Metadata
Doel: Markeer metadata die is afgeleid (niet origineel aanwezig)
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

def mark_inferred_metadata(entries):
    """Markeer afgeleid metadata met inference flag"""
    
    print("\n" + "="*70)
    print("🏷️  MARKEER INFERRED METADATA")
    print("="*70)
    
    marked_count = 0
    
    for entry in entries:
        if 'metadata' not in entry:
            continue
        
        metadata = entry['metadata']
        inference_added = False
        
        # Check 1: created_via zonder origineel veld
        if 'created_via' in metadata and 'created_via' not in entry:
            # Entry heeft GEEN origineel created_via veld (top-level)
            # Dus de waarde in metadata is afgeleid
            metadata['created_via_inferred'] = True
            inference_added = True
        
        # Check 2: type zonder origineel type
        # (Alle types zijn afgeleid, want origineel was er geen type veld in entries)
        # Maar we markeren alleen als we het niet 100% zeker weten
        if 'type' in metadata:
            # Snap is 100% zeker (ID prefix), dus NIET markeren
            if metadata['type'] == 'snap' and entry.get('id', '').startswith('snap-'):
                pass  # Zeker, geen inference
            # Custom types (bio, definitie) zijn origineel, NIET markeren
            elif metadata['type'] in ['bio', 'definitie']:
                pass  # Origineel, geen inference
            # Knowledge is een aanname (fallback), WEL markeren
            elif metadata['type'] == 'knowledge':
                metadata['type_inferred'] = True
                inference_added = True
        
        # Check 3: timestamps zonder origineel veld
        if 'created_at' in metadata:
            # Check of created_at is gekopieerd of afgeleid
            if 'detected_at' not in entry and 'created_at' not in entry and 'datum' not in entry:
                # Timestamp is niet van origineel veld, maar fallback gebruikt
                if metadata['created_at'] == "2026-03-01T12:00:00.000000":
                    metadata['created_at_inferred'] = True
                    inference_added = True
        
        if inference_added:
            marked_count += 1
    
    print(f"\n✅ Inference markers toegevoegd aan: {marked_count} entries")
    
    return entries

def analyze_inferred_data(entries):
    """Analyseer hoeveel data is afgeleid"""
    
    print("\n" + "="*70)
    print("📊 INFERENCE ANALYSE")
    print("="*70)
    
    stats = {
        'created_via_inferred': 0,
        'type_inferred': 0,
        'created_at_inferred': 0
    }
    
    for entry in entries:
        if 'metadata' not in entry:
            continue
        
        metadata = entry['metadata']
        
        if metadata.get('created_via_inferred'):
            stats['created_via_inferred'] += 1
        if metadata.get('type_inferred'):
            stats['type_inferred'] += 1
        if metadata.get('created_at_inferred'):
            stats['created_at_inferred'] += 1
    
    total = len(entries)
    
    print(f"\n   Afgeleid metadata (van {total} entries):")
    print(f"   • created_via_inferred: {stats['created_via_inferred']} ({stats['created_via_inferred']/total*100:.1f}%)")
    print(f"   • type_inferred: {stats['type_inferred']} ({stats['type_inferred']/total*100:.1f}%)")
    print(f"   • created_at_inferred: {stats['created_at_inferred']} ({stats['created_at_inferred']/total*100:.1f}%)")
    
    # Sample entries met inference
    print(f"\n📋 VOORBEELDEN:")
    
    # created_via inferred
    example1 = next((e for e in entries if e.get('metadata', {}).get('created_via_inferred')), None)
    if example1:
        print(f"\n   1. Entry met inferred created_via:")
        print(f"      • Begrip: {example1.get('begrip')}")
        print(f"      • created_via: {example1['metadata'].get('created_via')} (inferred)")
        print(f"      • type: {example1['metadata'].get('type')}")
    
    # type inferred
    example2 = next((e for e in entries if e.get('metadata', {}).get('type_inferred')), None)
    if example2:
        print(f"\n   2. Entry met inferred type:")
        print(f"      • Begrip: {example2.get('begrip')}")
        print(f"      • type: {example2['metadata'].get('type')} (inferred)")
        print(f"      • created_via: {example2['metadata'].get('created_via')}")

def main():
    print("🏷️  Mark Inferred Metadata Script...")
    print(f"📁 Bestand: {KB_PATH}\n")
    
    # Load
    data = load_kb()
    entries = data['knowledge_entries']
    
    print(f"📊 Totaal entries: {len(entries)}")
    
    # Backup
    backup_path = f"{KB_PATH}.mark_inferred_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"💾 Backup: {backup_path}")
    
    # Mark inferred
    entries = mark_inferred_metadata(entries)
    
    # Analyze
    analyze_inferred_data(entries)
    
    # Update data
    data['knowledge_entries'] = entries
    if 'metadata' not in data:
        data['metadata'] = {}
    data['metadata']['last_updated'] = datetime.now().isoformat()
    data['metadata']['inference_marked'] = datetime.now().isoformat()
    
    # Save
    print(f"\n💾 Opslaan...")
    save_kb(data)
    
    print("\n" + "="*70)
    print("✅ INFERENCE MARKING VOLTOOID!")
    print("="*70)
    print("\n📌 Transparantie:")
    print("   • Echte data (origineel) blijft ongemarkeerd")
    print("   • Afgeleide data krijgt *_inferred: true flag")
    print("   • Later makkelijk te filteren of corrigeren")
    print("="*70)

if __name__ == '__main__':
    main()
