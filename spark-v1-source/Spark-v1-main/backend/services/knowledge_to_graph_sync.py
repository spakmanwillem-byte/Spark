"""
Knowledge to Graph Sync Service

Synchroniseert knowledge_base.json (master) naar nodes.json (graph representation)

Architecture:
- knowledge_base.json = MASTER database met lagen structuur
- nodes.json = AFGELEIDE graph voor visualisatie en queries

Dit script:
1. Leest knowledge_base.json
2. Converteert elke entry naar een graph node
3. Behoudt: begrip, lagen, tags, belangrijkheid
4. Genereert edges op basis van shared tags
5. Schrijft naar nodes.json
"""

import json
from datetime import datetime
from typing import List, Dict, Set, Tuple
import re


class KnowledgeToGraphSync:
    """Sync knowledge_base.json → nodes.json"""
    
    KB_PATH = "/app/backend/data/learned_knowledge/knowledge_base.json"
    NODES_PATH = "/app/backend/data/graph/nodes.json"
    EDGES_PATH = "/app/backend/data/graph/edges.json"
    METADATA_PATH = "/app/backend/data/graph/metadata.json"
    
    @staticmethod
    def load_knowledge_base() -> List[Dict]:
        """Load master knowledge base"""
        with open(KnowledgeToGraphSync.KB_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('knowledge_entries', [])
    
    @staticmethod
    def convert_kb_entry_to_node(entry: Dict) -> Dict:
        """
        Convert knowledge_base entry to graph node
        
        Behoudt:
        - ID
        - begrip → label
        - lagen (laag1, laag2, laag3, laag4)
        - tags
        - belangrijkheid
        - metadata
        """
        node_id = entry.get('id')
        begrip = entry.get('begrip', 'Onbekend')
        lagen = entry.get('lagen', {})
        tags = entry.get('tags', [])
        belangrijkheid = entry.get('belangrijkheid', 5)
        
        # Build description from lagen
        # Laag1 = korte beschrijving, Laag3 = uitgebreide beschrijving
        description = lagen.get('laag3') or lagen.get('laag2') or lagen.get('laag1', '')
        
        # Short description for previews
        short_desc = lagen.get('laag1', '')
        
        node = {
            'id': node_id,
            'label': begrip,
            'type': 'knowledge',
            'description': description,
            'short_description': short_desc,
            'lagen': lagen,  # Behoud alle lagen
            'tags': tags,
            'metadata': {
                'belangrijkheid': belangrijkheid,
                'source': 'knowledge_base',
                'created_at': entry.get('created_at', ''),
                'created_by': entry.get('created_by_user_id', ''),
                'usage_count': entry.get('usage_count', 0),
                'last_used': entry.get('last_used', ''),
                'status': entry.get('status', 'active')
            }
        }
        
        # Add ws5 if present
        if entry.get('ws5'):
            node['ws5'] = entry.get('ws5')
        
        # Add topic if present
        if entry.get('topic'):
            node['metadata']['topic'] = entry.get('topic')
        
        return node
    
    @staticmethod
    def generate_edges_from_tags(nodes: List[Dict]) -> List[Dict]:
        """
        Generate edges between nodes based on shared tags
        
        EXCLUDES meta tags: knowledge-snap, auto-generated
        
        Logic:
        - Nodes met 2+ shared tags krijgen een edge (strength = aantal shared tags)
        - Max 10 edges per node (belangrijkste verbindingen)
        """
        edges = []
        edge_id_counter = 0
        
        # Meta tags die NIET gebruikt worden voor edge generation
        META_TAGS = {'knowledge-snap', 'auto-generated'}
        
        # Build tag index: tag -> [node_ids] (excluding meta tags)
        tag_index = {}
        for node in nodes:
            node_id = node['id']
            for tag in node.get('tags', []):
                # Skip meta tags
                if tag in META_TAGS:
                    continue
                    
                if tag not in tag_index:
                    tag_index[tag] = []
                tag_index[tag].append(node_id)
        
        # For each node, find related nodes via shared tags
        processed_pairs = set()
        
        # Meta tags die NIET gebruikt worden voor edge generation
        META_TAGS = {'knowledge-snap', 'auto-generated'}
        
        for node in nodes:
            node_id = node['id']
            # Filter out meta tags
            node_tags = set(tag for tag in node.get('tags', []) if tag not in META_TAGS)
            
            # Find all nodes that share tags
            related_nodes = {}  # {related_node_id: shared_tag_count}
            
            for tag in node_tags:
                for related_id in tag_index.get(tag, []):
                    if related_id == node_id:
                        continue
                    
                    if related_id not in related_nodes:
                        related_nodes[related_id] = 0
                    related_nodes[related_id] += 1
            
            # Create edges for nodes with 2+ shared tags
            # Sort by shared tag count (most related first)
            sorted_related = sorted(
                related_nodes.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            # Take top 10 most related nodes
            for related_id, shared_count in sorted_related[:10]:
                if shared_count < 2:
                    continue  # Require at least 2 shared tags
                
                # Create unique pair ID to avoid duplicates
                pair = tuple(sorted([node_id, related_id]))
                if pair in processed_pairs:
                    continue
                processed_pairs.add(pair)
                
                edge = {
                    'id': f'edge-{edge_id_counter}',
                    'source': node_id,
                    'target': related_id,
                    'type': 'related',
                    'strength': min(shared_count / 5.0, 1.0),  # Normalize to 0-1
                    'metadata': {
                        'shared_tags': shared_count,
                        'generated': True
                    }
                }
                edges.append(edge)
                edge_id_counter += 1
        
        return edges
    
    @staticmethod
    def sync_knowledge_to_graph(
        generate_edges: bool = True,
        verbose: bool = True
    ) -> Dict:
        """
        Main sync function
        
        Args:
            generate_edges: Generate edges from tags (default True)
            verbose: Print progress (default True)
            
        Returns:
            Summary dict with counts
        """
        if verbose:
            print("=" * 60)
            print("KNOWLEDGE BASE → GRAPH SYNC")
            print("=" * 60)
            print()
        
        # 1. Load knowledge base (master)
        if verbose:
            print("📚 Loading knowledge_base.json (MASTER)...")
        kb_entries = KnowledgeToGraphSync.load_knowledge_base()
        if verbose:
            print(f"   Loaded {len(kb_entries)} knowledge entries")
            print()
        
        # 2. Convert to nodes
        if verbose:
            print("🔄 Converting knowledge entries → graph nodes...")
        nodes = []
        for entry in kb_entries:
            node = KnowledgeToGraphSync.convert_kb_entry_to_node(entry)
            nodes.append(node)
        if verbose:
            print(f"   Created {len(nodes)} nodes")
            print()
        
        # 3. Generate edges (optional)
        edges = []
        if generate_edges:
            if verbose:
                print("🔗 Generating edges from shared tags...")
            edges = KnowledgeToGraphSync.generate_edges_from_tags(nodes)
            if verbose:
                print(f"   Created {len(edges)} edges")
                print()
        
        # 4. Save nodes.json
        if verbose:
            print("💾 Saving nodes.json...")
        nodes_data = {
            'nodes': nodes,
            'metadata': {
                'total_nodes': len(nodes),
                'generated_at': datetime.now().isoformat(),
                'source': 'knowledge_base.json',
                'sync_version': '1.0'
            }
        }
        with open(KnowledgeToGraphSync.NODES_PATH, 'w', encoding='utf-8') as f:
            json.dump(nodes_data, f, indent=2, ensure_ascii=False)
        if verbose:
            print(f"   Saved {len(nodes)} nodes")
            print()
        
        # 5. Save edges.json
        if generate_edges:
            if verbose:
                print("💾 Saving edges.json...")
            edges_data = {
                'edges': edges,
                'metadata': {
                    'total_edges': len(edges),
                    'generated_at': datetime.now().isoformat(),
                    'generation_method': 'shared_tags'
                }
            }
            with open(KnowledgeToGraphSync.EDGES_PATH, 'w', encoding='utf-8') as f:
                json.dump(edges_data, f, indent=2, ensure_ascii=False)
            if verbose:
                print(f"   Saved {len(edges)} edges")
                print()
        
        # 6. Update metadata
        if verbose:
            print("📝 Updating metadata...")
        metadata = {
            'last_sync': datetime.now().isoformat(),
            'nodes_count': len(nodes),
            'edges_count': len(edges),
            'source': 'knowledge_base.json',
            'version': '1.0'
        }
        with open(KnowledgeToGraphSync.METADATA_PATH, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        if verbose:
            print("   Metadata updated")
            print()
        
        # Summary
        if verbose:
            print("=" * 60)
            print("✅ SYNC COMPLETE!")
            print("=" * 60)
            print(f"📊 Knowledge entries: {len(kb_entries)}")
            print(f"🔵 Nodes created: {len(nodes)}")
            print(f"🔗 Edges created: {len(edges)}")
            print(f"💾 Files updated:")
            print(f"   - nodes.json")
            print(f"   - edges.json")
            print(f"   - metadata.json")
            print()
        
        return {
            'success': True,
            'knowledge_entries': len(kb_entries),
            'nodes_created': len(nodes),
            'edges_created': len(edges),
            'files_updated': ['nodes.json', 'edges.json', 'metadata.json']
        }


def main():
    """CLI entry point"""
    import sys
    
    verbose = '--quiet' not in sys.argv
    no_edges = '--no-edges' in sys.argv
    
    result = KnowledgeToGraphSync.sync_knowledge_to_graph(
        generate_edges=not no_edges,
        verbose=verbose
    )
    
    if not verbose:
        print(json.dumps(result, indent=2))
    
    return 0 if result['success'] else 1


if __name__ == "__main__":
    exit(main())
