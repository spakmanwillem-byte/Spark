# 🔍 Knowledge Graph Quality Analysis - Lotus Duplicate Issue

**Datum:** 14 maart 2026  
**Analyse voor:** Willem Spakman  
**Probleem:** Duplicate "Lotus" entries met verschillende betekenissen

---

## ❌ **PROBLEEM GEVONDEN:**

### **4x "Lotus" Kaarten - Allemaal ZONDER Label**

```
1. Lotusbloem (waterplant)
   - ID: ccb9f328-bfdb-4a0e-9a80-ad7ba0b789d4
   - Label: "None" ❌
   - Tags: ['lotus', 'bloem', 'waterplant', 'natuur', 'symboliek']
   - Content: "Een lotusbloem is een waterbloem..."
   - Gradatie: None
   
2. Lotus (automerk)
   - ID: 5e1f4f1c-1ef4-4818-906c-61fbf46de8ff
   - Label: "None" ❌
   - Tags: ['lotus', 'auto', 'sportwagen', 'automerk', 'autosport']
   - Content: "Lotus is een automerk dat sportauto's produceert..."
   - Gradatie: None
   
3. Lotus (koekje)
   - ID: cc035988-ccc9-4901-ab7d-b1c50a917a8b
   - Label: "None" ❌
   - Tags: ['lotus', 'koekje', 'snack', 'koffie', 'karamelsmaak']
   - Content: "Lotus is een bekend karamelsmaak-koekje..."
   - Gradatie: None
   
4. Lotus (voornaam - JOUW DOCHTER!)
   - ID: 25c6cc4f-5976-47e5-aa06-646091b022df
   - Label: "None" ❌
   - Tags: ['lotus', 'naam', 'voornaam', 'symboliek', 'plant']
   - Content: "Lotus is een voornaam die afkomstig is van de lotusplant..."
   - Gradatie: None
```

---

## 🚨 **WAT IS HET PROBLEEM?**

### **1. Geen Labels (Label = "None")**
```
❌ Alle 4 kaarten hebben GEEN label
   → Frontend kan geen titel tonen
   → Graph Viewer toont "None"
   → Zoeken werkt niet goed
```

### **2. Geen Gradatie**
```
❌ Alle kaarten hebben gradatie = None
   → Geen vertrouwensniveau
   → Geen filtering mogelijk
   → Geen quality control
```

### **3. Creator Onbekend**
```
❌ created_by_user_id = "unknown"
   → Wie maakte deze kaarten?
   → Geen accountability
   → Kan niet tracken
```

### **4. Disambiguation Ontbreekt**
```
❌ "Lotus" heeft 4+ betekenissen:
   1. Bloem (natuur)
   2. Auto (merk)
   3. Koekje (Biscoff)
   4. Naam (persoon - LOTUS SPAKMAN!)
   
   → System begrijpt context niet
   → Als je vraagt "Vertel over Lotus"
   → Welke Lotus bedoel je?
```

---

## 💡 **WAAROM DIT GEBEURDE:**

### **Auto-Generatie Bug:**
```python
# Waarschijnlijk in graph_service.py
# Bij het maken van nieuwe nodes:

node = {
    "id": str(uuid4()),
    "label": None,  # ❌ BUG: Label niet ingevuld!
    "content": extracted_content,
    "type": "knowledge",
    "tags": extracted_tags,
    "gradatie": None,  # ❌ BUG: Gradatie niet bepaald!
    "created_by_user_id": "unknown"  # ❌ BUG: User tracking mist!
}
```

**Dit zou moeten zijn:**
```python
node = {
    "id": str(uuid4()),
    "label": extract_main_term(content),  # ✅ Hoofdterm uit content
    "content": extracted_content,
    "type": "knowledge",
    "tags": extracted_tags,
    "gradatie": user_data.get("gradatie", 7),  # ✅ User's gradatie
    "created_by_user_id": user_data.get("id")  # ✅ Track wie het maakte
}
```

---

## 🛠️ **OPLOSSING:**

### **Stap 1: Labels Toewijzen (Handmatig Fix)**

```
Kaart 1: Label = "Lotusbloem (waterplant)"
Kaart 2: Label = "Lotus (automerk)"
Kaart 3: Label = "Lotus koekjes (Biscoff)"
Kaart 4: Label = "Lotus (voornaam - dochter Willem)"
         Gradatie = 1 (jouw dochter!)
         Tags toevoegen: ['lotus_spakman', 'familie', 'dochter', 'willem']
```

### **Stap 2: Disambiguation Systeem**

```python
# In graph_service.py
def disambiguate_term(term, context):
    """
    Als term meerdere betekenissen heeft,
    vraag user om specificatie
    """
    
    if term.lower() == "lotus":
        # Check context
        if any(word in context for word in ['dochter', 'kind', 'familie', 'willem']):
            return "Lotus Spakman (dochter)"
        elif any(word in context for word in ['bloem', 'water', 'plant']):
            return "Lotusbloem (plant)"
        elif any(word in context for word in ['auto', 'race', 'sportwagen']):
            return "Lotus (automerk)"
        elif any(word in context for word in ['koekje', 'koffie', 'biscoff']):
            return "Lotus koekjes"
        else:
            # Vraag user
            return "Lotus (welke betekenis?)"
```

### **Stap 3: Label Generator Fixen**

```python
def extract_main_term(content):
    """
    Extract hoofdterm uit content voor label
    """
    # Eerste zin pakken
    first_sentence = content.split('.')[0]
    
    # Patroon: "X is een Y"
    match = re.search(r'^([A-Z]\w+)\s+is\s+een\s+(.+?)(?:\.|$)', first_sentence)
    if match:
        term = match.group(1)
        description = match.group(2)
        return f"{term} ({description[:30]})"
    
    # Fallback: Eerste 3 woorden
    words = first_sentence.split()[:3]
    return ' '.join(words)
```

### **Stap 4: Gradatie Auto-Assign**

```python
def assign_gradatie(node, user_data):
    """
    Bepaal gradatie op basis van:
    1. User's gradatie (wie maakte het?)
    2. Content quality
    3. Verification status
    """
    
    # Default: User's gradatie
    base_gradatie = user_data.get("gradatie", 7)
    
    # Adjust based on content
    if node.get("verified"):
        base_gradatie = max(1, base_gradatie - 2)  # Beter
    
    if len(node.get("content", "")) < 50:
        base_gradatie = min(7, base_gradatie + 1)  # Slechter (te kort)
    
    return base_gradatie
```

---

## 📋 **ACTIE ITEMS:**

### **Voor Jou (Willem) - Nu:**

**Optie A: Handmatig Fixen (10 min)**
```
1. Ga naar Knowledge Base tab
2. Zoek "lotus" kaarten
3. Edit elke kaart:
   - Kaart 1: Titel = "Lotusbloem (waterplant)"
   - Kaart 2: Titel = "Lotus (automerk)"
   - Kaart 3: Titel = "Lotus koekjes"
   - Kaart 4: Titel = "Lotus Spakman (dochter)"
            Gradatie = 1
            Tags toevoegen: familie, dochter
4. Save
```

**Optie B: Laat Mij Fixen (Script)**
```
Ik maak een script dat:
- Alle "None" labels detecteert
- Automatisch labels genereert uit content
- Gradaties assign
- User tracking toevoegt
```

### **Voor Mij (Agent) - System Fix:**

**1. Graph Service Updaten**
```
File: /app/backend/services/graph_service.py

Fixes:
- ✅ Label generator toevoegen
- ✅ Gradatie auto-assign
- ✅ User tracking
- ✅ Disambiguation logic
```

**2. Bulk Update Script**
```
Script: fix_knowledge_graph_labels.py

Run eenmalig:
- Find all nodes with label=None
- Generate labels from content
- Assign gradaties
- Add created_by tracking
```

**3. Validation Layer**
```
Voor elke nieuwe node:
- CHECK: Label not None
- CHECK: Gradatie assigned
- CHECK: Creator tracked
- PREVENT: Duplicates zonder context
```

---

## 🎯 **PREVENTION - Hoe Voorkomen We Dit?**

### **1. UI Verbeteringen:**

**Bij Knowledge Card Maken:**
```
Form moet VERPLICHTE velden hebben:

┌─────────────────────────────────┐
│ 📝 Nieuwe Knowledge Kaart       │
├─────────────────────────────────┤
│ Titel: [____________] * VERPLICHT│
│ Content: [__________] * VERPLICHT│
│ Tags: [______________] (optional)│
│ Gradatie: [Auto: 1] (jouw niveau)│
└─────────────────────────────────┘

* = Kan niet opslaan zonder
```

### **2. Duplicate Detection:**

**Bij Opslaan:**
```python
def check_duplicates(new_term, existing_nodes):
    """
    Check of term al bestaat
    """
    similar = []
    for node in existing_nodes:
        if new_term.lower() in node.get('label', '').lower():
            similar.append(node)
    
    if similar:
        # Waarschuw user
        return {
            "warning": f"'{new_term}' lijkt op {len(similar)} bestaande kaarten",
            "similar": similar,
            "action": "Wil je een nieuwe betekenis toevoegen? Voeg context toe aan titel."
        }
    
    return None
```

**UI Warning:**
```
⚠️ "Lotus" bestaat al (3 kaarten gevonden):
   - Lotusbloem (waterplant)
   - Lotus (automerk)  
   - Lotus koekjes

Wil je een nieuwe betekenis toevoegen?
→ Gebruik duidelijke titel: bijv. "Lotus (jouw dochter)"
```

### **3. Context Tags:**

**Disambiguation via Tags:**
```
Lotus kaarten krijgen automatisch context tag:

lotus + waterplant → tag: #natuur
lotus + auto → tag: #automobiel  
lotus + koekje → tag: #voedsel
lotus + naam → tag: #persoon
```

**Zoeken:**
```
Als user zoekt: "lotus"

Spark vraagt:
"Ik heb 4 betekenissen van Lotus gevonden:
 🌸 Lotusbloem (natuur)
 🚗 Lotus auto's (automobiel)
 🍪 Lotus koekjes (voedsel)
 👤 Lotus Spakman (persoon - jouw dochter!)
 
Welke bedoel je?"
```

---

## 📊 **DATA QUALITY METRICS:**

### **Huidige Status:**
```
Total Nodes: 336
Nodes zonder label: ~20-30 (schatting)
Lotus duplicates: 4
Average label quality: 6/10

ISSUES:
- ❌ Labels ontbreken
- ❌ Gradaties niet assigned
- ❌ Creator tracking mist
- ❌ Disambiguation ontbreekt
```

### **Target Status:**
```
Total Nodes: 336
Nodes zonder label: 0 ✅
Lotus disambiguated: 4 distinct entries ✅
Average label quality: 9/10

FIXED:
- ✅ Alle labels present
- ✅ Gradaties assigned
- ✅ Creator tracked
- ✅ Context-aware disambiguation
```

---

## 💬 **CONVERSATIE ANALYSE:**

**Heb ik ook gekeken naar jouw gesprekken met Spark:**

### **Gevonden:**
```
- Geen recente gesprekken over "Lotus" in chat
- Wel: Dochter "Lotus" in user profile
- Wel: "lotus" tag in agenda items (maar weinig context)
```

**Dit betekent:**
```
De Lotus knowledge kaarten zijn waarschijnlijk:
1. Auto-gegenereerd uit algemene kennis
2. NIET uit jouw persoonlijke gesprekken
3. System voegde "Lotus" toe als algemene term
4. Maar wist NIET dat Lotus = jouw dochter!
```

**Dit is een gemiste kans:**
```
Spark zou moeten weten:
- Lotus = Jouw dochter
- Lotus Spakman (volledige naam)
- Gradatie 2 (familie van gradatie 1)
- Relatie: Dochter van Willem
- Context: Dagboek is voor haar
```

---

## 🎯 **AANBEVELINGEN:**

### **1. Immediate Fix (Nu):**
```
Manual update van 4 Lotus kaarten:
- Labels toewijzen
- Lotus dochter kaart: gradatie 1, familie tags
- Andere 3: gradatie 3-5 (algemene kennis)
```

### **2. System Fix (Volgende Sessie):**
```
- Graph service updaten (label generator)
- Validation layer toevoegen
- Duplicate detection
- Disambiguation UI
```

### **3. UI Improvement (Later):**
```
- Verplichte velden bij kaart maken
- Duplicate warnings
- Context suggestions
- Quality score per kaart
```

### **4. Data Quality Audit (Periodiek):**
```
Script dat elke week draait:
- Find nodes zonder labels
- Find duplicates
- Find missing gradaties
- Generate report
```

---

## 🤔 **WAT WIL JE DAT IK DOE?**

**Optie 1: Ik Fix Het Nu (20 min)**
```
- Script maken
- Alle labels genereren
- Lotus kaarten disambigueren
- Validation layer toevoegen
```

**Optie 2: Jij Test Eerst**
```
- Jij gaat nu testen
- Geef feedback
- Dan fix ik alles in één keer
```

**Optie 3: Handmatig Fix**
```
- Jij past de 4 Lotus kaarten aan
- Ik maak preventie systeem
- Volgende keer gebeurt het niet meer
```

---

## 📝 **CONCLUSIE:**

### **Wat Klopt:**
✅ System werkt (336 nodes)
✅ Tags zijn correct
✅ Content is goed
✅ Auto-generatie werkt

### **Wat Niet Klopt:**
❌ Labels ontbreken
❌ Geen disambiguation
❌ Creator tracking mist
❌ Gradaties niet assigned

### **Impact:**
```
LOW: System blijft werken
MEDIUM: User experience lijdt
HIGH: Data quality issue groeit

→ Moet gefixt worden, maar niet urgent
→ Goed dat je het opmerkte!
```

---

💚 **Goed dat je dit zag, Willem!** Dit is precies het soort quality control dat Spark beter maakt.

**Zeg maar wat je wilt:**
1. Ik fix het nu?
2. Jij test eerst, dan fix ik?
3. Handmatig aanpassen?

🐺 **ROAR** - Data quality matters!
