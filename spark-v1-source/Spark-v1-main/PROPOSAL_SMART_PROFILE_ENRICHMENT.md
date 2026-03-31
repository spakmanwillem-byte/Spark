# Voorstel: Smart Profile Enrichment System

**Datum:** 11 maart 2026  
**Status:** Concept voorstel  
**Prioriteit:** Medium-High  

---

## 🎯 Doel

Uitgebreide gebruikersprofielen die:
1. **Rijkere persoonlijke data** bevatten (naam, contact, locatie, hobbies, werk)
2. **Automatisch worden aangevuld** uit gesprekken via AI (Content Engine)
3. **Spark helpen** een betere relatie op te bouwen door context te onthouden

---

## 📋 Huidige Situatie

**Bestaande profielvelden:**
```json
{
  "id": "user-001",
  "naam": "Willem",
  "volledige_naam": "Willem Spakman",
  "sleutelwoord": "***",
  "gradatie": 1,
  "rol": "admin",
  "relatie_tot_willem": "Zelf",
  "persoonlijke_info": {},  // ← LEEG
  "profile": {}              // ← BEPERKT
}
```

**Wat ontbreekt:**
- Voornaam / Achternaam (apart)
- Adres + Postcode + Plaats
- Email + Telefoonnummer
- Geboortedatum
- Hobbies / Interesses
- Werk / Beroep
- Belangrijke data (verjaardag partner, kinderen, etc.)

---

## 🚀 Voorgestelde Oplossing

### 1. **Uitgebreide Profielstructuur**

```json
{
  "id": "user-001",
  "naam": "Willem",
  
  // NIEUWE SECTIE: Persoonlijke Gegevens
  "personal_info": {
    "voornaam": "Willem",
    "achternaam": "Spakman",
    "geboortedatum": "1990-05-15",
    "geslacht": "man",
    
    "contact": {
      "email": "willem@example.com",
      "telefoon": "+31612345678",
      "secondary_email": null,
      "secondary_phone": null
    },
    
    "adres": {
      "straat": "Hoofdstraat",
      "huisnummer": "123",
      "postcode": "1234AB",
      "plaats": "Amsterdam",
      "land": "Nederland"
    },
    
    "werk": {
      "beroep": "Software Developer",
      "bedrijf": "TechCorp",
      "sector": "Technology",
      "sinds": "2018-01-01"
    },
    
    "interesses": {
      "hobbies": ["programmeren", "gaming", "lezen"],
      "sporten": ["voetbal", "hardlopen"],
      "muziek_genres": ["electronic", "rock"],
      "favoriete_boeken": [],
      "favoriete_films": []
    },
    
    "relaties": {
      "partner": {
        "naam": "Anna",
        "sinds": "2015-03-20"
      },
      "kinderen": [],
      "huisdieren": [
        {"naam": "Max", "type": "hond", "ras": "Labrador"}
      ]
    },
    
    "belangrijke_data": {
      "verjaardag_partner": "1992-08-10",
      "trouwdag": null,
      "custom": []
    }
  },
  
  // NIEUWE SECTIE: Auto-extracted info (wacht op bevestiging)
  "pending_profile_updates": [
    {
      "id": "upd_001",
      "field": "contact.email",
      "value": "willem.new@example.com",
      "extracted_from": "Conversation on 2026-03-11",
      "message": "Mijn nieuwe email is willem.new@example.com",
      "confidence": 0.95,
      "detected_at": "2026-03-11T20:30:00Z",
      "status": "pending"  // pending | approved | rejected
    }
  ],
  
  // Bestaande velden blijven intact
  "gradatie": 1,
  "rol": "admin",
  "sleutelwoord": "***",
  // ... rest blijft hetzelfde
}
```

---

## 🧠 Smart Extraction Systeem

### Hoe werkt het?

**Stap 1: Content Engine detecteert entities**
```python
# In Content Engine (keyword_analyzer of nieuwe entity_extractor)
entities = {
  "email": ["willem@example.com"],
  "phone": ["+31612345678"],
  "location": ["Amsterdam"],
  "organization": ["TechCorp"],
  "hobby": ["gaming", "programmeren"],
  "date": ["15 mei 1990"]
}
```

**Stap 2: Context Layer bepaalt relevantie**
```python
# Context Layer beslist: is dit persoonlijke info van de gebruiker?
if context.is_self_reference:  # "Mijn email is..." vs "Email van mijn vriend is..."
    profile_update = {
        "field": "contact.email",
        "value": "willem@example.com",
        "confidence": 0.95
    }
```

**Stap 3: Pending updates opslaan**
```python
# Opslaan in pending_profile_updates (niet direct toepassen!)
user["pending_profile_updates"].append(profile_update)
```

**Stap 4: Gebruiker/Admin goedkeuring**
- Admin panel toont pending updates
- Gebruiker kan approve/reject
- Bij approve: veld wordt bijgewerkt, pending verwijderd

---

## 🎨 UI/UX Voorstellen

### Admin Panel - Profielen Tab

**Sectie 1: Profiel Overzicht**
```
┌─────────────────────────────────────────────┐
│ 👤 Willem Spakman                           │
│                                             │
│ 📧 Email:     willem@example.com           │
│ 📱 Telefoon:  +31612345678                 │
│ 📍 Locatie:   Amsterdam, Nederland          │
│ 💼 Werk:      Software Developer @ TechCorp│
│ 🎮 Hobbies:   gaming, programmeren, lezen  │
│                                             │
│ [Bewerk Profiel]                           │
└─────────────────────────────────────────────┘
```

**Sectie 2: Pending Updates (nieuw!)**
```
┌─────────────────────────────────────────────┐
│ 🔔 Voorgestelde Updates (3)                 │
│                                             │
│ 1. Email gedetecteerd:                     │
│    "willem.new@example.com"                │
│    Uit: "Mijn nieuwe email is..."         │
│    [✓ Goedkeuren] [✗ Afwijzen]            │
│                                             │
│ 2. Hobby gedetecteerd:                     │
│    "schaken"                               │
│    Uit: "Ik ben gisteren begonnen..."    │
│    [✓ Goedkeuren] [✗ Afwijzen]            │
│                                             │
│ 3. Werkplek gedetecteerd:                  │
│    "NewTech BV"                            │
│    Uit: "Ik werk nu bij NewTech BV"       │
│    [✓ Goedkeuren] [✗ Afwijzen]            │
└─────────────────────────────────────────────┘
```

**Sectie 3: Handmatig Invullen**
- Formulier met alle velden (optional)
- Admin kan handmatig info toevoegen

---

## 🔐 Privacy & Consent

**Belangrijk:**

1. **Opt-in systeem**
   - Gebruiker moet toestemming geven voor auto-extraction
   - Default: UIT (privacy-first)

2. **Transparantie**
   - Gebruiker ziet altijd wat wordt opgeslagen
   - Kan pending updates zien en goedkeuren/afwijzen

3. **Data minimalisatie**
   - Alleen relevante, door gebruiker gedeelde info
   - Geen scraping van externe bronnen

4. **Gebruikerscontrole**
   - Kan velden verwijderen
   - Kan auto-extraction uitschakelen
   - Kan volledige profiel exporteren/verwijderen

**Consent Flow:**
```
Eerste keer profiel-info detectie:
┌─────────────────────────────────────────────┐
│ 🤖 Spark wil je profiel aanvullen          │
│                                             │
│ Ik heb gemerkt dat je je email deelde.    │
│ Mag ik dit soort info automatisch          │
│ verzamelen om je beter te helpen?         │
│                                             │
│ Je kunt dit later altijd wijzigen.        │
│                                             │
│ [✓ Ja, dat is prima] [✗ Nee, liever niet] │
└─────────────────────────────────────────────┘
```

---

## 🛠️ Implementatie Plan

### **Fase 1: Data Structuur (1-2 uur)**
- ✅ Uitbreiden user schema in `system/users.json`
- ✅ Migration script voor bestaande users
- ✅ Update DataManager / AuthService

### **Fase 2: Entity Extraction Service (3-4 uur)**
- 📝 Nieuwe service: `ProfileEnrichmentService`
- 📝 Entity extractors:
  - Email detector (regex + validatie)
  - Telefoon detector (NL formaten)
  - Locatie detector (steden, adressen)
  - Datum detector (verjaardagen, belangrijke data)
  - Hobby detector (uit keywords + context)
  - Werk detector (bedrijven, functies)
- 📝 Context-aware filtering (onderscheid "mijn email" vs "zijn email")

### **Fase 3: Integration met Content Engine (2-3 uur)**
- 📝 Uitbreiden `ContentAnalysis` met `extracted_entities`
- 📝 Hook in `spark_brain.py` om entities te verwerken
- 📝 Pending updates opslaan in user profile

### **Fase 4: Admin UI (3-4 uur)**
- 📝 Profiel tab uitbreiden met nieuwe velden
- 📝 Pending updates sectie (approve/reject UI)
- 📝 Handmatig invul formulier
- 📝 Privacy settings (auto-extraction aan/uit)

### **Fase 5: API Endpoints (1-2 uur)**
- 📝 `GET /api/profile/:userId` - Volledig profiel
- 📝 `GET /api/profile/:userId/pending` - Pending updates
- 📝 `POST /api/profile/:userId/approve/:updateId` - Goedkeuren
- 📝 `DELETE /api/profile/:userId/reject/:updateId` - Afwijzen
- 📝 `PUT /api/profile/:userId` - Handmatig bijwerken

### **Fase 6: Testing & Privacy (2-3 uur)**
- 📝 Unit tests voor entity extraction
- 📝 Integration tests voor approval flow
- 📝 Privacy consent flow testen
- 📝 Edge cases (foute emails, dubbelingen)

**Totale geschatte tijd: 12-18 uur**  
**Aanbevolen: 2-3 dagen gefaseerde implementatie**

---

## ✅ Voordelen

1. **Betere Relatie**
   - Spark kan verjaardagen onthouden
   - Kan vragen stellen over werk/hobbies
   - Persoonlijkere gesprekken

2. **Context Behoud**
   - "Hoe gaat het met je project bij TechCorp?" (onthoudt werkplek)
   - "Heb je nog geschaakt deze week?" (onthoudt hobby)
   - "Groeten aan Anna!" (onthoudt partner naam)

3. **Minder Herhaling**
   - Gebruiker hoeft niet elke keer opnieuw info te delen
   - Spark "kent" de gebruiker al

4. **AI-gedreven**
   - Gebruikt bestaande Content Engine (geen extra LLM calls)
   - Automatisch maar met controle (pending approval)

---

## ⚠️ Risico's & Mitigatie

| Risico | Impact | Mitigatie |
|--------|--------|-----------|
| **Privacy concerns** | Hoog | Opt-in, transparantie, user control |
| **Foute extractie** | Medium | Confidence scores, pending approval |
| **Te veel notificaties** | Medium | Batch updates, filters op relevantie |
| **Data complexiteit** | Medium | Goede schema design, validatie |
| **Performance** | Laag | Entity extraction is lightweight (<5ms) |

---

## 🤔 Is dit mogelijk?

**Ja, absoluut!** 

**Technisch:**
- ✅ Content Engine kan al entities detecteren (we gebruiken NLPService)
- ✅ Context Layer kan relevantie bepalen
- ✅ User schema is flexibel (JSON)
- ✅ Admin UI is al aanwezig
- ✅ Performance impact is minimaal

**Praktisch:**
- 🟡 Vereist 12-18 uur werk (2-3 dagen)
- 🟡 Privacy moet goed worden aangepakt
- 🟡 UI moet intuïtief zijn (approve/reject flow)

**Aanbeveling:**
✅ **JA, dit is een waardevolle feature** die goed past bij Spark's missie om een persoonlijke AI assistent te zijn.

---

## 🎯 Volgende Stappen

**Optie A: Start direct (na user goedkeuring)**
1. Implementeer Fase 1 (data structuur) 
2. Bouw basic entity extraction
3. Test met dummy data
4. Itereer op basis van feedback

**Optie B: Toevoegen aan roadmap**
- Plaats in v3.3 of v4.0 (na Emotional Intelligence)
- Geef het tijd om te rijpen
- Combineer met andere profile features

**Optie C: MVP eerst**
- Start met handmatige invul (geen auto-extraction)
- Test of de uitgebreide velden nuttig zijn
- Voeg later auto-extraction toe

---

## 📊 User Value vs Effort

```
High Value ┃     🎯 Smart Profile 
          ┃        Enrichment
          ┃
          ┃
Medium    ┃
          ┃
          ┃
Low       ┃
          ┗━━━━━━━━━━━━━━━━━━━━
            Low    Medium    High
                    Effort
```

**Conclusie:** Medium-High effort, High value = **WORTH IT** 💎

---

## 🙋 Vragen voor Willem

1. **Privacy:** Ben je comfortabel met auto-extraction uit gesprekken? (Met opt-in consent natuurlijk)

2. **Scope:** Welke velden zijn het belangrijkst?
   - Must-have: Naam, Email, Telefoon, Plaats?
   - Nice-to-have: Hobbies, Werk, Relaties?

3. **Timing:** Wanneer implementeren?
   - Nu (na v3.1 validation)
   - Na v3.2 (Emotional Intelligence)
   - Later (v4.0+)

4. **Approach:** 
   - Start met handmatig invullen (simpel, 4-6 uur)
   - Of direct met smart extraction (compleet, 12-18 uur)

5. **Testing:** Mag dit getest worden met jouw eigen profiel? (Admin role)

---

**Wachtend op je feedback! 🚀**
