# 🎯 GERICHTE SCAN: Jouw Specifieke Ideeën

**Datum:** 10 maart 2026  
**Vraag:** Bestaan deze systemen al, gedeeltelijk, of helemaal niet?

---

## 1️⃣ SOUND EVENTS

### **Status:** ⚠️ **HALF VOORBEREID** (70%)

**✅ WAT BESTAAT:**
- **Event-trigger systeem:** ✅ VOLLEDIG
  - XP triggers (`xp_triggers.json`)
  - Achievement unlocks
  - Level calculations
  - Rank changes (auto-growth)
  
**Event Types die Sound kunnen Triggeren:**
```json
{
  "snap_approved": "XP awarded (10 XP)",
  "achievement_unlock": "Achievement unlocked",
  "level_up": "New level reached",
  "rank_up": "Gradatie verhoogd",
  "emotion_change": "Spark's emotie verandert"
}
```

**Locaties:**
- `/app/backend/services/achievement_service.py` (award_xp, unlock_achievement)
- `/app/backend/services/auth_service.py` (update_gradatie)
- `/app/backend/data/system/xp_triggers.json`

**❌ WAT ONTBREEKT:**
- Sound file management (geen `/public/sounds/` folder)
- Audio playback logic (geen `sound_manager.js`)
- Sound → event mapping
- User preferences voor sound (volume, on/off)

**🔧 WAT NODIG IS OM HET AF TE MAKEN:**
```javascript
// Frontend: /src/utils/sound_manager.js
const SOUNDS = {
  'xp_gain': '/sounds/coin.mp3',
  'level_up': '/sounds/level_up.mp3',
  'achievement': '/sounds/achievement.mp3',
  'rank_up': '/sounds/fanfare.mp3'
};

export function playSound(event_type, volume = 0.5) {
  if (!user_preferences.sounds_enabled) return;
  
  const audio = new Audio(SOUNDS[event_type]);
  audio.volume = volume;
  audio.play().catch(e => console.log('Sound play failed:', e));
}
```

**Integratie Punten:**
1. `achievement_service.award_xp()` → call `playSound('xp_gain')`
2. `achievement_service.unlock_achievement()` → call `playSound('achievement')`
3. Level-up detection → call `playSound('level_up')`
4. Gradatie update → call `playSound('rank_up')`

**ADVIES:**
- **Effort:** 4-6 uur
- **Impact:** Hoog (instant feedback, veel beter UX)
- **Priority:** Medium-High
- **Next Step:** 
  1. Download gratis sound effects (freesound.org)
  2. Maak `/public/sounds/` folder
  3. Bouw `sound_manager.js`
  4. Hook into existing events

---

## 2️⃣ COMMAND SIMPLIFICATION

### **Status:** ⚠️ **GEDEELTELIJK WERKEND** (65%)

**✅ WAT WERKT (Natuurlijke Taal):**

**Voorbeelden die NU werken:**
```
"Wat is de roadmap" → roadmap command ✅
"Wie ben je" → bio query ✅
"Help" → help command ✅
"Hoe gaat het met je" → system status ✅
"Welke gebruikers ken je" → show users ✅
"Afmeld" / "Uitloggen" → logout ✅
```

**Detectie Methode:**
- Keyword triggers (in `nlp_service.py`)
- Pattern matching (regex)
- Multiple variations per command

**Locatie:** `/app/backend/services/nlp_service.py` (detect_command method)

**❌ WAT NIET WERKT:**

**Math Commands:**
```
"Hoeveel is 25x25" → ❌ Niet gedetecteerd
"Wat is 15% van 200" → ❌ Niet gedetecteerd
"Tel 5 en 10 op" → ❌ Niet gedetecteerd
```

**Flexible Learning:**
```
"Onthoud dat ik van koffie hou" → ⚠️ Vereist "note:" prefix
"Vergeet mijn verjaardag niet" → ❌ Geen reminder parsing
```

**🔧 WAT NODIG IS:**

**A. Math Parser toevoegen:**
```python
# In nlp_service.py
def detect_math(text):
    """
    Parse math expressions:
    - "hoeveel is 25x25" → ("math", "25*25")
    - "wat is 15% van 200" → ("math", "200*0.15")
    - "tel 5 en 10 op" → ("math", "5+10")
    """
    text_lower = text.lower()
    
    # Pattern: "hoeveel is X [operator] Y"
    patterns = [
        (r'hoeveel is (\d+)\s*[\*x×]\s*(\d+)', lambda m: f"{m.group(1)}*{m.group(2)}"),
        (r'wat is (\d+)%\s*van\s*(\d+)', lambda m: f"{m.group(2)}*{m.group(1)}/100"),
        (r'tel (\d+) en (\d+) op', lambda m: f"{m.group(1)}+{m.group(2)}"),
    ]
    
    for pattern, builder in patterns:
        match = re.search(pattern, text_lower)
        if match:
            expression = builder(match)
            result = eval(expression)  # Safe in this context
            return ("math", result)
    
    return None
```

**B. Flexible "Onthoud" parsing:**
```python
# Detect "onthoud [iets]" zonder prefix
if text_lower.startswith("onthoud"):
    content = text[7:].strip()  # Remove "onthoud"
    return ("note", content)
```

**ADVIES:**
- **Effort:** 2 uur (math parser)
- **Impact:** Medium (nice-to-have feature)
- **Priority:** Medium
- **Next Step:** Voeg math detection toe aan `detect_command()`

---

## 3️⃣ GRADATIE SYSTEEM

### **Status:** ✅ **VOLLEDIG WERKEND** (100%)

**✅ VOLLEDIG GEÏMPLEMENTEERD:**

**Gradaties (1-7):**
```
1. Grasspriet (beginner)
2. Sprinkhaantje
3. Zaailing
4. Vlinder
5. Eik
6. Admin
7. Master (Willem)
```

**Privacy Implementatie:**
- **Users:** Kunnen hun gradatie NIET zien ✅
- **Admin:** Kan alle gradaties zien ✅
- **Master:** Full control ✅

**Waar het Zit:**
- **Backend:** `/app/backend/services/auth_service.py`
  - `check_auto_gradatie_growth()` - Auto verhogen
  - `update_gradatie()` - Manual override (admin)
  
- **Frontend:** `/app/frontend/src/components/ProfielenTab.js`
  - Admin UI om gradaties te bekijken/wijzigen
  - Verborgen voor normale users

- **Data:** `/app/backend/data/system/users.json`
```json
{
  "gradatie": 7,
  "gradatie_description": "Master"
}
```

**User Profiel (wat user ziet):**
```json
{
  "naam": "Willem",
  "stats": {
    "level": 5,
    "xp": 450,
    "rank": "Eik"  // ← Dit zie je WEL (rank)
  }
  // gradatie is verborgen
}
```

**Admin Profiel Tab (wat admin ziet):**
```
Naam: [User]
Rank: Eik
Gradatie: 5 [dropdown: 1-7]  ← Admin kan aanpassen
XP: 450
```

**Auto-Growth Logica:**
```python
# Automatisch verhogen op basis van activiteit
if gesprekken_count >= 100 and current_gradatie < 3:
    new_gradatie = 3  # Zaailing
elif gesprekken_count >= 250 and current_gradatie < 4:
    new_gradatie = 4  # Vlinder
# etc.
```

**PERFECT ZOALS HET IS!** ✅

**ADVIES:**
- Geen actie nodig
- Misschien later: gradatie-specific perks (feature unlocks)

---

## 4️⃣ ADMIN SLEUTELWOORDEN

### **Status:** ✅ **VOLLEDIG WERKEND** (100%)

**✅ ADMIN COMMANDS VIA SLEUTELWOORDEN:**

**Command Format:**
```
emotie: [emotienaam] [minuten]
```

**Voorbeelden:**
```
"emotie: blij 30" → Spark wordt blij voor 30 minuten
"emotie: boos 15" → Spark wordt boos voor 15 minuten
"emotie: neutraal" → Reset naar neutral
```

**Locatie:**
- **Detection:** `/app/backend/services/nlp_service.py` (line 252)
```python
if text_lower.startswith("emotie:"):
    content = text.split(":", 1)[1].strip()
    return ("emotion", content)
```

- **Execution:** `/app/backend/services/spark_brain.py`
```python
if cmd_type == "emotion" and user_data.get("rol") in ["admin", "master"]:
    # Parse emotie command
    # Set emotion via EmotionService
```

**Permission Check:**
```python
# Alleen admin/master kunnen emotie commands gebruiken
if user_data.get("rol") not in ["admin", "master"]:
    return "Sorry, alleen admins kunnen emoties aanpassen."
```

**Andere Admin Commands:**
- **Via UI (Admin Tab):**
  - Knowledge approve/reject/delete
  - User gradatie aanpassen
  - Snaps beheren
  
- **Via API (admin_routes.py):**
  - `PUT /api/admin/knowledge/{id}`
  - `DELETE /api/admin/knowledge/{id}`
  - `POST /api/admin/users/{id}/gradatie`

**VOLLEDIG OPERATIONEEL!** ✅

**Mogelijke Uitbreidingen:**
```python
# Toekomstige admin commands:
"debug: on" → Enable debug mode
"maintenance: start" → Maintenance mode
"broadcast: [message]" → Message to all users
```

**ADVIES:**
- Werkt perfect
- Later: meer admin shortcuts toevoegen

---

## 5️⃣ MASTERKEY / ROOT

### **Status:** ✅ **VOLLEDIG WERKEND** (100%)

**✅ MASTER SYSTEEM GEÏMPLEMENTEERD:**

**Hiërarchie:**
```
User (rol: "user")
  ↓
Admin (rol: "admin")
  ↓
Master (rol: "master") ← Willem met MASTERKEY
```

**Masterkey:**
- **Waarde:** `"SAMEN"` (case-insensitive)
- **Detection:** `/app/backend/services/nlp_service.py` (line 32-43)
```python
masterkey_patterns = [
    r"(?:mijn\s+)?masterkey\s+is\s+(\w+)",
    r"masterkey[:\s]+(\w+)",
    r"masterkey\s+(\w+)"
]
# Check: masterkey.lower() == "samen"
```

**Login Voorbeelden:**
```
"Willem Masterkey Samen" ✅
"Ik ben Willem, mijn Masterkey is Samen" ✅
"Willem MASTERKEY samen" ✅
```

**Permission Matrix:**

| Feature | User | Admin | Master |
|---------|------|-------|--------|
| Chat | ✅ | ✅ | ✅ |
| View KB | ✅ | ✅ | ✅ |
| Edit KB | ❌ | ✅ | ✅ |
| Admin Tab | ❌ | ✅ | ✅ |
| Profielen Tab | ❌ | ✅ | ✅ |
| Emotie Control | ❌ | ✅ | ✅ |
| **Delete Users** | ❌ | ❌ | ✅ |
| **System Config** | ❌ | ❌ | ✅ |
| **Roadmap Edit** | ❌ | ⚠️ | ✅ |

**Master-Only Functies:**
- User deletion
- System-wide configuration
- Roadmap management
- Emergency overrides

**Noodoverride:**
- Master kan ALTIJD inloggen (zelfs als systeem locked)
- Master kan andere admins degraderen
- Master heeft toegang tot alle data

**Code Check:**
```python
# auth_service.py
def is_master(user_data):
    return user_data.get("rol") == "master"

def is_admin_or_higher(user_data):
    return user_data.get("rol") in ["admin", "master"]
```

**PERFECT GEÏMPLEMENTEERD!** ✅

**ADVIES:**
- Werkt uitstekend
- Overweeg: emergency "god mode" command voor extreme situaties

---

## 6️⃣ INTENT HERKENNING (Roadmap Matching)

### **Status:** ⚠️ **GEDEELTELIJK** (40%)

**✅ WAT BESTAAT:**

**A. Basis Pattern Detection:**
- **Locatie:** `/app/backend/services/pattern_detection_service.py`
- **Capabilities:**
  - Extract topics from text
  - Key phrase extraction
  - Stopword detection ("belangrijk", "onthoud")
  - Frequent topic analysis

**Voorbeeld:**
```python
analyze_message("Ik wil graag een leaderboard bouwen") →
{
  "topics": ["leaderboard", "bouwen"],
  "importance_score": 3,
  "should_remember": False
}
```

**B. Classification System:**
- **Locatie:** `/app/backend/services/classification_service.py`
- **Capabilities:**
  - Classify into klassen (Personen, Activiteiten, Werk, etc.)
  - Context labeling
  - Confidence scoring

**❌ WAT ONTBREEKT:**

**Roadmap Intent Matching:**
```python
# Dit bestaat NIET:
user_input = "Ik wil graag sound effects toevoegen bij achievements"

match_with_roadmap(user_input) →
{
  "matched_items": [
    {
      "id": "v1_5_005",
      "title": "Sound Triggers",
      "similarity": 0.85,
      "status": "planned"
    }
  ],
  "is_duplicate": False,
  "suggestions": ["Dit staat al op de roadmap als v1_5_005"]
}
```

**Module Intent Matching:**
```python
# Dit bestaat NIET:
user_input = "Kunnen we math commands toevoegen?"

match_with_existing_modules(user_input) →
{
  "related_services": ["nlp_service", "command_parser"],
  "existing_patterns": ["Command detection aanwezig"],
  "missing_pieces": ["Math expression parser"],
  "effort_estimate": "2 hours"
}
```

**Eerdere Intenties:**
```python
# Dit bestaat NIET:
# Geen systeem om user's eerdere ideeën te tracken
# Geen "wish list" of "feature request" systeem
```

**🔧 WAT NODIG IS:**

**A. Roadmap Matcher Service:**
```python
# /app/backend/services/roadmap_matcher.py

import difflib
from services.roadmap_service import RoadmapService

class RoadmapMatcher:
    def match_intent(self, user_input: str):
        roadmap = RoadmapService.get_full_roadmap()
        
        # Extract keywords from input
        keywords = self._extract_keywords(user_input)
        
        # Match against roadmap items
        matches = []
        for item in roadmap:
            similarity = self._calculate_similarity(
                keywords, 
                item['title'] + ' ' + item.get('notes', '')
            )
            if similarity > 0.6:
                matches.append({
                    'item': item,
                    'similarity': similarity
                })
        
        # Sort by similarity
        matches.sort(key=lambda x: -x['similarity'])
        
        return {
            'matches': matches[:3],
            'is_likely_duplicate': matches[0]['similarity'] > 0.8 if matches else False
        }
```

**B. Feature Request Tracker:**
```json
// /app/backend/data/user_wishes/{user_id}.json
{
  "wishes": [
    {
      "id": "wish-001",
      "description": "Sound effects bij achievements",
      "requested_at": "2026-03-10",
      "status": "on_roadmap",
      "roadmap_item": "v1_5_005",
      "priority": "medium"
    }
  ]
}
```

**C. Intent History:**
```python
# Track wat user heeft gevraagd
conversation_service.log_intent(
    user_id=user.id,
    intent_type="feature_request",
    description="Sound effects toevoegen",
    matched_roadmap_item="v1_5_005"
)
```

**ADVIES:**
- **Effort:** 6-8 uur (voor volledige intent matching)
- **Impact:** Hoog (voorkomt duplicates, betere planning)
- **Priority:** Medium
- **Next Step:**
  1. Start simpel: keyword matching tegen roadmap titles
  2. Later: embeddings voor semantic matching
  3. Build feature request tracker

---

## 📊 SAMENVATTENDE TABEL

| Systeem | Status | Compleetheid | Effort om af te maken | Priority |
|---------|--------|--------------|----------------------|----------|
| **Sound Events** | ⚠️ Voorbereid | 70% | 4-6h | **Medium-High** |
| **Command Simplification** | ⚠️ Partieel | 65% | 2h (math) | Medium |
| **Gradatie Systeem** | ✅ Compleet | 100% | - | - |
| **Admin Sleutelwoorden** | ✅ Compleet | 100% | - | - |
| **Masterkey / Root** | ✅ Compleet | 100% | - | - |
| **Intent Herkenning** | ⚠️ Basis | 40% | 6-8h | Medium |

---

## 🎯 AANBEVOLEN ACTIEPLAN

### **FASE A: Afmaken Sound System** (4-6h)
**Reden:** Event systeem is al klaar, alleen audio playback ontbreekt

**Stappen:**
1. Download sound effects (1h)
2. Maak sound_manager.js (2h)
3. Hook into events (1h)
4. Add user preferences (1h)
5. Test & polish (1h)

**Impact:** Hoog - Instant gratification bij XP/achievements

---

### **FASE B: Math Commands** (2h)
**Reden:** Quick win, direct bruikbaar

**Stappen:**
1. Add math patterns to nlp_service (1h)
2. Test verschillende math expressions (0.5h)
3. Add to help command (0.5h)

**Impact:** Medium - Nice feature, niet critical

---

### **FASE C: Intent Matching** (6-8h)
**Reden:** Voorkomt dubbel werk, betere planning

**Stappen:**
1. Build roadmap_matcher.py (3h)
2. Add feature request tracking (2h)
3. Integrate in conversation flow (2h)
4. Test & refine (1h)

**Impact:** Hoog - Lange termijn efficiency

---

## 💡 LOGISCHE VOLGORDE

**Vandaag/Deze Week:**
1. ✅ Math commands (2h) - Quick win
2. ✅ Sound system (6h) - High impact

**Volgende Week:**
3. ⏳ Intent matching basis (4h) - Keyword-based
4. ⏳ Feature request tracker (2h)

**Later:**
5. 🔮 Semantic intent matching (ML-based)
6. 🔮 Advanced sound system (zones, 3D audio)

---

## ✨ CONCLUSIE

**Je Hebt Al:**
- ✅ Gradatie systeem (perfect!)
- ✅ Admin/Master structuur (perfect!)
- ✅ Event-trigger systeem (klaar voor sound)
- ⚠️ Command parsing (werkt, maar kan beter)
- ⚠️ Basis pattern detection (maar geen roadmap matching)

**Focus Op:**
1. **Sound system** - Event infra is klaar, voeg alleen audio toe
2. **Math commands** - 2 uur werk, direct bruikbaar
3. **Intent matching** - Later, maar wel waardevol

**Je bent 70-80% klaar met deze ideeën!** 🎉

De fundamenten zijn gelegd, nu alleen de finishing touches toevoegen.

**Wil je dat ik begin met sound system of math commands?** 🚀
