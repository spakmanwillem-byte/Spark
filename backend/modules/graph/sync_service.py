"""
Graph sync — houdt nodes.json + edges.json in lijn met knowledge_base.json.

Strategie:
- Lichte incrementele updates: bij ADD/UPDATE/DELETE van een snap wordt alleen
  die node + zijn directe verwante edges aangepast.
- Edges worden gebaseerd op shared tags (zelfde algoritme als initiële build).
- Volledige rebuild beschikbaar via rebuild_graph_full() voor admin-knop.
"""
from pathlib import Path
import uuid
from modules.core.storage import load_json, save_json

GRAPH_DIR = Path(__file__).parent.parent.parent / "data" / "graph"
NODES_FILE = GRAPH_DIR / "nodes.json"
EDGES_FILE = GRAPH_DIR / "edges.json"

# Edge-config — zelfde als initieel
MIN_SHARED_TAGS = 1
MAX_EDGES_PER_NODE = 20


def _load_nodes_raw():
    return load_json(NODES_FILE, default={"nodes": []}).get("nodes", [])


def _load_edges_raw():
    return load_json(EDGES_FILE, default={"edges": []}).get("edges", [])


def _save_nodes(nodes):
    save_json(NODES_FILE, {"nodes": nodes})


def _save_edges(edges):
    save_json(EDGES_FILE, {"edges": edges})


def _invalidate_graph_cache():
    """Reset graph cache in routes module zodat eerstvolgende GET nieuwe data ziet."""
    try:
        import sys
        gm = sys.modules.get("modules.graph")
        if gm is not None:
            gm._nodes_cache = None
            gm._edges_cache = None
    except Exception:
        pass


def _entry_to_node(entry: dict) -> dict:
    """Bouw een graph-node uit een knowledge-entry."""
    return {
        "id": entry.get("id"),
        "label": entry.get("begrip", ""),
        "type": "knowledge",
        "description": (entry.get("lagen", {}) or {}).get("laag1", "")[:300],
        "tags": entry.get("tags", []),
        "topic": entry.get("topic", ""),
        "belangrijkheid": entry.get("belangrijkheid", 0),
    }


# v5_kbv2_graph_001 — KB v2 kaarten ook in graph, met lade-info als kleur-bron
LADE_COLORS = {
    "voelen":  "#ec4899",
    "spreken": "#06b6d4",
    "weten":   "#f59e0b",
    "doen":    "#a855f7",
}


def _v2_entry_to_node(entry: dict, lade: str = None) -> dict:
    """Bouw een graph-node uit een KB v2 kaart. Bevat lade-info voor kleuring."""
    return {
        "id": entry.get("id"),
        "label": entry.get("begrip", ""),
        "type": "knowledge_v2",
        "lade": lade or entry.get("lade"),
        "lade_color": LADE_COLORS.get(lade or entry.get("lade") or "", "#94a3b8"),
        "description": (entry.get("lagen", {}) or {}).get("laag1", "")[:300],
        "tags": entry.get("tags", []),
        "topic": entry.get("topic", ""),
        "belangrijkheid": (entry.get("footnote") or {}).get("belangrijkheid", 5),
        "vertrouwen": (entry.get("footnote") or {}).get("vertrouwen", 0.5),
    }


def _shared_tags_count(tags_a, tags_b) -> int:
    if not tags_a or not tags_b:
        return 0
    return len(set(tags_a) & set(tags_b))


def _make_edge(source_id, target_id, shared_count) -> dict:
    return {
        "id": f"edge-{uuid.uuid4().hex[:10]}",
        "source": source_id,
        "target": target_id,
        "type": "related",
        "strength": min(1.0, 0.3 + shared_count * 0.15),
        "metadata": {"shared_tags": shared_count, "generated": True},
    }


# ============================================================
# PUBLIC API — aan te roepen vanuit snap_service / knowledge routes
# ============================================================

def upsert_node_from_entry(entry: dict):
    """Voeg node toe of update bestaande. Herberekent edges van deze node."""
    if not entry or not entry.get("id"):
        return

    nodes = _load_nodes_raw()
    edges = _load_edges_raw()
    eid = entry["id"]

    new_node = _entry_to_node(entry)

    # Update of insert
    found = False
    for i, n in enumerate(nodes):
        if n.get("id") == eid:
            nodes[i] = new_node
            found = True
            break
    if not found:
        nodes.append(new_node)

    # Wis bestaande edges van/naar deze node
    edges = [e for e in edges if e.get("source") != eid and e.get("target") != eid]

    # Bereken nieuwe edges: vergelijk tegen alle andere nodes via tags
    new_tags = new_node.get("tags") or []
    if new_tags:
        candidates = []
        for n in nodes:
            if n.get("id") == eid:
                continue
            shared = _shared_tags_count(new_tags, n.get("tags") or [])
            if shared >= MIN_SHARED_TAGS:
                candidates.append((n["id"], shared))
        # Sorteer op sterkte, beperk
        candidates.sort(key=lambda x: -x[1])
        for target_id, shared in candidates[:MAX_EDGES_PER_NODE]:
            edges.append(_make_edge(eid, target_id, shared))

    # related_to (homoniem-variant) — voeg directe link toe
    related_to = entry.get("related_to")
    if related_to:
        # Strong link, type 'variant'
        edges.append({
            "id": f"edge-{uuid.uuid4().hex[:10]}",
            "source": eid,
            "target": related_to,
            "type": "homonym_variant",
            "strength": 1.0,
            "metadata": {"shared_tags": 0, "homonym": True},
        })

    _save_nodes(nodes)
    _save_edges(edges)
    _invalidate_graph_cache()


def remove_node(entry_id: str):
    """Wis node + alle edges van/naar deze node."""
    if not entry_id:
        return
    nodes = [n for n in _load_nodes_raw() if n.get("id") != entry_id]
    edges = [
        e for e in _load_edges_raw()
        if e.get("source") != entry_id and e.get("target") != entry_id
    ]
    _save_nodes(nodes)
    _save_edges(edges)
    _invalidate_graph_cache()


def rebuild_graph_full() -> dict:
    """Volledige herbouw vanuit knowledge_base v1 + KB v2 lades + inbox.
    v5_kbv2_graph_001 — Verbanden tab toont nu ook v2 kaarten gekleurd per lade."""
    from modules.core.storage import load_json as _lj
    BASE = Path(__file__).parent.parent.parent / "data" / "knowledge"
    kb_file = BASE / "learned_knowledge" / "knowledge_base.json"

    # 1. v1 entries
    v1_data = _lj(kb_file, default={"knowledge_entries": []})
    v1_entries = v1_data.get("knowledge_entries", [])
    v1_nodes = [_entry_to_node(e) for e in v1_entries if e.get("id")]

    # 2. v2 lades + inbox
    v2_nodes = []
    v2_dir = BASE / "v2"
    for lade in LADE_COLORS:
        d = _lj(v2_dir / f"knowledge_v2_{lade}.json", default={"kaarten": []})
        for c in d.get("kaarten", []):
            if c.get("id"):
                v2_nodes.append(_v2_entry_to_node(c, lade=lade))
    # Inbox: lade=None → grijze nodes
    inbox = _lj(v2_dir / "knowledge_inbox.json", default={"kaarten": []})
    for c in inbox.get("kaarten", []):
        if c.get("id"):
            v2_nodes.append(_v2_entry_to_node(c, lade=None))

    nodes = v1_nodes + v2_nodes

    # 3. Bouw edges via shared tags (mengt v1 en v2 nodes)
    edges = []
    tag_to_nodes = {}
    for n in nodes:
        for t in (n.get("tags") or []):
            tag_to_nodes.setdefault(t, set()).add(n["id"])

    edge_pairs = set()
    edges_per_node = {n["id"]: 0 for n in nodes}
    node_by_id = {n["id"]: n for n in nodes}

    for n in nodes:
        nid = n["id"]
        if edges_per_node[nid] >= MAX_EDGES_PER_NODE:
            continue
        tags = n.get("tags") or []
        candidates = {}
        for t in tags:
            for other_id in tag_to_nodes.get(t, set()):
                if other_id == nid:
                    continue
                candidates[other_id] = candidates.get(other_id, 0) + 1

        ranked = sorted(candidates.items(), key=lambda x: -x[1])
        for target_id, shared in ranked:
            if edges_per_node[nid] >= MAX_EDGES_PER_NODE:
                break
            if edges_per_node.get(target_id, 0) >= MAX_EDGES_PER_NODE:
                continue
            pair_key = tuple(sorted([nid, target_id]))
            if pair_key in edge_pairs:
                continue
            edge_pairs.add(pair_key)
            edges.append(_make_edge(nid, target_id, shared))
            edges_per_node[nid] += 1
            edges_per_node[target_id] = edges_per_node.get(target_id, 0) + 1

    # 4. Homoniem-varianten (v1 only)
    for e in v1_entries:
        rt = e.get("related_to")
        if rt and e.get("id") in node_by_id and rt in node_by_id:
            edges.append({
                "id": f"edge-{uuid.uuid4().hex[:10]}",
                "source": e["id"],
                "target": rt,
                "type": "homonym_variant",
                "strength": 1.0,
                "metadata": {"homonym": True},
            })

    _save_nodes(nodes)
    _save_edges(edges)
    _invalidate_graph_cache()

    return {
        "success": True,
        "nodes": len(nodes),
        "edges": len(edges),
        "entries_scanned": len(v1_entries) + len(v2_nodes),
        "v1_nodes": len(v1_nodes),
        "v2_nodes": len(v2_nodes),
        "v2_by_lade": {l: sum(1 for n in v2_nodes if n.get("lade") == l) for l in LADE_COLORS},
        "v2_inbox": sum(1 for n in v2_nodes if not n.get("lade")),
    }
