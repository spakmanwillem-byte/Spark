# 🚀 LIVE TRADING TEST PROCEDURE - €5 Single Pot

## ✅ HUIDIGE STATUS
- API Credentials: **Opgeslagen & Getest** (READ + WRITE permissies)
- Mode: **MOCK** (veilig voor observatie)
- Pre-flight checks: **PASSED**

---

## 📋 STAP-VOOR-STAP LIVE TEST

### **FASE 1: PRE-FLIGHT VALIDATIE**

```bash
# Run pre-flight test (ALTIJD eerst doen!)
/app/preflight_api_test.sh
```

**Verwachte output:**
```
✅ Backend is running
✅ API credentials valid
✅ Balance retrieved successfully
✅ Ticker retrieved successfully
✅ Currently in MOCK mode
```

**⚠️ STOP ALS EEN CHECK FAALT!**

---

### **FASE 2: SWITCH NAAR LIVE MODE**

**Stap 1: Edit backend environment**
```bash
nano /app/backend/.env
```

Wijzig:
```
USE_MOCK_TRADING=false
```

**Stap 2: Restart backend**
```bash
sudo supervisorctl restart backend
sleep 3
sudo supervisorctl status backend
```

**Stap 3: Verificatie**
```bash
curl "https://spark-foundation.preview.emergentagent.com/api/bitvavo/live-trading/status?user_id=user-001"
```

Verwachte output:
```json
{
  "success": true,
  "mock_mode": false,  ← MOET false zijn!
  "user_id": "user-001"
}
```

---

### **FASE 3: CLEAN START - RESET POSITIE**

⚠️ **Belangrijk:** Start met lege positie voor duidelijke test

**Optie A: Via frontend**
1. Open Wallet Tab
2. Klik Spark Core → Crypto Detail
3. Klik Monitor mode (🤖)
4. Start nieuwe monitoring run
5. Run ID wordt automatisch aangemaakt

**Optie B: Via API**
```bash
# Start nieuwe run (clean state)
curl -X POST "https://spark-foundation.preview.emergentagent.com/api/bitvavo/live-monitor/start?user_id=user-001&coin=BCH&interval=1h" \
  -H "Content-Type: application/json"
```

Output bevat: `"run_id": "..."`  
**→ Bewaar deze run_id!**

---

### **FASE 4: MONITORING STARTEN**

**Config check:**
- ✅ Timeframe: **1h** (zoals je wilt)
- ✅ Trade size: **€5** (1 potje)
- ✅ Profit target: **1%**
- ✅ Trailing stop: **0.4%**

**Via Frontend:**
1. BCH modal open
2. Monitor mode actief
3. Klik "▶️ Start Monitoring"
4. **OBSERVEER** - geen manual trades!

**Polling:**
- Elke 10 seconden haalt frontend nieuwe candle op
- Decision engine analyseert
- Bij BUY/SELL signal → **LIVE TRADE wordt uitgevoerd**

---

### **FASE 5: EERSTE TRADE MONITORING**

**Real-time logs:**
```bash
# Backend logs
tail -f /app/backend/data/logs/systeem_events.log | grep -E "LIVE TRADE|MOCK TRADE"

# Output:
# [LIVE TRADE] BUY executed | Order: ... | Amount: €5.0 | Mock: False
```

**Check Bitvavo Dashboard:**
1. Log in op Bitvavo
2. Ga naar Orders/History
3. Zoek naar BCH-EUR order
4. Verificeer: Amount, Price, Status

**Check Trade History API:**
```bash
curl "https://spark-foundation.preview.emergentagent.com/api/bitvavo/trade-history?user_id=user-001&limit=5"
```

Verwacht:
```json
{
  "trades": [
    {
      "action": "BUY",
      "market": "BCH-EUR",
      "amount": 5.0,
      "price": 410.50,
      "mock": false,  ← MOET false zijn!
      "success": true
    }
  ]
}
```

---

### **FASE 6: OBSERVATIE PERIODE**

**Wat te monitoren:**

✅ **Trade Execution:**
- Wordt de trade echt uitgevoerd op Bitvavo?
- Matcht de prijs met de decision?
- Wordt de order gevuld?

✅ **Position Tracking:**
- Frontend toont: "Positie: OPEN"
- Entry price correct?
- Trailing stop actief bij 1% winst?

✅ **Logging:**
- Elke decision gelogd?
- Geen dubbele trades?
- Timestamps kloppen?

✅ **Bitvavo API:**
- Geen rate limit errors?
- Orders succesvol?
- Balance updates correct?

**Stop Conditions:**
- ❌ Dubbele trade uitgevoerd
- ❌ Trade gefaald maar geen error
- ❌ Position state niet synchroon
- ❌ API errors in logs

---

### **FASE 7: FIRST COMPLETE CYCLE**

**Wacht op:**
1. BUY signal → Trade uitgevoerd → Position OPEN
2. Prijs stijgt 1%+ → Trailing stop actief
3. Prijs daalt 0.4% → SELL signal → Position CLOSED

**Verwachte PnL:**
- ~€0.05 winst (1% van €5 minus fees)
- Check: `"total_pnl"` in API response

**Validatie:**
```bash
# Check statistics
curl "https://spark-foundation.preview.emergentagent.com/api/bitvavo/trade-statistics?user_id=user-001"
```

Verwacht:
```json
{
  "total_trades": 2,
  "buy_count": 1,
  "sell_count": 1,
  "success_count": 2,
  "real_count": 2,  ← BEIDE real trades
  "mock_count": 0
}
```

---

### **FASE 8: POST-TEST EVALUATIE**

**Checklist:**
- [ ] Eerste BUY trade succesvol op Bitvavo
- [ ] Position correct getrackt in frontend
- [ ] SELL trade succesvol bij trailing stop
- [ ] PnL berekening klopt
- [ ] Geen edge cases of fouten
- [ ] Logs compleet en logisch
- [ ] Bitvavo balance correct

**⚠️ Bij problemen:**
1. Stop monitoring (Stop button)
2. Switch terug naar mock mode
3. Analyseer logs: `/app/backend/data/logs/systeem_events.log`
4. Check trade history voor fouten

---

## 🔄 TERUG NAAR MOCK MODE

Als je wilt stoppen of iets niet klopt:

```bash
# Edit .env
nano /app/backend/.env
# Change: USE_MOCK_TRADING=true

# Restart
sudo supervisorctl restart backend
```

---

## 📊 QUICK REFERENCE COMMANDS

```bash
# Pre-flight test
/app/preflight_api_test.sh

# Check mode
curl "https://spark-foundation.preview.emergentagent.com/api/bitvavo/live-trading/status?user_id=user-001"

# View trade history
curl "https://spark-foundation.preview.emergentagent.com/api/bitvavo/trade-history?user_id=user-001&limit=10"

# View logs
tail -f /app/backend/data/logs/systeem_events.log | grep "LIVE TRADE"

# Check statistics
curl "https://spark-foundation.preview.emergentagent.com/api/bitvavo/trade-statistics?user_id=user-001"
```

---

## ✅ SUCCESS CRITERIA

**Test succesvol als:**
1. ✅ Eerste BUY trade uitgevoerd op Bitvavo
2. ✅ Position correct bijgehouden
3. ✅ Trailing stop werkt (SELL bij 0.4% drop)
4. ✅ Geen dubbele trades
5. ✅ Logging compleet
6. ✅ Bitvavo orders zichtbaar
7. ✅ PnL berekening klopt

**Dan kun je opschalen naar meer potjes!**

---

**Huidige status: KLAAR VOOR LIVE TEST**  
**API: ✅ Getest & Werkend**  
**Mode: 🟡 MOCK (switch naar LIVE wanneer klaar)**
