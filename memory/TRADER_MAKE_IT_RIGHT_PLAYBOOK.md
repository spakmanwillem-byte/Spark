# Trader "Make It Right" — Deploy Playbook (sessie 56b)

**Situatie**: In productie stond de trader met **ghost-potjes** doordat Willem's
Bitvavo-EUR-saldo tijdelijk leeg was. Bots deden ondertussen buy-cycles die
inconsistent gefilled zijn. Willem heeft de trader in productie op **STOP**
gezet en wil na deploy alles in 1x rechtzetten.

## Nieuwe endpoints (klaar in preview, deploy nodig)

### 1. Ghost-scan / auto-fix (state-corruption)
```
POST /api/trade/potjes/auto-fix-ghosts/{user_id}?dry_run=true
POST /api/trade/potjes/auto-fix-ghosts-all?dry_run=true
```
Detecteert potjes met `position.is_open=True` maar geen BUY in trade_log.
Reset ze naar 'vrij' status. Bewaart history in `audit_log`.

**Preview-test bewijs**: user-000 had 2 ghosts (pot-007 ETH, pot-008 BCH).
Beide gereset naar 'vrij' na `dry_run=false`. Herscan = 0 ghost.

### 2. Bitvavo-sync ijkpunt (kloppend maken)
```
POST /api/trade/potjes/sync-from-bitvavo-ijkpunt/{user_id}?dry_run=true
```
Complete flow:
1. Fetch actual coin balance van Bitvavo (via user's API-key)
2. Per markt: anchor-pot (of eerste open) → `position.filled_coin` = actual
3. `entry_price` = huidige markt-prijs (nieuw ijkpunt = nu)
4. `amount_eur` = actual_coin × current_price
5. Bitvavo=0 + pot open → auto-close (ghost)
6. Bitvavo>0 zonder pot → orphan-report (Willem verplaatst handmatig)
7. Papertrail-log entry als `trader_ijkpunt` event

**Preview-test bewijs** (user-000 met echte Bitvavo API-call):
- BCH pot-001 sync → 0.000956 BCH (was 2 ghost pots eromheen)
- BTC pot-002 sync → 0.000002 BTC
- ETH pot-003 sync → 0.000047 ETH
- SOL pot-004 sync → 0.001390 SOL
- ADA pot-005 sync → 1.901460 ADA
- Orphan-coins: CSPR (159), GRT, ATOM, LPT, XTZ, LUNA, LUNA2, KSM, NEO

## Aanbevolen deploy-flow voor Willem

1. **Deploy preview → productie**
2. Trader in productie blijft op STOP (belangrijk!)
3. Draai productie-URL:
   ```
   curl -X POST "$PROD/api/trade/potjes/auto-fix-ghosts-all?dry_run=true"
   ```
   → check wat er zou gebeuren, alle users
4. Als dat er goed uitziet:
   ```
   curl -X POST "$PROD/api/trade/potjes/auto-fix-ghosts-all?dry_run=false"
   ```
5. Voor Spark (user-000) specifiek de Bitvavo-sync:
   ```
   curl -X POST "$PROD/api/trade/potjes/sync-from-bitvavo-ijkpunt/user-000?dry_run=true"
   curl -X POST "$PROD/api/trade/potjes/sync-from-bitvavo-ijkpunt/user-000?dry_run=false"
   ```
6. Check papertrail: er staat een `trader_ijkpunt` event met alle balances +
   acties op moment X. Dat is het nieuwe "ijkpunt vanaf hier klopt alles".
7. Trader bots weer aanzetten
8. Nieuwe trades registeren nu wel `filled_coin` (**let op**: architectuur-fix
   voor `execute_real_trade` moet nog — zie ROADMAP P0 backlog)

## Nog TE DOEN (aparte sessie)

Preventie van herhaling:
- `execute_real_trade`: parse `filledAmount` uit Bitvavo response, fail bij 0
- `open_pot`: verplicht `filled_coin > 0` argument, weiger anders
- Auto-pauze bots als EUR-saldo langer dan X uur onder minimum

Zie `/app/memory/ROADMAP_CORE.md` → cluster sessie 56b → P1 backlog.
