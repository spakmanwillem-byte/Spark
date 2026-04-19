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
- User-001 (Willem): 10 ROAR tokens (100% eigendom)
- User-000 (Spark treasury): 999,990
- Totaal gestort: €50.80 op Bitvavo
- 10 tokens × €5.08 = €50.80 (eerste 10 tokens vaste prijs)
- Prijs is nu DYNAMISCH: Spark Core waarde / circulerende tokens
- Start: €50.80 / 10 = €5.08 per token
- Groeit mee met trading winst van de monitor bot
- Alleen hele tokens kopen/verkopen

## Roadkill Shop
- **Merch producten**: Roadkill Cap (€17.50), Roadkill Hoodie (€55), Hoodie+Broek Set (€85)
- **ROAR Token** als apart product (dynamische prijs)
- Winkelwagen systeem met bestellen
- Bestellingen worden automatisch geboekt in kasboek (Roadkill Merch entity)
- Wallet saldo check bij bestellen

## Kasboeken (4 stuks)
1. **Spark AI** — Bitvavo wallet (€50.80 startkapitaal)
2. **Spark Zorgboerderij** — IBAN: NL43 INGB 0006 6836 13
3. **Roadkill Shop** — IBAN: NL43 INGB 0006 6836 13
4. **Mijn Prive** — Persoonlijk vermogen

## Bot Systeem
- Madelief Stouten: sociaal, reageert op groeten
- Harry Klokkenmaker: tijdsmelding, reageert op "hoe laat"
- Mr Smith: security, reageert op bugs/errors

## Voltooide Pagina's

### WORKSPACE
- [x] Dashboard, Gesprekken, Kennisbank, Agenda, Dagboek, Notities & Taken, Roadmap

### SPARK AI
- [x] Spark Brain, Triggers, Emoties, Verbanden

### MODULES
- [x] Trade (BCH candles, countdown, watchlist, monitor, snel handelen)
- [x] Wallet (EUR, ROAR, opnames, transacties, Spark Card)
- [x] Winkel (Roadkill Merch shop + ROAR Token, winkelwagen, bestelsysteem)
- [x] Boekhouding (4 kasboeken met IBAN/Bitvavo info)
- [x] Achievements, Leaderboard, Persoonskaarten
- [x] Community (bot chat, keyword triggers)
- [x] Integraties

### BEHEER
- [x] Mijn Profiel, Gebruikers, Analytics, Instellingen

## Backlog
- [ ] Bitvavo API keys koppelen (echte trades + saldo ophalen)
- [ ] BTW-rapportage
- [ ] Instellingen backend
- [ ] Backtesting module
- [ ] Knowledge Quiz
- [ ] Knowledge kaarten context-antwoorden (Spark-stijl)

## Datum: 19 april 2026
