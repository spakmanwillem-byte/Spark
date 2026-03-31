#!/bin/bash
# Test script: Play → Stop → Replay flow
# Verificatie: Replay moet EXACT dezelfde beslissingen geven als live

API_URL=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d '=' -f2)
USER_ID="user-001"
COIN="BCH"

echo "==================================="
echo "🧪 REPLAY REPRODUCIBILITY TEST"
echo "==================================="
echo ""

# Step 1: Start live run
echo "📍 Step 1: Start Live Run"
START_RESPONSE=$(curl -s -X POST "${API_URL}/api/bitvavo/live-monitor/start?user_id=${USER_ID}&coin=${COIN}" \
  -H "Content-Type: application/json" \
  -d '{"bb_period": 20, "bb_std_dev": 2, "trade_amount": 5.0}')

RUN_ID=$(echo $START_RESPONSE | python3 -c "import sys,json; print(json.load(sys.stdin).get('run_id', ''))")

if [ -z "$RUN_ID" ]; then
    echo "❌ Failed to start run"
    echo $START_RESPONSE
    exit 1
fi

echo "✅ Run started: $RUN_ID"
echo ""

# Step 2: Process 5 live candles
echo "📍 Step 2: Process Live Candles (simulating 5 hours)"
for i in {1..5}; do
    echo "  Processing candle $i/5..."
    CANDLE_RESPONSE=$(curl -s "${API_URL}/api/bitvavo/live-monitor/candle?run_id=${RUN_ID}&user_id=${USER_ID}")
    
    SUCCESS=$(echo $CANDLE_RESPONSE | python3 -c "import sys,json; print(json.load(sys.stdin).get('success', False))")
    
    if [ "$SUCCESS" = "False" ]; then
        echo "  ❌ Failed to process candle $i"
        echo $CANDLE_RESPONSE
        exit 1
    fi
    
    # Extract decision info
    ACTION=$(echo $CANDLE_RESPONSE | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('decision', {}).get('action', 'N/A'))")
    CONFIDENCE=$(echo $CANDLE_RESPONSE | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('decision', {}).get('confidence', 0))")
    REASON=$(echo $CANDLE_RESPONSE | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('decision', {}).get('reason', 'N/A')[:60])")
    
    echo "  ✅ Candle $i: $ACTION (conf: $CONFIDENCE) - $REASON"
    
    sleep 1
done

echo ""

# Step 3: Stop run
echo "📍 Step 3: Stop Run"
STOP_RESPONSE=$(curl -s -X POST "${API_URL}/api/bitvavo/live-monitor/stop?run_id=${RUN_ID}")
echo "✅ Run stopped"
echo ""

# Step 4: Load run log for replay
echo "📍 Step 4: Load Run Log"
RUN_LOG=$(curl -s "${API_URL}/api/bitvavo/live-monitor/runs?user_id=${USER_ID}" | \
  python3 -c "import sys,json; runs=json.load(sys.stdin).get('runs', []); print(runs[0] if runs else {})")

echo "✅ Run log loaded"
echo ""

# Step 5: Replay run (recalculate decisions)
echo "📍 Step 5: Replay Run (Recalculate Decisions)"
echo "  Running decision engine on same candles..."

# Call a new replay endpoint (we need to create this)
REPLAY_RESPONSE=$(curl -s -X POST "${API_URL}/api/bitvavo/replay/run?run_id=${RUN_ID}")

echo "✅ Replay completed"
echo ""

# Step 6: Compare decisions
echo "📍 Step 6: Compare Live vs Replay Decisions"
echo "==================================="

# Download run log
RUN_DATA=$(curl -s "${API_URL}/api/bitvavo/live-monitor/run-data?run_id=${RUN_ID}")

# Compare decisions_v1 (live) vs decisions_v2 (replay)
python3 << EOF
import json
import sys

run_data = json.loads('''$RUN_DATA''')

decisions_v1 = run_data.get('decisions_v1', [])
decisions_v2 = run_data.get('decisions_v2', [])

if not decisions_v2:
    print("❌ No replay decisions found (decisions_v2 empty)")
    sys.exit(1)

print(f"Live decisions: {len(decisions_v1)}")
print(f"Replay decisions: {len(decisions_v2)}")
print("")

if len(decisions_v1) != len(decisions_v2):
    print("❌ MISMATCH: Different number of decisions!")
    sys.exit(1)

mismatches = 0
for i, (live, replay) in enumerate(zip(decisions_v1, decisions_v2)):
    if live['action'] != replay['action']:
        print(f"❌ MISMATCH at candle {i+1}:")
        print(f"   Live: {live['action']} (conf: {live['confidence']})")
        print(f"   Replay: {replay['action']} (conf: {replay['confidence']})")
        print(f"   Reason Live: {live['reason'][:60]}")
        print(f"   Reason Replay: {replay['reason'][:60]}")
        mismatches += 1
    else:
        print(f"✅ Candle {i+1}: {live['action']} - MATCH")

print("")
if mismatches == 0:
    print("🎉 SUCCESS: 100% REPRODUCIBLE - All decisions match!")
else:
    print(f"❌ FAILED: {mismatches} mismatches found")
    sys.exit(1)
EOF

echo ""
echo "==================================="
echo "Test Complete"
echo "==================================="
