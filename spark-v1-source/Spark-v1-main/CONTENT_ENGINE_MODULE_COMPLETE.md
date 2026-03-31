# 📦 Content Engine - Modulaire Structuur

**Datum:** 10 maart 2026  
**Status:** ✅ Geïmplementeerd en Getest

---

## 🎯 Overzicht

De Content Engine is een modulaire hub die content-analyse coördineert via gespecialiseerde analyzers. Het produceert een unified `ContentAnalysis` output die door de Context Layer gebruikt wordt.

---

## 📁 Directory Structuur

```
/app/backend/services/content_engine/
├── __init__.py                    # ContentEngine hub/orchestrator
├── models.py                      # Dataclasses (ContentAnalysis, etc.)
├── helpers.py                     # Gedeelde utility functies
├── keyword_analyzer.py            # Keyword & topic extractie
├── intent_detector.py             # Intent/command detectie
├── compliment_detector.py         # Compliment & waardering detectie
└── language_style_analyzer.py     # Tone, sentiment, stijl analyse
```

**Bestandsgroottes:**
- `__init__.py` (hub): ~3.5 KB
- `models.py`: ~3.8 KB
- `helpers.py`: ~5.2 KB
- `keyword_analyzer.py`: ~2.4 KB
- `intent_detector.py`: ~3.6 KB
- `compliment_detector.py`: ~4.3 KB
- `language_style_analyzer.py`: ~4.1 KB

**Totaal:** ~27 KB (7 bestanden, gemiddeld ~3.8 KB per bestand) ✅

---

## 🏗️ Architectuur

### **Content Engine Hub**

```python
from services.content_engine import ContentEngine

engine = ContentEngine()
analysis = engine.analyze("Wat is een auto?", user_data=user)
```

**Flow:**
```
┌─────────────────────────────────────────────────────────┐
│                 ContentEngine.analyze()                 │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
┌─────────────┐ ┌─────────┐ ┌──────────────┐
│  Keyword    │ │ Intent  │ │ Compliment   │
│  Analyzer   │ │Detector │ │  Detector    │
└──────┬──────┘ └────┬────┘ └──────┬───────┘
       │             │              │
       │    ┌────────▼────────┐     │
       │    │  Language Style │     │
       │    │    Analyzer     │     │
       │    └────────┬────────┘     │
       │             │              │
       └─────────────┼──────────────┘
                     ▼
           ┌──────────────────┐
           │ ContentAnalysis  │
           │   (Unified)      │
           └──────────────────┘
```

---

## 📊 Data Models

### **ContentAnalysis** (Main Output)

```python
@dataclass
class ContentAnalysis:
    text: str
    
    # Sub-analyses
    language_style: LanguageStyle
    intent: IntentAnalysis
    keywords: KeywordAnalysis
    compliments: ComplimentAnalysis
    
    # Quick access
    primary_topic: Optional[str]
    tone: str  # "friendly", "formal", "casual", "urgent", "playful"
    sentiment: str  # "positief", "negatief", "neutraal"
    
    # Metadata
    analyzed_at: datetime
    processing_time_ms: int
    confidence: float
```

### **Sub-Models**

**LanguageStyle:**
- tone, sentiment, formality_level, emotional_intensity
- uses_emoji, uses_capitals, uses_punctuation_emphasis
- contains_compliments, compliment_targets
- word_count, avg_word_length, question_count

**IntentAnalysis:**
- primary_intent, confidence
- is_command, command_type, command_content
- is_question, question_type
- is_teaching, teaching_signal

**KeywordAnalysis:**
- primary_keywords, topics, entities
- has_stop_words, stop_words_found, importance_score

**ComplimentAnalysis:**
- has_compliment, compliment_type, compliment_intensity
- targets, compliment_phrases

---

## 🔗 Hergebruik Bestaande Services

De Content Engine is een **orchestrator** die bestaande services hergebruikt:

### **NLPService** (hergebruikt)
- `detect_sentiment()` → LanguageStyleAnalyzer
- `detect_command()` → IntentDetector

### **PatternDetectionService** (hergebruikt)
- `analyze_message()` → KeywordAnalyzer
- `analyze_message()` → LanguageStyleAnalyzer (emotional_tone)

### **Nieuwe Modules**
- `ComplimentDetector` → Nieuwe logica voor complimenten
- `Helpers` → Nieuwe utility functies (emoji, capitals, formality)

---

## ✅ Test Resultaten

### **Test 1: Simpele Vraag**
```
Input: "Wat is een auto?"
✓ Intent: question
✓ Question Type: what
✓ Primary Topic: auto
✓ Confidence: 0.81
```

### **Test 2: Compliment**
```
Input: "Bedankt Spark! Je bent geweldig!"
✓ Has Compliment: True
✓ Compliment Type: direct
✓ Intensity: 1.00
✓ Tone: friendly
```

### **Test 3: Command**
```
Input: "Laat de roadmap zien"
✓ Intent: command
✓ Command Type: roadmap
```

### **Test 4: Teaching**
```
Input: "Onthoud dit: auto's hebben vier wielen"
✓ Intent: teaching
✓ Teaching Signal: onthoud
```

### **Test 5: Urgent/Emotional**
```
Input: "HELP!!! Mijn systeem werkt niet!!!"
✓ Tone: urgent
✓ Uses Capitals: True
✓ Punctuation Emphasis: True
✓ Emotional Intensity: 0.60
```

### **Test 6: Casual/Playful**
```
Input: "Hey! Hoe gaat het? 😊 Haha leuk dit"
✓ Tone: playful
✓ Uses Emoji: True
✓ Formality: 0.10 (very casual)
```

### **Test 7: Important Signals**
```
Input: "Luister goed, dit is CRUCIAAL voor mijn toekomst"
✓ Has Stop Words: True
✓ Stop Words: ['cruciaal']
✓ Importance Score: 5
```

**All tests passed!** ✅

---

## 🚀 Usage Example

```python
from services.content_engine import ContentEngine

# Initialize (eenmalig)
engine = ContentEngine()

# Gebruik in spark_brain.py
def process_message(self, message: str, user_data: dict, session_id: str):
    # LAYER 1: Content Analysis
    content_analysis = engine.analyze(
        text=message,
        user_data=user_data
    )
    
    # Access results
    print(f"Intent: {content_analysis.intent.primary_intent}")
    print(f"Tone: {content_analysis.tone}")
    print(f"Topics: {content_analysis.keywords.topics}")
    print(f"Has Compliment: {content_analysis.compliments.has_compliment}")
    
    # LAYER 2: Context Layer (next step)
    # contextual_analysis = context_layer.enrich(
    #     content_analysis=content_analysis,
    #     user_data=user_data,
    #     session_id=session_id
    # )
    
    # ... rest of processing ...
```

---

## 📈 Performance

**Gemiddelde Processing Time:** 0-5ms per bericht

**Breakdown:**
- Keyword Analysis: ~1ms
- Intent Detection: ~1ms
- Compliment Detection: ~1ms
- Language Style: ~2ms

**Total:** ~5ms (zeer acceptabel) ✅

---

## 🎯 Voordelen van Modulaire Opzet

### **1. Kleine Bestanden**
- Elk bestand ~3-5 KB
- Gemakkelijk te lezen en onderhouden
- Overzichtelijke verantwoordelijkheden

### **2. Testbaarheid**
- Elke analyzer afzonderlijk testbaar
- Mock dependencies eenvoudig
- Unit tests per module mogelijk

### **3. Herbruikbaarheid**
- Analyzers kunnen los gebruikt worden
- Hergebruikt bestaande services
- Geen code duplicatie

### **4. Uitbreidbaarheid**
- Nieuwe analyzers toevoegen = nieuw bestand
- Bestaande analyzers uitbreiden zonder anderen te breken
- Clear separation of concerns

### **5. Clean API**
- Single entry point: `ContentEngine.analyze()`
- Unified output: `ContentAnalysis`
- Type-safe met dataclasses

---

## 🔄 Next Steps

Nu de Content Engine klaar is, kunnen we verder met:

### **Phase 1: Context Layer Cache** (volgende stap)
- Implementeer `ContextCache` (in-memory cache)
- Integreer met bestaande `ContextLayer`
- Test performance met cache

### **Phase 2: Context Layer** (na cache)
- Herstructureer `context_layer.py` als modular hub
- Gebruik `ContentAnalysis` als input
- Produceer `ContextualAnalysis` als output

### **Phase 3: Emotion Detector** (later)
- Update om `ContextualAnalysis` te gebruiken
- Context-aware emotion detection

---

## 📝 Notes

**Bestaande Services Behouden:**
- `context_engine.py` blijft bestaan (user profiles, notes)
- `nlp_service.py` blijft bestaan (hergebruikt door Content Engine)
- `pattern_detection_service.py` blijft bestaan (hergebruikt)

**Geen Breaking Changes:**
- Content Engine is nieuw, breekt niets
- Bestaande code blijft werken
- Geleidelijke integratie mogelijk

**Clean Architecture:**
- Content Engine = Content Analysis (WHAT is said)
- Context Engine = Context Enrichment (WHAT it means)
- Emotion Detector = Emotion Detection (HOW it's said)

---

## ✅ Status: READY FOR PHASE 1

De modulaire Content Engine is **volledig geïmplementeerd en getest**.

We kunnen nu verder met **Phase 1: Cache Implementation** zoals beschreven in het Performance Architecture document.

**Next Action:**
- Implementeer `ContextCache` class
- Integreer met Content Engine flow
- Test performance improvements
