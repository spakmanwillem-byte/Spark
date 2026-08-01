# Blueprint — Boekhouder (Finance Hub v10)

> **Refactor 2026-07-20** — Dispatcher-patroon met 8 sub-agents (`v10_finance_hub_001`)
> Pad: `backend/modules/boekhouder`

## 🎯 Doel
Enige bron van waarheid voor de complete finance-economie:
- **ROAR tokens** (balance, mint, gift, supply)
- **Trader potjes** (waarde = live token-prijs, hybride)
- **EUR wallet** (saldo, deposits, Tikkie)
- **Bitvavo saldo** (live)
- **Token-prijs** (dynamisch)
- **Drift & ruis** (reconciliatie)
- **SEPA** (placeholder voor bankkoppeling)
- **Persona** (Boekhouder chat + weekverslagen)

## 🧬 De hybride token-potje regel (hybride regel)
- `1 token = 1 pot` — hard boekhouding
- `pot.capital = current_token_price` — leeft mee met prijs
- Deposits → verhogen Bitvavo → verhogen dynamische prijs → alle potjes stijgen mee
- Trader-winst → overflow_pool → auto-mint bij drempel → nieuwe pot naar user's wallet
- **Ruis** = `bitvavo_total - sum(alle_potjes_capital)` — extra vlees, blijft op Bitvavo

## 🏗️ Architectuur

```
modules/boekhouder/
├── _meta.json                        (bijgewerkt met sub_agents)
├── routes.py                         (dun laagje API)
├── service.py                        (bestaande close_cycle logica behouden)
├── finance_hub.py                    🆕 dispatcher / hub singleton
├── agents/                           🆕 8 sub-agents
│   ├── base_agent.py
│   ├── token_agent.py                → 'roar_token' topic
│   ├── price_agent.py                → 'token_prijs' topic  
│   ├── wallet_agent.py               → 'eur_wallet' topic
│   ├── potjes_agent.py               → 'trader_potjes' topic
│   ├── bitvavo_agent.py              → 'bitvavo_saldo' topic
│   ├── recon_agent.py                → 'reconciliation' topic
│   ├── sepa_agent.py                 → 'sepa_bank' topic (placeholder)
│   └── persona_agent.py              → 'boekhouder_persona' topic
└── blueprints/
    └── finance_hub.json              🆕 alle formules + hooks + chat_intents
```

## 🔌 Endpoints (v10)

| Endpoint | Doel | Wie belt |
|---|---|---|
| `GET /boekhouder/snapshot/{user_id}` | ÉÉN CALL → alles | Wallet-UI, chat-intents |
| `GET /boekhouder/token/price` | Live prijs uit formule | Shop, TokenGifts |
| `GET /boekhouder/potjes/{user_id}` | Potjes met dynamische capital | Trader UI |
| `GET /boekhouder/reconcile` | Drift + ruis systeem-breed | Admin |
| `GET /boekhouder/blueprint` | Volledige blueprint uitlezen | Admin UI |
| `GET /boekhouder/chat-snapshot/{user_id}` | Snapshot als NL chat-tekst | Spark chat |

Legacy behouden:
- `POST /boekhouder/close-cycle/{user_id}` (rollup)
- `GET /boekhouder/closings` (lijst)

## 🪝 Hooks (in blueprint)
- `on_deposit` → recon + price + potjes revalue
- `on_trade_close` → price + recon + auto_mint_check
- `on_mint` → price + add_pot + log_event
- `on_gift` → transfer + log_event

## 💬 Chat intents (in blueprint)
Voor Spark's fast-path detection:
- `wallet_query`, `token_query`, `price_query`, `potjes_query`, `reconcile_query`, `boekhouden_query`

## 📊 Reality vs Roadmap

| Punt | Reality | Plan |
|---|---|---|
| Token drift | ⚠️ wallet toont 15, roar leeg | Fase 2: sync-all |
| Token-prijs | ⚠️ €7,60 stale in roar_balances | ✅ PriceAgent fresh |
| Pot-capital | ⚠️ vast €10 in files | ✅ Dynamic via hybride regel |
| Auto-mint | ⚠️ code bestaat maar losgekoppeld | Fase 2: hook aansluiten |
| SEPA | ❌ nog niks | 🚧 Placeholder klaar |
| Boekhouder chat | ⚠️ persona bestaat, data losstaand | ✅ persona_agent + format_snapshot_for_chat |

## 🔐 Encryption-plan
- Status: `⚪ slot leeg` (financieel = privacy-gevoelig)
- Volgende stap: F2F encryption voor `wallets.json` transacties + `roar_balances.transactions`

## 🚧 Fase-plan
- **Fase 1 (DONE)** — Readonly snapshot + reconcile + persona + blueprint doc
- **Fase 2** — Sync-all endpoint (fix drift), auto-mint hook op staking_growth, admin UI in Instellingen
- **Fase 3** — Migreer wallet-UI, shop, chat-intents naar `/boekhouder/snapshot`
- **Fase 4** — SEPA-agent activeren + Boekhouden-tab UI

## 📖 Voor toekomstige agents
- **Nieuwe finance-topic toevoegen?** → Nieuwe sub-agent in `agents/`, sectie in blueprint, endpoint in routes
- **Formule wijzigen?** → Blueprint JSON (niet code)
- **Chat-intent uitbreiden?** → `chat_intents` sectie in blueprint
