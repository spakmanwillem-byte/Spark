# Spark Core 2.0 — PRD

## Original problem statement
Modular, offline-first personal legacy system. Memory & knowledge machine. STRICT requirement: data lives in local JSON files (NO MongoDB).

## User language
Dutch (always respond in Dutch).

## Architecture
- React 18 + FastAPI + JSON file storage at `/app/backend/data/`
- 5-layer AI: NLP heuristics, smart_intents, snap_service, shadow observer, fallback
- Gradation-based visibility (1=eigenaar, 2=fam/admin, 3=vrienden, 4=collega's, 5-7=community)

## Completed (recent)
- 2026-05-13: Spark Vocab editable via Triggers page (v4_013a)
- 2026-05-13: Static strings → JSON, all trigger lists editable (v4_013c)
- 2026-05-14: Knowledge schema 2.0 (kaart_type + metadata)
- 2026-05-15: Backup/Restore ZIP (export changes/full + dry-run preview)
- 2026-05-15: Shadow Observer (v4_015) + dashboard widget
- 2026-05-15: Chat session storage + Recap intent + Glow notifications
- 2026-05-15: Smart Chat Intents (Agenda, topic overview, roadmap check) + 5W+H consent
- 2026-05-15: Trader keepalive + Snelhandel Quick Buy with Potjes auto-pickup
- 2026-05-15: Removed obsolete "Te Herzien" tab
- 2026-05-15: Dagboek tree-view (Year→Month→Day)
- 2026-05-15: Spark self-aware welcome via system:login event
- 2026-05-16: Dashboard "Gesprekken" card connected to live data (Spark log + Community + Privé contacts)
- 2026-05-16: Verbanden Statistieken — backend top 10 → top 20, frontend bars scale dynamically (max relative)
- 2026-05-16: **Bug-melder MVP (v4_bugs_001)** — anyone can report bugs via "Bug melden" button in Notities; admins (gradatie ≤ 2) see "Bugs" tab; auto private confirmation message from Spark AI to reporter. Open follow-up: split gradatie 2 into fam vs admin.
- 2026-05-16: **v4_bugs_002** — Enriched bug confirmation PM (cites description, prominent ref, when+where) + new status-update PM on every admin status change with optional note.
- 2026-05-16: **v4_notities_tree_001** — Notities & Taken tree-view (Year→Month→Day), auto-opens today, same as Dagboek/Archief.
- 2026-05-16: **v4_dq_a** — Code Quality fixes: circular imports resolved (trade/routes uses relative imports, graph/sync_service uses sys.modules), `random.choice` → `secrets.choice` across chat/bots/contributions modules.
- 2026-05-16: **v4_016a — Analyser laag 1 (unused-vocab)** — Read-only endpoint `GET /api/spark/insights/unused-vocab` analyseert shadow events en geeft kandidaat-woorden terug die vaak voorkwamen maar niet in vocab/triggers/knowledge zitten. Stopwoorden + tijd-tokens uitgefilterd. Geen wijzigingen, alleen suggesties.

## In progress / backlog
### P0 / Open follow-ups
- Gradatie 2 splitsen (fam ↔ admin) → fam ziet géén Bugs-tab

### P1
- Missing React hook deps audit (already lint-clean on AuthContext.js + GesprekkenPage.js)
- v4_dq_b: Split big components (TraderPage, UsersAdminPage, MainLayout)
- v4_014: Guard Layer (priority resolver, conflict logger, fallback hierarchy)
- v4_016: Analyser `/api/spark/insights` (shadow events analysis: unused vocab, trigger overlap, recurring unknown words)
- v4_017: Advisor UI "Spark Inzichten" page (approve/reject analyser suggestions)

### P2
- v4_020: Chain-anchor (hide chain-of-thought to debug payload)
- v4_013b: Response Composer (Wat + Hoe)

### P3
- v4_018: Export/Import personality packs

## Key files
- `/app/backend/modules/bugs/routes.py` — NEW bug-melder module
- `/app/backend/server.py` — Module 23 mount
- `/app/frontend/src/components/workspace/NotitiesPage.js` — Bug-melden knop + Bugs tab
- `/app/frontend/src/components/dashboard/DashboardPage.js` — live Gesprekken card
- `/app/frontend/src/components/spark/VerbandenPage.js` — top 20 + dynamic bars
- `/app/backend/data/notes/notes.json` — bugmelder notitie geupdated (MVP done)
- `/app/backend/data/system/roadmap.json` — v4_bugs_001 entry toegevoegd

## Tech stack
React 18, FastAPI, JSON files, Bitvavo API (trade), OpenAI TTS/STT via emergentintegrations
