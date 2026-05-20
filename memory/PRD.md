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
- 2026-05-15: Trader keepalive + Snelhandel Quick Buy met Potjes auto-pickup
- 2026-05-15: Dagboek tree-view (Year→Month→Day)
- 2026-05-15: Spark self-aware welcome via system:login event
- 2026-05-16: Dashboard "Gesprekken" card live
- 2026-05-16: Verbanden Statistieken top 20 + dynamic bars
- 2026-05-16: **v4_bugs_001/002** — Bug-melder MVP + status-update PMs
- 2026-05-16: **v4_notities_tree_001** — Notities/Taken tree-view
- 2026-05-16: **v4_dq_a** — Code Quality: circular imports + secrets.choice
- 2026-05-16: **v4_016a** — Analyser unused-vocab (read-only)
- 2026-05-16: **v4_kb_create_001** — Kennisbank "Nieuwe kaart" tab + dup-check
- 2026-05-18: **v4_identity_001** — Identity-Intent laag (Spark over zichzelf)
- 2026-05-19: **v4_logout_001** — logout clear_state
- 2026-05-19: **v4_5w_consolidate_001** — bulk card_session flow deprecated
- 2026-05-19: **v4_xp_fix_001** — achievements via xp_service (optellend)
- 2026-05-19: **v4_actions_001** — Action-Intent laag: STT + Ambient via chat
- 2026-05-19: **v4_time_001** — "Hoe laat is het?"
- 2026-05-19: **v4_rel_001** — Relation Extraction (22 types)
- 2026-05-19: **v4_settings_001** — Settings architectuur: system.json + user_overrides, gradatie-gating, 19 keys
- 2026-05-19: **v4_voice_002** — Voice flow upgrade: auto-start mic op (stt aan), 2s stilte-detectie + auto-send (configurable `stt_silence_sec`), TTS-glow indicator, continue voice-loop na Spark antwoord
- 2026-05-19: **v4_vocab_growth_001** — Vocab kandidaten uit kennisbank + approve-flow (`/api/spark/vocab/approve-growth` → algemeen.uit_kennisbank), tags-zonder-kaart endpoint, "Groeien" tab in Spark Brain
- 2026-05-19: **v4_data_recovery_001** — Atomic save_json (tmp+rename), graph orphan-check + orphan-recover endpoints. 74 weeskaarten hersteld uit graph→KB (waaronder 2 Arent-kaarten die "kwijt" leken)
- 2026-05-19: **v4_agenda_announce_001** — Spark vermeldt aankomende afspraak (≤60min) in welcome message. Glow ack-flow: klik op nav/tab → POST /api/urgent/acknowledge → glow uit. Ack TTL = event_dt+10min.
- 2026-05-19: **v4_rel_002** — relation_extraction sync naar persons cards: nieuwe relaties uit chat schrijven nu OOK in `/data/persons/{user_id}.json` (cards UI). Bestaande relations gemigreerd: Arent Pelster (jeugdvriend), Willie Bakker (vader, overleden), Heidi Spakman (moeder), Maurice (vriend i.p.v. collega), Maaike Spakman (zus). Fix maakt sneller zichtbaar in Persoonkaarten UI.
- 2026-05-19: **v4_notes_002 — user-bound notes/tasks**: `/api/notes/*` heeft nu verplicht `user_id` param + filtert op owner. 403 bij andermans notitie. Bestaande 3 notities gemigreerd naar user-001. Vóór deze fix waren alle notes 1 gedeelde pool voor alle users.
- 2026-05-19: **v4_dashboard_grad_001 — Dashboard per gradatie**: 4 widgets (Triggers, Systeem Status, Gebruikers, Shadow Observer) + 2 top-stats (Triggers/Users badges) nu alleen zichtbaar voor gradatie ≤ 2. Lower gradaties zien een gestripte, persoonlijke dashboard.
- 2026-05-20: **v4_gradatie_visibility_002 — Tab-finetune per gradatie** (12 bug-fixes uit prod):
  - Grad 2: -Voice (wel Gebruikers tab — `isAdmin` uitgebreid naar gradatie ≤ 2)
  - Grad 3: -Voice (zelfde als 4)
  - Grad 4: -Voice
  - Grad 5: -Voice -Trade -Boekhouding
  - Grad 6: + -Dagboek
  - Grad 7: + -Agenda -Archief
  - Visueel getest met 4 bestaande users (Harry/Smith/Heidi/Madelief): alle 12 bugs ✓ opgelost

## In progress / backlog
### P0 / Open follow-ups
- Gradatie 2 splitsen (fam ↔ admin) → fam ziet géén Bugs-tab

### P1
- v4_dq_b: Split big components (TraderPage, UsersAdminPage, MainLayout)
- v4_014: Guard Layer (priority resolver, conflict logger, fallback hierarchy)
- v4_017: Advisor UI "Spark Inzichten" page (approve/reject analyser suggestions)
- **v4_accounting_002 — Boekhouding per user**: refactor `personal_willem` → `personal_{user_id}`. Auto-create privé-kasboek bij eerste login. Definieer rol-toegang per kasboek (system/project/business). Scheiding handhaven: Boekhouding (admin/transacties) vs Wallet (intern Spark-tegoed) vs Bank-koppeling (IBAN per user, future feature).
- **v4_kb_split_001 — KB-leak naar persons**: detector voor "X is mijn Y" zinnen in KB → migrate naar persons cards. Splitter voor double-meaning cards (Bakker = achternaam + beroep).
- **v4_snap_dedupe_001 — KB duplicates**: snap_service moet lowercase dedup doen (10 oude duplicates: vergrootglas, balk, klem, etc).

### P2
- Enkelvoud/meervoud schema voor begrippen (woord-normalisatie)
- v4_020: Chain-anchor (hide chain-of-thought to debug payload)
- v4_013b: Response Composer (Wat + Hoe)

### P3
- v4_018: Export/Import personality packs
- v6_avatar_001: Avatar-tab + verhaal-modus + ziel-verslonden mechaniek

## Key files (recent)
- `/app/backend/modules/settings/routes.py` — Settings module
- `/app/backend/modules/insights/routes.py` — vocab-from-knowledge + tags-without-card
- `/app/backend/modules/graph/__init__.py` — orphan-check + orphan-recover
- `/app/backend/modules/urgent/routes.py` — acknowledge + upcoming-spoken
- `/app/backend/modules/spark/__init__.py` — vocab/approve-growth
- `/app/backend/modules/core/storage.py` — atomic save (tmp+rename)
- `/app/backend/modules/chat/routes.py` — welcome met agenda-announce
- `/app/frontend/src/components/admin/InstellingenPage.js` — real settings API
- `/app/frontend/src/components/workspace/GesprekkenPage.js` — voice auto-start, silence detect, TTS-glow, agenda ack
- `/app/frontend/src/components/spark/SparkBrainPage.js` — "Groeien" tab (vocab/tags/orphans)
- `/app/frontend/src/components/layout/MainLayout.js` — sidebar nav ack flow

## Tech stack
React 18, FastAPI, JSON files, Bitvavo API (trade), OpenAI TTS/STT via emergentintegrations
