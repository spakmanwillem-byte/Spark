# ROAR Economic System - Kasboek Architectuur

## Gescheiden Kasboeken

### 1. **Spark Core - ROAR Economie** (Intern)
- **Locatie:** `/app/backend/data/financial/transactions.json`
- **Prijs:** €5.08 FIXED (niet gekoppeld aan Bitvavo)
- **Transactie types:**
  - `buy_roar`: Gebruiker koopt ROAR tokens
  - `sell_roar`: Gebruiker verkoopt ROAR tokens (toekomstig)
  - `deposit`: Gebruiker stort EUR
  - `admin_grant`: Admin geeft tokens weg
  - `reward`: Systeem rewards

### 2. **Bitvavo Trading Bot** (Extern)
- **Locatie:** `/app/backend/data/live_trading/position_state.json`
- **Doel:** Automatische BCH trading (10-potjes systeem)
- **NIET gekoppeld aan ROAR prijs**
- **Data:**
  - `trade_amount`: Huidige inzet per trade
  - `total_profit`: Totale winst van bot
  - `position`: Current trading position

## API Response Structuur

```json
{
  "balances": {
    "eur": 4.29,
    "roar": 14.0,
    "roar_value_eur": 71.12
  },
  "roar_market": {
    "current_price": 5.08,
    "total_supply": 1000000,
    "circulating": 14.0,
    "note": "Internal ROAR economy - fixed price"
  },
  "bitvavo_trading": {
    "trade_amount": 5.12,
    "total_profit": 245.67,
    "position": "long",
    "description": "External Bitvavo trading - NOT part of ROAR economy"
  }
}
```

## Berekeningen

### ROAR Balance (per user):
```
ROAR tokens = SUM(buy_roar.token_amount) - SUM(sell_roar.token_amount)
ROAR value = tokens * ROAR_PRICE_FIXED (5.08)
```

### EUR Balance (per user):
```
EUR = SUM(deposits) - SUM(buy_roar.amount_eur) + SUM(sell_roar.amount_eur)
```

### Circulating Supply:
```
Circulating = TOTAAL tokens distributed via buy_roar + admin_grant
Spark reserve = total_supply - circulating
```

## Waarom Gescheiden?

**Probleem (oud):**
- ROAR prijs kwam uit Bitvavo bot state (`position_state.json`)
- Als bot €5.12 had → ROAR tokens = €5.12
- Dit creëerde verwarring: is ROAR waarde afhankelijk van trading?

**Oplossing (nieuw):**
- ROAR heeft **vaste prijs** van €5.08
- Bitvavo trading is **apart kasboek**
- Geen verwarring: ROAR economie = intern, Trading = extern

## Toekomstige Uitbreidingen

Als je Bitvavo winst wilt koppelen aan ROAR:
1. Maak nieuwe transaction type: `"trade_profit"`
2. Boek Bitvavo winst als deposit naar Spark Core wallet
3. Blijf kasboeken gescheiden maar link via expliciete transacties

## Code Locatie

- **Central Wallet:** `/app/backend/routes/central_wallet_routes.py`
- **ROAR prijs:** `ROAR_PRICE_FIXED = 5.08` (regel 23)
- **Bitvavo state:** `get_bitvavo_state()` (regel 86)
