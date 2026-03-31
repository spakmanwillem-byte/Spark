# 🔍 Audit: Wat Werkt Er Al? (Verfijnen, Niet Uitbreiden)

**Datum:** 13 maart 2026, 22:30  
**Doel:** Check bestaande features voordat we uitbreiden

---

## ✅ **SETTINGS TAB**

### **WAT WERKT:**
1. **Sessie Instellingen:**
   - ✅ Heartbeat Interval (10/30/60/120 sec) - **WERKEND**
   - ✅ Session Timeout (2/5/10/30/60 min) - **WERKEND**
   - ✅ API: `/api/settings` (GET & PUT) - **GEKOPPELD**

2. **Interface Instellingen:**
   - ✅ Notificatie Geluiden (checkbox) - **WERKEND**
   - ✅ Auto-Save (checkbox) - **WERKEND**

3. **Developer Instellingen:** (alleen voor gradatie 1)
   - ✅ Debug Mode - **WERKEND**

### **WAT ONTBREEKT (Voor Verfijning):**
- ❌ **Volume slider** voor audio (0-100%)
- ❌ **Master volume** voor alle geluiden
- ❌ **Per-sound volume** (trigger specifiek)
- ❌ **Kleurenschema editor** (3 sliders voor primaire kleuren)
- ❌ **Theme customization** (dark/light mode toggle?)

---

## ✅ **GELUIDEN TAB**

### **WAT WERKT:**
1. **Upload Systeem:**
   - ✅ Drag & drop audio files - **WERKEND**
   - ✅ File picker - **WERKEND**
   - ✅ Upload naar backend (`/api/sounds/mapping`) - **WERKEND**

2. **Trigger Management:**
   - ✅ Woord koppelen aan geluid - **WERKEND**
   - ✅ Display name editable - **WERKEND**
   - ✅ Frequency (every/10sec/30sec/60sec) - **WERKEND**
   - ✅ Edit bestaande mappings - **WERKEND**
   - ✅ Delete mappings - **WERKEND**
   - ✅ Test button (speelt af) - **WERKEND**

3. **Afspelen in Chat:**
   - ✅ Detectie van trigger woord in chat - **WERKEND** (bijv. "succes")
   - ✅ Audio streaming via `/api/sounds/stream/{filename}` - **WERKEND**

### **WAT ONTBREEKT (Voor Verfijning):**
- ❌ **Volume control PER geluid** (in de lijst)
- ❌ **Volume bij afspelen** (niet gekoppeld aan master volume)
- ❌ **Waveform preview** van audio
- ❌ **Geluid bij ANDERE acties:**
  - Verzendknop (chat submit)
  - Achievement unlocked
  - Login/logout
  - Error/success notifications
  - Button clicks (optioneel)

---

## ⚠️ **TRIGGER MANAGER TAB** (EMOTIES)

### **WAT WERKT:**
- ✅ UI laadt
- ✅ Emotie categorieën (blij, verdrietig, boos, bang) zichtbaar
- ✅ Backend heeft data: `/app/backend/data/triggers/emotion_triggers.json`

### **WAT NIET WERKT (2 BUGS):**
- ❌ **Trigger woorden niet zichtbaar** - Data parsing issue (nested object vs array)
- ❌ **Kan geen woorden toevoegen** - Backend `.append()` op dict crasht

### **WAT ONTBREEKT (Voor Verfijning):**
- ❌ **Sentiment analysis op zin-niveau:**
  - Zin → Som van emoties → Positief/Negatief score
  - Voorbeeld: "Ik ben teleurgesteld maar ook hoopvol" → 40% Bedroeft + 60% Blij = Positief
  
- ❌ **Emotie tags in Knowledge Cards:**
  - Knowledge kaart "Teleurgesteld" → tags: Bang, Bedroeft
  - Knowledge kaart "Gehaktbal" (als scheldwoord) → tag: Boos
  - Knowledge kaart "Vreugde" → tag: Blij

---

## 🎨 **KLEURENSCHEMA (Nog Niet Gemaakt)**

### **Willem's Idee:**
3 sliders voor primaire kleuren:
- **Slider 1:** Primaire kleur (accent, buttons)
- **Slider 2:** Secundaire kleur (borders, highlights)  
- **Slider 3:** Achtergrond tint

**Als je schuift:** Interface kleuren veranderen real-time

### **Implementatie Plan:**
1. **CSS Variables gebruiken:**
   ```css
   :root {
     --color-primary: #4CAF50;
     --color-secondary: #2196F3;
     --color-bg: #0a0a0a;
   }
   ```

2. **Settings Tab:**
   - 3 color pickers of HSL sliders
   - Preview panel
   - Reset knop

3. **LocalStorage:**
   - Opslaan van custom theme
   - Auto-load bij page refresh

---

## 🎯 **VERFIJNINGS PRIORITEITEN**

### **P0 - Bugs Fixen Eerst:**
1. ✅ Chat weergave (DONE)
2. ✅ Knowledge graph stopwoorden (DONE)
3. ⏳ TriggerManager - Toon woorden (10 min)
4. ⏳ TriggerManager - Add button fix (10 min)

### **P1 - Audio Verfijning:**
1. **Master Volume Slider** (Settings) → ~15 min
   - Slider 0-100%
   - LocalStorage persist
   - Koppelen aan alle audio playback

2. **Geluid bij Chat Verzenden** → ~10 min
   - Success sound (configurable)
   - Optioneel per user (Settings toggle)

3. **Geluid bij Achievements** → ~15 min
   - Achievement unlocked sound
   - Different sounds per achievement tier?

### **P2 - Emotie Verfijning:**
1. **Sentiment Analysis op Zin Niveau** → ~30 min
   - Service die zin analyseert
   - Score: [-1.0 = zeer negatief, +1.0 = zeer positief]
   - Breakdown: [Bang: 20%, Boos: 10%, Bedroeft: 30%, Blij: 40%]

2. **Emotie Tags in Knowledge** → ~20 min
   - Bulk tagging tool (script)
   - Of: Admin UI voor manual tagging
   - Graph connecties o.b.v. emoties

### **P3 - Kleurenschema:** → ~40 min
1. Settings tab: Color pickers
2. CSS variables system
3. Real-time preview
4. Presets (Dark, Light, Cyberpunk, Nature)

---

## 📊 **HUIDIGE STATUS SAMENVATTING**

### ✅ **100% Werkend:**
- Session management (heartbeat, timeout)
- Audio triggers (upload, edit, delete, play)
- Settings (save/load)
- Emotie systeem (backend data + UI display in ticker)
- Knowledge graph (met stopwoorden fix!)

### ⚠️ **90% Werkend (Kleine Bugs):**
- TriggerManager (UI ja, data parsing nee)
- Achievements (visueel glow? Te verifiëren)

### 📦 **Ontbreekt (Verfijning Ideeën):**
- Volume controls (master + per-sound)
- Audio bij meer acties (verzenden, achievements)
- Sentiment analysis (zin-niveau)
- Emotie tags in knowledge cards
- Kleurenschema customization

---

## 🎯 **Willem's Prioriteit:**

> "Verfijnen, niet uitbreiden"

**Mijn voorstel:**
1. **Fix 2 TriggerManager bugs** (20 min)
2. **Master volume slider** (15 min)  
3. **Geluid bij verzenden** (10 min)
4. **Dan:** Sentiment analysis OF Kleurenschema (Willem's keuze)

**Wat wil je eerst?** 🚀
