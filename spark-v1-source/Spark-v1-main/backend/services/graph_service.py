"""
Graph Service - Knowledge Graph voor Spark
Beheert nodes (concepten) en edges (relaties) tussen alle content
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from utils.data_manager import DataManager
import json
import uuid

import re

class GraphService:
    """Service voor het beheren van de Knowledge Graph"""
    
    GRAPH_PATH = "graph"
    
    # Relatie types
    RELATION_TYPES = [
        "related_to",      # Algemeen gerelateerd
        "part_of",         # Is onderdeel van
        "leads_to",        # Leidt tot
        "caused_by",       # Veroorzaakt door
        "belongs_to",      # Behoort tot
        "example_of",      # Is voorbeeld van
        "contrasts_with"   # Contrasteert met
    ]
    
    # Source types
    SOURCE_TYPES = [
        "knowledge",       # Uit knowledge base
        "user_note",       # Uit notities
        "conversation",    # Uit gesprekken
        "system"          # Systeem-gegenereerd
    ]
    
    @staticmethod
    def initialize_graph():
        """Initialiseer graph files als ze niet bestaan"""
        try:
            DataManager.load_json("graph/nodes.json")
        except:
            DataManager.save_json("graph/nodes.json", {"nodes": []})
        
        try:
            DataManager.load_json("graph/edges.json")
        except:
            DataManager.save_json("graph/edges.json", {"edges": []})
        
        try:
            DataManager.load_json("graph/metadata.json")
        except:
            DataManager.save_json("graph/metadata.json", {
                "total_nodes": 0,
                "total_edges": 0,
                "last_updated": datetime.now().isoformat(),
                "version": "1.0"
            })
    
    @staticmethod
    def add_node(titel: str, content: str, node_type: str, source: str, 
                 tags: List[str] = None, metadata: Dict = None) -> Dict:
        """
        Voeg een node toe aan de graph
        
        Args:
            titel: Titel/naam van de node
            content: Inhoud
            node_type: Type (knowledge, notitie, concept, norm, waarde)
            source: Bron (knowledge, user_note, conversation, system)
            tags: Tags voor de node
            metadata: Extra metadata
        """
        GraphService.initialize_graph()
        
        node = {
            "id": str(uuid.uuid4()),
            "titel": titel,
            "content": content,
            "type": node_type,
            "source": source,
            "tags": tags or [],
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # Load en save
        data = DataManager.load_json("graph/nodes.json")
        data["nodes"].append(node)
        DataManager.save_json("graph/nodes.json", data)
        
        # Update metadata
        meta = DataManager.load_json("graph/metadata.json")
        meta["total_nodes"] = len(data["nodes"])
        meta["last_updated"] = datetime.now().isoformat()
        DataManager.save_json("graph/metadata.json", meta)
        
        return node
    
    @staticmethod
    def get_node(node_id: str) -> Optional[Dict]:
        """Haal een specifieke node op"""
        GraphService.initialize_graph()
        data = DataManager.load_json("graph/nodes.json")
        
        for node in data["nodes"]:
            if node["id"] == node_id:
                return node
        return None
    
    @staticmethod
    def get_all_nodes(node_type: Optional[str] = None, source: Optional[str] = None) -> List[Dict]:
        """Haal alle nodes op, optioneel gefilterd"""
        GraphService.initialize_graph()
        data = DataManager.load_json("graph/nodes.json")
        nodes = data["nodes"]
        
        if node_type:
            nodes = [n for n in nodes if n["type"] == node_type]
        
        if source:
            nodes = [n for n in nodes if n["source"] == source]
        
        return nodes
    
    @staticmethod
    def search_nodes(query: str) -> List[Dict]:
        """Zoek nodes op basis van query"""
        GraphService.initialize_graph()
        data = DataManager.load_json("graph/nodes.json")
        query_lower = query.lower()
        
        results = []
        for node in data["nodes"]:
            # Use 'label' field (nodes use 'label' not 'titel')
            node_label = node.get("label", node.get("titel", "")).lower()
            node_content = node.get("description", node.get("content", "")).lower()
            if (query_lower in node_label or
                query_lower in node_content or
                any(query_lower in tag.lower() for tag in node.get("tags", []))):
                results.append(node)
        
        return results
    
    @staticmethod
    def add_relation(from_node_id: str, to_node_id: str, relation_type: str, 
                     strength: float = 0.5, auto_detected: bool = False,
                     metadata: Dict = None) -> Dict:
        """
        Maak een relatie tussen twee nodes
        
        Args:
            from_node_id: Van node ID
            to_node_id: Naar node ID
            relation_type: Type relatie (zie RELATION_TYPES)
            strength: Sterkte van relatie (0-1)
            auto_detected: Was dit automatisch gedetecteerd?
            metadata: Extra info
        """
        GraphService.initialize_graph()
        
        # Valideer relation type
        if relation_type not in GraphService.RELATION_TYPES:
            raise ValueError(f"Invalid relation type: {relation_type}")
        
        # Check of nodes bestaan
        if not GraphService.get_node(from_node_id) or not GraphService.get_node(to_node_id):
            raise ValueError("One or both nodes don't exist")
        
        edge = {
            "id": str(uuid.uuid4()),
            "from": from_node_id,
            "to": to_node_id,
            "relation_type": relation_type,
            "strength": max(0.0, min(1.0, strength)),  # Clamp tussen 0 en 1
            "auto_detected": auto_detected,
            "usage_count": 0,
            "created_at": datetime.now().isoformat(),
            "last_used": None,
            "metadata": metadata or {}
        }
        
        # Load en save
        data = DataManager.load_json("graph/edges.json")
        
        # Check of relatie al bestaat
        for existing_edge in data["edges"]:
            # Edges use 'source' and 'target' not 'from' and 'to'
            edge_from = existing_edge.get("source", existing_edge.get("from"))
            edge_to = existing_edge.get("target", existing_edge.get("to"))
            edge_relation = existing_edge.get("type", existing_edge.get("relation_type"))
            if (edge_from == from_node_id and 
                edge_to == to_node_id and
                edge_relation == relation_type):
                # Update bestaande relatie
                existing_edge["strength"] = max(existing_edge["strength"], strength)
                existing_edge["updated_at"] = datetime.now().isoformat()
                DataManager.save_json("graph/edges.json", data)
                return existing_edge
        
        # Nieuwe relatie toevoegen
        data["edges"].append(edge)
        DataManager.save_json("graph/edges.json", data)
        
        # Update metadata
        meta = DataManager.load_json("graph/metadata.json")
        meta["total_edges"] = len(data["edges"])
        meta["last_updated"] = datetime.now().isoformat()
        DataManager.save_json("graph/metadata.json", meta)
        
        return edge
    
    @staticmethod
    def get_relations(node_id: str, direction: str = "both") -> List[Dict]:
        """
        Haal alle relaties op voor een node
        
        Args:
            node_id: Node ID
            direction: "outgoing", "incoming", of "both"
        """
        GraphService.initialize_graph()
        data = DataManager.load_json("graph/edges.json")
        
        relations = []
        for edge in data["edges"]:
            # Edges use 'source' and 'target' not 'from' and 'to'
            edge_from = edge.get("source", edge.get("from"))
            edge_to = edge.get("target", edge.get("to"))
            if direction in ["outgoing", "both"] and edge_from == node_id:
                relations.append(edge)
            elif direction in ["incoming", "both"] and edge_to == node_id:
                relations.append(edge)
        
        return relations
    
    @staticmethod
    def get_all_edges() -> List[Dict]:
        """Haal alle edges op"""
        GraphService.initialize_graph()
        data = DataManager.load_json("graph/edges.json")
        return data.get("edges", [])
    
    @staticmethod
    def get_edges_for_node(node_id: str) -> List[Dict]:
        """Haal alle edges voor een specifieke node"""
        return GraphService.get_relations(node_id, "both")
    
    @staticmethod
    def increment_usage(edge_id: str):
        """Verhoog usage count van een relatie (Spark gebruikt deze)"""
        GraphService.initialize_graph()
        data = DataManager.load_json("graph/edges.json")
        
        for edge in data["edges"]:
            if edge["id"] == edge_id:
                edge["usage_count"] = edge.get("usage_count", 0) + 1
                edge["last_used"] = datetime.now().isoformat()
                DataManager.save_json("graph/edges.json", data)
                return True
        
        return False
    
    @staticmethod
    def get_related_nodes(node_id: str, max_depth: int = 2, min_strength: float = 0.3) -> List[Dict]:
        """
        Haal gerelateerde nodes op tot een bepaalde diepte
        
        Returns:
            List van {node: Dict, path: List[str], strength: float}
        """
        GraphService.initialize_graph()
        
        visited = set()
        results = []
        
        def traverse(current_id, depth, path, cumulative_strength):
            if depth > max_depth or current_id in visited:
                return
            
            visited.add(current_id)
            
            # Haal relaties op
            relations = GraphService.get_relations(current_id, "outgoing")
            
            for rel in relations:
                # Use 'strength' field with fallback
                rel_strength = rel.get("strength", 0.5)
                if rel_strength < min_strength:
                    continue
                
                # Edges use 'target' not 'to'
                target_id = rel.get("target", rel.get("to"))
                if not target_id:
                    continue
                    
                target_node = GraphService.get_node(target_id)
                
                if target_node and target_id not in visited:
                    new_strength = cumulative_strength * rel_strength
                    # Use 'type' not 'relation_type'
                    rel_type = rel.get("type", rel.get("relation_type", "related"))
                    results.append({
                        "node": target_node,
                        "path": path + [rel_type],
                        "strength": new_strength,
                        "edge_id": rel["id"]
                    })
                    
                    if depth < max_depth:
                        traverse(target_id, depth + 1, path + [target_node.get("label", target_node.get("titel", ""))], new_strength)
        
        traverse(node_id, 0, [], 1.0)
        
        # Sort op strength
        results.sort(key=lambda x: x["strength"], reverse=True)
        
        return results
    
    @staticmethod
    def find_path(from_node_id: str, to_node_id: str, max_depth: int = 4) -> Optional[List[Dict]]:
        """
        Vind het kortste pad tussen twee nodes (BFS)
        
        Returns:
            List van nodes in het pad, of None als geen pad bestaat
        """
        GraphService.initialize_graph()
        
        if from_node_id == to_node_id:
            return [GraphService.get_node(from_node_id)]
        
        queue = [(from_node_id, [from_node_id])]
        visited = {from_node_id}
        
        while queue:
            current_id, path = queue.pop(0)
            
            if len(path) > max_depth:
                continue
            
            # Haal relaties op
            relations = GraphService.get_relations(current_id, "outgoing")
            
            for rel in relations:
                next_id = rel["to"]
                
                if next_id == to_node_id:
                    # Gevonden!
                    full_path = path + [next_id]
                    return [GraphService.get_node(nid) for nid in full_path]
                
                if next_id not in visited:
                    visited.add(next_id)
                    queue.append((next_id, path + [next_id]))
        
        return None  # Geen pad gevonden
    
    @staticmethod
    def get_graph_stats() -> Dict:
        """Haal statistieken op van de graph"""
        GraphService.initialize_graph()
        
        nodes_data = DataManager.load_json("graph/nodes.json")
        edges_data = DataManager.load_json("graph/edges.json")
        meta = DataManager.load_json("graph/metadata.json")
        
        # Count per type
        node_types = {}
        for node in nodes_data["nodes"]:
            node_type = node.get("type", "unknown")  # Fallback to "unknown"
            node_types[node_type] = node_types.get(node_type, 0) + 1
        
        # Count per source
        sources = {}
        for node in nodes_data["nodes"]:
            source = node.get("source", "unknown")  # Fallback to "unknown"
            sources[source] = sources.get(source, 0) + 1
        
        # Relation stats
        relation_types = {}
        for edge in edges_data["edges"]:
            rel_type = edge.get("type", "unknown")  # Use "type" field (not "relation_type")
            relation_types[rel_type] = relation_types.get(rel_type, 0) + 1
        
        return {
            "total_nodes": len(nodes_data["nodes"]),
            "total_edges": len(edges_data["edges"]),
            "nodes_by_type": node_types,
            "nodes_by_source": sources,
            "relations_by_type": relation_types,
            "last_updated": meta.get("last_updated"),
            "version": meta.get("version")
        }
    
    @staticmethod
    def extract_label_from_content(content: str) -> str:
        """
        Genereer een duidelijk label uit content
        Gebruikt voor auto-labeling van nodes
        
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
        match = re.search(
            r'^([A-Z]\w+(?:\s+\w+)?)\s+is\s+een\s+(.+?)(?:\s+die|\s+dat|$)', 
            first_sentence, 
            re.IGNORECASE
        )
        if match:
            term = match.group(1).strip()
            description = match.group(2).strip()
            desc_words = description.split()[:3]
            return f"{term} ({' '.join(desc_words)})"
        
        # Patroon 2: "Een X is een Y"
        match = re.search(
            r'^(?:Een|De)\s+([A-Z]\w+(?:\s+\w+)?)\s+is\s+(?:een\s+)?(.+?)(?:\s+die|\s+dat|$)', 
            first_sentence, 
            re.IGNORECASE
        )
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
    
    @staticmethod
    def assign_gradatie_from_tags(tags: List[str], user_gradatie: int = 7) -> int:
        """
        Bepaal gradatie op basis van tags en user
        
        1 = Persoonlijk/Familie (hoogste vertrouwen)
        2-3 = Verified/Belangrijk
        4-5 = Algemene kennis
        6-7 = Ongecontroleerd
        """
        tags_lower = [t.lower() for t in tags]
        
        # Familie/Persoonlijk
        if any(tag in tags_lower for tag in ['familie', 'dochter', 'zoon', 'partner', 'persoon']):
            return 1
        
        # Roadkill/Community (Willem)
        if any(tag in tags_lower for tag in ['roadkill', 'willem', 'biografie']):
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
        
        # Default: inherit from user
        return user_gradatie
    
    @staticmethod
    def validate_node(node: Dict) -> Tuple[bool, List[str]]:
        """
        Valideer of een node compleet is
        Returns: (is_valid, list_of_errors)
        """
        errors = []
        
        # Check required fields
        if not node.get('label'):
            errors.append("Label ontbreekt")
        
        if not node.get('content'):
            errors.append("Content ontbreekt")
        
        if not node.get('type'):
            errors.append("Type ontbreekt")
        
        if not node.get('gradatie'):
            errors.append("Gradatie ontbreekt")
        
        if not node.get('created_by_user_id'):
            errors.append("Creator ontbreekt")
        
        return (len(errors) == 0, errors)
    
    @staticmethod
    def check_duplicates(label: str, existing_nodes: List[Dict]) -> List[Dict]:
        """
        Check of een label al bestaat (disambiguation)
        Returns list of similar nodes
        """
        similar = []
        label_lower = label.lower()
        
        for node in existing_nodes:
            node_label = node.get('label', '').lower()
            # Exact match
            if label_lower == node_label:
                similar.append(node)
            # Partial match (eerste woord)
            elif label_lower.split()[0] in node_label:
                similar.append(node)
        
        return similar

