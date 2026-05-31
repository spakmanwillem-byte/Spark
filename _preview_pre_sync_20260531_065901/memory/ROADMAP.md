# Spark Core 2.0 — Engineering Practices & Backlog

> **Zie ook**: `MISSION.md` voor missie/visie/identiteit/privacy (DNA-laag).

## 🟢 Redeploy-ready check — 2026-05-29 (avond)

### ✅ Sessie 16 (2026-05-29 avond) — Trade-systeem dynamisch & multi-user echt

**🎯 Werkende eindstaat na sessie 16:**
| User | Tokens | Anchors | Trade-pots | Werkend |
|---|---|---|---|---|
| Spark | 10 | 6 (BCH/BTC/ETH/SOL/ADA/ATOM) | 4 vrij | ✅ |
| Willem | 21 | 0 | 21 vrij | ✅ E2E getest |
| Gijs | 2 | 0 | 2 vrij | ✅ E2E getest |
| Roadkill / Lotus / Gerben | 1 elk | 0 | 1 elk | ✅ E2E getest |

**🎯 Bitvavo ↔ Anchors synced (live):**
- Bitvavo €376.55 = €314.01 cash + 6 coin-anchors (BCH €9.96 · BTC €10.03 · ETH €9.92 · SOL €9.91 · ADA €10.05 · ATOM €12.67)
- Som Spark anchors = €62.54 = Bitvavo crypto (exact match)
- ROAR price = €376.53 / 36 = €10.46 per token
- Market Cap = €376.56

**Belangrijkste fixes:**
- [x] 🪙 **ATOM** toegevoegd aan watchlist (6e coin)
- [x] 🔗 **Bitvavo proxy via Spark** (v6_bitvavo_proxy_via_spark_001): non-Spark users zonder eigen keys → fallback op Spark's keys. Trade-log markeert `proxied_via_spark`. Mock-fallback verwijderd.
- [x] 🎯 **Echte fill-prices** (v6_pot_real_price_001): entry_price en close_pot gebruiken Bitvavo's `avg_price` ipv ticker.
- [x] 🎯 **Potje blijft op zijn coin** (v6_pot_market_match_001): `get_available_pot(prefer_market=...)` zoekt eerst potje van diezelfde markt.
- [x] 📊 **Per-user stats** (v6_pot_live_value_per_user_001): non-Spark users zien eigen JSON-aandeel.
- [x] ⚖️ **Token = Potje model** geherbevestigd (sessie 16 evening): 1 ROAR = 1 trade-pot van €10. Capital is claim op gedeelde Bitvavo, niet vastgezette coin. `rebalance_from_bitvavo()` endpoint blijft beschikbaar maar auto-trigger uit close_pot is uit (botste met token-model).
- [x] 🔒 **Lock-enforcement bevestigd**: open/close/get-available respecteren `pot_locked=True`. E2E getest.
- [x] 💰 **Bitvavo Staking adjustment** (v6_bitvavo_staking_manual_001): handmatige veld voor Spaar/Staking-deel (`bitvavo_extras.json`). Endpoint `POST /api/shop/token/bitvavo-staking`. Telt mee in `spark_core_value` en `bitvavo_base_locked_eur`.
- [x] 🔧 **Force-sell endpoint** (v6_force_sell_real_001): doet nu echte Bitvavo SELL voor admin-close.
- [x] 🔧 **Bitvavo amount format fix** (v6_sell_amount_decimals_001): 8-decimal string ipv wetenschappelijke notatie.
- [x] 📊 **Dashboard breakdown**: `bitvavo_cash_eur` + `bitvavo_base_locked_eur` (= coins, groeit met prijs) + `bitvavo_staking_eur` (handmatig).
- [x] 🏷️ **Admin/Analytics bots-view fix**: `pot_count` altijd gezet (was None), markets uit registry overlay (v6_admin_bots_potcount_fix_001 + v6_admin_bots_markets_fix_001).
- [x] 🚫 **Spark auto-fill UIT** (v6_spark_no_autofill_001): Spark krijgt geen automatische 15 base-pots meer. Voorkomt fantoom-potjes.
- [x] 🧹 **Clean Slate '1 juni 2026'**: accounting + financial + wallet + spark_kasboek + roar transactions allemaal op 0. ROAR balances behouden. Capital baseline gereset. Trade-logs gearchiveerd in `data/_backups/clean_slate_1juni_2026/` en `data/_backups/post_user_bot_tests_29mei/`.
- [x] 📥 **Productie-data sync** (sessie 16 morning): 22 users + 36 ROAR + alle relaties uit prod-zip. Backup: `data/_backups/preview_before_prodsync_20260529_180040/`.
- [x] 🐛 **Gerben sync**: user toegevoegd met basis-avatar (gallery:31c6dc04a2fd).
- [x] 🐛 **joel123/Jayden avatar+gradatie sync** uit productie.
- [x] 📈 **Wallet line-chart fluctuatie** (v6_price_chart_density_001): 5-min snapshot interval ipv 1u, ±1% padding, auto-refresh 30s, "+" knop voor manual snapshot, delta-info in header. Snapshot bucket dedupe-bug gefixt (laatste prijs wint).
- [x] 🤝 **5/6 users E2E getest** met echte BUY+SELL via Bitvavo proxy. Spark ATOM-restje was dust (1.47 ATOM < min-order 2.81), administratief gesloten.

**Bekend / aan te scherpen:**
- Bitvavo Staking API direct lezen ipv handmatige veld (kost extra endpoint research)
- Capital-row in stats kan beter splitsen tussen "claim op cash" vs "echte coin-waarde"

**Status**: Stabiel. Klaar voor redeploy.

### ✅ Sessie 15 (2026-05-29, vervolg) — D&D Spark World
- [x] 🎭 **Body Slots** (v6_body_slots_001):
  - Backend: 3 endpoints (`GET /persons/body-slots/config`, `PUT /persons/cards/{u}/{p}/body-slots`, `DELETE .../body-slots/{slot_id}`)
  - 8 slot-types met anatomische posities: head / shoulders / chest / hands / waist / feet / aura / pocket
  - Per slot: label · icon (emoji) · color · note · ts
  - Frontend: `BodySlotsPanel.js` met SVG-silhouet + visuele klikbare slots + edit-modal
  - Geïntegreerd in PersoonsPage expand-view (onder notes, boven verwijder-knop)
  - E2E getest: Lotus krijgt "Houten ketting" in borst-slot → orange glow + legenda
- [x] 🌲 **Spark World "The North"** (v6_spark_world_north_001):
  - Backend: `modules/dnd/spark_world_north.py` — locaties als persistent JSON in `data/dnd/spark_world/locations.json`
  - Seed: **The North** (Groningen base) met 4 sub-locaties (Werkplaats/Tuin/Studio/Kampvuur) + 2 NPCs (De Dood, De Boekhouder)
  - Endpoints: `GET /dnd/spark-world/locations`, `GET /.../locations/{id}`, `POST /.../locations/travel`
  - Frontend: travel-banner in `DnDBarkPanel.js` + lazy-loaded sub-locaties + NPC-chips + senses-hints per plek
  - E2E getest: Spark World modal → Locaties → The North → werkplaats sub-pick → full travel context

**Status**: Stabiel. Geen code-blockers. Wacht op EUR-storting Willem zodat Spark potjes-commitment volledig gedekt is door Bitvavo.

### ✅ Sessie 15 (2026-05-29) — wat gedaan
- [x] 🐛 **Token-buy UI feedback** (v6_token_buy_ux_001):
  - `<Toaster>` globaal gemount in `App.js`
  - Preemptive guard in `WinkelPage.buyToken()`: blokkeert API-call als `qty × price > wallet`
  - 3 zichtbare lagen bij tekort: inline rood waarschuwingsvlak (live met qty), toast rechtsboven, inline error-box
  - E2E: 999 ROAR met €9.18 → alle 3 signalen tegelijk zichtbaar
- [x] 🚀 **Auto-anchor voor nieuwe coins** (v6_auto_anchor_001):
  - `potjes.ensure_anchors_for_markets(user_id, markets)` — Spark-only
  - Gehookt op `POST /api/trade/monitor/markets/{user_id}` → response geeft `anchors_created`
  - Per nieuwe coin: locked anker (€10, `source=auto_anchor_for_new_coin`) automatisch aangemaakt
  - Verified: bestaande coins worden correct overgeslagen
- [x] 🏷️ **KB Curation Dashboard** (v6_kb_curation_dashboard_001):
  - Nieuw component `components/workspace/KbV2TagCuration.js`
  - 6e tab "Tag-curatie" in Kennisbank met 4 stat-tegels (gescand/stammen/dedupe-kansen/sessie-merges)
  - 1-klik merge per stem met variant-dropdown + expand-knop voor alle varianten als chips
  - Sessie-historie van merges onderaan
  - E2E: 52 dedupe-kansen zichtbaar (systeem 377×, relatie 98×, grondstof 87×)
- [x] 💸 **Overflow Auto-Mint instant** (v6_overflow_auto_mint_instant_001):
  - `staking_growth.run_auto_mint_only()` — mint-only loop (geen rente)
  - Direct gehookt in `potjes.close_pot()` voor `user-000`
  - Smoke-test: overflow €25 → 2 potjes gemint + €5 rest, geen 24h-wachttijd meer
  - `close_pot` returnt nu ook `auto_mint: {minted, n_minted, overflow_after}`
  - Daily scheduler-hook behouden als safety-net
- [x] 🎨 **UI Theme refactor — Amber/Orange** (v6_spark_theme_001):
  - CSS-variabelen in `index.css`: `--spark-primary/-hover/-soft/-ring/-secondary/-accent`
  - Utility-klassen: `bg-spark-primary`, `text-spark-primary`, `border-spark-primary`, `ring-spark-primary`
  - 23 frontend files gepasseerd: cosmetic chrome (buttons, focus-rings, upload-chrome, link-hovers) van purple/blue → amber
  - Bewust intact: mood-glow palet (semantische emotie-kleuren), status-indicators (paused/mock = blauw), chart-distinctions, module-color-coding in AnalyticsPage, layer-kleuren in EmotiesPage/SparkBrainPage
  - Dashboard + KB Curation getest, geen visuele regressie

### ✅ Sessie 14 (2026-05-28/29) — wat gedaan
- [x] 🐛 KB v2 legacy media routes hersteld (path-traversal guard)
- [x] 🧹 Disk cleanup 615 MB
- [x] 🔄 KB v2 sync uit productie (42 verhuisde kaarten)
- [x] 🔤 Tag-normalizer (45 dedupe-kansen, 5 endpoints)
- [x] 🧠 SPARK AI sidebar restructure (geen dubbele tabs)
- [x] 🦅 Spark Brein-overzicht dashboard (6-kaarten helikopter-view)
- [x] 🐛 `/api/trade/stats/*` HTTP 500 (float vs dict fix)
- [x] 🐛 Quick-buy €5.08 → €10 (capital als bron)
- [x] 🐛 Open potje amount_eur backfill (11 gefixed)
- [x] 🐛 Winkelstraat avatar/logo (gallery: prefix resolve)
- [x] 🔒 Lock-bug defense-in-depth (open+close+distribute)
- [x] 🏗️ Spark 5 anchor pots (1 per coin) + hernummering pot-001..015
- [x] 🎨 Locked potjes onderaan UI (sort-key)
- [x] 🐛 €43.25 fix (growth-distortion in live_value)
- [x] 🐛 Snel Handelen panel (skip locked + capital + refresh 10s)
- [x] 🐛 Ghost-anchors Willem + Gijs verwijderd (alleen Spark hoort anchors te hebben)
- [x] 🐛 Ghost-positions Willem (6 fake OPEN → cleared)
- [x] 🐛 Auto-lock hook beperkt tot Spark (was bug die anchors bij iedereen herstelde)
- [x] 🐛 Willem coin-balance 3-1-2-2-2 → 2-2-2-2-2 symmetrisch
- [x] 📋 7 bugs.json afgevinkt met resolution-tag
- [x] 📈 ROAR price-history snapshots + scheduler-hook (1×/uur)
- [x] 📜 Disclaimer uitgebreid (5 nieuwe secties: privacy/werking/eigendom/transparantie/aansprakelijkheid)
- [x] 💰 **6 Boekhouding-hooks gecentraliseerd** (v6_accounting_hooks_001):
  - `modules/accounting/hooks.py` met 6 idempotente helpers (tx_ref-based)
  - Hook 1: ROAR token-buy → income spark_core (gift/sales o.b.v. anker/klant)
  - Hook 2: Bitvavo coin-buy → expense spark_core (Materiaal)
  - Hook 3: Sell-back → expense spark_core (Refunds)
  - Hook 4: Shop verkoop → income shop-kasboek + 2% commissie naar spark_core
  - Hook 5: Tikkie deposit → income personal_<naam>
  - Hook 6: Trade SELL resultaat → income/expense Crypto Profit
  - Aanroepen toegevoegd in `shop/routes.py` (token-buy/sell-back/shop-sale), `trade/potjes.py` (open_pot+close_pot), `wallet/tikkie.py` (confirm)
  - Stille-fail mode: hook-error blokkeert nooit een product-actie
- [x] 🌱 **Staking Growth Engine** (v6_staking_growth_engine_001):
  - `modules/trade/staking_growth.py` — 3-in-1 module
  - Auto-rente: 1.5% per anchor per maand uit overflow_pool (30-dag interval)
  - Auto-mint: bij overflow >= €10 → nieuw trade-potje
  - Auto-anchor: `POST /auto-anchor` voor nieuwe coin (alleen Spark, idempotent)
  - 3 endpoints: `/trade/growth/run`, `/trade/growth/status`, `/trade/growth/auto-anchor`
  - Scheduler-hook dagelijks check (intern 30-dag rente-interval)
  - **Live getest**: €25.50 overflow → 5 anchors +€0.38 elk + 2 mints + €3.59 rest. Reset naar clean state.
- [x] 📅 **Boekhouder weekrapport** (v6_boekhouder_weekrapport_001 + v6_weekrapport_token_holders_001):
  - `modules/boekhouder/weekly_report.py` — verzamelt anchor-groei + overflow + mints + trade-PnL + ROAR-activiteit
  - Stuurt zondagavond 20:00-22:00 UTC een PM naar admin met human-readable rapport
  - **+ Alle ROAR token-houders krijgen PM** (idee Willem): bot stuurt rapport aan iedereen met >=1 token, holders voelen de groei van hun investering zonder app-bezoek
  - Projectie: "Bij dit tempo verdienen anchors zichzelf in N maanden terug"
  - 3 endpoints: `/preview` (UI), `/run` (admin-trigger met `also_token_holders` toggle), `/history`
  - History archief in `data/boekhouder/weekly_reports.json` (max 200 entries = ~4 jaar) + recipients-tracking
- [x] 🛍️ **Token-koop via shop referral** (v6_shop_referral_token_001):
  - `BuyTokenRequest.via_shop_id` optionele parameter
  - Als ROAR via een specifieke shop wordt verkocht (bv. Roadkillshop), krijgt die shop **2% commissie** in z'n eigen kasboek (`Referral`-categorie)
  - Alleen voor klanten, niet voor anker-aankopen (die zijn fundering)
  - Stille-fail (non-blocking)
- [x] 📜 **Disclaimer v6.2** — `staking_growth` sectie + `nieuw_sessie14` shop-referral & holder-newsletter

### Conceptueel kader (uit deze sessie)
- **Emotie Detectie** (`/spark/emotions`, iedereen) = "Wat voelt user nú?" → 4 emoties (blij/boos/bang/bedroefd) + state + test
- **Emotie Routering** (`/spark/routering`, admin) = "Hoe reageer ik?" → 7 lagen → behavior_class (begrenzen/vertragen/exploreren/kalmeren)
- Niet duplicaat, maar gestapelde ketting (hybride-by-design, niet bipolair)

### Token-balans (live, ongewijzigd)
| Wie | Tokens | Betaald (cash in) | Rol |
|---|---|---|---|
| Spark (user-000) | 10 | — | Anker / fundering |
| Willem (user-001) | 10 | €50.80 | Anker / fundering |
| Gijs (user-a0ee2d7e) | 2 | €20.80 | Klant (gift-fase, 0% BTW) |
| **Totaal circulating** | **22** | **€71.60 cash in** | |
| Spark treasury | 999,978 | — | Pool |

### Bitvavo & potjes-status (sessie 16, na rebalance-from-bitvavo)
- Bitvavo live crypto: **€90.50** (BCH €20 / BTC €20 / ETH €10 / SOL €10 / ADA €20 / ATOM €10)
- Bitvavo EUR-cash: ~€245
- Spark commitment: 6 locked anchors = **€10.50** (BCH €0.01 / BTC €0.10 / ETH €0.21 / SOL €0.16 / ADA €9.90 / ATOM €0.12)
- Willem trade-pots: 8 × €10 = **€80** (2 BCH / 2 BTC / 1 ETH / 1 SOL / 1 ADA / 1 ATOM)
- **Som potjes = Bitvavo crypto: €90.50 ✅** (exact match)
- ROAR-prijs-formule: `Bitvavo balance ÷ circulating` — past zich auto aan bij elke storting
- Auto-rebalance triggert na elke `close_pot()` → systeem houdt zichzelf in sync

### Wat live werkt (smoke-checked, mag op productie)
- Bitvavo trading LIVE — alle user-bots via Spark's keys (proxy fallback, sessie 16). Echte fills uit Bitvavo `avg_price` voor entry/exit op potjes.
- Multi-user bots: Spark + Willem + Gijs + Roadkill + Lotus + Gerben (5 users met tokens kunnen autonoom traden)
- ROAR economy v6 (gift-fase, 0% BTW, dynamic price)
- Boekhouding 4 entiteiten (Spark Core / Zorgboerderij / Roadkill Merch / Privé Willem) met BTW-summary + reconcile + retroactief fix-endpoint
- Tikkie-storting flow (user→admin PM→confirm→wallet bijschrijven + auto-archief in admin's bestanden)
- Winkelstraat hub met owner-shop-isolation (`shops/{shop_id}/products.json`)
- 8 capabilities + 17 in chat-router (5 executable, 12 met handlers ready)
- Synapse auto-documenter (90 containers, 419 endpoints, 78 actief, 12 skelet, 59 blueprints)
- KB v2 hooks-laag (5 hooks live: vocab/tell-layer/verbanden/dnd-link/voice-snippet)
- KB tag-normalizer met 45 dedupe-kansen geïdentificeerd
- @traced observability (auth/login + logout, trade buy/start/stop, shop-gift, kbv2 mutations)
- 21:00 Boekhouder roundup-bark + Madelief error-pointer (5-min scheduler)

### Open P0 (niet blocker voor deploy, mag erna)
- [ ] 6 Boekhouding-hooks centraliseren (token-buy / bitvavo coin-buy / sell-back / shop-sale / deposit / trader-result → automatisch posten op `/api/accounting/transactions`)
- [ ] Legacy `spark_kasboek.json` schrijfpaden uitfaseren (alleen-lezen + migratie-script)

### Open daarna (P1+)
- [ ] **📚 Help + Commands update + spliten** (afgesproken, sessie 15):
  - Bestaande `help_g{n}.json` per gradatie staan nog niet voor v6-features (staking-growth, weekrapport, shop-referral, 5 anchors, tag-merge, ...)
  - Plan: split per module-area (trade-help / shop-help / kb-help / boekhouding-help) ipv 1 grote per-gradatie file
  - Auto-gegeneer uit command_registry tags
  - Cluster D #cmd-gradatie-files + #cmd-grad-lock + #cmd-priv-fallback bouwen hier verder op
- [x] ✅ 1-klik UI **#kb-curation-dash** bovenop `/api/kb/v2/tags/scan` (sessie 15, v6_kb_curation_dashboard_001)
- [x] ✅ **🌱 Staking Growth Engine** (sessie 14 + sessie 15 instant-mint):
  - [x] Auto-rente uit overflow_pool → anchor.capital groei (sessie 14)
  - [x] Auto-mint bij `overflow_pool >= €10` (sessie 14, daily) + **instant na elke close_pot** (sessie 15)
  - [x] Auto-create base-anchor bij toevoegen nieuwe coin aan watch (sessie 15, v6_auto_anchor_001)
- [x] ✅ **🎨 Unified Theme Engine** (sessie 15, v6_spark_theme_001 — eerste pas):
  - [x] CSS-vars in `index.css` (`--spark-primary`, `--spark-secondary`, `--spark-accent`, ...)
  - [x] Sweep cosmetic chrome `bg-purple-/bg-blue-/focus:border-purple-` → `bg-amber-/focus:border-amber-` in 23 files
  - [x] Semantic colors (mood/status/charts) bewust intact gelaten
  - [ ] Nog te doen (v2): ThemeContext per section, user-override in Settings, light/dark-mode voorbereiden
- [ ] Tag-merge auto-fire optie in `classify_card` (opt-in flag)
- [ ] Exception-list uitbreiden bij volgende false-positives
- [ ] 2 endpoints uitbreiden (`/spark/disclaimer.leidende_lagen_counts.bijbel + capabilities` + `/kb/v2/stats.inbox.count`) zodat overzicht alle cijfers heeft i.p.v. `-`
- → Zie clusters A-J hieronder voor volledige backlog

---


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
5. **#trigger-hooks** + **#trigger-community** (gemeenschap-uitbreidbaar)
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
6. **#sw-char-sheet** — Vervang Persoonskaart pas als alle data-streams er zijn.

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
