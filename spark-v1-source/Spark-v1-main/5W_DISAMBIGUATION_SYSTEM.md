# 🎯 5W Disambiguation Systeem - Voorstel

**Datum:** 15 maart 2026  
**Voor:** Willem Spakman  
**Concept:** Gebruik 5W's (Who/What/When/Where/Why/How) voor context-aware antwoorden

---

## 💡 HET PROBLEEM

### **"Lotus" heeft meerdere betekenissen:**

```
Vraag: "Vertel over Lotus"

Mogelijke antwoorden:
1. WIE: Lotus Spakman (dochter Willem) - PERSOONLIJK DOSSIER
2. WAT: Lotus koekjes (Biscoff) - KNOWLEDGE BASE
3. WAT: Lotusbloem (waterplant) - KNOWLEDGE BASE
4. WAT: Lotus (automerk) - KNOWLEDGE BASE

→ Systeem weet niet welke!
```

---

## 🎯 DE OPLOSSING: 5W Context

### **De W in de vraag bepaalt het antwoord:**

```python
# Vraag analyse
"WIE is Lotus?"      → Type: PERSOON → Check persoonlijk dossier
"WAT is Lotus?"      → Type: OBJECT → Check knowledge base
"WAAR is Lotus?"     → Type: PLAATS → Check locaties
"WANNEER is Lotus?"  → Type: TIJD/EVENT → Check agenda/gebeurtenissen
"WAAROM Lotus?"      → Type: REDEN → Check motivaties/filosofie
"HOE werkt Lotus?"   → Type: PROCES → Check procedures
```

---

## 🏗️ IMPLEMENTATIE

### **Stap 1: Metadata Toevoegen aan Kaarten**

**Huidige kaart structuur:**
```json
{
  "id": "xxx",
  "label": "Lotus Spakman (dochter Willem)",
  "content": "...",
  "tags": ["lotus_spakman", "familie", "dochter"],
  "gradatie": 1
}
```

**Nieuwe structuur (met 5W type):**
```json
{
  "id": "xxx",
  "label": "Lotus Spakman (dochter Willem)",
  "content": "...",
  "tags": ["lotus_spakman", "familie", "dochter"],
  "gradatie": 1,
  "w_type": "WHO",  // ← NIEUW!
  "category": "persoon",
  "source": "persoonlijk_dossier"
}
```

**Alle W Types:**
```
WHO    = Persoon, familie, gebruiker
WHAT   = Object, concept, kennis
WHERE  = Plaats, locatie
WHEN   = Tijd, datum, gebeurtenis
WHY    = Reden, motivatie, doel
HOW    = Proces, methode, instructie
```

---

### **Stap 2: Query Analyse**

```python
def analyze_query(user_question):
    """
    Bepaal de W-type van de vraag
    """
    question_lower = user_question.lower()
    
    # WHO vragen
    if any(word in question_lower for word in ['wie', 'who', 'persoon', 'iemand']):
        return {
            'w_type': 'WHO',
            'priority': ['persoonlijk_dossier', 'users', 'familie'],
            'filters': {'category': ['persoon', 'gebruiker', 'familie']}
        }
    
    # WHAT vragen
    if any(word in question_lower for word in ['wat', 'what', 'betekent', 'definitie']):
        return {
            'w_type': 'WHAT',
            'priority': ['knowledge_base', 'concepts'],
            'filters': {'category': ['object', 'concept', 'kennis']}
        }
    
    # WHERE vragen
    if any(word in question_lower for word in ['waar', 'where', 'locatie', 'plek']):
        return {
            'w_type': 'WHERE',
            'priority': ['locaties', 'plaatsen'],
            'filters': {'category': ['plaats', 'locatie', 'land', 'stad']}
        }
    
    # WHEN vragen
    if any(word in question_lower for word in ['wanneer', 'when', 'datum', 'tijd']):
        return {
            'w_type': 'WHEN',
            'priority': ['agenda', 'gebeurtenissen', 'geschiedenis'],
            'filters': {'category': ['tijd', 'datum', 'gebeurtenis']}
        }
    
    # WHY vragen
    if any(word in question_lower for word in ['waarom', 'why', 'reden', 'doel']):
        return {
            'w_type': 'WHY',
            'priority': ['filosofie', 'motivaties'],
            'filters': {'category': ['reden', 'motivatie', 'doel']}
        }
    
    # HOW vragen
    if any(word in question_lower for word in ['hoe', 'how', 'methode', 'manier']):
        return {
            'w_type': 'HOW',
            'priority': ['processen', 'instructies'],
            'filters': {'category': ['proces', 'methode', 'instructie']}
        }
    
    # Default: context-based
    return {
        'w_type': 'CONTEXT',
        'priority': ['persoonlijk_dossier', 'knowledge_base'],
        'filters': {}
    }
```

---

### **Stap 3: Context-Aware Response**

```python
async def answer_question(user_question, user_id):
    """
    Beantwoord vraag met W-type disambiguation
    """
    
    # 1. Analyseer vraag
    query_context = analyze_query(user_question)
    w_type = query_context['w_type']
    
    # 2. Extract entities (bijv. "Lotus")
    entities = extract_entities(user_question)
    
    # 3. Search met priority
    results = []
    for entity in entities:
        for source in query_context['priority']:
            if source == 'persoonlijk_dossier':
                # Check user profile first
                user = get_user_profile(user_id)
                if entity.lower() in str(user.get('dochter', '')).lower():
                    results.append({
                        'source': 'persoonlijk_dossier',
                        'type': 'WHO',
                        'entity': user.get('dochter'),
                        'relation': 'dochter',
                        'gradatie': 1,
                        'confidence': 1.0
                    })
            
            elif source == 'knowledge_base':
                # Check knowledge cards
                cards = search_knowledge(entity, filters=query_context['filters'])
                results.extend(cards)
    
    # 4. Rank results
    ranked = rank_by_relevance(results, w_type, user_id)
    
    # 5. Generate response
    if ranked:
        best_match = ranked[0]
        
        if best_match['type'] == 'WHO':
            return f"{best_match['entity']} is {best_match['relation']} van {user.naam}. (Gradatie {best_match['gradatie']})"
        
        elif best_match['type'] == 'WHAT':
            return f"{entity} is {best_match['definition']}. (Bron: {best_match['source']})"
    
    return "Ik heb geen info over dit onderwerp."
```

---

## 🎬 VOORBEELDEN

### **Voorbeeld 1: WIE vraag**

```
User: "Wie is Lotus?"

Query Analysis:
  - W-type: WHO
  - Priority: [persoonlijk_dossier, users, familie]

Search:
  1. Persoonlijk dossier → MATCH!
     - user-001.dochter = "Lotus"
     - Gradatie: 1 (familie)
  
  2. Knowledge base → Skip (niet relevant voor WHO)

Response:
  "Lotus is je dochter, Lotus Spakman. (Gradatie 1 - familie)"
```

### **Voorbeeld 2: WAT vraag**

```
User: "Wat is Lotus?"

Query Analysis:
  - W-type: WHAT
  - Priority: [knowledge_base, concepts]

Search:
  1. Persoonlijk dossier → Skip (WHAT vraag, niet WHO)
  
  2. Knowledge base → MATCHES:
     a. Lotus (koekje) - Gradatie 4
     b. Lotusbloem (plant) - Gradatie 4
     c. Lotus (auto) - Gradatie 4

Response:
  "Lotus heeft meerdere betekenissen:
   - Lotus koekjes (Biscoff karamel koekje)
   - Lotusbloem (waterplant, symbool van zuiverheid)
   - Lotus (Brits automerk, sportwagens)
   
   Welke bedoel je?"
```

### **Voorbeeld 3: Context-aware**

```
User: "Vertel over Lotus" (GEEN W-woord)

Query Analysis:
  - W-type: CONTEXT
  - Priority: [persoonlijk_dossier, knowledge_base]

Search:
  1. Persoonlijk dossier → MATCH! (hoogste gradatie)
     - Lotus = dochter
     - Gradatie: 1
  
  2. Knowledge base → 3 matches
     - Gradatie: 4

Ranking (gradatie 1 > gradatie 4):
  → Persoonlijk dossier wint!

Response:
  "Lotus is je dochter. Wil je ook weten over de andere betekenissen? 
   (Lotus koekjes, lotusbloem, of Lotus auto's?)"
```

---

## 📊 VOORDELEN

### **1. Context-Aware:**
```
"Wie is Lotus?" → Persoonlijk (dochter)
"Wat is Lotus?" → Kennis (koekje/bloem/auto)
```

### **2. Gradatie als Priority:**
```
Gradatie 1 (familie) > Gradatie 4 (algemene kennis)
→ Persoonlijke info eerst!
```

### **3. Duidelijke Disambiguation:**
```
Als meerdere matches:
  → Vraag welke bedoeld wordt
  → Toon opties met context
```

### **4. Leerbaar:**
```
User kiest optie
  → Spark onthoudt voorkeur
  → Next time: direct juiste antwoord
```

---

## 🛠️ IMPLEMENTATIE PLAN

### **Fase 1: Metadata Toevoegen (1 uur)**
- Script: Voeg `w_type` toe aan alle kaarten
- Lotus dochter: `w_type: "WHO"`
- Lotus koekje/bloem/auto: `w_type: "WHAT"`

### **Fase 2: Query Analyse (2 uur)**
- Functie: `analyze_query()` 
- Detect W-woorden in vraag
- Return priority + filters

### **Fase 3: Search & Rank (2 uur)**
- Search met W-type filter
- Rank op: gradatie + relevance + source
- Persoonlijk dossier > Knowledge base

### **Fase 4: Response Generator (1 uur)**
- Template per W-type
- Disambiguation bij meerdere matches
- Leer van user keuzes

### **Fase 5: Testing (1 uur)**
- Test alle W-types
- Test edge cases
- User feedback

---

## 🎯 RESULTAAT

### **VOOR:**
```
User: "Vertel over Lotus"
Spark: "Lotus is een voornaam die..." (random knowledge)
  → Mist persoonlijke context!
```

### **NA:**
```
User: "Wie is Lotus?"
Spark: "Lotus is je dochter, Lotus Spakman. Ze is vernoemd naar de lotusbloem."
  → Persoonlijk + context!

User: "Wat is Lotus?"
Spark: "Lotus heeft meerdere betekenissen:
        - Lotus koekjes (Biscoff)
        - Lotusbloem (waterplant)
        - Lotus (automerk)
        Welke bedoel je?"
  → Duidelijke opties!
```

---

## 💎 CONCLUSIE

**Willem's inzicht is goud:**

> "De W in de vraag bepaalt het antwoord"

**Dit systeem:**
- ✅ Gebruikt 5W's voor disambiguation
- ✅ Persoonlijk dossier > Knowledge base
- ✅ Gradatie als priority
- ✅ Context-aware responses
- ✅ Leerbaar over tijd

**Next step:**
Wil je dat ik dit implementeer? Of eerst prototype testen?

---

💚🐺 **ROAR** - Context is alles!

---

_Gedocumenteerd: 15 maart 2026_  
_Door: E1 Agent_  
_Bron: Willem's 5W inzicht_  
_Voor: Spark Context-Aware System_
