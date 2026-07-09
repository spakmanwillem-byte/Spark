"""Backtest v4 — Willems hypothesen H1 (rebound) + H2 (48u loss-cut) + Post-event autopsy.

Nieuwe strategieën:
  P. D + 48u loss-cut bij -3% (kapitaal vrijmaken)
  Q. D + rebound-BUY tijdens event (koop juist tijdens crash, mikpunt 2%)
  R. Combined D + P + Q
  S. Baseline A + P (baseline met loss-cut, geen gap-filter)

Post-event autopsy:
  Voor elk van de 185 events uit v3: check prijs 24u/48u/72u erna.
  Bewijs: overreageert markt? Recovery >2% verwachtbaar?
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from backtest_v3 import (  # type: ignore
    fetch_candles, detect_events, detect_regime,
    std_of, Position, MARKETS, INTERVAL, DAYS,
    TRADE_AMOUNT_EUR, BITVAVO_FEE,
)


# ============================================================
# NIEUWE STRATEGIE-HELPERS
# ============================================================

CANDLE_SEC = 900  # 15m
LOSS_CUT_HOURS = 48
LOSS_CUT_PCT = -0.03  # -3% (verlies)
REBOUND_TARGET_PCT = 0.02  # +2% winst-target voor rebound-buy


def sell_with_loss_cut(window, position: Position, current_idx: int,
                       allow_break_even=False, loss_cut_enabled=True) -> Optional[str]:
    """Standaard fee-aware trailing + 48u loss-cut.
    Return 'SELL' als exit-signaal, None anders."""
    price = window[-1]["close"]
    position.highest_price = max(position.highest_price, window[-1]["high"])
    entry = position.entry_price
    profit_pct = (price - entry) / entry
    fees = TRADE_AMOUNT_EUR * BITVAVO_FEE * 2
    netto = TRADE_AMOUNT_EUR * profit_pct - fees

    # 48u loss-cut check
    if loss_cut_enabled:
        hold_bars = current_idx - position.entry_idx
        hold_hours = hold_bars * (CANDLE_SEC / 3600)
        if hold_hours >= LOSS_CUT_HOURS and profit_pct <= LOSS_CUT_PCT:
            return "SELL_LOSSCUT"  # gemarkeerd voor stats

    # Trailing stop (winst)
    if not position.trailing_active and netto >= 2 * fees:
        position.trailing_active = True
    if position.trailing_active:
        drop = (position.highest_price - price) / position.highest_price
        if drop >= 0.004:
            if netto > 0.01 or (allow_break_even and netto >= -fees):
                return "SELL"
    return None


def strat_A_baseline(window, pos, i, extra=None):
    if pos:
        r = sell_with_loss_cut(window, pos, i, loss_cut_enabled=False)
        return r or "HOLD"
    if len(window) < 20:
        return "HOLD"
    closes = [c["close"] for c in window[-20:]]
    mean = sum(closes) / 20
    lower = mean - 2 * std_of(closes)
    price = window[-1]["close"]
    window_high = max(closes[-10:])
    drop = (window_high - price) / window_high if window_high > 0 else 0
    if price < lower and drop >= 0.01:
        return "BUY"
    return "HOLD"


def strat_D_gap_body(window, pos, i, extra=None):
    if pos:
        r = sell_with_loss_cut(window, pos, i, loss_cut_enabled=False)
        return r or "HOLD"
    if strat_A_baseline(window, None, i) != "BUY":
        return "HOLD"
    if len(window) < 2:
        return "HOLD"
    prev, curr = window[-2], window[-1]
    if not (prev["close"] < prev["open"] and curr["close"] > curr["open"]):
        return "HOLD"
    pb = abs(prev["open"] - prev["close"])
    cb = abs(curr["close"] - curr["open"])
    if cb >= pb * 0.5 and cb > 0:
        return "BUY"
    return "HOLD"


def strat_P_D_plus_losscut(window, pos, i, extra=None):
    """D + 48u loss-cut bij ≥3% verlies"""
    if pos:
        r = sell_with_loss_cut(window, pos, i, loss_cut_enabled=True)
        return r or "HOLD"
    # BUY-logica = D
    return strat_D_gap_body(window, None, i)


def strat_S_A_plus_losscut(window, pos, i, extra=None):
    """Baseline A + 48u loss-cut — zonder gap-filter, wel met loss-cut"""
    if pos:
        r = sell_with_loss_cut(window, pos, i, loss_cut_enabled=True)
        return r or "HOLD"
    return strat_A_baseline(window, None, i)


def strat_Q_rebound(window, pos, i, extra=None):
    """D + rebound-BUY: koop juist als drop >5% in 24u (i.p.v. pauzeren).
    Target: 2% winst binnen redelijke tijd."""
    if pos:
        # Sell bij +2% (target bereikt) of loss-cut
        entry = pos.entry_price
        price = window[-1]["close"]
        profit_pct = (price - entry) / entry
        if profit_pct >= REBOUND_TARGET_PCT:
            return "SELL"
        r = sell_with_loss_cut(window, pos, i, loss_cut_enabled=True)
        return r or "HOLD"

    # BUY: 5%+ drop in laatste 24u (96 × 15m candles)
    if len(window) < 30:
        return "HOLD"
    if len(window) >= 96:
        window_24h = window[-96:]
        peak = max(c["high"] for c in window_24h)
        current = window[-1]["close"]
        if peak > 0 and (peak - current) / peak >= 0.05:
            return "BUY"
    return "HOLD"


def strat_R_combined(window, pos, i, extra=None):
    """D + P (loss-cut) + Q (rebound BUY tijdens event)"""
    if pos:
        # Target 2% for rebound-open positions? niet zo makkelijk; behandel gelijk
        r = sell_with_loss_cut(window, pos, i, loss_cut_enabled=True)
        return r or "HOLD"
    # Try rebound first (aggressief tijdens crash)
    rebound = strat_Q_rebound(window, None, i)
    if rebound == "BUY":
        return "BUY"
    # Anders: D
    return strat_D_gap_body(window, None, i)


STRATEGIES = [
    ("A", "Baseline (geen filters)", strat_A_baseline),
    ("D", "D — Bollinger + gap-body", strat_D_gap_body),
    ("P", "P — D + 48u loss-cut (-3%)", strat_P_D_plus_losscut),
    ("Q", "Q — Rebound (BUY tijdens crash, target +2%)", strat_Q_rebound),
    ("R", "R — Combined D + loss-cut + rebound", strat_R_combined),
    ("S", "S — Baseline A + 48u loss-cut", strat_S_A_plus_losscut),
]


# ============================================================
# POST-EVENT AUTOPSY
# ============================================================

def post_event_analysis(candles: List[Dict], events: List[Dict]) -> Dict:
    """Voor elk event: wat deed de prijs 24u, 48u, 72u erna?"""
    results = []
    for ev in events:
        end_idx = ev["idx_end"]
        low_price = ev["low_price"]
        recoveries = {}
        for hours, label in [(24, "24h"), (48, "48h"), (72, "72h")]:
            bars = hours * 4  # 4 candles per uur (15m)
            target_idx = end_idx + bars
            if target_idx < len(candles):
                future_price = candles[target_idx]["close"]
                recovery_pct = ((future_price - low_price) / low_price * 100) if low_price > 0 else 0
                recoveries[label] = round(recovery_pct, 2)
            else:
                recoveries[label] = None
        results.append({
            "drop_pct": ev["drop_pct"],
            "low_price": low_price,
            "recovery_24h_pct": recoveries.get("24h"),
            "recovery_48h_pct": recoveries.get("48h"),
            "recovery_72h_pct": recoveries.get("72h"),
        })

    # Stats
    def _valid(k):
        return [r[k] for r in results if r[k] is not None]
    stats = {}
    for k in ["recovery_24h_pct", "recovery_48h_pct", "recovery_72h_pct"]:
        v = _valid(k)
        if not v:
            stats[k] = None
            continue
        stats[k] = {
            "n": len(v),
            "mean": round(sum(v) / len(v), 2),
            "median": round(sorted(v)[len(v)//2], 2),
            "min": round(min(v), 2),
            "max": round(max(v), 2),
            "pct_positive": round(100 * sum(1 for x in v if x > 0) / len(v), 1),
            "pct_over_2": round(100 * sum(1 for x in v if x >= 2) / len(v), 1),
        }
    return {"per_event": results[:20], "stats": stats, "n_events": len(results)}


# ============================================================
# SIMULATIE
# ============================================================

def simulate(candles: List[Dict], strat_fn) -> Dict:
    trades = []
    position: Optional[Position] = None
    equity = [0.0]
    losscut_trades = 0
    WINDOW = 30
    for i in range(WINDOW, len(candles)):
        window = candles[i - WINDOW:i + 1]
        action = strat_fn(window, position, i, None)

        if action == "BUY" and not position:
            position = Position(window[-1]["close"], i, window[-1]["timestamp"])
        elif action in ("SELL", "SELL_LOSSCUT") and position:
            entry = position.entry_price
            exit_p = window[-1]["close"]
            gross = TRADE_AMOUNT_EUR * (exit_p - entry) / entry
            fees = TRADE_AMOUNT_EUR * BITVAVO_FEE * 2
            netto = gross - fees
            trade = {
                "entry_ts": position.entry_ts, "exit_ts": window[-1]["timestamp"],
                "entry_price": round(entry, 4), "exit_price": round(exit_p, 4),
                "net_pnl": round(netto, 4), "hold_bars": i - position.entry_idx,
                "win": netto > 0, "exit_type": action,
            }
            trades.append(trade)
            if action == "SELL_LOSSCUT":
                losscut_trades += 1
            equity.append(equity[-1] + netto)
            position = None

    n = len(trades)
    wins = sum(1 for t in trades if t["win"])
    total = sum(t["net_pnl"] for t in trades)
    peak = 0
    dd = 0
    for e in equity:
        peak = max(peak, e)
        dd = max(dd, peak - e)

    # Open drawdown = unrealized verlies bij einde
    open_drawdown = 0.0
    if position:
        entry = position.entry_price
        last_price = candles[-1]["close"]
        open_drawdown = TRADE_AMOUNT_EUR * (last_price - entry) / entry

    return {
        "trades": n, "wins": wins, "losses": n - wins,
        "win_rate": round(100 * wins / n, 1) if n else 0,
        "total_pnl_eur": round(total, 2),
        "avg_pnl_eur": round(total / n, 3) if n else 0,
        "max_drawdown_eur": round(dd, 2),
        "open_drawdown_eur": round(open_drawdown, 2),
        "avg_hold_hours": round(sum(t["hold_bars"] for t in trades) / n * 0.25, 1) if n else 0,
        "losscut_trades": losscut_trades,
        "open_at_end": position is not None,
    }


# ============================================================
# MAIN
# ============================================================

def main():
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_dir = Path(f"/app/backend/data/trade/backtests/{run_id}_v4")
    run_dir.mkdir(parents=True, exist_ok=True)

    print(f"[v4] {run_id} — H1 rebound + H2 loss-cut + post-event autopsy", file=sys.stderr)

    all_candles = {}
    all_events = {}
    for m in MARKETS:
        print(f"[fetch] {m}...", file=sys.stderr)
        cs = fetch_candles(m, INTERVAL, DAYS)
        if cs:
            all_candles[m] = cs
            all_events[m] = detect_events(cs, threshold_pct=5.0)

    # Post-event autopsy per markt
    autopsy = {}
    for m, cs in all_candles.items():
        autopsy[m] = post_event_analysis(cs, all_events[m])

    # Aggregeer autopsy
    all_recoveries_24 = []
    all_recoveries_48 = []
    all_recoveries_72 = []
    for m in autopsy:
        for ev in autopsy[m]["per_event"]:
            if ev.get("recovery_24h_pct") is not None:
                all_recoveries_24.append(ev["recovery_24h_pct"])
            if ev.get("recovery_48h_pct") is not None:
                all_recoveries_48.append(ev["recovery_48h_pct"])
            if ev.get("recovery_72h_pct") is not None:
                all_recoveries_72.append(ev["recovery_72h_pct"])

    def stats_of(vals):
        if not vals:
            return None
        return {
            "n": len(vals),
            "mean_pct": round(sum(vals)/len(vals), 2),
            "median_pct": round(sorted(vals)[len(vals)//2], 2),
            "pct_positive": round(100*sum(1 for x in vals if x > 0)/len(vals), 1),
            "pct_over_2": round(100*sum(1 for x in vals if x >= 2)/len(vals), 1),
            "pct_over_5": round(100*sum(1 for x in vals if x >= 5)/len(vals), 1),
        }

    autopsy_agg = {
        "n_events": sum(a["n_events"] for a in autopsy.values()),
        "recovery_24h": stats_of(all_recoveries_24),
        "recovery_48h": stats_of(all_recoveries_48),
        "recovery_72h": stats_of(all_recoveries_72),
    }

    # Strategie-simulaties
    results = {}
    for m, cs in all_candles.items():
        results[m] = {}
        for sid, sname, sfn in STRATEGIES:
            results[m][sid] = {"strategy": sname, **simulate(cs, sfn)}

    # Aggregeer strategieën
    agg = {}
    for sid, sname, _ in STRATEGIES:
        total_trades = sum(results[m][sid]["trades"] for m in results)
        total_wins = sum(results[m][sid]["wins"] for m in results)
        total_pnl = sum(results[m][sid]["total_pnl_eur"] for m in results)
        total_losscuts = sum(results[m][sid]["losscut_trades"] for m in results)
        total_open_dd = sum(results[m][sid]["open_drawdown_eur"] for m in results)
        agg[sid] = {
            "strategy": sname, "trades": total_trades, "wins": total_wins,
            "win_rate": round(100 * total_wins / total_trades, 1) if total_trades else 0,
            "total_pnl_eur": round(total_pnl, 2),
            "avg_pnl_eur": round(total_pnl / total_trades, 3) if total_trades else 0,
            "losscut_trades": total_losscuts,
            "open_drawdown_eur": round(total_open_dd, 2),
            "net_including_open": round(total_pnl + total_open_dd, 2),
        }

    # Save
    meta = {
        "run_id": run_id, "created_at": datetime.now(timezone.utc).isoformat(),
        "doel": "Test H1 rebound + H2 48u loss-cut + post-event autopsy",
        "markten": MARKETS, "periode_dagen": DAYS,
        "strategieën": [{"id": s[0], "name": s[1]} for s in STRATEGIES],
        "vorige_runs": ["20260709_205003 (v2)", "20260709_205846 (v3)"],
    }
    (run_dir / "_meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    (run_dir / "aggregate.json").write_text(json.dumps(agg, indent=2, ensure_ascii=False))
    (run_dir / "per_market.json").write_text(json.dumps(results, indent=2, ensure_ascii=False))
    (run_dir / "autopsy.json").write_text(json.dumps({"aggregate": autopsy_agg, "per_market": autopsy}, indent=2, ensure_ascii=False))

    # Update index
    idx_file = Path("/app/backend/data/trade/backtests/_meta.json")
    idx = json.loads(idx_file.read_text()) if idx_file.exists() else {"_type": "backtest_index", "runs": []}
    idx["runs"].append({"run_id": run_id, "type": "v4_hypotheses", "doel": meta["doel"], "path": f"backtests/{run_id}_v4/"})
    idx["laatst_bijgewerkt"] = meta["created_at"]
    idx_file.write_text(json.dumps(idx, indent=2, ensure_ascii=False))

    # Report
    write_report_v4(agg, autopsy_agg, run_dir, meta)

    # Console
    print("\n" + "=" * 100, file=sys.stderr)
    print(f"{'#':<3}{'Strategie':<45}{'Trades':>7}{'Win%':>6}{'PnL':>9}{'OpenDD':>9}{'Netto':>9}{'LossCuts':>10}", file=sys.stderr)
    print("=" * 100, file=sys.stderr)
    for sid, r in sorted(agg.items(), key=lambda x: -x[1]["net_including_open"]):
        print(f"{sid:<3}{r['strategy']:<45}{r['trades']:>7}{r['win_rate']:>5.1f}%"
              f"€{r['total_pnl_eur']:>+7.2f}€{r['open_drawdown_eur']:>+7.2f}"
              f"€{r['net_including_open']:>+7.2f}{r['losscut_trades']:>10}", file=sys.stderr)

    print("\n=== POST-EVENT AUTOPSY (Willems H1) ===", file=sys.stderr)
    for k, v in autopsy_agg.items():
        if isinstance(v, dict):
            print(f"  {k}: n={v['n']}, mean={v['mean_pct']}%, median={v['median_pct']}%, "
                  f"positive={v['pct_positive']}%, >2%={v['pct_over_2']}%, >5%={v['pct_over_5']}%", file=sys.stderr)
        else:
            print(f"  {k}: {v}", file=sys.stderr)

    print(f"\n[done] {run_dir}", file=sys.stderr)


def write_report_v4(agg, autopsy, run_dir, meta):
    lines = [f"# Backtest v4 — Hypothesen H1 (rebound) + H2 (48u loss-cut)\n\n"]
    lines.append(f"- Run: `{meta['run_id']}` — {meta['periode_dagen']} dagen × {len(meta['markten'])} markten\n\n")

    lines.append("## Aggregaat — sorteerd op ECHT netto (PnL + open drawdown)\n\n")
    lines.append("| # | Strategie | Trades | Win% | PnL € | Open DD € | ECHT netto € | Loss-cuts |\n")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|\n")
    for sid, r in sorted(agg.items(), key=lambda x: -x[1]["net_including_open"]):
        lines.append(f"| **{sid}** | {r['strategy']} | {r['trades']} | {r['win_rate']}% | "
                     f"€{r['total_pnl_eur']:+.2f} | €{r['open_drawdown_eur']:+.2f} | "
                     f"**€{r['net_including_open']:+.2f}** | {r['losscut_trades']} |\n")
    lines.append("\n**KEY**: 'ECHT netto' = gerealiseerde PnL + onrealized open verlies. Dit is de EERLIJKE metric die 100% win-rate ontmaskert.\n\n")

    lines.append("## 🔬 POST-EVENT AUTOPSY (Willems H1)\n\n")
    lines.append(f"Totaal geanalyseerde events: **{autopsy['n_events']}**\n\n")
    lines.append("| Window | N | Mean % | Median % | Positief % | ≥2% herstel | ≥5% herstel |\n")
    lines.append("|---|---:|---:|---:|---:|---:|---:|\n")
    for k, label in [("recovery_24h", "24u na dip"), ("recovery_48h", "48u na dip"), ("recovery_72h", "72u na dip")]:
        v = autopsy.get(k)
        if v:
            lines.append(f"| {label} | {v['n']} | {v['mean_pct']}% | {v['median_pct']}% | "
                         f"{v['pct_positive']}% | {v['pct_over_2']}% | {v['pct_over_5']}% |\n")
    lines.append("\n**Interpretatie H1**: als %positief >70% en %≥2% is >50% → BUY-tijdens-crash is beter dan pauzeer.\n\n")

    winner = max(agg.items(), key=lambda x: x[1]["net_including_open"])
    lines.append(f"## 🏆 Winnaar op ECHT netto: **{winner[0]}. {winner[1]['strategy']}**\n\n")
    lines.append(f"- Gerealiseerd: €{winner[1]['total_pnl_eur']:+.2f}\n")
    lines.append(f"- Open drawdown: €{winner[1]['open_drawdown_eur']:+.2f}\n")
    lines.append(f"- **ECHT netto**: €{winner[1]['net_including_open']:+.2f}\n")
    lines.append(f"- Loss-cuts: {winner[1]['losscut_trades']} (van {winner[1]['trades']} totaal)\n\n")

    (run_dir / "REPORT.md").write_text("".join(lines), encoding="utf-8")
    Path(f"/app/test_reports/backtest_v4_{meta['run_id']}.md").write_text("".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
