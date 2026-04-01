# Spark Core 2.0 - PRD

## Origineel Verzoek
Herbouw "Spark AI" als "Spark Core 2.0" - volledig standalone, modulair, zonder cloud of MongoDB. Alle data in lokale JSON bestanden. Dark-themed dashboard.

## Tech Stack
- **Backend**: FastAPI + JSON file storage (geen MongoDB!)
- **Frontend**: React + Tailwind CSS + Lucide icons
- **Auth**: JWT token-based met lokale users.json
- **Storage**: `/app/backend/data/*.json`
- **NLP**: Standalone Snap engine (geen spaCy/Levenshtein)

## Voltooide Pagina's (ALLES MET ECHTE API)

### WORKSPACE
- [x] Dashboard - Live data kaarten
- [x] Gesprekken - Chat met Snap/NLP engine
- [x] Kennisbank - 2424+ kaarten zoeken/bewerken
- [x] Agenda - Week kalender + events CRUD
- [x] Dagboek - Mood tracking + entries CRUD
- [x] Notities & Taken - Hybrid met tabs, notes+tasks CRUD
- [x] Roadmap - Fase-overzicht

### SPARK AI
- [x] Spark Brain - Identiteit (v1 data), Normen & Waarden (11 kernwaarden, 6 normen), Spark Bijbel (11 items + reactie voorbeelden)
- [x] Triggers - 258 triggers in 27 groepen (conversatie, kalender, emotie, admin, systeem)
- [x] Emoties - Volledig emotie detectie systeem (4 tabs)
- [x] Verbanden - Knowledge Graph: 2424 nodes, 11757 edges, interactieve SVG visualisatie, clusters, statistieken

### MODULES
- [x] Trader
- [x] Achievements (13 milestones, XP)
- [x] Leaderboard
- [x] Wallet (UI only - mocked)
- [x] Persoonskaarten - 6 personen, gradatie groepering, relatie tracking
- [x] Integraties (bestandsbrowser + sandbox)

### BEHEER
- [x] Mijn Profiel
- [x] Gebruikers - Gradatie overzicht (7 levels) + personalia editing
- [x] Analytics
- [x] Instellingen (6 tabs - UI only)

## Backlog
- [ ] Backend koppelen aan: Instellingen, Wallet
- [ ] Bank/Geld module
- [ ] Cross-reference met spark-v1-source voor gemiste features

## Datum: 1 april 2026
