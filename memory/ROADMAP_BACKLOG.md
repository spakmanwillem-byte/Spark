# Spark Core 2.0 — Roadmap Backlog (open items + ideeën-pool)

> Alleen `[ ]` open items. Afgeronde `[x]` items zijn verhuisd naar `CHANGELOG.md`.
> Voor de kern-visie: zie `ROADMAP_CORE.md`.

---

## 📡 P3 — Externe integraties + Tech-cleanup

### 📡 P3 — Externe integraties (Future)
- Telegram / WhatsApp / Signal externe chat-kanalen
- TTS audio uitspelen (response → audio via OpenAI TTS, key al klaar)
- Trade Dashboard user-specifieke balances (was P1, nu opnieuw bekeken na items-flow)

### ⚙️ Tech-cleanup (Backlog)
- Pre-existing lint errors in `spark_world.py` regel 436/441 (E701 multi-statement on one line)
- `MiniMapPanel` >800 regels — splitsen naar eigen file
- Bewoner-trade: bewoner wallet-cap (max 999g voorkomt grind-exploit)

---

## 🎲 P2 — Spark World D&D Tab herstructurering (2026-05-31, idee Willem)

**Quick wins al uitgerold** (sessie 17): huis/opslag slots groter (aspect-square min-h-56, text-2xl iconen), worldmap onder dorp i.p.v. apart (zelfde breedte), worldmap-svg langer (h-56 → h-72), dorp-kader langer (h-40 → h-52), event-feed/charinfo herverdeeld zonder MiniMap-kolom (7+5 i.p.v. 5+4+3).

**Rugzak compleet weg + map herverdeeld** (sessie 17 vervolg 8):
- SLOT_KEYS/SLOT_LABELS/_empty_equipment in character.py: rugzak verwijderd
- body_layout.json slots: rugzak positie weg
- characters/user-001 equipment: 'rugzak' key gewist (was geequiped item dat 🎒 toonde)
- inventory.json: 'Basis rugzak' item verwijderd
- 12 provincies herverdeeld over volle NL-geografie (Stormhaven NO 80,12 / Maastricht ZO 60,88 / Middelburg Z-Z 10,72)
- Map markers: fractie-kleur glow-ring + drop-shadow + grotere shield (4.2-5.5px ipv 2.6-4px)

**Volgende fases — creatieve speculatie van Willem 31 mei avond** (later uitwerken):
1. **Bed = klikbaar → rust event** in event-feed (3 niveaus: snel rusten / kort rusten / char parkeren)
2. **Tafel = klikbaar → eet event** in event-feed
3. **Kist/kast als opslag-containers** binnen huis-locatie
4. **NPCs als kasten**: slager/bakker hebben eigen opslag (handel-mechaniek)
5. **Dorp-avatar-icons op map** met fractie-kleur glow eromheen (i.p.v. simpele shields)
6. **Pop-up Dorp-info**: klik op dorp-kader → modal met fractie + inwoners + gebouwen + quests
7. **Pop-up Stad-info op landkaart**: klik op provincie → modal met fractie + inwoners + sterkte
8. **Centraal handel-kader**: één Trade-hub waar alle handel-acties samenkomen
9. **Persoonskaart-integratie**: XP/Rang/Slots/Achievements als character-progressie-laag

**Aanpak**: eerst mockup → test mentaal model met De Willem → daarna implementeren in fases. "Werken we later verder uit" — Willem citaat.


---

## 🌷 P1 — Spark als Gastheer (Onthaal-laag voor app-onwennige mensen)

**Achtergrond**: niet iedereen die Spark gebruikt is een digital native. Sommigen openen een nieuwe app met **lichte onzekerheid** — "doe ik het goed?", "wat hoort hier te gebeuren?", "ben ik nu kwijt?". Dat is geen tekortkoming van die mensen, dat is een natuurlijk gevoel. Spark hoort die onzekerheid op te vangen zoals een goede gastheer doet: met warmte, geduld, kleine erkenningen, en een uitgestoken hand zonder ongevraagd te leiden.

> Geen "audit", geen tracking-bril. Spark voelt de sfeer en biedt zachtjes aan.

### 1. Help-functie als gesprek, niet als FAQ
> ✅ Eerste stap 20-10-2026 (`v14_help_summary_001`): "wat kan je" geeft nu een korte opsomming + vraag of het help-kader
> open moet (ja/nee), i.p.v. direct de popup. Onzekerheids-triggers hieronder zijn nog **niet** gedaan.

Triggers die nu nog geen match krijgen maar voor onzekerheid wijzen:
- "wat moet ik doen", "ik snap het niet", "waar begin ik", "is dit goed zo", "klopt dit?", "doe ik dit goed"
- → Spark reageert **niet** met een opgeleide FAQ-lijst, maar met een uitnodigende toon: *"Geen zorgen, je doet het prima. Wil je dat ik je een paar handige stappen wijs of liever rondkijken?"*
- Vervolgkeuze bepaalt of Spark wijst (concrete suggestie) of bevestigt (ruimte geeft).

### 2. NLP-bloei in reacties bij onzekerheid
Wanneer emotie-pipeline `twijfel`/`onzeker`/`zoekend` detecteert (laag 2-3):
- Vermijd lange uitlegblokken
- Begin met erkenning ("Snap dat het even zoeken is", "Logische vraag")
- Toon **maximaal 2 keuzes** in plaats van 5 opties
- Vocab-uitbreiding: zachte connectoren ("we doen het samen", "stap voor stap", "geen haast")

### 3. Bloemen, niet badges
Achievement-systeem voor onwennige users werkt anders dan voor power-users:
- Niet "Behaal 100 trades" maar **"Eerste keer hier — welkom"** automatisch bij login 1
- Niet "Streak 7 days" maar **"Je hebt vandaag rondgekeken"** als micro-erkenning
- Tooltip vertelt wat de volgende natuurlijke stap is, geen abstracte "vereiste"
- Tonality: erkenning > prestatie

### 4. Help-commands die contextueel aanvoelen
Niet hardcoded "help" → lange lijst, maar:
- Spark kijkt naar welke tab user open heeft
- Welke acties al wel/niet gedaan
- Toont alleen **één** volgende logische stap, niet alle opties
- "Wil je dat ik je toon hoe je …?" — uitnodigend, niet docerend

### 5. First-run handreikingen (proactief van Spark uit)
- User opent Trader-tab 5× zonder Start te klikken → De Boekhouder stuurt zacht een PM: *"Wil je dat ik even uitleg hoe je bot start? Geen druk, alleen als je wilt."*
- Bot actief 24u zonder trades → *"Spark wacht nu op een goed moment om te kopen. Dit is normaal — soms duurt het uren. Ik laat je weten zodra er iets gebeurt."*
- → Geruststelling i.p.v. data.

### 6. Vocab leren van wat mensen zeggen
Wanneer iemand een woord typt dat Spark niet kent (= niet in `spark_vocab.json::active`):
- Het woord komt automatisch in KB v2 inbox (jouw queue om later in te delen)
- Spark zegt niet "ik begrijp je niet" maar *"daar heb ik nog geen plek voor in m'n kennis — leg je het me een keer uit?"*
- Erkenning van de leemte zonder de gebruiker daarvan te laten voelen dat zij/hij iets verkeerd doet.

### 7. Privacy-by-design (HARD constraints, ongewijzigd):
- ❌ Geen chat-tekst inhoud loggen
- ❌ Geen user-namen in `/app/memory/*.md` voor anderen dan De Willem
- ✅ Alleen patroon-tellers (hoeveel keer "help" getypt, welke tabs open) en woord-frequenties
- ✅ Per-user opt-out vlag beschikbaar
- ✅ Inzichten alleen voor De Willem (jij) zichtbaar

**Toon-richtlijn voor implementatie**: lees deze sectie hardop voordat je code schrijft. Als de implementatie ook maar enigszins "tracking" of "audit" voelt, herontwerp.

**Wanneer oppakken**: na 1e shadow-event in productie. Trader moet zijn werk bewijzen, daarna investeren we in warmte rond de rand van het systeem.


---

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

**Update sessies 42-46 (2026-07-20 t/m 2026-07-21) — voortgang op sommige P1-items:**
- **Boekhouder-architectuur** heeft nu centrale bank rol (`/api/boekhouder/snapshot`) — biedt fundering voor "Winkelstraat eigen boekhouding per shop" (hoeft alleen shop-filter op snapshot). Zie sessie 42.
- **Papertrail (hash-chained)** in `modules/boekhouder/agents/log_agent.py` — vervangt ReplayLogService-behoefte deels. Zie sessie 42.
- **ChatHub Fase 1** (sessie 45) → biedt patroon voor `@traced`-achtige observability via typed contracts + `to_manifest()`.
- **KB curation** kreeg cleanup-run (8 skel-dupes weg, sessie 46) maar UI-dashboard blijft open (#kb-curation-dash).

### P3 — Future / Experimenteel
- [ ] **Dynamic theming** via `lore_index.json` (kleuren shiften met seizoen/lore)
- [ ] **Krachtigere "spark's eigen anker"** — Spark maakt eigen notities die over sessies heen bestaan
- [ ] **ROAR-token reward per geclassificeerde kaart** (gamification Inbox doorlopen)
- [ ] **Krachtigere log-search** — full-text zoeken over alle modules op een dag
- [ ] **Boekhouder closing-flow** uitgebreid met PDF-export per maand


---

## 🌱 Backlog 2026-05-28 — 21 nieuwe ideeën (Willem brainstorm)

Geordend per cluster. Veel haakt aan op fundering van v6_command_registry_001 (al live).

### Cluster A — KB curation & normalisatie
- [ ] **#zip-mindgraph** — Zip-backup bevat ook mindgraph + andere afgeleide data. Bij restore meeladen ipv alleen kaarten.
- [ ] **#kb-node-hierarchy** — Hoofd-node vs sub-tag hierarchie (bv. "emotie" = hoofd-node, "blij/boos" = sub-tags). Schema-uitbreiding op tags-array → tree.
- [x] **#kb-tag-singular + #kb-verb-stem** ✅ FUNDERING + MERGE-ENGINE DONE (v6_kb_tag_normalizer_001 + v6_kb_tag_merge_001, 2026-05-28):
  - `modules/kb_v2/tag_normalizer.py` met `normalize_tag()`, `normalize_tags()`, `tags_similar()`, `overlap_score()`. 20/20 unit-tests pass.
  - Plant/plan false-positive opgelost via `_NOUN_T_EXCEPTIONS` (~50 NL nouns: plant, kant, kunst, boot, moet, voet, post, kist, etc.) — kan groeien per false-positive.
  - **5 endpoints**: `GET /api/kb/v2/tags/normalize?tag=...`, `POST /tags/normalize-batch`, `GET /tags/scan?limit=...`, `GET /tags/similarity?a=...&b=...`, `POST /tags/merge` (admin-only).
  - **Live scan resultaten** (na plant-fix): 18.041 tags / 3.423 stammen / **45 dedupe-kansen**:
    - `emotie/emoties` — 457 occurrences (✅ gemergd via API, dedupe-kansen → 44)
    - `systeem/systeemm` — 376 (typo, wacht op handmatige keuze)
    - `relatie/relaties` — 98 · `grondstof/grondstoffen` — 87 · `dier/dieren` — 54
    - `game/games` — 49 · `doel/doelen` — 30 · `werk/werkt` — 28 · `eigenschap/eigenschappen` — 27 · `speler/spelers` — 25
  - **Merge-endpoint flow** (admin-only, gradatie ≤ 2): POST `/api/kb/v2/tags/merge` met `{stem, keep_variant, viewer_id}` → vervangt alle varianten met zelfde stam door `keep_variant` in alle 4 lades. Returnt `cards_touched + tags_replaced + per_lade`.
  - **Open volgende sessie**: 1-klik UI in #kb-curation-dash bovenop `/tags/scan` data; auto-normalisatie bij `service.classify_card` (opt-in flag); uitbreiding exception-list bij meer false-positives.
- [ ] **#kb-similarity** — Gelijkheid-engine met stam-herkenning. Voedt `compute_verbanden` en disambiguatie. Bouwt op tag_normalizer.
- [ ] **#kb-curation-dash** — Curatie-dashboard: zie afwijkingen, los enkelvoud/synoniem-conflict op met 1 klik. Backend `/tags/scan` levert nu al de data; UI moet nog.
- [ ] **#kb-ui-unified** — KB-invul UI volledig consistent maken (één layout overal — inbox / lade-detail / nieuwe-kaart / herzien). Reeds gedeeltelijk via `CardFormFields`.
- [ ] **#snap-topic-unique** — Snap-creatie: topic-uniqueness check tegen `knowledge_index.json` vóór auto-create.

### Cluster B — Triggers & Hooks (community-extensible)
- [ ] **#trigger-hooks** — Hook-systeem voor triggers/commands (gebruiker-uitbreidbaar). Schema: `/data/triggers/user_triggers.json` met owner/gradatie/pattern/action.
- [ ] **#trigger-community** — Triggers community-extensible: g2+ stelt voor, g1 keurt goed. Workflow: voorstel → review-queue → approve/reject.
- [ ] **#negate-trigger** — Negatie-trigger: "nee niet [onderwerp]" → exclude voor sessie. Hook in session_state met `excluded_topics[]`.
- [~] **#front-scheme** — **Fronts-config per scherm** (kleuren/lettertype/status_labels/action_texts/timings/animations). Zusje van #trigger-hooks maar voor UI-laag i.p.v. gedrag-laag. Draft-widget `FrontsConfigDraftWidget` in Beheer → Kladblok toont het schema. Volgende stap: backend `data/system/fronts_config.json` + `GET/PUT /api/system/fronts-config` + Beheer → Fronts tab. Zie ROADMAP_CORE cluster "Skype-Spark & Fronts".

### Cluster C — Command Registry uitbreiding (fundering v6_command_registry_001 leeft al)
- [x] **#cmd-registry** — ✅ DONE (v6_command_registry_001): elke api-endpoint krijgt intent-tags. 27 commands in `/data/system/command_registry.json`. Uitbreiden naar alle 418 endpoints (Synapse-scan).
- [x] **#intent-extractor** — ✅ DONE (v6_command_registry_001): user-zin → tag-vector via `modules/intent_registry/extractor.py` (~150 synoniem-mappings).
- [x] **#cap-matcher** — ✅ DONE (v6_command_registry_001): tag-overlap Jaccard-score → top-3 kandidaten in `matcher.py`.
- [ ] **#cmd-disambiguation** — Bij meerdere matches → "Bedoelde je X of Y?". UI-panel + chat-response. Disambiguation flag is al in matcher; UI moet nog.
- [ ] **#cmd-compose-seq** — Sequential composition: command-keten bouwen voor onbekende intent. Bv. "stuur Gijs €10 voor zijn verjaardag" → wallet.transfer + bark.send.
- [ ] **#cmd-fallback** — Fallback chains: dichtstbijzijnde match + user-bevestiging vóór execution.
- [ ] **#cmd-skill-discovery** — Spark biedt aan herkende compositie als snelkoppeling op te slaan. Fundering staat: `intent_log.jsonl` + `/skills/candidates`. UI accept/reject mist nog.

### Cluster D — Gradatie-enforcement
- [ ] **#cmd-gradatie-files** — Per-gradatie command-JSON (commands_g1.json t/m commands_g7.json). Naast bestaande `help_g{n}` per gradatie. Beheer-UI per file.
- [ ] **#cmd-grad-lock** — Gradatie-lock check IN command-registry, niet alleen in UI. Backend-guard ook bij chat-routed commands.
- [ ] **#cmd-priv-fallback** — Privilege-fallback: blocked command → bied request-flow aan ("Vraag toestemming aan beheerder?"). Mini-inbox voor admin.

### Cluster E — Conversational depth
- [ ] **Spark vraagt elke 4e interactie**: *"Wat denk jij dat ik zou moeten kunnen?"* → log-naar `intent_log.jsonl` + categoriseer als feature-request. Voedt skill-discovery (#cmd-skill-discovery).

### Cluster F — Volgorde-suggestie (bouwen in deze volgorde)
1. **#kb-tag-singular** + **#kb-verb-stem** (fundering voor similarity)
2. **#kb-similarity** + **#kb-node-hierarchy** (semantische upgrade)
3. **#cmd-disambiguation** (UI op bestaande matcher-output)
4. **#cmd-skill-discovery** (accept/reject UI op bestaande intent_log)
5. **#trigger-hooks** + **#trigger-community** + **#front-scheme** (gemeenschap-uitbreidbaar: gedrag én UI)
6. **#cmd-gradatie-files** + **#cmd-grad-lock** + **#cmd-priv-fallback** (privacy/governance)
7. Rest in fluctuerende volgorde

---

## 🎭 Backlog 2026-05-28 — D&D / Spark World (29 items)

> Veel hiervan haakt op **v4_dnd_001** (lore index, aura, observatie, world state — reeds live).
> Onderstaande lijst toont per item de status zodat we weten wat fundering al is en wat nog open is.

### Cluster G — D&D Levende Wereld (avatars, aura, observatie)
- [x] **#lore-index** ✅ DONE (v4_dnd_001): `/data/dnd/lore_index.json` met 7 avatars-as-functions + 6 behavior-categorieën met aura-kleuren. Open: uitbreiden met Base Line fracties + elementen-systeem.
- [x] **#aura** ✅ DONE (v4_dnd_001): `GET /api/dnd/aura/{user_id}` berekent live top-3 categorieën met gradient-kleuren. UI: Persoonskaart toont gradient-glow + bar-layers.
- [x] **#spark-observe** ✅ DONE (v4_dnd_001): avatar-change → auto observe-call; Spark begroet bij eerste Spark AI tab-open met benoeming van events; mark-spoken voorkomt herhaling.
- [x] **#avatar-functions** ✅ DONE (v4_dnd_001): 7 avatars-as-functions (Het Eerste Licht=begin, De Reaper=einde, Boekhouder=balans, Harry=tijd, Madelief=emotie, Mr Smith=manipulatie, Story Teller=geheugen). Acteren actief in community.
- [x] **#world-state** ✅ DONE (v4_dnd_001): `GET /api/dnd/world-state` aggregeert per-entiteit dominantie over alle users. >60% = `dominant=true` flag (klaar voor aspect-bark trigger).
- [x] **#hyperlink-stats** ✅ DONE (v4_dnd_001): gedrag → identiteit zonder cijfers; behaviors verschijnen als pills op Persoonskaart met kleur-codering.
- [ ] **#persoonskaart** — Persoonskaart UI uitbreiden met **inventory + slots/gewicht** systeem (rugzak/cape/helm/schoenen). Inventory leest uit user-container + KB v2 kaarten met `dnd.type=item` tag.
- [ ] **#body-slots** — Body-slots na Rugzak: helm / cape / schoenen / handschoenen / amulet. Equip-mechanic via D&D-kaart drag-drop. Effect-modifiers op aura.
- [ ] **#particles** — Particles op aura: klok-deeltjes (Harry), runen (Smith), mist (Reaper), confetti (Madelief). Canvas-overlay op gradient-glow.
- [ ] **#auto-bark** — Auto-bark als community reward bij milestone-unlock. Bot kiest passende reactie op basis van event-type.
- [ ] **#aspect-bark** — Aspect-bark bij dominantie (>60% van events in een week). Avatar reageert met spreuk uit lore_index. Hook in `world-state` cron.
- [ ] **#emergent-quests** — Quest-systeem ontstaat **uit gedragspatronen**. Pattern-detector scant behavior-tracker → genereert "Vind de balans"-quest als user 7d veel kb_create + 0 emotie-trigger heeft.
- [ ] **#lore-currency** — Zeldzame KB-kaarten = waarde. Kaart met `dnd.rarity=legendary` + tag `lore/dnd/spark world/base line` telt mee in user-score. Display als trophy-grid.
- [ ] **#dynamic-canon** — Vervormde verhalen: canon herschrijven via community-consensus. Bv. 5+ users met `dnd_choice_horen` → "Horen werd het pad". Vereist 51%-vote in community.

### Cluster H — Stem-laag + Bots
- [x] **#bot-voice** ✅ DEELS DONE (sessie 8): STT/TTS toggles per bot in `auth/admin/bots/{bot_id}/settings` met 6 OpenAI stemmen. Audio-uitspeel hangt nog (TTS settings opgeslagen maar player niet gehookt).
- [ ] **#dnd-voice-cards** — D&D-kaart als spreekkanaal: bot leest kaart-tekst (`vraag` + `antwoord`) voor via TTS. Hook in `cards/service.py::play_card_voice(card_id, bot_id)`.

### Cluster I — Spark World (NL als fantasy-continent)
- [ ] **#sw-nl-base** — **Nederland als fantasy-continent** (basiswereld). Begin met geografische skelet uit Open Street Map → vertaal naar lore-vlakken.
- [ ] **#sw-facties** — **12 provincies = 12 facties** met eigen kleur/wapen/leider. Hook in lore_index als sub-tree.
- [ ] **#sw-the-north** — **Startgebied "The North" — Groningen**. Eerste fase content. Locaties: Stad-Groningen (hoofdstad), Lauwersmeer (mistgebied), Borkum-fjord.
- [ ] **#sw-foto-flow** — **Foto → Fantasy workflow** (asset creator). User uploadt foto → AI genereert lore-asset (Nano Banana / Sora 2). Output landt in system_archive met tag `sw_asset`.
- [ ] **#sw-asset-types** — 4 asset-types: wereldkaart (continent-view) / stad top-down / scene view (1st-person) / NPC avatars. Per type aparte prompt-template.
- [ ] **#sw-realtime-weer** — **Realtime weer-koppeling per regio** (weer.nl per provincie). Voedt sw-weather-mood (#weather-mood is breder).
- [ ] **#sw-realtime-tijd** — **24-uurs realtime dag/nacht sync** (zonsop/zonsondergang per breedtegraad). Beïnvloedt scene-lighting in asset-render.
- [ ] **#sw-char-sheet** — **D&D character sheet UI (Stormhaven-stijl)**: stats / inventory / aura / lore-currency / faction-banner. Vervangt huidige Persoonskaart.
- [ ] **#sw-multi-shop** — **Multi-tenant shop per user** (in-world eigen tab). Reeds: Winkelstraat-hub. Sw-extensie: shop-locatie in fantasy-stad (Groningen-marktplein).
- [ ] **#sw-avatar-tshirts** — **Avatar-T-shirts (on-demand print)**. Roadkill-merch uitbreiden met user-avatar-as-design. Print-on-demand via Printful API (P3).
- [ ] **Per-user GB opslagsysteem** — 1GB standaard, bij te kopen met ROAR/EUR. `users/{user_id}/_meta.json.quota_gb`. Block uploads bij overschrijding. Voedt sw-foto-flow want assets schalen snel.

### Cluster J — Andere
- [x] **#weather-mood** ✅ ROADMAPPED (sessie 8): weer.nl koppeling → cloud/humeur per user. **Niet alleen voor Spark** (universeel). Wachten op user-locatie-veld in profile.
- [x] **#community-plus** ✅ ROADMAPPED: token-tier (1+ token = community member, bot-toegang ∝ wallet). Voorbereid in shop/balance endpoints.

### Volgorde-suggestie cluster G→I (na P0 boekhouding-hooks)
1. **#persoonskaart + #body-slots** — Eerste visuele win (bestaande aura uitbreiden met inventory-grid).
2. **#aspect-bark** — Hook bovenop bestaande `world-state >60%` flag → eerste autonoom-gedrag.
3. **#emergent-quests** — Pattern-detector op bestaande behavior-tracker counters.
4. **#sw-nl-base + #sw-the-north** — Begin klein (1 provincie) als testbed.
5. **#sw-foto-flow** — Pas zodra Nano Banana / Sora budget vast staat (kost credits per asset).
