"""
Knowledge Graph Quality Fixer
Eenmalig script om alle data quality issues op te lossen
"""
import json
import re
from pathlib import Path
from datetime import datetime

def extract_label_from_content(content):
    """
    Genereer een label uit de content
    
    Patronen:
    - "X is een Y" → "X (Y)"
    - "De X is een Y" → "X (Y)"
    - Anders: Eerste 5 woorden
    """
    if not content:
        return "Onbekend"
    
    # Clean content
    first_sentence = content.split('.')[0].strip()
    
    # Patroon 1: "X is een Y"
    match = re.search(r'^([A-Z]\w+(?:\s+\w+)?)\s+is\s+een\s+(.+?)(?:\s+die|\s+dat|$)', first_sentence, re.IGNORECASE)
    if match:
        term = match.group(1).strip()
        description = match.group(2).strip()
        # Shorten description
        desc_words = description.split()[:3]
        return f"{term} ({' '.join(desc_words)})"
    
    # Patroon 2: "Een X is een Y"
    match = re.search(r'^(?:Een|De)\s+([A-Z]\w+(?:\s+\w+)?)\s+is\s+(?:een\s+)?(.+?)(?:\s+die|\s+dat|$)', first_sentence, re.IGNORECASE)
    if match:
        term = match.group(1).strip()
        description = match.group(2).strip()
        desc_words = description.split()[:3]
        return f"{term} ({' '.join(desc_words)})"
    
    # Fallback: Eerste 5 woorden
    words = first_sentence.split()[:5]
    label = ' '.join(words)
    if len(label) > 50:
        label = label[:47] + "..."
    return label


def assign_gradatie_from_tags(tags):
    """
    Bepaal gradatie op basis van tags
    
    1 = Persoonlijk/Familie (hoogste vertrouwen)
    2-3 = Verified/Belangrijk
    4-5 = Algemene kennis
    6-7 = Ongecontroleerd
    """
    tags_lower = [t.lower() for t in tags]
    
    # Familie/Persoonlijk
    if any(tag in tags_lower for tag in ['familie', 'dochter', 'willem', 'persoon', 'lotus_spakman']):
        return 1
    
    # Roadkill/Community
    if any(tag in tags_lower for tag in ['roadkill', 'community', 'willem', 'biografie']):
        return 2
    
    # Verified/Wikipedia
    if any(tag in tags_lower for tag in ['wikipedia', 'verified', 'definitie']):
        return 3
    
    # Algemene kennis
    if any(tag in tags_lower for tag in ['algemeen', 'natuur', 'voedsel', 'auto']):
        return 4
    
    # User vragen/Notes
    if any(tag in tags_lower for tag in ['user-vraag', 'onbeantwoord', 'notitie']):
        return 5
    
    # Default
    return 4


def fix_lotus_cards(nodes):
    """
    Speciale behandeling voor Lotus kaarten
    """
    lotus_nodes = [n for n in nodes if any('lotus' in str(t).lower() for t in n.get('tags', []))]
    
    fixes = []
    for node in lotus_nodes:
        tags = [t.lower() for t in node.get('tags', [])]
        content = node.get('content', '').lower()
        
        # 1. Lotusbloem (waterplant)
        if 'bloem' in tags or 'waterplant' in tags:
            node['label'] = 'Lotusbloem (waterplant)'
            node['gradatie'] = 4
            fixes.append(f"✅ Lotusbloem: label + gradatie 4")
        
        # 2. Lotus (automerk)
        elif 'auto' in tags or 'sportwagen' in tags:
            node['label'] = 'Lotus (automerk)'
            node['gradatie'] = 4
            fixes.append(f"✅ Lotus auto: label + gradatie 4")
        
        # 3. Lotus koekjes
        elif 'koekje' in tags or 'snack' in tags:
            node['label'] = 'Lotus koekjes (Biscoff)'
            node['gradatie'] = 4
            fixes.append(f"✅ Lotus koekjes: label + gradatie 4")
        
        # 4. Lotus (voornaam - DOCHTER!)
        elif 'naam' in tags or 'voornaam' in tags:
            node['label'] = 'Lotus Spakman (dochter Willem)'
            node['gradatie'] = 1  # Familie = hoogste vertrouwen
            # Add extra tags
            if 'familie' not in node['tags']:
                node['tags'].append('familie')
            if 'dochter' not in node['tags']:
                node['tags'].append('dochter')
            if 'lotus_spakman' not in node['tags']:
                node['tags'].append('lotus_spakman')
            fixes.append(f"✅ Lotus dochter: label + gradatie 1 + familie tags")
    
    return fixes


def fix_all_nodes(nodes_file):
    """
    Fix alle nodes in het graph
    """
    print("🔧 Loading nodes...")
    with open(nodes_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    nodes = data.get('nodes', [])
    print(f"📊 Total nodes: {len(nodes)}\n")
    
    # Statistics
    stats = {
        'no_label': 0,
        'no_gradatie': 0,
        'no_creator': 0,
        'fixed_labels': 0,
        'fixed_gradaties': 0,
        'lotus_fixes': 0
    }
    
    # Fix Lotus first (special case)
    print("🌸 Fixing Lotus cards...")
    lotus_fixes = fix_lotus_cards(nodes)
    stats['lotus_fixes'] = len(lotus_fixes)
    for fix in lotus_fixes:
        print(f"  {fix}")
    print()
    
    # Fix all other nodes
    print("🔧 Fixing all nodes...")
    for node in nodes:
        # Count issues
        if not node.get('label') or node.get('label') == 'None':
            stats['no_label'] += 1
        if not node.get('gradatie') or node.get('gradatie') == 'None':
            stats['no_gradatie'] += 1
        if not node.get('created_by_user_id') or node.get('created_by_user_id') == 'unknown':
            stats['no_creator'] += 1
        
        # Fix label
        if not node.get('label') or node.get('label') == 'None':
            content = node.get('content', '')
            if content:
                node['label'] = extract_label_from_content(content)
                stats['fixed_labels'] += 1
            else:
                # Fallback: use first tag
                tags = node.get('tags', [])
                if tags:
                    node['label'] = tags[0].capitalize()
                    stats['fixed_labels'] += 1
                else:
                    node['label'] = f"Node {node.get('id', 'unknown')[:8]}"
        
        # Fix gradatie
        if not node.get('gradatie') or node.get('gradatie') == 'None':
            tags = node.get('tags', [])
            node['gradatie'] = assign_gradatie_from_tags(tags)
            stats['fixed_gradaties'] += 1
        
        # Fix creator (default to system if unknown)
        if not node.get('created_by_user_id') or node.get('created_by_user_id') == 'unknown':
            node['created_by_user_id'] = 'system'
    
    # Update metadata
    if 'metadata' not in data:
        data['metadata'] = {}
    data['metadata']['last_quality_check'] = datetime.utcnow().isoformat()
    data['metadata']['quality_fixes_applied'] = stats
    
    # Save
    print(f"\n💾 Saving fixed nodes...")
    with open(nodes_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    # Report
    print(f"\n✅ QUALITY FIX COMPLETE!\n")
    print(f"📊 Statistics:")
    print(f"  - Nodes without label: {stats['no_label']}")
    print(f"  - Nodes without gradatie: {stats['no_gradatie']}")
    print(f"  - Nodes without creator: {stats['no_creator']}")
    print(f"\n🔧 Fixed:")
    print(f"  - Labels generated: {stats['fixed_labels']}")
    print(f"  - Gradaties assigned: {stats['fixed_gradaties']}")
    print(f"  - Lotus cards fixed: {stats['lotus_fixes']}")
    print(f"\n💚 All {len(nodes)} nodes now have proper labels and gradaties!")


if __name__ == "__main__":
    nodes_file = Path("/app/backend/data/graph/nodes.json")
    fix_all_nodes(nodes_file)
