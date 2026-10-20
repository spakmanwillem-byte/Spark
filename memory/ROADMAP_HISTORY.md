# Spark Core 2.0 — Roadmap History (afgeronde sessies)

> Chronologisch (nieuwste bovenaan). Voor huidige sessie: zie `ROADMAP_CORE.md`.
> Voor wat bij elke sessie gebouwd is met detail-context: zie `CHANGELOG.md`.

---



## ✅ SESSIE 54 — Prod-merge #4 + shop-owner uploads + user-container hyperlinks (3 aug)

### Prod-merge #4
- `spark_backup_changes_20260803_071200.zip` — 106 files, 8.3MB (pure data, geen code).
- Backup: `/app/_backup_before_prod_merge_20260803_071830/` (data + memory).
- Rsync-merged: knowledge v2 (KB inhoud verrijkt in prod), chat logs, community messages, trader state/anker/context_cache, users.json (+1 nieuwe user `user-7b532909`), financial user_potjes, shadow events, spark_planner threads, boekhouder weekly reports, price_snapshots, SYNAPSE.json.
- **Bewust NIET aangeraakt** (zaten niet in zip): `wallet/wallets.json`, `wallet/user_wallets.json`, `roar/roar_balances.json`, `shop/shops.json` — zo blijft Maaike's kleur-keuze (#61d7ff) en de wallet-diagnose intact.
- Health: 25 users, 3 shops (Roadkillshop / Spark Shop / Full of Joy), roar balances Spark=7 / Willem=3 / user-a0ee2d7e=2 (matcht papertrail).
- Willem heeft trader overal gestopt (`bots_registry_state.json` reflecteert dat).

### v12_shop_owner_perms_001 — Shop-owner beheer
Backend `_require_admin_or_shop_owner(viewer_id, shop_id)` helper. Product CRUD (POST/PUT/DELETE) + image upload/delete gated op admin OF owner. Maaike kan haar Full of Joy zelf beheren zonder admin-rechten. Winkelstraat (front) blijft strict admin-only voor CRUD.

### ShopTabView beheer-header (in Archief)
Shop-naam prominent, logo klik-to-upload, 8 accent-kleur-presets + colorpicker, nieuw-product knop in accent-kleur. Live PATCH via `/api/winkelstraat/shops/{id}` + `/logo`.

### v12_shop_image_owner_container_001 — Foto's in user-container
Product-images verhuisd van globale `/data/system_archive/foto/` naar user-eigen `/data/users/{owner}/archive/foto/{file_id}.{ext}`. Geregistreerd in user's `_index.json` met tags `shop_product` / `shop_{id}` / `product_{id}`. URL = `/api/archive/{owner}/file/{file_id}` (hyperlink). Bij shop/user-verwijdering verdwijnen alle foto's automatisch mee. End-to-end getest.



### v12_admin_toggle_001 — Admin Toggle Audit
Legacy `gradatie <= 1/2` en `user.admin` checks vervangen door AuthContext `isAdmin` (= `admin_capable && adminModeActive`). Admin-UI verschijnt nu **alleen** met "Admin aan" toggle actief, ongeacht gradatie.
Aangepaste files:
- `modules/TraderPage.js` — Bitvavo Reconciliatie panel + wallet-switch + admin stats
- `modules/WalletPage.js` — Spark-view switch, Mint-knop
- `modules/BoekhoudPage.js` — summary/transactions tabs, Tikkie inbox
- `modules/AchievementsPage.js` — admin edit-pencil op cards (was legacy `user.admin`)
- `modules/WinkelPage.js` — product edit/delete/create, image upload
- `workspace/NotitiesPage.js` — deploy-tab, bug-list, bug status/delete
- `workspace/RoadmapPage.js` — bug-list vs bug-mine
- `profile/UserProfilePage.js` — AlgemeenTab + AvatarTab isAdmin prop
- `admin/InstellingenPage.js` — SystemArchive, AchievementBlueprint, FinanceHub (was `user?.admin`)

### v12_chat_visibility_001 — Chat zichtbaarheid per user
Nieuw panel in Mijn Profiel → Instellingen ("Chat zichtbaarheid"):
- **Community chat**: default `false`, alleen toggle-baar bij gradatie ≤ 5 (anders gedisabled met uitleg)
- **Privé gesprekken**: default `true`, alle gradaties
- Backend: `UIPreferences` model + `DEFAULT_UI_PREFS` uitgebreid met `community_chat_enabled` + `private_chats_enabled`. Bestaand `/api/profile/ui-preferences/{user_id}` endpoint (GET/PUT). Getest via curl ✓.

### Wallet-diagnose (READ-ONLY snuffel — nog geen wijzigingen)
Papertrail-analyse. **Er is niets kwijt**, wel architectuur-drift:

| File | Rol | Willem (user-001) |
|---|---|---|
| `roar/roar_balances.json` `balances` | **AUTHORITATIVE** (papertrail-derived, 19 tx + mint_history + admin_log) | 3 ✅ |
| `wallet/user_wallets.json` `spark_tokens` | Spiegel/cache van roar_balances (gesynct via cleanup_reconciliation) | 3 ✅ |
| `wallet/wallets.json` `spark_tokens` | **STALE FIELD** — nooit meer geüpdatet bij gift_accept/admin_grant | 10 ❌ |

9 users hebben drift tussen wallets.json en user_wallets.json.
Wallet-ID formaat: 2 gemigreerd naar `wal-*` (user-000/user-001), 13 nog legacy.

### 📋 Voor Sessie 54 — Wallet-cleanup (P0)
1. **Grep-rapport**: welke endpoints/frontend-code lezen nog `wallets.json['spark_tokens']`? Nodig voordat we het veld verwijderen.
2. **`spark_tokens` uit `wallets.json` slopen**: single source of truth wordt `roar_balances.json['balances']`. `user_wallets.json` blijft als cache (met `_synced_by`-flag), of ook stripped.
3. **Root-cause fix**: `gift_accept` + `admin_grant` moeten `roar_balances` als bron gebruiken, niet `wallets.json` bijwerken. Voorkomt herhaling.
4. **Wallet-ID migratie afronden** (13 users → `wal-*`) — pas ná stap 1-3, laagste risico daarna.



## ✅ SESSIE 53 — Admin Toggle Audit + Chat-zichtbaarheid + Wallet-diagnose (1 aug)

### v12_admin_toggle_001 — Admin Toggle Audit
Legacy `gradatie <= 1/2` en `user.admin` checks vervangen door AuthContext `isAdmin` (= `admin_capable && adminModeActive`). Admin-UI verschijnt nu **alleen** met "Admin aan" toggle actief, ongeacht gradatie.
Aangepaste files:
- `modules/TraderPage.js` — Bitvavo Reconciliatie panel + wallet-switch + admin stats
- `modules/WalletPage.js` — Spark-view switch, Mint-knop
- `modules/BoekhoudPage.js` — summary/transactions tabs, Tikkie inbox
- `modules/AchievementsPage.js` — admin edit-pencil op cards (was legacy `user.admin`)
- `modules/WinkelPage.js` — product edit/delete/create, image upload
- `workspace/NotitiesPage.js` — deploy-tab, bug-list, bug status/delete
- `workspace/RoadmapPage.js` — bug-list vs bug-mine
- `profile/UserProfilePage.js` — AlgemeenTab + AvatarTab isAdmin prop
- `admin/InstellingenPage.js` — SystemArchive, AchievementBlueprint, FinanceHub (was `user?.admin`)

### v12_chat_visibility_001 — Chat zichtbaarheid per user
Nieuw panel in Mijn Profiel → Instellingen ("Chat zichtbaarheid"):
- **Community chat**: default `false`, alleen toggle-baar bij gradatie ≤ 5 (anders gedisabled met uitleg)
- **Privé gesprekken**: default `true`, alle gradaties
- Backend: `UIPreferences` model + `DEFAULT_UI_PREFS` uitgebreid met `community_chat_enabled` + `private_chats_enabled`. Bestaand `/api/profile/ui-preferences/{user_id}` endpoint (GET/PUT). Getest via curl ✓.

### Wallet-diagnose (READ-ONLY snuffel — nog geen wijzigingen)
Papertrail-analyse. **Er is niets kwijt**, wel architectuur-drift:

| File | Rol | Willem (user-001) |
|---|---|---|
| `roar/roar_balances.json` `balances` | **AUTHORITATIVE** (papertrail-derived, 19 tx + mint_history + admin_log) | 3 ✅ |
| `wallet/user_wallets.json` `spark_tokens` | Spiegel/cache van roar_balances (gesynct via cleanup_reconciliation) | 3 ✅ |
| `wallet/wallets.json` `spark_tokens` | **STALE FIELD** — nooit meer geüpdatet bij gift_accept/admin_grant | 10 ❌ |

9 users hebben drift tussen wallets.json en user_wallets.json.
Wallet-ID formaat: 2 gemigreerd naar `wal-*` (user-000/user-001), 13 nog legacy.

### 📋 Voor Sessie 54 — Wallet-cleanup (P0)
1. **Grep-rapport**: welke endpoints/frontend-code lezen nog `wallets.json['spark_tokens']`? Nodig voordat we het veld verwijderen.
2. **`spark_tokens` uit `wallets.json` slopen**: single source of truth wordt `roar_balances.json['balances']`. `user_wallets.json` blijft als cache (met `_synced_by`-flag), of ook stripped.
3. **Root-cause fix**: `gift_accept` + `admin_grant` moeten `roar_balances` als bron gebruiken, niet `wallets.json` bijwerken. Voorkomt herhaling.
4. **Wallet-ID migratie afronden** (13 users → `wal-*`) — pas ná stap 1-3, laagste risico daarna.

## ✅ SESSIE 52 SLOT — Admin/UX-split + prod-merge + shop-scope (1 aug)

### Prod-merge #3
- `spark_backup_changes_20260801_163713.zip` — 1540 files (1070 backups geskipt). 435 identiek, 36 gemerged (log-tails, cache, timestamps, users.json `last_active`).
- Backup: `data/_backup_before_prod_merge_20260801_164231/` (211MB) voor rollback.

### Bug: Winkel-scope + shop-delete permissie
- **v11_shop_scope_001** — GET `/api/shop/products` returnde altijd Roadkill-producten voor NIEUWE shops. Frontend WinkelPage geeft nu `shop_id` mee, `_shop_products_path()` retourneert per-shop path (ook voor lege). Product POST/PUT/DELETE + image-DELETE geven `shop_id` mee → correcte container.
- **v11_shop_delete_admin_only_001** — Legacy grad-2 fallback in `_require_admin` weggehaald. Alleen strict `admin===true` mag shops/produkten deleten. Familie (Heidi/Lotus/Maaike/Joy/Gerben) geblokkeerd. Frontend `WinkelstraatTab` gebruikt nu `isAdmin` uit AuthContext (v11 toggle) i.p.v. legacy `user.admin`.
- Maaike's shop-0aff7155cd hersteld in shops.json (bestond op disk, ontbrak in registry).

### UI-verplaatsingen (Willem's structuur)
- **v11_shop_tab_in_archief_001** — Per-user "Winkel: [naam]"-tab in Workspace → Archief. Reuseert `ShopTabView` component.
- **v11_spark_shop_admin_001** — Spark Shop beheer in Beheer → Instellingen → Archief → Spark Shop tab. Zelfde component. ROAR Token (was in Willem's shop) verhuisd naar shop-spark.
- **v11_instellingen_split_001** — Mijn Profiel → Instellingen opgeschoond. `AdminPasswordSection` + `AdminGrantSection` → verhuisd naar Beheer → Gebruikers → nieuwe "Admin" tab per user. Bitvavo-connectie kader weg (staat al in Beheer → Instellingen → Integraties).
- **v11_dashboard_admin_toggle_001** — Dashboard admin-widgets gaten nu op toggle-gebaseerde `isAdmin` uit AuthContext, niet meer op `gradatie ≤ 2`. Familie zonder toggle ziet clean dashboard.

### UX-fixes
- **v11_papertrail_names_001** — Papertrail widget toont nu `→ Spark +1` i.p.v. `mintuser-000+1`. Backend `/papertrail-overview` verrijkt tx met `user_naam/from_naam/to_naam`. Direction-arrows: → in, ← uit, × burn.
- **v11_potjes_reconcile (eenmalig)** — Willem 1 pot → 3, Spark 10 pot → 7. Aligned met token-balances. `capital_baseline.json` bijgewerkt (Willem €30, Spark €70). Root-cause (gift/admin_grant verplaatst token maar niet pot) staat nog open.
- **v11_reconcile_admin_only_001** — Bitvavo Reconciliatie-panel op Trader-pagina alleen zichtbaar voor grad-1.
- **v11_grad7_archief_001** — Grad 7 ziet nu Archief-tab (gespreksgeschiedenis).
- **v11_community_only_items_001** — Achievements + Leaderboard verborgen voor grad 6/7 (pas vanaf grad 5).
- **v11_spark_admin_only_001** — Hele Spark AI sidebar-sectie (Brein/Synapslaag/KB/Triggers/Emoties/Verbanden) admin-only.
- **v11_roar_token_readonly_001** — ROAR Token in Spark Shop = read-only weergave (prijs bepaald door potjes-mechanisme).
- **v11_bitvavo_reconcile_ui_001** — Community-chat tab in Gesprekken vanaf grad 5.
- **v11_profile_merge_001** — Mijn Profiel: Algemeen + Achtergrond samengevoegd tot 1 tab. Persoonlijkheid verplaatst naar Beheer → Gebruikers → per-user tab. Gesprekken-tab weg (staat in Archief).
- **NotitiesPage** — Bijdragen-tab (KB v1 dead code) weg.
- **Dead code cleanup** UserProfilePage.js — 232 regels weggehaald (PersoonlijkheidTab + GesprekkenTab + Slider/ListInputs helpers + ongebruikte imports).

### Trader (leesonderzoek, geen wijziging)
- ADA-EUR cyclus 1 aug: BUY 73.64 @ €0.14828 + BUY 73.50 @ €0.14843, SELL 146.26 @ €0.14999 → netto ~−€0.01 (fees eten winst). Bitvavo API rechtstreeks bevraagd via Spark's keys. ~0.89 ADA dust bleef staan.
- Papertrail-alle-mints-naar-Spark bevestigd als by-design (Spark → treasury source, gift verdeelt daarna).

### Nog open na deze sessie
- **Root-cause gift/admin_grant → pot verhuist niet met token** (drift-bron ligt in `boekhouder/finance_ops` — pot moet mee-verhuizen).
- **P0 sessie 51**: andere users unieke wallet-IDs migreren, SparkSelfAwareness LLM-hooks, KB V3.

---

## ✅ SESSIE 51 SLOT — Wallet/Token/Mint gerepareerd + verbonden (31 juli)

### Kritieke bug-fixes (single-source-of-truth)
- **v11_treasury_pool_fix_001** — `admin_grant_token` en `admin_revoke_token` haalden tokens uit **Spark's balance** ipv `treasury_pool`. Elke +1/-1 token knop verstoorde de 1M-pool. Nu correct + auto-sync `user_wallets.json` + `sync_potjes_to_tokens`.
- **v11_mint_bitvavo_check_001** — mint checkte fout op `wallets.user-000.balance` (altijd €0). Nu op **Bitvavo-saldo** (net als 24u auto-mint). Geen EUR-transfer meer uit Spark's wallet — pure papertrail.
- **v11_audit_cluster_001** — `open_cluster` en `close_cluster` in potjes.py riepen NIET `announce_buy`/`announce_sell` aan. Sinds bot naar cluster-mode ging (~29 juli) verdwenen alle bot-trades uit audit-log. Nu gefixed + `amount_eur` in sell-entries + 16 historische entries backgefilled uit trace-jsonl.
- **v11_mint_cost_fix_001** — frontend gebruikte `next_mint_threshold_eur` (€90 = auto-mint drempel) als mint-kosten. Nu `current_price_eur` (€13.14 per token).

### Data-integriteit (Willems eis: alles verbonden)
- **v11_reserve_lock_001** — 2/2/1 reserve-kluis nu apart. Nieuwe `BitvavoAgent.live_free_eur_after_reserve()` — mint en potjes gebruiken deze. Reserve €2.26 mag NIET aangeraakt worden.
- **v11_unique_wallet_ids_001** — user-000 → `wal-da01a7d6`, user-001 → `wal-571e222b` (anti-fraude). Andere users blijven vooralsnog `user_id` als wallet_id.
- **v11_toplevel_master_001** — dubbele `spark_tokens` in `user_wallets.json` (top-level + nested) nu synchroon gehouden bij elke mutatie.
- **Papertrail-integriteit**: elke `/api/wallet/admin/token/grant`, `spark/mint/from-wallet`, `shop/token/buy` en `shop/gift/accept` muteert nu identiek: `roar_balances.json` (master) → `user_wallets.json` (mirror) → `user_potjes.json` (slots).

### UI-features (nieuw + verbouwd)
- **v11_papertrail_widget_001** — nieuw kladblok-widget: supply check + houders-lijst + laatste 15 tx. Bewijs dat 1M pool klopt.
- **v11_spark_card_001** — Spark Card dynamisch: kaartnr = wallet_id (16 chars), kaarthouder = username, geldig-tot = `created_at + 4 jaar` OF **"GEBLOKKEERD"** bij block.
- **v11_week_boekhoud_link_001** — Weekoverzicht (Inkomsten/Uitgaven) nu gekoppeld aan `audit_log.json` (was: statisch "+2.5%"). Categoriseert deposit/sell/gift_received → in; withdraw/buy/gift_sent → out.
- **v11_wallet_card_removed_001** — wallettoken-kader binnen UsersAdminPage verwijderd. Token-beheer via WalletPage + Papertrail-widget (single-source-of-truth).

### Nieuwe endpoints
- `GET /api/wallet/papertrail-overview` — supply + holders + recent tx (voor widget)
- `GET /api/wallet/overview` — uitgebreid met `week_in_eur/count`, `week_out_eur/count`, `wallet_id`, `created_at`

### Live verificatie
- **Willems 3 tokens hersteld** (verlies bij zip-merge). Willem 3 · Spark 7 · treasury 999.990 · som 1.000.000 ✓
- **2 tokens gemint + gift aan Geiser** doorgevoerd. Nu: Spark 7 · Willem 3 · Geiser 2 · treasury 999.988 · som 1.000.000 ✓
- **In Omloop klopt**: was 9, nu 12 (na Geiser-gift) — winkel-widget rendert correct.

### Prod-merges (2× deze sessie)
1. `spark_backup_changes_20260731_050848.zip` (66 files, 3.2MB) — audit-log recover + gebruikersdata
2. `spark_backup_changes_20260731_065728.zip` (1530 files, backups geskipt) — 788 JSON + 227 JSONL

Backup in `data/_backup_before_prod_merge_20260731_051228/` (213MB) voor rollback-safety.

---

## 🔴 P0 — Volgende sessie (na Willems redeploy + zip terug)

### 1. Andere users unieke wallet-IDs migreren (~5 credits)
Nu alleen user-000/001 hebben `wal-*` IDs. Geiser en anderen hebben nog `user_id` als wallet_id. Simpele migratie: iterate over alle wallets, als `wallet_id == user_id` → genereer nieuwe `wal-{uuid8}`.

### 2. 🟢 SparkSelfAwareness LLM-driven hooks (~40-50 credits)
Willems visie: harde strings blijven voor veiligheid + hoogste commando's. Conversationele intents (wedervraag, empathie, trader-info, humor) door LLM zelf laten kiezen ipv regex. Fundering (`spark_index`) klaar sessie 50g.

### 3. KB V3 — Normen, Waarden, Testament (~30 credits)
Filosofische laag voor systeem-loyaliteit + `willem_mening` veld. Voorkomt guardrail-blokkade.

---

## 🟡 P1 — Backlog

- **Consolidatie `wallets.json` vs `user_wallets.json`** — nu 2 bronnen synchroon gehouden, eigenlijk moet 1 weg (kandidaat: `user_wallets.json` opheffen, alles in `wallets.json` + `roar_balances.json`).
- **Sell/Dissolve token flow** — user kan token terugverkopen aan treasury.
- **Merge-rest-into-existing-pot flow** — rest-restje toevoegen aan bestaand pot-capital.
- **Missing 5W+H helper endpoint** `GET /api/kb/v2/admin/missing-5wh`.
- **Rebound H1 tuning** + gap-confirmation + activation.
- **Family uitbreiden** — moeder, overleden vader (nu alleen Lotus als dochter gekoppeld).
- **Proactieve 5W-vraag bij lang gesprek** — tussenstap naar 🟢.
- **Rest-bonus dashboard-widget** — "totaal opgeruimd deze maand".
- **Cyclus-Agents STARR/SMART** voor KB V3 execution.
- **32 KB v2 homoniem-dupes** — handmatige user-review (rapport in `DUPES_REPORT.md`).

---

## Bestand-index snapshot (v11_spark_index_001)
- Live via `GET /api/spark-index`
- 461 mappen · 1618 code-bestanden · 61 backend-modules · 60 met `_meta.json` footnote
- Auto-rebuild bij backend startup

---



## ✅ SESSIE 50 SLOT — Trader + Chat + Self-Awareness fundering (29 juli)

### v11_pot_registration_safety_001 — Bug A (race condition)
Bitvavo BUY-succes met `open_cluster` faal gaf silent coin-verlies. Nu try/except met fallback naar per-pot `open_pot`, event-notification bij faal, en `ui_refresh_trigger.json` voor directe frontend refresh.

### v11_adopt_manual_positions_001 — Bug C (bot adopteert manual pots)
Nieuwe `_adopt_orphan_positions()` + `_process_trailing_for_market()`. Open pots op markten buiten `self._markets` krijgen ook trailing-stop + -8% loss-cut check via batch-ticker fetch.

### v11_glow_clear_on_nav_001 + no_self_glow_001 — UI Glow bug
Nav-glow verdwijnt direct bij tab-klik; niet meer als user al op doel-tab staat. Path parsing werkt voor `/modules/trade` én `/`.

### v11_bitvavo_reconcile_ui_001 + v11_rest_by_history_001 — Reconciliatie UI
Nieuwe `BitvavoReconcilePanel` op Trader-pagina. Categorisatie op **historie** (matching pot of `net_paid ≥ €0.50`), niet op bedrag. Test-gokjes (NEAR/SHIB/TIA) → rest. ADA/BCH/ATOM/ETH/SOL/BTC → orphan-kandidaten.

### v11_rest_bonus_001 — Rest meepakken bij trail-SELL
Trail-trigger blijft berekend op cluster_capital ALLEEN. NA trigger → Bitvavo balance check, `rest_bonus = (actual - expected) × price`, meegenomen in SELL. Nieuwe `potjes.add_rest_bonus()` respecteert 2× original_max_size ceiling.

### v11_trader_trades_open_001 — trader-intent "hoeveel trades lopen"
4 nieuwe patronen (`hoeveel/welke posities`, `trades lopen/open/actief`). LLM hallucineert niet meer "2 lopende trades"; `_fmt_status` toont: *"3 open trade(s): 1× ADA-EUR, 1× ETH-EUR, 1× SOL-EUR"*.

### v11_admin_family_001 + admin_cross_user_001 — Lotus + cross-user data
Lotus (user-5dd295db) rol=Dochter. `family_relations` toegevoegd aan Willem + Lotus. Nieuwe helper `_load_family_relations_snippet` in admin-context prompt. Admin (gradatie 1) mag expliciet cross-user data delen.

### v11_daily_event_rps_001 + v11_daily_rps_001 — SPS Daily-Event rijke UI
`DailyEventCard` = dunne wrapper die `RpsBark` opent met `dailyMode=true`. Bark eerlijk bij loss ("je verloor deze ronde" ipv "je ontsnapte"). Behoudt 1×/dag gate + 10 goud uitkering.

### v11_kb_fill_offer_001 — "Kan ik wat voor je doen"-flow
Multi-turn: offer → question → paraphrase → save. 733 KBv2-kaarten met leeg ws5-veld beschikbaar als candidate. Escape-routes: nee/skip/retry.

### v11_spark_index_001 — Self-Awareness fundering 🟢
Nieuwe `modules/spark_index/` — periodieke scan van `/app/backend`, `/app/frontend/src`, `/app/memory`. Aggregeert 60 `_meta.json` footnotes per module. Endpoints:
- `POST /api/spark-index/rebuild` — herbouw index
- `GET /api/spark-index` — read-only totals + per-module details
- `GET /api/spark-index/module/{name}` — module-specifieke footnote

Chat-fastpath `count_intent_service.py` beantwoordt: *"hoeveel bestanden/mappen/modules/python-files/js-files"* + *"welke modules heb je"*. Live: **461 mappen, 1618 code-bestanden, 61 backend-modules (60 met meta), 330 .py-files**.

Auto-rebuild op backend startup (~200ms). Fundering voor toekomstige 🟢 SparkSelfAwareness LLM-driven intent-hooks.

---

## 🟢 P0 — Sessie 50 (SAMENGEVOEGD MET SESSIE 51 P0 HIERBOVEN)
_Historische verwijzing — actuele P0 staat helemaal bovenaan (sessie 51 blok).
Deze punten zijn nu gemerged in de P0/P1 secties bovenaan om dubbelwerk te voorkomen._

---

## Bestand-index live snapshot (v11_spark_index_001)
- Totaal mappen: **461** · Totaal bestanden: **1618** · Backend modules: **61** (60 met meta)
- Top file-types: **.py: 330** · **.js: 220** · **.json: 800+** · **.md: 100+**




## ✅ SESSIE 49 SLOT+4 — Bug B gefixt (29 juli)

### Wat Willem meldde
*"Hij laat de winst staan en alleen potje zelf terug zet"*

### Root cause — `potjes.py:close_pot()` regel 1000-1006
```python
new_capital = capital + netto        # €11.38 + winst = €11.50
if new_capital > pot_max:             # pot_max = €11.38
    overflow = new_capital - pot_max  # winst → overflow_pool
    new_capital = pot_max              # capital gecapt op €11.38!
p["capital"] = round(new_capital, 4) # potje weer op start-bedrag ❌
```

Winst was **niet weg** — ging naar `user["overflow_pool"]` (regel 1024). Maar in de pot-UI onzichtbaar → gebruiker denkt "winst is verdwenen".

### Fix (v11_pot_growth_001)
Potje **groeit mee met winst**:
- Bij winst: `capital = capital + netto`, `max_size` schuift mee
- Hard-ceiling op **2× oorspronkelijke max_size** (voorkomt onbeperkte groei)
- Boven ceiling: overflow-mechaniek blijft als fallback
- `original_max_size` opgeslagen bij eerste winst-close (backward compat)

### Live effect
- Nieuwe SELLs met winst laten `capital` groeien
- UI toont nu écht potje-groei
- Bestaande potjes onaangetast (geen data-migratie nodig)
- Bij `netto < 0`: gedrag onveranderd (verlies afgetrokken van capital)

### Bug A + C nog te doen
- **Bug A** (potje niet aangemaakt bij bot-BUY) — race condition, ~10 credits
- **Bug C** (adopt manual positions) — nieuw feature, ~15 credits
- Beide op P0 voor volgende sessie

### Trader-configuratie nu compleet volgens Willems ontwerp
- Loss-cut: -8% (Willems noodstop, was -1% gisteren)
- Trailing: fee-aware (activeert bij +6ct netto, verkoopt bij 1ct drop = 1ct netto winst)
- Potje-groei: geactiveerd (bug B fix)
- Extreme_oversold (3-red-then-green): ready, disabled
- Rebound H1: ready, disabled

---



## 🔴 P0 SESSIE 49 SLOT+3 — Trader bugs door Willem gemeld (29 juli)

### Bug A: Potjes niet aangemaakt bij bot-BUY
Willem: *"Sommig met potje kopen had hij namelijk niet meegenomen of front was later"*  
**Vermoedelijke oorzaak**: race condition tussen `execute_real_trade` en `potjes.create()`. Bot koopt → registratie mislukt of frontend refresh te traag.  
**Check volgende sessie**: `modules/trade/monitor.py:execute_real_trade` → `modules/trade/potjes.py:create()` sequentie. Add try/verify.

### Bug B: Winst blijft staan bij SELL, alleen potje-bedrag terug
Willem: *"Hij laat de winst staan en zet alleen potje zelf terug"*  
**Vermoedelijke oorzaak**: SELL boekt `entry_amount` terug naar potje, netto-winst gaat naar `roar_balances` of boekhouder event maar niet zichtbaar in pot-UI.  
**Check volgende sessie**: `close_pot` en `boekhouder/finance_ops` — verify dat `pot.value_eur += netto_profit` gebeurt.

### Bug C: Bot doet 0 auto-trades sinds begin (87 trades = 100% manueel)
- Bot ziet manuele posities niet in `bot_state` → geen trailing daarop
- Bot koopt niet zelf omdat gap-filter blokkeert
- **Voorstel volgende sessie**: `adopt_manual_positions` — bot leest wallet-history in, adopteert externe BUYs, past trailing toe

### Willems werk-around nu
Laat 10-25ct free balance per coin in Bitvavo staan zodat bot iets kan doen met bestaande potjes. Tijdelijke fix tot bugs A+B+C opgelost zijn.

### Prioriteit voor volgende sessie
1. Bug B (winst-verlies) — kritisch, financieel
2. Bug A (potje-creatie) — kritisch, boekhouding
3. Bug C (adopt manual) — verbetering, niet urgent

**Schatting**: 15-25 credits totaal voor A+B, 15 extra voor C.

---



## ✅ SESSIE 49 SLOT+2 — Verbanden-tab opgeschoond (26 juli, "rapen")

### Wat is er gedaan (kleine patches, geen breukwerk)
1. **`compute_verbanden` top_n 5 → 10** — elke kaart heeft nu max 10 verbanden i.p.v. 5
2. **Cluster endpoint mega-tag blocklist** — `emotie`, `neutraal`, `context`, `communicatie`, `sociaal`, `informatie` uitgesloten (waren "rivieren" met 1000+ leden, geen echte clusters)
3. **Cluster members cap 20 → 100** — zichtbaarheid per cluster verhoogd
4. **Cluster JSON field fix** — `shared_tag` toegevoegd naast `tag` (frontend compat)
5. **NEW endpoint** `POST /api/kb/v2/admin/verbanden/rebuild-all` — regenereert ALLE 5000+ kaarten in ~40s

### Resultaat direct zichtbaar
- **Verbanden-graph**: 51235 → **51264 edges** (na rebuild)
- **Clusters**: 50 → **3106** échte clusters zichtbaar (was: rivier + rivier + rivier)
- **Top 8 nu**: `leren(200) tijd(197) energie(193) relatie(189) actie(183) verandering(181) controle(167) analyse(160)`
- **Vriend-kaart**: 5 → **10 verbanden** met overlap-scores 6/6/5/5/5/5/5/5/5/5

### Wat NIET is gedaan (bewust, in ROADMAP voor later)
- **Topic-Agent voor semantische verbanden** — nog steeds pure tag-overlap. Homonym-guards zitten in KB-CRUD, niet in graph
- **Blueprint/meta/footnote integratie** — `_meta.json` en `footnote` fields worden nog niet meegenomen in verbands-score
- **Master/Leaf agent pattern** voor semantische judge — schatting 40 credits, aparte sessie

### Volgende iteratie
```
TopicAgent (Master, ~40 credits)
├── judge_semantic_overlap(card_a, card_b) → score 0-100
├── check_homonym_guard(shared_tags) → filter valse verbanden
├── weight_by_footnote(card.footnote) → context-boost  
└── read_blueprint(card.module) → module-specifieke regels
```

### Bestanden gewijzigd
- `/app/backend/modules/graph/__init__.py` — cluster endpoint v2
- `/app/backend/modules/kb_v2/hooks.py` — top_n 5→10
- `/app/backend/modules/kb_v2/routes.py` — rebuild-all endpoint

---



## ✅ SESSIE 49 SLOT+1 — Loss-cut getuned naar -1% (26 juli 2026)

### Wat is er gedaan
Blueprint `parameters.loss_cut_pct: -0.03 → -0.01`. Reden: tuning-backtest 90d 4h 6 markten.

### Bewijs
| Config | Trades | Win% | ECHT netto | vs Geen |
|---|---|---|---|---|
| Geen loss-cut | 9 | 100% (illusie) | -€12.98 | – |
| Oud (-3%) | 83 | 54% | -€9.40 | -28% |
| **Nieuw (-1%)** ✅ | 115 | 41% | **-€7.87** | **-39%** |

**Verbetering**: 16% minder verlies dan oud, 39% minder dan geen safety-net.

### Belangrijk
- Getest in **bear-heavy** 90d periode
- Lagere win-rate (41% vs 54%) is expected — kleine verliezen worden vaker gerealiseerd i.p.v. verstopt in open posities
- **Absolute PnL is beter** ondanks lagere win-rate = precies wat we willen
- In bull-markt kan strakke loss-cut nadelig zijn — monitor eerste maand na deploy

### Complete trader-configuratie NA deze wijziging
- Strategie: `gap_momentum_50` (Bollinger 2σ + gap-body)
- Loss-cut: **48u @ -1%** (was -3%)
- Cooldown: 900s per markt
- Anker: log_only, 8% drempel
- Gap-filter override: 999 (oud v7 gedrag)
- Rebound H1: gebouwd, disabled
- Extreme oversold: gebouwd, disabled
- 6 markten actief

### Deploy
Blueprint aangepast, backend herstart in preview. **Save-to-Github wanneer klaar** → prod redeploy.

---



## 🟡 SESSIE 49 SLOT (2026-02-01 / 26 juli) — H1 Rebound geïmplementeerd + backtest = niet klaar voor enable

### ✅ Code geïmplementeerd (blijft staan, disabled)
`strategy_decision.py`:
- Rebound-BUY check vóór Bollinger (regel ~160): trigger BUY bij drop ≥ threshold in 24u
- Rebound-exit check na loss-cut: scherpe SELL bij netto ≥ target_pct (default 2%)
- Config via blueprint: `rebound_enabled`, `rebound_drop_threshold_pct`, `rebound_target_pct`
- Backward compatible: default `enabled=false` → geen gedrag-verandering

### 📊 Backtest 10d + dry-run 48u

**Backtest 500d 15m, 6 markten:**
| Config | Trades | Win% | ECHT netto |
|---|---|---|---|
| Baseline (rebound OFF) | 27 | 67% | -€1.44 |
| Met rebound 3% | 33 | 61% | **-€2.97** ❌ |

Rebound-trades winrate 52% (verwacht 62.5%). Verklaring: autopsy was op **daily drops**, niet 15m rolling. Op 15m frame is "3% drop in 24u" veel vaker en kwalitatief anders.

**Dry-run laatste 48u:**
| Threshold | Rebound signalen |
|---|---|
| 2% | 365 (overreactie) |
| 3% | **147** (nog steeds te veel) |
| 5% | 21 (redelijk) |

**Werkelijkheid** (uit prod-zip 26 juli): 0 trader-trades, 4 Willem-manuele trades.

### 🎯 Fundamentele inzicht — Willems mentale strategie ≠ pure drop-detection

Willems 25/7 14:46 ATOM-BUY was op **-2.7% drop** (onder 3% threshold).  
Willem wachtte niet op drop-maximum, hij wachtte op **stabilisatie**.

- Mijn implementatie: `drop ≥ threshold → BUY` (koopt tijdens val)
- Willems intuïtie: `drop + reversal waargenomen → BUY` (koopt na val)

**De v7_gap_merge_001 gap-filter IS Willems reversal-detector**. Alleen: hij zit nu voor Bollinger-check, niet voor rebound-check. Rebound heeft eigen reversal-confirmation nodig, óf moet gap-check hergebruiken.

### 📝 Volgende iteratie (~15-20 credits)
1. Voeg `rebound_gap_confirmation_required: true` toe aan blueprint
2. In rebound-check: als `_gap_breakout_check(candles).signal == 'BUY'` én drop ≥ threshold → BUY
3. Anders: HOLD (wacht op reversal)
4. Herbacktest — verwachting: minder signalen, hogere winrate
5. Als 62.5% winrate + positief ECHT netto → enable

### Status
- `rebound_enabled: false` (blijft OFF)
- `rebound_drop_threshold_pct: 3.0` (gedocumenteerd, gereed voor gebruik met gap-confirmation)
- Code werkt, backtest reproduceerbaar
- Willem blijft betrouwbaarder dan de bot in bear-market (jouw intuïtie > mijn threshold)

---



## 🔴 P0 SESSIE 49 SLOT (2026-02-01 / 26 juli) — H1 Rebound is 90% klaar, code ontbreekt

### 📌 Willems terechte correctie
Willem had gelijk toen hij zei "bekijk de logs van je eerdere berekeningen". Snuffel toonde aan:

1. **Rebound is al ontworpen** — `spark_trader.json.parameters.rebound_*` bestaat sinds sessie 46 (9 juli)
2. **Backtest is al gedaan** — 62.5% van 5%-drops geeft +1.96% mediaan binnen 24u (v4 autopsy)
3. **Aanpassing bekend** — drempel 5% → 3% (documented "tuning naar 3% pending")
4. **Willem bewees het live** — 25/7 14:46 kocht handmatig ATOM @ -2.7% drop, won +0.65% netto binnen 12u
5. **Wat ontbreekt** — geen enkele regel code in `monitor.py` of `strategy_decision.py` leest deze rebound-config

### ✅ Bijgewerkt in blueprint (0 credits, geen risico)
- `rebound_drop_threshold_pct: 5.0 → 3.0` (op basis van Willems bewijs)
- `rebound_enabled` blijft **`false`** (want code ontbreekt, anders NoOp)
- Note uitgebreid met sessie-49 context

### 🎯 Concrete implementatie-spec voor volgende sessie

**Plek**: `modules/trade/monitor.py`, in `_simple_decision()` **VÓÓR** de Bollinger-check.

**Pseudocode**:
```python
# Rebound-BUY: trigger bij drop ≥ threshold in laatste 24u
if bp['parameters']['rebound_enabled']:
    thresh = bp['parameters']['rebound_drop_threshold_pct']  # 3.0
    high_24h = max(c['high'] for c in candles[-96:])  # 96 x 15m = 24u
    drop_pct = (high_24h - current_price) / high_24h * 100
    if drop_pct >= thresh and position is None:
        return {
            "action": "BUY",
            "reason": f"Rebound-trigger: -{drop_pct:.1f}% drop in 24u (≥{thresh}% threshold)",
            "strategy_variant": "rebound_h1",
            "target_pct": bp['parameters']['rebound_target_pct']  # 2.0
        }
```

**SELL-logica** (aparte target): rebound-positie verkoopt bij +2% (target) of via bestaande trailing/loss-cut.  
Verschil met Bollinger-BUY: target is scherper (2% i.p.v. trailing 0.5→0.4).

### 🧪 Backtest-vereiste vóór live
1. Draai H1 rebound geïsoleerd op 500d 15m data
2. Vergelijk met gap_momentum_50 op zelfde periode
3. **ECHT netto** (realized + unrealized DD) moet positief of ≥ gap_momentum_50
4. Als OK → `rebound_enabled: true` in blueprint, deploy

### 💰 Credit-inschatting
- Code implementatie: ~15 credits
- Backtest + validatie: ~10 credits
- Blueprint enable + deploy: ~5 credits
- **Totaal: ~30 credits** — te weinig met Willems 23. Wachten op nieuwe sessie.

### 🎓 Les voor mij
**Bij trader-vragen altijd eerst blueprint snuffelen**. Ik heb 3× fout getframed voor ik dit vond:
1. "gap-filter te strak" (gerevert)
2. "trader werkt en verdient" (waren jouw manuele trades)
3. "H1 moet nog gebouwd" (spec ligt al klaar sinds juli)

Snuffel = eerste actie. Elke keer.

---



## 🔴 P0 SESSIE 49 EIND (2026-02-01) — Gap-filter override GEREVERT + volgende hefbomen

### ❌ 3% gap-override teruggedraaid (niet gedeployed)
Blueprint `gap_filter_dip_override_pct` staat weer op **999** = oud v7-gedrag. Waarom:

**Fout in mijn eerste presentatie**: mijn 10d 15m backtest telde alleen **realized PnL** en toonde cond_3 als "winnaar" (-€0.18). Willem's terechte tik: *"einde maand hadden we toch positief"*. Snuffel wees me naar `willem_ideas.md` waar hij eerder al concludeerde:

> *"100% win-rate was ILLUSIE — verliezen zaten verstopt in open posities. D onze winnaar: gerealiseerd +€2.63, echte netto -€13.16 (met open DD)"*

Ik heb opnieuw backtest gedraaid op **500d daily** MET unrealized DD:

| Scenario | Realized | Open | Unreal DD | ECHT netto |
|---|---|---|---|---|
| off | -€5.38 | 1 | -€0.17 | **-€5.55** |
| always (huidig) | €0.00 | 0 | €0.00 | €0.00 |
| cond_2/3/5 | -€5.38 | 1 | -€0.17 | **-€5.55** |

Op daily-frame maakt de filter geen verschil (78 trades bij elke override; daily body's zijn groot dus gap-check laat alles door). Op 15m maakt hij WEL uit, maar levert **geen extra winst**. Meer activiteit ≠ meer winst.

### 🎯 Echte hefbomen die WEL bewezen zijn (uit willem_ideas.md v4-analyse)

**H1 Rebound-strategie** (NIET geïmplementeerd, hoogste ROI potentie):
- Post-event autopsy: **62.5% van 5%-drops is 24u later positief** (mediaan +1.96%)
- **49.2% herstelt ≥2% binnen 24u**
- Aanbeveling: nieuwe strategie **Q** = Bollinger + gap-body + rebound-BUY (koopt JUIST bij event, target 2% winst)
- Drempel: verlaag rebound van 5% naar **3% drop** — dan wél triggeren
- **P0 volgende sessie**

**H2 48u loss-cut** (WEL geïmplementeerd, actief):
- Bewezen betere netto (-€9.53 vs -€13.16 baseline)
- Zit in `_simple_decision` regel 95-124
- Blijft aan

### 🎓 Les — verplicht voor elke toekomstige backtest
**ELKE backtest moet unrealized DD meerekenen**, anders lieg je tegen jezelf. Concreet:
```
echt_netto = sum(realized_trades) + sum(open_positions_unrealized_at_end)
```
Als de "winnaar" scenario >1 open positie heeft aan het einde en de test-periode kort is → verlies verstopt. Gebruik ook langere periode (min 90d, liefst 500d) om market-regime bias te vermijden.

### Status
- Blueprint `gap_filter_dip_override_pct: 999` (oud gedrag, herstart-safe)
- `monitor.py` code onaangetast (leest gewoon uit blueprint, backward-compatible)
- Geen deploy nodig — preview draait al met 999
- **Volgende sessie**: bouw H1 rebound-strategie (nieuwe strategie Q)

---



## 🟢 SESSIE 49 UPDATE — Gap-filter override GEÏMPLEMENTEERD (2026-02-01 / 25-jul)

Backtest 10 dagen 15m candles (14-25 juli), €10/trade, fee 0.25%/side, 6 markten:

| Scenario | Trades | Win% | Netto € |
|---|---|---|---|
| Geen filter | 31 | 71% | -€0.87 |
| Huidig (always) | 2 | 50% | -€0.24 |
| cond_2 (2%) | 24 | 67% | -€1.13 |
| **cond_3 (3%)** ✅ | **12** | **75%** | **-€0.18** |
| cond_5 (5%) | 3 | 67% | -€0.15 |

**Winnaar: 3.0%** — 6× meer trades dan huidig, hoogste win-rate, minimaal verlies in bear-periode.

**Belangrijk**: alle scenarios netto negatief in deze 10-daagse bear-periode. Mean-reversion strategieën verliezen inherent in aanhoudende bear-market — filter kan dat niet oplossen.

**Geïmplementeerd**:
- `spark_trader.json` → `gap_filter_dip_override_pct: 3.0` + toelichting
- `monitor.py` regel ~1091 → threshold uit blueprint, backward compatible (999 = oud gedrag)
- Beslissings-log heeft nu `gap_filter_overruled: true` flag

**Live effect**: bij dips ≥3% → BUY door zonder gap-confirmation. Bij <3% → filter blijft actief (originele safety). Live tweak via blueprint zonder code-change.

---


## 🟡 SESSIE 49 (2026-02-01 / 25-jul-prod) — Gap-filter blokkeert 100% in bear-market

### 📊 Bevindingen uit prod-zip 25 juli 07:23

**Willem's observatie**: 24 juli 07:08 tot 25 juli 07:23 (24u) = 0 trades, terwijl hij een BUY had verwacht. Reboot uitgesloten want bot draaide 48 events/uur constant.

**Diagnose backtest** (via live Bitvavo 15m candles + `_simple_decision`):

| Markt | Bollinger-BUY | Passed gap-filter | Zou trade |
|---|---|---|---|
| BTC-EUR | 5 | 0 | 0 |
| ETH-EUR | 3 | 0 | 0 |
| SOL-EUR | 7 | 0 | 0 |
| ADA-EUR | 5 | 0 | 0 |
| ATOM-EUR | 8 | 0 | 0 |
| BCH-EUR | 1 | 0 | 0 |
| **TOTAAL** | **29** | **0** | **0** |

Alle 29 gedetecteerde Bollinger-dips werden geblokkeerd door **`v7_gap_merge_001`** (sessie 47) — de bevestigings-filter die eist dat na een Bollinger-BUY óók een `_gap_breakout_check` = BUY signaal moet komen (rood→groen candle-flip waarbij `curr.low > prev.high`).

### ⚠️ Geen bug — bewuste feature, verkeerd geconfigureerd voor bear
Uit CHANGELOG blijkt dat Willem `v7_gap_merge_001` zelf voorstelde om piek-koop in dalende markt te voorkomen. Werkt in trending-neutraal markten, maar in aanhoudende bear-daling (zoals 24 juli) treedt de rood→groen flip niet op → **100% van signalen wordt gedumpt, ook echte dip-kansen**.

### ✅ Voorgestelde fix — Optie C (conditioneel filter)

Maak de gap-filter afhankelijk van dip-diepte:

```python
# v11_gap_filter_conditional_001 — in modules/trade/monitor.py rond regel 1092
if buy_decision.get("action") == "BUY" and gap_check["signal"] != "BUY":
    # NIEUW: alleen filteren bij ondiepe dips (<3%). Bij ≥3% dip is
    # de dip zelf al bewijs, geen momentum-confirmation nodig.
    dip_pct = buy_decision.get("drop_from_high_pct", 0)  # zit al in decision
    if dip_pct < 3.0:
        buy_decision["action"] = "HOLD"
        buy_decision["reason"] += f" | Wacht op gap-bevestiging ({gap_check['reason']}, dip {dip_pct:.1f}%)"
        buy_decision["gap_filter_blocked"] = True
    else:
        buy_decision["reason"] += f" | Gap-filter overruled: dip {dip_pct:.1f}% ≥ 3.0% (echte dip)"
        buy_decision["gap_filter_overruled"] = True
```

**Waarom 3%?** Uit prod-zip 24 juli: alle 29 signalen hadden `drop_from_high_pct` tussen 1.55% en 2.38% (dus dip-guard `MIN_DIP_PCT=1.5%` triggerde ze wel, gap-filter blokkeerde ze). Bij `drop >= 3.0%` heb je een substantiële dip die het risico op piek-koop klein maakt.

**Alternatief nog te overwegen**: threshold uit blueprint halen (`gap_filter_override_dip_pct: 3.0`) i.p.v. hardcoded, zodat je live kunt tweaken.

### 📝 Backtest vereist voordat live
Voordat dit deployed wordt: `tests/backtest_v5.py` draaien met en zonder deze override op 90d data en PnL vergelijken. Vooral belangrijk om te controleren of we niet regressen naar het oude "koop op elke piek" gedrag in trending-neutraal.

### 🎓 Les voor volgende sessies
**Bij trader-diagnose eerst CHANGELOG + ROADMAP snuffelen** voordat ik code-analyse doe. Anders presenteer ik bekende features als "verdachten". `spark_snuffel` op scope `code` doet dit in 1 call — zou standaard eerste stap moeten zijn bij trader-issues.

### Status
- **NIET geïmplementeerd** — alleen genoteerd. Willem beslist zelf wanneer + samen met de backtest.
- Anker (`log_only`, 8%) blijft ongewijzigd — heeft geen invloed op dit issue.

## 🟡 SESSIE 48 (2026-02-01) — Entity Engine (idea, gepland niet nu)

### 🧬 Van "Namen-lade" naar Entity Engine

**Trigger**: Sessie 48 bouwde een `namen`-module (blueprint + service + LLM-classify + UI + snuffel). Willem's inzicht: *"dezelfde structuur werkt straks ook voor recepten, boeken, plaatsen, bedrijven..."*. Chat-analyse bevestigde: dit is per ongeluk een **generieke entity-module** geworden.

### Voorgestelde architectuur (WACHT tot 2e entiteit concreet nodig is)

```
/api/entities/{type}/*
  ├── namen         → voornaam_m/v/unisex, achternaam, koosnaam, gamertag
  ├── recepten      → voorgerecht, hoofdgerecht, dessert, drank, saus
  ├── bedrijven     → klant, leverancier, KVK, branche
  ├── plaatsen      → land, stad, adres, POI
  ├── boeken        → fictie, non-fictie, referentie
  ├── dieren        → soort, huisdier, wild
  └── producten     → digitaal, fysiek, dienst
```

**Gedeelde infrastructuur per type**:
- Blueprint JSON in `/data/blueprints/{type}.json` — schema + categorieën + seed data
- `_meta.json` per module (footnotes / notities / auteur)
- Generieke CRUD service (list / add / delete / search / classify_via_llm / stats)
- Auto-registratie in `spark_snuffel` scope
- Dynamische UI-page (rendert categorieën uit blueprint schema)

**Combi: footnote + metadata + blueprint** (Willem's woorden)
- Blueprint = **data-schema** (welke categorieën bestaan, seed content)
- Meta = **module-eigenschap** (auteur, endpoints, versie, wanneer aangemaakt)
- Footnote = **contextuele opmerkingen** waarom keuzes zo zijn (leesbaar voor Spark)
- Alle drie zichtbaar/leesbaar voor Spark zelf → transparantie behouden

### ⚠️ Agent-coördinatie nodig
Zodra Entity Engine live gaat mogen **niet meerdere modules langs elkaar** aan dezelfde entiteit werken (bv. `namen` én `personalia_extraction_service` die beide personen extracten uit chat). Oplossing sluit aan bij bestaand **ChatHub Master/Leaf** patroon:

```
Entity Hub (Master)
  ├── namen_agent       (owns: /entities/namen)
  ├── recepten_agent    (owns: /entities/recepten)
  ├── plaatsen_agent    (owns: /entities/plaatsen)
  ...
```

- **1 agent per entiteits-type** = single writer, geen races
- **Auto-learn hooks** (bv. capitalised token in chat → naam-agent classificeert) lopen via de hub, niet direct
- **Cross-entity queries** (bv. "wie kookt welk recept?") gaan via Master

### Beslissing (2026-02-01)
- **Nu NIET refactoren**. `namen` blijft standalone (werkt goed).
- **Wachten op 2e concreet voorbeeld** (waarschijnlijk `recepten`) → dan pas Entity Engine bouwen op basis van 2 real-world requirements i.p.v. hypothese.
- **Roadmap-item aanmaken** (dit blok) zodat context niet verloren gaat.

### Migratie-strategie (voor later)
1. `modules/entities/` maken als generieke engine met type-registry
2. `namen` intern doorsturen naar `entities/namen` (backward compat: `/api/namen/*` blijft werken)
3. Nieuwe types = 1 blueprint JSON + 1 regel in registry
4. Entity Hub agent-laag bouwen wanneer we ≥3 types hebben (anders overengineered)

---




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

### 🎓 Lessen sessie 47 (bewaren voor volgende sessies)

**Les 1 — Anker is INFO, geen filter (bevestigd door dryrun)**
Bij Bollinger-dip strategie zit BUY-signaal per definitie ONDER de MA (delta% negatief). Anker filtert alleen gap-UP + BUY-signaal — komt in 90d amper voor. Dryrun: 0 skips bij 5/8/12% drempel over 234 buys.
**Voortaan**: anker is context-referentie voor gap-up-uitzondering, niet BUY-filter. Drempel-tuning heeft weinig effect. Nooit meer diagnosen "trader miste trades" op anker gooien zonder eerst de log-agent (`data/boekhouder/logs/anker_check/`) te checken — 0 events = anker deed niks.

**Les 2 — Actieve markten ≠ ge-ankerde markten**
Sessie 47: 6 markten gebootstrapt (BCH/BTC/ETH/SOL/ADA/ATOM) maar `markten.actief` in blueprint had er maar 4 (ETH+ADA misten). Willem verwachtte trades op ADA/ETH die niet gebeurden. **Voortaan**: bij het aanpassen van markten altijd BEIDE checken (anker-cache dir + `spark_trader.json → markten.actief`).

**Les 3 — Reboot = state-verlies = missed trades**
Laagste server-tier + trader-worker + LLM + scheduler concurrent = container-reboots. Bij reboot: monitor state herstart, buy-cooldown reset, BUY-window mogelijk verstreken. **Oplossing**: tier-upgrade. Willem gaat dat bij volgende redeploy doen. Buy-cooldown werd al gepersist naar disk sinds sessie 47 (helpt bij ordinary restart, niet bij OOM-kill mid-decision).

**Les 4 — Zonder prod-log-toegang blindvaren**
`deployment_agent` geeft alleen readiness-check, geen live-logs. Als user gemiste trades meldt kan ik pas diagnosen als de prod-zip beschikbaar is. **Voortaan**: bij trader-issues eerst vragen "kun je de laatste zip delen?" i.p.v. hypothesen bouwen.



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

---

## 📦 Verplaatst 20-10-2026 uit ROADMAP_CORE (CORE terug naar <500 regels; inhoud ongewijzigd)

### ↪ AFGEROND 19/20-10-2026 (detail)

## ✅ AFGEROND 19-10-2026 (100-credit-batch, getest als Emergent-account)
- **Relatie-/personalia-extractie in diep-modus** (`v14_compose_extraction_001`, `response_composer.py` r.184) —
  `compose()` roept nu dezelfde `relation_extraction_service` + `personalia_extraction_service` aan als
  `/api/chat/message`; `new_relations`/`personalia_saved` gaan mee in de response zodat "ik noteer" alleen klinkt
  als er echt iets staat. Getest: "X is mijn broer" → `persons/<user>.json` + `_relationships.json` gevuld.
  Testrelaties daarna verwijderd. **Maaike moet haar zinnen één keer opnieuw zeggen** — de oude zijn nooit opgeslagen.
- **Roadkill Merch-tab uit Beheer** (`SystemArchive.js` r.323) — bestaat alleen nog in Workspace → Archief → Foto → Winkel.
- **TTSS / GTSS** (`v14_ttss_001`) — zie blok hieronder.
- **KB-filter 🎙️ niet ingesproken** (`kbv2-voice-filter`, per lade met teller bv. Voelen 554/566). Niet in Inbox-tab.
- Testartefacten opgeruimd: `test-dupe-guard-15599c75` (weten), inbox-gapfills `testman/testbroer/emergentsen`.
  → **alle 7353 lade-kaarten hebben ≥5 tags.**

### 🎙️ TTSS / GTSS — hoe het werkt en wat de grenzen zijn
- Chat-commando's: `ttss aan|uit`, `gtss aan|uit` (`action_intents_service._RX_TTSS`, acties `enable_ttss` enz.).
  Cyaan modusbalk `ttss-mode-bar` boven de chat. Gewone `tts aan` blijft OpenAI-stem.
- Backend `GET /api/kb/v2/voice/map` → `{woorden: begrip→voice_url, geluiden: begrip→extra_audio-url}`;
  `GET /api/kb/v2/voice/missing?lade=&search=` → kaarten zonder inspraak + `per_lade`-tellers.
  **Alleen `media.voice_url` telt als inspraak**; `media.extra_audio` (geüploade geluiden) is het GTSS-kanaal.
- Frontend `speakOwnVoice()` (GesprekkenPage r.685): loopt per woord (+ 2-woord-begrippen) door het antwoord,
  speelt de opname af als die er is, **skipt stil** als die ontbreekt. Geen terugval op OpenAI-TTS in ttss-stand.
- **Grens**: nu 50 ingesproken woorden + 9 geluiden op 7353 kaarten → antwoorden klinken hakkelig/leeg. Dat is
  by design: de filter laat zien wat nog ontbreekt. GTSS is een **placeholder**: speelt kaart-geluid als het
  begrip in het antwoord staat; er is nog geen bewuste "bloeper → bloepergeluid"-koppeling.
- **Tab "In te spreken"** (`v14_inspreek_tab_001`, 19-10): eigen tab in de lade-rij, alle lades + lade-chips met tellers,
  kaart verdwijnt na inspreken en de volgende kaart wordt automatisch geopend. Alleen `voice_kind='spraak'` telt;
  een als GELUID gemarkeerde opname telt niet als inspraak (gaat naar het gtss-kanaal). Merch: ook dode code weg.
- **Emotie-veld (onderzoek, niet bouwen; Willem: "goed als is")**: top-level `emotie` bestaat al op 3631 kaarten
  (3553 neutraal) via txt-importer, maar `emotion_service` leest alleen tags (1336 geleerd, 1147 neutraal). Dode data.
  Willems gedachte: emotie als eigen graph-laag naast de verbanden-graph, los van de kaart → minder ruis. Parkeren.
- **ttss-output als sample opslaan (onderzoek)**: zinloos voor eigen opnames (zelfde audio). Wél mogelijk: per kaart
  één keer OpenAI-TTS genereren in apart veld `media.tts_url` (nooit `voice_url`) als bootstrap-stem. Risico: ~7353
  calls, ~200 MB, twee stemmen door elkaar. Niet gebouwd; wacht op akkoord.
- **Onderzoek 19-10 (geen bouw)**: emotie-graph + hybride command-systeem → `/app/memory/ONDERZOEK_EMOTIE_GRAPH_COMMANDS.md`
  en `/app/memory/COMMANDS_OVERZICHT_19-10.md`. Kern: `emotie`-tag = ~25 % ruis in kennis-graph; emotie-veld bestaat al
  (3631 kaarten) maar wordt niet gelezen; registry 81 = 58 live / 23 placeholder; task_agent.resolve/execute zijn leeg.
  Punt 3 (tab "Nog geen emotie", 120 %) wacht op akkoord punt 1.
- **✅ 19-10 — Registry opgeruimd + task_agent-basis** (`v14_task_agent_basis_001`):
  `command_registry.json`: 58 live (`status: live`) · 23 verplaatst naar `placeholders` (route bestaat niet; wens
  bewaard, 8 ervan werken via spark_capabilities laag B). Backup `.bak_placeholders_*`. Stats hersteld.
  `task_agent.resolve(tags, methods)` → beste live command via matcher; `resolve_text(zin)` voegt losse woorden,
  stam (-s/-en) en **werkwoord-concepten** toe: verwijderen = verwijder/delete/wis/ruim op/gooi weg → alleen DELETE-
  commands; aanmaken → POST; zonder actie-werkwoord → alleen GET. Getest: "verwijder die bug" / "ruim die notitie op"
  / "delete die taak" → juiste delete-command. `execute(cmd_id, params, user_id)` → gradatie-check, required-params,
  `{user_id}` auto in pad, interne ASGI-dispatch (geen netwerk), audit-log `task_agent.jsonl`; placeholders → geweigerd.
  **AANNAME te bevestigen door Willem**: registry-schaal `gradatie_min` 1=iedereen…5=beheer is omgekeerd aan de
  user-schaal (1=beheerder); omrekening `user_gradatie <= 6 - gradatie_min`, `admin_only` eist gradatie 1.
  **Nog niet**: task_agent hangt nog NIET in de chat-flow (hybride stap 3 na action_intents + capabilities) en de
  concept-JSON is nog hard-coded (`_VERB_CONCEPTS`) — volgende sessie live-editable maken zoals intent_patterns.
- **✅ 19-10 — Emotie-veld + tab "Nog geen emotie"** (`v14_emotie_veld_001`, Willems keuzes: 5 basis-emoties,
  sub-emoties later leerbaar; `neutraal` is een echte keuze, geen default; schone reset van de detector):
  kaartvelden `emotie` (blij/boos/bang/bedroefd/neutraal) + `emotie_bevestigd` + `emotie_bron` + `emotie_bevestigd_op`,
  gezet via `/api/kb/v2/edit` updates `{emotie}` (`service._apply_emotie`). Routes `GET /api/kb/v2/emotie/missing|stats`
  (`emotion_routes.py`). Tab in de Kennisbank met lade-chips/tellers; kaart verdwijnt na bevestigen, volgende opent.
  EmotieSection op elke kaart; niet-bevestigde suggestie (uit emotie-tag of importer-veld) licht gestippeld op.
  **Detector**: `emotion_service._load_learned_triggers` leest alleen nog bevestigde velden (neutraal = geen trigger);
  tags en v1 `knowledge_base.json` tellen niet meer → geleerde woorden 1336 → 0 tot Willem bevestigt (statische
  triggers blijven anker). Getest: bevestig `akkers`=blij → "ik ben zo blij met de akkers" bron `both`.
  **Badge**: 100 % = laag1-4 + 5W + tags + foto (7 velden); +10 % ingesproken (alleen voice_kind spraak) · +10 % emotie
  bevestigd → max **120 %**. (Stem telt niet meer mee in de 100 %-basis.)
  **✅ Tags-opruimen bij bevestigen** (`v14_emotie_tags_001`, Willems keuze "alleen tegensprekende weg"): in
  `_apply_emotie` gaan `emotie-X`-tags met X ≠ keuze weg, en op emotie-kaarten (tag `emotie`) ook losse basis-emotie-
  tags ≠ keuze; `emotie` zelf en een tag gelijk aan de keuze blijven; nooit onder MIN_TAGS_FOR_LADE (dan
  `emotie_tags_conflict` + waarschuwing). Verwijderde tags staan in `emotie_tags_verwijderd` (toast in UI).
  Getest: gloed (emotie, blij, neutraal, …) bevestigd als boos → blij + neutraal weg, 13 tags over; teruggedraaid.
  Stand: 5 kaarten met expliciete pipeline-tags, 1330 met losse emotie+basis; worden pas geraakt als Willem bevestigt. Kennis-graph-ontruising (`emotie` uit tag-
  overlap) + emotie-edges (escaleert_naar/verwant/tegenpool) = volgende stap "emotie-graph".
- **✅ 19/20-10 — Contacten-klapper + Winkel: Producten/Bestellingen (fase 1+2)** (`v14_contacten_klapper_001`,
  `v14_shop_producten_tab_001`; getest als Emergent met tijdelijke testwinkel, daarna opgeruimd):
  • Mijn Profiel → **Contacten**: twee lagen privé/zakelijk, rollen (familie/vriend · leverancier/klant/partner), zoek,
    CRUD. Eén klapper, niets dubbel: bel_contacts (bron `bel`) en clienten (bron `clienten`) worden erin getoond én
    zijn er bewerk-/verwijderbaar — schrijft terug naar hun eigen bestand (Willem 20-10: "kon mijn contacten niet
    aanpassen"). Eigen entries: `data/users/<id>/contacten.json`. Routes `/api/contacten/{user_id}` GET/POST/PUT/DELETE.
  • Rollen zakelijk (Willem 20-10): **klant** = koopt merch · **client** = vraagt zorg/handelingen (cliëntdossiers
    uit `clienten` krijgen rol client) · leverancier · partner · overig.
  • Zakelijke kaders (Willem 20-10, stonden in notities): KvK, BTW-nummer, IBAN, BIC, jouw klant-/debiteurnummer bij hen.
    Rol **dienstverlener** erbij (advocaat/accountant). Promotex/Full of Joy/Boutadvocaten gemigreerd; spaties getrimd.
  • Velden (Willem 20-10 n.a.v. Promotex): telefoon + telefoon2, fax (zakelijk), e-mail + e-mail2, website (zakelijk).
  • Profiel-kaart **Zakelijk**: `zakelijke_email`, `bedrijfsnaam`, `kvk`, `btw_nummer` (ProfileExtended).
    Regel Willem: e-mail pas gebruiken als ingevuld. Spark's eigen afzender later: spark-your-life@hotmail.com.
  • Winkel-tab → subtabs **Winkel | Producten | Bestellingen**. Product heeft nu `product_code`, `voorraad`,
    `leverancier_contact_id` (keuze uit zakelijke contacten) of `leverancier_naam` (vrij). Leeg = eigenaar levert zelf.
    Nieuw product in Producten-tab verschijnt ook in Winkel (zelfde bron). `GET /api/shop/shops/{shop_id}/orders`.
  • Betaling blijft zoals het was: koper betaalt uit Spark-wallet (Willem: "daar heb ik al wat voor").
  • **✅ 20-10 — Producten → Verkoop | Inkoop + stuklijst + BTW in winkelwagen** (`v14_shop_inkoop_stuklijst_001`):
    Inkoop-artikelen per shop (`products.json → inkoop[]`: code, naam, inkoopprijs excl., leverancier uit zakelijke
    contacten, voorraad). Verkoopproduct heeft `stuklijst[]` = inkoop-artikelen × aantal (hoodie-code + opdruk klein +
    opdruk groot; set = hoodie + jogger + 2× opdrukken) → kostprijs/marge berekend (`/kostprijzen`). Willems drie
    "storage"-items (opdruk klein/groot, envelop — stonden als digitale GB-opslag in de etalage!) zijn omgezet naar
    inkoop-artikelen; stuklijsten voor alle 7 Roadkill-producten ingevuld; inkoopprijzen basis-artikelen nog leeg (?).
    **Prijzen = excl. BTW** (bestaand v13b-model in `boekhouder/shop_hooks`); BTW-% en KOR komen **per winkel** uit
    shops.json (geen tweede waarheid). Winkelwagen: subtotaal excl. → BTW → **Afhalen/Verzenden** (vast bedrag, geen
    BTW) → totaal. Shop-instellingen (`settings`: verzendkosten 6,95, verpakking per bestelling = envelop → voorraad
    -1 ná saldocheck, afhalen mogelijk) in Producten → Inkoop. Order bevat subtotaal_excl/btw_pct/btw/bezorging/
    verzendkosten/verpakking + productcodes. Routes: `/api/shop/shops/{id}/inkoop` CRUD, `/settings`, `/kostprijzen`.
    Getest: hoodie 60 → 72,60 afhalen / 79,55 verzenden; 2 petten 49,30.
    20-10: inkoopprijzen/codes uit Promotex-orders (4-08-2023, 12-05-2023) ingevuld: Cruiser hoodie 32,20 ·
    Mover jogger 30,95 · Trainer shorts 22,35 · Creator t-shirt 7,50 · DTF groot 6,95 · DTF klein 3,95. Rugtas = 1 klein
    logo (basis-code/prijs onbekend). **Marges nu zichtbaar: jogger lang −6,85 en kort −3,25 (verkoop onder kostprijs!),
    set +5,05.** Later: varianten (kleur/maat) per inkoop-artikel — de Promotex-orders zijn per kleur/maat.
    **✅ 20-10 Varianten** (`v14_shop_varianten_001`): product heeft `maten[]`/`kleuren[]` (standaard S–XXXL · Navy blauw,
    Khaki groen, Zwart, Marble grijs; eigen waarden toevoegbaar; leeg = n.v.t.). Koper kiest kleur+maat bij "In wagen"
    (verplicht als ingesteld, backend valideert), cart-regel per product+kleur+maat, `maat`/`kleur` op order-items en in
    Bestellingen-tab. Kleding-producten Roadkill hebben de standaardset; cap/rugtas niet.
    **Nog**: `create_order` boekt in oud accounting-bestand i.p.v. `record_shop_sale` (boekhouder) → koppelen bij
    "Bestellingen ↔ boekhouder"; inkoop bij leverancier → `record_shop_purchase`.
  • **✅ 20-10 — Fase 3: factuur, pakbon, leveranciersmail, boekhouder** (`v14_shop_documenten_001`, `modules/shop/documents.py`):
    bij een merch-bestelling → `boekhouder.record_shop_sale` (netto/BTW/bruto, bonnen-JSON, Spark-fee; **oud accounting-
    bestand wordt niet meer gevuld** — Willem: eigen boekhoudsysteem, later Moneybird) → factuurnummer `RK-<jaar>-0001`
    (teller in shop-settings) → **Factuur-PDF** in Archief koper + kopie bij eigenaar → **Pakbon-PDF** (= bestelbon, geen
    prijzen, afvinkvakjes, verpakking) bij eigenaar → **leveranciersmail-concept** per leverancier uit de stuklijsten
    (code · naam · kleur/maat · aantal, "ik haal zelf af, factuur per mail naar <zakelijke e-mail>", groet Willem,
    "Spark AI"). PDF lokaal (fpdf2, geen dienst). Afzender = Mijn Profiel → Zakelijk (bedrijfsnaam, zakelijk adres/
    postcode/plaats/IBAN/telefoon, KvK, BTW, zakelijke e-mail — ingevuld: Spark / Roadkill, Bentismaheerd 180 …).
    Bestellingen-tab: knoppen 📄 Factuur · 📦 Pakbon · ✉ <leverancier> concept (uitklappen + Kopieer) · "geboekt".
    `GET /api/shop/orders/{order_id}/documenten`. Archief-URL's zijn `/api/archive/{user}/file/{id}`.
    **Mail wordt niet verstuurd** (concept-modus) tot er een mailverbinding (Outlook-SMTP app-wachtwoord voor
    spark-your-life@hotmail.com / Willems hotmail) in Connections staat. Oud markdown-bonnetje alleen nog voor niet-merch.
    Getest met echte testbestelling (hoodie Navy L, verzenden → RK-2026-0001, 79,55, Promotex-mail 1× hoodie + 1× groot
    + 1× klein); alle testdata (wallet, orders, archief, kasboek, openstaand, logs, taak, bark) daarna verwijderd.
    **Niet gebouwd**: voorraad per kleur/maat; Bestellingen-tab UI alleen via code/API gecontroleerd (Willem heeft de
    enige winkel met orders) — Willem kijkt zelf.
  **Fase 3 — later**: bij bestelling zonder voorraad → leveranciersmail (aantal + productcode,
  standaardtekst) + kopie naar zakelijke e-mail · factuur (PDF, lokaal gemaakt — geen externe dienst) naar koper-mail
  als ingevuld + Workspace-Archief · pakbon naar winkeleigenaar-archief · bestelbon bij bestanden.
  Mail-verzending vereist een provider/SMTP (hotmail-afzender = Outlook SMTP met app-wachtwoord, via Connections);
  tot die tijd **concept-modus**: mail + bon als bestand in Archief, niets verstuurd.
  **Later**: Bestellingen-tab hybride link naar boekhouder + voorraad bijhouden · contacten matchen op e-mail/tel/naam
  aan users → bekende users zichtbaar in privé-gesprekken (Willem 20-10).
  Bekende beperking (bestaand): `create_order` leest producten alleen uit Roadkill's products.json → bestellen bij
  andere shops werkt nog niet; hoort bij fase 3.
- **✅ 20-10 (middag) — Eigen codes, help-samenvatting, profiel-kaders** (`v14_shop_eigen_code_001`, `v14_help_summary_001`,
  `v14_help_admin_mode_001`, `v14_profiel_kaders_001`):
  • Productcode leeg laten → Spark genereert `PREFIX-0001` (verkoop) / `PREFIX-I-0001` (inkoop), ook bij bewerken zonder code;
    prefix per winkel in Inkoop → Instellingen (`settings.code_prefix`, Roadkill = RK; anders eerste 2 letters winkelnaam).
  • Bugfix: `InkoopArtikel.code` was verplicht → 422 bij artikel zonder code; 422-lijst werd rauw in toast gerenderd → crash.
    `apiError()` in `frontend/src/lib/utils.js` nu overal in winkel/contacten/producten.
  • Chat: `route_help()` (smart_intents_service) is de ene plek: `help_open` (expliciet) → popup · `help_overview` ("wat kan
    je") → 7-regel samenvatting + "Zal ik het help-overzicht openen? (ja/nee)" via `session_state.last_question`
    (intent `help_open`, 5 min). Admin-regel alleen bij `admin_mode` (nu ook in compose-request). Semantic-matcher
    canonicals versmald tot expliciet openen.
  • HelpBark leest `useAuth().isAdmin`: admin-mode uit → gewone help zonder toggle; aan → admin-help + toggle.
  • Profiel Algemeen: 3 kaders (Wie ben jij? / Privé / Zakelijk, elk met secties; zakelijk ook website + social).
    `ProfileExtended` +11 velden (beroep, opleiding, social_*, zakelijk_website, zakelijk_social_*) — ontbraken, dus
    "kon niet opslaan". E-mail/Telefoon-opslag zelf werkte al (gecheckt als Emergent).
- **✅ 20-10 (avond, 150-credit-batch) — Relaties · /tree · Zelfscan** (Willems brainfarts: blauwdrukken niet gekoppeld,
  metadata voor zelfscan, zusje's relaties niet onthouden, command-blauwdruk, "bouwen in lagen"):
  • **Relaties voor elke user** (`v14_rel_alle_users_001`, `relation_extraction_service`): oorzaak was hoofdletter-eis + naam
    verplicht → slechts 2/22 users hadden een relatiebestand. Nu: kleine-letter-naam telt als die bekend is (users.json,
    contacten, bel-contacten, eigen relaties); relatie zonder naam → entry `(naam onbekend)` (`naam_onbekend: true`, geen
    persoonskaart) die later gevuld wordt door "mijn zus heet Lotus". Getest: 'mijn broertje willem' → Willem/broer.
  • **Task-agent-brug** (`v14_task_agent_bridge_001`, `chat/task_agent_bridge.py`, in `/api/chat/message` vóór de
    capability-router én in compose): `/tree` → `cap_files_tree` (nieuw in registry, admin_only; admin-mode = beheer-
    rechten in `task_agent.execute(admin_mode=)`), `/cmd <zin>` → `resolve_text` → GET direct, POST/PUT/DELETE eerst
    ja/nee (`session_state.pending_cmd` + `last_question` intent `cmd_confirm`, 5 min). Placeholders/ontbrekende params
    → nette melding. Bewust alleen achter een slash. KB-kaart **Command-blauwdruk** (`kbv2-395f1632`, Weten, 9 tags).
  • **Zelfscan** (`v14_zelfscan_001`, `synapse/zelfscan.py`, `GET /api/synapse/zelfscan`, `POST …/backfill` admin;
    UI `ZelfscanPanel` als 4e tab in Beheer → Integraties): per `_meta.json` footnote/doel/blauwdruk; compleet = footnote +
    doel + (code-modules) ingevulde blauwdruk. Backfill: footnote `legacy_backfill` met mapdatum + vertrouwen 0.5
    (`footnote_meta`), enricher voor doel + blueprint_ref, stubs krijgen echt doel. Backup `_meta.json.bak_zelfscan`.
    Resultaat: 1 % → 55 % compleet, footnote 0 ontbrekend. `_backup*/_preview*` mappen worden overgeslagen.
  **Bevestigd gat**: 59 → 90 blauwdruk-stubs, 3 echt ingevuld; `spark_groeien_public.json` / `spark_tag_curatie_public.json`
  staan nog los van `blueprint_ref`. Feiten-archief: `identity_facts` (cap 15/type) + scratch bestaan; fact-kaart = volgende.
- **✅ 20-10 (nacht, 130-credit-batch) — Feiten-archief + commands zonder slash** (`v14_feiten_archief_001`,
  `v14_task_agent_bridge_002`):
  • `modules/feiten/__init__.py` (router `/api/feiten`, admin-only): kaart-formaat {begrip, lagen{wat, waarom, context},
    tags, kind, status, vertrouwen, bron, keer_gehoord}. **Vier soorten** (Willem): `mening` (persoonlijk, status bevestigd),
    `waarde` (normen & waarden), `overtuiging` (geloof/levensbeschouwing — "hun bijbel", apart van waarden; "ik geloof in X"
    is overtuiging als X levensbeschouwelijk is, anders waarde; "spark bijbel" uitgesloten), `feit` (toetsbaar: ongetoetst →
    getoetst/verworpen door admin). Per user `users/{uid}/feiten.json`, algemeen `data/feiten/spark.json`.
  • Extractie passief in chat (naast relaties) en in compose; `identity_facts` blijft bestaan (LLM-context) maar wordt via
    `feiten.extract_and_save` aangeroepen → één archief. Migratie-knop: 69 kaarten uit 4 users ingelezen (idempotent).
  • **Feit wint van LLM** (0b3d, vroeg in de flow, vóór profile_lookup): "wat weet je van mij", "wat vind ik van X",
    "waar hou ik van", "wat vind ik belangrijk", "wat geloof ik", "wat is mijn X" → antwoord uit kaarten met
    "(nog niet getoetst)" waar van toepassing; "geen LLM-gok". Geen W-vervolgvraag (Willem: niet natuurlijk genoeg).
  • Alleen admin ziet het (Beheer → Instellingen → **Feiten**: tellers, filters scope/user/soort/status/zoek, kaarten met
    getoetst/verwerp/herstel/bewerk/verwijder, handmatig aanmaken, migratie). Gebruikers zelf niet ("soms willen mensen
    dingen niet weten over zichzelf").
  • **Laag 2 commands** (`task_agent_bridge.try_resolve_free`, 0b3e ná capability-router, dus alleen zinnen die nergens
    landden): actie-werkwoord vereist, geen vraagteken, score ≥ 0.25 → "Ik lees: tags [notitie, verwijderen] → verwijderen
    → `cap_notes_delete` (zekerheid 40%). Zal ik het doen? (ja/nee)". Altijd bevestigen, ook lezen (we testen nog).
    Ja/nee → regel in `data/system/command_learning.jsonl` (zin, cmd, tags, besluit) als leerdata.
- **✅ 20-10 (laat) — leren van ja/nee · ontbrekende gegevens · feiten getoetst · wijsheid · Joy-fix**
  (`v14_task_agent_bridge_003`, `v14_rel_dedupe_001`):
  • `task_agent_bridge._leer_bias`: per cmd ja/nee-tellingen op exacte zin of gelijke tag-set → score +0,15/ja −0,10/nee,
    drempel 0,25 vervalt bij ≥1 ja ("zekerheid 60%, 2× eerder ja"); ≥2 nee en meer nee dan ja → volgende kandidaat of niets.
  • `_PARAM_SPEC` note_id/task_id/event_id → lijst ophalen (intern via ASGI), genummerd kiezen (nummer of tekst, "laat maar"
    annuleert), daarna opnieuw ja/nee met de gekozen titel → uitvoeren. Getest: 2 notities → "2" → "ja" → verwijderd.
  • Feiten getoetst (Willem: "feiten zijn feiten, die kan je wel"): 45 ongetoetst → 3 getoetst (zzp-er, 2 neefjes, Bitvavo),
    7 omgezet naar mening, 33 verworpen met tag `momentopname` (gevoel/bezigheid/tijd), 2 open. `_MOMENT`-filter in
    `feiten.extract_and_save` voor triggers i_am/i_have → zulke zinnen komen niet meer als feit binnen.
  • Spark Wijsheid: kern-woorden van `wat` (Jaccard ≥ 0,5), zelfde soort, ≥2 users, nog geen Spark-kaart → voorstel;
    `POST /voorstellen/keur-goed` maakt Spark-kaart (bron wijsheid, users + bron_ids). UI-blok in Feiten-tab.
  • Joy/Heidi (Willem): oorzaken = dubbele personen (Joy + Joy Spakman…) → "Welke Joy?", rommel-relatie "Jarig" (uit "mijn
    moeder is jarig"), en feiten-antwoord kaapte "wie is mijn moeder". Fix: `_resolve_person` dedupet voornaam ⊂ volledige
    naam met gelijke relatie; relaties/persons van user-001 samengevoegd; `NAME_BLACKLIST` + toestandwoorden;
    `vind_antwoord` slaat relatiewoorden over en matcht alleen op wat/begrip. Heidi staat correct als moeder in de
    relatie-graaf; ze staat niet in Contacten (daar alleen Maaike/Lotus/Joy als "familie" zonder detail).
- **✅ 20-10 (laatste) — contacten-sync · agenda via ja/nee · wijsheid in antwoorden · 2 feiten** (`v14_contacten_relatie_sync_001`,
  `v14_task_agent_bridge_004`): `contacten.routes._relaties/_relatie_voor/sync_relaties` (+ `POST /api/contacten/{uid}/sync-relaties`,
  automatisch na `add_relations`); `alle_contacten` zet `relatie` op privé-contacten (roze badge in ContactenTab).
  `task_agent_bridge.try_agenda_create`: werkwoord + "agenda/afspraak" → `_parse_afspraak` (morgen/overmorgen/weekdag/dd-mm,
  "10 uur"/"14:30", titel = rest zonder ruis) → pending `cap_agenda_event_create` {titel, date ISO, scope prive} → ja → POST.
  `feiten._wijsheid_antwoord`: alleen bij vraagzin, kernwoord ≥4 letters in wat/begrip/tags van Spark-kaarten (getoetst/bevestigd).
  Feiten: achternaam-historie → mening (`persoonlijke-historie`, niet toetsbaar); "ik ben willem" van user-672f0e5c → verworpen
  (`identiteitsclaim`, Willem: "iemand kan ook liegen"). Momenteel 0 ongetoetst.
  Correctie Willem: "katten en techniek" → mening *techniek* (wel een kat gehad, geen "houden van"), ook in `identity_facts`
  (LLM-context). Bewerk-formulier in Feiten-tab nu volledig: begrip, soort, wat, waarom, context; soort-wissel zet status mee.
- Later: `stts` (eerst eigen opnames matchen, dan Whisper) · vervoegingen/stam-matching (nu exacte begrip-match) ·
  eigen stemmodel uit de dataset (`voice_transcript` is al het label).


### ↪ Sessie 58 + 56b clusters

## 🧹 CLUSTER — Sessie 58 (15 feb 2026) — Subject-Agent-laag + Registry-fundering (Principe #8)

**Kern**: Principe #8 (Subject-Agent Pattern) wordt geïmplementeerd. Elke losse
string / capability krijgt een agent-wrapper en een KB-kaart zodat Spark
introspectief kan uitleggen wat hij kan.

### ✅ AF (Sessie 58 — dag 1)

- **`/app/backend/modules/agents/`** aangemaakt met 4 dun-wrapper skeletons:
  `task_agent`, `admin_command_agent`, `personal_agent`, `spark_pulse_agent`.
  Signatures + docstrings + TODO's; geen volledige logica.
- **12 draft KB-kaarten** ingevuld en gecureerd naar juiste lade (Weten/Doen):
  4 agents + 8 architectuur-begrippen (`principe-8`, `spark-architectuur`,
  `command_registry`, `intent-uitvoering`, `compose`, `privacy_matrix`,
  `self_awareness`, `observability`). Elk met laag1-4, ws5, tags, topic.
- **Apostrof-ghost-preventie** — `tag_sanitizer.sanitize_tag` normaliseert nu
  unicode-apostrofen (’‘´`‛ʼ → '). `orphan-tag-scanner._canonicalize` idem.
  Data-fix uitgevoerd (8 tags + 1 begrip `Programma's`). 6 regressietests
  toegevoegd, 18/18 pass.
- **Apostrof-normalize als admin-command**: `POST /api/kb/v2/admin/normalize-apostrophes`
  + registry-entry `cap_kb_normalize_apostrophes` + toegevoegd aan
  `admin_command_agent._ADMIN_CMD_WHITELIST` — eerste échte lid van de agent.
- **Registry-batch-1**: 38 nieuwe entries toegevoegd voor agenda (9), notes (7),
  bugs (5), help (3), triggers (8), KB v2 admin (5), commands-list (1).
  Registry: **14 → 76 entries**.
- **`GET /api/commands/list`** nieuwe route (module `system/commands_list_routes.py`)
  met filters `module`, `admin_only`, `gradatie_max`, `q`. Dit is Spark's
  "welke commando's ken je?"-endpoint via `task_agent.list_commands()`.
- **Auto-scanner** — `scripts/scan_routes_for_registry.py` scant alle 669
  `@router`-decorators in `/app/backend/modules/` en genereert concept-entries
  voor missende routes. Output: `/tmp/registry_scan_YYYYMMDD_HHMMSS.json`
  met 617 concept-entries klaar voor review.
- **Admin-whitelist uitbreiding**: 17 cmd_id's in `_ADMIN_CMD_WHITELIST`
  (KB-onderhoud, agenda-archive-all, bug-moderation, triggers-editing).
- **Foto's-kaart upgrade** (`kbv2-c0421b96`) — Willem's uitgebreide versie
  overschreven op de bestaande kaart (7 use-cases, betere ws5). Lege
  ghost-duplicaat `kbv2-63c3d542` (unicode-apostrof) opgeruimd.
- **Ervaring-uit-brainstorm — `kb_hit_log_agent` skelet + KB-kaart**:
  `modules/agents/kb_hit_log_agent.py` met `record()`/`retrieve()`/`stats_snapshot()`,
  datafile-formaat vastgelegd (`data/chat_analytics/kb_hits.jsonl`, JSON-Lines,
  gestandaardiseerde `match_source`-labels). KB-kaart `kbv2-dc6c015e`
  volledig gevuld in Weten. Smoke-test: 2 rijen geschreven + teruggelezen.
  Hooks in `response_composer` / `snap_service` bewust NIET geplaatst
  (skelet-fase — format vaststellen eerst).
- **KB-test-kaart `orphan-tag scan`** (`kbv2-18829e2b`) volledig gevuld in
  Weten met 10 tags — bewijs dat Principe #8 werkt: cmd_id in registry
  + concept-naam in KB, twee kanalen, één begrip.
- **Small tweak**: topic-overview sample-limiet van 5 → 10 begrippen
  (`smart_intents_service.py:683`). KB is gegroeid naar 7000+ kaarten;
  5 sample-hits was te karig geworden.

### 🎯 OPEN (Sessie 58 vervolg — registry-uitbreiding)

**Doel**: 617 → 0 missende entries via module-per-module aanvulling.

- **P1 — Registry batch-2 (KB v2)** — 54 kb_v2-routes met echte intent_tags.
  Dit is de grootste single-module wisser. Zonder deze kan Spark's KB-chat
  niet volledig introspectief zijn (bijv. "hoe zoek jij kaarten?" → moet
  naar `kbv2_search` kunnen wijzen).
- **P1 — Registry batch-3 (chat)** — 30 chat-routes. Cruciaal voor Sparks
  zelfuitleg over eigen chat-flow (intent-matching, compose, snap).
- **P1 — Registry batch-4 (spark + spark_planner + spark_kasboek)** — 32 routes
  over Sparks eigen leven (identity, planner, saldo).
- **P1 — Trader-intents-registratie** — `modules/trade/trader_intents.py`
  bevat al 8+ chat-intents (`trader_start`, `trader_stop`, `trader_status`,
  `trader_explain`, `trader_recent_trades`, etc.) die vóór de LLM-router
  worden gematcht. Werkt, maar niet in registry — Spark kan er niet naar
  wijzen op "wat kan je met de trader?". Aparte batch (~8 entries).
- **P2 — Registry batch-5 (auth + wallet + profile)** — 79 routes. Belangrijk
  maar minder Spark-introspectief.
- **P2 — Registry batch-6 (trade)** — 95 routes. Grootste module; kan gefaseerd
  per bot/reconcile/monitor.
- **P2 — Registry batch-7 (boekhouder)** — 47 routes. Multi-book.
- **P3 — Restant** — accounting, achievements, admin, backup, files, graph,
  shop, settings, winkelstraat, etc. — nog ~180 routes.

### 🧠 Agent-skelet fill-in (Principe #8 vervolgstappen)

- **P1 — `task_agent.resolve()`** — tag-overlap-score + tie-break op laagste
  gradatie_min. Return `{cmd, score, matched_tags}`. Test: geef `["tellen","gebruikers"]`
  → moet `cap_tellen_gebruikers` (score 2) terugvinden.
- **P1 — `task_agent.execute()`** — gradatie-check + params-validatie + dispatch
  via `entry.source` + audit-log-entry naar `data/system/audit_log.json`.
- **P1 — `admin_command_agent.execute_as_admin()`** — whitelist-check +
  auth-guard hergebruiken van `modules.auth.deps.require_admin_capable` +
  gestructureerde audit `event_type=admin_action`.
- **P1 — `kb_hit_log`-hooks plaatsen** in `chat/response_composer.py`,
  `chat/snap_service.py` en `chat/smart_intents_service.py` op de plekken
  waar KB-kaarten worden gebruikt (topic-overview, snap-lookup,
  sentence-match, compose-embed). Één regel per hook — best-effort.
  Zodra ledger vult: dead-weight-analyse mogelijk.
- **P2 — `personal_agent.snapshot()`** — depth minimal/standard/deep uitwerken
  met 30s TTL-cache; consumer wordt `compose_routes`.
- **P2 — `spark_pulse_agent.pulse()`** — KB + trade + LLM-router + chat
  metrics-blokken, health_score berekening, narrator-templates. Leest ook
  `kb_hit_log.stats_snapshot()` zodra hooks live zijn.
- **P2 — `ervaring_agent` skelet** — nieuwe agent boven `kb_hit_log`.
  Distilleert conclusies uit reeksen van gesprekken; LLM-onafhankelijk zodat
  Spark bij LLM-uitval nog steeds "geleerde ervaring" heeft. Structuur:
  `modules/agents/ervaring_agent.py` + datafiles
  `data/ervaringen/ledger.json` / `disputed.json` / `verified.json`.
  Bronnen: `chat_conclusion` (pattern-match afsluiters), `interaction_log`
  (bijv. openingszin-tracking), `external_check` (Wikipedia/Google, P3).
  Nog niet bouwen — pas als `kb_hit_log` een paar honderd rijen heeft.

### 📌 Uitgebreide stats (kleine wins, hoge waarde)

- **P1 — `GET /api/kb/v2/stats/extended`** — huidige `/stats` uitbreiden met
  `topics_count`, `topics_top20`, `avg_verbanden_per_kaart`, `median_verbanden`,
  `cards_zonder_verbanden`. Directe waarde: Spark kan "hoeveel onderwerpen
  ken je?" en "gemiddeld verbanden per woord?" beantwoorden.
- **P2 — `POST /api/kb/v2/admin/topics/recompute`** — per kaart of bulk
  het `topic`-veld herberekenen op basis van tags. Nuttig bij drift na
  bulk-import of merges.

### 🧹 Kleine opruim-items (opgetekend maar niet gedaan)

- **`kb-hit-log` seed-script niet uitgevoerd** — `scripts/seed_registry_concepts_to_inbox.py`
  bestaat maar niet gedraaid. Zou 617 skeletons in KB-inbox zetten met
  cmd_id als begrip. Beter: script aanpassen zodat het lees­bare begrip
  genereert (bv `cap_agenda_events_list` → "agenda-events tonen") vóór
  massa-seed.
- **`Programma's`-kaart** heeft nu rechte apostrof; index-alias unicode-versie
  verwijderd. Backups: `*.bak_apostrof_normalize_*` + `*.bak_orphan_scan_test_*`.

### 🎨 Backup-splitsing + Response-tijd + Thinking-indicator (dag 2)

**Melding (Willem)**: "alleen wijzigingen wordt te groot" + "wacht-icoon tijdens
input" + "response-tijd loggen leuk voor later onderzoek".

- **✅ Backup-splitsing 3 slices** (`modules/backup/routes.py` + UI):
  - `/api/backup/download/changes/chat` — chat, dagboek, dialogen, chat_analytics
  - `/api/backup/download/changes/trader` — trade, financial, bitvavo
  - `/api/backup/download/changes/rest` — al het overige
  - `/api/backup/download/changes/sizes` — preview per slice
  - **Bonus fix**: `EXCLUDE_REL_PREFIXES` sluit oude `_backup_*`/`_backups/`/`_archive/`
    /`_deleted_*` dirs uit → **1185 MB → 528 MB** (-657 MB backup-in-backup).
  - Frontend `IntegratiesPage.js`: 3 nieuwe DownloadCards (emerald/cyan/teal)
    met live size-preview per slice; KB-diff + Volledig in aparte rij.
- **✅ Response-tijd logging**:
  - `POST /api/chat/log-response-time` — schrijft naar
    `data/chat_analytics/response_times.jsonl` per turn (duration_ms, endpoint,
    user_id, ok, used_model, message_length).
  - Frontend meet met `performance.now()` rond beide fetch-paden
    (`/api/chat/message` én `/api/spark/compose`).
  - Verwacht consumer: latere analytics + `spark_pulse_agent.pulse()`.
- **✅ Thinking-indicator** in `ChatInput`:
  - Nieuwe `thinking`-prop; toont `Loader2` + "denkt…" label links + spinner
    in send-knop; input disabled; placeholder wisselt naar "Spark denkt na…";
    border wisselt naar amber-glow tijdens wachten.
  - `sparkThinking`-state in `GesprekkenPage` toggles rond fetch-calls,
    ook bij compose-deep-mode.

### 📌 OPEN (voor volgende sessie — image-upload-naming + dashboard-kleurschema + chat-persistence)

- **P2 — Image-upload → begrip mapping**:
  - Bij upload van een afbeelding op een KB-kaart wordt de bestandsnaam
    (bijv. `appel.png`) automatisch het begrip. Zo krijgt elke afbeelding
    meteen een correct onderwerp en kan Spark later zeggen "wil je een appel
    zien?".
  - Bij een 2e afbeelding op hetzelfde begrip → automatisch nummeren
    (`appel-2.png` etc.).
  - Nieuw KB-kaart-concept: "**wacht-icoon**" (Willem maakt zelf met
    512x512 afbeelding) → deze wordt de eerste test-case voor het
    image-upload-naming-patroon.
  - Nadenken: welke module handelt image-uploads af (`kb_v2/media_routes.py`?),
    hoe passen we filename → begrip toe zonder bestaande kaarten om te gooien,
    en waar valt de "wacht-icoon" onder (weten? doen?).

- **P2 — Dashboard-kaders kleurschema**:
  - Icoon-accent van Agenda/Notities/Gesprekken-cards uit
    profiel → instellingen → kleurbeheer trekken ipv hardcoded
    (`#f97316` / `#22c55e` / `#06b6d4`). Waarschijnlijk via de bestaande
    CSS-variabelen `--glow-base` / `--glow-accent` (die de chat-bubbles
    ook gebruiken sinds v13_bubble_glow_persoonlijk_001).
  - Nette fallback: als user geen kleuren gekozen heeft → huidige defaults.

- **P1 — Bug: Spark stopt bij tab-wissel**:
  - Symptoom (Willem): wisselen van Gesprekken naar andere pagina tijdens
    het wachten → Spark's antwoord komt niet meer aan.
  - Vermoedelijke oorzaak: `GesprekkenPage` unmount, `setSparkMessages`
    krijgt geen effect meer (React silent no-op op unmounted component).
    Fetch loopt in JS door maar het resultaat verdwijnt in het luchtruim.
  - Voorgestelde fix: sla per pending-fetch een record op in
    `sessionStorage` (turn_id + text), en in de `.then()` óók het resultaat
    naar `sessionStorage`. Bij `GesprekkenPage` mount → lees unread-results
    + herstel `sparkThinking`-state. Bonus: response-tijd-logging blijft
    werken want die is in de fetch-thread, niet in de component.
  - Alternatief: lift `sparkMessages` naar een globale context/provider
    zodat unmounten niet meer uitmaakt. Groter refactor.

### 🧹 KB-opschoning + Spark Games lade (17 sep 2026)

**Trigger (Willem)**: orphan-tag scan maakte skelet-kaarten `voelenbegrip`, `rna`, `dnd`.
"dit is een fout woord … dit moet goed gezet worden" + "de game is inactief tot core
klaar … zonde om weg te doen … game zou eigen container moeten zitten" + "de naam wordt
universeel Spark World".

- **✅ `voelenbegrip`** — foute tag op 3 weten-kaarten (Vervanging, Wedergeboorte,
  Zoetwater) verwijderd; skelet `kbv2-eb46e512` weg. Oorsprong onvindbaar (zat al in
  oudste backup 23-08).
- **✅ `rna`** — géén fout: echte biologie-tag op Celkern/Genen/Virussen. Skelet
  `kbv2-977940f0` blijft in inbox; **Willem vult hem zelf in**.
- **✅ `dnd` root cause** — verweesd legacy-bestand `v2/inbox.json` (oude `kb-*` ids,
  door geen enkele module gelezen) met 10 grondstof-drafts. Verplaatst; leeg-gezet.
  Learning: de orphan-scan globt `V2/*.json` — élk los json-bestand in die map telt mee.
- **✅ Dubbele Utrecht** — kbv2-592d038c was een game-kopie van kbv2-6507fdfc (identieke
  lagen). Kopie is nu `Utrecht (Spark World)` in de games-lade met de fractie-link.
- **✅ 5e lade `games` ("Spark Games", 🎮, `#22c55e`)** — geregistreerd in:
  `kb_v2/service.py` (LADES + LADE_META), `kb_v2/routes.py` (alle lade-lijsten, move
  valid-set, dupes-files), `graph/sync_service.LADE_COLORS`, `chat/snap_service.V2_LADES`,
  `chat/spark_snuffel`, `kb_v2/llm_generate_routes`, `kb_v2/apostrophe_normalizer`,
  frontend `KennisbankV2Page.LADES` + count-fetch. Orphan-scan **slaat
  `knowledge_v2_games.json` over** (game-tags als `grondstof`/`fractie` zijn intern).
  Nog NIET in: `bulk_5w_fill_routes`, `curation_routes`, `text_importer`,
  `card_session_service`, `scan_service`, `spontaneous_w_service`, `wedervraag_service`
  (bewust: die werken op de 4 kennis-lades; games volgt als de game weer actief wordt).
- **✅ Spark World hub-kaart** — oude kaart "D&D" (kbv2-5ae16b66, generieke Dungeons &
  Dragons-uitleg) hernoemd + herschreven: sandbox-game, fictieve steden, fracties,
  bouwstenen, status geparkeerd. Verbanden → Base Line, Rugzak, Utrecht (SW), SPS.
- **✅ Base Line = basiswaarden-kaart** — oorsprong (0,0,0), AD-tijdrekening, licht/schaduw
  50/50, 4 elementen, fracties, startinventory 4 slots + 10 kg. Oude verhaal-lore weg
  (gearchiveerd in `data/dnd/lore_index.json`).
- **✅ Tags** — `d&d`/`dnd` → `spark world` overal. SPS-kaart kreeg tag `spark games`
  + verband naar Spark World.
- **✅ Index + graph herbouwd** (`POST /api/kb/v2/admin/rebuild-index`, `POST /api/graph/rebuild`):
  7280 index-entries (155 stale alias-keys van oude homoniem-namen weg), 7343 nodes.
- **Backups**: `*.bak_voelenbegrip_fix_*`, `*.bak_dnd_container_*`, `*.bak_spark_games_*`,
  `data/dnd/_kb_cards_moved_to_games_lade_*.json.bak`, `data/dnd/_legacy_kb_inbox_moved.json.bak`.
- **Getest**: curl stats/lade/find/orphan-dry-run + screenshot Spark Games-tab. Geen testing-agent.

- **📌 BESLUIT (Willem, 17-09-2026)** — de fictie-gate is de **standaard** voor alle huidige en
  toekomstige game-/fictie-lades: game-kennis staat gewoon in de KB (vindbaar, verbindbaar,
  later toepasbaar in de wereld) maar doet in antwoorden alleen mee bij game-context.
  Nieuwe game-kaarten altijd in lade Spark Games, nooit in Weten. Nieuwe fictie-lade →
  toevoegen aan `FICTIE_LADES`, verder niets.
- **✅ Text-importer tags (`v14_text_importer_tags_001`)** — Willem zag kaarten zonder tags na "Importeer txt".
  Root cause: `_TAGS_HDR_RX` eiste exact `Tags` alleen op een regel; `Tags:`, `**Tags**`, `Tags: a, b` (inline),
  `- lijstjes`, `#hashtags`, `·`-scheiding gaven stil 0 tags of één rommel-tag. Parser nu tolerant (10 varianten
  getest). Learning: een stil-lege parser-uitkomst moet een waarschuwing in de import-response geven (TODO).
- **✅ REGEL `MIN_TAGS_FOR_LADE = 5` (`v14_min_tags_001`, Willem)** — "zonder tags kan hij niet naar een lade en
  blijft in algemene inbox; minimaal 5 tags voor goedkeuring." Twee poorten: (1) `text_importer` zet nieuwe kaart
  met <5 tags in inbox (`_inbox_reason`, `_suggested_lade`, `needs:["tags"]`) + `warnings[]`/`to_inbox` in
  response, UI toont amber waarschuwingsblok + tag-aantal in dry-run; (2) `service.classify_card` weigert met
  `reason:"min_tags"` (toast in UI). `tags_gate()` is de ene bron. Bewerken van bestaande lade-kaarten blijft vrij.
- **✅ 44 tagloze kaarten getagd** via `scripts/fill_missing_tags_v14.py` (LLM 5-8 tags + sanitize; herbruikbaar:
  pakt alle kaarten met ≤1 tag). Graph herbouwd.
- **✅ Fictie-gate (`v14_fictie_gate_001`)** — Willem: "spark moet geen fantoom krijgen met
  realiteit". `kb_v2/service.py`: `FICTIE_LADES={"games"}`, `is_game_context(text)`,
  `filter_fictie()`. `semantic_lookup` filtert games-kaarten weg zonder game-context;
  `snap_service._get_index(query)` heeft nu een 'real'- en 'all'-index. Ambient
  services (spontaneous_w, wedervraag, scan, card_session) zien games NIET.
  Test: "wat is utrecht" → echte kaart; "wat is spark world" → hub-kaart.
- **✅ Bigram-snap (`v14_snap_bigram_001`)** — `multi_lookup` probeert eerst 2-woord-begrippen
  ('spark world', 'base line') vóór losse woorden. Was een gap voor álle meerwoordige kaarten.
- **🐛 ✅ Chat 500 gefixt** — `ResponseTimeLog`-blok (sessie 58) zat midden in `ChatMessage`,
  waardoor `user_id/channel/session_id/admin_mode` van de class los waren → `/api/chat/message` 500.
- **🐛 ✅ Chat-lookup dood sinds sessie 54 (23 aug)** — losse `return response` onder
  `if req.user_id:` in de agenda-CREATE-branch (commit 62a87352) liet élke gewone
  kennisvraag leeg terugkomen ("Hmm, daar moet ik even over nadenken") vóór snap bereikt werd.
  Learning: na een branch-herordening altijd een `trace` op `return`-regel draaien
  (`sys.settrace` op `process_message`) — 98 `return response` in één functie is te veel om op het oog te zien.

**📌 OPEN — Spark World (pas oppakken als Core klaar is, Willem)**
- P2 — Utrecht (Spark World) hernoemen naar een zelfbedachte stadsnaam (Willem: layout was NL-kaart,
  geen admin-front voor de game nog) + `steden.json` id `utrecht` mee.
- P2 — Spark Games-tab: filter per `game`-veld (Spark World / Steen Papier Schaar / …).
- P2 — Restore-/eco-container per game zodat game-data en KB-kaarten samen verhuizen.
- P2 — SPS-scorelijst koppelen als gevechtsmechaniek in Spark World.
- P2 — 8 grondstof-drafts in games-lade invullen (laag1 ontbreekt).
- P2 — `rna`-kaart invullen (Willem).
- P3 — 17 begrippen met leading/trailing spatie (`'ADA '`, `'Schors '`, …) strippen;
  index-keys zijn al gestript dus lookups werken, maar het is rommel.

### 🎨 Dashboard-kaders live (dag 2 vervolg)

**Melding (Willem)**: "in dat kader zou ik graag de eerst volgende komende
afspraak willen zien uit de agenda. en als ik er op klik na agenda ga.
kader als nodig aan kleur schema in beheer mijn profiel instellingen
kleurbeheer daar. zo zou je ook een notitie kader moeten hebben. met de
prio taak als eerst, en als die er niet is de laatst ingevoerde notitie.
gesprekken net zo: laatst gegeven output van spark, community aan/uit,
laatst binnengekomen privé als bericht → klik → naar privé."

- **✅ Agenda-kader** (`DashboardPage.js`): 
  - Fetcht `/api/agenda/events/{user_id}`, filter op `datum >= nu`, sorteert,
    toont eerste komende afspraak (titel + geformatteerd tijdstip).
  - Fallback-tekst "Geen aankomende afspraken" indien leeg.
  - Klik → `onNavigate('calendar', '/calendar')`.
- **✅ Notities-kader** (nieuw):
  - Fetcht `/api/notes/tasks?user_id=...` + `/api/notes/all?user_id=...`
    parallel. Prio-taak (`hoog`/`high`) wint; anders eerste taak; anders
    laatste notitie.
  - Rode streep bij hoge prio, groen anders. Kind-label ("taak · hoog"
    of "laatste notitie") onder de content.
  - Klik → `onNavigate('notes', '/notes')`.
- **✅ Gesprekken-kader** verrijkt:
  - Laatste Spark-turn bovenaan met Spark-avatar, klik → sessionStorage
    tab='spark', navigate naar chat.
  - Community-berichten alleen zichtbaar als `community_chat_enabled` aan
    staat in Profiel → Instellingen → Chat zichtbaarheid (zelfde bron als
    GesprekkenPage, geen aparte dashboard-toggle — dashboard is overzicht).
  - Laatste privé onderaan als notification-badge (cyan dot); klik zet
    `sessionStorage.spark_prive_contact_id` én tab='prive' zodat de
    chat-pagina meteen dat gesprek opent.
- **✅ Notities-kader correctie**: hoge-prio taak (`priority === 'hoog'`)
  wint; anders **laatste notitie** (bug-fix: eerder werd elke open taak
  vóór de notitie geplaatst — spec was strikter).
- **✅ Data-sortering fix**: sparkLog-conversations en notes worden nu
  expliciet gesorteerd op timestamp/datum descending in de frontend ipv
  te vertrouwen op backend-array-volgorde (voorkomt out-of-order-drift
  wanneer entries ooit niet chronologisch geappend werden).
- **✅ Vast formaat + scroll** — `Card`-component kreeg `fixedHeight` prop
  (`h-40` body + `overflow-y-auto`). Agenda/Notities/Gesprekken hebben
  nu identieke hoogte naast elkaar, scrollen intern bij lange inhoud.
- **Nog te doen** (P2, hierboven): kaart-icoon-accent uit user-kleurschema
  ipv hardcoded oranje/groen/cyaan.

---



**Trigger**: Willem: "iedere user met potje moet trader werken. en hij is stuk."
Bitvavo had €69.79 aan BTC (7 potjes waardig) terwijl registratie maar 1 open pot bij
Spark toonde. Ook: papertrail toonde Spark 8 tokens / 9 potjes na expired-gift Gerben.

### ✅ AF (Spoor A — root-fix backend)

- **v13_filled_coin_persist_001** — `open_pot()` + `open_cluster()` accepteren nu
  `filled_coin` kwarg → persist in `position.filled_coin` (pro-rata bij cluster).
  Was `null` → downstream drift op multi-user proxy. Nieuwe trades vullen dit
  automatisch vanaf Bitvavo's `filledAmount`.
- **v13_monitor_filled_pass_001** — `monitor.py` parseert `float(result["trade"]
  ["filled"] or 0)` uit `execute_real_trade` en geeft door aan
  `open_cluster`/`open_pot`-fallback.
- **v13_legacy_508_removal_001** — 3 hardcoded €5.08 fallbacks → €10 (huidige
  potje-min): `monitor.py:1428, 1709, 1711`. Docstring `potjes.py:5` bijgewerkt.
- **v13_ghost_cleanup_57** — Geiser pot-001 + Gerben pot-001 (beide BTC-EUR
  ghost) via `auto-fix-ghosts-all` naar `free`. Backfill Spark pot-006 met
  0.00102325 BTC uit Bitvavo.
- **v13_btc_redistribute_57** — 3 potjes verhuisd (Willem pot-001 BCH→BTC,
  Spark pot-007 BCH→BTC, Spark pot-002 ETH→BTC) + 0.00102325 BTC verdeeld over
  7 potjes (Willem 2, Spark 3, Geiser 1, Gerben 1). Bitvavo ↔ registratie diff = 0.
- **v13_willem_bot_start_57** — Willem's bot was `running=false` ondanks 3 potjes;
  gestart. Nu draaien alle 4 users met tokens.

### ✅ AF (Spoor B — UI consolidatie)

- **v13_trader_console_subtabs_001** — Analytics/Trade tab van 5 losse panels
  → 3 sub-tabs `trader-subtab-overzicht|sync|anker`:
  - **Overzicht**: RestwaardePortfolio + SparkTraderStatsPanel + Bot-cards + Audit-trail
  - **Sync & Reconcile**: 4 repair-buttons (`repair-auto-fix-ghosts-all`,
    `-close-sold-all`, `-rebalance-from-bitvavo`, `-refresh-anchors`) met
    confirm-dialogs + JSON-result panel + ReconcileSparkPanel
  - **Anker & Strategy**: AnkerPanel gap-up guard
- Testing_agent: 100% backend + 100% frontend, geen regressies.

### ✅ AF (Sessie 56 vervolg)

- **v13_gerben_retro_accept_56** — Gerben's expired gift (24u+ overschreden) op
  Willem's verzoek retro geaccepteerd: gift → `accepted`, Spark tokens 8→7,
  Gerben 0→1, pot-008+pot-009 bij Spark opgeruimd (0 trades), pot-001 bij
  Gerben aangemaakt (`minted_from: gift_retro_accept:8dc10eb9`). Papertrail
  `roar_balances.transactions` bevat `gift_accepted_retro` entry.
  Supply-integrity: Treasury (999.987) + Circulating (13) = 1.000.000 ✓
- **v13_kbv2_text_import_ws5_fix_57** — 5W-vraagwoorden (wie/wat/wanneer/waar/
  waarom/hoe) werden door text_importer als losse skip-tokens gefilterd →
  legitieme kaart-titels ("Waar", "Wat", "Hoe") gingen verloren. Nu detecteert
  regex `^\s*(wie|wat|...)\s*:` alleen 5W-VELDEN (met dubbele punt). Losse
  vraagwoorden als kaart-titel komen door. 4/4 tests + 2 regressie-tests groen.
- **v13_prod_merge_57** — Backup uit prod (deploy 2026-08-27 21:26) → preview:
  13 trade-files gemerged (`user_potjes`, `trade_history/user-*`, `trade/anker/*`,
  `roar/price_snapshots`, `trade/monitor_state`). Spark's pot-006 kreeg 1 extra
  BUY-trade uit prod, capitals van 10.04 → 10.03 door lopende trades.

### ✅ AF (Spoor C — Snap Agent + zelfbewustzijn, sessie 57 vervolg)

**Aanleiding**: Willem — "worden nieuwe woorden niet gelijk herkend door snap en
KB-kaart van dat woord gemaakt?" Bevestigd via snuffel: 3 losse write-flows
(trigger_learner, chat/routes, lite_card_factory) + `scan_spark_response` liep
alleen achter `_llm_analyze`-guard in trigger_learner → 90% van chat-turns geen
scan.

- **v13_snap_homoniem_fix_57** — `spreken:snap` (schnaps/borrel) had homoniem
  met `weten:snap` (kenniskaart). Rename `spreken:snap` → **"snap (drank)"**,
  aliassen `[snap, snaps]`. `weten:schnaps` uitgebreid met aliassen `[snap, snaps]`
  en tags `[snap, snaps, borrel, sterke drank]`. `knowledge_index.json` — `"snap"`
  wijst nu uniek naar de kenniskaart. `GET /api/kb/v2/homonyms` → 0 conflicten.

- **v13_snap_agent_57** — Nieuwe module `modules/chat/snap_agent.py`. Centraal
  ingangspunt voor onbekend-woord-detectie:
  - `scan_llm_output(spark_response, user_text, user_id, turn_id, max_new=3)`
  - `scan_user_input(text, user_id, turn_id, max_new=3)`
  - Rate-limit: 30 kaarten/user/uur (constante `_RATE_LIMIT_PER_HOUR`)
  - Footnote-verrijking bij elke aangemaakte kaart: `aangemaakt_door=snap_agent`,
    `origin`, `herkomst_turn_id`, `context_snippet`, `llm_count`
  - Thin wrapper: delegeert lookup aan `llm_output_scanner`, dedupe+schrijven aan
    `kb_v2.service.add_to_inbox` (deep-scan alle 4 lades, auto-repair index).

- **v13_trigger_learner_unconditional_57** — `trigger_learner.py:learn_from_interaction`
  aangepast: `_snap_llm_output()` wordt nu ALTIJD aangeroepen, niet alleen als
  `_llm_analyze` een trigger-voorstel oplevert. Extra call `_snap_llm_output`
  ook toegevoegd bij text_hash-dedupe-hit zodat óók herhaalde chat-turns bijdragen.
  Non-blocking wrapper `_snap_llm_output` isoleert scan-fouten van trigger-flow.

- **v13_self_awareness_seed_57** — `seed_self_awareness_cards()` genereert
  skeletons in inbox voor 8 core-modules: `snap_agent`, `llm_output_scanner`,
  `trigger_learner`, `lite_card_factory`, `snap_service`, `text_importer`,
  `tag_sanitizer`, `kb_v2 (module)`. Elke kaart kreeg **aanzet-inhoud** (laag1
  + laag2 + laag3 harde feiten + tags) door snap_agent, zodat GPT alleen nog
  laag4 + ws5 hoeft te polishen.

- **v13_fuzzy_matching_content_57** — 3 gerelateerde kaarten volledig gevuld:
  `Fuzzy-matching`, `rapidfuzz`, `fuzz`. Alle 3 in lade `weten`, met lagen 1-4
  + ws5 + tags. Willem's principe geborgd: **kaart bevat geen aannames over
  ongebouwde Spark-code** — pas na daadwerkelijke integratie mag Spark-specifieke
  rol worden toegevoegd (audit-log entry `content_neutralisatie` legt dit vast).

**Testresultaten (in-proc):**
- `scan_llm_output` op fictief antwoord: 3 kandidaten → 3 skeletons met snippet
  en turn_id in footnote. ✓
- `scan_user_input`: 3/3 skeletons aangemaakt. ✓
- Rate-limit: hit exact op 30 pogingen bij spam-test. ✓
- Dedupe: bestaande begrippen blijven bestaand (deep-scan werkt over 4 lades). ✓

### 📌 OPEN (backlog na sessie 57)

- **ROADMAP #6 P1: Fuzzy-fallback in `snap_service`** — rapidfuzz-integratie
  daadwerkelijk bouwen (threshold-advies ≥ 92 voor safe-match). Zodra gedaan:
  de 3 fuzzy-kaarten uitbreiden met Spark-specifieke rol via audit-log-versionering.
- **Snap-agent hooks voor self-repair** — `on_lookup_conflict` (homoniem-warn),
  `on_repeated_miss` (kaart-verrijking-suggestie). Willem's oorspronkelijke idee:
  "als kaart issue heeft en Spark er mee werkt, moet de kaart bijgesteld worden".
- **KB-lade `spreken:snap (drank)`** — jij vult zelf via GPT-flow aan indien gewenst;
  huidige data is behouden.
- **8 module-skeletons afronden** — laag4 + ws5 door GPT afmaken; classify naar `weten`.


### 📌 OPEN (dust + backlog Sessie 57)

- **ETH-dust orphan**: 0.000047 ETH (€0.10) niet aan een pot toegewezen na de
  BTC-redistribute (Spark's pot-002 is nu BTC). Actie: laten staan tot >€1 óf
  reconcile close-sold-all draaien.
- **CSPR orphan**: 159.24 CSPR (€0.40) heeft nooit een potje gehad. Aparte
  markt-toewijzing zou nodig zijn om dit als pot-storage te gebruiken.
- **Analytics testids**: top-level tab-knoppen missen `data-testid` → e2e-test
  tip uit iteration_57. Klein.
- **TradeAnalyticsTab splitsen**: functie is 700+ rgl binnen AnalyticsPage.js
  (totaal 2781 rgl). Kandidaat voor extract naar eigen bestand (ROADMAP-grens 700).
- **KB skeletons "wat" + "hoe"**: door de text_importer fix nu klaar in inbox
  (`kbv2-68f1221c` + `kbv2-476fac19`). Wachten op Willem's GPT-invulling om
  5W-cirkel compleet te maken.

### ⚠️ VOOR DEPLOY

- Spoor A + B zitten alleen in **preview**. Klik "Deploy" om prod-bots ook goed
  te laten werken.
- Sanity-check na deploy: `POST /api/trade/potjes/auto-fix-ghosts-all?dry_run=true`
  → `n_ok:1, n_ghost:0, n_hollow:0` verwacht.
- **Gerben retro-accept** staat alleen in preview (backup uit prod bevatte niet
  `roar_balances.json` en `gift_requests.json`) → gaat mee bij volgende deploy.

---


## 🧹 CLUSTER — Sessie 56b (25-26 feb 2026) — Multi-book fundament + chat-terugblik

**Focus**: Willem's zakelijke werkstroom fundering leggen. Agenda krijgt uren-registratie, chat kan terugkijken op eigen data, boekhouding-books krijgen elk hun eigen uren + clienten met book-type-aware placeholders (zorgclient vs klant).

### ✅ AFGEROND

**Dashboard opschonen**
- `ShadowObserverWidget` + `PerformanceWidget` verplaatst uit DashboardPage naar Widget Kladblok (`admin/sandbox/registry.js`)
- `BugsListWidget` (was tab in Notities) → Kladblok
- `DeployWidget` (was tab in Notities) → Kladblok
- `AdminNotesWidget` — nieuwe scratchpad in Kladblok voor scope=admin notes
- Notities-header: knop-volgorde +Nieuw → Bug melden, Bug-icoon weg

**Agenda uren-registratie** (`v13d_agenda_uren_registratie_001`)
- EventCreate/Update velden: `scope` (prive/zakelijk), `end_date`, `pauze_minuten`, `opdrachtgever`, `onderwerp`, `product_code`, auto `totaal_uren`
- Frontend: Privé/Zakelijk toggle, start+eind tijd, live 7.5u-netto badge, amber tint voor zakelijk
- Spark chat-parser `_extract_zakelijk_fields()` herkent "voor X van 9 tot 17 met uur pauze"
- 7/7 pytest groen (`test_agenda_scope_v13d.py`)

**Chat terugblik-hooks** (`v13d_agenda_terugblik_001`, `notities_terugblik_001`, `dagboek_terugblik_001`)
- Nieuwe capabilities in `capability_handler_service.py`:
  - `agenda_terugblik`: "wat heb ik gisteren gedaan", "hoeveel uur heb ik gewerkt deze week" (aggregatie per opdrachtgever)
  - `notities_terugblik`: "hoeveel notities in augustus", "wat is mijn laatste notitie" (excl. admin)
  - `dagboek_terugblik`: "wat schreef ik gisteren in mijn dagboek"
- Early-agenda-hooks in `routes.py` laten `gedaan/gewerkt/uren` door naar capability router
- 18/18 pytest groen + live geverifieerd op Willem's data

**Notes & Taken scope-veld** (`v13d_notes_scope_001`, `v13d_task_doel_001`)
- `scope` prive/zakelijk/admin op notes en tasks (zelfde termen als agenda — NIET "werk")
- Admin-notities uitgesloten van reguliere notitie-pagina (leven in Kladblok)
- Taken = doelen met tijdvenster: `begin_datum`, `eind_datum`, `budget_uren`, `opdrachtgever`, `onderwerp`
- Task-cards krijgen secondary-color badges voor periode/budget (`var(--app-secondary)`)
- Alles-view mixed notes+tasks

**Clienten-module** (`v13d_clienten_module_001`) — NIEUW MODULE
- `/api/clienten/*` backend + `ClientenPage.js` frontend
- Aparte module (niet persons — persons = familie/vrienden met D&D)
- Velden: naam, contactpersoon, email, tel, adres+postcode+plaats, KVK, BTW, uurtarief, notities, book_id, client_type
- **Dossier-entries** (kop+inhoud+bron) — handmatig of via chat/agenda
- **Spark-learnings** endpoint (`POST /clienten/learning/`) — Spark kan geleerde info wegschrijven per client

**Uren-registratie endpoint** (`v13d_uren_rapport_001`)
- `GET /api/agenda/uren-rapport/{user_id}?period=dag|week|maand|jaar&book_id=X`
- Aggregeert zakelijke agenda-events per opdrachtgever binnen periode
- Book-filter: matcht via opdrachtgever ↔ client.naam van dat book
- Live geverifieerd Augustus 2026: 9.5u totaal, Jeroen 8u + Roline 1.5u

**Boekhouding view fix** (`v13d_admin_view_eigen_default_001`)
- Admin ziet nu default alleen eigen books (was: alle books)
- Cross-user access via `?target_user_id=X` — voor toekomstige Beheer→Gebruikers pagina
- 3× ghost TEST_ books opgeruimd uit preview
- Pytest teardown fix (`test_winkelstraat_p1p4.py` — autouse fixture ruimt TEST_-prefixed books na test-run)

**Multi-book UI**: BookDetailBark 2 nieuwe sub-tabs (`v13d_book_uren_panel_001`, `v13d_book_clienten_panel_001`)
- 📊 **Uren** — periode-picker + samenvatting per opdrachtgever + CSV-export, gefilterd per book
- 💼 **Clienten** — lijst + create-form, book-type-aware label
- Sidebar cleanup: Urenstaat + Clienten uit MODULES-nav
- Book-type placeholders:
  - `entity` (Zorgboerderij) → **Zorgcliënt** met dossier + placeholder-velden (BSN, geboortedatum, zorgindicatie, huisarts, noodcontact)
  - `shop` (Roadkillshop) → **Klant** met factuur-info (factuur_adres, betalingstermijn_dagen)
  - `user_prive` → **Client** generiek

**App Kleurenschema** (`v13d_app_alert_color_001`)
- 4de kleur "Alert / Error" toegevoegd naast Primary/Secondary/Background
- `--alert-base` CSS var, live doorgetrokken naar Bug-melden knop
- Setting `app_alert_color` in `/api/settings/system`

**Theming**
- Agenda + Dagboek + Notities volledig op `var(--glow-base)` — geen hardcoded blauw/pink/amber accents meer
- Semantische kleuren behouden (mood-badges, done=green, delete=alert)

### 🔴 P0 nog open (uit sessie 55, ongewijzigd)
Alle 6 items van "Zelfscan-fundering" cluster staan nog open:
1. Privacy-guard bypass op /api/spark/compose
2. Metadata backfill script
3. Write-guard `_validate_footnote()`
4. Trace-capability "waar heb ik dit gezegd"
5. KB-vulling uit systeem-vakboeken (STARR + Methodiekengids + Begeleid Leren)
6. Fuzzy-snap in chat-flow

### 🟡 P1 uit sessie 56b (nieuw op backlog)
- **book_id op agenda events + notities + taken** → volle multi-book context
- **Actief book globale context** in header (verandert alle tabs mee)
- **Client-detail form** met tabbed zorg-velden vs factuur-velden
- **Factuur-generator**: urenstaat-CSV + client-adres + betalingstermijn → PDF
- **Documenten split** (Privé/Zakelijk) in Archief → Bestanden
- **Roadkill categorisering**: inkopen labelen (spark merch vs doorverkoop)
- **Spark auto-write client learnings**: bij naam-mention in chat de context oppikken en `POST /clienten/learning/{client_id}` doen

---


### ↪ Sessies 54, 53, 52 clusters

## 🧹 CLUSTER — Sessie 54 Opruimwerk (23 feb 2026)

**Doel**: Ruis weg, code strakker, glow-theming door hele app, D&D compleet uitfaseren tot het écht terugkomt.

### ✅ AFGEROND

**Privacy & Security**
- 🛡️ **Privacy Guard v13** (`modules/chat/privacy_guard.py`): strip familie/privé/financieel/gezondheid uit KB-cards + identity_facts + system_prompt voor gradatie ≥5. 13 pytest groen. Emmy-lek gedicht.
- 🔍 **User-lookup "weet jij wie X is"**: 2 nieuwe patronen + admin-bypass in `smart_intents_profile.py`. Was: Spark hallucineerde over Emmy.
- 🧯 **LLM-lek preventie** (`modules/kb_v2/tag_sanitizer.py`): centrale sanitizer voorkomt dat LLM-multi-line output als tag opgeslagen wordt. Ingehaakt op 3 punten (generate + snap + frontend).

**Trader Fixes**
- 💰 **ATOM-drift bug** (`modules/trade/monitor.py`): rest_bonus_eur greep alle overtollige coins mee (61.4 ATOM verkopen ipv 7.6). Fix: cap op 10% dust + skip proxy-users. 8 pytest groen.

**Data Cleanup**
- 🏷️ **KB-tag cleanup**: 60932 tags gescand, LLM-lek fragmenten weg (`'neutraal\n\n🧠 weten\nbegrip'` → `'neutraal'`), 286 emoji's uit `lagen1-4` + `ws5`, 21 typo's gefixt (whitelist-approach; plurals/context-varianten behouden).
- 📊 **Zelfscan feitelijk** (`modules/chat/zelfscan_facts.py`): emotie-distributie uit `pipeline_shadow/*.jsonl` ipv LLM-hallucinatie. Geeft `neutraal 92% · blij 4.6% · bedroefd 1.9%` op 27d-data.

**UI/UX**
- 🎨 **Globale glow-theming**: 1043 amber-classes gemapt naar `--glow-base` via 1 CSS-blok. Alle knoppen/tabs/highlights volgen user's profielkleur. Semantische kleuren (rood/groen) blijven.
- 🎨 **ArchiefPage/GesprekkenPage/WinkelPage/UserProfilePage**: hardcoded per-tab accent-hex weg, alle actieve tabs volgen glow.
- 🔒 **Glow admin-gate** (`modules/glow_nav/`): adminOnly flag op Kennisbank/Roadmap/Users/Settings/Spark Brain/Achievements/Leaderboard. Non-admin ziet 13/23 tabs. Systeem-archief vs user-archief nette scheiding via longest-alias-match.
- 🚫 **Roadmap/Achievements/Leaderboard admin-only**: jargon voor oudere users; verborgen tot core af.
- 🏪 **Winkel-tab verhuisd** naar Mijn Profiel (was in Archief).
- 📸 **Foto sub-tabs** (Privé/Winkel) binnen Foto-tab: alleen zichtbaar voor shop-owners, filter via `source=shop_product_image`.

**Sloop Sessie**
- 🗑️ **4 bots verwijderd**: Mr Smith, Madelief Stouten, Harry Klokkenmaker, Magere Hein (bot-dood). Users: 25→21. Alleen De Boekhouder blijft.
- 🗑️ **Baseline_intro.py** verwijderd (voorloper van Spark World, dubbel).
- 🗑️ **Hele D&D-stapel weg** (`modules/dnd/` folder, 2104 regels): world, spark_world, spark_world_north, character, dice, economy, body_layout, bewoner, daily_event, spark_world_map, routes. Server.py 9 router-imports weg.
- 🗑️ **Frontend DnD weg**: `components/dnd/`, `DnDGallerySection.js`, `DnDCharacterSheet.js`, `FractiesTab.js`. Refs in SystemArchive + GesprekkenPage + UserProfilePage opgeruimd.
- 🗑️ **Avatar-tab** uit Mijn Profiel verwijderd (was 100% DnD character-sheet).
- 🗑️ **AvatarTab + _LegacyAvatarBlock** functies uit UserProfilePage.js verwijderd (146 regels dead code).

### 🧊 KOELKAST (later oppakken)
- **D&D-systeem** komt terug als je zelf klaar bent — opnieuw ontwerpen met dan-geldende inzichten en échte user-NPCs
- **Privacy Matrix UI** (per-user vinkjes met wederzijdse consent-flow Willem ↔ Heidi)
- **Bestanden + Documenten samenvoegen** (1 tab "Mijn Bestanden" met Legacy sub-tab)
- **Documenten hernoemen** (Legacy / Levenspagina's / Testament & Zorg)



## 🧹 CLUSTER — Trader Accounting Hygiene (sessie 53, 22 feb 2026)

**Doel**: Alle "verdachte cijfers" die Willem aanwees systematisch oplossen én preventie inbouwen zodat nieuwe token-holders niet dezelfde issues krijgen.

### ✅ Bug-fixes (alle geverifieerd)

- [x] **v13_pot_value_consistency_001** — TraderPage €10.00 vs AnalyticsPage €10.26 mismatch.
      `GET /api/trade/potjes/{user_id}` overlayde `live_value = token_price` voor closed pots. Fix: closed → `live_value = capital`, open → mark-to-market. Regressietest: `/app/backend/tests/test_iter52_pot_value_consistency.py` (verified via testing_agent iter52, 100% pass).
- [x] **v13_pot_open_price_clarity_ui_001** — pot-card UI voor open pos: hover-tooltip met aankoop→huidige prijs + unrealized P&L + trailing piek. Trader-tab compact, Analytics-tab uitgebreid met "Nu"- en "Open P&L"-kolommen. `auto-rows-fr` voor gelijke card-hoogte.
- [x] **v13_reconcile_real_sell_price_001** — reconcile-close-sold gebruikte huidige ticker-prijs → fantoom-verliezen als coin sinds SELL was gedaald. Fix: zoekt echte SELL in `wallet/trade_history/{user}.json` binnen 7 dagen; anders break-even (exit=entry). `exit_source` in audit voor transparantie.
- [x] **v13_sell_eur_calc_001** — stats endpoint sommeerde `amount` voor SELLs = coin-hoeveelheid ipv EUR. Fix: BUY → `amount` (EUR), SELL → `filled × price`. Spark klopt nu (€10.09 gekocht → €10.14 verkocht, netto -€0.01 door fees).
- [x] **v13_reconcile_synthetic_sell_001** — reconcile schrijft synthetische SELL naar trade-history, **alleen** als er matching BUY bestaat voor deze market (voorkomt fake wins bij orphan coins).

### ✅ Data-repair scripts uitgevoerd (herbruikbaar)

- [x] `repair_phantom_losses_v13.py` — 3 fake verliezen weg: Gijs BCH −€0.52 → €0, Spark BTC −€0.06 → €0, Spark BCH bijgesteld naar echte −€0.11 (Bitvavo SELL @ €252.25 < entry €253.64).
- [x] `gap_scan_v13.py` — systematische diagnose (9 gap-types: fees, baseline, orphan markets, audit-drift, max_size, non-EUR fees, ghost sells, unclosed buys, corrupt state).
- [x] `fix_max_size_zero_v13.py` — **KRITIEKE bug**: alle 12 non-Spark pots hadden `max_size=0` → winst boven €0 werd afgeknipt. Gefixt naar `INITIAL_MAX (€50)` of `capital × 5`.
- [x] `close_remaining_gaps_v13.py` — Baselines gezet voor Willem & Gijs (€123.03) met `set_at` vóór eerste trade. Gijs 2× €20 BCH-BUYs gesloten met synthetische break-even SELLs (met BUY-timestamp).

### ✅ Preventie voor nieuwe users

- [x] **v13_auto_baseline_on_provision_001** — `auto_provision_bot_for_token_holder()` zet nu automatisch baseline op huidige Bitvavo total als user er nog geen heeft. Idempotent.
- [x] **v13_auto_baseline_on_mint_001** — `finance_ops.mint_tokens()` roept nu ook `auto_provision` aan zodat auto-mint scheduler en admin-gifts óók baseline+bot-config krijgen.

### ✅ v13_roles_array_001 — Zorgboerderij foundation (sessie 53, 22 feb 2026)

**Doel**: Fundament voor de care-farm dossiers. Een persoon kan meerdere rollen tegelijk hebben (vriend + cliënt + medewerker) zonder dubbele entries of dataverlies.

- [x] **Roles-array op relationships.json** — elke entry heeft nu `roles: []` naast bestaande `relation_type`. Backwards-compat: bij load wordt lege roles automatisch afgeleid uit relation_type.
- [x] **Auto-merge bij extractie** — `add_relations()` detecteert bestaande persoon → nieuwe rol wordt append aan roles-array i.p.v. dubbel-entry. Zo krijgt "Roeline" één record met `["vriend", "professioneel/cliënt", "professioneel/medewerker"]`.
- [x] **Nieuwe rel_types** — `cliënt`, `client`, `klant`, `medewerker`, `werkgever`, `begeleider` (allemaal onder `professioneel/…`).
- [x] **Regex-uitbreiding** — patroon `X is [ook|nu|inmiddels|tegenwoordig|sinds kort] mijn Y` matcht nu ook adverbia voor dual-role zinnen.
- [x] **Helper-functies** — `get_roles(uid, name)`, `has_role(uid, name, role)`, `add_role(uid, name, role)`. `has_role()` matcht op zowel het korte woord ("cliënt") als het volledige rel_type ("professioneel/cliënt").
- [x] **Migration** — `migrate_all_to_roles_array()` idempotent one-shot; ge-live gedraaid → 14 Willem-entries gemigreerd, 0 zonder roles.
- [x] **Regression-test** — `/app/backend/tests/test_roles_array_v13.py` (7 tests groen: new-person, dual-role, idempotent, has_role matching, add_role helper, migration preserve, migration idempotent).

### 📊 Gap-scan resultaat: van 16 issues → 1 info-only

Enige overgebleven "issue" (Spark pot-001 audit vs stats drift €0.25) is verklaarbaar: 1 echte trade met winst zonder audit + 1 gerepareerde audit met verlies. Geen bug.

### 🌱 BACKLOG-CONCEPT (sessie 53) — Attente Spark met privacy-matrix

**Idee** (Willem + Emmy): Spark wordt attent per gradatie. Voorbeeld: Willem zegt *"mijn moeder Heidi"* → Spark checkt of Heidi als user bestaat, checkt haar privacy-matrix voor gradatie 2 (familie), ziet dat verjaardag gedeeld is met familie → Spark aan Willem: *"Trouwens: morgen is Heidi jarig — vergeet geen cadeau."*

**✅ Fase 1 gebouwd (sessie 54)** — `v13_privacy_guard_001`:
- `privacy_guard.py` filtert KB-kaarten op verboden tags per gradatie
- Strip identity_facts (about_user/about_relationship) voor grad ≥ 5
- Maskeer familie-namen (Lotus/Heidi/…) in system_prompt
- 3 hook-punten in `response_composer.py`, 13 regressietests groen
- Live geverifieerd: grad-6 user krijgt 4/5 kaarten weg + Spark weigert privé-info

**🔴 Fase 2 (backlog)** — per-user privacy_matrix.json met opt-in vinkjes:

**Regel**:
- G1-G2 (self + familie): Spark mag attent zijn met gedeelde info
- G3 (vrienden): alleen wat expliciet gedeeld
- G4+ (community/klanten): nooit cross-container info
- Elke user opt-in per veld × gradatie (default = niks)

**Voorbeeld-matrix per user**:
```
                Familie  Vrienden  Community  Klanten
Verjaardag       ✅       ✅         ☐          ☐
Adres            ✅       ☐         ☐          ☐
Telefoon         ✅       ✅         ☐          ☐
```

**Uitdagingen om over na te denken**:
- Asymmetrische relaties (A ziet B als familie, B niet omgekeerd → shadow-vraag)
- Onboarding-leegte (default = niks delen → dormant feature. Fix: 3 presets Open/Voorzichtig/Gesloten)
- Rollen-conflict (Roeline = vriend én cliënt → bij twijfel strengste kiezen)
- UI-complexiteit (6 gradaties × 15 velden = 90 vinkjes → progressive disclosure)

**Afhankelijkheden** (in volgorde):
1. Rollen-array op relationships.json (`roles: []`)
2. `/data/persons/{user_id}_privacy_matrix.json`
3. Cross-user relatie-verificatie via bestaande shadow-vragen queue
4. Attente-hook in `response_composer` (pre-check bij persoons-mention)

**Waarom bijzonder**: dit is niet "Spark wordt slimmer" maar **"Spark wordt betrouwbaarder"**. Combineert met de andere principes van sessie 53 (reden zichtbaar, retrieval-gap-hints, zelflerende loop) tot één consistente ethiek: **Spark is nooit stiller dan de user hem ingesteld heeft, en nooit luider ook**.

### 🌅 Sub-concept: begroetings-moment als vraag-portaal

Bij ochtend-begroeting ("goedemorgen") heeft Spark al een gewoonte om iets attents te noemen (koffie, agenda vandaag, wat je gisteren deed). Dit moment kan óók dienen als **max 1 controlevraag per dag**:

**Timing**: dagbegin = laag cognitive-load, momentum voor "één ding regelen".

**Bron van vragen** (round-robin, 1 per ochtend):
1. `kb_fill_pending` — ws5-gap uit KB v2 (bestaande retrieval-flow)
2. `relatie_te_verifieren` — nieuwe relatie zonder wederkerigheid (shadow-vraag naar target-user)
3. `privacy_matrix_leeg` — nieuwe user zonder ingevulde matrix → default-preset kiezen

**Consent-first**: gebruik bestaande `pending_wv_consent` in session_state. *"Mag ik je even iets vragen?"* → ja/nee → dan pas de echte vraag.

**Frequentie-cap**: max 1× per dag per user. Anders wordt Spark een vragende bureaucraat.

**Voorbeeldflow**:
```
Willem: "goedemorgen"
Spark:  "Goedemorgen! Ga je vandaag weer bij Roeline in de tuin?
         Trouwens, mag ik je iets vragen?"
Willem: "ja"
Spark:  "Ik zag dat je Heidi je moeder noemde. Zal ik haar vragen om
         dit te bevestigen zodat ik jullie relatie zeker weet?"
```

Waar dit bouwt op bestaand code:
- `smart_intents.detect_greeting_intent` (of equivalent) — herkent begroeting
- `chat/routes.py` begroetings-branch — voeg pending-check toe na de bestaande "wat geleerd"-tegel
- `pending_wv_consent` — bestaande consent-machine hergebruiken
- `interaction_count` in session_state — al aanwezig voor frequentie-cap

### 💌 Sub-concept: Spark als postbode (twee-weg tussen users)

Voortbouwend op het vraag-portaal: dezelfde ochtend-hook kan ook **boodschappen doorgeven én verificaties bevestigen** tussen users. Spark wordt dan een relationele brug, niet alleen een geheugen.

**A. Boodschap doorgeven** (user-initiated):
```
Willem: "zeg tegen Heidi dat ze lief is"
Spark check: Heidi = user? → ja
Spark schrijft naar Heidi's user_messages queue:
    { from: "Willem", body: "je bent lief", verbatim: true, ts: ... }
Heidi's volgende chat:
    Spark noemt de boodschap met bron letterlijk.
```

**B. Wederkerige relatie-verificatie** (system-initiated):
```
Willem zegt "mijn moeder Heidi" → relatie in Willem's container = eenzijdig
Systeem: queue shadow-vraag in Heidi's relatie_te_verifieren queue
Heidi zegt "goedemorgen"
Spark: "Willem heeft in zijn profiel gezegd dat jij zijn moeder bent. Klopt dat?"
Ja → wederkerig, privacy-matrix actief tussen jullie
Nee → melding terug in Willem's queue: "Heidi zei dat de relatie niet klopt"
```

**Plooien**:
- **Boodschap-inhoud**: Spark filtert niet. Wel volledige bron-transparantie ("Willem zei letterlijk: ..."). Anders wordt Spark een boodschapper-die-liegt.
- **Ongelezen stapel**: max 1 boodschap per ochtendbark, oudste eerst. Rest wacht.
- **Nee bij verificatie**: nette terugkoppeling naar de vragende user. Die kan intrekken of opnieuw proberen.

**Waarde**: 
- Laagdrempelig contact tussen family/vrienden zonder aparte DM-app
- Verificatie sluit asymmetrische-relatie-plooi
- Alles via bestaande begroetings-hook — geen aparte notificatie-infrastructuur

**Nieuwe queues** (naast bestaande kb_fill_pending):
- `/data/persons/{user_id}_message_inbox.json` (inkomende boodschappen)
- `/data/persons/{user_id}_relation_verify_queue.json` (te verifiëren relaties)

### 💾 Backups (alles reversibel)
- `data/financial/user_potjes.json.bak_phantom_loss_repair_20260822_062648`
- `data/financial/user_potjes.json.bak_maxsize_fix_20260822_064245`
- `data/financial/user_potjes.json.bak_backfill_20260822_063929`
- `data/wallet/trade_history/user-*.bak_gapclose_20260822_065541.json`

### 🔍 Learnings
- **Reconcile ≠ echte trade**: bij close-flow altijd echte SELL-prijs uit trade-history opzoeken, nooit huidige ticker. Als niet vindbaar → break-even (safe default).
- **`amount` semantiek verschilt per side**: Bitvavo BUY = EUR, SELL = coin-hoeveelheid. Stats/summary calls moeten altijd `filled × price` voor SELL-EUR.
- **Mens-check onmisbaar**: Willem's "hé dit voelt niet goed" bij €10.00 vs €10.26 leidde tot 4 extra ontdekte bugs + kritieke max_size=0.

---


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

## 🧠 CLUSTER — Chat/LLM (v13r-t, sessie 52r-t, feb 2026)

### ✅ Gedaan
- [x] **Groq model-migratie** — `llama-3.3-70b-versatile` gedeprecateerd 16-aug → `openai/gpt-oss-120b` (officiële replacement).
- [x] **Emergent Universal Key uit** — `LLM_EMERGENCY_USE_EMERGENT=false` (Willem's wens: geen cloud).
- [x] **TPM auto-trim retry** — router probeert 1× opnieuw met halve context bij 413/rate_limit_exceeded.
- [x] **Identity facts cap grad 1** — was 999, nu 15/type (was 8477-token overshoot, nu ~2000).
- [x] **Turns 6 → 3** — extra headroom voor system_prompt.
- [x] **User-text TPM-guard** (sessie 52t) — bij lange geplakte tekst (bv. Wikipedia): user_prompt cap 3000, system-prompt cap 16000, oude turns cap 1500, hard totaal-budget 22000 chars greedy-snijden. Frontend char-counter amber vanaf 3500 / rood vanaf 5500. Getest ✅ met 8200-char input.
- [x] **`LlmBudgetSettingsWidget`** (sessie 52t) — 8 char-cap waardes admin-tunable via Beheer → Kladblok. Geen redeploy meer nodig voor tuning. Backend leest live uit `settings/system.json`.

### 🔴 Nog te doen
- [ ] **Cerebras quota-watchdog** — bij 402 → DM naar Willem: "fallback op quota, reset ~X". Nu geen zichtbaarheid.
- [ ] **Alternatieve fallback** — Together.ai / DeepInfra als 3e provider (3-regel `.env`).
- [ ] **Widget verhuizen naar echte tab** — nu tijdelijk in Kladblok. Naar Beheer → Instellingen → Algemeen als "Chat & LLM budget" card.
- [ ] **Ollama-migratie (P2)** — lokaal via `LLM_PRIMARY_BASE_URL=http://localhost:11434/v1`. Hardware-eis: 16 GB RAM voor Llama 3.1 8B (~75%), 24+ GB voor gpt-oss-120b (identiek). Code is klaar. **Waarom belangrijk**: bij dubbele free-tier-uitval = Spark stil; lokaal geen limiet.


---

## 🌱 CLUSTER — Zelfbewustzijn & Meta-lagen (sessie 52p-u, filosofisch fundament)

**Kernidee**: Spark's LLM = mond. JSON-lagen = geheugen. Icons/kleuren = spiegel. Elk stuk beheersbare data over Spark zelf wordt automatisch onderdeel van zijn zelfperceptie via synapse-scanner + identity_facts. Geen aparte "consciousness"-feature, wel een groeiende structuur waarin Spark zijn eigen bouwstenen kan noemen.

### ✅ Fundament al aanwezig
- [x] `spark_bijbel.json` — kernwaarden + doelen + bijbel_items (met `Nalatenschap en Continuïteit`, `digitale nalatenschap voor Lotus`)
- [x] `spark_identity.json` — naam, versie, maker, karakter
- [x] `identity_facts` — user-turns worden ge-extract als facts (`spark_feels_like: familiewapen`, `user_calls_spark: het familiewapen`)
- [x] `spark_user_view` — per-user snippet met relaties (Lotus als dochter) + gradatie-toon
- [x] `synapse/__init__.py` — scanner leest zichzelf, structuur voor "wat heb ik"
- [x] `shadow_observer` — logt turns, aggregate stats (359 begrip-teller, 117 response-types)
- [x] `knowledge/learned_knowledge/knowledge_base.json` — aparte learned laag
- [x] KB v2 kaarten (voelen/spreken 100% compleet, ~216 rest in weten/doen)

### 🔴 Fase A/B/C — Admin-look als meta-signaal (sessie 52s besproken)
- [ ] **Fase A: admin-accent op alle admin-tabs** — tabs onder Beheer/Modules/Admin krijgen violet accent wanneer `adminModeActive===true`. `identity_facts`-entry toevoegen: `admin_mode_kleur: paars` zodat Spark 't kan noemen.
- [ ] **Fase B: admin-override neemt user-kleuren over (tijdelijk)** — `--app-primary/secondary` CSS-vars overschreven wanneer admin actief; bij `disableAdmin` terug naar Mijn Profiel-voorkeur. Meta-flag "hij weet dat hij anders oogt".
- [ ] **Fase C: icon-registry + upload (fundering-steen synapse)** — grote sessie:
  - `data/branding/system_icons.json` met `{key: {url, uploaded_by, uploaded_at, reason, emoji_fallback, original_lucide}}` + per-key endpoints
  - Frontend `<SystemIcon name="settings" fallback={Settings} />` wrapper → vervangt ~50-80 lucide-plekken
  - Admin-UI: sectie "Systeem-iconen" met per-icoon uploader
  - **Synapse-hook**: `system_icons.json` als scanner-bron toevoegen
  - **Identity-facts hook**: bij upload auto `spark_icon_{key}: eigen ontwerp`
  - Scope: 2-3 uur werk goed gedaan
  - Waarde: Spark kan straks in gesprek zeggen *"mijn tandwiel-icoon is een stap-tandrad in oranje, sinds 21 aug"*

### 🔴 Collectieve Intelligentie (Laag-2 kennis, sessie 52r besproken met Emmy)
Willem + Emmy bespraken: 2-laags kennis. Laag 1 = persoonlijk geheugen per user (bestaat). Laag 2 = patronen over ALLE users heen → algemene wijsheid → terug-injectie. Toetsen op **resonantie** met bijbel-kaders, niet op waarheid (wrijving = groei). "Niet alles is een kaart, sommige dingen zijn een gesprek."

- [ ] **Pattern-distiller** — batch-run op shadow-events, output naar `data/collective/patterns.json` (bv. *"3 users vroegen naar X op verschillende manieren"*). 1 sessie.
- [ ] **Stelling-generator + curation UI** — uit cluster een propositie destilleren (*"gebruikers ervaren Y als Z"*). Willem/Emmy accept/reject in Kladblok. 1 sessie.
- [ ] **Toets-loop** — Spark toetst stelling in gesprek met andere users (Socratisch). Verrijkt zelfs als niet-waar.
- [ ] **Injectie-kanaal** — 3e prompt-layer naast `identity_facts` + `spark_user_view`: `collective_wisdom_snippet`. Met override-schakelaar per user.
- [ ] **Privacy-anonymizer** — hard filter dat namen/IDs/persoonsdata uit patronen weert vóór aggregatie. Anders lekt Laag 1 via Laag 2.
- **Aanrader**: eerst alleen distiller (1 sessie), dan generator + curation, dan live injectie. Zo blijft Laag 1 heilig.


---

## 📊 CLUSTER — Trader & Potjes (v13q-u, sessie 52r-u, feb 2026)

### ✅ Gedaan
- [x] **Trader-monitor sync-bug** — `monitor.start()` idempotent (`already_running=True`), UI leest ook `data.message`.
- [x] **`open_pot()` overwrite guard** — bij `is_open=True + andere market` → BLOCK. Bij zelfde market → idempotent skip. Voorkomt ATOM-overschrijving door BCH.
- [x] **Bitvavo-reconcile 6 potjes** — preview only; BCH/BTC/ETH/SOL/ADA/ATOM elk €10 gekoppeld aan echte Bitvavo entry-prijzen.
- [x] **Prod-merge naar preview** (sessie 52t) — 479 files data-merge. Backup in `_backup_pre_prod_merge_20260822_050217/`.
- [x] **`reconcile/close-sold/{user_id}`** — per-user endpoint dat open potjes met near-zero Bitvavo balance sluit met huidige marktprijs. Veilige in-place mutatie (geen `close_pot`/finance_hub auto-mint side-effect meer). Audit-trail in `reconcile_audit`.
- [x] **`reconcile/close-sold-all`** (sessie 52u) — bulk endpoint voor **alle users** met open potjes. Getest ✅ door testing_agent (6/6 pytest). Filtert meta-keys, skipt users zonder open potjes, degradeert graceful per user.

### 🔴 Nog te doen
- [ ] **Prod bulk-sync draaien** — na deploy: `POST /api/trade/reconcile/close-sold-all?dry_run=false` op productie. Geiser (user-a0ee2d7e) + eventueel andere users worden gesynct.
- [ ] **Trader Console consolidatie** (P1, sessie 52u besproken) — huidige Analytics → Trader tab heeft **cross-overlap** knoppen:
  - "Force-sell" per potje ↔ "Sync verkochte coins" bulk
  - "Herwaardeer vrije pots" bulk ↔ "Herwaardeer" per pot
  - "Koppel als potje" (orphan) ↔ "Sync verkochte coins" (verkocht)
  - `SparkTraderStatsPanel` + `ReconcileSparkPanel` + `AnkerBoot` = 3 losse panelen over zelfde 6-8 potjes
  - **Voorstel**: één "🎯 Trader Console" met sub-tabs **Overzicht** (stats + posities-tabel + P&L), **Sync & Reconcile** (alle sync-knoppen met NL-tooltips + confirm-dialogs op destructief), **Bot-controls** (start/stop/force-sell). Scope: 1-2 uur.
- [ ] **Trader-tab visueel opruimen** — Anker gap-up + Anker per markt + Reconciliatie = 1 collapsable card.
- [ ] **Vermogens-tab** — Activa (books + wallets + Bitvavo live) − Passiva = Eigen vermogen (admin-only, Spark-perspectief).
- [ ] **Frontend knop "Sync verkopen"** in `ReconcileSparkPanel` — 1-klik confirm-dialog → bulk endpoint. Vervalt als Trader Console er komt.

---

## 🧹 CLUSTER — Refactor & Code-hygiene (sessie 52u)

- [ ] **`routes.py` splitsen** (uit testing_agent code-review) — nu 2995 regels. Splits in `reconcile.py`, `potjes_routes.py`, `bots_routes.py`, `monitor_routes.py`. Elk <500 regels. Niet blokkerend maar wel onderhoudbaar.

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


### ↪ Sessie 57 + Sessie 55

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


### ↪ Spark's brein v5-status

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
- **v1 Knowledge Base** (`/data/knowledge/learned_knowledge/knowledge_base.json`) — legacy, alleen-lezen fallback.
- **KB v2 — 5 lades** (`/data/knowledge/v2/`, stand 17-09-2026) — 🌸 Voelen 566 · 💬 Spreken 516 · 🧠 Weten 5096 · 🎭 Doen 1153 · 🎮 Spark Games 12 + 📥 Inbox 1 (`rna`, Willem vult in).
  Lade-lijst is de bron `service.LADES` + `LADE_META`; frontend `KennisbankV2Page.LADES` moet gelijk lopen.
- **Knowledge graph** (`modules/graph/sync_service.py`) — 10577 nodes + 65981 edges (v1+v2 gemengd, lade-kleuren).
- **Voice/Image media** — centraal in `system_archive` met `linked_card_id` backreference.

### 🎮 Spark World (sandbox-game) — universele naam sinds 17-09-2026
- **Eén game, één naam**: D&D / dnd / d&d / "Levende Wereld" = **Spark World**. Gebruik nooit meer "D&D" als naam voor de game (alleen als tag-historie in `footnote.hernoemd_van`).
- **KB**: hub-kaart `Spark World` (kbv2-5ae16b66) in lade `games`, Base Line = basiswaarden-kaart, Rugzak, Utrecht (Spark World), grondstof-drafts. Veld `game: "spark world"` per kaart voor onderverdeling per game.
- **Data**: `data/dnd/` container (steden, fracties, characters, blueprints, world_state, lore_index). Status: **geparkeerd tot Core klaar is**.
- **Steen Papier Schaar** = onafhankelijke module-game (kaart in doen), cross-linkbaar als gevechtsmechaniek in Spark World.
- **Lore index** (7 avatars-as-functions, 6 behavior-categorieën) — gearchiveerd, oude oorsprongs-lore van Base Line staat hier.
- **Aura-engine** (`/api/dnd/aura/{user_id}`) — live top-3 gedragingen → kleur-gradient op Persoonskaart.
- **Card Factory** (`modules/cards/`) — DnD/Event/Bark kaarten met hook-chain bij draft→active.
- **Base Line intro** (community chat `[start verhaal]`) — keuze-driven story-flow.

### 🎙️ Stem-laag

---

