#!/usr/bin/env python3
"""
Cleanup script: Remove 'gradatie' field from all knowledge cards
Gradatie is ONLY for users (relatie tot Willem), NOT for cards!
Cards only have 'metadata.belangrijkheid' (rating 1-10)
"""

import json
from datetime import datetime

def cleanup_gradatie_from_nodes():
    """Remove gradatie field from all nodes in nodes.json"""
    
    nodes_file = '/app/backend/data/graph/nodes.json'
    
    # Load current data
    with open(nodes_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    nodes = data.get('nodes', [])
    
    print(f"🔍 Scanning {len(nodes)} nodes...")
    
    removed_count = 0
    for node in nodes:
        if 'gradatie' in node:
            del node['gradatie']
            removed_count += 1
    
    print(f"✅ Removed 'gradatie' from {removed_count} nodes")
    
    # Save cleaned data
    with open(nodes_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"💾 Saved cleaned data to {nodes_file}")
    
    # Verify
    with open(nodes_file, 'r', encoding='utf-8') as f:
        verify_data = json.load(f)
    
    remaining = sum(1 for n in verify_data.get('nodes', []) if 'gradatie' in n)
    print(f"\n📊 Verification: {remaining} nodes still have 'gradatie' (should be 0)")
    
    if remaining == 0:
        print("✅ CLEANUP SUCCESSFUL!")
    else:
        print("⚠️ WARNING: Some nodes still have gradatie field")
    
    return removed_count

if __name__ == "__main__":
    print("=" * 60)
    print("CLEANUP: Remove 'gradatie' from Knowledge Cards")
    print("=" * 60)
    print()
    
    removed = cleanup_gradatie_from_nodes()
    
    print()
    print("=" * 60)
    print(f"DONE: Cleaned {removed} nodes")
    print("=" * 60)
