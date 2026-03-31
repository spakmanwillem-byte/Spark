"""
Graph API Routes - API endpoints voor Knowledge Graph
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from services.graph_service import GraphService
from services.relation_detection_service import RelationDetectionService

router = APIRouter()
from services.knowledge_to_graph_sync import KnowledgeToGraphSync



class NodeCreate(BaseModel):
    titel: str
    content: str
    node_type: str  # knowledge, notitie, concept, norm, waarde
    source: str     # knowledge, user_note, conversation, system
    tags: Optional[List[str]] = []
    metadata: Optional[dict] = {}


class RelationCreate(BaseModel):
    from_node_id: str
    to_node_id: str
    relation_type: str
    strength: Optional[float] = 0.5
    metadata: Optional[dict] = {}


@router.get("/stats")
async def get_graph_stats():
    """Haal graph statistieken op"""
    stats = GraphService.get_graph_stats()
    return stats


@router.get("/nodes")
async def get_nodes(
    node_type: Optional[str] = None, 
    source: Optional[str] = None,
    limit: Optional[int] = None,
    sort: Optional[str] = None
):
    """Haal alle nodes op, optioneel gefilterd"""
    nodes = GraphService.get_all_nodes(node_type=node_type, source=source)
    
    # Sort if requested
    if sort == "recent":
        nodes = sorted(nodes, key=lambda n: n.get('created_at', ''), reverse=True)
    
    # Limit if requested
    if limit:
        nodes = nodes[:limit]
    
    return nodes


@router.get("/nodes/{node_id}")
async def get_node(node_id: str):
    """Haal een specifieke node op"""
    node = GraphService.get_node(node_id)
    
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    
    return {"node": node}


@router.get("/nodes/{node_id}/related")
async def get_related_nodes(node_id: str, max_depth: int = 2, min_strength: float = 0.3):
    """Haal gerelateerde nodes op"""
    node = GraphService.get_node(node_id)
    
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    
    related = GraphService.get_related_nodes(node_id, max_depth=max_depth, min_strength=min_strength)
    
    return {
        "node": node,
        "related": related,
        "count": len(related)
    }


@router.post("/nodes")
async def create_node(node: NodeCreate):
    """Creëer een nieuwe node"""
    try:
        new_node = GraphService.add_node(
            titel=node.titel,
            content=node.content,
            node_type=node.node_type,
            source=node.source,
            tags=node.tags,
            metadata=node.metadata
        )
        
        # Auto-detect relaties
        relations_created = RelationDetectionService.auto_detect_and_create_relations(new_node["id"])
        
        return {
            "success": True,
            "node": new_node,
            "relations_created": relations_created
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/relations")
async def create_relation(relation: RelationCreate):
    """Creëer een nieuwe relatie"""
    try:
        edge = GraphService.add_relation(
            from_node_id=relation.from_node_id,
            to_node_id=relation.to_node_id,
            relation_type=relation.relation_type,
            strength=relation.strength,
            auto_detected=False,
            metadata=relation.metadata
        )
        
        return {"success": True, "edge": edge}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/path/{from_id}/{to_id}")
async def find_path(from_id: str, to_id: str, max_depth: int = 4):
    """Vind pad tussen twee nodes"""
    path = GraphService.find_path(from_id, to_id, max_depth=max_depth)
    
    if not path:
        return {"path": None, "message": "Geen pad gevonden"}
    
    return {
        "path": path,
        "length": len(path),
        "nodes": [n["titel"] for n in path]
    }


@router.get("/search/{query}")
async def search_graph(query: str):
    """Zoek in de graph"""
    results = GraphService.search_nodes(query)
    
    return {
        "results": results,
        "count": len(results)
    }


@router.get("/quality-check")
async def quality_check():
    """
    Check data quality van alle nodes
    Returns nodes met issues
    """
    try:
        data = DataManager.load_json("graph/nodes.json")
        nodes = data.get("nodes", [])
        
        issues = {
            "no_label": [],
            "no_gradatie": [],
            "no_creator": [],
            "potential_duplicates": []
        }
        
        # Check elke node
        for node in nodes:
            if not node.get('label') or node.get('label') == 'None':
                issues["no_label"].append(node.get('id'))
            
            if not node.get('gradatie') or node.get('gradatie') == 'None':
                issues["no_gradatie"].append(node.get('id'))
            
            if not node.get('created_by_user_id') or node.get('created_by_user_id') in ['unknown', 'system']:
                issues["no_creator"].append(node.get('id'))
        
        # Check duplicates
        labels = {}
        for node in nodes:
            label = node.get('label', '').lower()
            if label and label != 'none':
                if label not in labels:
                    labels[label] = []
                labels[label].append(node.get('id'))
        
        # Find duplicates
        for label, node_ids in labels.items():
            if len(node_ids) > 1:
                issues["potential_duplicates"].append({
                    "label": label,
                    "count": len(node_ids),
                    "node_ids": node_ids
                })
        
        return {
            "total_nodes": len(nodes),
            "issues_found": sum([
                len(issues["no_label"]),
                len(issues["no_gradatie"]),
                len(issues["no_creator"]),
                len(issues["potential_duplicates"])
            ]),
            "issues": issues,
            "status": "healthy" if all(len(v) == 0 for v in issues.values()) else "needs_attention"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    synced = {
        "knowledge": 0,
        "notities": 0,
        "normen": 0,
        "waarden": 0,
        "relations": 0
    }
    
    try:
        # Sync knowledge
        all_knowledge = KnowledgeService.get_all_knowledge()
        for item in all_knowledge:
            if item.get("status") == "active":  # Skip trash
                GraphService.add_node(
                    titel=item["begrip"],
                    content=f"{item.get('lagen', {}).get('laag1', '')} {item.get('lagen', {}).get('laag2', '')}",
                    node_type="knowledge",
                    source="knowledge",
                    tags=item.get("tags", []),
                    metadata={"knowledge_id": item["id"], "belangrijkheid": item.get("belangrijkheid", 3)}
                )
                synced["knowledge"] += 1
        
        # Sync notities (van alle users)
        users = DataManager.load_users()
        for user in users:
            user_notes = NotesService.get_all_notes(user.get("id"))
            for note in user_notes:
                GraphService.add_node(
                    titel=note["titel"],
                    content=note["inhoud"],
                    node_type="notitie",
                    source="user_note",
                    tags=note.get("tags", []),
                    metadata={"note_id": note["id"], "categorie": note.get("categorie"), "user_id": user.get("id")}
                )
                synced["notities"] += 1
        
        # Sync normen
        personality = DataManager.load_json("system/personality.json")
        for norm in personality.get("norms", []):
            GraphService.add_node(
                titel=norm["norm"],
                content=norm.get("uitleg", ""),
                node_type="norm",
                source="system",
                tags=["norm"],
                metadata={"norm_id": norm.get("id")}
            )
            synced["normen"] += 1
        
        # Sync waarden
        for waarde in personality.get("values", []):
            GraphService.add_node(
                titel=waarde["waarde"],
                content=waarde.get("beschrijving", ""),
                node_type="waarde",
                source="system",
                tags=["waarde"],
                metadata={"waarde_id": waarde.get("id")}
            )
            synced["waarden"] += 1
        
        # Auto-detect relaties voor alles
        synced["relations"] = RelationDetectionService.scan_all_nodes_for_relations()
        
        return {
            "success": True,
            "synced": synced,
            "message": f"Synced {sum(synced.values())} items"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/relations/{edge_id}/use")
async def use_relation(edge_id: str):
    """Markeer een relatie als gebruikt (increment usage count)"""
    success = GraphService.increment_usage(edge_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Edge not found")
    
    return {"success": True, "message": "Usage count incremented"}



@router.get("/metadata")
async def get_graph_metadata():
    """Get graph metadata (totals, last updated, etc.)"""
    import json
    from pathlib import Path
    
    graph_dir = Path(__file__).parent.parent / "data" / "graph"
    
    # Load metadata
    metadata_file = graph_dir / "metadata.json"
    if metadata_file.exists():
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
            return {
                "total_nodes": metadata.get("total_nodes", 0),
                "total_edges": metadata.get("total_edges", 0),
                "last_updated": metadata.get("last_updated", None)
            }
    
    return {"total_nodes": 0, "total_edges": 0, "last_updated": None}


@router.get("/edges")
async def get_edges(limit: Optional[int] = None):
    """Get all edges, optionally limited"""
    edges = GraphService.get_all_edges()
    
    if limit:
        edges = edges[:limit]
    
    return edges


@router.get("/search")
async def search_graph(query: str, limit: int = 20):
    """Search nodes by query and return connected subgraph"""
    # Search nodes
    matching_nodes = GraphService.search_nodes(query)[:limit]
    
    if not matching_nodes:
        return {"nodes": [], "edges": []}
    
    # Get edges between matching nodes
    node_ids = [n["id"] for n in matching_nodes]
    all_edges = GraphService.get_all_edges()
    
    relevant_edges = [
        e for e in all_edges 
        if e.get("from") in node_ids or e.get("to") in node_ids
    ]
    
    return {
        "nodes": matching_nodes,
        "edges": relevant_edges[:100]  # Limit edges voor performance
    }


@router.get("/connections/{node_id}")
async def get_node_connections(node_id: str, max_depth: int = 1):
    """Get all connected nodes for a specific node"""
    try:
        # Get the main node
        node = GraphService.get_node(node_id)
        if not node:
            raise HTTPException(status_code=404, detail="Node not found")
        
        # Get all edges
        all_edges = GraphService.get_all_edges()
        
        # Find connected nodes
        connected_ids = set()
        for edge in all_edges:
            if edge.get("from") == node_id:
                connected_ids.add(edge.get("to"))
            elif edge.get("to") == node_id:
                connected_ids.add(edge.get("from"))
        
        # Get connected nodes
        connected_nodes = [GraphService.get_node(nid) for nid in connected_ids if GraphService.get_node(nid)]
        
        return {
            "node": node,
            "connections": connected_nodes,
            "total_connections": len(connected_nodes)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync")
async def sync_knowledge_to_graph():
    """
    Sync knowledge_base.json (MASTER) → nodes.json (graph)
    
    Architecture:
    - knowledge_base.json = Master database met lagen structuur
    - nodes.json = Afgeleide graph voor visualisatie
    
    This endpoint regenerates the entire graph from knowledge_base.json
    """
    try:
        result = KnowledgeToGraphSync.sync_knowledge_to_graph(
            generate_edges=True,
            verbose=False
        )
        return {
            'success': True,
            'message': 'Graph synced from knowledge_base.json',
            'stats': result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sync/status")
async def get_sync_status():
    """
    Check sync status between knowledge_base and graph
    """
    try:
        import json
        from datetime import datetime
        
        # Load knowledge_base count
        with open('/app/backend/data/learned_knowledge/knowledge_base.json', 'r') as f:
            kb_data = json.load(f)
            kb_count = len(kb_data.get('knowledge_entries', []))
        
        # Load nodes count
        with open('/app/backend/data/graph/nodes.json', 'r') as f:
            nodes_data = json.load(f)
            nodes_count = len(nodes_data.get('nodes', []))
        
        # Load metadata
        try:
            with open('/app/backend/data/graph/metadata.json', 'r') as f:
                metadata = json.load(f)
        except:
            metadata = {}
        
        in_sync = kb_count == nodes_count
        
        return {
            'in_sync': in_sync,
            'knowledge_base_count': kb_count,
            'graph_nodes_count': nodes_count,
            'last_sync': metadata.get('last_sync'),
            'message': 'In sync ✅' if in_sync else f'Out of sync ⚠️ ({kb_count} KB vs {nodes_count} nodes)'
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

        # Get related nodes
        related = GraphService.get_related_nodes(node_id, max_depth=max_depth, min_strength=0.3)
        
        connected_nodes = [r["node"] for r in related if "node" in r]
        
        # Get edges
        edges = GraphService.get_edges_for_node(node_id)
        
        return {
            "node": node,
            "connected_nodes": connected_nodes,
            "edges": edges,
            "total_connections": len(connected_nodes)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
