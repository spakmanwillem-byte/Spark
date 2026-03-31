# 📁 User Data Architectuur - Spark Core 4.1

## Huidige Structuur

```
/app/backend/data/
├── users/
│   ├── user-001/              ← Persoonlijke data per user (ID-based)
│   │   ├── agenda.json
│   │   ├── dagboek.json
│   │   ├── settings.json
│   │   ├── achievements.json
│   │   ├── expenses.json
│   │   ├── income.json
│   │   └── [MOET TOEVOEGEN: sounds.json]
│   │
│   ├── user-002/
│   ├── spark-system/          ← Systeem user (global data)
│   └── ...
│
├── system/
│   ├── sound_mappings.json    ← CENTRAAL (alle users mixed)
│   ├── user_files_index.json
│   └── ...
│
└── media/
    ├── sounds/                ← CENTRAAL (alle audio files mixed)
    └── users/                 ← Per-user media (files)
```

---

## ❌ Probleem:

**Sounds zijn nu CENTRAAL opgeslagen:**
- `sound_mappings.json` bevat ALLE users (user-001, user-002, spark-system)
- Mixed data = moeilijker te beheren
- Privacy concerns (één file met alles)
- Geen duidelijke ownership

**Vergelijk met andere data:**
- ✅ Agenda → per user folder (`user-001/agenda.json`)
- ✅ Dagboek → per user folder (`user-001/dagboek.json`)
- ✅ Settings → per user folder (`user-001/settings.json`)
- ❌ Sounds → centraal (`system/sound_mappings.json`)

---

## ✅ Verbeterde Structuur

### **Voorstel: User-Specific Sound Storage**

```
/app/backend/data/users/
├── user-001/
│   ├── agenda.json
│   ├── dagboek.json
│   ├── settings.json
│   ├── sounds.json            ← NIEUW: Eigen geluiden
│   └── conversations.json     ← NIEUW: Eigen chats
│
├── user-002/
│   ├── sounds.json            ← Aparte file per user
│   └── ...
│
└── spark-system/
    ├── sounds.json            ← Global systeem geluiden
    └── settings.json
```

### **Media Storage (Audio Files)**

```
/app/backend/data/media/sounds/
├── user-001/
│   ├── koe_1234567890.mp3     ← User-001's audio files
│   ├── hoi_1234567891.mp3
│   └── ...
│
├── user-002/
│   ├── yes_1234567892.mp3     ← User-002's audio files
│   └── ...
│
└── spark-system/
    ├── succes_1234567893.mp3  ← Global system sounds
    ├── error_1234567894.mp3
    └── ...
```

---

## 📋 user-001/sounds.json Format

```json
{
  "user_id": "user-001",
  "sounds": [
    {
      "id": "sound_1",
      "word": "koe",
      "display_name": "Koe",
      "frequency": "every",
      "file": "koe_1234567890.mp3",
      "filepath": "/app/backend/data/media/sounds/user-001/koe_1234567890.mp3",
      "visibility": "private",
      "type": "user",
      "created_at": "2026-03-29T18:30:00Z",
      "play_count": 12
    }
  ]
}
```

---

## 🔄 Migratie Plan

### **Stap 1: Backend API Update**

**Huidige API:**
```python
# Centraal bestand
SOUNDS_MAPPING_FILE = "/app/backend/data/system/sound_mappings.json"

def load_mappings():
    # Load ALL users from central file
    with open(SOUNDS_MAPPING_FILE) as f:
        return json.load(f)
```

**Nieuwe API:**
```python
def get_user_sounds_file(user_id: str) -> str:
    """Get path to user's sounds.json"""
    if user_id == 'spark-system':
        return "/app/backend/data/users/spark-system/sounds.json"
    return f"/app/backend/data/users/{user_id}/sounds.json"

def load_user_sounds(user_id: str):
    """Load only this user's sounds"""
    filepath = get_user_sounds_file(user_id)
    if os.path.exists(filepath):
        with open(filepath) as f:
            return json.load(f)
    return {"user_id": user_id, "sounds": []}

def load_sounds_for_playback(user_id: str):
    """Load sounds user should hear (own + spark-system)"""
    user_sounds = load_user_sounds(user_id)
    spark_sounds = load_user_sounds('spark-system')
    
    return {
        "sounds": user_sounds.get("sounds", []) + spark_sounds.get("sounds", [])
    }
```

### **Stap 2: Migratie Script**

```python
# Migrate central sound_mappings.json to per-user files
def migrate_sounds():
    central_file = "/app/backend/data/system/sound_mappings.json"
    
    with open(central_file) as f:
        data = json.load(f)
    
    # Group by user_id
    user_sounds = {}
    for mapping in data.get("mappings", []):
        uid = mapping.get("user_id", "unknown")
        if uid not in user_sounds:
            user_sounds[uid] = []
        user_sounds[uid].append(mapping)
    
    # Save to individual files
    for user_id, sounds in user_sounds.items():
        user_dir = f"/app/backend/data/users/{user_id}"
        os.makedirs(user_dir, exist_ok=True)
        
        output = {
            "user_id": user_id,
            "sounds": sounds
        }
        
        with open(f"{user_dir}/sounds.json", 'w') as f:
            json.dump(output, f, indent=2)
    
    # Backup central file
    shutil.copy(central_file, central_file + ".backup")
    print(f"✅ Migrated {len(user_sounds)} users")
```

### **Stap 3: Move Audio Files**

```python
def migrate_audio_files():
    """Move audio files to user-specific folders"""
    sounds_dir = "/app/backend/data/media/sounds"
    
    # Create user folders
    for user_id in ["user-001", "user-002", "spark-system"]:
        user_sound_dir = f"{sounds_dir}/{user_id}"
        os.makedirs(user_sound_dir, exist_ok=True)
    
    # Read mappings to know which file belongs to which user
    # Move files accordingly
    # ...
```

---

## 🎯 Voordelen

### **✅ Privacy & Ownership**
- Elke user heeft eigen `sounds.json`
- Duidelijke data ownership
- Geen mixed data van alle users

### **✅ Consistentie**
- Net zoals `agenda.json`, `dagboek.json`, `settings.json`
- Uniform data model
- Makkelijker te begrijpen

### **✅ Performance**
- Kleinere files (alleen eigen data)
- Sneller laden
- Minder parsing overhead

### **✅ Backup & Export**
- Per-user backup mogelijk
- User kan eigen data exporteren
- GDPR compliant

### **✅ Relaties & Sharing (Later)**
```json
// user-001/sounds.json
{
  "sounds": [...],
  "shared_with": ["user-002", "user-003"],  // Who can hear my sounds
  "can_hear_from": ["user-005"]              // Whose sounds I can hear
}
```

---

## 🔗 Relatie Herkenning

**Voor later (met mixer):**

```json
// user-001/relationships.json
{
  "user_id": "user-001",
  "friends": ["user-002", "user-003"],
  "blocked": [],
  "sound_sharing": {
    "allow_from": ["user-002"],           // Ik hoor sounds van user-002
    "share_with": ["user-002", "user-003"] // Zij horen mijn sounds
  }
}
```

**API:**
```python
GET /api/sounds/mappings?user_id=user-001
→ Returns:
  - user-001's own sounds
  - spark-system sounds (global)
  - sounds from users in sound_sharing.allow_from
```

---

## 📝 Implementatie Prioriteit

### **Nu (P0):**
1. ✅ Centraal systeem werkt (sound_mappings.json)
2. ✅ Filtering op user_id (backend API)
3. ✅ Privacy (alleen eigen + spark-system)

### **Binnenkort (P1):**
1. Migratie naar per-user `sounds.json`
2. Audio files per user folder
3. Update API routes
4. Test met bestaande data

### **Later (P2):**
1. Relatie systeem (friends, sharing)
2. Audio mixer integratie
3. Community sounds tab
4. Sharing controls in UI

---

## 💡 Conclusie

**Huidige aanpak werkt**, maar voor **schaalbaarheid** en **consistentie** is per-user storage beter:

- ✅ **Agenda** → `user-001/agenda.json`
- ✅ **Dagboek** → `user-001/dagboek.json`
- ✅ **Settings** → `user-001/settings.json`
- 🔄 **Sounds** → `user-001/sounds.json` (VOORSTEL)
- 🔄 **Files** → `user-001/files.json` (VOORSTEL)
- 🔄 **Conversations** → `user-001/conversations.json`

**Wil je dat ik de migratie nu doe?** Of eerst verder met huidige structuur (werkt ook!)
