# Spark Core — Architecture Notes

Levend document met **dual-source patterns** en architecturale beslissingen die anders verzanden. Elk item heeft een datum, een trigger ("hoe ontdekt"), en de keuze.

Convenant: bij elke vondst van een dual-source moment → entry hier + cross-reference comment in beide bestanden.

---

## DSP-001 · Bot-data: `bot_users.json` ↔ `system/users.json`

- **Datum**: 2026-05-23
- **Trigger**: De Boekhouder + De Dood waren toegevoegd aan `users.json` maar verschenen niet in de "Online bots" widget. `/api/bots/list` leest namelijk uit een **andere** file.
- **Twee bronnen**:
  - `/app/backend/data/system/users.json` — **alle** menselijke users + bots in één unified list (auth, gradatie, avatar, persoonlijkheid). Gebruikt door auth-flow, admin overzicht, bot-instellingen tab.
  - `/app/backend/data/bots/bot_users.json` — alleen bots, mét hun **interactie-logica**: triggers (keyword/user_join/user_leave) + responses. Gebruikt door `/api/bots/list`, community-keyword-detection.
- **Beslissing**: Beide behouden — ze serveren verschillende doelen. `bot_users.json` is essentieel voor de keyword-trigger engine; `users.json` is essentieel voor de unified identity-laag.
- **Verplichting**: Bij **elke nieuwe bot** beide files updaten. Bij bot-rename → beide. Liever niet hercoderen tot één bron, want triggers-veld is bot-specifiek en zou users.json onnodig verzwaren.
- **Cross-refs toegevoegd**:
  - Comment in `bot_users.json` (top-regel `_arch_ref`)
  - Comment in `users.json` (top-regel `_arch_ref`)
  - Beide verwijzen terug naar dit document, DSP-001.

---

## DSP-002 · Verteller-bot user_id NIET gelijkstellen aan user

- **Datum**: 2026-05-23
- **Trigger**: Bij `[start verhaal]` had ik de 4 verteller-berichten user_id `user-001` gegeven (Willem's id) → alle verhaal-bubbles kregen Willem's avatar. De community avatar-lookup pakt namelijk via `user_id`.
- **Beslissing**: Verteller-rol heeft altijd zijn eigen bot-id (in dit geval `bot-dood`). NOOIT user-001 of een andere echte user-id "lenen" voor bot-output. Ook al voelt het narratief logisch.
- **Verplichting**: Bij elke nieuwe bot-output (storyteller, sage, GM, NPC) → check dat `user_id` matched met een bot in `bot_users.json` met eigen avatar.
- **Patroon-naam**: "Avatar-userid coupling".

---

## DSP-003 · Naam-display swap user-000 ↔ user-001

- **Datum**: 2026-05-23
- **Trigger**: User's mental model: "De Willem = wallet 00, Spark = wallet 01". Maar de data heeft het andersom: user-000 = Spark, user-001 = De Willem (waar Bitvavo creds & 11MB chat-history op staan).
- **Beslissing**: ALLEEN display-laag swap, NIET data-swap. Force-override `user_naam` in `/api/trade/admin/bots` zodat admin overzicht klopt met mental model. Data ongemoeid.
- **Verplichting**: Bij elke admin-overview (analytics, dashboard, persoonkaart) waar user-000/001 voorkomt — display-override toepassen. NOOIT in users.json zelf de namen omdraaien (zou alle history breken).
- **Verwijst naar**: code in `/app/backend/modules/trade/routes.py` zoek `v5_display_swap_001`.

---

## DSP-004 · ROAR balances: `roar_balances.json` ↔ `user_wallets.json`

- **Datum**: 2026-05-23
- **Trigger**: Admin token-batch (Willem +5 ROAR @ €10.10 + 1 gift Gijs) toonde wallet-UI `spark_tokens: 0` terwijl `roar_balances.json` correct stond. Mirror was niet gesynct.
- **Twee bronnen**:
  - `/app/backend/data/roar/roar_balances.json` → `balances.{user_id}: int` — **autoritatief**, audit-trail (transactions, admin_log)
  - `/app/backend/data/wallet/user_wallets.json` → `user_wallets.{uid}.wallet.spark_tokens` — display-mirror voor wallet UI
- **Beslissing**: roar_balances = bron van waarheid. user_wallets.spark_tokens is een **mirror** die bij elke balance-mutatie automatisch moet syncen.
- **Verplichting**: Elke `roar.balances[uid]` mutatie → óók `user_wallets[uid].wallet.spark_tokens = roar.balances[uid]` + `last_sync`. `shop/gift.py` accept doet dit auto. Admin-scripts: zelf nadenken.
- **Toekomst (P2)**: Centrale `roar_service.set_balance(uid, n)` die beide files atomair update.
- **Cross-refs**: `/app/backend/modules/shop/gift.py` (sync-block na accept), `/app/backend/modules/shop/routes.py` (token-buy)

---

## DSP-005 · Bot-settings: React-state ↔ `bot_registry_state.json`

- **Datum**: 2026-05-23
- **Trigger**: Willem: "2 json met info die elkaar nodig zijn maar niet van elkaar bestaan weten" — cycle-keuze in TraderPage (15m/1h/4h/1d) klonk niet door naar draaiende bot.
- **Twee bronnen**:
  - `TraderPage.js` React-state: `candleInterval`, `monitorMarkets`, `usePotjes` (lokale UI)
  - `/app/backend/data/bots/bot_registry_state.json` + `bot_state_{user_id}.json`: server-side autoritatieve waarde
- **Beslissing**: Elk veld dat tijdens running aanpasbaar moet zijn → hot-patch endpoint + auto-sync UI poll → setter. Eenrichtings-sync (backend → UI) is niet genoeg.
- **Implementatie**:
  - Markets: `POST /api/trade/monitor/markets/{user_id}` (langer bestaand)
  - Candle/cycle: `POST /api/trade/monitor/candle/{user_id}` (v5_candle_hotswap_001)
  - Auto-sync hooks in TraderPage.js useEffect op `monitorStatus.markets` / `.candle_interval`
- **Verplichting**: Bij elk nieuw monitor-setting veld → óf read-only (alleen via restart) óf hot-patch endpoint + sync-effect. Beslis bewust per veld.
- **Toekomst (P2)**: trade_amount, interval (poll-frequentie), auto_trade, use_mock — gelijktrekken naar hot-swap pattern.
- **Patroon-naam**: "UI state ↔ JSON snapshot sync"
- **Cross-refs**: `/app/backend/modules/trade/monitor.py` (`update_markets`, `update_candle_interval`), `/app/frontend/src/components/modules/TraderPage.js` (`changeCandleInterval`, `toggleMonitorMarket`)

---

## DSP-006 · Gift paper-trail: `gift_requests.json` ↔ `roar_balances.transactions`

- **Datum**: 2026-05-23
- **Trigger**: Gift-feature toevoegen (Wallet UI). Gift heeft 2 sporen:
  - **Lifecycle**: pending → accepted/rejected/cancelled/expired → `gift_requests.json` (state machine + 24h expiry)
  - **Transfer**: bij accept de eigenlijke token-mutatie → `roar_balances.transactions[]` (audit)
- **Beslissing**: Beide bewaren. `gift_requests.json` is UI/state, `roar_balances.transactions` is financial audit. Pending gifts staan niet in transactions (geen token-mutatie yet).
- **Verplichting**: Bij accept hook → push naar transactions[] + admin_log[] + DSP-004 sync. Bij reject/expired/cancel → geen financial tx (alleen lifecycle).
- **Privacy-implicatie**: `gift_requests.json` bevat sender/recipient pairs zichtbaar voor alle servers/backups → encryption-at-rest later overwegen (P2).
---

## INDEX · Waar zit wat (voor agent-handoff, overleeft deploy + zip-cycle)

| Bestand / Locatie | Inhoud | Voor wie |
|---|---|---|
| `/app/backend/data/bugs/bugs.json` | Bug-meldingen + ideeën door users via Notities → Bugs tab. Open + opgelost mengen. | Echte bugs + brain-dump van user |
| `/app/backend/data/notes/notes.json` | User-notities (Willem's eigen titels/inhoud zoals "5w", "Bugmelder uitleg") | **USER**-content — NIET agent-context |
| `/app/backend/data/system/roadmap.json` | Versies (v3.0, v4.0, v5.0, v6.0, known_issues, technical_debt, architectural_decisions, notes) | Boom-structuur, niet UI-flat-list |
| `/app/frontend/src/components/workspace/RoadmapPage.js` | **Hardcoded phase-array** met done/active/planned items. Dit is wat user ziet | User-visible roadmap |
| `/app/memory/AGENT_BACKLOG.md` | **NIEUW**: alleen agent-context — brain-dump-items die nog niet user-visible zijn | Agent (mij) |
| `/app/memory/ARCHITECTURE.md` | DSP-patronen, dual-source afspraken, dit overzicht | Agent (verplicht lezen) |
| `/app/memory/PRD.md` | Original problem statement + recent done | Agent + handoff |
| `/app/memory/test_credentials.md` | Login-info | Agent + test runs |
| `/app/backend/data/personality/spark_vocab.json` | Spark's eigen woordenlijst — per emotie 4 intents (begroet/bedank/afscheid/reactie), + algemeen (twijfel/enthousiasme/zelfspot/openers/afsluiters/uit_kennisbank) | Spark's stem-variatie |

### Cross-doc regels (om mijn fouten te voorkomen)
1. **Vóór coden**: lees `ARCHITECTURE.md` + `PRD.md` + huidige roadmap-fases in `RoadmapPage.js`
2. **Geen aannames**: bij bug-melding eerst vragen welke environment (preview vs https://roadkillcommunity.nl)
3. **Mijn fouten** horen NIET op user-zichtbare roadmap of bugs.json — alleen in AGENT_BACKLOG
4. **Roadmap = boom, niet lijst**: stam (architectuur) / wortels (audit-vragen) / takken (concrete items). RoadmapPage.js moet die hiërarchie respecteren
5. Bij elke balance/state mutatie: check DSP-004/005/006 voor sync-verplichtingen

---

## Convenant-oorsprong (waarom dit bestaat)


- **Datum**: 2026-05-23
- **Trigger**: Willem merkte op dat ik bij dual-source ontdekkingen geen voetnoot maakte. Quote: "in situaties als deze moet je het in footnote en meta zetten als je er nog niet mee werkt na elkaar verwijzen als je er achterkomt. ook deze opmerking hahaha".
- **Beslissing**: Dit document is hét single point of truth voor dual-source patterns. Bij elke nieuwe ontdekking → DSP-entry + cross-ref in betrokken files.
- **Verplichting agent**: vóór een dual-source workaround eerst dit document checken; bij nieuwe vondst altijd entry maken.

---

## Meta · Hoe deze notebook werkt

- Nieuwe entry = **DSP-NNN** (Dual-Source Pattern) of **AD-NNN** (Architecture Decision).
- Iedere entry heeft minimaal: datum, trigger, files involved, beslissing, verplichting.
- Cross-references: in elk betrokken bestand een `_arch_ref` veld met de DSP-id en pad naar dit document.
- Dit document hoort bij elke onboarding/handoff te worden gelezen.
- **Ook zichtbaar in Roadmap UI**: phase "📐 Werkwijze & Conventies" toont de belangrijkste afspraken voor user-zicht.
