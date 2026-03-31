"""
Migratie Script: Knowledge Cards → Graph Nodes
Migreert alle bestaande knowledge cards naar de graph service
"""
import json
from services.graph_service import GraphService
from services.relation_detection_service import RelationDetectionService

def migrate_knowledge_to_graph():
    """Migreer alle knowledge cards naar graph nodes"""
    
    # Laad knowledge base
    with open('/app/backend/data/learned_knowledge/knowledge_base.json', 'r', encoding='utf-8') as f:
        kb = json.load(f)
    
    entries = kb.get('knowledge_entries', [])
    print(f"📚 Gevonden: {len(entries)} knowledge cards")
    
    # Migreer elke entry
    migrated = 0
    skipped = 0
    
    for entry in entries:
        try:
            # Gebruik 'begrip' als titel (niet 'titel')
            begrip = entry.get('begrip', 'Onbekend')
            
            # Combineer alle lagen tot content
            lagen = entry.get('lagen', {})
            content_parts = []
            for laag_key in sorted(lagen.keys()):
                content_parts.append(lagen[laag_key])
            content = '\n\n'.join(content_parts) if content_parts else begrip
            
            # Maak graph node
            node = GraphService.add_node(
                titel=begrip,
                content=content,
                node_type="knowledge",
                source="knowledge_base_migration",
                tags=entry.get('tags', []),
                metadata={
                    'original_id': entry.get('id'),
                    'created_by_user_id': entry.get('created_by_user_id'),
                    'created_via': entry.get('created_via'),
                    'created_by_admin': entry.get('created_by_admin'),
                    'belangrijkheid': entry.get('belangrijkheid'),
                    'lagen': lagen
                }
            )
            
            migrated += 1
            if migrated % 50 == 0:
                print(f"✅ Gemigreerd: {migrated}/{len(entries)}")
                
        except Exception as e:
            print(f"❌ Error bij '{entry.get('begrip', 'Unknown')[:30]}': {str(e)}")
    
    print(f"\n🎉 MIGRATIE COMPLEET!")
    print(f"   ✅ Gemigreerd: {migrated}")
    print(f"   ⏭️  Overgeslagen: {skipped}")
    
    return migrated

def auto_detect_all_relations():
    """Run auto-detect op alle nodes"""
    print(f"\n🔗 START: Auto-detect relaties...")
    
    total_relations = RelationDetectionService.scan_all_nodes_for_relations()
    
    print(f"🎉 RELATIES COMPLEET!")
    print(f"   🔗 Aangemaakt: {total_relations} relaties")
    
    return total_relations

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 KNOWLEDGE → GRAPH MIGRATIE")
    print("=" * 60)
    
    # Stap 1: Migreer nodes
    migrated_count = migrate_knowledge_to_graph()
    
    # Stap 2: Detecteer relaties
    if migrated_count > 0:
        relations_count = auto_detect_all_relations()
    
    # Statistieken
    stats = GraphService.get_graph_stats()
    print("\n📊 FINALE STATISTIEKEN:")
    print(f"   Nodes: {stats.get('total_nodes', 0)}")
    print(f"   Relaties: {stats.get('total_relations', 0)}")
    print(f"   Gemiddeld: {stats.get('avg_relations_per_node', 0):.1f} relaties per node")
    print("=" * 60)
