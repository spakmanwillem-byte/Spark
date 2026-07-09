"""Backtest van trader-strategieën op historische Bitvavo BCH-EUR data.

Vergelijkt 4 varianten over 6 maanden 15m candles:
  A: Bollinger-only (huidig zonder gap-filter)
  B: Bollinger + gap-streng (v7: curr.low > prev.high)
  C: Bollinger + gap-los (curr.close > prev.high)
  D: Bollinger + N-red-then-green (Neef's variant, N=3)

Uitvoer: markdown rapport in /app/test_reports/backtest_bch_YYYYMMDD.md
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import requests

# Zodat we _simple_decision uit monitor.py kunnen hergebruiken
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from modules.trade.monitor import _simple_decision  # type: ignore

BITVAVO_URL = "https://api.bitvavo.com/v2"
MARKET = "BCH-EUR"
INTERVAL = "15m"
INTERVAL_MS = 15 * 60 * 1000  # ms per candle
DAYS = 180
LIMIT_PER_CALL = 1440

TRADE_AMOUNT_EUR = 10.0  # €10 per potje (realistisch)
BITVAVO_FEE = 0.0025  # 0.25% maker/taker


def fetch_candles_paginated(market: str, interval: str, days: int) -> List[Dict]:
    """Haal N dagen candles op via pagination (bitvavo 'end' param, in ms)."""
    now_ms = int(time.time() * 1000)
    start_ms = now_ms - (days * 24 * 60 * 60 * 1000)
    all_candles: List[Dict] = []
    end_ms = now_ms
    calls = 0
    while end_ms > start_ms:
        url = f"{BITVAVO_URL}/{market}/candles?interval={interval}&limit={LIMIT_PER_CALL}&end={end_ms}"
        try:
            r = requests.get(url, timeout=15)
            r.raise_for_status()
            raw = r.json()
            if not raw:
                break
            batch = []
            for c in raw:
                if len(c) >= 6:
                    batch.append({
                        "timestamp": c[0],
                        "open": float(c[1]),
                        "high": float(c[2]),
                        "low": float(c[3]),
                        "close": float(c[4]),
                        "volume": float(c[5]),
                    })
            if not batch:
                break
            all_candles.extend(batch)
            calls += 1
            # Bitvavo returns newest-first → oldest is last in batch
            oldest = min(c["timestamp"] for c in batch)
            if oldest <= start_ms or oldest >= end_ms:
                break
            end_ms = oldest - 1
            time.sleep(0.1)  # gentle rate-limit
        except Exception as e:
            print(f"[fetch] error at end_ms={end_ms}: {e}", file=sys.stderr)
            break
    # sort chronologisch (oldest first)
    all_candles.sort(key=lambda x: x["timestamp"])
    # dedupe by timestamp
    seen = set()
    unique = []
    for c in all_candles:
        if c["timestamp"] not in seen:
            seen.add(c["timestamp"])
            unique.append(c)
    print(f"[fetch] {calls} calls → {len(unique)} unieke candles "
          f"({datetime.fromtimestamp(unique[0]['timestamp']/1000, tz=timezone.utc):%Y-%m-%d} → "
          f"{datetime.fromtimestamp(unique[-1]['timestamp']/1000, tz=timezone.utc):%Y-%m-%d})", file=sys.stderr)
    return unique


# ============================================================
# GAP-CHECK VARIANTEN
# ============================================================

def gap_streng(prev: Dict, curr: Dict) -> str:
    """v7 huidig: groene candle volledig boven vorige rode."""
    prev_bearish = prev["close"] < prev["open"]
    curr_bullish = curr["close"] > curr["open"]
    if prev_bearish and curr_bullish and curr["low"] > prev["high"]:
        return "BUY"
    return "NONE"


def gap_los(prev: Dict, curr: Dict) -> str:
    """Losser: sluit boven vorige high (mag overlappen op low)."""
    prev_bearish = prev["close"] < prev["open"]
    curr_bullish = curr["close"] > curr["open"]
    if prev_bearish and curr_bullish and curr["close"] > prev["high"]:
        return "BUY"
    return "NONE"


def n_red_then_green(candles: List[Dict], n: int = 3) -> str:
    """Neef's variant: N opeenvolgende rode candles gevolgd door groene."""
    if len(candles) < n + 1:
        return "NONE"
    reds = candles[-(n + 1):-1]
    curr = candles[-1]
    all_red = all(c["close"] < c["open"] for c in reds)
    curr_green = curr["close"] > curr["open"]
    if all_red and curr_green:
        return "BUY"
    return "NONE"


# ============================================================
# SIMULATIE
# ============================================================

class BacktestSim:
    def __init__(self, name: str, gap_filter: Optional[str] = None, n_red: int = 3):
        self.name = name
        self.gap_filter = gap_filter  # None | "streng" | "los" | "n_red"
        self.n_red = n_red
        self.trades: List[Dict] = []
        self.position: Optional[Dict] = None
        self.equity_curve: List[float] = [0.0]  # cumulatieve netto PnL €
        self.blocked_by_gap = 0
        self.allowed_by_gap = 0

    def gap_check(self, window: List[Dict]) -> str:
        if not self.gap_filter or len(window) < 2:
            return "BUY"  # geen filter = altijd doorlaten
        if self.gap_filter == "streng":
            return gap_streng(window[-2], window[-1])
        if self.gap_filter == "los":
            return gap_los(window[-2], window[-1])
        if self.gap_filter == "n_red":
            return n_red_then_green(window, n=self.n_red)
        return "BUY"

    def step(self, window: List[Dict], candle_idx: int):
        """Één candle-stap. window = laatste 20+ candles t/m huidige."""
        if len(window) < 20:
            return

        current_price = window[-1]["close"]

        # Position update?
        if self.position and self.position["is_open"]:
            self.position["highest_price"] = max(self.position["highest_price"], window[-1]["high"])

        # Decision via bestaande engine
        decision = _simple_decision(window, position=self.position, trade_amount=TRADE_AMOUNT_EUR)

        if decision["action"] == "BUY" and (not self.position or not self.position["is_open"]):
            # gap-filter?
            g = self.gap_check(window)
            if g != "BUY":
                self.blocked_by_gap += 1
                return
            self.allowed_by_gap += 1
            self.position = {
                "is_open": True,
                "entry_price": current_price,
                "entry_idx": candle_idx,
                "highest_price": current_price,
                "trailing_active": False,
            }

        elif decision["action"] == "SELL" and self.position and self.position["is_open"]:
            entry = self.position["entry_price"]
            exit_price = current_price
            gross_pnl = TRADE_AMOUNT_EUR * (exit_price - entry) / entry
            fees = TRADE_AMOUNT_EUR * BITVAVO_FEE * 2  # buy + sell fee
            net_pnl = gross_pnl - fees
            hold_bars = candle_idx - self.position["entry_idx"]
            self.trades.append({
                "entry_price": round(entry, 4),
                "exit_price": round(exit_price, 4),
                "entry_ts": window[max(0, len(window) - 1 - hold_bars)]["timestamp"],
                "exit_ts": window[-1]["timestamp"],
                "gross_pnl": round(gross_pnl, 4),
                "net_pnl": round(net_pnl, 4),
                "hold_bars": hold_bars,
                "win": net_pnl > 0,
            })
            self.equity_curve.append(self.equity_curve[-1] + net_pnl)
            self.position = None

    def report(self) -> Dict:
        n = len(self.trades)
        wins = sum(1 for t in self.trades if t["win"])
        total = sum(t["net_pnl"] for t in self.trades)
        avg = total / n if n else 0
        equity_peak = 0
        max_dd = 0
        for e in self.equity_curve:
            if e > equity_peak:
                equity_peak = e
            dd = equity_peak - e
            if dd > max_dd:
                max_dd = dd
        avg_hold = sum(t["hold_bars"] for t in self.trades) / n if n else 0
        return {
            "name": self.name,
            "trades": n,
            "wins": wins,
            "losses": n - wins,
            "win_rate": round(100 * wins / n, 1) if n else 0,
            "total_pnl_eur": round(total, 2),
            "avg_pnl_eur": round(avg, 3),
            "max_drawdown_eur": round(max_dd, 2),
            "avg_hold_bars": round(avg_hold, 1),
            "avg_hold_hours": round(avg_hold * 0.25, 1),  # 15m per bar
            "blocked_by_gap": self.blocked_by_gap,
            "allowed_by_gap": self.allowed_by_gap,
            "open_position_at_end": self.position is not None,
        }


def run_backtest(candles: List[Dict]) -> Dict:
    sims = [
        BacktestSim("A. Bollinger-only", gap_filter=None),
        BacktestSim("B. Bollinger + gap-streng (v7 huidig)", gap_filter="streng"),
        BacktestSim("C. Bollinger + gap-los", gap_filter="los"),
        BacktestSim("D. Bollinger + 3-red-then-green (Neef)", gap_filter="n_red", n_red=3),
    ]

    # Walk-forward: elke stap krijgt window van laatste 30 candles t/m huidige
    WINDOW = 30
    for i in range(WINDOW, len(candles)):
        window = candles[i - WINDOW:i + 1]  # +1 = inclusief huidige
        for sim in sims:
            sim.step(window, i)

    return {
        "market": MARKET,
        "interval": INTERVAL,
        "days_covered": DAYS,
        "n_candles": len(candles),
        "trade_amount_eur": TRADE_AMOUNT_EUR,
        "fee_pct_per_side": BITVAVO_FEE * 100,
        "period_from": datetime.fromtimestamp(candles[0]["timestamp"] / 1000, tz=timezone.utc).isoformat(),
        "period_to": datetime.fromtimestamp(candles[-1]["timestamp"] / 1000, tz=timezone.utc).isoformat(),
        "sims": [s.report() for s in sims],
        "trades_by_sim": {s.name: s.trades[:20] for s in sims},  # eerste 20 per sim voor detail
    }


def write_report(result: Dict, out_path: Path):
    lines = []
    lines.append(f"# Trader Backtest — {result['market']}\n")
    lines.append(f"- Periode: **{result['period_from'][:10]} → {result['period_to'][:10]}** ({result['days_covered']} dagen)\n")
    lines.append(f"- Candles: {result['n_candles']:,} × {result['interval']}\n")
    lines.append(f"- Trade-bedrag per potje: €{result['trade_amount_eur']:.2f}\n")
    lines.append(f"- Fees: {result['fee_pct_per_side']:.2f}% per zijde (buy + sell = 0.50% roundtrip)\n\n")

    lines.append("## Resultaten per strategie\n\n")
    lines.append("| Strategie | Trades | Wins | Losses | Win% | PnL € | Ø/trade € | Max DD € | Ø hold |\n")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|\n")
    for s in result["sims"]:
        lines.append(
            f"| {s['name']} | {s['trades']} | {s['wins']} | {s['losses']} | {s['win_rate']}% | "
            f"{s['total_pnl_eur']:+.2f} | {s['avg_pnl_eur']:+.3f} | {s['max_drawdown_eur']:.2f} | {s['avg_hold_hours']}h |\n"
        )
    lines.append("\n")

    lines.append("## Gap-filter effectiviteit\n\n")
    lines.append("| Strategie | Bollinger BUY toegelaten | Geblokkeerd door gap-filter | % blok |\n")
    lines.append("|---|---:|---:|---:|\n")
    for s in result["sims"]:
        total_attempts = s["allowed_by_gap"] + s["blocked_by_gap"]
        pct = 100 * s["blocked_by_gap"] / total_attempts if total_attempts else 0
        lines.append(f"| {s['name']} | {s['allowed_by_gap']} | {s['blocked_by_gap']} | {pct:.1f}% |\n")
    lines.append("\n")

    # Winnaar bepalen
    best = max(result["sims"], key=lambda s: s["total_pnl_eur"])
    lines.append(f"## 🏆 Winnaar op PnL\n\n**{best['name']}** met €{best['total_pnl_eur']:+.2f} totaal, {best['win_rate']}% win-rate over {best['trades']} trades.\n\n")

    # Kritische observaties
    lines.append("## Observaties\n\n")
    baseline = result["sims"][0]
    for s in result["sims"][1:]:
        diff = s["total_pnl_eur"] - baseline["total_pnl_eur"]
        trade_diff = s["trades"] - baseline["trades"]
        winrate_diff = s["win_rate"] - baseline["win_rate"]
        lines.append(
            f"- **{s['name']}** vs baseline: PnL {diff:+.2f}€, "
            f"{trade_diff:+d} trades, win-rate {winrate_diff:+.1f}pp\n"
        )
    lines.append("\n")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("".join(lines), encoding="utf-8")
    print(f"[report] geschreven: {out_path}", file=sys.stderr)


if __name__ == "__main__":
    print(f"[start] {MARKET} {INTERVAL} {DAYS} dagen ophalen...", file=sys.stderr)
    candles = fetch_candles_paginated(MARKET, INTERVAL, DAYS)
    if not candles:
        print("GEEN CANDLES — abort", file=sys.stderr)
        sys.exit(1)
    print(f"[sim] backtest op {len(candles)} candles...", file=sys.stderr)
    result = run_backtest(candles)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out = Path(f"/app/test_reports/backtest_bch_{ts}.md")
    write_report(result, out)
    # Ook JSON voor Spark-verdere-analyse
    json_out = out.with_suffix(".json")
    json_out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[report] JSON: {json_out}", file=sys.stderr)
    # Console samenvatting
    print("\n=== SAMENVATTING ===", file=sys.stderr)
    for s in result["sims"]:
        print(f"  {s['name']:45s}  trades={s['trades']:4d}  win={s['win_rate']:5.1f}%  PnL=€{s['total_pnl_eur']:+8.2f}  DD=€{s['max_drawdown_eur']:.2f}", file=sys.stderr)
