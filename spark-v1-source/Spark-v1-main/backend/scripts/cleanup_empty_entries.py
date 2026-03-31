#!/usr/bin/env python3
"""
Knowledge Base Cleanup Script
Verwijdert ALLEEN lege entries (met lege lagen en/of geen begrip)
BEHOUDT alle duplicaten met verschillende topics (zoals Willem aangaf)
"""

import json
import sys
from datetime import datetime
from typing import Dict, List, Tuple

def load_knowledge_base(path: str) -> Dict:
    """Laad knowledge base JSON"""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_knowledge_base(path: str, data: Dict):
    """Sla knowledge base op"""
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def is_empty_entry(entry: Dict) -> Tuple[bool, str]:
    """
    Bepaal of een entry leeg is en waarom
    Returns: (is_leeg, reden)
    """
    begrip = entry.get("begrip", "").strip()
    lagen = entry.get("lagen", {})
    
    # Check 1: Geen begrip of begrip is leeg
    if not begrip:
        return True, "Geen begrip"
    
    # Check 2: Alle lagen zijn leeg
    if lagen:
        all_empty = all(
            not str(v).strip() 
            for v in lagen.values() 
            if v is not None
        )
        if all_empty:
            return True, "Alle lagen leeg"
    
    return False, ""

def cleanup_empty_entries(kb_path: str, dry_run: bool = False) -> Dict:
    """
    Verwijder lege entries uit knowledge base
    
    Args:
        kb_path: Path naar knowledge_base.json
        dry_run: Als True, toon alleen wat zou worden verwijderd
    
    Returns:
        Stats dict met resultaten
    """
    print(f"🔍 Laden knowledge base van {kb_path}...")
    data = load_knowledge_base(kb_path)
    entries = data.get("knowledge_entries", [])
    
    original_count = len(entries)
    print(f"📊 Origineel: {original_count} entries")
    
    # Filter lege entries
    print("\n🗑️  Identificeren lege entries...")
    to_remove = []
    to_keep = []
    removal_reasons = {}
    
    for entry in entries:
        is_empty, reason = is_empty_entry(entry)
        if is_empty:
            to_remove.append(entry)
            entry_id = entry.get("id", "unknown")
            begrip = entry.get("begrip", "(leeg)")
            removal_reasons[entry_id] = {
                "begrip": begrip,
                "reason": reason,
                "detected_by": entry.get("detected_by", "unknown")
            }
        else:
            to_keep.append(entry)
    
    print(f"✅ Te behouden: {len(to_keep)} entries")
    print(f"❌ Te verwijderen: {len(to_remove)} entries")
    
    # Toon eerste 10 entries die verwijderd worden
    print("\n📋 Eerste 10 te verwijderen entries:")
    for i, (entry_id, info) in enumerate(list(removal_reasons.items())[:10]):
        print(f"   {i+1}. '{info['begrip']}' - {info['reason']} (ID: {entry_id[:12]}...)")
    
    if len(to_remove) > 10:
        print(f"   ... en {len(to_remove) - 10} meer")
    
    # Uitvoeren of dry run
    if dry_run:
        print("\n⚠️  DRY RUN - Geen wijzigingen opgeslagen")
    else:
        print(f"\n💾 Opslaan gefilterde entries...")
        data["knowledge_entries"] = to_keep
        
        # Update metadata
        if "metadata" not in data:
            data["metadata"] = {}
        
        data["metadata"]["last_cleanup"] = datetime.now().isoformat()
        data["metadata"]["cleanup_removed"] = len(to_remove)
        data["metadata"]["cleanup_kept"] = len(to_keep)
        
        save_knowledge_base(kb_path, data)
        print(f"✅ Opgeslagen! {len(to_keep)} entries behouden")
    
    # Stats
    stats = {
        "original_count": original_count,
        "removed_count": len(to_remove),
        "kept_count": len(to_keep),
        "removal_reasons": removal_reasons
    }
    
    print("\n" + "="*70)
    print("📈 RESULTAAT")
    print("="*70)
    print(f"Voor cleanup:    {original_count} entries")
    print(f"Na cleanup:      {len(to_keep)} entries")
    print(f"Verwijderd:      {len(to_remove)} entries ({len(to_remove)/original_count*100:.1f}%)")
    print(f"File grootte:    ~{len(json.dumps(data, ensure_ascii=False))/1024:.1f} KB")
    
    return stats

def main():
    kb_path = "/app/backend/data/learned_knowledge/knowledge_base.json"
    
    # Eerst dry run om te controleren
    print("="*70)
    print("🧪 DRY RUN - Controleren wat verwijderd zou worden")
    print("="*70)
    cleanup_empty_entries(kb_path, dry_run=True)
    
    print("\n" + "="*70)
    print("💥 ECHTE UITVOERING")
    print("="*70)
    input("Druk op ENTER om door te gaan met verwijderen...")
    
    stats = cleanup_empty_entries(kb_path, dry_run=False)
    
    print("\n✅ Cleanup compleet!")
    return 0

if __name__ == "__main__":
    # Direct uitvoeren zonder confirmatie voor automatisering
    kb_path = "/app/backend/data/learned_knowledge/knowledge_base.json"
    stats = cleanup_empty_entries(kb_path, dry_run=False)
    sys.exit(0)
