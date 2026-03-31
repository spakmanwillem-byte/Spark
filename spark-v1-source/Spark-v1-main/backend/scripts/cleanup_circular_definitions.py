#!/usr/bin/env python3
"""
Cleanup: Entries met triviale/circulaire definities
Verwijdert entries waar laag1 alleen het begrip herhaalt zonder uitleg
"""

import json
import sys
from datetime import datetime

def load_knowledge_base(path: str):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_knowledge_base(path: str, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def is_circular_definition(begrip: str, laag1: str) -> bool:
    """
    Check of laag1 een circulaire definitie is
    (herhaalt alleen het begrip zonder echte uitleg)
    """
    if not laag1:
        return True
    
    begrip_lower = begrip.lower().strip()
    laag1_lower = laag1.lower().strip()
    
    # Exact hetzelfde
    if laag1_lower == begrip_lower:
        return True
    
    # Herhaalt begrip met minimale toevoeging (< 5 extra woorden)
    if laag1_lower.startswith(begrip_lower):
        extra = laag1_lower[len(begrip_lower):].strip()
        # Als extra minder dan 20 chars is, is het triviaal
        if len(extra) < 20:
            return True
    
    # Zeer kort (< 15 chars) en lijkt op begrip
    if len(laag1) < 15 and begrip_lower in laag1_lower:
        return True
    
    return False

def cleanup_circular_definitions(kb_path: str, dry_run=False):
    print("🔍 Laden knowledge base...")
    data = load_knowledge_base(kb_path)
    entries = data.get("knowledge_entries", [])
    
    original_count = len(entries)
    print(f"📊 Origineel: {original_count} entries\n")
    
    # Filter circulaire definities
    to_remove = []
    to_keep = []
    
    for entry in entries:
        begrip = entry.get("begrip", "").strip()
        lagen = entry.get("lagen", {})
        laag1 = lagen.get("laag1", "").strip()
        
        # Check andere lagen ook
        laag2 = lagen.get("laag2", "").strip()
        laag3 = lagen.get("laag3", "").strip()
        laag4 = lagen.get("laag4", "").strip()
        
        # Als laag1 circulair is EN andere lagen ook leeg/kort
        if is_circular_definition(begrip, laag1):
            # Check of andere lagen substantie hebben
            has_substance = any(
                len(layer) > 30 
                for layer in [laag2, laag3, laag4] 
                if layer
            )
            
            if not has_substance:
                to_remove.append({
                    'entry': entry,
                    'begrip': begrip,
                    'laag1': laag1,
                    'id': entry.get('id', '')[:15],
                    'status': entry.get('status', '')
                })
            else:
                to_keep.append(entry)
        else:
            to_keep.append(entry)
    
    print(f"✅ Te behouden: {len(to_keep)} entries")
    print(f"❌ Te verwijderen: {len(to_remove)} entries (circulaire definities)\n")
    
    if to_remove:
        print("📋 Te verwijderen entries (eerste 20):")
        for i, item in enumerate(to_remove[:20], 1):
            print(f"  {i}. '{item['begrip']}' → Laag1: \"{item['laag1']}\" (ID: {item['id']})")
        
        if len(to_remove) > 20:
            print(f"  ... en {len(to_remove) - 20} meer")
    
    if dry_run:
        print("\n⚠️  DRY RUN - Geen wijzigingen opgeslagen")
    else:
        print(f"\n💾 Opslaan gefilterde entries...")
        data["knowledge_entries"] = to_keep
        
        # Update metadata
        if "metadata" not in data:
            data["metadata"] = {}
        
        data["metadata"]["last_circular_cleanup"] = datetime.now().isoformat()
        data["metadata"]["circular_removed"] = len(to_remove)
        
        save_knowledge_base(kb_path, data)
        print(f"✅ Opgeslagen! {len(to_keep)} entries behouden")
    
    print("\n" + "="*80)
    print("📈 RESULTAAT")
    print("="*80)
    print(f"Voor cleanup:    {original_count} entries")
    print(f"Na cleanup:      {len(to_keep)} entries")
    print(f"Verwijderd:      {len(to_remove)} entries ({len(to_remove)/original_count*100:.1f}%)")
    
    return {
        'original': original_count,
        'kept': len(to_keep),
        'removed': len(to_remove)
    }

if __name__ == "__main__":
    kb_path = "/app/backend/data/learned_knowledge/knowledge_base.json"
    
    # Dry run eerst
    print("="*80)
    print("🧪 DRY RUN - Preview")
    print("="*80)
    cleanup_circular_definitions(kb_path, dry_run=True)
    
    print("\n\n" + "="*80)
    print("💥 ECHTE UITVOERING")
    print("="*80)
    print("Druk ENTER om door te gaan...")
    input()
    
    cleanup_circular_definitions(kb_path, dry_run=False)
    print("\n✅ Cleanup compleet!")
