# 🏗️ SPARK CORE 4.1 - SYSTEEM INDELING

*Laatst bijgewerkt: 28 maart 2026*

---

## 📊 NAVIGATIE STRUCTUUR

### **KERN**
1. 👤 Mijn Profiel
2. 💬 Spark Chat

### **PRODUCTIVITEIT**
1. 📅 Agenda
2. 📝 Dagboek
3. 📋 Notities

### **FINANCIEEL**
1. 💳 Mijn Wallet (user wallet)
2. 🛒 Winkel

### **COMMUNITY & SPEL**
1. 🌟 Community
2. 🌍 Spark World
3. 🏆 Leaderboard
4. 🏅 Achievements

### **INFO**
1. 🗺️ Roadmap

### **ADMIN** (Gradatie 1 only)
1. 🧠 Knowledge Base
2. 🗺️ Knowledge Graph
3. 👑 Admin Panel

---

## 👤 MIJN PROFIEL - TABS

1. **📊 Overzicht** - Profiel samenvatting, stats, recente activiteit
2. **✏️ Bewerk Profiel** - Naam, bio, contact info aanpassen
3. **⚙️ Instellingen** - Persoonlijke voorkeuren (audio, video, thema, taal, notificaties, privacy)
4. **📁 Bestanden** - Persoonlijke bestanden beheer

**Extra:**
- ❓ Help modal (rechts boven, rood vraagteken icoon)
- 🔒 Privacy footer onderaan

---

## 👑 ADMIN PANEL - SECTIES

### **🧠 SPARK BRAIN**
- Knowledge Base (met search, filters, A-Z index)
- Snaps
- Values
- Normen

### **🎭 PERSOONLIJKHEID**
- Spark Bijbel
- Triggers
- Emoties

### **⚙️ SYSTEEM**
- Users
- Files (met syntax validation)
- Settings
- Logs
- **Wallet** (kasboeken: Spark Core, Spark Your Life, Roadkill, Personal)

### **🎮 GAME BEHEER**
- World
- Buildings
- Blueprints

---

## 💳 WALLET ARCHITECTUUR

### **User Wallet** (Mijn Profiel → verplaatst naar FINANCIEEL)
- Persoonlijke wallet per gebruiker
- Balans (EUR)
- Spark Tokens (optioneel)
- Credits (optioneel)
- Opwaarderen via bank transfer

### **System Wallets** (Admin → Wallet)
**Kasboeken (entities):**
1. **Spark Core** - Crypto trading (Bitvavo)
2. **Spark Your Life** - Community funding
3. **Roadkill** - Merch revenue
4. **Personal** - Willem persoonlijk

**Scheiding:**
- User wallet = profiel niveau
- System wallets = systeem boekhouding

---

## 🧠 KNOWLEDGE BASE

**Data:**
- 2380 entries
- 11807 graph edges
- 5.9 MB JSON

**Types:**
- `knowledge` (853 entries) - Topic kaarten → uitleg
- `unknown` (1527 entries) - Context kaarten → response

**Search & Filter:**
- 🔎 Full-text search (titel, inhoud, tags)
- 📋 Type filter (knowledge/context/snaps)
- 🔤 A-Z index
- 📊 Results count

**Structuur:**
- Lagen (1-4): Korte → Volledige uitleg
- Tags: Vrije tagging
- 5W+H: Reasoning data
- Relaties: parent, children, related, mentions

---

## 🛠️ FEATURES OVERZICHT

### **File Browser (Admin → Files)**
- Syntax validation (Python, JS, JSON)
- Line numbers
- Ctrl+S shortcut
- Live validation (1s debounce)
- Error panel met line numbers
- Backup systeem (.backup files)

### **Bitvavo Trading (Admin → Wallet → Spark Core)**
- Live BCH/EUR tracking
- Balance API (read-only)
- Rate limiting + caching
- Potje waarde tonen bij BUY (€5.00)

### **User Instellingen**
- Audio/Video (mic, camera)
- Thema (donker/licht, accent)
- Taal (NL/EN)
- Notificaties
- Privacy opties

### **Dragable Tabs**
- Drag & drop binnen secties
- localStorage persistence
- Visual feedback (opacity 50%)
- Title hint tijdens hover

### **Help & Privacy**
- Modal systeem (geen tabs)
- FAQ + sneltoetsen
- AVG/GDPR compliant
- Contact info
- Footer link

---

## 🔐 AUTHENTICATION & ROLES

**Gradaties:**
- **1** = Admin (full access)
- **2-3** = Users (beperkte access)
- **4+** = Limited users

**Login:**
- Conversational NLP: "Ik ben [Naam], [Sleutelwoord]"
- Multi-word names supported
- Auto-create disabled (voorkomt vervuiling)

**Test Account:**
- Naam: "De Willem"
- Sleutelwoord: "Appelsap"

---

## 📁 DATA STORAGE

**Primair: JSON** (308 bestanden)
- `users.json` - 8 users
- `knowledge_base.json` - 2380 entries
- `entities.json` - Wallet kasboeken
- `user_wallets.json` - User balances

**MongoDB: Orphaned**
- 0 users, 0 data
- Status: On hold
- Intentie: Onbekend (mogelijk toekomstige scaling)

**Logs:**
- 76 conversations (39 active, 37 archived)
- Supervisor logs (backend/frontend)
- 12 knowledge backups

---

## 🚀 RECENT COMPLETED (v4.1)

1. ✅ Roadmap v4.1 toegevoegd
2. ✅ File Browser verbeterd (syntax, line numbers, Ctrl+S)
3. ✅ Bitvavo potje waarde bij BUY
4. ✅ User Wallet (gescheiden van kasboeken)
5. ✅ Knowledge Base search + filters + A-Z
6. ✅ Navigation cleanup (duplicates verwijderd)
7. ✅ User Instellingen (profiel-gebonden)
8. ✅ Help & Privacy modal systeem
9. ✅ Dragable tabs binnen secties

---

## 📝 ARCHITECTURE NOTES

**Frontend:**
- React + Tailwind CSS
- Hot reload enabled
- Port 3000 (internal)

**Backend:**
- FastAPI + Python
- 77 services, 36 routes
- Port 8001 (internal)
- Supervisor managed

**Database:**
- Primary: JSON files
- Secondary: MongoDB (unused)

**Key Services:**
- `spark_brain.py` - Conversatie engine
- `nlp_service.py` - Intent detection
- `knowledge_service.py` - KB queries
- `bitvavo_service.py` - Crypto trading
- `game_engine.py` - Spark World (4231 regels)

---

**© 2026 Spark Core 4.1 | Reality Check Complete**
