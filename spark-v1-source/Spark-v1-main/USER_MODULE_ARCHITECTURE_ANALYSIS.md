# User Module Architecture - Analyse & Voorstel

**Datum:** 11 maart 2026  
**Context:** Willem's vraag over user-specific modules uit Spark Core V4  

---

## 🤔 De Vraag

**Willem's V4 concept:** Elke user had een eigen module die actief alles bijhield voor die user.

**Voordeel:** 
- Bij meerdere gebruikers kan elke module parallel processen draaien
- User-specific state management
- Betere isolatie

**Vraag:** Is dit nodig of maakt het het systeem onnodig complex?

---

## 📊 Huidige Architectuur (V3.0)

### **Hoe het NU werkt:**

```python
# spark_brain.py (Singleton - 1 instance voor ALLE users)
class SparkBrain:
    def __init__(self):
        # Shared services (stateless)
        self.nlp = NLPService()
        self.content_engine = ContentEngine()
        self.context_layer = ContextLayer()
        # ... etc
    
    def process_message(self, message: str, user_data: dict, session_id: str):
        # user_data wordt meegegeven als parameter
        # Alle services zijn STATELESS
        # User context wordt ad-hoc opgehaald uit database
        pass
```

**Karakteristieken:**
- ✅ **1 SparkBrain instance** voor alle users
- ✅ **Stateless services** (geen user state in memory)
- ✅ **User data als parameter** (functional approach)
- ✅ **Database als single source of truth**

**Voor/Nadelen:**
- ✅ Simpel en begrijpelijk
- ✅ Geen memory overhead
- ✅ Makkelijk te debuggen
- ⚠️ Bij elke request opnieuw user data ophalen
- ⚠️ Geen user-specific caching
- ⚠️ Moeilijk om background tasks per user te draaien

---

## 🏗️ V4 User Module Concept

### **Hoe het ZOU kunnen werken:**

```python
# user_module.py
class UserModule:
    """
    User-specific module die state en processing beheert voor 1 gebruiker.
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.user_data = None  # Cached user data
        self.conversation_history = []  # In-memory cache
        self.pending_tasks = []  # Background tasks
        self.last_activity = None
        
        # User-specific analyzers
        self.profile_enricher = ProfileEnricher(user_id)
        self.agenda_manager = AgendaManager(user_id)
        self.pattern_tracker = PatternTracker(user_id)
        
        # Load initial state
        self._load_user_state()
    
    def process_message(self, message: str, session_id: str):
        """Process message with user-specific context already loaded"""
        # Content analysis
        content = self.content_engine.analyze(message, self.user_data)
        
        # Profile enrichment (automatic)
        self.profile_enricher.extract_and_suggest(content)
        
        # Agenda management (automatic)
        self.agenda_manager.extract_events(content)
        
        # Pattern tracking
        self.pattern_tracker.track(content)
        
        # Generate response with full user context
        response = self._generate_response(content)
        
        # Update state
        self._update_state(message, response)
        
        return response
    
    def run_background_tasks(self):
        """Runs periodically for this user"""
        # Check for upcoming birthdays
        self.agenda_manager.check_reminders()
        
        # Generate conversation summaries
        self.profile_enricher.generate_summary_if_needed()
        
        # Clean old cache
        self._cleanup_old_data()
    
    def _load_user_state(self):
        """Load user data into memory"""
        self.user_data = DataManager.load_user(self.user_id)
        self.conversation_history = ConversationService.get_recent(self.user_id, limit=50)
    
    def _update_state(self, message: str, response: str):
        """Update in-memory state"""
        self.conversation_history.append({
            "message": message,
            "response": response,
            "timestamp": datetime.now()
        })
        self.last_activity = datetime.now()
        
        # Persist to database (async)
        self._persist_state()


# user_module_manager.py
class UserModuleManager:
    """
    Beheert alle user modules.
    """
    
    def __init__(self):
        self.modules: Dict[str, UserModule] = {}
        self.lock = threading.Lock()
    
    def get_module(self, user_id: str) -> UserModule:
        """Get or create user module"""
        with self.lock:
            if user_id not in self.modules:
                self.modules[user_id] = UserModule(user_id)
            return self.modules[user_id]
    
    def cleanup_inactive_modules(self):
        """Remove modules for inactive users"""
        with self.lock:
            inactive = [
                user_id for user_id, module in self.modules.items()
                if module.last_activity < datetime.now() - timedelta(hours=1)
            ]
            for user_id in inactive:
                del self.modules[user_id]
    
    def run_background_tasks(self):
        """Run background tasks for all active modules"""
        for module in self.modules.values():
            module.run_background_tasks()


# In spark_routes.py
user_module_manager = UserModuleManager()

@router.post("/chat")
async def chat(message: ChatMessage):
    # Get user-specific module
    module = user_module_manager.get_module(message.user_id)
    
    # Process with user module
    response = module.process_message(message.message, message.session_id)
    
    return ChatResponse(response=response)
```

---

## ⚖️ Vergelijking: Huidige vs User Module

| Aspect | Huidige (Stateless) | User Module |
|--------|---------------------|-------------|
| **Complexiteit** | ⭐⭐ Laag | ⭐⭐⭐⭐ Hoog |
| **Memory gebruik** | ⭐⭐⭐⭐⭐ Minimaal | ⭐⭐ Per user overhead |
| **Scalability (1-10 users)** | ⭐⭐⭐⭐⭐ Perfect | ⭐⭐⭐ Overkill |
| **Scalability (100+ users)** | ⭐⭐⭐ OK | ⭐⭐⭐⭐⭐ Excellent |
| **User-specific caching** | ⭐⭐ Beperkt | ⭐⭐⭐⭐⭐ Excellent |
| **Background tasks** | ⭐⭐ Moeilijk | ⭐⭐⭐⭐⭐ Excellent |
| **Real-time features** | ⭐⭐⭐ OK | ⭐⭐⭐⭐⭐ Excellent |
| **Debugging** | ⭐⭐⭐⭐⭐ Makkelijk | ⭐⭐⭐ Moeilijker |
| **Testbaarheid** | ⭐⭐⭐⭐⭐ Excellent | ⭐⭐⭐ OK |

---

## 🎯 Wanneer WEL User Modules?

### **Scenario's waar het ZINVOL is:**

1. **Veel actieve users (50+)**
   - Memory overhead weegt op tegen database calls
   - Caching per user loont

2. **Background processing nodig**
   - Periodieke reminders (verjaardagen, afspraken)
   - Automatische summaries
   - Patroon detectie over tijd

3. **Real-time features**
   - Live notifications
   - Proactieve suggesties
   - Multi-device sync

4. **Complex user state**
   - Veel in-memory tracking
   - Conversatie context over meerdere sessies
   - User-specific ML models

5. **High-frequency interactions**
   - Meerdere messages per seconde
   - Database calls worden bottleneck

### **Voorbeeld use cases:**
- 💬 **Slack bot** met 100+ teams
- 🤖 **Customer service bot** met 1000+ concurrent users
- 🎮 **Gaming companion** met real-time tracking
- 📊 **Analytics dashboard** met live data processing

---

## 🚫 Wanneer NIET User Modules?

### **Scenario's waar het OVERKILL is:**

1. **Weinig users (< 20)**
   - Memory overhead niet waard
   - Simpeler systeem volstaat

2. **Lage frequentie**
   - Gebruikers chatten 1x per dag
   - Database calls zijn geen probleem

3. **Eenvoudige state**
   - Alleen user profile + history
   - Geen complexe tracking nodig

4. **Geen background tasks**
   - Alle processing is request-driven
   - Geen periodieke jobs nodig

5. **Development snelheid prioriteit**
   - Sneller itereren met simpel systeem
   - Minder bugs, makkelijker debuggen

### **Jouw huidige situatie (Spark):**
- 👤 **Weinig users** (< 10?)
- 💬 **Normale frequentie** (niet real-time)
- 📊 **Medium complexiteit** (groeiend)
- ⏱️ **Development fase** (snel itereren belangrijk)

**→ Huidige systeem is waarschijnlijk voldoende!**

---

## 🔀 Middle Ground: UserContextManager (Aanbevolen)

### **Beste van beide werelden:**

```python
# user_context_manager.py
class UserContextManager:
    """
    Lightweight user state manager zonder volledige module overhead.
    """
    
    def __init__(self):
        # Simpele cache met TTL
        self.user_cache: Dict[str, Dict] = {}
        self.cache_ttl = 3600  # 1 uur
    
    def get_user_context(self, user_id: str) -> Dict:
        """
        Get user context (cached if possible).
        """
        if user_id in self.user_cache:
            cached = self.user_cache[user_id]
            if cached['expires_at'] > time.time():
                return cached['data']
        
        # Cache miss - load from database
        user_data = DataManager.load_user(user_id)
        
        # Enrich with additional context
        context = {
            'user_data': user_data,
            'recent_conversations': ConversationService.get_recent(user_id, limit=10),
            'pending_profile_updates': self._get_pending_updates(user_id),
            'pending_agenda_items': self._get_pending_agenda(user_id),
            'active_patterns': PatternDetectionService.get_active_patterns(user_id)
        }
        
        # Cache it
        self.user_cache[user_id] = {
            'data': context,
            'expires_at': time.time() + self.cache_ttl
        }
        
        return context
    
    def invalidate_cache(self, user_id: str):
        """Invalidate cache when user data changes"""
        if user_id in self.user_cache:
            del self.user_cache[user_id]
    
    def _get_pending_updates(self, user_id: str) -> List:
        """Get pending profile/agenda updates"""
        # Check for auto-extracted info waiting for approval
        return ProfileEnrichmentService.get_pending(user_id)
    
    def _get_pending_agenda(self, user_id: str) -> List:
        """Get pending agenda items"""
        return AgendaService.get_pending(user_id)


# In spark_brain.py
class SparkBrain:
    def __init__(self):
        # ... existing services ...
        self.user_context_manager = UserContextManager()
    
    def process_message(self, message: str, user_data: dict, session_id: str):
        # Get enriched context (cached if available)
        user_context = self.user_context_manager.get_user_context(user_data['id'])
        
        # Use enriched context in processing
        content_analysis = self.content_engine.analyze(
            message, 
            user_context['user_data']
        )
        
        # ... rest of pipeline ...
        
        # If user data changed, invalidate cache
        if profile_updated:
            self.user_context_manager.invalidate_cache(user_data['id'])
```

**Voordelen:**
- ✅ Simpel caching systeem (geen volledige modules)
- ✅ Beter performance (minder database calls)
- ✅ Makkelijk uit te breiden naar volledige modules later
- ✅ Lage complexiteit
- ✅ Goed genoeg voor 1-50 users

---

## 💡 Mijn Aanbeveling voor Spark

### **Huidige Fase (v3.x):**

**Blijf bij huidige systeem + voeg UserContextManager toe**

**Waarom:**
1. ✅ Je hebt nog weinig users
2. ✅ Development snelheid is belangrijk
3. ✅ Je wilt snel kunnen itereren
4. ✅ Simpel systeem = minder bugs
5. ✅ UserContextManager geeft je voldoende caching

**Wat toevoegen:**
- Lightweight `UserContextManager` voor caching
- Pending updates systeem (profile + agenda)
- Simple background job voor reminders (scheduled task, niet per-user modules)

### **Toekomst (v5.0+):**

**Overweeg User Modules wanneer:**
1. Je hebt 50+ actieve users
2. Real-time features worden belangrijk
3. Je wilt per-user background processing
4. Memory overhead is acceptabel

---

## 🏁 Conclusie

### **Is het een dom idee?**
**NEE!** Het is een valide architecturaal patroon.

### **Is het nodig NU?**
**Waarschijnlijk niet.** Voor jouw huidige schaal is het overkill.

### **Wat WEL doen?**
**UserContextManager** implementeren:
- Simpel caching systeem
- Pending updates beheer
- Basis voor toekomstige uitbreiding
- Lage complexiteit, goede performance

### **Implementatie voorstel:**

**Fase 1: UserContextManager (2-3 uur)**
- Basis caching systeem
- Context enrichment
- Cache invalidation

**Fase 2: Pending Updates System (3-4 uur)**  
- Profile updates tracking
- Agenda items tracking
- Approve/reject flow

**Fase 3: Background Jobs (2-3 uur)**
- Simpele scheduled tasks (niet per-user modules!)
- Birthday reminders
- Summary generation

**Totaal: ~8-10 uur**

Dit geeft je 80% van de voordelen van User Modules met 20% van de complexiteit! 🎯

---

## 🤔 Vragen voor Willem

1. **Hoeveel users verwacht je?**
   - < 10: Huidige systeem prima
   - 10-50: UserContextManager toevoegen
   - 50+: Overweeg volledige User Modules

2. **Hoe werkten de modules in V4?**
   - Wat deden ze precies?
   - Welke voordelen merkte je?
   - Wat waren nadelen/problemen?

3. **Welke features zijn prioriteit?**
   - Background reminders?
   - Real-time updates?
   - Proactieve suggesties?

4. **Development snelheid vs optimalisatie?**
   - Snel itereren (huidige systeem houden)
   - Performance focus (User Modules overwegen)

**Mijn advies:** Start met **UserContextManager** en kijk hoe ver dat je brengt! 🚀
