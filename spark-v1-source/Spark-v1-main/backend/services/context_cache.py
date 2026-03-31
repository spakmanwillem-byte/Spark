"""
Context Cache - In-memory LRU cache voor conversation context

Onderdeel van de 3-laagse caching strategie:
- Laag 1: In-Memory Cache (dit bestand) - INSTANT toegang
- Laag 2: Samenvattingen - SNEL
- Laag 3: Volledige History - ON-DEMAND
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime, timedelta, timezone
from collections import OrderedDict
import sys


@dataclass
class CachedMessage:
    """Lightweight message representation voor cache"""
    message: str
    sender: str  # 'user' of 'spark'
    timestamp: datetime
    session_id: str
    
    # Optional analysis data
    emotion: Optional[str] = None
    topics: List[str] = field(default_factory=list)
    sentiment: Optional[str] = None
    intent: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dict voor compatibility"""
        return {
            "message": self.message,
            "sender": self.sender,
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id,
            "emotion": self.emotion,
            "topics": self.topics,
            "sentiment": self.sentiment,
            "intent": self.intent
        }


class ContextCache:
    """
    In-memory LRU cache voor actieve sessies.
    
    Features:
    - LRU (Least Recently Used) eviction policy
    - Configurable max sessions en messages per session
    - Statistics tracking (hits, misses, hit rate)
    - Automatic cleanup van oude sessies
    - Memory usage estimation
    
    Performance:
    - get(): O(1)
    - add_message(): O(1)
    - Memory: ~1 MB voor 100 sessies × 20 berichten
    """
    
    def __init__(self, max_sessions: int = 100, messages_per_session: int = 20):
        """
        Initialize cache
        
        Args:
            max_sessions: Maximum aantal actieve sessies in cache
            messages_per_session: Maximum aantal berichten per sessie
        """
        self.max_sessions = max_sessions
        self.messages_per_session = messages_per_session
        
        # OrderedDict = auto LRU behavior via move_to_end()
        self._cache: OrderedDict[str, List[CachedMessage]] = OrderedDict()
        
        # Statistics
        self.hits = 0
        self.misses = 0
        self.total_messages_cached = 0
    
    def get(self, session_id: str) -> Optional[List[CachedMessage]]:
        """
        Haal berichten op uit cache.
        
        Args:
            session_id: Session identifier
        
        Returns:
            List[CachedMessage] if found, None if cache miss
        """
        if session_id in self._cache:
            self.hits += 1
            # Move to end (most recently used)
            self._cache.move_to_end(session_id)
            return self._cache[session_id].copy()  # Return copy voor safety
        
        self.misses += 1
        return None
    
    def add_message(self, session_id: str, message: CachedMessage):
        """
        Voeg bericht toe aan cache.
        Handhaaft maximum aantal berichten per sessie.
        
        Args:
            session_id: Session identifier
            message: CachedMessage object
        """
        if session_id not in self._cache:
            # Nieuwe sessie
            if len(self._cache) >= self.max_sessions:
                # Remove oldest session (LRU eviction)
                oldest_session_id, oldest_messages = self._cache.popitem(last=False)
                self.total_messages_cached -= len(oldest_messages)
            
            self._cache[session_id] = []
        
        # Add message
        self._cache[session_id].append(message)
        self.total_messages_cached += 1
        
        # Maintain max messages per session
        if len(self._cache[session_id]) > self.messages_per_session:
            # Remove oldest message from this session
            self._cache[session_id].pop(0)
            self.total_messages_cached -= 1
        
        # Move to end (most recently used)
        self._cache.move_to_end(session_id)
    
    def get_session_count(self, session_id: str) -> int:
        """
        Get aantal berichten in een sessie
        
        Args:
            session_id: Session identifier
        
        Returns:
            Aantal berichten in cache voor deze sessie
        """
        if session_id in self._cache:
            return len(self._cache[session_id])
        return 0
    
    def has_session(self, session_id: str) -> bool:
        """
        Check of sessie bestaat in cache
        
        Args:
            session_id: Session identifier
        
        Returns:
            True if session exists in cache
        """
        return session_id in self._cache
    
    def clear_session(self, session_id: str):
        """
        Verwijder sessie uit cache (bijv. bij uitloggen)
        
        Args:
            session_id: Session identifier
        """
        if session_id in self._cache:
            self.total_messages_cached -= len(self._cache[session_id])
            del self._cache[session_id]
    
    def clear_old_sessions(self, max_age_hours: int = 24) -> int:
        """
        Verwijder sessies ouder dan X uur (background cleanup task).
        
        Args:
            max_age_hours: Maximum leeftijd van sessie in uren
        
        Returns:
            Aantal verwijderde sessies
        """
        now = datetime.now(timezone.utc)
        to_remove = []
        
        for session_id, messages in self._cache.items():
            if not messages:
                to_remove.append(session_id)
                continue
            
            # Check laatste bericht timestamp
            last_message = messages[-1]
            
            # Ensure timestamp is timezone-aware
            last_time = last_message.timestamp
            if last_time.tzinfo is None:
                last_time = last_time.replace(tzinfo=timezone.utc)
            
            age = (now - last_time).total_seconds() / 3600
            
            if age > max_age_hours:
                to_remove.append(session_id)
        
        # Remove old sessions
        for session_id in to_remove:
            self.clear_session(session_id)
        
        return len(to_remove)
    
    def clear_all(self):
        """Clear entire cache (voor testing)"""
        self._cache.clear()
        self.total_messages_cached = 0
        # Keep statistics
    
    def get_stats(self) -> Dict:
        """
        Cache statistics voor monitoring
        
        Returns:
            Dict met hit rate, active sessions, memory usage, etc.
        """
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0.0
        
        return {
            "hits": self.hits,
            "misses": self.misses,
            "total_requests": total_requests,
            "hit_rate_percent": round(hit_rate, 1),
            "active_sessions": len(self._cache),
            "total_messages": self.total_messages_cached,
            "memory_usage_mb": round(self._estimate_memory_usage(), 2),
            "max_sessions": self.max_sessions,
            "messages_per_session": self.messages_per_session
        }
    
    def _estimate_memory_usage(self) -> float:
        """
        Rough estimate van geheugengebruik (MB)
        
        Returns:
            Geschat geheugengebruik in MB
        """
        # Rough estimate: avg 500 bytes per message
        # (includes string content, metadata, Python overhead)
        avg_message_size = 500  # bytes
        total_bytes = self.total_messages_cached * avg_message_size
        
        # Add overhead voor OrderedDict en dataclasses (~20%)
        total_bytes *= 1.2
        
        # Convert to MB
        return total_bytes / (1024 * 1024)
    
    def get_session_messages_as_dicts(self, session_id: str) -> List[Dict]:
        """
        Get berichten als dictionaries (voor backward compatibility)
        
        Args:
            session_id: Session identifier
        
        Returns:
            List van message dicts
        """
        messages = self.get(session_id)
        if messages is None:
            return []
        return [msg.to_dict() for msg in messages]


# Global singleton instance
_global_cache: Optional[ContextCache] = None


def get_cache() -> ContextCache:
    """
    Get singleton cache instance.
    
    Returns:
        Global ContextCache instance
    """
    global _global_cache
    if _global_cache is None:
        _global_cache = ContextCache(
            max_sessions=100,
            messages_per_session=20
        )
    return _global_cache


def reset_cache():
    """Reset global cache (voor testing)"""
    global _global_cache
    _global_cache = None
