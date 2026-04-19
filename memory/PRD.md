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

## Backlog
- [ ] Bitvavo API keys koppelen (echte trades + saldo)
- [ ] BTW-rapportage
- [ ] Instellingen backend
- [ ] Backtesting module
- [ ] Knowledge Quiz
- [ ] Knowledge kaarten context-antwoorden (Spark-stijl)

## Datum: 19 april 2026
