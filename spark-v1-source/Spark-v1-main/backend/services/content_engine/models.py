"""
Data models voor Content Engine output
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime


@dataclass
class LanguageStyle:
    """Taalstijl analyse"""
    tone: str  # "friendly", "formal", "casual", "urgent", "playful"
    sentiment: str  # "positief", "negatief", "neutraal"
    formality_level: float  # 0.0 (casual) - 1.0 (formal)
    emotional_intensity: float  # 0.0 (flat) - 1.0 (intense)
    
    # Specifieke markers
    uses_emoji: bool = False
    uses_capitals: bool = False
    uses_punctuation_emphasis: bool = False  # !!!, ???
    
    # Complimenten
    contains_compliments: bool = False
    compliment_targets: List[str] = field(default_factory=list)  # ["spark", "system"]
    
    # Stijlkenmerken
    word_count: int = 0
    avg_word_length: float = 0.0
    question_count: int = 0


@dataclass
class IntentAnalysis:
    """Intent/doel van het bericht"""
    primary_intent: str  # "question", "statement", "command", "greeting", "teaching"
    confidence: float  # 0.0 - 1.0
    
    # Command detection
    is_command: bool = False
    command_type: Optional[str] = None  # "roadmap", "show_users", "bio_query"
    command_content: Optional[str] = None
    
    # Question analysis
    is_question: bool = False
    question_type: Optional[str] = None  # "what", "how", "why", "who", "when", "where"
    
    # Teaching detection
    is_teaching: bool = False
    teaching_signal: Optional[str] = None  # "leer jezelf", "onthoud", etc.


@dataclass
class KeywordAnalysis:
    """Keyword en topic analyse"""
    primary_keywords: List[str] = field(default_factory=list)  # Top 5 keywords
    topics: List[str] = field(default_factory=list)  # Detected topics
    entities: List[str] = field(default_factory=list)  # Named entities (mensen, plaatsen)
    
    # Stop woorden (belangrijke signaal woorden)
    has_stop_words: bool = False
    stop_words_found: List[str] = field(default_factory=list)
    importance_score: int = 0  # 0-5


@dataclass
class ComplimentAnalysis:
    """Compliment detectie"""
    has_compliment: bool = False
    compliment_type: Optional[str] = None  # "direct", "indirect", "gratitude"
    compliment_intensity: float = 0.0  # 0.0 - 1.0
    targets: List[str] = field(default_factory=list)  # Wie/wat wordt geprezen
    compliment_phrases: List[str] = field(default_factory=list)  # Gevonden zinnen


@dataclass
class ContentAnalysis:
    """
    Complete content analyse output van Content Engine.
    Dit is de unified output die naar Context Layer gaat.
    """
    # Original input
    text: str
    
    # Sub-analyses
    language_style: LanguageStyle
    intent: IntentAnalysis
    keywords: KeywordAnalysis
    compliments: ComplimentAnalysis
    
    # Quick access properties (duplicated voor convenience)
    primary_topic: Optional[str] = None
    tone: str = "neutral"
    sentiment: str = "neutraal"
    
    # Metadata
    analyzed_at: datetime = field(default_factory=datetime.now)
    processing_time_ms: int = 0
    confidence: float = 0.0  # Overall confidence
