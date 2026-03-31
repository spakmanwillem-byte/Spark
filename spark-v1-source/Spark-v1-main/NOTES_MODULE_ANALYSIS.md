# 📝 Notes Module - Analyse & Voorstel

**Datum:** 21 maart 2026  
**Status:** Voor volgende sessie  
**Context:** Fase 1 compleet (Uitgaven ✅, Inkomsten ✅, Dagboek ✅)

---

## 🔍 Analyse Bestaand Systeem

### **Wat Bestaat Al:**

**Backend:**
- ✅ `/app/backend/services/notes_service.py` - Volledig CRUD systeem
- ✅ `/app/backend/routes/notes_routes.py` - API endpoints
- ✅ **Data opslag:** `/app/backend/data/notes/notes.json` (GLOBAAL, niet per user!)

**Frontend:**
- ✅ `/app/frontend/src/components/NotitiesTab.js` - Volledig werkende UI

**Huidige Features:**
- ✅ CRUD operations (Create, Read, Update, Delete)
- ✅ Categorieën: Algemeen, Inzicht, Patroon, Observatie, TODO
- ✅ Tags support (komma-gescheiden)
- ✅ Search functionaliteit
- ✅ Stats per categorie
- ✅ Filter op categorie
- ✅ `created_by` tracking (Spark vs User)
- ✅ UI met icons per categorie

**Huidige Gedrag:**
- Notities worden GLOBAAL opgeslagen (niet per user)
- Frontend heeft al hint: "💡 Type 'note:' in chat om snel toe te voegen"
- Maar chat integratie bestaat nog NIET

---

## ⚠️ Belangrijke Bevindingen

### **Probleem 1: Globale Opslag**
```
HUIDIG:  /app/backend/data/notes/notes.json  (alle users samen)
GEWENST: /app/backend/data/users/{user_id}/notes.json  (per user gescheiden)
```

**Impact:** 
- Conflicteert met principe "per user gescheiden"
- Kan niet schalen naar multi-user systeem
- Privacy issue

### **Probleem 2: Geen Chat Integratie**
- UI hint bestaat ("note: ...")
- Maar trigger werkt niet
- Spark gedrag ontbreekt

### **Probleem 3: Vermengd Doel**
- Huidige categorieën zijn breed: Algemeen, Inzicht, Patroon, Observatie, TODO
- Overlap mogelijk met Dagboek (emoties) en Taken
- Moet scherper gedefinieerd worden

---

## 🎯 Voorstel voor Volgende Sessie

### **Fase 1: Migratie naar Per-User Opslag**

**Backend Aanpassingen:**
```python
# HUIDIG (globaal):
DataManager.load_json("notes/notes.json")

# NIEUW (per user):
DataManager.load_data(f"users/{user_id}/notes.json")
```

**Wat Hergebruiken:**
- ✅ Alle service methods (add, update, delete, search)
- ✅ API routes structuur
- ✅ Frontend UI (volledig)
- ✅ Tags systeem
- ✅ Categorieën systeem (wel aanpassen/verfijnen)

**Wat Aanpassen:**
- ❌ Data opslag path (naar per user)
- ❌ API endpoints (user_id parameter toevoegen)
- ❌ Service methods (user_id parameter toevoegen)

**Geschatte effort:** ~30 min (vergelijkbaar met Uitgaven/Inkomsten aanpak)

---

### **Fase 2: Chat Integratie**

**Trigger Gedrag:**
```
User:  "note: nieuwe feature idee"
       → Direct opslaan zonder bevestiging
       → Response: "📝 Notitie opgeslagen in categorie Algemeen"

Spark: [tijdens gesprek detecteert idee]
       → Voorstellen: "Wil je dit opslaan als notitie? (ja/nee)"
       → Bij "ja": opslaan met categorie Inzicht/Observatie
```

**Implementatie:**
- Intent detection (response_behavior.py uitbreiden)
- Trigger patterns (intent_triggers.py uitbreiden)
- Backend handler voor note: command

**Geschatte effort:** ~45 min (chat flow + Spark gedrag)

---

### **Fase 3: Categorieën Verfijnen**

**Huidige overlap voorkomen:**

| Module | Doel | Categorieën |
|--------|------|-------------|
| 📔 **Dagboek** | Emotie, reflectie | Mood-based (blij, verdrietig, etc.) |
| 📝 **Notes** | Ideeën, plannen | Idee, Plan, Analyse, TODO, Link |
| 💸 **Uitgaven** | Financieel | Boodschappen, Transport, etc. |

**Voorgestelde Notes Categorieën:**
- 💡 **Idee** - Nieuwe concepten, features
- 📋 **Plan** - Actiepunten, strategieën
- 🔍 **Analyse** - Observaties, patronen (wat Spark ziet)
- ✅ **TODO** - Taken (behouden)
- 🔗 **Link** - Referenties, inspiratie

**Verschil met Dagboek:**
- Dagboek = "Hoe voel ik me?" (emotie)
- Notes = "Wat wil ik bouwen?" (actie)
- NIET MIXEN

---

## 📋 Implementatie Roadmap

### **Sessie 1: Basis (volgende keer)**
1. ✅ Migreer naar per-user opslag
2. ✅ Update API endpoints (user_id param)
3. ✅ Test backend CRUD
4. ✅ Verifieer frontend werkt met nieuwe structuur

### **Sessie 2: Chat Integratie**
1. ✅ Intent detection voor "note:"
2. ✅ Spark voorstellen gedrag
3. ✅ Backend handler
4. ✅ E2E testing

### **Sessie 3: Polish**
1. ✅ Categorieën verfijnen
2. ✅ Export functie (zoals Dagboek)
3. ✅ Dashboard integratie (overzicht van alle modules)

---

## 🔄 Verschil Dagboek vs Notes

**Dagboek:**
- Emotie, gevoel, reflectie
- Privé, persoonlijk
- Mood selector
- Chronologisch
- Export naar text/markdown

**Notes:**
- Ideeën, plannen, taken
- Kan gedeeld worden (met Spark)
- Categorieën (Idee, Plan, TODO)
- Zoekbaar op inhoud/tags
- Actiegericht

**Gemeenschappelijk:**
- Per user opslag
- Tags support
- CRUD operations
- Export functie
- Datum filtering

---

## 🚀 Quick Start (voor volgende agent)

**Stap 1:** Kopieer `notes_service.py` → pas alle functies aan voor user_id
**Stap 2:** Update `notes_routes.py` → voeg user_id parameter toe
**Stap 3:** Test backend API (zoals we deden voor Uitgaven/Inkomsten)
**Stap 4:** Verifieer frontend (minimale aanpassingen nodig)
**Stap 5:** Testing subagent draaien

**Verwachte tijd:** 1-2 uur voor complete Notes module (inclusief testing)

---

## 📊 Status Check

**Klaar voor Implementatie:**
- ✅ Bestaand systeem geanalyseerd
- ✅ Voorstel gemaakt
- ✅ Hergebruik strategie bepaald
- ✅ Verschil Dagboek/Notes helder
- ✅ Roadmap opgesteld

**Nog Niet Gedaan:**
- ❌ Daadwerkelijke migratie naar per-user
- ❌ Chat integratie
- ❌ Testing

**Dependencies:**
- Wacht op: Willem's feedback over gebruik Fase 1 modules
- Bouwt op: Intent Priority System (al werkend)
- Voorbereiding voor: Dashboard & volledige chat integratie

---

**Opgeslagen voor:** Volgende sessie  
**Actie:** Wacht op Willem's go voor Notes implementatie
