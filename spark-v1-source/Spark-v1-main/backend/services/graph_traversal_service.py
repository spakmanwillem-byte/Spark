"""
Graph Traversal Service - Helpt Spark verbanden vinden en gebruiken
Focus: Simpel en snel voor real-time gesprekken
"""
from typing import Dict, List, Optional, Tuple
from services.graph_service import GraphService
from services.pattern_detection_service import PatternDetectionService
from services.personality_service import PersonalityService


class GraphTraversalService:
    """Zoek en gebruik verbanden in gesprekken"""
    
    @staticmethod
    def find_relevant_connections(message: str, max_connections: int = 5) -> List[Dict]:
        """
        Vind relevante graph connections voor een bericht
        
        Args:
            message: User bericht
            max_connections: Max aantal connections om te retourneren (default 5)
            
        Returns:
            List van {from_node, to_node, relation_type, strength, context_text}
        """
        # 1. Extract topics uit bericht
        analysis = PatternDetectionService.analyze_message(message)
        topics = analysis.get("topics", [])
        
        if not topics:
            return []
        
        # 🔧 FIX: Filter Nederlandse stopwoorden om irrelevante matches te voorkomen
        stopwoorden = {
            'de', 'het', 'een', 'en', 'van', 'in', 'op', 'voor', 'met', 'aan', 'door',
            'over', 'naar', 'uit', 'bij', 'om', 'er', 'te', 'dat', 'dit', 'is', 'zijn',
            'als', 'maar', 'wat', 'wie', 'waar', 'wanneer', 'hoe', 'waarom',
            'vertel', 'geef', 'laat', 'toon', 'leg', 'uit', 'kan', 'wil', 'moet'
        }
        
        filtered_topics = [t for t in topics if t.lower() not in stopwoorden and len(t) > 2]
        
        if not filtered_topics:
            return []
        
        # 2. Zoek nodes die matchen met topics
        matching_nodes = []
        for topic in filtered_topics[:3]:  # Max 3 topics om snel te blijven
            results = GraphService.search_nodes(topic)
            matching_nodes.extend(results[:2])  # Max 2 results per topic
        
        if not matching_nodes:
            return []
        
        # 3. Voor elke matching node, haal gerelateerde nodes op
        all_connections = []
        
        for node in matching_nodes[:3]:  # Max 3 nodes om te verwerken
            related = GraphService.get_related_nodes(
                node["id"], 
                max_depth=2,  # Niet te diep
                min_strength=0.4  # Alleen sterke relaties
            )
            
            for rel in related[:3]:  # Top 3 per node
                # Maak context tekst
                context_text = GraphTraversalService._build_connection_text(
                    from_node=node,
                    to_node=rel["node"],
                    relation_path=rel["path"],
                    strength=rel["strength"]
                )
                
                all_connections.append({
                    "from_node": node,
                    "to_node": rel["node"],
                    "relation_type": rel["path"][0] if rel["path"] else "related_to",
                    "strength": rel["strength"],
                    "context_text": context_text,
                    "edge_id": rel.get("edge_id")
                })
        
        # 4. Sort op strength en return top N
        all_connections.sort(key=lambda x: x["strength"], reverse=True)
        return all_connections[:max_connections]
    
    @staticmethod
    def _build_connection_text(from_node: Dict, to_node: Dict, relation_path: List[str], strength: float) -> str:
        """Bouw een natuurlijke tekst voor de connectie"""
        
        relation_type = relation_path[0] if relation_path else "related_to"
        
        # Natuurlijke taal per relation type
        # Use 'label' field (nodes use 'label' not 'titel')
        from_label = from_node.get('label', from_node.get('titel', 'item'))
        to_label = to_node.get('label', to_node.get('titel', 'item'))
        
        relation_phrases = {
            "related_to": f"{from_label} hangt samen met {to_label}",
            "part_of": f"{from_label} is onderdeel van {to_label}",
            "leads_to": f"{from_label} leidt tot {to_label}",
            "caused_by": f"{from_label} wordt veroorzaakt door {to_label}",
            "belongs_to": f"{from_label} behoort tot {to_label}",
            "example_of": f"{from_label} is een voorbeeld van {to_label}",
            "contrasts_with": f"{from_label} contrasteert met {to_label}"
        }
        
        return relation_phrases.get(relation_type, f"{from_label} is gerelateerd aan {to_label}")
    
    @staticmethod
    def build_graph_context_for_spark(message: str) -> str:
        """
        Bouw een compacte context string die Spark kan gebruiken
        
        Returns:
            String met graph-based context, of empty string als geen relevante info
        """
        connections = GraphTraversalService.find_relevant_connections(message, max_connections=3)
        
        if not connections:
            return ""
        
        # Bouw context
        context_parts = ["🔗 Graph Context (verbanden):"]
        
        for conn in connections:
            context_parts.append(f"  • {conn['context_text']}")
        
        return "\n".join(context_parts)
    
    @staticmethod
    def suggest_conversation_bridge(current_topic: str, user_profile: Dict = None) -> Optional[str]:
        """
        Suggereer een conversatie-brug op basis van graph
        
        Bijvoorbeeld: "Dit doet me denken aan..."
        
        Returns:
            Suggestie string of None
        """
        # Zoek node voor current topic
        results = GraphService.search_nodes(current_topic)
        
        if not results:
            return None
        
        current_node = results[0]
        
        # Haal sterk gerelateerde nodes op
        related = GraphService.get_related_nodes(current_node["id"], max_depth=1, min_strength=0.6)
        
        if not related:
            return None
        
        # Kies beste relatie
        best = related[0]
        
        # Use 'label' field (nodes use 'label' not 'titel')
        best_label = best['node'].get('label', best['node'].get('titel', 'dit'))
        
        # Verschillende suggestie types
        suggestions = [
            f"Dit doet me denken aan {best_label}.",
            f"Interessant! Dat raakt aan {best_label}.",
            f"Dat hangt samen met wat je eerder zei over {best_label}.",
        ]
        
        # Als het naar user profile linkt, speciale suggestie
        if best["node"].get("source") == "user_note" and user_profile:
            if "need" in best_label.lower():
                return f"Dit past bij jouw need om {user_profile.get('profile', {}).get('need', 'impact te maken')}."
            elif "believe" in best_label.lower():
                return f"Dat sluit aan bij wat je gelooft: {user_profile.get('profile', {}).get('believe', 'iedereen verdient een kans')}."
        
        # Return willekeurige suggestie
        import random
        return random.choice(suggestions)
    
    @staticmethod
    def mark_connection_used(edge_id: str):
        """Markeer dat een relatie is gebruikt (increment usage_count)"""
        if edge_id:
            GraphService.increment_usage(edge_id)
    
    @staticmethod
    def check_norms_and_values_availability() -> Tuple[bool, str]:
        """
        Check of Spark normen en waarden heeft om mee te werken
        
        Returns:
            (has_norms_and_values: bool, message: str)
        """
        norms = PersonalityService.get_all_norms()
        values = PersonalityService.get_all_values()
        
        has_norms = len(norms) > 0
        has_values = len(values) > 0
        
        if not has_norms and not has_values:
            message = "\n\n💡 **Admin Willem:** Ik heb nog geen normen en waarden ingesteld. Wil je er een paar toevoegen in het Admin-paneel zodat ik ze kan gebruiken in mijn antwoorden?"
            return False, message
        elif not has_norms:
            # Er zijn waarden, maar geen normen - lichte suggestie
            message = f"\n\n💡 **Tip:** Ik heb {len(values)} waarden om mijn antwoorden te vormen, maar nog geen normen. Je kunt normen toevoegen in het Admin-paneel voor nog rijkere context."
            return True, message
        elif not has_values:
            # Er zijn normen, maar geen waarden
            message = f"\n\n💡 **Tip:** Ik heb {len(norms)} normen, maar nog geen waarden. Je kunt waarden toevoegen in het Admin-paneel voor completere antwoorden."
            return True, message
        else:
            # Alles is aanwezig
            return True, ""
    
    @staticmethod
    def get_norms_and_values_context() -> str:
        """
        Haal normen en waarden op als context voor Spark
        
        Returns:
            String met normen/waarden context, of empty als niet beschikbaar
        """
        norms = PersonalityService.get_all_norms()
        values = PersonalityService.get_all_values()
        
        if not norms and not values:
            return ""
        
        context_parts = []
        
        if values:
            context_parts.append("🌟 Mijn Kernwaarden:")
            for value in values[:3]:  # Max 3 voor compactheid
                belangrijkheid = value.get("belangrijkheid", 3)
                if belangrijkheid >= 4:  # Alleen belangrijke waarden
                    context_parts.append(f"  • {value['waarde']}: {value['beschrijving']}")
        
        if norms:
            context_parts.append("\n📋 Mijn Normen:")
            for norm in norms[:3]:  # Max 3
                belangrijkheid = norm.get("belangrijkheid", 3)
                if belangrijkheid >= 4:
                    context_parts.append(f"  • {norm['norm']}: {norm['beschrijving']}")
        
        if context_parts:
            return "\n".join(context_parts)
        
        return ""
