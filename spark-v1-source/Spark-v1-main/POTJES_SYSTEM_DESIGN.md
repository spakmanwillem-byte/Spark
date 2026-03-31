# 📦 POTJES SYSTEEM - DESIGN DOCUMENT

**Status:** 🔮 TOEKOMSTIGE FEATURE (niet geïmplementeerd)  
**Datum:** 26 maart 2026  
**Prioriteit:** Fase 3 (na succesvolle €5 single pot test)

---

## 🎯 CONCEPT

### **Wat is het Potjes Systeem?**
Een multi-position trading systeem waarbij elk "potje" onafhankelijk handelt met eigen capital, strategie en PnL tracking.

**Analogie:** 10 mini-traders die elk hun eigen €5 beheren, in plaats van 1 trader met €50.

---

## 📋 REQUIREMENTS

### **Core Features**
1. **Meerdere Potjes**
   - Start: 10 potjes × €5 = €50 total
   - Elk potje handelt onafhankelijk
   - Parallel execution mogelijk

2. **Onafhankelijke Tracking**
   - Elk potje heeft eigen:
     - Position state (OPEN/CLOSED)
     - Entry price & amount
     - Trailing stop state
     - Trade history
     - PnL accumulator

3. **Winst Per Potje**
   - Winst blijft in het potje
   - Geen herverdeling tussen potjes
   - Potje groeit van €5 → €5.05 → €5.10 etc.

4. **Opschaal Logic**
   - **Trigger:** Totaal target bereikt (bijv. €50 winst)
   - **Actie:** Alle potjes opschalen €5 → €10
   - **Mechanisme:** 
     - Optie A: Wacht tot alle potjes CLOSED zijn
     - Optie B: Geleidelijk opschalen per potje

5. **Geen Gedeelde Balans**
   - Geen "pool" van capital
   - Elk potje beheert eigen saldo
   - Independent risk per potje

---

## 🏗️ ARCHITECTUUR DESIGN

### **Database Schema**

```python
# Potje Model
{
    "pot_id": "pot-001",
    "user_id": "user-001",
    "market": "BCH-EUR",
    "
    "initial_capital": 5.0,
    "current_capital": 5.12,  # Inclusief winst
    "size_tier": "5",  # "5" of "10" of "20"
    
    "position": {
        "is_open": True,
        "entry_price": 410.0,
        "entry_amount": 0.0122,
        "entry_time": "...",
        "trailing_stop_active": False
    },
    
    "statistics": {
        "total_trades": 5,
        "wins": 4,
        "losses": 1,
        "total_pnl": 0.12,
        "win_rate": 80.0
    },
    
    "status": "active",  # active | paused | archived
    "created_at": "...",
    "last_trade": "..."
}
```

### **Service Layer**

```
PotManager
├── create_pot(user_id, initial_capital)
├── get_user_pots(user_id)
├── execute_pot_trade(pot_id, decision)
├── sync_pot_with_exchange(pot_id)
├── scale_up_pots(user_id, new_tier)
└── get_pot_statistics(user_id)

PotTrader (extends LiveTrader)
├── execute_decision_for_pot(pot_id, decision)
├── check_pot_safety_limits(pot_id)
└── calculate_pot_pnl(pot_id)
```

### **Execution Flow**

```
Monitor Loop (1h interval)
    ↓
For each active pot:
    ↓
    1. Fetch current price
    ↓
    2. Get pot position state
    ↓
    3. Decision Engine (independent per pot)
    ↓
    4. Execute trade for pot
    ↓
    5. Update pot state & PnL
    ↓
Check scaling trigger
```

---

## 🎮 GEBRUIK SCENARIOS

### **Scenario 1: Start met 10 Potjes**
```javascript
// Initialize
for (let i = 0; i < 10; i++) {
    await createPot({
        user_id: "user-001",
        initial_capital: 5.0,
        market: "BCH-EUR"
    });
}

// Result: 10 independent pots, each with €5
```

### **Scenario 2: Parallel Trading**
```
Pot 1: OPEN  (entry €408)
Pot 2: CLOSED (waiting for BUY signal)
Pot 3: OPEN  (entry €410, trailing stop active)
Pot 4: CLOSED
...
Pot 10: OPEN (entry €409)

// Each pot makes decisions independently
// No coordination needed
```

### **Scenario 3: Opschaling**
```javascript
// Check total PnL
const stats = await getPotStatistics("user-001");
// { total_pnl: 50.0, total_capital: 100.0 }

if (stats.total_pnl >= 50.0) {
    // Scale up all pots
    await scaleUpPots("user-001", new_tier="10");
    // All pots now trade with €10 instead of €5
}
```

### **Scenario 4: Potje Fails**
```
Pot 5 hits max loss (3%)
→ Pot closes position
→ Pot capital: €4.85
→ Pot continues trading with €4.85
→ Other pots unaffected
```

---

## 🔧 TECHNISCHE OVERWEGINGEN

### **1. Position Management**
**Probleem:** Bitvavo heeft 1 BCH balance, niet 10 separate balances

**Oplossing A: Virtual Allocation**
```python
# Track virtual allocation per pot
total_bch_on_exchange = 0.12
pot_1_virtual_bch = 0.012
pot_2_virtual_bch = 0.011
...

# On SELL: only sell pot's virtual amount
```

**Oplossing B: Separate Sub-Accounts**
- Gebruik Bitvavo sub-accounts (als beschikbaar)
- Elk potje krijgt eigen sub-account
- Echte isolatie

**Aanbevolen:** Virtual allocation (simpeler, geen extra API calls)

### **2. Trade Execution**
**Sequential vs Parallel:**
- **Sequential:** Potjes handelen 1 voor 1 (veiliger, rate limits)
- **Parallel:** Alle potjes tegelijk (sneller, complexer)

**Aanbevolen:** Sequential met async/await

### **3. Sync Complexity**
**Bij crash/restart:**
- Sync 1 pot: eenvoudig (huidige implementatie)
- Sync 10 pots: complexer

**Strategie:**
1. Haal BCH balance op
2. Check welke pots OPEN positions hebben
3. Verdeel BCH over open pots
4. Als mismatch: flaggen voor handmatige review

### **4. Opschaling Timing**
**Wanneer opschalen?**

**Optie A: Wacht tot alle CLOSED**
- Veilig, geen mid-trade opschaling
- Kan lang duren
```python
if all_pots_closed() and total_pnl >= target:
    scale_up()
```

**Optie B: Geleidelijk per Potje**
- Sneller, maar complexer
- Potje dat CLOSED wordt, schaalt direct op
```python
if pot.is_closed and total_pnl >= target:
    scale_pot(pot_id, new_tier)
```

**Aanbevolen:** Optie A (simpeler, cleaner)

---

## 📊 MONITORING & UI

### **Dashboard View**
```
╔═══════════════════════════════════════════════════════╗
║  💰 POTJES OVERZICHT                                  ║
╠═══════════════════════════════════════════════════════╣
║  Total Capital: €51.20 (+€1.20)                       ║
║  Active Pots: 10                                      ║
║  Open Positions: 6                                    ║
║  Win Rate: 78%                                        ║
╠═══════════════════════════════════════════════════════╣
║  Pot #1  │ €5.15 │ OPEN   │ +€0.15 │ ▲ €410.00      ║
║  Pot #2  │ €5.10 │ CLOSED │ +€0.10 │ - -            ║
║  Pot #3  │ €5.08 │ OPEN   │ +€0.08 │ ▲ €408.50      ║
║  Pot #4  │ €4.95 │ CLOSED │ -€0.05 │ - -            ║
║  Pot #5  │ €5.12 │ OPEN   │ +€0.12 │ ▲ €409.00      ║
║  ...                                                  ║
╠═══════════════════════════════════════════════════════╣
║  🎯 Target: €50.00 winst voor opschaling              ║
║  Progress: €1.20 / €50.00 (2.4%)                      ║
╚═══════════════════════════════════════════════════════╝
```

### **Per Potje Detail**
```
╔═══════════════════════════════════════════════════════╗
║  POT #3 DETAILS                                       ║
╠═══════════════════════════════════════════════════════╣
║  Capital: €5.08 (+1.6%)                               ║
║  Position: OPEN                                       ║
║  Entry: €408.50 @ 0.0124 BCH                          ║
║  Current: €410.00 (+0.37%)                            ║
║  Trailing Stop: ACTIVE (peak €410.50)                ║
║                                                       ║
║  Statistics:                                          ║
║    Trades: 3 (2W, 1L)                                 ║
║    Win Rate: 66.7%                                    ║
║    Best Trade: +€0.06                                 ║
║    Worst Trade: -€0.02                                ║
╚═══════════════════════════════════════════════════════╝
```

---

## 🚀 IMPLEMENTATIE FASES

### **Fase 3.1: Single → Multi Pot Foundation** (1-2 dagen)
- [ ] Database schema voor pots
- [ ] PotManager service
- [ ] Virtual BCH allocation logic
- [ ] Pot state persistence

### **Fase 3.2: Parallel Execution** (2-3 dagen)
- [ ] Loop over active pots
- [ ] Sequential trade execution
- [ ] Per-pot decision engine calls
- [ ] Error handling per pot

### **Fase 3.3: PnL & Statistics** (1 dag)
- [ ] Per-pot trade history
- [ ] Aggregated statistics
- [ ] Win/loss tracking
- [ ] Performance metrics

### **Fase 3.4: Opschaal Logic** (1 dag)
- [ ] Target detection
- [ ] Scale-up trigger
- [ ] Capital reallocation
- [ ] Tier management

### **Fase 3.5: UI & Monitoring** (2 dagen)
- [ ] Potjes overview dashboard
- [ ] Per-pot detail view
- [ ] Real-time status updates
- [ ] Manual pot controls

**Total Estimate:** ~1 week development + testing

---

## ⚠️ RISICO'S & MITIGATIES

### **Risico 1: Sync Complexity**
- **Probleem:** 10 pots out of sync met exchange
- **Mitigatie:** Regular sync checks, manual review flagging

### **Risico 2: Rate Limits**
- **Probleem:** 10 trades/interval = meer API calls
- **Mitigatie:** Batch requests waar mogelijk, rate limiting

### **Risico 3: Concurrent Modifications**
- **Probleem:** Race conditions bij parallel execution
- **Mitigatie:** Sequential execution, transaction locks

### **Risico 4: Capital Fragmentation**
- **Probleem:** Kleine potjes (€4.85) niet efficient
- **Mitigatie:** Min capital threshold, pot consolidation

### **Risico 5: User Confusion**
- **Probleem:** Te veel informatie, onduidelijk overzicht
- **Mitigatie:** Clean UI, aggregated views, simple controls

---

## 📝 DESIGN BESLISSINGEN VOOR HUIDIGE IMPLEMENTATIE

### **Wat nu al voorbereid moet worden:**

1. **Database Structure**
   - ✅ Gebruik `user_id` in alle services (niet hardcoded)
   - ✅ Trade history per run_id (kan later per pot_id)
   - ✅ Position state als separate entity (niet embedded)

2. **Service Interfaces**
   - ✅ `execute_decision()` accepteert parameters (niet global state)
   - ✅ `sync_position_with_exchange()` per run_id
   - ✅ PnL tracking per trade (niet global)

3. **Safety Limits**
   - ✅ Per-trade limits (€5) al geïmplementeerd
   - ⚠️ Geen global balance check (goed voor multi-pot)

4. **API Endpoints**
   - ✅ All endpoints accept `user_id` + `run_id`
   - ✅ Statistics API per user (kan aggregeren over pots)

### **Wat NIET moet veranderen:**
- ❌ Geen hardcoded single-position assumptie
- ❌ Geen global state dependencies
- ❌ Geen "total balance" requirements in trade logic

---

## 🎯 SUCCES CRITERIA

### **MVP Potjes Systeem:**
- [ ] 10 potjes actief en trading
- [ ] Elk potje tracked own PnL
- [ ] Win rate > 70% over 1 week
- [ ] Sync blijft correct bij crashes
- [ ] Opschaling werkt bij target
- [ ] UI duidelijk en responsive
- [ ] Geen race conditions
- [ ] Max 2% out-of-sync events

### **Advanced Features (later):**
- [ ] Custom potje strategies (per pot config)
- [ ] Pot pause/resume
- [ ] Pot archiving
- [ ] Pot performance ranking
- [ ] Auto-rebalancing tussen pots
- [ ] Risk distribution optimization

---

## 📚 REFERENTIES

**Inspiratie:**
- Grid Trading bots (Binance, KuCoin)
- DCA (Dollar Cost Averaging) strategies
- Portfolio management systems

**Technisch:**
- Current single-pot implementation
- `LiveTraderService` architecture
- Trade history system

---

**STATUS:** 📋 GEDOCUMENTEERD - NIET GEÏMPLEMENTEERD  
**Next Step:** Successful €5 single pot test → Dan Fase 3 planning  
**ETA:** Evaluatie na 1 week live trading

---

## 💡 WILLEM'S INPUT

> "Voor later wil ik een potjes systeem bouwen:
> * Meerdere potjes (bijv. 10x €5)
> * Elk potje handelt onafhankelijk
> * Winst blijft per potje
> * Bij totaal target (bijv. €50) opschalen naar €10 per potje
> * Geen gedeelde balans maar per-potje tracking"

**Design aligned met deze requirements** ✅
