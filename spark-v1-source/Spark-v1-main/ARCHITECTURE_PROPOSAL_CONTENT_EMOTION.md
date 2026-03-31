# 🏗️ ARCHITECTUUR VOORSTEL: Content Engine & Emotion Detection

**Project:** Spark Foundation  
**Datum:** 10 maart 2026  
**Versie:** 1.0

---

## 🎯 EXECUTIVE SUMMARY

**Doel:** Twee geïntegreerde systemen die Spark's begrip van content en emoties fundamenteel verbeteren.

**Systemen:**
1. **Content Engine** - Analyseer en structureer content naar knowledge layers
2. **Emotion/Intention Detection** - Detecteer emotionele signalen en intent

**Strategie:** Build on existing infrastructure, create modular services, maintain backward compatibility.

---

## 📊 HUIDIGE INFRASTRUCTUUR (Hergebruik)

### **Bestaande Services die We Hergebruiken:**

| Service | Huidige Rol | Nieuwe Rol |
|---------|-------------|------------|
| `nlp_service.py` | Command detection, sentiment | **Basis NLP** voor beide systemen |
| `pattern_detection_service.py` | Stopwords, key phrases | **Pattern engine** voor content |
| `classification_service.py` | Topic classification | **Context detection** |
| `emotion_service.py` | Spark's emotions | **Emotion state management** |
| `context_engine.py` | User context | **Context provider** |

**Strategie:** Niet vervangen, maar **uitbreiden en verbinden**.

---

## 🏗️ ARCHITECTUUR OVERZICHT

```
┌─────────────────────────────────────────────────────────────┐
│                    USER INPUT (Text)                         │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │     CONTENT ENGINE (New)              │
        │  - Parse & Structure                  │
        │  - Extract Keywords                   │
        │  - Detect Context                     │
        │  - Analyze Language Style             │
        └───────┬───────────────────┬───────────┘
                │                   │
                ▼                   ▼
    ┌──────────────────┐   ┌──────────────────┐
    │  Knowledge Layer │   │  Emotion/Intent  │
    │  Generator       │   │  Detector (New)  │
    └──────────────────┘   └────────┬─────────┘
                                     │
                                     ▼
                          ┌──────────────────────┐
                          │  Spark Emotion       │
                          │  State Manager       │
                          └──────────────────────┘
```

---

## 1️⃣ CONTENT ENGINE

### **A. Service Architecture**

**Locatie:** `/app/backend/services/content_engine.py`

**Core Responsibilities:**
1. **Parse Content** - Break down text into analyzable units
2. **Extract Keywords** - Identify important terms and concepts
3. **Detect Context** - Understand domain and topic
4. **Analyze Language** - Detect tone, formality, friendliness
5. **Structure to Layers** - Map to Spark's knowledge layers (1-4)

**Class Structure:**
```python
class ContentEngine:
    def __init__(self):
        self.nlp = NLPService()
        self.pattern_detector = PatternDetectionService()
        self.classifier = ClassificationService()
    
    # Main entry point
    def analyze(self, text: str, context: dict = None) -> ContentAnalysis
    
    # Core methods
    def extract_keywords(self, text: str) -> List[Keyword]
    def detect_context(self, text: str, entities: dict) -> Context
    def analyze_language_style(self, text: str) -> LanguageStyle
    def detect_compliments(self, text: str) -> List[Compliment]
    def detect_intent(self, text: str) -> Intent
    
    # Knowledge layer mapping
    def structure_to_knowledge_layers(self, analysis: ContentAnalysis) -> KnowledgeLayers
```

---

### **B. Data Models**

**1. ContentAnalysis (Main Output)**
```python
@dataclass
class ContentAnalysis:
    """Complete content analysis result"""
    
    # Basic info
    text: str
    word_count: int
    sentence_count: int
    
    # Keywords
    keywords: List[Keyword]
    primary_topic: str
    secondary_topics: List[str]
    
    # Context
    context: Context
    domain: str  # "natuur", "technologie", "persoonlijk", etc.
    
    # Language style
    language_style: LanguageStyle
    tone: str  # "vriendelijk", "formeel", "neutraal", "speels"
    complexity: str  # "simpel", "normaal", "complex"
    
    # Special detections
    compliments: List[Compliment]
    questions: List[str]
    key_statements: List[str]
    
    # Intent
    intent: Intent
    
    # Knowledge mapping (for KB creation)
    suggested_layers: KnowledgeLayers
    confidence: float  # 0.0 - 1.0
    
    # Metadata
    analyzed_at: datetime
    processing_time_ms: int
```

**2. Keyword**
```python
@dataclass
class Keyword:
    word: str
    importance: float  # 0.0 - 1.0
    frequency: int
    category: str  # "concept", "entity", "action", "descriptor"
    context: str  # Surrounding context
```

**3. Context**
```python
@dataclass
class Context:
    domain: str  # Primary domain
    sub_domain: Optional[str]
    related_topics: List[str]
    entities: Dict[str, List[str]]  # {"personen": [...], "locaties": [...]}
    temporal_context: Optional[str]  # "verleden", "heden", "toekomst"
    social_context: str  # "persoonlijk", "professioneel", "algemeen"
```

**4. LanguageStyle**
```python
@dataclass
class LanguageStyle:
    tone: str  # "vriendelijk", "formeel", "neutraal", "speels", "serieus"
    formality: float  # 0.0 (casual) - 1.0 (formal)
    friendliness: float  # 0.0 (cold) - 1.0 (warm)
    complexity: str  # "simpel", "normaal", "complex"
    
    # Style indicators
    uses_emoji: bool
    uses_questions: bool
    uses_exclamations: bool
    sentence_length_avg: float
    
    # Politeness
    politeness_markers: List[str]  # ["alsjeblieft", "graag", "dank je"]
    
    # Special patterns
    contains_compliments: bool
    contains_criticism: bool
    contains_humor: bool
```

**5. Compliment**
```python
@dataclass
class Compliment:
    text: str  # The compliment itself
    target: str  # Who/what is complimented
    type: str  # "appearance", "skill", "character", "work", "general"
    intensity: float  # 0.0 - 1.0
```

**6. Intent**
```python
@dataclass
class Intent:
    primary_intent: str  # "learn", "share", "ask", "command", "chat"
    confidence: float  # 0.0 - 1.0
    sub_intents: List[str]
    
    # Intent categories
    is_question: bool
    is_command: bool
    is_teaching: bool
    is_seeking_help: bool
    is_social: bool
    
    # Action required
    requires_action: bool
    suggested_action: Optional[str]
```

**7. KnowledgeLayers (for KB creation)**
```python
@dataclass
class KnowledgeLayers:
    begrip: str  # The concept
    
    laag1: str  # Basis definitie (extracted from content)
    laag2: str  # Context (generated)
    laag3: str  # Diepte (generated)
    laag4: Optional[str]  # Verdieping (optional)
    
    suggested_tags: List[str]
    suggested_topic: str
    confidence: float
```

---

### **C. Implementation Example**

```python
# /app/backend/services/content_engine.py

from dataclasses import dataclass
from typing import List, Optional, Dict
from datetime import datetime
import re
from collections import Counter

class ContentEngine:
    """
    Core content analysis engine.
    Analyzes text and structures it for Spark's knowledge system.
    """
    
    def __init__(self):
        from services.nlp_service import NLPService
        from services.pattern_detection_service import PatternDetectionService
        from services.classification_service import ClassificationService
        
        self.nlp = NLPService()
        self.pattern_detector = PatternDetectionService
        self.classifier = ClassificationService()
        
        # Load language patterns
        self._load_patterns()
    
    def _load_patterns(self):
        """Load detection patterns for compliments, tone, etc."""
        self.compliment_patterns = [
            r'je bent (?:echt |zo |heel )?(geweldig|fantastisch|super|top|geweldig|slim|mooi)',
            r'dat is (?:echt |zo )?(goed|mooi|knap|slim|interessant)',
            r'goed (?:gedaan|werk|bezig)',
            r'je doet het (goed|geweldig|super)',
        ]
        
        self.friendly_markers = [
            "graag", "alsjeblieft", "dank je", "bedankt", "fijn", "leuk",
            "😊", "🙏", "❤️", "👍", "🎉"
        ]
        
        self.formal_markers = [
            "meneer", "mevrouw", "u ", "geachte", "bijgaand", "hoogachtend"
        ]
    
    def analyze(self, text: str, context: dict = None) -> ContentAnalysis:
        """
        Main entry point: Complete content analysis
        
        Args:
            text: Input text to analyze
            context: Optional user context
            
        Returns:
            ContentAnalysis object with all findings
        """
        start_time = datetime.now()
        
        # Step 1: Basic text metrics
        word_count = len(text.split())
        sentences = re.split(r'[.!?]+', text)
        sentence_count = len([s for s in sentences if s.strip()])
        
        # Step 2: Extract keywords
        keywords = self.extract_keywords(text)
        
        # Step 3: Classify and get entities
        entities = self._extract_entities(text)
        classification = self.classifier.classify_topic(text, entities)
        
        # Step 4: Detect context
        content_context = self.detect_context(text, entities, classification)
        
        # Step 5: Analyze language style
        language_style = self.analyze_language_style(text)
        
        # Step 6: Detect compliments
        compliments = self.detect_compliments(text)
        
        # Step 7: Detect intent
        intent = self.detect_intent(text, context)
        
        # Step 8: Extract special content
        questions = self._extract_questions(text)
        key_statements = self._extract_key_statements(text)
        
        # Step 9: Map to knowledge layers (if applicable)
        suggested_layers = self._suggest_knowledge_layers(
            text, keywords, content_context, classification
        )
        
        # Calculate overall confidence
        confidence = self._calculate_confidence(
            keywords, classification, intent
        )
        
        # Build result
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return ContentAnalysis(
            text=text,
            word_count=word_count,
            sentence_count=sentence_count,
            keywords=keywords,
            primary_topic=classification.get("klasse", "Algemeen"),
            secondary_topics=classification.get("labels", {}).get("context", []),
            context=content_context,
            domain=content_context.domain,
            language_style=language_style,
            tone=language_style.tone,
            complexity=language_style.complexity,
            compliments=compliments,
            questions=questions,
            key_statements=key_statements,
            intent=intent,
            suggested_layers=suggested_layers,
            confidence=confidence,
            analyzed_at=datetime.now(),
            processing_time_ms=int(processing_time)
        )
    
    def extract_keywords(self, text: str) -> List[Keyword]:
        """Extract important keywords with scoring"""
        # Use pattern detector
        analysis = self.pattern_detector.analyze_message(text)
        topics = analysis.get("topics", [])
        
        # Extract all words
        words = re.findall(r'\b\w{4,}\b', text.lower())
        word_freq = Counter(words)
        
        keywords = []
        for word, freq in word_freq.most_common(10):
            # Skip common words
            if word in ['deze', 'zijn', 'maar', 'voor', 'naar']:
                continue
            
            importance = min(freq / len(words) * 10, 1.0)
            
            # Boost if in pattern detector topics
            if word in topics:
                importance = min(importance * 1.5, 1.0)
            
            # Categorize
            category = self._categorize_keyword(word, text)
            
            keywords.append(Keyword(
                word=word,
                importance=importance,
                frequency=freq,
                category=category,
                context=self._get_keyword_context(word, text)
            ))
        
        return keywords
    
    def detect_context(self, text: str, entities: dict, classification: dict) -> Context:
        """Detect content context and domain"""
        
        # Determine domain from classification
        domain = classification.get("klasse", "Algemeen")
        sub_domain = classification.get("sub_klasse")
        
        # Extract related topics
        related_topics = self.pattern_detector.analyze_message(text).get("topics", [])
        
        # Determine temporal context
        temporal_indicators = {
            "verleden": ["was", "had", "ging", "deed", "vroeger", "toen"],
            "heden": ["is", "ben", "doe", "nu", "momenteel", "vandaag"],
            "toekomst": ["zal", "ga", "wordt", "morgen", "binnenkort", "straks"]
        }
        
        temporal_context = "heden"  # default
        text_lower = text.lower()
        for time, indicators in temporal_indicators.items():
            if any(ind in text_lower for ind in indicators):
                temporal_context = time
                break
        
        # Determine social context
        social_context = "algemeen"
        if any(w in text_lower for w in ["ik", "mijn", "me"]):
            social_context = "persoonlijk"
        elif any(w in text_lower for w in ["werk", "klant", "project", "meeting"]):
            social_context = "professioneel"
        
        return Context(
            domain=domain,
            sub_domain=sub_domain,
            related_topics=related_topics,
            entities=entities,
            temporal_context=temporal_context,
            social_context=social_context
        )
    
    def analyze_language_style(self, text: str) -> LanguageStyle:
        """Analyze language style and tone"""
        text_lower = text.lower()
        
        # Detect tone indicators
        friendly_count = sum(1 for marker in self.friendly_markers if marker in text_lower)
        formal_count = sum(1 for marker in self.formal_markers if marker in text_lower)
        
        # Calculate scores
        friendliness = min(friendly_count / 3.0, 1.0)
        formality = min(formal_count / 3.0, 1.0)
        
        # Determine tone
        if friendliness > 0.5:
            tone = "vriendelijk"
        elif formality > 0.5:
            tone = "formeel"
        elif "!" in text or "?" in text:
            tone = "speels" if friendly_count > 0 else "nieuwsgierig"
        else:
            tone = "neutraal"
        
        # Check for special elements
        uses_emoji = bool(re.search(r'[\U0001F600-\U0001F64F]', text))
        uses_questions = '?' in text
        uses_exclamations = '!' in text
        
        # Sentence length
        sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
        sentence_length_avg = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
        
        # Complexity
        if sentence_length_avg < 8:
            complexity = "simpel"
        elif sentence_length_avg < 15:
            complexity = "normaal"
        else:
            complexity = "complex"
        
        # Extract politeness markers
        politeness_markers = [m for m in self.friendly_markers if m in text_lower]
        
        # Special patterns
        contains_compliments = bool(self.detect_compliments(text))
        contains_criticism = any(w in text_lower for w in ["slecht", "fout", "verkeerd", "niet goed"])
        contains_humor = any(w in text_lower for w in ["haha", "lol", "grappig", "😂"])
        
        return LanguageStyle(
            tone=tone,
            formality=formality,
            friendliness=friendliness,
            complexity=complexity,
            uses_emoji=uses_emoji,
            uses_questions=uses_questions,
            uses_exclamations=uses_exclamations,
            sentence_length_avg=sentence_length_avg,
            politeness_markers=politeness_markers,
            contains_compliments=contains_compliments,
            contains_criticism=contains_criticism,
            contains_humor=contains_humor
        )
    
    def detect_compliments(self, text: str) -> List[Compliment]:
        """Detect compliments in text"""
        compliments = []
        text_lower = text.lower()
        
        for pattern in self.compliment_patterns:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                compliment_text = match.group(0)
                
                # Determine target (who is complimented)
                target = "Spark"  # default
                if "je" in compliment_text or "jij" in compliment_text:
                    target = "Spark"
                
                # Determine type
                comp_type = "general"
                if any(w in compliment_text for w in ["slim", "intelligent"]):
                    comp_type = "skill"
                elif any(w in compliment_text for w in ["mooi", "leuk"]):
                    comp_type = "appearance"
                elif any(w in compliment_text for w in ["goed", "super", "top"]):
                    comp_type = "character"
                
                # Calculate intensity
                intensity = 0.7  # default
                if any(w in compliment_text for w in ["heel", "echt", "zo"]):
                    intensity = 0.9
                if any(w in compliment_text for w in ["geweldig", "fantastisch"]):
                    intensity = 1.0
                
                compliments.append(Compliment(
                    text=compliment_text,
                    target=target,
                    type=comp_type,
                    intensity=intensity
                ))
        
        return compliments
    
    def detect_intent(self, text: str, context: dict = None) -> Intent:
        """Detect user intent"""
        text_lower = text.lower()
        
        # Check for command
        is_command = self.nlp.detect_command(text) is not None
        
        # Check for question
        is_question = '?' in text or self.nlp.is_question(text)
        
        # Check for teaching intent
        is_teaching = any(w in text_lower for w in [
            "onthoud", "leer", "weet je", "snap je", "begrijp je"
        ])
        
        # Check for help seeking
        is_seeking_help = any(w in text_lower for w in [
            "help", "hulp", "snap het niet", "weet niet", "hoe doe"
        ])
        
        # Check for social
        is_social = self.nlp.is_greeting(text) or any(w in text_lower for w in [
            "hoe gaat het", "hoe is het", "alles goed"
        ])
        
        # Determine primary intent
        if is_command:
            primary_intent = "command"
            confidence = 0.9
        elif is_question:
            primary_intent = "ask"
            confidence = 0.8
        elif is_teaching:
            primary_intent = "teach"
            confidence = 0.7
        elif is_seeking_help:
            primary_intent = "seek_help"
            confidence = 0.8
        elif is_social:
            primary_intent = "chat"
            confidence = 0.6
        else:
            primary_intent = "share"
            confidence = 0.5
        
        # Collect sub-intents
        sub_intents = []
        if is_question: sub_intents.append("question")
        if is_teaching: sub_intents.append("teaching")
        if is_social: sub_intents.append("social")
        
        # Determine if action is required
        requires_action = is_command or is_seeking_help or is_question
        
        # Suggest action
        suggested_action = None
        if is_command:
            suggested_action = "execute_command"
        elif is_question:
            suggested_action = "provide_answer"
        elif is_teaching:
            suggested_action = "store_knowledge"
        
        return Intent(
            primary_intent=primary_intent,
            confidence=confidence,
            sub_intents=sub_intents,
            is_question=is_question,
            is_command=is_command,
            is_teaching=is_teaching,
            is_seeking_help=is_seeking_help,
            is_social=is_social,
            requires_action=requires_action,
            suggested_action=suggested_action
        )
    
    # Helper methods
    def _extract_entities(self, text: str) -> Dict:
        """Extract entities using NLP"""
        # Simplified - could use spaCy NER
        return {
            "personen": [],
            "locaties": [],
            "organisaties": []
        }
    
    def _categorize_keyword(self, word: str, text: str) -> str:
        """Categorize a keyword"""
        # Simplified categorization
        action_words = ["maken", "doen", "gaan", "worden", "zijn"]
        if word in action_words:
            return "action"
        return "concept"
    
    def _get_keyword_context(self, word: str, text: str) -> str:
        """Get surrounding context of keyword"""
        sentences = re.split(r'[.!?]+', text)
        for sentence in sentences:
            if word in sentence.lower():
                return sentence.strip()[:100]
        return ""
    
    def _extract_questions(self, text: str) -> List[str]:
        """Extract questions from text"""
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() + '?' for s in sentences if '?' in s or self.nlp.is_question(s)]
    
    def _extract_key_statements(self, text: str) -> List[str]:
        """Extract key statements"""
        analysis = self.pattern_detector.analyze_message(text)
        return analysis.get("key_phrases", [])
    
    def _suggest_knowledge_layers(self, text: str, keywords: List[Keyword], 
                                  context: Context, classification: dict) -> Optional[KnowledgeLayers]:
        """Suggest knowledge layer structure"""
        # Only if this looks like knowledge content
        if len(keywords) < 2 or context.domain == "Algemeen":
            return None
        
        # Extract main concept
        begrip = keywords[0].word.capitalize() if keywords else "Concept"
        
        # Generate layers (simplified)
        laag1 = f"{begrip} is {text[:80]}..."
        laag2 = f"Context: {context.domain}"
        laag3 = text[:200] if len(text) > 200 else text
        
        tags = [kw.word for kw in keywords[:5]]
        
        return KnowledgeLayers(
            begrip=begrip,
            laag1=laag1,
            laag2=laag2,
            laag3=laag3,
            laag4=None,
            suggested_tags=tags,
            suggested_topic=context.domain.lower(),
            confidence=0.6
        )
    
    def _calculate_confidence(self, keywords: List[Keyword], 
                             classification: dict, intent: Intent) -> float:
        """Calculate overall confidence"""
        scores = [
            len(keywords) / 10.0,  # More keywords = higher confidence
            classification.get("confidence", 0.0),
            intent.confidence
        ]
        return sum(scores) / len(scores)
```

---

## 2️⃣ EMOTION/INTENTION DETECTION

### **A. Service Architecture**

**Locatie:** `/app/backend/services/emotion_detector.py`

**Core Responsibilities:**
1. **Analyze Text Emotionally** - Detect emotional signals
2. **Map to Spark's 4 Base Emotions** - Translate to Spark's emotional model
3. **Detect Sentiment Intensity** - How strong is the emotion?
4. **Provide Emotional Context** - Why did we detect this emotion?
5. **Feed Spark's Emotion State** - Optionally trigger emotion changes

**Spark's 4 Base Emotions:**
```python
BASE_EMOTIONS = {
    "happy": {
        "keywords": ["blij", "gelukkig", "fijn", "leuk", "geweldig", "super", "top"],
        "emoji": ["😊", "😀", "🎉", "❤️", "👍"],
        "intensity_multipliers": {"heel": 1.5, "echt": 1.3, "zo": 1.2}
    },
    "sad": {
        "keywords": ["verdrietig", "somber", "jammer", "spijt", "helaas"],
        "emoji": ["😢", "😞", "💔"],
        "intensity_multipliers": {"heel": 1.5, "erg": 1.4}
    },
    "angry": {
        "keywords": ["boos", "gefrustreerd", "irritant", "vervelend", "slecht"],
        "emoji": ["😠", "😡", "💢"],
        "intensity_multipliers": {"heel": 1.6, "ontzettend": 1.8}
    },
    "neutral": {
        "keywords": ["ok", "oké", "goed", "prima", "normaal"],
        "emoji": ["😐", "🤔"],
        "intensity_multipliers": {}
    }
}
```

**Class Structure:**
```python
class EmotionDetector:
    def __init__(self):
        self.nlp = NLPService()
        self.content_engine = ContentEngine()
        self._load_emotion_patterns()
    
    # Main entry point
    def detect(self, text: str, context: dict = None) -> EmotionalAnalysis
    
    # Core methods
    def analyze_emotional_signals(self, text: str) -> List[EmotionalSignal]
    def map_to_base_emotions(self, signals: List[EmotionalSignal]) -> EmotionMapping
    def calculate_intensity(self, emotion: str, text: str) -> float
    def get_emotional_context(self, emotion: str, text: str) -> str
    
    # Integration with Spark's emotion system
    def should_trigger_emotion_change(self, analysis: EmotionalAnalysis, user_data: dict) -> bool
    def suggest_emotion_transition(self, current_emotion: str, detected_emotion: str) -> Optional[str]
```

---

### **B. Data Models**

**1. EmotionalAnalysis (Main Output)**
```python
@dataclass
class EmotionalAnalysis:
    """Complete emotional analysis of text"""
    
    text: str
    
    # Detected emotion
    primary_emotion: str  # "happy", "sad", "angry", "neutral"
    confidence: float  # 0.0 - 1.0
    intensity: float  # 0.0 (mild) - 1.0 (extreme)
    
    # Supporting evidence
    emotional_signals: List[EmotionalSignal]
    emotion_mapping: EmotionMapping
    
    # Context
    emotional_context: str  # Why this emotion?
    trigger_words: List[str]
    
    # Spark integration
    should_trigger_change: bool
    suggested_spark_emotion: Optional[str]  # Spark's 13 sub-emotions
    suggested_intensity: float
    
    # Metadata
    analyzed_at: datetime
```

**2. EmotionalSignal**
```python
@dataclass
class EmotionalSignal:
    """Individual emotional indicator found in text"""
    
    signal_type: str  # "keyword", "emoji", "punctuation", "context"
    emotion: str  # Which emotion it indicates
    strength: float  # 0.0 - 1.0
    source: str  # The actual word/emoji
    context: str  # Surrounding text
```

**3. EmotionMapping**
```python
@dataclass
class EmotionMapping:
    """Mapping of detected emotions to Spark's system"""
    
    # Base emotions (Spark's 4)
    happy_score: float
    sad_score: float
    angry_score: float
    neutral_score: float
    
    # Dominant emotion
    dominant: str
    dominant_score: float
    
    # Spark's sub-emotion suggestion
    suggested_sub_emotion: Optional[str]
    reason: str
```

---

### **C. Implementation Example**

```python
# /app/backend/services/emotion_detector.py

from dataclasses import dataclass
from typing import List, Optional, Dict
from datetime import datetime
import re

class EmotionDetector:
    """
    Emotion and intention detection system.
    Analyzes text for emotional signals and maps to Spark's emotion model.
    """
    
    # Spark's 4 base emotions with detection patterns
    BASE_EMOTIONS = {
        "happy": {
            "keywords": [
                "blij", "gelukkig", "fijn", "leuk", "geweldig", "super", "top",
                "fantastisch", "perfect", "mooi", "prettig", "vrolijk", "tevreden"
            ],
            "emoji": ["😊", "😀", "😃", "😄", "🎉", "❤️", "👍", "✨", "🌟"],
            "patterns": [
                r'\b(heel|erg|zo) (blij|gelukkig|fijn)',
                r'(super|geweldig|fantastisch)',
                r'(dank je|bedankt|thanks)'
            ],
            "intensity_multipliers": {
                "heel": 1.5, "erg": 1.4, "zo": 1.3, "echt": 1.3,
                "super": 1.6, "mega": 1.7
            }
        },
        "sad": {
            "keywords": [
                "verdrietig", "somber", "jammer", "spijt", "helaas", "triest",
                "pijn", "missen", "alleen", "eenzaam", "verlies"
            ],
            "emoji": ["😢", "😞", "😔", "💔", "😭"],
            "patterns": [
                r'\b(heel|erg|zo) (verdrietig|somber)',
                r'(jammer|helaas) (dat|genoeg)',
                r'(mis|verlang)'
            ],
            "intensity_multipliers": {
                "heel": 1.5, "erg": 1.4, "zo": 1.3, "enorm": 1.6
            }
        },
        "angry": {
            "keywords": [
                "boos", "gefrustreerd", "irritant", "vervelend", "slecht", "kwaad",
                "woedend", "ergert", "zeik", "stomme", "irriteert"
            ],
            "emoji": ["😠", "😡", "💢", "😤"],
            "patterns": [
                r'\b(heel|erg|zo) (boos|gefrustreerd)',
                r'(irritant|vervelend|slecht)',
                r'(wtf|damn|shit)'
            ],
            "intensity_multipliers": {
                "heel": 1.6, "ontzettend": 1.8, "verschrikkelijk": 2.0
            }
        },
        "neutral": {
            "keywords": [
                "ok", "oké", "goed", "prima", "normaal", "rustig", "kalm"
            ],
            "emoji": ["😐", "🤔", "😶"],
            "patterns": [r'(ok|prima|goed hoor)'],
            "intensity_multipliers": {}
        }
    }
    
    def __init__(self):
        from services.nlp_service import NLPService
        self.nlp = NLPService()
        self._load_emotion_patterns()
    
    def _load_emotion_patterns(self):
        """Compile regex patterns for efficiency"""
        self.compiled_patterns = {}
        for emotion, data in self.BASE_EMOTIONS.items():
            self.compiled_patterns[emotion] = [
                re.compile(pattern, re.IGNORECASE) 
                for pattern in data.get("patterns", [])
            ]
    
    def detect(self, text: str, context: dict = None) -> EmotionalAnalysis:
        """
        Main entry point: Detect emotion and intention
        
        Args:
            text: Input text to analyze
            context: Optional context (user data, conversation history)
            
        Returns:
            EmotionalAnalysis with complete findings
        """
        # Step 1: Find all emotional signals
        signals = self.analyze_emotional_signals(text)
        
        # Step 2: Map signals to base emotions
        emotion_mapping = self.map_to_base_emotions(signals)
        
        # Step 3: Determine primary emotion
        primary_emotion = emotion_mapping.dominant
        confidence = emotion_mapping.dominant_score
        
        # Step 4: Calculate intensity
        intensity = self.calculate_intensity(primary_emotion, text, signals)
        
        # Step 5: Get emotional context (why this emotion?)
        emotional_context = self.get_emotional_context(primary_emotion, text, signals)
        
        # Step 6: Extract trigger words
        trigger_words = [s.source for s in signals if s.emotion == primary_emotion]
        
        # Step 7: Decide if Spark should change emotion
        should_trigger = self.should_trigger_emotion_change(
            emotion_mapping, context
        )
        
        # Step 8: Suggest Spark emotion (if applicable)
        suggested_emotion = None
        if should_trigger:
            suggested_emotion = self.suggest_spark_emotion(
                primary_emotion, intensity
            )
        
        return EmotionalAnalysis(
            text=text,
            primary_emotion=primary_emotion,
            confidence=confidence,
            intensity=intensity,
            emotional_signals=signals,
            emotion_mapping=emotion_mapping,
            emotional_context=emotional_context,
            trigger_words=trigger_words,
            should_trigger_change=should_trigger,
            suggested_spark_emotion=suggested_emotion,
            suggested_intensity=intensity,
            analyzed_at=datetime.now()
        )
    
    def analyze_emotional_signals(self, text: str) -> List[EmotionalSignal]:
        """Find all emotional indicators in text"""
        signals = []
        text_lower = text.lower()
        
        for emotion, data in self.BASE_EMOTIONS.items():
            # Check keywords
            for keyword in data["keywords"]:
                if keyword in text_lower:
                    strength = 0.7  # Base strength
                    
                    # Check for intensity multipliers
                    for multiplier, factor in data.get("intensity_multipliers", {}).items():
                        if multiplier in text_lower:
                            strength = min(strength * factor, 1.0)
                    
                    signals.append(EmotionalSignal(
                        signal_type="keyword",
                        emotion=emotion,
                        strength=strength,
                        source=keyword,
                        context=self._get_context(keyword, text)
                    ))
            
            # Check emoji
            for emoji in data["emoji"]:
                if emoji in text:
                    signals.append(EmotionalSignal(
                        signal_type="emoji",
                        emotion=emotion,
                        strength=0.8,
                        source=emoji,
                        context=""
                    ))
            
            # Check patterns
            for pattern in self.compiled_patterns.get(emotion, []):
                matches = pattern.finditer(text)
                for match in matches:
                    signals.append(EmotionalSignal(
                        signal_type="pattern",
                        emotion=emotion,
                        strength=0.9,
                        source=match.group(0),
                        context=self._get_context(match.group(0), text)
                    ))
        
        # Check punctuation (exclamations = excitement)
        exclamation_count = text.count('!')
        if exclamation_count > 0:
            strength = min(exclamation_count / 3.0, 1.0)
            # Could be happy or angry - check context
            has_positive = any(s.emotion == "happy" for s in signals)
            has_negative = any(s.emotion == "angry" for s in signals)
            
            emotion = "happy" if has_positive else ("angry" if has_negative else "happy")
            signals.append(EmotionalSignal(
                signal_type="punctuation",
                emotion=emotion,
                strength=strength,
                source="!",
                context="exclamation"
            ))
        
        return signals
    
    def map_to_base_emotions(self, signals: List[EmotionalSignal]) -> EmotionMapping:
        """Map signals to Spark's 4 base emotions"""
        # Aggregate scores
        scores = {
            "happy": 0.0,
            "sad": 0.0,
            "angry": 0.0,
            "neutral": 0.0
        }
        
        for signal in signals:
            scores[signal.emotion] += signal.strength
        
        # Normalize
        total = sum(scores.values())
        if total > 0:
            scores = {k: v / total for k, v in scores.items()}
        else:
            scores["neutral"] = 1.0
        
        # Find dominant
        dominant = max(scores, key=scores.get)
        dominant_score = scores[dominant]
        
        # Suggest Spark sub-emotion
        sub_emotion = self._map_to_sub_emotion(dominant, dominant_score)
        
        return EmotionMapping(
            happy_score=scores["happy"],
            sad_score=scores["sad"],
            angry_score=scores["angry"],
            neutral_score=scores["neutral"],
            dominant=dominant,
            dominant_score=dominant_score,
            suggested_sub_emotion=sub_emotion,
            reason=f"Dominant emotion based on {len([s for s in signals if s.emotion == dominant])} signals"
        )
    
    def calculate_intensity(self, emotion: str, text: str, signals: List[EmotionalSignal]) -> float:
        """Calculate intensity of detected emotion"""
        # Count signals for this emotion
        relevant_signals = [s for s in signals if s.emotion == emotion]
        
        if not relevant_signals:
            return 0.0
        
        # Average strength
        avg_strength = sum(s.strength for s in relevant_signals) / len(relevant_signals)
        
        # Boost by signal count
        count_factor = min(len(relevant_signals) / 5.0, 1.0)
        
        # Combine
        intensity = (avg_strength + count_factor) / 2.0
        
        return min(intensity, 1.0)
    
    def get_emotional_context(self, emotion: str, text: str, signals: List[EmotionalSignal]) -> str:
        """Explain why this emotion was detected"""
        relevant_signals = [s for s in signals if s.emotion == emotion]
        
        if not relevant_signals:
            return "Geen duidelijke emotionele signalen"
        
        # Describe the signals
        signal_types = {}
        for signal in relevant_signals:
            signal_types.setdefault(signal.signal_type, []).append(signal.source)
        
        parts = []
        if "keyword" in signal_types:
            parts.append(f"Emotionele woorden: {', '.join(signal_types['keyword'][:3])}")
        if "emoji" in signal_types:
            parts.append(f"Emoji: {' '.join(signal_types['emoji'][:3])}")
        if "pattern" in signal_types:
            parts.append("Emotionele patronen gedetecteerd")
        
        return "; ".join(parts)
    
    def should_trigger_emotion_change(self, emotion_mapping: EmotionMapping, context: dict = None) -> bool:
        """Decide if Spark should change emotion"""
        # Only trigger if confidence is high
        if emotion_mapping.dominant_score < 0.6:
            return False
        
        # Don't trigger for neutral
        if emotion_mapping.dominant == "neutral":
            return False
        
        # Check if user is admin (admins can trigger)
        if context and context.get("rol") in ["admin", "master"]:
            return emotion_mapping.dominant_score > 0.5
        
        # For regular users, need very strong signal
        return emotion_mapping.dominant_score > 0.8
    
    def suggest_spark_emotion(self, base_emotion: str, intensity: float) -> Optional[str]:
        """Map detected emotion to Spark's 13 sub-emotions"""
        
        # Mapping from base to sub-emotions
        emotion_map = {
            "happy": {
                0.3: "blij",
                0.6: "enthousiast",
                0.9: "euforie"
            },
            "sad": {
                0.3: "neerslachtig",
                0.6: "verdrietig",
                0.9: "somber"
            },
            "angry": {
                0.3: "geïrriteerd",
                0.6: "boos",
                0.9: "woede"
            }
        }
        
        if base_emotion not in emotion_map:
            return None
        
        # Find appropriate sub-emotion based on intensity
        thresholds = emotion_map[base_emotion]
        for threshold, sub_emotion in sorted(thresholds.items()):
            if intensity <= threshold:
                return sub_emotion
        
        # Return highest intensity
        return list(thresholds.values())[-1]
    
    # Helper methods
    def _get_context(self, word: str, text: str, window: int = 50) -> str:
        """Get surrounding context of a word"""
        text_lower = text.lower()
        word_lower = word.lower()
        
        pos = text_lower.find(word_lower)
        if pos == -1:
            return ""
        
        start = max(0, pos - window)
        end = min(len(text), pos + len(word) + window)
        
        return text[start:end].strip()
    
    def _map_to_sub_emotion(self, base_emotion: str, score: float) -> Optional[str]:
        """Map base emotion + score to sub-emotion"""
        return self.suggest_spark_emotion(base_emotion, score)
```

---

## 3️⃣ INTEGRATION: Content Engine → Emotion Detector

### **Flow Architecture**

```python
# In spark_brain.py - process_message()

def process_message(self, message: str, user_data: dict, session_id: str):
    # Step 1: Content analysis
    content_analysis = ContentEngine().analyze(message, context=user_data)
    
    # Step 2: Emotional analysis (fed by content analysis)
    emotional_analysis = EmotionDetector().detect(
        message, 
        context={
            "user": user_data,
            "content_style": content_analysis.language_style,
            "intent": content_analysis.intent
        }
    )
    
    # Step 3: Decide response strategy based on both
    if emotional_analysis.should_trigger_change:
        # Update Spark's emotion
        EmotionService.set_emotion(
            state=emotional_analysis.primary_emotion,
            sub_state=emotional_analysis.suggested_spark_emotion,
            intensity=emotional_analysis.suggested_intensity,
            triggered_by="auto_detection"
        )
    
    # Step 4: Use content analysis for response generation
    response = self._generate_response(
        message,
        content_analysis=content_analysis,
        emotional_analysis=emotional_analysis,
        user_data=user_data
    )
    
    return response
```

---

## 4️⃣ API ENDPOINTS

### **A. Content Engine API**

```python
# /app/backend/routes/content_routes.py

from fastapi import APIRouter, HTTPException
from services.content_engine import ContentEngine

router = APIRouter(prefix="/api/content", tags=["content"])

@router.post("/analyze")
async def analyze_content(request: AnalyzeRequest):
    """
    Analyze content and return structured analysis
    
    POST /api/content/analyze
    Body: {
        "text": "...",
        "context": {...}
    }
    """
    engine = ContentEngine()
    result = engine.analyze(request.text, request.context)
    
    return {
        "success": True,
        "analysis": result
    }

@router.post("/extract-knowledge")
async def extract_knowledge(request: ExtractKnowledgeRequest):
    """
    Extract knowledge layers from content
    
    POST /api/content/extract-knowledge
    Body: {
        "text": "...",
        "auto_create": false
    }
    """
    engine = ContentEngine()
    analysis = engine.analyze(request.text)
    
    if not analysis.suggested_layers:
        raise HTTPException(400, "No knowledge structure detected")
    
    if request.auto_create:
        # Auto-create knowledge entry
        knowledge = KnowledgeService.add_knowledge(
            begrip=analysis.suggested_layers.begrip,
            laag1=analysis.suggested_layers.laag1,
            laag2=analysis.suggested_layers.laag2,
            laag3=analysis.suggested_layers.laag3,
            tags=analysis.suggested_layers.suggested_tags,
            topic=analysis.suggested_layers.suggested_topic,
            created_by_admin="AI"
        )
        return {"success": True, "knowledge": knowledge}
    
    return {
        "success": True,
        "suggested_layers": analysis.suggested_layers
    }
```

### **B. Emotion Detector API**

```python
# /app/backend/routes/emotion_detection_routes.py

from fastapi import APIRouter
from services.emotion_detector import EmotionDetector

router = APIRouter(prefix="/api/emotion", tags=["emotion"])

@router.post("/detect")
async def detect_emotion(request: EmotionDetectRequest):
    """
    Detect emotion in text
    
    POST /api/emotion/detect
    Body: {
        "text": "...",
        "context": {...}
    }
    """
    detector = EmotionDetector()
    result = detector.detect(request.text, request.context)
    
    return {
        "success": True,
        "analysis": result
    }

@router.post("/analyze-batch")
async def analyze_batch(request: BatchAnalyzeRequest):
    """
    Analyze multiple texts (for conversation history)
    
    POST /api/emotion/analyze-batch
    Body: {
        "texts": ["...", "..."],
        "aggregate": true
    }
    """
    detector = EmotionDetector()
    results = [detector.detect(text) for text in request.texts]
    
    if request.aggregate:
        # Aggregate emotions over conversation
        emotion_counts = {}
        for result in results:
            emotion_counts.setdefault(result.primary_emotion, 0)
            emotion_counts[result.primary_emotion] += 1
        
        dominant = max(emotion_counts, key=emotion_counts.get)
        
        return {
            "success": True,
            "results": results,
            "aggregate": {
                "dominant_emotion": dominant,
                "emotion_distribution": emotion_counts,
                "overall_tone": dominant
            }
        }
    
    return {"success": True, "results": results}
```

---

## 5️⃣ FRONTEND INTEGRATION

### **A. Content Analysis UI**

```jsx
// /app/frontend/src/components/ContentAnalyzer.js

import React, { useState } from 'react';
import { Button } from './ui/button';
import { Textarea } from './ui/textarea';
import { Card } from './ui/card';

export function ContentAnalyzer() {
  const [text, setText] = useState('');
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);

  const analyzeContent = async () => {
    setLoading(true);
    
    const response = await fetch(`${API}/api/content/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    });
    
    const data = await response.json();
    setAnalysis(data.analysis);
    setLoading(false);
  };

  return (
    <div className="space-y-4">
      <Textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Plak hier content om te analyseren..."
        rows={8}
      />
      
      <Button onClick={analyzeContent} disabled={loading}>
        {loading ? 'Analyseren...' : 'Analyseer Content'}
      </Button>
      
      {analysis && (
        <Card className="p-4 space-y-4">
          <div>
            <h3 className="font-bold">Keywords</h3>
            <div className="flex flex-wrap gap-2">
              {analysis.keywords.map((kw, i) => (
                <span key={i} className="px-2 py-1 bg-blue-100 rounded">
                  {kw.word} ({(kw.importance * 100).toFixed(0)}%)
                </span>
              ))}
            </div>
          </div>
          
          <div>
            <h3 className="font-bold">Context</h3>
            <p>Domain: {analysis.domain}</p>
            <p>Tone: {analysis.tone}</p>
          </div>
          
          <div>
            <h3 className="font-bold">Intent</h3>
            <p>{analysis.intent.primary_intent}</p>
          </div>
          
          {analysis.suggested_layers && (
            <div>
              <h3 className="font-bold">Knowledge Layers</h3>
              <pre className="text-sm bg-gray-50 p-2 rounded">
                {JSON.stringify(analysis.suggested_layers, null, 2)}
              </pre>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}
```

---

## 6️⃣ TESTING STRATEGIE

### **A. Unit Tests**

```python
# /app/backend/tests/test_content_engine.py

def test_keyword_extraction():
    engine = ContentEngine()
    text = "De zon is een ster die energie uitstraalt"
    analysis = engine.analyze(text)
    
    assert len(analysis.keywords) > 0
    assert any(kw.word == "zon" for kw in analysis.keywords)
    assert any(kw.word == "energie" for kw in analysis.keywords)

def test_compliment_detection():
    engine = ContentEngine()
    text = "Je bent echt super slim!"
    analysis = engine.analyze(text)
    
    assert len(analysis.compliments) > 0
    assert analysis.compliments[0].type == "skill"
    assert analysis.compliments[0].intensity > 0.7

def test_intent_detection():
    engine = ContentEngine()
    text = "Wat is een auto?"
    analysis = engine.analyze(text)
    
    assert analysis.intent.is_question == True
    assert analysis.intent.primary_intent == "ask"
```

```python
# /app/backend/tests/test_emotion_detector.py

def test_happy_detection():
    detector = EmotionDetector()
    text = "Ik ben zo blij! Dit is geweldig! 😊"
    analysis = detector.detect(text)
    
    assert analysis.primary_emotion == "happy"
    assert analysis.confidence > 0.7
    assert analysis.intensity > 0.6

def test_angry_detection():
    detector = EmotionDetector()
    text = "Dit is heel irritant en vervelend"
    analysis = detector.detect(text)
    
    assert analysis.primary_emotion == "angry"
    assert len(analysis.emotional_signals) > 0

def test_neutral_fallback():
    detector = EmotionDetector()
    text = "De auto rijdt over de weg"
    analysis = detector.detect(text)
    
    assert analysis.primary_emotion == "neutral"
```

---

## 7️⃣ ROADMAP INTEGRATIE

### **Add to roadmap.json:**

```json
{
  "id": "v1_6_001",
  "titel": "Content Engine - Basis",
  "status": "in_progress",
  "priority": "critical",
  "progress": 0,
  "notes": "Analyseer content en structureer naar knowledge layers",
  "sub_items": [
    "Keyword extraction",
    "Context detection",
    "Language style analysis",
    "Compliment detection",
    "Intent detection",
    "Knowledge layer mapping"
  ]
},
{
  "id": "v1_6_002",
  "titel": "Emotion/Intention Detection",
  "status": "in_progress",
  "priority": "critical",
  "progress": 0,
  "notes": "Detecteer emotionele signalen en map naar Spark's emoties",
  "sub_items": [
    "Emotional signal detection",
    "Map to 4 base emotions",
    "Intensity calculation",
    "Spark emotion suggestions",
    "Auto-emotion triggering"
  ]
},
{
  "id": "v1_6_003",
  "titel": "Content → Emotion Integration",
  "status": "planned",
  "priority": "high",
  "progress": 0,
  "notes": "Verbind content engine met emotion detector voor context-aware emotionele analyse"
}
```

---

## 8️⃣ IMPLEMENTATIE VOLGORDE

### **FASE 1: Content Engine Core (Week 1)**
**Effort:** 12-16 uur

1. **Data models** (2h)
   - ContentAnalysis, Keyword, Context, etc.
   
2. **Basic ContentEngine class** (4h)
   - analyze() method
   - extract_keywords()
   - detect_context()
   
3. **Language style analysis** (3h)
   - analyze_language_style()
   - Tone detection
   - Formality scoring
   
4. **Compliment & Intent detection** (3h)
   - detect_compliments()
   - detect_intent()
   
5. **Testing** (2h)
   - Unit tests
   - Integration tests

---

### **FASE 2: Emotion Detector (Week 2)**
**Effort:** 10-14 uur

1. **Data models** (1h)
   - EmotionalAnalysis, EmotionalSignal, etc.
   
2. **EmotionDetector class** (4h)
   - detect() method
   - analyze_emotional_signals()
   - map_to_base_emotions()
   
3. **Intensity & context** (2h)
   - calculate_intensity()
   - get_emotional_context()
   
4. **Spark integration** (3h)
   - should_trigger_emotion_change()
   - suggest_spark_emotion()
   
5. **Testing** (2h)
   - Unit tests
   - Edge cases

---

### **FASE 3: Integration & API (Week 3)**
**Effort:** 8-12 uur

1. **Connect engines** (3h)
   - Content feeds emotion
   - Integrated flow in spark_brain
   
2. **API endpoints** (3h)
   - content_routes.py
   - emotion_detection_routes.py
   
3. **Frontend UI** (4h)
   - ContentAnalyzer component
   - Emotion visualization
   
4. **End-to-end testing** (2h)
   - Full flow tests
   - Performance optimization

---

## 9️⃣ SUCCESS METRICS

**Content Engine:**
- ✅ Can extract 5+ relevant keywords from average text
- ✅ Detects context with >70% accuracy
- ✅ Identifies compliments with >80% accuracy
- ✅ Correctly maps content to knowledge layers 60%+ of time

**Emotion Detector:**
- ✅ Detects primary emotion with >75% accuracy
- ✅ Intensity scoring correlates with human judgment
- ✅ Maps to Spark emotions consistently
- ✅ False positive rate <15%

**Integration:**
- ✅ Processing time <500ms per message
- ✅ Spark emotion changes feel natural
- ✅ No regression in existing functionality

---

## 🎯 SUMMARY

**What We're Building:**
1. **Content Engine** - 6 core capabilities, modular design
2. **Emotion Detector** - 4-emotion system, Spark-aware
3. **Integration Layer** - Seamless connection between both

**Architecture Strengths:**
- ✅ Reuses existing infrastructure
- ✅ Modular and extensible
- ✅ Clear data models
- ✅ Testable components
- ✅ API-first design

**Timeline:**
- Week 1: Content Engine
- Week 2: Emotion Detector
- Week 3: Integration

**Total Effort:** 30-42 hours

---

**Ready for Approval?** 🚀

Let me know if you want any adjustments to the architecture!
