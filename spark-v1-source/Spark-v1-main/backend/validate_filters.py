#!/usr/bin/env python3
"""
Validation Test - Baseline vs Filter Set A
Test op VERSCHILLENDE periodes voor consistency check
"""

import sys
sys.path.insert(0, '/app/backend')

import requests
import re
from services.spark_decision_engine import SparkDecisionEngine, PositionState

def fetch_historical_candles(coin="BCH", interval="15m", limit=672, start_time=None):
    """Fetch historical candles met optional start time"""
    market = f"{coin}-EUR"
    url = f"https://api.bitvavo.com/v2/{market}/candles"
    params = {"interval": interval, "limit": limit}
    
    if start_time:
        params["start"] = start_time
    
    response = requests.get(url, params=params)
    if response.status_code != 200:
        print(f"❌ Error: {response.status_code}")
        return None
    
    candles = response.json()
    formatted = []
    for c in candles:
        formatted.append({
            "timestamp": c[0],
            "open": float(c[1]),
            "high": float(c[2]),
            "low": float(c[3]),
            "close": float(c[4]),
            "volume": float(c[5])
        })
    
    return formatted


def run_baseline_logic(candle, context, position_state, trading_locked):
    """OLD LOGIC: RSI optional, 0.2% BB tolerance"""
    config = SparkDecisionEngine.DEFAULT_CONFIG
    
    all_candles = context + [candle]
    prices = [float(c["close"]) for c in all_candles]
    current_price = float(candle["close"])
    
    bb = SparkDecisionEngine.calculate_bollinger_bands(prices, config["bb_period"], config["bb_std_dev"])
    rsi = SparkDecisionEngine.calculate_rsi(prices, 14)
    
    action = "HOLD"
    pnl_eur = 0.0
    
    if bb is None:
        return action, pnl_eur, position_state
    
    # Trailing stop check
    if position_state.position_type == "LONG":
        stop_trigger = position_state.update_trailing_stop(current_price)
        if stop_trigger == "TRIGGER_STOP":
            pnl = position_state.calculate_pnl(current_price)
            pnl_eur = pnl.get("pnl_eur", 0)
            position_state.exit_position()
            return "SELL", pnl_eur, position_state
    
    # BUY logic (BASELINE: RSI optional, 0.2% tolerance)
    if position_state.position_type == "NONE" and not trading_locked:
        if current_price <= bb["lower"] * 1.002:  # 0.2%
            action = "BUY"
            position_state.enter_position("LONG", current_price, candle["timestamp"])
            return action, 0.0, position_state
    
    # SELL logic
    if position_state.position_type == "LONG":
        if current_price >= bb["upper"] * 0.998:
            pnl = position_state.calculate_pnl(current_price)
            pnl_eur = pnl.get("pnl_eur", 0)
            position_state.exit_position()
            return "SELL", pnl_eur, position_state
    
    return action, 0.0, position_state


def run_filtered_logic(candle, context, position_state, trading_locked):
    """NEW LOGIC: RSI required, 0.1% BB tolerance"""
    config = SparkDecisionEngine.DEFAULT_CONFIG
    
    all_candles = context + [candle]
    prices = [float(c["close"]) for c in all_candles]
    current_price = float(candle["close"])
    
    bb = SparkDecisionEngine.calculate_bollinger_bands(prices, config["bb_period"], config["bb_std_dev"])
    rsi = SparkDecisionEngine.calculate_rsi(prices, 14)
    
    action = "HOLD"
    pnl_eur = 0.0
    
    if bb is None:
        return action, pnl_eur, position_state
    
    # Trailing stop check
    if position_state.position_type == "LONG":
        stop_trigger = position_state.update_trailing_stop(current_price)
        if stop_trigger == "TRIGGER_STOP":
            pnl = position_state.calculate_pnl(current_price)
            pnl_eur = pnl.get("pnl_eur", 0)
            position_state.exit_position()
            return "SELL", pnl_eur, position_state
    
    # BUY logic (FILTERED: RSI required, 0.1% tolerance)
    if position_state.position_type == "NONE" and not trading_locked:
        if current_price <= bb["lower"] * 1.001:  # 0.1%
            if rsi and rsi < 40:  # REQUIRED
                action = "BUY"
                position_state.enter_position("LONG", current_price, candle["timestamp"])
                return action, 0.0, position_state
    
    # SELL logic
    if position_state.position_type == "LONG":
        if current_price >= bb["upper"] * 0.998:
            pnl = position_state.calculate_pnl(current_price)
            pnl_eur = pnl.get("pnl_eur", 0)
            position_state.exit_position()
            return "SELL", pnl_eur, position_state
    
    return action, 0.0, position_state


def run_backtest(candles, logic_func, name):
    """Run backtest met specifieke logic"""
    position_state = PositionState()
    trading_locked = False
    
    trades = []
    total_pnl = 0.0
    
    for i, candle in enumerate(candles):
        context = candles[max(0, i-100):i]
        action, pnl_eur, position_state = logic_func(candle, context, position_state, trading_locked)
        
        if action == "BUY":
            trades.append({"type": "BUY", "price": candle["close"]})
        elif action == "SELL":
            trades.append({"type": "SELL", "price": candle["close"], "pnl": pnl_eur})
            total_pnl += pnl_eur
    
    sells = [t for t in trades if t["type"] == "SELL"]
    wins = [t for t in sells if t.get("pnl", 0) > 0]
    losses = [t for t in sells if t.get("pnl", 0) <= 0]
    
    return {
        "name": name,
        "total_trades": len(sells),
        "wins": len(wins),
        "losses": len(losses),
        "winrate": (len(wins) / len(sells) * 100) if sells else 0,
        "total_pnl": total_pnl,
        "roi": (total_pnl / (len([t for t in trades if t["type"] == "BUY"]) * 5) * 100) if trades else 0
    }


def print_comparison(period_name, results_baseline, results_filtered, candles):
    """Print vergelijking"""
    print("\n" + "="*70)
    print(f"📊 VALIDATION: {period_name}")
    print("="*70)
    print(f"Dataset: {len(candles)} candles (15m)")
    print(f"Start: €{candles[0]['close']:.2f}")
    print(f"End:   €{candles[-1]['close']:.2f}")
    print(f"Market: {((candles[-1]['close'] - candles[0]['close']) / candles[0]['close'] * 100):+.2f}%")
    print()
    
    print(f"{'Metric':<20} {'Baseline':<15} {'Filter Set A':<15} {'Delta':<15}")
    print("-"*70)
    print(f"{'Trades':<20} {results_baseline['total_trades']:<15} {results_filtered['total_trades']:<15} {results_filtered['total_trades'] - results_baseline['total_trades']:+}")
    print(f"{'Winrate':<20} {results_baseline['winrate']:<15.1f}% {results_filtered['winrate']:<15.1f}% {results_filtered['winrate'] - results_baseline['winrate']:+.1f}%")
    print(f"{'Total PnL':<20} €{results_baseline['total_pnl']:<14.2f} €{results_filtered['total_pnl']:<14.2f} €{results_filtered['total_pnl'] - results_baseline['total_pnl']:+.2f}")
    print(f"{'ROI':<20} {results_baseline['roi']:<15.2f}% {results_filtered['roi']:<15.2f}% {results_filtered['roi'] - results_baseline['roi']:+.2f}%")
    print("="*70)
    
    # Quick verdict
    improvements = 0
    if results_filtered['winrate'] > results_baseline['winrate']:
        improvements += 1
    if results_filtered['total_pnl'] > results_baseline['total_pnl']:
        improvements += 1
    if results_filtered['roi'] > results_baseline['roi']:
        improvements += 1
    
    if improvements >= 2:
        print("✅ Filter Set A performs BETTER")
    elif improvements == 1:
        print("⚠️  Mixed results")
    else:
        print("❌ Baseline performs better")
    print()


if __name__ == "__main__":
    print("\n🔄 Fetching historical data for validation...")
    
    # Get current timestamp
    response = requests.get("https://api.bitvavo.com/v2/BCH-EUR/candles", params={"interval": "15m", "limit": 1})
    current_time = response.json()[0][0]
    
    # Period 1: Recent data (laatste 28 dagen)
    print("\n📅 Period 1: Recent (last ~28 days)")
    candles_recent = fetch_historical_candles("BCH", "15m", 672)
    
    if candles_recent:
        results_baseline_p1 = run_backtest(candles_recent, run_baseline_logic, "Baseline")
        results_filtered_p1 = run_backtest(candles_recent, run_filtered_logic, "Filter Set A")
        print_comparison("Period 1 (Recent)", results_baseline_p1, results_filtered_p1, candles_recent)
    
    # Period 2: 2 months earlier (different market conditions)
    print("\n📅 Period 2: 2 Months Earlier")
    two_months_ago = current_time - (60 * 24 * 60 * 60 * 1000)  # 60 days
    
    url = "https://api.bitvavo.com/v2/BCH-EUR/candles"
    params = {"interval": "15m", "limit": 672, "end": two_months_ago}
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        candles_data = response.json()
        candles_earlier = []
        for c in candles_data:
            candles_earlier.append({
                "timestamp": c[0],
                "open": float(c[1]),
                "high": float(c[2]),
                "low": float(c[3]),
                "close": float(c[4]),
                "volume": float(c[5])
            })
        
        results_baseline_p2 = run_backtest(candles_earlier, run_baseline_logic, "Baseline")
        results_filtered_p2 = run_backtest(candles_earlier, run_filtered_logic, "Filter Set A")
        print_comparison("Period 2 (2 Months Earlier)", results_baseline_p2, results_filtered_p2, candles_earlier)
    else:
        print("⚠️  Could not fetch earlier period data")
    
    print("\n" + "="*70)
    print("📊 OVERALL VALIDATION SUMMARY")
    print("="*70)
    print("If Filter Set A is consistently better across both periods,")
    print("then improvements are VALIDATED and not period-specific.")
    print("="*70)
