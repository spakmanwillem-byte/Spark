"""
Relation Detection Service - Detecteert automatisch verbanden tussen nodes
Gebruikt: woord overlap, tags, topics uit pattern detection, semantic similarity
"""
from typing import Dict, List, Tuple
from services.graph_service import GraphService
from services.pattern_detection_service import PatternDetectionService
from collections import Counter
import re


class RelationDetectionService:
    """Detecteert automatisch relaties tussen content"""
    
    # Thresholds
    MIN_STRENGTH = 0.25  # Verlaagd voor context matches
    TAG_MATCH_WEIGHT = 0.35
    TOPIC_MATCH_WEIGHT = 0.25
    WORD_OVERLAP_WEIGHT = 0.15
    KEYWORD_MATCH_WEIGHT = 0.4
    CONTEXT_MATCH_WEIGHT = 0.5  # NIEUW: Voor semantic/context matching
    
    @staticmethod
    def detect_relations_for_node(node_id: str, max_relations: int = 10) -> List[Dict]:
        """
        Detecteer relaties voor een nieuwe node
        
        Returns:
            List van {target_node_id, relation_type, strength, reason}
        """
        node = GraphService.get_node(node_id)
        if not node:
            return []
        
        # Haal alle andere nodes op
        all_nodes = GraphService.get_all_nodes()
        other_nodes = [n for n in all_nodes if n["id"] != node_id]
        
        # Score elke potentiële relatie
        scored_relations = []
        
        for other_node in other_nodes:
            score, relation_type, reasons = RelationDetectionService._calculate_relation_score(
                node, other_node
            )
            
            if score >= RelationDetectionService.MIN_STRENGTH:
                scored_relations.append({
                    "target_node_id": other_node["id"],
                    "relation_type": relation_type,
                    "strength": score,
                    "reasons": reasons
                })
        
        # Sort op score en return top N
        scored_relations.sort(key=lambda x: x["strength"], reverse=True)
        return scored_relations[:max_relations]
    
    @staticmethod
    def _calculate_relation_score(node_a: Dict, node_b: Dict) -> Tuple[float, str, List[str]]:
        """
        Bereken similarity score tussen twee nodes
        
        Returns:
            (score, relation_type, reasons)
        """
        score = 0.0
        reasons = []
        
        # 1. Tag overlap
        tags_a = set(node_a.get("tags", []))
        tags_b = set(node_b.get("tags", []))
        tag_overlap = tags_a & tags_b
        
        if tag_overlap:
            tag_score = len(tag_overlap) / max(len(tags_a), len(tags_b), 1)
            score += tag_score * RelationDetectionService.TAG_MATCH_WEIGHT
            reasons.append(f"Tags match: {', '.join(tag_overlap)}")
        
        # 2. Topic extraction en match (gebruik pattern detection)
        topics_a = RelationDetectionService._extract_topics(node_a["content"])
        topics_b = RelationDetectionService._extract_topics(node_b["content"])
        
        topic_overlap = set(topics_a) & set(topics_b)
        if topic_overlap:
            topic_score = len(topic_overlap) / max(len(topics_a), len(topics_b), 1)
            score += topic_score * RelationDetectionService.TOPIC_MATCH_WEIGHT
            reasons.append(f"Topics match: {', '.join(list(topic_overlap)[:3])}")
        
        # 3. Keyword matching in content
        keywords_a = RelationDetectionService._extract_keywords(node_a["titel"])
        content_b_lower = node_b["content"].lower()
        
        keyword_matches = [kw for kw in keywords_a if kw in content_b_lower]
        if keyword_matches:
            score += RelationDetectionService.KEYWORD_MATCH_WEIGHT
            reasons.append(f"Keywords found: {', '.join(keyword_matches[:2])}")
        
        # 4. Word overlap (simpel)
        words_a = set(RelationDetectionService._tokenize(node_a["content"]))
        words_b = set(RelationDetectionService._tokenize(node_b["content"]))
        
        word_overlap = words_a & words_b
        if len(word_overlap) > 5:  # Minstens 5 woorden overlap
            overlap_ratio = len(word_overlap) / max(len(words_a), len(words_b), 1)
            score += overlap_ratio * RelationDetectionService.WORD_OVERLAP_WEIGHT
            reasons.append(f"{len(word_overlap)} woorden overlap")
        
        # 5. 🧠 NIEUW: Context/Semantic matching
        context_score, context_reason = RelationDetectionService._check_context_similarity(
            node_a, node_b
        )
        if context_score > 0:
            score += context_score * RelationDetectionService.CONTEXT_MATCH_WEIGHT
            reasons.append(context_reason)
        
        # 6. Bepaal relation type op basis van context
        relation_type = RelationDetectionService._determine_relation_type(
            node_a, node_b, reasons
        )
        
        return (min(score, 1.0), relation_type, reasons)
    
    @staticmethod
    def _determine_relation_type(node_a: Dict, node_b: Dict, reasons: List[str]) -> str:
        """Bepaal het type relatie op basis van context"""
        
        # Heuristics voor relation types
        content_a = node_a["content"].lower()
        content_b = node_b["content"].lower()
        
        # "part_of" - als A onderdeel is van B
        if any(word in content_a for word in ["onderdeel", "deel van", "binnen"]):
            return "part_of"
        
        # "example_of" - als A voorbeeld is van B
        if any(word in content_a for word in ["bijvoorbeeld", "bijv", "zoals"]):
            return "example_of"
        
        # "leads_to" - als A leidt tot B
        if any(word in content_a for word in ["leidt tot", "resulteert in", "zorgt voor"]):
            return "leads_to"
        
        # "contrasts_with" - als tegenstelling
        if any(word in content_a for word in ["maar", "echter", "daarentegen", "in tegenstelling"]):
            return "contrasts_with"
        
        # "belongs_to" - als A behoort tot categorie B
        if node_b["type"] in ["norm", "waarde"] and node_a["type"] == "concept":
            return "belongs_to"
        
        # Default: related_to
        return "related_to"
    
    @staticmethod
    def _extract_topics(text: str) -> List[str]:
        """Extract topics uit tekst (gebruik dezelfde logica als PatternDetectionService)"""
        return PatternDetectionService._extract_topics(text)
    
    @staticmethod
    def _extract_keywords(text: str) -> List[str]:
        """Extract belangrijke keywords uit tekst"""
        # Verwijder stopwoorden
        stopwords = {'de', 'het', 'een', 'en', 'van', 'in', 'op', 'is', 'dat', 'die', 
                    'aan', 'voor', 'met', 'als', 'zijn', 'er', 'maar', 'om', 'te'}
        
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [w for w in words if w not in stopwords and len(w) > 3]
        
        return keywords[:5]  # Top 5
    
    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """Simpele tokenizer"""
        stopwords = {'de', 'het', 'een', 'en', 'van', 'in', 'op', 'is', 'dat', 'die', 
                    'aan', 'voor', 'met', 'als', 'zijn', 'er', 'maar', 'om', 'te', 
                    'ze', 'bij', 'ook', 'naar', 'kan', 'wat', 'niet'}
        
        words = re.findall(r'\b\w+\b', text.lower())
        return [w for w in words if w not in stopwords and len(w) > 3]
    
    @staticmethod
    def _check_context_similarity(node_a: Dict, node_b: Dict) -> Tuple[float, str]:
        """
        🧠 Check semantic/context similarity tussen nodes
        Gebruikt concepten en betekenis ipv alleen woorden
        
        Returns:
            (score 0-1, reason string)
        """
        content_a = node_a["content"].lower()
        content_b = node_b["content"].lower()
        titel_a = node_a["titel"].lower()
        titel_b = node_b["titel"].lower()
        
        # Concept clusters - woorden die semantisch gerelateerd zijn
        concept_clusters = {
            "helpen": ["helpen", "ondersteunen", "bijstaan", "zorg", "opvang", "steun", "hulp"],
            "community": ["community", "gemeenschap", "samen", "verbinding", "groep", "mensen"],
            "leren": ["leren", "kennis", "educatie", "ontwikkeling", "groei", "opleiding"],
            "inclusie": ["inclusief", "iedereen", "toegankelijk", "open", "welkom", "acceptatie"],
            "gaming": ["game", "gamen", "gaming", "spel", "spelen", "gamer"],
            "creativiteit": ["creatief", "kunst", "maken", "bouwen", "design", "creëren"],
            "ondernemerschap": ["business", "bedrijf", "ondernemen", "startup", "verkopen"],
            "technologie": ["tech", "technologie", "software", "app", "platform", "code"],
            "gezondheid": ["gezond", "welzijn", "mentaal", "fysiek", "therapie", "behandeling"],
            "financieel": ["geld", "betalen", "inkomen", "budget", "financieel", "kosten"]
        }
        
        # Check welke concepten in elke node zitten
        concepts_a = set()
        concepts_b = set()
        
        for concept_name, keywords in concept_clusters.items():
            if any(kw in content_a or kw in titel_a for kw in keywords):
                concepts_a.add(concept_name)
            if any(kw in content_b or kw in titel_b for kw in keywords):
                concepts_b.add(concept_name)
        
        # Concepten overlap?
        concept_overlap = concepts_a & concepts_b
        
        if concept_overlap:
            score = len(concept_overlap) / max(len(concepts_a), len(concepts_b), 1)
            concept_names = ", ".join(concept_overlap)
            return (score, f"Context match: {concept_names}")
        
        # Geen concept match
        return (0.0, "")
    
    @staticmethod
    def auto_detect_and_create_relations(node_id: str) -> int:
        """
        Detecteer en creëer relaties automatisch voor een node
        
        Returns:
            Aantal gecreëerde relaties
        """
        relations = RelationDetectionService.detect_relations_for_node(node_id)
        
        created_count = 0
        for rel in relations:
            try:
                GraphService.add_relation(
                    from_node_id=node_id,
                    to_node_id=rel["target_node_id"],
                    relation_type=rel["relation_type"],
                    strength=rel["strength"],
                    auto_detected=True,
                    metadata={"reasons": rel["reasons"]}
                )
                created_count += 1
            except Exception as e:
                print(f"[RELATION ERROR] {str(e)}")
        
        return created_count
    
    @staticmethod
    def scan_all_nodes_for_relations():
        """Scan alle bestaande nodes en maak relaties"""
        all_nodes = GraphService.get_all_nodes()
        
        total_created = 0
        for node in all_nodes:
            count = RelationDetectionService.auto_detect_and_create_relations(node["id"])
            total_created += count
        
        return total_created
