#!/usr/bin/env python3
"""
Long-term Validation - 6 Months
Test Filter Set A over extended period voor degradation check
"""

import sys
sys.path.insert(0, '/app/backend')

import requests
import time
from datetime import datetime
from services.spark_decision_engine import SparkDecisionEngine, PositionState

def fetch_candles_batch(coin, interval, end_time, limit=1000):
    """Fetch batch of candles ending at specific time"""
    market = f"{coin}-EUR"
    url = f"https://api.bitvavo.com/v2/{market}/candles"
    params = {"interval": interval, "limit": limit, "end": end_time}
    
    response = requests.get(url, params=params)
    if response.status_code != 200:
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


def fetch_6_months_data(coin="BCH", interval="1h"):
    """
    Fetch 6 months of data in batches
    1h interval × 6 months = ~4320 candles
    Need multiple API calls (max 1000 per call)
    """
    print(f"🔄 Fetching 6 months of {coin} data ({interval})...")
    
    all_candles = []
    
    # Start from now and work backwards
    current_time = int(time.time() * 1000)
    
    # Fetch in batches of 1000 candles
    batches_needed = 5  # 5 × 1000 = 5000 candles (~7 months for safety)
    
    for i in range(batches_needed):
        print(f"  Fetching batch {i+1}/{batches_needed}...")
        batch = fetch_candles_batch(coin, interval, current_time, 1000)
        
        if batch is None or len(batch) == 0:
            print(f"  ⚠️  No more data available")
            break
        
        all_candles = batch + all_candles  # Prepend (oldest first)
        current_time = batch[0]["timestamp"] - 1  # Move to before oldest candle
        
        time.sleep(0.5)  # Rate limit friendly
    
    print(f"✅ Fetched {len(all_candles)} candles total")
    
    # Keep only last 6 months (~4320 candles for 1h)
    target_candles = 24 * 180  # 6 months in hours
    if len(all_candles) > target_candles:
        all_candles = all_candles[-target_candles:]
        print(f"📊 Using last {len(all_candles)} candles (6 months)")
    
    return all_candles


def run_baseline_logic(candle, context, position_state, trading_locked):
    """Baseline: RSI optional, 0.2% BB"""
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
    
    # Trailing stop
    if position_state.position_type == "LONG":
        stop_trigger = position_state.update_trailing_stop(current_price)
        if stop_trigger == "TRIGGER_STOP":
            pnl = position_state.calculate_pnl(current_price)
            pnl_eur = pnl.get("pnl_eur", 0)
            position_state.exit_position()
            return "SELL", pnl_eur, position_state
    
    # BUY (baseline)
    if position_state.position_type == "NONE" and not trading_locked:
        if current_price <= bb["lower"] * 1.002:  # 0.2%
            position_state.enter_position("LONG", current_price, candle["timestamp"])
            return "BUY", 0.0, position_state
    
    # SELL
    if position_state.position_type == "LONG":
        if current_price >= bb["upper"] * 0.998:
            pnl = position_state.calculate_pnl(current_price)
            pnl_eur = pnl.get("pnl_eur", 0)
            position_state.exit_position()
            return "SELL", pnl_eur, position_state
    
    return action, 0.0, position_state


def run_filtered_logic(candle, context, position_state, trading_locked):
    """Filter Set A: RSI required, 0.1% BB"""
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
    
    # Trailing stop
    if position_state.position_type == "LONG":
        stop_trigger = position_state.update_trailing_stop(current_price)
        if stop_trigger == "TRIGGER_STOP":
            pnl = position_state.calculate_pnl(current_price)
            pnl_eur = pnl.get("pnl_eur", 0)
            position_state.exit_position()
            return "SELL", pnl_eur, position_state
    
    # BUY (filtered)
    if position_state.position_type == "NONE" and not trading_locked:
        if current_price <= bb["lower"] * 1.001:  # 0.1%
            if rsi and rsi < 40:  # REQUIRED
                position_state.enter_position("LONG", current_price, candle["timestamp"])
                return "BUY", 0.0, position_state
    
    # SELL
    if position_state.position_type == "LONG":
        if current_price >= bb["upper"] * 0.998:
            pnl = position_state.calculate_pnl(current_price)
            pnl_eur = pnl.get("pnl_eur", 0)
            position_state.exit_position()
            return "SELL", pnl_eur, position_state
    
    return action, 0.0, position_state


def run_backtest(candles, logic_func, name):
    """Run backtest"""
    position_state = PositionState()
    trading_locked = False
    
    trades = []
    total_pnl = 0.0
    
    print(f"\n🤖 Running {name}...")
    
    for i, candle in enumerate(candles):
        context = candles[max(0, i-100):i]
        action, pnl_eur, position_state = logic_func(candle, context, position_state, trading_locked)
        
        if action == "BUY":
            trades.append({"type": "BUY", "price": candle["close"]})
        elif action == "SELL":
            trades.append({"type": "SELL", "price": candle["close"], "pnl": pnl_eur})
            total_pnl += pnl_eur
        
        if (i + 1) % 1000 == 0:
            print(f"  Progress: {i+1}/{len(candles)} candles...")
    
    sells = [t for t in trades if t["type"] == "SELL"]
    wins = [t for t in sells if t.get("pnl", 0) > 0]
    
    return {
        "name": name,
        "total_trades": len(sells),
        "wins": len(wins),
        "losses": len(sells) - len(wins),
        "winrate": (len(wins) / len(sells) * 100) if sells else 0,
        "total_pnl": total_pnl,
        "roi": (total_pnl / (len([t for t in trades if t["type"] == "BUY"]) * 5) * 100) if trades else 0
    }


if __name__ == "__main__":
    print("\n" + "="*70)
    print("📊 LONG-TERM VALIDATION: 6 MONTHS")
    print("="*70)
    
    # Fetch 6 months data
    candles = fetch_6_months_data("BCH", "1h")
    
    if not candles or len(candles) < 100:
        print("❌ Insufficient data")
        sys.exit(1)
    
    # Print dataset info
    start_date = datetime.fromtimestamp(candles[0]["timestamp"]/1000).strftime("%Y-%m-%d")
    end_date = datetime.fromtimestamp(candles[-1]["timestamp"]/1000).strftime("%Y-%m-%d")
    market_change = ((candles[-1]["close"] - candles[0]["close"]) / candles[0]["close"]) * 100
    
    print(f"\n📅 Dataset:")
    print(f"  Period: {start_date} → {end_date}")
    print(f"  Candles: {len(candles)} (1h interval)")
    print(f"  Days: {len(candles) / 24:.0f}")
    print(f"  Start Price: €{candles[0]['close']:.2f}")
    print(f"  End Price: €{candles[-1]['close']:.2f}")
    print(f"  Market Change: {market_change:+.2f}%")
    
    # Run backtests
    print("\n" + "="*70)
    results_baseline = run_backtest(candles, run_baseline_logic, "Baseline")
    results_filtered = run_backtest(candles, run_filtered_logic, "Filter Set A")
    
    # Print comparison
    print("\n" + "="*70)
    print("📊 RESULTS COMPARISON (6 Months)")
    print("="*70)
    
    print(f"\n{'Metric':<20} {'Baseline':<15} {'Filter Set A':<15} {'Delta':<15}")
    print("-"*70)
    print(f"{'Total Trades':<20} {results_baseline['total_trades']:<15} {results_filtered['total_trades']:<15} {results_filtered['total_trades'] - results_baseline['total_trades']:+}")
    print(f"{'Wins':<20} {results_baseline['wins']:<15} {results_filtered['wins']:<15} {results_filtered['wins'] - results_baseline['wins']:+}")
    print(f"{'Losses':<20} {results_baseline['losses']:<15} {results_filtered['losses']:<15} {results_filtered['losses'] - results_baseline['losses']:+}")
    print(f"{'Winrate':<20} {results_baseline['winrate']:<15.1f}% {results_filtered['winrate']:<15.1f}% {results_filtered['winrate'] - results_baseline['winrate']:+.1f}%")
    print(f"{'Total PnL':<20} €{results_baseline['total_pnl']:<14.2f} €{results_filtered['total_pnl']:<14.2f} €{results_filtered['total_pnl'] - results_baseline['total_pnl']:+.2f}")
    print(f"{'ROI':<20} {results_baseline['roi']:<15.2f}% {results_filtered['roi']:<15.2f}% {results_filtered['roi'] - results_baseline['roi']:+.2f}%")
    
    # Calculate average per trade
    avg_baseline = results_baseline['total_pnl'] / results_baseline['total_trades'] if results_baseline['total_trades'] > 0 else 0
    avg_filtered = results_filtered['total_pnl'] / results_filtered['total_trades'] if results_filtered['total_trades'] > 0 else 0
    
    print(f"{'Avg per Trade':<20} €{avg_baseline:<14.3f} €{avg_filtered:<14.3f} €{avg_filtered - avg_baseline:+.3f}")
    
    print("="*70)
    
    # Verdict
    print("\n🔍 LONG-TERM CONSISTENCY CHECK:")
    
    improvements = 0
    if results_filtered['winrate'] > results_baseline['winrate']:
        print(f"  ✅ Winrate improved: {results_baseline['winrate']:.1f}% → {results_filtered['winrate']:.1f}%")
        improvements += 1
    else:
        print(f"  ❌ Winrate degraded: {results_baseline['winrate']:.1f}% → {results_filtered['winrate']:.1f}%")
    
    if results_filtered['total_pnl'] > results_baseline['total_pnl']:
        print(f"  ✅ Total PnL improved: €{results_baseline['total_pnl']:.2f} → €{results_filtered['total_pnl']:.2f}")
        improvements += 1
    else:
        print(f"  ❌ Total PnL degraded: €{results_baseline['total_pnl']:.2f} → €{results_filtered['total_pnl']:.2f}")
    
    if results_filtered['roi'] > results_baseline['roi']:
        print(f"  ✅ ROI improved: {results_baseline['roi']:.2f}% → {results_filtered['roi']:.2f}%")
        improvements += 1
    else:
        print(f"  ❌ ROI degraded: {results_baseline['roi']:.2f}% → {results_filtered['roi']:.2f}%")
    
    print("\n" + "="*70)
    if improvements >= 2:
        print("✅ VALIDATION PASSED - Filter Set A remains superior over 6 months")
        print("   Filters do NOT degrade over time. Ready for production!")
    else:
        print("⚠️  VALIDATION MIXED - Review results carefully")
    print("="*70)
