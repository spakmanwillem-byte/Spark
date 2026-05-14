# Spark Core 2.0 - PRD

## Origineel Verzoek
Herbouw "Spark AI" als "Spark Core 2.0" - volledig standalone, modulair, zonder cloud of MongoDB. Alle data in lokale JSON bestanden. Dark-themed dashboard.

## Tech Stack
- **Backend**: FastAPI + JSON file storage (geen MongoDB!)
- **Frontend**: React + Tailwind CSS + Lucide icons
- **Auth**: JWT token-based met lokale users.json
- **Externe API**: Bitvavo publieke API (candles, tickers)

## ROAR Token Systeem
- Token = aandeel in Spark Core, dynamische prijs
- User-001 (Willem): 10 ROAR tokens (100% eigendom)
- Totaal gestort: €50.80 op Bitvavo
- Prijs nu DYNAMISCH: Spark Core waarde / circulerende tokens = €5.08
- Alleen hele tokens kopen/verkopen

## Roadkill Shop
- Merch: Roadkill Cap (€17.50), Hoodie (€55), Hoodie+Broek Set (€85)
- ROAR Token als apart product (dynamische prijs)
- Winkelwagen + bestelsysteem + kasboek koppeling

## Kasboeken (4 stuks)
1. **Spark AI** — Bitvavo wallet (€50.80)
2. **Spark Zorgboerderij** — IBAN: NL43 INGB 0006 6836 13
3. **Roadkill Shop** — IBAN: NL43 INGB 0006 6836 13
4. **Mijn Prive** — Per-user kasboek, IBAN uit Mijn Profiel (gekoppeld via user_id)

## Profiel-Kasboek Koppeling
- Mijn Profiel bevat nu IBAN + Bank velden
- IBAN wordt automatisch gekoppeld aan persoonlijk kasboek via user_id
- Wallet (user_id) → Profiel (user_id) → Kasboek (user_id) = verbonden maar gescheiden
- Schaalbaar: elke nieuwe gebruiker krijgt automatisch eigen kasboek

## Voltooide Pagina's
### WORKSPACE
- [x] Dashboard, Gesprekken, Kennisbank, Agenda, Dagboek, Notities & Taken, Roadmap
### SPARK AI
- [x] Spark Brain, Triggers, Emoties, Verbanden
### MODULES
- [x] Trade, Wallet, Winkel (Roadkill Shop), Boekhouding (4 kasboeken)
- [x] Achievements, Leaderboard, Persoonskaarten, Community, Integraties
### BEHEER
- [x] Mijn Profiel (incl. IBAN/bank), Gebruikers, Analytics, Instellingen

## Recente toevoegingen
- [x] Live Bitvavo trading (API keys, P&L met fees, trailing stop)
- [x] 10-Potjes trading systeem met exponentiële volume-scaling
- [x] Trading Context engine (S/R, trend, patronen)
- [x] Donaties/Deposits tracker voor baseline P&L
- [x] Draggable sidebar (reorderable nav items)
- [x] User Admin: Add user modal + Persoonskaarten per user
- [x] Chat Archive systeem (per-user gesprekslogs)
- [x] Knowledge Snap systeem
- [x] Spark Brain Bijbel CRUD endpoints (POST/PUT/DELETE /api/spark/bijbel/{section})
- [x] **Users admin**: Verwijder knop (admin user-001 beschermd) + Reset WW knop (default Welkom01) [20 apr 2026]
- [x] **Homoniem-flow** (v3_012): rejection + confirmation triggers, 'bedoel je een andere X?', auto-creatie variant snap [20 apr 2026]
- [x] **Spark Leraar achievement** (v3_013): +15 XP voor homoniem-disambiguatie via xp_service [20 apr 2026]
- [x] **5W+H veld-bugfix** (v3_011): NLP leest nu ws5+context_5wh, 2398 kaarten leveren rijke context [20 apr 2026]
- [x] **Persoonlijk Archief** (v3_007): 4 categorieën (Bestanden/Foto/Geluiden/Filmpjes), per-user opslag, indexed search, inline previews [11 mei 2026]
- [x] **Storage quota systeem** (v3_014): 1GB basis, koop/cadeau, breakdown chart op dashboard [11 mei 2026]
- [x] **Winkel herindeling** (v3_016): Hoofdtab Merch/Digitaal + sub-tabs Opslag/Token, product_type veld voor boekhouding [11 mei 2026]
- [x] **Dashboard "Mijn Opslag" widget** (v3_017, in_progress): user-gebonden, breakdown met kleurenlegenda [11 mei 2026]
- [x] **Gesprekken in Archief** (v3_018): read-only tab + cascade-delete bij account-verwijderen [11 mei 2026]
- [x] **Gesprekken hiërarchisch** (v3_019): Jaar > Maand > Dag, automatische toekomst-jaar in december [11 mei 2026]
- [x] **Analytics > DATA tab** (v3_021): storage breakdown donut chart met klikbare segmenten [11 mei 2026]
- [x] **Analytics > SYSTEEM tab** (v3_022): echte psutil-data, portable (werkt na zip-uitpakken) [11 mei 2026]
- [x] **Analytics > NETWORK + LAYER** (v3_023): NETWORK live via middleware-tracker, LAYER gemarkeerd in-ontwikkeling [11 mei 2026]
- [x] **Systeem Archief in Instellingen** (v3_024): Bestanden/Foto/Geluiden/Filmpjes/**Dialogen** met 20 tags [11 mei 2026]
- [x] **Storage mapping fix** (v3_026): chat_sessions + accounting + system_archive gecategoriseerd, 0 B ongemapt [11 mei 2026]
- [x] **Knowledge Graph auto-sync** (v3_027): nieuwe snaps (word/sentence/homonym) updaten direct nodes.json + edges.json; shared-tag edges (≤20/node) + sterke homonym_variant edge; Rebuild Graph knop op Verbanden voor volledige herbouw [11 mei 2026]
- [x] **Auto-zin-snap bij chat** (v3_028): nieuwe zin met onbekende woorden → ook hele zin als context-snap (tag context-zin, status draft, is_sentence True) [12 mei 2026]
- [x] **Verwijderknop fix Kennisbank** (v3_029): 2-staps inline bevestiging (geen window.confirm meer) + graph-node mee verwijderen [12 mei 2026]
- [x] **Self-state trigger v1** (v4_001a): analytics-aware respons op "hoe gaat het met jou", drempels 75/50/25 met emotie-staartje [12 mei 2026]
- [x] **Multi-turn 5W+H wedervragen** (v4_001b): bij nieuwe snap stelt Spark gerichte vraag (wat/wanneer/waar/wie/waarom/hoe), antwoord vult ws5, max 2 turns, skip-woorden ondersteund [12 mei 2026]
- [x] **Agenda intent-extractor** (v3_302+v3_303): tijd+activiteit+locatie uit chat → voorstel-flow ja/nee → automatisch agenda-event, conflict-detectie binnen 1u [12 mei 2026]
- [x] **Self-scan commando** (v4_005): admin chat-commando "scan alle knowledge kaarten op onderwerpen" → Spark scant eigen ws5+tags op woorden zonder snap, max 100 per run met tag scan-discovered [12 mei 2026]
- [x] **Compositional Reasoning** (v4_006): onbekend samengesteld woord → split in 2 bekende delen → tags erven, conflict-detectie ("suiker+spin tegenstrijdig — wat is het?") [12 mei 2026]
- [x] **Spontane W-vulling** (v4_007): vrije zin "gisteren bij mijn moeder" → vult ws5.when/where/who van actieve snap (alleen auto-generated, geen overschrijven, terloopse hint) [12 mei 2026]
- [x] **Admin kaart-invul sessie** (v4_008): "ik wil kaarten invullen" → Spark loopt door 50 onbeantwoorde kaarten, vraagt 6 W+H velden per kaart, skip/stop ondersteund, tag sessie-ingevuld toegevoegd [12 mei 2026]
- [x] **NL ws5 keys migratie** (v4_009a): EN keys (who/what/when/where/why/how) → NL (wie/wat/wanneer/waar/waarom/hoe); context_5wh data gemerged in ws5 en context_5wh verwijderd. Backup bewaard. 14.702 velden hernoemd, 86 gemerged [12 mei 2026]
- [x] **Bijdrage-portaal** (v4_009): nieuwe Workspace-tab waar gradatie 1-5 onbeantwoorde kaarten invullen. Fair-share claim (1 per user, 24u TTL, oudste verbeurt). Admin review tab voor goedkeuring. XP +25 per goedgekeurde kaart bij ≥75% gevuld. 4 nieuwe achievements toegevoegd [12 mei 2026]
- [x] **Bijdragen UI-restructure** (v4_009b): Bijdragen verplaatst van eigen sidebar-tab naar 4de sub-tab onder Notities & Taken (Alles/Notities/Taken/Bijdragen). Uitgebreide start-triggers voor chat: "ik wil een kaart invullen", "kenniskaarten invullen" en 20+ varianten [12 mei 2026]
- [x] **Conversationele Diepte** (v4_011): Spark gebruikt nu laag2/3/4 wanneer user vraagt "vertel meer", "leg dieper uit", "ga dieper", "diepere uitleg", "verdieping", "ga verder", "wat nog meer", expliciet "laag 2/3/4" of "tweede/derde/vierde laag". Cycle auto-incrementeert per beurt (laag1 → 2 → 3 → 4), met fallback als gevraagde laag leeg is. Sentence-snap fuzzy match (Optie B): zinnen met 3+ woordoverlap met opgeslagen context-zinnen krijgen voorrang en gebruiken de laag-tekst als conversationele reactie. Hint na elke kennis-match: "Wil je een diepere uitleg?" wanneer laag2/3/4 gevuld is [13 mei 2026]
- [x] **Emotie-tag flex matching** (v4_011a): emotion_service.py herkent nu losse tags `emotie` + `blij/boos/bang/bedroefd/neutraal` op dezelfde kaart (i.p.v. enkel `emotie-blij`). Ook combo-tag `emotie blij` werkt. `neutraal` toegevoegd als 5e emotie. Status-filter verwijderd (draft kaarten tellen mee). Resultaat: 81 'blij' woorden + 68 'neutraal' woorden direct beschikbaar uit bestaande kaarten [13 mei 2026]
- [x] **Spark Bijbel CRUD + Chat integratie** (v4_011b, Fase B): 
  - Backend: SECTION_SCHEMAS uitgebreid met ws5/lagen/tags/sterren/voorbeelden. GET /api/spark/bijbel auto-migreert items zonder id. `kernwaarden` heeft nu ook id_field.
  - Chat: nieuwe `bijbel_lookup_service.py` detecteert 13 self-question intents (voorkeur_blij/boos/bang/bedroefd, missie, visie, doel, functie, filosofie, geloof, behoefte, waarde, norm). Self-ref vereist ('je/jij/jouw/spark'). Antwoord uit kernwaarden/normen/bijbel_items via tag-match, met fallback naar identity.doel of identity.filosofie.
  - Frontend: SparkBrainPage editor-modal met velden naam/beschrijving/belangrijkheid(sterren)/tags/lagen 1-4/ws5/voorbeelden. + knoppen op Kernwaarden, Normen en Bijbel-items. Edit/delete knoppen per item. NormCard expandable [13 mei 2026]
- [x] **Spark Vocab — woordenlijsten** (v4_013a, Fase C deel 1): `/data/personality/spark_vocab.json` met 5 emoties × 4 intenties (begroeting/bedanken/afscheid/reactie) + 5 algemene categorieën (twijfel, enthousiasme, zelfspot, openers, afsluiters), 100 woorden seed. CRUD endpoints op `/api/spark/vocab`. Vocab geïntegreerd in Triggers-pagina als type 'vocab' (paars) met inline add/delete chips — user kan elke lijst zelf personaliseren [13 mei 2026]
- [x] **Statische strings → JSON + alle triggers editable** (v4_013c): Hard-coded fallback-strings uit chat/routes.py (general_fallback, unknown_words_partial, wedervraag_done/skip, agenda_declined, card_session_stopped/empty/denied, scan_denied) verplaatst naar system_fallback.json. Nieuwe `fallback_service.pick(key, default)` helper kiest random uit lijst. Triggers-pagina: ALLE groepen editable (conv/cal/emo/admin/system/vocab) met inline add/delete chips voor triggers EN responses-lijsten. Generieke `/api/triggers/edit/{kind}/{key}/add+DELETE` endpoint [13 mei 2026]
- [x] **Knowledge schema v2.0 + Review-tab** (v4_018a + v4_019): Schema v2.0 stil toegepast op alle 2679 kaarten — `kaart_type` (default `concept`, geldige types: concept/recept/procedure/dialogue/blueprint/emotional_pattern/context) + `metadata.created_at/updated_at/reviewed_at/review_count`. Nieuwe Review-tab in Kennisbank: 5e paarse filter-pill, inline-editable ReviewPanel (oudste/nooit-gereviewde eerst), 4 actie-knoppen (Overslaan / Goedgekeurd-volgende / Opslaan / Opslaan-&-volgende). Backend: /api/knowledge/review/next + /{id}/review endpoints, mark_reviewed + get_next_review service, stats.review_pending, updated_at-stamping bij elke PUT [14 mei 2026]
- [x] **Spark Backup Systeem** (v4_backup_001): Nieuwe module `/app/backend/modules/backup/` + tab "Backup Systeem" in Integraties. 5 endpoints: POST /api/backup/mark-deployed (zet deploy-marker timestamp), GET /api/backup/status (toont marker + gewijzigde files via filesystem mtime), GET /api/backup/download/full (ZIP van alle data+memory), GET /api/backup/download/changes (alleen files gewijzigd sinds marker), POST /api/backup/restore/preview + /restore (merge-only — overschrijft of voegt toe, verwijdert nooit). Scope: /app/backend/data/ + /app/memory/. ZIP bevat manifest met metadata. UI toont status-card, twee download-knoppen, drag-drop restore met preview-classificatie (nieuw/wijzigen/identiek/overgeslagen) en confirm-dialog. Past bij offline-first filosofie — geen externe storage nodig [14 mei 2026]
- [x] **Shadow Observer + lichte zelf-lering** (v4_shadow_001): Stille observator hookt in chat `_save_log`. Schrijft per chat-beurt naar `/data/shadow/events/YYYY-MM-DD.jsonl` (append-only JSONL) + aggregate counters in `stats.json`. Tracked: trigger_type, response_type, begrippen, laag, fallback usage, vocab/bijbel ids, unknown_words count. Auto-detecteert correction-signals ("nee dat klopt niet", "verkeerd antwoord") en confirmations ("precies", "klopt") via regex. Read-only endpoints: `/api/chat/shadow/stats`, `/recent`, `/unused`, `/corrections`, `/reset`. Niet-blokkerend (try/except). Fundament voor v4_016 Analyser en v4_017 Advisor UI [14 mei 2026]
- [ ] **Files-viewer: memory/ folder + meer extensies** (v4_files_fix): /app/memory toegevoegd aan ALLOWED_DIRS, test_credentials.md beschermd. Frontend filter-dropdown uitgebreid met Markdown/HTML/Tekst/YAML opties [14 mei 2026]

## Backlog
- [ ] Spark Brain Bijbel Editor UI (frontend add/edit modals voor kernwaarden/normen/bijbel/doelen)
- [ ] 5 Test accounts voor NLP live-test (moeder, dochter, zusje, zusje's dochter, oud-collega)
- [ ] Baseline scan rapport (triggers, knowledge cards, NLP-woordenschat vóór test)
- [ ] Dashboard verder user-id-gradatie-gebonden maken (v3_017 in progress)
- [ ] Context-laag: zin-snaps met cross-linking (v3_009)
- [ ] 5W+H als conversatie-tool, niet alleen display (v3_010)
- [ ] Intent-laag: chat queries → live data acties (bv. "Heb je winst?" → Bitvavo P&L)
- [ ] Triggers simplificeren (1 trigger = 1 woord, NLP synoniemen)
- [ ] Dag-samenvatting + Trigger-clustering (v3_020)
- [ ] Dialoog-leermodule (v3_025): scan + tag-gebaseerde response-style-library
- [ ] Soundmappings koppelen: Instellingen > Geluid leest uit system_archive/sounds
- [ ] LAYER tab herwerken naar echte module-inventaris
- [ ] BTW-rapportage + sales-report endpoint per product_type
- [ ] Backtesting module, Knowledge Quiz
- [ ] Admin UI: "Cadeau GB" knop in UsersAdmin
- [ ] Event-triggers voor automatisch storage cadeau (100 snaps → 500MB)
- [ ] Homoniem-flow: context-binding < 60 sec voor "ja"-acceptatie
- [ ] Core Protection & Sandbox Split (v4.1 roadmap)

## Datum: 11 mei 2026
