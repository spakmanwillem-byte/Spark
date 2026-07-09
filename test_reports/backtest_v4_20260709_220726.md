# Backtest v5 (360d) — Hypothesen H1 (rebound) + H2 (48u loss-cut)

- Run: `20260709_220726` — 360 dagen × 6 markten

## Aggregaat — sorteerd op ECHT netto (PnL + open drawdown)

| # | Strategie | Trades | Win% | PnL € | Open DD € | ECHT netto € | Loss-cuts |
|---|---|---:|---:|---:|---:|---:|---:|
| **Q** | Q — Rebound (BUY tijdens crash, target +2%) | 0 | 0% | €+0.00 | €+0.00 | **€+0.00** | 0 |
| **P** | P — D + 48u loss-cut (-3%) | 138 | 73.2% | €-9.04 | €-0.20 | **€-9.24** | 37 |
| **R** | R — Combined D + loss-cut + rebound | 138 | 73.2% | €-9.04 | €-0.20 | **€-9.24** | 37 |
| **D** | D — Bollinger + gap-body | 62 | 100.0% | €+8.84 | €-22.30 | **€-13.46** | 0 |
| **A** | Baseline (geen filters) | 77 | 100.0% | €+9.80 | €-39.06 | **€-29.26** | 0 |
| **S** | S — Baseline A + 48u loss-cut | 1188 | 73.1% | €-77.10 | €-0.75 | **€-77.85** | 319 |

**KEY**: 'ECHT netto' = gerealiseerde PnL + onrealized open verlies. Dit is de EERLIJKE metric die 100% win-rate ontmaskert.

## 🔬 POST-EVENT AUTOPSY (Willems H1)

Totaal geanalyseerde events: **373**

| Window | N | Mean % | Median % | Positief % | ≥2% herstel | ≥5% herstel |
|---|---:|---:|---:|---:|---:|---:|
| 24u na dip | 120 | 1.42% | 1.14% | 60.0% | 41.7% | 24.2% |
| 48u na dip | 120 | 1.4% | 0.73% | 57.5% | 43.3% | 27.5% |
| 72u na dip | 120 | 0.38% | 0.33% | 51.7% | 40.8% | 24.2% |

**Interpretatie H1**: als %positief >70% en %≥2% is >50% → BUY-tijdens-crash is beter dan pauzeer.

## 🏆 Winnaar op ECHT netto: **Q. Q — Rebound (BUY tijdens crash, target +2%)**

- Gerealiseerd: €+0.00
- Open drawdown: €+0.00
- **ECHT netto**: €+0.00
- Loss-cuts: 0 (van 0 totaal)

