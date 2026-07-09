"""Backtest v3 — Stress + Contrarian + Event-analyse.

Extra strategieën t.o.v. v2:
  I. Random buy 50% (chaos baseline)
  J. Buy-and-hold (single BUY at start)
  K. Inverse Bollinger (breakout: BUY bij upper band, SELL bij lower)
  L. All-red panic (5+ rode candles → BUY)
  M. All-green profit-take (5+ groene → SELL forced)
  N. Volume-weighted (BUY alleen als volume > 1.5× gem)
  O. Adaptive sigma (2σ default, 3σ als recent volatiel, 1.5σ als rustig)

Extra analyse:
  - Event-detection: periodes met >5% daily drop → per-strategie prestatie
  - Marktregime-detectie: bull/bear/range → welke strategie waar
  - Correlatie tussen markten (voor diversificatie-advies)
"""
from __future__ import annotations

import json
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

BITVAVO_URL = "https://api.bitvavo.com/v2"
MARKETS = ["BCH-EUR", "BTC-EUR", "ETH-EUR", "SOL-EUR", "ADA-EUR", "ATOM-EUR"]
INTERVAL = "15m"
DAYS = 180
LIMIT_PER_CALL = 1440
TRADE_AMOUNT_EUR = 10.0
BITVAVO_FEE = 0.0025
CACHE_DIR = Path("/tmp/candles_cache")


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
            print(f"[fetch] {market}: {e}", file=sys.stderr)
            break
    seen = set()
    unique = sorted(
        [c for c in all_candles if c["timestamp"] not in seen and not seen.add(c["timestamp"])],
        key=lambda x: x["timestamp"]
    )
    cache_file.write_text(json.dumps(unique))
    return unique


# ============================================================
# DECISION-ENGINES (per strategie custom)
# ============================================================

def std_of(values):
    if len(values) < 2:
        return 0.001
    m = sum(values) / len(values)
    v = sum((x - m) ** 2 for x in values) / len(values)
    return v ** 0.5 or 0.001


class Position:
    __slots__ = ["entry_price", "entry_idx", "entry_ts", "highest_price", "trailing_active"]
    def __init__(self, price, idx, ts):
        self.entry_price = price
        self.entry_idx = idx
        self.entry_ts = ts
        self.highest_price = price
        self.trailing_active = False


def default_sell(window, position: Position, allow_break_even=False) -> bool:
    """Standaard fee-aware trailing exit. Return True = SELL."""
    price = window[-1]["close"]
    position.highest_price = max(position.highest_price, window[-1]["high"])
    entry = position.entry_price
    profit_pct = (price - entry) / entry
    fees = TRADE_AMOUNT_EUR * BITVAVO_FEE * 2
    netto = TRADE_AMOUNT_EUR * profit_pct - fees
    if not position.trailing_active and netto >= 2 * fees:
        position.trailing_active = True
    if position.trailing_active:
        drop = (position.highest_price - price) / position.highest_price
        if drop >= 0.004:
            if netto > 0.01 or (allow_break_even and netto >= -fees):
                return True
    return False


# ---- Strategieën ----

def strat_A_baseline(window, pos, i, extra=None):
    """Bollinger 2σ (baseline)"""
    if pos:
        return "SELL" if default_sell(window, pos) else "HOLD"
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
    """Bollinger 2σ + gap-body 50%"""
    if pos:
        return "SELL" if default_sell(window, pos) else "HOLD"
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


def strat_I_random(window, pos, i, extra=None):
    """Random buy: 1/288 kans (elke cycle 0.35% kans = ~1 per 3 dagen)"""
    if pos:
        return "SELL" if default_sell(window, pos) else "HOLD"
    return "BUY" if random.random() < 1 / 288 else "HOLD"


def strat_J_buy_hold(window, pos, i, extra=None):
    """1 BUY aan begin, SELL nooit (of alleen op laatste candle)"""
    if pos:
        # Verkoop alleen op laatste candle
        if i == extra.get("last_idx"):
            return "SELL"
        return "HOLD"
    if i == 30:  # eerste beslissings-kans
        return "BUY"
    return "HOLD"


def strat_K_inverse(window, pos, i, extra=None):
    """Inverse Bollinger: BUY bij UPPER (breakout), SELL bij LOWER (reversal)"""
    if len(window) < 20:
        return "HOLD"
    closes = [c["close"] for c in window[-20:]]
    mean = sum(closes) / 20
    std = std_of(closes)
    upper = mean + 2 * std
    lower = mean - 2 * std
    price = window[-1]["close"]
    if pos:
        # SELL bij lower band (breakout gefaald)
        if price < lower:
            return "SELL"
        # Ook default fee-aware trailing
        return "SELL" if default_sell(window, pos) else "HOLD"
    # BUY bij upper band breakout
    if price > upper:
        return "BUY"
    return "HOLD"


def strat_L_all_red(window, pos, i, extra=None):
    """5+ opeenvolgende rode candles → BUY (extreme oversold)"""
    if pos:
        return "SELL" if default_sell(window, pos) else "HOLD"
    if len(window) < 5:
        return "HOLD"
    last5 = window[-5:]
    if all(c["close"] < c["open"] for c in last5):
        return "BUY"
    return "HOLD"


def strat_M_all_green(window, pos, i, extra=None):
    """Baseline BUY, maar 5+ groene = geforceerde SELL (winst nemen)"""
    if pos and len(window) >= 5:
        last5 = window[-5:]
        if all(c["close"] > c["open"] for c in last5):
            # Force sell — check als winst >0
            entry = pos.entry_price
            price = window[-1]["close"]
            netto = TRADE_AMOUNT_EUR * (price - entry) / entry - TRADE_AMOUNT_EUR * BITVAVO_FEE * 2
            if netto > 0.01:
                return "SELL"
    return strat_A_baseline(window, pos, i)


def strat_N_volume(window, pos, i, extra=None):
    """Baseline BUY, maar alleen als volume > 1.5× gemiddelde"""
    if pos:
        return "SELL" if default_sell(window, pos) else "HOLD"
    if strat_A_baseline(window, None, i) != "BUY":
        return "HOLD"
    if len(window) < 20:
        return "HOLD"
    vols = [c["volume"] for c in window[-20:]]
    avg = sum(vols) / 20
    if window[-1]["volume"] >= 1.5 * avg:
        return "BUY"
    return "HOLD"


def strat_O_adaptive(window, pos, i, extra=None):
    """Adaptive sigma: 3σ bij hoge volatiliteit, 1.5σ bij lage"""
    if pos:
        return "SELL" if default_sell(window, pos) else "HOLD"
    if len(window) < 20:
        return "HOLD"
    closes = [c["close"] for c in window[-20:]]
    mean = sum(closes) / 20
    std = std_of(closes)
    # Volatiliteit: std / mean als ratio
    vol_ratio = std / mean if mean else 0
    if vol_ratio > 0.02:  # >2% = hoog
        sigma = 3.0
    elif vol_ratio < 0.005:  # <0.5% = laag
        sigma = 1.5
    else:
        sigma = 2.0
    lower = mean - sigma * std
    price = window[-1]["close"]
    window_high = max(closes[-10:])
    drop = (window_high - price) / window_high if window_high > 0 else 0
    if price < lower and drop >= 0.01:
        return "BUY"
    return "HOLD"


STRATEGIES = [
    ("A", "Bollinger 2σ (baseline)", strat_A_baseline),
    ("D", "Bollinger 2σ + gap-body (winnaar v2)", strat_D_gap_body),
    ("I", "Random buy (chaos-baseline)", strat_I_random),
    ("J", "Buy-and-hold (1× kopen, houden)", strat_J_buy_hold),
    ("K", "Inverse Bollinger (breakout-buy)", strat_K_inverse),
    ("L", "All-red panic (5× rood → BUY)", strat_L_all_red),
    ("M", "Baseline + all-green profit-take", strat_M_all_green),
    ("N", "Baseline + volume-weighted (>1.5×)", strat_N_volume),
    ("O", "Adaptive sigma (1.5/2/3 dynamic)", strat_O_adaptive),
]


# ============================================================
# EVENT-DETECTIE (Willem's oorlog-vraag)
# ============================================================

def detect_events(candles: List[Dict], threshold_pct: float = 5.0) -> List[Dict]:
    """Detecteer 'shock-events': periodes waarin prijs >5% daalde binnen 24 uur (96 candles)"""
    events = []
    for i in range(96, len(candles)):
        window = candles[i - 96:i]
        high = max(c["high"] for c in window)
        low = min(c["low"] for c in window[-24:])  # laatste 6 uur = 24 × 15m
        if high > 0:
            drop_pct = (high - low) / high * 100
            if drop_pct >= threshold_pct:
                events.append({
                    "idx_start": i - 96, "idx_end": i,
                    "ts_start": window[0]["timestamp"],
                    "ts_end": candles[i]["timestamp"],
                    "high_price": round(high, 4),
                    "low_price": round(low, 4),
                    "drop_pct": round(drop_pct, 2),
                })
    # Dedupe: overlappende events samenvoegen
    merged = []
    for e in events:
        if merged and e["idx_start"] < merged[-1]["idx_end"]:
            merged[-1]["idx_end"] = max(merged[-1]["idx_end"], e["idx_end"])
            merged[-1]["ts_end"] = max(merged[-1]["ts_end"], e["ts_end"])
            merged[-1]["drop_pct"] = max(merged[-1]["drop_pct"], e["drop_pct"])
        else:
            merged.append(e)
    return merged


def detect_regime(candles: List[Dict], idx: int, window: int = 96) -> str:
    """Bull/Bear/Range voor gegeven index (kijkt naar laatste 24u = 96 candles)"""
    if idx < window:
        return "unknown"
    slice_ = candles[idx - window:idx + 1]
    start = slice_[0]["close"]
    end = slice_[-1]["close"]
    change_pct = (end - start) / start * 100
    if change_pct > 2:
        return "bull"
    if change_pct < -2:
        return "bear"
    return "range"


# ============================================================
# SIMULATIE (uniform voor alle strategieën)
# ============================================================

def simulate(candles: List[Dict], strat_fn, extra_ctx: Dict = None) -> Dict:
    extra = extra_ctx or {}
    extra["last_idx"] = len(candles) - 1
    trades = []
    position: Optional[Position] = None
    equity = [0.0]
    WINDOW = 30
    regime_trades = {"bull": [], "bear": [], "range": []}
    event_trades = {"in_event": [], "out_event": []}
    event_idxs = extra.get("event_idxs", set())

    for i in range(WINDOW, len(candles)):
        window = candles[i - WINDOW:i + 1]
        action = strat_fn(window, position, i, extra)

        if action == "BUY" and not position:
            position = Position(window[-1]["close"], i, window[-1]["timestamp"])

        elif action == "SELL" and position:
            entry = position.entry_price
            exit_p = window[-1]["close"]
            gross = TRADE_AMOUNT_EUR * (exit_p - entry) / entry
            fees = TRADE_AMOUNT_EUR * BITVAVO_FEE * 2
            netto = gross - fees
            trade = {
                "entry_ts": position.entry_ts, "exit_ts": window[-1]["timestamp"],
                "entry_price": round(entry, 4), "exit_price": round(exit_p, 4),
                "net_pnl": round(netto, 4), "hold_bars": i - position.entry_idx,
                "win": netto > 0,
                "regime": detect_regime(candles, position.entry_idx),
                "in_event": position.entry_idx in event_idxs,
            }
            trades.append(trade)
            regime_trades[trade["regime"] if trade["regime"] in regime_trades else "range"].append(trade)
            event_trades["in_event" if trade["in_event"] else "out_event"].append(trade)
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

    # Per-regime PnL
    regime_pnl = {k: {"trades": len(v), "pnl": round(sum(t["net_pnl"] for t in v), 2)}
                  for k, v in regime_trades.items()}
    event_pnl = {k: {"trades": len(v), "pnl": round(sum(t["net_pnl"] for t in v), 2)}
                 for k, v in event_trades.items()}

    return {
        "trades": n, "wins": wins, "losses": n - wins,
        "win_rate": round(100 * wins / n, 1) if n else 0,
        "total_pnl_eur": round(total, 2),
        "avg_pnl_eur": round(total / n, 3) if n else 0,
        "max_drawdown_eur": round(dd, 2),
        "open_at_end": position is not None,
        "regime_pnl": regime_pnl,
        "event_pnl": event_pnl,
    }


# ============================================================
# MARKT-CORRELATIE
# ============================================================

def compute_correlation(all_candles: Dict[str, List[Dict]]) -> Dict:
    """Pearson correlation matrix op 15m closes."""
    # Align by timestamp: neem alleen candles met timestamps in ALLE markten
    markets = list(all_candles.keys())
    ts_sets = [set(c["timestamp"] for c in all_candles[m]) for m in markets]
    common_ts = sorted(set.intersection(*ts_sets))
    aligned = {m: {} for m in markets}
    for m in markets:
        for c in all_candles[m]:
            if c["timestamp"] in aligned[m] or c["timestamp"] not in common_ts:
                continue
            aligned[m][c["timestamp"]] = c["close"]
    # Corr matrix
    from statistics import mean
    matrix = {}
    for m1 in markets:
        matrix[m1] = {}
        for m2 in markets:
            if m1 == m2:
                matrix[m1][m2] = 1.0
                continue
            a = [aligned[m1][ts] for ts in common_ts if ts in aligned[m1] and ts in aligned[m2]]
            b = [aligned[m2][ts] for ts in common_ts if ts in aligned[m1] and ts in aligned[m2]]
            if len(a) < 100:
                matrix[m1][m2] = None
                continue
            ma, mb = mean(a), mean(b)
            num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
            den = (sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b)) ** 0.5
            matrix[m1][m2] = round(num / den, 3) if den else None
    return matrix


# ============================================================
# MAIN
# ============================================================

def main():
    random.seed(42)  # reproduceerbare "random" strategie
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_dir = Path(f"/app/backend/data/trade/backtests/{run_id}_v3")
    run_dir.mkdir(parents=True, exist_ok=True)

    print(f"[v3] {run_id} — {len(MARKETS)} markten × {len(STRATEGIES)} strategieën", file=sys.stderr)

    # 1) Fetch alles
    all_candles = {}
    for m in MARKETS:
        print(f"[fetch] {m}...", file=sys.stderr)
        cs = fetch_candles(m, INTERVAL, DAYS)
        if cs:
            all_candles[m] = cs
            print(f"  {len(cs)} candles", file=sys.stderr)

    # 2) Events + regimes per markt
    events_per_market = {}
    for m, cs in all_candles.items():
        events_per_market[m] = detect_events(cs, threshold_pct=5.0)

    # 3) Correlatie tussen markten
    corr = compute_correlation(all_candles)

    # 4) Simulaties per markt × strategie
    results = {}
    for m, cs in all_candles.items():
        event_idxs = set()
        for ev in events_per_market[m]:
            for i in range(ev["idx_start"], ev["idx_end"] + 1):
                event_idxs.add(i)
        results[m] = {}
        for sid, sname, sfn in STRATEGIES:
            r = simulate(cs, sfn, extra_ctx={"event_idxs": event_idxs})
            results[m][sid] = {"strategy": sname, **r}

    # 5) Aggregeer
    agg = {}
    for sid, sname, _ in STRATEGIES:
        total_trades = sum(results[m][sid]["trades"] for m in results)
        total_wins = sum(results[m][sid]["wins"] for m in results)
        total_pnl = sum(results[m][sid]["total_pnl_eur"] for m in results)
        max_dd = max((results[m][sid]["max_drawdown_eur"] for m in results), default=0)
        # Regime aggregate
        bull_pnl = sum(results[m][sid]["regime_pnl"]["bull"]["pnl"] for m in results)
        bear_pnl = sum(results[m][sid]["regime_pnl"]["bear"]["pnl"] for m in results)
        range_pnl = sum(results[m][sid]["regime_pnl"]["range"]["pnl"] for m in results)
        # Event aggregate
        in_event_pnl = sum(results[m][sid]["event_pnl"]["in_event"]["pnl"] for m in results)
        out_event_pnl = sum(results[m][sid]["event_pnl"]["out_event"]["pnl"] for m in results)
        in_event_trades = sum(results[m][sid]["event_pnl"]["in_event"]["trades"] for m in results)
        out_event_trades = sum(results[m][sid]["event_pnl"]["out_event"]["trades"] for m in results)
        agg[sid] = {
            "strategy": sname, "trades": total_trades, "wins": total_wins,
            "win_rate": round(100 * total_wins / total_trades, 1) if total_trades else 0,
            "total_pnl_eur": round(total_pnl, 2),
            "avg_pnl_eur": round(total_pnl / total_trades, 3) if total_trades else 0,
            "max_drawdown_eur": round(max_dd, 2),
            "regime": {"bull": round(bull_pnl, 2), "bear": round(bear_pnl, 2), "range": round(range_pnl, 2)},
            "event": {
                "in_event_pnl": round(in_event_pnl, 2), "out_event_pnl": round(out_event_pnl, 2),
                "in_event_trades": in_event_trades, "out_event_trades": out_event_trades,
            },
        }

    # 6) Opslag
    meta = {
        "run_id": run_id, "created_at": datetime.now(timezone.utc).isoformat(),
        "doel": "Stress + contrarian + event-analyse. Test onze aannames en zoek onverwachte winners.",
        "extra_analyse": "Event-detection (>5% daily drop), regime-detection (bull/bear/range), inter-market correlatie",
        "markten": MARKETS, "periode_dagen": DAYS, "candle_interval": INTERVAL,
        "trade_bedrag_eur": TRADE_AMOUNT_EUR, "fee_pct": BITVAVO_FEE,
        "strategieën": [{"id": s[0], "name": s[1]} for s in STRATEGIES],
        "vorige_run_ref": "20260709_205003",
        "footnote": {"kb_kaart_ref": "kbv2-2f55a485", "code_ref": "backend/tests/backtest_v3.py"},
    }
    (run_dir / "_meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    (run_dir / "aggregate.json").write_text(json.dumps(agg, indent=2, ensure_ascii=False))
    (run_dir / "per_market.json").write_text(json.dumps(results, indent=2, ensure_ascii=False))
    (run_dir / "events.json").write_text(json.dumps(events_per_market, indent=2, ensure_ascii=False))
    (run_dir / "correlation.json").write_text(json.dumps(corr, indent=2, ensure_ascii=False))

    # Update index
    idx_file = Path("/app/backend/data/trade/backtests/_meta.json")
    idx = json.loads(idx_file.read_text()) if idx_file.exists() else {"_type": "backtest_index", "runs": []}
    idx["runs"].append({"run_id": run_id, "type": "v3_stress", "doel": meta["doel"],
                        "path": f"backtests/{run_id}_v3/"})
    idx["laatst_bijgewerkt"] = meta["created_at"]
    idx_file.write_text(json.dumps(idx, indent=2, ensure_ascii=False))

    # Report
    write_report_v3(agg, results, events_per_market, corr, run_dir, meta)

    # Console
    print("\n" + "=" * 100, file=sys.stderr)
    print(f"{'#':<3}{'Strategie':<45}{'Trades':>7}{'Win%':>7}{'PnL €':>9}{'Bull':>7}{'Bear':>7}{'Range':>7}", file=sys.stderr)
    print("=" * 100, file=sys.stderr)
    for sid, r in sorted(agg.items(), key=lambda x: -x[1]["total_pnl_eur"]):
        rg = r["regime"]
        print(f"{sid:<3}{r['strategy']:<45}{r['trades']:>7}{r['win_rate']:>6.1f}%€{r['total_pnl_eur']:>+7.2f}"
              f"€{rg['bull']:>+5.2f}€{rg['bear']:>+5.2f}€{rg['range']:>+5.2f}", file=sys.stderr)
    print(f"\n[done] {run_dir}", file=sys.stderr)
    return run_dir


def write_report_v3(agg, results, events, corr, run_dir, meta):
    lines = [f"# Trader Backtest v3 — Stress + Contrarian + Event\n\n"]
    lines.append(f"- Run: `{meta['run_id']}` — {meta['periode_dagen']} dagen × {len(meta['markten'])} markten\n\n")

    lines.append("## Aggregaat (gesorteerd op PnL)\n\n")
    lines.append("| # | Strategie | Trades | Win% | PnL € | Bull | Bear | Range |\n")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|\n")
    for sid, r in sorted(agg.items(), key=lambda x: -x[1]["total_pnl_eur"]):
        rg = r["regime"]
        lines.append(f"| **{sid}** | {r['strategy']} | {r['trades']} | {r['win_rate']}% | "
                     f"€{r['total_pnl_eur']:+.2f} | €{rg['bull']:+.2f} | €{rg['bear']:+.2f} | €{rg['range']:+.2f} |\n")
    lines.append("\n")

    lines.append("## 🌪 Event-analyse (>5% daily drop periodes)\n\n")
    total_events = sum(len(ev) for ev in events.values())
    lines.append(f"- Gedetecteerd: **{total_events} shock-events** over 6 markten × 6 maanden\n")
    for m, ev_list in events.items():
        if ev_list:
            worst = max(ev_list, key=lambda e: e["drop_pct"])
            lines.append(f"  - {m}: {len(ev_list)} events, ergste −{worst['drop_pct']}%\n")
    lines.append("\n### Per-strategie in-event vs out-event\n\n")
    lines.append("| # | Strategie | In-event PnL | In-event trades | Out-event PnL | Out-event trades |\n")
    lines.append("|---|---|---:|---:|---:|---:|\n")
    for sid, r in sorted(agg.items(), key=lambda x: -x[1]["total_pnl_eur"]):
        e = r["event"]
        lines.append(f"| {sid} | {r['strategy']} | €{e['in_event_pnl']:+.2f} | {e['in_event_trades']} | "
                     f"€{e['out_event_pnl']:+.2f} | {e['out_event_trades']} |\n")
    lines.append("\n")

    lines.append("## 🔀 Markt-correlatie (Pearson op 15m closes)\n\n")
    lines.append("| | " + " | ".join(MARKETS) + " |\n")
    lines.append("|---|" + "---|" * len(MARKETS) + "\n")
    for m1 in MARKETS:
        row = f"| **{m1}** |"
        for m2 in MARKETS:
            v = corr.get(m1, {}).get(m2)
            row += f" {v:+.2f} |" if v is not None else " – |"
        lines.append(row + "\n")
    lines.append("\n**Interpretatie**: dichter bij +1.0 = markten bewegen samen (minder diversificatie). ")
    lines.append("Dichter bij 0 of negatief = onafhankelijk (goed voor risico-spreiding).\n\n")

    lines.append("## 🎯 Winnaar & aanbeveling\n\n")
    winner_id = max(agg, key=lambda k: agg[k]["total_pnl_eur"])
    w = agg[winner_id]
    lines.append(f"**{winner_id}. {w['strategy']}** — €{w['total_pnl_eur']:+.2f} met {w['trades']} trades\n\n")
    lines.append("Regime-analyse toont dat strategieën in **bull/bear/range** verschillend presteren. ")
    lines.append("Adaptive keuze per regime = mogelijk volgende stap.\n")

    (run_dir / "REPORT.md").write_text("".join(lines), encoding="utf-8")
    Path(f"/app/test_reports/backtest_v3_{meta['run_id']}.md").write_text("".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
