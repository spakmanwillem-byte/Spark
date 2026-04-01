# Spark Core 2.0 - PRD

## Origineel Verzoek
Herbouw "Spark AI" als "Spark Core 2.0" - volledig standalone, modulair, zonder cloud of MongoDB. Alle data in lokale JSON bestanden. Dark-themed dashboard.

## Tech Stack
- **Backend**: FastAPI + JSON file storage (geen MongoDB!)
- **Frontend**: React + Tailwind CSS + Lucide icons
- **Auth**: JWT token-based met lokale users.json
- **Externe API**: Bitvavo publieke API (candles, tickers)

## ROAR Token Systeem
- Token = aandeel in Spark Core, dynamische prijs
- User-001: 11 ROAR, User-000 (Spark): 999,989 treasury
- Systeem gereset: EUR €0 (alles opgenomen van Bitvavo)

## Bot Systeem
- Madelief Stouten: sociaal, reageert op groeten
- Harry Klokkenmaker: tijdsmelding, reageert op "hoe laat"
- Mr Smith: security, reageert op bugs/errors
- Bots reageren automatisch op keyword triggers in community chat

## Voltooide Pagina's

### WORKSPACE
- [x] Dashboard, Gesprekken, Kennisbank, Agenda, Dagboek, Notities & Taken, Roadmap

### SPARK AI
- [x] Spark Brain, Triggers, Emoties, Verbanden

### MODULES
- [x] Trade (BCH candles 15m/1h/4h/1d, countdown, watchlist, monitor, snel handelen)
- [x] Wallet (EUR, ROAR, opnames, transacties, Spark Card)
- [x] Winkel (ROAR Token kopen/verkopen, dynamische prijs)
- [x] Boekhouding (4 kasboeken)
- [x] Achievements, Leaderboard, Persoonskaarten
- [x] **Community** (bot chat, keyword triggers, V1 berichten)
- [x] Integraties

### BEHEER
- [x] Mijn Profiel, Gebruikers, Analytics, Instellingen

## Backlog
- [ ] BTW-rapportage
- [ ] Instellingen backend
- [ ] Live Bitvavo trading
- [ ] Backtesting module (V1 data beschikbaar)
- [ ] Cross-reference spark-v1-source

## Datum: 1 april 2026
