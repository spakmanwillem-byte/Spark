#!/bin/bash
# 1H INTERVAL TEST
# Test Bollinger Bands + Trailing Stop strategie op 1h BCH candles
# Focus: Observatie van gedrag, niet optimalisatie

API_URL=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d '=' -f2)
USER_ID="user-001"
COIN="BCH"
INTERVAL="1h"

echo "=========================================="
echo "🧪 1H INTERVAL STRATEGY TEST"
echo "=========================================="
echo ""
echo "Configuratie:"
echo "  Coin:           BCH"
echo "  Interval:       1h"
echo "  BB Period:      20"
echo "  BB StdDev:      2"
echo "  Trade Amount:   €5"
echo "  Trailing:       +1% activate, -0.4% trigger"
echo ""
echo "Doel: Observeer gedrag, niet optimaliseren"
echo "=========================================="
echo ""

# Fetch 100 candles (4+ days of data)
echo "📍 Fetching 100 x 1h BCH candles (~4 dagen)..."
CANDLES_JSON=$(curl -s "${API_URL}/api/bitvavo/candles?market=BCH-EUR&interval=${INTERVAL}&limit=100")

CANDLE_COUNT=$(echo $CANDLES_JSON | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('candles', [])))")

if [ "$CANDLE_COUNT" -eq "0" ]; then
    echo "❌ Failed to fetch candles"
    exit 1
fi

echo "✅ Fetched $CANDLE_COUNT candles"
echo ""

# Start run
echo "📍 Starting run..."
START_RESPONSE=$(curl -s -X POST "${API_URL}/api/bitvavo/live-monitor/start?user_id=${USER_ID}&coin=${COIN}" \
  -H "Content-Type: application/json" \
  -d '{"bb_period": 20, "bb_std_dev": 2, "trade_amount": 5.0, "trailing_profit": 0.01, "trailing_stop": 0.004, "max_loss_lock": 0.03}')

RUN_ID=$(echo $START_RESPONSE | python3 -c "import sys,json; print(json.load(sys.stdin).get('run_id', ''))")
echo "✅ Run: $RUN_ID"
echo ""

# Process candles
echo "📍 Processing $CANDLE_COUNT candles..."
echo ""

python3 << PYEOF
import json
import sys
from datetime import datetime
sys.path.append('/app/backend')

from services.spark_decision_engine import SparkDecisionEngine, PositionState

candles_data = json.loads('''$CANDLES_JSON''')
candles = candles_data.get('candles', [])

with open('/app/backend/data/wallet/replay_logs/${RUN_ID}.json', 'r') as f:
    run_log = json.load(f)

config = run_log['config']
position_state = PositionState()
trading_locked = False

# Stats tracking
buy_signals = 0
sell_signals = 0
positions_opened = []
positions_closed = []
max_position_duration = 0
total_pnl = 0.0

print(f"Processing {len(candles)} 1h candles...")
print("=" * 80)
print()

for i, candle in enumerate(candles):
    context = candles[:i]
    
    decision = SparkDecisionEngine.analyze_candle(
        candle=candle,
        context=context,
        config=config,
        position_state=position_state,
        trading_locked=trading_locked
    )
    
    # Track signals
    if decision['action'] == 'BUY':
        buy_signals += 1
        positions_opened.append({
            'candle_index': i,
            'timestamp': candle['timestamp'],
            'price': float(candle['close']),
            'reason': decision['reason']
        })
        print(f"🟢 Candle {i+1:3d}/100: BUY at €{float(candle['close']):.2f}")
        if decision.get('indicators', {}).get('bb'):
            bb = decision['indicators']['bb']
            print(f"   BB: Lower=€{bb['lower']:.2f}, Price=€{decision['indicators']['price']:.2f}, Upper=€{bb['upper']:.2f}")
            print(f"   Reason: {decision['reason']}")
    
    elif decision['action'] == 'SELL':
        sell_signals += 1
        pnl = decision.get('pnl', {})
        positions_closed.append({
            'candle_index': i,
            'timestamp': candle['timestamp'],
            'price': float(candle['close']),
            'pnl_eur': pnl.get('pnl_eur', 0),
            'pnl_percent': pnl.get('pnl_percent', 0),
            'reason': decision['reason']
        })
        total_pnl += pnl.get('pnl_eur', 0)
        
        # Calculate position duration
        if positions_opened:
            duration = i - positions_opened[-1]['candle_index']
            max_position_duration = max(max_position_duration, duration)
        
        print(f"🔴 Candle {i+1:3d}/100: SELL at €{float(candle['close']):.2f}")
        print(f"   P&L: €{pnl.get('pnl_eur', 0):.2f} ({pnl.get('pnl_percent', 0):.2f}%)")
        print(f"   Reason: {decision['reason']}")
    
    # Update state
    if decision.get('position_update'):
        saved_state = decision['position_update']
        if saved_state.get('position_type') != 'NONE':
            position_state.position_type = saved_state['position_type']
            position_state.entry_price = saved_state['entry_price']
            position_state.entry_time = saved_state['entry_time']
            position_state.highest_price = saved_state['highest_price']
            position_state.trailing_stop_active = saved_state.get('trailing_stop_active', False)
        else:
            position_state.exit_position()
    
    if decision.get('lock_triggered'):
        trading_locked = True
        print(f"⚠️  Candle {i+1:3d}/100: TRADING LOCK ACTIVATED")
    
    # Append to log
    run_log['candles'].append(candle)
    run_log['decisions_v1'].append({'timestamp': candle['timestamp'], **decision})
    run_log['position_state'] = decision.get('position_update', position_state.to_dict())
    run_log['trading_locked'] = trading_locked

# Save
with open('/app/backend/data/wallet/replay_logs/${RUN_ID}.json', 'w') as f:
    json.dump(run_log, f, indent=2)

print()
print("=" * 80)
print("📊 STRATEGY BEHAVIOR ANALYSIS (1h interval)")
print("=" * 80)
print()
print(f"Total Candles:        {len(candles)}")
print(f"BUY Signals:          {buy_signals}")
print(f"SELL Signals:         {sell_signals}")
print(f"Positions Opened:     {len(positions_opened)}")
print(f"Positions Closed:     {len(positions_closed)}")
print()

if positions_closed:
    print("Closed Positions:")
    for i, pos in enumerate(positions_closed, 1):
        print(f"  {i}. P&L: €{pos['pnl_eur']:.2f} ({pos['pnl_percent']:.2f}%)")
        print(f"     Reason: {pos['reason'][:70]}")
    print()
    
    avg_pnl = total_pnl / len(positions_closed)
    print(f"Total P&L:            €{total_pnl:.2f}")
    print(f"Average P&L/trade:    €{avg_pnl:.2f}")

print()
print(f"Max Position Duration: {max_position_duration} candles (~{max_position_duration} hours)")
print()

if trading_locked:
    print("⚠️  Trading Lock Activated (loss > 3%)")
print()

# Trailing Stop Analysis
trailing_activations = sum(1 for pos in positions_closed if 'trailing stop' in pos['reason'].lower())
print("Trailing Stop Behavior:")
print(f"  Activations:         {trailing_activations}/{len(positions_closed)}")
if len(positions_closed) > 0:
    print(f"  Hit Rate:            {trailing_activations/len(positions_closed)*100:.1f}%")
print()

print("=" * 80)
print("OBSERVATIONS:")
print("=" * 80)
print()

# Observations
if buy_signals == 0:
    print("⚠️  No BUY signals triggered - BB bands may be too wide or price too stable")
elif buy_signals > 10:
    print("⚠️  Many BUY signals - May indicate choppy market or tight bands")
else:
    print(f"✅ {buy_signals} BUY signals - Reasonable frequency for 1h interval")

if len(positions_closed) > 0:
    avg_duration = sum([positions_closed[i]['candle_index'] - positions_opened[i]['candle_index'] 
                        for i in range(len(positions_closed))]) / len(positions_closed)
    print(f"✅ Avg position duration: {avg_duration:.1f} hours")
    
    if avg_duration < 2:
        print("⚠️  Positions closing quickly - Trailing stop (0.4%) may be TOO TIGHT")
    elif avg_duration > 24:
        print("⚠️  Long position durations - Consider if trailing stop is too loose")

if total_pnl < 0:
    print(f"⚠️  Negative total P&L: €{total_pnl:.2f}")
    print("    → Strategy underperforming in this period")
elif total_pnl > 0:
    print(f"✅ Positive total P&L: €{total_pnl:.2f}")

print()

PYEOF

echo ""
echo "=========================================="
echo "Test Complete"
echo "=========================================="
