# KNOWLEDGE CARD ANALYSIS RAPPORT
**Datum:** 2026-03-16  
**Totaal Kaarten:** 859 active  
**Analysedoel:** Learning Module voorbereiding + Organisatie verbetering

---

## 📊 EXECUTIVE SUMMARY

### Belangrijkste Bevindingen:
- ✅ **99.1% kaarten zijn volledig** (alle 3 lagen ingevuld)
- 🎯 **78 kaarten geschikt** voor Learning Module (5⭐ importance + volledig)
- 📁 **30 grote thema clusters** gevonden (>= 3 kaarten per cluster)
- 🔗 **841 kaarten hebben connecties** met andere kaarten
- ❓ **9 expliciete triggers** gedetecteerd ("Wat weet jij over...")
- 🏷️ **1751 unieke tags** - veel ruimte voor clustering

### Aanbevelingen:
1. **Organisatie:** Implementeer folder/categorie systeem gebaseerd op top 30 tags
2. **Learning Module:** Start met top 78 learning candidates (5⭐ kaarten)
3. **Data Structuur:** Voeg placeholders toe voor bronnen, clusters, learning metadata
4. **Trigger Expansion:** Voeg meer "Wat weet jij over..." kaarten toe als learning exercises

---

## 1️⃣ TRIGGER ANALYSE (Learning Module Candidates)

### Huidige Triggers:
- **Directe vragen:** 4 kaarten (bv: "Wat weet jij over het lichaam")
- **Impliciete vragen:** 5 kaarten (eindigt met ?)
- **Definitie verzoeken:** 0 kaarten
- **Totaal:** 9 kaarten (1.0% van totaal)

### Observatie:
🔍 **Zeer weinig expliciete triggers** in huidige knowledge base. De meeste kaarten zijn statement-based ("Water", "Leven") in plaats van question-based ("Wat weet jij over water?").

### Aanbeveling Learning Module:
**Strategie A - Dual Format:**
- Behoud huidige statement kaarten als "Knowledge"
- Creëer automatisch "Wat weet jij over [begrip]?" variants als "Learning Triggers"
- Koppel trigger → knowledge card

**Strategie B - Metadata Toggle:**
- Voeg `learning_mode: true/false` toe aan elk card
- In learning mode: transformeer "Water" → "Wat weet jij over water?"
- Spark stelt vraag, gebruiker antwoordt, vergelijk met laag1/2/3

**Voorkeur:** Strategie B (cleaner, minder dubbele data)

---

## 2️⃣ RELATIES & CONNECTIES

### Top Connected Cards:
1. **Mollen** - 18 connecties (ster, leven, bodem, licht, regen)
2. **Bodem** - 16 connecties (organismen, leven, natuur, rond, insect)
3. **Mens** - 15 connecties (ster, leven, lopen, samenleving, groepen)

### 841 van 859 kaarten (97.9%) hebben concept overlap
Dit betekent: kaarten noemen elkaar in hun definities → sterke knowledge graph.

### Use Case voor Learning Module:
**Learning Paths** kunnen gemaakt worden door connected cards te volgen:
- Start: "Water" → mentions "leven", "organismen", "natuur"
- Next: Gebruiker leert over "Leven" → mentions "mens", "dier", "plant"
- Deep dive: "Mens" → mentions "samenleving", "bewustzijn"

---

## 3️⃣ THEMA CLUSTERING (Folder Structuur Voorstel)

### Top 15 Clusters (voor folder organisatie):

| Cluster | Size | Voorbeelden |
|---------|------|-------------|
| 🌿 Natuur | 68 | Peer, Seizoen, Leven, Organismen, Plant |
| 💬 Communicatie | 38 | Geluid, Taal, Empathie, Samenwerking |
| ⚡ Energie | 34 | Energie, Accu, Batterij, Eten, Slapen |
| 🐾 Dier | 33 | Konijn, Dier, Insect, Vogel, Slang |
| 🌐 Netwerk | 33 | Graph, Node, Edges, Verbinding, Netwerk |
| 🔧 Gereedschap | 29 | Wapen, Spijker, Tool, Bestek, Gereedschap |
| 🍎 Voedsel | 26 | Fruit, Koffie, Thee, Koken, Eten |
| 😊 Gedrag | 25 | Regels, Respect, Motivatie, Loyaliteit |
| 🔒 Beveiliging | 25 | Security, Hacking tools, Backdoors, Firewalls |
| 🌱 Plant | 24 | Fruit, Bloem, Boom, Plant, Groei |
| 💪 Lichaam | 24 | Ademen, Rust, Hoofd, Lichaam, Gezondheid |
| 📈 Ontwikkeling | 24 | Groei, Leren, Innovatie, Creëren |
| 🧠 Kennis | 24 | Denken, Wijsheid, Taal, Begrip, Leren |
| 💖 Emotie | 24 | Blij, Bang, Bedroefd, Boos, Emotie |
| 🏗️ Bouw | 24 | Spijker, Baksteen, Blauwdruk, Constructie |

### Voorstel Folder Structuur:
```
📁 Natuur & Leven (68 + 33 + 24 + 24 = 149 kaarten)
   └─ Natuur, Dier, Plant, Lichaam

📁 Technologie & Tools (33 + 29 + 25 = 87 kaarten)
   └─ Netwerk, Gereedschap, Beveiliging

📁 Menselijk & Sociaal (38 + 26 + 25 + 24 + 24 = 137 kaarten)
   └─ Communicatie, Voedsel, Gedrag, Emotie, Kennis

📁 Energie & Fysica (34 + 24 = 58 kaarten)
   └─ Energie, Ontwikkeling

📁 Bouw & Creatie (24 kaarten)
   └─ Bouw

📁 Overig (428 kaarten)
   └─ Kaarten met kleine/unieke tags
```

---

## 4️⃣ BELANGRIJKHEID ANALYSE (Sterren ⭐)

### Distributie:
- ⭐ 0-1: 8 kaarten (0.9%) - Onbeoordeeld
- ⭐ 2: 114 kaarten (13.3%) - Laag
- ⭐ 3: 432 kaarten (50.3%) - **Gemiddeld (grootste groep)**
- ⭐ 4: 227 kaarten (26.4%) - Belangrijk
- ⭐ 5: 78 kaarten (9.1%) - Zeer belangrijk
- ⭐ 6-10: 0 kaarten (0%) - Expert niveau (nog niet gebruikt)

### Observatie:
🔍 **Sterren 6-10 worden niet gebruikt.** Dit betekent dat de 1-10 schaal eigenlijk een 1-5 schaal is.

### Aanbeveling:
**Optie A:** Blijf 1-5 gebruiken (huidige gedrag)
**Optie B:** Gebruik 6-10 voor expert/advanced knowledge in de toekomst
**Optie C:** Rescale naar 1-10 (× 2)

---

## 5️⃣ LAGEN COMPLETENESS

### Status:
- ✅ **Laag 1 (Basis):** 851 kaarten (99.1%)
- ✅ **Laag 2 (Dieper):** 851 kaarten (99.1%)
- ✅ **Laag 3 (Expert):** 851 kaarten (99.1%)
- ✅ **Alle 3 lagen:** 851 kaarten (99.1%)
- ❌ **Geen lagen:** 8 kaarten (0.9%)

### Bevinding:
🎉 **Uitstekende kwaliteit!** Vrijwel alle kaarten zijn volledig uitgewerkt met 3 lagen van diepte.

### Use Case Learning Module:
- **Laag 1:** Beginners vraag (basis begrip)
- **Laag 2:** Intermediate vraag (dieper begrip)
- **Laag 3:** Expert vraag (advanced toepassing)

---

## 6️⃣ LEARNING MODULE - TOP 78 CANDIDATES

### Selectie Criteria:
- ⭐ 5 sterren (zeer belangrijk)
- Volledig (alle 3 lagen)
- Goede definities

### Top 20:
1. Water 💧
2. Leven 🌱
3. Bewustzijn 🧠
4. Heelal 🌌
5. Dier 🐾
6. Mens 👤
7. Eten 🍽️
8. Slapen 😴
9. Denken 💭
10. Plant 🌿
11. Voedsel 🥘
12. Ademen 💨
13. Warmte 🔥
14. Aarde (planeet) 🌍
15. Lucht 🌤️
16. Tijd ⏰
17. Ruimte 🚀
18. Materie ⚛️
19. Kracht 💪
20. Zwaartekracht 🌑

### Thema's in Top 78:
- **Fundamentals:** Water, Leven, Heelal, Aarde, Lucht
- **Biologie:** Dier, Mens, Plant, Voedsel, Ademen
- **Fysica:** Warmte, Tijd, Ruimte, Materie, Kracht, Zwaartekracht
- **Menselijk:** Bewustzijn, Eten, Slapen, Denken

### Perfect voor Learning Module v1.0!

---

## 7️⃣ DATA STRUCTUUR - TOEKOMSTIGE UITBREIDINGEN

### Huidige Knowledge Card Schema:
```json
{
  "id": "uuid",
  "begrip": "Water",
  "lagen": {
    "laag1": "Basis definitie",
    "laag2": "Dieper begrip",
    "laag3": "Expert niveau"
  },
  "tags": ["natuur", "leven"],
  "belangrijkheid": 5,
  "status": "active"
}
```

### Voorgestelde Uitbreidingen (Placeholders):

#### A. Learning Module Metadata:
```json
{
  "learning": {
    "enabled": true,
    "difficulty": "beginner",  // beginner, intermediate, expert
    "estimated_time": 5,  // minutes
    "prerequisites": ["leven", "natuur"],  // begrippen die eerst geleerd moeten worden
    "quiz_questions": [
      {
        "question": "Wat is water?",
        "expected_answer": "laag1",  // verwijst naar lagen.laag1
        "difficulty": "easy"
      }
    ],
    "user_progress": {
      "times_practiced": 0,
      "last_practiced": null,
      "mastery_level": 0,  // 0-100%
      "next_review": null  // spaced repetition
    }
  }
}
```

#### B. Source/Bron Koppeling:
```json
{
  "bronnen": [
    {
      "type": "pdf",  // pdf, audio, video, url
      "titel": "Hacken voor Dummies",
      "bestand": "hacken_voor_dummies.pdf",
      "pagina": 42,
      "uploaded_at": "2026-03-16T14:00:00Z"
    },
    {
      "type": "audio",
      "titel": "Uitspraak: Water",
      "bestand": "water_pronunciation.mp3",
      "uploaded_at": "2026-03-15T10:30:00Z"
    }
  ]
}
```

#### C. Cluster/Folder Metadata:
```json
{
  "cluster": {
    "folder": "Natuur & Leven",
    "subfolder": "Natuur",
    "position": 1,  // voor custom sortering binnen folder
    "pinned": false  // voor favorieten
  }
}
```

#### D. Relation Metadata:
```json
{
  "relaties": {
    "parent": ["leven"],  // breder concept
    "children": ["regen", "ijs", "stoom"],  // smaller concepts
    "related": ["lucht", "aarde"],  // gerelateerd
    "mentions": ["organismen", "natuur"]  // genoemd in definitie
  }
}
```

### Implementatie Strategie:
1. **Fase 1 (Nu):** Voeg lege placeholders toe aan schema (backward compatible)
2. **Fase 2 (Later):** Vul learning metadata in voor top 78 candidates
3. **Fase 3 (Later):** Implementeer bron upload functionaliteit
4. **Fase 4 (Later):** Build UI voor learning module

---

## 8️⃣ KNOWLEDGE BASE ORGANISATIE - CONCRETE VOORSTELLEN

### Probleem:
Met 859 kaarten wordt scrollen onpraktisch. Gebruikers hebben structuur nodig.

### Oplossing 1: Folder/Categorie Systeem ✅ AANBEVOLEN
**Implementatie:**
- Gebruik top 15 clusters als main folders
- Auto-assign kaarten op basis van hun tags
- Kaarten zonder matching tag → "Overig" folder
- UI: Expandable folders in sidebar (zoals Windows Explorer)

**Voordelen:**
- Logische groepering
- Schaalbaar (kan subfolders maken)
- Overzichtelijk

### Oplossing 2: Alfabet Index
**Implementatie:**
- A-Z quick jump buttons bovenaan
- Click "M" → scroll naar eerste card met "M"

**Voordelen:**
- Simpel
- Snel voor bekende begrippen

### Oplossing 3: Smart Search + Filters (AL GEÏMPLEMENTEERD - 80%)
**Huidige status:**
- ✅ Search query filtering
- ✅ Sort by alfabet/importance
- ✅ Filter by sterren
- ⏳ Pagination
- ⏳ Filter by tags (UI nog toevoegen)

**Te voltooien:**
- UI bar met search + filters
- Tag filter dropdown (met top 30 tags)

### Aanbeveling:
**Combineer alle 3:**
1. **Folders** voor thematisch bladeren
2. **Alfabet** voor quick lookup
3. **Search + Filters** voor advanced queries

---

## 9️⃣ ROADMAP UPDATE VOORSTEL

### v4.0 - Learning & Education Module
**Priority:** High  
**ETA:** Q2 2026

**Features:**
- Learning mode toggle (transform statements → questions)
- Quiz system (vraag → antwoord → feedback)
- Progress tracking per gebruiker
- Spaced repetition algorithm
- Mastery levels (0-100%)
- Learning paths (prerequisite system)
- Top 78 candidates as v1.0 content

**Data Structuur:**
- ✅ Schema uitbreiding met `learning` metadata
- ✅ User progress tracking
- ✅ Quiz questions

**UI Components:**
- Learning tab (apart van Knowledge Base)
- Practice mode
- Review schedule
- Progress dashboard

---

### v4.5 - Source Management & Multi-Format Support
**Priority:** Medium  
**ETA:** Q3 2026

**Features:**
- PDF upload & koppeling aan kaarten
- Audio upload (al werkend voor keywords)
- Video upload (optioneel)
- URL referenties
- Bron bibliotheek tab
- Citeer functionaliteit (kaart → bron → pagina)

**Data Structuur:**
- ✅ Schema uitbreiding met `bronnen` array
- Bron types: pdf, audio, video, url
- Metadata: titel, bestand, pagina, uploaded_at

**Use Case:**
1. Upload "Hacken voor Dummies.pdf"
2. Maak kaarten van indexwoorden
3. Koppel bron aan kaarten: `"bron": "Hacken voor Dummies", "pagina": 42`
4. Spark kan nu zeggen: "Dit komt uit Hacken voor Dummies, pagina 42"

---

### v5.0 - Knowledge Clusters & Smart Organization
**Priority:** Medium  
**ETA:** Q4 2026

**Features:**
- Folder/categorie systeem (15 main folders)
- Drag & drop organization
- Custom folders (gebruiker-gedefinieerd)
- Smart auto-categorization (AI-powered)
- Cluster analytics (welke clusters veel gebruikt)

**Data Structuur:**
- ✅ Schema uitbreiding met `cluster` metadata
- Folder hierarchy
- Position/pinned support

---

### v6.0 - Advanced Relations & Knowledge Graph
**Priority:** Low  
**ETA:** 2027

**Features:**
- Parent/child relaties (hierarchie)
- Related kaarten (gerelateerd)
- Mentions tracking (kaart A noemt kaart B)
- Relation visualization (interactive graph)
- Learning paths op basis van relaties

**Data Structuur:**
- ✅ Schema uitbreiding met `relaties` metadata
- Parent, children, related, mentions arrays

---

## 🎯 ACTIE ITEMS - PRIORITEIT VOLGORDE

### P0 - Direct (Deze Week):
1. ✅ Knowledge analysis rapport (DONE - dit document)
2. ⏳ Update knowledge_base schema met placeholders (backward compatible)
3. ⏳ Finish Knowledge Base UI (search bar, filter dropdowns)
4. ⏳ Test nieuwe layout zonder rechter sidebar

### P1 - Binnenkort (Volgende Week):
5. Add folder/categorie support in Knowledge Base
6. Auto-categorize kaarten op basis van tags
7. Alfabet index toevoegen
8. Tag filter UI (dropdown met top 30 tags)

### P2 - Later (Volgende Maand):
9. Learning Module v1.0 design
10. Quiz system prototype
11. Progress tracking backend

### P3 - Toekomst (Q2-Q4 2026):
12. PDF upload functionaliteit
13. Bron bibliotheek UI
14. Advanced relations
15. Knowledge graph visualization

---

## 📊 SAMENVATTING - KEY TAKEAWAYS

1. **Kwaliteit is hoog:** 99.1% kaarten volledig met 3 lagen ✅
2. **78 kaarten ready** voor Learning Module ✅
3. **30 grote clusters** perfect voor folder structuur ✅
4. **841 kaarten connected** - sterke knowledge graph ✅
5. **Data structuur placeholders** kunnen NU toegevoegd worden ✅
6. **Roadmap v4.0-6.0** gedefinieerd voor Learning + Sources + Clusters ✅

### Volgende Stap:
Update `knowledge_base.json` schema met placeholders, zodat nieuwe features later eenvoudig in te pluggen zijn **zonder grote refactors**.

---

**END OF REPORT**
