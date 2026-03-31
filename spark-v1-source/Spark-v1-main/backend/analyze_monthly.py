#!/usr/bin/env python3
"""
Monthly Breakdown Analysis
Kijk per maand waar baseline vs Filter A verschilt
"""

import sys
sys.path.insert(0, '/app/backend')

import requests
import time
from datetime import datetime
from collections import defaultdict
from services.spark_decision_engine import SparkDecisionEngine, PositionState

def fetch_candles_batch(coin, interval, end_time, limit=1000):
    """Fetch batch"""
    market = f"{coin}-EUR"
    url = f"https://api.bitvavo.com/v2/{market}/candles"
    params = {"interval": interval, "limit": limit, "end": end_time}
    
    response = requests.get(url, params=params)
    if response.status_code != 200:
        return None
    
    candles = []
    for c in response.json():
        candles.append({
            "timestamp": c[0],
            "open": float(c[1]),
            "high": float(c[2]),
            "low": float(c[3]),
            "close": float(c[4]),
            "volume": float(c[5])
        })
    return candles

def fetch_full_data(coin="BCH", interval="1h"):
    """Fetch zo veel mogelijk data"""
    print(f"🔄 Fetching maximum BCH data ({interval})...")
    
    all_candles = []
    current_time = int(time.time() * 1000)
    
    for i in range(5):
        print(f"  Batch {i+1}...")
        batch = fetch_candles_batch(coin, interval, current_time, 1000)
        if not batch:
            break
        all_candles = batch + all_candles
        current_time = batch[0]["timestamp"] - 1
        time.sleep(0.5)
    
    print(f"✅ Fetched {len(all_candles)} candles")
    return all_candles

def run_baseline_logic(candle, context, position_state, trading_locked):
    """Baseline: RSI optional, 0.2%"""
    config = SparkDecisionEngine.DEFAULT_CONFIG
    all_candles = context + [candle]
    prices = [float(c["close"]) for c in all_candles]
    current_price = float(candle["close"])
    
    bb = SparkDecisionEngine.calculate_bollinger_bands(prices, config["bb_period"], config["bb_std_dev"])
    
    action = "HOLD"
    pnl_eur = 0.0
    
    if bb is None:
        return action, pnl_eur, position_state, trading_locked
    
    # Trailing stop
    if position_state.position_type == "LONG":
        stop_trigger = position_state.update_trailing_stop(current_price)
        if stop_trigger == "TRIGGER_STOP":
            pnl = position_state.calculate_pnl(current_price)
            pnl_eur = pnl.get("pnl_eur", 0)
            position_state.exit_position()
            return "SELL", pnl_eur, position_state, trading_locked
    
    # Max loss check
    if position_state.position_type == "LONG":
        pnl = position_state.calculate_pnl(current_price)
        if pnl["pnl_percent"] <= -config["max_loss_lock"]:
            pnl_eur = pnl.get("pnl_eur", 0)
            position_state.exit_position()
            trading_locked = True
            return "SELL", pnl_eur, position_state, trading_locked
    
    # BUY
    if position_state.position_type == "NONE" and not trading_locked:
        if current_price <= bb["lower"] * 1.002:
            position_state.enter_position("LONG", current_price, candle["timestamp"])
            return "BUY", 0.0, position_state, trading_locked
    
    # SELL at upper
    if position_state.position_type == "LONG":
        if current_price >= bb["upper"] * 0.998:
            pnl = position_state.calculate_pnl(current_price)
            pnl_eur = pnl.get("pnl_eur", 0)
            position_state.exit_position()
            return "SELL", pnl_eur, position_state, trading_locked
    
    return action, 0.0, position_state, trading_locked

def run_filtered_logic(candle, context, position_state, trading_locked):
    """Filter A: RSI required, 0.1%"""
    config = SparkDecisionEngine.DEFAULT_CONFIG
    all_candles = context + [candle]
    prices = [float(c["close"]) for c in all_candles]
    current_price = float(candle["close"])
    
    bb = SparkDecisionEngine.calculate_bollinger_bands(prices, config["bb_period"], config["bb_std_dev"])
    rsi = SparkDecisionEngine.calculate_rsi(prices, 14)
    
    action = "HOLD"
    pnl_eur = 0.0
    
    if bb is None:
        return action, pnl_eur, position_state, trading_locked
    
    # Trailing stop
    if position_state.position_type == "LONG":
        stop_trigger = position_state.update_trailing_stop(current_price)
        if stop_trigger == "TRIGGER_STOP":
            pnl = position_state.calculate_pnl(current_price)
            pnl_eur = pnl.get("pnl_eur", 0)
            position_state.exit_position()
            return "SELL", pnl_eur, position_state, trading_locked
    
    # Max loss check
    if position_state.position_type == "LONG":
        pnl = position_state.calculate_pnl(current_price)
        if pnl["pnl_percent"] <= -config["max_loss_lock"]:
            pnl_eur = pnl.get("pnl_eur", 0)
            position_state.exit_position()
            trading_locked = True
            return "SELL", pnl_eur, position_state, trading_locked
    
    # BUY (filtered)
    if position_state.position_type == "NONE" and not trading_locked:
        if current_price <= bb["lower"] * 1.001:
            if rsi and rsi < 40:
                position_state.enter_position("LONG", current_price, candle["timestamp"])
                return "BUY", 0.0, position_state, trading_locked
    
    # SELL at upper
    if position_state.position_type == "LONG":
        if current_price >= bb["upper"] * 0.998:
            pnl = position_state.calculate_pnl(current_price)
            pnl_eur = pnl.get("pnl_eur", 0)
            position_state.exit_position()
            return "SELL", pnl_eur, position_state, trading_locked
    
    return action, 0.0, position_state, trading_locked

def run_monthly_backtest(candles, logic_func, name):
    """Run backtest met monthly breakdown"""
    position_state = PositionState()
    trading_locked = False
    
    monthly_stats = defaultdict(lambda: {"trades": 0, "wins": 0, "pnl": 0.0, "locks": 0})
    
    for i, candle in enumerate(candles):
        context = candles[max(0, i-100):i]
        action, pnl_eur, position_state, trading_locked = logic_func(candle, context, position_state, trading_locked)
        
        month_key = datetime.fromtimestamp(candle["timestamp"]/1000).strftime("%Y-%m")
        
        if action == "SELL":
            monthly_stats[month_key]["trades"] += 1
            monthly_stats[month_key]["pnl"] += pnl_eur
            if pnl_eur > 0:
                monthly_stats[month_key]["wins"] += 1
            
            # Reset lock after sell
            if trading_locked:
                monthly_stats[month_key]["locks"] += 1
                trading_locked = False
    
    return dict(monthly_stats)

if __name__ == "__main__":
    print("\n" + "="*80)
    print("📊 MONTHLY BREAKDOWN ANALYSIS")
    print("="*80)
    
    candles = fetch_full_data("BCH", "1h")
    
    if len(candles) < 100:
        print("❌ Insufficient data")
        sys.exit(1)
    
    start = datetime.fromtimestamp(candles[0]["timestamp"]/1000).strftime("%Y-%m-%d")
    end = datetime.fromtimestamp(candles[-1]["timestamp"]/1000).strftime("%Y-%m-%d")
    
    print(f"\n📅 Dataset: {start} → {end} ({len(candles)} candles, {len(candles)/24:.0f} days)")
    print(f"💰 Market: €{candles[0]['close']:.2f} → €{candles[-1]['close']:.2f} ({((candles[-1]['close']-candles[0]['close'])/candles[0]['close']*100):+.2f}%)")
    
    print("\n🤖 Running analysis...")
    baseline_monthly = run_monthly_backtest(candles, run_baseline_logic, "Baseline")
    filtered_monthly = run_monthly_backtest(candles, run_filtered_logic, "Filter A")
    
    # Get all months
    all_months = sorted(set(list(baseline_monthly.keys()) + list(filtered_monthly.keys())))
    
    print("\n" + "="*80)
    print("📊 MONTHLY COMPARISON")
    print("="*80)
    print(f"\n{'Month':<12} {'Baseline Trades':>15} {'Baseline PnL':>15} {'Filter A Trades':>15} {'Filter A PnL':>15} {'Delta PnL':>12}")
    print("-"*80)
    
    total_baseline_pnl = 0.0
    total_filtered_pnl = 0.0
    total_baseline_trades = 0
    total_filtered_trades = 0
    
    for month in all_months:
        b = baseline_monthly.get(month, {"trades": 0, "pnl": 0.0, "wins": 0})
        f = filtered_monthly.get(month, {"trades": 0, "pnl": 0.0, "wins": 0})
        
        delta = f["pnl"] - b["pnl"]
        winner = "✅" if delta > 0 else "❌" if delta < 0 else "="
        
        total_baseline_pnl += b["pnl"]
        total_filtered_pnl += f["pnl"]
        total_baseline_trades += b["trades"]
        total_filtered_trades += f["trades"]
        
        pnl_baseline_str = f"€{b['pnl']:>6.2f}"
        pnl_filtered_str = f"€{f['pnl']:>6.2f}"
        delta_str = f"€{delta:>6.2f}"
        
        print(f"{month:<12} {b['trades']:>8} ({b['wins']}/{b['trades']}) {pnl_baseline_str:>15} {f['trades']:>8} ({f['wins']}/{f['trades']}) {pnl_filtered_str:>15} {delta_str:>9} {winner}")
    
    total_str_b = f"€{total_baseline_pnl:>6.2f}"
    total_str_f = f"€{total_filtered_pnl:>6.2f}"
    delta_total_str = f"€{total_filtered_pnl - total_baseline_pnl:>6.2f}"
    
    print("-"*80)
    print(f"{'TOTAL':<12} {total_baseline_trades:>15} {total_str_b:>15} {total_filtered_trades:>15} {total_str_f:>15} {delta_total_str:>12}")
    
    # Summary
    baseline_winrate = sum([m["wins"] for m in baseline_monthly.values()]) / max(total_baseline_trades, 1) * 100
    filtered_winrate = sum([m["wins"] for m in filtered_monthly.values()]) / max(total_filtered_trades, 1) * 100
    
    print("\n" + "="*80)
    print("📈 SUMMARY")
    print("="*80)
    print(f"Baseline:  {total_baseline_trades} trades, {baseline_winrate:.1f}% winrate, €{total_baseline_pnl:.2f} total PnL")
    print(f"Filter A:  {total_filtered_trades} trades, {filtered_winrate:.1f}% winrate, €{total_filtered_pnl:.2f} total PnL")
    print()
    
    months_won_baseline = sum([1 for m in all_months if baseline_monthly.get(m, {}).get("pnl", 0) > filtered_monthly.get(m, {}).get("pnl", 0)])
    months_won_filtered = sum([1 for m in all_months if filtered_monthly.get(m, {}).get("pnl", 0) > baseline_monthly.get(m, {}).get("pnl", 0)])
    
    print(f"Months won by Baseline: {months_won_baseline}/{len(all_months)}")
    print(f"Months won by Filter A: {months_won_filtered}/{len(all_months)}")
    print("="*80)
