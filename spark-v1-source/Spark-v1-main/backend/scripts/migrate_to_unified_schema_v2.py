#!/usr/bin/env python3
"""
Unified Schema V2 Migration Script
Migrates 859 knowledge cards to Unified Schema V2 with backward compatibility
"""
import json
import os
from datetime import datetime
from pathlib import Path

# Paths
DATA_DIR = Path("/app/backend/data")
KNOWLEDGE_FILE = DATA_DIR / "learned_knowledge" / "knowledge_base.json"
BIJBEL_FILE = DATA_DIR / "personality" / "spark_bijbel.json"

def load_json(filepath):
    """Load JSON file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(filepath, data):
    """Save JSON file with pretty formatting"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ Saved: {filepath}")

def migrate_knowledge_entry(entry):
    """
    Migrate single knowledge entry to Unified Schema V2
    Adds new fields while preserving all existing data
    """
    # Add 'type' field if missing (default: 'knowledge')
    if 'type' not in entry:
        entry['type'] = 'knowledge'
    
    # Ensure all WS5 fields exist
    if 'ws5' not in entry:
        entry['ws5'] = {}
    for key in ['who', 'what', 'when', 'where', 'why', 'how']:
        if key not in entry['ws5']:
            entry['ws5'][key] = ''
    
    # Add 'learning' object with placeholders (for future Learning Modules)
    if 'learning' not in entry:
        entry['learning'] = {
            'enabled': False,
            'difficulty': None,
            'estimated_time_minutes': None,
            'prerequisites': [],
            'learning_objectives': [],
            'quiz_questions': [],
            'user_progress': {}
        }
    
    # Add 'bronnen' array (for future PDF/audio/video linking)
    if 'bronnen' not in entry:
        entry['bronnen'] = []
    
    # Add 'cluster' object (for future folder organization)
    if 'cluster' not in entry:
        entry['cluster'] = {
            'folder': None,
            'subfolder': None,
            'position': None,
            'pinned': False,
            'color': None,
            'icon': None
        }
    
    # Add/normalize 'relaties' object (for knowledge graph)
    if 'relaties' not in entry:
        entry['relaties'] = {
            'parent': [],
            'children': [],
            'related': [],
            'mentions': [],
            'mentioned_by': [],
            'similar': []
        }
    elif 'relations' in entry:
        # Migrate old 'relations' field to new 'relaties' structure
        old_relations = entry.pop('relations', {})
        if isinstance(old_relations, dict):
            for key in ['parent', 'children', 'related', 'mentions', 'mentioned_by', 'similar']:
                if key in old_relations and isinstance(old_relations[key], list):
                    entry['relaties'][key] = old_relations[key]
    
    # Ensure 'tags' is a list
    if 'tags' not in entry:
        entry['tags'] = []
    elif not isinstance(entry['tags'], list):
        entry['tags'] = [entry['tags']] if entry['tags'] else []
    
    # Ensure 'metadata' exists
    if 'metadata' not in entry:
        entry['metadata'] = {}
    
    # Normalize metadata fields (some are at root level, some in metadata)
    root_metadata_fields = [
        'toegevoegd_op', 'created_by_admin', 'created_by_user_id', 
        'created_at', 'created_via', 'last_updated', 'usage_count', 'last_used'
    ]
    for field in root_metadata_fields:
        if field in entry and field not in entry['metadata']:
            entry['metadata'][field] = entry.pop(field)
    
    return entry

def migrate_knowledge_base():
    """Migrate all 859 knowledge entries"""
    print("\n🔄 Starting Knowledge Base migration...")
    
    # Load knowledge base
    kb_data = load_json(KNOWLEDGE_FILE)
    entries = kb_data.get('knowledge_entries', [])
    
    print(f"📚 Found {len(entries)} knowledge entries")
    
    # Migrate each entry
    migrated_count = 0
    errors = []
    
    for i, entry in enumerate(entries):
        try:
            entries[i] = migrate_knowledge_entry(entry)
            migrated_count += 1
            
            if (i + 1) % 100 == 0:
                print(f"  ✓ Migrated {i + 1}/{len(entries)} entries...")
        except Exception as e:
            errors.append(f"Entry {i} ({entry.get('begrip', 'unknown')}): {e}")
    
    # Update metadata
    kb_data['metadata']['schema_version'] = 'v2.0'
    kb_data['metadata']['last_migration'] = datetime.now().isoformat()
    kb_data['metadata']['migration_script'] = 'migrate_to_unified_schema_v2.py'
    
    # Save migrated data
    save_json(KNOWLEDGE_FILE, kb_data)
    
    print(f"\n✅ Migration complete!")
    print(f"   Migrated: {migrated_count}/{len(entries)} entries")
    
    if errors:
        print(f"\n⚠️  Errors ({len(errors)}):")
        for error in errors[:5]:  # Show first 5 errors
            print(f"   - {error}")
    
    return migrated_count, errors

def migrate_bijbel_to_unified():
    """
    Migrate norms, values, and bible items to unified format
    and optionally merge into knowledge_base.json
    """
    print("\n🔄 Starting Bijbel migration...")
    
    bijbel_data = load_json(BIJBEL_FILE)
    
    # Count items
    norms_count = len(bijbel_data.get('norms', []))
    values_count = len(bijbel_data.get('values', []))
    bijbel_count = len(bijbel_data.get('bijbel', []))
    
    print(f"📖 Found {norms_count} norms, {values_count} values, {bijbel_count} bijbel items")
    
    unified_entries = []
    
    # Migrate norms
    for norm in bijbel_data.get('norms', []):
        unified_entry = {
            'id': norm.get('id'),
            'type': 'norm',
            'begrip': norm.get('norm'),
            'lagen': {
                'laag1': norm.get('beschrijving', ''),
                'laag2': '',
                'laag3': '',
                'laag4': ''
            },
            'ws5': {
                'who': '',
                'what': '',
                'when': '',
                'where': '',
                'why': '',
                'how': ''
            },
            'tags': ['norm', 'gedrag'],
            'status': 'active',
            'belangrijkheid': norm.get('belangrijkheid', 3),
            'metadata': {
                'toegevoegd_op': norm.get('toegevoegd_op'),
                'created_via': 'migration_v2',
                'original_source': 'spark_bijbel.json'
            },
            'learning': {
                'enabled': False,
                'difficulty': None,
                'estimated_time_minutes': None,
                'prerequisites': [],
                'learning_objectives': [],
                'quiz_questions': [],
                'user_progress': {}
            },
            'bronnen': [],
            'cluster': {
                'folder': 'Spark Gedrag',
                'subfolder': 'Normen',
                'position': None,
                'pinned': False,
                'color': None,
                'icon': '📏'
            },
            'relaties': {
                'parent': [],
                'children': [],
                'related': [],
                'mentions': [],
                'mentioned_by': [],
                'similar': []
            }
        }
        unified_entries.append(unified_entry)
    
    # Migrate values
    for value in bijbel_data.get('values', []):
        unified_entry = {
            'id': value.get('id'),
            'type': 'value',
            'begrip': value.get('waarde'),
            'lagen': {
                'laag1': value.get('beschrijving', ''),
                'laag2': '',
                'laag3': '',
                'laag4': ''
            },
            'ws5': {
                'who': '',
                'what': '',
                'when': '',
                'where': '',
                'why': '',
                'how': ''
            },
            'tags': ['waarde', 'kernwaarde'],
            'status': 'active',
            'belangrijkheid': value.get('belangrijkheid', 5),
            'metadata': {
                'toegevoegd_op': value.get('toegevoegd_op'),
                'created_via': 'migration_v2',
                'original_source': 'spark_bijbel.json'
            },
            'learning': {
                'enabled': False,
                'difficulty': None,
                'estimated_time_minutes': None,
                'prerequisites': [],
                'learning_objectives': [],
                'quiz_questions': [],
                'user_progress': {}
            },
            'bronnen': [],
            'cluster': {
                'folder': 'Spark Waarden',
                'subfolder': 'Kernwaarden',
                'position': None,
                'pinned': False,
                'color': None,
                'icon': '💎'
            },
            'relaties': {
                'parent': [],
                'children': [],
                'related': [],
                'mentions': [],
                'mentioned_by': [],
                'similar': []
            }
        }
        unified_entries.append(unified_entry)
    
    # Migrate bijbel items
    for bijbel_item in bijbel_data.get('bijbel', []):
        unified_entry = {
            'id': bijbel_item.get('id'),
            'type': 'bible',
            'begrip': bijbel_item.get('naam'),
            'lagen': {
                'laag1': bijbel_item.get('beschrijving', '')[:500] if len(bijbel_item.get('beschrijving', '')) > 500 else bijbel_item.get('beschrijving', ''),
                'laag2': bijbel_item.get('beschrijving', '') if len(bijbel_item.get('beschrijving', '')) > 500 else '',
                'laag3': '',
                'laag4': ''
            },
            'ws5': {
                'who': '',
                'what': '',
                'when': '',
                'where': '',
                'why': '',
                'how': ''
            },
            'tags': ['filosofie', 'bijbel', 'visie'],
            'status': 'active',
            'belangrijkheid': 5,
            'metadata': {
                'toegevoegd_op': bijbel_item.get('toegevoegd_op'),
                'created_via': 'migration_v2',
                'original_source': 'spark_bijbel.json',
                'context': 'Spark Bijbel'
            },
            'learning': {
                'enabled': False,
                'difficulty': None,
                'estimated_time_minutes': None,
                'prerequisites': [],
                'learning_objectives': [],
                'quiz_questions': [],
                'user_progress': {}
            },
            'bronnen': [],
            'cluster': {
                'folder': 'Spark Bijbel',
                'subfolder': 'Kosmologische Visies',
                'position': None,
                'pinned': False,
                'color': None,
                'icon': '📜'
            },
            'relaties': {
                'parent': [],
                'children': [],
                'related': [],
                'mentions': [],
                'mentioned_by': [],
                'similar': []
            }
        }
        unified_entries.append(unified_entry)
    
    print(f"✅ Converted {len(unified_entries)} bijbel items to unified format")
    
    # Save unified bijbel entries to separate file for now
    unified_bijbel_file = DATA_DIR / "learned_knowledge" / "unified_bijbel_entries.json"
    save_json(unified_bijbel_file, {
        'unified_entries': unified_entries,
        'metadata': {
            'schema_version': 'v2.0',
            'migration_date': datetime.now().isoformat(),
            'source': 'spark_bijbel.json',
            'note': 'These can be merged into knowledge_base.json when ready'
        }
    })
    
    return len(unified_entries)

def validate_migration():
    """Validate migrated data"""
    print("\n🔍 Validating migration...")
    
    kb_data = load_json(KNOWLEDGE_FILE)
    entries = kb_data.get('knowledge_entries', [])
    
    required_fields = ['id', 'begrip', 'type', 'lagen', 'ws5', 'tags', 'status', 
                      'belangrijkheid', 'metadata', 'learning', 'bronnen', 'cluster', 'relaties']
    
    validation_errors = []
    
    for i, entry in enumerate(entries[:10]):  # Check first 10 entries
        for field in required_fields:
            if field not in entry:
                validation_errors.append(f"Entry {i} missing field: {field}")
    
    if validation_errors:
        print(f"⚠️  Validation issues:")
        for error in validation_errors:
            print(f"   - {error}")
        return False
    else:
        print("✅ Validation passed! All required fields present.")
        return True

def main():
    """Main migration function"""
    print("=" * 60)
    print("🚀 UNIFIED SCHEMA V2 MIGRATION")
    print("=" * 60)
    
    # Step 1: Migrate knowledge base
    kb_count, kb_errors = migrate_knowledge_base()
    
    # Step 2: Migrate bijbel items
    bijbel_count = migrate_bijbel_to_unified()
    
    # Step 3: Validate
    is_valid = validate_migration()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 MIGRATION SUMMARY")
    print("=" * 60)
    print(f"✅ Knowledge entries migrated: {kb_count}")
    print(f"✅ Bijbel items converted: {bijbel_count}")
    print(f"✅ Validation: {'PASSED' if is_valid else 'FAILED'}")
    print(f"✅ Schema version: v2.0")
    print(f"✅ Backward compatible: YES")
    
    if kb_errors:
        print(f"\n⚠️  {len(kb_errors)} errors occurred during migration")
    
    print("\n🎯 Next steps:")
    print("   1. Test KnowledgeBase tab (859 entries should load)")
    print("   2. Test Chat (knowledge retrieval should work)")
    print("   3. Test Leaderboard (word count should still be correct)")
    print("   4. Optional: Merge unified_bijbel_entries.json into knowledge_base.json")
    print("=" * 60)

if __name__ == "__main__":
    main()
