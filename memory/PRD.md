# Spark Core 2.0 - PRD

## Origineel Verzoek
Herbouw "Spark AI" als "Spark Core 2.0" - volledig standalone, modulair, zonder cloud of MongoDB. Alle data in lokale JSON bestanden. Dark-themed dashboard.

## Tech Stack
- **Backend**: FastAPI + JSON file storage (geen MongoDB!)
- **Frontend**: React + Tailwind CSS + Lucide icons
- **Auth**: JWT token-based met lokale users.json
- **Externe API**: Bitvavo publieke API (candles, tickers - geen auth nodig)

## Voltooide Pagina's

### WORKSPACE
- [x] Dashboard, Gesprekken, Kennisbank, Agenda, Dagboek, Notities & Taken, Roadmap

### SPARK AI
- [x] Spark Brain, Triggers, Emoties, Verbanden (Knowledge Graph)

### MODULES
- [x] **Trade** - Crypto Trader met:
  - Live candle grafiek (OHLC) via Bitvavo API, interval selectie (1h/4h/1d), markt selectie
  - Watchlist: BCH, BTC, ETH, SOL, ADA live prijzen + 24h % change
  - Monitor systeem: Background thread, Start/Stop/Pause, Bollinger Band decision engine, auto-trade optie
  - Snel Handelen: Koop/Verkoop uitvoeren (mock of live), resultaat feedback
  - Bitvavo integratie tab (API credentials + instellingen)
  - 287+ historische BCH-EUR trades
- [x] **Wallet** - Spark Tokens, Credits, EUR saldo, Opname systeem, Transactie Geschiedenis, Spark Card
- [x] Winkel (hardcoded frontend)
- [x] Boekhouding - 4 kasboeken
- [x] Achievements, Leaderboard, Persoonskaarten, Integraties

### BEHEER
- [x] Mijn Profiel, Gebruikers, Analytics, Instellingen

## Recent Voltooid (1 april 2026)
- [x] Wallet UI hersteld met originele layout + echte API data, entiteiten verwijderd
- [x] Trader UI hersteld + 4 nieuwe features:
  - Live Bitvavo candle grafiek (BCH/BTC/ETH/SOL/ADA)
  - Watchlist met 5 coins + live prijzen
  - Monitor systeem met start/stop/pause + decision engine
  - Werkend Snel Handelen panel (mock trades)
- [x] Opname endpoint (POST /api/wallet/withdraw/{user_id})
- [x] Testing iteratie 9: 100% backend + 100% frontend

## API Endpoints (Trade)
- GET /api/trade/candles?market=X&interval=X&limit=X (Bitvavo publiek)
- GET /api/trade/tickers (5 coins live)
- POST /api/trade/execute/{user_id} (mock/live trade)
- POST /api/trade/monitor/start|stop|pause
- GET /api/trade/monitor/status|decisions

## Backlog
- [ ] Winkel backend (store API koppelen)
- [ ] BTW-rapportage (automatisch BTW rapport)
- [ ] Instellingen backend koppeling
- [ ] Live Bitvavo trading (met echte API keys - user koppelt zelf)
- [ ] Cross-reference met spark-v1-source voor gemiste features

## Datum: 1 april 2026
