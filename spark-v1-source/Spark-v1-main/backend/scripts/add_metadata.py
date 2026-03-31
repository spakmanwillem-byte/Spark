#!/usr/bin/env python3
"""
Add Metadata to Entries
Doel: Voeg metadata object toe aan 1260 entries die dit missen
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
    backup_path = f"{KB_PATH}.add_metadata_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"💾 Backup aangemaakt: {backup_path}")
    return backup_path

def add_metadata_to_entries(entries):
    """Voeg metadata toe aan entries die dit missen"""
    
    print("\n" + "="*70)
    print("➕ METADATA TOEVOEGEN")
    print("="*70)
    
    updated_count = 0
    skipped_count = 0
    
    for entry in entries:
        # Skip entries die al metadata hebben
        if 'metadata' in entry:
            skipped_count += 1
            continue
        
        # Maak metadata object
        metadata = {}
        
        # Type (meestal 'knowledge' of 'snap')
        if entry.get('id', '').startswith('snap-'):
            metadata['type'] = 'snap'
            metadata['created_via'] = 'snap'
        else:
            metadata['type'] = 'knowledge'
            metadata['created_via'] = entry.get('created_via', 'conversation')
        
        # Timestamps - gebruik bestaande velden indien beschikbaar
        if 'detected_at' in entry:
            metadata['created_at'] = entry['detected_at']
            metadata['toegevoegd_op'] = entry['detected_at']
        elif 'created_at' in entry:
            metadata['created_at'] = entry['created_at']
            metadata['toegevoegd_op'] = entry['created_at']
        else:
            # Fallback: gebruik een standaard timestamp (oudere entries)
            # We gebruiken een datum in het verleden om aan te geven dat dit oude data is
            fallback_timestamp = "2026-03-01T12:00:00.000000"
            metadata['created_at'] = fallback_timestamp
            metadata['toegevoegd_op'] = fallback_timestamp
        
        # Creator info - gebruik bestaande velden
        if 'detected_by' in entry:
            metadata['created_by_admin'] = entry['detected_by']
        
        if 'last_edited_by_user_id' in entry:
            metadata['created_by_user_id'] = entry['last_edited_by_user_id']
        elif 'xp_awarded_to' in entry:
            metadata['created_by_user_id'] = entry['xp_awarded_to']
        
        # Usage tracking
        metadata['usage_count'] = entry.get('usage_count', 0)
        
        if 'last_used' in entry:
            metadata['last_used'] = entry['last_used']
        
        # Voeg metadata toe
        entry['metadata'] = metadata
        updated_count += 1
    
    print(f"\n✅ Metadata toegevoegd aan: {updated_count} entries")
    print(f"⏭️  Overgeslagen (had al metadata): {skipped_count} entries")
    
    return entries

def validate_structure(data):
    """Valideer KB structuur na metadata toevoeging"""
    
    print("\n" + "="*70)
    print("🧪 VALIDATIE")
    print("="*70)
    
    entries = data.get('knowledge_entries', [])
    
    # Check 1: Alle entries hebben metadata
    without_metadata = sum(1 for e in entries if 'metadata' not in e)
    print(f"   • Entries zonder metadata: {without_metadata}")
    
    if without_metadata == 0:
        print(f"   ✅ Alle entries hebben nu metadata!")
    else:
        print(f"   ⚠️  Nog {without_metadata} entries zonder metadata")
    
    # Check 2: Metadata structuur
    with_metadata = [e for e in entries if 'metadata' in e]
    print(f"   • Entries met metadata: {len(with_metadata)}")
    
    # Check metadata velden
    metadata_fields = {}
    for entry in with_metadata[:100]:  # Sample eerste 100
        for field in entry['metadata'].keys():
            metadata_fields[field] = metadata_fields.get(field, 0) + 1
    
    print(f"   • Meest voorkomende metadata velden:")
    for field, count in sorted(metadata_fields.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"     - {field}: {count}/100 entries")
    
    # Check 3: JSON serializable
    try:
        json.dumps(data)
        print(f"   ✅ Data is valid JSON")
    except Exception as e:
        print(f"   ❌ JSON error: {e}")
    
    return data

def main():
    print("➕ Metadata Toevoegen Script gestart...")
    print(f"📁 Bestand: {KB_PATH}\n")
    
    # Load data
    data = load_kb()
    entries = data['knowledge_entries']
    
    # Count entries without metadata
    without_metadata = sum(1 for e in entries if 'metadata' not in e)
    with_metadata = sum(1 for e in entries if 'metadata' in e)
    
    print(f"📊 Status VOOR:")
    print(f"   • Totaal entries: {len(entries)}")
    print(f"   • Met metadata: {with_metadata}")
    print(f"   • Zonder metadata: {without_metadata}")
    
    # Backup
    backup_path = make_backup(data)
    
    # Add metadata
    entries = add_metadata_to_entries(entries)
    
    # Update data
    data['knowledge_entries'] = entries
    
    # Update top-level metadata
    if 'metadata' not in data:
        data['metadata'] = {}
    data['metadata']['last_updated'] = datetime.now().isoformat()
    data['metadata']['metadata_added'] = datetime.now().isoformat()
    data['metadata']['metadata_added_count'] = without_metadata
    
    # Validate
    data = validate_structure(data)
    
    # Save
    print(f"\n💾 Schrijf data met metadata...")
    save_kb(data)
    
    # Final report
    print("\n" + "="*70)
    print("✅ METADATA TOEVOEGEN VOLTOOID!")
    print("="*70)
    
    # Count again
    final_without = sum(1 for e in data['knowledge_entries'] if 'metadata' not in e)
    final_with = sum(1 for e in data['knowledge_entries'] if 'metadata' in e)
    
    print(f"   📊 Status NA:")
    print(f"   • Totaal entries: {len(data['knowledge_entries'])}")
    print(f"   • Met metadata: {final_with}")
    print(f"   • Zonder metadata: {final_without}")
    print(f"   • Toegevoegd aan: {without_metadata} entries")
    print(f"   • Backup: {backup_path}")
    print("="*70)

if __name__ == '__main__':
    main()
