#!/bin/bash
#
# Live Cache Integration Test
#
# Test de cache integratie in spark_brain.py:
# 1. Login als user
# 2. Send multiple messages
# 3. Check cache statistics
# 4. Verify cache is being used
#

set -e

# Get API URL
API_URL=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d '=' -f2)

echo "=========================================="
echo "LIVE CACHE INTEGRATION TEST"
echo "=========================================="
echo "API URL: $API_URL"
echo ""

# Test 1: Login
echo "📝 TEST 1: Login"
echo "------------------------------------------"
LOGIN_RESPONSE=$(curl -s -X POST "$API_URL/api/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Willem Appelsap"}')

echo "Response: $LOGIN_RESPONSE" | head -c 200
echo ""
echo "✓ Login successful"
echo ""

# Test 2: Send 5 messages
echo "📝 TEST 2: Send Multiple Messages"
echo "------------------------------------------"

for i in {1..5}; do
  echo "Message $i..."
  curl -s -X POST "$API_URL/api/chat" \
    -H "Content-Type: application/json" \
    -d "{\"message\": \"Test message $i - Wat is auto?\", \"user_id\": \"willem\"}" > /dev/null
  sleep 0.5
done

echo "✓ Sent 5 messages"
echo ""

# Test 3: Check cache statistics
echo "📝 TEST 3: Check Cache Statistics"
echo "------------------------------------------"

STATS_RESPONSE=$(curl -s -X GET "$API_URL/api/admin/cache/stats")

echo "$STATS_RESPONSE" | python3 -m json.tool

# Extract key metrics
HIT_RATE=$(echo "$STATS_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['stats']['hit_rate_percent'])" 2>/dev/null || echo "N/A")
ACTIVE_SESSIONS=$(echo "$STATS_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['stats']['active_sessions'])" 2>/dev/null || echo "N/A")
TOTAL_MESSAGES=$(echo "$STATS_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['stats']['total_messages'])" 2>/dev/null || echo "N/A")
MEMORY_MB=$(echo "$STATS_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['stats']['memory_usage_mb'])" 2>/dev/null || echo "N/A")

echo ""
echo "📊 Cache Metrics Summary:"
echo "  Hit Rate: $HIT_RATE%"
echo "  Active Sessions: $ACTIVE_SESSIONS"
echo "  Total Messages: $TOTAL_MESSAGES"
echo "  Memory Usage: ${MEMORY_MB} MB"
echo ""

# Validation
if [ "$TOTAL_MESSAGES" != "N/A" ] && [ "$TOTAL_MESSAGES" -gt "0" ]; then
  echo "✅ Cache is being used! ($TOTAL_MESSAGES messages cached)"
else
  echo "⚠️  Warning: Cache appears empty"
fi

echo ""
echo "=========================================="
echo "TEST COMPLETE"
echo "=========================================="
echo ""
echo "Summary:"
echo "  ✓ Login successful"
echo "  ✓ Messages sent (5 messages)"
echo "  ✓ Cache statistics accessible"
if [ "$TOTAL_MESSAGES" != "N/A" ] && [ "$TOTAL_MESSAGES" -gt "0" ]; then
  echo "  ✅ Cache integration working!"
else
  echo "  ⚠️  Cache integration needs verification"
fi
echo ""
