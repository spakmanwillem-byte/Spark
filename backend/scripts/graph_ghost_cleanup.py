"""v6_graph_ghost_cleanup_001 — Verwijder V1 (snap-*) ghost-nodes uit knowledge graph.

Wat doet het:
  - Voor elke snap-X node: zoek V2-equivalent (kbv2-Y) op basis van label↔begrip
  - Als match: rewire alle edges (source=snap-X → kbv2-Y, target=snap-X → kbv2-Y),
    dedupe edges die nu identiek zijn, en verwijder de snap-X node
  - Als geen V2 match: drop snap-X node + alle edges die hem raken (echte orphans)
  - Backup beide bestanden vóór wijziging

Resultaat:
  - VerbandenPage toont alleen nog V2 kennisbank-kaarten (geen lege ghost-clicks meer)
  - Edges blijven behouden voor zover ze in V2-knooppunten landen
"""
import json
import shutil
from pathlib import Path
from datetime import datetime
from collections import defaultdict

BASE = Path(__file__).parent.parent / "data"
GRAPH_DIR = BASE / "graph"
V2_DIR = BASE / "knowledge" / "v2"
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")


def _load_v2_index():
    """begrip (lowercase) -> v2-kaart-id"""
    out = {}
    for fname in ["knowledge_v2_doen", "knowledge_v2_weten", "knowledge_v2_voelen",
                  "knowledge_v2_spreken", "knowledge_inbox"]:
        fp = V2_DIR / f"{fname}.json"
        if not fp.exists():
            continue
        for k in json.loads(fp.read_text()).get("kaarten", []):
            b = (k.get("begrip") or "").strip().lower()
            if b and b not in out:
                out[b] = k["id"]
    return out


def main():
    nodes_fp = GRAPH_DIR / "nodes.json"
    edges_fp = GRAPH_DIR / "edges.json"

    # Backup
    backup_nodes = nodes_fp.with_suffix(f".backup_ghost_{STAMP}.json")
    backup_edges = edges_fp.with_suffix(f".backup_ghost_{STAMP}.json")
    shutil.copy(nodes_fp, backup_nodes)
    shutil.copy(edges_fp, backup_edges)
    print(f"📦 Backup → {backup_nodes.name} + {backup_edges.name}")

    nodes_data = json.loads(nodes_fp.read_text())
    edges_data = json.loads(edges_fp.read_text())
    nodes = nodes_data.get("nodes", [])
    edges = edges_data.get("edges", [])

    print(f"\n📊 Start: {len(nodes)} nodes, {len(edges)} edges")

    v2_by_begrip = _load_v2_index()

    # Bouw remap: snap-X → kbv2-Y of None (drop)
    remap = {}            # snap-X → kbv2-Y
    drop_node_ids = set() # snap-X zonder V2-match → verwijder
    for n in nodes:
        nid = n.get("id") or ""
        if not nid.startswith("snap-"):
            continue
        label = (n.get("label") or "").strip().lower()
        if label in v2_by_begrip:
            target = v2_by_begrip[label]
            if target != nid:
                remap[nid] = target
        else:
            drop_node_ids.add(nid)

    print(f"  🔁 Rewire-plan:  {len(remap)} snap-* → kbv2-*")
    print(f"  🗑️  Drop-plan:    {len(drop_node_ids)} snap-* (geen V2 match)")

    # 1. Rewire edges (vervang ids in source/target)
    new_edges_raw = []
    dropped_edge_count = 0
    for e in edges:
        s, t = e.get("source"), e.get("target")
        if s in drop_node_ids or t in drop_node_ids:
            dropped_edge_count += 1
            continue
        if s in remap:
            s = remap[s]
        if t in remap:
            t = remap[t]
        if s == t:
            # self-loop na rewire - skip
            dropped_edge_count += 1
            continue
        e2 = dict(e)
        e2["source"] = s
        e2["target"] = t
        new_edges_raw.append(e2)

    # 2. Dedupe edges (zelfde source+target+type → som de weights/counts)
    edge_key = lambda e: (e.get("source"), e.get("target"), e.get("type") or e.get("relation") or "")
    grouped = defaultdict(list)
    for e in new_edges_raw:
        grouped[edge_key(e)].append(e)

    deduped_edges = []
    merged_count = 0
    for key, group in grouped.items():
        if len(group) == 1:
            deduped_edges.append(group[0])
        else:
            # merge — som weight/count
            merged = dict(group[0])
            total_w = sum((g.get("weight") or 1) for g in group)
            total_c = sum((g.get("count") or 1) for g in group)
            merged["weight"] = total_w
            merged["count"] = total_c
            merged["_merged_from"] = len(group)
            deduped_edges.append(merged)
            merged_count += len(group) - 1

    print(f"  ✂️  Edges verwijderd (orphan):    {dropped_edge_count}")
    print(f"  🔗 Edges samengevoegd (duplicaat): {merged_count}")

    # 3. Filter nodes (drop snap-* in remap én drop_node_ids)
    nodes_to_remove = set(remap.keys()) | drop_node_ids
    new_nodes = [n for n in nodes if n.get("id") not in nodes_to_remove]

    print(f"\n📊 Eind: {len(new_nodes)} nodes, {len(deduped_edges)} edges")
    print(f"   Δ nodes: {len(nodes) - len(new_nodes):+d}, Δ edges: {len(deduped_edges) - len(edges):+d}")

    # Update metadata
    nodes_data["nodes"] = new_nodes
    nodes_data.setdefault("metadata", {})["ghost_cleanup"] = {
        "ts": STAMP,
        "removed_snap_nodes": len(nodes_to_remove),
        "rewired": len(remap),
        "dropped_orphan": len(drop_node_ids),
        "backup": backup_nodes.name,
    }
    edges_data["edges"] = deduped_edges
    edges_data.setdefault("metadata", {})["ghost_cleanup"] = {
        "ts": STAMP,
        "merged_count": merged_count,
        "dropped_orphan": dropped_edge_count,
        "backup": backup_edges.name,
    }

    nodes_fp.write_text(json.dumps(nodes_data, indent=2, ensure_ascii=False))
    edges_fp.write_text(json.dumps(edges_data, indent=2, ensure_ascii=False))
    print(f"\n✅ Opgeschoond. Cache in graph-module moet ge-invalideerd worden (restart of clear).")


if __name__ == "__main__":
    main()
