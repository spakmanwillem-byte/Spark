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
- [x] Gesprekken - Chat met Snap/NLP engine (Spark AI, Community, Privé)
- [x] Kennisbank - 2424+ kaarten zoeken/bewerken
- [x] Agenda
- [x] Dagboek - Mood tracking
- [x] Notities & Taken - Hybrid met tabs
- [x] Roadmap - Fase-overzicht

### SPARK AI
- [x] Spark Brain - Identiteit, Normen & Waarden, Spark Bijbel (3 tabs)
- [x] Triggers - Trigger woord lijsten beheren
- [x] Emoties - Volledig emotie detectie systeem (4 tabs: Overzicht, Live Detectie, Sub-Emoties, Hoe het werkt)
- [x] Verbanden - Knowledge Graph placeholder

### MODULES
- [x] Trader
- [x] Achievements (13 milestones, XP)
- [x] Leaderboard
- [x] Wallet (UI only - mocked)
- [x] Integraties (bestandsbrowser + sandbox)

### BEHEER
- [x] Mijn Profiel
- [x] Gebruikers
- [x] Analytics
- [x] Instellingen (6 tabs - UI only)

## API Endpoints
- Auth: POST /api/auth/login, GET /api/auth/users, GET /api/auth/me
- Knowledge: GET/PUT/DELETE /api/knowledge/*, GET /api/knowledge/stats
- Files: GET /api/files/tree, GET /api/files/content, POST /api/files/save
- Modules: GET/POST/DELETE /api/modules/*
- Achievements: GET /api/achievements/all, GET /api/achievements/progress/{user_id}
- Chat/Snap: POST /api/chat/message, POST /api/chat/snap, GET /api/chat/lookup/{query}
- Emoties: GET /api/chat/emotions/state, GET /api/chat/emotions/all, GET /api/chat/emotions/learned, POST /api/chat/emotions/detect

## Backlog
- [ ] Backend koppelen aan: Instellingen, Dagboek, Notities, Agenda, Wallet
- [ ] Bank/Geld module (disambiguation: bank zitten vs bank geld)
- [ ] Placeholder verificatie: cross-reference spark-v1-source data

## Datum: 1 april 2026
