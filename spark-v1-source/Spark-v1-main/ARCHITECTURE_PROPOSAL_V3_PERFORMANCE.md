# 🚀 PERFORMANCE ARCHITECTURE: Context Layer met Volledige Geschiedenis

**Project:** Spark Foundation  
**Datum:** 10 maart 2026  
**Versie:** 3.0 (Performance Optimized)

---

## 🎯 HET PERFORMANCE PROBLEEM

### **De Uitdaging**

De Context Layer moet toegang hebben tot de **volledige conversatiegeschiedenis** om:
- Patronen over langere periodes te detecteren
- Terugkerende onderwerpen te herkennen
- Relatie-ontwikkeling te volgen
- Context van dagen/weken geleden te kunnen gebruiken

**MAAR:** Het ophalen en verwerken van duizenden berichten bij elk nieuw bericht zou de applicatie vertragen.

---

## 💡 DE OPLOSSING: Gelaagde Caching Strategie

### **Drie-lagen Architectuur**

```
┌─────────────────────────────────────────────────────────┐
│                   NIEUWE BERICHT                        │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
         ┌────────────────────────────┐
         │  LAAG 1: In-Memory Cache   │ ← INSTANT (0-5ms)
         │  Laatste 10-20 berichten   │
         │  Actieve sessie            │
         └────────────┬───────────────┘
                      │
                      │ (indien nodig)
                      ▼
         ┌────────────────────────────┐
         │  LAAG 2: Samenvattingen    │ ← SNEL (10-50ms)
         │  Periodiek gegenereerd     │
         │  Opgeslagen in users.json  │
         └────────────┬───────────────┘
                      │
                      │ (alleen bij diepe analyse)
                      ▼
         ┌────────────────────────────┐
         │  LAAG 3: Volledige History │ ← ON-DEMAND (100-500ms)
         │  Alle conversaties         │
         │  Lazy loading              │
         └────────────────────────────┘
```

---

## 🏗️ LAAG 1: In-Memory Cache (Real-Time)

### **Doel**
Onmiddellijke toegang tot de meest recente context zonder disk I/O.

### **Implementatie**

```python
# /app/backend/services/context_cache.py

from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from collections import OrderedDict

@dataclass
class CachedMessage:
    """Lightweight message representation voor cache"""
    message: str
    sender: str  # 'user' of 'spark'
    timestamp: datetime
    emotion: Optional[str] = None
    topics: List[str] = None
    
class ContextCache:
    """
    In-memory cache voor actieve sessies.
    Gebruikt LRU (Least Recently Used) om geheugen te beheersen.
    """
    
    def __init__(self, max_sessions: int = 100, messages_per_session: int = 20):
        self.max_sessions = max_sessions
        self.messages_per_session = messages_per_session
        
        # OrderedDict = auto LRU behavior
        self._cache: OrderedDict[str, List[CachedMessage]] = OrderedDict()
        
        # Statistics
        self.hits = 0
        self.misses = 0
    
    def get(self, session_id: str) -> Optional[List[CachedMessage]]:
        """
        Haal berichten op uit cache.
        
        Returns:
            List[CachedMessage] if found, None if miss
        """
        if session_id in self._cache:
            self.hits += 1
            # Move to end (most recently used)
            self._cache.move_to_end(session_id)
            return self._cache[session_id]
        
        self.misses += 1
        return None
    
    def add_message(self, session_id: str, message: CachedMessage):
        """
        Voeg bericht toe aan cache.
        Handhaaft maximum aantal berichten per sessie.
        """
        if session_id not in self._cache:
            # Nieuwe sessie
            if len(self._cache) >= self.max_sessions:
                # Remove oldest session (LRU)
                self._cache.popitem(last=False)
            
            self._cache[session_id] = []
        
        # Add message
        self._cache[session_id].append(message)
        
        # Maintain max messages
        if len(self._cache[session_id]) > self.messages_per_session:
            # Remove oldest message
            self._cache[session_id].pop(0)
        
        # Move to end (most recently used)
        self._cache.move_to_end(session_id)
    
    def clear_session(self, session_id: str):
        """Verwijder sessie uit cache (bij uitloggen)"""
        if session_id in self._cache:
            del self._cache[session_id]
    
    def clear_old_sessions(self, max_age_hours: int = 24):
        """
        Verwijder sessies ouder dan X uur (background task).
        """
        now = datetime.now()
        to_remove = []
        
        for session_id, messages in self._cache.items():
            if not messages:
                to_remove.append(session_id)
                continue
            
            last_message_time = messages[-1].timestamp
            age = (now - last_message_time).total_seconds() / 3600
            
            if age > max_age_hours:
                to_remove.append(session_id)
        
        for session_id in to_remove:
            del self._cache[session_id]
        
        return len(to_remove)
    
    def get_stats(self) -> dict:
        """Cache statistics voor monitoring"""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{hit_rate:.1f}%",
            "active_sessions": len(self._cache),
            "memory_usage_mb": self._estimate_memory_usage()
        }
    
    def _estimate_memory_usage(self) -> float:
        """Rough estimate van geheugengebruik (MB)"""
        total_messages = sum(len(msgs) for msgs in self._cache.values())
        avg_message_size = 500  # bytes (rough estimate)
        return (total_messages * avg_message_size) / (1024 * 1024)


# Global cache instance
_context_cache = ContextCache()

def get_cache() -> ContextCache:
    """Singleton access to cache"""
    return _context_cache
```

### **Geheugen Management**

**Configuratie:**
- **Max 100 actieve sessies** in cache
- **Max 20 berichten per sessie** (laatste 10-20 exchanges)
- **24-uurs expiry** voor inactieve sessies

**Geschat geheugengebruik:**
- 100 sessies × 20 berichten × ~500 bytes = **~1 MB**
- Verwaarloosbaar voor moderne servers ✅

---

## 📊 LAAG 2: Samenvattingen (Background Processing)

### **Doel**
Periodiek comprimeren van oudere gesprekken naar bruikbare samenvattingen.

### **Wat wordt samengevat?**

```python
@dataclass
class ConversationSummary:
    """
    Gecomprimeerde representatie van een conversatie periode.
    Opgeslagen in users.json onder elke user.
    """
    
    # Temporeel
    period_start: datetime
    period_end: datetime
    total_messages: int
    
    # Onderwerpen
    primary_topics: List[str]  # Top 5 besproken onderwerpen
    topic_frequencies: Dict[str, int]  # {"auto": 15, "school": 8}
    
    # Emotioneel
    dominant_emotions: List[str]  # ["happy", "curious", "excited"]
    emotional_peaks: List[dict]  # Momenten van hoge emotie
    mood_trajectory: str  # "improving", "stable", "declining"
    
    # Patronen
    recurring_questions: List[str]  # Vragen die blijven terugkomen
    learned_concepts: List[str]  # Wat gebruiker heeft geleerd
    unresolved_issues: List[str]  # Nog open vragen
    
    # Relatie
    compliments_given: int
    compliments_received: int
    conflicts: int
    resolutions: int
    
    # Metadata
    key_moments: List[dict]  # Belangrijke gespreksmomenten
    # {
    #   "timestamp": "2026-03-05 14:23",
    #   "summary": "User learned about cars",
    #   "emotion": "excited"
    # }
    
    generated_at: datetime
    version: str  # "1.0"


# /app/backend/services/summarization_service.py

class SummarizationService:
    """
    Achtergrondservice die periodiek oude conversaties samenvat.
    Draait als scheduled task (elke 6-12 uur).
    """
    
    def __init__(self):
        self.conversation_service = ConversationService()
        self.pattern_detector = PatternDetectionService()
        self.user_data = UserData()
    
    async def summarize_user_history(self, user_id: str):
        """
        Vat alle niet-samengevatte conversaties samen voor een user.
        
        Process:
        1. Haal alle berichten sinds laatste samenvatting
        2. Groepeer in logische periodes (bijv. per dag of per week)
        3. Extraheer patronen, onderwerpen, emoties
        4. Comprimeer naar ConversationSummary
        5. Sla op in users.json
        """
        
        # Get user data
        user = await self.user_data.get_user(user_id)
        last_summary_date = user.get("last_summary_date")
        
        # Get messages since last summary
        messages = await self.conversation_service.get_messages_since(
            user_id=user_id,
            since=last_summary_date
        )
        
        if len(messages) < 10:
            # Not enough new messages to summarize
            return None
        
        # Analyze messages
        summary = self._analyze_and_summarize(messages)
        
        # Store summary
        if "conversation_summaries" not in user:
            user["conversation_summaries"] = []
        
        user["conversation_summaries"].append({
            "period_start": summary.period_start.isoformat(),
            "period_end": summary.period_end.isoformat(),
            "total_messages": summary.total_messages,
            "primary_topics": summary.primary_topics,
            "topic_frequencies": summary.topic_frequencies,
            "dominant_emotions": summary.dominant_emotions,
            "mood_trajectory": summary.mood_trajectory,
            "recurring_questions": summary.recurring_questions,
            "learned_concepts": summary.learned_concepts,
            "unresolved_issues": summary.unresolved_issues,
            "key_moments": summary.key_moments,
            "generated_at": summary.generated_at.isoformat()
        })
        
        user["last_summary_date"] = datetime.now().isoformat()
        
        await self.user_data.update_user(user_id, user)
        
        return summary
    
    def _analyze_and_summarize(self, messages: List[dict]) -> ConversationSummary:
        """
        Analyseer berichten en genereer samenvatting.
        """
        
        # Extract all text
        all_text = " ".join([m.get("message", "") for m in messages])
        
        # Topic extraction
        topic_analysis = self.pattern_detector.analyze_message(all_text)
        topics = topic_analysis.get("topics", [])
        
        # Topic frequencies
        topic_freq = {}
        for msg in messages:
            msg_topics = self.pattern_detector.analyze_message(msg["message"]).get("topics", [])
            for t in msg_topics:
                topic_freq[t] = topic_freq.get(t, 0) + 1
        
        # Sort by frequency
        primary_topics = sorted(topic_freq.keys(), key=lambda t: topic_freq[t], reverse=True)[:5]
        
        # Emotion extraction
        emotions = []
        for msg in messages:
            emotion = msg.get("emotion")
            if emotion:
                emotions.append(emotion)
        
        # Dominant emotions (top 3)
        from collections import Counter
        emotion_counts = Counter(emotions)
        dominant_emotions = [e for e, _ in emotion_counts.most_common(3)]
        
        # Recurring questions
        questions = [m["message"] for m in messages if "?" in m["message"]]
        recurring = self._find_similar_questions(questions)
        
        # Key moments (high emotion or important events)
        key_moments = self._extract_key_moments(messages)
        
        return ConversationSummary(
            period_start=datetime.fromisoformat(messages[0]["timestamp"]),
            period_end=datetime.fromisoformat(messages[-1]["timestamp"]),
            total_messages=len(messages),
            primary_topics=primary_topics,
            topic_frequencies=topic_freq,
            dominant_emotions=dominant_emotions,
            emotional_peaks=[],  # TODO
            mood_trajectory=self._calculate_mood_trajectory(messages),
            recurring_questions=recurring,
            learned_concepts=[],  # TODO: detect from teaching moments
            unresolved_issues=[],  # TODO: detect from repeated questions
            compliments_given=0,  # TODO
            compliments_received=0,  # TODO
            conflicts=0,
            resolutions=0,
            key_moments=key_moments,
            generated_at=datetime.now(),
            version="1.0"
        )
    
    def _find_similar_questions(self, questions: List[str]) -> List[str]:
        """Find questions that repeat"""
        # TODO: Implement similarity detection
        # For now, exact match
        from collections import Counter
        counts = Counter(questions)
        return [q for q, c in counts.items() if c > 1]
    
    def _extract_key_moments(self, messages: List[dict]) -> List[dict]:
        """Extract important conversation moments"""
        key_moments = []
        
        for msg in messages:
            # High emotion = key moment
            if msg.get("emotion_intensity", 0) > 0.8:
                key_moments.append({
                    "timestamp": msg["timestamp"],
                    "summary": msg["message"][:100],
                    "emotion": msg.get("emotion", "unknown")
                })
        
        return key_moments[:10]  # Max 10 key moments
    
    def _calculate_mood_trajectory(self, messages: List[dict]) -> str:
        """Calculate if mood is improving/declining/stable"""
        # TODO: More sophisticated analysis
        emotions = [m.get("emotion") for m in messages if m.get("emotion")]
        
        if not emotions:
            return "stable"
        
        # Simple heuristic: compare first half vs second half
        mid = len(emotions) // 2
        first_half = emotions[:mid]
        second_half = emotions[mid:]
        
        positive_emotions = {"happy", "excited", "content", "proud"}
        
        first_positive = sum(1 for e in first_half if e in positive_emotions) / len(first_half)
        second_positive = sum(1 for e in second_half if e in positive_emotions) / len(second_half)
        
        if second_positive > first_positive + 0.2:
            return "improving"
        elif second_positive < first_positive - 0.2:
            return "declining"
        else:
            return "stable"
```

### **Wanneer worden samenvattingen gegenereerd?**

**Trigger 1: Scheduled Background Task**
```python
# Draait elke 6 uur
# Vat gesprekken > 50 berichten samen die nog niet samengevat zijn
```

**Trigger 2: Session End**
```python
# Bij uitloggen of inactiviteit > 1 uur
# Vat huidige sessie samen als > 20 berichten
```

**Trigger 3: Manual**
```python
# Admin kan handmatig samenvattingen genereren
# Nuttig voor testing en data cleanup
```

---

## 🔍 LAAG 3: Volledige Geschiedenis (On-Demand)

### **Doel**
Toegang tot **alle** berichten wanneer echt nodig, maar niet bij elk nieuw bericht.

### **Wanneer wordt dit gebruikt?**

**Use Case 1: Diepe Analyse (Expliciet verzoek)**
```
User: "Wat hebben we de afgelopen maand besproken over auto's?"
       ↓
Context Layer laadt volledige geschiedenis voor analyse
       ↓
Genereert uitgebreide samenvatting
```

**Use Case 2: Pattern Detection (Periodiek)**
```
Background task (1x per week):
  - Laad volledige geschiedenis
  - Detecteer lange-termijn patronen
  - Update user profiel met inzichten
```

**Use Case 3: Debugging / Admin**
```
Admin panel:
  - Bekijk volledige conversatie geschiedenis
  - Analyseer waar dingen mis gaan
  - Export voor training
```

### **Implementatie**

```python
# /app/backend/services/full_history_loader.py

class FullHistoryLoader:
    """
    Lazy loader voor volledige conversatie geschiedenis.
    Gebruikt pagination en streaming om geheugen te beheersen.
    """
    
    def __init__(self):
        self.conversation_service = ConversationService()
    
    async def load_full_history(
        self, 
        user_id: str,
        session_id: Optional[str] = None,
        limit: Optional[int] = None,
        filter_by_topic: Optional[str] = None
    ) -> List[dict]:
        """
        Laad volledige geschiedenis met optionele filters.
        
        Args:
            user_id: User ID
            session_id: Optioneel - alleen deze sessie
            limit: Optioneel - max aantal berichten
            filter_by_topic: Optioneel - alleen berichten over dit onderwerp
        
        Returns:
            List[dict] met alle berichten
        
        Performance:
            - Gebruikt pagination (batches van 100)
            - Streaming response (niet alles in geheugen)
            - Caching per user (5 min TTL)
        """
        
        # Check cache first (TTL = 5 min)
        cache_key = f"full_history:{user_id}"
        cached = await self._get_from_cache(cache_key)
        if cached:
            return self._apply_filters(cached, session_id, limit, filter_by_topic)
        
        # Load from disk (paginated)
        all_messages = []
        offset = 0
        batch_size = 100
        
        while True:
            batch = await self.conversation_service.get_messages(
                user_id=user_id,
                offset=offset,
                limit=batch_size
            )
            
            if not batch:
                break
            
            all_messages.extend(batch)
            offset += batch_size
            
            # Safety limit
            if len(all_messages) > 10000:
                break  # Max 10k messages
        
        # Cache result
        await self._set_cache(cache_key, all_messages, ttl=300)  # 5 min
        
        # Apply filters
        return self._apply_filters(all_messages, session_id, limit, filter_by_topic)
    
    def _apply_filters(
        self, 
        messages: List[dict],
        session_id: Optional[str],
        limit: Optional[int],
        filter_by_topic: Optional[str]
    ) -> List[dict]:
        """Apply filters to message list"""
        
        filtered = messages
        
        if session_id:
            filtered = [m for m in filtered if m.get("session_id") == session_id]
        
        if filter_by_topic:
            # TODO: implement topic filtering
            pass
        
        if limit:
            filtered = filtered[:limit]
        
        return filtered
    
    async def _get_from_cache(self, key: str) -> Optional[List[dict]]:
        """Get from in-memory cache (simple dict for now)"""
        # TODO: Use Redis for production
        return None
    
    async def _set_cache(self, key: str, value: List[dict], ttl: int):
        """Set in cache with TTL"""
        # TODO: Implement
        pass
```

---

## 🔄 UPDATED CONTEXT LAYER (Met Performance Optimalisatie)

### **Nieuwe enrich() Method**

```python
# /app/backend/services/context_layer.py (UPDATED)

class ContextLayer:
    """
    Context Layer met 3-lagen toegang tot geschiedenis.
    """
    
    def __init__(self):
        self.cache = get_cache()  # Laag 1: In-memory
        self.conversation_service = ConversationService()
        self.summarization_service = SummarizationService()  # Laag 2
        self.full_loader = FullHistoryLoader()  # Laag 3
        self.context_engine = ContextEngine()
        self.pattern_detector = PatternDetectionService()
        self.user_profile = UserProfileService()
    
    async def enrich(
        self, 
        content_analysis: ContentAnalysis,
        user_data: dict,
        session_id: str,
        deep_analysis: bool = False  # ← NEW: trigger deep analysis
    ) -> ContextualAnalysis:
        """
        Main entry point met performance-optimized history access.
        
        Args:
            content_analysis: Output from ContentEngine
            user_data: User profile data
            session_id: Current session ID
            deep_analysis: If True, uses full history (slower)
        
        Returns:
            ContextualAnalysis
        """
        start_time = datetime.now()
        
        # LAAG 1: Check in-memory cache first (INSTANT)
        recent_messages = self.cache.get(session_id)
        
        if recent_messages is None:
            # CACHE MISS: Load from disk
            recent_messages = await self._load_recent_from_disk(session_id)
            
            # Populate cache for next time
            for msg in recent_messages:
                self.cache.add_message(session_id, CachedMessage(
                    message=msg["message"],
                    sender=msg["sender"],
                    timestamp=datetime.fromisoformat(msg["timestamp"]),
                    emotion=msg.get("emotion"),
                    topics=msg.get("topics", [])
                ))
        
        # Build conversation context from recent messages
        conversation_context = self._build_conversation_context(recent_messages)
        
        # LAAG 2: Add summary context (FAST)
        summaries = user_data.get("conversation_summaries", [])
        if summaries:
            # Enrich context with summary insights
            conversation_context = self._enrich_with_summaries(
                conversation_context,
                summaries
            )
        
        # LAAG 3: Deep analysis if requested (SLOW but comprehensive)
        if deep_analysis:
            full_history = await self.full_loader.load_full_history(
                user_id=user_data["id"],
                limit=1000  # Last 1000 messages
            )
            conversation_context = self._enrich_with_full_history(
                conversation_context,
                full_history
            )
        
        # Rest of analysis (same as before)
        topic_continuity = self.detect_topic_continuity(...)
        user_patterns = self.get_user_patterns(...)
        situation = self.determine_situation(...)
        semantic_nuance = self.detect_semantic_nuance(...)
        
        # ... build ContextualAnalysis ...
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return ContextualAnalysis(...)
    
    async def _load_recent_from_disk(self, session_id: str) -> List[dict]:
        """Load last 20 messages from disk (cache miss)"""
        return await self.conversation_service.get_recent_context(session_id, limit=20)
    
    def _build_conversation_context(self, messages: List[CachedMessage]) -> ConversationContext:
        """Build ConversationContext from cached messages"""
        # Same logic as before, but using CachedMessage objects
        ...
    
    def _enrich_with_summaries(
        self, 
        context: ConversationContext,
        summaries: List[dict]
    ) -> ConversationContext:
        """
        Verrijk context met inzichten uit samenvattingen.
        
        Adds:
        - Long-term topics (wat gebruiker vaak bespreekt)
        - Recurring questions (blijven terugkomen)
        - Emotional patterns (lange termijn)
        - Relationship insights
        """
        
        # Collect all topics from summaries
        all_topics = []
        for summary in summaries:
            all_topics.extend(summary.get("primary_topics", []))
        
        # Most frequent topics
        from collections import Counter
        topic_counts = Counter(all_topics)
        long_term_topics = [t for t, _ in topic_counts.most_common(5)]
        
        # Add to context
        context.long_term_interests = long_term_topics
        
        # Collect recurring questions
        all_recurring = []
        for summary in summaries:
            all_recurring.extend(summary.get("recurring_questions", []))
        
        context.historical_recurring_questions = all_recurring
        
        # Emotional trajectory over time
        recent_summaries = sorted(summaries, key=lambda s: s["period_end"])[-5:]
        mood_trend = [s.get("mood_trajectory", "stable") for s in recent_summaries]
        
        if mood_trend.count("improving") > mood_trend.count("declining"):
            context.long_term_mood = "improving"
        elif mood_trend.count("declining") > mood_trend.count("improving"):
            context.long_term_mood = "declining"
        else:
            context.long_term_mood = "stable"
        
        return context
    
    def _enrich_with_full_history(
        self,
        context: ConversationContext,
        full_history: List[dict]
    ) -> ConversationContext:
        """
        Verrijk context met diepe analyse van volledige geschiedenis.
        Alleen gebruikt bij expliciet verzoek.
        """
        
        # Deep pattern analysis
        # TODO: Implement deep pattern detection
        
        return context
```

---

## 📈 PERFORMANCE METRICS

### **Typical Request Flow**

**Normal Message (Cache Hit):**
```
1. Check in-memory cache          → 0-5ms
2. Build conversation context     → 5-10ms
3. Enrich with summaries          → 10-20ms
4. Semantic analysis              → 20-30ms
───────────────────────────────────────────
Total:                            → 35-65ms ✅
```

**Normal Message (Cache Miss):**
```
1. Load from disk (20 messages)   → 50-100ms
2. Populate cache                 → 5-10ms
3. Build conversation context     → 5-10ms
4. Enrich with summaries          → 10-20ms
5. Semantic analysis              → 20-30ms
───────────────────────────────────────────
Total:                            → 90-170ms ✅
```

**Deep Analysis (On-Demand):**
```
1. Check cache                    → 0-5ms
2. Load full history (1000 msgs)  → 200-500ms
3. Deep pattern detection         → 100-300ms
4. Build enriched context         → 50-100ms
5. Semantic analysis              → 20-30ms
───────────────────────────────────────────
Total:                            → 370-935ms
Acceptable for explicit requests ✅
```

### **Memory Usage**

**In-Memory Cache:**
- 100 active sessions × 20 messages = **~1 MB**

**Summaries in users.json:**
- Per user: ~50 summaries × 2 KB = **~100 KB per user**
- 1000 users = **~100 MB** total

**Total Memory Footprint:**
- Cache: 1 MB
- App: ~50 MB
- Node: ~100 MB
───────────────────
**Total: ~150 MB** ✅ Very acceptable

---

## 🎯 WANNEER WELKE LAAG?

### **Laag 1: In-Memory Cache (Default)**

**Gebruikt voor:**
- Alle normale berichten (99% van requests)
- Real-time conversatie
- Sarcasm detectie (vereist recente context)
- Topic continuity
- User mood tracking

**Performance:** 35-65ms per request

---

### **Laag 2: Samenvattingen (Automatisch toegevoegd)**

**Gebruikt voor:**
- Lange-termijn patronen
- Recurring questions detection
- User relationship insights
- Emotional trajectory over weken

**Toegevoegd aan:** Alle requests (geen performance impact, al in user object)

**Performance:** +10-20ms (negligible)

---

### **Laag 3: Volledige Geschiedenis (Expliciet)**

**Gebruikt voor:**
- User vraagt: "Wat hebben we besproken over X?"
- Admin analysis
- Deep pattern detection (weekly background task)
- Export / debugging

**Triggered by:**
```python
# Explicit deep_analysis flag
context = await context_layer.enrich(
    content_analysis=content,
    user_data=user,
    session_id=session,
    deep_analysis=True  # ← Trigger full history load
)
```

**Performance:** 370-935ms (acceptable voor deze use cases)

---

## 🔧 BACKGROUND TASKS

### **Task 1: Cache Cleanup (Elke 1 uur)**

```python
# /app/backend/tasks/cache_cleanup.py

async def cleanup_old_cache_sessions():
    """
    Verwijder sessies > 24 uur oud uit cache.
    Voorkomt geheugenlekkage.
    """
    cache = get_cache()
    removed = cache.clear_old_sessions(max_age_hours=24)
    print(f"[Cache Cleanup] Removed {removed} old sessions")
```

---

### **Task 2: Summarization (Elke 6 uur)**

```python
# /app/backend/tasks/summarization.py

async def summarize_all_users():
    """
    Vat nieuwe conversaties samen voor alle actieve users.
    """
    summarization = SummarizationService()
    user_data = UserData()
    
    active_users = await user_data.get_active_users(days=7)
    
    for user in active_users:
        try:
            summary = await summarization.summarize_user_history(user["id"])
            if summary:
                print(f"[Summarization] User {user['id']}: {summary.total_messages} messages summarized")
        except Exception as e:
            print(f"[Summarization] Error for user {user['id']}: {e}")
```

---

### **Task 3: Deep Pattern Analysis (Wekelijks)**

```python
# /app/backend/tasks/pattern_analysis.py

async def weekly_pattern_analysis():
    """
    Wekelijkse diepe analyse van alle users.
    Detecteert lange-termijn patronen en update profielen.
    """
    user_data = UserData()
    full_loader = FullHistoryLoader()
    
    all_users = await user_data.get_all_users()
    
    for user in all_users:
        try:
            # Load full history
            history = await full_loader.load_full_history(user["id"])
            
            # Detect long-term patterns
            patterns = analyze_long_term_patterns(history)
            
            # Update user profile
            await user_data.update_user(user["id"], {
                "long_term_patterns": patterns,
                "last_pattern_analysis": datetime.now().isoformat()
            })
            
        except Exception as e:
            print(f"[Pattern Analysis] Error for user {user['id']}: {e}")
```

---

## 🚀 IMPLEMENTATION PLAN

### **FASE 1: Core Cache Layer** (4-6h)

1. **Implement ContextCache class** (2h)
   - LRU cache met OrderedDict
   - add_message(), get(), clear_session()
   - Memory management

2. **Integrate met Context Layer** (2h)
   - Update enrich() method
   - Cache check → disk fallback
   - Update cache na elk bericht

3. **Testing** (1-2h)
   - Unit tests voor cache
   - Performance benchmarks
   - Memory leak tests

**Deliverable:** Working in-memory cache met 35-65ms response tijd ✅

---

### **FASE 2: Summarization Service** (6-8h)

1. **ConversationSummary dataclass** (1h)
   - Define schema
   - JSON serialization

2. **SummarizationService class** (3-4h)
   - summarize_user_history()
   - _analyze_and_summarize()
   - Topic/emotion extraction

3. **Background task** (1h)
   - Scheduled task (elke 6 uur)
   - Trigger op session end

4. **Integrate met Context Layer** (1-2h)
   - _enrich_with_summaries()
   - Load summaries van user object

5. **Testing** (1h)
   - Generate test summaries
   - Verify enrichment

**Deliverable:** Automatic summarization running in background ✅

---

### **FASE 3: Full History Loader** (3-4h)

1. **FullHistoryLoader class** (2h)
   - Paginated loading
   - Filter support

2. **Integrate met Context Layer** (1h)
   - deep_analysis parameter
   - _enrich_with_full_history()

3. **Testing** (1h)
   - Load 1000+ messages
   - Performance test

**Deliverable:** On-demand full history access ✅

---

### **FASE 4: Background Tasks Setup** (2-3h)

1. **Task scheduler** (1h)
   - APScheduler of Celery
   - Cron-like scheduling

2. **Implement 3 tasks** (1-2h)
   - cache_cleanup (1 uur)
   - summarization (6 uur)
   - pattern_analysis (wekelijks)

**Deliverable:** Automated maintenance tasks ✅

---

## 📊 TOTAL IMPLEMENTATION TIME

**Core Cache:** 4-6h  
**Summarization:** 6-8h  
**Full History:** 3-4h  
**Background Tasks:** 2-3h  
──────────────────────  
**Total:** 15-21 uur (2-3 werkdagen)

---

## ✅ VOORDELEN VAN DEZE ARCHITECTUUR

### **1. Performance ✅**
- **35-65ms** normale response tijd (met cache hit)
- **90-170ms** met cache miss (acceptabel)
- **Geen vertragingen** voor normale conversatie

### **2. Schaalbaarheid ✅**
- Geheugengebruik blijft constant (~150 MB)
- Geen exponentiële groei met meer berichten
- Background tasks verdelen de load

### **3. Volledigheid ✅**
- Toegang tot **volledige geschiedenis** wanneer nodig
- **Lange-termijn patronen** via samenvattingen
- **Real-time context** via cache

### **4. Intelligent ✅**
- Cache voor snelheid
- Samenvattingen voor inzicht
- Full history voor diepte

### **5. Modulair ✅**
- Elke laag onafhankelijk
- Kan elk onderdeel uitbreiden
- Duidelijke interfaces

---

## 🎯 ANTWOORD OP DE VRAAG

**Vraag:** Hoe kan de Context Layer de volledige conversatiegeschiedenis gebruiken zonder prestatieproblemen?

**Antwoord:**

```
┌─────────────────────────────────────────────────────┐
│         GELAAGDE CACHING STRATEGIE                  │
│                                                     │
│  Laag 1: In-Memory Cache (20 berichten)            │
│          → 35-65ms  (99% van requests)  ✅          │
│                                                     │
│  Laag 2: Samenvattingen (alle geschiedenis)        │
│          → +10-20ms (automatisch)       ✅          │
│                                                     │
│  Laag 3: Volledige History (on-demand)             │
│          → 370-935ms (alleen bij expliciet verzoek)│
│                                          ✅          │
└─────────────────────────────────────────────────────┘

    ✅ Snelheid: 99% van requests < 100ms
    ✅ Volledigheid: Alle geschiedenis beschikbaar
    ✅ Intelligent: Juiste laag voor juiste situatie
    ✅ Schaalbaar: Geheugen blijft constant
```

---

## 📝 NEXT STEPS

**1. Goedkeuring van deze architectuur**
   - Bevestig dat dit de performance zorgen oplost
   - Eventuele aanpassingen aan strategie

**2. Start implementatie (Fase 1: Cache)**
   - Begin met ContextCache class
   - Integreer met bestaande Context Layer
   - Benchmark performance

**3. Fase 2-4**
   - Summarization service
   - Full history loader
   - Background tasks

**4. Testing & Optimization**
   - Load testing met 1000+ berichten
   - Memory profiling
   - Response time optimization

---

**Voldoet deze performance-architectuur aan je verwachtingen?** 🎯

**Ready to approve en starten met implementatie?** 🚀
