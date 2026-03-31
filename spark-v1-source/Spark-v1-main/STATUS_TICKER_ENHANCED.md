# ⭐ Enhanced Status Ticker System

## Overzicht

De StatusTicker is de **levende hartslag** van Spark - een horizontal bar die real-time de status van de gebruiker en het systeem toont.

---

## 🎯 Enhanced Display Format

### **Voor Ingelogde Gebruikers:**
```
👤 Willem | ⭐ 850 XP | 🗺️ Rank Explorer | 🧠 312 Knowledge | 🟢 Spark Core Online | ⏱️ 45 min
```

### **Voor Niet-ingelogde Gebruikers:**
```
👋 Niet ingelogd - Stel jezelf voor aan Spark | 🟢 Spark Core Online
```

---

## 📊 Metrics Uitleg

### 1. **👤 Gebruiker**
- Display: Naam van de ingelogde gebruiker
- Voorbeeld: `👤 Willem`

### 2. **⭐ XP (Experience Points)**
- Display: Actuele XP waarde
- Voorbeeld: `⭐ 850 XP`
- Source: `userData.xp`
- Updates: Real-time bij achievement unlocks, knowledge card creation

### 3. **🏆 Rank/Title System**
- Display: Rank icon + naam met kleurcode
- Dynamisch gebaseerd op XP level
- Voorbeeld: `🗺️ Rank Explorer`

**Rank Tiers:**
| XP Range | Rank | Icon | Color |
|----------|------|------|-------|
| 0-499 | Novice | 🔰 | Gray |
| 500-1,999 | Beginner | ✨ | Yellow |
| 2,000-4,999 | Learner | 🌱 | Light Green |
| 5,000-9,999 | Explorer | 🗺️ | Green |
| 10,000-19,999 | Scholar | 📚 | Blue |
| 20,000-49,999 | Expert | 🎓 | Purple |
| 50,000+ | Master | 👑 | Gold |

### 4. **🧠 Knowledge Count**
- Display: Aantal active knowledge cards
- Voorbeeld: `🧠 312 Knowledge`
- Source: `knowledgeCount` prop of `userData.achievements.progress.word_count`
- Represents: User's contribution to Spark's knowledge base

### 5. **🟢 Spark Core Status**
- Display: Real-time system health indicator
- Voorbeeld: `🟢 Spark Core Online` / `🔴 Spark Core Offline`
- Visual: Pulsing green dot when online
- Makes system feel "alive"

### 6. **⏱️ Session Duration** (optional)
- Display: Time since login
- Voorbeeld: `⏱️ 45 min`
- Only shows when available

---

## 🎨 Visual Design

### **Animations:**
- ✨ Pulsing green indicator voor "Spark Core Online"
- 🌊 Smooth transitions on data updates
- 💫 Hover effect op "Spark Core" tekst

### **Color Coding:**
- **Rank Colors:** Dynamic based on tier (zie tabel)
- **Green (#4CAF50):** Online, healthy, positive
- **Red (#f44336):** Offline, error
- **Gold (#FFD700):** Master rank
- **Purple (#9C27B0):** Expert rank

### **Typography:**
- Font size: 14px (readable but compact)
- Icon size: 16px
- Spacing: 15px gap between items
- Dividers: 1px subtle line (rgba(255,255,255,0.1))

---

## 💡 Future Enhancements

### **Planned Additions:**
1. **🔥 Streak Counter**
   - "🔥 12 day streak"
   - Tracks consecutive active days

2. **🎯 Active Goal Indicator**
   - "🎯 Goal: Learn 50 new words"
   - Shows current active goal

3. **📈 Trend Indicators**
   - "⬆️ +150 XP today"
   - Shows daily/weekly growth

4. **🌟 Recent Achievement Flash**
   - Brief animation when achievement unlocked
   - "🎉 New Achievement: Taal Architect!"

5. **👥 Community Stats** (multi-user fase)
   - "👥 15 users online"
   - Active community members

6. **🧪 Current Mode**
   - "🧪 Focus Mode" / "🎨 Creative Mode"
   - Shows Spark's operational mode

---

## 🔧 Technical Implementation

### **Component Structure:**
```jsx
<StatusTicker
  userData={userData}           // User object met XP, naam, achievements
  sessionDuration="45 min"      // Optional: time since login
  systemStatus="online"         // "online" | "offline"
  knowledgeCount={312}          // Optional: active knowledge card count
/>
```

### **Rank Calculation:**
```javascript
const getRank = (xp) => {
  if (xp >= 50000) return { name: 'Master', icon: '👑', color: '#FFD700' };
  if (xp >= 20000) return { name: 'Expert', icon: '🎓', color: '#9C27B0' };
  // ... etc
  return { name: 'Novice', icon: '🔰', color: '#9E9E9E' };
};
```

### **Data Sources:**
- `userData.xp` - XP waarde
- `userData.naam` - User name
- `userData.achievements.progress.word_count` - Knowledge count (fallback)
- `knowledgeCount` prop - Preferred knowledge count (from API)
- `systemStatus` - Backend health check

---

## 🎯 Design Philosophy

### **"Make It Feel Alive"**
De StatusTicker is niet alleen een informatiedisplay - het is de **hartslag** van Spark:

1. **Real-time Updates:** Data verandert live (XP gains, knowledge growth)
2. **Visual Feedback:** Pulsing indicator, smooth transitions
3. **Gamification:** Rank progression motivates users
4. **System Personality:** "Spark Core Online" voelt meer "levend" dan "System: OK"
5. **At-a-Glance Value:** User ziet direct hun progress

---

## 📐 Layout Position

```
┌─────────────────────────────────────────────────────────────┐
│ 👤 Willem | ⭐ 850 XP | 🗺️ Explorer | 🧠 312 | 🟢 Core Online│ ← StatusTicker (50px height)
└─────────────────────────────────────────────────────────────┘
```

- **Position:** Fixed top
- **Height:** 50px
- **Width:** Full viewport (100vw)
- **Z-index:** 100 (always on top)
- **Scroll:** Sticky (stays visible when scrolling)

---

## ✅ Implementation Status

**Completed:**
- ✅ Rank system (7 tiers)
- ✅ XP display with actual number
- ✅ Knowledge count display
- ✅ "Spark Core Online" branding
- ✅ Pulsing animation on indicator
- ✅ Color-coded ranks
- ✅ Responsive layout

**Planned:**
- ⏳ Streak counter
- ⏳ Active goal display
- ⏳ Trend indicators
- ⏳ Achievement flash animations
- ⏳ Community stats (multi-user)

---

**Result:** StatusTicker is nu een **levend dashboard** dat motivatie, progress, en system health in één blik toont! 🚀
