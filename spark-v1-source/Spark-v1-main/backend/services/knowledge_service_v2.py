"""
Knowledge Service V2 - Complete ranking system with caching
"""
from typing import Dict, List, Optional
from utils.data_manager import DataManager
from datetime import datetime
import math
import time
import threading


class KnowledgeServiceV2:
    """Service with intelligent ranking and performance optimization"""
    
    # Memory cache
    _cache = None
    _cache_timestamp = 0
    _cache_ttl = 30  # seconds
    _pending_writes = {}
    _write_lock = threading.Lock()
    _last_write = 0
    _write_interval = 30  # Write every 30 seconds
    
    @staticmethod
    def _load_with_cache() -> List[Dict]:
        """Load knowledge with memory caching"""
        current_time = time.time()
        
        # Check cache validity
        if KnowledgeServiceV2._cache is not None:
            if current_time - KnowledgeServiceV2._cache_timestamp < KnowledgeServiceV2._cache_ttl:
                return KnowledgeServiceV2._cache
        
        # Load fresh
        knowledge = DataManager.load_knowledge()
        KnowledgeServiceV2._cache = knowledge
        KnowledgeServiceV2._cache_timestamp = current_time
        
        return knowledge
    
    @staticmethod
    def _invalidate_cache():
        """Invalidate cache"""
        KnowledgeServiceV2._cache = None
    
    @staticmethod
    def _schedule_write(knowledge_id: str, updates: Dict):
        """Schedule write (batched for performance)"""
        with KnowledgeServiceV2._write_lock:
            if knowledge_id not in KnowledgeServiceV2._pending_writes:
                KnowledgeServiceV2._pending_writes[knowledge_id] = {}
            KnowledgeServiceV2._pending_writes[knowledge_id].update(updates)
    
    @staticmethod
    def _flush_writes():
        """Flush pending writes to disk"""
        with KnowledgeServiceV2._write_lock:
            if not KnowledgeServiceV2._pending_writes:
                return
            
            current_time = time.time()
            if current_time - KnowledgeServiceV2._last_write < KnowledgeServiceV2._write_interval:
                return
            
            # Load
            data = DataManager.load_json("learned_knowledge/knowledge_base.json")
            entries = data.get("knowledge_entries", [])
            
            # Apply updates
            for entry in entries:
                entry_id = entry.get("id")
                if entry_id in KnowledgeServiceV2._pending_writes:
                    updates = KnowledgeServiceV2._pending_writes[entry_id]
                    entry.update(updates)
            
            # Save
            data["knowledge_entries"] = entries
            DataManager.save_json("learned_knowledge/knowledge_base.json", data)
            
            # 🔄 AUTO-SYNC: Trigger graph sync
            from utils.auto_sync import trigger_graph_sync
            trigger_graph_sync(background=True)
            
            # Clear
            KnowledgeServiceV2._pending_writes.clear()
            KnowledgeServiceV2._last_write = current_time
            KnowledgeServiceV2._invalidate_cache()
    
    @staticmethod
    def calculate_rank_score(entry: Dict) -> float:
        """
        Calculate ranking score
        
        Formula:
        rank_score = (belangrijkheid * 3)
                   + log(usage_count + 1)
                   + (feedback_score * 5)
                   - (days_since_last_used * 0.05)
        """
        belangrijkheid = entry.get("belangrijkheid", 3)
        usage_count = entry.get("usage_count", 0)
        feedback = entry.get("feedback", {})
        feedback_score = feedback.get("score", 0.5)
        last_used_str = entry.get("last_used")
        
        # Time decay
        days_since = 999
        if last_used_str:
            try:
                last_used = datetime.fromisoformat(last_used_str)
                days_since = (datetime.now() - last_used).days
            except Exception:
                pass
        
        score = (
            (belangrijkheid * 3) +
            math.log(usage_count + 1) +
            (feedback_score * 5) -
            (days_since * 0.05)
        )
        
        return round(score, 2)
    
    @staticmethod
    def get_all_knowledge() -> List[Dict]:
        """Get all knowledge with rank scores"""
        entries = KnowledgeServiceV2._load_with_cache()
        
        # Add rank_score to each
        for entry in entries:
            entry["rank_score"] = KnowledgeServiceV2.calculate_rank_score(entry)
        
        return entries
    
    @staticmethod
    def get_ranked_knowledge() -> List[Dict]:
        """Get knowledge sorted by rank_score"""
        entries = KnowledgeServiceV2.get_all_knowledge()
        entries.sort(key=lambda e: e.get("rank_score", 0), reverse=True)
        return entries
    
    @staticmethod
    def increment_usage(knowledge_id: str) -> bool:
        """
        Increment usage and update last_used
        Performance: Batched writes every 30s
        """
        entries = KnowledgeServiceV2._load_with_cache()
        
        for entry in entries:
            if entry.get("id") == knowledge_id:
                # Update in cache
                if "usage_count" not in entry:
                    entry["usage_count"] = 0
                entry["usage_count"] += 1
                entry["last_used"] = datetime.now().isoformat()
                
                # Schedule write
                KnowledgeServiceV2._schedule_write(knowledge_id, {
                    "usage_count": entry["usage_count"],
                    "last_used": entry["last_used"]
                })
                
                # Try flush (if interval passed)
                KnowledgeServiceV2._flush_writes()
                
                return True
        
        return False
    
    @staticmethod
    def record_feedback(knowledge_id: str, was_helpful: bool) -> bool:
        """Record feedback"""
        entries = KnowledgeServiceV2._load_with_cache()
        
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
                
                # Schedule write
                KnowledgeServiceV2._schedule_write(knowledge_id, {
                    "feedback": entry["feedback"]
                })
                
                KnowledgeServiceV2._flush_writes()
                
                return True
        
        return False
    
    @staticmethod
    def get_entry_stats(knowledge_id: str) -> Optional[Dict]:
        """Get detailed stats including rank_score"""
        entries = KnowledgeServiceV2.get_all_knowledge()
        entry = next((e for e in entries if e.get("id") == knowledge_id), None)
        
        if not entry:
            return None
        
        return {
            "knowledge_id": knowledge_id,
            "begrip": entry.get("begrip"),
            "usage_count": entry.get("usage_count", 0),
            "last_used": entry.get("last_used"),
            "feedback": entry.get("feedback", {"helpful": 0, "not_helpful": 0, "score": 0.5}),
            "belangrijkheid": entry.get("belangrijkheid", 3),
            "rank_score": entry.get("rank_score", 0)
        }
