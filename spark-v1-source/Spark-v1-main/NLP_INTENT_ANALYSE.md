# 🔍 NLP & Intent Systeem Analyse

**Datum:** 26 maart 2026  
**Status:** Bestaand systeem geanalyseerd

---

## 📊 WAT ER AL BESTAAT

### 1. **Input Parsing & Preprocessing**

#### A. **NLPService** (`/app/backend/services/nlp_service.py`)
**Functie:** Primaire NLP service voor tekst analyse

**Capabilities:**
- ✅ **Identificatie extractie**: Namen, sleutelwoorden, masterkeys detecteren
- ✅ **Sentiment detectie**: Positief/negatief/neutraal
- ✅ **Command detectie**: 30+ verschillende commands
- ✅ **Typo correctie**: Levenshtein distance voor spelling
- ✅ **Greeting detectie**: Via conversation_triggers.json
- ✅ **Thanks detectie**: Via conversation_triggers.json
- ✅ **How-are-you detectie**: Via conversation_triggers.json
- ✅ **Question detectie**: Vraagwoorden + "?" patroon

**Commands gedetecteerd:**
```python
- roadmap, show_users, bio_query, help, logout
- system_status, triggers_menu, achievements
- dagboek_entry, agenda_event
- yes_response, no_response
- learn, forget, show, note, emotion
```

**Blacklist systeem:**
- Voorkomt false positives (bijv. "Ik ben moe" is geen identificatie)
- Filtert common words: blij, boos, verdrietig, moe, etc.

#### B. **Dutch Stopwords** (`/app/backend/config/dutch_stopwords.py`)
**Functie:** Concept extractie en filtering

**Features:**
- ✅ Lidwoorden filter (de, het, een)
- ✅ Filler words filter (eigenlijk, precies, nou)
- ✅ Meaning detection: Actie, emotie, intentie, mening
- ✅ Concept extraction: Haalt betekenisvolle begrippen uit tekst
- ✅ Normalization: Capitalizes, removes filler words

**Gebruikt voor:**
- Knowledge snap creation
- Filtering van zinloze woorden
- Extractie van betekenisvolle concepten

---

### 2. **Intent Herkenning & Classificatie**

#### A. **IntentDetector** (`/app/backend/services/content_engine/intent_detector.py`)
**Functie:** Detecteert primaire intentie van bericht

**Intent types:**
- `command` - Expliciet commando
- `teaching` - User wil iets leren
- `question` - Vraag
- `greeting` - Begroeting
- `statement` - Gewone uitspraak

**Teaching signals:**
```python
"leer jezelf", "onthoud", "onthoud dit", "dit is belangrijk",
"weet dat", "je moet weten", "ik vertel je"
```

**Confidence scores:** 0.7 - 0.9 (afhankelijk van type)

#### B. **Intent Manager** (`/app/backend/services/intent_manager.py`)
**Functie:** Mode switching en response formatting

**Modes:**
- `kort` - Korte antwoorden (eerste 2 zinnen of 150 chars)
- `uitleg` - Uitgebreide antwoorden met context
- `brainstorm` - Gestructureerde ideeën
- `normal` - Standaard (geen aanpassingen)

**Pattern matching:**
```python
"kort": ["kort", "beknopt", "kort graag", "snel", "tldr"]
"uitleg": ["leg uit", "uitleg", "vertel meer", "uitgebreid"]
"brainstorm": ["brainstorm", "ideeën", "brainstorm mee", "denk mee"]
"help": ["help", "hulp", "commands", "wat kan je"]
```

---

### 3. **Communicatie Patronen & Triggers**

#### A. **Conversation Triggers** (`/app/backend/data/triggers/conversation_triggers.json`)
**Bevat:**

**Greetings:**
```json
"hoi", "hallo", "hey", "hi", "goedemorgen", "goedemiddag", "goedenavond"
```

**Thanks:**
```json
"bedankt", "dankjewel", "dank je", "thanks", "hartelijk dank"
```

**How are you:**
```json
"hoe gaat het", "hoe is het", "alles goed", "gaat het goed"
```

**Goodbyes:**
```json
"doei", "dag", "tot ziens", "bye", "tot later"
```

**Compliments:**
```json
"goed gedaan", "top", "geweldig", "super", "slim", "knap"
```

#### B. **Emotion Triggers** (`/app/backend/data/triggers/emotion_triggers.json`)
**4 basis emoties met intensiteit scores:**

**Blij (😊):**
- blij: 5, gelukkig: 7, vrolijk: 6, enthousiast: 7
- geweldig: 8, fantastisch: 9, perfect: 9

**Boos (😠):**
- boos: 5, woedend: 10, kwaad: 6, gefrustreerd: 4

**Bang (😰):**
- bang: 5, angstig: 6, nerveus: 3, doodsbang: 10

**Bedroefd (😢):**
- verdrietig: 7, somber: 6, depressief: 10, huilen: 7

**Intensifiers:**
```json
"extreem": 2.0, "enorm": 2.0, "super": 1.8, "heel": 1.5
"een beetje": 0.5, "licht": 0.7
```

**Empathische responses per emotie aanwezig**

---

### 4. **Beslissingslogica Na User Input**

#### **SparkBrain Processing Flow** (`/app/backend/services/spark_brain.py`)

**Volgorde:**
1. **Content Analysis** (ContentEngine)
   - Intent, tone, topics, compliments analyseren

2. **Context Analysis** (ContextLayer)
   - Conversation phase, response style, topic continuation

3. **Event Extraction** (EventExtractionService)
   - Detecteer afspraken/events uit conversatie

4. **Emotion Detection** (EmotionDetectionService)
   - Emotie + intensiteit + contextual linking

5. **User Context** (ContextEngine)
   - Profile, notities, patronen ophalen

6. **Command Handling**
   - Check voor specific commands (logout, help, etc.)

7. **Knowledge Lookup**
   - Zoek in knowledge base
   - Disambiguation bij meerdere matches

8. **LLM Fallback**
   - Als geen knowledge match: gebruik GPT-4o

9. **Response Enhancement**
   - Format op basis van mode (kort/uitleg/brainstorm)
   - Add empathie bij emotie
   - Apply word limit

**Route Flow** (`/app/backend/routes/spark_routes.py`):
```
POST /chat
  → Session validatie
  → Mode switch check (IntentManager)
  → Person detection check
  → SparkBrain.process_message()
  → Response formatting
  → Return ChatResponse
```

---

## 🎯 WAT HET PRECIES DOET

### Input Processing:
1. **Tekst normalisatie**: Lowercase, trim, stopwords filter
2. **Pattern matching**: Regex voor identificatie, commands, teaching
3. **Keyword detection**: Triggers voor greeting, thanks, emotions
4. **Intent classification**: Command > Teaching > Question > Greeting > Statement
5. **Context enrichment**: User history, patterns, emotion state

### Intent Herkenning:
- **Expliciete commands**: Via keyword matching (30+ commands)
- **Impliciete intents**: Via NLP analyse (teaching signals, questions)
- **Mode switching**: Via intent patterns (kort, uitleg, brainstorm)
- **Emotion detection**: Via weighted trigger words + intensifiers

### Beslissingen:
- **Route selection**: Command → Knowledge → LLM fallback
- **Response style**: Based on mode (kort/uitleg/brainstorm)
- **Empathie**: Based on detected emotion
- **Word limit**: Based on emotion state
- **Disambiguation**: Multiple knowledge matches → vraag keuze

---

## ❌ WAT ER ONTBREEKT

### 1. **Dedicated Intent/Communicatie Layer**
**Probleem:**
- Communicatie zinnen ("Hoi", "Bedankt") zitten NIET in aparte structuur
- Ze worden verspreid afgehandeld:
  - NLPService.is_greeting()
  - NLPService.detect_thanks()
  - conversation_triggers.json
- Geen centrale "communication intent" manager

**Impact:**
- Moeilijk om nieuwe communicatie patronen toe te voegen
- Geen consistente handling
- Verwarring tussen "kennis" en "communicatie"

### 2. **Voorbeeldzinnen / Training Data**
**Probleem:**
- Geen corpus van voorbeeldzinnen voor intents
- Pattern matching is hardcoded
- Geen machine learning op basis van voorbeelden

**Impact:**
- Nieuwe intents vereisen code changes
- Geen adaptief leren
- Beperkte variatie in herkenning

### 3. **Context-Aware Intent Detection**
**Probleem:**
- Intent detectie is stateless
- Geen begrip van conversatie flow
- "Ja" kan betekenen:
  - Account aanmaken
  - Knowledge bevestigen
  - Algemene bevestiging

**Impact:**
- Disambiguation vereist extra logica
- Context wordt niet gebruikt voor intent

### 4. **Confidence Scoring**
**Probleem:**
- Confidence scores zijn hardcoded (0.7-0.9)
- Geen dynamische scoring op basis van:
  - Pattern strength
  - Context alignment
  - User history

**Impact:**
- Geen prioritering bij conflicterende intents
- Moeilijk om accuracy te meten

### 5. **Structured Intent Schema**
**Probleem:**
- Geen gestandaardiseerde intent structuur
- Verschillende services gebruiken verschillende formaten:
  - NLPService: (command_type, content)
  - IntentDetector: IntentAnalysis object
  - IntentManager: mode strings

**Impact:**
- Inconsistentie tussen services
- Moeilijk te onderhouden

### 6. **Intent Logging & Analytics**
**Probleem:**
- Geen tracking van:
  - Welke intents vaak mislukken
  - Welke patronen niet worden herkend
  - False positives/negatives

**Impact:**
- Geen inzicht in systeem performance
- Moeilijk om te verbeteren

---

## 💡 WAT ER NODIG IS

### **Aparte Communicatie/Intent Laag**

**Doel:**
Scheiding tussen:
- **Kennis** (tijdloze concepten in knowledge_base)
- **Communicatie** (zinnen, intents, conversatie patronen)

**Structuur:**
```
/app/backend/data/intents/
  ├── greetings.json          # Begroetingen + responses
  ├── thanks.json             # Bedankjes + responses
  ├── confirmations.json      # Ja/nee + context
  ├── questions.json          # Vraagpatronen
  └── small_talk.json         # Alles goed, hoe is ie, etc.
```

**Schema per intent:**
```json
{
  "intent": "greeting",
  "patterns": [
    "hoi", "hallo", "hey", "goedemorgen"
  ],
  "examples": [
    "Hoi Spark!",
    "Goedemorgen, hoe gaat het?",
    "Hey! Ben je er?"
  ],
  "responses": [
    "Hoi! Hoe kan ik je helpen?",
    "Hey! Leuk om van je te horen."
  ],
  "context_required": false,
  "priority": "high"
}
```

**Service:**
```python
class CommunicationIntentService:
    def detect_intent(text, context=None):
        # Pattern matching + context
        # Returns: Intent object met confidence
        pass
    
    def get_response(intent, context=None):
        # Select appropriate response
        # Context-aware (niet herhalen)
        pass
```

---

## 🔄 AANBEVOLEN AANPAK

### **Fase 1: Inventarisatie (NU)**
- ✅ Analyse compleet
- ⏳ Bepaal scope van communicatie/intent laag

### **Fase 2: Schema Design**
- Ontwerp intent schema structuur
- Definieer welke intents in nieuwe laag
- Plan migratie van bestaande triggers

### **Fase 3: Implementation**
- Bouw CommunicationIntentService
- Migreer conversation_triggers naar nieuwe structuur
- Integreer in SparkBrain flow

### **Fase 4: Testing & Refinement**
- Test met bestaande patronen
- Voeg nieuwe voorbeeldzinnen toe
- Meet accuracy en verbeter

---

## 📝 CONCLUSIE

**Sterke punten huidige systeem:**
- ✅ Uitgebreide command detectie (30+)
- ✅ Emotion tracking met intensifiers
- ✅ Multi-layer analysis (content → context → emotion)
- ✅ Mode switching (kort/uitleg/brainstorm)
- ✅ Pattern matching voor identificatie
- ✅ Blacklist systeem voor false positives

**Zwakke punten:**
- ❌ Communicatie zinnen verspreid over systeem
- ❌ Geen dedicated intent management
- ❌ Hardcoded patterns zonder voorbeelden
- ❌ Geen context-aware intent detection
- ❌ Inconsistente structuur tussen services

**Aanbeveling:**
Een **aparte communicatie/intent laag** is zinvol als ondersteuning voor NLP, maar alleen als:
1. Je meer flexibiliteit wilt in communicatie patronen
2. Je voorbeeldzinnen wilt toevoegen zonder code changes
3. Je context-aware intent detection wilt

**Voor nu:**
Het bestaande systeem werkt goed voor de huidige use cases. Een dedicated laag wordt pas echt waardevol bij:
- Meer complexe conversatie flows
- Behoefte aan dynamische pattern matching
- Machine learning integratie
- Multi-language support

---

**Volgende stap:** Willem bepaalt of en wanneer de communicatie/intent laag wordt gebouwd.
