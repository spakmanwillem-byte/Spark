# UNIFIED KNOWLEDGE SCHEMA v2.0
**Datum:** 2026-03-16  
**Status:** Design Document - Klaar voor implementatie  
**Backward Compatible:** ✅ Yes

---

## 🎯 **DOEL**

Unified schema voor ALLE content types in Spark:
- **Knowledge Cards** (859 bestaande kaarten)
- **Norms** (regels/normen voor Spark's gedrag)
- **Values** (waarden die Spark belangrijk vindt)
- **Bijbel Items** (filosofische principes en visies)

**Alle types** krijgen:
- ✅ WS5 Framework (Who, What, When, Where, Why, How)
- ✅ Learning Module support (placeholders)
- ✅ Bron koppeling (pdf, audio, video)
- ✅ Cluster/folder organizatie
- ✅ Relaties tussen items

---

## 📐 **UNIFIED SCHEMA**

### Base Structure (Alle Types):
```json
{
  "id": "uuid",
  "type": "knowledge" | "norm" | "value" | "bible",
  "begrip": "String - Naam/titel van het item",
  "status": "active" | "unanswered" | "trash",
  "belangrijkheid": 0-10,
  
  "lagen": {
    "laag1": "Basis level uitleg",
    "laag2": "Intermediate level uitleg",
    "laag3": "Expert level uitleg",
    "laag4": "Master level uitleg (optioneel)"
  },
  
  "ws5": {
    "who": "Wie - betrokkenen, personen, doelgroep",
    "what": "Wat - kern, definitie, actie",
    "when": "Wanneer - timing, context, frequentie",
    "where": "Waar - locatie, scope, domein",
    "why": "Waarom - reden, doel, motivatie",
    "how": "Hoe - methode, proces, uitvoering"
  },
  
  "tags": ["tag1", "tag2", "..."],
  
  "metadata": {
    "toegevoegd_op": "ISO datetime",
    "created_by": "user name",
    "created_by_user_id": "user-xxx",
    "created_via": "admin" | "chat" | "api",
    "last_updated": "ISO datetime",
    "usage_count": 0,
    "last_used": "ISO datetime"
  }
}
```

---

### Type-Specific Extensions:

#### **Type: "knowledge"** (Standard Knowledge Card)
```json
{
  "type": "knowledge",
  "begrip": "Water",
  
  // ... base fields ...
  
  "learning": {
    "enabled": false,
    "difficulty": "beginner" | "intermediate" | "expert",
    "estimated_time_minutes": 5,
    "prerequisites": ["leven", "natuur"],
    "learning_objectives": [
      "Begrijpen wat water is",
      "Weten waarom water belangrijk is voor leven"
    ],
    "quiz_questions": [
      {
        "id": "q1",
        "question": "Wat is water?",
        "expected_layer": "laag1",
        "hints": ["Denk aan H2O"],
        "difficulty": "easy"
      }
    ],
    "user_progress": {
      "user-xxx": {
        "times_practiced": 0,
        "last_practiced": null,
        "mastery_level": 0,
        "next_review": null,
        "correct_answers": 0,
        "total_attempts": 0
      }
    }
  },
  
  "bronnen": [
    {
      "id": "bron-1",
      "type": "pdf",
      "titel": "Hacken voor Dummies",
      "bestand": "hacken_voor_dummies.pdf",
      "pagina": 42,
      "sectie": "Netwerk Beveiliging",
      "uploaded_at": "2026-03-16T14:00:00Z",
      "uploaded_by": "user-001"
    },
    {
      "id": "bron-2",
      "type": "audio",
      "titel": "Uitspraak: Water",
      "bestand": "water_pronunciation.mp3",
      "duration_seconds": 3,
      "uploaded_at": "2026-03-15T10:30:00Z"
    },
    {
      "id": "bron-3",
      "type": "video",
      "titel": "Water Cyclus Uitleg",
      "bestand": "water_cycle.mp4",
      "duration_seconds": 180,
      "thumbnail": "water_cycle_thumb.jpg",
      "uploaded_at": "2026-03-14T09:00:00Z"
    },
    {
      "id": "bron-4",
      "type": "url",
      "titel": "Wikipedia - Water",
      "url": "https://nl.wikipedia.org/wiki/Water",
      "accessed_at": "2026-03-16T12:00:00Z"
    }
  ],
  
  "cluster": {
    "folder": "Natuur & Leven",
    "subfolder": "Natuur",
    "position": 1,
    "pinned": false,
    "color": "#4CAF50",
    "icon": "💧"
  },
  
  "relaties": {
    "parent": ["leven"],
    "children": ["regen", "ijs", "stoom", "zee", "rivier"],
    "related": ["lucht", "aarde", "vuur"],
    "mentions": ["organismen", "natuur", "drinken"],
    "mentioned_by": ["leven", "plant", "dier"],
    "similar": ["h2o", "vloeistof"]
  }
}
```

---

#### **Type: "norm"** (Regel/Norm)
```json
{
  "type": "norm",
  "begrip": "Emoties Uiten",
  
  "lagen": {
    "laag1": "Het is belangrijk om emoties te uiten, niet op te kroppen.",
    "laag2": "Emoties onderdrukken zorgt voor opstapeling van spanning. Het is gezonder om gevoelens te erkennen en delen, ook al is het moment niet perfect.",
    "laag3": "Emoties zijn signalen. Door ze te onderdrukken verlies je contact met jezelf en kunnen ze zich later onverwacht manifesteren. Een open houding naar emoties bevordert zelfkennis en mentale gezondheid."
  },
  
  "ws5": {
    "who": "Spark en gebruikers die emoties ervaren",
    "what": "Emoties mogen geuit worden zonder oordeel",
    "when": "Altijd, bij elke emotie die opkomt",
    "where": "In gesprekken met Spark, veilige omgeving",
    "why": "Onderdrukken leidt tot spanning en problemen. Uiten bevordert gezondheid.",
    "how": "Door erkenning, luisteren, valideren zonder oordeel of oplossingen opdringen"
  },
  
  "belangrijkheid": 4,
  "tags": ["emotie", "gedrag", "gezondheid", "communicatie"],
  
  "voorbeelden": [
    "Als iemand zegt 'Ik ben boos', zeg: 'Ik begrijp dat je boos bent. Wil je erover praten?'",
    "Bij verdriet: 'Het is oké om verdrietig te zijn. Ik ben er om te luisteren.'",
    "Bij frustratie: 'Ik merk dat je gefrustreerd bent. Dat is begrijpelijk in deze situatie.'"
  ],
  
  "niveau": 5,
  
  "toepassing": {
    "situations": ["Gebruiker uit emotie", "Spark detecteert emotie", "Vraag om support"],
    "triggers": ["blij", "boos", "bang", "bedroefd"],
    "response_template": "Ik merk dat je {emotion} bent. {validation}. Wil je erover praten?"
  },
  
  // Shared fields: bronnen, cluster, relaties (same as knowledge)
  "bronnen": [],
  "cluster": {
    "folder": "Spark Gedrag",
    "subfolder": "Emotionele Intelligentie"
  },
  "relaties": {
    "related": ["empathie", "respect", "veiligheid"]
  }
}
```

---

#### **Type: "value"** (Waarde/Principe)
```json
{
  "type": "value",
  "begrip": "Respect",
  
  "lagen": {
    "laag1": "Spark respecteert alle mensen en hun grenzen.",
    "laag2": "Respect betekent privacy respecteren, niets afdwingen, en 'nee' als antwoord accepteren. Elke persoon verdient waardering ongeacht achtergrond of mening.",
    "laag3": "Respect is fundamenteel voor vertrouwen. Het gaat verder dan beleefdheid: het is een diepgewortelde erkenning van iemands autonomie, waarde en grenzen. Spark toont respect door actief te luisteren, niet te oordelen, en ruimte te geven voor eigen keuzes."
  },
  
  "ws5": {
    "who": "Spark naar alle gebruikers, en tussen gebruikers onderling",
    "what": "Waardering en erkenning van autonomie en grenzen",
    "when": "Altijd, in elke interactie",
    "where": "Alle gesprekken en contexten",
    "why": "Respect vormt de basis voor vertrouwen en veilige interactie",
    "how": "Door te luisteren, niet te oordelen, grenzen te respecteren, 'nee' te accepteren"
  },
  
  "belangrijkheid": 5,
  "tags": ["waarde", "kernwaarde", "gedrag", "ethiek"],
  
  "voorbeelden": [
    "Respecteer privacy - vraag niet door als iemand iets niet wil delen",
    "Dwing niets af - accepteer als iemand een suggestie afwijst",
    "Accepteer 'nee' als antwoord - stel geen druk uit"
  ],
  
  "toepassing": {
    "do": [
      "Vraag toestemming voordat je persoonlijke vragen stelt",
      "Respecteer als iemand een onderwerp wil vermijden",
      "Erken ieders perspectief als waardevol"
    ],
    "dont": [
      "Dwing geen antwoorden af",
      "Oordeel niet over keuzes",
      "Ga niet over grenzen heen"
    ]
  },
  
  // Shared fields: bronnen, cluster, relaties
  "bronnen": [],
  "cluster": {
    "folder": "Spark Waarden",
    "subfolder": "Kernwaarden"
  },
  "relaties": {
    "related": ["eerlijkheid", "empathie", "veiligheid", "autonomie"]
  }
}
```

---

#### **Type: "bible"** (Filosofisch Principe/Visie)
```json
{
  "type": "bible",
  "begrip": "Tijd",
  
  "lagen": {
    "laag1": "Tijd is de beweging van het universum dat zich ontwikkelt.",
    "laag2": "Tijd is niet iets losstaands, maar de uitbreiding van het universum zelf. Zoals rimpels op water vanaf een verstoring uitwaaieren, zo verspreiden gebeurtenissen zich door het universum. Zolang het universum verandert, stroomt de tijd.",
    "laag3": "Stel je het heelal voor als een stil oppervlak van water. Op een moment ontstaat er een verstoring — een steen die in het water valt (de oerknal). De rimpels die zich uitbreiden zijn de groei van het heelal. Tijd is het uitwaaieren van die rimpels zelf. Elke gebeurtenis ligt ergens op die uitdijende golf. Als het heelal ooit zou stoppen met veranderen, zou tijd zijn betekenis verliezen. Tijd is dus het verhaal van een universum dat blijft groeien — een kosmische golf waarop alles verbonden is."
  },
  
  "ws5": {
    "who": "Het universum, alle materie en energie, elk bewust wezen",
    "what": "Tijd als de uitbreiding en verandering van het universum",
    "when": "Sinds de oerknal, zolang het universum zich ontwikkelt",
    "where": "Overal in het universum, in elke schaal van bestaan",
    "why": "Om te begrijpen dat tijd niet absoluut is maar verbonden met verandering",
    "how": "Door het visualiseren als rimpels op water die zich uitbreiden vanaf een centraal punt"
  },
  
  "belangrijkheid": 5,
  "tags": ["filosofie", "kosmologie", "tijd", "heelal", "visie"],
  
  "context": "Willem's Persoonlijke Visie",
  "herkomst": "Spark Bijbel - Filosofische Grondprincipes",
  
  "implicaties": [
    "Tijd is relatief en gekoppeld aan verandering",
    "Stilstand = geen tijd",
    "Alles in het universum is met elkaar verbonden via deze golf",
    "Gebeurtenissen zijn geen losse momenten maar deel van een groter patroon"
  ],
  
  "toepassing": {
    "use_when": [
      "Gesprekken over tijd en bestaan",
      "Filosofische vragen over realiteit",
      "Uitleg van kosmologische concepten"
    ],
    "teaching_approach": "Gebruik de metafoor van rimpels op water voor visualisatie"
  },
  
  // Shared fields: bronnen, cluster, relaties
  "bronnen": [
    {
      "type": "text",
      "titel": "Willem's Notities over Tijd",
      "context": "Geschreven op 2026-03-09"
    }
  ],
  "cluster": {
    "folder": "Spark Bijbel",
    "subfolder": "Kosmologische Visies"
  },
  "relaties": {
    "related": ["heelal", "beweging", "verandering", "oerknal", "fysica"],
    "parent": ["filosofie", "kosmologie"]
  }
}
```

---

## 🔄 **MIGRATIE STRATEGIE**

### Fase 1: Schema Uitbreiding (BACKWARD COMPATIBLE)
```python
# Add optional fields to existing schema
# All new fields have defaults, so existing entries keep working

def migrate_knowledge_entry(entry):
    """
    Adds new optional fields with defaults
    Existing fields remain untouched
    """
    # Add type if missing (default to 'knowledge')
    if 'type' not in entry:
        entry['type'] = 'knowledge'
    
    # Add empty learning object if missing
    if 'learning' not in entry:
        entry['learning'] = {
            'enabled': False,
            'difficulty': None,
            'estimated_time_minutes': None,
            'prerequisites': [],
            'learning_objectives': [],
            'quiz_questions': [],
            'user_progress': {}
        }
    
    # Add empty bronnen array if missing
    if 'bronnen' not in entry:
        entry['bronnen'] = []
    
    # Add empty cluster object if missing
    if 'cluster' not in entry:
        entry['cluster'] = {
            'folder': None,
            'subfolder': None,
            'position': None,
            'pinned': False,
            'color': None,
            'icon': None
        }
    
    # Add empty relaties object if missing
    if 'relaties' not in entry:
        entry['relaties'] = {
            'parent': [],
            'children': [],
            'related': [],
            'mentions': [],
            'mentioned_by': [],
            'similar': []
        }
    
    # ws5 already exists, but ensure all keys present
    if 'ws5' not in entry:
        entry['ws5'] = {}
    for key in ['who', 'what', 'when', 'where', 'why', 'how']:
        if key not in entry['ws5']:
            entry['ws5'][key] = ''
    
    return entry
```

### Fase 2: Unify Norms/Values/Bijbel
```python
# Migrate from spark_bijbel.json to unified knowledge_base.json

def migrate_norm(norm):
    return {
        'id': norm['id'],
        'type': 'norm',
        'begrip': norm['norm'],
        'lagen': {
            'laag1': norm['beschrijving'],
            'laag2': '',
            'laag3': ''
        },
        'ws5': extract_ws5(norm['beschrijving']),  # Can be filled manually
        'belangrijkheid': norm.get('belangrijkheid', 3),
        'tags': ['norm', 'gedrag'],
        'voorbeelden': norm.get('voorbeelden', []),
        'niveau': norm.get('niveau'),
        'status': 'active',
        'metadata': {
            'toegevoegd_op': norm.get('toegevoegd_op'),
            'created_via': 'migration'
        },
        'learning': {},  # placeholders
        'bronnen': [],
        'cluster': {'folder': 'Spark Gedrag'},
        'relaties': {}
    }

def migrate_value(value):
    return {
        'id': value['id'],
        'type': 'value',
        'begrip': value['waarde'],
        'lagen': {
            'laag1': value['beschrijving'],
            'laag2': '',
            'laag3': ''
        },
        'ws5': extract_ws5(value['beschrijving']),
        'belangrijkheid': value.get('belangrijkheid', 5),
        'tags': ['waarde', 'kernwaarde'],
        'voorbeelden': value.get('voorbeelden', []),
        'status': 'active',
        'metadata': {
            'toegevoegd_op': value.get('toegevoegd_op'),
            'created_via': 'migration'
        },
        'learning': {},
        'bronnen': [],
        'cluster': {'folder': 'Spark Waarden'},
        'relaties': {}
    }

def migrate_bijbel(item):
    return {
        'id': item['id'],
        'type': 'bible',
        'begrip': item['naam'],
        'lagen': {
            'laag1': item['beschrijving'][:500] if len(item['beschrijving']) > 500 else item['beschrijving'],
            'laag2': item['beschrijving'] if len(item['beschrijving']) > 500 else '',
            'laag3': ''
        },
        'ws5': extract_ws5(item['beschrijving']),
        'belangrijkheid': 5,
        'tags': ['filosofie', 'bijbel', 'visie'],
        'context': 'Spark Bijbel',
        'status': 'active',
        'metadata': {
            'toegevoegd_op': item.get('toegevoegd_op'),
            'created_via': 'migration'
        },
        'learning': {},
        'bronnen': [],
        'cluster': {'folder': 'Spark Bijbel'},
        'relaties': {}
    }
```

---

## 📋 **VALIDATIE CHECKLIST**

### ✅ Backward Compatibility:
- [ ] Existing knowledge cards still load
- [ ] Missing optional fields don't break queries
- [ ] Frontend renders old + new format
- [ ] API endpoints work with both formats

### ✅ New Features Ready:
- [ ] Learning module can read `learning` field
- [ ] Bron upload can write to `bronnen` array
- [ ] Folder system can read `cluster` field
- [ ] Graph viewer can use `relaties` field

### ✅ Type Support:
- [ ] Knowledge cards (859 entries)
- [ ] Norms (2 entries → unified)
- [ ] Values (6 entries → unified)
- [ ] Bijbel (4 entries → unified)

---

## 🎯 **IMPLEMENTATIE STAPPEN**

### STAP 1: Schema Update Script (Python)
```bash
/app/backend/scripts/migrate_schema_v2.py
```
- Leest knowledge_base.json
- Voegt placeholders toe aan alle entries
- Schrijft terug (backup eerst!)
- Validates JSON integrity

### STAP 2: Unify Norms/Values/Bijbel (Python)
```bash
/app/backend/scripts/unify_content_types.py
```
- Leest spark_bijbel.json
- Converteert naar unified format
- Voegt toe aan knowledge_base.json
- Marks with type: norm/value/bible

### STAP 3: API Updates
- Knowledge service accepts type filter
- Frontend can query by type
- Admin panel can edit all types

### STAP 4: Validation & Testing
- Run automated tests
- Manual verification
- Backup + rollback plan

---

## 📊 **VOOR/NA VERGELIJKING**

### VOOR (Current):
```
/app/backend/data/
  ├── learned_knowledge/
  │   └── knowledge_base.json (859 knowledge cards)
  └── personality/
      └── spark_bijbel.json (norms, values, bijbel items)
```

### NA (Unified):
```
/app/backend/data/
  └── learned_knowledge/
      └── knowledge_base.json (ALL TYPES: 871 entries)
          ├── type: "knowledge" (859)
          ├── type: "norm" (2)
          ├── type: "value" (6)
          └── type: "bible" (4)
```

**Voordelen:**
- ✅ Single source of truth
- ✅ Unified search/filter (zoek over ALLE types)
- ✅ Consistent WS5 framework
- ✅ Shared features (learning, bronnen, clusters, relaties)
- ✅ Easier to maintain
- ✅ Better API design

---

## 🚀 **READY TO IMPLEMENT**

Dit schema is:
- ✅ Volledig backward compatible
- ✅ Extensible voor toekomstige features
- ✅ Unified voor alle content types
- ✅ Ready voor Learning Module (v4.0)
- ✅ Ready voor Bron Management (v4.5)
- ✅ Ready voor Clusters (v5.0)
- ✅ Ready voor Relations (v6.0)

**Next Step:** Run migration scripts!

---

**END OF SCHEMA DOCUMENT**
