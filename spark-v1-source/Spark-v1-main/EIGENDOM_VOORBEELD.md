# Spark Core Eigendom - Voorbeeld

## Start Situatie

**Spark Core (user-000):**
- Value: €0
- Tokens: 0 (Spark heeft NOOIT tokens!)

**Users:**
- Niemand heeft nog tokens

---

## Stap 1: Users Storten

**user-001:**
- Deposit: €50
- Spark Core value: €50

**user-002:**
- Deposit: €30
- Spark Core value: €80

**Resultaat:**
- Spark Core: €80
- Nog geen tokens uitgegeven
- Users hebben alleen EUR (liquide)

---

## Stap 2: Users Kopen Tokens

**user-001:**
- Buy 2 tokens (€50)
- EUR: €0 (omgezet)
- Tokens: 2

**user-002:**
- Buy 1 token (€30)
- EUR: €0 (omgezet)
- Tokens: 1

**Resultaat:**
```
Spark Core: €80
Total tokens: 3 (allemaal bij users!)
Token price: €80 / 3 = €26.67

user-001: 2 tokens = 66.67% eigendom = €53.34
user-002: 1 token  = 33.33% eigendom = €26.67
```

---

## Stap 3: Trading Winst

**Trade profit: +€120**

```
Spark Core: €200 (€80 + €120)
Total tokens: 3 (onveranderd)
Token price: €200 / 3 = €66.67 ⬆️

user-001: 2 tokens = 66.67% = €133.34 (was €53.34)
user-002: 1 token  = 33.33% = €66.67  (was €26.67)
```

**Effect:**
- user-001 tokens +€80 waard
- user-002 tokens +€40 waard
- Proportioneel aan eigendom!

---

## Stap 4: Nieuwe User

**user-003 deposits €100:**

```
Spark Core: €300
Total tokens: 3 (nog niet gekocht)
```

**user-003 buys 1 token (€100):**

```
Spark Core: €300
Total tokens: 4
Token price: €300 / 4 = €75

user-001: 2 tokens = 50.00% = €150
user-002: 1 token  = 25.00% = €75
user-003: 1 token  = 25.00% = €75
```

**Effect:**
- Token price daalt (€66.67 → €75) door dilutie
- Maar absolute waarde blijft gelijk
- user-003 koopt "in" tegen actuele prijs

---

## Withdrawal Scenario

**user-001 withdraws €50:**

```
Spark Core: €250 (€300 - €50)
Total tokens: 4
Token price: €250 / 4 = €62.50 ⬇️

user-001: 2 tokens = 50% = €125
user-002: 1 token  = 25% = €62.50
user-003: 1 token  = 25% = €62.50
```

**Effect:**
- Spark Core value daalt
- Token price daalt
- Alle holders verliezen proportioneel

---

## Belangrijke Regels

1. **Spark Core heeft NOOIT tokens**
   - user-000 = alleen vermogen
   - Geen eigendomsclaim

2. **Users bezitten 100%**
   - Via hun tokens
   - Proportioneel aan aantal tokens

3. **Token price is dynamisch**
   - Stijgt bij trade profit
   - Daalt bij withdrawals
   - Dilutie bij nieuwe tokens

4. **Geen dubbele waarde**
   - EUR OF tokens
   - Niet beide

5. **Transparant eigendom**
   - Ownership % = tokens / total
   - Altijd 100% bij users
   - Real-time berekend
