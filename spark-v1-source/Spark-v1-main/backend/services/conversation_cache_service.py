"""
Conversation Cache Service - Integreert ContextCache met ConversationService

Deze service fungeert als een laag tussen de cache en de conversation storage,
en zorgt voor:
- Automatisch cachen van nieuwe berichten
- Cache-first ophalen van recente berichten
- Fallback naar disk bij cache miss
- Populeren van cache na disk load
"""
from typing import List, Dict, Optional
from datetime import datetime, timezone
from services.context_cache import get_cache, CachedMessage
from services.conversation_service import ConversationService


class ConversationCacheService:
    """
    Service die conversation history beheert met caching.
    
    Flow:
    1. Check cache voor recente berichten
    2. Bij cache miss: load van disk
    3. Populeer cache voor volgende keer
    4. Return berichten
    """
    
    def __init__(self):
        self.cache = get_cache()
        self.conversation_service = ConversationService()
    
    def get_recent_messages(
        self,
        user_id: str,
        session_id: str,
        limit: int = 20
    ) -> List[Dict]:
        """
        Haal recente berichten op (cache-first).
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            limit: Maximum aantal berichten
        
        Returns:
            List van message dicts (meest recente eerst)
        """
        # STEP 1: Check cache
        cached_messages = self.cache.get(session_id)
        
        if cached_messages is not None:
            # CACHE HIT ✓
            # Convert to dicts en return
            messages = [msg.to_dict() for msg in cached_messages]
            # Return laatste N berichten
            return messages[-limit:]
        
        # STEP 2: CACHE MISS - Load from disk
        disk_messages = self.conversation_service.get_user_conversations(
            user_id=user_id,
            limit=limit
        )
        
        # STEP 3: Populate cache voor next time
        self._populate_cache_from_disk(session_id, disk_messages)
        
        # STEP 4: Return berichten
        return disk_messages[-limit:]
    
    def add_message(
        self,
        session_id: str,
        message: str,
        sender: str,
        user_id: str,
        emotion: Optional[str] = None,
        topics: Optional[List[str]] = None,
        sentiment: Optional[str] = None,
        intent: Optional[str] = None
    ):
        """
        Voeg nieuw bericht toe aan cache.
        
        Note: Deze functie voegt ALLEEN toe aan cache.
        Het opslaan naar disk gebeurt via ConversationService.log_conversation().
        
        Args:
            session_id: Session identifier
            message: Message text
            sender: 'user' of 'spark'
            user_id: User identifier
            emotion: Optional emotion
            topics: Optional topics list
            sentiment: Optional sentiment
            intent: Optional intent
        """
        cached_msg = CachedMessage(
            message=message,
            sender=sender,
            timestamp=datetime.now(timezone.utc),
            session_id=session_id,
            emotion=emotion,
            topics=topics or [],
            sentiment=sentiment,
            intent=intent
        )
        
        self.cache.add_message(session_id, cached_msg)
    
    def get_conversation_context(
        self,
        user_id: str,
        session_id: str,
        limit: int = 10
    ) -> Dict:
        """
        Get conversation context voor analysis.
        
        Returns een rijke context met:
        - Recent messages
        - Topic history
        - Emotional signals
        - Conversation patterns
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            limit: Number of recent messages to analyze
        
        Returns:
            Dict met conversation context
        """
        messages = self.get_recent_messages(user_id, session_id, limit=limit)
        
        if not messages:
            return self._empty_context()
        
        # Extract topics from messages
        all_topics = []
        for msg in messages:
            if isinstance(msg, dict):
                analysis = msg.get('analysis', {})
                classification = analysis.get('classification', {})
                klasse = classification.get('klasse')
                if klasse:
                    all_topics.append(klasse)
        
        # Extract emotions
        emotions = []
        for msg in messages:
            if isinstance(msg, dict):
                # Check if emotion is stored directly
                emotion = msg.get('emotion')
                if not emotion:
                    # Fallback to analysis
                    analysis = msg.get('analysis', {})
                    emotion = analysis.get('sentiment')
                if emotion:
                    emotions.append(emotion)
        
        # Build context
        return {
            'messages': messages,
            'message_count': len(messages),
            'topics': list(set(all_topics)),  # unique topics
            'primary_topic': all_topics[-1] if all_topics else None,
            'emotions': emotions,
            'recent_emotion': emotions[-1] if emotions else None,
            'user_id': user_id,
            'session_id': session_id
        }
    
    def clear_session(self, session_id: str):
        """
        Clear session from cache (bijv. bij logout).
        
        Args:
            session_id: Session identifier
        """
        self.cache.clear_session(session_id)
    
    def get_cache_stats(self) -> Dict:
        """
        Get cache statistics voor monitoring.
        
        Returns:
            Dict met cache stats
        """
        return self.cache.get_stats()
    
    def _populate_cache_from_disk(self, session_id: str, disk_messages: List[Dict]):
        """
        Populate cache from disk-loaded messages.
        
        Args:
            session_id: Session identifier
            disk_messages: Messages loaded from disk
        """
        for msg_data in disk_messages:
            # Parse message data
            if isinstance(msg_data, dict):
                message_text = msg_data.get('user_message', '')
                timestamp_str = msg_data.get('timestamp', '')
                
                # Parse timestamp
                try:
                    timestamp = datetime.fromisoformat(timestamp_str)
                    if timestamp.tzinfo is None:
                        timestamp = timestamp.replace(tzinfo=timezone.utc)
                except:
                    timestamp = datetime.now(timezone.utc)
                
                # Extract analysis data
                analysis = msg_data.get('analysis', {})
                
                # Create cached message
                cached_msg = CachedMessage(
                    message=message_text,
                    sender='user',  # From disk, these are user messages
                    timestamp=timestamp,
                    session_id=session_id,
                    emotion=analysis.get('sentiment'),
                    topics=[analysis.get('classification', {}).get('klasse', '')] if analysis.get('classification') else [],
                    sentiment=analysis.get('sentiment'),
                    intent=analysis.get('command')
                )
                
                self.cache.add_message(session_id, cached_msg)
    
    def _empty_context(self) -> Dict:
        """Return empty context"""
        return {
            'messages': [],
            'message_count': 0,
            'topics': [],
            'primary_topic': None,
            'emotions': [],
            'recent_emotion': None,
            'user_id': None,
            'session_id': None
        }
