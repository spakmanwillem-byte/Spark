# ⏱️ CANDLE COUNTDOWN TIMER - FEATURE DESIGN

**Status:** 🔮 Toekomstige Feature  
**Prioriteit:** Nice-to-have (UX enhancement)  
**Voor:** Admin monitoring & observation

---

## 🎯 CONCEPT

### **Wat is het?**
Een real-time countdown timer die laat zien wanneer de volgende candle sluit en een nieuwe decision/trade kan komen.

**Waarom handig?**
- Admin weet exact wanneer actie kan komen
- Geen constant refreshen/wachten
- Betere observatie experience
- Spannender tijdens live monitoring

---

## 💡 USE CASES

### **Scenario 1: Live Monitoring**
```
Willem heeft 15-min interval actief en wil weten:
"Wanneer komt de volgende trade mogelijk?"

UI toont:
┌─────────────────────────────────────────┐
│ 🕐 Volgende Candle Over:                │
│                                         │
│        ⏱️  02:47                        │
│                                         │
│         (in 4 min 23 sec)               │
│                                         │
│ ▓▓▓▓▓▓▓▓▓▓░░░░░░ 70%                   │
└─────────────────────────────────────────┘

→ Willem weet: "Over 4 minuten kan er actie komen"
```

### **Scenario 2: Multi-Interval Dashboard**
```
Admin dashboard met meerdere intervals:

┌─────────────────────────────────────────┐
│ ⏱️  CANDLE TIMERS                       │
├─────────────────────────────────────────┤
│ 15 min  │ 02:45 │ ▓▓▓░░ 2m 15s         │
│ 30 min  │ 03:00 │ ▓░░░░ 17m 45s        │
│ 1 hour  │ 03:00 │ ▓░░░░ 17m 45s        │
│ 4 hour  │ 06:00 │ ░░░░░ 3h 17m         │
└─────────────────────────────────────────┘

→ Overzicht van alle actieve intervals
```

### **Scenario 3: Notification Before Candle Close**
```
5 minuten voor candle close:
🔔 "BCH 1h candle sluit over 5 minuten"

1 minuut voor:
🔔 "BCH 1h candle sluit over 1 minuut - BUY/SELL mogelijk!"

→ Proactive alerts voor observatie momenten
```

---

## 🎨 UI DESIGN

### **Variant 1: Compact Widget (rechtsonder)**
```
┌─────────────────────────┐
│ ⏱️  Next: 02:45         │
│    4m 23s               │
│ ▓▓▓▓▓▓▓▓░░░░ 70%       │
└─────────────────────────┘
```

### **Variant 2: In Monitor Panel**
```
╔═══════════════════════════════════════╗
║ 🤖 BCH Live Monitor - ACTIVE         ║
╠═══════════════════════════════════════╣
║                                       ║
║ Current Position: OPEN                ║
║ Entry: €408.50 @ 0.0122 BCH          ║
║                                       ║
║ ⏱️  Next Decision In:                 ║
║    ┌─────────────────────────────┐   ║
║    │      4m 23s                  │   ║
║    │ ▓▓▓▓▓▓▓▓▓▓░░░░░░ 70%        │   ║
║    │ Next: 02:45 (15min candle)  │   ║
║    └─────────────────────────────┘   ║
║                                       ║
╚═══════════════════════════════════════╝
```

### **Variant 3: Minimalist Top Bar**
```
┌────────────────────────────────────────────────────────────┐
│ Spark Core | 💰 Wallet | ⏱️  Next: 02:45 (4m 23s) ▓▓▓▓░░ │
└────────────────────────────────────────────────────────────┘
```

---

## 🔧 TECHNICAL IMPLEMENTATION

### **Frontend Logic**

```javascript
// CoinChartModal.js - Add countdown component

const CandleCountdown = ({ interval }) => {
  const [timeRemaining, setTimeRemaining] = useState(null);
  const [percentage, setPercentage] = useState(0);
  
  useEffect(() => {
    const calculateNextCandle = () => {
      const now = new Date();
      const minutes = now.getMinutes();
      const seconds = now.getSeconds();
      
      // Calculate next candle based on interval
      let nextCandleMin;
      if (interval === '15m') {
        nextCandleMin = Math.ceil((minutes + 1) / 15) * 15;
      } else if (interval === '30m') {
        nextCandleMin = Math.ceil((minutes + 1) / 30) * 30;
      } else if (interval === '1h') {
        nextCandleMin = 60;
      }
      
      const nextCandle = new Date(now);
      nextCandle.setMinutes(nextCandleMin, 0, 0);
      
      if (nextCandleMin === 60) {
        nextCandle.setHours(nextCandle.getHours() + 1);
        nextCandle.setMinutes(0);
      }
      
      // Calculate time remaining
      const diff = nextCandle - now;
      const minutesLeft = Math.floor(diff / 60000);
      const secondsLeft = Math.floor((diff % 60000) / 1000);
      
      // Calculate percentage
      const intervalMs = getIntervalMs(interval);
      const elapsed = intervalMs - diff;
      const pct = (elapsed / intervalMs) * 100;
      
      setTimeRemaining({ minutes: minutesLeft, seconds: secondsLeft });
      setPercentage(Math.max(0, Math.min(100, pct)));
    };
    
    // Update every second
    calculateNextCandle();
    const timer = setInterval(calculateNextCandle, 1000);
    
    return () => clearInterval(timer);
  }, [interval]);
  
  return (
    <div className="candle-countdown">
      <div className="countdown-label">⏱️ Next Candle In:</div>
      <div className="countdown-time">
        {timeRemaining ? 
          `${timeRemaining.minutes}m ${timeRemaining.seconds}s` 
          : 'Calculating...'}
      </div>
      <div className="progress-bar">
        <div 
          className="progress-fill" 
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};

const getIntervalMs = (interval) => {
  switch(interval) {
    case '15m': return 15 * 60 * 1000;
    case '30m': return 30 * 60 * 1000;
    case '1h': return 60 * 60 * 1000;
    case '4h': return 4 * 60 * 60 * 1000;
    default: return 60 * 60 * 1000;
  }
};
```

### **Styling**

```css
.candle-countdown {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 16px;
  color: white;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.countdown-label {
  font-size: 14px;
  opacity: 0.9;
  margin-bottom: 8px;
}

.countdown-time {
  font-size: 32px;
  font-weight: bold;
  font-family: 'Monaco', monospace;
  text-align: center;
  margin-bottom: 12px;
}

.progress-bar {
  height: 8px;
  background: rgba(255,255,255,0.2);
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #4ade80 0%, #22c55e 100%);
  transition: width 1s linear;
  border-radius: 4px;
}

/* Animate when close to candle close */
.countdown-time.urgent {
  animation: pulse 1s infinite;
  color: #fbbf24;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}
```

---

## ⚡ ADVANCED FEATURES

### **1. Color Coding**
```
> 10 min remaining: 🟢 Green (relaxed)
5-10 min:           🟡 Yellow (attention)
1-5 min:            🟠 Orange (prepare)
< 1 min:            🔴 Red (imminent, pulse animation)
```

### **2. Sound Notifications**
```javascript
// Play subtle sound 1 minute before candle close
if (minutesLeft === 1 && secondsLeft === 0) {
  playSound('candle-warning.mp3');
}

// Play sound when candle closes
if (minutesLeft === 0 && secondsLeft === 0) {
  playSound('candle-close.mp3');
}
```

### **3. Desktop Notifications**
```javascript
if (Notification.permission === 'granted' && minutesLeft === 5) {
  new Notification('BCH Monitor', {
    body: 'Candle sluit over 5 minuten',
    icon: '/bch-icon.png'
  });
}
```

### **4. Multiple Timers Dashboard**
```javascript
const MultiIntervalTimers = () => {
  const intervals = ['15m', '30m', '1h', '4h'];
  
  return (
    <div className="timers-grid">
      {intervals.map(interval => (
        <CandleCountdown 
          key={interval} 
          interval={interval}
          compact={true}
        />
      ))}
    </div>
  );
};
```

---

## 📊 DATA REQUIREMENTS

### **From Backend:**
```json
{
  "current_time": "2026-03-26T02:40:37Z",
  "interval": "15m",
  "next_candle_close": "2026-03-26T02:45:00Z",
  "time_remaining_ms": 263000,
  "interval_duration_ms": 900000,
  "percentage_complete": 70.8
}
```

### **Or Calculate Client-Side:**
- Pro: No backend changes needed, real-time accuracy
- Con: Relies on client clock sync

**Recommended:** Client-side calculation (simpler, real-time)

---

## 🎯 IMPLEMENTATION PHASES

### **Phase 1: Basic Timer** (2-3 hours)
- [ ] Calculate next candle time
- [ ] Display countdown (minutes:seconds)
- [ ] Update every second
- [ ] Basic styling

### **Phase 2: Visual Polish** (1-2 hours)
- [ ] Progress bar animation
- [ ] Color coding (green → yellow → orange → red)
- [ ] Smooth transitions
- [ ] Responsive design

### **Phase 3: Advanced Features** (2-3 hours)
- [ ] Sound notifications
- [ ] Desktop notifications
- [ ] Pulse animation when < 1 min
- [ ] Multi-interval dashboard view

### **Phase 4: Settings** (1 hour)
- [ ] Enable/disable sounds
- [ ] Enable/disable notifications
- [ ] Position preference (corner, top, inline)
- [ ] Hide/show timer

**Total Estimate:** 6-9 hours development

---

## 💡 ALTERNATIVE APPROACHES

### **Option A: Simple Text (Easiest)**
```
Next candle: 02:45 (in 4 minutes)
```

### **Option B: Progress Ring (Cool)**
```
    ⏱️
   4m 23s
  ⚪⚪⚪⚪⚫⚫
```

### **Option C: Animated GIF**
```
Clock animation that fills up as interval progresses
```

**Recommended:** Option A for MVP, Option B for polish

---

## 🔗 INTEGRATION POINTS

### **Where to Add:**
1. **Monitor Panel** (primary location)
   - Inline with position info
   - Always visible during monitoring

2. **Dashboard Widget** (optional)
   - Small widget rechtsonder
   - Persistent across tabs

3. **Top Bar** (minimal)
   - Next to username/settings
   - Global visibility

**Recommended:** Monitor Panel (most contextual)

---

## ⚠️ EDGE CASES

### **1. Timezone Issues**
- Use UTC for calculations
- Display in user's local time
- Handle DST transitions

### **2. Page Inactive**
- Timer keeps running in background
- Visual indicator if timer drifts
- Re-sync on page focus

### **3. Multiple Monitors**
- Each monitor has own timer
- Different intervals possible
- Sync across tabs (localStorage)

### **4. Server Downtime**
- Timer keeps counting
- Warning if backend unreachable
- "Estimated" label if uncertain

---

## 📝 NOTES

**Willem's Original Idea:**
> "Een afteller voor de candle voor 15 min 30 min uur enzo  
> dan weet je wanneer actie komt als admin"

**Key Benefits:**
- 🎯 Reduces uncertainty
- ⏰ Better time management
- 👀 More engaging monitoring
- 📊 Professional trading feel

**Similar Features in:**
- TradingView: Candle countdown
- Binance: Next funding time
- Crypto exchanges: Order expiry timers

---

**STATUS:** 📋 GEDOCUMENTEERD - READY FOR IMPLEMENTATION  
**Priority:** Medium (UX enhancement, not critical)  
**Next Step:** Implement after successful live trading validation

---

## 🚀 QUICK WIN VERSION

Voor nu (if you want quick test):

```javascript
// Add this to CoinChartModal.js for instant countdown
const [countdown, setCountdown] = useState('');

useEffect(() => {
  const timer = setInterval(() => {
    const now = new Date();
    const min = now.getMinutes();
    const sec = now.getSeconds();
    
    // Next 15-min mark
    const nextMin = Math.ceil((min + 1) / 15) * 15;
    const minsLeft = (nextMin - min - 1);
    const secsLeft = (60 - sec) % 60;
    
    setCountdown(`Next: ${minsLeft}m ${secsLeft}s`);
  }, 1000);
  
  return () => clearInterval(timer);
}, []);

// Display: <div>{countdown}</div>
```

Simpel maar effectief! ⏱️
