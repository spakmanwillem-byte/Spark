# ROAR Token Economie - Gebruikers Eigendom Model

## Concept: Users Own 100% via Tokens

**Spark Core (user-000):**
- Bevat het totale systeem vermogen
- **Heeft GEEN tokens**
- Is het "kasboek" van het systeem

**Users (user-001, user-002, etc.):**
- Bezitten ALLE tokens
- Tokens = eigendom van Spark Core
- 100% van systeem is eigendom van users

---

## Eigendomsverhouding

```
Spark Core Value = €100
Total User Tokens = 10

User-001: 6 tokens = 60% eigendom = €60 waarde
User-002: 4 tokens = 40% eigendom = €40 waarde

Spark Core (user-000): 0 tokens = geen eigendom, alleen vermogen
```

---

## Hoe Het Werkt

### 1. Spark Core Vermogen
```
Spark Core Value = Alle deposits + Trade profit - Withdrawals
```

**Voorbeeld:**
- Users storten totaal: €10.16
- Trading bot maakt winst: €50.00
- **Totaal Spark Core: €60.16**

### 2. Token Prijs (Dynamisch)
```
Token Price = Spark Core Value / Total Tokens Distributed
```

**Voorbeeld:**
- Spark Core: €60.16
- Tokens distributed: 2
- **Token prijs: €60.16 / 2 = €30.08**

### 3. User Wallet

**EUR Balance:**
- Alleen deposits en withdrawals
- NIET beïnvloed door token aankoop
- User heeft ALTIJD zijn deposits beschikbaar

**ROAR Tokens:**
- Aantal tokens = aandelen in Spark Core
- Waarde = tokens × current price
- Waarde STIJGT als Spark Core groeit

---

## Voorbeeld Flow

### Situatie A: Start
```
User-001:
  - Deposit: €10.16
  - Buy: 2 ROAR tokens (costs €10.16)
  
Result:
  EUR balance: €0.00 (omgezet naar tokens)
  ROAR tokens: 2
  Token price: €10.16 / 2 = €5.08
  ROAR value: 2 × €5.08 = €10.16
  Total value: €10.16 ✅
```

### Situatie B: Na Trading Winst
```
Spark Core:
  - Trade profit: +€50.00
  - New total: €60.16
  
User-001:
  EUR balance: €0.00 (onveranderd)
  ROAR tokens: 2 (onveranderd)
  Token price: €60.16 / 2 = €30.08 ⬆️
  ROAR value: 2 × €30.08 = €60.16 ⬆️
  Total value: €60.16 ✅
```

### Situatie C: Mix EUR + Tokens
```
User-001:
  - Deposit: €20.00 extra (NIET omgezet)
  
Result:
  EUR balance: €20.00 (liquide)
  ROAR tokens: 2
  Token price: €80.16 / 2 = €40.08
  ROAR value: €80.16
  Total value: €100.16 ✅
  
Breakdown:
  - €20 in EUR (kan withdrawen)
  - €80.16 in tokens (aandelen)
  - Totaal: €100.16 (geen dubbele telling!)
```

---

## Transactie Types

### Deposit (User → Spark Core)
```json
{
  "type": "deposit",
  "user_id": "user-001",
  "amount_eur": 10.00
}
```
- ✅ Verhoogt user EUR balance
- ✅ Verhoogt Spark Core value
- ✅ Verhoogt token prijs (voor iedereen)

### Buy ROAR (Aandelen Kopen)
```json
{
  "type": "buy_roar",
  "user_id": "user-001",
  "token_amount": 2.0,
  "amount_eur": 10.16
}
```
- ❌ GEEN effect op EUR balance (deposits blijven!)
- ✅ User krijgt tokens (aandelen)
- ✅ Tokens vertegenwoordigen % van Spark Core

### Trade Profit (Winst → Spark Core)
```json
{
  "type": "trade_profit",
  "user_id": "user-000",
  "amount_eur": 50.00
}
```
- ✅ Verhoogt Spark Core value
- ✅ Verhoogt token prijs
- ✅ Alle token holders profiteren

### Withdrawal (Spark Core → User)
```json
{
  "type": "withdrawal",
  "user_id": "user-001",
  "amount_eur": 10.00
}
```
- ❌ Verlaagt user EUR balance
- ❌ Verlaagt Spark Core value
- ❌ Verlaagt token prijs

---

## Balans Berekeningen

### User EUR Balance
```python
EUR = SUM(deposits) 
    - SUM(buy_roar.amount)  # EUR wordt omgezet!
    + SUM(sell_roar.amount)
    - SUM(withdrawals)
```

### User ROAR Balance
```python
ROAR = SUM(buy_roar.tokens) 
     + SUM(admin_grant.tokens)
     - SUM(sell_roar.tokens)
```

### Spark Core Value
```python
Core Value = SUM(all deposits) 
           + SUM(trade_profit) 
           - SUM(all withdrawals)
           - SUM(all sell_roar)
```

### Token Price
```python
Price = Spark Core Value / Total User Tokens

# user-000 (Spark Core) heeft GEEN tokens!
# Alleen user tokens tellen mee
```

### User Ownership %
```python
Ownership = (User Tokens / Total User Tokens) × 100%
```

### User ROAR Value
```python
ROAR Value = User Tokens × Token Price
```

### User Total Value (No Duplication!)
```python
Total = EUR Balance + ROAR Value
```

**Belangrijk:** Geld zit OF in EUR OF in tokens, NIET beide!

---

## Voordelen Model

### 1. Transparant
- Alle users zien token prijs
- Prijs = direct resultaat van Spark Core performance
- Geen verborgen kosten

### 2. Fair
- Trading winst wordt gedeeld met ALLE token holders
- Niemand kan individueel profiteren zonder anderen
- Proportioneel aan aantal tokens

### 3. Flexibel
- Token prijs past zich automatisch aan
- Geen handmatige prijsaanpassingen nodig
- Real-time waardering

### 4. Veilig
- EUR deposits blijven beschikbaar
- Users kunnen altijd withdrawals doen
- ROAR tokens zijn extra, niet vereist

---

## API Response

```json
{
  "balances": {
    "eur": 10.16,
    "roar": 2.0,
    "roar_value_eur": 60.16
  },
  "roar_market": {
    "current_price": 30.08,
    "spark_core_value": 60.16,
    "circulating": 2.0,
    "note": "Token price = Spark Core value / total tokens (SHARES)"
  }
}
```

---

## Code Locatie

- **Central Wallet:** `/app/backend/routes/central_wallet_routes.py`
- **Balans berekening:** `calculate_user_balance()` (regel 66)
- **Spark Core value:** `calculate_spark_core_value()` (regel 100)
- **Trade profit script:** `/app/backend/book_trade_profit.py`
