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
- 2026-05-20: **v4_dank_004 — Credits bonus voor herkende users**:
  - Naam in dank.json `namen[]` met spatie (voor+achternaam) wordt gematcht tegen `users.json[].volledige_naam` (case-insensitive)
  - Match + gradatie ≤ 4 → user krijgt:
    - `credits_bonus: true` (flag, idempotent)
    - `credits_multiplier: 1.2` (toekomstige trust-gains × 1.2 via `_trust_carry` accumulator)
    - One-time `trust_score +10` (capped 100)
    - Timestamp `credits_bonus_applied_at`
  - Auto-sync na elke rename/add in credits (via chat of Triggers UI). Spark vermeldt herkenning in chat-bericht.
  - Admin endpoints: `GET /api/admin/credits-bonus` (status) + `POST /api/admin/credits-bonus/sync` (handmatig)
  - `update_activity` gebruikt nu `credits_multiplier` met fractional carry (1.2 = +1 met 0.2 carry, na 5× +6 totaal)
  - Getest: Heidi Spakman (grad 3) toegevoegd → +10 trust, mult 1.2 ✓
- 2026-05-20: **v4_dank_003 — Credits edit via chat**:
  - Spark verstaat in chat (mits scope-keyword `credits|bedank|dank` in zin):
    - **rename**: _"verander Nick naar Nick Teeuwen in de credits"_, _"wijzig Lotus Martens naar Lotus in bedanklijst"_, _"pas Nick aan naar Nick Teeuwen in credits"_
    - **add**: _"voeg Pieter Smith toe aan de credits"_
    - **remove**: _"verwijder Heidi uit de credits"_
  - **Disambiguation**: als naam vaker voorkomt (bv. 2× Nick), vraagt Spark verduidelijking ipv blind eerste pakken
  - Regex met negatieve lookahead `_NW` filtert stopwoorden (naar/in/tot/de/het/credits/toe/erbij) zodat namen schoon worden geparsed
  - Geïntegreerd in `chat/routes.py` vóór credits-info-intent (anders zou "credits" winnen)
- 2026-05-20: **v4_dank_002 — Credits in Triggers UI + Lotus Martens**:
  - Lotus Martens toegevoegd achteraan voornamen-lijst (vóór "iedereen die ik vergeet")
  - 2 nieuwe groepen in Spark AI → Triggers (filter: Conversatie):
    - `credits_namen` — Credits — Voornamen (7 items, met X-knop per naam + toevoeg-veld)
    - `credits_extra` — Credits — Extra dank (community e.d.)
  - Backend: kind `credits` toegevoegd aan `_KIND_TO_FILE` → maps naar `dank.json`. Edit-endpoints `POST /api/triggers/edit/credits/{namen|extra_dank}/add` en `DELETE /api/triggers/edit/credits/{key}/triggers/{word}` werken
  - Sparks credits-bericht toont nu: "Maurice, Nick ×2, Heidi, Ron, Arent en Lotus Martens"
- 2026-05-20: **v4_dank_001 — Sparks bedank-uiting**:
  - `/data/system/dank.json` met voornamen (Maurice, Nick × 2, Heidi, Ron, Arent), de community, "iedereen die vergeten wordt"
  - `dank_service.py` met 2 detectors:
    - `detect_credits_intent` ("credits", "wie heeft jou gemaakt", "aan wie ben je dankbaar") → **altijd** bedanken, credits_count++
    - `detect_free_choice_intent` ("Spark wat zou jij willen doen?", "kies zelf") → **1× bedanken** (first_choice_done flag), daarna valt door naar `handle_suggest` (agenda/roadmap)
  - Geïntegreerd vóór bestaande suggest-intent in `chat/routes.py`
  - Format: "Maurice, Nick ×2, Heidi, Ron en Arent — bedankt" + extra dank voor community
- 2026-05-20: **v4_profile_revamp_001 — Mijn Profiel volledig herzien**: 5 tabs in plaats van 3 (Algemeen / Achtergrond / Persoonlijkheid / Gesprekken / Avatar). Elke tab heeft eigen content (was eerst alles op één pagina).
  - **Algemeen**: avatar-preview, leeftijd/beroep/locatie/opleiding, geslacht, sociale media
  - **Achtergrond**: NAW + contact + adres + noodcontact + bank (formele identiteit)
  - **Persoonlijkheid**: 6 sliders + doelen/behoeften/zintuigen/mediagedrag + Pijn/Angst sectie (read-only, Spark observeert)
  - **Gesprekken**: eigen chat-historie gesorteerd jaar→maand→dag (collapsible tree), system-prompts uitgefilterd. Endpoint `GET /api/profile/chat-history/{user_id}` (649 gesprekken Willem zichtbaar)
  - **Avatar**: huidige avatar + galerij-kiezer + eigen portret-upload
- 2026-05-20: **v4_avatar_001 — Avatar systeem**: 
  - Backend module `/api/avatar/*` (gallery + user portrait + select)
  - Pillow resize max 512×512 JPEG quality 85 (storage-vriendelijk: 35KB voor 512×512)
  - System-galerij `/data/system/avatars/` (admin-only beheer, alle users kiezen)
  - User-portret `/data/users/{id}/avatar.jpg` (scope=profile, niet in algemeen archief)
  - `users.json[id].avatar = "gallery:{id}" | "user" | null` voor selectie
  - Admin sectie in **Beheer → Instellingen → Beeld → Avatar Galerij** (upload titel+tags, delete, SEED-badge)
  - Seed: Roadkill-logo gekopieerd uit user-001 archive naar `/system/avatars/roadkill-logo.jpg`

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
- 2026-05-20: **v4_route_guard_001 — Admin routes guard** (bug #5): non-admins (gradatie > 2) die op `/admin/users`, `/admin/analytics` of `/admin/settings` URL landen worden automatisch teruggestuurd naar dashboard. Voorkomt witscherm/leeg-pagina na gradatie-wijziging.
- 2026-05-20: **v4_grad_titel_001 — Warme gradatie-titels**: gradaties hernoemd van klinisch ("Communityleden", "Klanten", "Onbekenden") naar warm ("Vriend", "Community Plus", "Community Member", "Bekend", "Leert graag kennen"). Backend `/login` retourneert `gradatie_titel` veld. Sidebar/dashboard tonen warme titel ipv "Gradatie X" (nummer alleen voor admins zichtbaar).
- 2026-05-20: **vocab-growth seed**: 15 natuurlijke woorden toegevoegd uit kennisbank-kandidaten (mensen, communicatie, gedrag, natuur, leven, taal, kennis, tijd, energie, iemand, iedereen, gesprekken, informatie, dieren, ontwikkeling).
- 2026-05-20: **Roadmap sync**: 20 items toegevoegd aan v4.0 roadmap (11 recent-done + 9 nieuwe planned). v4.0 progress: 75% (62/83 done).
- 2026-05-20: **v4_storage_cache_001 — In-memory file cache** (gratis prestatie-upgrade): mtime-based cache in `storage.py` voor files >50KB. Knowledge_base (8MB) + graph nodes (1.2MB) + edges (7MB) worden nu maar 1× geparsd tot file mtime verandert. Cache wordt automatisch geïnvalideerd bij `save_json` of externe writes. **Gemeten winst**: vocab-endpoint 24% sneller, graph-stats 30% sneller, orphan-check 53% sneller. Diagnostics via `GET /api/admin/storage-cache` + `POST /api/admin/storage-cache/clear`. Backup-restore clear cache automatisch.
- 2026-05-20: **v4_storage_cache_002 — Cache warmup bij startup**: backend laadt KB + graph + vocab + users alvast in geheugen tijdens `@startup` (138ms, 5 files, 15.76 MB). Eerste user-request is meteen warm — geen cold-start latency meer. Log toont `🔥 Cache warmup: 5/5 files in Xms`.
- 2026-05-20: **Roadmap sync 76%**: v4.0 nu 65/86 done. Toegevoegd: warmgradatie-titels, upgrade-regels, storage cache, cache warmup.
- 2026-05-20: **v4_perf_widget_001 — Performance Card op admin dashboard** (admin-only): live cache stats (MB in geheugen, # files, file-namen + grootte) + "Cache leegmaken" knop voor debug. Fetcht `/api/admin/storage-cache`. Zichtbaar getest: 16.34 MB cached, 6 files. Non-admin (gradatie>2) ziet kaartje niet.
- 2026-05-20: **v4_wallet_cleanup_001 — Wallet test-data weggehaald**: €40 fake balance + 4 fake transactions ("genesis-deposit", "Bestelling test") verwijderd. ROAR-tokens (10) en wallet structuur behouden. Credits + activity_score op 0 (waren ook test).
- 2026-05-20: **v4_grad_growth_002 — Upgrade-pad regels gedocumenteerd**:
  - **7 → 6**: profiel-completeness ≥ 80% (10 velden: volledige naam, geboortedatum, plaats, straat, postcode, land, telefoon, nationaliteit, geslacht, noodcontact). Spark "kent" basis-info.
  - **6 → 5**: gedrag-based (oude regel, onveranderd) — 15 gesprekken + 30 dagen + trust ≥ 60
  - **5 → 4**: Roarr-token bezit ≥ 1 (wacht op v4_token_potje_001 mechaniek)
  - **4 → 3**: admin-only (jouw persoonlijke kring). Spark mag suggereren via `suggest_gradatie_promotion()` bij ≥ 50 gesprekken + trust ≥ 80
  - **3 → 2 → 1**: admin-only, geen auto-groei
  - Trust-score blijft basis voor "betrouwbaarheid + gedragsstabiliteit" zoals user beschrijft
  - 5 unit-tests groen (zie auth/service.py `check_auto_gradatie_growth`)

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
