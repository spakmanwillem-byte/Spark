# Trader Backtest v2 — Multi-market

- Run-ID: `20260709_205003`
- Periode: **180 dagen** (t/m 2026-07-09)
- Markten: BCH-EUR, BTC-EUR, ETH-EUR, SOL-EUR, ADA-EUR, ATOM-EUR
- Trade-bedrag: €10.00 per trade, fees 0.25% per zijde

## Aggregaat over alle 6 markten

| # | Strategie | Trades | Win% | PnL € | Ø/trade € | DD € | Blok% |
|---|---|---:|---:|---:|---:|---:|---:|
| **D** | Bollinger 2σ + gap-body (50%) | 22 | 100.0% | +3.29 | +0.150 | 0.00 | 98.3% |
| **E** | Bollinger 2σ + 3-red-green (Neef) | 21 | 100.0% | +3.19 | +0.152 | 0.00 | 96.7% |
| **F** | Bollinger 1.5σ (losser BUY) | 20 | 100.0% | +3.03 | +0.152 | 0.00 | 0.0% |
| **A** | Bollinger 2σ (baseline huidig) | 19 | 100.0% | +2.78 | +0.146 | 0.00 | 0.0% |
| **G** | Bollinger 1.5σ + gap-body | 11 | 100.0% | +1.66 | +0.151 | 0.00 | 93.6% |
| **H** | Bollinger 1.5σ + gap-body + break-even sell | 11 | 100.0% | +1.66 | +0.151 | 0.00 | 93.6% |
| **C** | Bollinger 2σ + gap-los | 3 | 100.0% | +0.31 | +0.103 | 0.00 | 99.9% |
| **B** | Bollinger 2σ + gap-streng (v7 huidig) | 0 | 0% | +0.00 | +0.000 | 0.00 | 100.0% |

## 🏆 Winnaar: **D. Bollinger 2σ + gap-body (50%)**

- €+3.29 totaal over 6 maanden × 6 markten
- 22 trades met 100.0% win-rate
- Max drawdown: €0.00

## Per markt detail (winnaar-strategie)

| Markt | Trades | Win% | PnL € | DD € |
|---|---:|---:|---:|---:|
| BCH-EUR | 1 | 100.0% | +0.10 | 0.00 |
| BTC-EUR | 1 | 100.0% | +0.13 | 0.00 |
| ETH-EUR | 1 | 100.0% | +0.14 | 0.00 |
| SOL-EUR | 7 | 100.0% | +1.23 | 0.00 |
| ADA-EUR | 0 | 0% | +0.00 | 0.00 |
| ATOM-EUR | 12 | 100.0% | +1.69 | 0.00 |

## Interpretatie

- **Baseline (A)** produceerde €+2.78 met 19 trades — dit is het referentiepunt.
- **B (Bollinger 2σ + gap-streng (v7 huidig))**: PnL -2.78€ vs baseline, 0 trades (100.0% van BUY-signalen geblokkeerd door gap-filter)
- **C (Bollinger 2σ + gap-los)**: PnL -2.47€ vs baseline, 3 trades (99.9% van BUY-signalen geblokkeerd door gap-filter)
- **D (Bollinger 2σ + gap-body (50%))**: PnL +0.51€ vs baseline, 22 trades (98.3% van BUY-signalen geblokkeerd door gap-filter)
- **E (Bollinger 2σ + 3-red-green (Neef))**: PnL +0.41€ vs baseline, 21 trades (96.7% van BUY-signalen geblokkeerd door gap-filter)
- **F (Bollinger 1.5σ (losser BUY))** [OPTIMALISATIE]: PnL +0.25€ vs baseline, 20 trades
- **G (Bollinger 1.5σ + gap-body)** [OPTIMALISATIE]: PnL -1.12€ vs baseline, 11 trades
- **H (Bollinger 1.5σ + gap-body + break-even sell)** [OPTIMALISATIE]: PnL -1.12€ vs baseline, 11 trades

**Data structureel opgeslagen** in `data/trade/backtests/20260709_205003/` met `_meta.json` (Willem's SoT-regel).
