# Spark Core 2.0 - PRD

## Origineel Verzoek
Herbouw "Spark AI" als "Spark Core 2.0" - volledig standalone, modulair, zonder cloud of MongoDB. Alle data in lokale JSON bestanden. Dark-themed dashboard met expandable sidebar, draggable cards, en specifieke secties.

## Tech Stack
- **Backend**: FastAPI + JSON file storage (geen MongoDB!)
- **Frontend**: React + Tailwind CSS + Lucide icons
- **Auth**: JWT token-based met lokale users.json
- **Storage**: `/app/backend/data/*.json`

## Architectuur
```
/app/backend/
  ├── modules/auth/     (login, users, gradaties)
  ├── modules/knowledge/ (kennisbank CRUD + zoeken)
  ├── modules/files/    (bestandsbrowser + module sandbox)
  ├── modules/achievements/ (XP + milestone tracking)
  └── data/             (alle JSON bestanden)

/app/frontend/src/
  ├── components/layout/     (MainLayout met sidebar)
  ├── components/dashboard/  (Dashboard overzicht)
  ├── components/workspace/  (Gesprekken, Kennisbank, Agenda)
  ├── components/spark/      (Emoties, Verbanden, Triggers)
  ├── components/modules/    (Trader, Achievements, Integraties)
  ├── components/admin/      (Analytics, UsersAdmin, Instellingen)
  └── components/profile/    (UserProfile)
```

## Voltooide Pagina's

### WORKSPACE
- [x] Dashboard - Overzicht met live data kaarten (kennisbank stats, triggers, systeem status, verbanden graph, users, bestanden, agenda, gesprekken)
- [x] Gesprekken - Chat met tabs (Spark AI, Community, Privé) in top banner
- [x] Kennisbank - Zoekengine voor 2424+ knowledge cards met filter/sort/edit/delete + detail modal
- [x] Agenda - Kalender met afspraken

### SPARK AI
- [x] Spark Brain - Knowledge graph placeholder
- [x] Triggers - Trigger woorden beheer
- [x] Emoties - Emotie analyse systeem
- [x] Verbanden - Knowledge graph visualisatie

### MODULES
- [x] Trader - Trading interface
- [x] Achievements - XP & milestones (9/13 unlocked, 26.350 XP, live data)
- [x] Integraties - Bestandsbrowser (105 bestanden) + Module Sandbox (aanmaken/testen/integreren)
- [ ] Wallet - Placeholder
- [ ] Community - Placeholder

### BEHEER
- [x] Mijn Profiel - User profiel pagina
- [x] Gebruikers - Admin users beheer
- [x] Analytics - Systeem/Network/Layer tabs
- [x] Instellingen - 6 tabs: Algemeen, Beeld, Geluid, Integraties, Features, Tips & Hulp (frontend-only, backend later)

## API Endpoints
- `POST /api/auth/login` - Inloggen
- `GET /api/auth/users` - Alle gebruikers
- `GET /api/auth/me` - Huidige user
- `GET /api/knowledge/all` - Kennisbank zoeken (search, filter, sort, paginatie)
- `GET /api/knowledge/stats` - Kennisbank statistieken
- `GET/PUT/DELETE /api/knowledge/{id}` - Kaart CRUD
- `GET /api/files/tree` - Bestandsboom
- `GET /api/files/content` - Bestand lezen
- `POST /api/files/save` - Bestand opslaan met syntax validatie
- `GET /api/modules/list` - Sandbox modules
- `POST /api/modules/create` - Module aanmaken
- `POST /api/modules/test` - Module testen
- `GET /api/achievements/all` - Alle achievements
- `GET /api/achievements/progress/{user_id}` - User voortgang + retroactive unlock

## Backlog
- [ ] Backend API koppelen aan Instellingen pagina (opslaan/laden settings.json)
- [ ] Wallet pagina invullen
- [ ] Community pagina invullen
- [ ] Spark Brain pagina invullen
- [ ] Backend API wire-up voor gemockte UI's (Trader, Analytics, etc.)

## Datum: 31 maart 2026
