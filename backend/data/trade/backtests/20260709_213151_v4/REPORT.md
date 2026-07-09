# Backtest v4 — Hypothesen H1 (rebound) + H2 (48u loss-cut)

- Run: `20260709_213151` — 180 dagen × 6 markten

## Aggregaat — sorteerd op ECHT netto (PnL + open drawdown)

| # | Strategie | Trades | Win% | PnL € | Open DD € | ECHT netto € | Loss-cuts |
|---|---|---:|---:|---:|---:|---:|---:|
| **Q** | Q — Rebound (BUY tijdens crash, target +2%) | 0 | 0% | €+0.00 | €+0.00 | **€+0.00** | 0 |
| **P** | P — D + 48u loss-cut (-3%) | 65 | 66.2% | €-9.35 | €-0.18 | **€-9.53** | 22 |
| **R** | R — Combined D + loss-cut + rebound | 65 | 66.2% | €-9.35 | €-0.18 | **€-9.53** | 22 |
| **D** | D — Bollinger + gap-body | 22 | 100.0% | €+2.63 | €-15.79 | **€-13.16** | 0 |
| **A** | Baseline (geen filters) | 23 | 100.0% | €+2.31 | €-28.46 | **€-26.15** | 0 |
| **S** | S — Baseline A + 48u loss-cut | 576 | 71.4% | €-44.95 | €-0.75 | **€-45.70** | 165 |

**KEY**: 'ECHT netto' = gerealiseerde PnL + onrealized open verlies. Dit is de EERLIJKE metric die 100% win-rate ontmaskert.

## 🔬 POST-EVENT AUTOPSY (Willems H1)

Totaal geanalyseerde events: **185**

| Window | N | Mean % | Median % | Positief % | ≥2% herstel | ≥5% herstel |
|---|---:|---:|---:|---:|---:|---:|
| 24u na dip | 120 | 0.47% | 1.96% | 62.5% | 49.2% | 17.5% |
| 48u na dip | 120 | 0.31% | 0.91% | 56.7% | 45.0% | 23.3% |
| 72u na dip | 120 | -0.63% | 0.85% | 53.3% | 38.3% | 20.0% |

**Interpretatie H1**: als %positief >70% en %≥2% is >50% → BUY-tijdens-crash is beter dan pauzeer.

## 🏆 Winnaar op ECHT netto: **Q. Q — Rebound (BUY tijdens crash, target +2%)**

- Gerealiseerd: €+0.00
- Open drawdown: €+0.00
- **ECHT netto**: €+0.00
- Loss-cuts: 0 (van 0 totaal)

