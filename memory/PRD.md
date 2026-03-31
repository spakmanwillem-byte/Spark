# Spark Core 2.0 - PRD (Product Requirements Document)

## Originele Probleemstelling
Herbouw Spark AI met modulaire architectuur om API mismatches tussen backend en frontend te voorkomen. Gelaagde opbouw: elke module volledig afmaken (backend + frontend) voordat naar volgende module wordt gegaan.

## Architectuur Principes
- **Modulair**: Elke module is zelfstandig
- **Geen afhankelijkheden**: Modules lopen niet door elkaar
- **API Contract**: Backend API volledig AF → dan pas frontend
- **JSON Storage**: Geen MongoDB, bestaande data behouden

## Gebruikerspersona's
1. **Beheerder (Gradatie 1)** - Volledige toegang, masterkey
2. **Familie (Gradatie 2)** - Familiegerelateerde functies
3. **Goede vrienden (Gradatie 3)** - Community + onderhoud
4. **Externe collega's (Gradatie 4)** - Community Plus
5. **Communityleden (Gradatie 5)** - Basis functies
6. **Klanten (Gradatie 6)** - Klantspecifieke functies
7. **Onbekenden (Gradatie 7)** - Alleen registratie

## Kernvereisten

### Stap 0: Core Setup ✅
- [x] server.py (entrypoint)
- [x] config/settings.py
- [x] modules/core/storage.py (JSON layer)

### Stap 1: Auth Module ✅
- [x] Backend: modules/auth/service.py
- [x] Backend: modules/auth/routes.py
- [x] Backend: modules/auth/models.py
- [x] Frontend: api/index.js
- [x] Frontend: context/AuthContext.js
- [x] Frontend: components/auth/LoginForm.js
- [x] Frontend: components/dashboard/Dashboard.js
- [x] Sessie management (heartbeat)
- [x] Gradatie systeem

## Geïmplementeerd

### 31 maart 2026
- **Spark Core 2.0 Foundation**
  - Nieuwe modulaire backend architectuur
  - JSON storage layer (thread-safe)
  - Auth module volledig (backend + frontend)
  - Dark theme UI met Spark branding
  - Login/logout flow
  - Dashboard met profiel, modules, statistieken
  - Gradatie systeem (7 niveaus)
  - Session management met heartbeat
  - 100% test coverage

## Backlog (Geprioriteerd)

### P0 - Kritiek (Volgende sessie)
- [ ] Knowledge Module (backend)
- [ ] Knowledge Module (frontend)

### P1 - Hoog
- [ ] Chat/Spark Brain Module (backend)
- [ ] Chat/Spark Brain Module (frontend)
- [ ] Conversation history

### P2 - Medium
- [ ] Admin Panel
- [ ] User Management UI
- [ ] Settings Module
- [ ] Notes Module

### P3 - Laag
- [ ] Achievements Module
- [ ] Wallet Module
- [ ] Community Module
- [ ] Game Module

## Volgende Taken
1. Knowledge Module Backend
   - /api/knowledge routes
   - CRUD voor knowledge entries
   - 3-lagen systeem (laag1, laag2, laag3)
   - Tags en metadata

2. Knowledge Module Frontend
   - Knowledge browser component
   - Search functionaliteit
   - Entry detail view

## Tech Stack
- **Backend**: FastAPI, Python 3.x
- **Frontend**: React 19, Tailwind CSS
- **Storage**: JSON files (geen MongoDB)
- **Auth**: Custom JWT-less session (sleutelwoord based)
