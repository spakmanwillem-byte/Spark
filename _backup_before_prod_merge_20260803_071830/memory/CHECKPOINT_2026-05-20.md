# 📍 Checkpoint — 20 mei 2026, ~22:15 UTC

## Toestand bij deploy
- **Baseline**: €101,60 (Bitvavo BCH-positie + idle cash)
- **Pot-1 winst** (geboekt): +€50,80 netto
- **Live P/L**: +€0,58 (vs baseline)
- **Recent Trades widget**: leeg — admin-reset trades verborgen, wacht op eerste echte live trade
- **Stats**: 1 round-trip trade · gekocht €5,08 · verkocht €56,03 · fees €0,15 · netto +€50,80

## Wat draait er
- ✅ Multi-coin monitor LIVE op **BCH, BTC, ETH, SOL, ADA** (15m candles, 10-potjes mode, real-trade auto)
- ✅ 10 potjes geseed (pot-1 = €10,00 cap, rest €5,08), overflow_pool €45,88
- ✅ Spark bonus-tokens systeem actief (1 token / €5,08 winst → user-000 treasury voor server-kosten)
- ✅ Candle TTL-cache + shared ticker-call beschermen tegen Bitvavo rate-limit
- ✅ Watchlist klik switcht chart + Snelhandel live-prijs

## Volgende fases (na credits-bijvulling)
- 🟡 **P1** `v4_accounting_002` — Boekhouding per user-id (personal_willem → personal_{user_id})
- 🟡 **P1** `v4_dq_b` — TraderPage (1140 regels) splitsen naar TraderDashboard/Monitor/Potjes/Shop componenten
- 🟡 Spark's Spaarpot widget op admin-dashboard (live counter server-fund)
- 🟡 Decisions-lijst filterbaar per coin (BCH/BTC/.../Alles knoppen)
- 🟢 P3 Multi-timeframe analyse (15m + 1h + 4h per coin tegelijk)

## Bestanden voor rollback
- `/app/backend/data/financial/user_potjes.json.bak_pre_reset.json` — 11-potjes BCH state vóór reset
- `/app/backend/data/wallet/trade_history/user-001_archive_pre_reset_20260520_220604.json` — 8 oude BUY-trades
