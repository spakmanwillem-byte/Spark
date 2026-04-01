# Spark Core 2.0 - PRD

## Origineel Verzoek
Herbouw "Spark AI" als "Spark Core 2.0" - volledig standalone, modulair, zonder cloud of MongoDB. Alle data in lokale JSON bestanden. Dark-themed dashboard.

## Tech Stack
- **Backend**: FastAPI + JSON file storage (geen MongoDB!)
- **Frontend**: React + Tailwind CSS + Lucide icons
- **Auth**: JWT token-based met lokale users.json
- **Externe API**: Bitvavo publieke API (candles, tickers)

## Token Systeem
- User-001 (Willem): 11 tokens
- Spark System (user-000): Treasury 49989 tokens
- Tokens worden besteed in Winkel, teruggestort naar Spark treasury
- Opnames via wallet reduceren tokens proportioneel

## Voltooide Pagina's

### WORKSPACE
- [x] Dashboard, Gesprekken, Kennisbank, Agenda, Dagboek, Notities & Taken, Roadmap

### SPARK AI
- [x] Spark Brain, Triggers, Emoties, Verbanden (Knowledge Graph)

### MODULES
- [x] **Trade** - Crypto Trader:
  - BCH-EUR candle grafiek (OHLC) via Bitvavo API
  - Interval: 15m, 1h, 4h, 1d + countdown timer per candle
  - Watchlist: BCH, BTC, ETH, SOL, ADA live prijzen
  - Monitor: Background thread, Start/Stop/Pause, Bollinger Band engine
  - Snel Handelen: Koop/Verkoop (mock/live)
  - Bitvavo integratie tab
- [x] **Wallet** - Tokens, Credits, EUR saldo, Opname systeem, Transacties, Spark Card
- [x] **Winkel** - Shop met token aankopen (6 items, token balance, purchase flow)
- [x] Boekhouding - 4 kasboeken
- [x] Achievements, Leaderboard, Persoonskaarten, Integraties

### BEHEER
- [x] Mijn Profiel, Gebruikers, Analytics, Instellingen

## API Endpoints
- `/api/shop/items|balance|buy|purchases` (Winkel token systeem)
- `/api/trade/candles|tickers|execute|monitor/*` (Trading + monitoring)
- `/api/wallet/user|transactions|withdraw` (Wallet)

## Backlog
- [ ] BTW-rapportage
- [ ] Instellingen backend
- [ ] Live Bitvavo trading (met echte API keys)
- [ ] Cross-reference spark-v1-source

## Datum: 1 april 2026
