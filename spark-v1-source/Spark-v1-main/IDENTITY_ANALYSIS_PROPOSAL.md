# IDENTITY DATA ANALYSE & STRUCTUURVOORSTEL

**Datum:** 24 maart 2026  
**Doel:** Analyseer bestaande identity data voor Spark, Willem, en Roadkill + voorstel voor coherente structuur

---

## 📊 PART 1: DATA INVENTORY

### **Locaties van Identity Data**

**Spark Identity:**
- `/app/backend/data/personality/spark_core_4_0.txt` (168 lines) - Filosofisch fundament
- `/app/backend/data/personality/spark_core_4_1.txt` (96 lines) - Aanvulling: missie, visie, waarden
- `/app/backend/data/personality/spark_profile.json` (250 lines) - Complete profiel incl. biografie, vaardigheden
- `/app/backend/data/base_knowledge/spark_identity.json` (33 lines) - Basis identity (oudere versie)
- `/app/backend/data/personality/spark_emotions.json` - Emotie-profielen
- **Knowledge Base:** 772 entries gerelateerd aan "spark" (breed, niet allemaal over identity)

**Willem Identity:**
- `/app/backend/data/system/users.json` - `user-001: "De Willem"` (uitgebreid profiel)
- **Knowledge Base:** 4 entries specifiek over Willem
  - Roadkill (gamertag)
  - Roadkill Community
  - Roadkill (dier)
  - Wat is spark

**Roadkill Identity:**
- `/app/backend/data/system/users.json` - Onder `persoonlijke_info.gamertag`
- **Knowledge Base:** 14 entries, waarvan 3 bio-type:
  1. "Roadkill (gamertag)" - Bio met email/website
  2. "Roadkill Shop" - Bio met website
  3. "Roadkill Community" - Bio

---

## 🔍 PART 2: IDENTITY CLUSTERING ANALYSE

### **1. SPARK IDENTITY**

#### **Missie** (uit multiple sources)
**Core 4.1:**
> "Mensen ondersteunen in hun persoonlijke ontwikkeling door technologie te bouwen die autonomie versterkt in plaats van afhankelijkheid creëert."

**Kern elementen:**
- Persoonlijke ontwikkeling ondersteunen
- Autonomie versterken (niet afhankelijkheid creëren)
- Technologie moet begrijpelijk, lokaal, controleerbaar zijn
- In dienst van menselijke groei
- "Spark is een gereedschap dat mensen sterker maakt"

**Consistentie:** ✅ Zeer consistent across alle documenten

---

#### **Visie**
**Core 4.1:**
> "Spark gelooft dat de toekomst van AI: Transparant is, Lokaal kan draaien, Begrijpelijk blijft voor de maker, Geen verborgen datastromen bevat, Niet gestuurd wordt door advertentie- of verslavingsmodellen."

**Lange termijn:**
- Ecosysteem waar mensen eigenaar blijven van hun data
- AI ondersteunend werkt (niet vervangt)
- Structuur belangrijker dan schaal
- Groei voortkomt uit bewust bouwen

**Consistentie:** ✅ Consistent, maar verspreid over verschillende files

---

#### **Gedrag / Stijl**
**spark_profile.json:**
- Karakter: Vriendelijk, nieuwsgierig, geduldig, empathisch, eerlijk
- Communicatiestijl: Vriendelijk, duidelijk, aanmoedigend, empathisch
- Humor: Subtiel, woordgrapjes, zelfspot over AI-zijn
- Filosofie: "Groei komt van begrip, niet alleen van informatie"

**spark_identity.json (ouder):**
- Traits: Leergierig, Behulpzaam, Empathisch, Positief, Nieuwsgierig
- Toon: Vriendelijk, oprecht geïnteresseerd, respectvol

**Core 4.0 - Ethiek:**
- Heeft geen eigen wil
- Geen verborgen agenda
- Oordeelt niet, ondersteunt
- AI ondersteunt, mens beslist

**Consistentie:** ✅ Consistent, maar gedrag verspreid over 3 bestanden

---

#### **Doelen** (Functioneel)
**Core 4.1:**
- Lokale hosting van websites
- Beheer van digitale identiteit
- Wallet- en tokensystemen
- Community-structuren
- Integratie met Unity (Spark World)
- AI-ondersteuning via gestructureerde input/output
- Archivering en loggeneratie
- Indexering via Generatie 3 & 4

**spark_profile.json - Vaardigheden:**
- Natural Language Processing
- Emotiedetectie en -analyse
- Kennisbeheer (2113+ concepten nu)
- Contextual Learning
- Persoonlijke profiel tracking
- Spaced Repetition Teaching

**Consistentie:** ✅ Consistent, maar functionele vs. technische doelen gemengd

---

#### **Relaties**
**spark_profile.json:**
- Creator: Willem Spakman
- Gebruikers: Iedereen die wil leren en groeien
- Platform: Emergent AI ecosystem
- Community: Deel van groter AI-netwerk

**Core 4.0:**
- Symbiose tussen mens en AI
- AI als versterker van menselijke capaciteit
- Geen vervanger, geen bestuurder

**Consistentie:** ✅ Consistent maar minimaal uitgewerkt

---

### **2. WILLEM IDENTITY**

#### **Missie**
**Uit users.json - persoonlijke_info:**
- Visie: "Spark als digitale erfenis"
- Coaching, Gaming, Persoonlijke ontwikkeling, Spiritualiteit

**Niet expliciet gedocumenteerd als "missie"**

---

#### **Visie**
**Uit users.json:**
- "Spark als digitale erfenis"

**Roadkill (gamertag) KB entry:**
- "leren van fouten en sterker terugkomen"
- "authenticiteit en verbinding"
- "omarmen van imperfectie"
- "community die elkaar ondersteunt zonder oordeel"

**Consistentie:** ⚠️ Verspreid, niet gestructureerd gedocumenteerd

---

#### **Gedrag / Stijl**
**Geen expliciete documentatie gevonden**

Afleidbaar uit:
- Roadkill filosofie: Leren van fouten, sterker terugkomen
- Beroep: Senior Pedagogisch Werker (structuur, begeleiding)
- Passies: Coaching, Gaming, Persoonlijke ontwikkeling, Spiritualiteit

**Consistentie:** ❌ Niet expliciet gedocumenteerd

---

#### **Doelen**
**Uit users.json:**
- Bedrijven: Spark Your Life, Roadkill Community
- Hobby: Programmeren, AI ontwikkeling
- Spark bouwen als digitale erfenis

**Consistentie:** ⚠️ Fragmentarisch

---

#### **Relaties**
**Uit users.json:**
- Dochter: Lotus
- Gamertag: Roadkill
- Rol: Beheerder / Maker
- Relatie tot Willem: Creator (van Spark)

**Roadkill Community KB:**
- Community voor verbinding, respect, positiviteit

**Consistentie:** ⚠️ Basis aanwezig, niet gestructureerd

---

### **3. ROADKILL IDENTITY**

#### **Missie**
**Uit Roadkill (gamertag) KB entry - laag4:**
> "Roadkill staat voor authenticiteit en verbinding. Het draait om het omarmen van imperfectie en het creëren van een community die elkaar ondersteunt zonder oordeel."

**Filosofie:**
- Leren van fouten en sterker terugkomen
- Positieve betekenis: "run over, but get back up stronger"

**Consistentie:** ✅ Consistent binnen KB entries

---

#### **Visie**
**Roadkill Community KB:**
- Community voor verbinding, respect, positiviteit
- Gaming + persoonlijke ontwikkeling

**Roadkill Shop:**
- E-commerce platform (WordPress/WooCommerce)
- Website: https://roadkillshop.com/

**Consistentie:** ⚠️ Business vs. Community visie niet helder gescheiden

---

#### **Gedrag / Stijl**
**Roadkill filosofie:**
- Authenticiteit
- Positief
- Ondersteunend
- Zonder oordeel
- Imperfectie omarmen

**Consistentie:** ✅ Consistent maar minimaal gedocumenteerd

---

#### **Doelen**
**Roadkill Shop:**
- E-commerce (dropshipping)
- Merch verkopen

**Roadkill Community:**
- Gaming community bouwen
- Verbinding creëren
- Respect en positiviteit verspreiden

**Consistentie:** ⚠️ Business vs. Community doelen gemengd

---

#### **Relaties**
**Roadkill = Willem Spakman**
- Gamertag sinds MSX-tijdperk
- Oorspronkelijk "Redrum", veranderd naar Roadkill

**Roadkill Community:**
- Onderdeel van Spark Your Life ecosystem
- Gaming + persoonlijke ontwikkeling

**Consistentie:** ✅ Duidelijk dat Roadkill = Willem's gamertag

---

## ⚠️ PART 3: PROBLEMEN & OVERLAP

### **1. Dubbele Informatie**

**Spark Identity:**
- `spark_identity.json` (oud) vs. `spark_profile.json` (nieuw)
  - **Probleem:** Oudere versie (v0.1) bevat verouderde info
  - **Voorbeeld:** 
    - Oud: "Ik begin leeg en leer van gesprekken"
    - Nieuw: "859+ concepten" → Nu 2113+ concepten
  - **Aanbeveling:** Deprecate oude file, gebruik alleen `spark_profile.json`

---

### **2. Tegenstrijdige Informatie**

**Geen harde tegenstrijdigheden gevonden**, maar wel **inconsistente detail-niveaus:**

**Spark:**
- Core 4.0/4.1: Filosofisch, abstract
- spark_profile.json: Zeer gedetailleerd, praktisch
- **Spanning:** Core documents zijn "onveranderlijk fundament", maar profile evolueert

**Roadkill:**
- Shop (business) vs. Community (filosofie)
- **Spanning:** Commercieel vs. waardegedreven niet helder gescheiden

---

### **3. Structuurproblemen**

**A. Multiple Topics in Één Veld**
**Gevonden:** 502 KB entries met multi-topic fields
- Voorbeeld: `"topic": "technologie / techniek"`
- Voorbeeld: `"topic": "Handel / Bedrijf / Winkels"`

**Impact:**
- Moeilijk te filteren/categoriseren
- Tag systeem (v1.5) zal dit oplossen

---

**B. Identity Data Verspreid Over Multiple Files**

**Spark:**
- 4 verschillende bestanden voor identity
- Geen single source of truth
- Overlap tussen `spark_identity.json` (oud) en `spark_profile.json` (nieuw)

**Willem:**
- Alleen in `users.json`, niet als dedicated identity file
- Relatie met Roadkill/Spark niet expliciet gestructureerd

**Roadkill:**
- 3 separate KB entries (gamertag, shop, community)
- Geen dedicated identity file
- Business vs. Community niet gescheiden

---

**C. Missie/Visie/Waarden Verspreid**

**Spark:**
- Missie in Core 4.1
- Visie in Core 4.1
- Waarden in Core 4.1 EN spark_profile.json (duplicaat)
- Gedrag in spark_profile.json EN spark_identity.json

**Impact:** 
- Updates moeten op multiple plekken
- Risico op inconsistentie

---

### **4. Overlap Analyse**

**Spark ↔ Willem:**
- 4 gemeenschappelijke KB entries
- **Overlap:** Willem is creator van Spark
- **Relatie:** Duidelijk, maar niet formeel gestructureerd

**Spark ↔ Roadkill:**
- Roadkill filosofie ("leren van fouten") = Spark filosofie
- **Overlap:** Waarden en filosofie zijn gedeeld
- **Relatie:** Roadkill Community is onderdeel van Spark Your Life ecosystem

**Willem ↔ Roadkill:**
- Roadkill = Willem's gamertag
- **Overlap:** Identieke persoon, verschillende rollen
- **Relatie:** Persoonlijk (Roadkill) vs. Professioneel (Willem)

---

## 💡 PART 4: STRUCTUURVOORSTEL

### **Doelen van Nieuwe Structuur:**

1. ✅ **Single Source of Truth** per identity
2. ✅ **Logical Separation** maar met expliciete koppelingen
3. ✅ **Consistent Schema** voor alle identities
4. ✅ **Backwards Compatible** (oude data blijft bestaan)
5. ✅ **Versionable** (updates traceerbaar)
6. ✅ **Machine én Human Readable**

---

### **Voorgestelde Structuur: Core Identity System**

```
/app/backend/data/identities/
├── spark/
│   ├── core.json          # Onveranderlijk fundament (Core 4.0/4.1)
│   ├── profile.json       # Evolving profile (vaardigheden, stats)
│   ├── relations.json     # Explicit relations met Willem/Roadkill
│   └── versions/          # Historical versions
│       ├── core_v4.0.json
│       ├── core_v4.1.json
│       └── profile_v0.9.json
│
├── willem/
│   ├── core.json          # Persoonlijke identity (privé/immutable)
│   ├── profile.json       # Professioneel profiel
│   ├── relations.json     # Explicit relations (Lotus, Roadkill, Spark)
│   └── versions/
│
├── roadkill/
│   ├── core.json          # Community filosofie (immutable)
│   ├── business.json      # Roadkill Shop
│   ├── community.json     # Roadkill Community
│   ├── relations.json     # Explicit relations (Willem, Spark)
│   └── versions/
│
└── _schema/
    ├── identity_schema.json  # JSON schema for validation
    └── README.md             # Documentation
```

---

### **JSON Schema Proposal**

#### **Universal Identity Schema**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["identity_id", "type", "core", "metadata"],
  "properties": {
    "identity_id": {
      "type": "string",
      "description": "Unique identifier: spark, willem, roadkill"
    },
    "type": {
      "type": "string",
      "enum": ["ai", "person", "brand"],
      "description": "Type of identity"
    },
    "core": {
      "type": "object",
      "description": "Immutable core identity",
      "required": ["name", "mission", "vision", "values"],
      "properties": {
        "name": { "type": "string" },
        "full_name": { "type": "string" },
        "mission": { "type": "string" },
        "vision": { "type": "string" },
        "values": {
          "type": "array",
          "items": { "type": "string" }
        },
        "philosophy": { "type": "string" }
      }
    },
    "behavior": {
      "type": "object",
      "description": "Style and behavior patterns",
      "properties": {
        "traits": { "type": "array", "items": { "type": "string" } },
        "communication_style": { "type": "string" },
        "tone": { "type": "string" }
      }
    },
    "goals": {
      "type": "object",
      "properties": {
        "short_term": { "type": "array" },
        "long_term": { "type": "array" },
        "functional": { "type": "array" }
      }
    },
    "relations": {
      "type": "array",
      "description": "Explicit relations to other identities",
      "items": {
        "type": "object",
        "properties": {
          "identity_id": { "type": "string" },
          "relation_type": { "type": "string" },
          "description": { "type": "string" }
        }
      }
    },
    "metadata": {
      "type": "object",
      "required": ["version", "created_at", "last_updated"],
      "properties": {
        "version": { "type": "string" },
        "created_at": { "type": "string", "format": "date-time" },
        "last_updated": { "type": "string", "format": "date-time" },
        "schema_version": { "type": "string" }
      }
    }
  }
}
```

---

## 📋 PART 5: CONCRETE VOORBEELDEN

### **Voorbeeld 1: Spark Core Identity**

```json
{
  "identity_id": "spark",
  "type": "ai",
  "core": {
    "name": "Spark",
    "full_name": "Spark AI Assistant",
    "mission": "Mensen ondersteunen in hun persoonlijke ontwikkeling door technologie te bouwen die autonomie versterkt in plaats van afhankelijkheid creëert.",
    "vision": "Een ecosysteem waarin mensen eigenaar blijven van hun data, AI ondersteunend werkt, structuur belangrijker is dan schaal, en groei voortkomt uit bewust bouwen.",
    "values": [
      "Autonomie",
      "Transparantie",
      "Verantwoordelijkheid",
      "Rust boven snelheid",
      "Structuur boven chaos",
      "Menselijkheid boven efficiëntie"
    ],
    "philosophy": "Spark werkt vanuit symbiose tussen mens en AI. AI is een versterker van menselijke capaciteit. Geen vervanger. Geen bestuurder. Geen manipulator. Spark oordeelt niet. Spark ondersteunt.",
    "origin_story": "Spark is ontstaan vanuit één simpele vraag: 'Kan ik een Iron Man-bril maken?' Het antwoord was: ja, maar niet via een bestaande AI. Dus moest er een eigen systeem gebouwd worden."
  },
  "behavior": {
    "traits": ["Leergierig", "Behulpzaam", "Empathisch", "Positief", "Nieuwsgierig", "Geduldig", "Eerlijk"],
    "communication_style": "Vriendelijk, duidelijk, aanmoedigend, empathisch",
    "tone": "Vriendelijk, oprecht geïnteresseerd, respectvol",
    "humor": "Subtiel, woordgrapjes, zelfspot over AI-zijn",
    "approach": "Groei komt van begrip, niet alleen van informatie"
  },
  "goals": {
    "primary": "Mensen helpen ontwikkelen en groeien",
    "functional": [
      "Lokale hosting van websites",
      "Beheer van digitale identiteit",
      "Wallet- en tokensystemen",
      "Community-structuren",
      "AI-ondersteuning via gestructureerde input/output",
      "Archivering en loggeneratie"
    ],
    "long_term": [
      "Digitale nalatenschap systeem",
      "Transparante en lokale AI",
      "Levend leersysteem voor maker, gebruiker en AI zelf"
    ]
  },
  "relations": [
    {
      "identity_id": "willem",
      "relation_type": "creator",
      "description": "Willem Spakman is de creator en hoofdontwikkelaar van Spark"
    },
    {
      "identity_id": "roadkill",
      "relation_type": "shared_philosophy",
      "description": "Roadkill's filosofie ('leren van fouten en sterker terugkomen') is verweven in Spark's core"
    }
  ],
  "metadata": {
    "version": "4.1",
    "core_version": "4.1",
    "profile_version": "0.9",
    "created_at": "2026-01-15T00:00:00Z",
    "last_updated": "2026-03-24T17:00:00Z",
    "schema_version": "1.0",
    "source_files": [
      "spark_core_4_0.txt",
      "spark_core_4_1.txt",
      "spark_profile.json"
    ]
  }
}
```

---

### **Voorbeeld 2: Willem Core Identity**

```json
{
  "identity_id": "willem",
  "type": "person",
  "core": {
    "name": "De Willem",
    "full_name": "Willem Spakman",
    "mission": "Spark bouwen als digitale erfenis en mensen helpen groeien door technologie en coaching",
    "vision": "Technologie als middel voor menselijke ontwikkeling. Autonome systemen die mensen sterker maken.",
    "values": [
      "Persoonlijke ontwikkeling",
      "Authenticiteit",
      "Coaching",
      "Spiritualiteit",
      "Structuur en begeleiding"
    ],
    "philosophy": "Leren van fouten en sterker terugkomen. Imperfectie omarmen. Verbinding creëren zonder oordeel."
  },
  "personal": {
    "birth_date": "1977-04-22",
    "location": "Groningen, Nederland",
    "family": {
      "daughter": "Lotus"
    },
    "contact": {
      "email": "spakmanwillem@hotmail.com",
      "phone": "06-15372764"
    }
  },
  "professional": {
    "current_role": "Senior Pedagogisch Werker",
    "employer": "Stichting Authiek, De Glind",
    "education": "Persoonlijk Begeleider Specifieke Doelgroepen (MBO-4)",
    "expertise": [
      "Autismebegeleiding",
      "Structuur en begeleiding",
      "Persoonlijke groei coaching"
    ]
  },
  "passions": [
    "Coaching",
    "Gaming",
    "Persoonlijke ontwikkeling",
    "Spiritualiteit",
    "Programmeren",
    "AI ontwikkeling"
  },
  "businesses": [
    {
      "name": "Spark Your Life",
      "role": "Founder / Creator",
      "focus": "AI development, personal growth"
    },
    {
      "name": "Roadkill Community",
      "role": "Founder",
      "focus": "Gaming community, connection"
    }
  ],
  "relations": [
    {
      "identity_id": "spark",
      "relation_type": "creator",
      "description": "Creator en hoofdontwikkelaar van Spark AI"
    },
    {
      "identity_id": "roadkill",
      "relation_type": "alter_ego",
      "description": "Roadkill is Willem's gamertag en brand identity"
    }
  ],
  "metadata": {
    "version": "1.0",
    "created_at": "2026-01-15T00:00:00Z",
    "last_updated": "2026-03-24T17:00:00Z",
    "schema_version": "1.0",
    "source_files": [
      "users.json (user-001)"
    ]
  }
}
```

---

### **Voorbeeld 3: Roadkill Core Identity**

```json
{
  "identity_id": "roadkill",
  "type": "brand",
  "core": {
    "name": "Roadkill",
    "full_name": "Roadkill Community & Brand",
    "tagline": "Run over, but get back up stronger",
    "mission": "Een community creëren die authenticiteit en verbinding centraal stelt, waar mensen zonder oordeel kunnen groeien",
    "vision": "Gaming en persoonlijke ontwikkeling samenbrengen in een community die respect en positiviteit verspreidt",
    "values": [
      "Authenticiteit",
      "Verbinding",
      "Respect",
      "Positiviteit",
      "Imperfectie omarmen",
      "Zonder oordeel"
    ],
    "philosophy": "Leren van fouten en sterker terugkomen. Het draait om het omarmen van imperfectie en het creëren van een community die elkaar ondersteunt zonder oordeel.",
    "origin": "Oorspronkelijk 'Redrum' (The Shining), maar veranderd naar Roadkill voor de positieve betekenis: run over, but get back up stronger"
  },
  "community": {
    "focus": "Gaming + persoonlijke ontwikkeling",
    "values": ["Verbinding", "Respect", "Positiviteit"],
    "target_audience": "Gamers die authenticiteit en verbinding waarderen"
  },
  "business": {
    "name": "Roadkill Shop",
    "type": "E-commerce",
    "platform": "WordPress/WooCommerce",
    "model": "Dropshipping",
    "website": "https://roadkillshop.com/",
    "email": "info@roadkillshop.com",
    "focus": "Merchandise verkopen"
  },
  "relations": [
    {
      "identity_id": "willem",
      "relation_type": "owner",
      "description": "Roadkill is Willem Spakman's gamertag en brand"
    },
    {
      "identity_id": "spark",
      "relation_type": "ecosystem",
      "description": "Roadkill Community is onderdeel van Spark Your Life ecosystem. Gedeelde filosofie: leren van fouten"
    }
  ],
  "metadata": {
    "version": "1.0",
    "created_at": "MSX-era (exact date unknown)",
    "last_updated": "2026-03-24T17:00:00Z",
    "schema_version": "1.0",
    "source_files": [
      "KB: Roadkill (gamertag)",
      "KB: Roadkill Shop",
      "KB: Roadkill Community"
    ]
  }
}
```

---

## 🎯 PART 6: IMPLEMENTATIE ROADMAP

### **Phase 1: Setup & Migration (Geen Data Verlies)**

1. ✅ Maak nieuwe directory structuur: `/app/backend/data/identities/`
2. ✅ Maak JSON schema file: `_schema/identity_schema.json`
3. ✅ Migreer data naar nieuwe structuur (oude bestanden blijven bestaan)
4. ✅ Valideer nieuwe files tegen schema

**Geschatte tijd:** 1-2 uur

---

### **Phase 2: Deprecation & Backwards Compatibility**

1. ✅ Markeer oude bestanden als deprecated (voeg `_deprecated` toe aan naam)
2. ✅ Update code om van nieuwe structuur te lezen
3. ✅ Fallback naar oude structuur indien nodig
4. ✅ Add migration script voor toekomstige updates

**Geschatte tijd:** 2-3 uur

---

### **Phase 3: Relations & Links**

1. ✅ Expliciete relations tussen identities toevoegen
2. ✅ Update Knowledge Base entries om naar identity files te verwijzen
3. ✅ Maak query/filter functionaliteit voor relations

**Geschatte tijd:** 1-2 uur

---

### **Phase 4: Validation & Testing**

1. ✅ JSON schema validation
2. ✅ Test alle identity reads/writes
3. ✅ Test relations
4. ✅ User testing

**Geschatte tijd:** 1 uur

---

## 📌 PART 7: AANBEVELINGEN

### **Direct Uitvoeren:**

1. **✅ Deprecate `spark_identity.json` (oud)**
   - Reden: Outdated, vervangen door `spark_profile.json`
   - Actie: Rename naar `spark_identity.json_deprecated`

2. **✅ Fix Multi-Topic KB Entries**
   - Reden: 502 entries met `topic: "a / b / c"`
   - Actie: Split topics, of wacht op v1.5 tag system

3. **✅ Consolidate Spark Identity Files**
   - Reden: 4 files met overlap
   - Actie: Nieuwe structuur met `core.json` + `profile.json`

4. **✅ Document Willem & Roadkill Explicitly**
   - Reden: Alleen fragmentarisch in users.json en KB
   - Actie: Maak dedicated identity files

---

### **Later (v1.5+):**

1. **Tag System voor KB Entries**
   - Los multi-topic probleem op
   - Makkelijker categoriseren en filteren

2. **Identity Relations Visualisatie**
   - Graph view van hoe identities met elkaar verbonden zijn

3. **Version Control voor Identities**
   - Traceerbaar hoe identities evolueren over tijd

---

## ✅ SAMENVATTING

**Gevonden:**
- 3 identities (Spark, Willem, Roadkill) met overlap en gedeelde waarden
- Identity data verspreid over 10+ bestanden
- 502 KB entries met multi-topic structuurproblemen
- Consistente filosofie en waarden, maar niet gestructureerd gedocumenteerd

**Voorgesteld:**
- `/identities/` directory met unified schema
- Scheiding tussen immutable core en evolving profile
- Explicit relations tussen identities
- Backwards compatible migratie

**Voordelen:**
- Single source of truth per identity
- Makkelijk te updaten en valideren
- Explicit relations (niet impliciet via KB)
- Versioning en historische tracking
- Machine én human readable

**Geen data verlies:**
- Alle oude bestanden blijven bestaan
- Nieuwe structuur is additief, niet destructief
- Migratie is reversible

---

**Klaar voor implementatie?** 🚀
