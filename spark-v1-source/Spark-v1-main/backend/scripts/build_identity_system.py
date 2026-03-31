#!/usr/bin/env python3
"""
Phase 1: Identity System Implementation
Doel: Bouw gestructureerde identity files uit bestaande KB data
Filosofie: Structuur geven, niet opschonen
"""

import json
from pathlib import Path
from datetime import datetime

# Paths
BACKEND_DATA = Path('/app/backend/data')
KB_PATH = BACKEND_DATA / 'learned_knowledge' / 'knowledge_base.json'
IDENTITIES_ROOT = BACKEND_DATA / 'identities'

def create_directory_structure():
    """Maak identity directory structuur"""
    
    print("\n" + "="*70)
    print("📁 CREATE IDENTITY DIRECTORY STRUCTURE")
    print("="*70)
    
    directories = [
        IDENTITIES_ROOT / 'roadkill',
        IDENTITIES_ROOT / 'spark_your_life',
        IDENTITIES_ROOT / 'spark',
        IDENTITIES_ROOT / 'willem',
        IDENTITIES_ROOT / '_schema',
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"   ✅ {directory.relative_to(BACKEND_DATA)}")
    
    return True

def load_kb():
    """Laad knowledge base"""
    with open(KB_PATH, 'r') as f:
        return json.load(f)

def find_kb_entry(kb_data, entry_id):
    """Find KB entry by ID"""
    entries = kb_data.get('knowledge_entries', [])
    return next((e for e in entries if e.get('id') == entry_id), None)

def build_roadkill_gamer_identity(kb_data):
    """Build Roadkill Gamer identity uit KB data"""
    
    print("\n🎮 Building Roadkill Gamer Identity...")
    
    # Source: Roadkill (gamertag) entry
    source_id = "12465c90-1ba7-447c-a370-6ba87f45e255"
    source_entry = find_kb_entry(kb_data, source_id)
    
    if not source_entry:
        print("   ⚠️  Source entry not found")
        return None
    
    lagen = source_entry.get('lagen', {})
    
    identity = {
        "identity_id": "roadkill_gamer",
        "type": "personal_brand",
        "schema_version": "1.0",
        "core": {
            "name": "Roadkill",
            "tagline": "Run over, but get back up stronger",
            "owner": "Willem Spakman",
            "origin": {
                "original_name": "Redrum",
                "inspiration": "The Shining",
                "change_reason": "Veranderd naar Roadkill voor positieve betekenis: leren van fouten en sterker terugkomen",
                "era": "MSX-computers era"
            },
            "description": lagen.get('laag1', ''),
            "philosophy": "Leren van fouten en sterker terugkomen. Het omarmen van imperfectie.",
            "core_message": "Fouten maken hoort bij leren. Je kunt keer op keer vallen en toch sterker terugkomen."
        },
        "evolution": {
            "start": "Gaming",
            "growth": "Begon met gaming maar groeide uit tot een community die mensen samenbrengt",
            "current": "Een beweging voor verbinding, respect en positiviteit"
        },
        "values": [
            "Authenticiteit",
            "Verbinding",
            "Respect",
            "Positiviteit",
            "Imperfectie omarmen",
            "Veerkracht",
            "Zonder oordeel"
        ],
        "impact": {
            "documented": "Autistische kinderen die via herkenbare hoodies verbinding vonden",
            "reach": "Community van supporters en mensen die hulp nodig hebben"
        },
        "relations": [
            {
                "identity_id": "willem",
                "type": "owner",
                "description": "Roadkill is Willem Spakman's gamertag"
            },
            {
                "identity_id": "roadkill_community",
                "type": "evolved_into",
                "description": "Gaming identity groeide uit tot community beweging"
            },
            {
                "identity_id": "spark_your_life",
                "type": "supports",
                "description": "Roadkill Community steunt Spark Your Life zorgboerderij"
            }
        ],
        "kb_sources": {
            "primary": source_id,
            "source_type": "bio",
            "detected_by": source_entry.get('detected_by', ''),
            "last_updated": source_entry.get('datum', '')
        },
        "metadata": {
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "version": "1.0",
            "extracted_from_kb": True,
            "organic_growth": True,
            "note": "Gebouwd uit bestaande KB data - brondata behouden"
        }
    }
    
    return identity

def build_roadkill_community_identity(kb_data):
    """Build Roadkill Community identity uit KB data"""
    
    print("🌐 Building Roadkill Community Identity...")
    
    source_id = "856d362f-aead-46e6-a0de-9c208ecc756e"
    source_entry = find_kb_entry(kb_data, source_id)
    
    if not source_entry:
        print("   ⚠️  Source entry not found")
        return None
    
    lagen = source_entry.get('lagen', {})
    
    identity = {
        "identity_id": "roadkill_community",
        "type": "community",
        "schema_version": "1.0",
        "core": {
            "name": "Roadkill Community",
            "tagline": "Community van supporters die Spark Your Life steunen",
            "mission": "Een inclusieve beweging om mensen te helpen die anders door de mazen van het net vallen",
            "description": lagen.get('laag1', ''),
            "purpose": "Spark Your Life steunen door merchandise te kopen"
        },
        "composition": {
            "supporters": "Mensen die Roadkill merchandise kopen",
            "beneficiaries": "Cliënten van de zorgboerderij",
            "combined": "Supporters en cliënten vormen samen de community"
        },
        "target_audience": {
            "primary": "Mensen die tussen wal en schip vallen",
            "specific_groups": [
                "Mensen die nergens bij horen",
                "Uitgeslotenen",
                "Mensen die hulp nodig hebben",
                "Mensen die door de mazen van het net vallen"
            ]
        },
        "values": [
            "Verbinding",
            "Respect",
            "Positiviteit",
            "Inclusiviteit",
            "Zonder oordeel"
        ],
        "impact": {
            "documented_cases": [
                "Autistische kinderen die via herkenbare hoodies verbinding vonden",
                "Mensen die nergens anders terecht konden en nu op de zorgboerderij groeien"
            ],
            "mechanism": "Elk verkocht kledingstuk helpt de droom van een inclusieve plek voor iedereen dichterbij te brengen"
        },
        "relations": [
            {
                "identity_id": "roadkill_shop",
                "type": "funded_by",
                "description": "Community wordt ondersteund via merch sales"
            },
            {
                "identity_id": "spark_your_life",
                "type": "supports",
                "description": "Community steunt de zorgboerderij"
            },
            {
                "identity_id": "roadkill_gamer",
                "type": "evolved_from",
                "description": "Ontstaan uit de gaming identity"
            }
        ],
        "kb_sources": {
            "primary": source_id,
            "source_type": "bio",
            "detected_by": source_entry.get('detected_by', '')
        },
        "metadata": {
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "version": "1.0",
            "extracted_from_kb": True
        }
    }
    
    return identity

def build_roadkill_business_identity(kb_data):
    """Build Roadkill Shop identity uit KB data"""
    
    print("💼 Building Roadkill Shop Identity...")
    
    source_id = "cedcf046-2a19-48f9-a1f0-b5cbfe6690b9"
    source_entry = find_kb_entry(kb_data, source_id)
    
    if not source_entry:
        print("   ⚠️  Source entry not found")
        return None
    
    lagen = source_entry.get('lagen', {})
    metadata_entry = source_entry.get('metadata', {})
    
    identity = {
        "identity_id": "roadkill_shop",
        "type": "business",
        "schema_version": "1.0",
        "core": {
            "name": "Roadkill Shop",
            "tagline": "Duurzame merchandise die Spark Your Life zorgboerderij steunt",
            "description": lagen.get('laag1', ''),
            "business_model": "Merchandise sales",
            "purpose": "Financiering van Spark Your Life zorgboerderij"
        },
        "contact": {
            "website": metadata_entry.get('website', 'https://roadkillshop.com/'),
            "email": metadata_entry.get('email', '')
        },
        "products": {
            "types": ["hoodies", "petten", "merchandise"],
            "materials": {
                "type": "Duurzaam",
                "specifics": ["gerecycled materiaal", "biologisch materiaal"]
            },
            "meaning": "Meer dan kleding - een symbool van verbinding, respect, en steun voor mensen die tussen wal en schip vallen"
        },
        "values": {
            "respect": "Iedereen verdient waardering",
            "veerkracht": "Leren van fouten en sterker terugkomen",
            "verbinding": "Mensen samenbrengen en inspireren",
            "duurzaamheid": "Bewuste keuzes maken",
            "positiviteit": "Constructief benaderen"
        },
        "sustainability": {
            "focus": "Duurzame materialen",
            "approach": "Gerecycled en biologisch materiaal gebruiken",
            "impact": "Bewuste keuzes maken voor mens en planeet"
        },
        "relations": [
            {
                "identity_id": "spark_your_life",
                "type": "funds",
                "description": "Primaire financiering voor de zorgboerderij"
            },
            {
                "identity_id": "roadkill_community",
                "type": "enables",
                "description": "Verkoopt merch aan community supporters"
            }
        ],
        "kb_sources": {
            "primary": source_id,
            "source_type": "bio",
            "detected_by": source_entry.get('detected_by', '')
        },
        "metadata": {
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "version": "1.0",
            "extracted_from_kb": True
        }
    }
    
    return identity

def build_roadkill_core_philosophy():
    """Build shared Roadkill philosophy"""
    
    print("📖 Building Roadkill Core Philosophy...")
    
    # Dit is de gedeelde laag4 uit alle Roadkill entries
    philosophy = {
        "identity_id": "roadkill_core_philosophy",
        "type": "shared_philosophy",
        "schema_version": "1.0",
        "philosophy": "Roadkill staat voor authenticiteit en verbinding. Het draait om het omarmen van imperfectie en het creëren van een community die elkaar ondersteunt zonder oordeel.",
        "core_principles": [
            "Authenticiteit boven perfectie",
            "Verbinding boven isolatie",
            "Imperfectie omarmen",
            "Zonder oordeel ondersteunen",
            "Leren van fouten",
            "Sterker terugkomen na tegenslagen"
        ],
        "tagline": "Run over, but get back up stronger",
        "used_by": [
            "roadkill_gamer",
            "roadkill_community",
            "roadkill_shop"
        ],
        "note": "Deze filosofie is geëxtraheerd uit laag4 van alle Roadkill KB entries (was duplicaat, nu single source)",
        "metadata": {
            "created_at": datetime.now().isoformat(),
            "version": "1.0",
            "extracted_from": "KB entries laag4 (shared content)"
        }
    }
    
    return philosophy

def build_spark_your_life_identity(kb_data):
    """Build Spark Your Life identity uit KB data"""
    
    print("✨ Building Spark Your Life Identity...")
    
    source_id = "6fde8072-7e2d-45a4-ad55-1417fbaabe73"
    source_entry = find_kb_entry(kb_data, source_id)
    
    if not source_entry:
        print("   ⚠️  Source entry not found")
        return None
    
    lagen = source_entry.get('lagen', {})
    
    identity = {
        "identity_id": "spark_your_life",
        "type": "social_enterprise",
        "schema_version": "1.0",
        "core": {
            "name": "Spark Your Life",
            "type": "Zorgboerderij",
            "tagline": "Voor mensen die tussen wal en schip vallen",
            "description": lagen.get('laag1', ''),
            "founder": "Willem Spakman"
        },
        "mission": lagen.get('laag2', '').replace('Missie:', '').strip(),
        "vision": "Een inclusieve plek waar iedereen die tussen wal en schip valt kan groeien en ontwikkelen",
        "approach": {
            "core_method": "Zingevende arbeid in de natuur + persoonlijke coaching + ondersteunende community",
            "components": [
                "Zingevende arbeid in de natuur",
                "Persoonlijke coaching",
                "Ondersteunende community",
                "Inspirerende omgevingen"
            ]
        },
        "target_audience": {
            "primary": "Mensen die tussen wal en schip vallen",
            "specific": [
                "Mensen die nergens bij horen",
                "Uitgeslotenen",
                "Mensen die hulp nodig hebben",
                "Mensen die door de mazen van het net vallen"
            ],
            "note": "KB laag3 had incomplete velden - aangevuld met context uit andere lagen"
        },
        "services": {
            "primary": ["Coaching", "Begeleiding", "Zorgboerderij"],
            "focus_areas": [
                "Zelfredzaamheid bevorderen",
                "Persoonlijke groei ondersteunen",
                "Verbinding tussen mensen creëren"
            ]
        },
        "funding_model": {
            "primary_source": "Roadkill Shop merchandise sales",
            "mechanism": "Community supporters kopen merch om zorgboerderij te financieren"
        },
        "values": [
            "Zelfredzaamheid",
            "Persoonlijke groei",
            "Verbinding",
            "Inclusiviteit",
            "Respect voor iedereen",
            "Veerkracht"
        ],
        "relations": [
            {
                "identity_id": "willem",
                "type": "founded_by",
                "description": "Willem's droom en project"
            },
            {
                "identity_id": "roadkill_shop",
                "type": "funded_by",
                "description": "Primaire financiering via merchandise verkoop"
            },
            {
                "identity_id": "roadkill_community",
                "type": "supported_by",
                "description": "Community van supporters die bijdragen"
            }
        ],
        "kb_sources": {
            "primary": source_id,
            "source_type": "bio",
            "detected_by": source_entry.get('detected_by', ''),
            "note": "Laag3 was incomplete (had lege velden) - aangevuld met context"
        },
        "metadata": {
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "version": "1.0",
            "extracted_from_kb": True,
            "incomplete_source_handled": True
        }
    }
    
    return identity

def save_identity_file(identity, filename):
    """Save identity to JSON file"""
    if not identity:
        return False
    
    filepath = IDENTITIES_ROOT / identity['identity_id'].split('_')[0] if '_' not in identity['identity_id'][:8] else IDENTITIES_ROOT / 'roadkill' / f"{filename}.json"
    
    # Bepaal correct pad
    identity_id = identity['identity_id']
    if identity_id.startswith('roadkill'):
        filepath = IDENTITIES_ROOT / 'roadkill' / f"{filename}.json"
    elif identity_id == 'spark_your_life':
        filepath = IDENTITIES_ROOT / 'spark_your_life' / 'core.json'
    else:
        filepath = IDENTITIES_ROOT / f"{identity_id}" / f"{filename}.json"
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(identity, f, indent=2, ensure_ascii=False)
    
    print(f"   ✅ Saved: {filepath.relative_to(BACKEND_DATA)}")
    return True

def create_kb_sources_mapping():
    """Create mapping van KB entries naar identity files"""
    
    print("\n📋 Creating KB Sources Mapping...")
    
    mapping = {
        "description": "Mapping van Knowledge Base entries naar Identity files voor traceability",
        "created_at": datetime.now().isoformat(),
        "mappings": {
            "12465c90-1ba7-447c-a370-6ba87f45e255": {
                "kb_entry": "Roadkill (gamertag)",
                "maps_to": [
                    "roadkill/gamer.json",
                    "roadkill/core_philosophy.json"
                ],
                "usage": "Primary source voor gamer identity en shared philosophy"
            },
            "856d362f-aead-46e6-a0de-9c208ecc756e": {
                "kb_entry": "Roadkill Community",
                "maps_to": ["roadkill/community.json"],
                "usage": "Primary source voor community identity"
            },
            "cedcf046-2a19-48f9-a1f0-b5cbfe6690b9": {
                "kb_entry": "Roadkill Shop",
                "maps_to": ["roadkill/business.json"],
                "usage": "Primary source voor business identity"
            },
            "6fde8072-7e2d-45a4-ad55-1417fbaabe73": {
                "kb_entry": "Spark Your Life",
                "maps_to": ["spark_your_life/core.json"],
                "usage": "Primary source voor Spark Your Life identity",
                "note": "Laag3 was incomplete - aangevuld met context uit andere lagen"
            }
        },
        "note": "Alle originele KB entries blijven bestaan. Deze mapping zorgt voor traceability."
    }
    
    filepath = IDENTITIES_ROOT / '_schema' / 'kb_mapping.json'
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)
    
    print(f"   ✅ Saved: {filepath.relative_to(BACKEND_DATA)}")
    return True

def create_readme():
    """Create README voor identities directory"""
    
    print("\n📄 Creating README...")
    
    readme = """# Identity System

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
"""
    
    filepath = IDENTITIES_ROOT / '_schema' / 'README.md'
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(readme)
    
    print(f"   ✅ Saved: {filepath.relative_to(BACKEND_DATA)}")
    return True

def main():
    print("🚀 PHASE 1: IDENTITY SYSTEM IMPLEMENTATION")
    print("="*70)
    print("Filosofie: Structuur geven aan organische groei")
    print("="*70)
    
    # Step 1: Create structure
    create_directory_structure()
    
    # Step 2: Load KB
    kb_data = load_kb()
    print(f"\n✅ Loaded KB: {len(kb_data.get('knowledge_entries', []))} entries")
    
    # Step 3: Build Roadkill identities
    print("\n" + "="*70)
    print("🎮 BUILDING ROADKILL IDENTITIES")
    print("="*70)
    
    roadkill_gamer = build_roadkill_gamer_identity(kb_data)
    save_identity_file(roadkill_gamer, 'gamer')
    
    roadkill_community = build_roadkill_community_identity(kb_data)
    save_identity_file(roadkill_community, 'community')
    
    roadkill_business = build_roadkill_business_identity(kb_data)
    save_identity_file(roadkill_business, 'business')
    
    roadkill_philosophy = build_roadkill_core_philosophy()
    save_identity_file(roadkill_philosophy, 'core_philosophy')
    
    # Step 4: Build Spark Your Life
    print("\n" + "="*70)
    print("✨ BUILDING SPARK YOUR LIFE IDENTITY")
    print("="*70)
    
    spark_your_life = build_spark_your_life_identity(kb_data)
    save_identity_file(spark_your_life, 'core')
    
    # Step 5: Create mapping & docs
    create_kb_sources_mapping()
    create_readme()
    
    # Summary
    print("\n" + "="*70)
    print("✅ PHASE 1 VOLTOOID!")
    print("="*70)
    print(f"\n📁 Created files:")
    print(f"   • roadkill/gamer.json")
    print(f"   • roadkill/community.json")
    print(f"   • roadkill/business.json")
    print(f"   • roadkill/core_philosophy.json")
    print(f"   • spark_your_life/core.json")
    print(f"   • _schema/kb_mapping.json")
    print(f"   • _schema/README.md")
    print(f"\n🔗 Alle bestanden traceable naar originele KB entries")
    print(f"📦 Originele KB entries blijven onaangetast")
    print(f"✨ Organische groei → Gestructureerde identity data")
    print("="*70)

if __name__ == '__main__':
    main()
