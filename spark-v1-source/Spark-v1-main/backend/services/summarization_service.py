"""
Summarization Service - Layer 2 van de 3-layer memory architecture

Periodiek comprimeren van oude conversaties naar bruikbare samenvattingen.
Opgeslagen in users.json voor lange-termijn geheugen.

3-Layer Architecture:
- Layer 1: Cache (laatste 20 berichten, instant)
- Layer 2: Summaries (periodieke samenvattingen, snel) ← This file
- Layer 3: Full History (volledige geschiedenis, on-demand)
"""
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional
from datetime import datetime, timezone, timedelta
from collections import Counter
from services.conversation_service import ConversationService
from services.pattern_detection_service import PatternDetectionService
from utils.data_manager import DataManager


@dataclass
class ConversationSummary:
    """
    Gecomprimeerde representatie van een conversatie periode.
    Opgeslagen in users.json onder elke user.
    """
    
    # Temporeel
    period_start: str  # ISO datetime
    period_end: str    # ISO datetime
    total_messages: int
    
    # Onderwerpen
    primary_topics: List[str] = field(default_factory=list)  # Top 5
    topic_frequencies: Dict[str, int] = field(default_factory=dict)
    
    # Emotioneel
    dominant_emotions: List[str] = field(default_factory=list)  # Top 3
    mood_trajectory: str = "stable"  # "improving", "stable", "declining"
    
    # Patronen
    recurring_questions: List[str] = field(default_factory=list)
    learned_concepts: List[str] = field(default_factory=list)
    
    # Key moments
    key_moments: List[Dict] = field(default_factory=list)
    # Format: {"timestamp": "...", "summary": "...", "emotion": "..."}
    
    # Metadata
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    version: str = "1.0"
    
    def to_dict(self) -> Dict:
        """Convert to dict for JSON storage"""
        return asdict(self)


class SummarizationService:
    """
    Service voor het samenvatten van conversatie geschiedenis.
    
    Usage:
        service = SummarizationService()
        summary = await service.summarize_user_history(user_id, since_date)
        await service.store_summary(user_id, summary)
    """
    
    def __init__(self):
        self.conversation_service = ConversationService()
        self.pattern_service = PatternDetectionService()
    
    def summarize_user_history(
        self,
        user_id: str,
        since_date: Optional[datetime] = None,
        limit: int = 100
    ) -> Optional[ConversationSummary]:
        """
        Vat conversatie geschiedenis samen voor een user.
        
        Args:
            user_id: User identifier
            since_date: Vat samen vanaf deze datum (optioneel)
            limit: Max aantal berichten om te analyseren
        
        Returns:
            ConversationSummary or None if insufficient data
        """
        
        # Get user conversations
        conversations = self.conversation_service.get_user_conversations(
            user_id=user_id,
            limit=limit
        )
        
        if not conversations or len(conversations) < 5:
            # Not enough data to summarize
            return None
        
        # Filter by date if specified
        if since_date:
            conversations = [
                c for c in conversations
                if self._parse_timestamp(c.get('timestamp')) >= since_date
            ]
        
        if len(conversations) < 5:
            return None
        
        # Analyze and create summary
        return self._analyze_and_summarize(conversations, user_id)
    
    def _analyze_and_summarize(
        self,
        conversations: List[Dict],
        user_id: str
    ) -> ConversationSummary:
        """
        Analyseer conversaties en genereer samenvatting.
        
        Args:
            conversations: List van conversation dicts
            user_id: User identifier
        
        Returns:
            ConversationSummary
        """
        
        # Extract timestamps
        timestamps = [
            self._parse_timestamp(c.get('timestamp'))
            for c in conversations
        ]
        period_start = min(timestamps).isoformat()
        period_end = max(timestamps).isoformat()
        
        # Collect all messages
        all_messages = []
        for conv in conversations:
            msg = conv.get('user_message', '')
            if msg:
                all_messages.append(msg)
        
        # Topic analysis
        topic_freq = self._extract_topic_frequencies(conversations, user_id)
        primary_topics = sorted(
            topic_freq.keys(),
            key=lambda t: topic_freq[t],
            reverse=True
        )[:5]
        
        # Emotion analysis
        emotions = self._extract_emotions(conversations)
        dominant_emotions = [e for e, _ in Counter(emotions).most_common(3)]
        
        # Mood trajectory
        mood_trajectory = self._calculate_mood_trajectory(conversations)
        
        # Recurring questions
        questions = [m for m in all_messages if '?' in m]
        recurring = self._find_recurring_questions(questions)
        
        # Learned concepts (from teaching moments)
        learned = self._extract_learned_concepts(conversations)
        
        # Key moments
        key_moments = self._extract_key_moments(conversations)
        
        return ConversationSummary(
            period_start=period_start,
            period_end=period_end,
            total_messages=len(conversations),
            primary_topics=primary_topics,
            topic_frequencies=topic_freq,
            dominant_emotions=dominant_emotions,
            mood_trajectory=mood_trajectory,
            recurring_questions=recurring[:5],  # Top 5
            learned_concepts=learned[:10],  # Top 10
            key_moments=key_moments[:10]  # Top 10
        )
    
    def _extract_topic_frequencies(
        self,
        conversations: List[Dict],
        user_id: str
    ) -> Dict[str, int]:
        """Extract topic frequencies from conversations"""
        
        topic_freq = {}
        
        for conv in conversations:
            message = conv.get('user_message', '')
            if not message:
                continue
            
            # Get user data for pattern detection
            user_data = {"id": user_id}
            
            # Analyze message
            try:
                analysis = self.pattern_service.analyze_message(message, user_data)
                topics = analysis.get('topics', [])
                
                for topic in topics:
                    topic_freq[topic] = topic_freq.get(topic, 0) + 1
                    
            except:
                # Continue on error
                pass
        
        return topic_freq
    
    def _extract_emotions(self, conversations: List[Dict]) -> List[str]:
        """Extract emotions from conversations"""
        
        emotions = []
        
        for conv in conversations:
            # Check analysis for sentiment
            analysis = conv.get('analysis', {})
            sentiment = analysis.get('sentiment')
            
            if sentiment:
                emotions.append(sentiment)
        
        return emotions
    
    def _calculate_mood_trajectory(self, conversations: List[Dict]) -> str:
        """
        Calculate if mood is improving/declining/stable.
        
        Compares first half vs second half of conversation period.
        """
        
        if len(conversations) < 10:
            return "stable"
        
        # Split in half
        mid = len(conversations) // 2
        first_half = conversations[:mid]
        second_half = conversations[mid:]
        
        # Count positive emotions
        positive_emotions = {"positief", "happy", "excited", "content", "proud"}
        
        def count_positive(convs):
            count = 0
            for c in convs:
                analysis = c.get('analysis', {})
                sentiment = analysis.get('sentiment', '')
                if sentiment.lower() in positive_emotions:
                    count += 1
            return count
        
        first_positive = count_positive(first_half)
        second_positive = count_positive(second_half)
        
        first_rate = first_positive / len(first_half) if first_half else 0
        second_rate = second_positive / len(second_half) if second_half else 0
        
        # Compare
        if second_rate > first_rate + 0.2:
            return "improving"
        elif second_rate < first_rate - 0.2:
            return "declining"
        else:
            return "stable"
    
    def _find_recurring_questions(self, questions: List[str]) -> List[str]:
        """Find questions that appear multiple times"""
        
        if not questions:
            return []
        
        # Normalize questions (lowercase, remove punctuation)
        normalized = {}
        for q in questions:
            norm = q.lower().strip('? ').strip()
            if norm:
                normalized[norm] = normalized.get(norm, 0) + 1
        
        # Return questions that appear > 1 time
        recurring = [q for q, count in normalized.items() if count > 1]
        
        # Sort by frequency
        recurring.sort(key=lambda q: normalized[q], reverse=True)
        
        return recurring
    
    def _extract_learned_concepts(self, conversations: List[Dict]) -> List[str]:
        """
        Extract concepts that were taught/learned.
        
        Look for teaching signals like "onthoud", "leer jezelf", etc.
        """
        
        learned = []
        
        teaching_signals = [
            'onthoud', 'leer jezelf', 'weet dat', 'belangrijk om te weten',
            'ik vertel je', 'luister goed'
        ]
        
        for conv in conversations:
            message = conv.get('user_message', '').lower()
            
            # Check for teaching signals
            has_teaching = any(signal in message for signal in teaching_signals)
            
            if has_teaching:
                # Extract the concept (simplified)
                # TODO: More sophisticated extraction
                words = message.split()
                if len(words) > 3:
                    # Take key words after signal
                    learned.append(message[:50])  # First 50 chars
        
        return learned
    
    def _extract_key_moments(self, conversations: List[Dict]) -> List[Dict]:
        """
        Extract key moments from conversation history.
        
        Key moments are:
        - High emotion intensity
        - Important topics (stopwoorden)
        - Significant events
        """
        
        key_moments = []
        
        for conv in conversations:
            analysis = conv.get('analysis', {})
            
            # High importance (stopwoorden)
            importance = analysis.get('importance_score', 0)
            has_stopwords = analysis.get('has_stop_words', False)
            
            if importance >= 4 or has_stopwords:
                key_moments.append({
                    'timestamp': conv.get('timestamp', ''),
                    'summary': conv.get('user_message', '')[:100],
                    'importance': importance,
                    'stopwords': analysis.get('stop_words_found', [])
                })
        
        # Sort by importance
        key_moments.sort(key=lambda m: m.get('importance', 0), reverse=True)
        
        return key_moments
    
    def store_summary(self, user_id: str, summary: ConversationSummary):
        """
        Store summary in users.json.
        
        Args:
            user_id: User identifier
            summary: ConversationSummary to store
        """
        
        # Load users data
        users_data = DataManager.load_json("system/users.json")
        
        # Find user
        user = None
        for u in users_data.get('users', []):
            if u.get('id') == user_id:
                user = u
                break
        
        if not user:
            # User not found, create entry
            user = {'id': user_id, 'naam': 'Unknown'}
            if 'users' not in users_data:
                users_data['users'] = []
            users_data['users'].append(user)
        
        # Add summary
        if 'conversation_summaries' not in user:
            user['conversation_summaries'] = []
        
        user['conversation_summaries'].append(summary.to_dict())
        
        # Update last summary date
        user['last_summary_date'] = datetime.now(timezone.utc).isoformat()
        
        # Save
        DataManager.save_json("system/users.json", users_data)
    
    def get_summaries(self, user_id: str) -> List[Dict]:
        """
        Get all summaries for a user.
        
        Args:
            user_id: User identifier
        
        Returns:
            List of summary dicts
        """
        
        users_data = DataManager.load_json("system/users.json")
        
        for user in users_data.get('users', []):
            if user.get('id') == user_id:
                return user.get('conversation_summaries', [])
        
        return []
    
    def get_latest_summary(self, user_id: str) -> Optional[Dict]:
        """
        Get most recent summary for a user.
        
        Args:
            user_id: User identifier
        
        Returns:
            Latest summary dict or None
        """
        
        summaries = self.get_summaries(user_id)
        
        if not summaries:
            return None
        
        # Sort by generated_at and return latest
        summaries.sort(key=lambda s: s.get('generated_at', ''), reverse=True)
        
        return summaries[0]
    
    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse timestamp string to datetime"""
        
        try:
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except:
            return datetime.now(timezone.utc)
