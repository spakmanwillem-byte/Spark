"""
Knowledge Card Analysis Script
Analyseert alle knowledge cards voor:
- Triggers (vraagvormen voor learning modules)
- Relaties tussen kaarten
- Clusters/thema's
- Leertriggers
"""
import json
import re
from collections import defaultdict, Counter
from datetime import datetime

# Load knowledge base
with open('/app/backend/data/learned_knowledge/knowledge_base.json', 'r') as f:
    kb = json.load(f)

entries = kb.get('knowledge_entries', [])
active_entries = [e for e in entries if e.get('status') != 'trash']

print(f"📊 Analyzing {len(active_entries)} active knowledge cards...")

# ============= TRIGGER DETECTION =============
print("\n1️⃣ TRIGGER DETECTION (Learning Module Candidates)")
print("=" * 60)

trigger_patterns = {
    'question_direct': [
        r'^wat weet (je|jij) (over|van)',
        r'^wat is',
        r'^leg uit',
        r'^vertel (over|van)',
        r'^beschrijf',
        r'^hoe werkt',
        r'^waarom',
        r'^waarvoor dient',
        r'^kun je uitleggen',
    ],
    'question_implicit': [
        r'\?$',  # Ends with question mark
    ],
    'definition_request': [
        r'^definitie van',
        r'^betekenis van',
        r'^uitleg over',
    ]
}

triggers_found = {
    'question_direct': [],
    'question_implicit': [],
    'definition_request': [],
    'no_trigger': []
}

for entry in active_entries:
    begrip = entry.get('begrip', '').lower()
    found_trigger = False
    
    for trigger_type, patterns in trigger_patterns.items():
        for pattern in patterns:
            if re.search(pattern, begrip, re.IGNORECASE):
                triggers_found[trigger_type].append({
                    'id': entry.get('id'),
                    'begrip': entry.get('begrip'),
                    'pattern': pattern,
                    'heeft_antwoord': bool(entry.get('lagen', {}).get('laag1'))
                })
                found_trigger = True
                break
        if found_trigger:
            break
    
    if not found_trigger:
        triggers_found['no_trigger'].append(entry)

print(f"✅ Directe vragen: {len(triggers_found['question_direct'])}")
print(f"✅ Impliciete vragen (eindigt met ?): {len(triggers_found['question_implicit'])}")
print(f"✅ Definitie verzoeken: {len(triggers_found['definition_request'])}")
print(f"📚 Normale knowledge cards: {len(triggers_found['no_trigger'])}")

total_triggers = len(triggers_found['question_direct']) + len(triggers_found['question_implicit']) + len(triggers_found['definition_request'])
print(f"\n🎯 **{total_triggers} kaarten geschikt voor Learning Module** ({(total_triggers/len(active_entries)*100):.1f}%)")

# Show examples
print("\n📝 Voorbeelden van triggers:")
for trigger_type in ['question_direct', 'question_implicit', 'definition_request']:
    if triggers_found[trigger_type]:
        print(f"\n{trigger_type}:")
        for item in triggers_found[trigger_type][:3]:
            status = "✅ Beantwoord" if item['heeft_antwoord'] else "❌ Nog geen antwoord"
            print(f"  - {item['begrip']} ({status})")


# ============= RELATIES & CLUSTERING =============
print("\n\n2️⃣ RELATIES TUSSEN KAARTEN")
print("=" * 60)

# Tag-based clustering
tag_counter = Counter()
tag_to_cards = defaultdict(list)

for entry in active_entries:
    tags = entry.get('tags', [])
    for tag in tags:
        tag_counter[tag] += 1
        tag_to_cards[tag].append(entry.get('begrip'))

print(f"📊 Totaal unieke tags: {len(tag_counter)}")
print(f"\n🏆 Top 20 meest gebruikte tags:")
for tag, count in tag_counter.most_common(20):
    print(f"  {tag}: {count} kaarten")

# Concept overlap (begrippen in definities)
concept_mentions = defaultdict(list)
begrippen_set = {e.get('begrip').lower() for e in active_entries}

print("\n\n🔗 Concept Overlap Detectie...")
for entry in active_entries:
    begrip = entry.get('begrip')
    laag1 = entry.get('lagen', {}).get('laag1', '').lower()
    laag2 = entry.get('lagen', {}).get('laag2', '').lower()
    laag3 = entry.get('lagen', {}).get('laag3', '').lower()
    
    all_text = f"{laag1} {laag2} {laag3}"
    
    # Check if other begrippen are mentioned
    for other_begrip in begrippen_set:
        if other_begrip != begrip.lower() and len(other_begrip) > 3:  # Skip short words
            if other_begrip in all_text:
                concept_mentions[begrip].append(other_begrip)

# Show cards with most connections
connected_cards = [(k, v) for k, v in concept_mentions.items() if len(v) > 0]
connected_cards.sort(key=lambda x: len(x[1]), reverse=True)

print(f"✅ {len(connected_cards)} kaarten hebben concept overlap")
print(f"\n🔗 Top 10 meest verbonden kaarten:")
for begrip, mentions in connected_cards[:10]:
    print(f"  {begrip}: {len(mentions)} verbindingen")
    print(f"    → {', '.join(list(set(mentions))[:5])}")


# ============= THEMA CLUSTERING =============
print("\n\n3️⃣ THEMA CLUSTERING")
print("=" * 60)

# Cluster by tags (cards with same tags)
clusters = []
for tag, count in tag_counter.most_common(30):
    if count >= 3:  # Only clusters with 3+ cards
        cluster_cards = tag_to_cards[tag]
        clusters.append({
            'theme': tag,
            'size': count,
            'cards': cluster_cards[:10]  # First 10
        })

print(f"🎨 Gevonden clusters (>= 3 kaarten): {len(clusters)}")
print(f"\n🏷️ Grootste thema clusters:")
for cluster in clusters[:15]:
    print(f"\n  📁 {cluster['theme']} ({cluster['size']} kaarten)")
    for card in cluster['cards'][:5]:
        print(f"     - {card}")


# ============= IMPORTANCE ANALYSIS =============
print("\n\n4️⃣ BELANGRIJKHEID ANALYSE (Sterren)")
print("=" * 60)

importance_dist = defaultdict(int)
for entry in active_entries:
    importance = entry.get('belangrijkheid', 0)
    importance_dist[importance] += 1

print("⭐ Distributie van sterren:")
for i in range(11):
    count = importance_dist.get(i, 0)
    percentage = (count / len(active_entries) * 100) if len(active_entries) > 0 else 0
    bar = "█" * int(percentage / 2)
    print(f"  {i:2d} ⭐: {count:4d} kaarten ({percentage:5.1f}%) {bar}")

# High importance cards
high_importance = [e for e in active_entries if e.get('belangrijkheid', 0) >= 8]
print(f"\n🌟 Zeer belangrijke kaarten (8-10 sterren): {len(high_importance)}")
for entry in high_importance[:10]:
    print(f"  - {entry.get('begrip')} ({entry.get('belangrijkheid')}⭐)")


# ============= LAGEN COMPLETENESS =============
print("\n\n5️⃣ LAGEN COMPLETENESS")
print("=" * 60)

laag_stats = {
    'laag1': 0,
    'laag2': 0,
    'laag3': 0,
    'all_three': 0,
    'none': 0
}

for entry in active_entries:
    lagen = entry.get('lagen', {})
    has_laag1 = bool(lagen.get('laag1'))
    has_laag2 = bool(lagen.get('laag2'))
    has_laag3 = bool(lagen.get('laag3'))
    
    if has_laag1: laag_stats['laag1'] += 1
    if has_laag2: laag_stats['laag2'] += 1
    if has_laag3: laag_stats['laag3'] += 1
    if has_laag1 and has_laag2 and has_laag3: laag_stats['all_three'] += 1
    if not (has_laag1 or has_laag2 or has_laag3): laag_stats['none'] += 1

print(f"📊 Laag 1 (Basis): {laag_stats['laag1']} kaarten ({laag_stats['laag1']/len(active_entries)*100:.1f}%)")
print(f"📊 Laag 2 (Dieper): {laag_stats['laag2']} kaarten ({laag_stats['laag2']/len(active_entries)*100:.1f}%)")
print(f"📊 Laag 3 (Expert): {laag_stats['laag3']} kaarten ({laag_stats['laag3']/len(active_entries)*100:.1f}%)")
print(f"✅ Alle 3 lagen: {laag_stats['all_three']} kaarten ({laag_stats['all_three']/len(active_entries)*100:.1f}%)")
print(f"❌ Geen lagen: {laag_stats['none']} kaarten ({laag_stats['none']/len(active_entries)*100:.1f}%)")


# ============= LEARNING MODULE RECOMMENDATIONS =============
print("\n\n6️⃣ LEARNING MODULE AANBEVELINGEN")
print("=" * 60)

learning_candidates = []
for entry in active_entries:
    # Check if suitable for learning
    is_trigger = entry in [t['id'] for trigger_list in triggers_found.values() for t in trigger_list if isinstance(t, dict)]
    heeft_antwoord = bool(entry.get('lagen', {}).get('laag1'))
    importance = entry.get('belangrijkheid', 0)
    
    if heeft_antwoord and importance >= 5:
        learning_candidates.append({
            'begrip': entry.get('begrip'),
            'importance': importance,
            'is_trigger': is_trigger,
            'has_layers': bool(entry.get('lagen', {}).get('laag2')),
            'tags': entry.get('tags', [])
        })

learning_candidates.sort(key=lambda x: x['importance'], reverse=True)

print(f"🎓 Geschikt voor Learning Module: {len(learning_candidates)} kaarten")
print(f"\n🌟 Top 20 learning candidates (hoge importance + antwoord):")
for idx, card in enumerate(learning_candidates[:20], 1):
    layers = "✓ Meerdere lagen" if card['has_layers'] else "○ Alleen basis"
    trigger = "❓ Vraag" if card['is_trigger'] else "📚 Kennis"
    print(f"  {idx:2d}. {card['begrip']} ({card['importance']}⭐) - {trigger} - {layers}")


# ============= SAVE RESULTS =============
print("\n\n💾 SAVING ANALYSIS RESULTS...")
print("=" * 60)

results = {
    'metadata': {
        'analyzed_at': datetime.now().isoformat(),
        'total_cards': len(active_entries),
        'total_triggers': total_triggers,
        'total_clusters': len(clusters)
    },
    'triggers': {
        'question_direct': [{'begrip': t['begrip'], 'heeft_antwoord': t['heeft_antwoord']} for t in triggers_found['question_direct']],
        'question_implicit': [{'begrip': t['begrip'], 'heeft_antwoord': t['heeft_antwoord']} for t in triggers_found['question_implicit']],
        'definition_request': [{'begrip': t['begrip'], 'heeft_antwoord': t['heeft_antwoord']} for t in triggers_found['definition_request']],
    },
    'top_tags': [{'tag': tag, 'count': count} for tag, count in tag_counter.most_common(50)],
    'clusters': clusters,
    'connected_cards': [{'begrip': k, 'connections': len(v)} for k, v in connected_cards[:50]],
    'learning_candidates': learning_candidates[:100],
    'importance_distribution': dict(importance_dist),
    'laag_stats': laag_stats
}

with open('/app/KNOWLEDGE_ANALYSIS_REPORT.json', 'w') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print("✅ Results saved to: /app/KNOWLEDGE_ANALYSIS_REPORT.json")
print("\n✅ ANALYSIS COMPLETE!")
