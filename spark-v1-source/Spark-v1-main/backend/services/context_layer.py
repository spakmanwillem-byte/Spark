"""
Context Layer - Transforms ContentAnalysis into ContextualAnalysis

This is Layer 2 of the analysis pipeline:
- Layer 1: Content Engine (WHAT is said)
- Layer 2: Context Layer (WHAT it means in context)  ← This file
- Layer 3: Emotion Detector (HOW user feels) - Future

The Context Layer enriches content analysis with:
- Conversation history patterns (Cache - Layer 1)
- Long-term patterns (Summaries - Layer 2) ← NEW!
- Topic continuity
- User patterns over time
- Situational awareness
- Semantic nuances (sarcasm, references, etc.)
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
from services.content_engine import ContentAnalysis
from services.conversation_cache_service import ConversationCacheService
from services.summarization_service import SummarizationService


@dataclass
class ConversationContext:
    """Rich conversation context"""
    recent_topics: List[str] = field(default_factory=list)
    topic_shifts: int = 0
    conversation_depth: int = 0  # How many exchanges
    
    # Patterns
    recurring_questions: List[str] = field(default_factory=list)
    user_interests: List[str] = field(default_factory=list)
    
    # Emotional arc
    recent_tones: List[str] = field(default_factory=list)
    tone_trajectory: str = "stable"  # "improving", "declining", "stable"
    
    # Conversation type
    is_casual_chat: bool = False
    is_deep_inquiry: bool = False
    is_problem_solving: bool = False
    
    # Long-term patterns (from summaries) ← NEW!
    long_term_topics: List[str] = field(default_factory=list)
    historical_mood: str = "stable"
    learned_concepts_count: int = 0


@dataclass
class ContextualAnalysis:
    """
    Complete contextual analysis - output van Context Layer.
    Combines ContentAnalysis + conversation context.
    """
    # Original content analysis
    content: ContentAnalysis
    
    # Conversation context
    conversation: ConversationContext
    
    # Topic analysis
    is_topic_continuation: bool = False
    is_topic_shift: bool = False
    previous_topic: Optional[str] = None
    
    # User patterns
    user_shows_curiosity: bool = False
    user_shows_frustration: bool = False
    user_shows_enthusiasm: bool = False
    
    # Semantic understanding
    likely_sarcasm: bool = False
    likely_rhetorical: bool = False
    references_previous_message: bool = False
    
    # Situational context
    conversation_phase: str = "ongoing"  # "greeting", "ongoing", "closing"
    suggested_response_style: str = "informative"  # "informative", "empathetic", "playful", "brief"
    
    # Metadata
    analyzed_at: datetime = field(default_factory=datetime.now)
    confidence: float = 0.0


class ContextLayer:
    """
    Context Layer - Layer 2 van de analysis pipeline.
    
    Transforms ContentAnalysis into ContextualAnalysis by adding:
    - Conversation history patterns (Cache - Layer 1)
    - Long-term patterns (Summaries - Layer 2) ← NEW!
    - Topic continuity
    - User behavior patterns
    - Semantic nuances
    
    Uses the 3-layer memory strategy:
    - Layer 1: Cache (immediate history, 0.02ms)
    - Layer 2: Summaries (long-term patterns, 1-5ms) ← NEW!
    - Layer 3: Full history (on-demand, 100-500ms) - Future
    """
    
    def __init__(self):
        self.cache_service = ConversationCacheService()
        self.summarization_service = SummarizationService()
    
    def enrich(
        self,
        content_analysis: ContentAnalysis,
        user_data: Dict,
        session_id: str
    ) -> ContextualAnalysis:
        """
        Main entry point: Enrich ContentAnalysis with context.
        
        Args:
            content_analysis: Output from ContentEngine
            user_data: User profile data
            session_id: Current session ID
        
        Returns:
            ContextualAnalysis with rich contextual understanding
        """
        
        # Get conversation history from cache (Layer 1)
        conversation_context = self.cache_service.get_conversation_context(
            user_id=user_data["id"],
            session_id=session_id,
            limit=10
        )
        
        # Get long-term patterns from summaries (Layer 2)
        latest_summary = self.summarization_service.get_latest_summary(user_data["id"])
        
        # Build conversation context
        conv_ctx = self._build_conversation_context(conversation_context, latest_summary)
        
        # Analyze topic continuity
        is_continuation, is_shift, prev_topic = self._analyze_topic_continuity(
            current_topic=content_analysis.primary_topic,
            recent_topics=conv_ctx.recent_topics
        )
        
        # Detect user patterns
        curiosity, frustration, enthusiasm = self._detect_user_patterns(
            content_analysis,
            conv_ctx
        )
        
        # Semantic analysis
        sarcasm, rhetorical, references = self._semantic_analysis(
            content_analysis,
            conversation_context
        )
        
        # Determine conversation phase
        phase = self._determine_conversation_phase(
            content_analysis,
            conv_ctx
        )
        
        # Suggest response style
        response_style = self._suggest_response_style(
            content_analysis,
            conv_ctx,
            phase
        )
        
        # Calculate confidence
        confidence = self._calculate_confidence(
            content_analysis,
            conversation_context
        )
        
        # Build ContextualAnalysis
        return ContextualAnalysis(
            content=content_analysis,
            conversation=conv_ctx,
            is_topic_continuation=is_continuation,
            is_topic_shift=is_shift,
            previous_topic=prev_topic,
            user_shows_curiosity=curiosity,
            user_shows_frustration=frustration,
            user_shows_enthusiasm=enthusiasm,
            likely_sarcasm=sarcasm,
            likely_rhetorical=rhetorical,
            references_previous_message=references,
            conversation_phase=phase,
            suggested_response_style=response_style,
            analyzed_at=datetime.now(),
            confidence=confidence
        )
    
    def _build_conversation_context(
        self,
        conversation_data: Dict,
        latest_summary: Optional[Dict] = None
    ) -> ConversationContext:
        """Build ConversationContext from cache data + summaries"""
        
        messages = conversation_data.get('messages', [])
        topics = conversation_data.get('topics', [])
        # emotions = conversation_data.get('emotions', [])  # Not used yet
        
        # Recent topics (last 5 unique)
        recent_topics = list(dict.fromkeys(topics))[-5:]
        
        # Topic shifts (how often topic changed)
        topic_shifts = 0
        for i in range(1, len(topics)):
            if topics[i] != topics[i-1]:
                topic_shifts += 1
        
        # Conversation depth
        conversation_depth = len(messages) // 2  # Pairs of exchanges
        
        # Recent tones (extract from messages if available)
        recent_tones = []
        # TODO: Extract from cached messages
        
        # Determine conversation type
        is_casual = conversation_depth < 3
        is_deep = conversation_depth > 5
        is_problem_solving = False  # TODO: Detect from intents
        
        # Enrich with summary data (Layer 2)
        long_term_topics = []
        historical_mood = "stable"
        learned_concepts_count = 0
        
        if latest_summary:
            long_term_topics = latest_summary.get('primary_topics', [])[:5]
            historical_mood = latest_summary.get('mood_trajectory', 'stable')
            learned_concepts_count = len(latest_summary.get('learned_concepts', []))
        
        return ConversationContext(
            recent_topics=recent_topics,
            topic_shifts=topic_shifts,
            conversation_depth=conversation_depth,
            recent_tones=recent_tones,
            is_casual_chat=is_casual,
            is_deep_inquiry=is_deep,
            is_problem_solving=is_problem_solving,
            long_term_topics=long_term_topics,
            historical_mood=historical_mood,
            learned_concepts_count=learned_concepts_count
        )
    
    def _analyze_topic_continuity(
        self,
        current_topic: Optional[str],
        recent_topics: List[str]
    ) -> tuple[bool, bool, Optional[str]]:
        """
        Analyze if current topic continues or shifts from previous.
        
        Returns:
            (is_continuation, is_shift, previous_topic)
        """
        if not current_topic or not recent_topics:
            return False, False, None
        
        previous_topic = recent_topics[-1] if recent_topics else None
        
        # Check if continuing same topic
        is_continuation = current_topic == previous_topic
        
        # Check if shifting to new topic
        is_shift = current_topic != previous_topic and previous_topic is not None
        
        return is_continuation, is_shift, previous_topic
    
    def _detect_user_patterns(
        self,
        content: ContentAnalysis,
        conv_ctx: ConversationContext
    ) -> tuple[bool, bool, bool]:
        """
        Detect user behavioral patterns.
        
        Returns:
            (curiosity, frustration, enthusiasm)
        """
        
        # Curiosity: questions, learning intent
        curiosity = (
            content.intent.is_question or
            content.intent.primary_intent == "teaching" or
            "?" in content.text
        )
        
        # Frustration: urgent tone, negative sentiment, CAPS
        frustration = (
            content.tone == "urgent" or
            content.sentiment == "negatief" or
            content.language_style.uses_capitals
        )
        
        # Enthusiasm: compliments, excited tone, emoji
        enthusiasm = (
            content.compliments.has_compliment or
            content.tone == "playful" or
            content.language_style.uses_emoji
        )
        
        return curiosity, frustration, enthusiasm
    
    def _semantic_analysis(
        self,
        content: ContentAnalysis,
        conversation_data: Dict
    ) -> tuple[bool, bool, bool]:
        """
        Detect semantic nuances.
        
        Returns:
            (sarcasm, rhetorical, references_previous)
        """
        
        # Sarcasm: positive words with negative context or vice versa
        # TODO: More sophisticated sarcasm detection
        sarcasm = False
        
        # Rhetorical: question but statement intent
        rhetorical = (
            content.intent.is_question and
            content.intent.question_type == "yes_no" and
            "!" in content.text
        )
        
        # References previous: words like "dat", "dit", "zo", "ook"
        reference_words = ["dat", "dit", "zo", "ook", "toen", "daarom"]
        references = any(word in content.text.lower() for word in reference_words)
        
        return sarcasm, rhetorical, references
    
    def _determine_conversation_phase(
        self,
        content: ContentAnalysis,
        conv_ctx: ConversationContext
    ) -> str:
        """
        Determine what phase of conversation we're in.
        
        Returns:
            "greeting", "ongoing", "closing"
        """
        
        # Greeting phase
        if content.intent.primary_intent == "greeting" or conv_ctx.conversation_depth <= 1:
            return "greeting"
        
        # Closing phase
        closing_signals = ["bedankt", "dank je", "dag", "doei", "later"]
        if any(signal in content.text.lower() for signal in closing_signals):
            return "closing"
        
        # Ongoing
        return "ongoing"
    
    def _suggest_response_style(
        self,
        content: ContentAnalysis,
        conv_ctx: ConversationContext,
        phase: str
    ) -> str:
        """
        Suggest appropriate response style.
        
        Returns:
            "informative", "empathetic", "playful", "brief", "detailed"
        """
        
        # Empathetic for frustration or negative sentiment
        if content.tone == "urgent" or content.sentiment == "negatief":
            return "empathetic"
        
        # Playful for casual, friendly tone
        if content.tone in ["playful", "casual"] and content.language_style.uses_emoji:
            return "playful"
        
        # Brief for greetings or simple acknowledgments
        if phase == "greeting" or content.language_style.word_count < 10:
            return "brief"
        
        # Detailed for deep inquiry or teaching
        if conv_ctx.is_deep_inquiry or content.intent.is_teaching:
            return "detailed"
        
        # Default: informative
        return "informative"
    
    def _calculate_confidence(
        self,
        content: ContentAnalysis,
        conversation_data: Dict
    ) -> float:
        """
        Calculate confidence in contextual analysis.
        
        Based on:
        - Content analysis confidence
        - Amount of conversation history
        - Clarity of patterns
        """
        confidence = 0.0
        
        # Base confidence from content analysis
        confidence += content.confidence * 0.5
        
        # Boost for conversation history
        message_count = conversation_data.get('message_count', 0)
        if message_count > 5:
            confidence += 0.2
        elif message_count > 2:
            confidence += 0.1
        
        # Boost for clear patterns
        if content.keywords.topics:
            confidence += 0.1
        
        if content.intent.confidence > 0.8:
            confidence += 0.1
        
        return min(1.0, confidence)
