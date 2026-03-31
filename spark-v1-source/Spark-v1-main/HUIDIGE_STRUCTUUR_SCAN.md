# 📊 HUIDIGE SPARK STRUCTUUR - COMPLETE SCAN

*Datum: 13 maart 2026*
*Agent: E1 Fork Agent*
*Voor: Willem Spakman*

---

## 🎯 HUIDIGE SIDEBAR NAVIGATIE (App.js)

### Voor ALLE gebruikers (ingelogd):
```
💬 Chat               → Hoofdchat interface
📖 Dagboek            → Persoonlijke dagboek entries
📅 Agenda             → Persoonlijke afspraken
📁 Bestanden          → File management
🗺️ Roadmap            → Development roadmap (zichtbaar voor iedereen)
🏆 Achievements       → Persoonlijke achievements & XP
```

### ALLEEN voor Gradatie 1 (Admin - Willem):
```
🧠 Knowledge Base     → System-wide knowledge management
📝 Notities          → System-wide notities
⚡ Status            → System health & statistics
👑 Admin Panel       → User management, profielen, personality items
```

---

## 📁 BACKEND STRUCTUUR

### Routes (API Endpoints):
```
/api/chat            → spark_routes.py (main chat endpoint)
/api/admin/*         → admin_routes.py (user management, achievements, cache, etc.)
/api/personal/*      → personal_routes.py (dagboek, agenda, uploads)
/api/knowledge/*     → knowledge_routes.py (knowledge CRUD)
/api/notes/*         → notes_routes.py (notities CRUD)
/api/graph/*         → graph_routes.py (knowledge graph)
/api/emotions/*      → emotion_routes.py (emotion management)
/api/profiles/*      → profile_routes.py (user profile management)
/api/roadmap/*       → roadmap_routes.py (roadmap data)
```

### Services (Business Logic):
```
CORE:
├─ spark_brain.py              → Main orchestrator (95KB!)
├─ nlp_service.py              → Command detection, NLP
├─ auth_service.py             → Login, registration, gradatie

KNOWLEDGE & LEARNING:
├─ knowledge_service.py        → Knowledge CRUD
├─ knowledge_service_v2.py     → Ranked knowledge
├─ layered_answer_service.py   → 4-layer answers
├─ knowledge_fallback_service.py
├─ graph_service.py            → Knowledge graph (15 nodes, 27 edges)
├─ graph_traversal_service.py

CONTEXT & CONVERSATION:
├─ conversation_service.py     → Conversation logging
├─ conversation_state_manager.py → Multi-turn state
├─ conversation_cache_service.py → Fast context retrieval
├─ conversation_context_manager.py
├─ context_engine.py
├─ context_layer.py            → Contextual analysis
├─ context_cache.py

CONTENT ANALYSIS:
├─ content_engine/             → Modular content analysis
│   ├─ intent_detector.py
│   ├─ keyword_analyzer.py
│   ├─ language_style_analyzer.py
│   ├─ compliment_detector.py
│   └─ models.py
├─ response_enhancer.py        → Response enhancement

EMOTION & PERSONALITY:
├─ emotion_service.py
├─ emotion_detection_service.py → Dynamic learning from KB
├─ personality_service.py

USER FEATURES:
├─ achievement_service.py      → Word-count achievements
├─ agenda_service.py           → Calendar/events
├─ dagboek_service.py         → Diary
├─ profile_service.py         → User profiles
├─ user_profile_service.py

UTILITIES:
├─ trigger_manager_service.py  → /triggers command (admin)
├─ notes_service.py
├─ roadmap_service.py
├─ system_health.py
├─ summarization_service.py
├─ pattern_detection_service.py
├─ personal_sharing_detector.py
├─ event_extraction_service.py
├─ relation_detection_service.py
└─ action_logger.py
```

---

## 🗄️ DATA STRUCTUUR

### System Data:
```
/backend/data/system/
├─ users.json              → Alle gebruikers (naam, gradatie, sleutelwoord)
├─ achievements.json       → Achievement definitions
├─ keywords.json          → NLP keywords
├─ gradaties.json         → Gradatie levels
├─ roadmap.json           → Development roadmap
├─ masterkey.json         → Admin masterkey
└─ xp_triggers.json       → XP beloningen
```

### User-specific Data:
```
/backend/data/users/{user-id}/
├─ achievements.json      → Unlocked achievements
├─ agenda.json           → Persoonlijke afspraken
└─ dagboek.json          → Dagboek entries
```

### Knowledge & Learning:
```
/backend/data/learned_knowledge/
└─ knowledge_base.json    → Alle knowledge cards (4-layer + 5W + snap)

/backend/data/graph/
├─ nodes.json            → Knowledge graph nodes (15 nodes)
├─ edges.json            → Relations (27 edges)
└─ metadata.json

/backend/data/notes/
└─ notes.json            → System notities
```

### Triggers & Personality:
```
/backend/data/triggers/
├─ emotion_triggers.json      → Basis emoties (blij, boos, bang, bedroefd)
├─ conversation_triggers.json → Greetings, thanks, how_are_you
├─ calendar_triggers.json
└─ system_fallback.json

/backend/data/personality/
├─ spark_bijbel.json         → Normen & waarden
└─ willem_personality.json

/backend/data/base_knowledge/
├─ spark_identity.json
├─ spark_your_life.json
├─ roadkill_community.json
└─ willem_profile.json
```

### Analytics & Logs:
```
/backend/data/conversations/   → Per-user conversation logs
/backend/data/analytics/       → Per-user analytics
/backend/data/feedback/        → Feedback log
/backend/data/system/action_log.json
```

---

## 🎨 FRONTEND COMPONENTEN

### Tabs (Components):
```
Chat:          Main chat interface (in App.js)
DagboekTab:    Dagboek entries viewer/creator
AgendaTab:     Agenda/calendar viewer
BestandenTab:  File upload/management
RoadmapTab:    Roadmap viewer
AchievementsTab: Achievement progress viewer

ADMIN ONLY:
KnowledgeBaseTab: System knowledge management
NotitiesTab:      System notities management  
StatusTab:        System health dashboard
AdminTab:         User management + Profielen beheer
ProfielenTab:     (Embedded in AdminTab) - Profile editor
```

### AdminTab Subtabs:
```
Admin Panel bevat:
├─ Gebruikers      → User list + gradatie management
├─ Profielen       → Profile editor (need, believe, WS5, interesses)
├─ Normen          → Personality normen
├─ Waarden         → Personality waarden
├─ Knowledge       → Knowledge cards (system-wide)
├─ Spark Bijbel    → Bijbel entries
└─ Cache/Summary   → Admin tools
```

---

## 🔑 USER SCHEMA (users.json)

```json
{
  "id": "user-001",
  "naam": "Willem Spakman",
  "volledige_naam": "Willem Spakman",
  "sleutelwoord": "Appelsap",
  "masterkey": "SAMEN",
  "gradatie": 1,
  "rol": "Beheerder / Maker",
  "registered_date": "2026-01-15T00:00:00Z",
  "last_active": "2026-03-13T08:20:22",
  "gesprekken_count": 337,
  "trust_score": 100,
  
  "persoonlijke_info": {
    "gamertag": "Roadkill",
    "dochter": "Lotus",
    "hobby": "Programmeren, AI ontwikkeling",
    ...
  },
  
  "profile": {
    "need": "Impact maken en anderen helpen",
    "believe": "Iedereen verdient een tweede kans",
    "interesses": ["Coaching", "Gaming", "AI", ...],
    "context": "Willem is bezig met Spark...",
    "ws5": {
      "who": "Willem Spakman - Founder & Roadkill",
      "what": "Bouwt Spark AI...",
      "when": "2026...",
      "where": "Nederland...",
      "why": "Om mensen te helpen...",
      "how": "Door coaching..."
    }
  },
  
  "achievements": {
    "unlocked": [...],
    "progress": { "word_count": 1234 }
  },
  
  "xp": 5000
}
```

---

## 🧠 KNOWLEDGE CARD SCHEMA

```json
{
  "id": "kb_xxx",
  "begrip": "Appel",
  "status": "active",
  "created_by": "user-001",
  "created_at": "2026-03-10T...",
  
  "lagen": {
    "laag1": "Korte definitie",
    "laag2": "Meer detail",
    "laag3": "Diepere context",
    "laag4": "Filosofische betekenis"
  },
  
  "ws5": {
    "wie": "Voor wie is dit relevant",
    "wat": "Wat is het precies",
    "waar": "Waar komt het vandaan",
    "wanneer": "Wanneer is het relevant",
    "waarom": "Waarom belangrijk"
  },
  
  "tags": ["emotie-blij", "voedsel", ...],
  "usage_count": 15,
  "last_used": "2026-03-12T..."
}
```

---

## 🔄 CONVERSATIE FLOW

### Login Flow:
```
1. User: "Ik ben Willem Spakman sleutelwoord Appelsap"
2. nlp_service.extract_identification() → parses naam + sleutelwoord
3. auth_service.authenticate_user() → finds user
4. Returns user_data → frontend stores in localStorage
5. Welkomstboodschap + "Hoe is het met je?"
6. conversation_state_manager.set_last_question(session_id, "how_are_you")
```

### Command Flow:
```
1. User: "/achievements"
2. nlp_service.detect_command() → ("achievements", "")
3. spark_brain._handle_command() → achievement_service.get_user_achievements()
4. Returns formatted achievement list
```

### Knowledge Question Flow:
```
1. User: "Wat is een appel?"
2. nlp_service.is_question() → True
3. spark_brain._handle_question()
4. knowledge_service_v2.search_knowledge("appel")
5. layered_answer_service.get_layered_answer()
6. graph_traversal_service.build_graph_context()
7. Returns: Laag 1 answer + Graph Context + Related nodes
```

### Emotion Detection Flow:
```
1. User: "Ik ben zo blij!"
2. emotion_detection_service.detect_emotion()
   - Checks emotion_triggers.json (base triggers)
   - Scans knowledge_base.json for "emotie-*" tags (learned)
3. If strong emotion → empathic_response
4. For admin → shows debug info: "[EMOTIE] Blij(score: 3, intensity: 2)"
```

---

## ⚙️ HUIDIGE FEATURES

### ✅ Werkende Features:
- **Chat:** Main conversatie interface
- **Login/Logout:** Met naam + sleutelwoord (of masterkey voor admin)
- **Knowledge Base:** 4-layer + 5W + snap structure
- **Knowledge Graph:** 15 nodes, 27 edges
- **Emotion Detection:** Dynamisch lerend van KB tags
- **Achievement System:** Word-count based XP & achievements
- **Self-Service Trigger Manager:** `/triggers` command (admin only)
- **Multi-turn Conversations:** State management voor follow-ups
- **Dagboek:** Personal diary entries
- **Agenda:** Calendar events
- **Bestanden:** File uploads
- **Roadmap:** Development tracking
- **Admin Panel:** 
  - User management
  - Profile editor (WS5, need, believe, interesses)
  - Normen/Waarden management
  - Knowledge CRUD
- **Gradatie System:** Auto-growth based on activity
- **Context Enhancement:** Response enhancement met tone/style

### 🔧 In Development / Incomplete:
- **Person Cards:** Concept exists, not implemented
- **Proactieve Assistentie:** Planned, not built
- **Achievement Celebration:** Logic exists, not tested
- **Natural Language Commands:** Partially working
- **Login Dashboard:** Not implemented

---

## 🐛 BEKENDE BUGS

### P0: Sessiecontext verlies na inactiviteit
**Symptoom:** Na inactiviteit herkent Spark gebruiker niet meer (behandelt als gast)
**Impact:** Breekt gebruikerservaring volledig
**Files:** auth_service.py, App.js (localStorage), spark_brain.py

### P1: Foutieve Login Trigger
**Symptoom:** "Ik ben blij" triggert login-flow
**Impact:** Frustrerende conversatie-interrupt
**Files:** nlp_service.py (extract_identification), spark_brain.py (line 302)

### P2: Natuurlijke Taal Commando's
**Symptoom:** "Bekijk mijn achievements" niet herkend
**Impact:** UX probleem - moet exact command gebruiken
**Files:** nlp_service.py (detect_command)

---

## 📐 ARCHITECTUUR OPMERKINGEN

### Sterke Punten:
✅ Modulaire service architectuur
✅ Duidelijke scheiding concerns (routes, services, models)
✅ Dynamisch lerend systeem (emotion triggers vanuit KB)
✅ Self-service admin tools (trigger manager)
✅ Gelaagde knowledge structuur (4 layers + 5W)
✅ Knowledge graph voor relaties

### Verbeterpunten:
⚠️ spark_brain.py is zeer groot (95KB, 2400+ lines)
⚠️ Geen duidelijke "User Dashboard" voor niet-admins
⚠️ Admin panel vs User features gemengd in sidebar
⚠️ Session management kwetsbaar (localStorage alleen)
⚠️ Geen tussenlagen tussen gradatie 7 en 1

---

## 💡 WILLEM'S FEEDBACK (13 maart)

### Observatie:
- Admin kan profielen aanmaken (werkt goed)
- Knowledge Base heeft goede structuur
- **Gemis:** Gebruikers hebben geen equivalent "dashboard" voor hun eigen data
- Knowledge Base zou eigenlijk het "profiel voor de gebruiker" moeten zijn

### Visie:
Een gelaagd dashboard systeem waar:
1. Elke gebruiker hun eigen "Mijn Profiel" dashboard heeft
2. Gradaties 1-7 krijgen progressief meer features
3. Betere scheiding tussen "persoonlijke data" en "system-wide admin"
4. Structuur van links naar rechts, boven naar beneden

### Nieuw Idee: Audio Trigger Systeem
- Tool om woorden te koppelen aan geluidsbestanden
- VLC player voor stabiliteit
- Upload geluid → opslaan in media map
- Woord in chat → geluid afspeelt
- On/off toggle
- Tab met alle audio triggers (zoals Windows sounds)
- Voorbeeld: "druppel" in chat → druppel geluid

---

## 🎯 CONCLUSIE

**Huidige staat:** Solide basis met modulaire architectuur, maar:
- Admin-focused (gradatie 1 krijgt alles, rest weinig)
- Geen "User Dashboard" concept
- Enkele kritieke bugs in session/intent detection

**Willem's visie is logisch:** 
- Graduele unlock van features per gradatie
- Personal dashboard voor elke gebruiker
- Duidelijke scheiding system vs personal data

**Volgende stappen:**
1. Fix kritieke bugs (P0 → P1 → P2)
2. Ontwerp User Dashboard architectuur
3. Implementeer gelaagde navigatie
4. (Later) Audio trigger systeem

---

*Deze scan vormt de basis voor alle verdere ontwikkeling.*
