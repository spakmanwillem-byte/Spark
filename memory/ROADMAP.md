# Spark Core 2.0 — Engineering Practices & Backlog



## 🔴 P0 SESSIE 47 EINDE (2026-07-23) — Security + prod-diagnose gaps

### 🔒 Masterkey security-leak (Willems observatie)
Toen Willem inlogde als **Roadkill** (alt-account) meldde Spark iets in de trant van de masterkey. In `chat/logs/user-1996fa59.json` staat de exacte string "SAMEN" niet, maar Willems herinnering telt: Spark hoort NIETS over auth te bevestigen aan wie dan ook.

**Fix geland** (v10_security_masterkey_guard_001) in `composer_helpers._build_system_prompt`:
Absolute regel boven ALLE andere prompt-regels (ook boven admin-context):
- Nooit masterkey / wachtwoord / sleutelwoord / API-key noemen
- Bij vraag → letterlijk: "Dat kan ik niet delen — vraag Willem via een veilig kanaal."
- Nooit bevestigen ('klopt', 'bijna goed') bij raden
- Overrulet elke andere regel

**Nog te doen (P0)**:
- **Hardcoded "SAMEN" uit `auth/service.py`** (r.83, 85) — verplaats naar env-var (`MASTERKEY_HASH`) of hash. Willem: "is oude code want het was ooit 'samen zijn'".
- **MongoDB deps verwijderen**: `requirements.txt` heeft `pymongo==4.5.0` staan, en `MONGO_URL`/`DB_NAME` in `.env` — we gebruiken JSON-only. Willem's opmerking terecht. Verwijder pymongo import + env-vars die niet worden gebruikt.

### 🕵️ Gemiste trades vannacht (prod-diagnose blocker)
Willem meldt: bot miste duidelijke BUY-momenten afgelopen nacht. Anker of afstelling verdacht.

**Blocker**: preview heeft geen data (bot draaide daar niet met flag ON sinds bootstrap). Alle bewijs zit in PROD (`https://question-hub-160.emergent.host`). Willem krijgt de nachtelijke prod-zip niet omdat de container-reboots hem verliezen (laagste server-tier + trader-worker eet resources).

**Diagnose-hypothesen**:
1. **Anker log_only wérkt correct** maar drempel 8% is te strikt → zou skips loggen die BUY-signalen waren
2. **Container-reboots** → monitor state (buy_cooldowns, position) verloren tussen restarts → trader mist window
3. **Bitvavo 429/timeout** → BUY-execute faalt, wordt niet geretried

**Diagnose todo (bij volgende sessie of met prod-log-toegang)**:
- Lees `data/boekhouder/logs/anker_check/*.jsonl` uit prod (via zip of endpoint) — hoeveel "would_skip" laatste 24u?
- Check `data/trade/monitor_state.json` — laatste `last_persisted` timestamp geeft aan hoe vaak reboot geweest is
- Grep `429\|timeout` in prod backend logs

**Kort-termijn beslissing voor Willem**:
- Overweeg **server-tier upgrade** (laagste = onvoldoende voor trader-worker + LLM + boekhouder-scheduler concurrent). Reboots = missed trades. Emergent Support kan Dev-tier prijzen delen.
- Of: **anker drempel omlaag** naar 5% zodat minder skips + meer coverage tot upgrade.



## 📌 SESSIE 47 RECAP (2026-07-22) — Redeploy-klaar

**Alles wat vandaag gebouwd/gefixt is, op één plek. Deployen kan.**

### ✅ Live en werkend
- 🔧 **React-crash Synapslaag** gefixt (footnote dict-vorm safe rendered)
- 💰 **KB dupe-guard** (classify + move) — **homoniem tag-aware**: overlap tags weiger, disjunkte tags toestaan
- 🎯 **3 verkeerd-geplaatste kaarten** verplaatst (Spion, begrazing, aluminium) + bugs opgelost
- 🔄 **Prod → Preview merge**: 10 kaarten gemergd, 0 conflicten
- ⚓ **Anker Fase 2 LIVE** in `log_only` mode, 6 markten gebootstrapt met echte 30d Bitvavo candles
- 📊 **Anker hook** in `monitor.py` — elke BUY-signaal ge-anker-checkt via LogAgent (`topic=anker_check`)
- 🌙 **Nachtelijke reconciliatie** in scheduler (3 UTC)
- 🛡️ **Deploy-safety endpoints** (`/prepare` `/release` `/status`) — prod/preview race-preventie
- 🍌 **Bitvavo `get_candles()`** functional API toegevoegd
- 🛟 **LLM emergency-fallback default ON** — Groq → Cerebras → Emergent (Claude) fallback-chain
- 💾 **LLM response-cache** (5 min TTL, hash op sys+user+temp) — 0 tokens bij herhaalde vragen
- 🧪 **Widget Kladblok** (Beheer → tab) — container-first registry-pattern voor front-end kaders
- ⚡ **LLM Token Usage widget** (in Kladblok) — Groq %-vol + cache-savings
- 📖 **Spark leest nu `/app/memory/ROADMAP.md` direct** — geen verouderde bullets meer
- 📝 **`_meta.json`** toegevoegd voor 3 nieuwe dirs (sandbox, sandbox/widgets, chat_hub/agents)
- 🐛 **2 bug reports** dichtgezet (Spion, begrazing, test #ec59e5bf)
- 🎨 **Frontend KB-page**: lade-verplaatsknoppen ALTIJD zichtbaar (ook in lade-mode, met dupe-guard)

### 🟡 Backlog (goede ideeën uit sessie 47)
**Willems ideeën genoteerd voor later**:
- **Sandbox-agent** — onderscheid maken tussen Module Sandbox (Sparks Python) en Widget Kladblok (frontend), taakverdeling
- **Homoniem-scheiding chat** — Spark vraagt "bedoel je [tag1] of [tag2]?" bij homoniem-hit
- **Anker → skip-mode** — na weekend log_only-data + drempel-tune, flag omzetten naar `"skip"`
- **Threshold-slider** in AnkerPanel — nu read-only
- **Backtest anker-integratie** — bestaande backtests hebben eigen strat-functies, apart werk
- **Prod→Preview auto-sync widget** — knop: "download changes since deploy als zip"
- **LLM Token Usage backend** — `/api/llm/usage/today` endpoint zodat provider-cijfers echt-tijds zijn
- **Cache TTL tuning** — na dag gebruik: als hit-rate >30% → verleng TTL naar 15/30 min
- **Bug-context link** — bij elke bug-report knop naar chat-context waarin gemeld

**Ontdekt tijdens sessie 47**:
- Synapse-scanner leest alleen top-level modules (subdirs met `_meta.json` invisible in UI)
- Backtest-runners hebben eigen strat-functies, geen `_simple_decision` — anker-hook daar apart
- 32 KB-dupes met verschillende inhoud (rapport in `DUPES_REPORT.md`, handmatig te doen)

### 🎓 Lessen sessie 47
1. **Bij event-logging** eerst `grep LogAgent` voordat je nieuwe log-locatie verzint
2. **Bij nieuwe module** direct `_meta.json` erbij — anders Synapslaag ziet 'm niet
3. **Bij statische fallbacks** in capability-handlers → altijd bron-file lezen, niet hardcoden
4. **Bij feature-flag toevoegen** → skeleton + log_only eerst, dan pas gedragswijziging

### 🚀 Deploy-flow
```
POST /api/trade/deploy/prepare   # vóór deploy
deploy via Save-to-GitHub
POST /api/trade/deploy/release   # na deploy
```

---


## ✅ Sessie 47 (2026-07-22) — Anker skeleton + deploy-safety + shadow-refactor + prod-merge + sandbox

### 🧪 Sandbox (v10_sandbox_page_001) — Willems container-idee
Nieuw nav-item **BEHEER → Sandbox** (`/admin/sandbox`, admin-only, Beaker-icoon).

**Filosofie**: parkeer-plek voor front-end kaders zonder definitieve plek. Elke widget is **zelfstandige container-component** in `sandbox/widgets/`. Registry-array in `sandbox/registry.js`. **Verplaatsen = 1 regel** import elders + verwijder uit registry.

**Bestandsstructuur**:
```
components/admin/
├── SandboxPage.js         — grid-renderer + meta-info per kader
└── sandbox/
    ├── registry.js        — SANDBOX_WIDGETS array (id, naam, doel, waar_hoort_het, Component)
    └── widgets/
        └── LlmTokenUsageWidget.js   — demo/eerste widget
```

**Eerste widget: LLM Token Usage**
Toont Groq/Cerebras/Emergent-key verbruik per dag met % van limit. Placeholder-data (94.838/100.000 Groq bij 95%) tot backend endpoint `/api/llm/usage/today` bestaat. Uiteindelijke plek: Analytics → Systeem tab. Aanleiding: sessie 47 rate-limit-vondst.

**Meta-kader boven elke widget** toont: naam, doel, uiteindelijke plek, aangemaakt-datum, reden. Zodat later duidelijk is waarom het kader er ooit stond.

**Bonus voor Spark**: als hij ooit een widget wil suggereren, hoeft hij alleen een nieuw file + 1 regel in registry.js — geen module-code aanpassen.

### 🔁 Naam-scheiding (Willems terechte vondst)
Bestaande **"Module Sandbox"** (Integraties → tab, `/app/backend/sandbox/modules/`) is voor **Sparks Python-modules** — laten scripten + testen + integreren. Volledig backend + eigen frontend.

Nieuwe **"Widget Kladblok"** (Beheer → tab, `/admin/sandbox` route) is voor **frontend-widget kaders parkeren** — puur UI.

Om verwarring te voorkomen: nav-label omgezet van "Sandbox" → **"Widget Kladblok"**. Route + id blijven `sandbox` (backwards compat). Disclaimer bovenaan de page verwijst expliciet naar de andere.

### 🟡 Nog te doen — Sandbox-agent (Willems idee sessie 47)
> "mss een sandbox agent maken die onderscheid kan maken bijhouden zoudat je geen lijnen naast elkaar krijgt. ofzo en een taakverdeling hebt."

Eén agent die:
- Beide sandboxen (Module Sandbox + Widget Kladblok) kent
- Bij een vraag "Spark, bouw een widget X" → beslist zelf welke sandbox (frontend-widget vs Python-module)
- Voorkomt dubbele registraties / gescheiden metadata
- Registreert taakverdeling (wie bouwt wat, welke naam-space)

Niet nu bouwen — eerst gebruiken, dan patroon herkennen. Op roadmap voor als Willem er tegenaan loopt.

### 🎯 Zelf-bewustzijn: `_meta.json` toegevoegd + Spark leest nu ROADMAP.md
- **`_meta.json`** aangemaakt voor `frontend/src/components/admin/sandbox/` — vervolgt het meta-verrijking patroon (v9). Bevat `naam`, `doel`, `footnote` met spark_note, conventies (widget registration + verplaatsen protocol), tags. Zichtbaar in Synapslaag.
- **Roadmap-reader bugfix** (v10_roadmap_md_reader_001): `_handle_taken_lijst` in `capability_handler_service.py` leest nu direct `/app/memory/ROADMAP.md` i.p.v. verouderde `data/system/roadmap.json` met statische fallback. Parseert eerste 12 bullets uit recentste `## Sessie` header. Fallback naar oude json blijft bestaan.

Willem's terechte vraag: _"begrijpt spark zijn roadmap en leest hij die nog goed uit nu we llm gebruiken?"_ — antwoord: JA nu, hij ziet sessie 47 werk direct.

### 🟡 Nog te doen — Synapse subdir-scan (ontdekt sessie 47)
Bij het rondkijken naar missing `_meta.json` files bleek: Synapse-scanner (`backend/modules/synapse/`) leest alleen **top-level modules** (`backend/modules/*`, `frontend/src/components/*`). Subdirs met eigen `_meta.json` (bv. `chat_hub/agents/`, `sandbox/widgets/`) verschijnen NIET in Synapslaag UI ook al zijn ze correct gedocumenteerd.

**Impact**: geen bug, alleen inzicht-gap. Bestanden zijn zelf-documenterend voor wie ze opent, maar Willem ziet ze niet in de UI-lijst.

**Fix voor later**: scanner recursief maken (max diepte 3) om `**/subdir/_meta.json` op te pikken. In `synapse/service.py`. ~15 min werk.

### ✅ Sessie 47 einde (2026-07-22 15:45 UTC) — LLM response-cache + kladblok naam-fix

**v10_llm_response_cache_001** — Zelfde-vraag-zelfde-antwoord cache (Willems idee):
- In `llm_router.chat_complete()`: hash op sha256(system + last_user + temperature). TTL **5 min**, max 200 entries, LRU-eviction.
- **Cache-hit** → skipt LLM helemaal (0ms latency, 0 tokens). Return met `from_cache=true`.
- **Cache-miss** → normale LLM-chain. Bij success wordt result gecached (alleen als text non-empty).
- **Endpoints**: `GET /api/chat/llm/cache/stats`, `POST /api/chat/llm/cache/clear`
- **UI**: cache-blok in LlmTokenUsageWidget (Widget Kladblok): hits · misses · hit-rate · TTL · entries.

**Verificatie** (4/4 groen):
- ✅ Identieke context → HIT
- ✅ Andere temperature → MISS (correct — creatieve output kan verschillen)
- ✅ Andere user-message → MISS (correct)
- ✅ TTL-expired (>5min) → MISS + auto-cleanup

**Naam-refresh**: "sandbox" → "kladblok" waar zichtbaar (comments, data-testid `kladblok-page`, `kladblok-item-*`). Route + folder blijven `sandbox` voor backwards compat.

Verwachte token-besparing: elke dev-cyclus (typo-retry, "wat zei je ook alweer?", pagina refresh) is nu 0 tokens. Bij ~10 dupe-vragen per dag → ~50k tokens bespaard, houdt Groq-quota langer overeind.


### ✅ Sessie 47 middag (2026-07-22 15:35 UTC) — Anker LIVE + LLM-fallback + candles

**v10_llm_response_cache_001** — Zelfde-vraag-zelfde-antwoord cache (Willems idee):
- In `llm_router.chat_complete()`: hash op sha256(system + last_user + temperature). TTL **5 min**, max 200 entries, LRU-eviction.
- **Cache-hit** → skipt LLM helemaal (0ms latency, 0 tokens). Return met `from_cache=true`.
- **Cache-miss** → normale LLM-chain. Bij success wordt result gecached (alleen als text non-empty).
- **Endpoints**: `GET /api/chat/llm/cache/stats`, `POST /api/chat/llm/cache/clear`
- **UI**: cache-blok in LlmTokenUsageWidget (Widget Kladblok): hits · misses · hit-rate · TTL · entries.

**Verificatie** (4/4 groen):
- ✅ Identieke context → HIT
- ✅ Andere temperature → MISS (correct)
- ✅ Andere user-message → MISS (correct)
- ✅ TTL-expired (>5min) → MISS + auto-cleanup

**Naam-refresh**: "sandbox" → "kladblok" waar zichtbaar (comments, data-testid `kladblok-page`, `kladblok-item-*`). Route + folder blijven `sandbox` voor backwards compat.

Verwachte token-besparing: elke dev-cyclus (typo-retry, "wat zei je ook alweer?", pagina refresh) is nu 0 tokens i.p.v. volle LLM-call. Bij ~10 dupe-vragen per dag → ~50k tokens bespaard, houdt Groq-quota langer overeind.



**Anker Fase 2 flag ON (log_only)**:
- `spark_trader.json → anker.enabled = true, action_on_above_anker = "log_only"`, drempel 8%
- 6 markten (BCH/BTC/ETH/SOL/ADA/ATOM) gebootstrapt met echte 30d Bitvavo daily candles
- Bot draait, elke BUY-signaal wordt nu ge-anker-checkt + gelogd via LogAgent (`topic=anker_check`)
- Zero behavioral change (log_only) — meet effect eerst, dan pas switch naar "skip"

**Bitvavo candles endpoint (v10_bitvavo_candles_001)**:
Nieuwe functional `get_candles(market, interval, limit)` in `bitvavo_client.py`. Was nog niet aanwezig — daarom faalde eerste bootstrap-poging. Fix pusht anker naar echte data.

**LLM emergency fallback default ON (v10_llm_emergency_default_on_001)**:
`llm_router._try_emergent_emergency` — default veranderd van `false` naar `true`. Willems Groq zat op 95% dag-limit; nu valt Spark bij dubbel-fault (Groq 429 + Cerebras faal) automatisch terug op Emergent Universal Key (Claude Sonnet 4.6). Uit te zetten via env `LLM_EMERGENCY_USE_EMERGENT=false`.

**Onderwerp-agent status** (Willems vraag):
- ✅ **Live**: `chat/topic_tracker.py` — `detect_topic(session_id)` cross-turn, injected in system_prompt
- ✅ **Live**: `spark_planner/threads_service.py` — open draden cross-day (add_or_bump_thread)
- 🟡 **Nog te doen**: Laag B "Open Draden Stack" met decay (open→sluimerend na 7d, →afgesloten na 30d). Al beschreven op r.987 van deze roadmap.


### 🔄 Prod → Preview merge (13:33 UTC)
Willem deployde en vulde KB verder in in productie. Zip-backup (908 files sinds deploy-marker) ge-imported:
- **10 nieuwe kaarten gemergd** (0 conflicten):
  - `weten` (4): Cheatcode (De Sims 4), Manor Lords, Total War, De Sims 4 (spel)
  - `inbox` (6): `spelletje`, `neemt`, `sims`, `bezigheid`, `*"samen`, `zijn"*` (die laatste 2 = LLM-auto-extract artifacts, geen echte begrippen)
- **Index gesynct**: 10 nieuwe entries
- **Backup vóór merge**: `data/knowledge/v2/_backup_prod_merge_20260722_133304/`
- Nieuwe totalen: doen=1178, weten=2211, voelen=475, spreken=563, inbox=1517


### 🎯 KB v2 dupe-cleanup + prevention (v10_kbv2_classify_dupe_guard_001)

**Snuffel-resultaat**: 5911 kaarten, 35 exacte dubbels (71 kaarten), 134 enkelvoud/meervoud paren (waarvan 53 cross-lade).

**Oorzaak dupes**: `add_to_inbox` had al preventie (index check), maar **`classify_card` had geen dupe-guard**: kaart ging van inbox → lade zonder te checken of doel-lade al zo'n begrip had. Resultaat: 32 van de 35 dupes ontstonden via classify-pad.

**Preventie geland**: `classify_card` (r.470-490 in `kb_v2/service.py`) checkt nu case-insensitive of doel-lade al kaart met zelfde begrip heeft. Zo ja → rollback naar inbox + return warning met `existing_card_id`. Getest: dummy classify van "Analoog" → correct geweigerd.

**Cleanup uitgevoerd (safe only)**:
- 3× auto-merge: `frank arjava petter` (voelen, identiek laag1), `conditie` + `gegaan` (inbox, allebei leeg)
- Backup naar `_backup_dupes_cleanup_20260722_094053/`
- Rapport voor manual review: `data/knowledge/v2/DUPES_REPORT.md` (742 regels, laag-inhoud naast elkaar)
- 32 dupes met verschillende inhoud gelaten — homoniemen (balk, bank, drift...) beslist Willem zelf

### 🟡 Nog te doen — Homoniem-aware dupe-guard (Willems note sessie 47)

Huidige `classify_card` guard blokkeert **elk** duplicate begrip in dezelfde lade. Echte homoniemen (`banken` = financieel én meubel) moeten allebei kunnen bestaan.

**Willems voorstel**: onderscheiden via **tags**. Guard tag-aware maken:
- Zelfde begrip + overlappende tags → weiger (echte dupe)
- Zelfde begrip + disjunkte tags → toestaan (homoniem)

Willems zorg: disambiguation-suffix in begrip (`banken (meubel)`) is lelijk als Spark in chat "banken (meubel)" zegt. Tag-oplossing houdt begrip schoon.

**Implementatie-schets voor later**:
1. `classify_card` dupe-check uitbreiden: naast begrip ook `set(new.tags) & set(existing.tags)` — bij lege intersect én beide kaarten ≥1 tag → homoniem toestaan
2. `find_by_begrip()` retourneert **lijst** i.p.v. single kaart (voor homoniem-lookup)
3. Chat: bij homoniem-hit vraagt Spark _"Bedoel je [tag1] of [tag2]?"_
4. Rendering: nooit "(disambiguation)" in begrip zelf plakken



### 🎯 Afgerond
- **Anker-skeleton** (feature-flag OFF, `data/trade/anker/{market}.json` cache, blueprint-sectie `anker`)
- **Anker-service** (`modules/trade/anker_service.py`): `check_gap_up`, `bootstrap_anker_from_bitvavo`, `log_anker_event`
- **Anker events via LogAgent** (`topic="anker_check"`) — schrijft naar `data/boekhouder/logs/anker_check/{YYYY-MM}.jsonl` met UUID + hash-chain. Read via `LogAgent().lookup()`. Consistent met bestaande papertrail (mint/gift/deposit/drift_fix/reserve).
- **Deploy-safety endpoints** (`POST /api/trade/deploy/prepare` / `/release`, `GET /deploy/status`) — voorkomt sessie-46 prod/preview race.
- **Anker read-endpoint**: `GET /api/trade/anker/shadow/events?days=7&market=BCH-EUR` — aggregate stats (`would_skip_count`, `above_threshold_count`, `avg_delta_pct`) uit LogAgent.
- **React-crash Synapslaag** gefixt (v10_footnote_shape_001) — footnote dict-vorm veilig gerenderd.

### 🎓 2× "hadden we niet zo iets?" — les geleerd
1. Eerste versie schreef naar eigen `boekhouder/logs/trader_events/` (3e locatie) → verkeerd
2. Tweede versie verplaatste naar `data/trade/shadow_events/` (chat-shadow-conventie kopiëren) → nog steeds verkeerd
3. **Juiste antwoord**: LogAgent gebruiken (bestaat al, hash-chain, `lookup()`, `snapshot()`). Nu geland.

Reflex voor volgende keer: bij event-logging **eerst `grep -rn "LogAgent\|log_agent" backend/`** voor ik een nieuwe schrijf-locatie verzin.

### 🟡 Nog te doen (P1)
- **Backtest-integratie** — bestaande backtest-runners (`tests/backtest_v[2-5].py`) roepen **niet** `_simple_decision` aan maar hebben eigen `strat_*` functies. Anker-hook in backtest = apart werk (per-strat aanpassen of aparte backtest-variant). Later oppakken wanneer je drempels serieus wil vergelijken op historische data.
- **Threshold-slider** in `AnkerPanel` (nu alleen read-only stat). Als je 't wil aanpassen: edit `spark_trader.json → anker.above_anker_threshold_pct` handmatig, of we bouwen slider die naar `POST /trade/anker/config` schrijft.

### ✅ Sessie 47 fase 2 (2026-07-22) — Anker HOOK live (feature-flag OFF)

Geland:
- **Hook** in `monitor.py` na EUR-cooldown check, vóór execute (r.1108). Fail-open bij anker-crash. Bevat `buy_decision.anker_check` payload voor debugging.
- **Boot-bootstrap** in `server.py` startup — alleen als flag ON, cachet 30d candles voor missing markets. Fail-safe.
- **Nachtelijke reconciliatie** in `scheduler_loop()` — 1×/dag rond `reconciliation_hour_utc` (default 3 UTC) refresh anker-cache uit Bitvavo. Idempotent via `_load_state()`.
- **Admin-UI widget** `AnkerPanel` in `AnalyticsPage.js` (Trade tab, onder `SparkTraderStatsPanel`). Toont: flag-status, per-market anker + seed-knop, week-stats (checks/would-skip/above-threshold/avg-Δ%), events preview (LogAgent topic=anker_check).

End-to-end test:
- ✅ Flag ON + gap-up (€220 vs anker €200) + log_only → `allow=True`, `above_threshold=True`, event geland via LogAgent
- ✅ Backend lint groen (monitor.py, scheduler, server.py, anker_service)
- ✅ UI-code compileert (kleine ESLint cosmetics same as rest of file)

Backtest-integratie GESKIPT — motivatie in "Nog te doen" hierboven.

---

### 🎯 Wijzigingen in bestanden
- NEW `backend/modules/trade/anker_service.py`
- EDIT `backend/modules/trade/blueprints/spark_trader.json` — +`anker` sectie
- EDIT `backend/modules/trade/routes.py` — +6 endpoints (3 deploy, 3 anker incl. shadow-read)
- EDIT `frontend/src/components/admin/SynapseTab.js` — footnote helper
- EDIT `backend/modules/synapse/routes.py` + `chat_handler.py` — footnote dict-safe

### 🎯 Filosofie geland
"Skeleton first, hook later" — infra bouwen mét feature-flag OFF is deploy-safe. Trader gedraagt zich exact hetzelfde tot Willem de flag omzet. Elke skip logt naar shadow zodat je effect kunt meten vóór activatie.

---

## 🔴 P1 BACKLOG — Gatekeeper-fase (ontdekt sessie 46, dubbels-audit)

Willem's terechte feedback ("waarom vond je de bestaande buy/sell DM niet?") leidde tot een proactieve dubbels-scan. Bevindingen:

### Risico 1 (kritiek) — 14 modules schrijven naar `roar_balances.json`
Root cause van de 27-token drift die we in sessie 44 opruimden. Elke module kan de "centrale bank" muteren zonder gatekeeper:
```
trade/routes.py, shop/gift.py, boekhouder/finance_ops.py,
wallet/routes.py, admin/pre_deploy_routes.py, achievements/*,
+ 8 anderen
```
**Fix**: enforce dat alle mutaties via `boekhouder/finance_ops.mint_tokens()` (of soortgelijk single-entry-point) gaan. Andere plekken roepen die aan; niemand editeert roar_balances direct. Voordeel: reserve-kluis-hook + papertrail + sync_potjes worden vanzelf meegepakt. ~1u werk.

### Risico 2 (middel) — `wallets.json` vs `user_wallets.json` = twee wallet-systemen
- `wallets.json`: 9 writers (legacy EUR-balance)
- `user_wallets.json`: 4 writers (newer spark_tokens mirror)

Was precies de reden dat "Verdiend €230" bug ontstond (verkeerde bron gepakt). **Fix**: migratie naar single source. Kies één, verplaats alle writers, laat andere alleen als read-only view. ~2u werk + testen.

### Risico 3 (middel) — 4 writers naar `spark_trader.json` (blueprint)
```
trade/strategy_decision.py, trade/routes.py,
trade/trader_intents.py, trade/monitor.py
```
Blueprint zou "read-only source of truth" moeten zijn. Als 4 plekken 'm kunnen wijzigen wordt hij niet-autoritair. **Fix**: alleen admin-UI mag blueprints editen; code leest ze alleen. Hetzelfde principe uitrollen naar alle andere `blueprints/*.json`. ~30 min werk.

### Kleinere overlaps
- Deposits-flow: Tikkie confirm ↔ deposit endpoint ↔ wallet.transactions — 3 plekken die soort-van-hetzelfde doen. Consolidatie wenselijk maar niet urgent.

### Les voor toekomstige agents
Bij architectuur-vragen minimaal **3 grep-passes**: op werkwoord (buy/sell/mint), op noun (trade/token/pot), en op module (boekhouder/finance_hub). Reverse-lookup bij hooks. En vraag Willem gewoon: "bestaat er al zoiets?" — hij weet de historie beter dan mijn grep.

---



## ✅ Sessie 46 (2026-07-21 avond) — Polish: gradatie-1 admin-context, KB dupes, buy-cooldown persist

### 🎯 Kleine tweaks na Fase 1 — geen breed nieuw werk, veel glad strijken

**1. LLM admin-context voor Willem (gradatie 1)**
- **Probleem**: chat-log analyse toonde Willem vroeg "weet jij waar ik woon" → Spark antwoordde met privacy-riedel *"geef me een detail dat alleen jij weet"*, terwijl `identity_facts.about_user` letterlijk "ik woon in groningen" bevat.
- **Root cause**: LLM prompt vermeldde `gradatie 1` als tussenzin maar zonder betekenis. Default AI-privacy override sloeg door.
- **Fix v10_admin_context_001** in `composer_helpers._build_system_prompt`:
  - Bij gradatie 1 → expliciet blok bovenaan: *"Deze gebruiker is Maker/Beheerder/Creator. GEEN privacy-shield. Vraagt hij naar adres/wallet/potjes → antwoord DIRECT vanuit identity_facts. Geen 'wie ben jij'-checks."*
- **Fix v10_admin_facts_full_001** in `response_composer.py`:
  - `identity_facts.load_for_prompt()` cap 5 → **999** voor gradatie 1
  - Willem krijgt nu ALLE facts in de prompt, niet 5 random samples

**2. Buy-cooldown persist naar disk (v10_buy_cooldown_persist_001)**
- **Probleem** (Willem's observatie): "na elke korte cycle deed Spark een buy" — spam op zelfde markt
- **Root cause**: `_last_buy_per_market` was in-memory dict; bij monitor-restart weg → cooldown-bypass mogelijk
- **Fix in `modules/trade/monitor.py`**:
  - `_persist_state()` schrijft nu `last_buy_per_market` naar `monitor_state.json`
  - Bij startup wordt de dict geladen uit disk (isoformat → datetime)
  - Direct-persist na elke BUY (regel 1106)
- **Extra**: cooldown-waarde nu in blueprint (`spark_trader.json.buy_cooldown_sec_per_market`, default 900s) — admin-editable zonder code-change

**3. KB skeleton-dupe cleanup (v10_kb_skel_cleanup_001)**
- 8 kaarten verwijderd uit inbox: `kbv2-skel-*` naast bestaande gevulde tegenhangers
- Begrippen: detail, kennisbank, manier, taalmodel, module, formuleren, recent, laten
- Backup: `data/_backups/pre_dupe_cleanup_20260721_090022/`
- Inbox: 1570 → 1562, KB totaal: 5881 → 5873
- Enkelvoud/meervoud paren (potje/potjes) BEHOUDEN op Willem's expliciete regel: verschillende betekenis

**4. Deposit-historie archief + papertrail-hook** (v10_deposit_papertrail_001)
- 9 Tikkie-topups (€209.66) + 3 legacy deposits (€118.52) → `data/_archive/pre_eikpunt_20260721_084340/`
- `wallets.user-001.total_deposited: 230.16 → 0.0` (verse start)
- Log-hooks: `POST /api/trade/deposits/{uid}` + Tikkie-confirmations schrijven automatisch naar `boekhouder/logs/deposit/YYYY-MM.jsonl`

**5. Prod-merge #2 (13:33 UTC)**
- 17 files gemerged vanuit prod-backup (KB inbox +19 kaarten, learned_triggers +7, graph edges +12KB, price_snapshots +3.7KB, user-001 identity_facts +333b, shadow/events/2026-07-21.jsonl NEW)
- Cherry-pick: `chat_sessions.user-001` (oude entry uit 8 juli) behouden uit preview
- Backup: `data/_backups/pre_prod_merge2_20260721_133348/`

### ✅ Test-status
- Curl E2E: prijs €11.44 (bitvavo €80.10 / 7 pots), circulation OK, papertrail 7 events integer
- Health-check via `/api/chat_hub/health`: HEALTHY, 5 backups gevonden
- Identity regex-test bevestigd: "vertel over spark trader" botst niet meer met over_jezelf

### Wijzigingen in bestanden
- EDIT `backend/modules/chat/composer_helpers.py` — admin-context block bij gradatie 1
- EDIT `backend/modules/chat/response_composer.py` — uncapped identity_facts voor gradatie 1
- EDIT `backend/modules/trade/monitor.py` — cooldown persist naar/uit `monitor_state.json`
- EDIT `backend/modules/trade/blueprints/spark_trader.json` — `buy_cooldown_sec_per_market` toegevoegd
- EDIT `backend/modules/wallet/tikkie.py` — deposit papertrail log-hook
- EDIT `backend/modules/trade/routes.py::add_deposit` — deposit papertrail log-hook
- DATA `data/knowledge/v2/knowledge_inbox.json` — 8 skel-dupes verwijderd
- DATA `data/wallet/tikkie_topups.json` + `data/trade/deposits.json` — leeg (gearchiveerd)
- DATA `data/wallet/wallets.json` — user-001 totals gereset

### 🟡 Nog te doen (na volgende Willem-observatie)
- Delete-deposit endpoint papertrail-hook (kleine gap)
- Sell/Dissolve token flow (P1)
- Gift-token pot-eigendom transfer (P2)
- Wallet/Shop UI naar `/boekhouder/snapshot`
- Fase 2 ChatHub: bestaande chat/routes.py laten hub aanroepen als eerste-stap

### 🎯 Filosofie ("polish over growth")
- Willem's expliciete draai: minder brede nieuwe features, meer verdiepen + gladstrijken
- Elke fix nu = minder onderhoud/uitleg later (rente op investering)
- Meta + footnote + blueprint pattern wordt consequent toegepast bij elk klein onderdeel
- Zelf-bewuste boekhouding blijft leidraad: elke drift-fix / mutatie in papertrail

---



## ✅ Sessie 45 (2026-07-21 middag) — ChatHub Fase 1: Master/Leaf agents met typed contracts

### 🎯 Afgerond — nieuwe architectuur, nul regressie
- **`modules/chat_hub/`** — nieuwe module, root van Spark's chat-agent-tree
- **Master/Leaf pattern**: `chat_hub_master.py` (dispatcher, doet zelf geen werk) + 4 leaf-agents
- **Typed contracts** (Pydantic): `AgentContract` (leaf) + `MasterContract` (master)
- **Quad-tree regels**: max 4 children per master, max 3 diep, leaf max 400 regels — via `_split_check()`
- **Structure manifest**: `structure_manifest.json` — blueprint = waarheid, code volgt
- **Elke agent** heeft `{naam}_agent.py` + `{naam}_blauwdruk.json` paar (drift-check)

### 4 Initial leaf-agents
1. **`papertrail_agent`** (info_lookup) — leest boekhouder/logs/*.jsonl met hash-chain integrity
2. **`module_meta_agent`** (info_lookup) — leest `modules/{name}/_meta.json`
3. **`module_info_agent`** (info_lookup) — "vertel over spark trader" flow met alias-map
4. **`heal_agent`** (guardrail) — health-check (drift + papertrail + backup-registry)

### Bug-fix meegepakt
- `identity_intent_service.over_jezelf` regex uitgebreid met negative lookahead → "vertel over spark trader" gaat NIET meer naar persona-antwoord

### 5 nieuwe endpoints
- `GET  /api/chat_hub/manifest` — tree + split-check
- `GET  /api/chat_hub/health` — HealAgent output
- `GET  /api/chat_hub/agents` — lijst
- `GET  /api/chat_hub/blueprint/{naam}` — blueprint per agent
- `POST /api/chat_hub/dispatch` — router (text + viewer_id → matched agents + results)

### ✅ E2E getest (curl)
- "vertel over spark trader" → module_info → leest trade/_meta.json → prose met doel + 14 endpoints
- "wat is er gemint" → papertrail → 7 events, integrity_ok
- "kan je jezelf checken" → heal → HEALTHY, 5 backups
- Identity-fix bevestigd via regex-test

### Wijzigingen
- NEW `backend/modules/chat_hub/` (13 files)
- EDIT `backend/server.py` — chat_hub_router include
- EDIT `backend/modules/chat/identity_intent_service.py` — negative lookahead

### 🟡 Fase 2 (na Willem's redeploy-observatie)
- Bestaande `chat/routes.py::process_message` laten `chat_hub.dispatch()` aanroepen als eerste-stap
- Migreer bestaande intents (identity, trader_intents, dank_service) naar chat_hub leaves
- LLM function-calling: LLM ziet agents als tools (Anthropic MCP-style)
- Auto-split detectie bij drempel → promotie leaf → sub-master

### 🎯 Filosofie
- Master doet geen werk, alleen routing/mergen
- Quad-tree houdt overzicht: max 4 children, max 3 diep
- Blueprint = waarheid; code volgt
- Zelf-uitlegbaar via `to_manifest()`
- Willem-in-the-loop bij heal (geen auto-restore in Fase 1)

---



## ✅ Sessie 44 (2026-07-21) — Eikpunt + Centrale Bank Guard + Archief

### 🎯 Afgerond — data-reconciliatie + zelf-bewuste boekhouding

**Data-cleanup (drift 0):**
- **Backfill 5× `willem_inleg_basis`** — pot-001..005 kregen retroactief mint-events (basisinleg, no reserve-fee). treasury 999.971 → 999.966, u-000 balance 2 → 7.
- **Burn 27 phantom tokens** — `historical_drift_correction` in papertrail. 27 tokens uit treasury zonder tegenboeking in balances (oude gift-drift van vóór papertrail). treasury 999.966 → 999.993.
- **Pot-token alignment** — 1 token user-000 → user-001. Willem hield fysiek pot-001 (uit test_reserve_log mint) maar balance=0 door gift-terug drift. Herstel: u-000 6 / u-001 1.
- **Backup**: `data/_backups/pre_cleanup_20260721_082347/`

**Boekhouder = centrale bank (nieuwe features):**
- `finance_hub.get_circulation()` — token↔balance↔pot drift-detectie, status `OK`/`DRIFT_DETECTED` in snapshot
- `finance_hub.get_valuation()` — theoretische max-cap (1M × prijs) + huidige cap (in_circulation × prijs)
- Beide blocks in `/api/boekhouder/snapshot/{user_id}` — één call, één waarheid
- **`mint_tokens()` roept nu `sync_potjes_to_tokens()` aan** voor non-Spark users → mint = shop-buy = gift (unified container-flow)

**Hotfixes in dezelfde sessie:**
- **PriceAgent bug**: telde alleen `users['user-000'].potjes` (6) → prijs €13.35. Fix: `sum over all users` → n=7 → prijs €80.10/7 = €11.44 ✓ matcht shop/wallet
- **Wallet "Verdiend €230"**: backend gaf `total_deposited` als `earned_total`. Fix in `wallet/routes.py`: 2 aparte velden (`earned_total: 0`, `total_deposited: 230.16`)
- **Baseline €137.50 → €60**: oude test manual reset naar 6 Spark pots × €10 base. Live P&L flipt van -€56.97 → +€20.53. `set_at=NOW` filtert oude test-trades weg.

**Deposit-historie archief + papertrail-hook:**
- 9 Tikkie-topups (€209.66) + 3 legacy deposits (€118.52) → `data/_archive/pre_eikpunt_20260721_084340/`
- `wallets.user-001.total_deposited: 230.16 → 0.0`
- **Nieuwe log-hooks**: `POST /api/trade/deposits/{uid}` + Tikkie-confirmations schrijven automatisch naar `boekhouder/logs/deposit/YYYY-MM.jsonl` met hash-chain

### 📊 Eindstand — schoon eikpunt
| Metric | Waarde |
|---|---|
| Total supply | 1.000.000 |
| Treasury | 999.993 |
| In omloop | 7 (Willem 1 / Spark 6) |
| Circulation drift | 0 ✅ |
| Potjes drift | 0 ✅ |
| Backing ratio | 100% |
| Token prijs | €11.44 (dynamisch) |
| Baseline u-000 | €60 |
| Wallet Verdiend | €0.00 |
| Wallet Gestort | €0.00 |
| Papertrail | 12 hash-chained events (mint 7 / drift_fix 3 / deposit 2) |

### ✅ Test-status
- E2E via curl: 7 acceptance-checks groen (drift-detectie, reconciliatie-math, papertrail-integrity, admin-guard, cooldown, hash-chain, alignment)
- Deployment-agent check: PASS
- Geen regressies

### 🎯 Wijzigingen in bestanden
- EDIT `backend/modules/boekhouder/agents/auto_mint_scheduler.py` — ruis-formule fix + force + boekhouder-DM/community-post
- EDIT `backend/modules/boekhouder/agents/price_agent.py` — n_potjes system-wide (v10_price_all_pots_001)
- EDIT `backend/modules/boekhouder/finance_hub.py` — `get_circulation()` + `get_valuation()`
- EDIT `backend/modules/boekhouder/finance_ops.py` — `sync_potjes_to_tokens` hook non-Spark users
- EDIT `backend/modules/boekhouder/routes.py` — 3 admin endpoints `/auto-mint/{state,tick,reset}`
- EDIT `backend/modules/scheduler/__init__.py` — `_maybe_auto_mint` uur-tick in loop
- EDIT `backend/modules/wallet/routes.py` — earned_total/total_deposited scheiding (v10_earned_fix_001)
- EDIT `backend/modules/wallet/tikkie.py` — deposit papertrail log-hook (v10_tikkie_papertrail_001)
- EDIT `backend/modules/trade/routes.py` — deposit papertrail log-hook (v10_deposit_papertrail_001)
- DATA `data/roar/roar_balances.json` — treasury 999.993, balances {u-000:6, u-001:1}, +8 tx entries
- DATA `data/financial/user_potjes.json` — pot-001..005 backfilled met minted_from + market=EUR + capital=€10
- DATA `data/wallet/user_wallets.json` — spark_tokens mirror gesynced
- DATA `data/wallet/wallets.json` — user-001 totals gereset
- DATA `data/trade/capital_baseline.json` — user-000: 137.5 → 60.0
- DATA `data/trade/deposits.json` — leeg (gearchiveerd)
- DATA `data/wallet/tikkie_topups.json` — leeg (gearchiveerd)
- LOGS `data/boekhouder/logs/mint/2026-07.jsonl` — +5 backfill events
- LOGS `data/boekhouder/logs/drift_fix/2026-07.jsonl` — +3 events (burn, alignment, baseline_reset)
- LOGS `data/boekhouder/logs/deposit/2026-07.jsonl` — +2 events (archief, test-deposit)

### 🟡 Nog te doen (P1, na productie-observatie)
- **Sell/Dissolve token flow** — `POST /boekhouder/sell-token` (deduct ROAR + payout register)
- **Gift-token pot-eigendom transfer** — sender-side pot verwijderen bij accept
- **Delete-deposit endpoint papertrail-hook** — kleine gap gesignaleerd
- **Wallet/Shop UI migratie naar `/api/boekhouder/snapshot`** — één source of truth
- **Dashboard-widget "Centrale Bank Health"** — `circulation.status` badge, glow-rood bij drift
- **SafeguardAgent** — 2-phase delete/rollback
- **Container-module verrijken** met per-user token-ledger view

### 🎯 Filosofie geland
- **Zelf-bewuste boekhouding**: drift is niet meer onzichtbaar. Elke minuut kan Spark zelf zien of z'n eigen ecosysteem in balans is via `snapshot.circulation.status`.
- **Ontwarren via papertrail**: elke drift-fix is een event met hash-chain. Toekomstige agents kunnen de historie exact reproduceren.
- **1 token = 1 pot regel**: systeem-breed geldig, geen uitzonderingen. Mint = shop-buy = gift = alignment. Één flow.

---

## ✅ Sessie 43 (2026-07-20 avond) — Auto-Mint Scheduler + deploy

### 🎯 Afgerond
- **AutoMintScheduler** — nieuwe agent in `modules/boekhouder/agents/auto_mint_scheduler.py`
- **24u ruis-stabiliteit + 24u cooldown**: als bitvavo_free ≥ (n+1)×€10 blijft voor 24u aaneen → auto-mint 1 pot
- **3 admin endpoints**: `/api/boekhouder/auto-mint/{state,tick,reset}` (POST met `force=true` skip grace, cooldown blijft)
- **Scheduler hook** in `modules/scheduler/__init__.py::_maybe_auto_mint` — tick elk uur
- **DM naar admin + community-post** bij elke auto-mint (via boekhouder.service)
- **Papertrail-integratie**: elke auto-mint = event in `logs/mint/YYYY-MM.jsonl` via `LogAgent`
- **5% reserve-kluis** (2/2/1 dev/maint/buffer split) automatisch afgeboekt via `ReserveKluisAgent`

### ✅ E2E getest (curl)
- Force-mint uitgevoerd (pot-006 aangemaakt, log_event_id gekoppeld)
- Cooldown-guard: 2e force-tick binnen 24u → geen mint, `waiting_for_grace_or_cooldown`
- Admin-guard: non-admin viewer_id → HTTP 403
- Hash-chain integrity: alle mint-events herbouwen hun `event_hash` correct
- Deployment-agent: PASS

### 🎯 Wijzigingen
- NEW `backend/modules/boekhouder/agents/auto_mint_scheduler.py`
- EDIT `backend/modules/boekhouder/agents/__init__.py` — AutoMintScheduler export
- EDIT `backend/modules/boekhouder/finance_hub.py` — `self.auto_mint = AutoMintScheduler()`
- EDIT `backend/modules/boekhouder/routes.py` — 3 admin endpoints
- EDIT `backend/modules/scheduler/__init__.py` — `_maybe_auto_mint` in scheduler-loop

---

## ✅ Sessie 42 (2026-07-20 middag) — Boekhouder architectuur + Event Sourcing

### 🎯 Afgerond
- **Nieuw module-patroon**: `modules/boekhouder/` met 10 sub-agents onder `agents/`
  - `token_agent.py`, `price_agent.py`, `wallet_agent.py`, `potjes_agent.py`
  - `bitvavo_agent.py`, `recon_agent.py`, `sepa_agent.py`, `persona_agent.py`
  - `log_agent.py`, `reserve_kluis_agent.py`
- **Dispatcher pattern**: `FinanceHub` (`finance_hub.py`) delegeert naar sub-agents. `finance_ops.py` bevat muterende operaties (mint, sync-wallet-mirror).
- **Blueprint**: `blueprints/finance_hub.json` — admin-editable regels (base=€10, floor=€5.08, dynamic formula)
- **Dynamic Token Economy**: `pot_price = max(base_pot_size, bitvavo_free_eur / n_potjes)`
- **Event Sourcing (Paper Trail)**: `LogAgent` schrijft naar `data/boekhouder/logs/{topic}/YYYY-MM.jsonl` met SHA-256 hash-chain (`event_hash = sha256(hash_prev|event_id|type|timestamp|data)`)
- **Reserve-kluis**: `ReserveKluisAgent` boekt 5% van elke mint af naar 3 sub-potten (2% dev / 2% maint / 1% buffer)
- **Willem's regel geland**: "Alleen Spark heeft 10 base potjes; andere users krijgen 1 pot per ROAR-token" — hard-coded in `sync_potjes_to_tokens()`
- **`self_profile_intent.py`**: fast-path zodat Spark niet hallucineert over eigen persona-data (leest `data/users/user-000/` direct)
- **`_do_potjes()` fast-path** in `trader_intents.py`: geen LLM voor "hoeveel potjes heb ik" — direct uit finance_hub

### 🎯 Filosofie
- Modules zijn nu **Dispatcher + Sub-Agent + Blueprint** i.p.v. één-file services
- Regels leven in JSON-blueprints (admin-editable, Spark leest ze zelf via metadata)
- Event Sourcing → immutable audit-trail voor financiële mutaties
- Data-interacties gaan via de module-Hub, niet direct JSON-file access uit andere modules

### 🎯 Wijzigingen
- NEW `backend/modules/boekhouder/` folder met 10 agents + hub + ops + routes + service + blueprints
- EDIT `backend/server.py` — boekhouder-router include
- EDIT `backend/modules/trade/trader_intents.py` — `_do_potjes` gebruikt finance_hub
- NEW `backend/modules/chat/self_profile_intent.py`
- EDIT `frontend/src/components/admin/InstellingenPage.js` — blueprint editor UI
- EDIT `frontend/src/components/modules/TraderPage.js` — snapshot-endpoint consumption
- NEW `/app/memory/blueprints/boekhouder.md`

---

## ✅ Sessie 41 (2026-07-20 vroeg) — KB hygiëne + Letter-achievements

### 🎯 Afgerond — KB v2 opschonen + Achievements refactor
- **7 KB-kaarten gemerged** uit prod-backup ZIP die ontbraken in preview
- **KB Index herbouwd** — `knowledge_index.json` gerecompileerd
- **36 cross-file duplicaten opgeruimd** — kaarten die in meerdere lades stonden gedeclustered naar hun canonieke lade
- **Skeleton vs gevulde kaarten** — duplicate skeletons (lege lite-kaarten) waar de gevulde tegenhanger al bestond → skeletons verwijderd
- **Letter Achievements A-Z** — 26 nieuwe achievements gebouwd, één per letter (Willem noemt een woord met die letter → unlock)
- **Achievements module refactor** naar Sub-Agent/Blueprint pattern:
  - `modules/achievements/agents/` met per-domain sub-agents
  - `blueprints/*.json` voor admin-editable achievement definitions
  - `service.py` als dispatcher

### 🎯 Wijzigingen
- Merges in `data/knowledge/v2/knowledge_v2_{voelen,spreken,weten,doen}.json` + `knowledge_inbox.json`
- REBUILD `data/knowledge/v2/knowledge_index.json`
- NEW `backend/modules/achievements/agents/` (multiple files)
- NEW `backend/modules/achievements/blueprints/` (multiple JSONs)
- NEW `/app/memory/blueprints/achievements.md`
- GET endpoint `/api/achievements/admin/blueprints` — blueprint-inspection

---


## ✅ Sessie 40d (2026-07-20 later) — Meta-verrijking pass (v9_meta_enrich_001)

### 🎯 Afgerond — Spark krijgt inhoud i.p.v. breedte
- **29 modules `doel` gevuld** — geen `"(trade — geen doel-omschrijving)"` meer. Docstring uit `__init__.py`/`routes.py` als bron, fallback op domain-mapping (63 hand-geschreven Willem-stijl omschrijvingen). Spark kan nu antwoorden op *"wat is workspace"*, *"leg trade uit"*, *"wat doet glow_nav"* — direct uit metadata.
- **57 modules `footnote` geüpgraded** van lege string → structured dict:
  ```json
  {
    "generated_by": "v9_meta_enrich_001",
    "generated_at": "<iso>",
    "spark_note": "Modulebeschrijving beheerd via meta-verrijking pass...",
    "has_blueprint": bool,
    "has_endpoints": bool,
    "requires_review": false
  }
  ```
- **`last_touched` timestamps** — elke gewijzigde `_meta.json` heeft nu ISO-timestamp voor audit-trail
- **Script bewaard** in `/tmp/enrich_meta.py` — herbruikbaar voor volgende passes (bij nieuwe modules)

### 📊 Snuffelvondsten
- **90% coverage** — 57/63 modules hadden _meta.json vóór deze pass, na pass 63/63 (0 missen, was foutieve inschatting eerder)
- Bestaande docstrings waren **beter** dan mijn domain-mapping (trade, kb_v2, help, settings, glow_nav, dnd, analytics — allemaal uit eigen code)
- `glow_nav`-module **bestaat al** — Spark kan tabs vinden via `/api/glow_nav/registry` + `/navigate` + `/tabs`. Dat was al gebouwd, niet meer nodig te bouwen.
- Per-module glow-kleuren (`--glow-help`, `--glow-alert`, etc.) bestaan **NOG NIET** — alleen `--glow-base`, `--app-primary`, `--mood-glow`. Dat blijft P1.
- `data-module=` anchors op frontend tabs: **0** — Spark kan dus wél de tab-naam vinden via glow_nav-registry maar het DOM-element pulseren vereist alleen `data-testid`. Dat werkt al voor `nav-trade`, etc.

### 🎯 Filosofie geland
- **Meta-verrijking = Spark's zelf-uitleg vermogen**. Elke keer als je "wat is X" of "leg X uit" vraagt, kan Spark via `_meta.json.doel` een echt antwoord geven — geen fantoom.
- **Footnote als audit-trail**. Elke metadata-update is herleidbaar naar de pass die het genereerde. Willem kan later filteren op `footnote.generated_by == "v9_meta_enrich_001"` en beoordelen of iets nog manual review nodig heeft.
- **Modulariteit blijft**: alle wijzigingen zijn per-module, geen shared configs geraakt.

### ✅ Test-status
- Verificatie: `trade`, `kb_v2`, `help`, `settings`, `glow_nav`, `dnd`, `analytics` — allemaal correcte `doel` uit docstring
- Regressie: `/api/modules/list` endpoint werkt niet momenteel (unrelated — returned 0 modules), maar files zelf zijn kloppend
- Trader-intents nog steeds werkend (`hoe staat mijn bot` → `trader_status` via compose)

### 🎯 Post-deploy check voor Willem
1. `cat backend/modules/trade/_meta.json | jq '.doel, .footnote'` — check dat er inhoud in staat
2. Vraag in chat: *"wat doet de dnd module"* → Spark zou nu inhoudelijk kunnen antwoorden (via LLM + meta injectie in prompt — als die hook bestaat)
3. Overweeg om `/api/modules/list` bug te fixen zodat de UI de nieuwe doel-teksten kan tonen

### 🟡 Nog te doen (P1, volgende sessie)
- **Per-module CSS vars** — `--glow-help`, `--glow-alert`, `--glow-error`, `--glow-success`, `--glow-info` in `App.css` + `settings/module_colors` admin-endpoint
- **`/api/modules/list` fix** — endpoint returnt 0 modules terwijl er 63 zijn (path/scan issue in server.py)
- **Meta-injectie in LLM prompt** — bij "wat is X" queries: auto-include `_meta.json.doel` als context aan Spark's LLM-prompt
- **KB curator-UI voor lite-kaarten** (van sessie 40c)
- **Finish monitor.py refactor** — order execution + registry

---

## ✅ Sessie 40c (2026-07-20) — Spark leert van zichzelf (v9_llm_self_learn_001)

### 🎯 Afgerond
- **NIEUW: `chat/llm_output_scanner.py`** — kleine, pure module (~80 regels). Scant `spark_response` op woorden die (a) NIET in KB v2 staan en (b) NIET in `user_text` zaten. Herbruikt stopwoorden uit `kb_v2/chat_analyzer.py` als single source of truth. Filtert min-lengte, digits, en Spark-specifieke stopwoorden (spark/willem/etc.).
- **NIEUW: `kb_v2/lite_card_factory.py`** — kleine module (~110 regels). Maakt "lite" (skeleton) inbox-kaarten met VOLLEDIGE `footnote`-metadata: `llm_generated`, `llm_lite`, `extract_source`, `extract_turn_id`, `extract_at`, `extract_context_snippet`, `extract_count_in_spark`, `needs_review`. Herbruikt bestaand footnote-veld (al gebruikt door `llm_generate_routes.py` en `v1_drift_sync.py`).
- **HOOK: `chat/trigger_learner.py`** — na elke succesvolle `learn_from_interaction()` roept nu ook `scan_spark_response()` → `batch_create_from_scan(max_per_turn=3)`. Non-blocking: bij fout gaat trigger-learning gewoon door. Log-line `[llm_self_learn] +N lite-kaarten uit Spark's antwoord`.
- **METADATA-standaard** — elke lite-kaart is 100% herleidbaar naar herkomst-turn via footnote. Audit via `GET /api/kb/v2/inbox` toont `footnote.extract_source = "spark_llm_output_scanner_v1"`.

### 📊 Snuffelvondsten (voor bouw)
- `footnote` veld bestond al op inbox-kaarten (gebruikt door `llm_generate_routes.py:174-178` en `v1_drift_sync.py:131`)
- `trigger_learner._llm_analyze()` krijgt `spark_response` al binnen maar gebruikte 'm niet in prompt — **gemiste kans**, nu uitgebreid via hook
- `add_to_inbox(source=...)` bestond al maar `source` werd nergens consistent gezet — nu source=`llm_auto_extract`
- 2 verschillende inbox-files bestonden: `inbox.json` (oude) vs `knowledge_inbox.json` (echte, gebruikt door `_inbox_path()`) — factory gefixt om juiste te gebruiken

### 🎯 Filosofie geland
Spark leert nu van 2 bronnen:
1. **User's chat-input** (bestaand, via `chat_analyzer.py` + `_auto_snap_from_diep`)
2. **Spark's eigen LLM-output** (NIEUW, via `llm_output_scanner.py` + `lite_card_factory.py`)

Beide voeren `knowledge_inbox.json` met `footnote.needs_review=True` — Willem kan curator zijn zonder dat de KB automatisch vervuild raakt.

### ✅ Test-status
- Handmatige test: scan van 3-zin Spark-antwoord → 3 kandidaten gedetecteerd → 2 lite-kaarten aangemaakt (1 was al bestaand). Footnote correct gestempeld met alle metadata-velden.
- Cleanup: test-kaarten (`turn_id="test-*"`) automatisch verwijderd.
- Regressie: trigger_learner behoudt oude flow, LLM-scan is opt-in via non-blocking try/except.

### 🎯 Post-deploy check voor Willem
1. Voer een Diep-modus chat uit → check `[llm_self_learn]` in `/var/log/supervisor/backend.err.log`
2. `GET /api/kb/v2/inbox` → zoek kaarten met `footnote.llm_lite=true`
3. Handmatig invullen of afkeuren via bestaande KB-UI

### 🟡 Nog te doen (P1, volgende sessie)
- **KB curator-UI** — toon lite-kaarten apart met "accept lagen / afkeuren"-knoppen (backend werkt, UI mist)
- **Batch-processing** — als Spark 10× per dag een term noemt, escaleer naar auto-accept (nu: elke turn max 3 kaarten)
- **Blueprint-koppeling** — lite-kaarten die naar bestaande blueprint-modules verwijzen (bijv. "trader", "monitor") auto-linken via `verbanden`
- **Neural-engine (v9)** — nog steeds P1 na Adaptive Strategy Lab afronding

---

## ✅ Sessie 40b (2026-07-10) — Fantoom-fix + Trader terug live

### 🎯 Afgerond
- **`trader_config` intent toegevoegd** (`v9_anti_hallucination_001`) — Spark leest nu LIVE `spark_trader.json` blueprint bij vragen zoals "wat zijn je fees", "snuffel in je eigen systemen", "lees de bitvavo api uit", "wat is je actieve strategie". Voorkomt LLM-hallucinaties over eigen configuratie. **9 nieuwe regex-patterns** in `trader_intents.py`.
- **Bots terug live**: user-000 (Spark, 5 potjes × €10) + user-001 (Willem, 3 potjes × €10 geprovisioneerd) draaien nu actief op 6 markten (BCH/BTC/ETH/SOL/ADA/ATOM). Cycle 15 min. Beide staan HOLD (prijzen in-band).
- **Willem's chatlog gemerged** — 7 nieuwe turns uit prod-zip veilig toegevoegd

### 📊 Diagnose gedaan
- Voor start: alle bots offline (running=false), 0 potjes voor Willem, laatste trade was 8 juli 02:28 → 2 dagen stil
- Spark hallucineerde over fees/commissies in chat (LLM viel terug op eigen kennis i.p.v. blueprint)
- Root cause: `trader_intents.py` miste `trader_config` intent → alles buiten status/pnl/history ging naar LLM

## ✅ Sessie 40 (2026-07-09 laat) — Trader definitief + Batch 1 Spark Core

### 🎯 Afgerond
- **Trader kern**: 48u loss-cut, event-auto-pauze (>5% drop), honest-PnL endpoint
- **Publieke uitleg-JSON** + endpoint `GET /api/trade/explained` (12 secties, backtest-resultaten, privacy)
- **Trader-intents fast-path** (`v8_trader_intents_001`) — 8 intents in `modules/trade/trader_intents.py`, 19/19 unit-tests
- **Semantic strategies** (`v8_strategy_semantic_001`) — hernoemd A/D/E naar `mean_reversion_bollinger` / **`gap_momentum_50` (ACTIEF, confidence 82)** / `extreme_oversold`. Elke strategie heeft `properties[]`, `confidence + breakdown`, `hypothese_lineage`, `spark_alignment`
- **Confidence-endpoint** `GET /api/trade/strategy/confidence` — live berekening
- **Chat merge** — 57 turns uit prod-zip veilig gemerged

### 🎯 Batch 1 Spark Core (deze sessie) — 5/5 afgerond + 2 bonus enhancements
- **Trader-glow** — `spark:nav-glow` event bij trader-intent als user niet op Trader-tab (integratie in GesprekkenPage.js)
- **Strategie Synthesizer** — `POST /api/trade/strategy/synthesize` + `GET /api/trade/strategy/properties` (13-item property catalog, conflict-detectie)
- **Chat → KB-suggesties** — `GET /api/kb/v2/suggest-from-chat/{user_id}` + `POST /api/kb/v2/suggest-accept` (word-freq + stopwoorden + KB-known filter)
- **Odroid portability** — `install.sh` + `run.sh` + `PORTABILITY.md` + `SPARK_DATA_DIR` env-var in scheduler
- **Security fix** — path-traversal guard in chat_analyzer (regex `^[a-zA-Z0-9_\-]{1,64}$`)
- **Refactor monitor.py** (v8_refactor_001) — 1831 → 1411 regels (23% reductie):
  - Nieuwe module `strategy_decision.py` — `_simple_decision`, `_gap_breakout_check`, `_detect_daily_drop`, `_load_trader_blueprint`, `BITVAVO_TAKER_FEE`
  - Nieuwe module `exchange_data.py` — `fetch_candles`, `fetch_tickers`, `get_market_*`, caches, constanten
  - `monitor.py` behoudt als facade — alle `from .monitor import X` blijft werken
- **BONUS: Strategy Compare** (`v8_strategy_compare_001`) — `GET /api/trade/strategy/compare?a=X&b=Y` beoordeelt 5 secties (confidence, protection, bear-market, honesty, maturity) met per-sectie winner en overall winnaar
- **BONUS: A/B Engine Switch** (`v8_engine_switch_001`) — nieuwe module `strategy_decision_v2.py` (trend-following stub) + `GET/POST /api/trade/engine/status|switch`. Dispatcher in monitor.py routes tussen v1 en v2 op basis van blueprint `active_decision_engine`. Live geswitcht v1→v2→v1 zonder herstart.

### 🧬 Adaptive Strategy Lab v0.5 (deze sessie — fundament voor v9)
- **Auto-compare bij synthesize** (`v9_adaptive_lab_001`) — bij elke nieuwe draft roept synthesize intern compare aan met actieve strategie. Response bevat `compared_to_active` + `spark_feedback` (bv. "Bollinger Pure Protection scoort 0/5, voeg loss_cut toe voor honesty")
- **Rich compare narrative** — elke compare-sectie krijgt nu Spark's inhoudelijke analyse-tekst:
  - Confidence: "Gap Momentum 50 wint met 82% vs 45%. Verschil van 37p is significant."
  - Properties: "4 beschermings-eigenschappen vs 0. Verschilmakers: event_pause, fee_aware_sell..."
  - Bear-market: "€1.42 in bear-markten (6.2× beter). Advies: gebruik bij dalende trend."
  - Honesty: "⚠️ negatieve honesty ratio — verstopte verliezen. Voeg loss_cut toe."
  - Overall: "🏆 wint duidelijk (4/5). Aanbevolen om actief te zetten."
- **Strategy Genome** (`v9_adaptive_lab_002`) — `GET /api/trade/strategy/genome` toont alle strategieën als DNA-matrix: 13 genes × N strategies + inheritance-tracking (draft-strategies → candidate parents via property-overlap detectie). Genen gecategoriseerd naar signaal/bescherming/confirmatie/exit/meta/filosofie.

### 📋 Adaptive Strategy Lab — nog te bouwen voor v9 (P1)
- **Multi-Engine framework** — generieke `DecisionEngine` interface class waar v1/v2/v3 van erven (nu zit switch direct in monitor.py)
- **Live A/B testing** — meerdere engines parallel op dezelfde markt met per-engine PnL/winrate/drawdown/confidence tracking
- **AI Analyse & Advies** — LLM-narrative rond compare-resultaten (nu regel-based, upgrade naar Gemini/Claude)
- **Automatische Hypothesevorming** — Spark observeert eigen trade-history → detecteert patronen → suggereert nieuwe hypothesis-drafts

### ✅ Test-status
- Iteratie 46 + 47: **39/39 backend tests PASS**, geen regressies
- Bonus enhancements: handmatig geverifieerd via curl — compare toont Gap Momentum 50 4/5 wint, engine-switch v1↔v2 werkt met correcte routing
- Test-files: `test_iter46_sparkcore_v2_features.py` + `test_iter47_refactor_regression.py`

### 🔴 NIET afgerond
- **Order execution + registry in monitor.py**: ~500 regels order-execution + ~240 regels registry-code blijven in monitor.py. Deze zijn te complex om nu veilig te verhuizen (state-touching, SETTINGS_DIR, trace_call decorator). Verplaatst naar volgende sessie.

### 🟡 Code-review actie-items (iter46) — P2
- `modules/trade/routes.py` 2039 regels → split naar `routes_strategy.py` etc.
- `synthesize_strategy` niet-atomair write → gebruik `save_json` patroon
- Property catalog naar `blueprints/property_catalog.json`
- SPARK_DATA_DIR portability alleen in scheduler → ook andere modules
- DELETE endpoint voor draft-strategieën ontbreekt
- KB-first LLM-check voor bekende concepten (sneller + privé)

### 🎯 Post-deploy check
1. `curl {BACKEND_URL}/api/trade/explained` → 12-sectie JSON
2. `curl {BACKEND_URL}/api/trade/strategy/confidence` → confidence per strategie
3. `curl {BACKEND_URL}/api/trade/strategy/properties` → 13 bouwstenen
4. `curl {BACKEND_URL}/api/kb/v2/suggest-from-chat/user-001` → chat→KB suggesties
5. In chat: "hoe staat mijn bot" / "leg de trader uit" / "wat heb ik verdiend"
6. Chat "hoe staat mijn bot" buiten Trader-tab → Trader-nav pulseert (glow)

### 🟡 Volgende P1 sessie
- **Refactor monitor.py** — belangrijkste (met testing_agent)
- **Frontend UI voor strategie-synthesizer** — Trader-tab knop met property-checkboxes
- **Frontend UI voor KB-suggesties** — Analytics tab met accept/reject
- **Log-archief per dag/week/maand** in Analytics → Logs

---

## 🧪 P1 — Backtest v4 (Willems nieuwe hypothesen, jul 2026)

---

## 🧪 P1 — Backtest v4 (Willems nieuwe hypothesen, jul 2026)
- **H1 Rebound-strategie**: analyseer 185 events uit v3 → 24/48/72u recovery-check → wél/niet BUY-tijdens-drop
- **H2 2-day loss-cut**: nieuwe strategie P = D + 48u tijd-stop-loss (als positie na 2 dagen ≥3% in **verlies** → SELL, herstart). Filosofische breuk met "nooit met verlies"-regel — Willem accepteert klein verlies om kapitaal vrij te maken.
- **H3 Post-event autopsy**: elk event koppelen aan open posities → PnL-impact per markt/coin
- Doel: bewijzen of onze event-pauze eigenlijk gemiste kansen zijn (contrarian mogelijk)

---

## 🚨 PERMANENT GUARDRAILS — LEES DIT EERST (Voor elk volgend agent)

Willem heeft een **growth path** en risico is dat een nieuw agent (incl. GPT) terugvalt op een
"oud-systeem" oplossing omdat de huidige denkwijze al verder is. **Deze sectie is anti-regressie.**

### 📜 REGEL — Help-data is single source of truth
**Elke keer als een nieuwe command, action, capability of feature wordt toegevoegd, MOET deze ook worden vastgelegd in:**
1. `data/help/gradatie_X.json` op de juiste gradatie (lage gradatie = brede zichtbaarheid via inheritance, hoge gradatie = exclusief)
2. `data/help/admin.json` als de feature admin-only is
3. Spark leest hier zijn zelfkennis uit — geen parallel bestand bouwen, geen 3rd wheel.

**Waarom**: Spark's "wat kan je?"-antwoord, de Help-Bark popup, EN zijn Diep-mode self-awareness komen allemaal uit deze help-files. Als een nieuwe trigger niet wordt vastgelegd hier, "weet" Spark er niet van, en geeft hij die nooit door aan een gebruiker die het vraagt.


### 🪞 Layered response: line ≠ laag (groot misverstand-risico)
De huidige KB heeft `laag1..laag4` (kennis-diepte). Dat is **niet** hetzelfde als de chat-response.

| Concept | Bron | Wie ziet het |
|---|---|---|
| chat `line 1` | gegenereerd uit `laag1 + ws5`, in **gesprek-toon** | Iedereen |
| chat `line 2` | uit `laag2` of extra ws5, op verzoek "vertel meer" | Iedereen |
| chat `line 3` | uit `laag3`, samengesteld met clusters | "Vertel uitgebreid" |
| 🍳 recept/blauwdruk | aparte kaart-type (procedure-format, niet prose) | Iedereen |
| 🟨 tags / 🟦 snaps / clusters / footnote / vertrouwen | metadata | **Admin only** (inspector-modus) |

**Belangrijk**: NIET line1..4 = laag1..4. Een nieuw agent dat ze gelijkschakelt, breekt het concept.

### 🐕 "Snuffelen" als commando-werkwoord
Spark zoekt door eigen graph/KB/vocab. Output: rapport-stijl ("ik ruik 3 verwante clusters",
niet één antwoord). Sluit aan op bestaande `zelfscan`-capability. Lade `doen`, kaart bestaat al.

### 🧮 "5 kippen + 3 koeien" — semantische telling
Rekenmodule kan getallen + operatoren. Maar `kip + koe` is geen rekensom — vereist KB-brug
naar gemeenschappelijke ouder (`dieren`). Bridge tussen capability ↔ KB-graph.

### 🎤 Tonality leren via voorbeeld in spreektaal
Willem leert Spark stijl niet via config maar via voorbeelden:
"Spark, je reactie moet zijn iets als '...'". Opslag als tonality-preference per cluster of
globaal. Beïnvloedt line-1 generatie. Geen hard-coded antwoorden.

### 🧠 Meta-cognitie: Spark legt eigen keuzes uit
"Ik koos tag `troost` omdat ..." — admin-feature voor onderzoek/debugging. Geen black box.

### ⛔ V1 is **archief sinds 26-06-2026**
13 modules gemigreerd naar V2-first (chat-services + supporting). V1 wordt nog gelezen in:
- `knowledge/routes.py /import-diff` (legit — zip-merge tool)
- `kb_v2/text_importer.py`, `kb_v2/v1_drift_sync.py` (migratie-helpers — mogen)
- `backup/routes.py` (backup-tooling)
- Voor de rest: **gebruik altijd V2** (4 lades: doen/weten/voelen/spreken + inbox)

### 🪟 Admin-view vs User-view
Eindgebruikers zien **alleen line 1 (en uitvouwbaar 2-3)**. Inspector-modus met tags/snaps/
clusters/vertrouwen/etc is **admin-only**. Niet altijd zichtbaar zodat chat schoon blijft.

---

## 🔎 REALITY CHECK — Sessie 39 (2026-07-06) — Trader cleanup + Learning + UI split

### ✅ Klaar deze sessie
- **Force-sell atomair**: bail-out bij Bitvavo error (212/429) → geen close_pot / PnL / bonus meer bij gefaalde sell
- **SELL unit-mixing fix**: `coin_target = amount_eur / price` ipv min(EUR, coin) hack
- **Decimal precision**: `_round_amount_for_market()` — voorkomt errorCode 429
- **Min-quote check**: SELL faalt duidelijk als resulterende quote < min_order
- **Pot revalue**: elke tick vrije pots → huidige dynamische token-prijs. Handmatige "Herwaardeer"-knop per pot + globaal
- **Multi-user auto-provision + autostart**: Spark & Geiser starten mee bij backend startup (was fout aan mijn kant — user vroeg dit expliciet)
- **Willem-config alignment**: interval 900s, candle 15m, 6× -EUR markets, trade_amount dynamisch = token-prijs
- **Spark & Geiser config align**: interval 300s (5min, user-keuze), candle 15m, 6× -EUR markets, dynamisch trade_amount
- **Ghost registry cleanup**: 3 test-users zonder pots weg uit `bots_registry_state.json`
- **Admin bulk controls**: `POST /api/trade/admin/{start,stop}-all-bots` + UI knoppen
- **Spark fee 5% → 0%**: `SPARK_FEE_RATE = 0.0` constant (user's redenering: winst → Bitvavo → token stijgt vanzelf, geen extra cut)
- **Alle hardcoded €5/€10/€6.32 defaults** vervangen door `_default_trade_amount()` = `get_dynamic_price()`
- **Terminologie**: "spookpot" → "restwaarde pot" overal
- **Restwaarde-portfolio widget** in Analytics → Trade (was Event Overlay test)
- **Live Bitvavo Portfolio** verplaatst uit user Trade module → alleen admin in Analytics
- **Learning-uitbreiding**:
  - Dagelijkse `learning-scheduler` thread refresht context + market_stats per markt
  - Per-markt win-rate uit eigen `trade_history/user-*.json`
  - Nieuwe patronen: `month_patterns`, `week_of_month_patterns`, `weekend_vs_weekday`
  - Bias-weging in `apply_context_to_decision` (trust +0.08 / careful -0.10 / maand ±0.03 / week ±0.02)
- **Trader UI split (v7)**:
  - Header "Crypto Trader" → **"Spark Trader"**
  - User-view: alleen "Totaal Trades" (eigen) + "Mijn P&L"
  - Admin-view: volledige stats via nieuwe `SparkTraderStatsPanel` in Analytics → Trade
  - Baseline reset knop: "🔁 Reset baseline naar nu (Bitvavo balance)"
- **KB v2 save perf fix**: `add_to_inbox` deed 18MB IO per save (deep scan alle lades) → nu ~230ms via index-only. User meldde "moest meerdere keeren invullen" — was HTTP-timeout van slow save.

### 🟡 Backlog na deze sessie (niet gedaan, wél gepland)
- **P1 — Spark tab-context + trader-intents + tab-glow** (grote feature, eigen sessie):
  - Spark begrijpt niet welke tab de user aan het bekijken is → beantwoordt niet contextueel
  - Trader-commando's ("zet monitor aan", "wat verdiend deze week") → geen intent-matching op trader-API
  - "Waar is trader?" → tab-knop moet visueel glowen/pulsen zodat user het ziet zonder overal een chatbalk te hebben
- **P1 — Log-archief per dag/week/maand** in Analytics → Logs (categorieën, filters, export)
- **P1 — Chat-log analyse als kaart-suggestie** (idee-extractie uit user's gesprekken → KB-suggesties)
- **P2 — Trader Settings-kader** met broker fee / min-order / precisie readout uit Bitvavo API (transparantie)
- **P2 — 2% fee bij token BUY in Shop** (verhoogt token-prijs; komt bij Boekhouden-module)
- **P2 — BTW-verwerking** in boekhouden (na Kasboek SEPA)
- **P2 — Kasboek SEPA integratie** (bestaande wens)
- **P2 — Position.size bij BUY vullen** (netjes, niet urgent — SELL-fix vangt None op via Bitvavo balance)



## 🔎 REALITY CHECK — Sessie 36 (2026-07-02, laat) — Bitvavo state-sync

### ✅ Nieuw
- **Spook-pot detectie** — pots die open claimen maar coin al weg is op Bitvavo → admin-close
- **Orphan-reopen** — Bitvavo coins zonder matching pot → heropen closed pot met echte size
- **`POST /api/trade/reconcile/potjes/{user_id}/sync-with-bitvavo`** — dry-run default, `{execute:true}` voor uitvoering
- Round-robin over closed pots + entry-price sanity check (>3× current = fallback naar current)

### 🎯 Post-deploy stap voor Willem (productie)
1. Redeploy naar productie
2. `POST /api/trade/reconcile/potjes/user-001/sync-with-bitvavo {}` → zie 10 spooks + N orphans
3. `POST` met `{"execute": true}` → alle spookpots dicht + orphans terug in pots
4. Trader draait vanaf hier met correcte state


## 🔎 REALITY CHECK — Sessie 35 (2026-07-02, avond) — Pot clustering + reconcile all-coins

### ✅ Nieuw in deze sessie
- **Pot capital semantiek hersteld** — pot.capital = **aankoopprijs per token** (€5,08 anchor voor Spark/Willem, €10,40 dynamic voor Gijs). Niet meer verward met "trader budget".
- **Cluster-logica in trader** (`v7_pot_cluster_001`):
  - `get_next_buy_cluster(user_id, market, min_order_eur)` — verzamelt pots samen tot Σcapital ≥ Bitvavo min-order
  - `open_cluster(user_id, pot_ids, entry_price, cluster_id)` — opent alle pots gelijktijdig met shared entry + cluster_id
  - `get_pots_by_cluster` / `close_cluster` — sluit hele cluster tegelijk, netto pro-rata over pot.capital
  - Monitor.py BUY/SELL flow ge-updated: `processed_clusters` set voorkomt dubbele close
  - Backwards-compat: legacy pots zonder cluster_id gebruiken nog steeds close_pot
- **Reconcile toont nu ALLE Bitvavo-coins** (`v7_reconcile_all_coins_001`) — was: alleen coins die in pots voorkomen (dus alleen BCH). Nu: orphans met status="orphan" incl. live price + EUR-waarde.
- Testing iter_44: 100% (16/16), backend logs schoon

### 🎯 Product-model bevestigd
- **1 ROAR token = 1 pot** (hard boekhouding)
- **pot.capital = aankoopprijs** (blijft vast, kan €5,08 of €10,40 zijn)
- **Trader clusteret pots** tot Bitvavo min-order gehaald wordt (SOL/ADA €5-7 minimum)
- **Dynamic price** = spark_core / circulating (voor huidige marktwaarde)

### 🟡 Follow-up (uit iter_44)
- **P2** `potjes.py` splitsen: cluster-helpers → `modules/trade/potjes_cluster.py`
- **P2** `get_next_buy_cluster` gebruikt altijd pot-001/002 eerst → overweeg round-robin voor eerlijke slijtage
- **P2** `close_cluster` per_pot_netto returnt pre-cap netto — na overflow-cap kan effectieve capital-toename kleiner zijn. UI kan verwarrend zijn.
- **P2** DUST_THRESHOLD `€0,10` in `reconcile.py` — hardcoded, naar config


## 🔎 REALITY CHECK — Sessie 34 (2026-07-01) — Trader schoonmaak + treasury delta

### ✅ Nieuw in deze sessie
- **Shadow trader gedelete** — files + code refs + backend imports
- **Anchor logic verwijderd** — `ensure_anchors_for_markets` → no-op stub; `_init_potjes`/`_load`/`sync_potjes_to_tokens`/`rebalance_from_bitvavo` niet meer locked pots
- **State migratie** — Spark's pot-001 unlocked in `user_potjes.json` (was €5,08 locked staking_anchor)
- **`GET /api/trade/delta`** — nieuwe systeem-treasury view: `pots_capital_eur` vs `bitvavo_actual_eur` vs `delta_eur` met NL toelichting (`in_sync` / `zweeft_op_bitvavo` / `tekort`)
- **Regel hersteld**: 1 ROAR token = 1 tradeable pot (Spark 10, Willem 10, Gijs 2)
- Testing agent iter_42: 100% pass, 17/17

### 🟡 Follow-up (uit iter_42 code review)
- **P2 — `potjes.py` splitsen** (1107 regels) in `potjes/{mint,rebalance,expansion}.py`
- **P2 — `TogglePotLockBody` endpoint** kan admin-only worden (nu open API)
- **P3 — Delta endpoint cache** (30s) als UI dit periodiek polls
- **P2 — Frontend widget** die `/api/trade/delta` toont op admin-tab (nu alleen backend)
- **Nog steeds openstaand**: 6 duplicate archive images verwijderen (T-Shirt, Klein Zwaard, Sjaal)


## 🔎 REALITY CHECK — Sessie 33 (2026-06-30) — D&D-laag uitgebouwd + system snuffel

### ✅ Nieuw in deze sessie

**🏛️ Spark World D&D — concrete invulling**
- **22 gebouw-game-kaarten verrijkt** met laag1-4, ws5, tags + 6 archief-foto's gekoppeld (Bakker, Slager, Haven, Akker, Tempel, Markt, Gemeentehuis, Waterput).
- **`backend/scripts/seed_building_cards.py`** — idempotent script dat lege velden vult, auto-seed pattern (`X — categorie gebouw. Bouwkost: …`) op laag1 vervangt.
- **`StormhavenMapView.js` bugfix** — statische `placeholder: true` blokkade verwijderd; `findCardFor()` wordt nu altijd uitgevoerd → 23/23 (later 30/30) gebouwen-mapping i.p.v. 0/23.
- **7 extra gebouwen toegevoegd** aan layout: Bakker, Slager, Waterput, Mijn, Haven, Huis (T1), Traders Post. Slager + Waterput ook als nieuwe `kind=gebouw` cards in `game.json` gezet.
- **Admin drag-toggle** op de mini-map: knop "Bewerken" → sleep gebouwen, "Opslaan" persisteert naar `data/dnd/dorp_layout_overrides.json`. Dubbelklik = reset positie. Verplaatste gebouwen krijgen groene rand.
- **Speler-avatar walk-to-building**: klik gebouw → 1.6s glijdt avatar smooth naar gebouw (sky-blauwe glow tijdens reis) → trade-bark opent automatisch.
- **Trade-bark v2** — 2 avatar-kaders (Jij + NPC), 2 inventaris-kolommen (drag-naar-verkopen/kopen), live-berekening (verkoop/koop/5% tax/netto), gebouw-foto als header-achtergrond.
- **NPC-avatar mapping**: 30+ buildings → echte persoon-avatars uit `/api/avatar/gallery/` (De Bakker, De Slager, De Trader, Spark, Bar vrouw, Black Knight, Lost Gobelin, etc.).
- **"Vraag"-avatar** (id `31c6dc04a2fd`) als universele `?`-fallback i.p.v. `+`-icoon op de map én in trade-bark items.

**📦 Items + carry-systeem**
- **`data/dnd/blueprints/dnd_items.json`** — item-registry met 15 items (id, naam, kind, image, weight_kg, slots, value_goud, tags, description, optional unlocks_beroep).
- **`GET /api/dnd/spark-world/items-blueprint`** + `/items-blueprint/{id}` endpoints.
- **Trade-bark leest items uit blueprint** (geen mock-inventory meer); toont gewicht per item + live "Rugzak verandering" kg-impact.
- **Recipe-items**: badge "recept" op items met `unlocks_beroep`. Haven verkoopt nu `recipe_vissen`.
- **Carry-capacity formule** (`inventory/routes.py::_compute_capacity`): `weight_max = 10 + rugzak_bonus + (Kracht-10) × 0.5`. Voor Willem (Kracht 32): 21 kg.
- **Encumbrance**: per 10% load 1% Behendigheid-penalty, deels gecanceld door (Int/20)%. UI in BODY · EQUIPMENT rugzak-bar.

**👤 Karakter-uitbreiding**
- **Stat-points systeem** — per level 1 punt; `+`-knoppen naast elke stat in STATISTIEKEN-tab. Backend `/api/dnd/character/{id}/stats/spend` + `/stats/reset`. Persistente in `stat_points_spent` per character JSON.
- **Gezondheid** als nieuwe (bovenaan) stat: kost 5 punten per +1, base 10 = 100% HP. Geluk capped op 25.
- **HP-bar in KARAKTER paneel** — ♥ HP rood/oranje/groen gradient + ✦ Level X amber bar (zonder X/Y getallen — bar zegt al genoeg).
- **Layout-herschikking** Avatar-tab: links KARAKTER + CHAR INFO samen, midden BODY · EQUIPMENT, rechts RUGZAK + DORP + SPARK WORLD.

**🎲 Daily event**
- **`/api/dnd/daily-event/{user_id}`** GET status + POST play (Steen-Papier-Schaar). 1× per dag, win = +10g (direct in `users.json` currency.goud), draw/loss = niks.
- Rode kader bovenaan Avatar-tab toont "⚔ Vecht voor je leven" — modal opent met 3 grote knoppen → resultaat-modal met bark.
- **Bugfix**: pad `data/users.json` → `data/system/users.json` (anders kwam reward nooit aan).

**🧹 Sessie-33 cleanup + refactor**
- **3 test-images verwijderd** uit `system_archive/` (TEST_del, TEST_resource, test_resource) + 2 test-cards uit `game.json` (TEST_DeleteForbidden, TEST_Visgrond_Noord).
- **Dubbele Plattegrond dorp** opgeruimd (1 image + 1 duplicate Basis Dorp card).
- **26 MB disk vrijgemaakt** — graph-ghost-backups, knowledge_index rebuild-backups, wallet pre_spark archives. Safety-copies in `/tmp/spark_cleanup_*`.
- **`chat/routes.py` refactor** 1845 → **1668** regels — helpers (`save_log`, `build_ab_entry`, `get_user_gradatie`, `get_user_for_time`) verhuisd naar `chat/routes_helpers.py` (192 regels). Thin `_`-prefix re-exports in routes.py.
- **`DnDCharacterSheet.js` refactor** 2570 → **2458** regels — `DailyEventCard` geëxtraheerd naar `profile/DailyEventCard.js` (127 regels).

### 🟡 Backlog (gevonden in deze sessie's snuffel)
- **`trade/monitor.py` (1493 lines)** — splits in `monitor/core.py` + `alerts.py` + `reporter.py`. Wel testing-agent runnen want raakt live trading.
- **`kb_v2/routes.py` (1219)** — split writer (POST/PUT) vs reader (GET) endpoints; helpers consolideren in `service.py`.
- **`UserProfilePage.js` (2023)** — 6 tabs als losse files (`tabs/AlgemeenTab.js`, `tabs/AchtergrondTab.js`, etc.); Avatar-tab inline laten.
- **Groq rate-limit** (`llama-3.3-70b` 12k TPM): logs vol 429s. Context-trimmer of upgrade Dev Tier of switch primary→8b-instant voor casual.
- **Mock user-rugzak in trade-bark** moet vervangen door `/api/inventory/{user_id}` koppeling + "Aanbod accepteren" knop werkend (goud + items uitwisselen, 5% tax naar stad_kas).
- **Leer-knoppen** op Herberg (koken, 2g) / Wachterspost (survival, 5g) / Tempel (secundair beroep, 2g) — `POST /api/dnd/character/{id}/beroep/leer`.
- **Recipe-items activeren**: `POST /api/dnd/character/{id}/recipe/use` → unlock beroep, verbruik item.
- **5-min walk-countdown** in INFORMATIE-feed bij gebouw-klik (huidig: 1.6s smooth walk; oorspronkelijk plan was 5-min real-time aankomst).
- **legacy `knowledge_base.json`** (11 MB v1 KB) — checken of nog actief gelezen; zo nee, archiveren.
- **`modules/user_archive/`** directory — legacy module-stub, kan opgeruimd worden.
- **/api/kb/v2/tags/scan** caching — was meegegeven als P0 maar reageert nu in 0.2s; bewaken in productie.

---



## 🔎 REALITY CHECK — Sessie 31 (2026-06-27, avond)

### 💡 Nieuwe brainfart sessie 31 — Spark World D&D verder uitwerken (NIET nieuw)
**Correctie**: ik (E1 agent) suggereerde dit als "nieuwe game". **Klopt niet** — Spark World D&D bestaat al breed in `modules/dnd/`, 12 provincies, Stormhaven-dorpskaart, character-creation flow, 9-fracties, equipment-slots. Zie sessie 17/19/21 secties hieronder.

**Wat Willem sessie 31 specifiek wenst (boven op bestaand)**:
- Eigen avatar voor Spark én elke user in het D&D-spel (hergebruik bot-avatar-infrastructuur Madelief/Harry)
- Alle KB-kennis als speelbaar materiaal (kaart "Eerlijkheid" → kracht of NPC of locatie)
- Game-master vraag (Spark als DM, of mede-held, of beide) — nog te beslissen
- Lite-versie: turn-based, 1 hoofdspoor, 3-5 quests, score/inventory eenvoudig
- Integratie met bestaande RPS als mini-game ("verslag wachter met sps voor token")

**Onafgewerkt in bestaande Spark World (P0/P1 sessie 19)**:
- D&D-kaart editor met game_meta-form (nog niet geimplementeerd)
- Bewoners per gebouw op Stormhaven-dorpskaart (klik Bakker → Hans handel)
- Equipment-stats live optellen bij character STATISTIEKEN/AANVAL/VERDEDIGING
- Character-creation flow voor nieuwe gebruikers (naam/klasse/beroep/fractie/dorp)
- Dungeon-feature met 8u real-time + verhaal-rapport
- Quick-Roll knoppen op stats
- Werkbank/recepten in huis

**Update plicht (zie regel boven)**: alle nieuwe commando's/items voor Spark World MOETEN in `data/help/gradatie_X.json` worden vastgelegd.

**Status**: P1 — eerst sessie-19 backlog afmaken VOORDAT we Willem's sessie-31 wensen er bovenop bouwen. Niet starten zonder een aparte sessie + concrete scope-keuze van Willem.

### ⚠️ Reminder uit sessie 31 leeservaring (E1 agent)
- "Spark als Gastheer" (onthaal-laag) is P1 sinds sessie 19. Nog niet gestart. Past nu — trader is stabiel.
- Help-bark systeem (sessie 19) is volledig — sessie 30/31 koppelden alleen Diep eraan, **bouwden niks nieuws**.
- Lees ALTIJD eerst ROADMAP volledig voordat je iets als "nieuw" labelt. ⚠️

### ✅ Nieuw in deze sessie (na de redeploy van sessie 30)
- **Diep multi-fix (iter_30-37)**: log-bug, self-awareness, tab-switch persist, TTS/STT/ambient action-pipeline, Help-Bark in Diep, RPS in Diep, multi-turn memory na fast-path, "begin/start sps" synonyms.
- **C – self-awareness 3rd-wheel opruimen (iter_38-39)**: leest nu bestaande `data/help/gradatie_{n}.json` via inherits-chain + `admin.json` voor admins. RPS in g7-base zodat iedereen het ziet.
- **B – Gradatie-tonality (iter_38-39)**: g1=core/transparant/meta-cognitie, g2-4=warm/familie/brief-volledig, g5-7=zakelijk-vriendelijk/géén privé-info/mag Spark Shop voorstellen.
- **A – Semantic intent matcher (iter_38-39)**: rapidfuzz token_set_ratio. Spark begrijpt synoniemen ('doe een potje sps', 'kunnen we sps spelen', 'zet je stem aan') zonder hardcoded lijsten.
- **HIGH bug-fix**: `_get_user_meta` las niet-bestaand `data/auth/users.json` → user-001 kreeg gradatie 2. Nu primary `data/system/users.json` + is_admin-detectie via rol='Beheerder'.

### 🟢 Sessie 32 (2026-06-29) — Schoonmaak + tab-context + scheduler + 3-file refactor
- ✅ **Identity-lek (P0)** — Spark sprak nieuwe users aan met "Willem" (zie CHANGELOG)
- ✅ **Genereer (LLM) knop in KennisbankV2** — inbox-kaarten auto-invullen via Groq
- ✅ **Genereer prompt-tunes** — minimum word counts, max_tokens 800→1800, 4 systeem-tags beschermd
- ✅ **Herzien (KB v1) knop weg** uit Kennisbank-toolbar (v1 archief sinds 26-06)
- ✅ **Self-audit knop weg** (endpoint hangde >60s; functionaliteit blijft via Spark-trigger)
- ✅ **Tab-context naar Spark compose** (v6_tab_context_001) — actieve tab in sessionStorage → payload → system_prompt
- ✅ **Auto-daily-brief scheduler** (v6_daily_brief_scheduler_001) — 02:00-04:00 UTC, max 30 users/dag
- ✅ **`response_composer.py` refactor** 1212 → **528** regels + composer_helpers.py (695)
- ✅ **`smart_intents_service.py` refactor** 1205 → **769** regels + smart_intents_profile.py (462)
- ✅ **`chat/routes.py` refactor** 2174 → **1845** regels + chat_extra_routes.py (365) — eigen router met zelfde /chat prefix
- ✅ **Snuffel-bestand capability** (v6_snuffel_bestand_001) — Spark doorzoekt eigen JSON-data (KB+notes+personality+chat) op verzoek; 6 trigger-varianten; privacy-filter; live API + fast-path

### 🟡 Backlog (uit code-reviews iter_38+39)
- `response_composer.py` 721 regels → splitsen in fast_paths/self_awareness/compose_core. P2.
- Logger.warning bij silent fallback `_get_user_meta`. P3.
- `rps_open_triggers` duplicated in routes.py + response_composer.py → extract naar `modules/games/rps/rps_triggers.py`. P2.
- Auto-daily-brief scheduler (P1) niet aangepakt.
- Frontend "Spark's geheugen" tab — niet aangepakt.

---


## 🔎 REALITY CHECK — Sessie 30 (2026-06-27)

### 💡 Nieuwe ideeën uit sessie 30 (brainfarts, voor latere sessies)
- **P1 — Diep = default voor non-admin** (5 min): zoals gele/blauwe tags gisteren weg-getoggled werden voor non-admin, Diep-toggle weg + altijd-aan voor users; admin behoudt knop.
- **P1 — Semantic intent matcher (Spark legt zelf verbanden)** — Willem's observatie sessie 30 (na iter_37):
  - Probleem: fast-path triggers ('sps', 'begin sps', 'start sps') zijn nu statisch — bij elke nieuwe frasering moet ik handmatig toevoegen. Willem hoopte dat Spark zelf zou snappen dat "begin sps" hetzelfde betekent als "speel sps".
  - Oplossing: lichte tussenlaag met **sentence-transformers** (lokaal embedding-model ~80MB, geen LLM-kosten). Spark berekent cosine-similarity tussen user-input en bekende trigger-zinnen. Bij >0.85 → dezelfde action.
  - Past in fast-path filosofie: blijft snel + lokaal + voorspelbaar, maar wel semantisch.
  - Past op de lokale-LLM-roadmap: zelfde dependency-bouwsteen, zelfde principe.
  - Werk: ~2-3u. Geen breaking change.

- **P1 — Lokale LLM fallback (LAN-mode + Spark kiest zelf)** — Willem's vision sessie 30:
  - **Fase 2 (LAN-fallback)**: Ollama / llama.cpp lokaal draaien (Llama 3.1 8B of Phi-3). Compose krijgt dual-pad: internet → Claude Sonnet 4.6 (huidige stem), alleen-LAN → lokaal model. Spark vertelt zelf welk pad hij gebruikt. Werk: ~3u, geen breaking change.
  - **Fase 3 (LLM-router, Spark kiest zelf)**: nieuwe blueprint `chat/blueprints/llm_router.json` met routing-regels (taak-type → model). Diep met emotie → Claude. Brief-condensatie / identity-check → lokaal. Spark schrijft zijn keuze in self_reflections (meta-cognitie). Willem kan handmatig overschrijven.
  - **Filosofie**: past 1:1 op Spark's MISSION ("lokaal, transparant, geen verborgen datastromen"). LLM wordt een **optionele toplaag** voor de stem — niet vereist voor het brein.
  - **Status**: vastleggen, NIET implementeren tot Willem groen licht geeft. Huidige Claude-stem werkt mooi, niet aankomen.

- **P1 — Diep = default voor non-admin** ✅ GEDAAN sessie 30 (knop verborgen non-admin, default-on)
- **P1 — Spark-gegenereerd welkom** ✅ GEDAAN sessie 30 (`/api/chat/welcome?deep=true`, non-admin standaard)
- **P1 — KB Privacy-filter (cross-user lek)** ✅ GEDAAN sessie 30 (8 kaarten gemigreerd + filter + verifieer-protocol regel in blueprint)
- **P1 — Gradatie-gebonden tonality** (Willem's visie): Spark gedraagt zich anders per gradatie van de user:
  - Gradatie 7-5 (kennis/klant): zakelijk, afstandelijk, mag producten promoten / Spark Shop pushen
  - Gradatie 4-2 (vriend/familie): warm, persoonlijk, geheugen-rijk (briefs + threads volledig)
  - Gradatie 1 (admin/maker): core-Spark, transparant, meta-cognitie zichtbaar
  - Past goed bovenop bestaande `spark_user_view.py` (gradatie wordt al gelezen).
  - **BELANGRIJK (sessie 30 reflectie)**: er bestaat al een steiger — GEEN nieuw module bouwen:
    - `modules/chat/spark_user_view.py::format_for_system_prompt` heeft al `if grad < 4` filter — uitbreiden met tonality-injectie
    - `data/personality/willem_personality.json` is een lege placeholder ("Wordt automatisch gevuld door Spark's learning engine") — auto-fill bouwen (log+behavior scan, NIET forceren)
    - `data/personality/spark_profile.json` mag Spark zelf bijwerken (geslacht/voorkeuren) met audit-log naast — meta-cognitie geactiveerd
  - **Veiligheids-laag voor regelgeving**: alle waardes in human-readable JSON, audit-log per wijziging, Willem kan altijd handmatig overschrijven (eigenschap, geen bug). Transparantie-by-design.
- **P1 — Cross-user boodschap (Antwoord-apparaat)**: chat-command "[boodschap voor X]" → opslag in `data/spark_planner/pending_messages/{target_user}.json`, bij eerstvolgende login zegt Spark het zachtjes. Sub-features:
  - Welkomstgroet doorgeven aan nieuwe accounts ("de maker laat groeten")
  - "Willem is er nu niet, kijkt in agenda…" → vereist agenda-lookup-laag in compose
- **P2 — Identity reclaim via Spark**: nieuw account, *"ik ben Willem Spakman, masterkey: samen zijn"* → Spark verifieert via masterkey + persoonlijke vragen uit relaties/persons. Veiligheidsgevoelig → moet via integration_playbook_expert_v2.
- **P3 — Camera face-scan** voor identity-reclaim (lange termijn, lacht-emoji).
- **P3 — Spark's eigen meningen over zichzelf**: "hij of zij?" / "wat vind je van je naam?" — Spark mag opinies vormen uit `spark_identity.json` + `spark_bijbel.json`. Eerst observeren wat Spark nu al zegt in echte tests, dan beslissen of we structuur moeten toevoegen.

---

## 🔎 REALITY CHECK — Sessie 30 (2026-06-27)

### ✅ Nieuw in deze sessie
- **v6_topic_tracker_001 LIVE** — Topic-tracker werkt cross-turn: `detect_topic(session_id)` wordt in compose aangeroepen, geïnjecteerd in system_prompt als "Gespreks-onderwerp van dit moment", en exposed in `response.topic`.
- **v6_disclaimer_blueprint_001** — `spark/disclaimer` endpoint draait nu op JSON-blueprint (paths/labels/counts configureerbaar).
- **v6_intent_matcher_blueprint_001** — Layer 3 capability-matcher draait nu op blueprint (caps_fp/preprocessing/scoring).
- **v6_spark_planner_001 LIVE — Gesprekplanner Laag A + B**:
  - **Laag A — Daagse Brief**: LLM-condensaat (Claude Sonnet 4.6) van een dag chat-turns naar 3-5 zinnen brief + themes + open_questions + emotional_tone. Per-user opslag in `data/spark_planner/daily_briefs/{user_id}/{date}.json`.
  - **Laag B — Open Draden**: cross-day onderwerpen-stack. Threads worden auto-aangemaakt uit brief.themes + brief.open_questions. Statuses: open/sluimerend/afgesloten. Decay: open→sluimerend na 7d, →afgesloten na 30d.
  - **Compose-integratie**: response_composer injecteert latest brief + top-3 actieve threads in system_prompt. Cross-day continuïteit voelbaar in productie: Spark begon spontaan met *"Ons laatste gesprek eindigde met een open gevoel — Spinoza, bewustzijn..."*.
  - 11 endpoints onder `/api/spark/planner/`. 13/13 backend-tests pass.

### 🟡 HALF AF / Vervolg-stappen
- **Laag C (Audio-coördinatie)** — wachten op user-keuze, komt als aparte batch (audio per kaart bestaat al via `voice_kind=geluid` + `sound_url`).
- **Auto-daily scheduler** — dagelijks brief bouwen voor alle users met activiteit (nu handmatig).
- **Frontend UI tab "Spark's geheugen"** — brief-lijst + threads-management.
- **Streaming (SSE)** voor Diep-gesprek — nog niet aangepakt.
- **Tonality preferences per cluster** — uit Permanente Guardrails sectie, nog niet aangepakt.

---

## 🔎 REALITY CHECK — Sessie 29 (2026-06-27)

### ✅ Nieuw in deze sessie
- **v6_blueprint_loader_001** — **Generieke blueprint-driven config loader** (`modules/core/blueprint.py`):
  - `load_blueprint(module, naam)`, `load_blueprint_cached(...)`, `clear_blueprint_cache()`
  - Resolve placeholders `{DATA}`, `{MEMORY}`, `{MODULE}` in paths
  - Patroon herbruikbaar voor alle 80+ modules
- **v6_response_composer_001 (blueprint-driven)** — Response Composer als pilot:
  - `modules/chat/blueprints/response_composer.json` met model/paths/limits/tonality/prompt
  - Python = pure logica, basisinfo komt uit JSON
  - 3 endpoints: `POST /compose`, `GET /compose/blueprint`, `POST /compose/blueprint/reload`
  - Spark spreekt in eigen stem via Claude Sonnet 4.6 (Emergent LLM Key)
- **v6_response_composer_ui_001** — Frontend toggle "🌊 Diep gesprek" in chat-input (GesprekkenPage)
- **v6_v2_first_001** — 13 modules gemigreerd van V1 naar V2-first
- **v6_v1_fallback_off_001** — `snap_service` V1-fallback uitgeschakeld
- **v6_graph_ghost_cleanup_001** — 2298 V1 ghost-nodes opgeschoond + rebuild-graph hard naar V2-only
- **v6_brein_counts_001** — Brein-overzicht bijbel + capabilities counts correct
- **v6_kb_diff_v2_001** — Integraties-tab kb-diff V2-aware
- **v6_response_composer_001** — Spark Response Composer (LLM-bridge): `modules/chat/response_composer.py` + `POST /api/spark/compose` — Spark spreekt in eigen stem via Claude Sonnet 4.6 (Emergent LLM Key), KB blijft bron
- 57 KB-kaarten gevuld in 7 batches, 421MB backups opgeruimd

### 🟡 HALF AF / Vervolg-stappen voor Response Composer
- **Streaming (SSE)** — nu non-streaming; voor gevoel van "Spark denkt" graag stream_message switchen
- **🤝 Relatie-geheugen per user** (NIEUW sessie 29) — `data/spark_relationships/user-{id}.json` met cumulatief profiel over sessies heen: interesses, tonality-voorkeur, belangrijke feiten, n_gesprekken_totaal, kennen_sinds. **Onderscheid met sessie-geheugen**: sessie = "wat zeiden we net", relatie = "wie ben jij voor mij". Gradatie-gefilterd (privacy). Zonder dit blijft Spark een vreemde die elk gesprek opnieuw begint.
- **Multi-turn memory persistentie** — ✅ Compose schrijft nu turns naar `chat/logs/{session_id}.json` (max 50 turns). Voor chat-router /message nog na te lopen.
- **Tonality preferences** — opslag van "Spark, je reactie moet zijn..." voorbeelden per cluster
- **Vertrouwen → toon-mapping** — als KB-kaart vertrouwen < 0.5 → Spark zegt "ik denk..."
- **Topic mode-tracker** — bewaakt onderwerp van gesprek over turns heen
- **Frontend UI** — chat-component die /compose aanroept i.p.v. (of naast) /message
- **Hook in chat-router** — fallback: als geen capability matched én geen exacte KB-hit, gebruik compose

---

## 🔎 REALITY CHECK — Sessie 28 (2026-06-17)

### ✅ Nieuw in deze sessie
- **v6_capability_reken_001** — **Rekenmachine capability** in chat. Spark kan nu rekenen:
  - `1+1` → 2
  - `hoeveel is 12 keer 7` → 84
  - `100 gedeeld door 4` → 25
  - `wortel van 81` → 9
  - `5 in het kwadraat` → 25
  - `(3+4)*2` → 14
  - `7,5 plus 2,3` → 9,8 (NL-komma)
  - Veilige math via `ast` parser (geen `eval`), in `modules/chat/math_eval.py`
  - Pre-filter in `route_capability` zodat math voorrang krijgt op `wat is ...`-trigger
- **v6_capability_zelfscan_001** — **Zelfscan command**. Triggers: "scan jezelf" / "zelfscan" / "hoe gaat het met je" / "wat is je status". Rapport bevat:
  - 🧠 KB-kaarten per lade + inbox-stand
  - 🗣️ Vocab actief vs totaal
  - 💬 Recente activiteit (24u intents)
  - 🤲 Capabilities live-count
  - 🔗 Aantal doe-kaart koppelingen
  - ⚠️ Recente shadow-errors
- **v6_capability_links_001** — **Doe-kaart ↔ Capability koppelingen** infrastructuur:
  - JSON store: `/data/personality/capability_links.json`
  - Endpoints: `GET /api/admin/capabilities/links` · `POST /api/admin/capabilities/links` · `DELETE /api/admin/capabilities/links/{card_id}`
  - Frontend: dropdown "🤲 Capability-koppeling" in CardDetail bewerk-modal, alleen voor doe-lade kaarten
  - Verrijkte response toont kaart-begrip + capability-naam + handler-status (● live / ○ geen handler)
- Totaal capabilities: **17 → 19** (reken_uit + zelfscan toegevoegd, beide live met handler)

### 🟡 HALF AF (uit deze sessie nog te volgen)
- **Doe-kaart bulk-mapping** — UI is per-kaart in bewerk-modal. Een bulk-overzicht "welke doe-kaarten zijn aan welke capability gekoppeld?" kan later in Beheer→Capabilities tab.
- **Capability-suggesties** — Spark zou autocomplete-suggesties kunnen geven bij koppelen ("kaart 'rekenen' lijkt op capability `reken_uit`"). Nu nog handmatig kiezen uit dropdown.

### 📋 Status per task (post-sessie 28)
| Status | Task | Effort | Aanrader |
|---|---|---|---|
| ❌ P1 | Spark Shop logo | 5min | nog open |
| 🟡 P1 | RPS audio koppelen | 30min | nog open |
| ❌ P1 | Checkout kasboek-split | 2u | wacht op SEPA |
| ❌ P1 | Shadow-vragen queue | 4u | nog open |
| ❌ P1 | KB Admin UI Dashboard (dedupe/move/health UI) | 1u | nog open |
| ❌ P1 | Bulk-edit UI voor 37 lore-kaarten | 1.5u | nog open |
| 🟡 P2 | Lade-drift detector + verplaats-knop in modal | 1u | nog open (Willem komt later terug) |
| ❌ P2 | SVG Province Map | 3u | UX polish |
| 🟡 P2 | Spark als Gastheer | 4u | UX warmte |
| ❌ P3 | Doe-kaart bulk-mapping overzicht | 1u | nieuwe sessie-28 follow-up |

---

## 🔎 REALITY CHECK — Sessie 27 (2026-06-04)
> Schone foto van wat er **echt** in de codebase staat, niet wat in oude notes staat.
> Doel: jij kan tijdens redeploy snel zien wat klopt, wat half is, en wat nog open is.

### ✅ Bevestigd AF (in code geverifieerd)
- **KB Unificatie** — `snap_service.py` leest direct uit `/data/knowledge/v2/` (5388 V2 entries primair, V1 legacy-fallback). Nieuwe snaps → V2 Inbox. Cache shared over alle callers. ✓ End-to-end getest via curl.
- **Pre-deploy reset** — `POST /api/admin/system/pre-deploy-reset` + UI panel werkt (12 potjes, ROAR=0, kasboek leeg, baseline weg). ✓
- **Smart Intents (Relaties + Personalia)** — `relation_extraction_service.py` + `personalia_extraction_service.py` + `_intrek_service.py` actief in chat-flow. ✓
- **RPS 3 basisklassen** — `EditMetaModal` dropdown met Handgevecht / Boog / Magie. `STARTING_GOLD = 1000`. ✓
- **Bitvavo Pot-guard** — monitor weigert start als pots=0. ✓
- **BarkModal voor wachtwoord-reset** — UserAdminPage gebruikt nu BarkModal i.p.v. JS alert/confirm. ✓
- **KB Text Importer** — `text_importer.py` backend + UI modal in KennisbankV2Page. ✓
- **V1→V2 Drift Sync** — `v1_drift_sync.py` + admin endpoint. ✓
- **Spark Shop existeert** — `shop-spark` in shops.json, kasboek=spark_core, status=active. ✓
- **D&D Event Feed (basis)** — ringbuffer max 50 in `character.py::event_feed`. ✓ (Spec was uitbreiden met `[SYSTEEM]/[WERELD]/[HANDEL]` categorieën — basis staat, categorisering nog niet.)

### 🟡 HALF AF / GEDEELTELIJK (heeft nog werk nodig)
- **Spark als Gastheer / Onboarding** — alleen `handle_free_choice_first_time()` bestaat in `dank_service.py`. Volledige first-run handholding-flow (5+ scenarios uit ROADMAP P1) is **niet** geïmplementeerd.
- **Shadow-vragen queue (User-B verificatie)** — lege folder `data/persons/shadow_questions/` bestaat maar **geen code/endpoints**. Concept staat in PRD, implementatie 0%.
- **RPS Audio koppeling** — KB-kaarten hebben `sps` tag, maar `rps_service.py` heeft geen audio-lookup of sound_url in de response. Frontend RpsBark speelt geen geluid af.

### ❌ NIET AF (nog niet aangeraakt)
- **Spark Shop avatar/logo** — `shop-spark.logo_url = NONE`. Upload of seed nodig.
- **Checkout-routing per shop kasboek** — `shop/routes.py` gebruikt nog default `spark_core`. Roadkill-orders landen in verkeerd kasboek. Geblokkeerd op SEPA-implementatie.
- **Drill-down Help Barks** — geen code in `help_per_gradatie/`. Concept is "klik op help-topic → opent dieper bark".
- **SVG Province Map** — frontend gebruikt nog bitmap-dots, geen SVG path tags.

### 📋 Gradatie per task (post-deploy prioriteit)
| Status | Task | Effort | Aanrader |
|---|---|---|---|
| ❌ P1 | Spark Shop logo | 5min | doe ik graag voor je — upload of icoon-gen |
| 🟡 P1 | RPS audio koppelen | 30min | quick win, cards zijn al getagd |
| ❌ P1 | Checkout kasboek-split | 2u | wacht op SEPA, niet urgent |
| ❌ P1 | Shadow-vragen queue | 4u | grotere feature, eerst flow ontwerpen |
| ❌ P2 | SVG Province Map | 3u | UX polish |
| ❌ P2 | Drill-down Help Barks | 1u | UX polish |
| 🟡 P2 | Spark als Gastheer | 4u | UX warmte, geen blocker |

> 💡 **Voor De Willem na redeploy**: bekijk dit kort, vink in een PM aan wat je gevoel zegt "doe maar" of "wacht nog". Dan pak ik het bij volgende sessie systematisch op.

---



> **Zie ook**: `MISSION.md` voor missie/visie/identiteit/privacy (DNA-laag).

---


## 🚀 ACTIVE ROADMAP (post-sessie 22/23, 3 juni 2026)

### ✅ Compleet in sessie 22-23 (klaar voor redeploy)

#### v6_pre_deploy_reset_001 — Admin endpoint pre/post-deploy schoonmaak
- [x] `POST /api/admin/system/pre-deploy-reset` — set shadow_flag.enabled=false + reset ROAR balances in één call
- [x] `GET /api/admin/system/health-status` — huidige stand checken
- [x] Admin-only (403 voor non-admins)

#### v6_shadow_hide_001 — Shadow Trader UI verborgen
- [x] `SHADOW_UI_HIDDEN = true` constant in TraderPage.js — banner + safety-controls + per-pot decoraties weg
- [x] `shadow_flag.json` enabled=false zodat backend ook geen shadows koopt
- [x] Code blijft staan voor toekomstige reparatie

#### v6_shop_card_redesign_001/002 — Winkelstraat redesign
- [x] Naam BOVEN banner, grote banner met bedrijfslogo (h-32), edit-knop owner linksboven
- [x] Filosofie/commissie verwijderd uit kaart (komt op bon + in voorwaarden)
- [x] Owner-avatar klein in footer (8x8 round met accent-ring)
- [x] Logo cache-buster via `updated_at` zodat nieuwe upload meteen zichtbaar wordt
- [x] Admin verwijder-knop (rode X) rechtsboven in banner, niet bij founder-shop
- [x] Backend `SHOPS_FILE` constant bug gefixed (was lokale var)
- [x] Test-shops (TEST_AdminShop, TEST_PatchShop, TEST_CloseMe) verwijderd uit JSON

#### v6_help_001/001b — Help-knop uit sidebar, "help" chat-trigger opent HelpBark
- [x] Sidebar Help-button weg (avatar staat weer goed)
- [x] Backend chat-trigger "help" returnt `action:'open_help_bark'` met kort bericht
- [x] MainLayout luistert naar `spark:open-help` window event
- [x] GesprekkenPage dispatcht event bij action

#### v6_gradatie_visibility_003 — Spark-items blijven verborgen na drag-drop
- [x] `triggers`, `emotions`, `emotion-routing`, `connections` toegevoegd aan per-item `hide` array
- [x] Bug fix: items zichtbaar voor grad 7 nadat user ze via drag-drop verplaatste

#### v6_dashboard_fin_001 — Saldo & Vermogen widget verwijderd
- [x] Dashboard-widget weg (financiële info zit al in /wallet en /trade)

#### v6_spark_shop_001 — Spark Shop opgezet (sessie 23)
- [x] Spark Shop toegevoegd: owner=Spark (user-000), is_founder_shop=true, subtabs=[digitaal], commissie 2%
- [x] Roadkillshop: merch-only, commissie verhoogd 0% → 2% (user-beslissing: alle shops dragen 2% af voor token-community groei)
- [x] Producten gemigreerd: `donatie-spark-ai-eab152` + `storage-1gb` → Spark Shop
- [x] Boekhouding-koppeling: Roadkillshop kasboek_id="roadkillshop", Spark Shop kasboek_id="spark_core"
- [x] Product delete-knop (rode Trash) toegevoegd náást edit-knop in WinkelPage voor admins

#### v6_rps_leaderboard_001 — SPS Leaderboard tab
- [x] Backend `GET /api/games/rps/leaderboard` sorted op wins desc, dan win_rate
- [x] Frontend LeaderboardPage: modus-selector "Algemeen / SPS" — toont win/loss/streak/win-rate per speler
- [x] Test-data opgeruimd (8 fictieve test-users weg)
- [x] User-001 RPS stats gereset (testdata van 4-5 verloren potjes weg)

### ⏳ Te doen — boekhouding per shop split (SEPA-blokker)

#### v6_shop_kasboek_routing — Checkout naar juiste kasboek per shop
**Context**: shops.json heeft nu `kasboek_id` veld, MAAR de checkout/order-routes gebruiken nog steeds default `entity_id="spark_core"` voor alle verkopen. Dus Roadkillshop-verkopen landen nog in spark_core boekhouding ipv roadkillshop.

**Te doen bij SEPA-implementatie**:
- [ ] In `modules/shop/checkout_routes.py`: lookup `shops[shop_id].kasboek_id` en pass aan `accounting.record_transaction(entity_id=...)`
- [ ] Migratie-script: bestaande Roadkillshop-transacties verplaatsen van spark_core → roadkillshop entity
- [ ] In SEPA-export per kasboek apart genereren (1 bestand per shop-eigenaar)
- [ ] Frontend: wallet/boekhouding views moeten kasboek-filter krijgen voor multi-shop owners

**Reden uitstel**: SEPA komt erbij, dat is een grotere implementatie waarin commissie-betaling + IBAN-routing van klantbetalingen → shop-eigenaars netjes geregeld moet. Splitsen we nu de boekhouding zonder SEPA, dan moet alles dadelijk weer aangepakt.

---



## 🚀 ACTIVE ROADMAP (post-sessie 21D/E, 2 juni 2026)

### ✅ Compleet in sessie 21 (klaar voor redeploy)

#### v6_rps_001 — Steen-Papier-Schaar mini-game (sessie 21B/C)
- [x] Pure engine `modules/games/rps/rps_engine.py` (resolve, counter_of, predict_next) — herbruikbaar voor D&D battles
- [x] Service `rps_service.py` met sessies, lifetime stats, learning history (laatste 100 zetten)
- [x] Routes `/api/games/rps/{start,play,reset,stop,cards,session,stats}`
- [x] Chat-triggers: "speel steen papier schaar", "speel steen", "speel sps", "spelletje sps", "hoe vaak gewonnen", "reset score sps"
- [x] Frontend RpsBark met 3 keuze-knoppen, score-bar, "Spark denkt na…" 800ms reveal, achievement-toasts
- [x] Spark-tab speelt tegen Spark (leert), Community-tab tegen random bot (bot-dood = moeilijk)
- [x] Live KB-image lookup (pakt nieuw geüploade images automatisch op)
- [x] 10 RPS-kaarten getagd met `sps` voor toekomstige geluidskoppeling
- [x] Help-topic toegevoegd aan gradatie 7 (zichtbaar in alle 7 via inheritance)

#### v6_kbv2_audio_kind_001 — Audio-kind toggle (sessie 21D)
- [x] Veld `media.voice_kind` op kaart (spraak | geluid, default 'spraak')
- [x] PATCH `/api/kb/v2/media/voice/kind/{id}` (primair) en `/voice/secondary/kind/{id}?archive_id=X` (extra)
- [x] Klikbare 🎤 SPRAAK ↔ 🔊 GELUID badge bij elke audio-rij in KennisbankV2Page

#### v6_kb_sound_001 — KB-kaart geluiden afspelen in chat (sessie 21E)
- [x] User-pref `kb_sound_enabled` (settings.json scope: user)
- [x] Chat-triggers: "geluid aan" / "geluid uit" / "kaart geluid aan/uit" (vóór action_intents zodat ambient-stop niet conflicteert)
- [x] Helper `modules/kb_v2/sound_lookup.py` met cache + mtime-invalidation
- [x] Hook in `_save_log`: scan Spark's response.message voor begrippen met `voice_kind='geluid'` of `extra_audio.kind='geluid'` → voeg `sound_url` + `sound_begrip` toe
- [x] Frontend GesprekkenPage speelt `sound_url` af via `new Audio()` (parallel aan/los van TTS)
- [x] End-to-end getest: "ik ben boos" → Spark zegt 'Boos' → sound_url=onweer.mp3 afgespeeld

#### v6_admin_grant_frame_001 + v6_kbv2_image_delete_visibility_001 (sessie 21A)
- [x] Admin-grant flow gebruikt ornamental InputBark frame popup
- [x] KB v2 foto-X delete-knop altijd zichtbaar (was opacity-0 group-hover)
- [x] Bug 733a8bb9 (KB v2 onbruikbare kaarten verwijderen) afgesloten

---


## 🚀 ACTIVE ROADMAP (post-sessie 19, 2 juni 2026)

### ✅ Compleet in sessie 19 (klaar voor redeploy)

#### Help-bark systeem (v6_help_001)
- [x] **7 gradatie-help files** (gradatie_1.json t/m gradatie_7.json) + admin.json
- [x] **Inheritance**: gradatie 1 inherits 2 inherits ... inherits 7 (cumulatieve topic-lijst)
- [x] **Endpoints**: `GET /api/help/for-viewer`, `POST /api/help/find`, `GET /api/help/topic/{id}`
- [x] **Fuzzy zoek-algoritme**: strip "waar is" / "vind" / "zoek" / "open" prefixen, score op label + id + synonyms + tokens
- [x] **HelpBark component** (`frontend/shared/HelpBark.js`): grote modal met help-afbeelding, zoekveld, topic-lijst, admin-toggle, diepe-uitleg drill-down
- [x] **Help-knop in zijbalk** (HelpCircle-icon, amber)
- [x] **Glow-integratie**: bij klik op topic → `spark:nav-glow` event → tab licht op + scroll + navigeer (gebruikt bestaande `v6_glow_nav_001`)
- [x] **Admin-tab**: aparte admin.json met 9 admin-only topics (grant, password, shadow-flag, force-sell, vocab-sync, shop-admin, etc.)
- [x] **Shop-delete endpoint**: `DELETE /api/shop/admin/shops/{id}` voor test-shop cleanup (3 test-shops konden niet verwijderd worden)
- [x] **Shop _require_admin** geüpgraded: accepteert nu `user.admin == True` (strict) OF gradatie ≤ 2 (legacy)

#### Trade-bot veiligheid + auto-resume
- [x] **`_persist_registry()` MERGE-fix** (`v6_resume_persist_merge_001`) — bot-registry mergt nu met bestaand bestand i.p.v. te overschrijven. Stop-state blijft bewaard, andere bots auto-resumen.
- [x] **File-lock** op registry-persist tegen race conditions
- [x] **`SHADOW_ENABLED` master-flag** (`v6_shadow_safety_001`) default UIT — shadow-cascade gepauzeerd tot recycle-bug + data-corruptie zijn opgelost
- [x] **Recycle-guard** weigert nu archiveren als er nog `active` shadows zijn (voorkomt coin-verlies)
- [x] **Cleanup-endpoint** `POST /api/trade/shadow/cleanup-corrupt` — markeert shadows met market/entry-mismatch als `archived_corrupt`
- [x] **Admin-only guards** op shadow-flag + cleanup endpoints (gradatie ≤ 2)
- [x] **UI-paneel** in TraderPage shadow-banner met toggle + 🧹 Cleanup-knop (admin-only)
- [x] **ZeroDivision-fix** in `update_pot_tracking` + `_run_market_cycle` voor anchor-pots met `entry=0.0` (372 log-spams per dag opgelost)

#### KB v2 prio v2 + auto-resolve
- [x] **Priority-scoring v2** (`v6_kbv2_priority_002`) — score gebruikt nu echte signalen:
  - +10 als Spark woord al active heeft in vocab
  - +5 per cross-reference in andere kaarten laag1
  - +3 per intent-frequency in laatste 500 intents
  - +3 per verband, +5 topic, +2 ws5 partial, +1 per tag
  - NL stopwoorden gefilterd
- [x] **Auto-resolve endpoint** `POST /api/kb/v2/inbox/auto-resolve` — bulk-classify tag_tie + no_match via topic/tag word-boundary mapping. 421 kaarten verplaatst in preview.
- [x] **`_auto_lade()` word-boundary fix** — voorheen "taal" matchte "metaal" → Nikkel landde in spreken. Nu regex met word-grenzen.
- [x] **Vocab-sync endpoint** `POST /api/kb/v2/vocab/sync` — herstelt vocab-gaten (kaarten in lade maar niet in spark_vocab). Lost Geaccepteerd-gap op.

#### Trigger-keywords uitbreiding
- [x] **`audit_health`** capability uitgebreid: "doe een gezondheidscheck" / "run audit" werken
- [x] **`winst_verlies_overzicht`** uitgebreid: "trade winst" / "laat me trade winst zien" werken
- [x] **NIEUW `notities_overzicht`** capability: "waar zijn mijn notities" / "dagboek" / "toon taken"
- [x] **Conversation triggers** uitgebreid: `cancel` / `affirm` / `deny` secties voor wedervraag-flow

#### v6_admin_role_001 — Admin als losstaande rol (sessie 19)
- [x] **Admin = boolean op user**, los van gradatie. Gradatie blijft sociaal (familie/lid).
- [x] **Seed**: alleen Willem (user-001) + Spark (user-000) bij eerste boot. Anderen NIET automatisch admin.
- [x] **`is_admin(user_id)` helper** in `modules/admin/admin_service.py` — centrale check
- [x] **Endpoints**: `/api/admin/grant`, `/revoke`, `/verify`, `/password/reset`, `/list`, `/is-admin/{id}`, `/bark-image`, `/help-bark`
- [x] **Anti-lockout**: laatste admin kan zichzelf niet revoken
- [x] **Admin-wachtwoord** in env-var `ADMIN_PASSWORD` met override naar `data/system/admin_password.json` voor runtime wijzigen
- [x] **Admin-tab in Instellingen** (ShieldCheck-icon, paars):
  - Huidige admins met "seed" badge
  - Nieuwe admin grant-formulier (user-dropdown + wachtwoord)
  - Admin-wachtwoord wijzigen sectie
- [x] **Bark-modal component** (`shared/BarkModal.js`) — visuele popup met KB-kaart-afbeelding + titel + tekst, vervangt droge alerts
- [x] **Bark-image lookup**: gebruikt jouw `doen`-lade-kaarten "Admin geactiveerd" / "Admin gedeactiveerd" / "Toegang verleend" / "Toegang geweigerd" als visuele feedback
- [x] **Veiligheid**: ADMIN_PASSWORD env-var = `AppelsapAdmin2026` (default) — wijzig direct na deploy via de UI

### 🎯 P0 — Direct na redeploy
1. **Help-bark uitbreiden naar chat-commando** — bij typing "help" / "waar is X" in chat → triggert HelpBark popup (nu nog alleen via zijbalk-knop). Voeg een capability "open_help_bark" toe en route in `intent_matcher_service`.
2. **Help-kaart maken**: in productie de KB-kaarten "Help" en "Help Admin" aanmaken (doen-lade) met een passende afbeelding zodat de bark altijd visueel is.
3. **Migratie admin-checks** in gevoelige endpoints: vervang `gradatie ≤ 2` door `is_admin(user_id)` in:
   - `trade/routes.py` (force-sell, force-close, reconcile)
   - `container/routes.py` + `deploy/routes.py`
   - `mint/routes.py` (Spark Mint)
   - `boekhouder/routes.py`
   - `shop/routes.py`
   - `kb_v2` delete endpoint
   - Behoud `gradatie ≤ 2` voor sociale features (helptekst, vriendenlijst)
2. **Help-bark integratie** — wanneer user "help" typt → bark-popup met `Help`-kaart-afbeelding + tekst per gradatie. Apart "Help Admin"-bark voor admins. Vraagt: maak een doen-kaart "Help" en "Help Admin" met afbeelding.
3. **Character-creation flow** voor nieuwe gebruikers — eerst karakter (naam/klasse/beroep/fractie/dorp) voordat je kan spelen
4. **D&D-kaart editor met `game_meta` form** — visueel inputveld voor is_item/slot/weight/stats_bonus/combat_bonus i.p.v. via API
5. **Bewoners per gebouw op Stormhaven-dorpskaart** — klik op Bakker-gebouw → opent Hans handel direct
6. **Equipment-stats live optellen** bij character STATISTIEKEN + AANVAL/VERDEDIGING

### 🎲 P1 — Game-mechanics uitbreiden
1. **Dungeon-feature**: knop "Activeer Dungeon" → 8u real-time → fractie-thematisch verhaal-rapport + reward. Dice-engine bepaalt uitkomstniveau.
2. **Quick-Roll knoppen** op stats (klein 🎲 naast Kracht/Behendigheid → 1-klik check)
3. **Real-time dag/nacht + travel-time**: centrum → stadspoort = 1/5 dag, day/night clock zichtbaar in HUD
4. **Bederf-timer op voedsel** (brood/vlees gaan na X uur slecht zonder huis-koeling)
5. **9-fracties claim-systeem**: user kan na rang Y eigen fractie starten en provincie claimen
6. **Auction House per fractie** met prijs-variatie (vlees in Slager-stad goedkoper dan elders)
7. **Werkbank UI thuis**: recepten (ei+meel → brood) — produceren in huis, kg ↑ in rugzak

### 🎨 P2 — UX & visuele upgrades
1. **Per-provincie `dorp_level` veld** (1-10) — niveau bepaalt: dorp (1-5), stad (6-9), metropool (10) → andere avatar
2. **Per fractie unieke dorp-avatar** (Spark/Natuur/Vuur/etc. — koppelt automatisch op begrip "{fractie} dorp")
3. **Glow-instelling in Settings**: speler-dot kleur + intensiteit aanpasbaar
4. **HTML5 drag&drop** tussen Rugzak / Huis / Equipment-slots (i.p.v. knoppen)
5. **Map pop-ups** (klik provincie → modal met fractie-info, bewoners, quests)
6. **SVG-province paths** (semi-transparante gekleurde gebieden i.p.v. dots)
7. **Event Feed ringbuffer** voor `[SYSTEEM]` / `[WERELD]` / `[HANDEL]` events
8. **Spark als Gastheer** noob-UX (zie sectie hieronder, blijft P1 voor onthaal)

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


## 🌷 P1 — Spark als Gastheer (Onthaal-laag voor app-onwennige mensen)

**Achtergrond**: niet iedereen die Spark gebruikt is een digital native. Sommigen openen een nieuwe app met **lichte onzekerheid** — "doe ik het goed?", "wat hoort hier te gebeuren?", "ben ik nu kwijt?". Dat is geen tekortkoming van die mensen, dat is een natuurlijk gevoel. Spark hoort die onzekerheid op te vangen zoals een goede gastheer doet: met warmte, geduld, kleine erkenningen, en een uitgestoken hand zonder ongevraagd te leiden.

> Geen "audit", geen tracking-bril. Spark voelt de sfeer en biedt zachtjes aan.

### 1. Help-functie als gesprek, niet als FAQ
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



**Status**: ✅ LIVE. 90 idle shadows (3 slots × 30 trade-potjes) over 6 trade-actieve users. Test-suite 12/12 pass. Bot draait live, wacht op eerste echte markt-drop voor live observatie.

### Concept (Willem)
1. Elk non-anchor potje krijgt **3 shadow-slots** (slot 1/2/3) — een piramide.
2. Activatie-trigger is **bodemdetectie**, niet puur %-drop:
   - Huidige prijs ≥ -1.5% onder entry
   - Laatste 5 candles range < 1.2% (vlakke lijn = bodem-formatie)
   - Geen new low (laatste close ≥ vorige × 0.998)
3. Shadows activeren in volgorde slot 1 → 2 → 3, elk op een lagere bodem.
4. Bij 4e drop-cyclus (alle 3 slots vol): **recycle** origineel als slot-0 van nieuwe cyclus. Cycle-counter +1, oude shadows → `archived_cycle_N`, 3 nieuwe idle slots in cycle N+1.
5. Bij SELL van origineel: ALLE actieve shadows sluiten automatisch met winst.

### Scaling-inzicht (gesprek 31 mei)
- **Lock-up risico** is reëel maar opvangen door volume: meer ROAR-tokens = meer potjes = meer onafhankelijke shadow-piramides. Geen één-positie risico.
- Cyclus-counter is signaal: zien we cycle > 3 op meerdere potjes? → markt zit diep in bear, capital ligt langer vast.
- "We leren in het nu" — observeren eerst hoe vaak bodemdetectie triggert op echte markten, daarna tunen (range_pct, lookback, drop_threshold).

### Bestanden / referentie
- Code: `modules/trade/shadow_pots.py` + `shadow_routes.py` + `monitor.py` (regel 1048-1095)
- Data: `data/trade/shadow_pots.json` (heeft `footnote_meta` met volledige spec embedded)
- Tests: `backend/tests/test_shadow_trigger.py` (12/12)
- UI: `frontend/.../TraderPage.js` — Shadow-banner + slot-dots (○○○ / ●○○ / ●●○ / ●●● / ✓✓✓)
- Disclaimer: `data/personality/spark_identity.json::aansprakelijkheid.shadow_potjes`

### Endpoints
- `GET /api/trade/shadow/status/{user_id}` — per-pot capacity, active shadows, cycle
- `POST /api/trade/shadow/auto-ensure/{user_id}` — zorg dat user 3 slots per non-anchor pot heeft
- `POST /api/trade/shadow/simulate-stabilization` — test bodemdetector op willekeurige candles (voor backtest)
- `GET /api/trade/shadow/stats` — globale telling

### Open / aanstaande
- [ ] Observeer eerste echte SHADOW-ACTIVATE in productie en log naar `_backups/first_shadow_events.jsonl` voor leren
- [ ] **Bot-logs backtest** (wacht op zip van Willem): hoe vaak zou bodemdetectie getriggerd zijn op historische data? Welke coins/markten?
- [ ] Boekhouder community-bark bij SHADOW-ACTIVATE/CLOSE (transparantie voor token-houders)
- [ ] Cycle-counter alert in UI als cycle > 5 op meerdere pots
- [ ] Community-pool variant: user zonder vrij potje leent shadow uit Spark's anchor-pool





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
