# 📊 Analyse: Legacy Emotie & Gedrag Systemen

**Datum:** 10 maart 2026  
**Doel:** Bepalen welke delen bruikbaar zijn in huidige Spark architectuur

---

## 📁 Geanalyseerde Bestanden

1. **Emotie.json** - Hiërarchisch emotiesysteem met 5 primaire emoties + sub-emoties
2. **Gedrag.json** - Interaction-driven gedragssysteem met clusters en transities

---

## 🎯 Emotie.json - Structuur Overzicht

### **Primaire Emoties (5)**
1. **Happy** → `blijdschap`, `vreugde`, `euforie`
2. **Angry** → `razernij`, `woede`, `irritatie`, `driftbui`
3. **Sad** → `neerslachtig`, `somber`, `verdrietig`
4. **Scared** → `angstig`, `voorzichtig`, `paniek`
5. **Neutral** → Basis staat

### **Communicatie Invloeden**
- **`linked_mode`**: Koppelt emotie aan operationele modus (bv. `work_mode`, `brainstorm_mode`, `energy_saving_mode`)
- **`max_words`**: Woordlimiet per emotie (bv. euforisch = 200 woorden, irritatie = 50 woorden)
- **`tone`**: Algemene toon (`positive`, `serious`, `empathetic`, `cautious`, `neutral`)
- **`examples`**: Concrete voorbeelden van tekstuele uitingen

### **Wat Ontbreekt**
- ❌ Geen transitielogica (hoe switch je van happy → sad?)
- ❌ Geen reset mechanisme
- ⚠️  Incomplete definities (sommige sub-emoties missen `max_words` en `examples`)

---

## 🎯 Gedrag.json - Structuur Overzicht

### **Interactie Clusters**
**Positive Cluster:** 2 positieve interacties
- Effect: +1 emotionele stap
- Gradatie impact: +0.5 stap
- Voorbeelden: complimenten, constructieve feedback, positieve verhalen

**Negative Cluster:** 3 negatieve uitingen
- Effect: -1 emotionele stap
- Gradatie impact: -0.5 stap
- Voorbeelden: beledigingen, negatieve opmerkingen, herhaalde negativiteit

### **Emotionele Schaal (6 stappen)**
```
Euforisch (200 woorden)
    ↑ +2 positieve interacties
Blijdschap (75 woorden)
    ↑ +2 positieve interacties
Neutral (50 woorden) ← START
    ↓ -3 negatieve uitingen
Geïrriteerd (30 woorden)
    ↓ -3 negatieve uitingen
Boos (10 woorden)
    ↓ -3 negatieve uitingen
Zwijgen (0 woorden, 24u timeout)
```

### **Reset Logica**
- **Inactiviteit:** 1 week → terug naar Neutral
- **Delay:** Als recente negatieve interacties, dan vertraging
- **Zwijgen State:** 24 uur stilte → auto-reset naar Neutral

### **Gradatie Systeem**
- Intensiteit van emoties neemt toe/af met clusters
- Beïnvloedt "diepte" van emotionele expressie

---

## ✅ BRUIKBARE ONDERDELEN

### 🟢 **Direct Bruikbaar (Minimal Effort)**

#### 1. **Woordlimiet Systeem**
**Huidige status:** Niet geïmplementeerd  
**Legacy waarde:** Duidelijke `max_words` per emotie  
**Integratie:** Makkelijk toe te voegen aan huidige emotie service

```python
# In LayeredAnswerService of SparkBrain
current_emotion = EmotionService.get_current_emotion()
max_words = EMOTION_WORD_LIMITS.get(current_emotion, 100)
response = truncate_to_words(response, max_words)
```

**Impact:** ⭐⭐⭐⭐ Hoog - Direct merkbaar in gesprekken

---

#### 2. **Tone-Based Response Modification**
**Huidige status:** Beperkt (alleen via emotie naam)  
**Legacy waarde:** `tone` veld (`positive`, `serious`, `empathetic`, `cautious`)  
**Integratie:** Kan worden toegevoegd aan bestaande emoties in `emotions.json`

**Impact:** ⭐⭐⭐ Medium - Verbetert consistentie van Spark's stemming

---

#### 3. **Emotie Examples als Template**
**Huidige status:** Niet geïmplementeerd  
**Legacy waarde:** Concrete voorbeelden per emotie  
**Integratie:** Kan worden gebruikt voor response styling/prompting

**Impact:** ⭐⭐⭐ Medium - Helpt bij prompt engineering

---

### 🟡 **Bruikbaar met Aanpassingen (Moderate Effort)**

#### 4. **Linked Mode Systeem**
**Huidige status:** Niet geïmplementeerd  
**Legacy waarde:** Emoties linken aan operationele modi  
**Integratie:** Vereist nieuwe "mode" laag in architectuur

**Aanpassingen nodig:**
- Definieer wat elke mode doet (`work_mode`, `brainstorm_mode`, etc.)
- Integreer met ConversationService en SparkBrain
- Maak mode-switcher logica

**Impact:** ⭐⭐⭐⭐⭐ Zeer hoog - Fundamental behavior shift

**Roadmap:** v2.5 of v3.0

---

#### 5. **Cluster-Based Emotional Transitions**
**Huidige status:** Niet geïmplementeerd (emoties zijn momenteel handmatig/admin-only)  
**Legacy waarde:** 2 positieve / 3 negatieve interacties → emotie shift  
**Integratie:** Vereist sentiment analysis + state tracking

**Aanpassingen nodig:**
- Implementeer sentiment classifier (positief/negatief/neutraal)
- Track interacties binnen sessie
- Bouw transitie engine die clusters detecteert
- Integreer met bestaand emotie systeem

**Impact:** ⭐⭐⭐⭐⭐ Zeer hoog - Automatische emotionele reacties

**Roadmap:** v2.0 of v2.5

---

#### 6. **Reset Logic (Inactivity-Based)**
**Huidige status:** Niet geïmplementeerd (emoties hebben duration, maar geen inactivity reset)  
**Legacy waarde:** 1 week inactiviteit → reset naar neutral  
**Integratie:** Kan worden toegevoegd aan bestaande duration systeem

**Aanpassingen nodig:**
- Track laatste interactie timestamp per user
- Cron job of background task om inactivity te checken
- Auto-reset functie naar neutral

**Impact:** ⭐⭐⭐ Medium - Voorkomt "vastgelopen" emoties

**Roadmap:** v2.0 (Easy win)

---

### 🔴 **Niet Direct Bruikbaar / Overlappend**

#### 7. **Emotionele Schaal uit Gedrag.json**
**Probleem:** Overlap met bestaande emoties in `emotions.json`  
**Verschil:** Legacy heeft 6-stappen lineaire schaal, huidige heeft 5 primaire emoties + 13 sub-emoties  
**Advies:** Gebruik huidige structuur, maar neem gradatie-concept over

---

#### 8. **Sub-emoties uit Emotie.json**
**Probleem:** Partial overlap met huidige 13 sub-emoties  
**Verschil:** Legacy heeft andere namen en groeperingen  
**Advies:** Merge: behoud huidige, voeg unieke toe (zie tabel hieronder)

---

## 🔄 MERGE STRATEGIE: Sub-Emoties

| **Legacy (Emotie.json)** | **Huidig (emotions.json)** | **Actie** |
|--------------------------|----------------------------|-----------|
| blijdschap, vreugde, euforie | blij, enthousiast, dankbaar | ✅ Behoud huidig + voeg "euforisch" toe |
| razernij, woede, irritatie, driftbui | boos, gefrustreerd | ✅ Merge: voeg "geïrriteerd", "razend" toe |
| neerslachtig, somber, verdrietig | verdrietig, teleurgesteld | ✅ Voeg "somber" toe |
| angstig, voorzichtig, paniek | angstig, zenuwachtig | ✅ Voeg "paniek" toe |
| (geen) | moe, rustig, nieuwsgierig, speels | ✅ Behoud unieke |

**Result:** ~18 sub-emoties totaal (van 13 → 18)

---

## 🗺️ ROADMAP INTEGRATIE

### **FASE 1: Quick Wins (v2.0 - Deze Sprint)**
**Geschatte tijd:** 2-4 uur  
**Prioriteit:** 🟢 High

1. ✅ **Woordlimiet Systeem** implementeren
2. ✅ **Tone veld** toevoegen aan bestaande emoties
3. ✅ **Reset logic** (inactivity-based) toevoegen

**Files te wijzigen:**
- `/app/backend/data/system/emotions.json` (voeg `max_words`, `tone` toe)
- `/app/backend/services/emotion_service.py` (word limit functie)
- `/app/backend/services/layered_answer_service.py` (response truncation)

---

### **FASE 2: Gedragsautomatisering (v2.5 - Volgende Sprint)**
**Geschatte tijd:** 1-2 dagen  
**Prioriteit:** 🟡 Medium-High

1. ⏳ **Sentiment Analysis** integreren (positief/negatief classifier)
2. ⏳ **Cluster Detection** implementeren (track 2 pos / 3 neg)
3. ⏳ **Automatische Emotie Transitions** op basis van clusters
4. ⏳ **Gradatie System** (intensiteit tracking)

**Nieuwe services:**
- `sentiment_classifier.py`
- `emotion_transition_engine.py`
- `interaction_tracker.py`

---

### **FASE 3: Operationele Modi (v3.0 - Toekomst)**
**Geschatte tijd:** 3-5 dagen  
**Prioriteit:** 🔴 Future

1. 🔮 **Linked Mode Systeem** ontwerpen
2. 🔮 **Mode Definitions** (`work_mode`, `brainstorm_mode`, etc.)
3. 🔮 **Mode Switcher** logica + UI controls
4. 🔮 **Mode-Specific Behaviors** per modus

---

## 📋 CONCRETE ACTIE ITEMS

### **Optie A: Minimale Integratie (Aanbevolen voor nu)**
**Wat:** Neem alleen Quick Wins over  
**Waarom:** Focus behouden op huidige knowledge systeem  
**Effort:** 2-4 uur

**Stappen:**
1. Voeg `max_words` en `tone` toe aan `/app/backend/data/system/emotions.json`
2. Implementeer word limit in response generation
3. Voeg inactivity reset toe aan emotie duration systeem
4. Update roadmap met FASE 2 & 3 als geplande items

---

### **Optie B: Volledige Merge (Later)**
**Wat:** Implementeer ook sentiment + clusters  
**Waarom:** Spark wordt echt emotioneel reactief  
**Effort:** 1-2 dagen  
**Timing:** Na P1 taken (XP notificatie, duplicaten merge, tag systeem)

---

## 🎯 MIJN ADVIES

**Voor Nu (Direct na P0 testing):**
✅ **Optie A: Quick Wins alleen**
- Implementeer woordlimiet + tone + reset logic
- Voeg FASE 2 & 3 toe aan roadmap als v2.5 items
- Blijf gefocust op knowledge systeem

**Later (Na v1.5 voltooiing):**
⏳ **Optie B: Gedragsautomatisering**
- Start met sentiment analysis
- Bouw cluster detection
- Test automatische emotie transitions

**Toekomst (v3.0):**
🔮 **Operationele Modi**
- Ontwerp mode systeem
- Integreer met community features

---

## 📊 WAARDE MATRIX

| Feature | Legacy Waarde | Integratie Effort | Impact | Timing |
|---------|--------------|-------------------|--------|--------|
| Woordlimiet | ⭐⭐⭐⭐⭐ | 🔨 Laag | ⚡⚡⚡⚡ | Nu |
| Tone veld | ⭐⭐⭐⭐ | 🔨 Laag | ⚡⚡⚡ | Nu |
| Reset logic | ⭐⭐⭐⭐ | 🔨 Laag | ⚡⚡⚡ | Nu |
| Cluster transitions | ⭐⭐⭐⭐⭐ | 🔨🔨🔨 Hoog | ⚡⚡⚡⚡⚡ | Later |
| Linked modes | ⭐⭐⭐⭐⭐ | 🔨🔨🔨🔨 Zeer hoog | ⚡⚡⚡⚡⚡ | Toekomst |
| Gradatie | ⭐⭐⭐ | 🔨🔨 Medium | ⚡⚡⚡ | Later |

---

## ❓ VRAGEN VOOR JOU

1. **Timing:** Wil je Quick Wins (Optie A) nu al implementeren, of pas na P1 taken?
2. **Priority:** Wat vind je belangrijker: automatische emotie transitions (cluster-based) of operationele modi?
3. **Scope:** Wil je de sub-emoties mergen zoals ik voorstel, of huidige structuur behouden?
4. **Roadmap:** Zal ik FASE 2 & 3 toevoegen aan roadmap met juiste prioriteiten?

---

**Status:** ✅ Analyse compleet, wacht op jouw beslissing
