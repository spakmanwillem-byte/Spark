# 📋 Roadmap Update: Contextueel Begrip Systeem

**Datum:** 10 maart 2026  
**Toegevoegd aan:** v2.0 - Spark Intelligence & Customization

---

## 🎯 Nieuw Roadmap Item

### **v2_001c: Contextueel Begrip - Multi-Betekenis Systeem**

**Prioriteit:** 🔴 Critical  
**Status:** Planned  
**Locatie:** v2.0 (tussen Knowledge Graph en 5 W's Framework)

---

## 📖 Concept Beschrijving

Spark moet meerdere betekenissen van hetzelfde woord kunnen herkennen op basis van context.

**Voorbeeld:**
- **"Aarde"** kan betekenen:
  1. Grond / bodem 🌱
  2. Planeet Aarde 🌍

---

## 🏗️ Implementatie Fasen

### **Fase 1: Context-Based Selection**
**Status:** Planned  
Spark probeert via conversatie-context automatisch het juiste concept te kiezen.

**Technisch:**
- Analyseer eerdere berichten in sessie
- Gebruik keywords en thema's om context te bepalen
- Selecteer meest waarschijnlijke betekenis

---

### **Fase 2: Disambiguation UI**
**Status:** Planned  
Bij twijfel toont Spark meerdere betekenissen voor de gebruiker.

**Voorbeeld:**
```
User: "Vertel over aarde"
Spark: "Ik ken twee betekenissen van 'aarde':
  1. Aarde (grond/bodem) - Voor planten
  2. Aarde (planeet) - Onze thuisplaneet
  
  Welke bedoel je?"
```

---

### **Fase 3: User Correction**
**Status:** Planned  
Gebruiker kan corrigeren binnen het gesprek.

**Voorbeeld:**
```
User: "Nee, niet die aarde"
Spark: "Ah, je bedoelt Aarde (planeet) dan?"
User: "Ja!"
Spark: [past selectie aan en onthoudt binnen sessie]
```

---

### **Fase 4: Context Memory & Ranking**
**Status:** Planned  
Spark onthoudt keuzes binnen gesprek + ranking op basis van context en feedback.

**Technisch:**
- Session-based memory: keuze-geschiedenis per gesprek
- Ranking algoritme: frequentie × context-match × feedback score
- Learning: populairste betekenis per context wordt default

---

### **Fase 5: Knowledge Kaarten & Relaties** 
**Status:** Vision  
Verbindingen tussen betekenissen visualiseren.

**Features:**
- Admin UI: netwerk visualisatie van concepten
- Relatie-types: "is_variant_van", "lijkt_op", "context_verschil"
- Training mode: admin kan correcte context-mappings bevestigen

---

## 🔧 Technische Requirements

### Database Schema Aanpassingen
```json
{
  "begrip": "Aarde",
  "begrip_type": "grond",  // NIEUW
  "begrip_variant": "aarde_grond",  // NIEUW
  "context_keywords": ["planten", "tuin", "groeien"],  // NIEUW
  "lagen": {...},
  "usage_by_context": {  // NIEUW
    "tuinieren": 15,
    "landbouw": 8,
    "algemeen": 3
  }
}
```

### Nieuwe Services
1. **`context_disambiguation_service.py`**
   - Analyseer context en selecteer betekenis
   - Bereken confidence scores

2. **`session_memory_service.py`**
   - Onthoud keuzes binnen sessie
   - Clear bij nieuwe sessie

3. **`concept_variant_service.py`**
   - Beheer meerdere betekenissen
   - CRUD voor varianten

### Frontend Components
1. **`DisambiguationPrompt.jsx`**
   - Toon meerdere betekenissen
   - Knoppen voor selectie

2. **`ConceptVariantEditor.jsx`** (Admin)
   - Beheer begrip varianten
   - Context keywords editor

---

## 🎯 Use Cases

### Use Case 1: Tuinieren Context
```
User: "Hoe maak ik de aarde vruchtbaarder?"
Context: [eerdere berichten over planten, groenten]
Spark: [selecteert automatisch "Aarde (grond)"]
Response: "Om de aarde vruchtbaarder te maken..."
```

### Use Case 2: Wetenschap Context
```
User: "Hoe groot is de aarde?"
Context: [eerdere berichten over planeten, ruimte]
Spark: [selecteert automatisch "Aarde (planeet)"]
Response: "De Aarde heeft een diameter van..."
```

### Use Case 3: Onzekere Context
```
User: "Wat weet je over aarde?"
Context: [geen relevante context]
Spark: "Ik ken twee betekenissen:
  1. 🌱 Aarde als grond/bodem
  2. 🌍 Aarde als planeet
  Welke wil je weten?"
```

---

## 📊 Relatie met Bestaande Features

### **Versterkt door:**
- ✅ **Knowledge Graph** (v2_001): Relaties tussen varianten
- ✅ **Context Engine** (v2_002d): Context-analyse
- ✅ **Disambiguation Flow** (v1_016): UI is al aanwezig voor lijst-selectie
- ✅ **Ranking System** (v1_5_001b): Feedback + usage tracking

### **Basis voor:**
- 🔮 **Adaptive Learning** (v2_007): Leren van correcties
- 🔮 **Meta-Learning** (v4_002): Begrip van begrip

---

## 🚀 Voordelen

1. **Nauwkeuriger antwoorden**
   - Minder miscommunicatie
   - Context-bewuste selectie

2. **Slimmer leren**
   - Spark leert welke betekenis in welke context
   - Automatische verbetering over tijd

3. **Beter UX**
   - Gebruiker kan altijd corrigeren
   - Transparante keuzes

4. **Schaalbaarheid**
   - Systematisch voor alle ambigue woorden
   - Admin kan varianten beheren

---

## 📝 Voorbeelden van Ambigue Concepten

- **Bank:** zitmeubel / financiële instelling
- **Muis:** dier / computer peripheral
- **Bal:** speelgoed / formeel feest
- **Slang:** dier / tuinslang
- **Veer:** vogelveer / metalen veer / veerdienst
- **Blad:** boom blad / papier blad / tijdschrift
- **Zegel:** postzegel / lakzegel / goedkeuring

---

## ⏭️ Volgende Stappen

**Wanneer implementeren?**
- Na v1.5 voltooiing (Feedback UI + Tag systeem)
- Voor v3.0 (Community features kunnen hiervan profiteren)

**Afhankelijkheden:**
- ✅ Disambiguation UI bestaat al (v1_016)
- ⏳ Context Engine V2 (v2_002d) moet eerst
- ⏳ Feedback systeem UI (v1_5_003) helpt met ranking

---

**Status:** 📋 Toegevoegd aan roadmap als v2_001c  
**Volgende:** Wacht op user verificatie van P0 (concept normalisatie)
