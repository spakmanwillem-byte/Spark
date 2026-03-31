# 🏗️ REVISED ARCHITECTURE: Context Layer Integration

**Project:** Spark Foundation  
**Datum:** 10 maart 2026  
**Versie:** 2.0 (Revised)

---

## 🎯 KEY ARCHITECTURAL CHANGE

### **Old Flow (v1.0):**
```
User Input → Content Engine → Emotion Detector → Response
```

### **New Flow (v2.0):**
```
User Input → Content Engine → Context Layer → Emotion Detector → Response
             ↓                ↓                ↓
          What is said    What it means    How it's said
          (Structure)     (Meaning)        (Tone)
```

---

## 📊 THE THREE LAYERS

### **Layer 1: Content Engine**
**Purpose:** Analyze WHAT is written  
**Output:** Structure, keywords, patterns, literal meaning

### **Layer 2: Context Layer** ⭐ NEW
**Purpose:** Determine what it ACTUALLY MEANS  
**Output:** Situational interpretation, intent clarification, sarcasm detection

### **Layer 3: Emotion/Intention Detector**
**Purpose:** Analyze HOW it's said  
**Output:** Tone, intensity, emotional state

---

## 🏗️ CONTEXT LAYER ARCHITECTURE

### **A. Service Structure**

**Locatie:** `/app/backend/services/context_layer.py`

**Core Responsibilities:**
1. **Conversation History Analysis** - What was said before?
2. **Topic Continuity Detection** - Are we still talking about X?
3. **User Pattern Recognition** - How does this user normally communicate?
4. **Situational Context** - What's the current situation?
5. **Semantic Interpretation** - Sarcasm, irony, implicit meaning
6. **Context Enrichment** - Add layers of meaning to content analysis

**Class Structure:**
```python
class ContextLayer:
    def __init__(self):
        self.conversation_service = ConversationService()
        self.context_engine = ContextEngine()  # Existing!
        self.pattern_detector = PatternDetectionService()
        self.user_profile_service = UserProfileService()
    
    # Main entry point
    def enrich(self, 
               content_analysis: ContentAnalysis, 
               user_data: dict,
               session_id: str) -> ContextualAnalysis
    
    # Core methods
    def analyze_conversation_history(self, session_id: str, limit: int = 10) -> ConversationContext
    def detect_topic_continuity(self, current_message: str, history: List[dict]) -> TopicContinuity
    def get_user_patterns(self, user_id: str) -> UserPatterns
    def determine_situation(self, content: ContentAnalysis, history: ConversationContext) -> Situation
    def detect_semantic_nuance(self, content: ContentAnalysis, context: ConversationContext) -> SemanticNuance
    
    # Special detections
    def detect_sarcasm(self, text: str, content: ContentAnalysis, context: ConversationContext) -> SarcasmAnalysis
    def detect_irony(self, text: str, context: ConversationContext) -> bool
    def detect_implicit_meaning(self, text: str, context: ConversationContext) -> Optional[str]
```

---

## 📐 DATA MODELS

### **1. ContextualAnalysis (Main Output)**

```python
@dataclass
class ContextualAnalysis:
    """
    Complete contextual analysis result.
    This is what flows to the Emotion Detector.
    """
    
    # Original input
    text: str
    content_analysis: ContentAnalysis  # From Content Engine
    
    # Conversation context
    conversation_context: ConversationContext
    topic_continuity: TopicContinuity
    
    # User context
    user_patterns: UserPatterns
    interaction_style: str  # "formal", "casual", "playful", "serious"
    
    # Situational context
    situation: Situation
    situational_factors: List[str]  # ["late_night", "frustrated_user", "repeated_question"]
    
    # Semantic interpretation
    semantic_nuance: SemanticNuance
    actual_intent: str  # What they REALLY mean
    confidence: float  # How sure are we?
    
    # Special detections
    is_sarcasm: bool
    sarcasm_analysis: Optional[SarcasmAnalysis]
    is_irony: bool
    implicit_meaning: Optional[str]
    
    # Context-adjusted properties
    adjusted_tone: str  # May differ from content.tone
    adjusted_intent: str  # May differ from content.intent
    emotional_priming: Optional[str]  # "positive", "negative", "neutral"
    
    # Metadata
    analyzed_at: datetime
    processing_time_ms: int
```

---

### **2. ConversationContext**

```python
@dataclass
class ConversationContext:
    """Recent conversation history and patterns"""
    
    # History
    recent_messages: List[Message]  # Last 5-10 messages
    message_count: int
    duration_minutes: float
    
    # Topics discussed
    primary_topic: Optional[str]
    topic_shifts: List[TopicShift]  # When topic changed
    topic_depth: int  # How deep into topic (1-5)
    
    # Patterns
    user_mood_trajectory: str  # "improving", "declining", "stable"
    spark_mood_trajectory: str
    interaction_rhythm: str  # "quick_back_forth", "thoughtful_pauses", "monologue"
    
    # Special markers
    repeated_questions: List[str]  # User asked same thing multiple times
    unresolved_issues: List[str]  # Things Spark couldn't answer
    positive_moments: List[str]  # Compliments, agreements
    negative_moments: List[str]  # Frustrations, disagreements
    
    # Relationships
    mentioned_people: List[str]
    mentioned_places: List[str]
    mentioned_events: List[str]
```

---

### **3. TopicContinuity**

```python
@dataclass
class TopicContinuity:
    """Is current message continuing previous topic?"""
    
    is_continuation: bool
    confidence: float
    
    # Topic tracking
    previous_topic: Optional[str]
    current_topic: Optional[str]
    topic_shift_detected: bool
    
    # Reference detection
    uses_pronouns: bool  # "het", "dit", "dat" (referring to previous)
    references_previous: List[str]  # What from previous message
    
    # Continuity type
    continuity_type: Optional[str]  # "answer", "follow_up", "clarification", "tangent"
    
    # Context clues
    contextual_keywords: List[str]
    assumed_knowledge: List[str]  # Things user assumes Spark knows
```

---

### **4. UserPatterns**

```python
@dataclass
class UserPatterns:
    """This specific user's communication patterns"""
    
    # Communication style
    typical_message_length: str  # "short", "medium", "long"
    formality_level: float  # 0.0 (casual) - 1.0 (formal)
    emoji_usage: str  # "never", "rare", "frequent"
    
    # Personality indicators
    uses_humor: bool
    uses_sarcasm_frequently: bool  # Important!
    politeness_level: float
    directness: float  # 0.0 (indirect) - 1.0 (direct)
    
    # Interaction preferences
    asks_many_questions: bool
    teaches_often: bool
    seeks_emotional_support: bool
    wants_quick_answers: bool
    
    # Historical context
    total_conversations: int
    total_messages: int
    favorite_topics: List[str]
    avoided_topics: List[str]
    
    # Trust & relationship
    trust_level: float  # 0.0 - 1.0
    relationship_stage: str  # "stranger", "acquaintance", "friend", "close"
    shared_experiences: List[str]
```

---

### **5. Situation**

```python
@dataclass
class Situation:
    """Current situational context"""
    
    # Temporal
    time_of_day: str  # "morning", "afternoon", "evening", "night", "late_night"
    day_of_week: str
    is_weekend: bool
    
    # Conversational
    conversation_stage: str  # "greeting", "main", "closing", "problem_solving"
    conversation_tone: str  # "light", "serious", "urgent", "playful"
    
    # User state (inferred)
    inferred_user_state: str  # "relaxed", "busy", "frustrated", "excited", "tired"
    stress_indicators: List[str]
    energy_level: str  # "low", "normal", "high"
    
    # Spark state
    spark_current_emotion: str
    spark_recent_actions: List[str]
    
    # External factors
    first_message_today: bool
    long_absence: bool  # User hasn't chatted in days
    returning_to_topic: bool  # User brings up old topic
```

---

### **6. SemanticNuance**

```python
@dataclass
class SemanticNuance:
    """Semantic layer - what does it REALLY mean?"""
    
    # Core interpretation
    literal_meaning: str  # What they said
    actual_meaning: str  # What they meant
    interpretation_confidence: float
    
    # Nuance types
    is_literal: bool  # Take at face value
    is_figurative: bool  # Metaphor, idiom
    is_sarcastic: bool
    is_ironic: bool
    is_rhetorical: bool  # Rhetorical question
    
    # Implicit elements
    implicit_request: Optional[str]  # Hidden request
    implied_emotion: Optional[str]  # Emotion they're not saying
    unstated_context: List[str]  # Things they assume you know
    
    # Social dynamics
    face_saving: bool  # Trying to save face
    indirect_criticism: bool  # Criticizing without saying so
    hidden_compliment: bool  # Compliment disguised as criticism
    
    # Interpretation notes
    interpretation_reasons: List[str]  # Why we think this
    alternative_interpretations: List[str]  # Other possible meanings
```

---

### **7. SarcasmAnalysis**

```python
@dataclass
class SarcasmAnalysis:
    """Detailed sarcasm detection"""
    
    is_sarcasm: bool
    confidence: float
    
    # Evidence
    sarcasm_indicators: List[str]
    contradictory_elements: List[str]  # Positive words + negative context
    
    # Type
    sarcasm_type: str  # "compliment_as_insult", "overstatement", "understatement"
    
    # Context clues
    requires_context: bool  # Needs previous message to detect
    context_contradiction: str  # How it contradicts context
    
    # Examples of indicators:
    # - "Dat was slim van je" after user made obvious mistake
    # - "Geweldig hoor" with negative context
    # - Over-the-top praise that doesn't fit situation
```

---

## 🔄 INTEGRATION FLOW

### **Complete Analysis Pipeline**

```python
# In spark_brain.py

def process_message(self, message: str, user_data: dict, session_id: str):
    """
    Complete 3-layer analysis pipeline
    """
    
    # LAYER 1: Content Analysis (What is said)
    content_analysis = ContentEngine().analyze(
        text=message,
        context={"user": user_data}
    )
    
    # LAYER 2: Context Enrichment (What it means)
    contextual_analysis = ContextLayer().enrich(
        content_analysis=content_analysis,
        user_data=user_data,
        session_id=session_id
    )
    
    # LAYER 3: Emotion Detection (How it's said)
    emotional_analysis = EmotionDetector().detect(
        text=message,
        content=content_analysis,
        context=contextual_analysis  # ← Enriched with full context!
    )
    
    # RESPONSE GENERATION
    # Now we have complete understanding:
    # - What they said (content)
    # - What they meant (context)
    # - How they feel (emotion)
    
    response = self._generate_contextual_response(
        message=message,
        content=content_analysis,
        context=contextual_analysis,
        emotion=emotional_analysis,
        user_data=user_data
    )
    
    return response
```

---

## 🎯 CONTEXT LAYER IMPLEMENTATION

### **Core Class**

```python
# /app/backend/services/context_layer.py

from dataclasses import dataclass
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from services.conversation_service import ConversationService
from services.context_engine import ContextEngine
from services.user_profile_service import UserProfileService
from services.pattern_detection_service import PatternDetectionService

class ContextLayer:
    """
    Context Layer: Bridges Content and Emotion.
    Determines what the content ACTUALLY MEANS in the current situation.
    """
    
    def __init__(self):
        # Reuse existing services
        self.conversation_service = ConversationService()
        self.context_engine = ContextEngine()  # Existing context engine
        self.user_profile = UserProfileService()
        self.pattern_detector = PatternDetectionService()
    
    def enrich(self, 
               content_analysis: ContentAnalysis,
               user_data: dict,
               session_id: str) -> ContextualAnalysis:
        """
        Main entry point: Enrich content analysis with context
        
        Args:
            content_analysis: Output from ContentEngine
            user_data: User profile data
            session_id: Current session ID
            
        Returns:
            ContextualAnalysis with full contextual interpretation
        """
        start_time = datetime.now()
        
        # Step 1: Get conversation history
        conversation_context = self.analyze_conversation_history(
            session_id=session_id,
            limit=10
        )
        
        # Step 2: Detect topic continuity
        topic_continuity = self.detect_topic_continuity(
            current_message=content_analysis.text,
            history=conversation_context.recent_messages,
            current_topics=content_analysis.primary_topic
        )
        
        # Step 3: Get user patterns
        user_patterns = self.get_user_patterns(
            user_id=user_data.get("id"),
            user_data=user_data
        )
        
        # Step 4: Determine current situation
        situation = self.determine_situation(
            content=content_analysis,
            history=conversation_context,
            user_data=user_data
        )
        
        # Step 5: Detect semantic nuance (sarcasm, irony, etc.)
        semantic_nuance = self.detect_semantic_nuance(
            text=content_analysis.text,
            content=content_analysis,
            context=conversation_context,
            user_patterns=user_patterns,
            situation=situation
        )
        
        # Step 6: Determine actual intent (may differ from content.intent)
        actual_intent = self._determine_actual_intent(
            content_intent=content_analysis.intent,
            semantic_nuance=semantic_nuance,
            situation=situation
        )
        
        # Step 7: Adjust tone based on context
        adjusted_tone = self._adjust_tone(
            content_tone=content_analysis.tone,
            semantic_nuance=semantic_nuance,
            situation=situation
        )
        
        # Step 8: Determine emotional priming
        emotional_priming = self._determine_emotional_priming(
            conversation_context=conversation_context,
            situation=situation
        )
        
        # Step 9: Calculate confidence
        confidence = self._calculate_confidence(
            content_analysis=content_analysis,
            conversation_context=conversation_context,
            semantic_nuance=semantic_nuance
        )
        
        # Build result
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return ContextualAnalysis(
            text=content_analysis.text,
            content_analysis=content_analysis,
            conversation_context=conversation_context,
            topic_continuity=topic_continuity,
            user_patterns=user_patterns,
            interaction_style=user_patterns.formality_level,
            situation=situation,
            situational_factors=self._extract_situational_factors(situation),
            semantic_nuance=semantic_nuance,
            actual_intent=actual_intent,
            confidence=confidence,
            is_sarcasm=semantic_nuance.is_sarcastic,
            sarcasm_analysis=semantic_nuance.sarcasm_details if semantic_nuance.is_sarcastic else None,
            is_irony=semantic_nuance.is_ironic,
            implicit_meaning=semantic_nuance.implicit_request,
            adjusted_tone=adjusted_tone,
            adjusted_intent=actual_intent,
            emotional_priming=emotional_priming,
            analyzed_at=datetime.now(),
            processing_time_ms=int(processing_time)
        )
    
    def analyze_conversation_history(self, session_id: str, limit: int = 10) -> ConversationContext:
        """Analyze recent conversation history"""
        
        # Get recent messages from ConversationService
        history = self.conversation_service.get_recent_context(session_id, limit)
        
        if not history:
            return self._empty_conversation_context()
        
        # Parse messages
        recent_messages = history.get("messages", [])
        
        # Extract topics discussed
        all_text = " ".join([m.get("message", "") for m in recent_messages])
        topics = self.pattern_detector.analyze_message(all_text).get("topics", [])
        
        # Detect topic shifts
        topic_shifts = self._detect_topic_shifts(recent_messages)
        
        # Analyze mood trajectory
        user_mood_trajectory = self._analyze_mood_trajectory(recent_messages, "user")
        spark_mood_trajectory = self._analyze_mood_trajectory(recent_messages, "spark")
        
        # Detect patterns
        repeated_questions = self._find_repeated_questions(recent_messages)
        positive_moments = self._find_positive_moments(recent_messages)
        negative_moments = self._find_negative_moments(recent_messages)
        
        # Interaction rhythm
        interaction_rhythm = self._determine_interaction_rhythm(recent_messages)
        
        return ConversationContext(
            recent_messages=recent_messages,
            message_count=len(recent_messages),
            duration_minutes=self._calculate_duration(recent_messages),
            primary_topic=topics[0] if topics else None,
            topic_shifts=topic_shifts,
            topic_depth=self._calculate_topic_depth(recent_messages, topics),
            user_mood_trajectory=user_mood_trajectory,
            spark_mood_trajectory=spark_mood_trajectory,
            interaction_rhythm=interaction_rhythm,
            repeated_questions=repeated_questions,
            unresolved_issues=[],  # TODO: detect from conversation
            positive_moments=positive_moments,
            negative_moments=negative_moments,
            mentioned_people=[],  # TODO: NER
            mentioned_places=[],
            mentioned_events=[]
        )
    
    def detect_topic_continuity(self, 
                                current_message: str,
                                history: List[dict],
                                current_topics: str) -> TopicContinuity:
        """Detect if current message continues previous topic"""
        
        if not history or len(history) < 1:
            return TopicContinuity(
                is_continuation=False,
                confidence=0.0,
                previous_topic=None,
                current_topic=current_topics,
                topic_shift_detected=False,
                uses_pronouns=False,
                references_previous=[],
                continuity_type=None,
                contextual_keywords=[],
                assumed_knowledge=[]
            )
        
        # Get previous message
        previous = history[-1].get("message", "")
        
        # Check for pronouns (referring to previous)
        pronouns = ["het", "dit", "dat", "ze", "hij", "zij", "hun"]
        uses_pronouns = any(p in current_message.lower() for p in pronouns)
        
        # Extract topics from previous
        prev_analysis = self.pattern_detector.analyze_message(previous)
        prev_topics = prev_analysis.get("topics", [])
        
        # Check topic overlap
        current_lower = current_message.lower()
        topic_overlap = [t for t in prev_topics if t in current_lower]
        
        # Determine if continuation
        is_continuation = (
            len(topic_overlap) > 0 or
            uses_pronouns or
            self._is_answer_pattern(current_message)
        )
        
        confidence = 0.0
        if topic_overlap:
            confidence += 0.6
        if uses_pronouns:
            confidence += 0.3
        if self._is_answer_pattern(current_message):
            confidence += 0.4
        confidence = min(confidence, 1.0)
        
        # Detect continuity type
        continuity_type = None
        if is_continuation:
            if self._is_answer_pattern(current_message):
                continuity_type = "answer"
            elif "?" in current_message:
                continuity_type = "follow_up"
            elif any(w in current_message.lower() for w in ["bedoel je", "snap ik", "dus"]):
                continuity_type = "clarification"
            else:
                continuity_type = "continuation"
        
        return TopicContinuity(
            is_continuation=is_continuation,
            confidence=confidence,
            previous_topic=prev_topics[0] if prev_topics else None,
            current_topic=current_topics,
            topic_shift_detected=not is_continuation,
            uses_pronouns=uses_pronouns,
            references_previous=topic_overlap,
            continuity_type=continuity_type,
            contextual_keywords=topic_overlap,
            assumed_knowledge=prev_topics
        )
    
    def detect_semantic_nuance(self,
                               text: str,
                               content: ContentAnalysis,
                               context: ConversationContext,
                               user_patterns: UserPatterns,
                               situation: Situation) -> SemanticNuance:
        """Detect sarcasm, irony, and other semantic nuances"""
        
        text_lower = text.lower()
        
        # Detect sarcasm
        sarcasm_analysis = self.detect_sarcasm(
            text=text,
            content=content,
            context=context,
            user_patterns=user_patterns
        )
        
        # Detect irony
        is_irony = self.detect_irony(text, context)
        
        # Check if literal or figurative
        is_literal = not (sarcasm_analysis.is_sarcasm or is_irony)
        is_figurative = not is_literal
        
        # Detect rhetorical questions
        is_rhetorical = self._is_rhetorical_question(text, context)
        
        # Detect implicit meaning
        implicit_request = self._detect_implicit_request(text, content, context)
        implied_emotion = self._detect_implied_emotion(text, context)
        
        # Unstated context
        unstated_context = self._detect_unstated_context(text, context)
        
        # Social dynamics
        face_saving = self._detect_face_saving(text, context)
        indirect_criticism = self._detect_indirect_criticism(text, content)
        hidden_compliment = self._detect_hidden_compliment(text, content)
        
        # Determine actual vs literal meaning
        if sarcasm_analysis.is_sarcasm:
            actual_meaning = self._invert_meaning(text, content)
            interpretation_confidence = sarcasm_analysis.confidence
        elif implicit_request:
            actual_meaning = implicit_request
            interpretation_confidence = 0.7
        else:
            actual_meaning = text
            interpretation_confidence = 0.9
        
        # Build interpretation reasons
        interpretation_reasons = []
        if sarcasm_analysis.is_sarcasm:
            interpretation_reasons.extend(sarcasm_analysis.sarcasm_indicators)
        if is_irony:
            interpretation_reasons.append("Ironic context detected")
        if implicit_request:
            interpretation_reasons.append(f"Implicit request: {implicit_request}")
        
        return SemanticNuance(
            literal_meaning=text,
            actual_meaning=actual_meaning,
            interpretation_confidence=interpretation_confidence,
            is_literal=is_literal,
            is_figurative=is_figurative,
            is_sarcastic=sarcasm_analysis.is_sarcasm,
            is_ironic=is_irony,
            is_rhetorical=is_rhetorical,
            implicit_request=implicit_request,
            implied_emotion=implied_emotion,
            unstated_context=unstated_context,
            face_saving=face_saving,
            indirect_criticism=indirect_criticism,
            hidden_compliment=hidden_compliment,
            interpretation_reasons=interpretation_reasons,
            alternative_interpretations=[]  # TODO
        )
    
    def detect_sarcasm(self,
                      text: str,
                      content: ContentAnalysis,
                      context: ConversationContext,
                      user_patterns: UserPatterns) -> SarcasmAnalysis:
        """
        Detect sarcasm using content + context
        
        Example: "Dat was slim van je" after user made mistake
        """
        text_lower = text.lower()
        
        # Sarcasm indicators
        sarcasm_indicators = []
        confidence = 0.0
        
        # Pattern 1: Positive words + negative context
        positive_words = ["slim", "geweldig", "super", "top", "goed gedaan", "knap"]
        has_positive = any(word in text_lower for word in positive_words)
        
        if has_positive and len(context.negative_moments) > 0:
            sarcasm_indicators.append("Positive words after negative context")
            confidence += 0.4
        
        # Pattern 2: Over-the-top praise
        over_the_top = ["geweldig hoor", "super hoor", "ja hoor", "natuurlijk"]
        if any(phrase in text_lower for phrase in over_the_top):
            sarcasm_indicators.append("Over-the-top expression detected")
            confidence += 0.3
        
        # Pattern 3: User tends to use sarcasm
        if user_patterns.uses_sarcasm_frequently:
            sarcasm_indicators.append("User frequently uses sarcasm")
            confidence += 0.2
        
        # Pattern 4: Contradictory elements
        if content.language_style.contains_compliments and len(context.negative_moments) > 0:
            sarcasm_indicators.append("Compliment contradicts recent negative exchange")
            confidence += 0.4
        
        # Pattern 5: Specific sarcastic phrases
        sarcastic_phrases = ["ja hoor", "natuurlijk niet", "vast wel", "zeker weten"]
        if any(phrase in text_lower for phrase in sarcastic_phrases):
            sarcasm_indicators.append(f"Sarcastic phrase: {[p for p in sarcastic_phrases if p in text_lower][0]}")
            confidence += 0.5
        
        # Determine sarcasm type
        sarcasm_type = "unknown"
        if has_positive and context.negative_moments:
            sarcasm_type = "compliment_as_insult"
        elif any(phrase in text_lower for phrase in over_the_top):
            sarcasm_type = "overstatement"
        
        # Context contradiction
        context_contradiction = ""
        if len(context.negative_moments) > 0:
            context_contradiction = f"Recent negative: {context.negative_moments[-1]}"
        
        is_sarcasm = confidence > 0.5
        
        return SarcasmAnalysis(
            is_sarcasm=is_sarcasm,
            confidence=min(confidence, 1.0),
            sarcasm_indicators=sarcasm_indicators,
            contradictory_elements=[],
            sarcasm_type=sarcasm_type if is_sarcasm else None,
            requires_context=len(context.recent_messages) > 0,
            context_contradiction=context_contradiction
        )
    
    # ... More helper methods ...
    # (truncated for brevity - full implementation would include all helpers)
```

---

## 🔗 UPDATED EMOTION DETECTOR

### **Now Context-Aware**

```python
# /app/backend/services/emotion_detector.py (UPDATED)

class EmotionDetector:
    def detect(self, 
               text: str,
               content: ContentAnalysis,
               context: ContextualAnalysis) -> EmotionalAnalysis:  # ← Now takes ContextualAnalysis!
        """
        Detect emotion with full contextual awareness
        """
        
        # Step 1: Find emotional signals (same as before)
        signals = self.analyze_emotional_signals(text)
        
        # Step 2: Map to base emotions
        emotion_mapping = self.map_to_base_emotions(signals)
        
        # Step 3: ADJUST based on context! ⭐
        if context.is_sarcasm:
            # Invert emotion if sarcastic
            emotion_mapping = self._invert_emotion_mapping(emotion_mapping)
        
        # Step 4: Consider conversation mood trajectory
        if context.conversation_context.user_mood_trajectory == "declining":
            # Bias towards negative emotions
            emotion_mapping.sad_score *= 1.3
            emotion_mapping.angry_score *= 1.2
        
        # Step 5: Consider situational factors
        if "frustrated_user" in context.situational_factors:
            emotion_mapping.angry_score *= 1.4
        
        # Step 6: Use adjusted tone from context
        primary_emotion = self._determine_primary_from_adjusted_tone(
            emotion_mapping,
            context.adjusted_tone
        )
        
        # ... rest of detection ...
        
        return EmotionalAnalysis(...)
```

---

## 📊 COMPLETE INTEGRATION DIAGRAM

```
┌─────────────────────────────────────────────────────┐
│              USER INPUT (Text)                      │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │    LAYER 1: Content Engine │
        │    - Keywords              │
        │    - Intent (literal)      │
        │    - Language Style        │
        │    - Compliments           │
        └────────────┬───────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │    LAYER 2: Context Layer  │ ⭐ NEW
        │    - Conversation History  │
        │    - Topic Continuity      │
        │    - User Patterns         │
        │    - Sarcasm Detection     │
        │    - Actual Intent         │
        └────────────┬───────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │  LAYER 3: Emotion Detector │
        │    - Emotional Signals     │
        │    - Context-Adjusted      │
        │    - Intensity             │
        │    - Spark Emotion         │
        └────────────┬───────────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │    SPARK RESPONSE          │
        │    (Contextually Aware)    │
        └────────────────────────────┘
```

---

## 🎯 EXAMPLE: "Dat was slim van je"

### **Scenario 1: After User Success**

**User History:**
```
[5 min ago] "Ik heb het eindelijk opgelost!"
[2 min ago] "Het werkt nu perfect!"
[now] "Dat was slim van je"  ← analyzing this
```

**Analysis Flow:**

**Content Engine:**
- Keywords: ["slim"]
- Intent: compliment
- Tone: friendly

**Context Layer:**
- Conversation: Recent positive moments detected
- Topic Continuity: References "oplossen" (solving)
- Sarcasm Detection: NO (positive context)
- Actual Meaning: Genuine compliment

**Emotion Detector:**
- Primary: happy
- Context-adjusted: happy (confirmed)
- Intensity: 0.7

**Result:** Spark interprets as genuine compliment ✅

---

### **Scenario 2: After User Mistake**

**User History:**
```
[5 min ago] "Dit werkt niet!"
[3 min ago] "Ik snap er niets van"
[1 min ago] "Oh wacht, ik deed het verkeerd"
[now] "Dat was slim van je"  ← analyzing this
```

**Analysis Flow:**

**Content Engine:**
- Keywords: ["slim"]
- Intent: compliment
- Tone: friendly

**Context Layer:**
- Conversation: Recent negative moments + user made mistake
- Topic Continuity: References mistake
- **Sarcasm Detection: YES** ⭐
  - Positive words after negative context
  - User made mistake, then "compliments" themselves
  - Confidence: 0.75
- **Actual Meaning: Self-deprecating sarcasm**

**Emotion Detector:**
- Primary: happy (inverted due to sarcasm)
- Context-adjusted: frustrated/embarrassed
- Intensity: 0.6

**Result:** Spark understands user is being sarcastic about their mistake ✅

**Spark can now respond appropriately:**
- "Haha, gebeurt ons allemaal! Het belangrijkste is dat je het door had."

Instead of misinterpreting as genuine compliment.

---

## 🏗️ MODULAR STRUCTURE

### **How It Stays Modular:**

**1. Clear Interfaces**
```python
# Each layer has defined input/output
ContentEngine.analyze(text) → ContentAnalysis
ContextLayer.enrich(ContentAnalysis) → ContextualAnalysis
EmotionDetector.detect(text, content, context) → EmotionalAnalysis
```

**2. Independent Testing**
```python
# Can test each layer separately
test_content_engine()  # No context needed
test_context_layer()   # Mock ContentAnalysis
test_emotion_detector()  # Mock all inputs
```

**3. Optional Layers**
```python
# Can skip Context Layer if needed
if simple_mode:
    emotion = EmotionDetector().detect(text, content, context=None)
else:
    context = ContextLayer().enrich(content, user, session)
    emotion = EmotionDetector().detect(text, content, context)
```

**4. Reuses Existing Code**
- `ConversationService` ✅
- `ContextEngine` ✅ (existing!)
- `PatternDetectionService` ✅
- No duplicate logic

**5. Gradual Enhancement**
```python
# Start simple, add features over time
class ContextLayer:
    # Phase 1: Basic conversation history
    def analyze_conversation_history(): ...
    
    # Phase 2: Add sarcasm detection
    def detect_sarcasm(): ...
    
    # Phase 3: Add user patterns
    def get_user_patterns(): ...
    
    # Phase 4: Add situation awareness
    def determine_situation(): ...
```

---

## 📅 REVISED IMPLEMENTATION TIMELINE

### **FASE 1: Content Engine** (Week 1) - 12-16h
*(No changes from original)*

### **FASE 2: Context Layer** (Week 2) - 14-18h ⭐ NEW
1. **Core ContextLayer class** (4h)
   - Data models
   - Main enrich() method
   - Conversation history analysis

2. **Topic & User Patterns** (4h)
   - Topic continuity detection
   - User pattern recognition
   - Situation determination

3. **Sarcasm & Semantic Detection** (6h)
   - Sarcasm detection logic
   - Irony detection
   - Implicit meaning

4. **Testing** (3h)
   - Unit tests
   - "Dat was slim" test cases
   - Edge cases

### **FASE 3: Emotion Detector (Updated)** (Week 3) - 10-14h
*(Updated to use ContextualAnalysis)*

### **FASE 4: Integration & API** (Week 4) - 8-12h
*(Update integration to include Context Layer)*

**Total:** 44-60 hours over 4 weeks

---

## ✅ BENEFITS OF THIS ARCHITECTURE

**1. Proper Separation of Concerns**
- Content = Structure
- Context = Meaning
- Emotion = Tone

**2. Solves Sarcasm Problem** ⭐
- "Dat was slim van je" correctly interpreted

**3. Enables Future Features**
- Topic-based responses
- Relationship tracking
- Adaptive communication style
- Long-term memory

**4. Maintains Modularity**
- Each layer independent
- Clear interfaces
- Testable

**5. Scales Well**
- Can add more context sources later
- Doesn't break existing code
- Gradual enhancement path

---

## 🎯 SUMMARY

**Key Change:**
Added dedicated **Context Layer** between Content and Emotion.

**What Context Layer Does:**
- Analyzes conversation history
- Detects topic continuity
- Recognizes user patterns
- Determines situational context
- **Detects sarcasm, irony, implicit meaning**
- Provides actual interpretation

**Flow:**
```
Content (What) → Context (Meaning) → Emotion (How)
```

**Modularity:**
- Clear interfaces
- Independent testing
- Reuses existing services
- Gradual enhancement

**Timeline:**
+1 week for Context Layer (14-18h)

---

**Does this architecture solve your concern about context?** 🎯

**Ready to approve and implement?** 🚀
