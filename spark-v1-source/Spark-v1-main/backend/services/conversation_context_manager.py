"""
Conversation Context Manager - Tracks conversation context per user

Keeps track of:
- Last discussed topic/concept
- Current knowledge layer
- Question history for "meer" and "dieper" requests
"""

from typing import Dict, Optional
from datetime import datetime, timedelta


class ConversationContextManager:
    """
    In-memory context store per user session
    Tracks recent topics to enable multi-turn knowledge conversations
    """
    
    # Class-level storage (in production, use Redis or database)
    _contexts: Dict[str, Dict] = {}
    
    
    # Disambiguation context storage
    _disambiguation_contexts: Dict[str, Dict] = {}

    @classmethod
    def set_knowledge_context(cls, user_id: str, concept: str, layer: int):
        """
        Store the current knowledge context for a user
        
        Args:
            user_id: User identifier
            concept: The concept being discussed (e.g., "appel")
            layer: Current layer (1, 2, or 3)
        """
        if user_id not in cls._contexts:
            cls._contexts[user_id] = {}
        
        cls._contexts[user_id].update({
            "type": "knowledge",
            "concept": concept,
            "layer": layer,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    @classmethod
    def get_knowledge_context(cls, user_id: str) -> Optional[Dict]:
        """
        Get the current knowledge context for a user
        
        Returns:
            Dict with concept and layer, or None if no context
        """
        if user_id not in cls._contexts:
            return None
        
        context = cls._contexts[user_id]
        
        # Check if context is recent (within 5 minutes)
        if "timestamp" in context:
            timestamp = datetime.fromisoformat(context["timestamp"])
            if datetime.utcnow() - timestamp > timedelta(minutes=5):
                # Context too old, clear it
                cls.clear_context(user_id)
                return None
        
        if context.get("type") == "knowledge":
            return {
                "concept": context.get("concept"),
                "layer": context.get("layer")
            }
        
        return None
    
    @classmethod
    def clear_context(cls, user_id: str):
        """Clear context for a user"""
        if user_id in cls._contexts:
            del cls._contexts[user_id]
    
    @classmethod
    def increment_layer(cls, user_id: str) -> Optional[int]:
        """
        Increment the layer for current context
        
        Returns:
            New layer number, or None if no context or already at max
        """
        context = cls.get_knowledge_context(user_id)
        if not context:
            return None
        
        current_layer = context.get("layer", 1)
        if current_layer >= 3:
            return None  # Already at max layer
        
        new_layer = current_layer + 1
        cls.set_knowledge_context(
            user_id,
            context.get("concept"),
            new_layer
        )
        
        return new_layer
    
    @classmethod
    def is_deeper_request(cls, message: str) -> bool:
        """
        Check if message is requesting deeper information
        
        Args:
            message: User's message
            
        Returns:
            True if user wants more depth/detail
        """
        message_lower = message.lower().strip()
        
        # Short requests indicating "more"
        deeper_keywords = [
            "meer",
            "dieper",
            "verder",
            "uitleg",
            "leg uit",
            "vertel meer",
            "ga door",
            "en verder",
            "nog meer",
            "volledig",
            "alles",
            "compleet"
        ]
        
        # Check if message is short and contains deeper keyword
        if len(message_lower.split()) <= 3:
            for keyword in deeper_keywords:
                if keyword in message_lower:
                    return True
        
        return False

    
    @classmethod
    def set_disambiguation_context(cls, session_id: str, concept: str, options: list):
        """
        Store disambiguation options for follow-up selection
        
        Args:
            session_id: Session identifier
            concept: The disambiguated concept
            options: List of knowledge entries shown (with IDs and begrip)
        """
        cls._disambiguation_contexts[session_id] = {
            "concept": concept,
            "options": options,
            "timestamp": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(minutes=5)
        }
    
    @classmethod
    def get_disambiguation_context(cls, session_id: str) -> Optional[Dict]:
        """
        Get stored disambiguation context
        
        Returns:
            Dict with concept and options, or None if expired/not found
        """
        context = cls._disambiguation_contexts.get(session_id)
        
        if not context:
            return None
        
        # Check expiry
        if datetime.utcnow() > context.get("expires_at"):
            del cls._disambiguation_contexts[session_id]
            return None
        
        return context
    
    @classmethod
    def clear_disambiguation_context(cls, session_id: str):
        """Clear disambiguation context after user makes selection"""
        if session_id in cls._disambiguation_contexts:
            del cls._disambiguation_contexts[session_id]

