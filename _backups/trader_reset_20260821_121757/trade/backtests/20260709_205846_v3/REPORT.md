# Trader Backtest v3 — Stress + Contrarian + Event

- Run: `20260709_205846` — 180 dagen × 6 markten

## Aggregaat (gesorteerd op PnL)

| # | Strategie | Trades | Win% | PnL € | Bull | Bear | Range |
|---|---|---:|---:|---:|---:|---:|---:|
| **I** | Random buy (chaos-baseline) | 27 | 100.0% | €+2.98 | €+0.68 | €+0.27 | €+2.04 |
| **D** | Bollinger 2σ + gap-body (winnaar v2) | 22 | 100.0% | €+2.63 | €+0.00 | €+1.42 | €+1.21 |
| **M** | Baseline + all-green profit-take | 23 | 100.0% | €+2.38 | €+0.69 | €+0.23 | €+1.46 |
| **A** | Bollinger 2σ (baseline) | 23 | 100.0% | €+2.31 | €+0.64 | €+0.23 | €+1.45 |
| **L** | All-red panic (5× rood → BUY) | 14 | 100.0% | €+1.74 | €+0.47 | €+0.00 | €+1.26 |
| **N** | Baseline + volume-weighted (>1.5×) | 15 | 100.0% | €+1.73 | €+0.29 | €+0.23 | €+1.20 |
| **O** | Adaptive sigma (1.5/2/3 dynamic) | 18 | 100.0% | €+1.60 | €+0.50 | €+0.11 | €+0.99 |
| **J** | Buy-and-hold (1× kopen, houden) | 6 | 0.0% | €-26.72 | €+0.00 | €+0.00 | €-26.72 |
| **K** | Inverse Bollinger (breakout-buy) | 1443 | 36.2% | €-88.58 | €-29.41 | €-14.23 | €-44.96 |

## 🌪 Event-analyse (>5% daily drop periodes)

- Gedetecteerd: **185 shock-events** over 6 markten × 6 maanden
  - BCH-EUR: 28 events, ergste −21.52%
  - BTC-EUR: 21 events, ergste −17.84%
  - ETH-EUR: 34 events, ergste −19.27%
  - SOL-EUR: 35 events, ergste −27.51%
  - ADA-EUR: 35 events, ergste −22.96%
  - ATOM-EUR: 32 events, ergste −18.44%

### Per-strategie in-event vs out-event

| # | Strategie | In-event PnL | In-event trades | Out-event PnL | Out-event trades |
|---|---|---:|---:|---:|---:|
| I | Random buy (chaos-baseline) | €+1.22 | 12 | €+1.76 | 15 |
| D | Bollinger 2σ + gap-body (winnaar v2) | €+2.18 | 18 | €+0.45 | 4 |
| M | Baseline + all-green profit-take | €+0.96 | 9 | €+1.41 | 14 |
| A | Bollinger 2σ (baseline) | €+0.77 | 9 | €+1.53 | 14 |
| L | All-red panic (5× rood → BUY) | €+0.12 | 2 | €+1.63 | 12 |
| N | Baseline + volume-weighted (>1.5×) | €+0.58 | 5 | €+1.14 | 10 |
| O | Adaptive sigma (1.5/2/3 dynamic) | €+0.35 | 5 | €+1.24 | 13 |
| J | Buy-and-hold (1× kopen, houden) | €-3.58 | 1 | €-23.14 | 5 |
| K | Inverse Bollinger (breakout-buy) | €-44.23 | 705 | €-44.33 | 738 |

## 🔀 Markt-correlatie (Pearson op 15m closes)

| | BCH-EUR | BTC-EUR | ETH-EUR | SOL-EUR | ADA-EUR | ATOM-EUR |
|---|---|---|---|---|---|---|
| **BCH-EUR** | +1.00 | +0.60 | +0.73 | +0.71 | +0.91 | +0.57 |
| **BTC-EUR** | +0.60 | +1.00 | +0.95 | +0.90 | +0.82 | +0.74 |
| **ETH-EUR** | +0.73 | +0.95 | +1.00 | +0.96 | +0.90 | +0.71 |
| **SOL-EUR** | +0.71 | +0.90 | +0.96 | +1.00 | +0.91 | +0.74 |
| **ADA-EUR** | +0.91 | +0.82 | +0.90 | +0.91 | +1.00 | +0.75 |
| **ATOM-EUR** | +0.57 | +0.74 | +0.71 | +0.74 | +0.75 | +1.00 |

**Interpretatie**: dichter bij +1.0 = markten bewegen samen (minder diversificatie). Dichter bij 0 of negatief = onafhankelijk (goed voor risico-spreiding).

## 🎯 Winnaar & aanbeveling

**I. Random buy (chaos-baseline)** — €+2.98 met 27 trades

Regime-analyse toont dat strategieën in **bull/bear/range** verschillend presteren. Adaptive keuze per regime = mogelijk volgende stap.
