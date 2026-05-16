"""
Graph Routes - Knowledge Graph API
Serves nodes, edges, clusters, and search for the Verbanden page.
nodes.json: 2424 nodes  |  edges.json: 11757 edges
"""
from fastapi import APIRouter, Query
from pathlib import Path
from typing import Optional
from modules.core.storage import load_json

router = APIRouter(prefix="/graph", tags=["graph"])
DATA_DIR = Path(__file__).parent.parent.parent / "data" / "graph"
KNOWLEDGE_FILE = Path(__file__).parent.parent.parent / "data" / "knowledge" / "learned_knowledge" / "knowledge_base.json"

_nodes_cache = None
_edges_cache = None


def _load_nodes():
    global _nodes_cache
    if _nodes_cache is None:
        data = load_json(DATA_DIR / "nodes.json", default={"nodes": []})
        _nodes_cache = data.get("nodes", [])
    return _nodes_cache


def _load_edges():
    global _edges_cache
    if _edges_cache is None:
        data = load_json(DATA_DIR / "edges.json", default={"edges": []})
        _edges_cache = data.get("edges", [])
    return _edges_cache


@router.get("/stats")
async def graph_stats():
    nodes = _load_nodes()
    edges = _load_edges()
    tags_count = {}
    for n in nodes:
        for t in (n.get("tags") or []):
            tags_count[t] = tags_count.get(t, 0) + 1
    top_tags = sorted(tags_count.items(), key=lambda x: -x[1])[:20]
    node_edge_counts = {}
    for e in edges:
        node_edge_counts[e["source"]] = node_edge_counts.get(e["source"], 0) + 1
        node_edge_counts[e["target"]] = node_edge_counts.get(e["target"], 0) + 1
    most_connected = sorted(node_edge_counts.items(), key=lambda x: -x[1])[:20]
    node_map = {n["id"]: n["label"] for n in nodes}
    return {
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "top_tags": [{"tag": t, "count": c} for t, c in top_tags],
        "most_connected": [{"id": nid, "label": node_map.get(nid, "?"), "connections": cnt} for nid, cnt in most_connected],
        "avg_connections": round(len(edges) * 2 / max(len(nodes), 1), 1),
    }


@router.get("/nodes")
async def get_nodes(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    tag: Optional[str] = None,
    search: Optional[str] = None,
):
    nodes = _load_nodes()
    filtered = nodes
    if tag:
        filtered = [n for n in filtered if tag in (n.get("tags") or [])]
    if search:
        q = search.lower()
        filtered = [n for n in filtered if q in (n.get("label") or "").lower() or q in (n.get("description") or "").lower()]
    total = len(filtered)
    return {
        "nodes": filtered[offset:offset + limit],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/edges")
async def get_edges(
    node_id: Optional[str] = None,
    limit: int = Query(200, ge=1, le=2000),
):
    edges = _load_edges()
    if node_id:
        edges = [e for e in edges if e["source"] == node_id or e["target"] == node_id]
    return {
        "edges": edges[:limit],
        "total": len(edges),
    }


@router.get("/neighborhood/{node_id}")
async def get_neighborhood(node_id: str, depth: int = Query(1, ge=1, le=2)):
    """Get a node and all its direct neighbors (1-hop or 2-hop)"""
    nodes = _load_nodes()
    edges = _load_edges()
    node_map = {n["id"]: n for n in nodes}

    if node_id not in node_map:
        return {"error": "Node niet gevonden"}

    collected_ids = {node_id}
    collected_edges = []

    for hop in range(depth):
        new_ids = set()
        for e in edges:
            if e["source"] in collected_ids:
                new_ids.add(e["target"])
                collected_edges.append(e)
            elif e["target"] in collected_ids:
                new_ids.add(e["source"])
                collected_edges.append(e)
        collected_ids |= new_ids

    # Limit to prevent oversized responses
    if len(collected_ids) > 100:
        sorted_ids = sorted(collected_ids, key=lambda nid: sum(1 for e in collected_edges if e["source"] == nid or e["target"] == nid), reverse=True)
        collected_ids = set(sorted_ids[:100])
        collected_ids.add(node_id)

    result_nodes = [node_map[nid] for nid in collected_ids if nid in node_map]
    result_edges = [e for e in collected_edges if e["source"] in collected_ids and e["target"] in collected_ids]
    # Deduplicate edges
    seen = set()
    unique_edges = []
    for e in result_edges:
        if e["id"] not in seen:
            seen.add(e["id"])
            unique_edges.append(e)

    return {
        "center_node": node_map.get(node_id),
        "nodes": result_nodes,
        "edges": unique_edges,
        "total_nodes": len(result_nodes),
        "total_edges": len(unique_edges),
    }


@router.get("/clusters")
async def get_clusters(min_size: int = Query(3, ge=2, le=50)):
    """Find clusters by shared tags"""
    nodes = _load_nodes()
    tag_groups = {}
    for n in nodes:
        for t in (n.get("tags") or []):
            if t not in tag_groups:
                tag_groups[t] = []
            tag_groups[t].append({"id": n["id"], "label": n["label"]})
    clusters = [
        {"tag": t, "size": len(members), "members": members[:20]}
        for t, members in sorted(tag_groups.items(), key=lambda x: -len(x[1]))
        if len(members) >= min_size
    ]
    return {"clusters": clusters[:50], "total_clusters": len(clusters)}


@router.get("/search")
async def search_graph(q: str = Query(..., min_length=1)):
    """Search nodes by label, description, or tags"""
    nodes = _load_nodes()
    query = q.lower()
    results = []
    for n in nodes:
        score = 0
        label = (n.get("label") or "").lower()
        desc = (n.get("description") or "").lower()
        tags = [t.lower() for t in (n.get("tags") or [])]
        if query == label:
            score = 100
        elif query in label:
            score = 80
        elif query in tags:
            score = 60
        elif query in desc:
            score = 40
        if score > 0:
            results.append({**n, "score": score})
    results.sort(key=lambda x: -x["score"])
    return {"results": results[:30], "total": len(results)}


@router.post("/rebuild")
async def rebuild_graph():
    """Volledige herbouw van nodes + edges vanuit knowledge_base."""
    from .sync_service import rebuild_graph_full
    return rebuild_graph_full()
