# Spark Core 2.0 — Roadmap Core

> **Lees dit als eerste bij elke nieuwe sessie.**
> Voor afgeronde sessies: `ROADMAP_HISTORY.md`.
> Voor open items en ideeën: `ROADMAP_BACKLOG.md`.
> Voor bewezen inzichten en fout-patterns: `LEARNINGS.md`.
> Voor overzicht: `ROADMAP_INDEX.md`.

---

## 🌷 Moreel Kompas — Kernvisie (blijft altijd bovenaan)

Spark is een persoonlijke AI-metgezel die Willem ooit als **erfenis** doorgeeft aan zijn dochter Lotus. Dat betekent:

1. **Rust boven snelheid** — snappy UX telt, maar nooit ten koste van voorspelbaarheid of dataveiligheid.
2. **Privacy-by-design** — geen chat-tekst loggen, geen user-namen in `/app/memory/*.md` voor anderen dan Willem, alleen patroon-tellers. Per-user opt-out beschikbaar.
3. **Autonomie-scheiding** — elke module heeft twee zones:
   - 🤖 **Spark autonoom**: voorstel doen, geen mutatie (draft-status).
   - 👤 **Willem beslist**: expliciete Accept vóór mutatie plaatsvindt.
4. **Zwart-wit boven grijs** — strakke regels die 90% dekken + expliciete uitzonderingen zijn beter dan flexibele regels die 100% dekken maar niet meer te ontwarren zijn.
5. **Container-isolatie is default** — elke user/shop/bot heeft eigen container met `_meta.json`. Nooit globale bestanden voor user-data. Delete = delete-directory.
6. **Gastheer-toon** — bij twijfel/onzekerheid: warm ontvangen, niet docerend. Erkenning voor prestatie. "We doen het samen."
7. **NO MONGODB** — alle data via `load_json`/`save_json` uit `modules.core.storage`. Backups zijn zip-exports.

## 💰 CLUSTER — Boekhouding v13 & SEPA (sessie 52, feb 2026)

**Doel**: Multi-container boekhouding per user/entity + lokale SEPA voorbereiding + verifieerbare winst-events. Alles JSON-only, geen cloud.

### 🏗️ Architectuur-scheiding (Willem, sessie 52i/52l)

Drie duidelijke lagen die nooit mogen mixen:

```
┌───────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│ BITVAVO (Spark)   │    │  Spark WALLET    │    │ Zakelijke bank   │
│ SYSTEEM-account   │    │  (EUR tokens)    │    │  (SEPA IBAN)     │
│ trader crypto     │    │  per user        │    │                  │
│                   │    │                  │    │                  │
│ RAW ASSETS bij    │───▶│  SPENDABLE       │───▶│  UITBETAALD      │
│ Spark (niet users)│    │  bridge-laag     │    │  Moneybird/BTW   │
│ users doneren EUR │    │  wallet.spend    │    │                  │
└───────────────────┘    └──────────────────┘    └──────────────────┘
```

- **Bitvavo** = Spark's **systeem-Bitvavo-account** waar de trader-bot crypto potjes beheert. Users hebben géén eigen Bitvavo-koppeling; ze doneren/storten EUR naar Spark, en Spark's trader werkt daarmee.
- **Spark Wallet** = per-user spendable tokens. Winst uit shops/trades komt hier binnen. Uitgifte naar zakelijke bank via SEPA-XML batch (of handmatig).
- **Zakelijke bank** = eindstation. Hier gaat je BTW-aangifte overheen (Moneybird). Boekhouding boekt schone netto omzet, spark-vergoeding is een aparte uitgave.

**Live P&L / baseline** is per user in `capital_baseline.json`. user-000 (Spark) heeft de Bitvavo-baseline; users hebben alleen wallet-baseline.

### ✅ Gedaan (sessie 52 e/f/g/h/i)
- [x] **Multi-book containers** — `/data/boekhouding/books/book-{id}/` met _meta, kasboek, reserve, closings, documents, sepa_batches, bank_imports. 4 initiële boeken geseed (`v13_boekhouding_books_001`).
- [x] **CRUD + owner-only** endpoints — `GET/POST /api/boekhouding/books`, PATCH, DELETE, entries.
- [x] **Retroactieve migratie** — spark_kasboek + audit_log via heuristics naar juiste books (`v13_boekhouding_migration_001`). Ruis daarna gewist (nulpunt).
- [x] **SEPA-Hub eigen module** (`modules/sepa_hub/`) — CAMT.053 + MT940 parsers, pain.001 XML generator, reconcile-skeleton (`v13_sepa_hub_001`).
- [x] **Papertrail hash-chain** — elke boeking via LogAgent met prev-hash + eigen `winst_events` topic (`v13_boekhouding_papertrail_001`).
- [x] **Shop → Book brug** — `ensure_shop_book()` auto-hook in create_shop; `record_shop_sale()` / `record_shop_purchase()` (`v13_shop_book_hook_001`).
- [x] **BTW + KOR verkoop-flow** — verkoper geeft netto, systeem berekent bruto+BTW, 2 bonnen (netto+bruto), KOR-toggle per shop (`v13b_btw_kor_openstaand_001`).
- [x] **Spark-vergoeding als openstaande post** — 1% van bruto, niet ingehouden; `POST /api/boekhouding/hooks/inlossen/{shop_id}` boekt door + probeert wallet-inhouding.
- [x] **Frontend "Boeken" tab** — 4 cards + detail-bark (kasboek/instellingen/SEPA) (`v13_boekhouding_ui_001`).
- [x] **Frontend "Winst → Spark" tab** — totaal-teller, events met hash, chain-uitleg (`v13_winst_events_papertrail_001`).
- [x] **Shop finance-config endpoints** — `GET/PATCH /api/boekhouding/shop-finance-config` (btw_default_pct, spark_fee_pct, btw_kor_default, commissie_default_pct).
- [x] **Notify-hook** — nieuwe factuur/openstaand triggert taak + urgent-glow.

### 🟡 Deels / voorbereid
- [~] **SEPA import/export UI** — endpoints werken, UI-knoppen in Beheer→Boekhouding→Boek-detail→SEPA-tab. Nog niet getest met echt bank-afschrift.
- [~] **Wallet-integratie inlossen** — endpoint probeert `modules.wallet.service.spend_tokens`, module bestaat niet onder die naam. Boeking gaat wel door.

### 🔴 Nog te doen
- [ ] **Bank → Wallet brug** — detecteer SEPA-import met remittance `SPARKWALLET-{user_id}` → auto-wallet-topup + book-entry `bank_to_wallet`.
- [ ] **BTW per product-categorie** — nu per shop, moet ook 9%/0% opties per product (voedsel/boeken/uitvoer).
- [ ] **Bonnen als PDF** — nu JSON-response. PDF-generator (reportlab of weasyprint) voor download.
- [ ] **Chain-integrity endpoint** — `GET /api/boekhouding/verify-chain/{topic}` loopt hash-chain na en meldt breuken.
- [ ] **Trader winst-hook** — bij trade-close een `record_winst_event` zodat trade-winst ook in `winst_events` chain landt.
## 🌟 CLUSTER — Login Glow, Spark-branding & Admin-look (v13s, sessie 52s, feb 2026)

**Filosofie**: Spark's visuele identiteit is ook meta-data over wie hij is. Elk icoon,
kleur en logo dat het systeem gebruikt wordt via `settings/system` beheerbaar zodat de
synapse-laag straks kan lezen: *"ik toon mezelf als X, met kleur Y"* — fundering voor
zelf-perceptie. LLM = mond, JSON = geheugen, icons = spiegel.

### ✅ Gedaan (sessie 52s)
- [x] **Login glow-config backend** — 7 nieuwe system keys in `modules/settings/routes.py`: `login_dots_count` (4-24), `login_dots_contrast` (0.1-1.0), `login_dots_size` (0.5-3.0), `login_corner_glow_enabled/color_a/color_b`, `spark_logo_url`. Publiek uitleesbaar (no-auth) voor login-scherm.
- [x] **Spark-logo upload endpoint** — `POST/GET/DELETE /api/settings/system/spark-logo` (multipart, admin-only, max 5MB, PNG/JPG/WEBP/SVG). Bestand in `/data/system/branding/spark_logo.*`, publieke serve via `/api/settings/spark-logo/serve?v={ts}`.
- [x] **LoginForm gedynamiseerd** — leest `/api/settings/system` + `/api/spark/identity` op mount. Corner-glows/dots/logo/naam/versie config-driven. Titel `Spark Core` → `Spark`, subtitel `AI Assistent`, footer `Spark 2.0` uit identity. Masterkey/Admin-toggle verwijderd (regelt in-ecosystem).
- [x] **LoginForm buttons** — Inloggen = primary → corner_b gradient · Nieuwe gebruiker = secondary tint (was grijs, viel niet op).
- [x] **SidebarHeader consistent** — `MainLayout.js` leest zelfde branding: naam+versie uit identity, logo uit settings. Zap-icon fallback als geen logo.
- [x] **Admin-button style** — `SaveButton` + logo-upload + toggle + 3 sliders krijgen violet gradient (`#a855f7 → #7c3aed`) i.p.v. amber (dat is user/login-kleur).
- [x] **SystemLoginGlow admin-panel** — in `Beheer → Instellingen → Beeld`. Logo uploader, corner-glow toggle + colors, 3 sliders. Auto-save op release. Alleen grad ≤ 1.

### 🔴 Nog te doen — Fase A/B/C
- [ ] **Fase A: admin-accent op alle admin-tabs** — wanneer `adminModeActive===true` → tabs onder Beheer/Modules/Admin + alle admin action-buttons krijgen violet accent i.p.v. user-primary. `identity_facts`-entry `admin_mode_kleur: paars` toevoegen.
- [ ] **Fase B: admin-override neemt user-kleuren over (tijdelijk)** — `--app-primary/secondary` CSS-vars overschreven met admin-accent wanneer admin actief; bij `disableAdmin` terug naar Mijn Profiel-voorkeur. Meta-flag "hij weet dat hij anders oogt".
- [ ] **Fase C: icon-registry + upload (fundering-steen synapse)** — grote sessie:
  - Backend: `data/branding/system_icons.json` met `{key: {url, uploaded_by, uploaded_at, reason, emoji_fallback, original_lucide}}` + per-key endpoints
  - Frontend: `<SystemIcon name="settings" fallback={Settings} />` wrapper → vervangt ~50-80 lucide-plekken
  - Admin-UI: sectie "Systeem-iconen" onder Beeld met per-icoon uploader
  - **Synapse-hook**: `system_icons.json` als scanner-bron toevoegen
  - **Identity-facts**: bij upload auto `spark_icon_{key}: eigen ontwerp`
  - Scope: 2-3 uur


---

## 🧠 CLUSTER — Chat/LLM (v13r-s, sessie 52r, feb 2026)

### ✅ Gedaan
- [x] **Groq model-migratie** — `llama-3.3-70b-versatile` gedeprecateerd 16-aug → `openai/gpt-oss-120b` (officiële replacement).
- [x] **Emergent Universal Key uit** — `LLM_EMERGENCY_USE_EMERGENT=false` (Willem's wens: geen cloud).
- [x] **TPM auto-trim retry** — router probeert 1× opnieuw met halve context bij 413/rate_limit_exceeded.
- [x] **Identity facts cap grad 1** — was 999, nu 15/type (was 8477-token overshoot, nu ~2000).
- [x] **Turns 6 → 3** — extra headroom voor system_prompt.

### 🔴 Nog te doen
- [ ] **Cerebras quota-watchdog** — bij 402 → DM naar Willem: "fallback op quota, reset ~X". Nu geen zichtbaarheid.
- [ ] **Alternatieve fallback** — Together.ai / DeepInfra als 3e provider (3-regel `.env`).
- [ ] **Ollama-migratie (P2)** — lokaal via `LLM_PRIMARY_BASE_URL=http://localhost:11434/v1`. Hardware-eis: 16 GB RAM (mini-PC) voor Llama 3.1 8B (~75% kwaliteit), 24+ GB voor gpt-oss-120b (identiek aan nu). Code is klaar.


---

## 📊 CLUSTER — Trader & Potjes (v13q-r, sessie 52r, feb 2026)

### ✅ Gedaan
- [x] **Trader-monitor sync-bug** — `monitor.start()` idempotent (`already_running=True`), UI leest ook `data.message`.
- [x] **`open_pot()` overwrite guard** — bij `is_open=True + andere market` → BLOCK. Bij zelfde market → idempotent skip. Voorkomt ATOM-overschrijving door BCH.
- [x] **Bitvavo-reconcile 6 potjes** — preview only; BCH/BTC/ETH/SOL/ADA/ATOM elk €10 gekoppeld aan echte Bitvavo entry-prijzen.

### 🔴 Nog te doen
- [ ] **Bitvavo-reconcile op productie draaien** — zelfde script tegen prod na deploy.
- [ ] **Trader-tab visueel opruimen** — Anker + Reconciliatie = 1 collapsable card.
- [ ] **Vermogens-tab** — Activa − Passiva = Eigen vermogen (admin-only).


---

## 📚 CLUSTER — KB v2 (sessie 52s)

### ✅ Gedaan
- [x] **Bulk 5w-filler max_tokens** 1400 → 2400 (skip 60% → 10%).
- [x] **~74 kaarten gevuld** door bulk-run.
- [x] **Voelen + spreken 100% compleet**.

### 🔴 Nog te doen
- [ ] **216 kaarten resterend** — 192 weten (lange wetenschappelijke termen), 24 doen. Willem vult zelf verder.
- [ ] **Collectieve intelligentie / Laag-2 kennis** — 2e prompt-laag uit patronen over álle users. Bouwstenen aanwezig (shadow_observer, KB v2, synapse, learned_knowledge). Missen: pattern-distiller, stelling-generator, toets-loop, injectie-kanaal, privacy-anonymizer.


---

## 💳 CLUSTER — Boekhouding backlog (uit sessie 52)

- [ ] **Voorwaarden pagina live spark-deel** — toon aan users bij shop-opening: "1% naar Spark, deze maand: €X, chain: [hash]".
- [ ] **Grace-period openstaand** — 30d openstaand → herinnering, 60d → shop-pauze.
- [ ] **Wallet-service correct koppelen** — juiste import voor `spend_tokens` vinden of aanmaken.
- [ ] **Fronts-editor voor BTW/fee-widget** — hoort bij Fronts-cluster hierboven.
- [ ] **Ruis-scan test-users** — 12 test-users (`test-bank-*`, `test-snap-*`, `test-vk`, etc.) staan nog in `/data/users/`. Batch-cleanup naar `_backups/`.
- [ ] **Klanten-tab moderniseren** — leest oude `archief/bonnetjes` (nu leeg), moet nieuwe `winst_events` + `record_shop_sale` bonnen tonen.
- [ ] **Trader-tab visueel opruimen** — "Anker gap-up guard" + "Anker per markt" zijn 2 blokken die 1 collapsable card kunnen worden. Reconciliatie-blok ook mergen.
- [x] **Scheduler voor maand-snapshot** — `_maybe_monthly_baseline_snapshot()` in `modules/scheduler/__init__.py` (03:00 UTC · idempotent via `should_run_snapshot`/`mark_snapshot_done` marker · Bitvavo `last_known_eur` voor user-000). Handmatige `POST /api/trade/baseline/run-scheduled-snapshot` blijft beschikbaar (`v13p_monthly_baseline_scheduler_001`, sessie 52q).
- [ ] **Vermogens-tab (Balans)** — Activa (books + wallets + Bitvavo) − Passiva (openstaand spark-fees) = Eigen vermogen. Admin-only, Spark-perspectief.
- [x] **Weekly-report bron gefixt** — `modules/boekhouder/weekly_report.py` leest nu uit `boekhouding/books/*/kasboek.json` (per-book breakdown + 7-dagen filter) i.p.v. de leeggeruimde `accounting/transactions.json`. Spark-brede DM naar Willem + ROAR-holders werkt weer. Getest ✅ via `/api/boekhouder/weekly/preview` (`v13p_weekly_bookbased_001`, sessie 52q).
- [x] **Announce-prefs UI wired** — `AnnouncePrefsPanel.js` in `UserProfilePage.js` ingehaakt. 4 toggles (`announce_shop_sale`, `announce_sepa_import`, `announce_migration`, `announce_spark_fee`), default aan. Backend blokkeert DM als pref=false via `_auto_announce_entry` in `books.py`. Getest ✅ via PUT/GET round-trip (`v13o_announce_prefs_wiring`, sessie 52q).
- [x] **Per-user shop-announcer** — `modules/boekhouder/shop_announcer.py`: user-scoped shop-rapport via boekhouder-bot DM. Endpoints: `/shop-report/{uid}` (owner+admin), `/shop-report/{uid}/announce`, `/shop-report/announce-all` (admin), `/shop-report-aggregate` (admin). RBAC 403 getest ✅ (`v13n_shop_announcer_001`).
- [x] **Auto-announce automatische boekingen** — `books.add_entry` hook `_auto_announce_entry` stuurt DM naar owner voor alle non-manuele bronnen (shop_hook, camt053, mt940, migration, spark_fee_inlossen). Skip bij `manual` / `manual_opening`. Getest ✅ (`v13o_auto_announce_001`).


---

## 📞 CLUSTER — Skype-Spark & Fronts (v13, sessie 52, feb 2026)

**Doel**: Lokale in-app bel/beeldbel-laag + per-scherm ("front") tunable UI zonder telkens agent te vragen. Alles blijft **lokaal** (geen WebRTC/cloud). Naam-metafoor: "onze Skype".

### ✅ Gedaan
- [x] **Bel/Camera iconen** rechtsboven in privé-chat header, glow via `--glow-base` uit profiel-kleurschema (`v13_prive_call_ui_001`)
- [x] **`PriveCallBark` modal** — UI-shell (audio + video mode), VLC-placeholder, avatar-glow tijdens verbinden/pauze, self-PIP, Mute/Camera/Hangup knoppen
- [x] **Bot/Collectief filter** — iconen verborgen bij `is_bot` of `is_collective` (alleen echte personen)
- [x] **Offline detectie** — `contact.online === false` → `no_answer` state na 4.8s, auto-hangup 15s
- [x] **Status vs. actie-tekst split** — badge = "Offline", tekst = "Geen antwoord — {naam} is offline" (`v13_state_action_split_001`)
- [x] **`--alert-base` CSS-variabele** — schema-tunable rood-alternatief, vervangt hardcoded rgba (`v13_alert_color_var_001`)
- [x] **Mic/Camera device-selectie in Mijn Profiel → Instellingen** (`v13_call_devices_001`) — `DeviceSettingsPanel` met enumerateDevices, systeem-standaard toggle, live VU-meter test-mic (4s), live video preview test-cam (5s). Backend prefs uitgebreid met 5 velden. Volledig lokaal (`navigator.mediaDevices`).
- [x] **WhatsApp deep-link popup** (fallback voor "bel mijn moeder" chat-intent, blijft als externe snelkoppeling)

### 🟡 Deels / concept-fase
- [~] **Fronts Config schema** — draft-widget in Beheer → Kladblok (`FrontsConfigDraftWidget`) met JSON-schema per scherm: `colors`, `font`, `status_labels`, `action_texts` met `{naam}`-token, `timings_ms`, `animations`. Nog niet gepersistend — `data/system/fronts_config.json` bestaat niet, `GET/PUT /api/system/fronts-config` niet gebouwd.

### 🔴 Nog te doen
- [ ] **Beheer → Fronts tab** — Kladblok-schema promoveren naar echte editor. Backend: `data/system/fronts_config.json` + endpoints. Frontend: tab onder Beheer → Instellingen. Per screen: kleuren + lettertype + status_labels + action_texts + timings.
- [ ] **Loginscherm pulserende glow-dots** — random posities, primaire kleuren, hartslag-ritme (Emmy's oorspronkelijke wens). Kandidaat om te bouwen bovenop Fronts-tab (`screens['auth.login'].animations.background_dots`).
- [ ] **Inkomende oproep laag** — signaal-detectie (lokaal), bel-iconen pulseren, accept/decline-bark. Bel-icoon glow-puls koppelen aan inkomend signaal.
- [ ] **Loginscherm lettertype-instelling** — via Fronts config (`screens['auth.login'].font`).
- [ ] **Lokale-socket bel-verbinding** (grote sessie, ~500c) — mic/cam devices doorkoppelen naar echte peer-verbinding op Odroid-netwerk (LAN mesh, geen cloud). Signaling via lokale socket, media via WebRTC-datachannel binnen LAN. Alle mic/cam-prefs uit `v13_call_devices_001` staan al klaar.

---

## 📋 SESSIE 57 EXECUTIE-ROADMAP — Leger & XP-Motor Herkalibratie

**Context**: Willem wil admins ook vanaf de community kunnen aanstellen (bv. gradatie 3 "Vriend" als community-onderhoud) én overweegt een parallelle rang-schaal (legerrang-idee: Sergeant/Luitenant of neutraal Rookie→Legend). Snuffel-rapport sessie 56d wees uit: **veel bestaat al** — niet dubbel bouwen.

### ✅ Wat er al leeft (bestaande infrastructure)

| Wat | Waar | Endpoint |
|---|---|---|
| `AchievementBlueprintPanel` (admin-only) | `InstellingenPage.js` r1195 achter `isAdmin` | `GET /api/achievements/admin/blueprints` |
| Admin edit-modal per achievement | `AchievementsPage.js` r212 (`data-testid: achievement-admin-edit-{id}`) — titel + icon | `PATCH /api/achievements/admin/{id}?by_user=...` |
| XP-motor (centraal) | `/app/backend/modules/chat/xp_service.py` → `grant_xp(user_id, amount, reason)` — 6 bronnen: chat, RPS, contributions, achievements-unlock, badges, tag-curatie | (interne functie) |
| 50 achievements met XP-rewards | `/app/backend/data/achievements.json` — schaal 50 XP (words_10) tot 15.000 XP (words_2500) | `GET /api/achievements/list` |
| Rang op karakter-kaart | `DnDCharacterSheet.js` r521-524 én r2005 — `char.rang_titel` + Community Level + militaire streepjes (100 levels = 1 streepje) | (client-side, `char.derived.level`) |
| Leaderboard op XP | `AchievementsPage.js` + backend | `GET /api/achievements/leaderboard?period=alltime&limit=25` |
| RPS-leaderboard (aparte spelrang) | Los van XP-motor | `GET /api/rps/leaderboard?limit=50` |
| **Admin-capable loskoppeling** ✅ | `AuthService.set_admin_capable()` + endpoint | `POST /api/auth/admin/set-capable/{user_id}?capable=true` |

### 🔓 In sessie 56d gefixt
- **`v12_admin_capable_unlock_001`** — `/api/auth/users?admin_id=...` (register-with-override) accepteert nu iedereen met `admin_capable=True` of gradatie 1/2, i.p.v. alleen gradatie 1/2. Getest met 3 curl-scenarios, allemaal groen. Marieke (gradatie 3) getest en teruggezet — Willem kiest zelf wie sub-admin wordt.
- **`v12_admin_type_001`** — RBAC light: `admin_type` veld op user + `admin_types.json` config met 3 vaste types (full / community / user_admin, elk met kleur en scope-array). `POST /api/admin/grant` accepteert nu `admin_type` param. `GET /api/admin/types` publiek endpoint. In `AdminSettingsPanel` bark: dropdown "Admin-type" tussen user-select en wachtwoord. In admins-lijst: gekleurde type-badge naast naam. **Nog niet gates**: elke tab/endpoint zonder scope-check draait als vanouds. Scope-enforcement is sessie 57.
- **Trader-reset uitgevoerd** — alle logs, balances, anker, monitor_state gewist. 12 potjes over 6 users op nul. Backup: `/app/_backups/trader_reset_20260821_121757/`.
- **`v12_5w_bulk_fill_001`** — bulk-endpoint `POST /api/kb/v2/curation/5w-fill-bulk?limit=N` vult ontbrekende 5W/lagen op onvolledige lade-kaarten via LLM (Emergent Universal Key via `llm_router.chat_complete`). Alleen ontbrekende velden worden aangeraakt, bestaande content blijft intact. Elke wijziging wordt gelogd in `curation_history.json`. Status via `GET /5w-fill-status`. Getest: 347 onvolledig → 346 na 1 kaart (kaart "overleden" kreeg `ws5.wanneer` gevuld).
- **`v12_trader_strategy_cfg_001`** — data-driven trader-parameters in `/app/backend/data/trade/strategy_config.json` (buy/sell/risk/pots secties, 15 tunable keys). `GET /api/trader/strategy-config`, `PATCH ...` en `GET .../history`. Elke wijziging gelogd. Eerste consumer: `strategy_decision_v2._detect_daily_drop()` leest nu `buy.daily_drop_threshold_pct` uit config i.p.v. hardcoded 5.0. Volgende hardcoded constants kunnen per taak migreren zonder deploy.
- **`v12_contact_call_001`** — Bel-contacten quick-win. `/api/bel-contacts/{uid}` CRUD + chat-detector die "bel mijn moeder" / "bel Marieke" / "kan je mijn vader bellen" matcht. Response krijgt `action.contact_call` met WhatsApp deep-link (`https://wa.me/...`) + `tel:` link. Frontend: `ContactCallPopup` in `GesprekkenPage` toont modal met "Open WhatsApp" + "Bel direct" knop. Placeholder tot echte WebRTC-integratie. Phone auto-genormaliseerd (0-prefix → +31). Getest: 5 scenarios groen (match op relatie, match op naam, onbekend → hulpbericht, normaal bericht → geen trigger).

### ❓ Open vragen / gaps voor sessie 57

1. ~~**Trade-monitor sync-bug**~~ ✅ **Opgelost sessie 52r** (`v13q_monitor_start_idempotent_001`)
   Root cause: backend returnde `success=False` bij "draait al" → UI showde geen alert (las alleen `data.error`, niet `data.message`). Fix: backend nu idempotent (`success=True, already_running=True`), frontend leest ook `data.message` bij fout. Getest ✅.

2. **XP-veld ontbreekt in edit-modal**
   `AchievementsPage.js` edit-modal past nu alleen titel + icon aan. `xp_reward` en `threshold`/`trigger`-waarden zijn nog blueprint-JSON-alleen (niet via GUI editable). *Vraag*: wil Willem die velden editable in de modal, of blijft dat blueprint-only werk voor Willem alleen?

2. **Rang-drempel-mapping**
   Karakter-kaart toont `char.rang_titel`. Waar wordt die string bepaald? Bestaat er een mapping-tabel `level → rang_titel` (bv. `0-9=Burger, 10-24=Rookie, ...`)? *Actie*: zoek de mapping (mogelijk `dnd_service.py` of `character_defaults`). Als hij niet bestaat: bouwen als losse config-JSON, niet als hardcoded Python.

3. **`text_importer` geeft geen XP**
   `/app/backend/modules/kb_v2/text_importer.py apply_cards_to_kb()` roept nergens `grant_xp()` aan. *Vraag*: bewust (import is admin-taak, geen zelf-XP) of onbedoeld (nieuwe kennis = groei = XP)? Vraag Willem.

4. **`admin_capable` UI-toggle ontbreekt in `UsersAdminPage`**
   Backend endpoint werkt (`POST /api/auth/admin/set-capable/{user_id}`), maar geen frontend switch. *Blocker*: gradatie-3 community-admin kan nu alleen via curl worden geactiveerd. Kleine toggle bouwen in de users-tabel (data-testid: `admin-capable-toggle-{user_id}`).

5. **Legerrang-schaal parallel aan gradatie**
   Emmy stelt Sergeant/Luitenant voor. Agent-advies: **neutrale labels eerst** (Rookie/Bronze/Silver/Gold/Master/Legend) tot er 15-20 users zijn en de XP-verdeling zichtbaar wordt. Dan pas kalibreren + hernoemen. Willem's keuze staat nog open.

### 🎯 Actie voor sessie 57 (voorstel-volgorde)
1. **Bouw `admin-capable-toggle`** in `UsersAdminPage` (gap 4) — kleinste blocker, direct nut
2. **Zoek + documenteer rang-drempel-mapping** (gap 2) — leren wat er is voor bouwen
3. **Beslis over `text_importer` XP-hook** (gap 3) — 1 regel code, product-keuze
4. **XP-veld in edit-modal** (gap 1) — als Willem het wil
5. **Neutrale rang-labels wirings** (gap 5) — nog niet bouwen, alleen ontwerp-schets
6. **`ROADMAP.md` sectie 57 afsluiten** na oplevering, verplaats naar CHANGELOG

---

## 📋 SESSIE 55 — De Grote IQ-Sprong (nog te plannen)

> **Status 4 aug 2026**: was gepland voor 5 aug maar overwoekerd door sessie 56 (tag-cleaner + admin-type). Herbevestigen met Willem of dit blijft staan.

**Doel**: KB structureel schoon + Spark autonoom binnen bewuste grenzen. Bouw voort op sessie-53/54 fundament:
- KB-Curatie Suite (backend + UI live in preview, wacht op redeploy)
- Blauwdruk `spark_tag_curatie_public.json` v1.1 met sectie 8 lade-regels
- Blauwdruk `spark_groeien_public.json` v1.0 met zelfreflectie-flow
- **KB veld-semantiek** `knowledge/_meta.json` schema v1.1 — elk kaart-veld (laag1-4, ws5, andere_velden) heeft eigen doel/toon/verboden. Werkt door in LLM-prompts van 5W-Filler
- Vier Werelden Bijbel-kaarten (Wonderland/Neverland/Mirrorland/Crossroads) — door Willem net toegevoegd

### 🎯 Autonomie-scheiding (leidend principe)
Elke module heeft **twee zones**:
- **🤖 Spark autonoom** — Spark mag zelfstandig voorstel doen. Draft-status, geen mutatie.
- **👤 Willem beslist** — Alleen Willem klikt Accept. Mutatie gebeurt na expliciete goedkeuring.

Deze scheiding staat in de blauwdrukken en wordt gerespecteerd door alle nieuwe endpoints via `_require_admin` gates.

---

### MODULE 1 — 5W-Filler (680 lege kaarten)
**Backend**: `POST /api/kb/v2/curation/5w-suggest/{id}` + `POST /5w-apply/{id}`  
**UI**: `Spark AI → Spark Brain → Groeien → KB-Curatie Suite → 5W-Filler`

**Executie-stappen**:
1. Filter op "alleen volledig lege 5W" (680 kaarten)
2. Sorteer op alfabetisch begrip; werk in batches van 20
3. Per kaart: klik "LLM vullen" → Spark stelt 6 velden voor
4. Review-modal: alle velden bewerkbaar, Willem past aan waar nodig
5. Accept → kaart wordt bijgewerkt + `curation_history` logged

**Zones**:
- 🤖 **Spark autonoom**: LLM-voorstel genereren (geen mutatie), lagen1-4 lezen voor context, tags scannen voor domein
- 👤 **Willem beslist**: elk voorstel individueel accepteren/bewerken/skippen. Geen bulk-accept.

**Deadline-schatting**: 680 kaarten × 30 sec review = ~5.5 uur. In 3 sessies van 2u haalbaar.

---

### MODULE 2 — Duplicate-Merger (32 paren)
**Backend**: `POST /api/kb/v2/curation/duplicate-merge`  
**UI**: `KB-Curatie Suite → Duplicaten`

**Prioriteit-volgorde**:
1. **Rood-flag (same-lade)**: 4 pure duplicaten eerst (`vroeg`, `ai-kunst`, `periodiek systeem`, ...)
2. **Cross-lade dupes**: check of het echte homoniemen zijn (bv. `drift` = drijven vs verlangen → beide houden) of migratie-fout
3. **Merge**: kies keeper met meest 5W-gevuld + meest verbanden → drop wordt weggegooid, tags/5W-gaten migreren

**Zones**:
- 🤖 **Spark autonoom**: identificatie duplicaten, samenvattings-diff tussen paren tonen
- 👤 **Willem beslist**: keeper-selectie. Bij echte homoniemen: één van beide begrip hernoemen zodat ze niet meer botsen.

**Deadline**: 32 paren × 1 min beslissing = ~35 min. Klaar in één sessie.

---

### MODULE 3 — Lade-Reclassificatie (~200-300 echte gevallen uit 695 voorstellen)
**Backend**: `GET /api/kb/v2/curation/lade-check` + `POST /lade-move/{id}`  
**UI**: `KB-Curatie Suite → Lade-check`  
**Blauwdruk-anker**: `spark_tag_curatie_public.json § 8_lade_toewijzing_regels`

**Executie-stappen**:
1. Scan geeft 695 voorstellen — waarvan ~400 vals-positief (zn-meervoud zoals `Begrippen`, `Aandelen`, `Structuren` — géén werkwoord)
2. **Vaste patroon-skips**: zn-meervoud eindigend op -en van zn-enkelvoud (`begrippen` = mv van `begrip`)
3. **Vaste patroon-accepts**: infinitief werkwoorden (`lopen`, `denken`, `benoemen`)
4. Skip zn-meervoud, Accept werkwoorden

**Zones**:
- 🤖 **Spark autonoom**: Regel 1 + 2 uitvoering, voorstel-generatie, patroon-detectie
- 👤 **Willem beslist**: Skip/Accept per voorstel. Bij twijfelgevallen (`spreken` als zn "het spreken" vs werkwoord `spreken`) → Willem oordeelt.

**Sessie 55 open vraag**: `_KNOWN_ZN_OP_EN_EXTENDED` uitbreiden zodra Willem patroon-groepen tegenkomt (bijv. alle zn eindigend op `-heden` = zn-meervoud, automatisch skippen backend-side).

---

### MODULE 4 — Vier Werelden integratie (Willem's nieuwe Bijbel-kaarten)
**Kaarten**: Wonderland (creatief onderzoek), Neverland (herinnering/opzoeken), Mirrorland (reflectie), Crossroads (keuze-ordening)  
**Doel**: Spark herkent deze werelden als **intent-hooks** in chat en gedraagt zich per wereld anders.

**Executie-stappen**:
1. **Chat intent-detectie**: nieuwe module `wereld_intent_service.py` — detecteert "Wonderland/Neverland/Mirrorland/Crossroads" (en synoniemen: "creatief onderzoek", "herinner je nog", "even reflecteren", "welke keuze")
2. **Response-modus per wereld**:
   - Wonderland → LLM temperature 0.8 (creatief), explorerende follow-ups
   - Neverland → KB-lookup prioriteit (rag over chat-log + KB), lage temperature 0.2
   - Mirrorland → reflectieve toon, samenvatting van eerdere uitspraken
   - Crossroads → Spark stelt keuze-lijst op maar kiest zelf NIET (autonomie-grens!)
3. **Blauwdruk toevoegen**: `spark_werelden_public.json` — zelfde patroon als groeien/tag-curatie

**Zones**:
- 🤖 **Spark autonoom**: wereld herkennen, response-modus schakelen, follow-up vragen formuleren
- 👤 **Willem beslist**: bij Crossroads NOOIT beslissen namens Willem. Alleen keuzes ordenen.
- 🛡️ **Harde grens**: Wonderland-creativiteit mag geen KB-mutaties triggeren. Alleen chat-space fantasie.

**Effort**: ~30 credits (nieuwe intent-module + blauwdruk + 4-manier LLM-tuning).

---

### MODULE 5 — Bulk Vocab-approve top-100 (klein maar zichtbaar)
**Backend**: bestaat al — `POST /api/spark/vocab/approve-growth`  
**UI**: bulk-checkbox "selecteer top-100" in bestaande Groeien → Vocab-tab

**Executie-stappen**:
1. Fetch top-100 van `vocab-from-knowledge`
2. Selecteer all
3. Klik goedkeuren → 5963 → 6063 vocab-woorden

**Zones**:
- 🤖 **Spark autonoom**: kandidaten scoren op frequentie
- 👤 **Willem beslist**: één bulk-accept, want elk woord komt 100+× in KB voor = impliciete endorsement

**Effort**: ~15 credits (alleen "selecteer all"-knop toevoegen).

---

### MODULE 6 — Graph-vulling beslissing (nadat KB schoon is)
**Doel**: Los de "broken belofte" van weeskaart-check op.  
**Voorstel**: nadat 5W-Filler + Dupe-Merger + Lade-Reclassificatie klaar zijn (KB is schoon), migreer alle KB-kaarten naar `graph/nodes.json` als knowledge-nodes met tag-relaties als edges.

**Zones**:
- 🤖 **Spark autonoom**: migratie-script draaien, statistieken teruggeven
- 👤 **Willem beslist**: knop indrukken om te starten. Rollback beschikbaar via backup.

**Effort**: ~40 credits. Kan naar Sessie 56 als 55 vol raakt.

---

### MODULE 7 — Inbox subtab "Onvolledig" ✅ DONE (sessie 52a, feb 2026)
**Doel**: 680 lege-5W kaarten zichtbaar maken in bestaande Inbox-tab i.p.v. nieuwe top-tab.  
**Anker**: `knowledge/_meta.json § kaart_veldsemantiek.incompleet_criterium.toon_in_ui`

**Status**: Geïmplementeerd én geïntegreerd in de sort-dropdown flow. `KennisbankV2Page` toont Onvolledig als filter binnen de Inbox-grid met sort-support. Zie CHANGELOG sessie 52a.

**Executie-stappen** (referentie, gedaan):
1. ~~Backend: `/api/kb/v2/inbox` endpoint krijgt optionele `?filter=incomplete` param~~
2. ~~Filter-logica hergebruikt `incompleet_criterium.checks` uit meta (7 regels)~~
3. ~~Frontend `KennisbankV2Page.js`: subtabs + sort-dropdown~~
4. ~~Klik op subtab → herlaadt met andere query-param~~

**Zones**:
- 🤖 **Spark autonoom**: incompleet-detectie via meta-regels
- 👤 **Willem beslist**: aanpak per kaart (invullen via 5W-Filler of manueel bewerken)

**Effort**: ~15 credits.

---

### MODULE 8 — Refine-endpoint per veld (chirurgische verbetering)
**Doel**: Willem kan Spark chirurgisch vragen "verbeter alleen laag3" i.p.v. hele kaart opnieuw.  
**Anker**: `knowledge/_meta.json § kaart_veldsemantiek.lagen.laag3` (of ws5.wat/waarom/etc.)

**Nieuw endpoint**: `POST /api/kb/v2/card/{id}/refine?field=laag3`  
**Flow**:
1. Lees kaart + veld-definitie uit meta (doel/toon/verboden)
2. Bouw LLM-prompt: "Verbeter alleen `field` volgens deze regels: `{doel}`, toon `{toon}`, vermijd `{verboden}`. Behoud alle andere velden."
3. Return voorstel voor review (draft, geen mutatie)
4. Willem accepteert → veld wordt bijgewerkt, curation_history logged

**UI-integratie**: 
- KennisbankV2Page → kaart-detail-view → klein potlood-icoontje per veld
- Klik → LLM voorstel modal → Accept/Cancel

**Zones**:
- 🤖 **Spark autonoom**: LLM-voorstel op basis van meta-regels
- 👤 **Willem beslist**: accept per veld, geen bulk

**Effort**: ~25 credits. Bouwt exact op de veld-semantiek die vandaag is vastgelegd — zonder die meta zou dit niet werken.

---

### 📊 Sessie 55 SLA (bijgewerkt)
- **Verwacht kredietverbruik**: ~130-160 credits (KB-Curatie executie + Werelden-module + vocab-bulk + inbox-subtab + refine-endpoint)
- **Minimaal resultaat**: 680 lege 5W ingevuld met scherpe LLM-voorstellen (dankzij nieuwe meta-regels) + 32 dupes weg + ~200 lade-fouten gecorrigeerd + Werelden werken in chat
- **Ideaal resultaat**: bovenstaand + Graph gevuld + top-100 vocab live + refine-per-veld werkend + inbox-subtab zichtbaar
- **Reserve-post**: Sessie 56 voor Graph-vulling als Sessie 55 vol raakt

### 🚦 Redeploy-checkpoint (nu)
Alles wat hierboven staat DRAAIT AL in preview:
- ✅ KB-Curatie Suite (backend + UI)
- ✅ `knowledge/_meta.json` schema v1.1 met veld-semantiek (130 regels definitie)
- ✅ 5W-Filler LLM-prompt leest de nieuwe veld-regels
- ✅ Blauwdrukken groeien + tag-curatie
- ✅ Vier Werelden Bijbel-kaarten
- ✅ Agenda intent-splitter, admin-toggle audit, chat-visibility toggles, shop-owner permissies + user-container foto's

Backup gemaakt: `/app/_backup_before_prod_merge_20260803_071830/`

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

---

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
