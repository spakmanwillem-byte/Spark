#!/usr/bin/env python3
"""
Auto-sync knowledge_base.json → nodes.json on startup

Run this script to ensure graph is always in sync with master knowledge base
"""

from services.knowledge_to_graph_sync import KnowledgeToGraphSync
import sys


def main():
    """Sync knowledge base to graph"""
    print("🔄 Auto-syncing knowledge_base.json → nodes.json...")
    
    try:
        result = KnowledgeToGraphSync.sync_knowledge_to_graph(
            generate_edges=True,
            verbose=True
        )
        
        if result['success']:
            print("✅ Sync successful!")
            return 0
        else:
            print("❌ Sync failed!")
            return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
