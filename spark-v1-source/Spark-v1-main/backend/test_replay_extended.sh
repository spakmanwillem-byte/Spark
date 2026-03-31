#!/bin/bash
# Extended test: Use historical BCH data for full Bollinger Bands calculation

API_URL=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d '=' -f2)
USER_ID="user-001"

echo "==================================="
echo "🧪 EXTENDED REPLAY TEST (with BB data)"
echo "==================================="
echo ""

# Get 30 historical BCH candles
echo "📍 Fetching 30 historical BCH candles..."
CANDLES=$(curl -s "${API_URL}/api/bitvavo/candles?market=BCH-EUR&interval=1h&limit=30")

echo "✅ Candles fetched"
echo ""

# Start run and inject historical candles
echo "📍 Starting run with historical data..."
START_RESPONSE=$(curl -s -X POST "${API_URL}/api/bitvavo/live-monitor/start?user_id=${USER_ID}&coin=BCH" \
  -H "Content-Type: application/json" \
  -d '{"bb_period": 20, "bb_std_dev": 2, "trade_amount": 5.0}')

RUN_ID=$(echo $START_RESPONSE | python3 -c "import sys,json; print(json.load(sys.stdin).get('run_id', ''))")
echo "✅ Run ID: $RUN_ID"
echo ""

# Manually inject candles into log (simulate 30 hours of data)
echo "📍 Injecting historical candles..."
python3 << EOF
import json
import sys

candles_response = json.loads('''$CANDLES''')
candles = candles_response.get('candles', [])

if not candles:
    print("❌ No candles fetched")
    sys.exit(1)

# Load run log
with open(f'/app/backend/data/wallet/replay_logs/${RUN_ID}.json', 'r') as f:
    run_log = json.load(f)

# Inject candles (first 25 for context, process last 5 with decisions)
run_log['candles'] = candles[:25]

with open(f'/app/backend/data/wallet/replay_logs/${RUN_ID}.json', 'w') as f:
    json.dump(run_log, f, indent=2)

print(f"✅ Injected {len(candles[:25])} context candles")
EOF

echo ""

# Now process 5 more candles with decisions
echo "📍 Processing 5 candles with Bollinger Bands active..."
for i in {26..30}; do
    echo "  Processing candle $i/30..."
    
    # Get the specific candle from history
    CANDLE_DATA=$(echo $CANDLES | python3 -c "import sys,json; candles=json.load(sys.stdin).get('candles', []); print(json.dumps(candles[$i-1]) if len(candles) >= $i else '{}')")
    
    if [ "$CANDLE_DATA" = "{}" ]; then
        echo "  ⚠️ No candle data for index $i"
        continue
    fi
    
    # Manually append candle and run decision
    python3 << PYEOF
import json
import sys
sys.path.append('/app/backend')

from services.spark_decision_engine import SparkDecisionEngine, PositionState

# Load run
with open('/app/backend/data/wallet/replay_logs/${RUN_ID}.json', 'r') as f:
    run_log = json.load(f)

candle = json.loads('''$CANDLE_DATA''')
context = run_log['candles']
config = run_log['config']

# Restore position state
position_state = PositionState()
saved_state = run_log.get('position_state', {})
if saved_state.get('position_type') != 'NONE':
    position_state.position_type = saved_state['position_type']
    position_state.entry_price = saved_state['entry_price']
    position_state.entry_time = saved_state['entry_time']
    position_state.highest_price = saved_state['highest_price']
    position_state.trailing_stop_active = saved_state.get('trailing_stop_active', False)

trading_locked = run_log.get('trading_locked', False)

# Run decision engine
decision = SparkDecisionEngine.analyze_candle(
    candle=candle,
    context=context,
    config=config,
    position_state=position_state,
    trading_locked=trading_locked
)

# Append to log
run_log['candles'].append(candle)
run_log['decisions_v1'].append({
    'timestamp': candle['timestamp'],
    **decision
})

# Update position state
if decision.get('position_update'):
    run_log['position_state'] = decision['position_update']

# Update trading lock
if decision.get('lock_triggered'):
    run_log['trading_locked'] = True

# Save
with open('/app/backend/data/wallet/replay_logs/${RUN_ID}.json', 'w') as f:
    json.dump(run_log, f, indent=2)

# Print decision
print(f"  ✅ {decision['action']} (conf: {decision['confidence']:.2f})")
if decision.get('indicators', {}).get('bb'):
    bb = decision['indicators']['bb']
    print(f"     BB: Lower={bb['lower']}, Middle={bb['middle']}, Upper={bb['upper']}")
    print(f"     Price: {decision['indicators']['price']}")
print(f"     Reason: {decision['reason'][:80]}")
PYEOF

    sleep 0.5
done

echo ""

# Stop run
echo "📍 Stopping run..."
curl -s -X POST "${API_URL}/api/bitvavo/live-monitor/stop?run_id=${RUN_ID}" > /dev/null
echo "✅ Run stopped"
echo ""

# Replay
echo "📍 Replaying run..."
REPLAY_RESPONSE=$(curl -s -X POST "${API_URL}/api/bitvavo/replay/run?run_id=${RUN_ID}")

echo "$REPLAY_RESPONSE" | python3 -c "
import sys, json
r = json.load(sys.stdin)
print(f\"✅ Replay complete\")
print(f\"   Candles: {r.get('candles_processed', 0)}\")
print(f\"   Matches: {r.get('matches', 0)}\")
print(f\"   Mismatches: {r.get('mismatches', 0)}\")
print(f\"   Reproducibility: {r.get('reproducibility_percent', 0):.1f}%\")
print(\"\")
if r.get('mismatches', 0) > 0:
    print(\"❌ DIFFERENCES FOUND:\")
    for diff in r.get('differences', []):
        print(f\"  Candle {diff['candle_index']}: Live={diff['live_action']} vs Replay={diff['replay_action']}\")
    sys.exit(1)
else:
    print(\"🎉 100% REPRODUCIBLE!\")
"

echo ""
echo "==================================="
echo "Test Complete"
echo "==================================="
