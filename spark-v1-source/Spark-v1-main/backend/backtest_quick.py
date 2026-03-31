#!/usr/bin/env python3
"""
Quick Backtest Script - BCH Decision Engine
Fetch historische data en run decision engine voor snelle stats
"""

import sys
import os
import re
sys.path.insert(0, '/app/backend')

import requests
from services.spark_decision_engine import SparkDecisionEngine, PositionState

def fetch_historical_candles(coin="BCH", interval="1h", limit=168):
    """Fetch historical candles van Bitvavo"""
    market = f"{coin}-EUR"
    url = f"https://api.bitvavo.com/v2/{market}/candles"
    params = {"interval": interval, "limit": limit}
    
    response = requests.get(url, params=params)
    if response.status_code != 200:
        print(f"❌ Error fetching data: {response.status_code}")
        sys.exit(1)
    
    candles = response.json()
    
    # Convert Bitvavo format to our format
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


def run_backtest(candles, config=None):
    """Run decision engine over alle candles"""
    if config is None:
        config = SparkDecisionEngine.DEFAULT_CONFIG
    
    position_state = PositionState()
    trading_locked = False
    
    trades = []
    decisions = []
    total_pnl = 0.0
    
    for i, candle in enumerate(candles):
        # Context = alle vorige candles
        context = candles[max(0, i-100):i]  # Max 100 voor BB berekening
        
        # Run decision engine
        decision = SparkDecisionEngine.analyze_candle(
            candle=candle,
            context=context,
            config=config,
            position_state=position_state,
            trading_locked=trading_locked
        )
        
        decisions.append({
            "timestamp": candle["timestamp"],
            "price": candle["close"],
            "action": decision["action"],
            "reason": decision["reason"],
            "pnl": decision.get("pnl", {})
        })
        
        # Track trades
        if decision["action"] == "BUY":
            trades.append({
                "type": "BUY",
                "price": candle["close"],
                "timestamp": candle["timestamp"]
            })
        elif decision["action"] == "SELL":
            # Parse PnL from reason string (engine resets after exit)
            reason = decision["reason"]
            match = re.search(r'P&L: €([-\d.]+) \(([-+\d.]+)%\)', reason)
            
            pnl_eur = 0.0
            pnl_pct = 0.0
            if match:
                pnl_eur = float(match.group(1))
                pnl_pct = float(match.group(2))
            
            trades.append({
                "type": "SELL",
                "price": candle["close"],
                "timestamp": candle["timestamp"],
                "pnl": {"pnl_eur": pnl_eur, "pnl_percent": pnl_pct}
            })
            
            # Add to total PnL
            total_pnl += pnl_eur
        
        # Check for trading lock
        if decision.get("lock_triggered"):
            trading_locked = True
    
    return {
        "trades": trades,
        "decisions": decisions,
        "total_pnl": total_pnl,
        "position_state": position_state
    }


def calculate_stats(result):
    """Bereken trading stats"""
    trades = result["trades"]
    
    # Count buy/sell
    buys = [t for t in trades if t["type"] == "BUY"]
    sells = [t for t in trades if t["type"] == "SELL"]
    
    # Calculate wins/losses
    wins = [s for s in sells if s.get("pnl", {}).get("pnl_eur", 0) > 0]
    losses = [s for s in sells if s.get("pnl", {}).get("pnl_eur", 0) <= 0]
    
    winrate = (len(wins) / len(sells) * 100) if len(sells) > 0 else 0
    
    # Average win/loss
    avg_win = sum([s["pnl"]["pnl_eur"] for s in wins]) / len(wins) if wins else 0
    avg_loss = sum([s["pnl"]["pnl_eur"] for s in losses]) / len(losses) if losses else 0
    
    return {
        "total_trades": len(sells),
        "buys": len(buys),
        "sells": len(sells),
        "wins": len(wins),
        "losses": len(losses),
        "winrate": winrate,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "total_pnl": result["total_pnl"]
    }


def print_results(stats, candles):
    """Print results mooi geformatteerd"""
    print("\n" + "="*60)
    print("🧪 BCH BACKTEST RESULTS")
    print("="*60)
    print(f"📊 Dataset: {len(candles)} candles")
    print(f"📅 Periode: ~{len(candles)} uur ({len(candles)//24} dagen)")
    print(f"💰 Start: €{candles[0]['close']:.2f}")
    print(f"💰 End:   €{candles[-1]['close']:.2f}")
    print(f"📈 Change: {((candles[-1]['close'] - candles[0]['close']) / candles[0]['close'] * 100):.2f}%")
    print()
    print("🎯 TRADING PERFORMANCE")
    print("-"*60)
    print(f"Total Trades:  {stats['total_trades']}")
    print(f"  BUYs:        {stats['buys']}")
    print(f"  SELLs:       {stats['sells']}")
    print()
    print(f"✅ Wins:        {stats['wins']} ({stats['winrate']:.1f}%)")
    print(f"❌ Losses:      {stats['losses']} ({100-stats['winrate']:.1f}%)")
    print()
    print(f"💰 Total PnL:   {'€' if stats['total_pnl'] >= 0 else '-€'}{abs(stats['total_pnl']):.2f}")
    
    if stats['total_pnl'] != 0:
        # Calculate ROI (based on €5 per trade)
        total_invested = stats['buys'] * 5
        roi = (stats['total_pnl'] / total_invested * 100) if total_invested > 0 else 0
        print(f"📊 ROI:         {roi:+.2f}%")
    
    if stats['avg_win'] > 0:
        print(f"📈 Avg Win:     €{stats['avg_win']:.2f}")
    if stats['avg_loss'] < 0:
        print(f"📉 Avg Loss:    €{stats['avg_loss']:.2f}")
    
    print("="*60)
    print()


if __name__ == "__main__":
    # Parse arguments
    coin = sys.argv[1] if len(sys.argv) > 1 else "BCH"
    interval = sys.argv[2] if len(sys.argv) > 2 else "1h"
    days = int(sys.argv[3]) if len(sys.argv) > 3 else 7
    
    limit = days * 24 if interval == "1h" else days * 24 * 12 if interval == "5m" else days * 24 * 4
    
    print(f"\n🔄 Fetching {days} days of {coin} data ({interval} interval)...")
    candles = fetch_historical_candles(coin, interval, limit)
    print(f"✅ Fetched {len(candles)} candles")
    
    print(f"\n🤖 Running decision engine...")
    result = run_backtest(candles)
    
    print(f"✅ Analysis complete")
    
    stats = calculate_stats(result)
    print_results(stats, candles)
    
    # Optional: Save detailed results
    if "--save" in sys.argv:
        import json
        output_file = f"/tmp/backtest_{coin}_{interval}_{days}d.json"
        with open(output_file, 'w') as f:
            json.dump({
                "stats": stats,
                "trades": result["trades"][:20],  # First 20 trades
                "config": SparkDecisionEngine.DEFAULT_CONFIG
            }, f, indent=2)
        print(f"💾 Detailed results saved to: {output_file}")
