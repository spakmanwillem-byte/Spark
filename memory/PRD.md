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
- Totaal gestort: €50.80 op Bitvavo
- Prijs nu DYNAMISCH: Spark Core waarde / circulerende tokens = €5.08
- Alleen hele tokens kopen/verkopen

## Roadkill Shop
- Merch: Roadkill Cap (€17.50), Hoodie (€55), Hoodie+Broek Set (€85)
- ROAR Token als apart product (dynamische prijs)
- Winkelwagen + bestelsysteem + kasboek koppeling

## Kasboeken (4 stuks)
1. **Spark AI** — Bitvavo wallet (€50.80)
2. **Spark Zorgboerderij** — IBAN: NL43 INGB 0006 6836 13
3. **Roadkill Shop** — IBAN: NL43 INGB 0006 6836 13
4. **Mijn Prive** — Per-user kasboek, IBAN uit Mijn Profiel (gekoppeld via user_id)

## Profiel-Kasboek Koppeling
- Mijn Profiel bevat nu IBAN + Bank velden
- IBAN wordt automatisch gekoppeld aan persoonlijk kasboek via user_id
- Wallet (user_id) → Profiel (user_id) → Kasboek (user_id) = verbonden maar gescheiden
- Schaalbaar: elke nieuwe gebruiker krijgt automatisch eigen kasboek

## Voltooide Pagina's
### WORKSPACE
- [x] Dashboard, Gesprekken, Kennisbank, Agenda, Dagboek, Notities & Taken, Roadmap
### SPARK AI
- [x] Spark Brain, Triggers, Emoties, Verbanden
### MODULES
- [x] Trade, Wallet, Winkel (Roadkill Shop), Boekhouding (4 kasboeken)
- [x] Achievements, Leaderboard, Persoonskaarten, Community, Integraties
### BEHEER
- [x] Mijn Profiel (incl. IBAN/bank), Gebruikers, Analytics, Instellingen

## Recente toevoegingen
- [x] Live Bitvavo trading (API keys, P&L met fees, trailing stop)
- [x] 10-Potjes trading systeem met exponentiële volume-scaling
- [x] Trading Context engine (S/R, trend, patronen)
- [x] Donaties/Deposits tracker voor baseline P&L
- [x] Draggable sidebar (reorderable nav items)
- [x] User Admin: Add user modal + Persoonskaarten per user
- [x] Chat Archive systeem (per-user gesprekslogs)
- [x] Knowledge Snap systeem
- [x] Spark Brain Bijbel CRUD endpoints (POST/PUT/DELETE /api/spark/bijbel/{section})
- [x] **Users admin**: Verwijder knop (admin user-001 beschermd) + Reset WW knop (default Welkom01) [20 apr 2026]

## Backlog
- [ ] Spark Brain Bijbel Editor UI (frontend add/edit modals voor kernwaarden/normen/bijbel/doelen)
- [ ] 5 Test accounts voor NLP live-test (moeder, dochter, zusje, zusje's dochter, oud-collega)
- [ ] Baseline scan rapport (triggers, knowledge cards, NLP-woordenschat vóór test)
- [ ] Intent-laag: chat queries → live data acties (bv. "Heb je winst?" → Bitvavo P&L)
- [ ] Triggers simplificeren (1 trigger = 1 woord, NLP synoniemen)
- [ ] BTW-rapportage
- [ ] Backtesting module
- [ ] Knowledge Quiz
- [ ] Knowledge kaarten context-antwoorden (Spark-stijl)
- [ ] Core Protection & Sandbox Split (v4.1 roadmap)

## Datum: 20 april 2026
