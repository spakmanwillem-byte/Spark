#!/usr/bin/env python3
"""
Update Roadmap - Add v0.0 (Prioriteit 0) and update v1.5 status
"""

import json
from datetime import datetime

ROADMAP_PATH = '/app/backend/data/system/roadmap.json'

def load_roadmap():
    with open(ROADMAP_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_roadmap(data):
    with open(ROADMAP_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def add_v0_prioriteit_0(roadmap):
    """Add v0.0 - Prioriteit 0 (Foundation Repair)"""
    
    print("\n📝 Adding v0.0 - Prioriteit 0...")
    
    v0_0 = {
        "naam": "🔧 Prioriteit 0: Foundation Repair",
        "beschrijving": "Kritieke bugs en data-integriteit gefixed voor stabiel fundament",
        "status": "done",
        "progress": 100,
        "start_date": "2026-03-24",
        "completed_date": "2026-03-24",
        "phase": "foundation",
        "items": [
            {
                "id": "p0_001",
                "titel": "Knowledge Base Reparatie & Cleanup",
                "status": "done",
                "priority": "critical",
                "progress": 100,
                "notes": "2001→2129→2113 entries. Duplicaten verwijderd (4 lege + 14 dup). Metadata toegevoegd met transparantie (*_inferred flags). 6 backups gearchiveerd.",
                "completed_date": "2026-03-24"
            },
            {
                "id": "p0_002",
                "titel": "Chat Sessie Bug Fix",
                "status": "done",
                "priority": "critical",
                "progress": 100,
                "notes": "last_active update bij elk chatbericht. Frontend detecteert session expiry correct. Login instructie gefixt: 'Ik ben [naam], [sleutelwoord]'",
                "completed_date": "2026-03-24"
            },
            {
                "id": "p0_003",
                "titel": "Trigger-lijsten API Fix",
                "status": "done",
                "priority": "high",
                "progress": 100,
                "notes": "API routes gecorrigeerd: /api/system/triggers/* → /api/triggers/*. Laden correct in Admin Panel.",
                "completed_date": "2026-03-24"
            },
            {
                "id": "p0_004",
                "titel": "Metadata Transparantie Systeem",
                "status": "done",
                "priority": "high",
                "progress": 100,
                "notes": "Afgeleide metadata gemarkeerd met *_inferred: true flags. 40% created_via afgeleid, 31.4% type afgeleid. Onderscheid tussen echt en afgeleid expliciet.",
                "completed_date": "2026-03-24"
            },
            {
                "id": "p0_005",
                "titel": "Phase 1 Data Archivering",
                "status": "done",
                "priority": "medium",
                "progress": 100,
                "notes": "37 conversations, 16 logs, 44 test users, 6 KB backups gearchiveerd naar /archives/phase_1_foundation/. Metadata en README toegevoegd.",
                "completed_date": "2026-03-24"
            }
        ]
    }
    
    # Insert v0.0 at the beginning (before v0.9)
    versions = roadmap.get('versions', {})
    
    # Create new ordered dict with v0.0 first
    new_versions = {"v0.0": v0_0}
    new_versions.update(versions)
    
    roadmap['versions'] = new_versions
    
    print("   ✅ v0.0 added with 5 items")
    
    return roadmap

def update_v1_5_status(roadmap):
    """Update v1.5 status to ready_to_start"""
    
    print("\n📝 Updating v1.5 status...")
    
    if 'v1.5' in roadmap['versions']:
        v1_5 = roadmap['versions']['v1.5']
        v1_5['status'] = 'ready_to_start'
        v1_5['phase'] = 'current'
        v1_5['foundation_completed'] = '2026-03-24'
        
        if 'notes' not in v1_5:
            v1_5['notes'] = ""
        
        v1_5['notes'] = "Foundation is stabiel. KB heeft complete metadata en transparantie. Klaar voor tag/thema/categorie uitbreiding."
        
        print("   ✅ v1.5 status updated: in_progress → ready_to_start")
        print("   ✅ v1.5 marked as current phase")
    else:
        print("   ⚠️  v1.5 not found in roadmap")
    
    return roadmap

def add_archive_metadata(roadmap):
    """Add archive info to roadmap metadata"""
    
    print("\n📝 Adding archive metadata...")
    
    if 'metadata' not in roadmap:
        roadmap['metadata'] = {}
    
    roadmap['metadata']['last_updated'] = datetime.now().isoformat()
    roadmap['metadata']['current_phase'] = 'v1.5'
    roadmap['metadata']['archive_location'] = '/app/backend/data/archives/'
    roadmap['metadata']['latest_archive'] = 'phase_1_foundation'
    
    print("   ✅ Archive metadata added")
    
    return roadmap

def main():
    print("📅 Roadmap Update Script")
    print("="*70)
    
    # Load
    roadmap = load_roadmap()
    print(f"✅ Loaded roadmap ({len(roadmap.get('versions', {}))} versions)")
    
    # Add v0.0
    roadmap = add_v0_prioriteit_0(roadmap)
    
    # Update v1.5
    roadmap = update_v1_5_status(roadmap)
    
    # Add metadata
    roadmap = add_archive_metadata(roadmap)
    
    # Save
    save_roadmap(roadmap)
    
    print("\n" + "="*70)
    print("✅ ROADMAP UPDATE VOLTOOID!")
    print("="*70)
    print(f"   • v0.0 toegevoegd (Prioriteit 0)")
    print(f"   • v1.5 status updated (ready_to_start)")
    print(f"   • Archive metadata toegevoegd")
    print(f"   • Total versions: {len(roadmap.get('versions', {}))}")
    print("="*70)

if __name__ == '__main__':
    main()
