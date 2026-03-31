"""
5W+H Light Migration Script
============================
Voegt context_5wh structuur toe aan alle knowledge cards

VEILIG:
- Maakt backup
- Backwards compatible
- Dry-run mode
"""

import json
import os
from datetime import datetime
from pathlib import Path

KB_PATH = "/app/backend/data/learned_knowledge/knowledge_base.json"
BACKUP_DIR = "/app/backend/data/learned_knowledge/"


def create_backup():
    """Maak backup van huidige knowledge_base.json"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{BACKUP_DIR}knowledge_base.backup_5wh_{timestamp}.json"
    
    with open(KB_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Backup created: {backup_path}")
    return backup_path


def migrate_card(card):
    """Voeg 5W+H structuur toe aan één card"""
    
    # Check of al gemigreerd
    if 'context_5wh' in card:
        return card, False  # Already migrated
    
    # Voeg nieuwe velden toe
    card['context_5wh'] = {
        'wie': '',
        'wat': '',
        'waar': '',
        'wanneer': '',
        'waarom': '',
        'hoe': ''
    }
    
    card['usage_count'] = 0
    card['voorgestelde_verbanden'] = []
    card['bevestigde_verbanden'] = []
    
    return card, True  # Migrated


def migrate_all(dry_run=True):
    """Migreer alle knowledge cards"""
    
    print("🔍 Loading knowledge_base.json...")
    with open(KB_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    entries = data.get('knowledge_entries', [])
    print(f"📊 Found {len(entries)} cards")
    
    migrated_count = 0
    skipped_count = 0
    
    print("\n🔄 Starting migration...")
    for i, card in enumerate(entries):
        updated_card, was_migrated = migrate_card(card)
        entries[i] = updated_card
        
        if was_migrated:
            migrated_count += 1
            if migrated_count <= 3:  # Show first 3
                print(f"  ✅ Migrated: {card.get('begrip', 'Untitled')}")
        else:
            skipped_count += 1
    
    data['knowledge_entries'] = entries
    
    print(f"\n📈 Results:")
    print(f"  - Migrated: {migrated_count} cards")
    print(f"  - Skipped (already had 5W+H): {skipped_count} cards")
    print(f"  - Total: {len(entries)} cards")
    
    if dry_run:
        print("\n⚠️  DRY RUN MODE - No changes saved")
        print("   Run with dry_run=False to save changes")
        
        # Show sample
        if len(entries) > 0:
            print("\n📋 Sample migrated card:")
            sample = entries[0]
            print(f"  Begrip: {sample.get('begrip', 'N/A')}")
            print(f"  Has context_5wh: {'context_5wh' in sample}")
            print(f"  Has usage_count: {'usage_count' in sample}")
            print(f"  Sample context: {sample.get('context_5wh', {})}")
        
        return data, migrated_count
    
    # SAVE
    print("\n💾 Saving changes...")
    with open(KB_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print("✅ Migration complete!")
    return data, migrated_count


def verify_migration():
    """Verify that migration worked"""
    print("\n🔍 Verifying migration...")
    
    with open(KB_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    entries = data.get('knowledge_entries', [])
    
    has_5wh = sum(1 for e in entries if 'context_5wh' in e)
    has_usage = sum(1 for e in entries if 'usage_count' in e)
    has_verbanden = sum(1 for e in entries if 'voorgestelde_verbanden' in e)
    
    print(f"  ✅ Cards with context_5wh: {has_5wh}/{len(entries)}")
    print(f"  ✅ Cards with usage_count: {has_usage}/{len(entries)}")
    print(f"  ✅ Cards with verbanden: {has_verbanden}/{len(entries)}")
    
    if has_5wh == len(entries) and has_usage == len(entries):
        print("\n🎉 Migration verified successfully!")
        return True
    else:
        print("\n⚠️  Migration incomplete - some cards missing fields")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("5W+H LIGHT MIGRATION")
    print("=" * 60)
    
    # Step 1: Backup
    backup_path = create_backup()
    
    # Step 2: Dry run
    print("\n" + "=" * 60)
    print("DRY RUN")
    print("=" * 60)
    migrate_all(dry_run=True)
    
    # Step 3: Confirm
    print("\n" + "=" * 60)
    confirm = input("\n🤔 Proceed with migration? (yes/no): ").strip().lower()
    
    if confirm == 'yes':
        print("\n" + "=" * 60)
        print("RUNNING MIGRATION")
        print("=" * 60)
        migrate_all(dry_run=False)
        
        # Step 4: Verify
        verify_migration()
        
        print(f"\n📁 Backup saved at: {backup_path}")
        print("✅ All done!")
    else:
        print("\n❌ Migration cancelled")
