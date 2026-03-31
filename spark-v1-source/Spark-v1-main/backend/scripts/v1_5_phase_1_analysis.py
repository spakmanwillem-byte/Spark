#!/usr/bin/env python3
"""
v1.5 Phase 1: Multi-Topic Analysis & Resolution Strategy
Doel: Analyseer multi-topic entries en stel strategie voor
"""

import json
from pathlib import Path
from collections import defaultdict

KB_PATH = Path('/app/backend/data/learned_knowledge/knowledge_base.json')

def load_kb():
    with open(KB_PATH, 'r') as f:
        return json.load(f)

def analyze_multi_topic_entries(kb_data):
    """Analyseer entries met multiple topics"""
    
    print("\n" + "="*70)
    print("📊 MULTI-TOPIC ANALYSE")
    print("="*70)
    print("Filosofie: Structuur toevoegen, niet verwijderen")
    print("="*70)
    
    entries = kb_data.get('knowledge_entries', [])
    
    # Find entries met multiple topics (/ separator)
    multi_topic = []
    for entry in entries:
        topic = entry.get('topic', '')
        if '/' in topic or ' / ' in topic:
            multi_topic.append(entry)
    
    print(f"\n📈 Gevonden: {len(multi_topic)} entries met multi-topic")
    
    # Categorize by pattern
    patterns = defaultdict(list)
    for entry in multi_topic:
        topic = entry.get('topic', '')
        # Normalize separators
        normalized = topic.replace(' / ', '/').replace('/ ', '/').replace(' /', '/')
        parts = [p.strip() for p in normalized.split('/')]
        pattern = ' / '.join(parts)
        patterns[pattern].append(entry)
    
    print(f"\n📋 Unieke topic patterns: {len(patterns)}")
    print(f"\nTop 10 meest voorkomende patterns:")
    
    sorted_patterns = sorted(patterns.items(), key=lambda x: len(x[1]), reverse=True)
    for i, (pattern, entries_list) in enumerate(sorted_patterns[:10], 1):
        print(f"   {i}. '{pattern}': {len(entries_list)} entries")
        # Show example
        example = entries_list[0]
        print(f"      Voorbeeld: '{example.get('begrip', 'N/A')}'")
    
    return multi_topic, patterns

def propose_resolution_strategy(multi_topic, patterns):
    """Stel strategie voor om multi-topics op te lossen"""
    
    print("\n" + "="*70)
    print("💡 RESOLUTION STRATEGIE")
    print("="*70)
    
    print("""
Probleem: 502 entries met topic "A / B / C"

Huidige situatie:
  topic: "technologie / techniek"
  
Gewenste situatie:
  primary_topic: "technologie"
  related_topics: ["techniek"]
  tags: ["technologie", "techniek"]
  
Voordelen:
  ✅ Duidelijk primary topic voor categorisatie
  ✅ Related topics behouden context
  ✅ Tags voor search/filter
  ✅ Geen data verloren
  
Implementatie:
  1. Parse topic string → split op '/'
  2. Eerste = primary_topic
  3. Rest → related_topics
  4. Alle delen → tags (indien nog niet aanwezig)
  5. Origineel topic behouden in metadata.original_topic
""")
    
    # Sample transformation
    print("\n📋 VOORBEELD TRANSFORMATIE:")
    if multi_topic:
        sample = multi_topic[0]
        topic = sample.get('topic', '')
        parts = [p.strip() for p in topic.replace(' / ', '/').split('/')]
        
        print(f"\nEntry: '{sample.get('begrip')}'")
        print(f"\n   VOOR:")
        print(f"      topic: '{topic}'")
        print(f"      tags: {sample.get('tags', [])}")
        
        print(f"\n   NA:")
        print(f"      primary_topic: '{parts[0]}'")
        print(f"      related_topics: {parts[1:]}")
        
        # Merge with existing tags
        existing_tags = sample.get('tags', [])
        new_tags = list(set(existing_tags + parts))
        print(f"      tags: {new_tags}")
        print(f"      metadata.original_topic: '{topic}' (preserved)")
    
    return {
        'strategy': 'split_and_preserve',
        'primary_topic': 'first',
        'related_topics': 'rest',
        'tags': 'all_parts',
        'preserve': 'original_topic in metadata'
    }

def analyze_tag_coverage(kb_data):
    """Analyseer huidige tag coverage"""
    
    print("\n" + "="*70)
    print("🏷️  TAG COVERAGE ANALYSE")
    print("="*70)
    
    entries = kb_data.get('knowledge_entries', [])
    
    with_tags = sum(1 for e in entries if e.get('tags'))
    without_tags = len(entries) - with_tags
    
    print(f"\n📊 Status:")
    print(f"   • Met tags: {with_tags} ({with_tags/len(entries)*100:.1f}%)")
    print(f"   • Zonder tags: {without_tags} ({without_tags/len(entries)*100:.1f}%)")
    
    # Unique tags
    all_tags = set()
    tag_frequency = defaultdict(int)
    
    for entry in entries:
        tags = entry.get('tags', [])
        if isinstance(tags, list):
            for tag in tags:
                all_tags.add(tag)
                tag_frequency[tag] += 1
    
    print(f"\n   • Unieke tags: {len(all_tags)}")
    print(f"\n   Top 15 meest gebruikte tags:")
    
    sorted_tags = sorted(tag_frequency.items(), key=lambda x: x[1], reverse=True)
    for i, (tag, count) in enumerate(sorted_tags[:15], 1):
        print(f"      {i}. '{tag}': {count} entries")
    
    return {
        'with_tags': with_tags,
        'without_tags': without_tags,
        'unique_tags': len(all_tags),
        'top_tags': sorted_tags[:15]
    }

def propose_tag_system():
    """Stel tag systeem voor"""
    
    print("\n" + "="*70)
    print("🏷️  TAG SYSTEEM VOORSTEL")
    print("="*70)
    
    print("""
Doel: Structuur toevoegen zonder data te verwijderen

Tag Hiërarchie:
  
  1. AUTO-TAGS (van topic/begrip afgeleid)
     - Automatisch toegevoegd bij save
     - Voorkomt lege tags
     
  2. MANUAL TAGS (door gebruiker toegevoegd)
     - Behouden en gerespecteerd
     
  3. SYSTEM TAGS (generated)
     - knowledge-snap, auto-generated, etc.
     - Technische metadata
     
  4. CATEGORY TAGS (van thema's)
     - technologie, persoonlijk, werk, etc.
     - Afgeleide categorieën

Tag Types:
  - content_tags: wat (technologie, filosofie)
  - context_tags: waarom/wanneer (werk, privé)  
  - relation_tags: wie/waar (persoon, locatie)
  - system_tags: hoe (auto-generated, snap)

Tag Rules:
  ✅ Tags toevoegen = altijd OK
  ✅ Bestaande tags behouden
  ✅ Duplicaten verwijderen (cleanup)
  ❌ Tags verwijderen = niet doen (tenzij duplicaat)
  
Implementation:
  - tag_suggestions: Voorgestelde tags obv content
  - tag_confidence: Hoe zeker zijn we (0.0-1.0)
  - tag_source: Waar komt tag vandaan (auto/manual/system)
""")

def main():
    print("🚀 v1.5 INTELLIGENT KNOWLEDGE SYSTEM")
    print("="*70)
    print("Phase 1: Multi-Topic Analysis & Tag System")
    print("="*70)
    
    kb_data = load_kb()
    entries_count = len(kb_data.get('knowledge_entries', []))
    print(f"\n✅ Loaded KB: {entries_count} entries")
    
    # Analyze multi-topic
    multi_topic, patterns = analyze_multi_topic_entries(kb_data)
    
    # Propose resolution
    strategy = propose_resolution_strategy(multi_topic, patterns)
    
    # Analyze tags
    tag_stats = analyze_tag_coverage(kb_data)
    
    # Propose tag system
    propose_tag_system()
    
    print("\n" + "="*70)
    print("✅ ANALYSE VOLTOOID")
    print("="*70)
    print(f"\n📊 Samenvatting:")
    print(f"   • Multi-topic entries: {len(multi_topic)}")
    print(f"   • Unieke patterns: {len(patterns)}")
    print(f"   • Entries met tags: {tag_stats['with_tags']}")
    print(f"   • Entries zonder tags: {tag_stats['without_tags']}")
    print(f"   • Unieke tags: {tag_stats['unique_tags']}")
    print(f"\n💡 Strategie: {strategy['strategy']}")
    print(f"   • Primary topic: {strategy['primary_topic']}")
    print(f"   • Related topics: {strategy['related_topics']}")
    print(f"   • Tags: {strategy['tags']}")
    print(f"   • Preserve: {strategy['preserve']}")
    print("\n🎯 Next: Implementeer multi-topic resolution + tag system")
    print("="*70)

if __name__ == '__main__':
    main()
