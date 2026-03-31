#!/usr/bin/env python3
"""
Fix Incomplete Metadata
Doel: Voeg ontbrekende velden toe aan bestaande metadata objecten
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

def fix_incomplete_metadata(entries):
    """Fix entries met incomplete metadata"""
    
    print("\n" + "="*70)
    print("🔧 FIX INCOMPLETE METADATA")
    print("="*70)
    
    fixed_count = 0
    
    for entry in entries:
        if 'metadata' not in entry or not entry['metadata']:
            continue
        
        metadata = entry['metadata']
        updated = False
        
        # Add missing 'type' field
        if 'type' not in metadata:
            if entry.get('id', '').startswith('snap-'):
                metadata['type'] = 'snap'
            else:
                metadata['type'] = 'knowledge'
            updated = True
        
        # Add missing 'created_via' field
        if 'created_via' not in metadata:
            if metadata.get('type') == 'snap':
                metadata['created_via'] = 'snap'
            else:
                metadata['created_via'] = entry.get('created_via', 'conversation')
            updated = True
        
        # Add timestamps if missing
        if 'created_at' not in metadata:
            if 'detected_at' in entry:
                metadata['created_at'] = entry['detected_at']
                metadata['toegevoegd_op'] = entry['detected_at']
                updated = True
            elif 'datum' in entry:
                metadata['created_at'] = entry['datum']
                metadata['toegevoegd_op'] = entry['datum']
                updated = True
        
        # Add creator info if missing
        if 'created_by_admin' not in metadata and 'detected_by' in entry:
            metadata['created_by_admin'] = entry['detected_by']
            updated = True
        
        if 'created_by_user_id' not in metadata:
            if 'last_edited_by_user_id' in entry:
                metadata['created_by_user_id'] = entry['last_edited_by_user_id']
                updated = True
            elif 'xp_awarded_to' in entry:
                metadata['created_by_user_id'] = entry['xp_awarded_to']
                updated = True
        
        # Ensure usage_count exists
        if 'usage_count' not in metadata:
            metadata['usage_count'] = entry.get('usage_count', 0)
            updated = True
        
        if updated:
            fixed_count += 1
    
    print(f"\n✅ Metadata aangevuld voor: {fixed_count} entries")
    
    return entries

def validate_metadata(entries):
    """Check metadata volledigheid"""
    
    print("\n" + "="*70)
    print("🧪 METADATA VALIDATIE")
    print("="*70)
    
    # Count velden
    field_counts = {
        'type': 0,
        'created_via': 0,
        'created_at': 0,
        'created_by_admin': 0,
        'created_by_user_id': 0,
        'usage_count': 0
    }
    
    for entry in entries:
        if 'metadata' not in entry:
            continue
        
        metadata = entry['metadata']
        for field in field_counts.keys():
            if field in metadata:
                field_counts[field] += 1
    
    total_with_metadata = sum(1 for e in entries if 'metadata' in e)
    
    print(f"   Metadata velden coverage (van {total_with_metadata} entries):")
    for field, count in field_counts.items():
        percentage = (count / total_with_metadata * 100) if total_with_metadata > 0 else 0
        status = '✅' if percentage > 90 else '⚠️ '
        print(f"   {status} {field}: {count}/{total_with_metadata} ({percentage:.1f}%)")

def main():
    print("🔧 Fix Incomplete Metadata Script...")
    print(f"📁 Bestand: {KB_PATH}\n")
    
    # Load
    data = load_kb()
    entries = data['knowledge_entries']
    
    # Before stats
    incomplete = sum(1 for e in entries if 'metadata' in e and e['metadata'] and 'type' not in e['metadata'])
    print(f"📊 Entries met incomplete metadata: {incomplete}")
    
    # Fix
    entries = fix_incomplete_metadata(entries)
    
    # Validate
    validate_metadata(entries)
    
    # Update data
    data['knowledge_entries'] = entries
    if 'metadata' not in data:
        data['metadata'] = {}
    data['metadata']['last_updated'] = datetime.now().isoformat()
    data['metadata']['metadata_fixed'] = datetime.now().isoformat()
    
    # Save
    print(f"\n💾 Opslaan...")
    save_kb(data)
    
    print("\n" + "="*70)
    print("✅ METADATA FIX VOLTOOID!")
    print("="*70)

if __name__ == '__main__':
    main()
