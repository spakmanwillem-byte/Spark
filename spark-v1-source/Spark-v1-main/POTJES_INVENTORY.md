# Potjessysteem - Wat Bestaat Er Al?

**Datum:** 2026-03-30  
**Status:** 📋 INVENTARISATIE

---

## ✅ Wat Er AL Is

### 1. Spark Core Balance System
**File:** `/app/backend/data/financial/spark_core_balance.json`

**Huidige staat:**
```json
{
  "spark_core": {
    "source": "bitvavo_auto_sync",
    "balance_eur": 15.45,  ← Externe Bitvavo balance (auto-sync)
    "last_updated": "2026-03-30T14:42:41"
  },
  "sync": {
    "auto_sync": true,
    "sync_interval_minutes": 30,
    "spark_user_id": "user-001"
  }
}
```

**Functionaliteit:**
- ✅ Auto-sync met Bitvavo (elke 30 min)
- ✅ Cached balance (€15.45 current)
- ✅ Last sync tracking
- ⚠️ Toont TOTALE balance, niet "potjes" onderscheid

**API Endpoints:**
- `GET /api/spark_core/sync/status` - Sync status
- `GET /api/spark_core/sync/balance` - Current balance
- `POST /api/spark_core/sync/enable` - Enable auto-sync
- `POST /api/spark_core/sync/disable` - Disable sync
- `POST /api/spark_core/sync/now` - Trigger sync

---

### 2. Central Wallet / Transaction System
**File:** `/app/backend/data/financial/transactions.json`

**Huidige staat:**
```json
{
  "transactions": [
    {
      "id": "bbe73d73-...",
      "user_id": "user-001",
      "type": "deposit",
      "amount_eur": 10.16,  ← Slechts 2 potjes gelogd
      "timestamp": "2026-03-29T21:33:42"
    },
    {
      "id": "5237ba3c-...",
      "user_id": "user-001",
      "type": "buy_roar",
      "amount_eur": 10.16,
      "token_amount": 2.0,
      "price_per_token": 5.08
    }
  ],
  "roar_config": {
    "initial_price": 5.08,
    "current_price": 5.08
  }
}
```

**Functionaliteit:**
- ✅ Transaction logging (deposit, buy, sell)
- ✅ ROAR token price tracking (€5.08)
- ✅ User balance calculation
- ⚠️ Geen potjes concept (alleen totaal)
- ⚠️ Deposit = alleen gebruikt bedrag (€10,16), niet totaal (€50,80)

**Routes:** `central_wallet_routes.py`

---

### 3. Live Trading System
**Files:**
- `/app/backend/data/live_trading/user-001/runs/{run_id}/position_state.json`
- `/app/backend/services/live_trader_service.py`

**Huidige runs:**
1. `run_user-001_BCH_1774489771` (€4.71)
2. `run_user-001_BCH_1774493528` (€5.02) ← GERESET
3. `test-sync-final` (€4.71) ← Test run?

**Functionaliteit:**
- ✅ Unieke run_id per trade
- ✅ Position state per run
- ✅ Mock vs Real trade support (USE_MOCK_TRADING env)
- ❌ **PROBLEEM:** Position states worden overschreven bij reset
- ❌ **PROBLEEM:** Geen onderscheid test vs echte trades

**Mock vs Real:**
```python
if USE_MOCK_TRADING:
    result = _execute_mock_trade(...)
else:
    result = _execute_real_trade(...)
```

**Position Reset Issue:**
- Run 1774493528 heeft `position_state_backup_before_reset.json`
- Backup entry: 0.02444969 BCH
- Na reset: 0.01264601 BCH
- **Data verloren**

---

### 4. User Wallets (Legacy?)
**File:** `/app/backend/data/wallet/user_wallets.json`

```json
{
  "user-001": {
    "wallet": {
      "spark_tokens": 1000,
      "credits": 250,
      "balance_eur": 0  ← Leeg
    }
  }
}
```

**Status:** Lijkt niet actief gebruikt voor jouw potjessysteem

---

## ❌ Wat ONTBREEKT

### 1. Potjes Tracking System
**Geen file/systeem voor:**
- Totaal aantal potjes (10)
- Potje waarde (€5,08)
- Gebruikt vs beschikbaar
- Potje toewijzing per trade

**Wat nodig is:**
```json
{
  "user-001": {
    "potjes_system": {
      "total_potjes": 10,
      "potje_value_eur": 5.08,
      "total_fund_eur": 50.80,
      "external_location": "bitvavo",
      "potjes": [
        {
          "id": 1,
          "status": "used",
          "run_id": "run_user-001_BCH_1774489771",
          "date_used": "2026-03-26T01:50:50"
        },
        {
          "id": 2,
          "status": "used",
          "run_id": "run_user-001_BCH_1774493528",
          "date_used": "2026-03-30T12:08:16"
        },
        {
          "id": 3,
          "status": "available"
        },
        // ... tot 10
      ],
      "available_potjes": 8,
      "used_potjes": 2
    }
  }
}
```

---

### 2. Test vs Real Trade Marking
**Huidige situatie:**
- Alle runs zien er hetzelfde uit
- `test-sync-final` lijkt test, maar niet expliciet gemarkeerd
- Action log heeft test trades (manual_001_xxx) maar geen scheiding

**Wat nodig is:**
- `is_test: true/false` flag per run
- Filter in queries (alleen echte trades tonen)
- Aparte test directory? `/test_runs/` vs `/live_runs/`

---

### 3. Position State Protection
**Huidige situatie:**
- Reset functie overschrijft position_state.json
- Backup wordt gemaakt MAAR origineel is weg
- Geen append-only / immutable log

**Wat nodig is:**
```python
# Option 1: Append-only log
position_state.json → NOOIT overschrijven
position_updates.json → Append updates

# Option 2: Versioning
position_state_v1.json
position_state_v2.json (na reset)
position_state.json → symlink naar latest

# Option 3: Immutable + current pointer
positions/
  - 2026-03-26_01-50-50.json
  - 2026-03-30_12-08-16.json
  - current.json → symlink
```

---

### 4. Duidelijk Extern vs Intern Onderscheid

**Extern (Bitvavo):**
- Totaal fund: €50,80
- Current balance (auto-sync): €15,45
- Beschikbaar voor nieuwe trades

**Intern (Spark systeem):**
- Gebruikt: 2 potjes = €10,16
- Trades: 2 runs
- Token holdings

**UI moet tonen:**
```
Potjessysteem
├─ Totaal fund (extern): €50,80
├─ Gebruikt: 2 potjes (€10,16)
├─ Beschikbaar: 8 potjes (€40,64)
└─ Bitvavo balance: €15,45 (live)
```

---

## 🔧 Bestaande Code om Te Gebruiken

### 1. Spark Core Sync Service
**File:** `/app/backend/services/spark_core_sync_service.py`

**Functionaliteit:**
```python
def sync_spark_core_balance():
    """Auto-sync Bitvavo balance"""
    balance = BitvavoService.get_balance("EUR")
    # Updates spark_core_balance.json
```

**Hergebruik:**
- ✅ Al werkend voor extern balance tracking
- Kan uitgebreid worden met potjes status

---

### 2. Central Wallet Routes
**File:** `/app/backend/routes/central_wallet_routes.py`

**Functionaliteit:**
```python
def calculate_user_balance(user_id, transactions):
    """Calculate EUR and ROAR balance"""
    # Loops door transactions
```

**Hergebruik:**
- ✅ Transaction logging infrastructure
- Kan uitgebreid met potjes transactions

---

### 3. Live Trader Service
**File:** `/app/backend/services/live_trader_service.py`

**Functionaliteit:**
```python
@staticmethod
def execute_decision(decision, user_id, run_id, market, config):
    """Execute trade"""
    if USE_MOCK_TRADING:
        return _execute_mock_trade(...)
    else:
        return _execute_real_trade(...)
```

**Te fixen:**
- ❌ Position state overschrijving
- Toevoegen: `is_test` flag
- Toevoegen: Potje linking

---

## 🎯 Conclusie Inventarisatie

### ✅ GOED NIEUWS
1. **Spark Core Balance auto-sync** werkt al → extern balance tracking
2. **Transaction system** bestaat al → kan uitgebreid worden
3. **Unieke run_ids** werken al → geen dubbele trades
4. **Mock vs Real** switch bestaat al → USE_MOCK_TRADING

### ⚠️ ONTBREEKT
1. **Potjes tracking** - geen systeem voor 10 potjes concept
2. **Extern vs Intern onderscheid** - alleen totalen, geen "beschikbaar vs gebruikt"
3. **Position state protection** - reset overschrijft data
4. **Test vs Real marking** - geen expliciete flags

### 🔧 MOET GEBOUWD
1. **Potjes data model** (nieuw JSON file of extend transactions)
2. **Position state append-only system** (fix overschrijving)
3. **Test run filtering** (is_test flag + queries)
4. **UI voor potjes overzicht** (extern fund + beschikbaar/gebruikt)

---

## 📋 Aanbevolen Aanpak

### Stap 1: Potjes Data Model (Minimaal)
**File:** `/app/backend/data/financial/user_potjes.json`

```json
{
  "user-001": {
    "total_fund_eur": 50.80,
    "external_location": "bitvavo",
    "potje_value_eur": 5.08,
    "total_potjes": 10,
    "used_count": 2,
    "available_count": 8,
    "used_potjes": [
      {
        "potje_id": 1,
        "run_id": "run_user-001_BCH_1774489771",
        "date_used": "2026-03-26T01:50:50",
        "amount_eur": 4.71
      },
      {
        "potje_id": 2,
        "run_id": "run_user-001_BCH_1774493528",
        "date_used": "2026-03-30T12:08:16",
        "amount_eur": 5.02
      }
    ]
  }
}
```

### Stap 2: Position State Protection
**Change:** `/app/backend/services/live_trader_service.py`

```python
# VOOR: Overschrijft position_state.json
def reset_position(...):
    DataManager.save_json(position_file, new_state)

# NA: Append-only
def reset_position(...):
    # Backup with timestamp
    backup_file = f"position_state_{timestamp}.json"
    shutil.copy(position_file, backup_file)
    
    # Create new version
    DataManager.save_json(position_file, new_state)
    
    # Log reset
    resets_log.append({
        "timestamp": timestamp,
        "old_file": backup_file,
        "reason": reason
    })
```

### Stap 3: Test Run Flag
**Add to run creation:**
```python
run_data = {
    "run_id": run_id,
    "is_test": is_test,  # ← NIEUW
    "created_at": timestamp
}
```

### Stap 4: UI Endpoint
**Nieuw:** `GET /api/potjes/status/{user_id}`

```json
{
  "total_fund_eur": 50.80,
  "potje_value_eur": 5.08,
  "total_potjes": 10,
  "used": 2,
  "available": 8,
  "bitvavo_balance": 15.45,
  "used_potjes": [...]
}
```

---

**Status:** Inventarisatie compleet - Klaar voor implementatie planning
