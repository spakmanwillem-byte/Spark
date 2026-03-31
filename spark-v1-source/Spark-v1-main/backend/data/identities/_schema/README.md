# Identity System

**Aangemaakt:** 24 maart 2026  
**Versie:** 1.0

## 📖 Overzicht

Dit directory bevat gestructureerde identity data voor alle belangrijke identiteiten in het Spark ecosysteem.

**Filosofie:** Gebouwd uit **organische groei** - bestaande KB entries zijn gebruikt als brondata en omgezet naar gestructureerde formats. Niets is verwijderd, alleen gestructureerd.

## 📁 Structuur

```
identities/
├── roadkill/
│   ├── gamer.json              # Personal gaming identity
│   ├── community.json          # Community movement
│   ├── business.json           # Roadkill Shop
│   ├── core_philosophy.json    # Shared philosophy
│   └── relations.json          # (toekomstig)
│
├── spark_your_life/
│   ├── core.json               # Zorgboerderij missie/visie
│   ├── services.json           # (toekomstig)
│   └── relations.json          # (toekomstig)
│
├── spark/                      # (toekomstig - AI identity)
├── willem/                     # (toekomstig - Willem identity)
│
└── _schema/
    ├── kb_mapping.json         # Traceability naar KB
    ├── identity_schema.json    # (toekomstig)
    └── README.md               # Dit bestand
```

## 🔍 Roadkill Ecosystem

Roadkill is **geen enkele identity**, maar een **ecosystem** met 3 dimensies:

1. **Gamer Identity** (`gamer.json`)
   - Willem's persoonlijke gamertag
   - Filosofie: "Leren van fouten en sterker terugkomen"
   - Origine: MSX-era, oorspronkelijk "Redrum"

2. **Community** (`community.json`)
   - Beweging voor inclusiviteit en verbinding
   - Supporters + Cliënten van zorgboerderij
   - Doel: Mensen helpen die tussen wal en schip vallen

3. **Business** (`business.json`)
   - Roadkill Shop (merchandise)
   - Duurzame producten (gerecycled/biologisch)
   - Financiert Spark Your Life zorgboerderij

**Shared:** `core_philosophy.json` - Gedeelde filosofie gebruikt door alle 3

## 🔗 Relaties

```
        WILLEM SPAKMAN
       (Founder/Creator)
              │
    ┌─────────┼─────────┐
    │         │         │
    ▼         ▼         ▼
  SPARK   ROADKILL  SPARK YOUR LIFE
   AI     (gamer)   (zorgboerderij)
           │              ▲
           ├─────────┐    │
           ▼         ▼    │
    ROADKILL     ROADKILL SHOP
    COMMUNITY    (funding)
           └──────►──────┘
```

## 📋 Traceability

Alle identity files zijn gebouwd uit bestaande Knowledge Base entries. De mapping is gedocumenteerd in `_schema/kb_mapping.json`.

**Belangrijke KB entries:**
- `12465c90-1ba7-447c-a370-6ba87f45e255` - Roadkill (gamertag)
- `856d362f-aead-46e6-a0de-9c208ecc756e` - Roadkill Community
- `cedcf046-2a19-48f9-a1f0-b5cbfe6690b9` - Roadkill Shop
- `6fde8072-7e2d-45a4-ad55-1417fbaabe73` - Spark Your Life

**Originele KB entries blijven bestaan** - deze identity files zijn gestructureerde extracties, geen vervangingen.

## 🎯 Gebruik

Identity files kunnen gebruikt worden voor:
- Consistent profile management
- Relation tracking
- Documentation
- API responses
- Frontend display

## 📝 Schema

Elk identity file volgt een consistent schema:
- `identity_id` - Unique identifier
- `type` - Type identity (personal_brand, community, business, etc.)
- `core` - Core identity info (immutable)
- `relations` - Explicit relations naar andere identiteiten
- `kb_sources` - Traceability naar originele KB entries
- `metadata` - Version info, timestamps, etc.

## 🔄 Updates

Identity files zijn **versionable**. Updates worden getraceerd via `metadata.version` en `metadata.last_updated`.

## ⚠️ Belangrijk

- **Niet verwijderen**: KB entries blijven bestaan
- **Organische groei**: Identity data komt uit echte gebruik
- **Inferred metadata**: Acceptabel en gedocumenteerd
- **Structuur, niet opschoning**: Doel is helderheid, niet perfectie

---

**Aangemaakt door:** Identity System Implementation (Phase 1)  
**Brondata:** Knowledge Base entries (learned_knowledge/knowledge_base.json)


---

## ⚠️ CRITICAL RULES - DATA INTEGRITY

### **3-Laags Scheiding**

**BELANGRIJK:** naam ≠ identiteit ≠ data-koppeling

#### **1. Auth Layer (Technisch)**
- **Doel:** Login, database, authentication
- **Voorbeeld:** "Willem Spakman" + "appelsap"
- **Gebruik:** Backend authentication ONLY

#### **2. Display Layer (Weergave)**
- **Doel:** AI-output, UI, representatie
- **Voorbeeld:** "De Willem"
- **Gebruik:** Frontend display, chat messages, UI labels

#### **3. System Layer (Data-koppeling)**
- **Doel:** Database queries, relationships, tracking
- **Voorbeeld:** `user-001`
- **Gebruik:** **ALTIJD** voor achievements, highscores, data linking

---

### **Kritieke Regels**

```
CR-001: naam ≠ identiteit ≠ data-koppeling
CR-002: ALTIJD op user_id matchen, NOOIT op naam
CR-003: display_name is alleen visueel
CR-004: Achievements en highscores → user_id
CR-005: Organische groei is waardevol (geen vervuiling)
```

### **Code Voorbeelden**

✅ **CORRECT:**
```python
# User lookup
user = db.users.find_one({'id': user_id}, {'_id': 0})

# Achievement save
achievement = {'user_id': user_id, 'type': 'xp', 'value': 100}

# Display in UI
display_name = user_data['display_layer']['display_name']  # "De Willem"
```

❌ **FOUT:**
```python
# NEVER do this
user = db.users.find_one({'naam': 'De Willem'})
achievement = {'naam': 'De Willem', 'type': 'xp'}
```

---

### **Waarom Dit Belangrijk Is**

- Namen kunnen veranderen (display preferences)
- IDs zijn persistent en uniek
- Matching op naam breekt bij typos, varianten, updates
- Data-integriteit hangt af van correcte ID-linking

**Zie ook:** `_schema/identity_system_rules.json` voor volledige documentatie

