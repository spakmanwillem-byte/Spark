# 🔍 NLP/Intent Architectuur vs Spark Roadmap/Visie

**Datum:** 26 maart 2026  
**Status:** Conceptuele & Technische Analyse

---

## 📖 SPARK CORE VISIE (uit Core 4.1 & Roadmap)

### **Kernprincipes:**

**1. Spark's Missie & Waardestructuur:**
- **Autonomie versterkt**, niet afhankelijkheid creëert
- **Transparantie**: Begrijpelijk, lokaal, controleerbaar
- **Structuur boven chaos**
- **Menselijkheid boven efficiëntie**

**2. Functionele Lagen (Bedoelde Architectuur):**

```
┌─────────────────────────────────────────┐
│  SPARK BRAIN (Reasoning & Beslissingen) │
├─────────────────────────────────────────┤
│  KENNIS LAAG (Tijdloze concepten)      │  ← Knowledge Base
├─────────────────────────────────────────┤
│  COMMUNICATIE LAAG (Zinnen/Intent)     │  ← Triggers, conversatie
├─────────────────────────────────────────┤
│  GEDRAG LAAG (Acties/Reacties)         │  ← Personality, emotie
└─────────────────────────────────────────┘
```

**3. Roadmap Intent Prioriteit (v3.0 - Compleet):**

**"INTENT HAS PRIORITY OVER CONTENT"** ✅

Uit roadmap (P0 - CRITICAL):
```
Core Problem Solved:
❌ "ik moet een uitgave registreren" → "Een uitgave is..." (WRONG)
✅ "ik moet een uitgave registreren" → "Genoteerd." (CORRECT)

Architecture:
1. Detect intent (actie, vraag, emotie, status)
2. Determine behavior (based on intent)
3. Use kenniskaart (for context, NOT for response type)
```

**Implementation:**
- ✅ Response Behavior System (`response_behavior.py`)
- ✅ Intent Triggers (`intent_triggers.py`) - 80+ agenda, 40+ boekhouding, 30+ werk woorden
- Priority order: VRAAG → ACTIE → EMOTIE → STATUS

---

## 🔍 HUIDIGE IMPLEMENTATIE

### **Wat er Is:**

**Lagenstructuur:**

```
┌──────────────────────────────────────────────┐
│ SparkBrain (Main Processing)                 │
│  ↓                                           │
│  1. ContentEngine (Intent, tone, topics)     │  ← GOEDE LAAG
│  2. ContextLayer (Conversation phase, style) │  ← GOEDE LAAG
│  3. EmotionDetection (4 basis emoties)       │  ← GEDRAG LAAG ✅
│  4. Knowledge Lookup                          │  ← KENNIS LAAG ✅
│  5. LLM Fallback                             │
│  6. Response Enhancement                      │
└──────────────────────────────────────────────┘
```

**Intent Herkenning:**

1. **IntentDetector** (content_engine):
   - command, teaching, question, greeting, statement
   - Confidence: 0.7-0.9
   
2. **IntentManager**:
   - Mode switching (kort/uitleg/brainstorm)
   - Pattern matching op keywords

3. **NLPService**:
   - 30+ commands hardcoded
   - Greeting/thanks/how-are-you via JSON triggers
   - Identification extractie

**Communicatie Patronen:**

```
conversation_triggers.json:  Greetings, thanks, how-are-you, goodbyes, compliments
emotion_triggers.json:       4 emoties (blij, boos, bang, bedroefd) + intensifiers
```

**Status: VERSPREID** ❌
- Sommige in JSON (conversation_triggers)
- Sommige hardcoded in NLPService
- Sommige in IntentDetector
- Geen centrale laag

---

## ✅ WAT KLOPT MET DE ROADMAP

### **1. Intent Priority Systeem - CORRECT** ✅

**Roadmap zegt:**
> "INTENT HAS PRIORITY OVER CONTENT"
> "1. Detect intent → 2. Determine behavior → 3. Use kenniskaart"

**Implementatie:**
```python
# SparkBrain.process_message():
1. content_analysis = ContentEngine.analyze()      # ✅ Intent detectie
2. contextual_analysis = ContextLayer.enrich()     # ✅ Context
3. emotion_detection = EmotionDetectionService()   # ✅ Emotie (voor knowledge)
4. knowledge_lookup                                 # ✅ Knowledge (context, niet type)
5. response_enhancement                             # ✅ Behavior
```

**Verdict:** **KLOPT** - Intent wordt VOOR knowledge gedetecteerd ✅

---

### **2. Lagenstructuur - DEELS CORRECT** ⚠️

**Roadmap bedoeling:**
- **Kennis laag**: Tijdloze concepten (knowledge_base.json)
- **Communicatie laag**: Zinnen/intents/conversatie patronen
- **Gedrag laag**: Persoonlijkheid/emotie/acties

**Implementatie:**

| Laag | Roadmap | Implementatie | Status |
|------|---------|---------------|--------|
| **Kennis** | Knowledge Base | ✅ `knowledge_base.json` (2.353 entries) | **CORRECT** ✅ |
| **Communicatie** | Centrale intent/communicatie laag | ⚠️ Verspreid (JSON + hardcoded) | **AFWIJKING** ❌ |
| **Gedrag** | Emotie/personality/acties | ✅ EmotionDetection, ResponseEnhancer | **DEELS** ⚠️ |

**Verdict:** Kennis en Gedrag grotendeels correct, Communicatie NIET centraal ❌

---

### **3. Modulaire Trigger Systeem - CORRECT** ✅

**Roadmap v3.3:**
> "Module + JSON Trigger Architecture"
> "Flexibel, modulair trigger systeem - logic in services, behavior in JSON"

**Implementatie:**
- ✅ `conversation_triggers.json` (greetings, thanks, etc.)
- ✅ `emotion_triggers.json` (4 emoties + scores)
- ✅ `calendar_triggers.json` (events)
- ✅ Trigger Manager Service (self-service admin tool)

**Verdict:** **KLOPT** - JSON-driven triggers zoals bedoeld ✅

---

### **4. Emotie Systeem - CORRECT** ✅

**Roadmap v3.2:**
> "Hybride Emotie Trigger Systeem"
> "STATIC + DYNAMIC learning via knowledge card tags"
> "Emotie detectie VÓÓ knowledge lookup"

**Implementatie:**
- ✅ Static: `emotion_triggers.json` (4 emoties, 138 woorden)
- ✅ Dynamic: Leert van knowledge cards met #emotie-* tags
- ✅ Detectie VOOR knowledge lookup in pipeline
- ✅ Empathische responses per emotie

**Verdict:** **KLOPT VOLLEDIG** - Exact zoals roadmap beschrijft ✅

---

### **5. Intent Triggers - CORRECT** ✅

**Roadmap:**
> "80+ agenda/planning woorden"
> "40+ boekhouding woorden"
> "30+ werk woorden"

**Implementatie:**
- ✅ `intent_triggers.py` aanwezig
- ✅ Pattern matching voor acties
- ✅ Priority system (VRAAG → ACTIE → EMOTIE)

**Verdict:** **KLOPT** ✅

---

## ❌ WAT AFWIJKT VAN DE ROADMAP

### **1. COMMUNICATIE LAAG - NIET CENTRAAL** ❌

**Roadmap bedoeling:**
```
┌────────────────────────────────────────┐
│  COMMUNICATIE LAAG                     │  ← Aparte, centrale laag
│  - Greetings, goodbyes, thanks        │
│  - Small talk, check-ins              │
│  - Ja/nee/bevestigingen               │
│  - Context-aware intent               │
└────────────────────────────────────────┘
```

**Huidige implementatie:**
```
NLPService.is_greeting()              ← Verspreid
NLPService.detect_thanks()            ← Verspreid
conversation_triggers.json            ← JSON
IntentDetector                        ← Engine
IntentManager                         ← Mode switching
```

**Probleem:**
- ❌ Geen enkele "CommunicationLayer" service
- ❌ Logica verspreid over 4+ services
- ❌ Moeilijk om nieuwe communicatie patronen toe te voegen
- ❌ Geen centrale plek voor "zinnen vs kennis"

**Impact:**
- Moeilijk onderhoud
- Geen duidelijke scheiding tussen "communicatie" en "kennis"
- Juist die communicatie zinnen ("Hoi", "Bedankt") werden net verwijderd uit knowledge base omdat ze GEEN kennis zijn
- Maar ze hebben nu GEEN eigen thuisplek

**Verdict:** **AFWIJKT** - Communicatie laag ontbreekt als aparte entiteit ❌

---

### **2. CONTEXT-AWARE INTENT - BEPERKT** ⚠️

**Roadmap impliceert:**
- Intent detectie moet context-aware zijn
- "Ja" betekent verschillende dingen in verschillende contexten

**Huidige implementatie:**
- ⚠️ ConversationStateManager bijhoudt `last_question`
- ⚠️ Disambiguation context werkt
- ❌ Maar algemene intent detectie is **stateless**
- ❌ "Ja" wordt altijd hetzelfde behandeld

**Voorbeeld probleem:**
```
Scenario 1:
Spark: "Wil je een account aanmaken?"
User: "Ja"  → MOET: account aanmaken

Scenario 2:
Spark: "Heb je meer informatie over X?"
User: "Ja"  → MOET: meer info geven

Scenario 3:
User: "Ja zeker!"  → Gewone bevestiging (geen actie)
```

**Huidige implementatie:**
- Werkt voor scenario 1 (account creation flow)
- Werkt NIET voor scenario 2/3 (geen generieke context)

**Verdict:** **AFWIJKT** - Intent is niet volledig context-aware ⚠️

---

### **3. STRUCTURED INTENT SCHEMA - INCONSISTENT** ⚠️

**Roadmap principe:**
> "Structuur boven chaos"

**Huidige implementatie:**

| Service | Return Format |
|---------|---------------|
| NLPService.detect_command() | `(command_type, content)` tuple |
| IntentDetector.analyze() | `IntentAnalysis` object |
| IntentManager.detect_mode_switch() | `dict` with keys |

**Probleem:**
- ❌ Geen gestandaardiseerde intent structuur
- ❌ Verschillende services gebruiken verschillende formats
- ❌ Moeilijk om intent te delen tussen services

**Verdict:** **AFWIJKT** - Geen consistente structuur ⚠️

---

### **4. VOORBEELDZINNEN / TRAINING DATA - ONTBREEKT** ❌

**Roadmap v5.0 (Vision):**
> "Pattern Learning - Learn from conversations automatically"

**Huidige implementatie:**
- ❌ Geen corpus van voorbeeldzinnen
- ❌ Alleen hardcoded patterns
- ❌ Geen adaptief leren

**Probleem:**
- Nieuwe intents vereisen code changes
- Geen machine learning op basis van voorbeelden
- Pattern matching is statisch

**Verdict:** **AFWIJKT** - Nog niet geïmplementeerd (maar wel roadmap visie) ❌

---

## 🎯 CONCEPTUELE BEOORDELING

### **"Past dit bij hoe Spark bedoeld is te denken en reageren?"**

**JA EN NEE:**

**✅ WAT WEL PAST:**

1. **Intent Priority** ✅
   - "Intent heeft prioriteit" is CORRECT geïmplementeerd
   - Actie/vraag/emotie/status worden eerst gedetecteerd
   - Knowledge dient als context, niet als response-bepaler
   
2. **Modulaire Triggers** ✅
   - JSON-driven configuratie
   - Self-service admin tools
   - Transparant en aanpasbaar
   - Past bij "begrijpelijk, controleerbaar"

3. **Gedragslagen** ✅
   - Emotie detectie voor empathie
   - Response enhancement voor stijl
   - Personality traits in responses

4. **Kennis Scheiding** ✅
   - Knowledge base bevat ALLEEN tijdloze concepten
   - 4-lagen systeem voor diepte
   - WS5 framework voor structuur

**❌ WAT NIET PAST:**

1. **Communicatie Verspreiding** ❌
   - **Tegen principe**: "Structuur boven chaos"
   - Communicatie logica zit overal EN nergens
   - Geen duidelijke laag zoals bedoeld
   - Willem VERWIJDERDE net communicatie uit knowledge base, maar ze hebben geen eigen thuis

2. **Stateless Intent** ❌
   - **Tegen principe**: "Context is belangrijk"
   - Intent detectie houdt geen rekening met conversatie flow
   - "Ja" wordt niet context-aware behandeld

3. **Inconsistente Structuur** ❌
   - **Tegen principe**: "Structuur boven chaos"
   - Verschillende formaten voor hetzelfde concept (intent)

---

### **"Is het een tijdelijke technische oplossing?"**

**JA - DEELS:**

**Tijdelijke oplossingen:**

1. **Verspreid systeem** 🕐
   - Communicatie intenties zijn VERSPREID
   - Geen centrale laag zoals Core 4.1 voorschrijft
   - **Waarom?** Historisch gegroeid, feature-by-feature gebouwd
   - **Status:** Werkt, maar niet volgens architectuur

2. **Hardcoded patterns** 🕐
   - Veel patterns zijn hardcoded in code
   - **Waarom?** Sneller om te bouwen voor MVP
   - **Status:** Werkt, maar niet schaalbaar

3. **Stateless intent** 🕐
   - Intent detectie houdt geen conversatie context bij
   - **Waarom?** Eenvoudiger om te implementeren
   - **Status:** Werkt voor simpele cases, faalt bij complexe dialogen

**Permanente implementaties:**

1. **JSON Triggers** ✅
   - **NIET tijdelijk** - dit IS de bedoelde architectuur
   - Modulair, transparant, aanpasbaar

2. **Intent Priority** ✅
   - **NIET tijdelijk** - dit IS de roadmap

3. **Emotie Systeem** ✅
   - **NIET tijdelijk** - volledige implementatie volgens roadmap

---

## 🔧 WAT LATER HERBOUWD MOET WORDEN

### **1. COMMUNICATIE LAAG - HERBOUW NODIG** 🔴

**Waarom:**
- Willem verwijderde net 9 communicatie zinnen uit knowledge base
- Deze zinnen zijn GEEN kennis, maar communicatie
- Ze hebben nu GEEN thuisplek
- De roadmap impliceert een aparte laag

**Wat herbouwen:**

```python
# NIEUW: CommunicationIntentService
class CommunicationIntentService:
    """
    Centrale laag voor communicatie intenties
    
    Scheiding:
    - KENNIS: Tijdloze concepten (knowledge_base.json)
    - COMMUNICATIE: Zinnen, intents, small talk (deze laag)
    - GEDRAG: Emotie, personality, acties (bestaand)
    """
    
    def detect_communication_intent(text, context=None):
        # Pattern matching + context
        # Returns: CommunicationIntent object
        pass
    
    def get_response(intent, context=None):
        # Select appropriate response
        # Context-aware (niet herhalen)
        pass
```

**Structuur:**
```
/app/backend/data/intents/
  ├── greetings.json
  ├── thanks.json
  ├── confirmations.json
  ├── questions.json
  └── small_talk.json
```

**Wanneer:** **P1** - Willem zei: "We bouwen eerst een zuivere knowledge base. Communicatie/intenties worden later in een aparte structuur ondergebracht."

---

### **2. CONTEXT-AWARE INTENT - UITBREIDING NODIG** 🟡

**Waarom:**
- Intent detectie is nu stateless
- "Ja" wordt niet context-aware behandeld
- Roadmap v4.0: "Conversational Depth" vereist context

**Wat herbouwen:**

```python
class ContextAwareIntentDetector:
    """
    Uitbreiding van IntentDetector met context
    
    Features:
    - Track conversation flow
    - Disambiguate based on context
    - Multi-turn intent resolution
    """
    
    def detect_intent(text, conversation_context):
        # Gebruik context om intent te bepalen
        # "Ja" betekent verschillende dingen in verschillende contexten
        pass
```

**Wanneer:** **P2** - Na communicatie laag, voor v4.0 (Conversational Depth)

---

### **3. STRUCTURED INTENT SCHEMA - STANDARDISATIE NODIG** 🟡

**Waarom:**
- Verschillende services gebruiken verschillende formaten
- Tegen "Structuur boven chaos" principe

**Wat herbouwen:**

```python
@dataclass
class Intent:
    """
    Gestandaardiseerde intent structuur
    Gebruikt door ALLE services
    """
    type: str  # command, question, greeting, etc.
    confidence: float  # 0.0 - 1.0
    category: str  # communication, knowledge, action
    content: Optional[str]
    context: Optional[Dict]
    metadata: Optional[Dict]
```

**Wanneer:** **P2** - Bij communicatie laag refactor

---

### **4. INTENT ANALYTICS - NIEUWE FEATURE** 🟢

**Waarom:**
- Roadmap v5.0: "Pattern Learning"
- Geen inzicht in welke intents vaak falen

**Wat bouwen:**

```python
class IntentAnalyticsService:
    """
    Track intent performance
    - Welke intents worden gedetecteerd
    - Welke falen (low confidence)
    - Welke patronen niet herkend
    """
    
    def log_intent_detection(intent, success, user_feedback):
        pass
    
    def get_stats():
        # Dashboard data
        pass
```

**Wanneer:** **P3** - Na basis communicatie laag werkt

---

## 📊 SAMENVATTING VERGELIJKING

### **SCORECARD:**

| Aspect | Roadmap | Implementatie | Score |
|--------|---------|---------------|-------|
| **Intent Priority** | ✅ Critical | ✅ Geïmplementeerd | **100%** ✅ |
| **Kennis Laag** | ✅ Tijdloze concepten | ✅ Knowledge Base | **100%** ✅ |
| **Gedrag Laag** | ✅ Emotie/personality | ✅ EmotionDetection | **90%** ✅ |
| **Communicatie Laag** | ✅ Aparte centrale laag | ❌ Verspreid | **30%** ❌ |
| **Context-Aware Intent** | ✅ Vereist | ⚠️ Beperkt | **50%** ⚠️ |
| **Modulaire Triggers** | ✅ JSON-driven | ✅ JSON triggers | **95%** ✅ |
| **Structured Schema** | ✅ Structuur > chaos | ⚠️ Inconsistent | **60%** ⚠️ |
| **Pattern Learning** | 🔮 Visie (v5.0) | ❌ Niet aanwezig | **0%** 🔮 |

**Overall Score: 66% (Goed fundament, communicatie laag ontbreekt)**

---

### **KERN CONCLUSIE:**

#### **WAT KLOPT:**
- ✅ **Intent heeft prioriteit** - CORRECT geïmplementeerd
- ✅ **Kennis laag** - Zuiver, gestructureerd, zoals bedoeld
- ✅ **Gedrag laag** - Emotie systeem volgt roadmap exact
- ✅ **Modulaire triggers** - JSON-driven, transparant

#### **WAT AFWIJKT:**
- ❌ **Communicatie laag ONTBREEKT** - Grootste afwijking
- ⚠️ **Intent is niet context-aware** - Beperking
- ⚠️ **Inconsistente structuur** - Tegen "structuur > chaos"

#### **WAT HERBOUWD MOET:**
- 🔴 **P1: Communicatie Laag** - Willem verwijderde net communicatie uit KB, ze hebben geen thuis
- 🟡 **P2: Context-Aware Intent** - Voor v4.0 Conversational Depth
- 🟡 **P2: Structured Schema** - Standaardisatie
- 🟢 **P3: Intent Analytics** - Voor v5.0 Pattern Learning

---

## 🎯 AANBEVELING VOOR WILLEM

### **Is huidige systeem een "tijdelijke oplossing"?**

**ANTWOORD: GEMENGD**

**✅ PERMANENT (behouden):**
- Intent priority systeem
- JSON trigger architectuur
- Emotie systeem
- Knowledge base structuur

**🕐 TIJDELIJK (herbouwen):**
- Verspreide communicatie logica → Centrale communicatie laag
- Stateless intent → Context-aware intent
- Inconsistente formats → Gestandaardiseerd schema

### **Moet je NU al de communicatie laag bouwen?**

**ANTWOORD: NEE, MAAR PLAN WEL**

**Waarom niet NU:**
- Knowledge base moet eerst VOLLEDIG schoon en stabiel
- Intent priority werkt al correct
- Huidige systeem functioneert (geen blocking issues)

**Waarom WEL plannen:**
- Willem verwijderde net 9 communicatie zinnen uit KB
- Deze zinnen zijn conceptueel "dakloos"
- Roadmap v4.0 vereist diepere conversatie (context-aware)
- Spark Core 4.1 vereist duidelijke lagenstructuur

**Timing:**
1. **NU**: Knowledge base schoon en stabiel maken (bijna klaar)
2. **DAARNA**: Testing van snap systeem en ja/nee flow
3. **DAN**: Communicatie laag bouwen (met voorbeelden uit verwijderde entries)
4. **LATER**: Context-aware intent voor v4.0

---

**DE VRAAG DIE JE STELDE:**
> "Past dit bij hoe Spark bedoeld is te denken en reageren? Of is het een tijdelijke technische oplossing?"

**ANTWOORD:**
**Het intent priority systeem past PERFECT bij de visie (✅).**  
**De communicatie laag implementatie past NIET bij de visie (❌) en moet herbouwd worden naar centrale laag zoals Core 4.1 voorschrijft.**

**Dit is GEEN acute crisis, maar WEL een architecturale schuld die later afbetaald moet worden.**
