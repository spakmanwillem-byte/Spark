#!/usr/bin/env python3
"""
Phase 1 Foundation Archive Script
Doel: Archiveer conversations, logs, test users, en KB backups van Phase 1
"""

import json
import shutil
import os
from datetime import datetime
from pathlib import Path

# Paths
BACKEND_DATA = Path('/app/backend/data')
ARCHIVE_ROOT = BACKEND_DATA / 'archives'
PHASE_1_ARCHIVE = ARCHIVE_ROOT / 'phase_1_foundation'

def create_archive_structure():
    """Maak archive directory structuur"""
    
    print("\n" + "="*70)
    print("📁 CREATE ARCHIVE STRUCTURE")
    print("="*70)
    
    directories = [
        PHASE_1_ARCHIVE / 'conversations',
        PHASE_1_ARCHIVE / 'logs',
        PHASE_1_ARCHIVE / 'test_users',
        PHASE_1_ARCHIVE / 'knowledge_backups',
        PHASE_1_ARCHIVE / 'supervisor_logs'
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"   ✅ Created: {directory.relative_to(BACKEND_DATA)}")
    
    return True

def archive_conversations():
    """Archiveer conversation bestanden"""
    
    print("\n" + "="*70)
    print("💬 ARCHIVE CONVERSATIONS")
    print("="*70)
    
    conv_source = BACKEND_DATA / 'conversations'
    conv_archive = PHASE_1_ARCHIVE / 'conversations'
    
    if not conv_source.exists():
        print("   ⚠️  No conversations folder found")
        return 0
    
    # Kopieer alle conversation bestanden
    archived_count = 0
    for conv_file in conv_source.glob('*.json'):
        shutil.copy2(conv_file, conv_archive / conv_file.name)
        archived_count += 1
    
    print(f"   ✅ Archived {archived_count} conversation files")
    print(f"   📁 Location: {conv_archive.relative_to(BACKEND_DATA)}")
    
    return archived_count

def archive_logs():
    """Archiveer system logs"""
    
    print("\n" + "="*70)
    print("📜 ARCHIVE LOGS")
    print("="*70)
    
    logs_source = BACKEND_DATA / 'logs'
    logs_archive = PHASE_1_ARCHIVE / 'logs'
    
    archived_count = 0
    
    # System logs
    if logs_source.exists():
        for log_file in logs_source.glob('*.log'):
            shutil.copy2(log_file, logs_archive / log_file.name)
            archived_count += 1
        print(f"   ✅ Archived {archived_count} system log files")
    
    # System JSON logs
    system_logs = [
        BACKEND_DATA / 'system' / 'logs.json',
        BACKEND_DATA / 'system' / 'action_log.json',
        BACKEND_DATA / 'feedback' / 'feedback_log.json'
    ]
    
    for log_file in system_logs:
        if log_file.exists():
            shutil.copy2(log_file, logs_archive / log_file.name)
            archived_count += 1
    
    print(f"   ✅ Total logs archived: {archived_count}")
    
    # Supervisor logs (snapshot)
    supervisor_source = Path('/var/log/supervisor')
    supervisor_archive = PHASE_1_ARCHIVE / 'supervisor_logs'
    
    supervisor_count = 0
    for log_file in supervisor_source.glob('*.log'):
        # Kopieer laatste 1000 regels (snapshot)
        dest_file = supervisor_archive / log_file.name
        os.system(f"tail -n 1000 {log_file} > {dest_file}")
        supervisor_count += 1
    
    print(f"   ✅ Archived {supervisor_count} supervisor log snapshots (last 1000 lines)")
    
    return archived_count + supervisor_count

def archive_test_users():
    """Archiveer test user folders"""
    
    print("\n" + "="*70)
    print("👥 ARCHIVE TEST USERS")
    print("="*70)
    
    users_source = BACKEND_DATA / 'users'
    users_archive = PHASE_1_ARCHIVE / 'test_users'
    
    if not users_source.exists():
        print("   ⚠️  No users folder found")
        return 0
    
    # Test user patterns
    test_patterns = [
        'test_*',
        'crud_test_*',
        'flow_test_*',
        'empty_user_*',
        'new_user_*'
    ]
    
    archived_count = 0
    for pattern in test_patterns:
        for user_folder in users_source.glob(pattern):
            if user_folder.is_dir():
                dest = users_archive / user_folder.name
                shutil.copytree(user_folder, dest, dirs_exist_ok=True)
                archived_count += 1
    
    print(f"   ✅ Archived {archived_count} test user folders")
    print(f"   📁 Location: {users_archive.relative_to(BACKEND_DATA)}")
    
    # List patterns archived
    if archived_count > 0:
        print(f"   📋 Patterns archived:")
        for pattern in test_patterns:
            count = len(list(users_archive.glob(pattern)))
            if count > 0:
                print(f"      • {pattern}: {count} folders")
    
    return archived_count

def archive_knowledge_backups():
    """Archiveer KB backup bestanden"""
    
    print("\n" + "="*70)
    print("🧠 ARCHIVE KNOWLEDGE BASE BACKUPS")
    print("="*70)
    
    kb_source = BACKEND_DATA / 'learned_knowledge'
    kb_archive = PHASE_1_ARCHIVE / 'knowledge_backups'
    
    if not kb_source.exists():
        print("   ⚠️  No learned_knowledge folder found")
        return 0
    
    # Backup patterns
    backup_patterns = [
        '*.backup',
        '*.backup_*',
        '*_backup_*'
    ]
    
    archived_count = 0
    for pattern in backup_patterns:
        for backup_file in kb_source.glob(pattern):
            if backup_file.is_file():
                shutil.copy2(backup_file, kb_archive / backup_file.name)
                archived_count += 1
    
    print(f"   ✅ Archived {archived_count} KB backup files")
    
    # List backups
    if archived_count > 0:
        print(f"   📋 Backup files:")
        for backup_file in sorted(kb_archive.glob('*'))[:5]:
            size = backup_file.stat().st_size / 1024 / 1024  # MB
            print(f"      • {backup_file.name} ({size:.1f} MB)")
        if archived_count > 5:
            print(f"      ... and {archived_count - 5} more")
    
    return archived_count

def create_archive_metadata(stats):
    """Maak metadata.json voor het archief"""
    
    print("\n" + "="*70)
    print("📋 CREATE ARCHIVE METADATA")
    print("="*70)
    
    metadata = {
        "phase": "phase_1_foundation",
        "description": "Foundational work: KB repair, metadata addition, transparency, bug fixes",
        "archived_date": datetime.now().isoformat(),
        "date_range": {
            "start": "2026-03-08",
            "end": "2026-03-24"
        },
        "contents": {
            "conversations": stats['conversations'],
            "logs": stats['logs'],
            "test_users": stats['test_users'],
            "kb_backups": stats['kb_backups']
        },
        "completed_work": [
            "Knowledge Base: 2001→2129→2113 entries (cleanup + metadata)",
            "Metadata Transparency: *_inferred flags for derived data",
            "Chat Session Bug: last_active update fix",
            "Trigger Lists: API route correction",
            "Login Format: Consistent 'Ik ben [naam], [sleutelwoord]'"
        ],
        "notes": "Data from Prioriteit 0 phase - Critical foundation work before v1.5 expansion",
        "archive_location": "/app/backend/data/archives/phase_1_foundation/",
        "data_preserved": True,
        "data_deleted": False
    }
    
    metadata_file = PHASE_1_ARCHIVE / 'metadata.json'
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    print(f"   ✅ Metadata created: {metadata_file.relative_to(BACKEND_DATA)}")
    
    return metadata

def create_readme():
    """Maak README.md voor het archief"""
    
    readme_content = """# Phase 1 Foundation Archive

## 📅 Periode
**Start:** 8 maart 2026  
**Eind:** 24 maart 2026

## 🎯 Doel
Kritieke foundation work om Spark stabiel te maken voor verdere ontwikkeling.

## ✅ Voltooide Werk

### 1. Knowledge Base Reparatie
- Entry count gecorrigeerd: 2001 → 2129 → 2113
- Opgeschoond: 18 entries (4 lege + 14 duplicaten)
- Metadata toegevoegd aan alle entries
- Transparantie: Inferred data gemarkeerd met *_inferred flags

### 2. Chat Sessie Bug
- `last_active` timestamp update bij elk bericht
- Frontend detecteert session expiry correct
- Login instructie gefixt naar consistent format

### 3. Trigger-lijsten Fix
- API routes gecorrigeerd naar `/api/triggers/*`
- Laden correct in Admin Panel

### 4. Metadata Transparantie
- 40% created_via is afgeleid (gemarkeerd)
- 31.4% type is afgeleid (gemarkeerd)
- Onderscheid tussen echt en afgeleid expliciet

## 📁 Archief Inhoud

```
phase_1_foundation/
├── conversations/      # Chat history (37+ bestanden)
├── logs/              # System & action logs
├── test_users/        # Test account data (47+ folders)
├── knowledge_backups/ # KB backup bestanden
├── supervisor_logs/   # Backend/frontend log snapshots
├── metadata.json      # Archief metadata
└── README.md         # Dit bestand
```

## 🔍 Data Status
- **Preserved:** Ja, alle data is behouden
- **Deleted:** Nee, niets is verwijderd
- **Purpose:** Referentie en debug voor toekomstige ontwikkeling

## 📌 Context
Dit archief bevat data van een dynamisch, evoluerend systeem met meerdere toegangspunten:
- Chat interface
- Admin interface  
- Test accounts (Madelief, Harry, Mr Smith)
- Continue ontwikkeling en experimenten

Incomplete metadata is geen fout, maar het gevolg van hoe het systeem is gebruikt tijdens development.

## ➡️ Volgende Fase
**v1.5: Intelligent Knowledge System**
- Tag/thema/categorie systeem
- Feedback UI voor knowledge kaarten
- Nu KB stabiel is, klaar voor uitbreiding
"""
    
    readme_file = PHASE_1_ARCHIVE / 'README.md'
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"   ✅ README created: {readme_file.relative_to(BACKEND_DATA)}")

def main():
    print("🗄️  Phase 1 Foundation Archive Script")
    print("="*70)
    
    # Create structure
    create_archive_structure()
    
    # Archive data
    stats = {
        'conversations': archive_conversations(),
        'logs': archive_logs(),
        'test_users': archive_test_users(),
        'kb_backups': archive_knowledge_backups()
    }
    
    # Create metadata
    metadata = create_archive_metadata(stats)
    
    # Create README
    create_readme()
    
    # Final summary
    print("\n" + "="*70)
    print("✅ PHASE 1 ARCHIVERING VOLTOOID!")
    print("="*70)
    print(f"\n📊 Statistieken:")
    print(f"   • Conversations: {stats['conversations']} files")
    print(f"   • Logs: {stats['logs']} files")
    print(f"   • Test Users: {stats['test_users']} folders")
    print(f"   • KB Backups: {stats['kb_backups']} files")
    print(f"\n📁 Archief locatie:")
    print(f"   {PHASE_1_ARCHIVE}")
    print(f"\n📋 Metadata & README aangemaakt")
    print("="*70)
    
    return True

if __name__ == '__main__':
    main()
