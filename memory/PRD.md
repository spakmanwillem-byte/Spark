# Spark Core 2.0 - PRD

## Origineel Verzoek
Herbouw "Spark AI" als "Spark Core 2.0" - volledig standalone, modulair, zonder cloud of MongoDB. Alle data in lokale JSON bestanden. Dark-themed dashboard.

## Tech Stack
- **Backend**: FastAPI + JSON file storage (geen MongoDB!)
- **Frontend**: React + Tailwind CSS + Lucide icons
- **Auth**: JWT token-based met lokale users.json
- **NLP**: Standalone Snap engine (geen spaCy/Levenshtein)

## Voltooide Pagina's (ALLES MET ECHTE API tenzij anders vermeld)

### WORKSPACE
- [x] Dashboard - Live data kaarten
- [x] Gesprekken - Chat met Snap/NLP engine
- [x] Kennisbank - 2424+ kaarten
- [x] Agenda - Week kalender + events CRUD
- [x] Dagboek - Mood tracking + entries CRUD
- [x] Notities & Taken - Hybrid notes+tasks CRUD
- [x] Roadmap - Fase-overzicht

### SPARK AI
- [x] Spark Brain - Identiteit (v1), Normen & Waarden (11 waarden, 6 normen), Spark Bijbel
- [x] Triggers - 258 triggers in 27 groepen
- [x] Emoties - Emotie detectie systeem (4 tabs)
- [x] Verbanden - Knowledge Graph (2424 nodes, 11757 edges, SVG visual, clusters, stats)

### MODULES
- [x] Trade - 287 BCH-EUR trades, stats, Bitvavo integratie, trader settings, draggable cards, prijsgrafiek, Snel Handelen panel
- [x] Wallet - Spark Tokens, Credits, EUR saldo, Opname systeem (withdrawal), Transactie Geschiedenis, Spark Card, Betaalmethoden
- [x] Winkel - Shop met items (HARDCODED - geen backend store)
- [x] Boekhouding - 4 kasboeken (Spark Core, SYL, Roadkill Merch, Persoonlijk), transaction CRUD, BTW
- [x] Achievements (13 milestones, XP)
- [x] Leaderboard
- [x] Persoonskaarten - 6 personen, gradaties, relaties
- [x] Integraties (bestandsbrowser + sandbox)

### BEHEER
- [x] Mijn Profiel
- [x] Gebruikers - Gradatie overzicht (7 levels) + personalia editing
- [x] Analytics
- [x] Instellingen (6 tabs - UI only)

## Recent Voltooid (1 april 2026)
- [x] Wallet UI hersteld met originele mooie layout + echte API data
- [x] Trader UI hersteld met originele mooie layout + echte API data
- [x] Entiteiten verwijderd uit Wallet (verhuisd naar Boekhouding)
- [x] Opname endpoint toegevoegd (POST /api/wallet/withdraw/{user_id})
- [x] Token reductie bij opnames (proportioneel)
- [x] Testing iteratie 8: 100% backend + 100% frontend

## Backlog
- [ ] Live Bitvavo Trading integratie (portfolio sync + live trading loop)
- [ ] Winkel backend (store API koppelen)
- [ ] BTW-rapportage (automatisch BTW rapport op basis van kasboeken)
- [ ] Backend koppelen aan: Instellingen
- [ ] Cross-reference met spark-v1-source voor gemiste features

## Datum: 1 april 2026
