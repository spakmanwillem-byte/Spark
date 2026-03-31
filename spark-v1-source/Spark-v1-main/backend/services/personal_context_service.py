"""
Personal Context Service - Fase 1 MVP
Extracts personen + relaties from conversation text
Stores in user profile without duplicates
"""

import re
import logging
from typing import Dict, List, Optional
from uuid import uuid4
from utils.data_manager import DataManager

logger = logging.getLogger(__name__)

# Relation keywords mapping
RELATION_KEYWORDS = {
    "parent": ["moeder", "vader", "ma", "pa", "mom", "dad", "ouder", "mam"],
    "sibling": ["broer", "zus", "zusje", "broertje", "brother", "sister"],
    "child": ["zoon", "dochter", "kind", "kindje", "son", "daughter"],
    "partner": ["vrouw", "man", "partner", "vriend", "vriendin", "wife", "husband", "boyfriend", "girlfriend"],
    "ex_partner": ["ex", "ex-vrouw", "ex-man", "ex-vriend", "ex-vriendin"],
    "friend": ["vriend", "vriendin", "maat", "buddy", "friend"],
    "colleague": ["collega", "baas", "manager", "colleague", "coworker"],
    "family": ["oma", "opa", "tante", "oom", "neef", "nicht", "grandma", "grandpa", "aunt", "uncle", "cousin"]
}

class PersonalContextService:
    """
    Minimal service for personal context management
    Phase 1: Only person + relation extraction
    """
    
    @staticmethod
    def _get_user_context_path(user_id: str) -> str:
        """Get path for user's context data"""
        return f"users/{user_id}/personal_context.json"
    
    def analyze_text(self, text: str, user_id: str) -> List[Dict]:
        """
        Extract persons and their relations from text
        WITH DEBUG LOGGING for observatie
        
        Args:
            text: Conversation text
            user_id: Who is saying this (source)
        
        Returns:
            List of extracted entities with relations
        """
        text_lower = text.lower()
        extracted = []
        
        # === DEBUG: Log input ===
        logger.info(f"[CONTEXT DEBUG] ═══════════════════════════════════════")
        logger.info(f"[CONTEXT DEBUG] Input: \"{text}\"")
        logger.info(f"[CONTEXT DEBUG] Source: {user_id}")
        
        # Pattern 1: "X is mijn Y" (about named person)
        # Example: "Lotus is mijn ex"
        pattern_named = r"(\w+)\s+is\s+mijn\s+(\w+)"
        matches_named = re.findall(pattern_named, text_lower)
        
        if matches_named:
            logger.info(f"[CONTEXT DEBUG] Pattern MATCHED: \"X is mijn Y\"")
        
        for name, role in matches_named:
            relation = self._detect_relation(role)
            
            # === DEBUG: Log match details ===
            logger.info(f"[CONTEXT DEBUG]   → Extracted: name=\"{name.capitalize()}\", role=\"{role}\"")
            
            if relation:
                logger.info(f"[CONTEXT DEBUG]   → Relation: \"{relation}\" (keyword: \"{role}\")")
                logger.info(f"[CONTEXT DEBUG]   → STORED: source={user_id}, about={name.capitalize()}, relation={relation}")
                
                extracted.append({
                    "source": user_id,
                    "about": name.capitalize(),  # Person name
                    "role": role,
                    "relation": relation,
                    "aliases": [role, name.capitalize()]
                })
            else:
                logger.info(f"[CONTEXT DEBUG]   → SKIPPED: \"{role}\" not a known relation keyword")
        
        # Pattern 2: "mijn Y" or "m'n Y" (no name mentioned)
        # Example: "mijn moeder belde"
        patterns_unnamed = [
            (r"\bmijn\s+(\w+)", "mijn X"),
            (r"\bm'n\s+(\w+)", "m'n X"),
            (r"\bde\s+(\w+)\s+van\s+me", "de X van me"),
            (r"\bmet\s+mijn\s+(\w+)", "met mijn X"),  # "ik sprak met mijn vader"
            (r"\bvan\s+mijn\s+(\w+)", "van mijn X"),  # "het huis van mijn moeder"
        ]
        
        for pattern, pattern_name in patterns_unnamed:
            matches = re.findall(pattern, text_lower)
            
            if matches:
                logger.info(f"[CONTEXT DEBUG] Pattern MATCHED: \"{pattern_name}\"")
            
            for role in matches:
                role = role.strip()
                relation = self._detect_relation(role)
                
                # === DEBUG: Log match details ===
                logger.info(f"[CONTEXT DEBUG]   → Extracted: role=\"{role}\" (no name)")
                
                # Check if not already extracted with name
                already_extracted = any(e["role"] == role and e.get("about") for e in extracted)
                
                if already_extracted:
                    logger.info(f"[CONTEXT DEBUG]   → SKIPPED: already extracted with name")
                    continue
                
                if relation:
                    logger.info(f"[CONTEXT DEBUG]   → Relation: \"{relation}\" (keyword: \"{role}\")")
                    logger.info(f"[CONTEXT DEBUG]   → STORED: source={user_id}, about=null, relation={relation}")
                    
                    extracted.append({
                        "source": user_id,
                        "about": None,  # No name mentioned
                        "role": role,
                        "relation": relation,
                        "aliases": [role]
                    })
                else:
                    logger.info(f"[CONTEXT DEBUG]   → SKIPPED: \"{role}\" not a known relation keyword")
        
        # === DEBUG: Summary ===
        logger.info(f"[CONTEXT DEBUG] ───────────────────────────────────────")
        logger.info(f"[CONTEXT DEBUG] RAW EXTRACTED: {len(extracted)} entities (before dedup)")
        
        # === DEDUPLICATION: Remove exact duplicates from same extraction ===
        unique_extracted = []
        seen = set()
        for entity in extracted:
            # Create unique key: role + about + relation
            key = (entity['role'], entity.get('about'), entity['relation'])
            if key not in seen:
                seen.add(key)
                unique_extracted.append(entity)
            else:
                logger.info(f"[CONTEXT DEBUG]   → Removed duplicate: {entity['role']} ({entity['relation']})")
        
        extracted = unique_extracted
        
        logger.info(f"[CONTEXT DEBUG] TOTAL EXTRACTED: {len(extracted)} entities (after dedup)")
        for i, entity in enumerate(extracted, 1):
            about_str = f"\"{entity['about']}\"" if entity.get("about") else "null"
            logger.info(f"[CONTEXT DEBUG]   {i}. {entity['relation']} → about={about_str}, role=\"{entity['role']}\"")
        logger.info(f"[CONTEXT DEBUG] ═══════════════════════════════════════")
        
        return extracted
    
    def _detect_relation(self, role: str) -> Optional[str]:
        """Detect relation type from role keyword"""
        for relation, keywords in RELATION_KEYWORDS.items():
            if role in keywords:
                return relation
        return None
    
    def update_user_context(self, user_id: str, extracted_entities: List[Dict]) -> Dict:
        """
        Update user profile with extracted entities
        Merges duplicates, updates aliases
        
        Args:
            user_id: User identifier
            extracted_entities: List of entities from analyze_text()
        
        Returns:
            Updated user profile
        """
        # Load existing context
        try:
            user_profile = DataManager.load_data(self._get_user_context_path(user_id))
        except:
            # Create new profile
            user_profile = {
                "user_id": user_id,
                "entities": []
            }
        
        existing_entities = user_profile.get("entities", [])
        
        # Process each extracted entity
        for new_entity in extracted_entities:
            merged = False
            
            # Check if entity already exists (by role or alias)
            for existing in existing_entities:
                if self._is_same_entity(existing, new_entity):
                    # MERGE: Update aliases, increment mention count
                    self._merge_entity(existing, new_entity)
                    merged = True
                    logger.info(f"[CONTEXT] Merged entity: {new_entity['role']} → {existing['role']}")
                    break
            
            # Add new entity if not merged
            if not merged:
                new_entity["id"] = str(uuid4())
                new_entity["mention_count"] = 1
                existing_entities.append(new_entity)
                logger.info(f"[CONTEXT] Added new entity: {new_entity['role']} ({new_entity['relation']})")
        
        # Save updated profile
        user_profile["entities"] = existing_entities
        DataManager.save_data(self._get_user_context_path(user_id), user_profile)
        
        return user_profile
    
    def _is_same_entity(self, entity1: Dict, entity2: Dict) -> bool:
        """
        Check if two entities are the same person
        Based on:
        1. Same source (perspective-based)
        2. Same relation type OR same "about" name
        3. Role/alias match
        """
        # Must be from same source (same person's perspective)
        if entity1.get("source") != entity2.get("source"):
            return False
        
        # If both have "about" names, check if same person
        about1 = entity1.get("about")
        about2 = entity2.get("about")
        
        if about1 and about2:
            # Same named person
            if about1.lower() == about2.lower():
                return True
        
        # Same relation type required (if no names)
        if not about1 and not about2:
            if entity1["relation"] != entity2["relation"]:
                return False
        
        # Check role match
        if entity1["role"] == entity2["role"]:
            return True
        
        # Check alias match
        aliases1 = set(entity1.get("aliases", []))
        aliases2 = set(entity2.get("aliases", []))
        
        if aliases1 & aliases2:  # Intersection
            return True
        
        # Check if role of one is in aliases of other
        if entity2["role"] in aliases1 or entity1["role"] in aliases2:
            return True
        
        return False
    
    def _merge_entity(self, existing: Dict, new: Dict):
        """
        Merge new entity data into existing entity
        Updates aliases, about name, and mention count
        """
        # Add new aliases
        existing_aliases = set(existing.get("aliases", []))
        new_aliases = set(new.get("aliases", []))
        existing["aliases"] = list(existing_aliases | new_aliases)
        
        # Update "about" if new mention has a name and existing doesn't
        if new.get("about") and not existing.get("about"):
            existing["about"] = new["about"]
            logger.info(f"[CONTEXT] Added name to entity: {new['about']}")
        
        # Increment mention count
        existing["mention_count"] = existing.get("mention_count", 0) + 1
        
        # === ORGANIC QUESTION OPPORTUNITY ===
        self._detect_question_opportunity(existing)
    
    def _detect_question_opportunity(self, entity: Dict):
        """
        Detect when it's a good moment to ask a clarifying question
        ONLY LOGS - doesn't actually ask yet
        
        This helps identify natural conversation moments for profile completion
        """
        opportunities = []
        
        # Opportunity 1: Entity without name (about=null) after first mention
        if entity.get("about") is None and entity.get("mention_count", 0) >= 2:
            opportunities.append({
                "type": "missing_name",
                "question": f"Hoe heet je {entity['role']}?",
                "reason": f"Mentioned {entity['mention_count']}x without name",
                "priority": "medium",
                "entity_id": entity.get("id")
            })
        
        # Opportunity 2: Frequently mentioned without name (high priority)
        if entity.get("about") is None and entity.get("mention_count", 0) >= 5:
            opportunities.append({
                "type": "frequent_unnamed",
                "question": f"Je hebt het vaak over je {entity['role']}, hoe heet hij/zij?",
                "reason": f"Mentioned {entity['mention_count']}x - frequent without name",
                "priority": "high",
                "entity_id": entity.get("id")
            })
        
        # Opportunity 3: Just got a name (could ask follow-up)
        if entity.get("about") and entity.get("mention_count", 0) == 1:
            opportunities.append({
                "type": "name_revealed",
                "question": None,  # Follow-up depends on context
                "reason": f"User just mentioned name '{entity['about']}' - potential for natural follow-up",
                "priority": "low",
                "entity_id": entity.get("id")
            })
        
        # === LOG OPPORTUNITIES ===
        for opp in opportunities:
            logger.info(f"[CONTEXT OPPORTUNITY] ═══════════════════════════════")
            logger.info(f"[CONTEXT OPPORTUNITY] Type: {opp['type']}")
            logger.info(f"[CONTEXT OPPORTUNITY] Priority: {opp['priority'].upper()}")
            logger.info(f"[CONTEXT OPPORTUNITY] Entity: {entity['role']} (mention_count={entity['mention_count']})")
            if opp['question']:
                logger.info(f"[CONTEXT OPPORTUNITY] Suggested Question: \"{opp['question']}\"")
            logger.info(f"[CONTEXT OPPORTUNITY] Reason: {opp['reason']}")
            logger.info(f"[CONTEXT OPPORTUNITY] ═══════════════════════════════")
    
    def get_user_entities(self, user_id: str) -> List[Dict]:
        """Get all entities for a user"""
        try:
            user_profile = DataManager.load_data(self._get_user_context_path(user_id))
            return user_profile.get("entities", [])
        except:
            return []
    
    def get_entity_by_role(self, user_id: str, role: str) -> Optional[Dict]:
        """Get specific entity by role"""
        entities = self.get_user_entities(user_id)
        for entity in entities:
            if entity["role"].lower() == role.lower():
                return entity
            if role.lower() in [a.lower() for a in entity.get("aliases", [])]:
                return entity
        return None
    
    def delete_entity(self, user_id: str, entity_id: str) -> bool:
        """Delete an entity from user profile"""
        try:
            user_profile = DataManager.load_data(self._get_user_context_path(user_id))
            original_count = len(user_profile.get("entities", []))
            user_profile["entities"] = [e for e in user_profile["entities"] if e.get("id") != entity_id]
            DataManager.save_data(self._get_user_context_path(user_id), user_profile)
            return len(user_profile["entities"]) < original_count
        except:
            return False
    
    def clear_user_context(self, user_id: str) -> bool:
        """Clear all entities for a user"""
        try:
            user_profile = {
                "user_id": user_id,
                "entities": []
            }
            DataManager.save_data(self._get_user_context_path(user_id), user_profile)
            return True
        except:
            return False
