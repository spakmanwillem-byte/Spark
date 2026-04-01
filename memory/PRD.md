# Spark Core 2.0 - PRD

## Origineel Verzoek
Herbouw "Spark AI" als "Spark Core 2.0" - volledig standalone, modulair, zonder cloud of MongoDB. Alle data in lokale JSON bestanden. Dark-themed dashboard.

## Tech Stack
- **Backend**: FastAPI + JSON file storage (geen MongoDB!)
- **Frontend**: React + Tailwind CSS + Lucide icons
- **Auth**: JWT token-based met lokale users.json
- **Externe API**: Bitvavo publieke API (candles, tickers)

## ROAR Token Systeem
- Token = aandeel in Spark Core. 1 ROAR = 1 deel van totale waarde
- Dynamische prijs = Spark Core totale waarde / circulerende tokens
- Basis prijs: €5.08, stijgt door trading profits
- User-001 (Willem): 11 ROAR tokens
- User-000 (Spark): 999,989 treasury
- Total supply: 1,000,000 ROAR
- V1 data gemigreerd: deposits, buy_roar, profits

## Voltooide Pagina's

### WORKSPACE
- [x] Dashboard, Gesprekken, Kennisbank, Agenda, Dagboek, Notities & Taken, Roadmap

### SPARK AI
- [x] Spark Brain, Triggers, Emoties, Verbanden (Knowledge Graph)

### MODULES
- [x] **Trade** - BCH-EUR candles (15m/1h/4h/1d), countdown timer, Watchlist (5 coins), Monitor (Bollinger Band), Snel Handelen, Bitvavo integratie
- [x] **Wallet** - EUR saldo, ROAR saldo, Opname systeem, Transacties, Spark Card, Betaalmethoden
- [x] **Winkel** - ROAR Token Winkel: kopen/verkopen, dynamische prijs, Token Verdeling, V1 transactie geschiedenis
- [x] Boekhouding - 4 kasboeken
- [x] Achievements, Leaderboard, Persoonskaarten, Integraties

### BEHEER
- [x] Mijn Profiel, Gebruikers, Analytics, Instellingen

## Recent Voltooid (1 april 2026)
- [x] ROAR Token systeem herbouwd van generieke items naar echt token trading
- [x] V1 financiële data gemigreerd (deposits, buy_roar, profits)
- [x] Dynamische token pricing op basis van Spark Core waarde
- [x] Koop/Verkoop functionaliteit met EUR wallet integratie
- [x] Wallet page toont nu ROAR balance + waarde + token prijs
- [x] Testing iteratie 11: 100% backend (17/17) + 100% frontend

## Backlog
- [ ] BTW-rapportage
- [ ] Instellingen backend
- [ ] Live Bitvavo trading (met echte API keys)
- [ ] Potjes systeem frontend
- [ ] Cross-reference spark-v1-source

## Datum: 1 april 2026
