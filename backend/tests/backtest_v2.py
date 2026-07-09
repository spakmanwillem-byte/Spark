"""Backtest v2 — Multi-market + optimalisatie-varianten.

Verbeteringen tov v1:
- 6 markten: BCH, BTC, ETH, SOL, ADA, ATOM
- 8 strategieën (baseline + 4 gap-varianten + 3 optimalisaties)
- Structurele opslag in /app/backend/data/trade/backtests/{run_id}/ met _meta.json
- Volgt Willem's regel "Help-data is single source of truth"
- Auto-genereert KB-footnote entry voor Spark Trader kaart
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
from copy import deepcopy

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from modules.trade.monitor import _simple_decision  # type: ignore

BITVAVO_URL = "https://api.bitvavo.com/v2"
MARKETS = ["BCH-EUR", "BTC-EUR", "ETH-EUR", "SOL-EUR", "ADA-EUR", "ATOM-EUR"]
INTERVAL = "15m"
DAYS = 180
LIMIT_PER_CALL = 1440
TRADE_AMOUNT_EUR = 10.0
BITVAVO_FEE = 0.0025


# ============================================================
# FETCH (paginated) — met TTL cache in /tmp/candles_cache/
# ============================================================

CACHE_DIR = Path("/tmp/candles_cache")
CACHE_DIR.mkdir(exist_ok=True)


def fetch_candles(market: str, interval: str, days: int) -> List[Dict]:
    cache_file = CACHE_DIR / f"{market}_{interval}_{days}d.json"
    if cache_file.exists() and (time.time() - cache_file.stat().st_mtime) < 3600:
        return json.loads(cache_file.read_text())
    now_ms = int(time.time() * 1000)
    start_ms = now_ms - (days * 86_400_000)
    all_candles: List[Dict] = []
    end_ms = now_ms
    while end_ms > start_ms:
        url = f"{BITVAVO_URL}/{market}/candles?interval={interval}&limit={LIMIT_PER_CALL}&end={end_ms}"
        try:
            r = requests.get(url, timeout=15)
            r.raise_for_status()
            raw = r.json()
            if not raw:
                break
            batch = [{
                "timestamp": c[0], "open": float(c[1]), "high": float(c[2]),
                "low": float(c[3]), "close": float(c[4]), "volume": float(c[5]),
            } for c in raw if len(c) >= 6]
            if not batch:
                break
            all_candles.extend(batch)
            oldest = min(c["timestamp"] for c in batch)
            if oldest <= start_ms or oldest >= end_ms:
                break
            end_ms = oldest - 1
            time.sleep(0.08)
        except Exception as e:
            print(f"[fetch] error {market}: {e}", file=sys.stderr)
            break
    seen = set()
    unique = sorted(
        [c for c in all_candles if c["timestamp"] not in seen and not seen.add(c["timestamp"])],
        key=lambda x: x["timestamp"]
    )
    cache_file.write_text(json.dumps(unique))
    return unique


# ============================================================
# BOLLINGER (aangepaste versie met σ-parameter)
# ============================================================

def bollinger_decision(candles: List[Dict], position: Optional[Dict],
                       sigma: float = 2.0, allow_break_even: bool = False) -> Dict:
    """Kopie van _simple_decision maar met tunable sigma en break-even sell."""
    if len(candles) < 5:
        return {"action": "HOLD", "reason": "te weinig data"}
    closes = [c["close"] for c in candles[-20:]]
    mean = sum(closes) / len(closes)
    var = sum((x - mean) ** 2 for x in closes) / len(closes)
    std = var ** 0.5 if var > 0 else 0.001
    price = candles[-1]["close"]
    lower = mean - sigma * std
    upper = mean + sigma * std

    if position and position.get("is_open"):
        entry = position["entry_price"]
        highest = max(position.get("highest_price", entry), price)
        profit_pct = (price - entry) / entry
        bruto = TRADE_AMOUNT_EUR * profit_pct
        fees = TRADE_AMOUNT_EUR * BITVAVO_FEE * 2
        netto = bruto - fees

        # Trailing activatie bij 2× fees winst
        trailing_active = position.get("trailing_active") or netto >= 2 * fees

        if trailing_active:
            drop_from_high = (highest - price) / highest if highest > 0 else 0
            if drop_from_high >= 0.004:  # -0.4% drop
                if netto > 0.01 or (allow_break_even and netto >= -fees):
                    return {"action": "SELL", "reason": f"trail exit netto=€{netto:.3f}",
                            "trailing_active": True}
        return {"action": "HOLD", "reason": "positie open, wacht", "trailing_active": trailing_active}

    # BUY: price onder lower band + drop vanaf recent high
    window_high = max(closes[-10:])
    drop = (window_high - price) / window_high if window_high > 0 else 0
    if price < lower and drop >= 0.01:
        return {"action": "BUY", "reason": f"price €{price:.4f} < lower €{lower:.4f} @ {sigma}σ, "
                                             f"drop {drop*100:.2f}% van piek"}
    return {"action": "HOLD", "reason": f"price in band ({(price-lower)/(upper-lower):.2f})"}


# ============================================================
# GAP-FILTERS
# ============================================================

def gap_streng(prev, curr):
    return (prev["close"] < prev["open"] and curr["close"] > curr["open"]
            and curr["low"] > prev["high"])


def gap_los(prev, curr):
    return (prev["close"] < prev["open"] and curr["close"] > curr["open"]
            and curr["close"] > prev["high"])


def gap_body_momentum(prev, curr, ratio=0.5):
    """Losste variant: green candle body > 50% van vorige red body, ongeacht price-overlap."""
    prev_red = prev["close"] < prev["open"]
    curr_green = curr["close"] > curr["open"]
    if not (prev_red and curr_green):
        return False
    prev_body = abs(prev["open"] - prev["close"])
    curr_body = abs(curr["close"] - curr["open"])
    return curr_body >= prev_body * ratio and curr_body > 0


def n_red_then_green(candles, n=3):
    if len(candles) < n + 1:
        return False
    return (all(c["close"] < c["open"] for c in candles[-(n+1):-1])
            and candles[-1]["close"] > candles[-1]["open"])


# ============================================================
# STRATEGIE DEFINITIES
# ============================================================

STRATEGIES = [
    # baseline
    {"id": "A", "name": "Bollinger 2σ (baseline huidig)",
     "sigma": 2.0, "gap": None, "break_even": False},

    # gap-varianten
    {"id": "B", "name": "Bollinger 2σ + gap-streng (v7 huidig)",
     "sigma": 2.0, "gap": "streng", "break_even": False},
    {"id": "C", "name": "Bollinger 2σ + gap-los",
     "sigma": 2.0, "gap": "los", "break_even": False},
    {"id": "D", "name": "Bollinger 2σ + gap-body (50%)",
     "sigma": 2.0, "gap": "body", "break_even": False},
    {"id": "E", "name": "Bollinger 2σ + 3-red-green (Neef)",
     "sigma": 2.0, "gap": "n_red3", "break_even": False},

    # optimalisaties (meer rendement)
    {"id": "F", "name": "Bollinger 1.5σ (losser BUY)",
     "sigma": 1.5, "gap": None, "break_even": False},
    {"id": "G", "name": "Bollinger 1.5σ + gap-body",
     "sigma": 1.5, "gap": "body", "break_even": False},
    {"id": "H", "name": "Bollinger 1.5σ + gap-body + break-even sell",
     "sigma": 1.5, "gap": "body", "break_even": True},
]


def check_gap(gap_type: Optional[str], window: List[Dict]) -> bool:
    if not gap_type:
        return True
    if len(window) < 2:
        return False
    if gap_type == "streng":
        return gap_streng(window[-2], window[-1])
    if gap_type == "los":
        return gap_los(window[-2], window[-1])
    if gap_type == "body":
        return gap_body_momentum(window[-2], window[-1])
    if gap_type == "n_red3":
        return n_red_then_green(window, n=3)
    return True


def simulate(candles: List[Dict], strategy: Dict) -> Dict:
    trades = []
    position: Optional[Dict] = None
    equity = [0.0]
    blocked = 0
    allowed = 0
    WINDOW = 30

    for i in range(WINDOW, len(candles)):
        window = candles[i - WINDOW:i + 1]

        if position and position.get("is_open"):
            position["highest_price"] = max(position["highest_price"], window[-1]["high"])

        d = bollinger_decision(window, position=position,
                               sigma=strategy["sigma"], allow_break_even=strategy["break_even"])

        if d["action"] == "BUY" and (not position or not position.get("is_open")):
            if not check_gap(strategy["gap"], window):
                blocked += 1
                continue
            allowed += 1
            position = {"is_open": True, "entry_price": window[-1]["close"],
                        "entry_idx": i, "entry_ts": window[-1]["timestamp"],
                        "highest_price": window[-1]["close"], "trailing_active": False}

        elif d["action"] == "SELL" and position and position.get("is_open"):
            entry = position["entry_price"]
            exit_p = window[-1]["close"]
            gross = TRADE_AMOUNT_EUR * (exit_p - entry) / entry
            fees = TRADE_AMOUNT_EUR * BITVAVO_FEE * 2
            netto = gross - fees
            trades.append({
                "entry_price": round(entry, 4), "exit_price": round(exit_p, 4),
                "entry_ts": position["entry_ts"], "exit_ts": window[-1]["timestamp"],
                "net_pnl": round(netto, 4), "hold_bars": i - position["entry_idx"],
                "win": netto > 0,
            })
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
    return {
        "trades": n, "wins": wins, "losses": n - wins,
        "win_rate": round(100 * wins / n, 1) if n else 0,
        "total_pnl_eur": round(total, 2),
        "avg_pnl_eur": round(total / n, 3) if n else 0,
        "max_drawdown_eur": round(dd, 2),
        "avg_hold_hours": round(sum(t["hold_bars"] for t in trades) / n * 0.25, 1) if n else 0,
        "blocked": blocked, "allowed": allowed,
        "open_at_end": position is not None,
        "trade_details": trades[:10],  # eerste 10 voor rapport
    }


# ============================================================
# MAIN + STRUCTURELE OPSLAG
# ============================================================

def main():
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_dir = Path(f"/app/backend/data/trade/backtests/{run_id}")
    run_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = run_dir / "raw"
    raw_dir.mkdir(exist_ok=True)

    print(f"[run] {run_id} — {len(MARKETS)} markten × {len(STRATEGIES)} strategieën", file=sys.stderr)

    all_results = {}
    for market in MARKETS:
        print(f"[fetch] {market}...", file=sys.stderr)
        candles = fetch_candles(market, INTERVAL, DAYS)
        if not candles:
            print(f"  SKIP {market} (no data)", file=sys.stderr)
            continue
        print(f"  {len(candles)} candles", file=sys.stderr)
        market_results = {}
        for strat in STRATEGIES:
            result = simulate(candles, strat)
            market_results[strat["id"]] = {**{"strategy": strat["name"]}, **result}
        all_results[market] = market_results
        (raw_dir / f"{market}.json").write_text(json.dumps(market_results, indent=2, ensure_ascii=False))

    # AGGREGATEN over alle markten
    aggregate = {}
    for strat in STRATEGIES:
        sid = strat["id"]
        total_trades = sum(all_results[m][sid]["trades"] for m in all_results)
        total_wins = sum(all_results[m][sid]["wins"] for m in all_results)
        total_pnl = sum(all_results[m][sid]["total_pnl_eur"] for m in all_results)
        total_blocked = sum(all_results[m][sid]["blocked"] for m in all_results)
        total_allowed = sum(all_results[m][sid]["allowed"] for m in all_results)
        max_dd = max((all_results[m][sid]["max_drawdown_eur"] for m in all_results), default=0)
        aggregate[sid] = {
            "strategy": strat["name"],
            "params": {k: v for k, v in strat.items() if k not in ("id", "name")},
            "trades": total_trades, "wins": total_wins,
            "win_rate": round(100 * total_wins / total_trades, 1) if total_trades else 0,
            "total_pnl_eur": round(total_pnl, 2),
            "avg_pnl_eur": round(total_pnl / total_trades, 3) if total_trades else 0,
            "max_drawdown_eur": round(max_dd, 2),
            "gap_blocked": total_blocked, "gap_allowed": total_allowed,
            "blocked_pct": round(100 * total_blocked / (total_blocked + total_allowed), 1)
                if (total_blocked + total_allowed) else 0,
        }

    # META per Willem's regel: single source of truth met bron + doel
    meta = {
        "run_id": run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "doel": "Vergelijk BUY-strategieën over historische Bitvavo-data om beste live-configuratie te kiezen",
        "bron": "Bitvavo public API /candles (17.000+ candles per markt via paginated end-param)",
        "markten": MARKETS,
        "periode_dagen": DAYS,
        "candle_interval": INTERVAL,
        "trade_bedrag_eur": TRADE_AMOUNT_EUR,
        "fee_pct": BITVAVO_FEE,
        "strategieën": [{"id": s["id"], "name": s["name"], "params": {k: v for k, v in s.items() if k not in ("id", "name")}} for s in STRATEGIES],
        "footnote": {
            "kb_kaart_ref": "kbv2-2f55a485",  # Spark Trader kaart
            "code_ref": "backend/tests/backtest_v2.py",
            "sibling_data": "market_stats.json (echte trade-stats voor cross-validatie)",
            "insight_dashboard_ref": "/beheer → Trader → Backtests (nog te bouwen UI)",
        },
    }
    (run_dir / "_meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    (run_dir / "aggregate.json").write_text(json.dumps(aggregate, indent=2, ensure_ascii=False))
    (run_dir / "per_market.json").write_text(json.dumps(all_results, indent=2, ensure_ascii=False))

    # Update backtests _meta.json (index van alle runs)
    idx_file = Path("/app/backend/data/trade/backtests/_meta.json")
    if idx_file.exists():
        idx = json.loads(idx_file.read_text())
    else:
        idx = {"_type": "backtest_index", "runs": []}
    idx["runs"].append({"run_id": run_id, "doel": meta["doel"], "markten": len(MARKETS),
                        "strategieën": len(STRATEGIES), "path": f"backtests/{run_id}/"})
    idx["laatst_bijgewerkt"] = meta["created_at"]
    idx_file.write_text(json.dumps(idx, indent=2, ensure_ascii=False))

    # Markdown rapport
    write_markdown(aggregate, all_results, run_dir, meta)
    write_console_summary(aggregate)
    return run_dir


def write_markdown(agg, per_market, run_dir, meta):
    lines = [f"# Trader Backtest v2 — Multi-market\n\n"]
    lines.append(f"- Run-ID: `{meta['run_id']}`\n")
    lines.append(f"- Periode: **{meta['periode_dagen']} dagen** (t/m {meta['created_at'][:10]})\n")
    lines.append(f"- Markten: {', '.join(meta['markten'])}\n")
    lines.append(f"- Trade-bedrag: €{meta['trade_bedrag_eur']:.2f} per trade, fees {meta['fee_pct']*100:.2f}% per zijde\n\n")

    lines.append("## Aggregaat over alle 6 markten\n\n")
    lines.append("| # | Strategie | Trades | Win% | PnL € | Ø/trade € | DD € | Blok% |\n")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|\n")
    sorted_agg = sorted(agg.items(), key=lambda x: -x[1]["total_pnl_eur"])
    for sid, r in sorted_agg:
        lines.append(f"| **{sid}** | {r['strategy']} | {r['trades']} | {r['win_rate']}% | "
                     f"{r['total_pnl_eur']:+.2f} | {r['avg_pnl_eur']:+.3f} | "
                     f"{r['max_drawdown_eur']:.2f} | {r['blocked_pct']}% |\n")
    lines.append("\n")

    winner_id, winner = sorted_agg[0]
    lines.append(f"## 🏆 Winnaar: **{winner_id}. {winner['strategy']}**\n\n")
    lines.append(f"- €{winner['total_pnl_eur']:+.2f} totaal over 6 maanden × 6 markten\n")
    lines.append(f"- {winner['trades']} trades met {winner['win_rate']}% win-rate\n")
    lines.append(f"- Max drawdown: €{winner['max_drawdown_eur']:.2f}\n\n")

    lines.append("## Per markt detail (winnaar-strategie)\n\n")
    lines.append("| Markt | Trades | Win% | PnL € | DD € |\n|---|---:|---:|---:|---:|\n")
    for m in meta["markten"]:
        if m in per_market:
            r = per_market[m][winner_id]
            lines.append(f"| {m} | {r['trades']} | {r['win_rate']}% | "
                         f"{r['total_pnl_eur']:+.2f} | {r['max_drawdown_eur']:.2f} |\n")
    lines.append("\n")

    lines.append("## Interpretatie\n\n")
    baseline = agg["A"]
    lines.append(f"- **Baseline (A)** produceerde €{baseline['total_pnl_eur']:+.2f} met "
                 f"{baseline['trades']} trades — dit is het referentiepunt.\n")
    for sid in ["B", "C", "D", "E"]:
        r = agg[sid]
        diff = r["total_pnl_eur"] - baseline["total_pnl_eur"]
        lines.append(f"- **{sid} ({r['strategy']})**: PnL {diff:+.2f}€ vs baseline, "
                     f"{r['trades']} trades ({r['blocked_pct']}% van BUY-signalen geblokkeerd door gap-filter)\n")
    for sid in ["F", "G", "H"]:
        r = agg[sid]
        diff = r["total_pnl_eur"] - baseline["total_pnl_eur"]
        lines.append(f"- **{sid} ({r['strategy']})** [OPTIMALISATIE]: PnL {diff:+.2f}€ vs baseline, "
                     f"{r['trades']} trades\n")
    lines.append(f"\n**Data structureel opgeslagen** in `data/trade/backtests/{meta['run_id']}/` "
                 f"met `_meta.json` (Willem's SoT-regel).\n")
    (run_dir / "REPORT.md").write_text("".join(lines), encoding="utf-8")
    # Ook een kopie in test_reports voor snel zichtbaar
    Path(f"/app/test_reports/backtest_v2_{meta['run_id']}.md").write_text("".join(lines), encoding="utf-8")


def write_console_summary(agg):
    print("\n" + "=" * 90, file=sys.stderr)
    print(f"{'#':<3} {'Strategie':<50} {'Trades':>6} {'Win%':>6} {'PnL €':>8} {'Blok%':>6}", file=sys.stderr)
    print("=" * 90, file=sys.stderr)
    for sid, r in sorted(agg.items(), key=lambda x: -x[1]["total_pnl_eur"]):
        print(f"{sid:<3} {r['strategy']:<50} {r['trades']:>6} {r['win_rate']:>5.1f}% "
              f"€{r['total_pnl_eur']:>+7.2f} {r['blocked_pct']:>5.1f}%", file=sys.stderr)


if __name__ == "__main__":
    run_dir = main()
    print(f"\n[done] {run_dir}", file=sys.stderr)
