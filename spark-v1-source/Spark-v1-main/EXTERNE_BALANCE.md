# Spark Core - Externe Balance Source

## Concept

Spark Core value = **ECHTE** Bitvavo wallet balance, NIET interne berekeningen.

---

## Hoe Het Werkt

### 1. External Balance File
```
/app/backend/data/financial/spark_core_balance.json
```

Dit bestand bevat de ACTUELE Bitvavo balance:
```json
{
  "spark_core": {
    "balance_eur": 15.40,
    "source": "bitvavo",
    "last_updated": "2026-03-29T22:00:00Z"
  }
}
```

### 2. Token Price Berekening
```
Token Price = External Bitvavo Balance / Total User Tokens
```

**Voorbeeld:**
```
Bitvavo balance: €15.40
Total tokens: 3
Token price: €15.40 / 3 = €5.13
```

### 3. GEEN Interne Boekhouding
- Deposits tellen NIET mee voor Core value
- Trade_profit transacties worden GENEGEERD
- Alleen externe balance is de waarheid

---

## Balance Updaten

### Optie 1: Handmatig (Aanbevolen)
```bash
# Edit het bestand
nano /app/backend/data/financial/spark_core_balance.json

# Update balance_eur naar actuele waarde
{
  "spark_core": {
    "balance_eur": 20.50,  # <-- nieuwe waarde
    "last_updated": "2026-03-29T23:00:00Z"
  }
}

# Restart backend (optioneel, hot reload werkt ook)
sudo supervisorctl restart backend
```

### Optie 2: Via Script (Toekomstig)
```bash
# Sync van Bitvavo API
python3 /app/backend/sync_bitvavo_balance.py

# Of via cron job (elke 10 minuten)
*/10 * * * * python3 /app/backend/sync_bitvavo_balance.py
```

### Optie 3: Via Admin API Endpoint (Toekomstig)
```bash
curl -X POST https://spark.../api/admin/sync-bitvavo \
  -H "Authorization: Bearer admin_token"
```

---

## Effect op Users

**user-001:**
- Heeft 2 tokens
- Bitvavo balance: €15.40
- Token price: €15.40 / 3 = €5.13
- user-001 value: 2 × €5.13 = **€10.27**

**Bij Bitvavo winst (+€10):**
- Nieuwe balance: €25.40
- Token price: €25.40 / 3 = €8.47 ⬆️
- user-001 value: 2 × €8.47 = **€16.94** ⬆️

**Bij Bitvavo verlies (-€5):**
- Nieuwe balance: €10.40
- Token price: €10.40 / 3 = €3.47 ⬇️
- user-001 value: 2 × €3.47 = **€6.93** ⬇️

---

## Waarom Externe Balance?

### ✅ Voordelen:
1. **Real value** - geen simulatie
2. **Transparant** - users zien echte Bitvavo waarde
3. **Eerlijk** - winst/verlies wordt direct gedeeld
4. **Simpel** - 1 bron van waarheid

### ❌ Oude Methode (Deposits + Trade Profit):
1. Interne boekhouding kon afwijken van werkelijkheid
2. "Fake" trade profit creëerde verwarring
3. Value mismatch tussen systeem en Bitvavo
4. Onduidelijk wat "echt" was

---

## Fallback

Als externe balance file niet bestaat of onleesbaar is:
```python
# Fallback: som van deposits
fallback_value = SUM(deposits) - SUM(withdrawals)
```

⚠️ Dit is alleen voor development/testing!
In productie moet altijd externe balance worden gebruikt.

---

## Monitoring

```bash
# Check huidige balance
cat /app/backend/data/financial/spark_core_balance.json

# Check wat API returnt
curl http://localhost:8001/api/central/wallet/user-001 | jq '.roar_market.spark_core_value'

# Check logs voor warnings
tail -f /var/log/supervisor/backend.out.log | grep "external"
```

---

## Implementatie Details

**Code:** `/app/backend/routes/central_wallet_routes.py`

```python
def calculate_spark_core_value(transactions: list):
    # Read REAL external balance
    if os.path.exists(SPARK_CORE_BALANCE_FILE):
        with open(SPARK_CORE_BALANCE_FILE, 'r') as f:
            config = json.load(f)
            return config['spark_core']['balance_eur']
    
    # Fallback (testing only)
    return sum_of_deposits()
```

**Key Points:**
- Externe file heeft prioriteit
- Geen interne berekeningen
- Token prijs = real-time op basis van Bitvavo
