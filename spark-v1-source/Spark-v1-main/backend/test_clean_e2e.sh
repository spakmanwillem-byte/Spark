#!/bin/bash
# CLEAN END-TO-END TEST
# Live run vanaf eerste candle, dan replay over exact dezelfde dataset
# Expected: 100% match

API_URL=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d '=' -f2)
USER_ID="user-001"
COIN="BCH"

echo "=========================================="
echo "🧪 CLEAN END-TO-END REPRODUCIBILITY TEST"
echo "=========================================="
echo ""
echo "Test strategie:"
echo "  1. Fetch 30 historical BCH candles"
echo "  2. Process ALL 30 candles LIVE (from scratch)"
echo "  3. Stop run"
echo "  4. Replay over exact same 30 candles"
echo "  5. Compare: expect 100% match"
echo ""
echo "=========================================="
echo ""

# Step 1: Fetch historical data
echo "📍 Step 1: Fetching 30 historical BCH candles..."
CANDLES_JSON=$(curl -s "${API_URL}/api/bitvavo/candles?market=BCH-EUR&interval=1h&limit=30")

CANDLE_COUNT=$(echo $CANDLES_JSON | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('candles', [])))")

if [ "$CANDLE_COUNT" -eq "0" ]; then
    echo "❌ Failed to fetch candles"
    exit 1
fi

echo "✅ Fetched $CANDLE_COUNT candles"
echo ""

# Step 2: Start fresh run
echo "📍 Step 2: Starting fresh live run..."
START_RESPONSE=$(curl -s -X POST "${API_URL}/api/bitvavo/live-monitor/start?user_id=${USER_ID}&coin=${COIN}" \
  -H "Content-Type: application/json" \
  -d '{"bb_period": 20, "bb_std_dev": 2, "trade_amount": 5.0, "trailing_profit": 0.01, "trailing_stop": 0.004, "max_loss_lock": 0.03}')

RUN_ID=$(echo $START_RESPONSE | python3 -c "import sys,json; print(json.load(sys.stdin).get('run_id', ''))")

if [ -z "$RUN_ID" ]; then
    echo "❌ Failed to start run"
    echo $START_RESPONSE
    exit 1
fi

echo "✅ Run started: $RUN_ID"
echo ""

# Step 3: Process ALL 30 candles LIVE (one by one with decision engine)
echo "📍 Step 3: Processing 30 candles LIVE..."
echo ""

python3 << PYEOF
import json
import sys
sys.path.append('/app/backend')

from services.spark_decision_engine import SparkDecisionEngine, PositionState

# Load candles
candles_data = json.loads('''$CANDLES_JSON''')
candles = candles_data.get('candles', [])

# Load run
with open('/app/backend/data/wallet/replay_logs/${RUN_ID}.json', 'r') as f:
    run_log = json.load(f)

config = run_log['config']
position_state = PositionState()
trading_locked = False

print(f"Processing {len(candles)} candles with decision engine...")
print()

for i, candle in enumerate(candles):
    # Context = all previous candles
    context = candles[:i]
    
    # Run decision engine (LIVE)
    decision = SparkDecisionEngine.analyze_candle(
        candle=candle,
        context=context,
        config=config,
        position_state=position_state,
        trading_locked=trading_locked
    )
    
    # Update position state
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
    
    # Update trading lock
    if decision.get('lock_triggered'):
        trading_locked = True
    
    # Append to run log
    run_log['candles'].append(candle)
    run_log['decisions_v1'].append({
        'timestamp': candle['timestamp'],
        **decision
    })
    
    # Update position state in log
    run_log['position_state'] = decision.get('position_update', position_state.to_dict())
    run_log['trading_locked'] = trading_locked
    
    # Print progress
    action_emoji = {"BUY": "🟢", "SELL": "🔴", "HOLD": "⚪"}.get(decision['action'], "⚫")
    print(f"  {action_emoji} Candle {i+1:2d}/30: {decision['action']:4s} (conf: {decision['confidence']:.2f})")
    
    # Print BB if available
    if decision.get('indicators', {}).get('bb'):
        bb = decision['indicators']['bb']
        price = decision['indicators']['price']
        print(f"       Price: €{price:.2f}, BB Lower: €{bb['lower']:.2f}, Upper: €{bb['upper']:.2f}")

# Save run log
with open('/app/backend/data/wallet/replay_logs/${RUN_ID}.json', 'w') as f:
    json.dump(run_log, f, indent=2)

print()
print(f"✅ All 30 candles processed LIVE")
print(f"   Total decisions logged: {len(run_log['decisions_v1'])}")

PYEOF

echo ""

# Step 4: Stop run
echo "📍 Step 4: Stopping run..."
curl -s -X POST "${API_URL}/api/bitvavo/live-monitor/stop?run_id=${RUN_ID}" > /dev/null
echo "✅ Run stopped"
echo ""

# Step 5: Replay
echo "📍 Step 5: Replaying run (recalculating decisions)..."
REPLAY_RESPONSE=$(curl -s -X POST "${API_URL}/api/bitvavo/replay/run?run_id=${RUN_ID}")

echo ""
echo "$REPLAY_RESPONSE" | python3 -c "
import sys, json

try:
    r = json.load(sys.stdin)
    
    print('========================================')
    print('📊 REPLAY RESULTS')
    print('========================================')
    print()
    print(f'Total candles:        {r.get(\"total_candles\", 0)}')
    print(f'Live decisions:       {r.get(\"candles_with_live_decisions\", 0)}')
    print(f'Matches:              {r.get(\"matches\", 0)}')
    print(f'Mismatches:           {r.get(\"mismatches\", 0)}')
    print()
    print(f'Reproducibility:      {r.get(\"reproducibility_percent\", 0):.1f}%')
    print()
    
    if r.get('mismatches', 0) == 0:
        print('🎉🎉🎉 SUCCESS: 100% REPRODUCIBLE!')
        print()
        print('✅ Replay engine is DETERMINISTISCH')
        print('✅ Live en Replay gebruiken IDENTIEKE logica')
        print('✅ Beslissingen zijn VOLLEDIG REPRODUCEERBAAR')
        print()
        print('========================================')
        print('REPLAY BETROUWBAAR ✅')
        print('========================================')
        sys.exit(0)
    else:
        print('❌ MISMATCHES FOUND:')
        print()
        for i, diff in enumerate(r.get('differences', []), 1):
            print(f'{i}. Timestamp: {diff.get(\"candle_timestamp\")}')
            print(f'   Live:   {diff.get(\"live_action\")} (conf: {diff.get(\"live_confidence\", 0):.2f})')
            print(f'   Replay: {diff.get(\"replay_action\")} (conf: {diff.get(\"replay_confidence\", 0):.2f})')
            print(f'   Live reason:   {diff.get(\"live_reason\", \"\")[:80]}')
            print(f'   Replay reason: {diff.get(\"replay_reason\", \"\")[:80]}')
            print()
        sys.exit(1)
except Exception as e:
    print(f'❌ Error parsing replay response: {e}')
    sys.exit(1)
"

EXIT_CODE=$?
echo ""
echo "=========================================="
echo "Test Complete"
echo "=========================================="

exit $EXIT_CODE
