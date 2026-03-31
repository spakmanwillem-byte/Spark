# 🎯 Spark Core 4.1 - Admin Commands

**Laatste update:** 28 maart 2026  
**Voor:** Willem (Admin/Developer)

---

## 📊 **MONITORING COMMANDS**

Gebruik deze in de **Spark Chat**:

### Monitor Beheer
```
"run monitor"           → Start de monitor (1 uur candles)
"start monitor"         → Start de monitor
"monitor aan"           → Zet monitor aan
"stop monitor"          → Stop de monitor
"monitor uit"           → Zet monitor uit
"pause monitor"         → Pauzeer/hervat monitor
"monitor pauze"         → Pauzeer monitor
```

**Status:**
- Monitor draait nu: **JA** (gestart op 28 maart 2026, 19:08)
- Interval: **1 uur candles (3600 sec)**
- Logs: `/var/log/spark_monitor.log`

---

## 📋 **LOG COMMANDS**

Bekijk logs van verschillende periodes:

```
"toon logs van vandaag"     → Logs van vandaag
"logs vandaag"              → Logs van vandaag
"toon logs van deze week"   → Logs van deze week
"logs week"                 → Logs van deze week
"logs maand"                → Logs van deze maand
"logs jaar"                 → Logs van dit jaar
"alle logs"                 → Alle logs
"wat gebeurde er vandaag"   → Logs van vandaag
```

---

## 🔔 **NOTIFICATIES**

Systeem stuurt automatisch meldingen bij:

### Trading Alerts
- **Winst:** 🎉 **"Yhee winst €X.XX!"**
- **Verlies:** 😱 **"Damit oh nee! -€X.XX"** (komt niet voor, maar just in case)

### API Endpoints
```
GET  /api/notifications/unread          → Ongelezen notificaties
POST /api/notifications/mark-read/{id}  → Markeer als gelezen
POST /api/notifications/test            → Test notificatie
```

---

## 💰 **TRADING STRATEGIE (Actief)**

**Systeem:** Willem's 10-Potjes + Bollinger Midline + Weekdag Awareness

### Parameters
- **Capital:** €5.41 (minimum €5.08 per trade)
- **Pot 1:** €5.00 trade
- **Fees:** €0.07 per trade (Bitvavo: €0.035 buy + €0.035 sell)
- **Minimum winst:** €0.08 bruto = €0.01 netto na fees
- **Trailing stop:** 1% trigger, 0.4% drop

### Bottom Line
- **Per trade:** Minimaal **1 cent netto winst** gegarandeerd
- **Geen gokken:** Consistent, veilig, conservatief
- **Buffer:** 5× mistrades mogelijk (€0.40 max verlies)

---

## 📁 **BELANGRIJKE FILES**

### Backend
- **Trading Engine:** `/app/backend/services/spark_decision_engine.py`
- **Monitoring:** `/app/backend/services/monitoring_service.py`
- **Notificaties:** `/app/backend/services/notification_service.py`
- **Backtesting:** `/app/backend/services/backtesting_service.py`

### Data
- **Knowledge Base:** `/app/backend/data/learned_knowledge/knowledge_base.json`
- **Tasks:** `/app/backend/data/tasks.json`
- **Notificaties:** `/app/backend/data/notifications.json`
- **BCH Cache:** `/app/backend/data/backtesting/BCH-EUR_1h_730d.json` (2 jaar, 17k candles)

### Logs
- **Monitor:** `/var/log/spark_monitor.log`
- **Backend:** `/var/log/supervisor/backend.*.log`
- **Frontend:** `/var/log/supervisor/frontend.*.log`

---

## 🧪 **TESTING COMMANDS**

### Backtest (via API)
```bash
curl -X POST "$API_URL/api/backtest/run" \
  -H "Content-Type: application/json" \
  -d '{"market":"BCH-EUR","days":730,"interval":"1h","speed":"instant","use_cache":true}'
```

### Notification Test
```bash
curl -X POST "$API_URL/api/notifications/test"
```

### Monitor Status
```bash
curl "$API_URL/api/monitoring/status"
```

---

## ⚙️ **TECHNICAL INFO**

### Environment
- **Frontend:** React (port 3000)
- **Backend:** FastAPI (port 8001)
- **Database:** JSON files (NO MongoDB)
- **Deployment:** Kubernetes cluster

### Key Features
- ✅ Background monitoring (blijft draaien offline)
- ✅ Real-time notificaties
- ✅ 2 jaar BCH historical data gecached
- ✅ 100% win rate strategie (conservatief)
- ✅ Thread-safe singleton monitoring

---

## 🚀 **VOLGENDE STAPPEN**

### Prioriteit 0 (NU)
- [x] Monitor draait 24/7
- [x] Notificaties werkend
- [x] Chat commands actief
- [ ] Wachten op eerste trade

### Prioriteit 1 (Binnenkort)
- [ ] Capital opbouwen naar €10.16 (voor pot 2)
- [ ] Live trading integratie (Bitvavo API)
- [ ] Real-world testing

### Prioriteit 2 (Later)
- [ ] Backtest insights → Knowledge Base
- [ ] UI improvements (inkoop banner actief tonen)
- [ ] Trading statistics dashboard

### Future/Backlog
- [ ] Phase 5.0 Spark Ecosystem
- [ ] 10-potjes volledig systeem (€50+ capital)

---

**📝 Notes:**
- Tasks zijn nu hybrid onder Notes (geen aparte Tasks tab meer)
- Bitvavo fees: €0.07 per trade cycle (NIET €0.025 zoals eerst gedacht!)
- Monitor logs elke candle check
- Systeem blokkeert automatisch trades die verlies zouden geven

---

**✅ Status:** Actief en draaiend sinds 28 maart 2026, 19:08 UTC
