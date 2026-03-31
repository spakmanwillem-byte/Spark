# Identity System - Quick Reference

**Created:** 24 maart 2026  
**Version:** 1.1 (met Critical Rules)

---

## 📊 SYSTEM OVERVIEW

### **10 Files Created**
```
identities/
├── roadkill/
│   ├── gamer.json              (2.6K) - Personal gaming identity
│   ├── community.json          (2.8K) - Community movement
│   ├── business.json           (2.5K) - Roadkill Shop
│   └── core_philosophy.json    (1.0K) - Shared philosophy
│
├── spark_your_life/
│   └── core.json               (3.1K) - Zorgboerderij identity
│
├── spark/
│   └── core.json               (2.4K) - AI identity (Core 4.1)
│
├── willem/
│   └── core.json               (3.8K) - Willem's identity + 3-layer separation
│
└── _schema/
    ├── identity_system_rules.json (4.2K) - Critical rules & examples
    ├── kb_mapping.json            (1.3K) - Traceability
    └── README.md                  (8.1K) - Complete documentation
```

**Total Size:** 68K

---

## ⚠️ CRITICAL RULES (naam ≠ identiteit ≠ data-koppeling)

### **3-Laags Scheiding**

```
┌─────────────────────────────────────────────────────────┐
│                      WILLEM                             │
└─────────┬───────────────┬──────────────────────┬────────┘
          │               │                      │
          ▼               ▼                      ▼
   ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐
   │ AUTH LAYER  │  │DISPLAY LAYER│  │  SYSTEM LAYER    │
   │─────────────│  │─────────────│  │──────────────────│
   │ Willem      │  │ De Willem   │  │ user-001         │
   │ Spakman     │  │             │  │                  │
   │─────────────│  │─────────────│  │──────────────────│
   │ + appelsap  │  │ (visueel)   │  │ (data-koppeling) │
   │─────────────│  │─────────────│  │──────────────────│
   │ Login       │  │ UI Display  │  │ Achievements     │
   │ Database    │  │ Chat        │  │ Highscores       │
   │ Auth        │  │ Frontend    │  │ Tracking         │
   └─────────────┘  └─────────────┘  └──────────────────┘
```

### **Regels**

1. ✅ **CORRECT:**
   ```python
   user = db.find_one({'id': 'user-001'})
   achievement = {'user_id': 'user-001', 'xp': 100}
   display = user['display_layer']['display_name']  # "De Willem"
   ```

2. ❌ **FOUT:**
   ```python
   user = db.find_one({'naam': 'De Willem'})  # NOOIT DOEN
   achievement = {'naam': 'Willem Spakman'}   # NOOIT DOEN
   ```

---

## 🎯 ROADKILL ECOSYSTEM

```
        WILLEM SPAKMAN
       (Owner/Creator)
              │
      ┌───────┴───────┐
      │   ROADKILL    │ (gamertag since MSX-era)
      └───────┬───────┘
              │
    ┌─────────┼─────────┐
    │         │         │
    ▼         ▼         ▼
┌────────┐ ┌──────┐ ┌─────────┐
│ GAMER  │ │COMMUNITY│ │BUSINESS │
│Personal│ │Movement│ │  Shop   │
└────────┘ └───┬───┘ └────┬────┘
               │         funds
               │           │
               supports    │
               │           │
               ▼           ▼
          ┌────────────────────┐
          │  SPARK YOUR LIFE   │
          │   (zorgboerderij)  │
          └────────────────────┘
```

**Shared:** `core_philosophy.json` - gebruikt door alle 3 Roadkill dimensies

---

## 📋 KB SOURCES (Traceability)

| Identity File | KB Entry ID | KB Begrip |
|---------------|-------------|-----------|
| roadkill/gamer.json | `12465c90...` | Roadkill (gamertag) |
| roadkill/community.json | `856d362f...` | Roadkill Community |
| roadkill/business.json | `cedcf046...` | Roadkill Shop |
| spark_your_life/core.json | `6fde8072...` | Spark Your Life |

**Alle originele KB entries blijven bestaan** - identity files zijn gestructureerde extracties.

---

## ✅ DATA INTEGRITY CHECKLIST

- ✅ **KB unchanged:** 2113 entries (none deleted)
- ✅ **Source files intact:** spark_profile.json, users.json, etc.
- ✅ **Traceability:** kb_mapping.json links naar originele data
- ✅ **Validation:** All 9 JSON files are valid
- ✅ **3-layer separation:** Implemented in Willem identity
- ✅ **Critical rules:** Documented in identity_system_rules.json
- ✅ **README:** Complete documentation met examples

---

## 🎯 GEBRUIK

**Query identity:**
```python
from pathlib import Path
import json

# Load identity
with open('/app/backend/data/identities/roadkill/gamer.json', 'r') as f:
    roadkill = json.load(f)

# Access
philosophy = roadkill['core']['philosophy']
relations = roadkill['relations']
```

**User lookup (CORRECT):**
```python
# ALTIJD via user_id
user_id = "user-001"
user = db.users.find_one({'id': user_id}, {'_id': 0})

# Display name
display_name = user['display_layer']['display_name']  # "De Willem"

# Achievement tracking
achievement = {'user_id': user_id, 'type': 'xp', 'value': 100}
```

---

## 📝 FILOSOFIE

> "Organische groei is geen vervuiling, maar waardevolle input.  
> Incomplete metadata is acceptabel.  
> Structuur geven, niet opschonen.  
> naam ≠ identiteit ≠ data-koppeling."

---

**Next:** Phase 2 (Backwards Compatibility) of v1.5 (Tag System)? 🚀
