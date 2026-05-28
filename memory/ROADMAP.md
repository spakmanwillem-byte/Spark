# Spark Core 2.0 — Engineering Practices & Backlog

> **Zie ook**: `MISSION.md` voor missie/visie/identiteit/privacy (DNA-laag).

## 🟢 Redeploy-ready check — 2026-05-29 (pre-storting €98.40)

**Status**: Stabiel. Geen blockers. Wacht op €98.40 storting Willem zodat Spark potjes-commitment 100% gedekt is door Bitvavo.

**Rekening (kloppend na storting)**:
- Spark potjes commitment: 15 × €10 = **€149.92**
- Bitvavo live wallet: **€122.74** (huidig)
- Open commitment: **€100.00** (= 10 trade-slots zonder `linked_bitvavo` flag)
- Willem privé saldo (Boekhouding): **€1.60**
- **Storting morgen: €98.40** → €100 commitment volledig gedekt (€1.60 privé + €98.40 = €100)

**Wat live werkt (smoke-checked, mag op productie)**:
- Bitvavo trading LIVE (3 bots: Spark 60m, Gijs 15m)
- ROAR economy v6 (gift-fase, 0% BTW, 12 tokens circulating: Willem 10 + Gijs 2)
- Boekhouding 4 entiteiten met BTW-summary + reconcile + retroactief fix-endpoint
- Winkelstraat hub met owner-shop-isolation (`shops/{shop_id}/products.json`)
- 8 capabilities (W-vraag, profile-lookup, relay, dashboard saldo, verbal deposit, etc.)
- Synapse auto-documenter (90 containers, 418 endpoints, 59 blueprints)
- KB v2 hooks-laag (5 hooks live: vocab/tell-layer/verbanden/dnd-link/voice-snippet)
- 12 capabilities executable in chat-router

**Open na redeploy (P0, niet blocker voor deploy)**:
- [ ] 6 Boekhouding-hooks centraliseren (token-buy / coin-buy / sell-back / shop-sale / deposit / trader-result → `/api/accounting/transactions`)
- [ ] Legacy `spark_kasboek.json` schrijfpaden uitfaseren (alleen-lezen + migratie)

**Open daarna (P1+)** — zie secties hieronder ongewijzigd.


## 🧠 Spark's brein — wat er AL is (v5-status, 2026-05-23)

> Deze sectie bestaat omdat de backlog hieronder anders de indruk wekt dat Spark
> nog hersenloos is. Hij is dat niet. Hij denkt al laagsgewijs mee — onderstaande
> modules zijn live en in productie:

### 🎯 5-laags AI-pipeline (in volgorde bij elk chat-bericht)
1. **Safe-word laag** (`chat/routes.py`) — universeel `stop`/`pauze`/`klaar` wist alle pending state, vóór elke andere verwerking.
2. **Identity & Action intents** (`identity_intent_service.py`, `action_intents_service.py`) — "wie ben je?", "wat kan je?", "verwijder mijn account" e.d. eerst.
3. **Smart intents heuristic** (`smart_intents_service.py`) — help / suggest / community-recap / dnd-help / legal / time / credits + Boekhouder/Madelief/Mr Smith barks.
4. **Snap & NLP service** (`snap_service.py`) — meerlaags KB-lookup met homoniem-disambiguatie, compositional reasoning (`compositional_service.py`), stem-fallback en auto-zin-snap.
5. **Fallback service** (`fallback_service.py` + `#DeWillem` graceful) — als er geen directe hit is, kiest Spark een buurkaart uit de KB v2 lade en stelt voor het concept apart te leren in plaats van "weet ik niet" te zeggen.

### 🔭 Observability & shadow-leren
- **`@traced` decorator** (`modules/core/spark_logger.py`) — pre/post/error logs met `duration_ms` per gedecoreerde route, JSON Lines per module, 28-dagen retentie.
- **Shadow observer** (`chat/shadow_observer.py`) — registreert elk chat-event + correction-examples voor toekomstige zelf-tuning.
- **Behavior tracker** (`modules/behavior_tracker.py`) — telt gedragingen (`help_msg`, `kb_create`, `lie_detected`, `used_safeword`, etc.) — voedt het D&D aura-systeem.

### 🧩 Specialized services (allemaal live, in chat-flow hooked)
- **`emotion_service.py`** — emotie-detectie per bericht (input voor Madelief barks).
- **`time_intent_service.py`** + `user_time_service.py` — "hoe laat is het?" met tijdzone-resolutie per user.
- **`agenda_intent_service.py`** — natuurlijke afspraken parsen ("vrijdag 14:00 lunch met Tineke").
- **`wedervraag_service.py`** — als info ontbreekt, vraagt Spark gericht door (5W+H flow).
- **`scan_service.py`** + `spontaneous_w_service.py` — woorden in lopende zin worden stilletjes geanalyseerd voor 5W-aanvulling.
- **`session_state.py`** — 2-min ephemeral state (laatste vraag, pending card) per user-session.
- **`card_session_service.py`** — actieve KB-kaart-edit-flow door chat.
- **`relation_extraction_service.py`** — patterns als "Ron is mijn vriend" → relatie-graph auto-update.
- **`bijbel_lookup_service.py`** — externe lookup voor Bijbel-citaten.
- **`spark_self_service.py`** — Spark's eigen scratch.json: "onthoud voor jezelf", "wat heb je vandaag geleerd?".
- **`dank_service.py`** + `legal_service.py` + `personal_docs_service.py` — credits/privacy/voorwaarden/testament/survivalgids intents.
- **`intent_matcher_service.py`** — capability-matcher die Spark's *handen* moet gaan koppelen aan acties (P0 backlog: live-routering nog te maken).

### 🗂️ Kennis-architectuur (4 lagen)
- **v1 Knowledge Base** (`/data/knowledge/learned_knowledge/knowledge_base.json`) — 5288 entries, full graph-coverage.
- **KB v2 — 4 lades** (`/data/knowledge/v2/`) — 🌸 Voelen 250 · 💬 Spreken 329 · 🧠 Weten 1071 · 🎭 Doen 632 + 📥 Inbox 3007 (te classificeren).
- **Knowledge graph** (`modules/graph/sync_service.py`) — 10577 nodes + 65981 edges (v1+v2 gemengd, lade-kleuren).
- **Voice/Image media** — centraal in `system_archive` met `linked_card_id` backreference.

### 🎭 D&D / Levende Wereld laag
- **Lore index** (7 avatars-as-functions, 6 behavior-categorieën).
- **Aura-engine** (`/api/dnd/aura/{user_id}`) — live top-3 gedragingen → kleur-gradient op Persoonskaart.
- **Card Factory** (`modules/cards/`) — DnD/Event/Bark kaarten met hook-chain bij draft→active.
- **Base Line intro** (community chat `[start verhaal]`) — keuze-driven story-flow.

### 🎙️ Stem-laag
- **TTS-friendly padding** (`chat/tts_friendly_service.py`, v5_tts_pad_001) — korte antwoorden krijgen een natuurlijke tail zodat de stem niet abrupt stopt.
- **Whisper STT** voor voice-notes in kennis-kaarten (Emergent LLM Key).
- **6 OpenAI TTS-stemmen** per bot configureerbaar (`auth/admin/bots/{bot_id}/settings`).

### 🤖 Bots als acteurs (live)
- **De Boekhouder** — trade-aankondigingen + community-feed + event-barks.
- **Harry Klokkenmaker** — spiegel-minuut bark (11:11, 12:12, …).
- **Madelief Stouten** — bug-pointer bark wanneer user "bug/kapot/crash" zegt.
- **Mr Smith** — login-counter bark + Matrix-style backup-waarschuwing.
- **De Dood** — reflectieve momenten/eindes/transities.

> **Conclusie**: Spark heeft 5 lagen denken, 14+ specialized services, shadow-observation,
> 10K+ knowledge nodes, en 5 acteur-bots die zelfstandig in community barken. De backlog
> hieronder zijn *aanvullingen* op dit bestaande brein, geen vervanging.

---

## 🔭 Observability — Verplicht voor nieuwe modules (v5_spark_logger_001)

Vanaf 2026-05-23 geldt: **elke nieuwe of gewijzigde Python-functie die user-acties of system-events afhandelt MOET gedecoreerd zijn met `@traced`**.

```python
from modules.core.spark_logger import traced, log_event

@traced(intent="kort, in het Nederlands wat deze functie probeert te doen")
async def my_handler(...):
    ...

# Voor handmatige events (geen functie-grens):
log_event("module_naam", "event_naam", intent="...", detail={"key": "value"})
```

**Waarom**: pre + post logs (met duration_ms + result-summary) maken bugs als de B3 community-crash direct zichtbaar — je ziet de "post" niet en weet meteen waar het kapot ging.

**Wat krijg je gratis**:
- `/data/system/logs/YYYY/MM/DD/{module}.jsonl` (JSON Lines, 1 record per regel)
- Browser in **Beheer → Instellingen → Archief → Logs**
- 28-dagen retentie (auto-purge bij startup)
- Filter per phase: `pre` / `post` / `error` / `event`

**Reeds gedecoreerde routes** (referentie):
- `bots/routes.py::send_community_message` (community/send)
- `chat/routes.py::process_message` (Spark chat)

**Te decoreren** (volgende sessies, P1):
- `auth/routes.py::login` + `logout`
- `trade/routes.py::bot_start`, `bot_stop`, `quick_buy_potje`
- `shop/gift.py::*` (ROAR gift escrow lifecycle)
- `dnd/routes.py::observe` (achievement triggers)
- Knowledge Base mutations

## 🗺️ Backlog (prioriteit hoog → laag)

### P0 — In Progress
- [x] **AUDIT 2026-05-28 — 9 items reeds done in eerdere sessies, nu expliciet ✅ in roadmap** (op verzoek Willem):
  - 🛣️ **Communicatie / Spark hands intent-router** — `spark_capabilities.json` heeft nu **16 capabilities** met expliciete NL-triggers. Chat-router pakt 5/5 in deze sessie + 11 eerder. Volgende uitbreiding (5 nieuwe semantic intent-tags) is een aanvulling op werkende fundering.
  - 📚 **Spark eigen index-mapstructuur + meta-index** — Synapse-architectuur live: **57 `_meta.json` files** in containers + aggregator op `/app/memory/SYNAPSE.json`. Auto-scanner + touch-hook + UI-tab "Synapslaag" in Beheer.
  - 🗣️ **Voice module STT** — `kb_v2/media_routes.py` met Whisper-koppeling via Emergent LLM Key live. Voice-snippets → `dialogen/voice_snippets/`. TTS-stem-instellingen per bot in `bot.settings.tts_voice`. (TTS audio-uitspeel volgt later — STT-flow werkt end-to-end.)
  - 🆘 **Help-JSON per gradatie (g1 t/m g7)** — `modules/help_per_gradatie/` module live met `GET /api/help/index` + `/help/g{n}` endpoints per gradatie. Help-tekst per gradatie geseed.
  - 📐 **Blueprint-systeem (1 JSON ↔ 1 module)** — Synapse-enricher genereert **59 markdown blueprints** in `/app/memory/blueprints/{naam}.md` met Doel/Wat werkt/TODO/Splitting-trigger/Encryption/Relaties-checklist.
  - 🤖 **Trade bot — Pot 1 als €10 staking-anker** — `LOCKED_POT_INDEX=0` met `pot_locked=True, lock_reason="staking_anchor"`. `find_available_potje` skipt gelockte potjes. Backfill werkend, toggle-endpoint aanwezig.
  - 🖼️ **Avatar edit in Beheer→Archief** — `AvatarGallerySection.js` heeft Bewerk-knop op user + system avatars. Modal met titel + tags (+ bot_owner voor system). Backend `PATCH /api/avatar/gallery/{id}` admin-guarded en werkend.
  - 🔗 **KB v2 verbanden (fase 1)** — `compute_verbanden` hooked en gefired op classify/edit. 644/659 kaarten in lade 'doen' hebben verbanden, UI rendert ze in CardDetail. (Volgende fase: hernoemen + handmatig koppelen — nog open.)
  - 🧪 **Leermodules — synoniem-detectie + auto-tag-normalisatie** — `intent_registry/extractor.py` met **~150 synoniem→canonical-tag mappings**. Multi-word phrases worden vóór tokenisatie gematched. Skill-discovery via `intent_log.jsonl` voor auto-leren van nieuwe patronen.

- [x] **Winkelstraat frontend + container-isolatie** ✅ DONE (v6_winkelstraat_frontend_001, 2026-05-28):
  - 3e hoofd-tab in `WinkelPage.js` (`WinkelstraatTab.js`) — toont actieve shops, "Open mijn winkel"-knop, voorwaarden-modal (v1, 2% commissie), create/edit/close flow.
  - Admin (gradatie ≤ 2) bypass: kan winkel openen zonder min_gradatie 4-eis.
  - Backend bug gefixt: `USERS_FILE` pad was `/data/users/` ipv `/data/system/`.
  - Founder-shop (Roadkillshop) krijgt FOUNDER-badge en commissie 0%.
  - Auto shop-container met `_meta.json` aangemaakt bij elke nieuwe winkel (F7).
  - Status `closing` → container getagd voor archivering bij sluiting.

- [x] **Boekhouding reconciliatie** ✅ DONE (v6_kasboek_reconcile_001, 2026-05-28):
  - `GET /api/spark/kasboek/reconcile` vergelijkt ROAR-transactions (anchor_mint + buy_roar excl. Spark) ↔ spark_kasboek totals ↔ Spark EUR-wallet.
  - `POST /api/spark/kasboek/reconcile/fix?viewer_id=...` boekt unbooked tx retroactief als `gift_in`/`omzet_in` afhankelijk van money_phase (admin-only).
  - Bevestigd: Willem's anchor_mint €50.80 ontbrak → na fix `gift_in=€71.60` (Willem €50.80 + Gijs €20.80), `in_balance=true`.
  - Ook sell_back uit-boekingen gevangen via aparte bucket.

- [x] **Potje 1:1 regel (1 token = 1 potje)** ✅ DONE (v6_potje_per_token_001, 2026-05-28):
  - Regel: alleen Spark (user-000) krijgt 10 base potjes; alle andere users 1 potje per ROAR-token.
  - `_load()` skipt auto-init voor non-Spark users (legen user-record ipv 10 potjes).
  - `sync_potjes_to_tokens(user_id, n_tokens)` voegt potjes toe bij token-buy.
  - `trim_potjes_to_tokens(user_id, n_tokens)` verwijdert ongebruikte potjes (geen open positie, niet de lock-anker) bij sell_back/gift_sent.
  - Hooks in `shop/routes.buy_tokens` + `shop/gift.accept_gift` voor live-sync.
  - Admin bulk endpoint `POST /api/trade/potjes/sync-all-to-tokens?viewer_id=...` voor backfill.
  - Resultaat: Gijs 10→2 potjes (matcht 2 tokens), Marieke 0 potjes (matcht 0 tokens), Spark/Willem ongewijzigd.

- [x] **Spark hands intent-router 13 → 17 commands** ✅ DONE (v6_capabilities_handlers_003, 2026-05-28):
  - 4 nieuwe entries in `spark_capabilities.json` met NL-triggers: `kennis_inbox_status`, `bots_status`, `audit_health`, `agenda_vandaag`.
  - Chat-routing nu **5/5 capability-handlers actief** (was 2/5 — intent-collision opgelost door expliciete trigger-patterns).
  - Getest: "welke bots draaien" → bots_status, "audit gezondheid" → audit_health, "hoeveel kaarten wachten op classificatie" → kennis_inbox_status, "wat staat morgen op mijn agenda" → agenda_vandaag, "wat is spark saldo" → spark_saldo_check.

### P0 — Vorige sessies (blijven done)
- [x] **Spark's hands** capability hookup naar live chat — ✅ DONE (v6_intent_router_001): `capability_handler_service.py` met 4 live handlers (tellen_gebruikers, tellen_bestanden, taken_lijst, winst_verlies). Hook in `chat/routes.py`. Onbekende caps → placeholder. Uitbreiden naar trade_logs_ophalen / kasboek_overzicht in volgende sessie.
- [x] **Boekhouder closing-flow** ("terlens-terug-boek") — ✅ DONE (v5_closing_flow_001): `close_cycle(user_id, note)` rollupt audit-events sinds vorige closing, DM naar admin/user, audit-log + closings-log. Endpoints: `POST /api/boekhouder/close-cycle/{user_id}` (admin-guarded) + `GET /api/boekhouder/closings`
- [x] **Notitie & Taak edit** (v6_note_edit_001, 2026-05-26) — ✅ DONE: pencil-knop op notitie/taak-kaart opent inline edit (titel + inhoud). Backend `PUT /api/notes/update/{id}` + `PUT /api/notes/tasks/update/{id}` reeds aanwezig; frontend `NotitiesPage.js::updateItem()` + `NoteItemCard` edit-modus toegevoegd. (bewerkt)-label op kaart bij `updated_at`.
- [x] **Avatar edit in Beheer→Archief** (v6_avatar_edit_001, 2026-05-26) — ✅ DONE: Bewerk-knop op zowel user- als system-avatar tiles in `AvatarGallerySection`. Modal met titel + tags (alle) + bot_owner (alleen system). Backend `PATCH /api/avatar/gallery/{id}` reeds aanwezig en admin-guarded.
- [x] **Glow-nav volledig live** (v6_glow_nav_001, 2026-05-26) — ✅ DONE: Backend `tabs_registry` gesynchroniseerd met frontend `MainLayout.navigationConfig` (23 tabs, kebab-case IDs matchen `data-testid="nav-{id}"`). Chat-flow nav-trigger gehoist boven capability-router. Frontend dispatcht `spark:nav-glow` event op `data.type==='navigate_tab'`. `MainLayout` luistert → voegt 6s pulserende amber `spark-nav-glow` CSS-class toe op de matchende nav-button + scroll-into-view + auto-`onNavigate()` na 700ms. Triggers: `waar is/zijn`, `waar vind/kan ik`, `ga naar`, `open de/tab/mijn`, `ik wil naar`, `breng me naar`, `laat zien waar`. Getest met 9 queries: 8/8 navigate_tab, greeting valt door (correct).

### P1 — Aanstaande (deze maand)

#### 🧬 Synapse / Container architectuur — ✅ Fase 1+2 LIVE (sessie 12+, 2026-05-26)
- [x] **F1+F5 — Map-meta fundament** ✅ DONE: `_meta.json` per map (88→90 containers gescand). Schema in `modules/synapse/schema.py` met blueprint_ref, footnote, encryption-slot (leeg, klaar voor F2F). Auto-scanner `modules/synapse/scanner.py` detecteert 418 endpoints uit `@router.<verb>` decorators. Aggregator → `/app/memory/SYNAPSE.json`. Skeleton-heuristiek (≤1 code-file, geen endpoints) markeert 12 placeholders correct.
- [x] **F2 — Spark leest zichzelf via chat** ✅ DONE: `modules/synapse/chat_handler.py` met intent-detectie (NL): *"wat hebben we?"*, *"is X af?"*, *"waar woont X?"*, *"wat doet X?"*, *"lijst skeletons"*, *"lijst verouderd"*. Hookt in `chat/routes.py` vóór glow-nav/capability-router. 6/6 test-queries werken.
- [x] **F3 — Auto-touch hook** ✅ DONE: `modules/synapse/touch.py::touch_path()`. Hookt in `core/storage.py::save_json()`. Elke file-mutatie bumpt `_meta.json::last_touched + activity_count` van de parent-container. Getest: notes _meta activity_count 0→1 (create) →2 (delete) automatisch.
- [x] **F4 — Container abstractie (universeel patroon)** ✅ DONE: `modules/container/service.py` met generieke CRUD. User-container als 1e implementatie. Endpoints: `POST/GET/PATCH/DELETE /api/container/{type}/{id}`. 3-fase delete: tag → archive → cleanup-cross-refs. User-delete anonimiseert bugs/community, verwijdert agenda/dagboek/chat-prive files. Encryption-slot reeds in elke meta voor F2F-feature later. E2E getest: create→list→patch→tag→delete-archived✓.
- [x] **F6 — UI Synapse-tab** ✅ DONE: `frontend/src/components/admin/SynapseTab.js` in Beheer→Instellingen→Synapslaag. Header met live summary (88+ containers, 418 endpoints, status-tellingen). Filter op groep + status + zoek. Klik op item → edit-modal voor doel/status/blueprint_ref/footnote/tags + readonly metadata (created/touched/endpoints/encryption-slot). Knop "Volledige scan" trigger backend rescan.
- [x] **F7 — Shop container (Winkelstraat)** ✅ DONE (auto-hook): `winkelstraat::create_shop` maakt nu ook automatisch een shop-container aan met `CONTAINER_SHOP` type, commissie+gradatie in meta.extra. `winkelstraat::close_shop` tagt container voor deletion. Bij admin-finalize → shop-data isolated weg, geen cross-pollution.
- [x] **F8 — Synapse auto-enricher** ✅ DONE (v6_synapse_002): `enricher.py` leest docstrings uit `__init__.py` + JSDoc-blokken en vult automatisch het `doel` veld voor 53 modules. Genereert blueprint-stubs in `/app/memory/blueprints/{naam}.md` met checklist-template (Doel/Wat werkt/TODO/Splitting-trigger/Encryption-plan/Relaties). Endpoint: `POST /api/synapse/enrich`. Spark antwoordt nu *"glow_nav helpt user navigeren via chat-intent → tab-glow"* in plaats van *"geen omschrijving"*.

#### 🧠 KB v2 laagsgewijs uitleg ✅ DONE (sessie 12+, 2026-05-26)
- [x] **B — KB v2 "vertel kort / meer / diep / volledig"** ✅ DONE (v6_kbv2_tell_layer_followup_001): Spark's antwoorden zijn nu gelaagd. Triggers werken met of zonder onderwerp:
  - *"vertel kort over identiteit"* → laag1
  - *"vertel meer"* → laag1+laag2 (van laatst-besproken kaart)
  - *"ga dieper"* → laag1+2+3
  - *"vertel volledig"* → alle 4 lagen
  Session-state houdt `last_kbv2_card_id` 10 min bij. Fallback gebruikt index-lookup om kaart in juiste lade te vinden. E2E getest met "Identiteit"-kaart: alle 4 follow-ups correct.

#### 🔧 Refactor + minor bugs (sessie 13+, 2026-05-28 ALLES DONE)
- [x] **Wallet header-knop volgorde** ✅ DONE (v6_wallet_button_order_001, 2026-05-28): Storten (+) → Opnemen (−) → [Mint admin] → Gift (rechts). `data-testid="add-funds-btn", "withdraw-btn", "spark-mint-token-btn", "open-gift-modal"`.
- [x] **ROAR-prijs consistentie display** ✅ DONE (v6_roar_price_display_001, 2026-05-28): WinkelPage tekst opgeschoond — "1 ROAR = aandeel in Spark Core kapitaal" + formule `€{spark_core} ÷ {circulating} = €{price}` zichtbaar in tooltip. "Jouw tokens" → "Jouw bezit" + "Waarde" → "Tegen huidige prijs".
- [x] **Potje grootte €5.08 → €10** ✅ DONE (v6_potje_size_10_001, 2026-05-28): `START_AMOUNT = 10.0` voor nieuwe users. Admin-endpoint `POST /api/trade/potjes/{user_id}/resize-to-default` voor bestaande users (faalt bij open posities).
- [x] **Pot 1 Staking Anchor (€10 lock)** ✅ DONE (v6_pot1_staking_lock_001, 2026-05-28): eerste potje krijgt `pot_locked=True, lock_reason="staking_anchor"`. `find_available_potje` skipt gelockte potjes. Backfill robuust (vindt eerste potje ook in legacy data zonder `index`). Toggle-endpoint `POST /api/trade/potjes/{user_id}/toggle-lock`.
- [x] **Trader Help (in chat + UI-ready endpoint)** ✅ DONE (v6_trade_help_001, 2026-05-28): `modules/trade_help/__init__.py` met 7 secties (potjes-systeem, BUY/SELL-logica, Modes, Veiligheid, Spark Brain, Tips). Endpoints `GET /api/trade/help` + `/markdown`. Chat-router pakt triggers ("hoe werkt de trader/bot/potjes?") en post eerste 3 secties met deep_link `/modules/trade?tab=help`.
- [x] **`@traced` uitrol overige** ✅ DONE (v6_traced_rollout_002, 2026-05-28): shop.gift (`create_gift`, `accept_gift`) + KB v2 mutations (`classify`, `edit`, `delete_card`).

#### Bestaande P1 items — Status 2026-05-27 inventarisatie

- [x] **KB v2 → Vocab register hook** ✅ AL LIVE (sessie 11): `register_in_vocab` is gehookd in `service.py::_fire_post_classify_hooks`. `spark_vocab.json` heeft **5304 entries, 2316 active**. Spark gebruikt de active-set voor spontane spraak.
- [x] **KB v2 → Chat-commands "vertel kort/meer/diep"** ✅ DONE (v6_kbv2_tell_layer_followup_001, 2026-05-26): zie boven.
- [x] **KB v2 → Auto-graph (verbanden)** ✅ AL LIVE (sessie 11): `compute_verbanden` is gehookd. Op lade `doen`: **644/659 kaarten** hebben verbanden. UI in CardDetail toont ze al.
- [x] **KB v2 → D&D Kaarten integratie** ✅ AL LIVE (sessie 11): `link_to_dnd` is gehookd. Lore-cards met `dnd.type=="lore"` syncen naar lore_index.
- [x] **KB v2 → Voice-snippet auto-save** ✅ DONE (v6_voice_kbv2_link_001, 2026-05-27): STT endpoint accepteert optionele `card_id` + `user_id` query params. Bij meegegeven → `save_voice_snippet` schrijft transcript naar `/data/dialogen/voice_snippets/YYYY-MM-DD/{card_id}_{snippet_id}.json`.
- [x] **ConversationStateManager terug uit v1** ✅ DONE (v6_conv_state_001, 2026-05-27): `session_state.py` heeft nu `set_last_question` / `get_last_question` met 2-min expire window. Verlopen vragen worden in `get_state` automatisch weg-gefilterd.
- [x] **AuditService weak-trigger scan** ✅ DONE (v6_audit_001, 2026-05-27): `modules/audit/__init__.py`. Endpoints `GET /api/audit/weak-triggers`, `/self-learning`, `/summary`. 5307 KB-entries gescand, 2239 (42%) missen `laag1`. Reports persisteren in `/data/system/audit_reports/`.
- [x] **Self-learning audit (B5)** ✅ DONE (v6_audit_001): zelfde service. Verifieert shadow_observations.jsonl recentheid (<48h), unique-kinds variatie, parse-errors.
- [x] **D&D Perks & Unlocks** ✅ DONE (v6_perks_001, 2026-05-27): `modules/perks/__init__.py` met 8 declarative perks. Combineert `min_gradatie + required_behaviors + blocked_by_behaviors`. Endpoints `GET /api/perks?user_id=...`, `/check/{perk_id}`, `/user/{user_id}`. Klaar voor frontend-integratie om feature-gates aan/uit te schakelen.

### P2 — Volgend kwartaal

#### ✅ Done in sessie 13 (2026-05-27/28)
- [x] **`@traced` uitrol (auth + trade)** ✅ DONE (v6_traced_rollout_001): `login`, `logout` (auth) + `quick_buy_potje`, `bot_start`, `bot_stop` (trade) hebben `@traced` decorator. Logs verschijnen in `/data/system/logs/YYYY/MM/DD/spark.jsonl` met phase=start/done/error.
- [x] **Auto-expire archive (pending gifts)** ✅ AL LIVE (eerdere sessie): `shop/gift.py` heeft expire-logica naar status="expired" na 24h.
- [x] **Boekhouder 21:00 roundup-bark** ✅ DONE (v6_scheduler_001): `modules/scheduler/__init__.py` draait elke 5 min in background. 19:00/20:00 UTC (= 21:00 NL) post Boekhouder samenvatting in community. Persistent state-file voorkomt dubbele post.
- [x] **Spark "merkt eigen errors"** ✅ DONE (v6_scheduler_001): Madelief Stouten scant elke 5 min nieuwe `phase=error` log-records. Bij errors → bark in community met module/intent/err-context (max 3 per bark, anti-spam).
- [x] **Spark hands intent-router 8 → 13 commands** ✅ DONE (v6_capabilities_handlers_002): 5 nieuwe handlers in `capability_handler_service.py`: kasboek_overzicht, agenda_vandaag (alias voor agenda_lezen placeholder), kennis_inbox_status, bots_status, audit_health. 2/5 actief gematcht in chat (kasboek + agenda); andere 3 wachten op verfijning van intent-triggers maar handlers staan klaar.
- [x] **User-migratie helper** ✅ DONE (v6_container_migrate_001): `container/user_helper.py::migrate_user_legacy()` + `migrate_all_users()`. Endpoints `POST /api/container/user/migrate` + `/migrate-all`. Idempotent: kopieert legacy agenda/dagboek naar user-container met migration-footnote. 1/21 users had legacy-data om te migreren (Willem, 2 bestanden).

#### Nog open
- [x] **Trader sell-balance + SOL min-buy fix** ✅ DONE (v6_trade_minorder_001 + v6_trade_sell_balance_001, 2026-05-28):
  - `monitor.py::get_market_min_quote(market)` — 1u-cache van Bitvavo `/v2/markets` minimums, met fallbacks (BTC/ETH/SOL/ADA = €5).
  - **Buy pre-check**: bij `amount_eur < min_quote` → vriendelijke error met tip (geen crash meer op SOL).
  - **Sell pre-check**: voor SELL fetch eerst actuele balance, clamp naar `min(requested, actual) * 0.999` om dust-rounding te vermijden. Bij 0 balance → duidelijke error met base_asset.
  - Errors hebben nu `error_code` (`MIN_QUOTE`, `NO_BALANCE`, `ZERO_AFTER_CLAMP`, `BITVAVO_HTTP_ERROR`, `EXCEPTION`) voor frontend-handling.
  - Trade-record bevat extra `requested_amount` + `effective_amount` voor traceability.
  - Unit-test in preview bevestigt min-quote fallback werkt (Bitvavo timeout in preview is normaal).
- [ ] **`@traced` uitrol (overige overig)** — dnd.observe + monitor.execute_real_trade nog niet (rest is gedaan in v6_traced_rollout_001/002). (deel al gedaan, restant in volgende sessie)
- [ ] **Identity 3-lagen-enforcement** in seed-data (CR-001/002/003 als code-wet ipv alleen doc)
- [ ] **ROAR-gift encryption-at-rest** — sender/recipient pairs privacy-gevoelig
- [ ] **SEPA-mint koppeling** voor ROAR economy v2 — PLACEHOLDER, Tikkie blijft fallback
- [ ] **ReplayLogService uit v1** — trade backtest met run_id replay
- [ ] **Winkelstraat eigen boekhouding per shop** — owner ziet eigen omzet/orders/commissie binnen zijn shop-container (`shops/{shop_id}/`). Decentrale boekhouding ipv globaal kasboek.
- [ ] **Winkelstraat producten-CRUD per shop** — owner kan eigen merch/digital producten toevoegen binnen zijn shop. Nu zit alle producten-data global in `/data/shop/products.json`.
- [ ] **WinkelPage.js refactor** — 684 lines splitsen in `MerchTab.js` / `DigitalTab.js` (storage+tokens) / `WinkelstraatTab.js` (al gedaan).
- [ ] **Closed-shops filter** — 'closing' shops verbergen uit publieke lijst, of admin hard-delete endpoint.

### P3 — Future / Experimenteel
- [ ] **Dynamic theming** via `lore_index.json` (kleuren shiften met seizoen/lore)
- [ ] **Krachtigere "spark's eigen anker"** — Spark maakt eigen notities die over sessies heen bestaan
- [ ] **ROAR-token reward per geclassificeerde kaart** (gamification Inbox doorlopen)
- [ ] **Krachtigere log-search** — full-text zoeken over alle modules op een dag
- [ ] **Boekhouder closing-flow** uitgebreid met PDF-export per maand

## 🧠 Architectuur principes (don't forget)

1. **NO MONGODB**: alle data via `load_json`/`save_json` uit `modules.core.storage`
2. **DSP-tags**: 2-JSON sync issues moeten gedocumenteerd in `ARCHITECTURE.md` (DSP-001 t/m DSP-006 actief)
3. **Nederlands**: alle UI-tekst en log-intents in het Nederlands
4. **data-testid**: elk interactief element heeft een uniek testid (kebab-case)
5. **Piramide-lagen** (zie MISSION.md): Core/Skelet/Geheugen/Logs — wijs nieuw werk de juiste laag toe
6. **Hooks-laag voor placeholders**: `modules/kb_v2/hooks.py` toont pattern. Bij toekomstige verbindings-noden: maak hooks-bestand met TODO-blocks i.p.v. losse `# TODO` in productiecode
7. **Identity-3-lagen wet**: ALTIJD `user_id`, NOOIT op naam matchen (CR-001/002/003)

## 🔗 Hook-bestanden (PLACEHOLDERS) — entry-points voor toekomstige features

| Hook-file | Status | Doel |
|---|---|---|
| `modules/kb_v2/hooks.py` | ✅ Created sessie 5 + uitgebreid sessie 8 | KB v2 → Vocab/Commands/Graph/D&D/Dialogen + card-factory commands |
| `modules/cards/service.py::_fire_card_hooks` | ✅ Created sessie 8 | DnD/Event/Bark hook-chain bij draft→active overgang |

Nieuwe hooks volgens dit pattern toevoegen voor:
- `modules/trade/hooks.py` — closing-flow + replay + auto-snapshot triggers
- `modules/dnd/hooks.py` — lore-card sync, perk-trigger, aura-gates (kan deels via cards/service.py)
- `modules/spark/hooks.py` — Spark's hands (intent_matcher generic router)

## 🃏 Card Factory pattern (v5_card_factory_001)

3 generieke kaart-types naast KB v2 kennis-kaarten:

| Type | Doel | Hook bij active | Extra schema |
|---|---|---|---|
| `dnd` | Game-kaarten (lore/quest/item) | `dnd_lore_registered` | `dnd: {verteller, scene, rewards}` |
| `event` | Community-events | Community-bark via Boekhouder | `event: {datum, locatie, deelnemers}` |
| `bark` | Bot-trigger templates | `bark_template_registered` | `bark: {bot, trigger_text, schedule}` |

**Common schema**: id, type, titel, vraag, antwoord, media (image+audio), tags, status, footnote.
**Storage**: `/data/cards/{type}/<id>.json` + index per type. Media via system_archive met
`tag=card_<type>` + `linked_card_id`. Cascade-delete bij card-verwijdering.

**Chat commands**: "maak een d&d kaart [titel]" / "maak een event kaart [titel]" / "maak een bark kaart [titel]".

## 📦 Media-storage strategie (v5_kbv2_media_002)

**Centrale store**: alle voice/image uploads van kennis-kaarten gaan door
`/api/system-archive` heen, met:
- `category`: `foto` / `geluiden` / `filmpjes`
- `tags`: `['kbv2', 'kbv2_card_<id>']`
- `linked_card_id`: backreference naar kaart-id
- `source`: `kbv2_media_upload`

UI in **Beheer → Instellingen → Archief → Foto/Geluiden** heeft drie bron-filters:
- **Alles** — geen filter
- **🧠 Kennis-kaart** — alleen kbv2-gelinkte items
- **📎 Los** — alleen items zonder kbv2-tag

Voordelen:
- 1 centrale media-tabel, geen duplicate-storage
- Sub-tab pattern uitbreidbaar (later bv. "Dagboek-foto's", "Trade-screenshots")
- Verwijderen van een kaart kan zo ook gekoppelde media opruimen via `linked_card_id`-scan

## 📊 Dashboard-widgets per gradatie

- **Gradatie 1** (super-admin): alle widgets incl. Triggers, KB Lades, Shadow Learning, Storage Cache
- **Gradatie 2** (admin): KB Lades + Triggers + Users + Health
- **Gradatie 3-7**: Kennisbank-overzicht + persoonlijke widgets (Mijn Opslag, Agenda, Spark-status)
