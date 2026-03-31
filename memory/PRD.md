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
- [x] Triggers
- [x] Emoties
- [x] Verbanden
- [ ] Spark Brain (placeholder)

### MODULES
- [x] Trader
- [x] Achievements (13 milestones, XP)
- [x] Leaderboard
- [x] Wallet
- [x] Integraties (bestandsbrowser + sandbox)

### BEHEER
- [x] Mijn Profiel
- [x] Gebruikers
- [x] Analytics
- [x] Instellingen (6 tabs)

## API Endpoints
- Auth: POST /api/auth/login, GET /api/auth/users, GET /api/auth/me
- Knowledge: GET/PUT/DELETE /api/knowledge/*, GET /api/knowledge/stats
- Files: GET /api/files/tree, GET /api/files/content, POST /api/files/save
- Modules: GET/POST/DELETE /api/modules/*
- Achievements: GET /api/achievements/all, GET /api/achievements/progress/{user_id}
- **Chat/Snap**: POST /api/chat/message, POST /api/chat/snap, GET /api/chat/lookup/{query}

## Backlog
- [ ] Spark Brain pagina invullen
- [ ] Backend koppelen aan: Instellingen, Dagboek, Notities, Agenda
- [ ] Wallet koppelen aan oude data
- [ ] Disambiguation (bank zitten vs bank geld)

## Datum: 31 maart 2026
