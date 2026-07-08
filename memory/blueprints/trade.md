# Blueprint — trade

> Single source of truth voor de Spark Trader-module.
> Locatie: `backend/modules/trade/`
> Laatst bijgewerkt: 2026-07-08 (sessie 46)
> Gekoppelde KB-kaart: `kbv2-2f55a485` ("Spark Trader" in lade `weten`)

---

## 🎯 Doel

Autonome, transparante crypto-handelsmodule die via Bitvavo koopt en verkoopt op meerdere EUR-markten. Ontworpen als **community-trader**: één Bitvavo-account, meerdere users met eigen potjes, geen verborgen fees, elke beslissing traceerbaar.

## ✅ Wat werkt al

- **Multi-market**: BCH-EUR, BTC-EUR, ETH-EUR, SOL-EUR, ADA-EUR, ATOM-EUR (6 markten, per user configureerbaar via `POST /api/trade/monitor/markets/{user_id}`)
- **Multi-user proxy**: Spark (`user-000`), Willem (`user-001`), Geiser (`user-a0ee2d7e`) — auto-provisioning voor users gradatie ≥ 5 via `POST /api/trade/admin/start-all-bots`
- **Potjes-systeem**: elk potje is een klein kapitaaltje (dynamisch geprijsd, momenteel €6.47/pot) met eigen open/closed status. 22 potjes totaal in het systeem, 1:1 gekoppeld aan ROAR-tokens.
- **Cluster-BUY**: bot opent 1..N potjes tegelijk in één Bitvavo-order als de decision-service dat aanbeveelt.
- **Atomaire force-sell**: `POST /trade/potjes/{user_id}/{pot_id}/force-sell` — als Bitvavo de SELL afwijst, wordt het potje teruggerold (`force_sell_audit.json` bewaart geschiedenis).
- **Learning-scheduler**: nachtelijk (`context_service.py`) → win-rate per markt uit trade-history, week/maand-patronen, BUY-drempel bias per markt.
- **Function tracing**: `trace_call` decorator → `data/trade/logs/trace_YYYY-MM-DD.jsonl`. Elke `execute_real_trade`, `open_cluster`, `close_pot` call is gelogd met args + duration + result.

## 💶 Fees & drempels

| Item | Waarde | Locatie |
|---|---|---|
| Fee Spark's eigen bot | 0.00% | `SPARK_FEE_RATE` in code |
| Bitvavo maker/taker fee | 0.25% | Bitvavo standaard |
| Minimum order size EUR | €5.00 | Bitvavo per-markt |
| Trade amount per potje | €6.47 (dynamic) | `get_dynamic_price()` in `routes.py` |
| BUY cooldown per markt | 900s (15 min) | `BUY_COOLDOWN_SEC` in `monitor.py` |
| EUR-cooldown na INSUFFICIENT | 1800s (30 min, globaal) | `EUR_COOLDOWN_SEC` in `monitor.py` (v7) |
| Cycle interval | 900s (15 min) | `interval` in monitor_state |
| Candle timeframe | 15m | `candle_interval` in monitor_state |

## 🧠 Beslissings-flow

```
_run_cycle (elke 15 min)
   ↓
Voor elke markt:
   ↓
1. Haal candles (Bitvavo `/candles`)
2. Bereken indicators (Bollinger Band, prijs vs SMA)
3. _simple_decision → BUY/HOLD/SELL
4. context_service.apply_context_to_decision → boost/dempen op basis van learned bias
5. Check cooldowns (BUY-cooldown, EUR-cooldown)
6. Als BUY én cluster mogelijk → execute_real_trade
7. Als SELL én positie open → execute_real_trade
   ↓
Log → trace_YYYY-MM-DD.jsonl + monitor_decisions.json
```

## 📂 Bestandsstructuur

| File | Rgl | Doel |
|---|---|---|
| `monitor.py` | 1660 | Trader loop + execute_real_trade + cooldowns |
| `routes.py` | 1533 | Alle 65 API endpoints |
| `potjes.py` | 1511 | Potjes CRUD + thread-safe locks + cluster-open/close |
| `reconcile.py` | 801 | Bitvavo ↔ potjes reconciliatie |
| `context_service.py` | 499 | Learning scheduler + market bias |
| `bitvavo_client.py` | ~200 | Bitvavo HMAC signing + rate-limit wrapper |
| `spark_trader_service.py` | ~150 | Spark-user-specifieke helpers |

## 📡 Key API endpoints

- `GET /api/trade/bot/status/{user_id}` — live bot-status per user (markets, position, cycles)
- `GET /api/trade/potjes/{user_id}` — alle potjes van deze user
- `GET /api/trade/delta` — global sync check: pot_capital vs Bitvavo market_value
- `POST /api/trade/baseline/{user_id}` — reset PnL-baseline (start opnieuw tellen)
- `POST /api/trade/potjes/{user_id}/{pot_id}/force-sell` — atomaire sell
- `POST /api/trade/admin/start-all-bots` / `stop-all-bots` — multi-user bot management
- `POST /api/trade/monitor/start` / `stop` / `pause` — per-user bot control

## ⚠️ Bekende beperkingen / risico's

- **Liquide EUR ≠ pot-capital**: 90% van pot-kapitaal zit meestal als coin op Bitvavo. Bij BUY-signalen kan liquide EUR ontoereikend zijn (30-min cooldown vangt dit op sinds v7).
- **Enkele Bitvavo-account voor alle users**: als API-key ban → alle users stil.
- **No stop-loss cascade**: trader heeft geen expliciete stop-loss; bescherming via cooldown + BUY-drempel + trailing (afhankelijk van positie).
- **File-lengte**: `monitor.py` 1660 rgl — splitting-trigger (>1000) overschreden, refactor kandidaat voor v8.

## 🔗 Relaties

- **Hangt af van**: `bitvavo_client`, `core/storage` (JSON persist), `core/tracing`, `wallet` (token-koppeling), `accounting` (kasboek), `context_service`
- **Wordt gebruikt door**: Frontend `TraderPage.js`, `AnalyticsPage.js`, Community feed, ROAR token-pricing (`spark_mint`)

## 🔐 Encryption-plan (F2F)

- Status nu: `⚪ slot leeg (klaar voor activatie)`
- Wanneer aan: API keys in `data/trade/bitvavo_credentials.json` versleutelen met AES-256-GCM
- Beschermt: bitvavo_api_key + bitvavo_api_secret per user

## 🧬 Verbinding met Spark-brein

Spark leest deze module via KB-kaart `kbv2-2f55a485` bij trader-gerelateerde vragen. Voor code-level introspectie kan Spark `snuffel_bestand` capability gebruiken op deze bestanden.

**Voorbeeld vragen die Spark nu kan beantwoorden**:
- "Wat is de fee?" → 0% voor Spark, 0.25% Bitvavo
- "Welke coins tradet Spark?" → BCH, BTC, ETH, SOL, ADA, ATOM
- "Hoe vaak koopt Spark?" → elke 15 min scan, max 1x per markt per 15 min
- "Wat gebeurt als er geen EUR is?" → 30 min cooldown vóór hij opnieuw probeert
- "Wat is een potje?" → klein kapitaaltje van €6.47 dat 1-op-1 met een ROAR-token gekoppeld is

## 📝 TODO / open items

- [ ] Pre-check EUR-balance vóór BUY-try (i.p.v. cooldown-vangnet achteraf)
- [ ] Split `monitor.py` in core / alerts / reporter
- [ ] Fill `position.size` expliciet bij BUY (nu fallback)
- [ ] Trader Settings-kader in UI (broker fee, precision, min-order readout)
- [ ] 2% fee bij token-BUY in Shop → routing naar token value
- [ ] BTW + SEPA integratie in kasboek
