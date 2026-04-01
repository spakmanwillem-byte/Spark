# Spark Core 2.0 - PRD

## Origineel Verzoek
Herbouw "Spark AI" als "Spark Core 2.0" - volledig standalone, modulair, zonder cloud of MongoDB. Alle data in lokale JSON bestanden. Dark-themed dashboard.

## Tech Stack
- **Backend**: FastAPI + JSON file storage (geen MongoDB!)
- **Frontend**: React + Tailwind CSS + Lucide icons
- **Auth**: JWT token-based met lokale users.json
- **Storage**: `/app/backend/data/*.json`
- **NLP**: Standalone Snap engine (geen spaCy/Levenshtein)

## Voltooide Pagina's

### WORKSPACE
- [x] Dashboard - Live data kaarten
- [x] Gesprekken - Chat met Snap/NLP engine
- [x] Kennisbank - 2424+ kaarten zoeken/bewerken
- [x] Agenda - Week kalender + events CRUD (API gekoppeld)
- [x] Dagboek - Mood tracking + entries CRUD (API gekoppeld)
- [x] Notities & Taken - Hybrid met tabs, notes+tasks CRUD (API gekoppeld)
- [x] Roadmap - Fase-overzicht

### SPARK AI
- [x] Spark Brain - Identiteit, Normen & Waarden, Spark Bijbel (echte v1 data via /api/spark/full)
- [x] Triggers - 258 triggers in 27 groepen geconsolideerd (API gekoppeld)
- [x] Emoties - Volledig emotie detectie systeem (4 tabs, API gekoppeld)
- [x] Verbanden - Knowledge Graph placeholder

### MODULES
- [x] Trader
- [x] Achievements (13 milestones, XP)
- [x] Leaderboard
- [x] Wallet (UI only - mocked)
- [x] Persoonskaarten - 6 personen, gradatie groepering, relatie tracking (API gekoppeld)
- [x] Integraties (bestandsbrowser + sandbox)

### BEHEER
- [x] Mijn Profiel
- [x] Gebruikers - Met gradatie overzicht (7 levels) + personalia editing (naam, volledige_naam, rol, gradatie met rechten)
- [x] Analytics
- [x] Instellingen (6 tabs - UI only)

## Alle API Endpoints
- Auth: POST /api/auth/login, GET /api/auth/users, GET /api/auth/me, PUT /api/auth/users/{id}, GET /api/auth/gradaties
- Knowledge: GET/PUT/DELETE /api/knowledge/*
- Files: GET /api/files/tree, GET /api/files/content, POST /api/files/save
- Achievements: GET /api/achievements/*
- Chat/Snap: POST /api/chat/message, POST /api/chat/snap
- Emoties: GET /api/chat/emotions/state|all|learned, POST /api/chat/emotions/detect
- Agenda: GET/POST/PUT/DELETE /api/agenda/events/{user_id}
- Dagboek: GET/POST/PUT/DELETE /api/dagboek/entries/{user_id}
- Notes: GET/POST/PUT/DELETE /api/notes/*, /api/notes/tasks/*
- Triggers: GET /api/triggers/all, GET /api/triggers/by-type/{type}
- Persons: GET/POST/PUT/DELETE /api/persons/cards/{user_id}, GET /api/persons/relationships/{user_id}
- Spark Core: GET /api/spark/identity, GET /api/spark/bijbel, GET /api/spark/full

## Backlog
- [ ] Backend koppelen aan: Instellingen, Wallet
- [ ] Bank/Geld module
- [ ] Placeholder verificatie: cross-reference spark-v1-source
- [ ] Verbanden pagina (Knowledge Graph)

## Datum: 1 april 2026
