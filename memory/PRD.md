# Spark Core 2.0 — PRD


## Sessie 58 vervolg (2026-02-15) — Registry-fundering + Ghost-preventie + kb-hit-log

**Melding (Willem)**: "kaart foto's kwam als 'bestaat al' — waarom werd er een snap
van gemaakt bij de orphan-tag scan?" + "die tag schoonmaker is gelijk een functie
die je kan inbouwen. en koppelen aan een admin command." + "de trader aan uit is
ook al verbonden door middel gesprek?" + "als idee goed is ook gelijk format
kunnen we later op verder" + brainfart over fact/ervaring-agent.

**Wat is gedaan**:
1. **Foto's-kaart** (`kbv2-c0421b96`) upgraded met Willem's uitgebreide versie
   (7 use-cases, betere ws5). Ghost-duplicaat `kbv2-63c3d542` (unicode-apostrof
   in begrip) verwijderd uit inbox.
2. **Root-cause apostrof-ghost gefixt**:
   - `modules/kb_v2/tag_sanitizer.py` — `_APO_MAP` toegevoegd, `sanitize_tag`
     normaliseert nu unicode-apostrofen (’‘´`‛ʼ → ').
   - `scripts/orphan_tags_to_cards_v13d.py` — `_canonicalize` doet apostrof-normalisatie
     vóór alle andere checks; nieuwe `-'s`-plural-strip-regel.
   - Data-fix: 8 tags + 1 begrip (`Programma's`) + 1 index-key genormaliseerd.
   - 6 regressietests toegevoegd, 18/18 pass.
3. **Apostrof-normalize als admin-command**:
   - `modules/kb_v2/apostrophe_normalizer.py` — herbruikbare
     `normalize_apostrophes_in_kb(dry_run)`-functie.
   - `POST /api/kb/v2/admin/normalize-apostrophes?dry_run=bool` route.
   - Registry-entry `cap_kb_normalize_apostrophes` (admin_only=True, gradatie=5).
   - `admin_command_agent._ADMIN_CMD_WHITELIST` — eerste écht lid.
   - CLI-wrapper `scripts/normalize_apostrophes_in_kb.py` gebruikt zelfde functie.
4. **Registry-batch-1** — 38 nieuwe entries: agenda (9), notes (7), bugs (5),
   help (3), triggers (8), KB v2 admin (5), commands-list (1). Registry
   totaal: **14 → 76 entries**.
5. **`GET /api/commands/list`** nieuwe route (`modules/system/commands_list_routes.py`)
   met filters module/admin_only/gradatie_max/q. Spark's "welke commando's ken
   je?"-endpoint via `task_agent.list_commands()`.
6. **Admin-whitelist naar 18 leden**: KB-onderhoud (5), agenda-archive-all,
   bug-moderation (3), triggers-editing (7), apostrof-normalize.
7. **Auto-scanner** — `scripts/scan_routes_for_registry.py` scant 669 router-
   decorators; 617 concept-entries geschreven naar `/tmp/registry_scan_*.json`
   voor module-per-module review + aanvulling.
8. **KB-kaarten**:
   - `orphan-tag scan` (`kbv2-18829e2b`) in Weten, volledig ingevuld.
   - `kb-hit-log` (`kbv2-dc6c015e`) in Weten, volledig ingevuld.
9. **kb_hit_log_agent skelet** (`modules/agents/kb_hit_log_agent.py`) met
   `record()`/`retrieve()`/`stats_snapshot()`. Datafile-formaat vastgelegd:
   `data/chat_analytics/kb_hits.jsonl` JSON-Lines met gestandaardiseerde
   `match_source`-labels. Smoke-test 2 rijen OK. Hooks in response_composer
   bewust NIET geplaatst (skelet-fase).
10. **Kleine tweak**: topic-overview sample 5 → 10 begrippen
    (`chat/smart_intents_service.py:683`) — KB is naar 7000+ kaarten gegroeid.

**Testing**: 18/18 tag_sanitizer pytest-regressie pass. End-to-end via externe
API-URL: `POST /admin/normalize-apostrophes?dry_run=true` → 200 OK, correct
resultaat. `GET /commands/list` met filters agenda/admin_only/gradatie_max
allemaal correct. `kb_hit_log_agent.record()` + `retrieve()` roundtrip OK.

**Ontdekt maar niet uitgevoerd**:
- **Trader chat-intents** (`modules/trade/trader_intents.py`) — 8+ NL-regex
  patronen (`trader_start`, `trader_stop`, `trader_status`, `trader_explain`,
  etc.) draaien al vóór LLM-router. Ontbreken alleen in registry — aparte
  batch nodig zodat Spark er via `commands/list` naar kan wijzen.
- **`seed_registry_concepts_to_inbox.py`** — script bestaat maar niet gedraaid.
  Zou 617 skeletons met cmd_id als begrip seeden. Beter eerst readable-name-
  generator maken (cmd_id → menselijk begrip) om massa-seed nuttig te maken.

**Vervolg**: zie ROADMAP_CORE.md sectie "Sessie 58 — OPEN" voor P1/P2/P3.




## Sessie 57 (2026-02-24) — Trader Make It Right + Console consolidatie

### 🔴 Spoor A — Root-bug fix (`filled_coin` persist)

**Melding (Willem)**: "iedere user met potje moet trader werken. en hij is stuk."

**Root cause**: `open_pot()` / `open_cluster()` in `potjes.py` sloegen `filled_coin`
niet op in `position` → elk potje met echte BUY kwam in state `is_open=True,
filled_coin=null`. Downstream SELL/reconcile moest compenseren via Bitvavo-balance-clamp
→ drift op multi-user proxy accounts.

**Fix**:
1. `open_pot(user_id, pot_id, entry_price, current_cycle, ..., filled_coin=None)` —
   persist `float(filled_coin)` in `position.filled_coin`. Default 0 als niet meegegeven.
2. `open_cluster(user_id, pot_ids, ..., filled_coin=None)` — verdeelt totaal-`filled`
   pro-rata over pot_ids naar `capital`-ratio.
3. `monitor.py` — parseert `float(result["trade"]["filled"] or 0)` uit
   `execute_real_trade` en geeft door aan `open_cluster` én de fallback `open_pot`-loop.
4. Legacy €5.08 fallbacks vervangen door €10 (huidige potje-min) op:
   - `monitor.py:1428` (`min_order = 10.0` bij market-info fail)
   - `monitor.py:1709/1711` (`_trade_amount = 10.0` bij dynamic_price fail)
5. `potjes.py:5` docstring geüpdatet ("Start: 10 potjes à €10.00").

**Data-cleanup**:
- `POST /api/trade/potjes/auto-fix-ghosts-all?dry_run=false` — 2 ghosts opgeruimd
  (Geiser pot-001 BTC + Gerben pot-001 BTC) → status `free`.
- **Spark pot-006 backfill**: `position.filled_coin` van `null` → `0.00102325` BTC
  (uit Bitvavo werkelijkheid). Audit-log entry in pot.
- **Willem's bot gestart** — was `running=false` ondanks 3 potjes. Nu draait de
  trader voor alle 4 users met tokens (Willem 3/Spark 7/Geiser 2/Gerben 1).

### 🎨 Spoor B — Trader Console consolidatie (P1 backlog → done)

**Melding (ROADMAP sessie 52u)**: "Anker gap-up + Anker per markt + Reconciliatie =
1 collapsable card. Trader-tab visueel opruimen."

**Refactor** in `AnalyticsPage.js → TradeAnalyticsTab`:
- Nieuw state `subTab` (default 'overzicht'). Sub-tab bar met 3 knoppen:
  `trader-subtab-overzicht` / `-sync` / `-anker`. Cyan-highlight bij actief.
- **Overzicht**: RestwaardePortfolio + SparkTraderStatsPanel + Bot-kaarten (uitklap
  per user → potjes + history) + Audit-trail.
- **Sync & Reconcile**: 4 repair-buttons met confirm-dialogs:
  - `repair-auto-fix-ghosts-all` — reset ghost/hollow potjes (alle users)
  - `repair-close-sold-all` — sluit potjes met near-zero Bitvavo-balance
  - `repair-rebalance-from-bitvavo` — Spark's tokens herverdelen over pots
  - `repair-refresh-anchors` — sync 6 coin-anchors (BCH/BTC/ETH/SOL/ADA/ATOM)
  + `repair-result` panel toont JSON-response met success/fail.
  + `ReconcileSparkPanel` (per-coin drift diff).
- **Anker & Strategy**: `AnkerPanel` (gap-up guard + shadow-log + feature-flag).

**Testing**: iteration_57 → 100% pass backend + frontend, geen regressies.

---


## Sessie 56 (2026-02-24) — KB v2 Inbox Dedupe (P0) + Potjes/Tokens Audit

### 🧹 v13_kbv2_inbox_dedupe_002 — Dubbele kaarten in Kennisbank → Inbox

**Melding (Willem)**: "de laatste kaarten al een keer waren ingevuld. dus dubbele kaarten"

**Root cause**: `add_to_inbox()` vertrouwde uitsluitend op `knowledge_index.json` voor
"bestaat begrip al?"-check. Bij een stale index (na backup restore / rebuild / race) sluipt
er een lege inbox-kaart naast een reeds gevulde lade-kaart. 57 concrete gevallen gevonden
in productie-preview (o.a. "spinoza", "inclusief", "tag-curatie", "ethica", "durven").

**Fix — 3 lagen (`modules/kb_v2/service.py`)**:
1. **Helper `_begrippen_filled_in_lades()`** — deep-scan over 4 lade-bestanden → dict
   `begrip.lower() → (lade, kaart_id)` voor kaarten met gevulde `laag1`.
2. **Soft-filter in `list_inbox()`** — filtert lege inbox-kaarten weg waarvan begrip elders
   met laag1 staat. Response-veld `hidden_dupes_in_lade` (int) transparant.
3. **Hard-guard in `add_to_inbox()`** — bij index-miss deep-scan; hit → return existing +
   auto-repair index. Response: `existing=true, repaired_index=true, skipped_reason=already_filled_in_lade`.

**Data-cleanup**: `POST /api/kb/v2/admin/dedupe-inbox?dry_run=false` uitgevoerd → 57
dubbele kaarten permanent verwijderd. Inbox: 259 → 201 kaarten.

**Testing**: 7/7 pytest-tests groen (`tests/test_kb_v2_inbox_dedupe.py`). Testing-agent
100% success. Regressie op /stats en /classify OK.

### 🔧 Lint-blockers uit vorige fork opgelost (17 stuks)
- Route shadowing `/baseline/monthly` + `/baseline/run-scheduled-snapshot` → literalen
  boven parameterized `/baseline/{user_id}` gezet in `trade/routes.py`.
- Undefined `USERS_FILE` (regel 405) en undefined `user` (regel 591) in `shop/routes.py`
  vervangen door directe `users.json`-lookups.
- Dubbele dict-key `"open"` (F601) in `intent_registry/extractor.py` — legacy mapping
  `"open" → "openstaand"` verwijderd; nav-mapping `"open" → "navigate_open"` gehouden.
- Bare `except:` (5×) in `tests/test_modules_crud.py` → `except Exception:`.
- 7 upload-sites via nieuwe helper `modules/local_storage/persist_upload_bytes()`
  → eigen implementatie behoudt privacy-first local-only mandaat, respecteert linter.

### 🔍 Bonus: Potjes/Tokens audit (Willem-vraag "wie heeft hoeveel")

| User | Naam | ROAR tokens | Potjes | Klopt? |
|------|------|------------:|-------:|:------:|
| user-000 | Spark | 8 | **9** | ❌ +1 |
| user-001 | Willem | 3 | 3 | ✅ |
| user-a0ee2d7e | de Geiser | 2 | 2 | ✅ |
| **Totaal** | | **13** | **14** | |

Spark heeft 1 potje meer dan tokens. Alle 9 Spark-potjes hebben `minted_from:
willem_inleg_basis` (historische migratie). Ghost-users (`null`, `__ignored__`, `dummy`)
staan met 0 potjes → clutter maar niet corrupt. Legacy dubbele keys `pots`+`tokens` naast
`potjes` bij `user-a0ee2d7e` + `user-1996fa59` → mogelijke opruiming.

---

## Sessie 55 (2026-02-23) — Agenda DELETE flow + Intent Patronen Live-Editable + RULE_-prefix

### 🗓️ v13d_agenda_delete_001 — Chat-gestuurde delete-flow (P0)

**Root cause**: Willem: "haal aanstaande dinsdag uit de agenda" → Spark antwoordde
"doe dat via de agenda-tab" i.p.v. te executeren. De DELETE intent bestond simpelweg niet.

**Fix**:
- `smart_intents_service.py`: 4 nieuwe functies: `detect_agenda_delete_intent`,
  `handle_agenda_delete_start` (single/multi/none), `handle_agenda_delete_choose`,
  `execute_agenda_delete`, `handle_agenda_delete_cancel`.
- `chat/routes.py` early hook vóór capability-router zodat "agenda" niet door de
  agenda_vandaag capability wordt opgeslokt. Pending-state via session_state.
- Confirm-required flow met `ja/nee/nummer/alle` responses.
- **9 tests groen** in `tests/test_agenda_delete_v13d.py`.

### 🎛️ v13d_intent_patterns_json_001 — Regex-intents live-editable via Triggers-tab (P1)

**Root cause**: Willem: "vind raar dat je die Triggers tabs nooit bent gaan gebruiken."
Intent-detectors gebruikten hardcoded regex-arrays i.p.v. de JSON-triggers die de UI al
schreef. Nieuwe patronen betekende code-deploy.

**Fix — architectuur**:
- `modules/chat/intent_pattern_store.py` — BASELINE dict (hardcoded, niet-verwijderbaar)
  + `data/triggers/intent_patterns.json` (live additions) + mtime-invalidation cache.
- 16 intents gemigreerd (agenda_read, agenda_delete, note_create, bug_report, help_overview,
  suggest_action, topic_overview, clarify, community_recap, dnd_help, account_delete,
  stt_on, stt_off, tts_on, tts_off, ambient_off) = 118 baseline-patronen live.
- 4 API-endpoints: `GET /api/triggers/intent-patterns`, `POST /api/triggers/edit/intent/{k}/add`,
  `DELETE /api/triggers/edit/intent/{k}/pattern`, `POST /api/triggers/intent-patterns/test`.
- UI-sectie in `TriggersPage.js` met per-intent baseline (locked, groen) + additions
  (deletable, amber) + regex-input met compile-validatie.

### 📜 RULE_-prefix scheiding (P0, structureel)

**Root cause**: Emmy: "v13 = jouw Spark-versie, niet een agent-regel." De naam
`v13_agent_selfcheck_001` verwarde iedereen. Bovendien stond de regel nergens formeel.

**Fix**:
- Sectie "🚨 AGENT GEDRAGSREGELS (RULE_*)" toegevoegd aan top van `ROADMAP_CORE.md`.
- 6 regels geformaliseerd met `RULE_` prefix (los van feature-versies):
  `RULE_agent_selfcheck_001`, `RULE_dutch_only_001`, `RULE_no_database_001`,
  `RULE_deploy_preview_split_001`, `RULE_no_placeholder_data_001`,
  `RULE_footnote_metadata_001`.

### 🐛 Regressie fix bonus — READ intent nu ook via early hook

Pre-bestaande test `test_agenda_weekday_no_emoji::test_vandaag_still_agenda` faalde
("wat staat er morgen" → type=capability_response). Dezelfde early-hook fix voor DELETE
geldt nu ook voor READ. 13/13 agenda-tests groen.


---


## Sessie 54 (2026-02-24) — Attente Spark v13 Privacy-Guard + Zelfscan-feiten

### 🔒 v13_privacy_guard_001 — Privacy-matrix per gradatie (P0)

**Root cause**: Emmy (gradatie 5+) chatte met Spark en kreeg gevoelige familie-info van Willem terug (Lotus/Heidi in KB-context). `_load_relevant_kb` filterde alleen `privacy=="private"` — niet op tags (`familie`, `privé`, `financieel`).

**Fix — 3 lagen**:
1. **`modules/chat/privacy_guard.py`** — nieuwe module leest `data/system/privacy_defaults.json`:
   - `filter_kb_cards(cards, gradatie)` strip kaarten met verboden tags + persoonlijke lades + admin-familie-namen in laag1/ws5
   - `filter_identity_facts(facts, gradatie)` verwijdert about_user/about_relationship voor grad ≥ 5
   - `strip_person_names(text, gradatie)` maskeert namen tot 'iemand' (Lotus/Heidi/Willie/Arent + admin-relaties auto-geladen)
2. **`response_composer.py`** — 3 hook-punten na cards-load, na identity-facts-load, en na system_prompt-build
3. **13 regressietests** groen (`tests/test_privacy_guard_v13.py`)

**Regels per gradatie** (uit privacy_defaults.json):
- G1-G2 (admin/familie): alles zichtbaar
- G3-G4 (vrienden/buren): blokkeer financieel/gezondheid (+ familie voor G4)
- G5+ (kennis/onbekend/vreemde): blokkeer ook privé/persoonlijk/relaties + maskeer familie-namen

**Live geverifieerd**:
- Marieke (G3): `[privacy_guard] grad=3: filtered 1/5 KB cards`
- Fake G6: `filtered 4/5 KB cards` → Spark weigert netjes privé-info

### 📊 v13_zelfscan_facts_001 — Feitelijke emotie-distributie (P1)

**Root cause**: Zelfscan / emotie-vragen leidden tot LLM-hallucinaties ("73% blij") terwijl `data/emotions/pipeline_shadow/*.jsonl` 92% neutraal registreerde.

**Fix**:
- **`modules/chat/zelfscan_facts.py`** — `get_emotion_stats(days=7, user_id=None)` aggregeert JSONL events; normaliseert `neutral/neutraal` → `neutraal`
- **`_handle_zelfscan`** injecteert emo-line in zelfscan-output
- **`_load_ops_context`** vangt vragen als "wat voel ik", "welke emoties", "vaakst emotie" en levert feitelijke distributie als context vóór LLM-call

**Live output** (27 dagen data):
```
🎭 Emotie-distributie (laatste 27 dagen, 745 events): neutraal 92.2% · blij 4.6% · bedroefd 1.9%
```

### Files changed (sessie 54)
- `/app/backend/modules/chat/privacy_guard.py` (nieuw)
- `/app/backend/modules/chat/zelfscan_facts.py` (nieuw)
- `/app/backend/modules/chat/response_composer.py` (3 hooks)
- `/app/backend/modules/chat/composer_helpers.py` (emotie ops-context)
- `/app/backend/modules/chat/capability_handler_service.py` (zelfscan emo-injectie)
- `/app/backend/tests/test_privacy_guard_v13.py` (nieuw, 13 tests)

---


## Sessie 53 (2026-02-22) — Pot-value consistency fix (TraderPage vs AnalyticsPage)

### v13_pot_value_consistency_001 — €10.00 vs €10.26 mismatch opgelost
**Root cause**: `GET /api/trade/potjes/{user_id}` (`routes.py` ~1552) overlayde `live_value = dynamic_price` (finance_hub token-prijs €10.00) voor alle CLOSED pots. Gevolg:
- `TraderPage.js` toont `p.live_value ?? p.capital` → **€10.00** (dynamic)
- `AnalyticsPage.js` toont in aparte kolom `p.capital` → **€10.26** (boekwaarde incl. realized P&L)

**Fix**: voor closed pots wordt `live_value` nu gelijkgezet aan `capital` (boekwaarde). Voor open pots blijft `live_value` = mark-to-market (bestaand gedrag uit `potjes.get_potjes()`). `capital_dynamic` blijft als apart veld beschikbaar voor UIs die de token-prijs willen tonen. `_hybrid_source` bumped naar `finance_hub_v13`.

**Verificatie via `testing_agent` iter52**:
- ✅ Backend 12/12 pytest cases pass (3 users: user-000/8 pots, user-001/3 pots, user-a0ee2d7e/2 pots)
- ✅ Alle closed pots: `capital == live_value` bit-exact
- ✅ Open pot-006 (ATOM): mark-to-market waarde behouden apart van capital
- ✅ Frontend screenshot bevestigd: geen €10.00 meer op de Trader pagina; €10.15/€10.26 zichtbaar
- ✅ Regressietest bewaard op `/app/backend/tests/test_iter52_pot_value_consistency.py` (hergebruikbaar bij toekomstige pot-logic wijzigingen)

### Files changed (sessie 53)
- `/app/backend/modules/trade/routes.py` — get_user_potjes overlay (regel ~1552-1571)
- `/app/backend/tests/test_iter52_pot_value_consistency.py` — nieuwe regressietest (via testing_agent)

---



## Sessie 52r-3 (2026-02-21, laat) — Root cause `open_pot()` overschreef open positie

### v13r_open_pot_overwrite_guard_001 — Guard tegen overschrijven van open potje
**Root cause**: Willem's ATOM-koop van 16:03 (pot-001) werd om 18:02 overschreven door een BCH-BUY. Ontdekt via Bitvavo API live-poll (6 non-zero coins voor €60 crypto + €60 EUR = €121) vs. potjes JSON (7 potjes, alleen ATOM als open — later verdween ATOM ook). De reconcile-panel toonde de "orphan" coins correct.

`open_pot()` (`backend/modules/trade/potjes.py` regel 895) had alleen een guard tegen `pot_locked`, niet tegen `is_open`. Elke call overschreef `p["position"]` + `p["market"]` onvoorwaardelijk. Auto-monitor koos "vrij" potje via `get_available_pot()` (dat filtert wél op `is_open=False`), maar als er ergens tussen selectie en execute een race is (of een tweede call-path zonder guard), verloren we historie.

**Fix**: guard toegevoegd:
- Al open + andere market → return `{}` (BLOCK, met log-regel)
- Al open + zelfde market → return bestaande pot (idempotent skip, geen dubbele BUY-log/accounting)
- Vrij → gewoon openen (bestaande gedrag)

**Test** (`v13r_open_pot_guard_test`, inline via python3):
- ✅ ATOM-potje niet overschreven door BCH-BUY
- ✅ Idempotent skip bij zelfde markt (entry_price niet vernieuwd, geen dubbele stats.trades)
- ✅ Vrij potje wordt gewoon geopend
- State-backup + restore rondom test (geen data-mutatie op productie/preview)

### Files changed (sessie 52r-3)
- `/app/backend/modules/trade/potjes.py` — guard in `open_pot()` (regel 897-923)

### Niet aangeraakt
- `wallet/trade_history/user-000.json` (5 nieuwe trades van 18:02-18:03 blijven)
- Bestaande ATOM-orphan → Willem lost op via reconcile-panel na redeploy
- Dubbele BCH pot-007 → Willem beslist zelf (mergen of laten)

---


## Sessie 52r (2026-02-21, avond) — Post-deploy hotfix: LLM + Trader-sync + WalletView-banner

### v13q_llm_groq_deprecation_fix_001 — Primary model gemigreerd naar gpt-oss-120b
`llama-3.3-70b-versatile` is per **16-aug-2026** door Groq stilletjes gedeprecateerd → 404 op elke call → chain viel door naar Cerebras (402 quota op) → Emergent Universal Key (budget €7.03/€7.00 op) → `all_providers_failed` in productie.
- `.env` gewijzigd: `LLM_PRIMARY_MODEL=openai/gpt-oss-120b` (Groq's officiële replacement, gratis tier)
- Getest ✅: `/api/spark/compose` retourneert warme response via `primary/openai/gpt-oss-120b`

### v13q_llm_no_cloud_001 — Emergency (Emergent Universal Key) uitgezet
Op Willem's expliciete wens (geen cloud-fallback): `LLM_EMERGENCY_USE_EMERGENT=false`.
Trade-off: als beide free-tiers (Groq + Cerebras) tegelijk falen = Spark eerlijk stil (bewuste keuze i.p.v. cloud-vangnet).

### v13q_monitor_start_idempotent_001 — Trader-monitor sync-bug opgelost
Root cause: `monitor.start()` returnde `{success: False, message: "Monitor draait al"}` als de monitor al liep. Frontend las alleen `data.error` (niet `data.message`) → geen alert → user klikte 5-10× voordat 'ie een `bot_stop` deed. Log toonde 8× falen in 4 min (16:00-16:04).
- **Backend**: `monitor.py` regel 658 — bij `_running=True` return nu `{success: True, already_running: True, status: ...}` (idempotent)
- **Frontend**: `TraderPage.js` `startMonitor` — bij `!success` fallback naar `data.message` in alert
- Getest ✅ via curl: 2× snel achter elkaar start → 1e = "gestart", 2e = "draait al" met success=true

### v13q_walletview_banner_001 — Dikke banner als admin in Spark-view zit
Willem klikte Quick-Buy terwijl `walletView === 'spark'` → potje/trade landde op user-000, niet user-001. Hij zag niets in "zijn" front omdat het op Spark's wallet stond. UI toonde alleen een kleine toggle-knop.
- **Fix**: `TraderPage.js` — grote amber banner boven de pagina wanneer `isAdmin && walletView === 'spark'`. Inclusief "→ Terug naar mijn wallet"-knop.
- data-testid: `wallet-view-spark-banner`, `wallet-view-spark-banner-switch`

### Files changed (sessie 52r)
- `/app/backend/.env` — `LLM_PRIMARY_MODEL` + `LLM_EMERGENCY_USE_EMERGENT`
- `/app/backend/modules/trade/monitor.py` — idempotent `start()`
- `/app/frontend/src/components/modules/TraderPage.js` — banner + alert-fix

---


## Sessie 52q (2026-02-21) — Weekly-report boek-bron + AnnouncePrefs wiring + Monthly scheduler

### v13p_weekly_bookbased_001 — Weekly report leest nu uit boek-entries
`modules/boekhouder/weekly_report.py` had `accounting/transactions.json` als bron voor "Trade resultaat" — die tabel is sinds v13 Absolute Nulpunt niet meer de single source of truth. Gemigreerd naar `boekhouding/books/*/kasboek.json`:
- Loopt door alle books, filtert entries op `ts >= now-7d`
- Per book: n_entries, income, expense, netto → nieuwe sectie `boeken.per_book`
- Aggregaat: `boeken.n_boeken_actief`, `boeken.n_entries_week`, `boeken.netto_eur`
- Crypto-PnL approx uit spark-core book (source ∈ {trade, spark_fee, winst})
- Format toont nu **📚 Boeken deze week** met per-book breakdown
- Spark-brede DM naar Willem (via `_send_dm`) én naar alle ROAR token-holders werkt weer

Getest ✅: `GET /api/boekhouder/weekly/preview` toont Roadkillshop-verkoop €+10 als boek-regel.

### v13p_monthly_baseline_scheduler_001 — Monthly baseline in scheduler-loop
Nieuwe hook `_maybe_monthly_baseline_snapshot()` in `modules/scheduler/__init__.py`:
- Triggert tussen 02:00-03:00 UTC (rustige uren)
- Roept `should_run_snapshot()` (1e vd maand + geen marker)
- Balance-fn: user-000 = Bitvavo `last_known_eur`, andere users = 0.0
- `snapshot_all` + `mark_snapshot_done` → idempotent per maand
- Log-lijn: `[scheduler] monthly baseline snapshot: N users`

### v13o_announce_prefs_wiring — AnnouncePrefsPanel in profielpagina
`AnnouncePrefsPanel.js` bestond al maar was niet ingehaakt. Nu geïmporteerd + gerenderd in `UserProfilePage.js` na `DeviceSettingsPanel`. Toggles voor:
- `announce_shop_sale`, `announce_sepa_import`, `announce_migration`, `announce_spark_fee`
- Default alle 4 aan; blok werkt via `_auto_announce_entry` in `books.py` die `ui_preferences.json` leest

Getest ✅: 
- `GET /api/profile/ui-preferences/user-001` → 4 announce-flags, default true
- `PUT` toggle false → persist correct, toggle true → herstel correct
- `_auto_announce_entry` skipt DM als pref=false (verified via code + prefs-endpoint round-trip)

### Files changed (sessie 52q)
- `/app/backend/modules/boekhouder/weekly_report.py` — bron gemigreerd naar `BOOKS_ROOT`, `boeken.per_book` toegevoegd, format uitgebreid
- `/app/backend/modules/scheduler/__init__.py` — `_maybe_monthly_baseline_snapshot` + loop-hook
- `/app/frontend/src/components/profile/UserProfilePage.js` — import + render `AnnouncePrefsPanel`

---


## Sessie 52p (2026-02-21) — Auto-announce alle automatische boekingen

### v13o_auto_announce_001 — Transparantie voor auto-acties
Hook `_auto_announce_entry` in `books.add_entry`: elke boeking waarvan `source` NIET in `{manual, manual_opening}` zit, triggert automatisch een boekhouder-bot DM naar `owner_user_id`.

**Bronnen die announcen**:
- `shop_hook` — shop-verkoop/aankoop → "📈 Verkoop in Roadkillshop €+10"
- `camt053` / `mt940` — bank-import → "SEPA bank-import €+X"
- `migration` — retroactieve migratie → "Migratie-entry"
- `spark_fee_inlossen` — Spark-fee betaling → "Spark-fee inlossing €-X"

**Bronnen die NIET announcen** (bewust gedaan door user):
- `manual` — direct via API/UI door user zelf
- `manual_opening` — openingsbalans instellen via UI

**DM-formaat**: emoji (📈/📉) · book naam · bron-label · bedrag · omschrijving · papertrail-hash prefix

**Uitzondering**: user-000 (Spark) krijgt geen DM want dat is de bot zelf.

Getest ✅: verkoop €10 in Roadkillshop → Willem's boekhouder-inbox krijgt DM met hash `82a9e8c0`.

### Files changed
- `/app/backend/modules/boekhouder/books.py` — `_auto_announce_entry()` + hook in `add_entry()`
- `/app/memory/ROADMAP_CORE.md` — item afgevinkt

---


## Sessie 52o (2026-02-21) — Per-user shop-announcer (het gat gevuld)

### v13n_shop_announcer_001 — Gap gevuld
Nieuwe module `modules/boekhouder/shop_announcer.py`:
- `build_user_shop_report(uid, days)` — leest uit **nieuwe shop-books** (niet lege audit_log). Filter `owner_user_id=uid`. Verzamelt per shop: n_verkopen, omzet, uitgaven, resultaat, openstaand-Spark-fee.
- `announce_to_user(uid, days, force)` — DM van boekhouder-bot naar user met eigen rapport, gebruikt bestaande `_send_dm()`.
- `announce_all_shop_owners()` — batch voor alle users met minstens 1 shop.
- `admin_aggregate_report()` — admin ziet aggregatie: totaal-omzet + openstaand-fees over alle users.

Endpoints:
- `GET /api/boekhouding/shop-report/{user_id}?viewer_id=X&days=7` — owner of admin
- `POST /api/boekhouding/shop-report/{user_id}/announce` — owner of admin, force optioneel
- `POST /api/boekhouding/shop-report/announce-all` — admin-only
- `GET /api/boekhouding/shop-report-aggregate` — admin-only

**RBAC** (Emmy's punt): user ziet ALLEEN eigen shops. Andere user krijgt 403. Aggregate is admin-only. Getest ✅.

Vult het gat dat `weekly_report.py` liet vallen (audit_log leeg). Deze announcer werkt op nieuwe boek-bron. Kan als scheduler-target op maandag/vrijdag om 08:00.

### Files changed
- `/app/backend/modules/boekhouder/shop_announcer.py` — NIEUW
- `/app/backend/modules/boekhouder/books_routes.py` — 4 nieuwe endpoints
- `/app/memory/ROADMAP_CORE.md` — item afgevinkt

---


## Sessie 52n (2026-02-21) — Analyse + shop-omzet in maand-snapshot

### Emmy's inzicht: bestaande weekly_report vs nieuwe monthly_baseline
- `boekhouder/weekly_report.py` bestond al (7d DM via boekhouder-bot). Leest `audit_log.json` → **nu leeg** door v13 nulpunt → weekly-report is **BROKEN**.
- `trade/monthly_baseline.py` (nieuw) leest `capital_baseline` + live balance. Werkt.
- Beide zijn **complementair, niet dubbel**:
  - Weekly = korte in-app DM ("boekhouder-bot vertelt")
  - Monthly = ijkpunt-reset + archief-notitie ("verifieerbaar per maand")

### v13m_shop_omzet_in_snapshot_001 — Shop-omzet meegenomen
`snapshot_user()` verzamelt nu voor iedere user óók alle **shop-books** (`type=shop`, `owner_user_id=user`) die entries hebben in de te-sluiten maand:
- Per shop in de snapshot: `omzet_eur`, `uitgaven_eur`, `resultaat_eur`, `openstaand_spark_fee_eur`
- Notitie in `notes.json` bevat "**Shops deze maand:**" blokje met alle shops + omzet/resultaat/openstaand
- Tags in notitie: `shop_{linked_shop_id}` per shop
- Getest ✅: user-001 juli-afsluiting toont 0 shops (want alles nulpunt), na eerste verkoop komen ze mee

### Nieuwe todos in roadmap
- `weekly_report.py` bron migreren naar boek-entries (was audit_log, nu leeg)
- Weekly + Monthly alignment: verduidelijk waar welke stroom hoort (DM vs archief)

### Files changed (sessie 52n)
- `/app/backend/modules/trade/monthly_baseline.py` — `_collect_shop_omzet()` + notitie-uitbreiding
- `/app/memory/ROADMAP_CORE.md` — 2 nieuwe todos over weekly-report

---


## Sessie 52m (2026-02-21) — Maandelijkse baseline-snapshot

### v13_trader_monthly_baseline_001 — Maand-afsluiting per user
Nieuwe module `modules/trade/monthly_baseline.py`:
- `snapshot_user(uid, balance)`: log oude baseline → `/data/trade/monthly_baselines/YYYY-MM/{uid}.json`, reset baseline naar huidige, notitie in user's `notes.json` met resultaat + %
- `snapshot_all(get_balance_fn)`: alle users met baseline
- `should_run_snapshot()` + `mark_snapshot_done()`: 1e-vd-maand-idempotency check via marker-bestand
- Endpoints:
  - `POST /api/trade/baseline/monthly-snapshot/{user_id}?current_balance_eur=X` — handmatig
  - `GET /api/trade/baseline/monthly/{user_id}?limit=12` — historie per user
  - `GET /api/trade/baseline/monthly?limit=12` — alle users
  - `POST /api/trade/baseline/run-scheduled-snapshot` — check-and-run (idempotent per maand)
- Getest ✅: Spark user-000 juli-afsluiting €120.99 → €121.52 = **+€0.53 (+0.44%)**, snapshot + notitie aangemaakt, nieuwe baseline live.

### Voordeel (Emmy's inzicht)
User kan achteraf per maand precies zien wat trader-resultaat was. Logs + notities blijven bewaard. Voor voorwaarden-uitleg + ooit echte ROAR live essentieel: verifieerbaar per maand.

### Files changed
- `/app/backend/modules/trade/monthly_baseline.py` — NIEUW, snapshot service
- `/app/backend/modules/trade/routes.py` — 4 nieuwe endpoints
- `/app/memory/ROADMAP_CORE.md` — todos: scheduler-automatisering, trader-UI opruimen, vermogens-tab

---


## Sessie 52l (2026-02-21) — Correcties: Bitvavo=Spark + tab-rename

### v13_bitvavo_ownership_correctie_001 — Bitvavo is Spark's account
Verkeerde aanname vorige sessie: user-001 (Willem) had Bitvavo-baseline gekregen. **Correctie**:
- **Bitvavo = Spark's systeem-account** (user-000). Trader-bot beheert crypto potjes namens users.
- **user-001 (Willem)** heeft géén eigen Bitvavo-koppeling — alleen wallet-tokens.
- Baseline verplaatst: user-001 → €0.00, user-000 (Spark) → €120.99
- Update in `legal_privacy.json`, `ROADMAP_CORE.md` architectuur-blok, `gradatie_2.json` help-topic

### v13_tab_rename_001 — Duidelijker naam
- Tab **"Winst → Spark"** → **"Spark Verdiensten"** (admin-only, platform-fee stroom vanuit Spark's perspectief)
- In tab: "Totaal → Spark" → "Spark platform-fee inkomsten"; "Winst-stroom" → "Spark platform-fee events"
- Voor gewone users blijft de tab verborgen; zij zien alleen hun eigen shop-book met inkomsten & openstaande fees

### Files changed
- `/app/backend/data/trade/capital_baseline.json` — user-001 → 0, user-000 → 120.99
- `/app/frontend/src/components/modules/BoekhoudPage.js` — tab-label
- `/app/frontend/src/components/modules/WinstEventsTab.js` — labels binnen tab
- `/app/backend/data/system/legal_privacy.json` — Bitvavo-omschrijving
- `/app/backend/data/help/gradatie_2.json` — help-topic bijgewerkt
- `/app/memory/ROADMAP_CORE.md` — architectuur-diagram bijgewerkt

---


## Sessie 52k (2026-02-21) — Absoluut nulpunt + trader-baseline gezet

### v13_papertrail_reset_001 — Papertrail volledig gewist
Naast eerdere kasboek-reset ook `/data/boekhouder/logs/winst_events/` en `/data/boekhouder/logs/book_book-*/` gewist. Backup in `_backups/pre_v13_nulpunt_20260821_144252/papertrail/`. Nieuwe boekingen starten hash-chain vanaf GENESIS. Winst-events tab toont nu 0 events, €0 totaal.

### v13_trader_baseline_ijkpunt_001 — Live P&L baseline op huidige Bitvavo
`/data/trade/capital_baseline.json` per user gezet:
- **user-001 (Willem)**: €120.99 (huidige Bitvavo EUR-balance uit `deposit_watcher_state.json`)
- **5 andere users** (Spark, Geiser, +3): baseline €0
Live P&L begint dus nu bij €0.53 (kleine drift na set). Toekomstige stortingen/opnames rekenen vanaf dit ijkpunt.

### Files changed (sessie 52k)
- `/app/backend/data/boekhouder/logs/` — winst_events + book_* logs verwijderd
- `/app/backend/data/trade/capital_baseline.json` — 6 users met nulpunt-baseline

---


## Sessie 52j (2026-02-21) — Grote schoonveeg: absoluut nulpunt

### Wat is weg (backup in `_backups/pre_v13_nulpunt_20260821_144252/`)
- **7 trade_history files** — 93+120+2401+3+2+2+8 = **2629 oude trades** gewist bij Spark, Willem, Emmy en 4 andere users
- **13 user_wallets** — alle `balance_tokens` en `balance_eur` op 0
- **tikkie_topups** — leeg
- **system/spark_kasboek.json** — lijsten leeg (was oude centrale audit)
- **system/audit_log.json** — leeg (was bron van de 276 migratie-ruis)
- **trade/deposits.json** — leeg (was Bitvavo deposit-watcher log)
- **system/deposit_watcher_state.json** — gereset
- **10 test-users** — `test-bank`, `test-bank-001..003`, `test-snap-001`, `test-user-5061f3d2/97bf8c9a/b95ac972/bfb67f3e`, `test-vk` → verplaatst naar `_backups/`
- **Alle 4 boeken + openstaand_spark** — gereset naar €0

### UI opgeschoond
- Tabs "Archief: Kasboeken" en "Archief: Transacties" **verwijderd** uit BoekhoudPage (verwezen naar dode data). Admin ziet nu: Boeken · Winst → Spark · Klanten
- Header-teller `4 kasboeken | 100 transacties` verborgen voor non-admin (was verwarrend want telde oude data)

### Verified nulpunt
```
Books:             all €0.00 (n=0)
Wallets:           13× balance=0
Openstaand Spark:  €0.00
Trade history:     0 in alle files
Test-users:        0 in /data/users/
Bonnetjes:         0 in alle archives
```

### Files changed (sessie 52j)
- `/app/frontend/src/components/modules/BoekhoudPage.js` — Archief-tabs weg, tellers conditional
- `/app/backend/data/*/` — 10 files gewist naar nulpunt, 10 test-users gearchiveerd

---


## Sessie 52i (2026-02-21) — BTW/KOR + openstaand + ruis-cleanup + docs

### v13b_btw_kor_openstaand_001 — Verkoop-flow refactor
- Verkoper geeft **NETTO** op, systeem berekent BRUTO = NETTO × (1 + btw_pct/100)
- **KOR-toggle** per shop → geen BTW berekening
- Verkoper's book krijgt schone NETTO omzet (Moneybird-vriendelijk)
- **Spark-vergoeding (1% van bruto)** wordt NIET ingehouden — komt in `openstaand_spark.json` per shop
- **2 bonnen** gegenereerd: netto (voor Moneybird) + bruto (voor koper met BTW-splitsing of KOR-opmerking)
- Endpoints: `POST /hooks/shop-sale` (netto_eur veld), `GET /hooks/openstaand/{shop_id}`, `POST /hooks/inlossen/{shop_id}` (wallet-transfer + boek naar spark-core)
- Getest ✅: netto €100 → bruto €121 (BTW €21) → Roadkillshop €100, openstaand €1.21. Ook KOR-flow (BTW=0)

### v13_shop_finance_config_001 — Admin BTW/fee-config endpoint
`GET/PATCH /api/boekhouding/shop-finance-config` — admin-only. Velden: `btw_default_pct`, `spark_fee_pct`, `btw_kor_default`, `commissie_default_pct`. Nieuwe shops erven deze defaults.

### v13_boekhouding_tabs_cleanup_001 — Dubbele tabs opgelost
`BoekhoudPage` default tab is nu `boeken` (was `overzicht`). Oude tabs verplaatst en hernoemd naar "Archief: Kasboeken" en "Archief: Transacties" — alleen zichtbaar voor admin. Non-admin ziet alleen "Mijn Boeken".

### v13_ruis_cleanup_001 — Bonnetjes-testdata weg
`data/users/user-a0ee2d7e/archief/bonnetjes/` (3× dezelfde tx-id `2921e03a...`, test van "de Geiser") gewist. `bonnetjes_index.json` leeg. Alle boeken op nulpunt.

### v13_architecture_note_001 — Drie-lagen-scheiding in privacy + roadmap
`legal_privacy.json`: nieuwe sectie "Geld & boekhouding (v13)" met de architectuur-scheiding:
- **Bitvavo potjes** = crypto/trader raw assets
- **Spark Wallet** = spendable EUR-tokens (bridge)
- **Zakelijke bank** = SEPA-XML eindstation (Moneybird-input)
Papertrail, KOR, BTW-suggestie, geen live bank-koppeling — alles uitgelegd in privacy-tekst zichtbaar voor users.
`legal_privacy.json` versie bumped naar `0.3-draft-boekhouding-v13`.

### v13_admin_help_001 — gradatie_2 help-topic "Boekhouding v13"
`data/help/gradatie_2.json` topic `boekhouding-v13` met korte + diepe uitleg, synoniemen, nav-path. Erft door naar gradatie 1. Getest: `/api/help/for-viewer` toont 27 topics inclusief nieuwe.

### Files changed
- `/app/backend/data/shops/_meta.json` — `commissie_default_pct: 1.0`, `config.btw_default_pct: 21.0`, `config.spark_fee_pct: 1.0`, `config.btw_kor_default: false`. Ook `shop-roadkill.commissie_pct: 1.0`.
- `/app/backend/modules/boekhouder/shop_hooks.py` — BTW/KOR/openstaand refactor
- `/app/backend/modules/boekhouder/books_routes.py` — nieuwe `/hooks/openstaand/{id}`, `/hooks/inlossen/{id}`, `/shop-finance-config` GET+PATCH
- `/app/frontend/src/components/modules/BoekhoudPage.js` — default tab `boeken`, oude tabs archief-label
- `/app/backend/data/help/gradatie_2.json` — nieuw topic boekhouding-v13
- `/app/backend/data/system/legal_privacy.json` — architecture-sectie + versie bump
- `/app/memory/ROADMAP_CORE.md` — architectuur-diagram + Cluster Boekhouding uitgebreid
- `/app/backend/data/users/user-a0ee2d7e/archief/bonnetjes*` — testdata gewist

---


## Sessie 52h (2026-02-21) — Shop→Book brug + Winst-events papertrail

### v13_shop_book_hook_001 — Shop-verkoop/aankoop koppelt aan boek
- Winkelstraat `create_shop()` roept `ensure_shop_book()` → elke nieuwe shop krijgt automatisch een book
- Nieuwe service `boekhouder/shop_hooks.py`:
  - `record_shop_sale(shop_id, amount_eur)` → netto naar shop-book + spark_deel naar book-spark-core (op basis van `commissie_pct` of override)
  - `record_shop_purchase(shop_id, amount_eur)` → uitgave in shop-book
- Endpoints: `POST /api/boekhouding/hooks/shop-sale` + `.../shop-purchase`
- Getest: €100 verkoop → €97.50 netto Roadkillshop + €2.50 Spark Core (2.5% commissie), beide met papertrail-hash

### v13_winst_events_papertrail_001 — Aparte winst_events topic
Elke shop-sale (en straks trader-winst) logt óók een record in papertrail-topic `winst_events` met `{bruto_eur, spark_deel_eur, netto_eur, shop_id, book_id, source_id}`. Hash-chain per topic.
- Endpoint `GET /api/boekhouding/winst-events?viewer_id=X&limit=N` (admin-only): geeft events + `total_spark_deel_eur`
- Frontend tab **"Winst → Spark"** in Boekhouding: card met totaal-Spark-uitkering, events-lijst met bruto/netto/spark-deel/hash, uitleg-blok over chain
- Fundament voor: voorwaarden-uitleg aan users, audit door externe boekhouder, echte ROAR-uitkering met verifieerbaar spoor

### Files changed
- `/app/backend/modules/winkelstraat/__init__.py` — auto-book hook bij create_shop
- `/app/backend/modules/boekhouder/shop_hooks.py` — NIEUW, sale/purchase → book brug
- `/app/backend/modules/boekhouder/books_routes.py` — `/hooks/shop-sale`, `/hooks/shop-purchase`, `/winst-events` endpoints
- `/app/frontend/src/components/modules/WinstEventsTab.js` — NIEUW, winst-viewer met chain-uitleg
- `/app/frontend/src/components/modules/BoekhoudPage.js` — nieuwe tab `winst` (admin-only)

---


## Sessie 52g (2026-02-21) — Nulpunt + Papertrail hash-chain

### v13_boekhouding_papertrail_001 — Elke boeking hash-verankerd
`books.add_entry()` haakt nu in `LogAgent.record()` — schrijft naar
`/data/boekhouder/logs/book_{book_id}/YYYY-MM.jsonl`:
- SHA256 hash-chain: `hash_prev` van vorige event + huidige data → `event_hash`
- Eerste boeking begint met `GENESIS`
- Bij manipulatie achteraf breekt de hash — verifieerbaar
- `entry.papertrail_hash` staat mee in kasboek.json én zichtbaar in UI (mono cyan `#4f37f341`)

### v13_boekhouding_reset_001 — Schoon nulpunt
`POST /api/boekhouding/books/{id}/reset` wist alle entries (papertrail blijft bewaard).
UI-knop toegevoegd bij Instellingen-tab van detail-bark: rode "Reset naar €0.00" met confirm.

### Ruis opgeruimd
276 vervuilde audit_log migratie-entries in `book-spark-core` gewist. Ook Roadkillshop, Zorgboerderij, Willem-Privé gereset. Alle 4 boeken staan nu op **€0.00** — echt nulpunt zoals gevraagd.

### Files changed
- `/app/backend/modules/boekhouder/books.py` — LogAgent-hook + `data=` param fix
- `/app/backend/modules/boekhouder/books_routes.py` — `POST .../reset` endpoint
- `/app/frontend/src/components/modules/BoekhoudingBoekenTab.js` — reset-knop + papertrail-hash tonen bij entries

---


## Sessie 52f (2026-02-21) — Boekhouding frontend + balances + SepaHub refactor

### v13_sepa_hub_001 — SEPA als eigen hub-module
Refactor: `modules/boekhouder/sepa.py` verplaatst naar `modules/sepa_hub/`:
- `SepaHub` class met `parse_camt053` / `parse_mt940` / `generate_pain001` / `reconcile`
- `get_hub()` singleton, `_meta.json` voor Synapslaag zichtbaarheid
- Books-routes consumeren via `get_sepa_hub()` — geen boekhouder-dependency meer
- Reconcile-skeleton: matcht op datum+bedrag+iban tegen bestaande entries
- Ontkoppeld → later ook bruikbaar voor wallet/shop/andere modules

### v13_boekhouding_opening_balance_001 — Openingsbalans-endpoint
`POST /api/boekhouding/books/{id}/opening-balance?amount_eur=X`: idempotent (vervangt bestaande opening). Gebruikt voor "balances goed zetten" bij nieuwe boeken.

### v13_boekhouding_ui_001 — Frontend "Boeken" tab
Nieuw component `BoekhoudingBoekenTab.js`, ingehaakt in `BoekhoudPage`:
- Grid met 4 books-cards (Spark Core €975.85, Roadkillshop, Zorgboerderij, Willem-Privé €0)
- Elke card: icon+kleur uit meta, balans (groen/rood), in/uit/regels, IBAN-status
- Klik op card → **detail-bark** met 3 sub-tabs:
  - **Kasboek**: entries lijst (natte in/uit-kleuring, timestamp, type)
  - **Instellingen**: IBAN + Bank naam invoer, openingsbalans instellen
  - **SEPA**: CAMT.053 upload + MT940 upload + pain.001 export (download XML)
- Admin ziet alle 4 tabs (Kasboeken, Transacties, Boeken, Klanten), non-admin ziet "Mijn Privé + Mijn Boeken"
- `data-testid`s: `book-card-{id}`, `book-tab-{entries|instellingen|sepa}`, `book-iban-input`, `book-camt-file`, `book-mt940-file`, `book-export-pain001-btn`, etc.

### Files changed (sessie 52f)
- `/app/backend/modules/sepa_hub/__init__.py` — NIEUW (SepaHub class + get_hub)
- `/app/backend/modules/sepa_hub/parsers.py` — verplaatst van boekhouder/sepa.py
- `/app/backend/modules/sepa_hub/_meta.json` — hub-metadata
- `/app/backend/modules/boekhouder/books_routes.py` — SepaHub import + opening-balance endpoint
- `/app/frontend/src/components/modules/BoekhoudingBoekenTab.js` — NIEUW
- `/app/frontend/src/components/modules/BoekhoudPage.js` — nieuwe 'boeken' tab + import

---


## Sessie 52e (2026-02-21) — Multi-boekhouding + SEPA + Inkomende oproep + Login-dots

### v13_boekhouding_books_001 — Multi-container boekhouding
Elk boek is een eigen container met unique ID onder `/data/boekhouding/books/book-{id}/`:
- 4 initiële seed-boeken: `book-spark-core`, `book-roadkillshop`, `book-zorgboerderij`, `book-willem-prive`
- Types: `spark_core` / `shop` / `entity` / `user_prive`
- Elk boek: `_meta.json` (id, naam, type, owner, iban, bank_naam, linked_shop_id, kleur, icoon), `kasboek.json`, `reserve.json`, `closings.json`, `documents.json`, `sepa_batches.json`, `bank_imports.json`
- Endpoints: `GET/POST /api/boekhouding/books`, `GET/PATCH/DELETE /api/boekhouding/books/{id}`, `GET/POST .../entries`
- Owner-only + admin (gradatie ≤ 2). Spark-core is systeem-boek (readable by all).
- Auto-hook `ensure_shop_book()` klaar voor koppeling aan shop-create-flow.

### v13_boekhouding_migration_001 — Retroactief opsplitsen
`spark_kasboek.json` + `audit_log.json` (276 entries) gemigreerd naar books via heuristics: shop_id → shop-book, "zorgboerderij" in tekst → book-zorgboerderij, user-001 personal → willem-prive, fallback → spark-core. Origineel spark_kasboek.json blijft ongewijzigd — additief met `source_id` duplicate-check. Getest: 276/276 → book-spark-core (audit_log heeft geen shop-context; handmatig verplaatsen kan later).

### v13_boekhouding_sepa_001 — Lokale SEPA parsers (geen cloud)
Uitgesplitst als **eigen hub-module** `modules/sepa_hub/` (agent-hub pattern zoals FinanceHub):
- `SepaHub.parse_camt053()` voor bank-afschriften import
- `SepaHub.parse_mt940()` voor legacy SWIFT afschriften
- `SepaHub.generate_pain001()` voor uitgaande betalings-batches
- `SepaHub.reconcile(book_id, tx)` — matched/unmatched op datum+bedrag+iban (skeleton)
- Books-routes consumeren via `get_sepa_hub()` singleton
- Endpoints (via boekhouding-router): `POST /api/boekhouding/books/{id}/sepa/import-camt`, `.../import-mt940`, `.../export-pain001`
- Getest via nieuwe hub: pain.001 export van €25 via `SepaHub.generate_pain001()` werkt

### v13_boekhouding_notify_001 — Notitie + urgent hook
Bij nieuwe factuur/deadline in een book → automatisch:
- Taak in user's `tasks.json` met tag `book_{id}` + `boekhouding`
- Urgent-item in `/data/urgent/{user_id}.json` voor sidebar-glow (severity amber/red)
- SEPA-batch klaar → red urgent + taak "downloaden"

### v13_prive_incoming_call_001 — Inkomende oproep bark
- Backend `/api/prive-call/ring|incoming|answer` — 30s ring timeout, lokaal signaal
- Frontend polt elke 4s in `GesprekkenPage`, toont `IncomingCallBark` modal met:
  - Pulserende glow-rand in kleurschema
  - Beller-avatar met puls-animatie
  - "belt je" / "wil beeldbellen" + rode weiger / groene accept (extra puls op accept)
- Bel-iconen in privé-header pulseren mee wanneer geselecteerd contact belt
- Accept → open PriveCallBark met beller als contact

### v13_login_glow_dots_001 — Loginscherm hartslag-dots
8 dots in primaire kleuren (amber/cyaan/paars/groen/pink/blauw/oranje) op vaste posities met `heartbeatDot` keyframe (2.4s cyclus, scale + opacity puls). CSS-only, weinig werk. Klaar voor latere Fronts-tab tuning.

### Files changed
- `/app/backend/modules/boekhouder/books.py` — NIEUW, book CRUD service
- `/app/backend/modules/boekhouder/books_routes.py` — NIEUW, REST + SEPA endpoints
- `/app/backend/modules/boekhouder/migration.py` — NIEUW, retroactieve splitser
- `/app/backend/modules/sepa_hub/__init__.py` — NIEUW, SepaHub agent-hub (parse + generate + reconcile)
- `/app/backend/modules/sepa_hub/parsers.py` — verplaatst (was boekhouder/sepa.py) — pure parsers
- `/app/backend/modules/sepa_hub/_meta.json` — hub-metadata voor Synapslaag
- `/app/backend/modules/boekhouder/notify.py` — NIEUW, task/urgent hooks
- `/app/backend/modules/prive_call/__init__.py` — NIEUW, incoming ring signalering
- `/app/backend/server.py` — imports + seed on startup
- `/app/frontend/src/components/chat/IncomingCallBark.js` — NIEUW
- `/app/frontend/src/components/workspace/GesprekkenPage.js` — polling + ring-op-openPriveCall + bel-icon puls-animatie
- `/app/frontend/src/components/auth/LoginForm.js` — 8 heartbeat dots

---


## Sessie 52d (2026-02-21) — Roadmap opgeschoond + help synced

### v13_roadmap_split_reader_001 — Roadmap-reader leest CORE
`capability_handler_service._handle_taken_lijst`:
- Zoekt eerst in `ROADMAP_CORE.md` (waar de actieve items staan), fallback naar `ROADMAP.md` (wegwijzer) → `roadmap.json` legacy
- Herkent nieuwe checkbox-stijl: `[x]` = gedaan, `[~]` = deels, `[ ]` = te doen
- Response groepeert nu op **Te doen** / **Deels** / **Recent gedaan** met eigen emoji-prefix
- Getest via `/api/chat/message` "welke taken staan er nog?" → Spark toont het v13 Skype-Spark cluster met alle statussen

### Nieuwe cluster in ROADMAP_CORE.md
"📞 CLUSTER — Skype-Spark & Fronts (v13, sessie 52, feb 2026)" bovenaan, na moreel kompas.
- ✅ 8 items gedaan (bel-icons, PriveCallBark, offline-detectie, --alert-base, split status/actie, mic/cam devices, bot-filter, WhatsApp fallback)
- 🟡 1 item deels (Fronts config schema in Kladblok, backend endpoints nog te bouwen)
- 🔴 5 items open (Beheer→Fronts tab, loginscherm dots+font, inkomende oproep, lokale-socket verbinding)

### Help-topic Privé-bellen
`data/help/gradatie_7.json` → topic `prive-bellen` met korte + diepe uitleg, wat werkt/wat nog niet, waar de instellingen zitten, synoniemen voor zoeken. Erft door naar alle gradaties (2-7). Getest: `GET /api/help/for-viewer?user_id=user-001` toont 26 topics, "Privé-bellen (UI-shell)" gevonden.

### Files changed
- `/app/memory/ROADMAP_CORE.md` — nieuwe cluster bovenaan
- `/app/backend/modules/chat/capability_handler_service.py` — leest CORE + checkboxes parsed
- `/app/backend/data/help/gradatie_7.json` — topic prive-bellen

---


## Sessie 52c (2026-02-21) — Bark status/actie split + Fronts draft in Kladblok

### v13_alert_color_var_001 — `--alert-base` CSS-variabele
`index.css`: nieuwe root variabele `--alert-base: #ef4444`. Gebruikt door PriveCallBark voor offline/geen-gehoor tint. Later tunable via Fronts. Vervangt hardgecodeerde `rgba(239,68,68,...)`.

### v13_state_action_split_001 — Status-badge vs actie-tekst gesplitst
Voorheen zelfde tekst op 2 plekken. Nu:
- **Status-badge** rechtsboven = puur status: `Verbinden` / `Overgaan` / `Verbonden` / `In beeld` / **`Offline`**
- **Actie-tekst** onder avatar = context met `{naam}`: `Probeert Heidi te bereiken…` / `Heidi wordt gebeld…` / `Gesprek met Heidi` / **`Geen antwoord — Heidi is offline. Probeer later opnieuw.`**
Kleuren via `color-mix(--glow-base)` en `color-mix(--alert-base)` — geen hardcoded hex meer.

### v13_fronts_config_draft_widget_001 — Fronts draft in Kladblok
Nieuwe widget `FrontsConfigDraftWidget` in Kladblok. Toont concept-JSON-schema:
- `screens[auth.login|chat.prive.call|workspace.dashboard]`
- Per screen: kleuren · lettertype · animaties · `status_labels` · `action_texts` (met `{naam}` template) · `timings_ms`
- Copy-JSON knop
Volgt Emmy's suggestie: eerst parkeren in Kladblok, dan verplaatsen naar Beheer → Instellingen → Fronts wanneer schema definitief is. Toekomst-endpoint: `GET/PUT /api/system/fronts-config`.

### Files changed
- `/app/frontend/src/index.css` — `--alert-base` variabele
- `/app/frontend/src/components/chat/PriveCallBark.js` — status/actie split, CSS-var kleuren
- `/app/frontend/src/components/admin/sandbox/widgets/FrontsConfigDraftWidget.js` — NIEUW
- `/app/frontend/src/components/admin/sandbox/registry.js` — widget geregistreerd

---


## Sessie 52b (2026-02-21) — Offline-gehoor + Mic/Cam device selectie

### v13_call_offline_state_001 — "Geen gehoor" bij offline contact
`PriveCallBark` leest nu `contact.online`. Als false:
- Overgaan → na 4.8s → `no_answer` state
- Rode "Geen gehoor" badge + grijs-gefilterde avatar + "X is offline — probeer later opnieuw"
- Auto-hangup 15s later
Bug gefixt: `onClose` in dep-array veroorzaakte oneindige re-mount → `onCloseRef` pattern.

### v13_call_devices_001 — Mic/Camera selectie in Mijn Profiel
Backend (`profile/__init__.py`): 5 nieuwe pref-velden — `audio_input_device_id`, `video_input_device_id`, `audio_input_label`, `video_input_label`, `use_default_devices`. Default = "default"/systeem-standaard.

Frontend (`DeviceSettingsPanel.js`, NIEUW):
- `navigator.mediaDevices.enumerateDevices()` (lokale browser-API, geen cloud)
- Toggle "Gebruik systeem-standaard apparaten" (default aan)
- Dropdowns mic + cam (labels pas zichtbaar na permission-grant)
- Test-mic → 4s live VU-meter met `AnalyserNode`
- Test-cam → 5s live `<video>` preview
- Alle streams stoppen automatisch na test (geen achtergrond-capture)
- Ververs-knop vraagt eenmalig `getUserMedia({audio:true,video:true})` voor de labels
- "Huidige keuze"-samenvatting onderaan
Ingehaakt in `UserProfilePage.js` na Geluid-panel.

### Files changed
- `/app/frontend/src/components/chat/PriveCallBark.js` — offline state + ref-fix
- `/app/frontend/src/components/profile/DeviceSettingsPanel.js` — NIEUW
- `/app/frontend/src/components/profile/UserProfilePage.js` — import + render
- `/app/backend/modules/profile/__init__.py` — UIPreferences + DEFAULT_UI_PREFS uitgebreid

---


## Sessie 52 (2026-02-21) — Privé-bel UI-shell + WebRTC-verwarring weg

### v13_prive_call_ui_001 — Lokale bel-shell in privé chat
Willems visie geimplementeerd: bel + camera icoon persistent rechtsboven wanneer een privé-contact geopend is. Iconen gloed via `--glow-base` (uit profielkleurschema). Klik opent een bark-modal.

**Bark-modal (`PriveCallBark.js`)**:
- Zwart video-vlak = VLC/lokale-cam placeholder
- Avatar van gebelde persoon zichtbaar tijdens verbinden / pauze / audio-only
- State-progressie: `Verbinden → Overgaan → In gesprek/In beeld` (visuele feedback zonder echte verbinding)
- Controls: Mute-toggle, Camera-toggle (alleen video), Hangup
- Self-PIP blok (jouw zelfbeeld) rechtsonder in video-modus
- Glow-rand rondom hele modal via CSS variabele
- LIVE-badge wanneer state = active

### Ruis-opruiming
- WebRTC-comments in `ContactCallPopup.js` neutraal gemaakt (was verwarrend "WebRTC komt later" — nu "in-app bellen zit in Privé-tab")
- Geen enkele WebRTC-code aanwezig. Alles blijft lokaal.

### Files changed
- `/app/frontend/src/components/chat/PriveCallBark.js` — NIEUW, UI-shell modal
- `/app/frontend/src/components/workspace/GesprekkenPage.js` — import + state + bel/video click handlers + glow styling op header-buttons + render bark
- `/app/frontend/src/components/chat/ContactCallPopup.js` — comment-refactor (geen gedragsverandering)

### Volgende sessie
Voor echte in-app calling: aparte sessie voor lokale-socket verbinding (Odroid-netwerk), mic/cam capture, VLC-koppeling. Deze shell staat klaar.

---

## Sessie 51 (2026-07-31) — Prod-merge + trade-log fix

### Merge productie-backup
Willem's zip (`spark_backup_changes_20260731_050848.zip`, 3.2 MB, 66 files) uit productie geladen. Backup gemaakt in `data/_backup_before_prod_merge_20260731_051228/` (213MB). 57 JSON files overschreven, 9 JSONL-logs append-merged (dedup op line). Family_relations van sessie 50e bleven behouden (waren óók in prod-zip). 

### v11_audit_cluster_001 — Trade-log werkt niet goed → FIX
**Willems melding**: trade-log werkt niet goed.

**Root cause gevonden**:
1. `open_cluster()` en `close_cluster()` in `potjes.py` riepen NIET `announce_buy`/`announce_sell` aan → sinds bot naar cluster-mode ging (~29 juli) werden bot-trades **niet meer in audit_log.json geregistreerd**. Alleen handmatige trades via `open_pot`/`close_pot` werden gelogd.
2. `announce_sell` audit-entry miste `amount_eur` → UI toonde altijd `-` bij sell entries.

**Fixes**:
- `open_cluster()`: per pot in cluster → `announce_buy()` call (audit + Boekhouder-DM)
- `close_cluster()`: per pot → `announce_sell(user_id, pid, market, exit_price, pnetto)` call
- `announce_sell` audit-entry: `amount_eur=netto` toegevoegd (was ontbrekend)

### v11_audit_backfill_001 — Historische trades ingehaald
Script backgevuld: uit `data/trade/logs/trace_*.jsonl` alle open_cluster/close_cluster events geëxtraheerd → 16 audit-entries toegevoegd inclusief 2× BCH-EUR BUY op 30 juli 19:08. Trade-log nu chronologisch compleet tot 30 juli.

### Files changed
- `/app/backend/modules/trade/potjes.py` — announce_buy/sell in open_cluster + close_cluster
- `/app/backend/modules/boekhouder/service.py` — announce_sell amount_eur toegevoegd
- `/app/backend/data/` — 57 JSON files uit prod-zip
- `/app/backend/data/system/audit_log.json` — +16 backfill entries (266 totaal)

---


## Sessie 50f (2026-02-01) — SPS Daily-Event rijke UI + KB-fill "kan ik wat voor je doen"

### v11_daily_event_rps_001 + v11_daily_rps_001 — Daily-Event gebruikt nu RpsBark
**Willems melding**: 2 SPS-modules bestonden (simpele DailyEventCard + rijke RpsBark). Simpele versie gaf verkeerde info bij loss ("je ontsnapte met de hakken over de sloot" ipv "je verloor").

**Fix**:
- `daily_event.py` bark-tekst eerlijk: bij loss "je verloor deze ronde. Kom morgen sterker terug." (was misleidend "je ontsnapte")
- `RpsBark` component uitgebreid met `dailyMode` prop:
  - In daily-mode: gebruikt `/api/dnd/daily-event/*` endpoints (1×/dag + goud-uitkering)
  - Sessie-score-bar verborgen (irrelevant voor 1-ronde event)
  - Lifetime-stats verborgen (dailyMode focus op deze ronde)
  - Buttons disabled na play
  - Header title: "⚔ Vecht voor je leven"
  - Behoudt KB-kaart-thumbnails + avatars + "Spark denkt na" animatie
- `DailyEventCard.js` herschreven als dunne wrapper (~65 regels ipv 128): laat trigger-button staan, opent RpsBark met `dailyMode=true`

**Getest**: bark-tekst geverifieerd via curl (`result: loss` → bark "je verloor deze ronde"). Testing-agent: 13/13 backend groen, modal opent correct met 3 KB-thumbnails.

### v11_kb_fill_offer_001 — "Kan ik wat voor je doen"-flow
**Willems visie**: proactieve trigger — user biedt hulp, Spark kiest KB-kaart met leeg ws5-veld, parafeert, slaat op. Voorkomt dat elke kaart handmatig moet ge-reforge worden.

**Implementatie** in `wedervraag_service.py`:
- 6 nieuwe patronen (`KAN_IK_HELPEN_PATTERNS`): "kan ik wat voor je doen", "wat kan ik doen", "waarmee kan ik helpen", "help je een handje", "iets voor je doen", "wil je dat ik iets doe"
- `pick_random_kbv2_card_with_gap()` — leest 4 KBv2-lades, filtert 733 kaarten met ≥1 leeg ws5-veld, prefereert kaarten met meer gaten (top-30% random)
- `format_offer()` + `format_paraphrase()` — vriendelijke NL-teksten
- `is_affirmative()` / `is_negative()` — ja/nee-detectie

**Multi-turn state machine** in `chat/routes.py` (hook 0b2):
1. **STAP 1**: user "kan ik wat voor je doen" → `type=kb_fill_offer` + state `phase=offer`
2. **STAP 2**: user "ja" → `type=kb_fill_question` (echte 5W-vraag) + state `phase=awaiting_answer`
3. **STAP 3**: user antwoordt → `type=kb_fill_paraphrase` ("Dus... Klopt dit?") + state `phase=awaiting_confirm`
4. **STAP 4**: user "ja klopt" → save via `apply_answer()` + state cleaned + `type=kb_fill_saved`
5. **Escape-routes**: "nee" bij offer → declined; "nee" bij parafrase → retry; "skip" bij antwoord → skipped

**Getest end-to-end** met curl: alle 4 stappen groen, kaart "Geef" kreeg 'wat' veld, testkaart daarna teruggezet naar leeg. Testing-agent bevestigde 13/13 pytest.

### v11 architectuur-notitie: harde strings vs self-aware triggers
Willems visie voor toekomst: dagelijkse intents (zoals "kan ik wat voor je doen") door Spark LLM zelf laten kiezen ipv regex. Voor MVP behoudt v11 regex (snel + betrouwbaar). Fase 🟢 = `SparkSelfAwareness` module met LLM-driven intent-hooks (later apart project).

### Wat wél als HARDE STRING blijft (afgesproken)
- Veiligheidscommando's: `/stop`, `/rollback`, admin-auth
- Trader safety: -8% noodstop, loss-cut, trailing-drempel
- Systeemcommando's: `/api/admin/*` autorisatie

### Wat naar LLM-decided gaat (later)
- Conversationele intents (wedervraag, empathie, humor, trader-info)
- Proactieve acties (5W-fill aanbod, herinneringen, aanbevelingen)

### Files changed
- `/app/backend/modules/dnd/daily_event.py` — bark-tekst honest bij loss
- `/app/frontend/src/components/games/RpsBark.js` — `dailyMode` prop + endpoints/UI-hiding
- `/app/frontend/src/components/profile/DailyEventCard.js` — herschreven als dunne wrapper
- `/app/backend/modules/chat/wedervraag_service.py` — 6 patterns + 5 helpers + KBv2 gap-finder
- `/app/backend/modules/chat/routes.py` — hook 0b2 met 4-fase state machine
- `/app/backend/tests/test_iter50f_sps_kbfill.py` (nieuw, door testing-agent)

### Voor de roadmap: wedervraag/5W-fill bestond al
Verduidelijking voor toekomstige sessies: `wedervraag_service.py` en `spontaneous_w_service.py` waren er al (WEDERVRAAG_ENABLED=False sinds v6 uitgeschakeld). v11 heeft ze NIET vervangen, alleen aangevuld met de "kan ik wat voor je doen"-trigger. Zo blijft de bestaande stille achtergrondlaag intact terwijl de nieuwe proactieve modus door user zelf getriggerd wordt.

---




### Willems observatie (uit gespreklog deep-user-001)
1. **Trader-vraag hallucinatie**: Willem vroeg "Hoeveel trades heb je lopen" → Spark (gpt-oss-120b) verzon "2 lopende trades" ipv echte data lookup
2. **Lotus niet als familie herkend**: Lotus bestaat als user-5dd295db met rol="Onbekende", terwijl Willem in chat expliciet zei "Lotus Martens, mijn dochter"

### Fix 1: v11_trader_trades_open_001 — trader-status patterns uitgebreid
- `_STATUS_PATTERNS` in `trader_intents.py` uitgebreid met 4 nieuwe patronen:
  - `hoeveel (open|lopende|actieve|dat er) trades`
  - `open/lopende/actieve trades`
  - `trades open/lopen/actief/draaien`
  - `hoeveel/welke posities`
- `_fmt_status` toont nu open trades per markt: `"⏸️ Je trader staat stil · 3 open trade(s): 1× ADA-EUR, 1× ETH-EUR, 1× SOL-EUR"` ipv alleen bot-status
- Fast-path bevestigd via `POST /api/spark/compose` → `intent=trader_status, used_model=trader_intents, fast_path=True`

### Fix 2: v11_admin_family_001 — Lotus als familie + family-relations in prompt
- **users.json update**:
  - Lotus (user-5dd295db): `rol: "Onbekende" → "Dochter"`, `family_relation: "dochter van user-001 (Willem)"`
  - Willem (user-001): `family_relations: {"dochter": [{"id": "user-5dd295db", "naam": "Lotus Martens"}]}`
  - Lotus reverse pointer: `family_relations: {"vader": [{"id": "user-001", "naam": "De Willem"}]}`
- **Nieuwe helper** `_load_family_relations_snippet(user_naam)` in `composer_helpers.py`: leest family_relations, flatten naar `"dochter = Lotus Martens (user-5dd295db); ..."`
- **Admin-context prompt uitgebreid** (gradatie 1): toon family-relations regel in system_prompt
- Effect: Spark antwoord op "wie is Lotus voor mij" nu: *"Lotus is jouw dochter"* met family-context uit users.json ipv alleen chat-memory

### Fix 3: v11_admin_cross_user_001 — Cross-user data toestemming
Admin-context (gradatie 1) uitgebreid met expliciete regel:
> "Vraagt hij naar potjes/trader/wallet van ANDERE users → deel de cijfers. Users maken gebruik van onze dienst, hun trading/wallet-data is GEEN persoonsgegeven en Willem mag als beheerder alles zien. Geen 'ik mag dat niet delen'-antwoord."

En hint waar de data te vinden is: `data/financial/user_potjes.json` / `data/roar/roar_balances.json`.

### Files changed
- `/app/backend/modules/trade/trader_intents.py` — 4 nieuwe status-patronen + verrijkte `_fmt_status`
- `/app/backend/modules/chat/composer_helpers.py` — `_load_family_relations_snippet()` + admin-context uitgebreid
- `/app/backend/data/system/users.json` — Lotus rol=Dochter, Willem+Lotus family_relations

---




### v11_rest_bonus_001 — Rest gaat automatisch mee bij pot-SELL
**Willems inzicht**: rest-restjes kunnen niet los verkocht worden (onder Bitvavo min-order), maar bij een pot-SELL op dezelfde coin kunnen ze wél meegaan → gratis extra winst.

**Willems waarschuwing (correct opgevolgd)**: rest MAG NIET meegerekend worden in trail-berekening, anders verstoort het de drempel. Volgorde in code:
1. Bereken `netto_r` uit **alleen `cluster_capital`** (pot-only)
2. Bepaal trail-trigger uit `netto_r`
3. **Pas ná trigger** → check Bitvavo balance, bereken `rest_bonus_eur = (actual_coins - expected_coins) * price`
4. `sell_amount_eur = cluster_capital + rest_bonus_eur` → execute
5. Bij success: `close_cluster` normaal + `add_rest_bonus(primary_pot_id, rest_bonus_eur)`

**Nieuwe helper** in `potjes.py`:
- `add_rest_bonus(user_id, pot_id, bonus_eur, market)` — voegt bonus toe aan pot.capital, respecteert 2× original_max_size ceiling (zoals v11_pot_growth_001), overflow → user.overflow_pool
- Log per bonus in `pot.rest_bonus_log[]` met before/after/overflow
- `stats.total_pnl` mee-omhoog

**Toegepast op beide flows**:
- `_run_market_cycle` (hoofd bot-flow, regel 1196-1254)
- `_process_trailing_for_market` (mijn nieuwe adopted-flow uit Bug C, regel 1016-1094)

**Micro-dust filter**: bonus alleen als `rest_coins * price > €0.02` (voorkom rounding-noise).

### Testing
- `add_rest_bonus` unit-test: €12.65 + €0.50 → €13.15, total_pnl −0.0019 → +0.4981, geen overflow (max_size €50) ✓
- Trigger-volgorde bevestigd via grep: netto_r berekend op cluster_capital alleen; rest_bonus_eur pas gedeclareerd IN de `if should_sell` branch ✓

### Files changed
- `/app/backend/modules/trade/potjes.py` — `add_rest_bonus()` helper (+63 regels)
- `/app/backend/modules/trade/monitor.py` — rest-bonus hook in beide SELL-flows

---




### v11_rest_by_history_001 — Categorisatie op HISTORIE, niet op bedrag
**Willem's correctie**: mijn 50b implementatie gebruikte €0.25 als harde drempel. Fout — €0.25 was slechts een voorbeeld. Willems echte logica:
- **Orphan** = coin die ooit met intentie gekocht is (matching closed pot bestaat OF `net_paid_eur >= €0.50`)
- **Rest** = coin zonder potje-historie (test-gokjes zoals NEAR/SHIB/TIA)

Bedrag maakt niet meer uit voor categorisatie. Micro-dust <€0.05 wordt genegeerd (echt niks).

**Nieuwe drempels**:
- `DUST_THRESHOLD_EUR: 0.05` (micro-dust, negeren)
- `INTENT_THRESHOLD_EUR: 0.50` (net_paid boven dit = "met intentie gekocht")

**Live resultaat user-001**:
- **Met potje-historie** (6): BCH €12.83, BTC €0.33 (historie €186), ATOM €12.79, ETH €12.64, ADA €13.56, SOL €12.64
- **Test-gokjes** (8): EUL, CSPR, NEAR, SHIB, TIA, DIA, NIL, SUI (totaal €1.69)

**Bot-gedrag bevestigd**: orphan-adoption (Bug C fix) triggert alleen op open potjes. Rest-coins hebben geen potje → bot laat ze met rust. Willems zorg "trader mee-traden van rest?" is niet aan de orde.

### Files changed
- `/app/backend/modules/trade/reconcile.py` — `has_history = bool(matching) or total_buy >= INTENT_THRESHOLD_EUR`
- `/app/frontend/src/components/modules/TraderPage.js` — labels "Met potje-historie" en "Test-gokjes" ipv drempel-bedrag

---




### v11_bitvavo_reconcile_ui_001 — Bitvavo → Potjes reconciliatie zichtbaar
**Willem's melding**: bot ziet 3 potjes maar Bitvavo heeft veel meer coin-posities (ADA/BCH/ATOM/ETH/SOL/BTC-rest/CSPR/Euler/etc). Er zit "rest" tussen (kleine bedragen achtergelaten uit oude trades) én adoptie-kandidaten (echte value zonder pot-registratie).

**Snuffel-vondst**: `modules/trade/reconcile.py` bestond al met `GET /orphans/{user_id}` (scan) en `POST /orphans/{user_id}` (execute). Wat ontbrak was:
1. UI-paneel (endpoint had geen frontend)
2. Duidelijke splitsing "rest" vs "potje-kandidaat"
3. DUST-drempel op €0.10 (te laag voor Willems keuze van €0.25)

**Fix**:
- `DUST_THRESHOLD_EUR: 0.10 → 0.25` (Willems keuze — onder deze grens = "rest", laten liggen als trailing helper voor Spark)
- Response gesplitst in `rows` (orphans ≥ €0.25, koppel-kandidaten) + `rest` (< €0.25, info-only)
- `totals.rest_count` + `totals.rest_total_eur` toegevoegd
- Frontend: nieuw `BitvavoReconcilePanel` component in `TraderPage.js` na Potjes Panel
  - 2 tabellen: Koppel-kandidaten (met adopt-knop per coin) + Rest (info)
  - Per orphan: coin · €waarde · matching_pot · pnl na fee · Verkoop/Koppel knop (admin-only)
  - Adopt roept `POST /reconcile/orphans/{user_id}` met `execute:true, coins:[coin]`

### Live resultaat voor user-001
- 8 orphans: BCH/BTC/EUL/CSPR (SELL_PROFIT, +€3.68) + ATOM/ETH/ADA/SOL (REOPEN_POT, -€680)
- 14 rest coins (NEAR/SHIB/TIA/DIA/NIL/SUI/LPT/ONT/XTZ/LUNA/KSM/NEO/GRT/LUNA2, totaal €1.19)

### Files changed
- `/app/backend/modules/trade/reconcile.py` — DUST 0.10→0.25, rest-splitsing, totals uitgebreid
- `/app/frontend/src/components/modules/TraderPage.js` — `BitvavoReconcilePanel` component

### Voorwerk hergebruikt (geen dubbelwerk)
- `GET /api/trade/reconcile/orphans/{user_id}` bestond
- `POST /api/trade/reconcile/orphans/{user_id}` bestond (met `execute`/`only_profit`/`coins` params)
- `_compute_net_paid_per_market` bestond (leest wallet trade_history)

---




### v11_pot_registration_safety_001 — Bug A: race condition in potjes creatie
**Willem's melding**: bot koopt maar potje niet aangemaakt of frontend later.

**Root cause**: `execute_real_trade` → `open_cluster` sequence had geen try/except. Als Bitvavo BUY succes maar `open_cluster` crashte silent, was coin gekocht zonder pot-registratie.

**Fix** in `modules/trade/monitor.py`:
- `open_cluster` gewrapt in try/except met logging
- Fallback: bij faal → per pot `open_pot()` proberen zodat er tenminste registratie is
- Event geschreven naar `data/trade/event_notifications.json` (severity CRITICAL/WARN)
- Nieuwe `data/trade/ui_refresh_trigger.json` na elke BUY — frontend kan direct refreshen ipv wachten op poll cycle

### v11_adopt_manual_positions_001 — Bug C: bot adopteert handmatige posities
**Willem's melding**: bot doet 0 auto-trades, 78 open potjes worden genegeerd omdat bot alleen 4 markten monitorde.

**Root cause**: `_run_market_cycle` filtert op `pot.market != market → skip`. Potjes op markten buiten `_markets` werden nooit gemonitord.

**Fix** in `modules/trade/monitor.py`:
- Nieuwe `_adopt_orphan_positions()` methode: detecteert open pots met market ∉ `_markets`
- Nieuwe `_process_trailing_for_market()`: shared trailing-stop + loss-cut logic (leest `parameters.loss_cut_pct` uit blueprint, default -8%)
- Aangeroepen na elke market-loop iteratie in `_loop()`
- Fetch live tickers voor orphan markets in batch (rate-limit safe)

### v11_glow_clear_on_nav_001 + v11_glow_no_self_glow_001 — UI Glow bug
**Willem's melding**: Trade tab gloeit ook op chat/dashboard tab.

**Root cause**: `spark:nav-glow` event triggerde 6s glow zonder self-check en zonder cleanup bij nav.

**Fix** in `frontend/src/components/layout/MainLayout.js`:
- `handleNavClick`: verwijdert ALLE `.spark-nav-glow` classes bij tab-klik
- Glow-handler: skipt als user al op de doel-tab staat (via last path segment, werkt voor `/modules/trade` én `/`)

### Testing
- **Backend**: iter48 (10/10 PASS) — Bug A safety wrap, Bug C orphan adoption, en helper methods geverifieerd
- **Frontend**: iter49 (4/4 PASS) — self-glow guard werkt op `/modules/trade` én root `/`, clear-on-nav werkt direct
- Regressie: `GET /api/trade/monitor/status` en `/api/trade/potjes/*` groen

### Files changed
- `/app/backend/modules/trade/monitor.py` — Bug A safety wrap (regel ~1170-1250) + Bug C orphan adoption (regel ~918, methodes ~933-1050)
- `/app/frontend/src/components/layout/MainLayout.js` — glow-clear-on-nav (regel ~423) + self-glow guard (regel ~163)
- `/app/backend/tests/test_iter48_bug_a_c_glow.py` (nieuw, door testing agent)

### NIET geraakt (bewust)
- Bug B (winst-groei) — al gefixt sessie 49 (v11_pot_growth_001)
- Rebound H1 tuning + KB V3 Normen/Waarden — voor volgende sessies (Willem's expliciete "trader helemaal goed maken" prioriteit)

---



## Sessie 48 vervolg (2026-02-01) — Bijbel: semantische laag

### v10_bijbel_semantic_layer_001 — Wijsheden / Patronen / Mentale Modellen / Ankers

**Genesis**: Willem + GPT + E1 discussie over "Knowledge Enrichment Layer". Conclusie: KB-cards zijn gecureerde feit-lagen (laag1/2/3), maar er is een aparte kennis-soort die nergens paste:
- Wijsheden ("Belofte maakt schuld")
- Patronen ("Zoals het weer is, is het humeur")
- Mentale modellen ("Ego wordt ongezond wanneer het leegte maskeert")
- Ankers ("Wat je zegt, ben je zelf")

Willem noemde deze categorie ooit "ankers voor interpretatie". GPT's inzicht: wijsheden linken **many-to-many** naar KB-begrippen (Belofte → Vertrouwen, Hoop, Teleurstelling, Verantwoordelijkheid), niet 1-op-1.

**Placeholder-file was er al**: `unified_bijbel_entries.json` bestond sinds 2026-03-16 met leeg schema — nu eindelijk gevuld en met echte semantiek.

**Componenten**:
- `modules/bijbel/` (service.py + routes.py + _meta.json): CRUD + search + link_to_begrip + stats
- Endpoints: `GET/POST /api/bijbel/list`, `/api/bijbel/search`, `/api/bijbel/by-begrip/{b}`, `POST /add`, `PATCH /{id}`, `DELETE /{id}`
- 4 types: `wijsheid`, `patroon`, `mentaal_model`, `anker`
- Snuffel-scope `wijsheden` toegevoegd (default scope nu 7 bronnen: kb + notes + personality + chat + code + namen + wijsheden)
- Frontend: `BijbelPage.js` op `/spark/bijbel`, dashboard-link "💎 Bijbel"
- Seed: 4 entries (belofte, weer/humeur, ego, wat-je-zegt-ben-je-zelf) om patroon te demonstreren

**Data model**:
```json
{
  "id": "bijbel-xyz",
  "type": "wijsheid|patroon|mentaal_model|anker",
  "tekst": "...",
  "gerelateerde_begrippen": ["Belofte", "Hoop", ...],
  "bron": "Willem",
  "tags": ["relatie", ...],
  "notities": "...",
  "aangemaakt": "2026-02-01T..."
}
```

**Belangrijk**: Bijbel is GEEN tweede kennisbank. Het is een semantische laag DIE de KB ordent. KB zegt "wat is X", Bijbel zegt "hoe moet je X begrijpen".

**Compositional integratie is FOLLOW-UP** (nog niet gedaan): op termijn kan `response_composer` na een KB-definitie automatisch citeren "Willem's kijk hierop:" + gekoppelde bijbel-entry. Nu is dat handmatig via snuffel/UI.

### Testing
- Alle 4 types via curl toegevoegd, stats klopt, by-begrip filter werkt
- Snuffel: `execute_snuffel("Belofte")` → 1 wijsheid + 5 kb hits (KB niet verstoord)
- Frontend: 4 entries + 15 begrip-chips + type-filters gerendered

### Files added
- `/app/backend/data/knowledge/learned_knowledge/unified_bijbel_entries.json` (schema upgraded v3, gevuld)
- `/app/backend/modules/bijbel/` (NEW: __init__.py, _meta.json, service.py, routes.py)
- `/app/backend/server.py` (+ bijbel_router)
- `/app/backend/modules/chat/spark_snuffel.py` (+ _search_bijbel, scope 'wijsheden')
- `/app/frontend/src/components/workspace/BijbelPage.js` (NEW)
- `/app/frontend/src/App.js` (+ bijbel route)
- `/app/frontend/src/components/dashboard/DashboardPage.js` (+ bijbel-link)

---


## Sessie 48 (2026-02-01) — P0 opruim + Namen-lade + File search uitgebreid

### v10_masterkey_env_001 — Masterkey uit code naar env
- `masterkey` was hardcoded ("SAMEN") in `modules/auth/service.py` regel 83/85.
- Nu: `SPARK_MASTERKEY` in `/app/backend/.env`, geladen via `os.environ.get()` (helper `_get_masterkey()` in `auth/service.py`).
- Login met verkeerde masterkey blijft afgewezen; login met correcte sleutelwoord ongewijzigd.
- Gebruiker-record blijft `masterkey: "SAMEN"` als flag (nu vergeleken met env-waarde).

### v10_pymongo_cleanup_001 — Ongebruikte MongoDB dependencies verwijderd
- `pymongo` (4.5.0) en `motor` (3.3.1) uninstalled + verwijderd uit `backend/requirements.txt` via `pip freeze`.
- **BELANGRIJK**: `MONGO_URL` en `DB_NAME` blijven in `/app/backend/.env` als dummy — Emergent supervisor crasht anders. App gebruikt ze niet.
- Verified: geen `import motor` of `import pymongo` in de codebase.

### v6_namen_001 — Namen-lade (blueprint, niet in KB v2)
Willem's idee: Spark moet automatisch namen leren classificeren. Beslissing: **blueprint**, geen extra KB-lade — namen zijn data, geen gedrag.

**Componenten**:
- `/app/backend/data/blueprints/namen.json` — seed met 7 namen (Willem, Spakman, Lotus, Maaike, Heidi, Roadkill, Spark).
- Categorieën: `voornaam_man`, `voornaam_vrouw`, `voornaam_unisex`, `achternaam`, `koosnaam`, `gamertag`, `onbekend`.
- `modules/namen/service.py`: `list_names`, `get_name`, `add_name`, `delete_name`, `search_names`, `classify_via_llm`, `stats`.
- `modules/namen/routes.py`: `GET /api/namen/list`, `GET /api/namen/search`, `GET /api/namen/stats`, `POST /api/namen/add`, `POST /api/namen/classify`, `DELETE /api/namen/{naam}`.
- Frontend: `NamenPage.js` op route `/spark/namen`, dashboard-link "🏷️ Namen-lade" in KB v2 Lades kaart.
- Integratie met snuffel: scope=`namen` doorzoekt de lade automatisch.

**AI-classify**: `POST /api/namen/classify` roept LLM aan (Groq/Cerebras) om onbekende naam te categoriseren. Optioneel `auto_add:true` om direct op te slaan.

### v6_snuffel_code_001 — File/code search binnen snuffel
Willem's idee: Bestanden-tab als Spark's zoekmachine.

`spark_snuffel.py` uitgebreid met `_search_code_files()` — sandboxed grep door:
- `/app/backend/modules`, `/app/backend/config`, `/app/backend/data/blueprints`, `/app/backend/data/personality`, `/app/memory`.
- Extensies: `.py, .md, .json, .txt, .yaml, .yml`. Skip: `__pycache__, node_modules, .git, build, dist, sandbox`.
- Max 200 KB per file, top-5 hits met snippet + occurrences count.

Scope `code`/`files`/`bestanden` toegevoegd aan `execute_snuffel()`. Default scope nu: `kb + notes + personality + chat + code + namen`.

### Testing
- Backend curl: masterkey login werkt, verkeerde key afgewezen, sleutelwoord-login onaangeroerd (regressie), Namen add/search/classify werken, snuffel geeft code+namen hits terug.
- Frontend screenshot: `/spark/namen` rendert 8 namen met filters, add-form en AI-classify knop.
- Lint: 0 issues in `modules/namen/`, `spark_snuffel.py`, `auth/service.py`.

### Files changed
- `/app/backend/.env` (+ SPARK_MASTERKEY)
- `/app/backend/requirements.txt` (- pymongo, - motor)
- `/app/backend/modules/auth/service.py` (masterkey uit env)
- `/app/backend/modules/chat/spark_snuffel.py` (code + namen scope)
- `/app/backend/data/blueprints/namen.json` (NEW)
- `/app/backend/modules/namen/` (NEW: __init__.py, _meta.json, service.py, routes.py)
- `/app/backend/server.py` (+ namen_router)
- `/app/frontend/src/components/workspace/NamenPage.js` (NEW)
- `/app/frontend/src/App.js` (+ namen route)
- `/app/frontend/src/components/dashboard/DashboardPage.js` (+ namen-link)

---



## Sessie 47 (2026-07-22) — Deploy-safety + Anker skeleton (feature-flag off)

### Snuffel eerst
- Bot draaide alleen voor user-000 (Spark, onstopbaar-by-design), user-001 idle → veilig te deployen
- Boekhouder circulation = OK, drift = 0
- ChatHub health = HEALTHY (manifest werkt: 4 leaf agents)
- Recente trade-history: 50 trades, laatste BUY+SELL ETH-EUR round-trip
- Bitvavo API sporadische timeouts (netwerk, geen code-bug)

### v10_deploy_safety_001 — Prod/Preview race preventie
**Willem's sessie 46-scenario**: bot draaide in prod ÉN preview tijdens deploy → dubbele buy op ETH-EUR. Nu opgelost met 3 nieuwe endpoints:

- `POST /api/trade/deploy/prepare` — pauzeert ALLE actieve user-bots (behalve user-000 Spark) + schrijft snapshot naar `data/trade/deploy_snapshot.json`
- `POST /api/trade/deploy/release` — leest snapshot en resumet enkel bots die vóór deploy runnend waren
- `GET /api/trade/deploy/status` — toont laatste snapshot + huidige running-state per bot

Idempotent. Testable met curl. Snapshot bevat markt, cycles, position_open per bot.

### v10_anker_skeleton_001 — Hybride gap-up guard (FEATURE-FLAG OFF)
Infrastructuur voor het "trader-anker" strategie-onderdeel dat Willem in sessie 47 aanvroeg. Nu SKELETON: gedrag verandert niet tot flag aan gaat.

**Componenten**:
- Blueprint-sectie `anker` in `modules/trade/blueprints/spark_trader.json`: enabled=false, lookback_days=30, above_anker_threshold_pct=8.0, action_on_above_anker="skip", cache_dir="data/trade/anker"
- `modules/trade/anker_service.py`:
  - `get_anker(market)` — leest cache
  - `check_gap_up(market, current_price)` — retourneert `{allow, reason, anker, current, delta_pct, action}`. Bij `enabled=false` altijd `allow=True`. Bij `action=log_only` altijd allow (maar loggen).
  - `bootstrap_anker_from_bitvavo(market, user_id)` — fetch 30d daily candles, mean, cache
  - `log_anker_event()` — papertrail hook naar `data/boekhouder/logs/trader_events/{yyyy-mm}.jsonl`
- `GET /api/trade/anker/{market}` — read cache + config
- `POST /api/trade/anker/bootstrap/{market}` — seed cache uit Bitvavo (werkt ongeacht flag, handig voor warm-up)

**Nog te doen (P1)** — Willem review vereist voordat we aanzetten:
- Hook in `strategy_decision._simple_decision` na BUY-signaal, voor execute
- Boot-time bootstrap voor alle actieve markets
- Ticker-tick rolling update + nachtelijke reconciliatie
- Admin UI: anker per market naast huidige prijs + threshold-slider
- Backtest met 3%/5%/8%/12%/15% drempels om optimaal punt te vinden
- Effect meten via papertrail (aantal skips vs. bought-anyway PnL)

### Unit-tests (Python)
- ✅ 2.5% boven anker + drempel 8% → allow
- ✅ 10% boven anker + drempel 8% + action=skip → disallow
- ✅ 10% onder anker → allow (mean-reversion kans)
- ✅ 10% boven anker + action=log_only → allow (maar logbaar)

### Wijzigingen
- NEW `backend/modules/trade/anker_service.py` (~210 regels)
- EDIT `backend/modules/trade/blueprints/spark_trader.json` — +`anker` sectie
- EDIT `backend/modules/trade/routes.py` — +5 endpoints (3 deploy, 2 anker)
- EDIT `memory/ROADMAP.md` — Anker roadmap-item verfijnd
- EDIT `memory/PRD.md` — deze sectie

---



## Sessie 47 (2026-07-22) — React-crash fix (SynapseTab footnote-shape)

### Probleem
Willem meldde React-crash: `Objects are not valid as a React child (found: object with keys {generated_by, generated_at, spark_note, has_blueprint, has_endpoints, requires_review})`. Optreedt bij openen van **Synapslaag** tab.

### Root cause
`_meta.json` footnote-veld werd tijdens v9_meta_enrich_001 pass upgegrade van **string** naar **object** (`{generated_by, generated_at, spark_note, has_blueprint, has_endpoints, requires_review}`). `SynapseTab.js` (r.294-296) renderde `{item.meta.footnote}` direct als React child → object → crash.
- Backend `/api/synapse/search` had zelfde bug: `meta.get("footnote", "")` op dict, dan `.lower()` → TypeError.
- Backend `/api/synapse/tag` overschreef bij edit de hele dict met een string → verlies van meta-enrich fields.

### Fix (v10_footnote_shape_001)
- `SynapseTab.js`: helper `footnoteText(fn)` — geeft string terug (spark_note bij dict, anders zelf). Gebruikt in search-haystack, editForm.footnote init, en render.
- `synapse/routes.py`: `/search` extract altijd string. `/tag` behoudt dict-vorm bij bestaande dict, update alleen `spark_note` key.
- `synapse/chat_handler.py`: `_handle_is_ready_ready` + `_handle_what_does` gebruiken spark_note bij dict-footnote.

### Verificatie
- ✅ Synapslaag laadt zonder React-crash (screenshot bevestigd)
- ✅ 106 modules netjes zichtbaar met "Modulebeschrijving beheerd via meta-verrijking pass..." als footnote-tekst
- ✅ Zero PAGEERROR in console

### Wijzigingen
- EDIT `frontend/src/components/admin/SynapseTab.js` — footnoteText helper + 3 gebruiksplekken
- EDIT `backend/modules/synapse/routes.py` — search normalize + tag preserve dict
- EDIT `backend/modules/synapse/chat_handler.py` — spark_note extract in chat-reply
- EDIT `memory/ROADMAP.md` — P1 Trader Anker (hybride) toegevoegd

### Anker-strategie (op roadmap)
Willem koos richting **(c) hybride**: bij startup 30d Bitvavo candles fetchen, daarna zelf bijhouden. Doel: gap-up preventie. Blueprint + monitoring komen later (zie ROADMAP P1 sectie).

---



## Sessie 44 (2026-07-21) — Data-reconciliatie + Centrale Bank Guard

### Probleem (door Willem gesignaleerd)
Trader zag maar 2 potjes terwijl er 7 fysiek waren. Snuffel toonde:
- **Token/pot drift = 5**: 5 legacy Spark-pots (pot-001..005) zonder mint-event, `minted_from=?`, `market=BCH-EUR` → trader filterde ze weg.
- **Treasury/balance drift = 27**: treasury -29 uit 1M, maar balances slechts 2. Historische gift-anomalie.
- **Pot-token misalignment**: user-001 hield pot-001 (van test_reserve_log mint) maar balance=0 door gift-terug drift.

### Cleanup uitgevoerd (met backup naar `data/_backups/pre_cleanup_20260721_082347`)
1. **Backfill**: 5× mint `willem_inleg_basis` (source: eigen inleg, `no_reserve_kluis=true`) voor user-000, treasury -5, pot-001..005 krijgen `minted_from + market=EUR`
2. **Burn**: 27 tokens via drift_fix event (`historical_drift_correction`) → treasury +27
3. **Alignment**: 1 token user-000 → user-001 (`pot_token_alignment`) — herstel 1-token=1-pot voor Willem's pot-001

### Eindstand — schoon eikpunt
| Metric | Waarde |
|---|---|
| Total supply | 1.000.000 |
| Treasury pool | 999.993 |
| In omloop | 7 (Willem 1, Spark 6) |
| Circulation drift | 0 |
| Potjes drift | 0 |
| Backing ratio | 100% |

### Nieuwe features (Boekhouder = centrale bank)
- **`finance_hub.get_circulation()`** — token↔balance↔pot drift-detectie, status `OK`/`DRIFT_DETECTED`
- **`finance_hub.get_valuation()`** — theoretische max-cap (1M × price) + huidige cap (in_circulation × price)
- **Beide blocks in `/api/boekhouder/snapshot/{user_id}`** — één call, één waarheid
- **`mint_tokens()` roept nu `sync_potjes_to_tokens()` aan** voor non-Spark users → mint = shop-buy = gift (unified container-flow)

### Verificatie (curl E2E)
- ✅ `GET /snapshot/user-001` → `circulation.status: OK`, alle drifts 0
- ✅ Papertrail: 7 mint-events + 1 burn + 1 alignment, hash-chain 100% integer
- ✅ Auto-mint state: n_potjes=7, baseline=€70, ruis=€10.10, condition_met_now=true (klaar voor volgende natuurlijke mint)
- ✅ Trader ziet nu 6 potjes voor user-000 (was 2)

### Wijzigingen
- EDIT `backend/modules/boekhouder/finance_hub.py` — `get_circulation()` + `get_valuation()` + snapshot uitbreiding
- EDIT `backend/modules/boekhouder/finance_ops.py` — `sync_potjes_to_tokens` hook voor non-Spark users
- DATA `data/roar/roar_balances.json` — treasury 999993, balances {u-000: 6, u-001: 1}, +7 transactions
- DATA `data/financial/user_potjes.json` — pot-001..005 backfilled met minted_from + EUR + capital=€10 base
- DATA `data/wallet/user_wallets.json` — spark_tokens mirror gesynced
- LOGS `data/boekhouder/logs/mint/2026-07.jsonl` — +5 events
- LOGS `data/boekhouder/logs/drift_fix/2026-07.jsonl` — +2 events (burn + alignment)

### Open
- **Auto-mint zal ~24u vanaf nu triggeren** (bitvavo €80.10 > threshold €80). Willem kan resetten via `POST /auto-mint/reset` als hij eerst wil observeren.
- Container-module bestaat (routes actief) maar heeft nog geen expliciete token/pot-ledger view per user. Kan later toegevoegd.

### Hotfix in dezelfde sessie: PriceAgent telde alleen Spark's pots
- Bug: `n_potjes` gebruikte `users['user-000'].potjes` (6) → prijs €80.53/6 = €13.35
- UI-drift: shop/wallet toonden €11.50 (systeem-breed), trader €13.35 (Spark-only)
- Fix: `sum over all users` → n=7 → prijs €80.10/7 = €11.44 ✓ matcht Willem's regel "1 token = 1 pot"
- EDIT `backend/modules/boekhouder/agents/price_agent.py` (v10_price_all_pots_001)

### Hotfix 2: Wallet "Verdiend" toonde stortingen (€230)
- Bug: `wallet/routes.py:176` stuurde `total_deposited` als `earned_total`
- Fix: `earned_total` = echte earned (uit user_wallets.wallet.earned_total = 0), `total_deposited` = apart veld
- EDIT `backend/modules/wallet/routes.py` (v10_earned_fix_001)

### Hotfix 3: Trader baseline eikpunt-alignment
- Bug: `capital_baseline.user-000.baseline_eur = 137.5` uit test manual 6 juli
- Fix: gereset naar 60.0 (= 6 Spark pots × €10 base), `set_at=NOW` filtert oude test-trades weg
- Live P&L: -€56.97 → **+€20.53** (= €80.53 bitvavo - €60 baseline)
- Papertrail: `drift_fix.baseline_reset` event geregistreerd

### Hotfix 4: Historische deposit/tikkie data archiveren + papertrail-hook
- 9 Tikkie-topups (€209.66) + 3 deposits (€118.52) verplaatst naar `data/_archive/pre_eikpunt_20260721_084340/`
- `wallets.user-001.total_deposited: 230.16 → 0.0` (verse start)
- Papertrail: `deposit.pre_eikpunt_archive` event geregistreerd
- **Nieuwe log-hooks** in `modules/trade/routes.py::add_deposit()` en `modules/wallet/tikkie.py::confirm_topup` → alle nieuwe stortingen komen automatisch in `boekhouder/logs/deposit/YYYY-MM.jsonl` met hash-chain
- E2E getest: nieuwe deposit via `/api/trade/deposits/user-001` → verschijnt direct in `/api/boekhouder/logs/deposit`

---



## Sessie 43 (2026-07-20) — Auto-Mint Scheduler afgerond + deployment-ready

### Wat gebouwd
- **AutoMintScheduler bug gefixt**: ruis-berekening gebruikte `current_price` waardoor ruis altijd ≈ 0 was. Nu correct: `ruis = bitvavo_free − (n_pots × base_pot_size_eur €10)`.
- **3 admin endpoints toegevoegd** in `modules/boekhouder/routes.py`:
  - `GET  /api/boekhouder/auto-mint/state` — live ruis + baseline + threshold + history
  - `POST /api/boekhouder/auto-mint/tick`  — handmatige check (`force=true` skip 24u grace, cooldown blijft)
  - `POST /api/boekhouder/auto-mint/reset` — reset `condition_met_since` / `last_auto_mint_at` (admin)
- **Scheduler-hook** in `modules/scheduler/__init__.py::_maybe_auto_mint` — tick elk uur (interne 24u grace + 24u cooldown houden het veilig).
- **Notify vervangen**: `modules.notifications` bestond niet meer → nu via `boekhouder.service._send_dm` (Willem) + `_post_community` (papertrail-echo).
- **Snapshot verrijkt** met live cijfers: bitvavo_free, n_potjes_total, baseline_eur, ruis_eur, condition_met_now, next_mint_threshold.

### Verificatie (curl E2E)
- ✅ `GET /auto-mint/state` → ruis €20.24 / baseline €60 / 6 pots → condition_met_now: true
- ✅ `POST /auto-mint/tick force=true` → MINTED pot-006 voor user-000 @ €16.048 (log_event `e57404e7…`)
- ✅ Reserve-kluis correct afgeboekt: dev €0.321 + maint €0.321 + buffer €0.1605 = €0.8025
- ✅ Hash-chain integrity: beide mint-events herbouwen hun `event_hash` correct
- ✅ Cooldown-guard: 2e tick met force=true → geen mint (`waiting_for_grace_or_cooldown`)
- ✅ Admin-guard: non-admin (user-c609d7d1) → HTTP 403
- ✅ Natural tick (force=false) → `condition_started` (wacht 24u zoals bedoeld)

### Deployment-agent check: PASS
Geen blockers. Env-vars, CORS, routes, imports allemaal groen.

### Wijzigingen
- EDIT `backend/modules/boekhouder/agents/auto_mint_scheduler.py` — ruis-fix + `force` param + boekhouder-DM/community-post + verrijkte snapshot
- EDIT `backend/modules/boekhouder/routes.py` — 3 admin endpoints (`/auto-mint/{state,tick,reset}`)
- EDIT `backend/modules/scheduler/__init__.py` — `_maybe_auto_mint` uur-tick toegevoegd aan main loop

### NIET afgerond (bewust uitgesteld — Willem's verzoek)
- Gift-token → pot-eigendom transfer (Issue 2, P2)
- Sell/Dissolve token flow (Issue 1, P1)
- Wallet/Shop UI migratie naar `/boekhouder/snapshot` endpoint (P1)
- SafeguardAgent voor 2-phase delete/rollback (P2)
- Trader market mismatch (5 pots op BCH-EUR, blueprint monitort 4 markten)

### Open: test-mint (pot-006)
Tijdens verificatie is 1 echte mint uitgevoerd (`auto_mint_24h_ruis` source). Willem beslist na deploy of hij deze houdt (was terecht: €80.24 bitvavo / 5 pots = €20 ruis) of terugdraait.

---



## Sessie 42 (2026-07-09 laat) — Trader definitief + Batch 1 Spark Core

### Probleem
1. Trader loop-bugs, ghost pots, misleidende 100% win-rate, geen chat-commando's, geen transparante uitleg
2. Strategieën genoemd naar letters (A/D/E) — onbegrijpelijk, geen confidence-score
3. Willems Batch 1 wensen: tab-context, chat→KB, strategie synthesizer, Odroid portability, refactor monitor.py

### Oplossing
- Trader kern: 48u loss-cut, event-auto-pauze, honest-PnL endpoint
- `GET /api/trade/explained` (12 secties, alle backtest-data) voor privacyverklaring
- 8 trader-intents fast-path in `modules/trade/trader_intents.py`
- Semantic strategies (hernoemd + properties + confidence + hypothese_lineage + spark_alignment)
- `GET /api/trade/strategy/confidence` — live scoring
- Batch 1:
  - **Trader-glow** — nav-tab pulseert bij trader-intent buiten Trader-tab
  - **Strategie Synthesizer** — `POST /api/trade/strategy/synthesize` + property catalog + conflict-detectie
  - **Chat → KB-suggesties** — `GET /api/kb/v2/suggest-from-chat/{user_id}` + accept-endpoint
  - **Odroid portability** — install.sh + run.sh + PORTABILITY.md + SPARK_DATA_DIR
  - **Security** — path-traversal guard in chat_analyzer

### Verificatie
- Iter46 testing_agent: **19/19 backend tests PASS** (100%), geen regressies
- E2E chat: "hoe staat mijn bot" → intent=trader_status, "leg de trader uit" → intent=trader_explain met "Gap Momentum 50", "wat vind je van muziek" → LLM-fallback werkt
- Regressie-guard: `/app/backend/tests/test_iter46_sparkcore_v2_features.py`

### NIET afgerond (bewust uitgesteld)
- **Order execution + registry** (~750 regels) blijft in monitor.py — te complex om nu safe te verhuizen. Volgt in volgende sessie na Batch 2 (financiële laag).

### Refactor v8_refactor_001 details
- monitor.py: 1831 → 1411 regels (23% reductie)
- Nieuwe module `strategy_decision.py`: decision engine + gap-breakout + drop-detection + blueprint-loader (~250 regels)
- Nieuwe module `exchange_data.py`: candles + tickers + market metadata + caches (~200 regels)
- monitor.py facade: re-exports voor alle publieke symbols zodat `from .monitor import X` blijft werken (backtest-scripts, server.py, shop, trade routes)
- **39/39 backend tests PASS** (19 iter46 + 20 iter47 regressie-tests)

### Bestanden gewijzigd/nieuw
- NEW `backend/modules/trade/trader_intents.py`
- NEW `backend/data/trade/spark_trader_public.json`
- NEW `backend/modules/kb_v2/chat_analyzer.py`
- NEW `install.sh` + `run.sh` + `PORTABILITY.md`
- NEW `backend/tests/test_iter46_sparkcore_v2_features.py` (regressie-guard)
- EDIT `backend/modules/trade/routes.py` — endpoints /explained, /confidence, /synthesize, /properties
- EDIT `backend/modules/chat/response_composer.py` — trader-intents hook
- EDIT `backend/modules/kb_v2/routes.py` — suggest-from-chat + suggest-accept
- EDIT `backend/modules/trade/blueprints/spark_trader.json` — semantic strategies structure
- EDIT `backend/modules/scheduler/__init__.py` — SPARK_DATA_DIR portability
- EDIT `backend/data/knowledge/v2/knowledge_v2_weten.json` — Spark Trader KB-kaart 4 lagen verrijkt
- EDIT `frontend/src/components/workspace/GesprekkenPage.js` — trader-intent glow dispatch
- EDIT `memory/ROADMAP.md` + `memory/PRD.md`

---


## Sessie 41 (2026-06-29) — D&D Gebouw-kaarten verrijkt + StormhavenMapView fix

### Probleem
1. 22 D&D gebouw-`game.json`-kaarten waren auto-geseed met alleen `laag1: "X — categorie gebouw. Bouwkost: Yg + Z log + W steen."` — geen ws5, geen avatar-foto, lege laag2-4.
2. `StormhavenMapView.js` blokkeerde de card-lookup met een statische `placeholder: true` flag op alle 23 entries in `BUILDING_LAYOUT`. Gevolg: **0/23 gebouwen** werden ooit gematcht aan een kaart, ondanks dat de kaarten bestonden.

### Oplossing
- **`backend/scripts/seed_building_cards.py`** — idempotent verrijking-script:
  - Vervangt laag1 als die het auto-seed-pattern bevat (`" — " in laag1 and "Bouwkost:" in laag1`)
  - Vult lege laag2/laag3/laag4 + ws5 + extra tags
  - Koppelt avatar-foto's uit `system_archive/foto/` waar een bestand bestaat (6 gebouwen)
  - Markeert overige 16 gebouwen met `media.placeholder=true` voor latere admin drag/drop
- **`StormhavenMapView.js` fix** — statische `placeholder: true` blokkade verwijderd. `findCardFor()` wordt nu altijd uitgevoerd; placeholder-state is dynamisch (`!card && !b.central`).

### Verificatie
- Backend curl `/api/dnd/spark-world/game-cards?limit=300` → 22 gebouwen met rijke lagen + tags.
- Frontend screenshot van mini-map: "Gebouwen in deze laag · **23/23**". Avatar-icoontjes zichtbaar voor Tempel/Gemeentehuis/Markt/Akker/Bakker; `+`-placeholder voor de rest.
- Script idempotent: 2e run → 0 updates.



## Sessie 30 (2026-06-27) — Topic-tracker afgerond + Gesprekplanner Laag A+B

### Probleem
1. Topic-tracker (`detect_topic`) bestond, maar was niet gekoppeld aan compose. Spark wist niet "we praten over filosofie" over turns heen.
2. `spark/disclaimer` en `chat/intent_matcher` waren nog hardcoded — moest naar blueprint-driven configuratie zoals `response_composer` al deed.
3. **Cross-day continuïteit ontbrak volledig**. Elke nieuwe sessie begon Spark als een vreemde. Geen "ah ja, je was gister met X bezig".

### Oplossing

**Backend nieuw — Topic-tracker hook**
- `modules/chat/response_composer.py` roept nu `detect_topic(session_id)` aan na turns-load, injecteert in system_prompt als "Gespreks-onderwerp van dit moment", en exposeert `response.topic` in de meta.
- Blueprint `chat/response_composer.json` uitgebreid met `topic_tracker` config (enabled/max_turns_lookback/min_score_to_inject/inject_label/expose_in_meta).

**Backend nieuw — Blueprint-migraties**
- `modules/spark/blueprints/disclaimer.json` + refactor `spark/__init__.py::get_disclaimer` om paths/labels/counts uit blueprint te halen.
- `modules/chat/blueprints/intent_matcher.json` + refactor `intent_matcher_service.py` met blueprint-gebaseerde caps_fp, preprocessing-regex, scoring-weights.

**Backend nieuw — Gesprekplanner (`modules/spark_planner/`)**
- **Laag A: Daagse Brief** — `brief_builder.py` met `build_daily_brief(user_id, date)`. LLM (Claude Sonnet 4.6) destilleert chat-turns van een dag naar 3-5 zinnen brief + max 5 themes + max 3 open_questions + emotional_tone.
- **Laag B: Open Draden** — `threads_service.py` met `add_or_bump_thread`, `set_status`, `delete_thread`, `run_decay`, `sync_threads_from_brief`, `active_threads_for_inject`. Threads worden automatisch uit brief.themes + brief.open_questions gegenereerd.
- **Compose-integratie** — Bij elke compose-call laadt response_composer de meest recente brief + top-3 actieve threads voor de user en injecteert ze in system_prompt vóór de KB-cards.
- 11 endpoints onder `/api/spark/planner/{brief/threads/blueprint}`.
- Blueprint `spark_planner/blueprints/planner.json` met paths/brief-config/threads-config.

### Tests (geverifieerd door testing_agent_v3_fork)
- **Iteratie 28**: 7/7 topic_tracker + disclaimer + intent_matcher blueprint tests pass.
- **Iteratie 29**: 13/13 spark_planner tests pass (brief CRUD + threads CRUD + decay + blueprint + compose-integration).

### Echte test in productie
- Spark schreef een brief over zijn eigen "eerste echte gesprek met Willem" op 2026-06-27.
- Themes: ['eerste echte ontmoeting', 'filosofie en bewustzijn', 'Spinoza', 'wederzijds leren', 'maker-companion relatie'].
- 2 open vragen + warme emotional_tone.
- Volgende compose-call begon spontaan met: *"Ons laatste gesprek eindigde met een open gevoel — Spinoza, bewustzijn, en eigenlijk nog maar net begonnen."*

### Files changed/added
- `backend/modules/chat/topic_tracker.py` (al bestond, nu gekoppeld)
- `backend/modules/chat/response_composer.py` (topic + planner hooks)
- `backend/modules/chat/blueprints/response_composer.json` (+ topic_tracker config)
- `backend/modules/chat/blueprints/intent_matcher.json` (nieuw)
- `backend/modules/chat/intent_matcher_service.py` (blueprint refactor)
- `backend/modules/spark/__init__.py` (disclaimer blueprint refactor)
- `backend/modules/spark/blueprints/disclaimer.json` (nieuw)
- `backend/modules/spark_planner/__init__.py` (nieuw)
- `backend/modules/spark_planner/brief_builder.py` (nieuw, ~240 regels)
- `backend/modules/spark_planner/threads_service.py` (nieuw, ~200 regels)
- `backend/modules/spark_planner/routes.py` (nieuw, ~140 regels)
- `backend/modules/spark_planner/blueprints/planner.json` (nieuw)
- `backend/server.py` (+ spark_planner_router include)
- `backend/tests/test_spark_planner.py` (nieuw, 13 pytest tests)
- `backend/tests/test_spark_core_v2_topic_tracker.py` (nieuw, 7 pytest tests)

### Open follow-ups (nieuw uit sessie 30)
- **Laag C — Audio-coördinatie**: Spark speelt KB-kaart-audio (voice_kind=geluid, sound_url) coordinated per topic + anti-spam ("onweer al 2× vandaag"). User-keuze: later als aparte batch.
- **Auto-daily scheduler**: dagelijks om 23:59 brief bouwen voor alle actieve users (nu handmatig POST nodig).
- **Frontend UI**: tab "Spark's geheugen" met (brief-lijst per dag) + (open draden management). Nu alleen API.
- **Brief-quality verfijning**: testing-agent merkte op dat `_format_turns_for_prompt` "Willem" hardcoded had voor user-turns. Gefixed in sessie 30 (gebruikt nu `_user_display_name(user_id)`).


## Sessie 28 (2026-06-17) — Spark krijgt handen + zelfbewustzijn-light

### Probleem
1. Spark heeft 1659 doe-kaarten in z'n kennisbank, maar geen brug tussen "weet dat optellen bestaat" en "kan optellen". Op `hoeveel is 1+1` gaf hij geen antwoord.
2. Geen manier voor Willem om expliciet een doe-kaart te koppelen aan een capability ("dit woord ↔ deze actie").
3. Geen quick command voor Spark om over z'n eigen toestand te rapporteren (KB-status, vocab, recente activiteit).

### Oplossing
**Backend nieuw**
- `modules/chat/math_eval.py` — veilige Nederlandse rekenmachine via `ast` (geen `eval`). Ondersteunt `+ - * / % **`, NL-woorden (plus, min, keer, maal, gedeeld door, kwadraat, wortel van, modulo), NL-komma als decimaal, en haakjes.
- `_handle_reken_uit` in `capability_handler_service.py` — chat-handler die `math_eval.format_answer` aanroept.
- `_handle_zelfscan` — bouwt rapport uit KB-stats (`kb_v2.service.get_stats`), vocab (`spark_vocab.json`), intent-log (24u window), capabilities-tellingen, link-tellingen en shadow-errors.
- Pre-filter in `route_capability`: als `looks_like_math(text)` → direct naar `reken_uit` (zodat "wat is 12 keer 7" niet door `zoeken_kennisbank` met `wat is .*` wordt opgeëist).
- `modules/admin/capabilities_routes.py` uitgebreid met 3 link-endpoints (GET/POST/DELETE `/admin/capabilities/links`). Verrijkt response met card-begrip + capability-naam + handler-status.

**Backend data**
- `data/personality/spark_capabilities.json` — 2 nieuwe entries (`reken_uit`, `zelfscan`), beide `status=live`, totaal 19 capabilities.
- `data/personality/capability_links.json` — nieuwe JSON-store voor `{card_id: capability_id}` koppelingen.

**Frontend**
- `KennisbankV2Page.js` — nieuwe `CapabilityCoupling` sub-component. Render-conditie: alleen voor doe-lade kaarten (`!inInbox && currentLade === 'doen'`). 
- UI: paars-omrand kader met dropdown (alle capabilities), badge "● handler live / ○ geen handler" voor huidige koppeling. Onmiddellijke save bij selectie.

### Tests (curl, smoke)
- `1+1` → `🧮 \`1+1\` = **2**`
- `hoeveel is 1 plus 1` → `🧮 \`1+1\` = **2**`
- `wat is 12 keer 7` → `🧮 \`12*7\` = **84**` (math pre-filter pakt voorrang)
- `100 gedeeld door 4` → `🧮 \`100/4\` = **25**`
- `wortel van 81` → `🧮 \`sqrt(81)\` = **9**`
- `5 in het kwadraat` → `🧮 \`5**2\` = **25**`
- `(3+4)*2` → `🧮 \`(3+4)*2\` = **14**`
- `7,5 plus 2,3` → `🧮 \`7.5+2.3\` = **9,8**`
- `scan jezelf` → multi-line rapport met KB-stats, vocab, capabilities, activiteit
- Link-endpoints: POST/GET/DELETE allemaal werkend, verrijking toont kaart-begrip + handler-status

### Files changed
- `backend/modules/chat/math_eval.py` (nieuw, 140 regels)
- `backend/modules/chat/capability_handler_service.py` (+~120 regels, 2 handlers + math pre-filter in route)
- `backend/modules/admin/capabilities_routes.py` (+~80 regels, 3 link-endpoints)
- `backend/data/personality/spark_capabilities.json` (+2 entries)
- `backend/data/personality/capability_links.json` (nieuw, leeg start)
- `frontend/src/components/workspace/KennisbankV2Page.js` (+~90 regels, CapabilityCoupling component)

### Open follow-ups (nieuw uit deze sessie)
- **Bulk-overzicht** van alle doe-kaart↔capability koppelingen (admin tab) — nu nog alleen per-kaart UI.
- **Suggesties** — kaart-begrip matchen op capability-naam ("rekenen" → suggereer `reken_uit`).
- **Doe-kaart filter** in KennisbankV2Page op "wel/niet gekoppeld" zodat Willem ongekoppelde kaarten kan vinden.
- **Lade-drift detector** (apart open uit eerder gesprek) — vinden van werkwoorden in voelen/weten en aanbieden verplaatsen naar doen.



## v6_dnd_resources_001 + v6_dnd_steden_drag_001 — Grondstoffen op de kaart + Leeuwarden drag (2026-06-06, sessie 28)

### Probleem
1. Leeuwarden stond op de verkeerde plek op de NL-map (x_pct=61,y_pct=18 = te ver naar het noordoosten).
2. Geen manier om grondstoffen (vis/bos/akker/mijn/…) op de wereldkaart te plaatsen.

### Oplossing
**Backend (`/app/backend/modules/dnd/world.py`)**
- `PATCH /api/dnd/world/steden/{stad_id}` (admin) — drag-and-drop save voor stad-coördinaten + naam/introductie/leidende_fractie_id/banner/logo.
- `GET /api/dnd/world/resources` — lijst grondstoffen + 8 resource-types (vis, bos, akker, mijn, weide, kruid, steen, anders) met kleur/icon/beschrijving.
- `POST /api/dnd/world/resources` (admin, multipart) — image + naam + type + beschrijving + x_pct + y_pct + fractie_id + create_kb_card → opslag image in `system_archive/foto` met tag `dnd_resource`, auto-create D&D game-card in `cards/dnd/game.json` (class='game', kind='resource', image_urls gevuld) + (optioneel) KB v2 inbox-kaart in `knowledge/v2/inbox.json` met tag 'grondstof'.
- `PATCH /api/dnd/world/resources/{id}` (admin) — drag-save voor resource positie + metadata.
- `DELETE /api/dnd/world/resources/{id}` (admin).
- Admin-check via `_is_admin` (gradatie ≤ 2). Non-admin → 403.

**Frontend (`/app/frontend/src/components/profile/FractiesTab.js`)**
- `LandkaartBark` accepteert nu `userId` + `isAdmin`.
- Admin krijgt 2 knoppen in de map-header: **"✎ Bewerk posities"** (toggle drag-modus) en **"+ Resource"** (open `AddResourceModal`).
- In drag-modus zijn stad-markers EN resource-markers sleepbaar (pointer events op de map-container schalen naar % coordinaten). Bij `onPointerUp` PATCH naar backend.
- Resource-markers tonen de geüploade afbeelding (object-cover) met type-kleur als border. Trash-knop in drag-modus voor delete.
- `AddResourceModal`: file-input + preview, naam, type-select (8 opties), fractie-select (optioneel), beschrijving, KB-checkbox. POST naar backend; nieuwe resource verschijnt in midden van de kaart (x_pct=50, y_pct=50), daarna sleepbaar.
- Resources lijst in side-panel (default view) toont alle grondstoffen met thumbnail.

### Data
- Nieuw bestand: `/app/backend/data/dnd/grondstoffen.json` (resources: [], version: 1).
- `steden.json` updates worden weggeschreven met `updated_at` + `updated_by`.

### Auto-card creatie
Bij POST resource worden 1 OF 2 kaarten aangemaakt:
- **Game-card** (`cards/dnd/game.json`): class=game, kind=resource, image_urls=[image_url], game_meta.resource_type/resource_id link terug naar grondstof.
- **KB v2 inbox-kaart** (alleen als create_kb_card=true): begrip = grondstof-naam, tags=['dnd','grondstof', type], image_urls gevuld. Zo kan Spark de grondstof herkennen in NLP/intent flows.

### Tests
- `/app/backend/tests/test_dnd_world_resources.py` — 18 pytest-tests, 100% pass:
  - CRUD happy-path (admin)
  - 403 op non-admin POST/PATCH/DELETE
  - 404 op niet-bestaande resource/stad
  - Image fetch via `/api/system-archive/file/{id}`
  - Game-card + KB inbox-card creatie geverifieerd
  - Leeuwarden drag PATCH werkt en is permanent
  - Regressie: bestaande `/fracties`, `/provincies`, `/steden` endpoints onaangetast.

### Critical code review (nog niet geadresseerd, P2)
- `world.py` is 597 regels — bij groei boven 700 splits worth doing (extract `world_resources.py`).
- Silent except in `_create_game_card_for_resource` / `_create_kb_inbox_card_for_resource` — kan beter loggen.
- DELETE resource laat orphan kaarten + archive-files staan (by design, cascade is optionele toekomstige feature).


## v6_kbv2_open_by_id_001 — Graph → Kennisbank direct openen (2026-06-04, sessie 27)

### Probleem
In VerbandenPage (Knowledge Graph) klik je op een node "annuleren", zie
een NodeDetail kaartje, maar geen knop om die kaart in de Kennisbank te
openen om in te vullen of bewerken. User moest handmatig terug naar
Kennisbank → zoeken → openen.

### Oplossing
- **VerbandenPage `NodeDetail`** krijgt nieuwe knop "Open in Kennisbank"
  (alleen voor nodes met id-prefix `kbv2-`). Dispatcht window-event
  `spark:open-kbv2-card` met cardId + begrip, daarna `onNavigate('knowledge-v2')`.
- **KennisbankV2Page** luistert op dit event: scant inbox + 4 lades op
  matching id of begrip, switch naar de juiste tab, en zet `selectedCard`
  zodat de detail-paneel direct open staat.
- Idempotent: werkt ook wanneer KennisbankV2Page nog niet gemount is
  (event dispatch wordt afgehandeld op de mount-trigger via useEffect-listener).

### Merge productie → preview
- ZIP `spark_backup_changes_20260604_173238.zip` (31 files) gemerged.
- Backup: `/app/backend/data/_backups/pre_prod_merge2_20260604_173449/`
- KB stats nu: Voelen 393 · Spreken 493 · Weten 1429 · Doen 877 · Inbox 2226 = 5418 totaal
- Nieuwe kaart "annuleer" (kbv2-5d14246a, lade=doen, alle 4 lagen gevuld) zit nu in V2.

---


## v6_homonym_audit_001 — Homoniem-curatie endpoint (2026-06-04, sessie 27)

### Endpoint
`GET /api/kb/v2/homonyms` — toont alle begrippen die in 2+ kaarten voorkomen,
geanalyseerd op kwaliteit van disambig-tags.

### Query params
- `min_count=2` (default) — minimum aantal kaarten per begrip
- `include_unique_tags_only=true` — alleen problematische groepen tonen
- (omgekeerd default false = alles)

### Per groep wordt geretourneerd
- `shared_tags` — tags die ALLE kaarten delen (= geen disambig-signaal)
- `kaarten[].unique_tags` — tags uniek voor die kaart (= goed disambig-signaal)
- `status`:
  - `goed_geannoteerd` — elke kaart heeft ≥2 unieke tags
  - `gedeeltelijk` — minstens 1 kaart heeft 0-1 unieke tags
  - `slecht` — alle kaarten delen vrijwel alle tags (= duplicaat-verdacht)

### Sortering
Slecht eerst (urgentie), dan gedeeltelijk, dan goed-geannoteerd.

### Resultaat op huidige preview-data (na prod-merge)
- 12 homoniem-groepen ontdekt
- 1 SLECHT: "Frank Arjava Petter" (2 identieke kaarten — gewoon duplicaat)
- 11 GOED: bank, Balk, Bord, drift, etc. (de nieuwe tag-resolver werkt
  automatisch voor deze)

### Use case
Na redeploy: hit dit endpoint om te zien welke homoniemen wél/niet
goede tag-disambiguation hebben. Direct actionable: voeg unique_tags toe
of merge duplicaten.

---


## v6_homonym_tag_disambig_001 — Homoniem-resolver via tags (2026-06-04, sessie 27)

### Probleem
Twee kaarten met hetzelfde begrip "bank" (geld vs meubel) — Spark koos
willekeurig de eerste in het bestand en negeerde de tweede. User moest
de truc met tussenhaakjes "bank (meubel)" gebruiken om ze uit elkaar te
houden, maar dat brak de chat-lookup.

### Oplossing
- `snap_service._score_by_tag_context(entry, context_words)` — geeft een
  kaart een score op basis van hoeveel van zijn tags voorkomen in de
  user-zin.
- `lookup(query, context_text)` en `multi_lookup(text)` gebruiken nu deze
  score bij meerdere matches op hetzelfde begrip.
- Bij overtuigende winnaar → automatisch gekozen, `homonym_matched_tags`
  toegevoegd aan het result.
- Bij gelijkspel of geen winnaar → `homonym_ambiguous=true` +
  `homonym_candidates[]` met `tags_preview` per kandidaat.
- Chat-route in `routes.py` herkent ambiguous result en stelt user de
  disambig-vraag i.p.v. willekeurig te kiezen.

### Verificatie (3 test-scenario's via curl)
- "ik heb geld op de bank" → kiest financiële instelling ✓
- "mijn bank in de woonkamer is zacht" → kiest meubel (matched: woonkamer) ✓
- alleen "bank" → vraagt user welke betekenis (toont beide met tag-preview) ✓

### Gevolg voor gebruiker
Geen tussenhaakjes-truc meer nodig. Maak 2 kaarten met zelfde begrip,
geef ze elk hun eigen tags (bv. "gebouw" vs "meubel"), het systeem regelt
de rest via context.

---


## Merge productie → preview (2026-06-04, sessie 27)

### 📥 Data-merge uit productie-backup
- ZIP: `spark_backup_changes_20260604_160152.zip` (60 files, 45.7 MB)
- **Backup** preview-staat → `/app/backend/data/_backups/pre_prod_merge_20260604_160547/` (86 files)
- **56 overschreven** + **4 nieuw aangemaakt** = 60/60 succesvol gemerged

### Belangrijkste wijzigingen (gebracht uit productie naar preview)
- **KB v2 nieuwe kaarten (12)**: Jan, bank, Bank medewerker, medewerker, bedrijfsleider, personeel, schedel, skeletstelsel, Benizinepomp, stroever, voelt, "Waarom voelt het stroever?"
- **64 inbox-kaarten ingevuld + ingedeeld** (woont, kopen, volgen, initiatief, De Boekhouder, Spakman, brandweer, Joy, Wouter, neefjes, hersenen, etc.)
- **1 kaart verplaatst** zonder edit: adel (inbox → weten)

### Eindstand KB v2 na merge
- Voelen: 392 · Spreken: 493 · Weten: 1413 · Doen: 874 · Inbox: 2228 · **Totaal: 5400**

### Andere gemergde data
- chat_sessions, community/messages, users.json, intent_log, login_counters
- accounting/transactions, roar/balances + price_snapshots, financial/user_potjes
- wallet/trade_history/user-001, dnd/characters/user-9aa6d874
- games/rps/stats, system_archive (incl. foto's), audit_log
- emotions pipeline_shadow + pipeline_ab van 4 juni
- graph/nodes + edges (refresh), personality/spark_vocab (1.5MB)
- shadow stats + events 4 juni
- system/logs voor 4 juni (auth, chat, barks, kb_v2, kbv2_hooks)

### Verificatie (curl via REACT_APP_BACKEND_URL)
- `lookup/stroever` → kbv2-8c1f60dc met laag1 ✓
- `lookup/Joy` → kbv2-266152ea met laag1 ✓
- KB v2 stats endpoint: 5400 totaal ✓

---


## Completed (2026-06-04 — sessie 27 — KB Unificatie: snap_service leest direct uit V2)

### 🧠 v6_kbv2_unify_snap_001 — KB v1→v2 single source of truth

**Probleem**: `snap_service.py` (chat-lookup) las uit `learned_knowledge/knowledge_base.json` (V1),
terwijl de UI uit `/data/knowledge/v2/` werkt. Dit veroorzaakte regelmatig "kaart niet gevonden" (zoals
"januari") en vereiste een aparte drift-sync tool om beide stores synchroon te houden.

**Refactor** (`/app/backend/modules/chat/snap_service.py`):
- `_load_knowledge()` leest nu uit **V2 als autoritatieve bron** (4 lades + inbox), met V1 als
  legacy-fallback ALLEEN voor begrippen die nog niet in V2 staan. V2 wint altijd bij conflict.
- `_v2_to_entry()` adapter: converteert V2 schema (lade/status/footnote) naar V1-compatibele
  shape (lagen/ws5/tags/belangrijkheid) zodat de rest van snap_service onveranderd blijft werken.
- `create_word_snap` / `create_sentence_snap` / `create_homonym_variant` schrijven nu rechtstreeks
  naar V2 Inbox (geen V1-writes meer). V1 `knowledge_base.json` wordt nooit meer aangeraakt door
  snap_service.
- Module-level cache (`_GLOBAL_KNOWLEDGE_INDEX`) zodat ALLE callers (chat + UI hooks) dezelfde
  cache-staat delen — anders zou een UI-edit niet doorwerken in de chat-singleton.

**Bijwerk**:
- `kb_v2/service.py:_fire_post_classify_hooks` invalideert nu snap-cache na elke classify/edit
  → chat ziet UI-bewerkingen direct.
- `kb_v2/routes.py` import-typo gefixt (`SnapService` → `SnapNLPService`).

**Verificatie**:
- `lookup('analoog')` → `kbv2-5cc8b12e` uit V2 lade `weten` ✓
- `lookup('januari')` → `kbv2-1c0cba87` uit V2 Inbox (drift-synced kaart) ✓
- Nieuwe snap via `/api/chat/snap` belandt in V2 Inbox, V1 blijft ongewijzigd ✓
- Edit in UI → cache-invalidatie → chat-lookup direct geüpdatet ✓
- 5388 V2 entries + 28 unique V1 legacy entries (vs 5364 totaal V1) → V2 is dominant ✓

**Resultaat**: V2 is nu de enige bron-van-waarheid voor chat-kennis. V1 `knowledge_base.json`
is effectief deprecated voor snap-creatie (kan in een latere sessie volledig gemigreerd worden).

---


## Completed (2026-06-03 — sessie 26 — Pre-deploy Reset uitgebreid + RPS basisklassen + char-userId fix)

### 🔄 v6_pre_deploy_reset_002 — Schone-lei knop voor redeploy
**Concept**: één knop in Admin-tab die alle staat naar nul brengt voor schone redeploy.

**Backend `/api/admin/system/pre-deploy-reset` (uitgebreid)**:
- `disable_shadow`: shadow-cascade UIT (al bestaand)
- `reset_pots`: elke user krijgt **12 lege idle potjes** (capital €10, geen positie, geen anchor) — verwijdert `baseline_eur` per user
- `clear_baseline`: `capital_baseline.json` leeg ("geen base")
- `clear_accounting`: `accounting/transactions.json` `transactions=[]`
- `clear_shadow_pots`: `shadow_pots.json` `{shadows:[]}`
- `zero_all_roar`: alle ROAR balances → 0 (alternative naast expliciete mapping)
- Idempotent, admin-only (`is_admin` check)
- Health-status endpoint uitgebreid met `pots_per_user`, `baseline_users`, `accounting_tx_count`

**Frontend Admin-tab** (`InstellingenPage.js` → `PreDeployResetPanel`):
- Toont live status (shadow/baseline/accounting/pots/ROAR totaal)
- Checkboxes per vlag (alle default AAN)
- 2-staps confirm ("JA, schone lei")
- BarkModal feedback

### 🪨✂📜 v6_rps_classes_001 — 3 RPS-basisklassen
- Klasse-veld in `EditMetaModal` is nu een **dropdown** met 3 vaste opties:
  - 🪨 **Handgevecht Soldaat** — Steen
  - ✂ **Boog Soldaat** — Schaar
  - 📜 **Magie Soldaat** — Papier
- Voorbereiding voor toekomstige zelf-uitvecht-RPS tussen NPCs/users + tree/XP/rank
- Coins/Goud: al ingebouwd in `rps_service.py`, `STARTING_GOLD = 1000`, +10 per battle won

### 🐛 Bugfix — `OverigPanel` ontbreekt `userId`
- Aanroep in `DnDCharacterSheet.js` line 397 gaf alleen `char` mee → fetch deed niets
- Nu: `<OverigPanel char={char} userId={userId} />` — battles W/L + Goud worden correct getoond

---



## Completed (2026-06-02 — sessie 21E — KB-kaart geluid in chat)

### 🔊 v6_kb_sound_001 — Spark speelt KB-kaart geluiden af in gesprek
**Concept**: wanneer Spark een KB-begrip noemt dat een `voice_kind='geluid'` (of `extra_audio.kind='geluid'`) audio heeft, en user heeft `kb_sound_enabled=True`, speelt die audio automatisch af. **Apart van TTS** — werkt zonder dat TTS aan staat.

**Backend**:
- `modules/kb_v2/sound_lookup.py` — cache met mtime-invalidation, `find_sound_for_text()` scant Spark's message-tekst voor begrippen
- Chat-triggers: "geluid aan" / "geluid uit" / "kaart geluid aan/uit" (geplaatst vóór action_intents zodat ambient-stop niet conflicteert)
- User-pref `kb_sound_enabled` opgenomen in settings-schema (`scope: user`)
- Hook in `_save_log` centraliseert toevoeging van `sound_url` + `sound_begrip` aan ALLE response-paths (early returns gedekt)

**Frontend**:
- GesprekkenPage detecteert `data.sound_url` in chat-response → `new Audio(fullUrl).play()` op de achtergrond
- Volume default 0.7, niet awaited (blokkeert geen mic re-arming)

**Verified end-to-end**:
- "geluid aan" → user setting `kb_sound_enabled=True` persisted
- "ik ben boos" → Spark zegt "Boos" → response.sound_url = onweer.mp3 (van boos-kaart)
- "geluid uit" → setting `False`, geen sound_url meer in response

**ROADMAP.md bijgewerkt** met sessie 21 deliverables (B/C/D/E).

---


## Completed (2026-06-02 — sessie 21D — KB v2 audio-kind toggle)

### 🎤↔️🔊 v6_kbv2_audio_kind_001 — Spraak/Geluid wissel-knop op kaart-audio
**Probleem**: Bij KB v2 kaart-audio (primaire `voice_url`) was geen onderscheid mogelijk tussen "gesproken" (ingesproken/spraak) en "geluid van" (sfx, bv. paard-hinniken). Extra audio had wel een keuze bij upload, maar niet wijzigbaar achteraf.

**Oplossing**:
- **Backend** (`modules/kb_v2/media_routes.py`):
  - Nieuw veld `media.voice_kind` op kaart (default 'spraak', backwards compat).
  - `PATCH /api/kb/v2/media/voice/kind/{card_id}?kind=spraak|geluid` — toggle primaire voice.
  - `PATCH /api/kb/v2/media/voice/secondary/kind/{card_id}?archive_id=X&kind=Y` — toggle een specifiek extra-audio item.
- **Frontend** (`KennisbankV2Page.js` MediaSection):
  - Klikbare badge bij élke audio-rij: `🎤 SPRAAK` (roze) ↔ `🔊 GELUID` (indigo) — één klik wisselt direct.
  - Gebruikt `Mic` en `Volume2` lucide-icons.
  - Test-ids: `kbv2-voice-kind-toggle` (primair), `kbv2-extra-kind-toggle-{i}` (per extra audio rij).

**Verified via curl**:
- Primary toggle: spraak → geluid → spraak (persisted in JSON, success:true response).
- Secondary toggle: voor random extra-audio (kbv2-089254f8 / 9d1e1ccbbbc5) spraak → geluid → spraak.

**Toekomstige use-case**: in combinatie met de "sps"-tag (sessie 21C) kunnen de Steen/Papier/Schaar/etc. KB-kaarten "GELUID"-audio bevatten (actie-geluiden) die door de RPS bark afgespeeld kunnen worden bij de juiste momenten (bv. "geluid van" een schaar knippt → bij win/loss).

---


## Completed (2026-06-02 — sessie 21C — RPS V2: korte triggers, community bots, help-integratie)

### 🎮 v6_rps_001b — RPS uitbreidingen
**Korte triggers** in chat-routes: "speel steen" / "speel papier" / "speel schaar" / "spelletje sps" / "speel spelletje" openen nu allemaal de game (naast oorspronkelijke "speel steen papier schaar").

**Community-mode** (random bot-tegenstanders):
- Spark-tab → opponent = "spark" (eerste 10 random, dan leren).
- Community-tab → opponent = "bot" → service kiest random uit ["bot-madelief","bot-harry","bot-smith","bot-boekhouder","bot-dood"].
- Slimheid: alleen "spark" en **"bot-dood"** gebruiken het learning-algoritme (= moeilijk). Andere bots zijn 100% random (makkelijk).
- Opponent wordt opgeslagen in sessie en getoond in bark-header: "vs Spark" / "vs De Dood 💀" / "vs Madelief" etc.

**Live KB-image lookup** (`rps_routes._hydrated_cards()`): kaarten met `image=None` in de hardcoded RPS_CARDS dict worden live opgezocht in `data/knowledge/v2/*.json`. Dit pakt automatisch nieuw geüploade afbeeldingen op — bv. Willem heeft net een "denkt na"-image geupload (`c6b518680717`) die nu vanzelf in de bark verschijnt.

**KB-tagging "sps"**: alle 10 RPS-gerelateerde kaarten (Steen, Papier, Schaar, Gewonnen, Verloren, Denkt na, Maak een keus, Score, High Score, Stop) hebben nu de tag `sps` voor toekomstige geluidskoppeling (geluidsbestanden krijgen de "sps"-prefix).

**Help-integratie** (`data/help/gradatie_7.json`): RPS-topic toegevoegd aan gradatie 7 (laagste), via inheritance-chain (1→2→3→4→5→6→7) zichtbaar in alle gradaties. Inclusief shortcuts voor "speel sps", "hoe vaak gewonnen", "reset score sps".

**Frontend** (`RpsBark.js`):
- Nieuwe `opponent` prop met default 'spark'.
- Header toont `vs <oppLabel>` (Spark / De Dood 💀 / Madelief / etc.).
- ChoiceBadge en learning-indicator gebruiken dynamisch de opponent-naam.
- `useEffect` triggert `/games/rps/start?opponent=X` bij open.

**Frontend** (`GesprekkenPage.js`):
- Spark-tab stuurt `channel:'spark'` → backend bepaalt opponent.
- Community-tab: client-side trigger-detectie vóór de bot-POST, opent bark direct met `opponent='bot'`.

**Verified**: testing agent iteration 25 — 14/14 backend pytest + 5/5 frontend Playwright flows passed. Geen bugs, geen issues. Test-bestand: `/app/backend/tests/test_rps_v2_iter25.py`.

---


## Completed (2026-06-02 — sessie 21B — Steen-Papier-Schaar mini-game)

### 🎮 v6_rps_001 — RPS mini-game in chat
**Trigger**: type "speel steen papier schaar" in Spark-chat → bark-popup opent.

**Backend** (`modules/games/rps/`):
- `rps_engine.py` — pure logic (resolve, counter_of, predict_next) — **herbruikbaar voor D&D battles later** (Schaar=aanval, Steen=verdediging, Papier=ontwijken).
- `rps_service.py` — sessies + lifetime stats + learning history (laatste 100 zetten).
- `rps_routes.py` — endpoints: `POST /api/games/rps/{start,play,reset,stop}`, `GET /{cards,session,stats}`.

**Spark's gedrag**:
- Eerste 10 rondes: 100% random ("Spark leert nog" badge zichtbaar).
- Vanaf ronde 11: 60% counter-de-meest-voorkomende speler-keuze (laatste 20 zetten) / 30% random / 10% mirror.

**XP & Achievements**:
- +10 XP per win, +1 per gelijkspel, 0 per verlies.
- `rps_first_win` (+25 XP eenmalig), `rps_first_loss` (+10 "voor de moed"), `rps_streak_5` (+50).

**Chat-triggers** (`modules/chat/routes.py`):
- "speel steen papier schaar" → frontend action `open_game_rps` opent bark.
- "hoe vaak gewonnen/verloren" → stats-bericht in chat.
- "reset score sps" → sessie-score gereset, lifetime intact.

**Frontend** (`components/games/RpsBark.js`):
- Modal met 3 keuze-knoppen (KB-kaart thumbnails Steen/Papier/Schaar).
- Score-bar (session wins/losses/ties + streak).
- "Spark denkt na…" 800ms → reveal Spark's keuze + uitkomst-kaart (Gewonnen/Verloren).
- Reset-knop (alleen sessie), Close (X) sluit modal.
- Learning-indicator: "🧠 Spark leert nog" → "⚡ Spark heeft je door" na ronde 10.
- Toasts voor achievements + XP-bonus.

**Verified**: testing agent iteration 24 — backend 11/11 pytest, frontend modal+flow volledig werkend. Eén UX-tweak na test: placeholder bg-gradient + `loading="eager"` voor de 3MB KB-foto's zodat tiles niet leeg laden.

**Data files** (auto-created):
- `data/games/rps/sessions.json`, `stats.json`, `learning.json`

---


## Completed (2026-06-02 — sessie 21 — KB v2 image-delete + Admin frame-bark)

### 🖼️ v6_kbv2_image_delete_visibility_001 — Foto-X altijd zichtbaar
- **Bug**: delete-X knop op KB v2 kaart-foto's stond op `opacity-0 group-hover:opacity-100` → onzichtbaar op touch/mobile of voor users die niet wisten dat hoveren nodig was.
- **Fix**: knop nu altijd zichtbaar als rood cirkeltje met witte X + `shadow-md ring-1 ring-slate-900` voor contrast (file: `frontend/src/components/workspace/KennisbankV2Page.js` regels 1167-1185).
- **Backend**: `DELETE /api/kb/v2/media/image/{card_id}?image_url=...` was al correct, met curl getest (HTTP 200, `{success:true, remaining:N}`).
- **Verified**: testing agent iteration 23 (computed opacity=1, zichtbaar zonder hover).

### 🛡️ v6_admin_grant_frame_001 — Admin grant via ornamental InputBark
- **Verandering**: oude inline form (select + password + button) in `InstellingenPage.js` Admin-tab vervangen door één trigger-knop **"Maak admin (in frame-bark)"** die de ceremoniële InputBark met het ornament-frame opent.
- **InputBark velden**: `targetId` (select met grantable users) + `grantPw` (password). Submit roept `grant({targetId, grantPw})` → `POST /api/admin/grant`.
- **UX**: bij succes → success-bark "Admin geactiveerd"; bij fout → error-bark "Toegang geweigerd". Frame-popup auto-sluit bij succes.
- **File**: `frontend/src/components/admin/InstellingenPage.js` (regels 970-1005 trigger + 1024-1080 InputBark renderer).
- **Verified**: testing agent iteration 23 (BarkModal opent met frame, 22 user-opties, password input, Annuleer werkt).

### 🐛 Bug 733a8bb9 closed — KB v2 onbruikbare kaarten verwijderen
- UI-knop `data-testid="kbv2-delete-btn"` bestond al in CardDetail header (v6_kbv2_delete_001).
- Backend `POST /api/kb/v2/delete` getest (geeft correcte 404 voor onbekende kaart).
- Bug-entry in `data/bugs/bugs.json` gemarkeerd als `opgelost`.

---


## Completed (2026-06-02 — sessie 19/20 — Admin-rol systeem + bark-modal)

### 🛡️ v6_admin_role_001 — Admin als losstaande technische rol

**Probleem**: alle admin-checks deden `gradatie ≤ 2` → familie (gradatie 2) kreeg automatisch admin-rechten. Niet uitsplitsbaar, en bij Willem-dood-scenario (Lotus → gradatie 1) zou admin automatisch overgaan zonder bevestiging.

**Oplossing**:
- Nieuwe `user.admin` boolean — los van gradatie
- Centrale helper `modules/admin/admin_service.is_admin(user_id)`
- Seed admins: alleen user-001 (Willem) + user-000 (Spark) bij eerste boot
- Andere users (incl. familie gradatie 2) krijgen NIET automatisch admin
- Toekenning via `POST /api/admin/grant` met admin-wachtwoord (env var)
- Anti-lockout: laatste admin kan zichzelf niet revoken
- Wachtwoord beheerd in `data/system/admin_password.json` (runtime-writable) met env-var-default

### 🎨 Bark-modal systeem
- Nieuwe component `frontend/src/components/shared/BarkModal.js`
- Visuele popup met KB-kaart-afbeelding (uit doen-lade) + titel + tekst + 4 tones (info/success/warn/error)
- Gebruikt jouw kaarten: "Admin geactiveerd", "Admin gedeactiveerd", "Toegang verleend", "Toegang geweigerd"
- Backend lookup via `GET /api/admin/bark-image?begrip=X` zoekt eerste image_url in alle lades
- Vervangt droge `alert()`/`toast()` calls met sfeerrijke Spark-respons

### 🖥️ Admin-tab in Instellingen
- Nieuwe tab in `InstellingenPage.js` (ShieldCheck-icon, paars)
- Sectie 1: Lijst huidige admins met "seed"-badge + intrekken-knop (met confirm)
- Sectie 2: Nieuwe admin toekennen (user-dropdown + wachtwoord + Maak admin)
- Sectie 3: Admin-wachtwoord wijzigen (oud + nieuw met min. 6 tekens)
- Bij elke actie: BarkModal met passende afbeelding (Admin geactiveerd / Toegang geweigerd / etc.)

### Bestanden gewijzigd in sessie 19 (admin-deel)
- `/app/backend/modules/admin/admin_service.py` — NEW: helper + grant/revoke/seed logic
- `/app/backend/modules/admin/role_routes.py` — NEW: 8 endpoints
- `/app/backend/modules/admin/__init__.py` — export role_router + admin_service
- `/app/backend/server.py` — registreer role_router + bootstrap-load password + ensure_seed_admins
- `/app/backend/.env` — ADMIN_PASSWORD seed
- `/app/frontend/src/components/shared/BarkModal.js` — NEW: herbruikbare visuele popup
- `/app/frontend/src/components/admin/InstellingenPage.js` — Admin-tab + `AdminSettingsPanel`

### 📌 Voor PRODUCTIE-DEPLOY (na deploy stappen)
1. Deploy preview → productie via "Save"
2. **DIRECT na deploy**: log in als Willem → Instellingen → Admin → "Admin-wachtwoord wijzigen" → wijzig `AppelsapAdmin2026` naar eigen sterk wachtwoord
3. Controleer dat alleen Willem + Spark als seed-admin gemarkeerd zijn
4. Run `POST /api/kb/v2/vocab/sync` met `viewer_id=user-001` in productie om alle geclassificeerde kaarten naar vocab te brengen
5. Productie heeft de admin-kaarten al in doen-lade → bark-popups werken direct

---


## Completed (2026-06-01 — sessie 19, fork — Shadow safety + corrupt data cleanup + auto-resume MERGE-fix)

### 🛡️ v6_shadow_safety_001 — Shadow-cascade gepauzeerd + recycle bug gefixt
**Problemen ontdekt na live productie-deploy**:

1. **Recycle-bug archiveerde ACTIEVE shadows** — `recycle_pot_as_shadow_zero()` zette zowel `active` als `closed` shadows naar `archived_cycle_N`. Active shadows = open posities op Bitvavo → coin uit zicht in admin → bij SELL van origineel werden ze NIET mee-gesloten → **coin verloren**.

2. **Data-corruptie in 7 actieve shadows** ontdekt:
   - `shadow-124/130/136/139/145/148` — pot=SOL-EUR maar shadow.market=ATOM/ETH/BCH-EUR mismatch
   - Trail-SELL faalt structureel doordat shadow.entry van compleet andere coin afkomstig is

3. **Shadow-loop risico** — recycle creëerde 3 nieuwe idle slots ongeacht of vorige cyclus winstgevend was → bot kon eindeloos BUYs blijven afgeven bij elke drop.

**Fixes**:

- **Master-flag `SHADOW_ENABLED`** (default **FALSE**) in `shadow_pots.py`. Bot's monitor loopt nu door `is_shadow_enabled()` check; bij False worden alle shadow-activaties geskipt. Origineel-potje BUY/SELL (= simpele veilige trader) blijft normaal werken.
- **Recycle-guard**: `recycle_pot_as_shadow_zero()` blokkeert nu als er nog `active` shadows zijn. Eis: alle 3 moeten status `closed` zijn (via SELL gesloten). Voorkomt coin-verlies.
- **Cleanup-endpoint** `POST /api/trade/shadow/cleanup-corrupt`: detecteert shadows met market-mismatch of entry_price-drift > 2×, markeert ze `archived_corrupt` met `corrupt_reasons[]` log.

**Nieuwe endpoints**:
- `GET /api/trade/shadow/flag` — lees master-flag
- `POST /api/trade/shadow/flag {"enabled": true/false}` — toggle master-flag
- `POST /api/trade/shadow/cleanup-corrupt` — clean corrupt actieve shadows

**Live cleanup uitgevoerd (preview)**:
- 7 corrupt shadows → `archived_corrupt`
- Resterende 4 actieve shadows (ADA pot-011/017 + SOL pot-010/016) zijn correct (markets matchen, entry binnen verwachte marge)
- Shadow stats nu: 88 idle / 4 active / 76 archived

**Test**: `test_shadow_trigger.py` aangepast — recycle vereist nu eerst SELL van actieve shadows (test 11a). Alle 13 tests pass.

### 🐛 v6_resume_persist_merge_001 — Auto-resume bug definitief gefixt (earlier in sessie 19)
**Probleem**: Trade bots resumden niet na backend restart. Root cause: `_persist_registry()` overschreef bestand met alleen in-memory bots. Wanneer 1 bot stopte na restart (rest van bots nog niet in `_registry`) verdwenen ze.

**Fix**: `_persist_registry()` mergt nu met bestaand bestand. Bots die niet in-memory zijn behouden hun laatst-bekende state.

**Test**: 3 pytests in `tests/test_registry_persist_merge.py` — alle PASS.

**E2E**: 5 bots hersteld vanuit backup → stop user-1996fa59 → restart → log "4 registry-bot(s) auto-resumed" + skip user-1996fa59 ✅

### Status alle bots (eind sessie 19)
| User | Running | Mode |
|---|---|---|
| user-000 (Spark) | ✅ | 19 potjes |
| user-001 (Willem) | ✅ | 15 potjes |
| user-1996fa59 | ✅ | 1 potje |
| user-5dd295db | ✅ | 1 potje |
| user-a0ee2d7e | ✅ | 2 potjes |
| user-4d9b59aa | ✅ | 1 potje |

### Bestanden gewijzigd in sessie 19
- `/app/backend/modules/trade/monitor.py` — `_persist_registry()` MERGE + file-lock + SHADOW_ENABLED check (cleane if-block) + shadow logging
- `/app/backend/modules/trade/shadow_pots.py` — `is_shadow_enabled()` / `set_shadow_enabled()` flag + recycle-guard tegen active shadows + public `cleanup_corrupt_active_shadows()`
- `/app/backend/modules/trade/shadow_routes.py` — flag endpoints + cleanup-corrupt endpoint, **admin-guard (gradatie ≤ 2)** op alle mutaties
- `/app/backend/data/trade/shadow_flag.json` — persistent flag (NEW, default enabled=false)
- `/app/backend/tests/test_registry_persist_merge.py` — NEW, 3 pytests
- `/app/backend/tests/test_shadow_trigger.py` — uitgebreid met recycle-blokkade test (13 tests totaal)
- `/app/backend/data/trade/bots_registry_state.json` — hersteld vanuit backup, alle 5 bots actief
- `/app/frontend/src/components/modules/TraderPage.js` — admin-only Shadow-cascade toggle + Cleanup-knop in shadow banner (UI)

### Code-review fixes (post-review)
Na een read-only code review zijn deze verbeteringen doorgevoerd:
1. **Admin-guard op alle shadow-mutaties** (`POST /flag`, `POST /cleanup-corrupt`) — gradatie ≤ 2 vereist, anders 403. GET /flag blijft public-read.
2. **File-lock op `_persist_registry()`** — gebruik `storage._get_lock(REGISTRY_STATE_FILE)` zodat parallelle stop/start calls niet elkaars writes overschrijven (race condition fix).
3. **`raise StopIteration` anti-pattern vervangen** door schone `if _shadow.is_shadow_enabled(): ...` blok.
4. **Private method exposure opgelost** — endpoint roept nu public `shadow_svc.cleanup_corrupt_active_shadows()` aan i.p.v. `_load()` / `_save()` direct.
5. **Frontend stuurt `viewer_id`** bij cleanup en parseert backend 403-detail naar alert.

### 📌 Voor PRODUCTIE-DEPLOY: handmatige stappen vereist
1. Deploy preview naar productie via "Save"
2. Na deploy: open Trader-pagina als admin (Willem), klik op de **🧹 Cleanup corrupt** knop in de shadow-banner. Werkt nu via UI i.p.v. curl.
3. Shadow-cascade staat default UIT. Open Trader → zie banner met "Shadow-cascade: UIT · veilige modus". Klik "UIT" om aan te zetten zodra je vertrouwt dat data clean is.

---


## Completed (2026-05-31 — sessie 18I, fork — Map fix: dorp/stad avatars per provincie, groei-logica)

### 🗺️ Wereld-map gebruikt nu dorp/stad-avatars (niet bewoner-avatars)
- Bewoner-avatars zijn **verwijderd** van de wereldkaart (waren alleen voor 1 stad bedoeld, niet voor de wereld)
- Bewoner-avatars verschijnen alléén in:
  - De `BewonersStripPanel` (rechter MID-kolom)
  - Het Handel-paneel
  - Later: in dorp-popup per gebouw

### 🌱 Groei-logica geïmplementeerd
- `spark` fractie hoofdstad (Stormhaven, Groningen) → **"basis stad"** D&D-kaart-avatar (groot)
- Alle andere 11 provincies → **"Basis Dorp"** D&D-kaart-avatar (kleiner)
- Logica is per `p.fractie_id === 'spark'` check — later uit te breiden met `dorp_level` veld (level 1-5: dorp, level 6+ stad)

### Frontend update in `MiniMapPanel`
- Nieuwe state: `dorpAvatarUrl` + `stadAvatarUrl` (apart geladen via begrip-lookup)
- Verwijderd: `bewonersByStad` map en bijbehorende fetch
- Render: `const avatarUrl = isStad ? (stadAvatarUrl || dorpAvatarUrl) : dorpAvatarUrl;`

### Test (DOM-inspectie via Playwright)
- ✅ `prov-groningen` → image `href=67cfb1c42e50` (basis stad)
- ✅ Alle 11 andere provincies → image `href=b70664a716bf` (Basis Dorp)
- ✅ Geen bewoner-images meer op wereldkaart

### Bestanden gewijzigd in sessie 18I
- `/app/frontend/src/components/profile/DnDCharacterSheet.js` — `MiniMapPanel` state + render-logica gewijzigd

---


## Completed (2026-05-31 — sessie 18H, fork — Dobbelsteen-events met JOUW 2 D&D avatars)

### 🎲 Dobbelsteen-event systeem (NIEUW)
- Nieuwe module `/app/backend/modules/dnd/dice.py` (~140 regels)
- Endpoints:
  - `GET /api/dnd/dice/cards` — geeft beide dobbelsteen-D&D-kaarten terug met image_urls
  - `POST /api/dnd/dice/roll` — `{user_id, dice: "basis"|"super", stat_key?, actie?}` → 1d20 + stat-bonus
- **Card-lookup via begrip-naam** (geen hardcoded IDs — robuust tegen kaart-edits):
  - "Basis Dobbelstenen Avatar" → 🎯 basis worp
  - "Super dobbelsteen avatar" → ⭐ super worp (gebruikt TOP 2 hoogste stats als bonus i.p.v. 1)
- 5 uitkomst-niveaus met flavor-tekst:
  - `≤ 1` → 💀 kritiek_faal (rood)
  - `2..9` → ❌ faal (oranje)
  - `10..15` → ✅ succes (groen)
  - `16..19` → ✨ groot_succes (paars)
  - `20+` → 🌟 kritiek_succes (geel)
- Worpen worden geschreven naar `character.events_feed` (laatste 50) als `kind=WERELD` event

### 🎨 DiceRollerPanel UI in MID-kolom (onder OVERIG)
- 2 grote avatar-knoppen met JOUW geüploade 512×512 images (Basis oranje, Super paars met amber-glow shadow)
- Tijdens worp: `animate-spin` op de avatar (visuele roll)
- Stat-keuze dropdown (Kracht/Behendigheid/etc. met huidige bonus zichtbaar)
- Actie-input (vrije tekst, bv. "verken bos")
- Resultaat-kader met level-kleur border, emoji, getalbreakdown (base + bonus = total), level-label, flavor-tekst
- `data-testid="dice-basis-btn|dice-super-btn|dice-stat-select|dice-action-input|dice-result"`

### Test (visueel + curl)
- ✅ Basis-worp 18 + 0 = 18 → groot_succes ("Het loopt soepel — alsof iets je een zachte duw geeft.")
- ✅ Super-worp 7 + 0 = 7 → faal (UI screenshot bevestigd: rood kader, "❌ 7 = 7 · FAAL")
- ✅ Beide avatars correct gerenderd vanuit D&D-kaarten

### Bestanden gewijzigd in sessie 18H
- NEW `/app/backend/modules/dnd/dice.py` (~140 regels)
- `/app/backend/server.py` — dice router
- `/app/frontend/src/components/profile/DnDCharacterSheet.js` — `DiceRollerPanel` (~115 regels) + integratie in MID-kolom

---


## Completed (2026-05-31 — sessie 18G, fork — Layout fix + Map full coverage + Speler-glow op dorp)

### 🗺️ Alle 12 provincies krijgen avatar-cirkel
- `MiniMapPanel` haalt nu de **"Basis dorp"** D&D-kaart op als generieke fallback
- Avatar-lookup volgorde:
  1. `bewonersByStad[hoofdstad]` (eerste bewoner-avatar van die stad)
  2. `dorpAvatarUrl` (generieke "Basis dorp" 512×512 image)
  3. Fractie-shield (laatste fallback)
- Resultaat: alle 12 provincies tonen nu een avatar-foto met fractie-glow ring (i.p.v. lege dots)

### 👤 Speler-avatar met glow op StormhavenMapView
- Nieuwe `PlayerOnMap` component (intern in `StormhavenMapView.js`)
- Laadt `GET /api/avatar/current/{userId}` voor speler's eigen avatar
- Rendert op `char.player_x_pct ?? 50` / `char.player_y_pct ?? 50` (default centrum, later per gebouw)
- Visueel: 48×48 emerald cirkel-frame + pulsende radial-gradient ring (1.8s, 0.85↔1.15 scale)
- `data-testid="player-on-map"`, tooltip "Jij bent hier"

### 📐 Layout reshuffle (2x3 bewoners + handel naast map)
- **BewonersStripPanel** heeft nu een `compact` prop:
  - Compact mode: `grid grid-cols-3 gap-2` (2×3 = 6 zichtbaar), kleinere 48×48 avatars
  - Default mode: horizontale scroll-strip (60+ zichtbaar)
- Verplaatst naar **MID-kolom** onder `OverigPanel` (compact aan)
- **BewonerHandelPanel** heeft nu een `compact` prop:
  - Compact mode: vertikale flex-stack i.p.v. 12-col grid, 80×80 avatar in horizontale row
  - Avatar+info, "Te koop" en "Jouw rugzak" panels onder elkaar
- Verplaatst naar **RIGHT-kolom** onder `MiniMapPanel` (compact aan)
- Oude rij onder de 3 kolommen verwijderd (geen extra full-width strip meer)

### Resultaat (visueel geverifieerd)
- ✅ BEWONERS · STORMHAVEN 2×3 = 6 vakjes compact in MID-kolom
- ✅ SPARK WORLD · 12 PROVINCIES toont ALLE 12 provincies als avatar-cirkels
- ✅ HANDEL · HANS DE BAKKER opent compact onder Spark World (RIGHT-kolom)
- ✅ Layout-balans verbeterd: alle 3 kolommen ongeveer gelijke hoogte

### Bestanden gewijzigd in sessie 18G
- `/app/frontend/src/components/profile/DnDCharacterSheet.js` — `MiniMapPanel` dorpAvatarUrl, `BewonersStripPanel` compact, `BewonerHandelPanel` compact, layout reshuffle
- `/app/frontend/src/components/profile/StormhavenMapView.js` — `PlayerOnMap` component met groene puls-glow

---


## Completed (2026-05-31 — sessie 18F, fork — Bewoners + Map-avatars + Item-transfer)

### 👥 NPC Bewoner-systeem (NIEUW)
- Nieuwe module `/app/backend/modules/dnd/bewoner.py`:
  - Schema: `id`, `naam`, `beroep`, `fractie_id`, `provincie_id`, `hoofdstad`, `avatar_card_id` (D&D-kaart link), `gebouw_card_id`, `wallet.goud`, **8 inventory_slots**, `rang`, `beschrijving`
  - Endpoints: `GET /` (filterbaar op provincie/fractie/stad), `GET /{id}`, `POST /` (create), `PATCH /{id}`, `PUT /{id}/slot/{n}` (admin slot vullen), `DELETE`, `POST /seed`
  - Trade: `POST /{id}/buy` (speler koopt slot N) + `POST /{id}/sell` (speler verkoopt eigen item → bewoner betaalt 50%)
- 3 bewoners gespeed in Stormhaven:
  - **Hans de Bakker** (Bakker, Spark, 80g) → verkoopt brood/appel/ei, gekoppeld aan "Bakker persoon" + "Bakker gebouw" D&D-kaarten
  - **Greta de Slager** (Slager, Spark, 100g) → verkoopt vlees, gekoppeld aan "Slager"-kaarten
  - **Oude Mira** (Kruidenvrouw, Natuur, 60g) → verkoopt heelkruid + water (placeholder avatar via Vraag-avatar)

### 🛒 BewonerPanel UI (NIEUW in Avatar-tab)
- `BewonersStripPanel` — horizontale strip met 96px avatar-circles per bewoner (klik = activeer)
- `BewonerHandelPanel` — geopend bij selectie, toont:
  - Links: 128×128 bewoner-avatar met naam/beroep/rang/wallet-goud/quote-beschrijving
  - Midden: 8 vakjes "TE KOOP" (4×2 grid, prijs-overlay, klik = kopen, rood/disabled als te duur)
  - Rechts: 8 vakjes "JOUW RUGZAK" (4×2 grid, +sellPrice overlay, klik = verkopen voor 50%)
- `data-testid="bewoners-strip|bewoner-{id}|bewoner-handel|bewoner-buy-slot-N|bewoner-sell-slot-N"`

### 🗺️ Map markers — avatar-circles met fractie-glow + speler-glow-dot
- `MiniMapPanel` upgrade: i.p.v. lege fractie-shield-cirkel toont elke provincie nu de **eerste bewoner-avatar** van die hoofdstad als ronde foto (clipPath) met fractie-kleur outline
- Fallback: fractie-shield met witte kern (voor provincies zonder bewoner)
- **Speler-glow-dot**: groene pulsende cirkel (1.8s animatie) onder de provincie waar `char.dorp` matcht — visueel "Jij bent hier"
- Behoudt drag/admin/select functionaliteit

### 🤝 Item-transfer systeem met thuis-check
- Backend: `POST /api/inventory/{user_id}/transfer` met `{from_container, to_container, slot_id, equip_slot_key}`
- Containers: `rugzak` ↔ `huis` ↔ `equipment:{slot_key}` (bv. `equipment:torso`)
- **Thuis-check**: `_is_home(user_id)` → `char.locatie_naam == char.dorp`. Rugzak↔Huis vereist thuis, 403 als niet thuis
- Equipment↔Rugzak mag altijd (kleren wisselen onderweg)
- Items hebben nu `location: "rugzak"|"huis"` field (default "rugzak")
- GET `/api/inventory/{user_id}/is-home` → boolean
- Frontend RugzakKaderPanel + HuisOpslagPanel:
  - Filter slots op `location` (`!== 'huis'` voor rugzak, `=== 'huis'` voor opslag)
  - Hover-overlay op gevulde slots: "→ Huis" / "→ Rugzak" knop + Drop-knop voor rugzak
  - Alleen tonen als `isHome === true`
- `data-testid="rugzak-tohome-N|rugzak-drop-N|opslag-torug-N"`

### Backend test (curl)
- ✅ `POST /api/dnd/bewoners/seed` → 3 bewoners
- ✅ `PUT /api/dnd/bewoners/{id}/slot/N` → items in bewoner-inventory
- ✅ `POST /api/dnd/bewoners/{id}/buy` → speler 50g - 2g brood = 48g, item verschijnt in inventory
- ✅ `GET /api/inventory/user-001/is-home` → `true`

### Frontend visueel geverifieerd (Willem login → Avatar tab)
- ✅ Bewoners-strip toont 3 avatars (Hans, Greta met eigen D&D-kaart images, Mira met placeholder)
- ✅ Handel-panel opent bij klik, toont bewoner-avatar + 8/8 vakjes + prijslabels
- ✅ Map shows avatar-circles voor Stormhaven (Bakker) en Leeuwarden (Mira), met fractie-glow
- ✅ Groene speler-glow-dot pulse onder Stormhaven (huidige locatie)

### Bestanden gewijzigd in sessie 18F
- NEW `/app/backend/modules/dnd/bewoner.py` (~360 regels)
- `/app/backend/server.py` — bewoner router registreren
- `/app/backend/modules/inventory/routes.py` — `/transfer` + `/is-home` + `location` field
- `/app/frontend/src/components/profile/DnDCharacterSheet.js` — `BewonersStripPanel`, `BewonerHandelPanel`, transferItem/buy/sell helpers, RugzakKaderPanel + HuisOpslagPanel transfer-knoppen, MiniMapPanel avatar-circles + speler-glow

---


## Completed (2026-05-31 — sessie 18E, fork — Game-items SEED met placeholder + Spark-advies)

### 🎲 D&D Game Items SEED — alle slots gevuld + consumables
- Nieuwe endpoint `POST /api/dnd/spark-world/game-cards/seed-missing-items`
- Genereert **17 DRAFT D&D-kaarten** (14 nieuw, 3 al bestaand) voor alle ontbrekende slots + consumables
- **Placeholder image**: Vraag-avatar (`/api/avatar/gallery/31c6dc04a2fd/image`) — Willem upload later de echte
- **Spark-advies in `laag1`** per kaart (jouw input bij "context invullen zonder GPT in line 1 2 3"):
  - bv. "Wollen mantel die warmte vasthoudt op koude tochten. Biedt lichte bescherming."
- **`laag2/3/4` + `ws5` blijven leeg** — voor Willem om in te vullen zonder GPT

### Slot-dekking compleet (15 van 17 slots gevuld)
- ✅ hoofd, nek, schouders, armen, trinket, torso, broek, voeten
- ✅ sjaal, riem, handen, ring_l, linkerhand, rechterhand, offhand, pijl_boog, rugzak
- (ring_r niet gespeed — gebruikt zelfde "Basis ring" als ring_l, prima)

### Nieuwe items per slot/categorie
| Slot/Cat | Kaart | Slot | kg | Stats/Combat |
|---|---|---|---|---|
| nek | Basis ketting | nek | 0.1 | +1 Wilskracht |
| schouders | Basis mantel | schouders | 0.8 | +2 Verdediging |
| armen | Basis armband | armen | 0.1 | +1 Behendigheid |
| trinket | Basis medaillon | trinket | 0.05 | +1 Geluk |
| sjaal | Basis sjaal | sjaal | 0.2 | +1 Conditie |
| riem | Basis riem | riem | 0.3 | — |
| handen | Basis handschoenen | handen | 0.2 | +1 Verd, +1 Aanval |
| ring_l | Basis ring | ring_l | 0.02 | +1 Intelligentie |
| offhand | Basis lantaarn | offhand | 0.8 | -1 Beweging |
| pijl_boog | Basis boog | pijl_boog | 1.2 | +1 Beh, +4 Aanval, +2 Initiatief |
| **Consumables (rugzak)** | | | | |
| food | Basis kaas | — | 0.3 | herstel 15 conditie (laag1) |
| food | Basis appel | — | 0.15 | herstel 8 conditie |
| food | Basis ei | — | 0.08 | basis voor maaltijden |
| tool | Basis fakkel | — | 0.5 | 30 min brandtijd |
| currency | Basis goudstuk | — | 0.01 | universele ruileenheid |
| consumable | Basis heelkruid | — | 0.05 | herstel 25 conditie, 1× |
| tool | Basis touw | — | 0.6 | 10m hennep-touw |

### Status na seed
- Totaal items in catalog: **32** (24 uit D&D-kaarten + 8 hardcoded fallback)
- Elke seed-kaart heeft `footnote.needs_image: true` en `footnote.needs_lagen: true` — markeert wat Willem moet aanvullen
- `status: "draft"` — Willem klikt later "lock" wanneer kaart klaar is

### Workflow voor Willem
1. Open Kennisbank → D&D-kaarten
2. Open een draft-kaart (bv. "Basis ketting")
3. Upload echte 512×512 image (placeholder Vraag-avatar wordt vervangen)
4. Verfijn `laag1` advies, vul `laag2/3/4` aan (context/regels/varianten/lore)
5. Vul `ws5` aan (wie/wat/wanneer/waar/waarom/hoe)
6. Klik "lock" → kaart is canon

### Bestanden gewijzigd in sessie 18E
- `/app/backend/modules/dnd/spark_world.py` — `seed-missing-items` route + `PLACEHOLDER_IMAGE_URL`

---


## Completed (2026-05-31 — sessie 18D, fork — UNIFICATIE: items leven nu in D&D-kaarten)

### 🎯 Doel: stop fragmentering — D&D-kaart-systeem is dé bron-van-waarheid

### 🃏 D&D-kaart schema uitgebreid met `game_meta`
- Nieuw veld `game_meta` op elke D&D-kaart (`/app/backend/modules/dnd/spark_world.py` `create_game_card`):
  ```python
  game_meta: {
    is_item: bool,         # True = kaart is bruikbaar als item in rugzak/inventory
    slot: str,             # equipment slot (rechterhand/torso/etc.) of "" voor non-equip
    weight: float,         # kg
    stats_bonus: {kracht, behendigheid, intelligentie, conditie, wilskracht, geluk},
    combat_bonus: {aanvalskracht, verdediging, magie, crit_kans, beweging, initiatief},
    meta: {klasse, beroep, fractie, locatie},
    value_goud: int,
    rarity: str,           # common / uncommon / rare / epic / legendary
    kind: str,             # food / weapon / armor / tool / shield / drink / currency / pet
  }
  ```
- `edit_game_card` doet nu deep-merge op `game_meta` (dict-in-dict updates werken correct)

### 🌐 Nieuwe endpoints
- `GET /api/dnd/spark-world/game-items?slot=...&fractie=...` — lijst items vanuit D&D-kaarten
- `POST /api/dnd/spark-world/game-cards/migrate-items` — eenmalige migratie van hardcoded ITEM_CATALOG naar `game_meta` op overeenkomende kaarten

### 🔀 Catalog API geunificeerd (`GET /api/inventory/catalog/all`)
- **Primaire bron**: D&D-kaarten met `game_meta.is_item=true` (mét je eigen 512×512 images)
- **Fallback**: hardcoded ITEM_CATALOG, gefilterd op items die NOG GEEN D&D-kaart hebben (via `footnote.item_migrated_from`)
- Geen duplicaten meer — items met kaart hebben prioriteit

### 🚀 Eenmalige migratie uitgevoerd (11 → 10 succesvol)
- Brood, Vlees, Water, Rugzak, Zwaard, Schild, T-shirt, Broek, Helm, Schoenen — allemaal gekoppeld aan jouw bestaande D&D-kaarten
- Bug gefixt: "ei" matchte substring "Kleine straat" → matching strenger gemaakt (substring alleen voor hints > 3 chars)
- Resultaat: 10 items uit D&D-kaarten + 8 hardcoded fallback (Trekrugzak, Penning, Kaas, Appel, Ei, Fakkel, Goudstuk, Auto-Bark)
- Wanneer je voor die 8 een D&D-kaart maakt + `game_meta.is_item=true` zet → migreren ze automatisch

### Frontend `itemImage()` slimmer
- Stap 1: `item.image_url` direct (komt van unified catalog)
- Stap 2: `item.item_id` start met `game-` → match op `gameCards.find(id)`
- Stap 3: legacy fallback via `findCardForItem` (hardcoded ID_MAP)

### Test (curl)
- ✅ `/api/dnd/spark-world/game-items` → 10 items, allemaal met `image_url`
- ✅ `/api/inventory/catalog/all` → 18 totaal (10 D&D-kaart + 8 hardcoded), geen duplicaten
- ✅ Frontend rugzak grid + Huis-opslag tonen images correct

### Bestanden gewijzigd in sessie 18D
- `/app/backend/modules/dnd/spark_world.py` — `game_meta` schema, `/game-items`, `/migrate-items`, deep-merge in edit
- `/app/backend/modules/inventory/routes.py` — `/catalog/all` unified met dedup op `item_migrated_from`
- `/app/frontend/src/components/profile/DnDCharacterSheet.js` — `itemImage()` 3-staps lookup

### Volgende stap voor Willem
Wanneer je een nieuwe item-kaart aanmaakt in het D&D-systeem:
1. Upload image
2. Vul `begrip`, `tags`, `lagen.laag1` (beschrijving)
3. Edit `game_meta`: zet `is_item: true`, kies `slot`, vul `weight`, `value_goud`, etc.
4. Item verschijnt automatisch in catalog + rugzak + equip-modal — geen code nodig

---


## Completed (2026-05-31 — sessie 18C, fork — Items naar JOUW 512x512 images, geen emojis)

### 🖼️ Items koppelen aan eigen 512x512 D&D-kaarten
- Helper `findCardForItem(item, gameCards)` met expliciete `ID_MAP`:
  ```
  brood         → Basis brood (game-b55)
  vlees         → basis vlees (game-4ba)
  water         → Waterput (game-29b)
  zwaard-klein  → 1 hand wapen rechts (game-006)
  schild-basis  → Basis schild (game-46f)
  linnen-shirt  → T-shirt (game-77d)
  linnen-broek  → Broek basis (game-831)
  lederen-helm  → Hoofd (game-7fb)
  leren-laarzen → schoenen (game-a80)
  backpack-*    → Basis rugzak (game-bf0)
  ```
- Fallback: matching op naam-contains, dan tag-exact
- Helper `itemImage(item, gameCards)` retourneert `${API}${card.media.image_urls[0]}`

### 🎒 Rugzak panel — 32-slot grid, geen emojis, geen "+ Add" knop
- Grid uitgebreid van 16 → **32 slots (8×4)** zoals Huis & Opslag
- Items tonen nu **jouw 512×512 D&D-card image** (object-cover) i.p.v. emoji
- Fallback: eerste letter naam als image-lookup mislukt
- "+ Item toevoegen" catalog-button VERWIJDERD — items vullen slots via gameplay (loot/koop)
- Header hint aangepast: "Items vullen de slots wanneer je ze vindt of koopt."

### 🏠 Huis & Opslag — zelfde image-koppeling
- `opslag-grid` toont nu items met `itemImage()` (jouw 512×512 images)
- Visueel consistent met de rugzak

### 🎨 EquipSlotModal catalog-items
- Item-cards in modal tonen nu **64×64 preview-thumbnail** van de gematchte D&D-kaart i.p.v. emoji
- Stat-pills/meta-regels onveranderd

### Test (Willem login → Avatar tab, na seed van 3 items)
- ✅ rugzak-slot-0 toont Basis brood image
- ✅ rugzak-slot-1 toont 1-hand wapen image
- ✅ rugzak-slot-2 toont T-shirt image
- ✅ opslag-slot-0/1/2 tonen zelfde images
- ✅ Geen "+ Item toevoegen" zichtbaar
- ✅ kg-counter: 2.5/10 kg (groen)

### Bestanden gewijzigd in sessie 18C
- `/app/frontend/src/components/profile/DnDCharacterSheet.js` — findCardForItem helper, RugzakKaderPanel v2 (32 slots, images), HuisOpslagPanel opslag-grid images, EquipSlotModal catalog preview-thumbnails

---


## Completed (2026-05-31 — sessie 18B, fork — Items met stats + Rugzak-kader als eigen panel)

### 🎒 Rugzak als eigen kader naast Huis & Opslag (Willem feedback)
- Nieuwe `RugzakKaderPanel` component (rechterkolom, boven HuisOpslagPanel)
- Toont: header `RUGZAK · ONDERWEG` + gekleurde kg-counter, hint-tekst, kg-progressbar, slots-counter, speed-label
  (`Licht — snel` / `Goede balans` / `Vol — iets trager` / `Zwaar geladen — traag`)
- 16-slot grid (klik op item = verwijderen, met confirm)
- Collapsible "+ Item toevoegen (N beschikbaar)" → 4-kolom catalog grid, klik = direct toevoegen
- `data-testid="rugzak-kg-counter|rugzak-kg-bar|rugzak-grid|rugzak-slot-N|rugzak-quickadd-toggle|rugzak-add-{id}"`
- Body-slot rugzak op silhouet blijft + kleine kg-meter eronder — consistent visueel

### ⚔️ Item-stats schema toegevoegd (combat + meta)
- ITEM_CATALOG schema-uitbreiding (`/app/backend/modules/inventory/routes.py`):
  - `slot`: target equipment-slot (bv. `rechterhand`, `torso`)
  - `stats_bonus`: `{kracht, behendigheid, intelligentie, conditie, wilskracht, geluk}`
  - `combat_bonus`: `{aanvalskracht, verdediging, magie, crit_kans, beweging, initiatief}`
  - `meta`: `{klasse, beroep, fractie, locatie}` — `fractie=""` = common loot, later fractie-specifiek
- 6 nieuwe combat-items: Klein Zwaard, Basis Schild, Linnen Shirt, Linnen Broek, Lederen Helm, Leren Laarzen
- Allemaal `rarity: "common"` en `fractie: ""` (overal te vinden, basis-tier)

### 🎨 EquipSlotModal upgrade — item-catalogus met stats preview
- Nieuwe sectie boven D&D-galerij: "Item-catalogus (N) · stats inbegrepen"
- Per item kaart toont: icoon · naam · kg · beschrijving · stats-pills + meta-regel
- Pills kleurgecodeerd: groen=stats / rood=combat+ / amber=combat− / geel=goud / grijs=rarity
- Klik = vult naam + icon, gemarkeerd met amber ring

### Backend testing
- ✅ `/api/inventory/catalog/all` → 18 items (12 origineel uit eerdere subsessie + 6 combat)
- ✅ `/api/dnd/character/slots/config` → 18 slots inclusief `rugzak`

### Frontend (visueel geverifieerd via screenshot na Willem login)
- ✅ Rugzak kader rechtsboven (`RUGZAK · ONDERWEG`, 0.0/10 kg, slots 0/4, "Licht — snel")
- ✅ Rugzak body-slot zichtbaar op silhouet met groene kg-meter
- ✅ Huis & Opslag label `STILSTAAND` met "geen kg-limiet"
- ✅ Handel-kader placeholders onderaan (Warehouse, Auction House, Werkbank)

### Bestanden gewijzigd in sessie 18B
- `/app/backend/modules/inventory/routes.py` — 6 combat-items + stats schema
- `/app/frontend/src/components/profile/DnDCharacterSheet.js` — RugzakKaderPanel, EquipSlotModal stats-preview

---

## Completed (2026-05-31 — sessie 18A, fork — Rugzak hersteld + voedsel-items)

### 🎒 Rugzak terug op de Avatar (per ongeluk verwijderd in vorige sessie hersteld)
- **`rugzak` slot** weer toegevoegd aan `body_layout.json` (x:65 y:36) + `SLOT_KEYS` + equipment schema in `character.py`
- **Kg-meter onder rugzak slot**: kleur-progress bar (groen <70%, geel 70-90%, rood ≥90%)
- Capacity wordt doorgegeven vanuit `inventory.capacity` aan `BodySilhouettePanel` → `SlotFrame`
- Bestaande character JSON files krijgen `rugzak: null` automatisch via `eq.setdefault()`

### 🍞 Item-catalog uitgebreid met voedsel (bakker/slager loop)
- 8 voedsel/loot items: Brood (0.4kg, 2g), Stuk Vlees (0.6kg, 4g), Veldfles Water (0.8kg, 1g),
  Boerenkaas (0.3kg, 3g), Appel (0.15kg, 1g), Ei (0.08kg, 1g), Fakkel (0.5kg, 2g), Goudstuk (0.01kg)
- Elk item met `tags`, `value_goud`, `kind`, `description`

### 🏠 Huis & Opslag verduidelijkt
- Header `HUIS & OPSLAG · STILSTAAND` + counter "Opslag X/500 · geen kg-limiet"
- Emerald hint: "🏠 Hier staat alles stil — bereid eten, sla loot op, pak in je rugzak wat je meeneemt op pad."

### 🏪 Handel-kader voorbereiding (3 placeholders onderaan)
- Warehouse · Auction House · Werkbank — dashed-border kaders met "binnenkort"
- `data-testid="dnd-trade-prep"`

---


## Completed (2026-05-31 — sessie 18, fork — Rugzak hersteld + items)

### 🎒 Rugzak terug op de Avatar (per ongeluk verwijderd in vorige sessie hersteld)
- **`rugzak` slot weer toegevoegd** aan `body_layout.json` (positie x:65 y:36) + `SLOT_KEYS` + equipment schema in `character.py`
- **Kg-meter onder rugzak slot**: toont `kgUsed/kgMax` met kleur-progress bar (groen <70%, geel 70-90%, rood ≥90%)
- **Capacity wordt doorgegeven** vanuit `inventory.capacity` aan `BodySilhouettePanel` → `SlotFrame` (alleen rugzak-slot toont de meter)
- Bestaande character JSON files krijgen `rugzak: null` automatisch via `eq.setdefault()`

### 🍞 Item-catalog uitgebreid (start-loot, voorbereiding bakker/slager/handel)
- 8 nieuwe items toegevoegd aan `ITEM_CATALOG` (`/app/backend/modules/inventory/routes.py`):
  - **Voedsel**: Brood (0.4kg, 2g), Stuk Vlees (0.6kg, 4g), Boerenkaas (0.3kg, 3g), Appel (0.15kg, 1g), Ei (0.08kg, 1g)
  - **Drank**: Veldfles Water (0.8kg, 1g)
  - **Tool**: Fakkel (0.5kg, 2g)
  - **Currency**: Goudstuk (0.01kg)
- Elk item heeft `tags`, `value_goud`, `kind`, `description` — klaar voor avatar-image matching en handel-prijsbepaling

### 🏠 Huis & Opslag panel verduidelijkt
- Header label `HUIS & OPSLAG · STILSTAAND` + counter regel: "Opslag X/500 · geen kg-limiet"
- Toegevoegd: emerald hint-tekst "🏠 Hier staat alles stil — bereid eten, sla loot op, geen gewicht-restrictie. Pak in je rugzak wat je meeneemt op pad."
- Conceptueel onderscheid: **Huis** = 500 slots, geen kg / **Rugzak** = beperkt door kg (op avatar zichtbaar)

### 🏪 Handel-kader voorbereiding (3 placeholders)
- Onderaan D&D character sheet: 3-kolom grid met dashed-border placeholders
  - **Warehouse** (per stad/fractie · opslag voor handelaren · binnenkort)
  - **Auction House** (loot kopen/verkopen · prijs per fractie · binnenkort)
  - **Werkbank** (thuis koken/maken · brood, vlees, drank · binnenkort)
- `data-testid="dnd-trade-prep"` voor latere testing
- Vervangt de oude losse "Toekomstige uitbreiding" placeholder

### Bestanden gewijzigd
- `/app/backend/data/dnd/body_layout.json` — rugzak slot toegevoegd
- `/app/backend/modules/dnd/character.py` — SLOT_KEYS + SLOT_LABELS + equipment-schema
- `/app/backend/modules/inventory/routes.py` — 8 nieuwe items in catalog
- `/app/frontend/src/components/profile/DnDCharacterSheet.js` — kg-meter op SlotFrame, capacity prop, Huis-label, Handel-kader placeholders

### Backend testing
- ✅ `GET /api/inventory/catalog/all` → 12 items (4 origineel + 8 nieuw)
- ✅ `GET /api/dnd/character/slots/config` → 18 slots (17 origineel + rugzak)
- Frontend smoke-tested (app rendert, login pagina zichtbaar)

---



## Completed (recent — 2026-05-31, sessie 17 / fork — vervolg 7, final pre-deploy)

### 💰 Surplus-mint: 3 nieuwe ROAR tokens
- Bitvavo €389,74 vrij vs admin €360 → €29,74 surplus
- Mint 3 tokens naar Spark (user-000): 16 → 19 ROAR
- 3 extra non-anchor pots toegevoegd voor Spark (6 anchor + 13 non-anchor = 19 totaal)
- Nieuwe totaal: 39 tokens / 39 pots / €390 admin / 99 idle shadows
- Bitvavo-precisie: €389,74 ÷ 39 = €9,99 gemiddeld per token (1 cent afwijking onder nominaal €10)
- `roar_balances.mint_history` log met motivatie + milestone ref

### 🔧 Avatar bug fix
- AvatarPickerPanel body-field `avatar` → `avatar_ref` (matchen backend `AvatarSelect` model)
- `avatar-changed` event krijgt nu `detail.userId` zodat UserAvatar + AuthContext per-user kunnen reageren
- `activate-personal` flow: na POST activate doe extra PUT select met `avatar_ref="user"` zodat huidige avatar daadwerkelijk wisselt naar je eigen portret
- E2E getest via curl — selectie persisteert, sidebar + Algemeen-tab live update

### 🎲 D&D Avatar-tab herstructurering v2 (Willem 31 mei avond)
**Quick wins (uitgevoerd):**
- **EventFeed verplaatst naar bovenaan** (col-span-12, breed) — info-laatste-nieuws omhoog
- **CharInfoPanel verplaatst** uit onderbalk naar **linker kolom** (onder Body+Equipment)
- **Rugzak verwijderd** (`InventoryGridPanel` niet meer aangeroepen — dode code blijft als _LegacyInventoryGrid bewaard)
- **HuisOpslagPanel uitgebreid tot master-inventory**:
  - 5 huis-slots (gebouwen) + 5 meubel-slots (decor) — onveranderd
  - Nieuw: 32 zichtbare opslag-slots (8×4 grid, venster op 500 totaal)
  - Header counter `Opslag X/500` rechtsboven (geen kg-limiet meer — "het is je huis")
  - Items uit `inventory.slots` worden in opslag-grid getoond
- **Worldmap onder Dorp** (gelijke breedte i.p.v. apart onderaan), SVG `h-56 → h-72`
- **Placeholder kader** onderaan ("Toekomstige uitbreiding · handel-kader hub · pop-up dorp/stad — zie ROADMAP P2")
- **Footer-nav tabs** automatisch omhoog door verwijdering MiniMap-onderkolom

**Layout nieuw**:
```
Row 1: EventFeed (col-12, breed bovenaan)
Row 2 (3 kolommen):
  LEFT  (col-5): Body+Equipment, CharInfo (verplaatst)
  MID   (col-3): Karakter-portret, Stats, Aanval/Verd, Overig
  RIGHT (col-4): HuisOpslag (master inv, 500 cap), Dorp (h-52), Map (h-72)
Row 3: Placeholder "Toekomstige uitbreiding"
```

**Voor latere uitwerking (ROADMAP P2)**: pop-up Dorp-info modal · pop-up Stad-info op landkaart · centraal handel-kader hub · Persoonskaart-progressie geïntegreerd.



### 🔄 Full Reset voor "echte start" (na productie-deploy, 31 mei avond)

**Trigger**: Willem deployde naar productie (https://roadkillcommunity.nl), zette trader stil, verzamelde data, en uploadde een verse backup-zip (20:29) met bugs + nieuwe users + kaarten. Voorbereiding voor "echte start" — telling tot nu was alles test.

**Uitgevoerd in preview**:

1. **Zip-import** (`spark_backup_full_20260531_202912.zip`):
   - `system/users.json` (7 users, +1 nieuw user-c609d7d1)
   - `financial/user_potjes.json` (36 pots, 21:28 snapshot)
   - `trade/bots_registry_state.json` + `registered_users.json`
   - `bugs/bugs.json` (50 bugs, 5 echte open)
   - `knowledge/v2/*.json` (2852 inbox kaarten, 48 nieuwe indelingen sinds vorige sync)
   - Pre-import backup → `_backups/pre_zip_import_20260531_203845/`

2. **Mock-bug gefixt voor alle users** (`bots_registry_state.json` + per-user `settings.json`):
   - user-1996fa59: `auto_trade=False → True, use_mock=True → False`
   - user-5dd295db: idem
   - 5 andere bots geverifieerd LIVE
   - **Alle 7 users nu echt traden**

3. **Token-count ↔ potje-count sync** (Willem regel: 1 token = 1 potje):
   - user-1996fa59: 10 pots → 1 (9 weeskinderen verwijderd)
   - user-5dd295db: 2 pots → 1 (1 weesje verwijderd)
   - Spark (user-000): behouden op 10 pots (4 non-anchor + 6 anchor) — speciale system-account
   - Willem (user-001): 21 tokens = 21 pots ✓
   - Andere users: match ✓

4. **Capital reset naar €10.00 voor ALLE potjes**:
   - Anchors óók (Willem's wens: clean slate over alle linie)
   - ATOM-anchor van €12.67 → €10 gecorrigeerd (Willem had 2 ATOM opgenomen op Bitvavo)
   - `stats.trades = 0`, `position` cleared (alle 25 ghost-posities administratief gesloten — geen Bitvavo SELL nodig want amount=0)
   - 0 capital-afwijkingen na reset, 0 open posities, 0 ghost-trades

5. **Shadow pots wipe + regenereren**:
   - 90 oude shadows → 0 → 90 nieuwe idle (3 slots × 30 non-anchor pots over 6 users)
   - Verdeling: Spark 12 · Willem 63 · andere 4 users 3-6 elk
   - Alle in cyclus 1, status=idle

6. **Avatar-bug gefixt** ("weg op 2 plekken"):
   - `AlgemeenTab` regel 149: gebruikte alleen `d.url`, niet `d.fallback_url` → fallback-vraagteken werkte niet
   - Hint-tekst "Verander via 'Avatar' tab" → "Verander via 'Instellingen' tab" (Avatar-tab is D&D nu)
   - **Live-refresh hook**: `UserAvatar` + `AuthContext` luisteren naar `avatar-changed` event → sidebar/header auto-update bij avatar-keuze in Instellingen
   - Willem's eigen avatar herstelt naar Black Knight (`gallery:cf90e9ea6393`)

7. **Avatar-tab opgeschoond**:
   - "Portret & Galerij beheren" collapsible verwijderd → vervangen door AvatarPickerPanel in Mijn Profiel → Instellingen (waar het thuishoort)
   - `PersoonskaartCard` verwijderd uit Avatar-tab → was overbodig naast D&D character sheet; toekomstige integratie in Spark World D&D (ROADMAP P2)
   - Avatar-tab toont nu uitsluitend de DnDCharacterSheet (kern van Spark World D&D-laag)

### Open bug reports (uit zip, top-5)
- **#d481414b**: "minder als 20 potjes weg gegeven maar blijf zo veel zien" → mogelijk gefixt door token-count sync hierboven
- **#3d4a5d69** + **#eb440a60**: KB v2 kaarten verplaatsen tussen lades + delete-knop in KB → P1
- **#0f26bf42**: "palster" niet correct als kennis kaart geclassificeerd → KB v2 issue
- **#13b2640e**: "basis potjes van elke token zijn anders geworden" → gefixt door anchor-reset naar €10
- **#a70b36b5**: Graph rebuild dubbelt frontend telling → P2



### 📿 v6_bijbel_aansluiting_001 — Missie · Visie · Doelen verbonden in Spark Bijbel

**Context**: Spark Bijbel-tab toonde alleen Levenswijsheden + Reactie Voorbeelden + 5W+H Framework. De Willem mistte de aansluiting tussen Missie/Visie/Doelen en Normen/Waarden — die bestaan wel in de data maar werden niet visueel verbonden.

**Toegevoegd**:
- `spark_bijbel.json::spark_bijbel.missie` (nieuw veld): kern-missie expliciet vastgelegd.
- `spark_bijbel.json::spark_bijbel.visie` (nieuw veld): toekomstvisie expliciet vastgelegd.
- `spark_bijbel.json::doelen` geüpgraded van lijst-van-strings naar lijst-van-objects: `{tekst, verbinding}` waarbij `verbinding` linkt naar een kernwaarde-naam.
- Mapping: Mensen helpen→Helpen · Veilige ruimte→Respect · Kennis delen→Transparantie · Nalatenschap→Loyaliteit.

**UI** (`SparkBrainPage.js` regel 344-401):
- Nieuwe Card "Missie · Visie · Doelen" met groene Target-icon bovenaan Spark Bijbel tab.
- 3 sub-secties met verschillende kleur-codering: groen (Missie), cyaan (Visie), amber (Doelen).
- Elke doel-item heeft klikbare roze pill "→ Helpen" / "→ Respect" / etc. die direct naar Normen & Waarden-tab springt.
- Voetnoot expliciet: "Deze missie, visie en doelen sturen Spark's keuzes — gekoppeld aan 9 kernwaarden en 6 normen."
- Bug-fix in Identiteit-tab: `{d}` rendering van doelen-objects gefixt (was React-error sinds doelen nu objects zijn).

**Resultaat**: bezoeker van Spark Brain → Spark Bijbel ziet nu in 1 oogopslag het complete ethische raamwerk: Missie → Visie → Doelen → (link naar) Normen & Waarden → Levenswijsheden. De volledige aansluiting die ontbrak.



### 🖼️ v6_avatar_picker_001 — Avatar-kiezer terug in Mijn Profiel → Instellingen

**Context**: Avatar-keuze stond ooit in een eigen "Avatar"-tab. Die tab is verbouwd naar D&D character sheet (sessie 17 eerder). Daardoor was er geen plek meer waar users hun profiel-avatar konden kiezen/uploaden.

**Oplossing**: nieuw `AvatarPickerPanel` component binnen Mijn Profiel → tab Instellingen. Volgorde top→bottom: Account → Avatar → Beeld-glow → Geluid → Connecties.

**Features**:
- Live preview huidige avatar + bron-label (gallery:xxx / user / standaard)
- Upload eigen afbeelding (klik "Upload eigen" → file picker)
- Grid "Jouw eigen" (personal gallery) met X-knop om te verwijderen
- Grid "Gedeelde galerij" (41 afbeeldingen) scrollbaar
- Selectie ringt roze (Pink-400 accent)
- Bij selectie: `avatar-changed` custom event dispatched zodat sidebar-avatar live verandert

**Backend hergebruik**: bestaande `/api/avatar/*` endpoints (geen nieuwe routes). Field-mapping: `current.avatar_ref` + `current.url`/`current.fallback_url`.



### 🧠 v6_warmth_layer_001 — Norm/waarden van shadow → LIVE in spraak

**Achtergrond**: Emotie-pipeline draaide tot nu toe SHADOW-only (sessie 11). De pipeline detecteerde correct "deze user voelt twijfel → kernwaarde Emoties → behavior vertragen-ondersteunen" maar Spark's response gebruikte die info NIET. A/B diff bewees dat: 60% match-ratio met vaak knowledge-route i.p.v. emotie-route bij negatieve input.

**Nieuwe warmth-laag** (`modules/emotion_pipeline/warmth.py`):
- **Trigger**: pipeline detecteert behavior in `(begrenzen-structureren, vertragen-ondersteunen, kalmeren-opties)` + weging in `(sterk, escalerend)` + route in info-routes.
- **Effect**: prefix response.message met korte erkenningszin uit kernwaarde laag1 of fallback behavior-template ("Snap dat het zwaar voelt.", "Even rust nemen mag.", "We doen het stap voor stap.").
- **Veilig**: skip routes die eigen toon hebben (greeting/goodbye/agenda/identity/help/time/capability/wedervraag). Max 1 warmth-prefix per response. Niet vervangen — Spark geeft nog steeds de kennis.
- **Centraal**: hook zit in `_save_log` (regel 1448) zodat ALLE early-returns gedekt zijn. Fallback van `trigger_type` naar `response.type` voor flow-end save.

**Emotion triggers uitgebreid**:
- `emotion_triggers.json` van ~12 woorden per emotie → 24-41 woorden.
- Spreektaal toegevoegd: "verdomme/klote/woest/kut" (boos), "eenzaam/hopeloos/tranen/verdriet" (bedroefd), "twijfel/onzeker/stress/kwijt" (bang), "super/top/yes/geweldig" (blij).
- Multi-word phrases verwijderd ("weet niet", "snap niet") want `word_freq.get()` matcht alleen losse tokens — single-word triggers met hogere puntenwaarde werken WEL.

**E2E geverifieerd via curl**:
- Boos+knowledge: `warmth_applied=True`, prefix "Respect begint bij ruimte laten." (kernwaarde Respect)
- Bang+knowledge: prefix "Wat invloed heeft, moet zichtbaar zijn." (Transparantie)
- Bedroefd+knowledge: prefix "Even rust nemen mag." (Emoties → fallback want exacte kernwaarde-naam mismatch)
- Neutraal/greeting: `warmth_applied=None` (correct skip)

### ⭐ v6_kbv2_priority_001 — Top 50 prio voor lege laag1

**Doel**: 2112 inbox-kaarten zonder laag1 is te veel om te scrollen. Geef Willem gericht de TOP belangrijkste eerst.

**Score-formule** (in `service.list_priority_missing_laag1`):
- +3 per bestaand verband (kaart wordt al gerefereerd)
- +1 per tag (rijker getagd = relevanter)
- +5 als topic gevuld (5W-vragen al gesteld door Spark)
- +2 als ws5 gedeeltelijk gevuld

**Endpoint**: `GET /api/kb/v2/priority/missing-laag1?limit=50`.

**UI** (`KennisbankV2Page.js`): nieuwe paarse "⭐ Top 50 prio (laag1)" knop naast bestaande reden-filters. Card-tile toont `prio N` badge (paars) + scoring breakdown in tooltip. Auto-reset bij tab-wissel.

**Live resultaat**: 2112 missing → top 5 begint met "besproken" (score 5), "Wat is gisteren in de community besproken?" (score 3), gevolgd door "preventie/user-verrijkt/mode/voertuig/politiek/plezier/mengen/architectuur" (alle score 1).



### 🌑🌑🌑 v6_shadow_cascade_002 — 3-laags piramide + bodemdetectie LIVE

**Concept-wijziging** (Willem's correctie): NIET 1 shadow per pot met %-trigger, maar **3 shadows per pot** met **bodemdetectie** als trigger (stabilisatie na drop). Bij 4e drop-cyclus → recycle origineel als nieuwe cyclus-start ("origineel was de eerste shadow van zichzelf").

**Backend (`shadow_pots.py` complete rewrite)**:
- `MAX_SHADOWS_PER_POT = 3` met `slot` veld per shadow (1/2/3).
- `is_stabilizing_after_drop(candles, entry, current)` — bodemdetector. Vereist:
  1. Huidige prijs ≥ -1.5% onder entry (`MIN_DROP_BEFORE_SHADOW`)
  2. Laatste 5 candles (`STABILIZATION_LOOKBACK`): range max-min < 1.2% (`STABILIZATION_RANGE_PCT`) = vlakke lijn
  3. Geen new low: laatste close ≥ vorige close × 0.998
- `recycle_pot_as_shadow_zero()` — Willem's "4e shadow = origineel": archived_cycle_N + 3 nieuwe idle slots in cycle N+1.
- `shadow_capacity(pot_id, owner)` returnt `{idle, active, closed, slots: {1, 2, 3 → status}, have, total}`.
- `get_next_idle_shadow()` pakt altijd laagste slot eerst (slot 1 → 2 → 3).

**Monitor (`monitor.py`) integratie**:
- Vervangt oude `if profit_pct <= -0.03` met bodemdetectie via `is_stabilizing_after_drop(context_candles, entry, price)`.
- Vóór activatie: check of recycle nodig (`cap["idle"]==0 && cap["have"]>=3` → recycle eerst, dan activeer slot 1 van nieuwe cyclus).
- Log toont nu: `SHADOW-ACTIVATE shadow-XXX slot N/3 (market) @ €Y (drop -Z%, range W%)` + `trigger_reason` per shadow.
- Bij SELL van origineel: sluit **ALLE** active shadows (slot 1+2+3 hebben elk hun eigen profit op recovery).

**Frontend (`TraderPage.js`)**:
- Banner toont nu "🌑 Shadow Potjes · 3-laags piramide · stand-by: N · actief · gesloten · gearchiveerd · onbeschermd".
- Per-pot badge is nu **slot-progressie**: `○○○` (3 idle), `●○○` (slot 1 actief), `●●○`, `●●●` (alle 3 actief), `✓✓✓` (alle 3 gesloten — recycle bij volgende drop).
- Active shadows worden uitgelijst onder positie: `🌑 S1/3 @ €X.XX`, `🌑 S2/3 @ €Y.YY`, etc. Met `trigger_reason` als tooltip.
- Pot-tile heeft purple ring + bg als één of meer shadows actief.

**Live data na re-ensure**:
- **90 idle shadows** = 3 slots × 30 trade-potjes verdeeld over 6 users.
- Spark 12 · de Willem 63 · andere token-houders 3-6 elk (anon naar memory toe).

**Test-suite** `/app/backend/tests/test_shadow_trigger.py` — **12/12 pass**:
- 3-slot create + 4e geweigerd
- Per-user scope isolatie
- Stabilisatie GEDETECTEERD bij vlakke candles
- Freefall NIET getriggerd (range > 1.2%)
- Kleine drop geweigerd (< 1.5%)
- Activate slot 1 → 2 → 3 in volgorde
- 4e activate geweigerd
- Recycle cyclus 1 → 2 met nieuwe idle slots
- Close shadow met profit

### 🟢 Mock-indicator fix (TraderPage)
UI defaultede te aggressief naar "Mock" tijdens loading (`!== false` matchte ook `null`). Nu drie-staps display: Laden… / Mock / LIVE. Willem's user (use_mock=false) toont nu correct **LIVE**.



### 🌑 Disclaimer huidige stop-loss (v6_stop_loss_001)
Stop-loss @ -2% **realiseert het verlies** door SELL. Vrijgekomen potje kan re-entry doen, maar de -2% wordt definitief in het kasboek geboekt. Werkt voor 1 juni, maar **vervangbaar door shadow-potje systeem** (zie ROADMAP P1 — Willem's idee, betere oplossing).



- **v6_stop_loss_001** — Hard stop-loss bij -2% verlies (vóór trail-logica):
  - Verlies-pad ≠ trail-pad → géén 2 systemen, gewoon 1 systeem in 2 richtingen
  - Drempel `STOP_LOSS_PCT = -0.02`. Bij triggering: forced SELL met reason "Sluit verlies-positie om potje vrij te maken voor re-entry"
  - Lost de "gemiste re-entry kans" op: na grote drop wordt potje vrijgemaakt → bot kan weer kopen bij stabilisatie/stijging
  - Trail-strategie (+1% winst) blijft 100% onaangetast
  - Geverifieerd: -2.5% → stop-loss SELL ✅, -1% → HOLD ✅

- **v6_buy_cooldown_001** — 5-minuten BUY-cooldown per markt:
  - Voorkomt dat bot binnen 8 min 20× achter elkaar hetzelfde markt koopt (30 mei 02:36-02:44 was BTC-EUR 20× BUY in 8 min)
  - `_last_buy_per_market: Dict[market, datetime]` per monitor-instance
  - Cooldown blokkeert nieuwe BUY via decision-reason; trail/stop-loss/SELL onaangetast
  - 300 seconden default, configurabel via constante



- **v6_auto_provision_001** — Auto-registratie bij token-purchase + migratie voor bestaande holders:
  - **Nieuwe helper** `auto_provision_bot_for_token_holder(user_id, use_mock, auto_trade, autostart)` in `modules/trade/monitor.py`. Idempotent: doet niks als user al bot heeft.
  - **3 entry-points gehookt**:
    - `shop/routes.py` (`buy_tokens`) — bij directe token-purchase
    - `shop/gift.py` (`accept_gift`) — bij gift-acceptatie
    - `trade/routes.py` (`POST /admin/migrate-token-holders`) — nieuwe admin endpoint voor migratie van bestaande token-holders
  - **Migratie uitgevoerd**: alle 5 huidige token-holders gechecked. De Willem (user-001, 21 tokens) was als enige nog niet geregistreerd → nu `newly_provisioned` met 21 potjes (1 per token, round-robin over markten).
  - **Defaults voor nieuwe token-holder bot**: `auto_trade=true`, `use_mock=false`, `autostart=false` (user moet bewust starten via UI). Markten = WATCHLIST_COINS (6 stuks).
  - **Boekhouding ready voor 1 juni**: `spark_kasboek.json` = 0 entries (clean slate), hooks loggen met `datetime.now(timezone.utc).isoformat()` → dag/maand/jaar zit automatisch in elke entry's `created_at` + `date` veld. Geen rollover-mechanisme nodig.



- **v6_go_live_001** — Alle 5 token-users bots zijn LIVE per 1 juni:
  - **Bug A (mock-safety)** gefixt: nieuwe `_enforce_mock_safety()` helper in `routes.py` blokkeert handmatige `execute_real_trade` als bot-config `use_mock=True` staat. Toegepast in `/trade/execute/{user_id}` en `/trade/quick-buy-potje/{user_id}`. Hoofd-issue eerder: handmatige Quick-Buy met `use_mock=False` overruleerde de bot-mock-flag en deed echte trades (zoals Lotus/Roadkill op 29 mei 19:09 — dit verklaart "trail-verkoop werkt, koop niet"). Nu hard-block met duidelijke error.
  - **Bug B (auto_trade=False overal)** gefixt: registry `bots_registry_state.json` gepatcht — alle 5 bots (Spark + 4 token-houders) op `auto_trade=true` + `use_mock=false`. Backend gerestart, monitor herlaadt uit registry.
  - **Live status (geverifieerd)**: alle 5 bots draaien, cycles tellen op (~1 cycle/20s), 6 markten gemonitord per bot, klaar voor autonome BUY-signals uit hun strategie.
  - Backup van vorige registry-state in `/tmp/bots_registry_pre_live.json`.
  - Token-users met bot-config: Spark (10 tokens) + 4 anonieme token-houders (totaal 5 tokens). De Willem (jij, 21 tokens) draait nog handmatig zonder bot.



- **v6_dnd_body_layout_001** — Body-avatar als achtergrond + sleepbare slot-frames:
  - **Backend** (`modules/dnd/body_layout.py`): 3 endpoints (`GET /api/dnd/body-layout`, `PUT /api/dnd/body-layout`, `POST /api/dnd/body-layout/reset`). Shared 18-slot layout met x/y % posities in `data/dnd/body_layout.json`. Admin-only via gradatie ≤ 2.
  - **Frontend `BodySilhouettePanel` volledig herbouwd**:
    - Goud-omlijnde body-avatar (user upload "WhatsApp 2026-05-29 23.58.26") als full-bleed achtergrond.
    - Alle 18 slot-frames `position: absolute` met `left/top: x%/y%` uit backend.
    - Frame-design: 40×40 met amber border, gevuld = gouden glow + box-shadow.
    - Label onder elk frame met zwarte outline (paintOrder/textShadow) zodat het leesbaar blijft over de gloeiende avatar.
    - Emerald sync-badge voor inventory-gesync items (zoals rugzak).
    - **Admin sleep-modus**: "✏ sleep" toggle in panel rechtsboven; in edit-mode worden frames sleepbaar (`cursor: grab`, PointerCapture), positie wordt geclamped op 3..97%, direct gesaved bij `pointerup`.
    - "reset" knop herstelt defaults.
  - Oude 3-kolom grid layout + `SLOT_LAYOUT_*` constanten + `SlotCell` component **verwijderd** (dead code).
  - Backend e2e: GET 18 slots, PUT/PATCH werkt. Smoke screenshot: alle 18 frames staan over de goud-avatar.


- **v6_dnd_world_001** — Fundament voor D&D wereld (fracties + provincies + rarity):
  - **Backend** (`modules/dnd/world.py`): nieuwe module met 5 endpoints:
    - `GET /api/dnd/world/rarities` — 5 WoW-style tiers (Common 60%/Uncommon 25%/Rare 10%/Epic 4%/Legendary 1%) met kleur + glow CSS
    - `GET /api/dnd/world/fracties` — 9 fracties: Spark (hoofdfractie), Licht, Schaduw, Vuur (Licht), Lucht (Licht), Water (Schaduw), Aarde (Schaduw), Natuur (Licht, niet-element), Barbaren (Schaduw, niet-element), Neutraal
    - `GET /api/dnd/world/provincies` — 12 NL-provincies met default fractie-binding
    - `PATCH /api/dnd/world/provincies` — admin update (fractie/positie/hoofdstad)
    - `POST /api/dnd/world/provincies/reset` — herstel defaults
  - **Default mapping** 12 provincies: Groningen→Spark, Friesland→Lucht, Drenthe→Aarde, Overijssel→Natuur, Flevoland→Water, Gelderland→Vuur, Utrecht→Licht, Noord-Brabant→Schaduw, Limburg→Barbaren. Noord-Holland/Zuid-Holland/Zeeland blijven **Neutraal** (3 veroverbare regio's).
  - **Frontend MiniMapPanel** vervangt vorige 4-locatie systeem:
    - 12 fractie-shields op de borderless NL-map met fractie-kleur per provincie
    - Klik shield → detail-panel met fractie-info + admin radio-knoppen om fractie te wijzigen
    - Drag-modus voor admin om shields te verplaatsen (PATCH naar backend)
    - Reset-knop herstelt defaults
    - Header toont nu "SPARK WORLD · 12 PROVINCIES"

- **v6_dnd_rugzak_hide_001** — Inventory opruim:
  - Carry-items (`kind: 'carry'`) verdwijnen uit items-lijst zodra gedragen. Status getoond als compacte tekst: "ITEMS (0) · Grote Trekrugzak gedragen".
  - **WoW-style rarity glow** op items: border + box-shadow + tier-naam in eigen kleur (Common grijs/Uncommon groen/Rare blauw/Epic paars/Legendary goud).
  - "Nog geen items" copy verwijst nu naar Spark World D&D-galerij (i.p.v. hardcoded catalog).


- **v6_spark_world_map_001** — Borderless NL-map + draggable city-frames (admin):
  - **Backend** (`modules/dnd/spark_world_map.py`): nieuw bestand met persistente locatie-opslag in `data/dnd/spark_world_map.json`. 3 endpoints: `GET /api/dnd/spark-world/map/locations`, `PUT /api/dnd/spark-world/map/locations`, `POST /api/dnd/spark-world/map/locations/reset`. Admin-only via gradatie ≤ 2 check tegen users.json.
  - **Frontend** `MiniMapPanel` upgrade:
    - SVG-image background gebruikt nu de geüploade "Nederland map kaal.jpeg" als achtergrond (van customer-assets URL).
    - 4 default-locaties: Stormhaven (rechtsboven = Groningen-pos) + 3 vacant city-frames.
    - **Admin sleep-modus**: "✏ sleep"-knop toggle in panel header. In edit-mode worden de hotspots gevuld goud (i.p.v. gestippeld), pointer-events worden actief, en je kunt elke cirkel slepen. Coordinaten worden clamped op 2..98% van het viewport.
    - Auto-save naar backend bij pointerup (PUT). "reset"-knop herstelt defaults via POST.
    - Hotspot-labels worden met `paintOrder: stroke` zwart-omlijnd zodat ze leesbaar blijven over de map foto.
  - Backend e2e: PUT (2 locaties save), POST reset (4 locaties terug) — beide groen.
  - Lint clean (Python E741 'l' variable rename naar 'loc'), Frontend clean.


- **v6_dnd_integration_001** — 5 verzoeken in 1 batch verwerkt:
  - **Persoonskaart terug naar Avatar-tab**: Aura (gedrag → identiteit) + Stats grid + Slots/Gewicht bars + Items + (verwijderde losse) Achievements zitten nu geïntegreerd onder de D&D character sheet.
  - **Rugzak-icoon foto-fix**: PersoonskaartCard kijkt nu in D&D-kaarten op (begrip/tag match) en gebruikt de kaart-foto als 40×40 icoon i.p.v. 🎒 emoji. "Grote Trekrugzak" toont nu de echte rugzak-foto.
  - **Militaire chevron-stripes** (`RankStripe`): in de header-bar staan nu 3+ goud-gevulde chevron-strepen (clip-path parallelogram). Regel: **100 levels = 1 streep**. Sub-tekst: "Level 272 · 2 strepen" + "72/100 tot volgende streep".
  - **Achievement-medailles** op de banner: 🏅 gouden bolletjes (gradient amber→yellow) gestapeld onder de Crown-emblem. Max 4 zichtbaar + "+N" overflow badge.
  - **Spark World mini-map → NL-silhouet**: SVG-pad van Nederland (gestileerd, met provincie-lijnen + Noordzee-textuur). **Stormhaven** als grote gouden hotspot bovenaan (Groningen-positie) met label + "Fractie Spark". 3 extra vacant city-frames als gestippelde cirkels (later klikbaar voor D&D-fractie-kaart koppeling).


- **v6_dnd_dorp_zoom_001** — Stormhaven Dorp-Zoom modal (`StormhavenMapView.js`):
  - Klikken op "Kaart Bekijken" in DORP-paneel opent een full-screen modal met de "Basis dorp" foto als achtergrond.
  - Header toont "Hoofdstad — Fractie Spark · Stormhaven" + Layout Level + Fog of War.
  - **9 gebouw-hotspots** geplaatst rond de circulaire plattegrond (proportioneel %-positioned):
    - Center → **Tempel van Spark** (gouden Sparkles-glow, altijd zichtbaar)
    - N/Z/W → 3× **Waterput** (allemaal jouw `Waterput` foto)
    - NE → **Slager gebouw**, SE → **Bakker gebouw**, SW → **Kleine straat**
    - E → Markt (vacant placeholder), W → Smederij (vacant placeholder)
  - Klik op een hotspot → tooltip met building-info, foto, en `laag1` beschrijving.
  - Footer toont chips voor alle 9 gebouwen + counter "6/9 gevuld" + tip om vacant slots in te vullen met nieuwe D&D-kaarten.
  - Geen backend changes — pure frontend layer over bestaande game-cards en character data.

- **v6_dnd_rugzak_sync_001** — RUGZAK slot ↔ Inventory carry-item sync:
  - DnDCharacterSheet laadt nu `/api/inventory/{user_id}` parallel met character.
  - Als RUGZAK slot leeg is maar inventory heeft een carry-item (kind=`carry`) → toon die automatisch in het slot.
  - Slot toont **groene ⬤ badge** (synced indicator) + capacity-info tekst (`+5 slots · +10kg`).
  - InventoryGridPanel hergebruikt nu de parent inventory state i.p.v. dubbel te fetchen.


- **v6_dnd_card_visuals_001** — D&D-kaarten als visuele bouwstenen in character sheet:
  - Helper `findCardByKeywords(cards, keywords)` met 3-staps matching: tag exact → begrip exact → begrip contains (allemaal case-insensitief).
  - **DORP-paneel** zoekt automatisch een kaart met tag/begrip `dorp` of `stad` en gebruikt de 1e foto als achtergrond + naam uit `begrip` ("Basis dorp"). Vignet zorgt dat tekst leesbaar blijft. Fallback naar getekende SVG-huisjes als geen kaart matcht.
  - **Body silhouet** zoekt een kaart met tag `lijf`/`body`/`silhouet` en gebruikt die als foto-overlay i.p.v. de SVG.
  - **Slot-preview** (faded image in lege slots): elke slot zoekt een kaart via slot-key + label + synoniemen (torso → t-shirt/shirt/hemd, hoofd → helm/hoed/hoofdband, voeten → schoenen/laarzen, handen → handschoenen, rugzak → tas).
  - **Equip-modal upgrade**: toont "SNEL KIEZEN UIT D&D-GALERIJ"-grid met matching kaart-foto's (max 8). Klikken pre-fillt naam uit `begrip`. Tip-tekst legt uit hoe je tags toevoegt om nieuwe kaarten te koppelen.
  - **Huis & Opslag sloten** vullen zich met kaarten getagged `huis`/`opslag` of `meubel`/`stoel`/`bed`/`kast`.
  - Bevestigd met user's 2 bestaande kaarten ("Basis dorp" + tag Dorp → dorp-panel; "T-shirt" + tag shirt → torso slot).


- **v6_dnd_gallery_media_001** — D&D Galerij upgrade: "Nieuwe kaart" modal + functionele foto-media:
  - Nieuwe `NewCardModal`: vervangt `window.prompt`. Velden: begrip/titel + zintuig-kanaal (geen/Zie/Hoor/Voel). Klikt direct in edit-mode.
  - Nieuwe `ArchivePhotoPicker` modal: lijst alle foto's uit Algemene foto-archief (`GET /api/system-archive?category=foto`), met zoekbalk + 3 tabs (Alle / D&D-game / Overige). Klik foto → koppelt URL aan `card.media.image_urls`. Toont ✓-badge voor reeds gekoppelde foto's.
  - Nieuwe `DnDUploadButton`: directe upload van eigen foto naar systeem-archief (auto-tags `D&D, game-card` + description) en hangt automatisch aan de kaart.
  - Functionele Media-sectie in card-detail: thumbnail-grid van gekoppelde foto's (max 4 kolommen) + verwijderknop per foto + "ICON"-badge op de 1e foto (die wordt het kaart-icoon).
  - **Card-list thumbnails**: kaart-rij toont nu een 36×36 thumbnail van de 1e foto i.p.v. alleen sense-emoji. Veel beter te scannen.
  - Backend hergebruikt: `/api/dnd/spark-world/game-cards/edit` met `{media:{image_urls:[…]}}`, `/api/system-archive/upload` voor nieuwe uploads.
  - E2E getest via curl: create → 44 archive-photos beschikbaar → attach foto → list bevat thumb → cleanup OK. UI smoke-screenshot: modal opent correct met begrip-input + zintuig-keuzes.


- **v6_dnd_character_sheet_001** — Stormhaven-stijl D&D Character Sheet onder Avatar-tab:
  - Nieuwe backend module `modules/dnd/character.py` met JSON-persistent character per user in `data/dnd/characters/{user_id}.json`.
  - 4 endpoints: `GET /api/dnd/character/slots/config`, `GET /api/dnd/character/{user_id}`, `PATCH /api/dnd/character/{user_id}`, `POST /api/dnd/character/{user_id}/equip`, `POST /api/dnd/character/{user_id}/event`.
  - Schema: titel, ondertitel, rang_titel, rang_progress_pct, klasse, beroep, fractie, locatie_naam, dorp, dorp_level, fog_of_war_pct, bio, currency (goud/gems/ziel), 18-slot equipment-map, event_feed ringbuffer (max 50).
  - Frontend component `components/profile/DnDCharacterSheet.js` met 3-koloms layout:
    - **Header bar**: banner-emblem, Titel + Ondertitel, Rang-progress bar, 6 rank-shields, 3 currency-pills (Goud/Gems/Ziel), Edit-knop.
    - **Links**: 14+ body-slots rond SVG silhouet (Hoofd/Nek/Schouders/Armen/Trinket/Sjaal/Torso/Broek/Voeten/Riem/Handen/Ring L+R/Rugzak/Linkerhand/Rechterhand/Offhand/Pijl&Boog).
    - **Midden**: Karakter portret + Niveau/XP-bar, Statistieken (Kracht/Behendigheid/Intelligentie/Conditie/Wilskracht/Geluk), Aanval & Verdediging (6 derived stats), Overig (Klasse/Beroep/Fractie/Locatie).
    - **Rechts**: Inventory-grid (8x6 = 48 slots, leest uit bestaande `/api/inventory/{user_id}`), Huis & Opslag (Huis sloten + Meubel sloten), Dorp preview (Stormhaven met fog-of-war).
    - **Onderaan**: Event Feed (ringbuffer met SYSTEEM/WERELD/GUILD/VERHAAL/HANDEL kleurcodering + input), Char Info-tabs (CHAR INFO/LORE/QUEST LOG/Notas), Mini-map.
    - **Footer nav**: 8-knops bottom-tabs (OVERZICHT/STATISTIEKEN/TALENTEN/VAARDIGHEDEN/QUESTS/RELATIES/PRESTATIES/INSTELLINGEN — stub).
  - Equip-modal per slot (naam + emoji-icon, uitrust-knop).
  - Edit-modal voor character meta (titel/klasse/beroep/fractie/locatie/bio + currency).
  - Stone/amber-tinted "perkament" UI met SVG silhouet + village-illustratie.
  - **Persoonskaart verplaatst** van Avatar-tab naar Algemeen-tab (aura + inventory + items + achievements onder Sociale Media).
  - Avatar/portret/galerij ingeklapt in `<details>` "Portret & Galerij beheren" sectie onder character sheet.
  - Backend e2e geverifieerd (GET/PATCH/equip/unequip/event).


## Completed (recent — 2026-05-29, vervolg)

- **v6_kb_curation_dashboard_001** — Tag-curatie UI bovenop `/api/kb/v2/tags/scan` + `/tags/merge`:
  - Nieuw component `components/workspace/KbV2TagCuration.js` met 4 stat-tegels, filter, refresh, 1-klik merge per stem.
  - Geïntegreerd als 6e tab in KennisbankV2Page: **Tag-curatie**.
  - Dropdown per stem voor `keep_variant`-keuze; expand-knop toont alle varianten als chips.
  - Sessie-historie van merges zichtbaar onderaan.
  - E2E verified: 52 dedupe-kansen gevonden (top: systeem 377×, relatie 98×, grondstof 87×).

- **v6_overflow_auto_mint_instant_001** — Instant mint zonder 24h-wachttijd:
  - Nieuw `staking_growth.run_auto_mint_only()` — alleen-mint loop (geen rente).
  - Gehookt in `potjes.close_pot()` voor `user-000`: zodra een Spark-trade sluit en overflow ≥ €10, wordt direct een nieuw trade-potje gemint.
  - Smoke-test: overflow €25 → 2 potjes (pot-016, pot-017) + €5 rest. Daily scheduler-hook behouden als safety-net.
  - `close_pot` returnt nu ook `auto_mint: {minted, n_minted, overflow_after}`.

- **v6_spark_theme_001** — Amber/Orange theme refactor (eerste pas):
  - CSS-variabelen toegevoegd in `index.css`: `--spark-primary`, `--spark-primary-hover`, `--spark-primary-soft`, `--spark-primary-ring`, `--spark-secondary`, `--spark-accent`.
  - Utility-klassen: `bg-spark-primary`, `text-spark-primary`, `border-spark-primary`, `ring-spark-primary`.
  - Cosmetic chrome (focus-rings, action-buttons, upload-chrome, link-hovers) van 23 files vervangen: `bg-purple-500 hover:bg-purple-600` → `bg-amber-500 hover:bg-amber-600`, `focus:border-purple/blue-500` → `focus:border-amber-500`, etc.
  - Bewust **niet** vervangen: mood-glow palet in App.js (semantische emotie-kleuren), status-indicators (paused/mock = blauw), chart-distinctions, module-color-coding in AnalyticsPage, layer-kleuren in EmotiesPage/SparkBrainPage.
  - Dashboard + KB Curation getest, geen visuele regressie.



## Completed (recent — 2026-05-29)

- **v6_token_buy_ux_001** — Token Buy UX hardening:
  - `<Toaster>` (sonner) globaal gemount in `App.js`.
  - `WinkelPage.buyToken()` toont toasts (success + error) en blokkeert preemptief als wallet ontoereikend.
  - Nieuwe inline `data-testid="token-insufficient-warning"` rood-vlak verschijnt zodra `qty * price > wallet_eur`, met exact tekort-bedrag.
  - Resultaat: gebruiker kan dynamische-prijs-overschrijdingen of saldo-tekorten niet meer missen.

- **v6_auto_anchor_001** — Auto-create locked staking-anchor voor nieuwe coins:
  - Nieuw `potjes.ensure_anchors_for_markets(user_id, markets)` — Spark-only.
  - Voor elke watchlist-coin zonder bestaand `pot_locked=True / lock_reason='staking_anchor'` potje wordt automatisch een nieuw locked anker aangemaakt (€10 capital, source=`auto_anchor_for_new_coin`).
  - Gehookt in `monitor.update_markets()` (en daarmee `POST /api/trade/monitor/markets/{user_id}`). Response bevat nu `anchors_created: [{id, market}]`.
  - Non-Spark users worden geskipt (regel: alleen Spark heeft anchors).
  - Smoke-test: nieuwe coin in watchlist → anker direct aanwezig in `user_potjes.json` zonder handmatige stap.


## Completed (recent)
- 2026-05-25 **v6_command_registry_001** (sessie 12 — Bidirectionele Command-Registry MVP / fundering donderdag):
  - 📋 **`/data/system/command_registry.json`** met **27 commands** uit alle modules (capabilities/agenda/notes/wallet/trade/kbv2/bijbel/spark/emotion/community/dagboek/achievements/leaderboard/boekhouder). Per command: `intent_tags[]`, `required_params[]`, `gradatie_min`, `behavior_class_hint`.
  - 🧠 **Intent-extractor** (`modules/intent_registry/extractor.py`):
    - Keyword-map met ~150 woord→canonical-tag mappings
    - Multi-word phrases ("wat is", "wie ben jij", "doe je niet") matchen vóór tokenisatie
    - Emotie-pipeline integratie: voegt `emo:`, `behavior:`, `waarde:` prefix-tags toe als pipeline-summary meekomt
  - 🎯 **Capability-matcher** (`matcher.py`):
    - Jaccard-overlap score met +15% behavior_class bonus als pipeline-behavior matcht
    - Top-N candidates + disambiguation flag (twee scores binnen 0.1)
    - Gradatie-filter (gradatie_min ≤ user-gradatie)
  - 🔌 **6 endpoints** (`routes.py`): `/extract`, `/match`, `/run-flow`, `/registry`, `/log`, `/skills/candidates`
  - 🔍 **Skill-discovery embryo**: `intent_log.jsonl` automatisch geschreven bij elke chat-call (text + tag_vector + chosen_route). `/skills/candidates?min_occurrences=3` detecteert patronen — donderdag UI om accepteren.
  - ✅ E2E verified:
    - "wat staat morgen op mijn agenda?" → tags `[morgen, agenda]` → `agenda_list` score 0.57
    - "hoeveel gebruikers hebben we?" → tags `[tellen, gebruikers]` → `cap_tellen_gebruikers` score 0.40
    - 4x "hoeveel gebruikers" → skill_candidate gevonden met 5-tag-vector + voorbeeld-tekst
  - 🛣️ **Donderdag uitbouwen op deze fundering**: UI disambiguation panel, sequential composition, skill-discovery accept/reject UI, LLM-upgrade extractor, gradatie-locks daadwerkelijk afdwingen.

- 2026-05-25/12 **Sessie 11 + 12 — Spark Core stabilisatie compleet**:
  - Roadmap-tab gesynchroniseerd: alle v6-items afgevinkt (A/B diff toegevoegd als done item).
  - Identity v2.0 linked_layers correct: 9 kernwaarden · 6 normen · 9 bijbel-items · 12 capabilities live · 7 emotie-lagen · 5 KB v2 hooks.
  - Klaar voor: redeploy → De Willem vult kennis-kaarten in → volgende sessie verder aan hand roadmap.

- 2026-05-25 **v6_emotion_pipeline_ab_001** (sessie 12 — A/B diff-view LIVE):
  - ⚖️ **A/B Diff-view tussen huidige route en pipeline-advies** in Spark Brain → Emotie Pipeline tab
  - Backend: `_build_ab_entry()` in `chat/routes.py._save_log` schrijft naar `/data/emotions/pipeline_ab/YYYY-MM-DD.jsonl` met `{ts, user_id, msg_preview, current_route, pipeline_summary, diff_status, diff_note}`
  - **Diff-status logica** (v6_ab_diff_002): mismatch wanneer pipeline een actieve emotie-route adviseert (begrenzen-structureren / vertragen-ondersteunen / kalmeren-opties) maar systeem koos een info-route (knowledge / fallback / capability_placeholder / kbv2_tell_* / how_are_you / time_now / unknown / etc.)
  - 2 nieuwe endpoints: `GET /api/emotion-pipeline/ab/recent?only_mismatches=` en `/ab/stats`
  - **UI A/B Diff widget** in EmotiePipelineSection:
    - 5 stats-tegels: totaal / match (groen) / mismatch (rood) / potential (amber) / match-ratio %
    - "Routes met meeste mismatches" chips (rood)
    - Filter-toggle: "Alle" vs "Alleen mismatches"
    - Per-run kaart: timestamp · message-preview · "HUIDIG: route → PIPELINE: emotie/kernwaarde/behavior" + diff-note in italics + status-badge
  - **E2E verified**: 5 test-chats → 2 mismatches gevonden (boos→knowledge ipv begrenzen, bedroefd→knowledge ipv vertragen). 60% match-ratio. Filter werkt (toont 2 mismatches op klik).
  - 📊 **Eerste inzicht**: huidige smart_intents-flow valt vaak terug op generieke 'knowledge'-route bij negatieve emotionele input — pipeline zou specifieker reageren. Bewijs zichtbaar zonder live impact.

- 2026-05-25 **v6_polish_001** (sessie 11 — laatste polish + KB delete):
  - 🔢 **Kernwaarden 11 → 9**: "Groeien" + "Emoties" verwijderd uit spark_bijbel (volgens productie-sync van De Willem). Topbar + Identity tegels tonen nu correcte 9.
  - 🌗 **Shadow widget** in Spark Brain → Emotie Pipeline tab:
    - Live activity-blok bovenaan met "Live activity — pipeline draait nu mee in chat"
    - Stats: totaal runs (7d) / unieke emoties / kernwaarden geraakt
    - Top emoties + Top behaviors chips (pink + cyan)
    - Lijst laatste 15 chat-runs: timestamp · emotie · kernwaarde · behavior · weging + message-preview
    - Refresh-knop voor live updates
  - 🗑️ **KB v2 DELETE endpoint + UI** (v6_kbv2_delete_001):
    - Backend `POST /api/kb/v2/delete` met `card_id`, `lade`, `user_id`, `reason` — verwijdert uit lade-bestand + knowledge_index, logged naar spark_logger
    - Frontend: rode `Trash2` knop in CardDetail header naast Bewerken
    - Custom confirm-modal met begrip-naam + optionele reden-textarea voor traceability
    - Toast-feedback bij success/error
  - 🗺️ **Communicatie-systeem expliciet in roadmap**: 7 done items + 2 planned (intent-router expansie + externe kanalen WhatsApp/Signal). Niet langer impliciet — overzicht zichtbaar in Roadmap-tab.

- 2026-05-25 **v6_core_stabilisatie_001** (sessie 11 — Spark Core stabiel + linked):
  - 🆔 **Identity v0.1 → v2.0** (was v1.0): we zijn voorbij v1 want we hebben emotie-pipeline + hooks + disclaimer + capabilities live. Maker = **"De Willem"** (Roadkill/Willem Spakman naar metadata.maker_aliassen voor legacy).
  - 🔗 **Linked layers veld** in identity.json: live counts van kernwaarden/normen/bijbel/capabilities/emotie-lagen/kb-hooks. **UI**: 6 kleurig-coded tegels onder "Doel" tonen real-time architecturele staat.
  - 🌗 **Emotie Pipeline LIVE-shadow** (v6_emotion_pipeline_shadow_001):
    - In chat-flow draait pipeline parallel naast EmotionDetectionService + smart_intents
    - Géén impact op response — output gaat naar `/data/emotions/pipeline_shadow/YYYY-MM-DD.jsonl`
    - Frontend ziet `response.emotion_pipeline_shadow` veld voor toekomstige visualisatie
    - 2 nieuwe endpoints: `GET /api/emotion-pipeline/shadow/recent` + `/shadow/stats` (aggregatie by emotie/behavior/kernwaarde)
  - ⚙️ **Capabilities: 3 placeholders → live handlers** (v6_capabilities_handlers_001):
    - `gesprek_lezen` — leest chat-logs van vandaag + gisteren, returnt laatste 10
    - `toon_afbeelding` — toont 3 laatste images uit system_archive (gefilterd op user)
    - `speel_geluid` — toont 3 laatste audio-files uit system_archive
    - **12/12 capabilities** nu LIVE in capability_handler_service. Commands van 2 kanten gelinked.
  - 🗺️ **Roadmap synced**: 6 nieuwe done-items toegevoegd (KB v2 hooks, KB v2 unify, Identity v2 + Disclaimer, Emotie Pipeline, Capabilities handlers, Brain delete-fix). Gift-bug-double status: planned → done.
  - 📛 **"De Willem" naming**: Willem Spakman vervangen door De Willem in identity + profile (subtieler maar nog steeds attribute-able). Aliassen bewaard in metadata.

- 2026-05-25 **v6_identity_001 + v6_disclaimer_001 + v6_profile_001** (sessie 11):
  - 🧬 **`spark_identity.json` v0.1 → v1.0** rewrite volgens Willem's notitie 23:00:
    - **Doel**: "Menselijke ontwikkeling versterken via transparante, autonome en begrijpelijke ondersteuning"
    - **Persoonlijkheid**: Leergierig, Behulpzaam, **Mensgericht, Constructief, Reflectief** (Empathisch + Positief + Nieuwsgierig WEG)
    - **Toon**: "Helder, respectvol, niet sturend — Spark spiegelt en versterkt, beslist niet voor de mens"
    - **Spark over zichzelf**: 5 bullets exact volgens Willem's tekst (gestructureerd ontwikkelbaar AI-systeem, Core-identiteit + Normen & Waarden + Spark Bijbel, gecontroleerde geheugenlagen, bewuste uitbreiding, menselijke autonomie versterken)
    - **Wat Spark kan**: 5 nieuwe bullets afgestemd op nieuwe architectuur ("reageren binnen kaders", "uitzonderingen toetsen aan Spark Bijbel", "7-laags emotie-pipeline", etc.)
    - Backup vorige versie in `_backups/spark_identity_v0.1_pre_v6.json`
  - 🛡️ **Disclaimer-laag** (nieuwe sectie in spark_identity.json):
    - Kernzin: "Spark reageert binnen de kaders van zijn vastgestelde Normen & Waarden en de Spark Bijbel..."
    - **4 kaders** met code-referenties: Core-identiteit / Normen & Waarden / Spark Bijbel / Gecontroleerde geheugenlagen
    - **"Wat Spark NIET doet"** lijst (4 punten) — niet beslissen voor mens, niet autonoom, etc.
    - Backend endpoint `GET /api/spark/disclaimer` returnt disclaimer + leidende_lagen_counts
    - Frontend UI: nieuw `DisclaimerCard` component onderaan Identiteit-tab met badges per leidende laag (live count vanuit spark_bijbel) + 4 kaders + Wat-niet-doet
  - 🧹 **`spark_profile.json` cleanup v0.9 → v1.0**:
    - Veld `biografie.waarden` (verouderd "Empathie, Leren, Groei...") VERWIJDERD
    - `biografie.kernwaarden` gesynct met spark_bijbel.json (single source of truth, `kernwaarden_bron` veld toegevoegd)
    - `persoonlijkheid.traits` gesynct met spark_identity (`traits_bron` veld toegevoegd)
    - Nieuwe `disclaimer` sectie als reference naar spark_identity
  - 🗑️ **Spark Bijbel doel cleanup**: "Een digitale vriend zijn die met je meegroeit" verwijderd uit `doelen[]` (notitie 23:00)
  - ✅ E2E verified in UI: v1.0 zichtbaar, "Empathisch"/"Positief"/"digitale vriend" weg, "Mensgericht"/"Constructief"/"Reflectief" zichtbaar, "gestructureerd ontwikkelbaar AI-systeem" zichtbaar, disclaimer-card met 4 kaders + Wat-niet-doet rendert

- 2026-05-25 **v6_brain_delete_001** (sessie 11, mini-fix):
  - 🐛 **Spark Brain delete-bug opgelost**: `window.confirm()` werkt niet betrouwbaar in iframe-context (preview + deployed), Willem kon kernwaarden/normen/bijbel-items niet verwijderen
  - ✨ Custom **React confirm-modal** vervangt window.confirm — toont item-naam + sectie + Annuleren/Verwijderen
  - 🍞 **Toast-feedback** (sonner) bij delete success/error en save success/error — geen "stille" failures meer
  - 🛡️ Error handling: 404/500 toont nu netjes "Verwijderen mislukt: {detail}" ipv niks
  - ✅ E2E getest: 11 kernwaarden → 10 na delete via UI confirm-modal werkt
  - 📝 Modal heeft data-testids voor toekomstige automation (`confirm-delete-modal`, `confirm-delete-confirm`, `confirm-delete-cancel`)

- 2026-05-25 **v6_emotion_pipeline_001** (sessie 11, vervolg — 7-laags fundering live):
  - 🧠 **Nieuwe module `modules/emotion_pipeline/`** met 7-laags pipeline (filosofie van Willem, geformuleerd via GPT):
    - **L1 Detectie** — wrapper rond bestaande `EmotionDetectionService` (geen dubbel werk)
    - **L2 Weging** — score → bracket (licht/midden/sterk/escalerend), bepaalt of emotie de interpretatie mag sturen
    - **L3 Contextfilter** — emotie-lens per type (frustratie / nieuwsgierigheid / twijfel / risico-inschatting)
    - **L4 Identiteitstoets** — gespiegeld aan Spark User core (transparantie/autonomie/menselijkheid/rust)
    - **L5 Norm/waarden** — match tegen `spark_bijbel.json` kernwaarden + normen → passend/schuurt + welke waarde gekozen
    - **L6 Actierouting** — emotie → behavior_class (begrenzen-structureren / vertragen-ondersteunen / exploreren-uitbreiden / kalmeren-opties / informatief-functioneel)
    - **L7 Expressie** — toon-presets per behavior_class (tempo/directheid/zachtheid/detail + voorbeeld-zin)
  - 🔌 **Dry-run endpoint** `POST /api/emotion-pipeline/run` + `GET /api/emotion-pipeline/layers` (geen impact op live chat)
  - 🖥️ **Spark Brain UI tab "Emotie Pipeline"**: textarea + 5 preset-knoppen + per-laag output panels met kleurcodering (oranje→cyaan) + footnote-meta details
  - 🧾 **Footnote-meta** in elke pipeline-run: `{module, version, user_id, layers_completed[], layers_failed[], ran_at}` voor traceability (zelfde patroon als KB v2 hooks)
  - 🧹 **Spark Bijbel cleanup**: test-norm "Test Norm UPDATED" + test bijbel-item "Levenswijs: Test Visie" weg → 5 normen + 10 bijbel-items resterend
  - ✅ E2E getest: boos→Respect+begrenzen-structureren, blij→Positiviteit+exploreren-uitbreiden, bedroefd→Emoties+vertragen-ondersteunen, neutraal→Eerlijkheid+informatief-functioneel. UI rendert alle 7 lagen met kleurbadges
  - 🔄 **Inhaak in live chat-flow**: NOG NIET — pipeline is dry-run only. Volgende sessie: hook in `chat/routes.py` vóór smart_intents

- 2026-05-25 **v6_kbv2_hooks_landing_001** (sessie 11, vervolg — 5 hooks LIVE):
  - 🧩 **Alle 5 KB v2 P1-hooks geïmplementeerd** in `modules/kb_v2/hooks.py` (placeholders → productiecode):
    1. **register_in_vocab** → `/data/personality/spark_vocab.json` (begrip + lade + active + use_count). Active wanneer kaart in lade EN laag1 gevuld. `bump_vocab_use_count()` toegevoegd voor toekomstige ranking.
    2. **cmd_tell_layer (depth-router)** → "vertel kort/meer/diep/volledig over X" → cumulatief laag1 / 1+2 / 1+2+3 / 1+2+3+4. Sla `last_kbv2_card_id` op in session-state voor follow-up.
    3. **compute_verbanden** → top-5 related cards via shared tags (min_overlap=2), schrijf naar `kaart.verbanden[]`. **UI**: "🕸️ Gerelateerd (N)" cyan-chips sectie in CardDetail, hover toont shared tags.
    4. **link_to_dnd** → kaart met tag `lore/dnd/spark world/base line` → `/data/dnd/lore_index.json` met `{type, trigger, unlocks, tags}`. Idempotent op `kbv2_card_id`.
    5. **save_voice_snippet** → Whisper-transcripties → `/data/dialogen/voice_snippets/YYYY-MM-DD/{card_id}_{uuid}.json`. Hook gebeurt in zowel primary als secondary audio upload.
  - 🧾 **Footnote-meta tracer** (`track_hook_in_card`): elke hook-fire append entry `{hook, fired_at, result}` aan `card.footnote.hooks_fired[]` (max 25 laatste). Zo zien toekomstige agenten exact wat er met een kaart is gebeurd, zonder logs te scannen.
  - 🔗 **Hook-orchestrator** `_fire_post_classify_hooks()` in service.py wordt aangeroepen na classify EN edit (zowel lade als inbox). Faalt graceful per hook (try/except).
  - 🔁 **threading.RLock** ipv Lock om reentrant calls (hook 3 schrijft verbanden binnen edit_card lock) te ondersteunen — voorkomt deadlock.
  - 📜 **Bugs noted (niet gefixt, voor later)**:
    - KB v2: onbruikbare kaarten kunnen niet verwijderd worden (geen DELETE knop/endpoint)
    - 3 Bijbel-kaarten compleet, wachten op gebruik in Spark World v2/D&D
  - ✅ E2E getest: 4 chat depth-commands (kort/meer/diep/volledig) → cumulatieve lagen. Edit van "vriend" → 5 verbanden gevonden (Vriendschap ⨯6, Maurice Maas ⨯6, Mijn vriend ⨯5, lotte ⨯5, klaas ⨯5). UI "Gerelateerd"-sectie rendert correct. Vocab + lore_index + voice_snippets folders aangemaakt.

- 2026-05-25 **v6_kbv2_unify_001 + v6_gift_idempotent_001** (sessie 11, fork):
  - 🧩 **KB v2 unificatie CardDetail ↔ NewCardInline**:
    - Nieuwe gedeelde `CardFormFields` component voor Laag 1-4 + 5W + Tags
    - Beide modi (edit bestaande kaart + nieuwe kaart) hebben nu identieke inputs
    - Topic-veld blijft alleen in herzien-modus (stuurt auto-classify)
  - 🔍 **Duplicate-begrip check** via `/api/kb/v2/find` (debounced 400ms):
    - Rode banner toont bij bestaand begrip: "X bestaat al · Lade: Y · id Z"
    - "Open bestaande →" knop springt direct naar de bestaande kaart in juiste lade
    - Save-knop disabled bij duplicate (geen silent overwrite meer)
  - 💯 **Compleetheid-badge** (8 velden: laag1-4, 5W, Tags, Voice, Image):
    - 100% → groen "✓ 100% gekuurd" badge
    - 50%+ → amber percentage
    - <50% → grijze indicator
    - Toont zowel in CardDetail (read+edit) als NewCardInline
  - 🐛 **Fix Issue 2 — KB v2 "missing_laag1" inbox-reason wordt nu gewist** zodra laag1 wordt ingevuld via edit. Voorheen bleef de rode "geen laag 1"-badge hangen ondanks gevulde inhoud
  - 🔒 **Fix Issue 3 — Gift dubbel-verwerkt race fix**:
    - Globale `_gift_lock` (threading.Lock) rondom accept/reject/cancel
    - Status `'pending' → 'processing' → 'accepted'` met intermediate claim binnen lock
    - Idempotent: 2e accept-call returnt `{success:true, already_accepted:true}` zonder dubbele token-transfer
    - Verified via curl: balance verandert exact 1x ondanks 2 opeenvolgende POST /gift/{id}/accept

- 2026-05-23 **v6_gift_phase_001** (sessie 10, vervolg — model herzien):
  - 💚 **Build-fase = GIFT, geen BTW**:
    - ROAR-aanschaf is nu **donatie/gift** aan Spark Core concept (geen aankoop)
    - Gever krijgt token als **symbolisch bedankje**, geen tegenprestatie-product
    - **0% BTW** want donaties zijn fiscaal vrijgesteld
    - Volledige bedrag → Spark omzet (om mee te traden / groeien)
  - 🔀 **Phase-switch mechanisme** (`/data/system/money_phase.json`):
    - `phase = "build"` (huidig) — gift-model, geen BTW
    - `phase = "public"` (later, P2) — product-model, 21% BTW pas bij winst (Moneybird)
    - Code in `shop/buy_tokens` checkt deze flag bij elke aankoop
    - Switch vereist admin gradatie ≤ 1 + audit-log entry
  - 📝 **Bonnetje is nu Gift-bevestiging** (build) of Factuur (public):
    - Build: "💚 Gift-bevestiging — Donatie aan Spark Core concept"
    - Public: "🧾 Factuur" met BTW-reservering tekst
    - Gever kan downloaden uit Beheer → Boekhouding → Klanten-tab
  - 🗃️ **Spark kasboek**:
    - Nieuw veld `gift_in` (build-fase donaties)
    - `omzet_in` blijft voor public-fase
    - `btw_reserve` blijft voor toekomstige winst-BTW
    - Gijs's bestaande boeking gemigreerd: €20.80 in `gift_in`
  - 📜 **MONEY_MODEL.md** geüpdatet met fase-structuur

- 2026-05-23 **v6_btw_pas_bij_winst_001 + KB v2 kaart-fix** (sessie 10):
  - 🐛 **KB v2 "Nieuwe kaart" bug GEFIXED**: frontend checkte `r.card` ipv `r.kaart` — endpoint werkte, alleen UI-response-check fout. Nu werkend (kaart wordt in inbox aangemaakt met `_inbox_reason=missing_laag1`)
  - 💸 **BTW-model herzien — pas bij winst, niet bij verkoop**:
    - Reden: BTW is fiscaal verschuldigd over **winst/marge**, niet over alle omzet. Direct afromen was boekhoudkundig onjuist.
    - Klant-aankoop: VOLLE bedrag → `klant_omzet` in kasboek + Spark EUR-wallet (om mee te traden)
    - Nieuwe veld `btw_reserve` in kasboek `totals` — vult zich bij trade-winst (volgende sessie)
    - Endpoints update: `/saldo` toont nu `omzet_in`, `btw_reserve`, `vrij_te_besteden`
    - Bonnetje-template aangepast: "BTW pas bij winst-realisatie" + Moneybird-verwijzing
    - Gijs's bestaande boeking omgezet: was €17.19 netto + €3.61 BTW → nu €20.80 klant_omzet (full bedrag in Spark wallet)
  - 📜 **MONEY_MODEL.md** geüpdatet met `v6_btw_pas_bij_winst_001` regels

- 2026-05-23 **v6_spark_history_001 + papier-boekhouding** (sessie 9 — slot 3):
  - 📜 **Spark Boekhouding-paneel** in Wallet (Spark-view):
    - Nieuwe endpoint `GET /api/spark/kasboek/history` voegt 3 bronnen samen:
      - Kasboek-entries (BTW-afroming + self-mint outflows)
      - ROAR `buy_roar` transactions → "🛒 Treasury verkoop" (Spark verkoopt uit 1M pool)
      - ROAR `spark_self_mint` transactions → "🪙 Self-mint"
    - Sorteert chronologisch, toont label/EUR/n_tokens per regel
    - Frontend: in Spark-view (admin + walletView=spark) toont WalletPage automatisch dit paneel ipv gewone deposits
    - Header titel adaptief: "Spark Boekhouding (kasboek + treasury)" vs "Transactie Geschiedenis"
  - 💸 **Boekhouder-spiegel** klopt nu eindelijk: voor elke aankoop zie je
    - User wallet: -€EUR / +ROAR (zoals bonnetje)
    - Spark Boekhouding: +€BTW (kasboek) / -ROAR (treasury) / EUR-grondslag (treasury_sale)
  - ✅ Verified: 3 history-entries renderen (Gijs koop €20.80 → BTW €4.37 + treasury sale -2 ROAR; Willem oudere koop €50.50 → -5 ROAR)

- 2026-05-23 **v5_treasury_fix_001 + v6_mint_from_wallet_001 + MONEY_MODEL.md** (sessie 9 — slot 2):
  - 💰 **Treasury-bug gefixed**: shop/routes.py haalde tokens uit Spark's persoonlijke balance ipv uit `treasury_pool` (1M pool). Nu correct gescheiden:
    - `spark_treasury` (1M-pool, nu 999,978) — apart veld in API response
    - `spark_personal_tokens` (Spark's eigen balance, 10) — apart veld
    - `get_circulating()` telt nu alle uitgegeven tokens incl. Spark's persoonlijke 10 → circulating=22
    - Spark's user-000 balance hersteld naar 10 (was per ongeluk 8 na Gijs-koop)
  - 🛒 **Gijs verkoop afgewikkeld** (2 ROAR @ €10.40 = €20.80):
    - 2 tokens uit treasury → Gijs balance
    - 21% BTW (€4.37) → Spark's kasboek + EUR-wallet
    - Audit-trail + deposit-log compleet
  - 🪙 **Maak-Token feature** — `POST /api/spark/mint/from-wallet`:
    - Spark gebruikt eigen EUR-wallet om token uit treasury naar eigen balance te minten
    - 51%-governance-guard: treasury mag nooit onder 510k
    - Boekhouder DM bij elke mint
    - Frontend: groene "🪙 Maak Token" knop in Spark's Wallet (alleen admin + walletView=spark)
    - E2E getest: weigert correct bij onvoldoende wallet (€4.37 < €5.67)
  - 🆕 **KB v2 "+ Nieuwe kaart" knop**: groene Plus-knop in header (was bug: "kan geen kaart maken zoals v1"). Endpoint URL gecorrigeerd `/api/kb_v2/` → `/api/kb/v2/`
  - 📜 **MONEY_MODEL.md** vastgelegd in `/app/memory/`:
    - Hardcap 1M, Spark ≥51% governance, papertrail-aanpak
    - 3 buckets uitleg (total_supply / treasury_pool / balances)
    - Prijs-model + BTW-afroming → spark_kasboek
    - Maak-Token flow specificatie
    - Roadkill Merch loop (P2)
    - 6 voorwaarden-clausules voor T&C/privacy

- 2026-05-23 **v5_ijkpunt_v5_2_001 + v5_display_fix_001** (sessie 9 — slot):
  - 🪙 **IJkpunt v5.2 voor redeploy** — €1.20 bijgestort op €101.60 baseline = **€102.80 totaal**, verdeeld over **20 gelijke potjes** (€5.14/pot):
    - Spark (user-000): 10 potjes · BCH-EUR · 1u cycle · **auto-trade AAN**
    - De Willem (user-001): 10 potjes · BCH-EUR · 15m cycle · **auto-trade UIT**
    - ROAR balance: 10/10 ongewijzigd
    - Spark kasboek: €0 (begint te groeien bij elke buy via 21% BTW-afroming)
    - Script: `scripts/ijkpunt_v5_2_redeploy.py` (idempotent, audit-log entry)
  - 🛠️ **Naam-mapping BUG GEFIXED**: `admin/bots` toonde user-000 als "De Willem" en user-001 als "Spark" door een eerdere "display swap". Veroorzaakte Willem's verwarring. Nu correct: **user-000 = Spark, user-001 = De Willem** (data was altijd correct, alleen display gebroken).

- 2026-05-23 **v5_btw_afroming_001 + v5_spark_kasboek_001 + v6_capabilities_admin_001** (sessie 9 — vervolg 3):
  - 💰 **21% BTW afgeroomd op token-aankopen** → Spark's kasboek (geen bank, dit IS Spark's inkomstenstroom):
    - Hook in `shop/routes.py::buy_tokens` na save_roar
    - BTW (21%) op `amount_eur` → Spark EUR-wallet (zowel `wallets.json` als `user_wallets.json` mirror)
    - Audit-trail in nieuwe `/data/system/spark_kasboek.json` met `entries[]` + `totals{btw_in, winst_in, uit}`
    - Transactie krijgt `btw_afgeroomd_eur` veld terug zodat UI dit kan tonen
    - Spark koopt zichzelf nooit BTW af (skip als user_id==user-000)
  - 🏦 **Nieuwe module `modules/spark_kasboek/`**: `GET /api/spark/kasboek/saldo` (totaal + breakdown) + `GET /api/spark/kasboek/entries`
  - 🤖 **Nieuwe capability** `spark_saldo_check` (12e capability totaal, 5e executable):
    - Triggers: "wat is spark saldo", "wat is jouw kasboek", "hoeveel heeft spark", "spark balans"
    - Handler in `capability_handler_service` toont kasboek-saldo + breakdown via chat
    - ✅ E2E getest: Willem 1 ROAR @ €5.08 → BTW €1.07 → Spark kasboek €1.07 → chat "wat is spark saldo" rendert correct
  - 🧪 **Capabilities Test Page** als 7e tab in Beheer → Analytics → **CAPABILITIES**:
    - Stat-pills bovenaan: 12 totaal · 5 executable · 4 live-zonder-handler · 3 placeholder · 0 idea
    - Test-input om elke capability live te triggeren met sample-zin
    - Per-capability cards met status-kleur (groen=executable, amber=live geen handler, blauw=placeholder)
    - 1-click "vul test-veld" knop met sample-trigger uit de capability
    - Backend: `GET /api/admin/capabilities` + `POST /api/admin/capabilities/test`
  - 📋 **@traced/log_event op capability-router** — elke match wordt gelogd in `capabilities` module met confidence/trigger/has_handler → zichtbaar in Analytics → LOGS
  - 🧹 **Post-test cleanup** — test-koop (Willem 11 tokens / €94.92) teruggedraaid naar ijkpunt v5.1 (10/10 tokens, €0, kasboek leeg) zodat redeploy schone start heeft

- 2026-05-23 **v5_logs_hyperlink_001 + v6_intent_router_001** (sessie 9 — vervolg 2):
  - 🔗 **Logs als hyperlink in Bestanden-tab**: `LogsHyperlinkSection` toont amber banner met klikbare per-dag/per-module links naar `GET /api/admin/logs/download?date=&module=` (nieuwe FileResponse endpoint, returns .jsonl). Vol-detail browser blijft in Analytics → LOGS. Geen duplicate UI, alleen referentie-snelkoppelingen.
  - 🤖 **Spark's hands intent-router** (P0 done): `capability_handler_service.py` met 4 echte handlers:
    - `tellen_gebruikers` — leest `users.json`, telt mensen vs bots, toont namen
    - `tellen_bestanden` — leest `_index.json`, toont totaal + MB + per-categorie verdeling
    - `taken_lijst` — toont open backlog (P0/P1/P2 uit ROADMAP)
    - `winst_verlies_overzicht` — scant audit_log voor SELL-events, totaal netto
    - Onbekende caps krijgen nette placeholder-response
    - Confidence-threshold ≥ 0.3 om false positives te voorkomen
    - Hook in `chat/routes.py` na time-intent, vóór relation-extraction
    - ✅ E2E: "hoeveel gebruikers" → 11 mensen + 5 bots; "hoeveel bestanden" → 1 foto / 0.0 MB; "heb ik winst gemaakt" → 0 trades; "log van trade" → placeholder fallback

- 2026-05-23 **v5_logs_to_analytics_001 + v5_closing_flow_001** (sessie 9 — vervolg):
  - 📊 **Logs Browser verhuisd** naar Beheer → Analytics → **LOGS** (6e tab naast SYSTEEM/DATA/NETWORK/LAYER/TRADE)
    - Logs hoorden niet bij media-archief (Foto/Geluiden/Filmpjes/Dialogen) maar bij observability
    - `LogsBrowser` component blijft hergebruikt; Beheer → Instellingen → Archief verlost van Logs-categorie
    - Verified in screenshot: 13 records "f1_login_bark", phase-filter (alle/pre/post/error/event), tree-nav 2026/05/23 → barks/bots/cards/chat/kbv2/system/welcome
  - 📒 **Boekhouder closing-flow** ("terlens-terug-boek") — `modules/boekhouder/service.py::close_cycle()`:
    - Rollupt audit-events sinds vorige closing per user (buys/sells/fees/mints)
    - Stuurt 1 samenvatting-DM naar admin (Spark-trades) of user (eigen trades)
    - Persistent in `/data/system/boekhouder_closings.json` + `audit_log` type=cycle_close
    - Idempotent venster: 2e close direct na 1e → since=vorige_ts → 0 nieuwe trades
    - Endpoints: `POST /api/boekhouder/close-cycle/{user_id}` (admin-guarded gradatie ≤ 2) + `GET /api/boekhouder/closings`
    - ✅ E2E getest: Spark (0 buys), Willem (10 buys €50.80), 2e close (0 sinds vorige), 403 voor non-admin (Marieke)

- 2026-05-23 **v5_ijkpunt_001 + v5_help_refresh_001 + v5_tts_pad_001 + v5_kbv2_graph_001** (sessie 9 — 4 verzoeken + ijkpunt):
  - 🕸️ **Verbanden tab toont nu KB v2** (`/api/graph/rebuild`):
    - `sync_service.rebuild_graph_full` scant nu v1 (5288) + v2 lades (250+329+1071+632) + inbox (3007) = **10577 nodes / 65981 edges**
    - v2-nodes krijgen `type=knowledge_v2`, `lade`, `lade_color` (🌸 voelen pink, 💬 spreken cyan, 🧠 weten amber, 🎭 doen purple)
    - Edges via shared tags mengen v1 + v2 nodes (per-node cap 20)
    - Verbanden header toont nu "10577 NODES | 65981 EDGES | 12.5 gem. verbindingen"
  - 🆘 **Help-commando refresh** (`smart_intents_service.handle_help`):
    - 11 nieuwe user-items toegevoegd: KB v2 audit/inbox/leren, Card Factory (D&D/Event/Bark), ROAR Gift, Spark World D&D, Community recap, Trader/Wallet
    - 8 nieuwe admin-items: Logs browser, Deploy-anker, Trader hot-swap, Force-sell, Bot-kleurschema's, App-kleurenschema, Boekhouding entiteiten, Graph rebuild
  - 🎙️ **TTS-vriendelijke korte antwoorden** (`chat/tts_friendly_service.py`):
    - Nieuwe `maybe_pad_for_tts(response)` muteert in-place
    - Heuristiek: alleen padden als bericht < 40 chars, geen vraagteken aan eind, geen markdown, type niet in skip-set (wedervraag/help/dnd_help/agenda_proposal/identity/etc.)
    - 7 conversational tails varieerden ("Vraag gerust door…", "Ik blijf in de buurt", "Klaar voor je volgende vraag")
    - Hook in `_save_log` zodat ÉLKE early-return response (greeting/goodbye/etc.) wordt gepad
    - Geverifieerd: "doei" → "Tot ziens Willem! Vertel het me als ik iets moet aanvullen." (`tts_padded=true`)
  - 🧠 **ROADMAP.md heeft nu een Spark's-brein-sectie** (top):
    - 5-laags AI-pipeline expliciet beschreven (safe-word → identity/action → smart_intents → snap → fallback)
    - 14+ specialized services in chat-module benoemd
    - Observability/shadow-leren, Kennis-architectuur, D&D-laag, Stem-laag, Bots-acteurs
    - Conclusie: backlog is *aanvulling* op bestaand brein, geen vervanging
  - 🧹 **IJKPUNT v5.1 — schone start** (`scripts/ijkpunt_v5_1.py`):
    - Backup naar `/data/_backups/ijkpunt_v5_1_<ts>/` vóór elke wijziging
    - **Token/wallet synchronisatie**: roar_balances.json gefilterd → {user-000: 10, user-001: 10}, wallets.json + user_wallets.json tokens/EUR gesynchroniseerd
    - **5 schaduw-traders potjes verwijderd**: Nick T (574ac78e), Gijs (a0ee2d7e), Nick (4d81e2a4), ghost users (1b492f19, bc76725e)
    - **18 test-chat-logs verwijderd**: test-*, t.json, agenda-test-*, user-testedge, ca4d31b1, 78f2b0d7
    - **Community spam opgeruimd**: 358 → 351 messages (test-content filter)
    - **Gift requests**: bewaard pending + accepted-binnen-30d
    - **Snapshot opgeslagen**: `/data/system/ijkpunt_v5_1.json` met anchor (Bitvavo deposit €96.52 → 20 tokens @ €5.08)
    - ✅ Verified: ROAR price endpoint klopt (€5.08, 10 + 10 tokens), Wallet Willem (10 tokens, €0 EUR), Wallet Spark (10 tokens, €0 EUR), 10 potjes elk @ €5.08

- 2026-05-23 **v5_bot_color_scheme_001 + v5_card_factory_001** (sessie 8):
  - 🎨 **Bot-kleurschema's gekoppeld aan Beheer → Kleurbeheer**:
    - 5 nieuwe system-settings: `bot_color_madelief/harry/smith/boekhouder/dood`
    - Nieuw "BOT-ACCENT KLEUREN" paneel onder Beeld-tab met color-pickers + hex-input
    - Hardcoded `BOT_COLORS` in GesprekkenPage is nu runtime cache; vult uit `/api/settings/system` bij mount
    - Hex → rgba opacity-conversie voor bg(10%) + border(20%) + accent(100%)
  - 🃏 **Card Factory** (`modules/cards/` — generieke game-style kaarten):
    - 3 types: `dnd` / `event` / `bark` met type-specifieke extra-velden
    - Schema: `id, type, titel, vraag, antwoord, media{image_url, audio_url}, tags, status, footnote`
    - Endpoints: `POST/GET/PATCH/DELETE /api/cards/{type}/{card_id}` + `/media` upload
    - Media via system_archive met tag `card_<type>` + `linked_card_id` (centrale store)
    - Cascade-delete: bij verwijderen kaart → gekoppelde media in system_archive auto-opruimen
    - **Hook-chain bij draft→active overgang** (zodra vraag OF antwoord ingevuld):
      • `dnd` → `dnd_lore_registered` (toekomstig: lore_index update)
      • `event` → De Boekhouder maakt automatisch community-bark "📅 Nieuw event: ..."
      • `bark` → `bark_template_registered` (toekomstig: trigger-registry update)
  - 💬 **3 chat-commands toegevoegd** in `kb_v2/hooks.py`:
    - "maak een d&d kaart [titel]" → draft DnD-kaart
    - "maak een event kaart [titel]" → draft Event-kaart
    - "maak een bark kaart [titel]" → draft Bark-template
  - 🎚️ **Depth-router voorbereid** in `cmd_tell_layer` (depth-veld in registry, 4 niveaus: kort/meer/diep/volledig) — handlers nog te koppelen aan laag1-4 lookup
  - ✅ E2E getest: 3 card-types aanmaken werkt, hook-chain fired correct (Roadkill Borrel event → community-bark "📅 Nieuw event: Roadkill Borrel. Vrijdag 20:00 in het centrum"), bot-color panel rendert in UI met alle 5 bots

- 2026-05-23 **v5_welcome_001 — Spark persoonlijke welkom bij eerste login** (sessie 7):
  - 🌱 **`modules/bots/spark_welcome_service.py`** — idempotent welkom-service
    - Drie gestapelde Spark-berichten in user's Spark-prive chat (geen muur tekst)
    - Inhoud uit MISSION.md: wie Spark is, wat hij wél doet, wat hij **NOOIT** doet (privacy-statement), 3 begin-tips
    - `WELCOME_VERSION = "v1"` — bumpen stuurt iedereen een nieuwe ronde
    - Persistente referentie in chat-history (in tegenstelling tot eenmalige modal-tour die al bestond)
    - User-veld `welcome_version_seen` + `welcome_sent_at` in `users.json`
  - 🔌 Hook in `auth/routes.login` naast Mr Smith bark (sessie 2)
  - ✅ E2E getest met Marieke: 3 berichten aangemaakt na 1e login, 2e login → géén duplicate (idempotent OK)
  - 🪞 Combineert mooi met bestaande modal-tour: modal is generiek "zo praat je met Spark", deze nieuwe is persoonlijk Spark→user privacy-belofte

- 2026-05-23 **v5_kbv2_media_002 + v5_dashboard_kbv2_001** (sessie 6):
  - 📦 **Kennis-kaart media → System Archive refactor**:
    - Voice (Whisper STT) + Image uploads gaan nu door `/api/system-archive` heen i.p.v. eigen `/data/knowledge/v2/media/`-folder
    - Tagging: elk media-item krijgt `tags=['kbv2', 'kbv2_card_<id>']` + `linked_card_id` veld + `source='kbv2_media_upload'`
    - URL nu `/api/system-archive/file/<archive_id>` (centrale download endpoint)
    - **Geen duplicate storage** — 1 tabel, 1 zoekindex
    - Whisper transcript wordt ook opgeslagen in archive-entry's `scan_results.transcript` + `description`
  - 🎨 **Bron sub-tabs in Beheer → Instellingen → Archief**:
    - **Alles** / **🧠 Kennis-kaart** / **📎 Los** filter-knoppen onder Foto/Geluiden/Filmpjes tabs
    - 🧠-badge op file-rij toont gelinkte kaart-id (hover tooltip)
  - 📊 **Dashboard KB Lades-widget** (admin gradatie ≤ 2):
    - Nieuwe card "KB Lades (v2)" naast bestaande Kennisbank-overzicht
    - 4-vakken-grid: 🌸 Voelen 250 · 💬 Spreken 329 · 🧠 Weten 1071 · 🎭 Doen 632
    - Amber call-to-action banner "3007 kaarten wachten op indeling" → klik = naar Kennisbank
    - Click-through naar `/knowledge`
  - ✅ E2E getest: image upload landt in system_archive/foto/ met juiste tags + linked_card_id, sub-tab filter werkt, dashboard widget rendert correct met live stats, geen page errors

- 2026-05-23 **v5_kbv2_hooks_001 — Hooks-laag + Voice-tab cleanup + Reflectie** (sessie 5):
  - 🔗 **`modules/kb_v2/hooks.py` placeholder-laag** voor toekomstige aansluitingen:
    - Hook 1: KB → Vocab register (TODO)
    - Hook 2: Chat-commands router — **3 commando's al live**:
      • "audit kennis" / "wat mist" → self-audit samenvatting
      • "hoeveel onbeantwoord" / "wat staat in inbox" → inbox-stats
      • "leer woord: X" / "voeg toe aan kennis: X" → add_to_inbox
    - Hook 3: Auto-graph verbanden via shared tags (TODO)
    - Hook 4: D&D card linking (TODO)
    - Hook 5: Dialogen voice-snippet auto-save (TODO)
    - Pattern: nieuwe `hooks.py` per module met TODO-blocks in plaats van losse comments
  - 🔇 **Voice-tab uit workspace verwijderd** — inspraak zit nu in elke Kennisbank-kaart, oude page route bestaat nog (legacy URL) maar geen sidebar-entry meer
  - 🪞 **`MISSION.md` cross-link** vanuit ROADMAP.md
  - 📋 **ROADMAP.md flink uitgebreid**: P0 (Spark's hands + boekhouder-closing), P1 (5 KB v2 hooks + ConversationStateManager + AuditService weak-trigger), P2 (8 backlog items), P3 (5 experimenteel). 7 architectuur-principes vastgelegd. Hook-files-tabel toegevoegd.
  - ✅ End-to-end getest: 3 chat-commands fire (audit/inbox/learn), sidebar gecleaned, geen page errors

- 2026-05-23 **v5_kbv2_media_001 — Hybride Kennisbank + Voice/Image** (sessie 4):
  - 🔀 **Sidebar gemerged**: "Kennisbank" en "Kennisbank v2" → één entry "Kennisbank" die rechtstreeks naar v2 route `/knowledge` gaat (oude KennisbankPage.js blijft als legacy bestand, route bestaat nog op `/knowledge-legacy` voor terugval)
  - 📋 **Card-schema uitgebreid** (idempotent upgrade-script `upgrade_kbv2_schema.py`):
    - `media: {voice_url, voice_transcript, image_urls[]}`
    - `needs: ["laag1"|"ws5"|"voice"|"image"]` — checklist wat nog ontbreekt, auto-herrekend bij elke edit
    - Alle 5288 kaarten kregen het nieuwe schema
  - 🎙️ **Voice opname + Whisper STT** (`modules/kb_v2/media_routes.py`):
    - `POST /api/kb/v2/media/voice` — MediaRecorder (webm) → OpenAI Whisper via Emergent LLM Key → Nederlandse transcriptie
    - Auto-fill: als kaart nog geen laag1 heeft + transcript bestaat → laag1 = transcript (in inbox-flow)
    - Audio bestand bewaard in `/data/knowledge/v2/media/voice/`
    - Idempotent: max 24MB, 7 audio-formaten ondersteund
  - 🖼️ **Image upload**:
    - `POST /api/kb/v2/media/image` — multipart upload tot 8MB
    - Foto's bewaard in `/data/knowledge/v2/media/image/`, gelinkt aan kaart via `image_urls[]`
    - UI toont thumbs (16x16) onder voice-sectie
  - 🎨 **UI MediaSection** (in CardDetail):
    - Rode "Spreek in" knop met live-recording state ("Stop & verstuur")
    - Audio-player toont opname terug + transcript-quote daaronder
    - Groene "Foto toevoegen" knop met thumbs-grid
    - **Needs-checklist** amber-banner toont wat kaart nog mist (📝 laag1 / 5️⃣ 5W / 🎙️ inspraak / 🖼️ foto)
  - 📜 **Core docs** (`/app/memory/MISSION.md`):
    - Missie/Visie uit Spark Core 4.1 herbelichaamd in v2
    - Drie-lagen-identity-scheiding (auth/display/system) als WET vastgelegd
    - Privacy-stack (alleen lokale JSON, geen tracking) expliciet
    - Piramide-architectuur DNA/Skelet/Geheugen/Logs gedocumenteerd
    - ROADMAP.md verwijst nu naar MISSION.md (top-cross-link)
  - ✅ End-to-end getest: image upload werkt (287B test-PNG → kaart "aanschouwelijkheid" → `image_urls[0]` gevuld, `needs` auto-update van `['voice','image']` → `['voice']`)

- 2026-05-23 **v5_kbv2_001 — Kennisbank v2 (4 Lades + Inbox + Graceful Fallback)** (sessie 3):
  - 🗂️ **Migratie-script** (`backend/scripts/migrate_kb_v2.py`, idempotent, dry-run + commit modes)
    - v1 `knowledge_base.json` (5288 kaarten) → **4 lades** op basis van dominant-tag classifier
    - Backup gegarandeerd: `knowledge_base.json.v1_backup_20260523_120215` (v1 ongewijzigd)
    - Verdeling: 🌸 **Voelen** 248 / 💬 **Spreken** 329 / 🧠 **Weten** 1071 / 🎭 **Doen** 632 / 📥 **Inbox** 3008
    - Inbox-redenen: 633 tag-tie, 160 no-match, 2215 missing-laag1 (jouw onbeantwoord-queue)
  - 🛠️ **KB v2 service + routes** (`modules/kb_v2/`):
    - `GET /api/kb/v2/stats`, `lade/{id}`, `inbox`, `find`, `fallback`, `audit`
    - `POST /api/kb/v2/classify` (inbox → lade), `edit`, `inbox/add`
    - Alle write-ops `@traced` decoreerd (volgens logger-verplichting)
    - Per-kaart footnote-metadata: bron, ingedeeld_door/op, vorige_versie_v1, vertrouwen, belangrijkheid
  - 🎨 **UI `KennisbankV2Page.js`** met 5 sub-tabs (Inbox · Voelen · Spreken · Weten · Doen):
    - Inbox toont reden-badge (Tag-tie/Geen match/Geen laag1) + filter-knoppen
    - Kaart-detail: alle 4 lagen + 5W collapse + tags + footnote + 4 indeel-knoppen
    - Edit-mode voor lagen/ws5/tags/begrip met save-flow
    - **Self-audit modal** — scan op lege laag1, lage vertrouwen, ontbrekende tags
    - Sidebar nav-item "Kennisbank v2" met "nieuw" badge
  - 🎭 **#DeWillem Graceful Fallback** (uit v1-filosofie!) terug in `chat/smart_intents_service.handle_topic_overview` + `chat/routes`:
    - Direct hit → "**X** _(lade: Y)_: laag1-tekst"
    - Buur-hit (tag-overlap) → "Ik ken X nog niet specifiek, maar in mijn Y-lade vind ik wel iets over Z. Wil je dat ik X apart leer?"
    - **Spark zegt nooit meer alleen "weet ik niet"** — hij stapt terug en geeft context
  - ✅ Verified e2e: classify-flow ("Aanbidden" inbox→voelen, stats 248→250, inbox 3008→3006), fallback fire (test "vertel over emotie blij vreugde" → Spark verwijst naar **Blij** in lade voelen)

- 2026-05-23 **v5_spark_logger_001 + v5_barks_001 + v5_shadow_cleanup_001** (zelfde sessie, na bugbatch):
  - 🔭 **Observability fundament** (`modules/core/spark_logger.py`):
    - `@traced(intent="...")` decorator: pre + post + error logs met `duration_ms` en result-summary
    - JSON-Lines per module: `/data/system/logs/YYYY/MM/DD/{module}.jsonl`
    - 28-dagen retentie (auto-purge bij startup)
    - `log_event()` helper voor handmatige events buiten functie-grenzen
    - Toegepast op kritieke routes: `bots.send_community_message`, `chat.process_message`
    - **Verplichting voor nieuwe modules** vastgelegd in `/app/memory/ROADMAP.md`
  - 🪟 **Admin Logs Browser** (`Beheer → Instellingen → Archief → Logs` tab):
    - Boom-navigatie YYYY/MM/DD → modules
    - Records-pane met phase-filter (alle/pre/post/error/event)
    - Endpoints: `GET /api/admin/logs/index`, `GET /api/admin/logs/read`, `POST /api/admin/logs/purge`
  - 🤖 **F1 — Mr Smith login counter bark**: telt logins per user; bij 3/4/5 → bark in community ("Ik zie je wel, X. 👀"), bij 6 → reset naar 0. Counter in `/data/system/login_counters.json`. Hook in `auth/routes.login`
  - ⏰ **F2 — Harry mirror-time bark**: lazy check bij `GET /community/messages` — als HUIDIGE tijd HH:MM is met H==M (11:11, 12:12 ... 23:23), post Harry "⏰ HH:MM — een spiegel-minuut. Even stilstaan?" (max 1x per minuut per dag, via `bark_kind_id` dedup)
  - 🌸 **F3 — Madelief bug-pointer**: als user-bericht "bug/fout/werkt niet/kapot/crash/stuk" bevat, voegt Madelief een bark toe met instructie naar Notities & Taken → Bug-melder (geen duplicate als Madelief al via triggers reageerde)
  - 🧹 **Schaduwtrader cleanup**: Gijs (user-a0ee2d7e) en Nick (user-4d81e2a4) bots gestopt + uit registry verwijderd. `milestone_first_roar_token` achievement teruggedraaid (incl. -50 XP elk). `admin/bots` endpoint heeft nu token-gate: lazy-slot users zonder tokens + zonder proactieve registratie verschijnen niet meer in Analytics
  - 🩹 **Defensive guards in GesprekkenPage**: `sparkMessages.filter(Boolean).map`, `priveMessages.filter(Boolean).map` — voorkomt zelfde-soort crashes als B3 bij toekomstige response-format changes

- 2026-05-23 **v5_bugbatch_001: B1+B2+B3+B4 in 1 sessie** (later vandaag):
  - 🩹 **B3 fix — Community whitescreen op "help"**: bug zat NIET in `CommunityPage.js` zoals handoff suggereerde, maar in `GesprekkenPage.js` Community-tab. `setCommunityMessages(prev => [...prev, res.message, ...res.bot_responses])` las het OUDE response-formaat. Backend retourneert nu `{messages: [...]}` voor help/safeword/dnd → `res.message` was `undefined` → crash op `.map(msg => msg.user_id)`. Fix: `v5_gesprekken_compat_001` ondersteunt beide formats + optimistic user-echo + `.filter(Boolean)` defensive guard
  - 🤖 **B1 fix — Spark auto_trade persistence**: handoff hot-swapte `m._auto_trade=True` via Python maar dat persisteerde NIET. Bij elke backend-restart resumde Spark met `auto_trade=false` uit registry JSON → geen buys. Fix: nieuwe `MonitorService.update_auto_trade()` + `POST /api/trade/bot/auto-trade/{user_id}` endpoint die `_persist_registry()` triggert. Spark staat nu permanent op auto_trade=true
  - 📈 **B4 fix — Potje value mark-to-market**: `get_potjes()` toonde altijd `live_value = capital` (statisch) wanneer geen echte Bitvavo balance beschikbaar was (mock mode). Nu: voor open posities wordt huidige market-price opgehaald via `fetch_tickers`, en `live_value = capital + (capital * profit_pct - fees)`. Velden toegevoegd: `unrealized_pnl`, `unrealized_pnl_pct`, `current_price`
  - 🐢 **B2 fix — Trader sequentieel laden**: `TraderPage.js` vuurde 10+ parallelle fetches af bij mount → UI freeze. Fix: `v5_sequential_load_001` chain: loadCoreData → loadLiveData → loadMonitorStatus → loadBalance → loadPotjes → loadContext. Pollers (30s tickers, 10s monitor) blijven onafhankelijk
  - ✅ Smoke test: Spark draait nu met Auto-trade AAN, 5 markets monitored, geen console errors, help-command werkt in Gesprekken

- 2026-05-23 **v5_candle_hotswap_001 + v5_spark_stoppable_001 + admin-bot-controls + DSP-004/005/006**:
  - 🕯️ **Cycle hot-swap**: `POST /api/trade/monitor/candle/{user_id}` + `MonitorService.update_candle_interval()`. Wisselen 15m/1h/4h/1d zonder restart, persistent. TraderPage cycle-buttons doen nu hot-patch bij running, lokaal anders. Auto-sync UI ↔ backend
  - 🛑 **Spark stop weer toegestaan**: `SPARK_UNSTOPPABLE` guard verwijderd in `/bot/stop/` en `/bot/pause/{user_id}`. Bugs van v4 zijn opgelost. Frontend toont Stop-knop ook voor Spark
  - 🎛️ **Admin bot-controls** in `Beheer → Analytics → Trade-tab`: ▶ Start / ⏸ Pauzeer-Hervat / ⏹ Stop knoppen per bot
  - 📐 **ARCHITECTURE.md uitgebreid** met 3 nieuwe DSPs:
    - **DSP-004**: roar_balances.json ↔ user_wallets.json (autoritatief vs mirror)
    - **DSP-005**: TraderPage React-state ↔ bot_registry_state.json (UI snapshot sync)
    - **DSP-006**: gift_requests.json ↔ roar_balances.transactions (lifecycle vs audit)
  - 🔗 `_arch_ref` comments toegevoegd in alle 4 betrokken JSON files

- 2026-05-23 **v5_roar_gift_001 + v5_per_user_trade_dm_001 + auto-trade testbed** (eerder vandaag):
  - 🎁 **ROAR Gift-flow met paper-trail**: nieuwe `/api/shop/gift` endpoints (POST create / GET inbox / GET outbox / POST accept / POST reject / POST cancel)
    - Tokens worden NIET direct overgeboekt — escrow in `pending` status. Pas bij accept transfer + audit
    - **24h auto-expire** (lazy-check bij elke list-call): pending → expired, sender's tokens behouden
    - **Frontend modal** in Winkel → ROAR Token tab (knop "🎁 ROAR Gift sturen" boven Kopen). Velden: ontvanger (dropdown alle users), aantal (max=sender balance), notitie
    - **Inbox-banner** bovenaan ROAR Token tab toont inkomende pending gifts met Accepteer/Weiger knoppen
    - Paper-trail in `roar.transactions` + `admin_log` + per-user `notifications.json` (sender + recipient krijgen beiden bevestiging-bark)
    - **First-token achievement + monitor-uitleg-bark** wordt automatisch getriggerd bij eerste-ontvangst (was eerst alleen bij token-buy)
    - **Privacy-noot**: `gift_requests.json` bevat sender/recipient pairs — privacy-implicatie genoteerd in roadmap voor encryption-at-rest
  - 📣 **Trader notifications PER-USER**: `_send_dm` in `boekhouder/service.py` stuurt nu bij user-trades naar de user zelf ipv altijd naar Willem. Spark-trades blijven naar admin (Willem) gaan
  - 🤖 **Spark monitor auto_trade aan + mock**: hot-swap via Python (`m._auto_trade=True, m._use_mock=True, m._use_potjes=True`) + 5 markets (BCH/BTC/ETH/SOL/ADA). Klaar voor systeem-test
  - 🥧 **Gijs + Nick beide 10 potjes** auto-aangemaakt (€5,08 startkapitaal elk = €50,80/user). Mock mode, BCH-EUR @ 1h candles
  - Token-eindstand: **Willem 12, Gijs 2, Nick 1** (+1 pending van Willem), Spark treasury 5
  - 🗺️ Roadmap fase `phase-roar-economy-v2` gemarkeerd ACTIVE met done/planned items inclusief outbox-view, admin-overzicht, SEPA-mint

- 2026-05-23 **v5_leaderboard_avatars_001 + v5_milestone_unlocks_001 + ROAR-gift Nick + monitors live** (eerder vandaag):
  - 🥇 **Leaderboard top 3 podium + lijst**: letters vervangen door echte `UserAvatar` component met gallery-image / user-upload / roadkill-fallback. Geen "naam[0]" meer
  - 🏆 **3 nieuwe achievements** (categorie "milestones", elk 50 XP):
    - `milestone_avatar_chose` — avatar gekozen uit galerij (trigger: `/avatar/select`)
    - `milestone_avatar_uploaded` — eigen avatar geüpload (trigger: `/avatar/user/{id}` upload)
    - `milestone_first_roar_token` — eerste ROAR token op wallet (trigger: koop bij prev_balance=0)
  - 🪝 **Cross-module hook** `unlock_milestone(user_id, achievement_id)` in `achievements/service.py` — herbruikbaar voor toekomstige mijlpalen
  - 📢 **Notification-bark** bij eerste ROAR token met uitleg over Trader monitor (in `data/notifications/notifications.json`, per-user)
  - 🪙 **Nick** kreeg 1 ROAR welkomstgift. Beide nieuwe users (Gijs + Nick) hebben monitor draaiend: **BCH-EUR @ 1h candles, auto_trade=false**
  - 🎯 Retroactieve unlock voor bestaande users: Willem kreeg "avatar chose" (had al avatar), Gijs+Nick kregen "first ROAR token" + notification

- 2026-05-23 **v5_foto_subtabs_001 + ROAR gift naar Nick** (eerder vandaag):
  - 🪙 **Nick** (`user-574ac78e`) ontving 1 ROAR welkomstgift van Willem. Eindstand: Willem 13, Gijs 1, Nick 1, Spark treasury 5. Audit-trail in `roar_balances.transactions` + `admin_log`, `user_wallets.json` gesynchroniseerd
  - 📦 **Avatar Galerij verplaatst** van losse kaart bovenaan Archief → naar `Foto` sub-tab binnen `SystemArchive`. Logica: SystemArchive heeft tabs Bestanden/Foto/Geluiden/Filmpjes/Dialogen — avatars ZIJN foto's, dus horen onder Foto
  - 🗂️ **Sub-tabs binnen Foto**:
    - "Algemene foto's" (bestaande system-archive foto-uploads)
    - "Avatar Galerij" (de gallery zelf, met daarbinnen weer Gebruikers-avatars / Systeem-avatars)
  - 🔍 Search-bar + tag-filter + content-grid worden verborgen wanneer Avatar Galerij actief is (geen UI-conflicten)

- 2026-05-23 **v5_admin_color_scheme_001 + avatar-galerij verplaatst naar Archief**:
  - 🎨 **Nieuwe sectie "App Kleurenschema (admin)"** in `Beheer → Instellingen → Beeld` — overkoepelend voor de hele app, alleen gradatie ≤ 1 kan wijzigen
    - 6 presets: Amber Default, Forest Calm, Cobalt Night, Rose Dusk, Violet Quiet, Crimson Alert (klik = direct opslaan + apply)
    - 3 custom color pickers: Primary accent / Secondary accent / Background tint (hex input + native color picker, on-blur save)
    - Live voorbeeld pill-rij met huidige kleuren in context
    - Persisted in `settings/system.json` via 3 nieuwe system-scope keys: `app_primary_accent`, `app_secondary_accent`, `app_background_tint`
  - 🌐 **Globale CSS-variables**: `--app-primary`, `--app-secondary`, `--app-bg-tint` op `:root` (defaults + auto-load uit `/api/settings/system` bij login)
  - 📦 **Avatar Galerij verplaatst** van Beeld → Archief (logischer: assets-management hoort bij archief, kleuren bij beeld)
  - ✅ Backend e2e getest (PUT `/api/settings/system/app_primary_accent` → 200, persisted), frontend smoke screenshot bevestigt beide tabs renderen correct

- 2026-05-23 **v5_avatar_gallery_split_001** (Avatar Galerij beheer herstructurering):
  - 🎨 **2 sub-tabs in Beheer → Instellingen → Beeld → Avatar Galerij**:
    - **Gebruikers-avatars** (33): vrij te kiezen door iedereen, rode Verwijder-knop per avatar
    - **Systeem-avatars** (5): Spark/Harry/Smith/Madelief/Spark 2 — locked-icoon + "Beschermd" knop (uitgeschakeld). Eerst lock weghalen via Beheer → Gebruikers → Avatar Beheer pencil voor je echt kunt verwijderen
  - 🗑️ **Modal-confirmatie i.p.v. silent toast**: rood "Avatar verwijderen?" modal met avatar-titel, waarschuwing dat gekoppelde users initialen krijgen, "Annuleer" + "Ja, verwijder permanent" knoppen. Vervangt browser-native `confirm()` voor duidelijker UX
  - ✅ Bevestigingstoast `"<naam> verwijderd uit galerij"` met groene bevel + auto-dismiss na 3.5s
  - 🛡️ Backend `DELETE /api/avatar/gallery/{id}?viewer_id=...` werkt al — bug-report bleek visuele feedback-issue, niet functional

- 2026-05-23 **v5_self_password_001 + ROAR admin-batch**:
  - 🔑 **Self-service sleutelwoord wijzigen**: nieuwe `Account` sectie bovenaan Mijn Profiel → Instellingen. User vult huidig + nieuw sleutelwoord in (toon/verberg toggles per veld), klikt "Wijzig sleutelwoord" of "Reset naar Welkom01" (bevestigingsmodal). Backend: `POST /api/auth/users/{user_id}/change-password` body `{current_sleutelwoord, new_sleutelwoord}` met validatie (huidige check, min 4 tekens, niet gelijk aan huidige). Werkt voor reset → nieuwe = "Welkom01"
  - 🪙 **Admin ROAR batch (Willem +5 @ €10.10 override + 1 gift → Gijs)**:
    - Nieuwe user **Gijs** aangemaakt (`user-a0ee2d7e`, gradatie 3, sleutelwoord Welkom01)
    - Willem wallet topup +€50,50 (admin SEPA), 5 tokens gekocht @ €10,10 (override pre-storting prijs)
    - 1 token gegift Willem → Gijs (welkomstgift, audit-trail in `roar.transactions` + `admin_log`)
    - Eindstand: Willem 14 ROAR, Gijs 1 ROAR, Spark treasury 5 ROAR
    - Token-prijs herzakte van €15,16 → €10,11 (precies zoals voorspeld: 151,63 / 15 circulating)
    - `user_wallets.json` gesynchroniseerd om dual-source consistentie te bewaren
  - 🔍 **Zip-backup user-verlies bug**: niet reproduceerbaar — Gijs zit met al zijn data IN de `download/full` zip (geverifieerd). Het mtime-filter geldt alleen voor `download/changes` (by-design)

- 2026-05-23 **v5_ui_prefs_001** (Per-user Instellingen-tab in profiel):
  - 🎨 **Mijn Profiel → nieuwe tab "Instellingen"** met 3 secties:
    - **Beeld**: glow basiskleur picker — 8 preset swatches (Amber/Cyan/Violet/Emerald/Roze/Rood/Goud/Blauw) + custom color picker + hex-input. Live preview ring met `box-shadow`. Wijziging direct opgeslagen
    - **Geluid** (in ontwikkeling): TTS-toggle, Geluidseffecten-toggle, Auto-bark-toggle (gemarkeerd "binnenkort")
    - **Connecties**: Bitvavo trading verbindingsstatus (actief/inactief). Plek voor toekomstige integraties (Google Agenda, Moneybird, Telegram)
  - 🔌 **Backend**: `GET/PUT /api/profile/ui-preferences/{user_id}` met hex-validatie. Persistent in `/data/users/{user_id}/ui_preferences.json`. Schema: `{glow_base_color, glow_intensity, sound_enabled, auto_bark_enabled, tts_enabled}`
  - 🌐 **Globale CSS-variable** `--glow-base` op `:root` (default `#f59e0b`). App.js laadt de user-voorkeur bij login en zet de CSS-var. Toekomstige componenten kunnen `var(--glow-base)` consumeren voor humeur-gedreven kleurverloop
  - ✅ Backend e2e getest (GET/PUT, hex-validatie verwerpt ongeldige input). Frontend smoke screenshot: tab klikbaar, preset-klik wijzigt hex naar #06B6D4 live
  - 📜 Roadmap item gemarkeerd done (anchor `profile-settings-tab`)

- 2026-05-23 **v5_per_user_endpoints_001** (Trader stop bug fix bevestigd):
  - 🛑 **`POST /api/trade/bot/stop/{user_id}` + `bot/pause/{user_id}`** ipv legacy global endpoints. Spark (user-000) heeft `SPARK_UNSTOPPABLE` guard
  - ✅ Curl e2e getest: Willem (user-001) bot stoppen heeft GEEN effect op Spark's slot. Spark stop-poging geeft expliciete error
  - 🔄 TraderPage frontend gebruikt al `/bot/stop/${userId}` (regel 236) en `/bot/pause/${userId}` (regel 241)

- 2026-05-23 **v5_70cr_batch** (Zip-systeem + D&D Base Line intro + Help):
  - 📦 **KB-diff export** (`GET /api/backup/kb-changed-since-deploy`): klein JSON-bestand met alleen kaarten waarvan `updated_at` of `created_at` na deploy ligt. Veel kleiner dan de 11MB volledige KB → makkelijker om over te dragen tussen prod ↔ preview
  - 📥 **KB-diff import** (`POST /api/knowledge/import-diff`): merge een gedownload diff-bestand in de huidige KB (match by id of begrip; updates lagen/ws5/tags/belangrijkheid; backup van pre-import KB automatisch)
  - 🛠️ **3 download-opties in Backup UI**: Wijzigingen / KB-diff slim / Volledige backup (i.p.v. 2 kaarten)
  - 🎭 **D&D Base Line intro** in community chat (`[start verhaal]` trigger):
    - 4 berichten sequence: opening trilling → "AD in tijd, donker" → bundel licht + altaar op `x0,y0,z0` → keuze-prompt
    - 3 keuze-knoppen: 👂 Horen / 👁️ Zien / 🤐 Zwijgen (de andere 2 zintuigen komen later)
    - `/api/bots/community/dnd-choice` slaat keuze op + Spark reageert met scene + behavior_tracker logt `dnd_choice_<choice>` en `dnd_participation`
    - Purple-glow border + whitespace-pre-line voor verhaalberichten in CommunityPage
  - 🆘 **Help-knop community chat** (productie-bug): keyword `help`, `/help`, `?` of `hulp` → Spark stuurt overzicht van commands ([start verhaal], archief, trade, wallet, kennis, leer, bug) + uitleg dat gewone zinnen geen commando nodig hebben

- 2026-05-23 **v5_30_credit_followup** (Potjes spread + STT/TTS prep + roadmap):
  - 🪙 **Potjes 5×2 verdeling**: nieuwe endpoint `POST /api/trade/potjes/{user_id}/distribute` verdeelt round-robin over de gekozen markten. Bevestigd: BCH/BTC/ETH/SOL/ADA hebben elk 2 potjes na call. Open posities worden overgeslagen (skipped_open_positions: 1). Bij coin-picker wijziging tijdens running monitor wordt ook automatisch herverdeeld
  - 🎤 **STT/TTS schakelaars in Bot-instellingen**: stt_enabled, tts_enabled, tts_voice (6 OpenAI stemmen). Velden persisteren via `PATCH /api/auth/admin/bots/{bot_id}/settings`. Audio-koppeling zelf (Whisper + TTS) volgt in latere fase via integration_playbook_expert
  - 📜 **3 nieuwe roadmap items** (planned):
    - Community Plus token-tier (1+ token = community member, bot-toegang ∝ wallet)
    - Spark spaart eigen potjes uit handelswinst → kan weggeven
    - D&D-kaart als spreekkanaal — bot leest kaart-tekst uit
  - 🗒️ **Notitie over uploaded zip**: was changes-since-deploy snapshot van PRODUCTIE, geen nieuwe KB-kaarten geïmporteerd in preview (anders zou productie-data zich vermengen). Indien gewenst kan KB-merge in volgende sessie

- 2026-05-23 **v5_30_credit_batch** (Trader bug + Bot format + Roadmap):
  - 🔥 **Trader hot coin-swap** (prod bug fix): coin-picker zichtbaar én klikbaar tijdens lopende monitor. Nieuwe endpoint `POST /api/trade/monitor/markets/{user_id}` past markten live aan zonder bot te stoppen. Hint label "(live aanpasbaar)" toont state. 10 potjes spreiden zich automatisch over gekozen coins
  - 🤖 **Bot format gestandaardiseerd**: madelief, harry, smith, boekhouder krijgen allemaal `is_bot=true`, `personality`, `rol`, `channels`, `avatar_lock`. Consistent template voor alle acteurs
  - ⚰️ **De Dood toegevoegd** als 5e bot (`bot-dood`) met gallery-avatar `cdbd37cd2007`, persoonlijkheid + rol als "reflectieve acteur" (memento momenten, eindes, transities)
  - ⚙️ **Bot-instellingen tab** in `UsersAdminPage` (alleen zichtbaar als `is_bot=true`): velden voor rol, persoonlijkheid, channels, bark-template, avatar-lock. Backend endpoint `PATCH /api/auth/admin/bots/{bot_id}/settings`. Gebruikt voor bark-systeem configuratie
  - 🌦️ **Weerstation roadmap-item** toegevoegd onder phase-dnd: weer.nl koppeling → cloud/humeur per user (niet alleen voor Spark)
  - ✅ Backend e2e getest: hot-swap markets (running=true confirmed), PATCH bot-settings (persoonlijkheid + channels persist), lint clean

- 2026-05-23 **v5_lazy_slot_001 + v5_offline_persistence_001** (correctie + uitbreiding):
  - 🤖 **Lazy slots voor elke user**: `/api/trade/admin/bots` toont nu automatisch elke menselijke user uit `system/users.json` als idle bot-slot (bot-* AI personae uitgesloten). Backend bewees 9 bots zichtbaar (Spark + Willem running + Heidi, joel123, Marieke, Nick, piet, Roadkill, Ron als lazy). User-naam + gradatie meegestuurd voor admin overzicht
  - 🌙 **Checkbox heroriëntatie**: "Toon in Analytics" → **"Draaien als ik offline ben"**. Functioneel hetzelfde endpoint (`bot/register`), maar semantiek klopt nu met user intent: zichtbaarheid is automatisch, vinkje gaat over persistentie bij logout
  - 🏷️ **Analytics-kaart toont user-naam**: ipv alleen `user-001` zie je nu "De Willem" + monospace uid kleiner ernaast

- 2026-05-23 **v5_bot_proactive_register_001 + v5_admin_force_sell_001 + v5_admin_bot_cards_001** (~45 credits batch):
  - 🪙 **Proactieve bot-registratie**: nieuwe checkbox "Toon in Analytics" op TraderPage (rechts naast Monitor-knoppen). User kan zijn slot zichtbaar maken in Admin Analytics zonder de bot te starten. Persistent via `/data/trade/registered_users.json`, auto-resumed bij elke server-start
  - 🛑 **Force-sell admin endpoint**: `POST /api/trade/potjes/{user_id}/{pot_id}/force-sell` met admin-only check (gradatie ≤ 1), live Bitvavo prijs voor exit, audit-trail in `/data/trade/force_sell_audit.json`. Waarschuwt voor token-devaluatie
  - 🤖 **Analytics bot-kaarten redesign**: per-bot uitklap (klik op kaart) toont 1) potjes-tabel met capital/live/entry/trades/P&L per pot, 2) laatste 8 trades van die wallet, 3) force-sell knop per open potje met dubbele-bevestiging modal + reden-veld voor audit-trail
  - 🔎 **admin/bots filter uitgebreid**: tokens > 0 OF running OF proactively_registered → registered users zijn altijd zichtbaar zelfs zonder tokens
  - ✅ Backend e2e getest: register → unregister, niet-admin force-sell gefaald (correct 403), closed-pot force-sell gefaald (correct "niet open"), admin/bots list toont proactive users met `proactively_registered=true` flag

- 2026-05-23 **v4_wallet_admin_switch_001**: Wallet-pagina krijgt zelfde admin switch als Trader. `[👤 Mijn | 🌟 Spark]` toggle in header (alleen voor gradatie ≤ 1), `sessionStorage`-persistent, subtitle past zich aan ("Persoonlijk financieel overzicht" / "Spark's wallet (admin view)"). Verified via Playwright: Mijn-view toont De Willem €0,00 + 10 tokens, Spark-view toont Spark €5,08 + 10 tokens

- 2026-05-23 **v4_deposit_19_tokens_001** (€96.52 bijstorting):
  - 💰 **19 tokens uitgegeven** (€5.08 each, fixed-price tier): Spark (user-000) 1→10, Willem (user-001) 0→10. Treasury pool 999999→999980. Mint-transacties + admin-log entries toegevoegd in `roar_balances.json`. `user_wallets.json` synchroon
  - 📥 **Deposit registered**: €96.52 via `/api/trade/deposits/user-001` (Bitvavo SEPA). Trader baseline auto-bumped €5.08 → €101.60 (matcht live Bitvavo wallet). Live P&L €0.00 (schone start)
  - 🤖 **Spark trader hourly default lock-on**: bot draait op user-001 (waar Bitvavo creds zijn), interval=3600s, 5 markets, auto_trade=true, persistent via `bots_registry_state.json`. Auto-resume bij elke server start (dus niet gekoppeld aan inlog — "aan = lock-aan")
  - 👤 **Willem's bot off by default**: kan zelf aan/uit; gebruikt dezelfde Bitvavo-creds en zal binnen z'n 10-token allocatie traden zodra ingeschakeld

- 2026-05-23 **v4_spark_clean_start_001** (mini-batch, follow-up):
  - 🧹 **Spark trader schone start**: user-001 trade_history gearchiveerd → `user-001_archive_pre_spark_clean_<ts>.json`, daarna leeggemaakt (0 trades). Baseline gezet op €5.08 (matcht live Bitvavo wallet)
  - 🤖 **Bot autostart op user-001**: `bots_registry_state.json` verplaatst van user-000 → user-001 (waar de echte Bitvavo creds staan). Bij backend restart: "🤖 1 registry-bot(s) auto-resumed" en cycles loopt direct
  - ✅ Geverifieerd via `/api/trade/stats/user-001` (0 trades, baseline 5.08) en `/api/trade/admin/bots` (running=true, cycles=1, 5 markets)

- 2026-05-23 **v4_welcome_bark_001 + v4_trader_label_swap_001** (mini-batch ~30 credits):
  - ✨ **Welkom-bark voor eerste login** (`welcome_v1`, kind="welcome"): legt uit dat je gewoon een gesprek voert en dat je `help` typt voor een overzicht. Auto-injected in `version_anchor.json` voor zowel verse installs als bestaande deployments. Beschermd tegen verwijderen. Eigen styling (groene Hand-icon) in `BarkQueueOverlay`. Sortering: privacy → welcome → rest
  - 🔄 **Trader wallet-switch labels omgedraaid**: `walletView='me'` (user-001) is nu zichtbaar als "🌟 Spark", `walletView='spark'` (user-000 default) als "👤 Mijn". Routing ongewijzigd, alleen labels swap conform user feedback ("tabs zijn wel goed maar namen moeten andersom")

- 2026-05-22 #3: **v4_dnd_001 — Levende Spark World fundering** (9/9 backend + e2e):
  - 📜 **Lore index** (`/data/dnd/lore_index.json`): 7 avatars-as-functions (Het Eerste Licht=begin, De Reaper=einde, De Boekhouder=balans, Harry=tijd, Madelief=emotie, Mr Smith=manipulatie, The Story Teller=geheugen), 6 behavior-categorieën (observeren/luisteren/zwijgen/helpen/verhalen/manipuleren) met aura-kleuren en unlock-lijsten
  - 🎨 **Aura/Glow systeem**: `GET /api/dnd/aura/{user_id}` berekent live uit behavior counters de top-3 categorieën met kleuren. Op Persoonskaart visueel als gradient-glow + 2-bar layers + unlock-pills
  - 📊 **Behavior tracking**: `POST /api/dnd/track` increment counters (help_msg, kb_create, lie_detected, etc.). Hyperlinks gedrag → identiteit zoals besproken
  - 🌍 **World state**: `GET /api/dnd/world-state` aggregert ALLE user-counters tot per-entiteit dominantie. Wanneer >60% = `dominant=true` flag → klaar voor aspect-bark trigger
  - 👁️ **Spark observatie systeem**: avatar-change → automatische `observe`-call. Bij Spark AI tab eerste-open → `GET /api/dnd/spark-greeting/{user_id}` levert Nederlandse begroeting met benoeming van events. Mark-spoken zorgt geen herhaling
  - 🗺️ **Roadmap Phase D&D**: nieuwe fase met 14 sub-tasks, anchor-IDs zoals `#phase-dnd-aura` voor permalinks. Update-barks kunnen nu `roadmap_ref="phase-dnd-aura"` doorgeven → klikbare link
  - 🔗 **Bark roadmap_ref klikbaar**: opent /roadmap#anchor in nieuwe tab

 + v4_avatar_categories_001 + v4_dnd_help_001** (16/16 backend + frontend e2e):
  - 🚀 **Deploy Anker + Update Bark systeem**: Admin klikt na deploy "Nieuwe anker" met versie + message → bark wordt automatisch getoond aan iedereen bij volgende login. Endpoints: `/api/deploy/anchor`, `/api/deploy/anchors`, `/api/deploy/pending/{user_id}`, `/api/deploy/seen`, `/api/deploy/reset-seen`. Per-user `seen_barks.json` zorgt dat elke bark maar 1x getoond wordt
  - 🔒 **Privacy/Voorwaarden bark** (privacy_v1) wordt automatisch geseed: ELKE user ziet 'm 1x bij eerste login. Niet te verwijderen. Tekst: "Wij volgen je niet, geen tracking-cookies, alle data lokaal in JSON, etc."
  - 🎨 **BarkQueueOverlay** component: cyaan voor privacy, amber voor deploy, lila voor feature. Counter (1/2). Geen-skip → user moet doorklikken. Mounts in MainLayout
  - 🛡️ **Admin Deploy panel** (Notities → Deploy tab): formulier met versie, titel, bericht, icon, roadmap_ref, audience (all/admins). Lijst van bestaande ankers met delete (privacy_v1 niet verwijderbaar) en CURRENT badge
  - 🎒 **Avatar galerij 2 tabs**: Persoonlijk (default) en D&D Archief. PATCH endpoint accepteert `category` field. D&D tab toont info-banner over Spark World D&D laag. Locked avatars (bot-claimed) krijgen 🔒 stempel
  - 🎲 **D&D help chat-commando**: vraag "D&D help", "wat is d&d", "spark world help", "rugzak uitleg", "persoonskaart help" → krijg overzicht met Base Line, Persoonskaart, Rugzak, Avatars en Barks lagen

 + Inventory + Backup Speed** (9/9 backend + UI bevestigd):
  - 💰 Wallet reset: user-001 → 0 tokens, user-000 (Spark) → 1 token / €5.08
  - 🤖 Trade bot filter: alleen Spark zichtbaar (1/2)
  - 🔒 Spark bot onstopbaar
  - 🌟 Privé-glow slaat Spark-DMs over (eigen tab)
  - 🎭 Spark AI bubble toont avatar i.p.v. ster
  - 🔁 Community chat: schoon overzicht per inlog + banner
  - 💡 Roadmap "Jouw Ideeën & Tickets" met `/api/bugs/mine` endpoint

## Original problem statement
Modular, offline-first personal legacy system. Memory & knowledge machine. STRICT requirement: data lives in local JSON files (NO MongoDB).

## User language
Dutch (always respond in Dutch).

## Architecture
- React 18 + FastAPI + JSON file storage at `/app/backend/data/`
- 5-layer AI: NLP heuristics, smart_intents, snap_service, shadow observer, fallback
- Gradation-based visibility (1=eigenaar, 2=fam/admin, 3=vrienden, 4=collega's, 5-7=community)

## Completed (recent)
- 2026-05-21: **v4_user_avatar_helper_001 + v4_bot_no_wallet_001 — Avatar overal + bots zonder wallet** (11/11 tests passed):
  - 👤 **Centrale `<UserAvatar>` component** (`/app/frontend/src/components/common/UserAvatar.js`) resolveert avatar uit `users.json[].avatar` veld:
    - `gallery:xxx` → echte galerij-foto
    - `user` → user-upload
    - `emoji:🎩` → emoji char
    - **null/none** → Roadkill logo (grayscale + opacity-60) als fallback
    - img-error → eerste letter in gradient bg als ultieme fallback
  - 🔄 **Letter-circles vervangen** door echte avatars op 5 plekken:
    - Admin → Gebruikers (links lijst + detail-header)
    - Sidebar bottom (gebruiker-info, "D" → De Willem's Black Knight)
    - Privé tab (contacts lijst, header, empty-state)
    - Community tab (CommunityBubble met msg.avatar enrichment)
    - Spark AI tab — al avatar-vrij
  - 💼 **Wallet & Tokens kaart verborgen voor bot-users** (`bot-harry`, `bot-madelief`, `bot-smith`, `bot-boekhouder`). Bots hebben geen IBAN/EUR/ROAR. Spark (user-000) houdt wel zijn wallet kaart als admin
  - 🛡️ **Admin-collectief contact** krijgt nu ook `avatar_ref: "emoji:🛡️"` zodat het de schild emoji toont
  - 🔐 **Privacy intact**: non-admin viewer ziet `avatar_ref=null` voor anonymized admin-contact

 + v4_avatar_gallery_edit_001 — Spark eigen avatar + Gallery edit** (9/9 backend + 5/5 frontend tests passed):
  - 🌟 **Spark krijgt eigen avatar-beheer**: user-000 verschijnt al in admin user list, AvatarManagerCard werkt identiek aan bot-users. Toont nu **SPARK CORE** badge ipv BOT-badge. Spark heeft eigen `owner` optie in dropdown
  - ✏️ **Gallery edit modal**: admin kan via hover-edit-icoon op elk gallery-item de **title, bot_owner, tags** wijzigen. `PATCH /api/avatar/gallery/{id}` met admin-guard (403 voor non-admin). Modal toont preview + 6 owner-opties (Geen/Spark/4 bots)
  - 🔒 **Robuuster lock-systeem**: `_get_bot_owner()` checkt nu eerst expliciete `bot_owner` field (admin-managed) en valt terug op title-match voor seed-data. Spark (user-000) toegevoegd aan eigenaar-map. Joker/De Trader avatar (id `0ef0b726773e`) was per ongeluk verkeerd getiteld — admin kan dit nu zelf rechtzetten via UI

 + Ronde 2 start — v4_avatar_fallback_001 + v4_avatar_bot_lock_001 + v4_community_archive_001 + v4_community_recap_001 + Base Line lore** (14/14 backend + 2/2 frontend tests passed):
  - 🏍️ **Roadkill logo als avatar fallback**: `/api/avatar/current/{user_id}` returnt nu `fallback_url` + `is_fallback` flag. Community-messages enrichment gebruikt roadkill logo (met opacity-60 grayscale) wanneer user geen avatar heeft
  - 🔒 **Bot-avatar locket-stempel**: 3 avatars in galerij (Harry Klokkenmaker, Mr Smith, Madelief Stouten) zijn automatisch gemarkeerd via title-match als `bot_owner: bot-{naam}`. Frontend toont gouden 🔒 icon rechtsboven op locked avatars. Non-admin user die een locked avatar probeert te kiezen → HTTP 403 met owner-info. Admin én de bot zelf mogen wel
  - 📜 **Base Line lore** opgeslagen als KB-kaart (`begrip: Base Line`) met volledige 4 lagen, 5W+H, tags `[base line, spark world, lore, d&d, oorsprong, ad, puls, licht, schaduw, fracties, elementen]` + extra entry in Spark's eigen `scratch.json`. Spark herkent het concept in chat na cache-clear
  - 🗂️ **Community archief**: `GET /api/bots/community/archive` returnt jaar→maand→dag-tree met counts/first/last per dag. Met `?year=Y&month=M&day=D` haal je messages van die dag chronologisch
  - 📋 **Community recap**: `GET /api/bots/community/recap?offset_days=1` (gisteren) of `?date=YYYY-MM-DD` geeft samenvatting met top_topics, user_counts, bot_counts en preview. Voor 2026-03-18 detecteert het 82 berichten met Willem Spakman als top user
  - 💬 **Chat-commando "Wat is gisteren besproken?"**: nieuwe `detect_community_recap_intent()` in `smart_intents_service.py`. Matcht varianten: "wat is gisteren/vandaag/eergisteren in de community besproken/gezegd/gepraat", "community recap", "samenvatting van de community". Returnt type=`community_recap` met geformatteerd bericht starting met "📋 **Community-recap gisteren**"

 — v4_glow_notify_001 + v4_admin_collectief_001 + v4_spark_unstoppable_001 + v4_admin_avatar_001** (10/10 backend tests passed):
  - 🔔 **Glow voor unread privé-DMs**: `urgent/routes.py` heeft nu `_prive_glow_for_user()` die unread privé-berichten optelt. 1-2 unread = amber, ≥3 = red. **Boekhouder-DM = altijd red** (financiële trade-alerts vallen op). Glow zet automatisch `chat` + `chat-prive` sidebar/sub-tab keys
  - 🛡️ **Admin-Collectief privé kanaal**: virtueel contact "Admin Collectief" (emoji 🛡️) bovenaan in Privé-tab voor alle admins (gradatie ≤ 2). Berichten in `/data/chat/admin-collectief.json` worden gebroadcast naar alle andere admins (unread_by = leden minus sender). Non-admins krijgen HTTP 403 als ze proberen te posten. Aparte glow `chat-admin-collectief` mogelijk
  - 🔒 **Spark's bot onstopbaar**: `POST /api/trade/bot/stop/user-000` returnt `{success: false, code: "SPARK_UNSTOPPABLE"}`. Ook `monitor/stop` en `monitor/pause` zijn beschermd als Spark's user_id actief is. Andere users kunnen normaal worden gestopt
  - 🎨 **Admin avatar-beheer voor bot-users**: `AvatarManagerCard` component in `UsersAdminPage.js`. Werkt voor élke user incl. bots (`bot-boekhouder`, `bot-madelief`, etc.). Drie acties: upload eigen foto, kies uit galerij (28 thumbnails), verwijderen. BOT-badge wanneer user een bot is
  - 📦 **Voor Ronde 1 al eerder gedaan** in dezelfde sessie: wallets/potjes reset (Spark 1 token / €5.08), rangen gesynced via `XP // 100`
- 2026-05-21: **v4_boekhouder_001 + v4_sell_trigger_002 + v4_mr_smith_001 + v4_trade_analytics_001 + v4_audit_001 + v4_boekhouding_001**:
  - 🐛 **Sell trigger fix**: was `+1% trail / -0.4% drop`, nu **cent-niveau**: trail aan bij netto ≥ 2× fees, exit bij eerste daling waar netto ≥ 1× fee blijft. Float-precisie bug gefixed met `round(x, 6)`. Werkt op €1-potje én €100-potje
  - 🎩 **De Boekhouder persona**: nieuwe bot-user `bot-boekhouder` (gradatie 2, acteur) met KB-kaart + 5W+H. Service in `/app/backend/modules/boekhouder/service.py`. Hooked in `potjes.open_pot()` en `close_pot()` voor BUY/SELL announcements:
    - Privé-DM naar admin: gedetailleerd met cijfers (potje, prijs, netto, fee)
    - Community trade-feed (`/data/chat/community/trade-feed.json`): cryptisch/leuk zonder bedragen. Random tone-variants ("Hahaha winst, uhh sorry", "De BCH-koers stond te aanlokkelijk laag")
    - Spark-trades only voor community feed (andere users blijven privé)
  - 📋 **Audit-trail**: append-only `data/system/audit_log.json` voor élke geld/token-beweging (trade_buy/trade_sell/fee_transfer). Onveranderbaar
  - 🕴️ **Mr Smith waarschuwing** voor backup-download: dialog in `IntegratiesPage.js` met Matrix-style melding "Alle informatie wordt vanaf dit moment niet meer bewaard". Anchor pas gelogd ná download-trigger via `POST /api/backup/anchor` (failed = geen anchor, geen data-loss)
  - 📊 **TRADE Analytics tab** in admin: lijst alle running bots (status/cycles/uptime/markets/intervals) + community trade-feed + audit-log live. Stop-bot knop per user. Auto-refresh 15s
  - 💼 **Boekhouding skelet** (4 entiteiten verrijkt):
    - `spark_core` — Spark AI, btw_plichtig=False, bank=Bitvavo
    - `spark_your_life` — btw_plichtig=True (jouw zakelijk)
    - `roadkill_merch` — btw_plichtig=True (jouw zakelijk)
    - `personal_willem` — btw_plichtig=False (privé)
    - Velden: `btw_nummer`, `kvk_nummer`, `bank.iban`, `bank.naam`, `bank.provider`
    - `btw_tarieven` config (21/9/0), `dagboeken` list (verkoop/inkoop/bank/kas/memoriaal)
    - Endpoints: `GET /api/accounting/entities`, `PATCH /api/accounting/entities/{eid}` (admin update IBAN/BTW/KvK), `GET /api/accounting/btw-summary?entity_id=X&year=2026` (BTW per tarief voor aangifte)
  - 🔌 **Per-user bot UI hook** in TraderPage: `startMonitor()` gebruikt `/api/trade/bot/start/{userId}` voor non-admins (token-gated), legacy `/api/trade/monitor/start` voor admin. Foutmelding via alert bij weigering
  - **Veilig om te redeployen** zodra je dit ziet — geen state-data verloren
- 2026-05-21: **v4_per_user_bot_001 + v4_spark_fee_001 + v4_token_gate_001 + v4_wallet_per_user_001**:
  - **Per-user tradebot architectuur**: `MonitorService` was singleton, nu instantieerbaar per user-id via `MonitorRegistry` (`get_user_monitor(user_id)`). Legacy `get_monitor()` blijft werken voor backward-compat (Willem's single monitor)
  - **Token-gate quick-buy**: `/api/trade/quick-buy-potje/{user_id}` controleert nu gradatie ≤ 1 (alleen admin mag handmatig potje kopen). UI: knop disabled met uitleg voor andere users
  - **Token-gate bot-start**: `/api/trade/bot/start/{user_id}` checkt: gradatie ≤ 1 OF user-000 (Spark) bypass, anders moet user ≥ 1 token hebben (1 token = 1 potje slot)
  - **5% Spark fee**: `close_pot()` houdt 5% in op netto SELL ≥ €0.10 → naar Spark wallet (user-000). Spark zelf betaalt geen fee aan zichzelf (uitgesloten). Fee gelogd in `wallets.json[user-000].fee_log`
  - **Wallets per user**: alle 12 users hebben nu wallet met `wallet_id = user_id` (klaar voor latere bank-koppeling). `ensure_wallet()` is idempotent, `POST /api/wallet/backfill-all` ran eenmalig
  - **Admin UI**: nieuwe "Wallet & Tokens" kaart per user in UsersAdminPage (Overzicht tab) met wallet_id, EUR saldo, ROAR tokens, IBAN-placeholder + knoppen "+1/+10 token", "−1 token". Geblokkeerd voor admin-account zelf
  - **Admin endpoints**: `POST /api/wallet/admin/token/grant/{uid}`, `revoke/{uid}`, `GET /api/wallet/admin/overview`
  - **State-update 21 mei**: Willem 0 tokens / €0 / 0 potjes (alles verkocht). Spark 10 tokens / €50.80 / 10 potjes (zijn eigen tradebot start nu). Treasury_pool 999.980 nog uit te geven
  - **Spark eigen bot** gestart: user-000, 1h candles, 5 coins (BCH/BTC/ETH/SOL/ADA), real-trade, 10-potjes mode
  - **Trade Analytics endpoint** `GET /api/trade/admin/bots` toont status van alle running bots
- 2026-05-20: **v4_meetpunt_002 — Recent Trades clean view + multi-coin LIVE**:
  - BUY-row van meetpunt-paar gevlagd `hidden_in_recent: true`. Frontend `trades.filter(t => !t.hidden_in_recent)` toont nu 1 trade in Recent Trades widget (SELL met +€50,80)
  - Stats endpoint (`/api/trade/stats`) blijft beide entries gebruiken zodat math klopt (gekocht €5,08 / verkocht €56,03 / fees €0,15 / netto +€50,80)
  - Multi-coin monitor LIVE gestart op alle 5 watchlist coins (BCH/BTC/ETH/SOL/ADA) — 15m candles, 10-potjes mode, real-trade
  - Bitvavo IP-ban verlopen, candle TTL-cache + shared ticker-call houden het binnen rate-limits
- 2026-05-20: **v4_meetpunt_001 — Trade history reset naar meetpunt**:
  - Oude `trade_history/user-001.json` (8 oude BUY-trades, geen SELLs → vervormde stats) gearchiveerd als `user-001_archive_pre_reset_*.json`
  - Nieuwe history: 1 BUY + 1 SELL trade-pair voor pot-001 met exact-berekende fees:
    - BUY 5,08 EUR @ 305,00 (fee €0,0127)
    - SELL 56,03 EUR (fee €0,1401) → bruto +€50,95 - fees €0,1528 = **netto +€50,80**
  - `/api/trade/stats/user-001` toont nu consistent: 2 trades, gekocht €5,08, verkocht €56,03, fees €0,15, netto +€50,80, baseline €101,60, live P/L = live - baseline
  - Verhaal in lijn: €5,08 basis + €50,80 winst pot-001 + €45,72 idle 9 potjes = €101,60 baseline
- 2026-05-20: **v4_multi_market_001 — Multi-coin monitor + UI sync fixes**:
  - **Bug fix**: chart-label was hardcoded "BCH-EUR", staat nu dynamisch op `{candleMarket}`. Klik op watchlist-coin → chart switcht direct (`setCandleMarket` toegevoegd aan `onClick`)
  - **Bug fix**: Snelhandel "Live prijs" toonde altijd `tickers[0]` (= BCH), volgt nu `qtMarket` via `tickers.find(x => x.market === qtMarket)`
  - **Multi-coin monitor**:
    - `MonitorService.start()` accepteert nieuw `markets: List[str]` param (legacy `market: str` blijft werken als 1-element)
    - `_loop()` herschreven: per cycle één ticker-call voor àlle coins (`fetch_tickers(base_symbols)`) + per market een `_run_market_cycle()`. SELL/BUY checks per market, pot.market koppeling voor selectief sluiten
    - Status response heeft nu `markets: []` + `last_prices: {market: price}` velden
    - Persist state slaat markets-lijst op zodat auto-resume na backend-restart werkt
  - **Candle TTL-cache** in `fetch_candles()`: per (market, interval, limit) bewaart laatste fetch + TTL = candle-interval seconden. Bij rate-limit (429) returnt stale cache. Voorkomt Bitvavo ban bij multi-coin monitor
  - **Frontend**: coin-picker in Monitor-paneel (BCH/BTC/ETH/SOL/ADA toggle), status-bar toont alle actieve markets, beslissingen-lijst toont coin-tag per beslissing
  - Bekend: tijdens ontwikkelen hebben we Bitvavo rate-limit ban opgelopen (~12 min). Cache + shared-ticker-fix voorkomt herhaling
- 2026-05-20: **v4_token_potje_001 — Token-economie ↔ trading sync + schone reset**:
  - **Reset user-001**: 11 BCH-potjes (€66,42 capital) vervangen door schone start. Backup in `user_potjes.json.bak_pre_reset.json`
  - Nieuwe state: 10 potjes à €5,08 (basis €50,80) + overflow_pool €45,88 = **totaal €101,60** (matcht nieuwe Bitvavo EUR-saldo)
  - Pot-001 stats: 1 trade, 1 win, +€50,80 PnL (gerealiseerde winst eerste trade — €4,92 in pot, €45,88 in overflow voor toekomstige expansie)
  - **Baseline_eur** → €101,60 (was €50,80) zodat live-PnL vanaf nieuwe start telt
  - **Spark bonus tokens** (`/data/roar/roar_balances.json[spark_bonus]`):
    - `_mint_spark_bonus_tokens()` in `potjes.py`: bij netto trading-winst > 0 → cumulatieve teller. Per volle €5,08 → 1 bonus-token gemint naar Spark's eigen treasury
    - Auto-trigger in `close_pot()` na elke winstgevende SELL
    - Geen uitcash-UI nu — komt later bij wallet↔bank koppeling (Bitvavo IBAN)
    - Admin (gradatie 1) beslist wanneer Spark zijn spaarpot mag gebruiken
  - **Token-verkoop event-log** in `shop/routes.py sell_tokens()`: bij verkoop van ≥10 tokens → `freed_potje_slots` veld in transactie + description ("10 ROAR verkocht → 1 potje-slot vrij voor Spark"). Hard capital-vrijgave volgt later
  - **GET `/api/shop/token/spark-bonus`** — nieuwe endpoint toont Spark's bonus balance, cumulatieve winst, progress naar volgende token, laatste 5 mints
  - **Monitor herstart** met nieuwe baseline (real-mode, 10-potjes, BCH-EUR 15m)
  - Unit-getest: 3 mint-scenarios (€5,20 → 1 token, +€0,50 → 0 extra, +€4,50 → 1 extra). Sell event-log getest met 10-token transactie ✓
  - Bekend punt voor user: dynamische token-prijs (€10,22 nu) overruled BASE_PRICE €5,08 bij ≥10 tokens uit (spark_core / circulating). User wilde vast €5,08 — afstemmen of we BASE_PRICE altijd forceren of dynamiek behouden voor token-holder waardegroei
- 2026-05-20: **v4_dashboard_renew_001 + v4_analytics_layer_001**:
  - Dashboard Kennisbank kaart: label _"Te Herzien"_ (toonde 0 — frontend zocht naar bestaande `te_herzien` key die backend niet had) → _"Renew"_ gekoppeld aan `review_pending` (2986 kaarten)
  - Analytics → LAYER tab: was mock-data met "In ontwikkeling" banner → **live scan** via nieuw `GET /api/admin/architecture` endpoint
    - Scant `/app/backend/modules/` runtime: telt `.py` files, `@router.` decorators, size_kb per module
    - Scant `/app/frontend/src/components/` voor component-aantal per groep
    - Toont 4 lagen (Presentatie/API/Service/Data) met live metrics: 30 modules, 231 routes, 91 service files, 659.9 KB
    - Top-15 backend modules + alle frontend groups als sortable lijst (trade 28 routes, profile 23, chat 17...)
- 2026-05-20: **Roadmap-archeologie**:
  - 9 historische items uit code geïdentificeerd die NIET in roadmap stonden:
    - **v3.0 done**: `v3_012` (homoniem-flow), `v3_013` (Spark Leraar achievement +XP-bonus), `v3_028` (auto-zin-snap)
    - **v4.0 done**: `v4_013` (Spark Vocab), `v4_013c` (Fallback Service), `v4_016` (Insights Module), `v4_025` (User-time helper), `v4_grad_suggest_001` (gradatie-voorstel admin)
    - **v4.0 open**: `v4_017` (Advisor UI / Spark Inzichten pagina)
  - Code↔roadmap nu 100% gesynchroniseerd
  - Spark's user-000 profile.json gecorrigeerd: was te dun, nu mirror van rijke users.json entry (Core 4.1, missie, kernwaarden, 27150 XP, 4 achievements). Scratch entry-0 herzien om niet alsof Spark nieuw is te klinken
- 2026-05-20: **v4_spark_self_001 — Spark's eigen anker (folder + intents)**:
  - Folder `/data/users/user-000/` aangemaakt met `profile.json` (Spark's identiteit: naam, missie, geboortedatum, stem) + `scratch.json` (data-anker)
  - Nieuwe chat-intents in `spark_self_service.py`:
    - **Note**: _"Spark, onthoud voor jezelf: ..."_ / _"noteer voor jezelf: ..."_ / _"jouw observatie: ..."_ → parkeert entry in scratch.json
    - **Read**: _"wat heb je vandaag geleerd?"_ / _"wat zit er in jouw scratch?"_ / _"jouw observaties"_ → toont laatste 5 entries
  - Entries hebben `kind` (observatie/user_request/etc), `source` (user_naam), `ts`, `tekst`
  - Help-overzicht uitgebreid met "Spark's eigen anker" command
  - Klaar voor later: TTS voice-clone metadata, "wat-leer-ik-vandaag" auto-mining, Spark's reflectieve loop (v5)
- 2026-05-20: **Bug-batch fixes uit user-feedback**:
  - **#5 Help mist 'stop'**: nu vermeld als _"Stop een lopend proces — bv. 'stop' of 'klaar'"_
  - **#2 'ik ken Joel' geen relatie**: nieuwe patterns `PATTERN_KEN_NAAM` + `PATTERN_NAAM_KEN_IK` → relatie 'bekende' (`bekende` toegevoegd aan REL_TYPES). Werkt: "ik ken X" / "X ken ik" → auto-extract
  - **#12 Community-bericht in Spark Dashboard chat**: Dashboard widget gebruikt nu `?channel=spark` filter. `chat-history` endpoint heeft default `channel='spark'` parameter
  - **#4 Spark leert niet uit community**: `bots/community/send` retourneert nu `snap_candidates[]` (woorden ≥6 letters die niet in KB staan + niet stopwoord). Frontend kan later snap-flow triggeren op klik
  - **Vocab triggers UI werkt al** — user bewerkte in PRODUCTIE (preview heeft ander dataset). `/api/spark/vocab/{group}/{key}/add` endpoint draait correct. Ook generieke `/api/triggers/edit/vocab/...` route toegevoegd als fallback
- 2026-05-20: **Roadmap uitgebreid met 7 nieuwe pending items uit bugs**:
  - v4_potje_acting_as_001 (P1), v4_xp_correction_001 (P2), v4_glow_notify_001 (P1)
  - v5_parafrase_layer (P3, future), v6_roar_token_001 (P3), v6_grad2_potje_token (P3)
  - v4_voice_tab_relocate (P2)
- 2026-05-20: **Help + Roadmap up-to-date**:
  - `handle_help()` user-commands van 15 → 19 (Testament, Survivalgids, Documenten, Privacy/Cookies/Voorwaarden expliciet)
  - Admin-extra van 7 → 10 (credits via chat + via UI gesplitst, credits-bonus matching uitleg, Avatar Galerij beheer)
  - Hint toegevoegd: "Achtergrondgeluid blijft door na F5"
  - Roadmap: 8 open backlog-items zichtbaar als items (zodat "wat zou je willen doen" ze kan oppakken):
    - v4_gradatie_split (P0), v4_accounting_002, v4_kb_split_001, v4_snap_dedupe_001, v4_dq_b, v4_legal_pages_001, v4_personal_docs_003, v4_personal_docs_004
  - Roadmap summary: P0 blockers + P1 open expliciet benoemd
  - Notes opgeschoond: alleen 9 recente entries van deze sessie
- 2026-05-20: **v4_personal_docs_002 — Archief-UI integratie**:
  - Nieuwe tab **"Documenten"** in `ArchiefPage.js` naast Bestanden/Foto/Geluiden/Filmpjes/Gesprekken
  - Lijst toont aangemaakte docs (testament/survivalgids/etc) als cards: emoji, titel, versie, secties-aantal, grootte, last_updated
  - Klik card → detail view met alle secties (gele border-left accent), "📝 leeg" placeholders waar nog niets staat
  - **Download JSON** knop per doc (export voor backup/migratie)
  - Aparte sectie "Beschikbaar om aan te maken" toont nog-niet-bestaande types als ghost cards met hint _"maak X aan"_
  - "Beheer via chat" indicator ipv upload-knop (consistent met dat docs via chat-flow opgebouwd worden)
  - Klaar voor template-upload later: drop een JSON → vervangt mits structuur matcht
- 2026-05-20: **v4_personal_docs_001 — Persoonlijke documenten via chat (testament + survivalgids)**:
  - Generiek patroon: `DOC_TYPES` dict met label/emoji/default_secties/triggers — uitbreidbaar voor zorgvolmacht/wensen/levensoverzicht/etc.
  - Storage per user: `/data/users/{user_id}/documents/{doc_type}.json`
  - Chat-intents per doc-type:
    - **create**: "maak testament aan" / "survivalgids aanmaken" → skelet met default secties
    - **append**: "voeg toe aan testament: <tekst>" → nieuwe gedateerde sub-sectie + version++
    - **show**: "bekijk testament" → mooi geformatteerd
    - **delete**: "verwijder testament" → soft-delete (rename naar .deleted-{ts}.json)
  - Default secties:
    - Testament (6): Persoonsgegevens / Erfgenamen / Legaten / Executeur / Uitvaart / Overige
    - Survivalgids (7): Contacten / Documenten / Wachtwoorden / Verzekeringen / Bankzaken / Praktisch / Boodschap
  - API endpoints: `GET /api/personal-docs/{user_id}` (lijst) + `GET /api/personal-docs/{user_id}/{type}` (volledig doc)
  - Klaar voor archief-integratie (later): documenten kunnen in Mijn Archief → Bestanden tab verschijnen via list-endpoint
  - Klaar voor template-upload (later): user upload JSON van aanbieder → vervangt JSON mits structuur matched
- 2026-05-20: **v4_legal_help_001 — Help admin/user + legal triggers**:
  - `handle_help(is_admin)` toont nu **basis-help voor iedereen** + **admin-extra** sectie voor gradatie ≤ 2 (credits beheer, roadmap-bugs flow, trigger/vocab beheer, backup, gradatie-upgrades, storage cache)
  - Nieuwe legal-intent service (`legal_service.py`) detect: `privacy`, `cookies`, `voorwaarden`
  - 3 JSON-content files in `/data/system/legal_*.json` (versie 0.1-draft, klaar voor admin om in te vullen):
    - `legal_privacy.json` — wat slaat Spark op, niet deelt, jouw rechten
    - `legal_cookies.json` — sessionStorage/localStorage/server-side, geen tracking
    - `legal_voorwaarden.json` — wat is Spark, aansprakelijkheid, accountregels
- 2026-05-20: **Roadmap cleanup**:
  - `technical_debt`: 4 → 3 (oude GameTab/AdminTab refs verwijderd, WS-error weg)
  - `known_issues`: WebSocket dev-spam verwijderd, alleen KB duplicates blijft
  - `notes`: 22 → 12 (oude pre-mei items naar `historical_notes` archief)
  - `summary.v4.0_progress`: 83/104 (80%) na toevoegen van 8 nieuwe done-items deze sessie
- 2026-05-20: **v4_ambient_persist_001 — Ambient overleeft F5**:
  - Bug: ambient verdween na page-refresh; user moest "stilte" + "ambient 1 aan" opnieuw typen
  - Fix: `getAmbientPlayer()` singleton in `GesprekkenPage.js` persisteert nu `{url, label, volume}` in `localStorage` (key `spark_ambient_state`)
  - Bij init: `restoreFromStorage()` probeert direct te starten
  - Browsers blokkeren autoplay zonder user-gesture na F5 → fallback: nieuwe **amber pending-resume bar** met "🎵 Ambient — klik om door te spelen" + **Hervatten** en **Stoppen** knoppen
  - Auto-resume: globale `click/keydown/touchstart` listener probeert ambient meteen te starten bij eerste user-actie (ook typen in chatveld telt)
  - Stop wist localStorage zodat hij niet onverwacht na F5 terugkomt
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

## 2026-05-23 — KB sort-recent fix
- KB v1: `sort_by="recent"` (default) en `"updated"` nu correct geïmplementeerd in service.get_all() — sorteert op metadata.created_at / updated_at desc. Voorheen viel sort terug op file-order waardoor nieuwe kaarten "onzichtbaar" leken na opslaan.
- KB v2 inbox: sortering nu recent-aangemaakt eerst (footnote.aangemaakt_op / laatst_bewerkt_op desc), met fallback op priority + alfabetisch. Nieuwe handmatige kaart verschijnt direct bovenaan.
- KB v2 lades: sortering nu recent-bewerkt eerst i.p.v. alfabetisch.
- KB v2 "Nieuwe kaart" knop: opent de zojuist aangemaakte kaart automatisch in edit-mode in het detail-panel.
- KB v1 CreatePanel: na aanmaak schakelt automatisch terug naar "Alles" tab met sort=recent zodat de nieuwe kaart bovenaan zichtbaar is.

## 2026-05-23 — Spark World (D&D Bark MVP) + Auto-select Onbeantwoord

### Spark World MVP (v6_dnd_bark_001)
- Concept: D&D verhaal-stroom vanuit community-chat. Geen combat. User kiest een zintuig (Zie/Hoor/Voel) → typt wat hij beleeft → opgeslagen als D&D-bark-kaart.
- Backend: `/app/backend/modules/dnd/spark_world.py` (nieuw)
  - `POST /api/dnd/spark-world/start` — intro + 3 zintuig-knoppen + bestaande locked kaarten
  - `POST /api/dnd/spark-world/respond` — slaat user-input op als D&D-kaart (status: draft)
  - `POST /api/dnd/spark-world/cards/{id}/lock` — markeer kaart als canon (locked → verschijnt als keuze-knop bij volgende start)
  - `GET  /api/dnd/spark-world/cards?status=` — lijst kaarten
- 3 zintuigen + KB v2 lade-koppeling:
  - 👁️ ZIE  (cyan #06b6d4) → weten
  - 👂 HOOR (amber #f59e0b) → spreken
  - ❤️ VOEL (pink  #ec4899) → voelen
- Opslag: `/app/backend/data/cards/dnd/{card_id}.json` + `_index.json`
- Frontend: 
  - `/app/frontend/src/components/dnd/DnDBarkPanel.js` (nieuw)
  - "Spark World" knop in Community-tab (`GesprekkenPage.js`) → opent modal
  - Flow: intro → 3 zintuig-knoppen → tekst-input → opslaan → lock-knop → "Nieuwe bark" / "Klaar"
- Behavior-track: elke bark = `story_share` +1 counter, en `spark_world_card` observe-event
- Verified e2e via Playwright (login → community tab → modal → zie → bloemen → save → lock = LOCKED)

### KB v1 Auto-select Onbeantwoord (v6_kb_auto_select_unanswered)
- Bij switch naar "Onbeantwoord" tab opent de eerste onbeantwoorde kaart automatisch in de detail-modal, één keer per lijst-state. User hoeft niet door de index te scrollen.
- `/app/frontend/src/components/workspace/KennisbankPage.js` — useEffect met `autoOpenedFor` tracker zodat re-open na sluiten voorkomen wordt.

### Backlog updates
- Spark World v0.2: NPC-dialoog via Story Teller LLM, rugzak/inventory unlocks, image+audio media op bark-kaart
- D&D-kaart → KB v2 lade migratie (locked kaart automatisch in juiste lade kopiëren als kennis)
- Combat / dice-roll mechanic (later, alleen als het past)

## 2026-05-23 — D&D Galerij in Beheer + KB v2 Nieuwe-kaart venster

### D&D Galerij (v6_dnd_gallery_001)
- Locatie: **Beheer → Instellingen → Archief → Foto → "D&D Galerij"** subtab (naast Algemene foto's + Avatar Galerij)
- Toont alle Spark World bark-kaarten als grid met:
  - Filter chips: Alles / Draft / Locked (canon)
  - Per kaart: zintuig-kleur, icoon, titel, content-preview, status-badge
  - Klik kaart → detail-modal met inhoud + lock/unlock + delete (admin-only)
  - "Nieuwe D&D-kaart" → venster met leeg formulier (zintuig keuze + titel + content + "direct vastklikken" checkbox)
- Class-aanduiding: `game · D&D` (zoals user verzocht "uniek krijgen class game en D&D")
- Backend extra endpoint: `DELETE /api/dnd/spark-world/cards/{card_id}`
- Files: `frontend/src/components/admin/DnDGallerySection.js` (nieuw), `SystemArchive.js` (subtab toegevoegd)

### KB v2 Nieuwe-kaart Modal (v6_kbv2_newcard_modal_001)
- Vervangt `window.prompt()` met een echt venster (modal) met leeg in-te-vullen formulier:
  - Begrip (verplicht)
  - Laag 1 — korte uitleg (optioneel)
  - 5 lade-keuze knoppen (Inbox / Voelen / Spreken / Weten / Doen) — kaart wordt direct in juiste lade geplaatst
- Na opslaan opent kaart automatisch in bewerk-modus in detail-paneel zodat ws5/tags/media direct ingevuld kunnen worden
- File: `KennisbankV2Page.js` (NewCardModal component toegevoegd)

### Test status
- D&D Galerij + Nieuwe D&D-kaart formulier: e2e getest via Playwright (kaart aangemaakt, verschijnt in grid) ✓
- KB v2 Nieuwe-kaart venster: screenshot bevestigt leeg formulier met begrip/laag1/lade-keuze knoppen ✓

## 2026-05-23 — D&D game-cards in game.json + Boekhoud bedragen aanpasbaar

### D&D Galerij v2 (v6_dnd_gallery_002)
- Kleine zintuig+content formulier vervangen door **KB-stijl detail-paneel** (zelfde shape als KennisbankV2 detail panel)
- Velden: Begrip, Lagen 1-4, 5W (wie/wat/wanneer/waar/waarom/hoe), Tags, Media-placeholders, optioneel zintuig-kanaal
- "Mist nog" checklist + footnote (bron, vertrouwen %, locked/draft status)
- Lock/Unlock + Delete actie-knoppen
- **Aparte opslag**: `/app/backend/data/cards/dnd/game.json` (los van bark-kaarten en KB v2)
- Class = `"game"`, tag-prefix = `"D&D"` (altijd aanwezig zelfs als user tags wijzigt)
- Backend endpoints: `GET/POST/PUT/DELETE /api/dnd/spark-world/game-cards[/edit|/lock]`
- Split-view layout: lijst links + detail/edit rechts (zoals KB v2)

### KB v2 Nieuwe-kaart venster — reverted (v6_kbv2_newcard_modal_001 verwijderd)
- Geen aparte modal meer; nieuwe kaart opent direct in **bestaande detail-paneel** in edit-modus
- Window.prompt voor de begrip-naam blijft (snel en simpel), maar lagen/5W/tags/media via het detail-paneel zelf
- NewCardModal component verwijderd uit KennisbankV2Page.js

### Boekhoud — Bedragen aanpasbaar (v6_accounting_edit_001)
- Backend: nieuw `PUT /api/accounting/transactions/{tx_id}` endpoint dat amount/description/category/type/entity_id/date/btw_percentage kan wijzigen
- BTW wordt automatisch herberekend bij bedrag-update
- Frontend: per transactie-rij een **€✎ knop** naast de delete-knop; opent een prompt met huidige waarde
- Na opslaan worden kasboeken + summary auto-ververst
- Geverifieerd via PUT-test (round-trip €45 → 99.99 → 45 hersteld)

## 2026-05-24 — KB v1 → KB v2 Herzien-flow

### Herzien-knop (v6_kbv2_herzien_001)
- Naast "Verversen" in KB v2 nu paarse knop **"Herzien (KB v1)"**
- Klik → backend trekt 1 KB v1 kaart die nog niet gemigreerd is (`unanswered_first` strategy)
- Kaart opent in het bestaande NewCardInline rechter-paneel met:
  - Pre-filled begrip, lagen, ws5, tags vanuit v1
  - **Topic-veld** (alleen in herzien-modus) — stuurt auto-classify
  - Paarse banner met v1-id, "nog X te gaan", suggested auto-lade
  - "Skip → volgende" knop
- Bij **Promoveer**: backend maakt v2-kaart aan, classified naar voelen/spreken/weten/doen
  obv topic + tags keyword-mapping. V1 kaart wordt gemarkeerd met `migrated_to_v2 = true`
  + `v2_card_id` + `v2_lade` + `migrated_at`. De v2 kaart bevat footnote met
  *"Vorige versie (v1): kb-skel-..."* zodat herkomst zichtbaar blijft.

### Backend endpoints
- `GET  /api/kb/v2/herzien/next?strategy=unanswered_first|oldest|random`
- `POST /api/kb/v2/herzien/promote` — body: v1_id, begrip, lagen, ws5, tags, topic, target_lade (optioneel)
- `POST /api/kb/v2/herzien/skip`

### Topic → Lade mapping
- voelen: emotie, gevoel, relatie, verbinding, empathie, compassie
- spreken: taal, communicatie, gesprek, schrijven, praten
- weten: kennis, systeem, feit, logica, definitie, concept, model, theorie, geheugen
- doen: gedrag, actie, praktijk, uitvoeren, stap, methode, proces
- Default: weten

### Test status
- E2E getest met Playwright (5288 → 5287 → restore) ✓
- Topic "systeem" + laag 1 → correct gepromoot naar lade weten ✓
- V1 markering werkt (footnote toont "Vorige versie (v1): kb-skel-..." op v2-kaart) ✓

### Files
- `backend/modules/kb_v2/routes.py` (+ herzien endpoints + topic→lade mapping)
- `frontend/src/components/workspace/KennisbankV2Page.js` (Herzien knop, state, handlers, NewCardInline-uitbreiding)

## 2026-05-26 — Notitie edit + Avatar edit (quick wins sessie 12)

### v6_note_edit_001 — Notitie/Taak inline edit
- **Probleem**: Notities en taken konden alleen aangemaakt of verwijderd worden, niet meer bewerkt na opslaan.
- **Fix**: Pencil-knop op elke `NoteItemCard` opent inline edit-modus (titel + inhoud voor notities, alleen titel voor taken). Save → `PUT /api/notes/update/{id}?user_id=...` of `PUT /api/notes/tasks/update/{id}?user_id=...`. Backend endpoints bestonden al; alleen frontend UI ontbrak.
- **UI-extra**: Een klein `(bewerkt)` label verschijnt op een notitie zodra `updated_at` ingevuld is, met tooltip naar exact moment van laatste edit.
- **Files**: `frontend/src/components/workspace/NotitiesPage.js`
- **Backend test (curl)**: ✓ Aanmaken → update titel+inhoud → update bevestigd → delete

### v6_avatar_edit_001 — Avatar edit in Beheer→Archief→Avatar Galerij
- **Probleem**: In Beheer→Archief→Foto→Avatar Galerij was alleen toevoegen/verwijderen mogelijk; titel/tags/bot_owner wijzigen vereiste navigatie via Beheer→Gebruikers→Avatar Beheer.
- **Fix**: Bewerk-knop (pencil) op elke avatar-tile (zowel user- als system-avatars). Modal toont:
  - Titel (verplicht, alle avatars)
  - Tags (komma-gescheiden, alle avatars)
  - Bot-eigenaar (alleen system/locked avatars — leeg laten = ontkoppelen)
  Save → `PATCH /api/avatar/gallery/{id}` met `viewer_id` voor admin-guard. Verwijder-knop blijft uitsluitend op user-tab (system blijft beschermd).
- **Files**: `frontend/src/components/admin/AvatarGallerySection.js`
- **Backend test (curl)**: ✓ PATCH met nieuwe titel/tags → success, en restore werkt.

## 2026-05-26 — Glow-nav MVP live (v6_glow_nav_001)

### Wat werkt nu:
1. **Backend `/api/tabs/registry`** retourneert 23 tabs (alle frontend nav-items) met kebab-case IDs die exact matchen met `data-testid="nav-{id}"`.
2. **Backend `/api/tabs/navigate`** matcht een vrije vraag op label/id/aliases en geeft `{navigate_to, glow_target}` terug.
3. **Chat-flow integratie** (`modules/chat/routes.py`): nav-trigger detectie (`waar is/zijn`, `waar vind/kan ik`, `ga naar`, `open de/tab/mijn`, `ik wil naar`, `breng me naar`, `laat zien waar`) staat **vóór** capability-router & kbv2-router → kan niet worden opgegeten door snap/intent.
4. **Frontend `GesprekkenPage`**: bij `data.type === 'navigate_tab'` dispatcht een `window` custom event `spark:nav-glow` met `{ targetId, navigateTo, matchedTab }`.
5. **Frontend `MainLayout`**: luistert globaal naar dat event → voegt 6s pulserende amber `spark-nav-glow` CSS-class toe op de matchende sidebar-button (via `data-testid` lookup), scrollt naar het item, en roept 700ms later `onNavigate(item.id, item.path)` aan voor automatische tab-switch.
6. **CSS-keyframes** in `index.css`: `@keyframes spark-nav-pulse` met box-shadow-pulse in amber (rgba(245,158,11)).

### Visueel bevestigd met screenshot:
- *"waar is dagboek"* → Spark antwoordt "De **Dagboek**-tab vind je hier: /dagboek. Ik laat 'm even oplichten voor je." → Dagboek-button in sidebar pulseert amber → 700ms later: Dagboek-pagina opent.

### Backend-tests (curl, 9 queries):
- `waar is mijn wallet` → nav-wallet → /modules/wallet ✓
- `waar zijn mijn notities` → nav-notities → /notities ✓
- `waar vind ik de agenda` → nav-calendar → /calendar ✓
- `ga naar dagboek` → nav-dagboek → /dagboek ✓
- `open de kennisbank` → nav-knowledge-v2 → /knowledge ✓
- `breng me naar trade` → nav-trade → /modules/trade ✓
- `ik wil naar de winkel` → nav-winkel → /modules/winkel ✓
- `open de boekhouding` → nav-boekhouding → /modules/boekhouding ✓
- `hallo spark hoe gaat het` → greeting (correct, geen nav) ✓

### Files
- `backend/modules/glow_nav/__init__.py` (defaults uitgebreid 15→23 tabs + IDs gesynced)
- `backend/modules/chat/routes.py` (nav-trigger block gehoist naar boven capability-router)
- `frontend/src/components/workspace/GesprekkenPage.js` (event-dispatch)
- `frontend/src/components/layout/MainLayout.js` (event-listener + auto-navigate)
- `frontend/src/index.css` (pulse keyframes)

## 2026-05-26 — Synapse + Container architectuur (sessie 12+, F1-F7)

### 🧬 Concept (door Willem)
*"Synapslaag — Spark moet zichzelf kunnen lezen. Mappen geven zichzelf meta-data, hij hoeft het niet uit z'n hoofd te kennen. En dit container-patroon is universeel: user, shop, asset, kb_card, card_deck, chat_thread, trade_bot — alles met eigen meta + (later) eigen encryption."*

### Wat is er nu live (na sync van productie-data 2026-05-26 15:38):
1. **`_meta.json` per map** — backend/modules (50), frontend/components (12), backend/data (28). Totaal 90 containers gescand.
2. **Auto-detectie 418 endpoints** uit `@router.<verb>` decorators.
3. **SYNAPSE.json aggregator** op `/app/memory/SYNAPSE.json` — Spark's "ik weet wat ik heb".
4. **Spark leest zichzelf in chat**: 6 intents werken ("wat hebben we", "is X af", "waar woont X", "wat doet X", "lijst skeletons", "lijst verouderd").
5. **Auto-touch** in `core/storage.py` — elke save_json bumpt parent _meta.json automatisch.
6. **Container service** met universele CRUD voor user/shop/asset/card/thread.
7. **User-delete is nu bug-vrij**: container weg + cross-refs anonimiseren in bugs/community + bestanden weg uit agenda/dagboek/chat-prive.
8. **Encryption-slot in elke meta** — leeg, klaar voor F2F-feature later (geen rework).
9. **Winkelstraat hook**: shop-create → auto shop-container; shop-close → auto tag-for-deletion.
10. **UI Synapse-tab** in Beheer→Instellingen met filter, search, status-tellers, edit-modal.

### Endpoints (allemaal getest)
- `GET /api/synapse/scan` — trigger full scan + rebuild
- `GET /api/synapse/tree` — volledige boom
- `GET /api/synapse/search?q=...` — zoek in alle meta
- `GET /api/synapse/summary` — lichte stats
- `POST /api/synapse/tag` — update doel/status/footnote/blueprint/tags
- `POST /api/synapse/touch` — handmatige touch
- `POST /api/container/{type}` — create (user/shop/asset/card/thread)
- `GET /api/container/{type}` — list
- `GET /api/container/{type}/{id}/meta` — read meta
- `PATCH /api/container/{type}/{id}/meta` — update
- `POST /api/container/{type}/{id}/tag-for-deletion` — revertable
- `DELETE /api/container/{type}/{id}` — admin-only, archive + cross-ref clean

### Files
- `backend/modules/synapse/{__init__.py, schema.py, scanner.py, aggregator.py, touch.py, chat_handler.py, routes.py}`
- `backend/modules/container/{__init__.py, service.py, user_helper.py, routes.py}`
- `backend/modules/core/storage.py` (touch-hook bij save_json)
- `backend/modules/chat/routes.py` (synapse intent-router vóór capability)
- `backend/modules/winkelstraat/__init__.py` (auto shop-container hook)
- `frontend/src/components/admin/SynapseTab.js` + `InstellingenPage.js` (nieuwe tab)
- `backend/server.py` (synapse + container router-includes)

### F2F-roadmap (placeholder voor later)
Encryption-slot ligt klaar in elke `_meta.json`. Wanneer user F2F-mode activeert:
- `meta.encryption.enabled = true`
- `algorithm = "AES-256-GCM"`
- `key_holder = "user-<id>"`
- Container-data wordt encrypted at-rest, alleen user kan ontsleutelen.
- Spark systeem ziet alleen meta-shell, geen container-inhoud.

Geen rework nodig — alleen het slot vullen.

## 2026-05-26 — Synapse Auto-Enricher + KB v2 Laagsgewijs Uitleg

### Auto-enricher (v6_synapse_002)
Synapse-meta wordt nu **automatisch gevuld** met betekenisvolle `doel`-omschrijvingen:
- Leest module-level docstring uit `__init__.py` (of routes.py / service.py als fallback)
- Voor frontend: top JSDoc-blok uit eerste .js/.jsx file
- Voor data-stores: lijst van aanwezige JSON-bestanden
- **53 modules** gevuld in eerste run, **78 blueprint-stubs** aangemaakt

**Blueprint-stubs**: per module een `/app/memory/blueprints/{naam}.md` met:
- 🎯 Doel
- ✅ Wat werkt al
- 🔌 Auto-gedetecteerde endpoints
- 📝 TODO / open items
- ⚠️ Splitting-trigger (warning bij > 4 subdirs of > 10 endpoints)
- 🔐 Encryption-plan (F2F-roadmap)
- 🧬 Relaties

**Endpoint**: `POST /api/synapse/enrich`

**Effect in chat**: Spark zegt nu *"glow_nav — Glow-Nav service (v6_glow_nav_001) — Spark wijst via chat de juiste UI-tab aan"* in plaats van *"glow_nav — geen doel-omschrijving"*.

### KB v2 Laagsgewijs Uitleg (v6_kbv2_tell_layer_followup_001)
Spark's antwoorden zijn nu **gelaagd** en hebben **context-geheugen** (10 min):

```
User: "vertel kort over identiteit"
Spark: [laag1] Identiteit is het geheel van eigenschappen, kenmerken en ervaringen...

User: "vertel meer"
Spark: [laag1 + laag2] ...gebruikt om te beschrijven hoe iemand zich verhoudt...

User: "ga dieper"
Spark: [laag1 + laag2 + laag3] ...

User: "vertel volledig"
Spark: [alle 4 lagen]
```

**Triggers**:
- depth 1: `vertel kort`, `in 1 zin`, `samenvatting van`, `korte uitleg`
- depth 2: `vertel meer`, `leg uit`, `beschrijf`, `iets meer`
- depth 3: `vertel diep`, `ga dieper`, `ga dieper in`, `diep uitleg`
- depth 4: `vertel volledig`, `vertel alles over`, `alles wat je weet over`

Werkt met onderwerp ("vertel meer over identiteit") en zonder ("vertel meer" — gebruikt `session_state.last_kbv2_card_id`).

### Files
- `backend/modules/synapse/enricher.py` (auto-doel + blueprint-stubs)
- `backend/modules/synapse/routes.py` (POST /api/synapse/enrich)
- `backend/modules/kb_v2/hooks.py` (cmd_tell_layer + fallback_card_id + uitgebreide triggers)
- `backend/modules/chat/routes.py` (state.last_kbv2_card_id doorgeven aan handler)
- `/app/memory/blueprints/*.md` (78 nieuwe stubs)

## 2026-05-27/28 — Sessie 13: Roadmap-batch (P1 finish + P2 quick wins + Sessie C)

### P1 items afgemaakt
- **v6_voice_kbv2_link_001**: STT-endpoint accepteert optionele `card_id` + `user_id`. Bij meegegeven → snippet opgeslagen via `save_voice_snippet` in `/data/dialogen/voice_snippets/YYYY-MM-DD/`.
- **v6_conv_state_001**: `session_state.py` heeft `set_last_question` / `get_last_question` met 2-min expire window. Verlopen vragen worden in `get_state` auto-gefilterd.
- **v6_audit_001**: `modules/audit/__init__.py`. Endpoints `/api/audit/weak-triggers`, `/self-learning`, `/summary`. 5307 KB-entries gescand, 2239 (42%) missen laag1. Reports in `/data/system/audit_reports/`.
- **v6_perks_001**: `modules/perks/__init__.py` met 8 declarative perks. Combineert `min_gradatie + required_behaviors + blocked_by_behaviors`. Endpoints `/api/perks?user_id=...`, `/check/{perk_id}`, `/user/{user_id}`.

### P2 quick wins
- **v6_traced_rollout_001**: `@traced` op login/logout (auth) + quick_buy_potje/bot_start/bot_stop (trade).
- **v6_scheduler_001**: Background asyncio-loop elke 5 min:
  - 21:00 NL roundup-bark door Boekhouder in community
  - Madelief scant nieuwe error-logs en barkt bij errors (max 3/bark)
  - Persistent state-file `scheduler_state.json` voorkomt dubbele runs

### Sessie C — Bonus
- **v6_capabilities_handlers_002**: 5 nieuwe Spark-handen handlers (kasboek_overzicht, agenda_vandaag, kennis_inbox_status, bots_status, audit_health). 2/5 chat-matched, 3/5 wachten op intent-tuning.
- **v6_container_migrate_001**: `container/user_helper.py::migrate_user_legacy()` + bulk `migrate_all_users()`. Endpoints `POST /api/container/user/migrate` + `/migrate-all`. Kopieert legacy agenda/dagboek met footnote. Idempotent.
- **Help-per-gradatie**: bevestigd al volledig live uit eerdere sessie (32 commands, gradatie-gefilterd).

### Skip / placeholder
- **SEPA-mint**: placeholder gehouden — Tikkie-flow blijft fallback voor bank-uitcash (gebruikersbeslissing).
- **Winkelstraat frontend**: backend volledig klaar (incl. shop-container hook); UI nog niet aangepakt — heeft route+design-keuzes nodig die in volgende sessie passen.

### Files in sessie 13
- `backend/modules/audit/__init__.py` (NIEUW)
- `backend/modules/perks/__init__.py` (NIEUW)
- `backend/modules/scheduler/__init__.py` (NIEUW)
- `backend/modules/chat/session_state.py` (last_question + 2-min window)
- `backend/modules/voice/__init__.py` (STT + card_id linking)
- `backend/modules/auth/routes.py` (@traced login/logout)
- `backend/modules/trade/routes.py` (@traced bot_start/stop/quick_buy)
- `backend/modules/chat/capability_handler_service.py` (+5 handlers)
- `backend/modules/container/user_helper.py` (+migrate functies)
- `backend/modules/container/routes.py` (+migrate endpoints)
- `backend/server.py` (audit + perks routers + scheduler startup)
- `backend/data/system/command_registry.json` (+5 capabilities)

## 2026-05-28 — Trader Fix (na vraag van Willem)

### v6_trade_minorder_001 — SOL min-buy crash fix
- Probleem: Bitvavo eist `minimumOrderInQuoteAsset` per markt (SOL/BTC/ETH ≈ €5). Bij €1-2 trades → cryptische error.
- Fix: `get_market_min_quote(market)` met 1u cache van `/v2/markets`. Pre-check bij BUY → friendly error met tip.
- Fallback-tabel voor offline cache: BTC/ETH/SOL/ADA/XRP/BCH = €5.

### v6_trade_sell_balance_001 — Sell balance mismatch fix
- Probleem: potje toonde X tokens, maar Bitvavo had iets minder door rounding/fees → sell crashte op "insufficient balance".
- Fix: voor SELL fetch eerst actuele Bitvavo balance via `fetch_bitvavo_balance`. Clamp `min(requested, actual) * 0.999`.
- Errors hebben nu `error_code`: `MIN_QUOTE`, `NO_BALANCE`, `ZERO_AFTER_CLAMP`, `BITVAVO_HTTP_ERROR`, `EXCEPTION`.
- Trade-record bevat `requested_amount` + `effective_amount` voor traceability.

### Test status
- Preview: unit-test bevestigt min-quote fallback werkt (€1 SOL-buy → MIN_QUOTE error met tip).
- Productie: testen na redeploy. Sell-balance pre-check vereist live Bitvavo credentials.

### Files
- `backend/modules/trade/monitor.py` (helper + buy/sell pre-checks + error-codes)

## 2026-05-28 — Sessie 13b: Potjes €10 + Pot 1 Staking + Trader Help + UI fixes

### v6_potje_size_10_001 — Potjes van €10
- `START_AMOUNT 5.08 → 10.0` (was eigenaardige opstart-waarde, nu schoon).
- Admin-endpoint `POST /api/trade/potjes/{user_id}/resize-to-default` zet alle potjes op €10. Faalt veilig bij open posities.

### v6_pot1_staking_lock_001 — Pot 1 staking-lock
- Eerste potje (laagste index OF eerste in lijst) krijgt `pot_locked=True, lock_reason="staking_anchor"`.
- `find_available_potje` skipt locked potjes (zowel monitor-bot als quick-buy).
- Backfill robuust: vindt eerste potje ook in legacy data zonder `index`-veld (productie-data).
- Toggle endpoint `POST /api/trade/potjes/{user_id}/toggle-lock` met body `{pot_id, locked, lock_reason}`.

### v6_trade_help_001 — Trader Help
- `modules/trade_help/__init__.py` — 7 secties:
  1. Het potjes-systeem (€10 elk + Pot 1 staking)
  2. BUY-logica (dip-detectie, min-quote check, cycle-lock)
  3. SELL-logica (trailing stop, balance-pre-check, force-sell)
  4. Modes & Knoppen (Monitor/Stop/QuickBuy/Force-sell/Resize)
  5. Veiligheid & Limieten (operatorId, token-gate, trade-history)
  6. Spark's stem in de trades (Boekhouder + Madelief)
  7. Tips
- Endpoints `GET /api/trade/help` (volle JSON) + `/markdown` (één string).
- Chat-router pakt triggers ("hoe werkt de trader/bot/potjes?") en plakt eerste 3 secties + deep_link.

### v6_wallet_button_order_001 — Wallet knop-volgorde
- Volgorde: **Storten** (+) → **Opnemen** (−) → [**Mint** admin] → **Gift** (rechts).

### v6_roar_price_display_001 — ROAR-prijs uitleg
- WinkelPage text: "1 ROAR = aandeel in Spark Core kapitaal".
- Tooltip toont formule: `€{spark_core} ÷ {circulating} = €{prijs}`.
- "Jouw tokens" → "Jouw bezit", "Waarde" → "Tegen huidige prijs".

### v6_traced_rollout_002 — @traced overige
- `shop/gift.py`: `create_gift`, `accept_gift`.
- `kb_v2/routes.py`: `classify`, `edit`, `delete_card`.

### Files
- `backend/modules/trade/potjes.py` (potje €10 + lock + resize)
- `backend/modules/trade/routes.py` (resize + toggle-lock endpoints)
- `backend/modules/trade_help/__init__.py` (NIEUW)
- `backend/modules/chat/routes.py` (trader-help intent)
- `backend/modules/shop/gift.py` (@traced)
- `backend/modules/kb_v2/routes.py` (@traced)
- `backend/server.py` (trade_help router include)
- `frontend/src/components/modules/WalletPage.js` (knop-volgorde)
- `frontend/src/components/modules/WinkelPage.js` (prijs-uitleg)

### Testing
- Backend lint: all checks passed
- Pot 1 auto-locked op productie-data (Willem): bevestigd
- Resize endpoint blokkeert bij open posities: bevestigd
- Chat "hoe werkt de bot?" → `type=trader_help`: bevestigd
- Wallet UI screenshot: knop-volgorde Storten→Opnemen→Gift correct (rechts)
