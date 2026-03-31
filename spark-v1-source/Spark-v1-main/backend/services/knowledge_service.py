from typing import List, Dict, Optional
from utils.data_manager import DataManager
from utils.logger import SparkLogger
from models.knowledge import KnowledgeEntry, KnowledgeCreate
import logging

# Dedicated logger voor snap creation debugging
snap_logger = logging.getLogger('snap_creation')
snap_logger.setLevel(logging.DEBUG)

class KnowledgeService:
    @staticmethod
    def add_knowledge(knowledge_create: KnowledgeCreate) -> KnowledgeEntry:
        """
        Add new knowledge entry
        """
        entries = DataManager.load_knowledge()
        
        # Create new entry
        new_entry = KnowledgeEntry(
            begrip=knowledge_create.begrip,
            betekenis=knowledge_create.betekenis,
            categorie=knowledge_create.categorie or "algemeen",
            bron=knowledge_create.bron
        )
        
        entries.append(new_entry.model_dump())
        DataManager.save_knowledge(entries)
        
        # Log
        SparkLogger.log_new_word(new_entry.begrip, new_entry.betekenis, new_entry.bron)
        
        return new_entry
    
    @staticmethod
    def search_knowledge(query: str) -> List[Dict]:
        """
        Search for knowledge
        """
        entries = DataManager.load_knowledge()
        query_lower = query.lower()
        
        results = [
            entry for entry in entries
            if query_lower in entry.get("begrip", "").lower() or
               query_lower in entry.get("betekenis", "").lower()
        ]
        
        return results
    
    @staticmethod
    def get_all_knowledge() -> List[Dict]:
        """
        Get all knowledge entries
        """
        return DataManager.load_knowledge()
    
    @staticmethod
    def increment_usage(knowledge_id: str) -> bool:
        """
        Increment usage count for a knowledge entry
        Track which entries are most chosen in disambiguation
        """
        data = DataManager.load_json("learned_knowledge/knowledge_base.json")
        entries = data.get("knowledge_entries", [])
        
        for entry in entries:
            if entry.get("id") == knowledge_id:
                # Initialize usage_count if not exists
                if "usage_count" not in entry:
                    entry["usage_count"] = 0
                entry["usage_count"] += 1
                
                # Save
                data["knowledge_entries"] = entries
                DataManager.save_json("learned_knowledge/knowledge_base.json", data)
                return True
        
        return False
    
    @staticmethod
    def record_feedback(knowledge_id: str, was_helpful: bool) -> bool:
        """
        Record user feedback on knowledge entry
        """
        data = DataManager.load_json("learned_knowledge/knowledge_base.json")
        entries = data.get("knowledge_entries", [])
        
        for entry in entries:
            if entry.get("id") == knowledge_id:
                # Initialize feedback
                if "feedback" not in entry:
                    entry["feedback"] = {"helpful": 0, "not_helpful": 0}
                
                if was_helpful:
                    entry["feedback"]["helpful"] += 1
                else:
                    entry["feedback"]["not_helpful"] += 1
                
                # Calculate score
                total = entry["feedback"]["helpful"] + entry["feedback"]["not_helpful"]
                entry["feedback"]["score"] = entry["feedback"]["helpful"] / total if total > 0 else 0.5
                
                # Save
                data["knowledge_entries"] = entries
                DataManager.save_json("learned_knowledge/knowledge_base.json", data)
                return True
        
        return False
    
    @staticmethod
    def log_unknown_word(word: str, context: str, user_naam: str):
        """
        Log word that Spark doesn't understand
        """
        SparkLogger.log_unknown_word(word, context, user_naam)
    
    @staticmethod
    def create_unanswered_question(question: str, asked_by: str) -> KnowledgeEntry:
        """
        Create a knowledge entry for a question Spark couldn't answer.
        Admin can later fill in the meaning or delete it.
        
        Now uses concept extraction and normalization to store clean concepts instead of full questions.
        """
        import uuid
        from datetime import datetime
        from config.dutch_stopwords import extract_concept_from_input, normalize_concept
        
        entries = DataManager.load_knowledge()
        
        # STEP 1: Extract concept from question
        extracted = extract_concept_from_input(question)
        if extracted:
            # Normalize the concept
            begrip = normalize_concept(extracted)
            SparkLogger.log_system_event(f"📝 Concept extracted from question: '{question}' → '{begrip}'")
        else:
            # Fallback: use original question if no concept could be extracted
            begrip = question
            SparkLogger.log_system_event(f"⚠️ Could not extract concept, using full question: '{question}'")
        
        # Check if this concept already exists (avoid duplicates)
        existing = [e for e in entries if e.get("begrip", "").lower() == begrip.lower()]
        if existing:
            return None  # Already exists
        
        # Create entry with empty meaning
        new_entry = {
            "id": str(uuid.uuid4()),
            "begrip": begrip,
            "lagen": {
                "laag1": "",  # Empty - admin will fill this
                "laag2": "",
                "laag3": ""
            },
            "tags": ["onbeantwoord", "user-vraag"],
            "gevraagd_door": asked_by,
            "gevraagd_op": datetime.now().isoformat(),
            "status": "pending",
            "original_question": question  # Store original for reference
        }
        
        entries.append(new_entry)
        DataManager.save_knowledge(entries)
        
        SparkLogger.log_system_event(f"Nieuwe onbeantwoorde vraag: '{begrip}' (van: '{question}') - {asked_by}")
        
        return new_entry
    
    @staticmethod
    def create_knowledge_snap(concept: str, context: str, user_naam: str, 
                              user_id: Optional[str] = None,
                              is_sentence_snap: bool = False,
                              needs_confirmation: bool = False,
                              similar_to: Optional[Dict] = None) -> Optional[Dict]:
        """
        Create a 'knowledge snap' - a placeholder knowledge entry for an unknown concept.
        
        Args:
            concept: The concept or sentence to create a snap for
            context: The original message context
            user_naam: User who triggered the snap (or "anonymous_xxx" for guests)
            user_id: User ID (None for anonymous guests)
            is_sentence_snap: If True, this is a CONTEXT ZIN (always save, no duplicate check)
            needs_confirmation: If True, this WOORD needs admin confirmation (possible duplicate)
            similar_to: Dict with info about similar existing entry
        
        WOORDEN: Check duplicates, ask confirmation if similar
        ZINNEN: Always save (except exact duplicates), no fuzzy matching
        GUESTS: Can contribute too! Marked with "anonymous" + session_id
        """
        import uuid
        from datetime import datetime
        from config.dutch_stopwords import (
            is_meaningful_concept, 
            get_concept_type,
            extract_concept_from_input,
            normalize_concept
        )
        
        # Store original input for context
        original_input = concept
        
        # VALIDATION: Reject completely empty input
        if not concept or not concept.strip():
            rejection_msg = f"❌ SNAP REJECTED: Leeg concept ontvangen | Context: '{context[:50]}...' | User: {user_naam}"
            SparkLogger.log_system_event(rejection_msg)
            snap_logger.warning(rejection_msg)
            print(f"[SNAP DEBUG] {rejection_msg}")
            return None
        
        # For sentence snaps (context zinnen), use ORIGINAL input - no extraction!
        if is_sentence_snap:
            # Skip extraction, use full sentence as-is
            concept = original_input.strip()
            extracted = concept
            
            # VALIDATION: Reject empty sentences
            if not concept or len(concept) < 2:
                rejection_msg = f"❌ SNAP REJECTED: Zinsnap te kort of leeg (lengte: {len(concept) if concept else 0}) | Input: '{concept}' | Context: '{context[:50]}...' | User: {user_naam}"
                SparkLogger.log_system_event(rejection_msg)
                snap_logger.warning(rejection_msg)
                print(f"[SNAP DEBUG] {rejection_msg}")
                return None
            
            # ZINNEN: NO duplicate check - Spark leert nog
            # Duplicates worden later via conversatie opgelost ("Bedoel je X?" → ja/nee)
            # Skip the existing entry check completely for sentences
        else:
            # WOORDEN: Extract and normalize
            extracted = extract_concept_from_input(concept)
            if not extracted:
                rejection_msg = f"❌ SNAP REJECTED: Geen concept te extraheren | Input: '{concept}' | Context: '{context[:50]}...' | User: {user_naam}"
                SparkLogger.log_system_event(rejection_msg)
                snap_logger.warning(rejection_msg)
                print(f"[SNAP DEBUG] {rejection_msg}")
                return None
            
            concept = normalize_concept(extracted)
            
            # Check if concept is meaningful (not a stopword)
            is_meaningful, reason = is_meaningful_concept(concept)
            if not is_meaningful:
                rejection_msg = f"❌ SNAP REJECTED: '{concept}' - {reason} | Context: '{context[:50]}...' | User: {user_naam}"
                SparkLogger.log_system_event(rejection_msg)
                snap_logger.warning(rejection_msg)
                print(f"[SNAP DEBUG] {rejection_msg}")
                return None
            
            # WOORDEN: Check duplicates (unless needs_confirmation is already set)
            if not needs_confirmation:
                data = DataManager.load_json("learned_knowledge/knowledge_base.json")
                entries = data.get("knowledge_entries", [])
                
                concept_lower = concept.lower()
                existing = [e for e in entries if concept_lower == e.get("begrip", "").lower()]
                if existing:
                    existing_topics = [e.get('topic', '(geen)') for e in existing]
                    rejection_msg = f"❌ SNAP REJECTED: '{concept}' bestaat al | Bestaande topics: {existing_topics} | Context: '{context[:50]}...' | User: {user_naam}"
                    SparkLogger.log_system_event(rejection_msg)
                    snap_logger.info(rejection_msg)
                    print(f"[SNAP DEBUG] {rejection_msg}")
                    return None
        
        # Load data for saving
        data = DataManager.load_json("learned_knowledge/knowledge_base.json")
        entries = data.get("knowledge_entries", [])
        # Determine concept type for analytics
        concept_type = get_concept_type(concept)
        
        # Determine status based on confirmation need and user type
        if needs_confirmation:
            status = "pending_confirmation"  # Needs Willem's review for duplicate
        elif user_id is None:
            status = "guest_contribution"  # From anonymous/guest user
        else:
            status = "draft"  # Normal draft from logged-in user
        
        # Determine if user is anonymous
        is_anonymous = user_id is None or user_naam.startswith("anonymous_")
        
        # FINAL VALIDATION: Ensure concept is not empty after all processing
        if not concept or not concept.strip():
            rejection_msg = f"❌ SNAP REJECTED: Concept werd leeg na processing | Original: '{original_input}' | Context: '{context[:50]}...' | User: {user_naam}"
            SparkLogger.log_system_event(rejection_msg)
            snap_logger.error(rejection_msg)
            print(f"[SNAP DEBUG] {rejection_msg}")
            return None
        
        # Create placeholder entry - VOLLEDIG zoals admin kaarten
        new_entry = {
            "id": f"snap-{uuid.uuid4().hex[:8]}",
            "begrip": concept.strip(),  # Ensure trimmed
            "lagen": {
                "laag1": "",
                "laag2": "",
                "laag3": "",
                "laag4": ""
            },
            "ws5": {
                "who": "",
                "what": "",
                "when": "",
                "where": "",
                "why": "",
                "how": ""
            },
            "tags": ["knowledge-snap", "auto-generated", concept_type],
            "bron": "auto-detected",
            "detected_by": user_naam,
            "detected_by_user_id": user_id,  # None voor guests
            "detected_at": datetime.now().isoformat(),
            "status": status,
            "belangrijkheid": 3,
            "usage_count": 0,
            "feedback": {"helpful": 0, "not_helpful": 0, "score": 0.5},
            "created_via": "snap",
            "topic": "",
            "snap_context": context[:200] if context else "",
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "created_via": "snap",
                "is_sentence": is_sentence_snap,
                "is_anonymous": is_anonymous
            }
        }
        
        # Add confirmation metadata if needed
        if needs_confirmation and similar_to:
            new_entry["confirmation_needed"] = {
                "reason": "possible_duplicate",
                "similar_to": similar_to.get('begrip'),
                "similar_description": similar_to.get('laag1', '')[:100]
            }
        
        entries.append(new_entry)
        data["knowledge_entries"] = entries
        DataManager.save_json("learned_knowledge/knowledge_base.json", data)
        
        # 🔄 AUTO-SYNC: Trigger graph sync after new entry
        from utils.auto_sync import trigger_graph_sync
        trigger_graph_sync(background=True)
        
        log_msg = f"✅ SNAP CREATED: '{concept}' (type: {concept_type}"
        if is_sentence_snap:
            log_msg += ", zin/context"
        if needs_confirmation:
            log_msg += ", needs confirmation"
        log_msg += f") | Topic: '{new_entry['topic']}' | Status: {status} | User: {user_naam} | ID: {new_entry['id']}"
        
        SparkLogger.log_system_event(log_msg)
        snap_logger.info(log_msg)
        print(f"[SNAP DEBUG] {log_msg}")
        
        return new_entry
