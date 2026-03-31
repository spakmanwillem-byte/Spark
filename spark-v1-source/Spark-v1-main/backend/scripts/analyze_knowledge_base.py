#!/usr/bin/env python3
"""
Knowledge Base Analyzer
Analyseert de knowledge_base.json voor:
- Lege entries (zonder betekenisvolle content)
- Duplicaten (rekening houdend met topic/context verschillen)
- Statistieken
"""

import json
import sys
from collections import defaultdict
from typing import Dict, List, Tuple

def load_knowledge_base(path: str) -> Dict:
    """Laad knowledge base JSON"""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def is_empty_entry(entry: Dict) -> Tuple[bool, str]:
    """
    Bepaal of een entry leeg is en waarom
    Returns: (is_leeg, reden)
    """
    begrip = entry.get("begrip", "").strip()
    lagen = entry.get("lagen", {})
    
    # Check 1: Geen begrip
    if not begrip:
        return True, "Geen begrip"
    
    # Check 2: Alle lagen leeg
    if lagen:
        all_empty = all(
            not str(v).strip() 
            for v in lagen.values() 
            if v is not None
        )
        if all_empty:
            return True, "Alle lagen leeg"
    
    # Check 3: Stopword of zinloos
    stopwords = ["de", "het", "een", "en", "van", "in", "op", "is"]
    if begrip.lower() in stopwords:
        return True, f"Stopword: {begrip}"
    
    return False, ""

def find_duplicates(entries: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Vind duplicaten, maar groepeer ze op begrip + topic/context
    Willem's waarschuwing: "pas op bubbel kan wel andere topic hebben"
    
    Returns: Dict met begrip als key, list van entries met dat begrip
    """
    duplicates = defaultdict(list)
    
    for entry in entries:
        begrip = entry.get("begrip", "").strip().lower()
        if begrip:
            duplicates[begrip].append(entry)
    
    # Filter alleen begrippen die >1 keer voorkomen
    return {k: v for k, v in duplicates.items() if len(v) > 1}

def categorize_duplicates(dup_entries: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Categoriseer duplicaten:
    - identical: 100% hetzelfde (begrip + topic + laag1)
    - different_topic: Zelfde begrip, maar ander topic/context
    - similar: Zelfde begrip, vergelijkbare content
    """
    if len(dup_entries) < 2:
        return {}
    
    result = {
        "identical": [],
        "different_topic": [],
        "similar": []
    }
    
    # Vergelijk eerste entry met de rest
    base = dup_entries[0]
    base_topic = base.get("topic", "").strip().lower()
    base_laag1 = base.get("lagen", {}).get("laag1", "").strip().lower()
    base_context = base.get("snap_context", "").strip().lower()
    
    for entry in dup_entries[1:]:
        entry_topic = entry.get("topic", "").strip().lower()
        entry_laag1 = entry.get("lagen", {}).get("laag1", "").strip().lower()
        entry_context = entry.get("snap_context", "").strip().lower()
        
        # 100% identiek?
        if (entry_topic == base_topic and 
            entry_laag1 == base_laag1 and 
            entry_context == base_context):
            result["identical"].append(entry)
        # Ander topic?
        elif entry_topic != base_topic or entry_context != base_context:
            result["different_topic"].append(entry)
        else:
            result["similar"].append(entry)
    
    return result

def main():
    kb_path = "/app/backend/data/learned_knowledge/knowledge_base.json"
    
    print("🔍 Laden knowledge base...")
    data = load_knowledge_base(kb_path)
    entries = data.get("knowledge_entries", [])
    
    total = len(entries)
    print(f"📊 Totaal entries: {total}")
    
    # Analyseer lege entries
    print("\n🗑️  Analyseren lege entries...")
    empty_entries = []
    empty_reasons = defaultdict(int)
    
    for entry in entries:
        is_empty, reason = is_empty_entry(entry)
        if is_empty:
            empty_entries.append(entry)
            empty_reasons[reason] += 1
    
    print(f"   Gevonden: {len(empty_entries)} lege entries")
    for reason, count in empty_reasons.items():
        print(f"     - {reason}: {count}")
    
    # Analyseer duplicaten
    print("\n🔄 Analyseren duplicaten...")
    duplicates = find_duplicates(entries)
    
    print(f"   Gevonden: {len(duplicates)} begrippen met duplicaten")
    
    total_identical = 0
    total_different_topic = 0
    total_similar = 0
    
    print("\n📋 Top 10 duplicaten:")
    for i, (begrip, dup_entries) in enumerate(list(duplicates.items())[:10]):
        categories = categorize_duplicates(dup_entries)
        identical = len(categories.get("identical", []))
        different = len(categories.get("different_topic", []))
        similar = len(categories.get("similar", []))
        
        total_identical += identical
        total_different_topic += different
        total_similar += similar
        
        print(f"\n   {i+1}. '{begrip}' ({len(dup_entries)} keer)")
        print(f"      - 100% identiek: {identical}")
        print(f"      - Ander topic/context: {different} ⚠️ NIET VERWIJDEREN")
        print(f"      - Vergelijkbaar: {similar}")
        
        # Toon topics van eerste 3 entries
        for j, entry in enumerate(dup_entries[:3]):
            topic = entry.get("topic", "(geen)")
            context = entry.get("snap_context", "")[:50]
            print(f"        [{j+1}] Topic: {topic}, Context: {context}...")
    
    # Samenvatting
    print("\n" + "="*70)
    print("📈 SAMENVATTING")
    print("="*70)
    print(f"Totaal entries:              {total}")
    print(f"Lege entries:                {len(empty_entries)} ({len(empty_entries)/total*100:.1f}%)")
    print(f"Begrippen met duplicaten:    {len(duplicates)}")
    print(f"  - 100% identiek (veilig):  {total_identical}")
    print(f"  - Ander topic (BEWAREN):   {total_different_topic} ⚠️")
    print(f"  - Vergelijkbaar:           {total_similar}")
    
    print("\n💡 AANBEVELINGEN:")
    print(f"1. Verwijder {len(empty_entries)} lege entries")
    print(f"2. Verwijder {total_identical} 100% identieke duplicaten")
    print(f"3. BEWAAR {total_different_topic} entries met ander topic/context")
    print(f"4. Review handmatig {total_similar} vergelijkbare entries")
    
    potential_savings = len(empty_entries) + total_identical
    new_size = total - potential_savings
    print(f"\n📉 Geschatte reductie: {total} → {new_size} entries ({potential_savings} verwijderd)")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
