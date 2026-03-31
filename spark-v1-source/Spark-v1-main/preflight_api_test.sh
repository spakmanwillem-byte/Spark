#!/bin/bash
# Pre-Flight API Test voor Live Trading
# Test de Bitvavo API grondig VOORDAT er trades worden gedaan

API_URL="https://spark-foundation.preview.emergentagent.com"
USER_ID="user-001"

echo "======================================"
echo "🔍 PRE-FLIGHT API TEST"
echo "======================================"
echo ""

# Test 1: Check if backend is running
echo "1️⃣  Checking backend status..."
if curl -s --fail "$API_URL/api/bitvavo/live-trading/status?user_id=$USER_ID" > /dev/null 2>&1; then
    echo "✅ Backend is running"
else
    echo "❌ Backend not responding"
    exit 1
fi
echo ""

# Test 2: Verify credentials are saved
echo "2️⃣  Testing API connection..."
CONN_TEST=$(curl -s -X POST "$API_URL/api/bitvavo/test?user_id=$USER_ID")
if echo "$CONN_TEST" | grep -q '"success":true'; then
    echo "✅ API credentials valid"
    echo "$CONN_TEST" | python3 -c "import sys,json; data=json.load(sys.stdin); print(f\"   Message: {data.get('message', 'OK')}\")"
else
    echo "❌ API credentials failed"
    echo "$CONN_TEST"
    exit 1
fi
echo ""

# Test 3: Get balance (READ operation)
echo "3️⃣  Fetching balance (READ test)..."
BALANCE=$(curl -s "$API_URL/api/bitvavo/balance?user_id=$USER_ID")
if echo "$BALANCE" | grep -q '"success":true'; then
    echo "✅ Balance retrieved successfully"
    echo "$BALANCE" | python3 -c "import sys,json; data=json.load(sys.stdin); bal=data.get('balance',{}); eur=bal.get('EUR',{}); bch=bal.get('BCH',{}); print(f\"   EUR: €{eur.get('available','0')}\"); print(f\"   BCH: {bch.get('available','0')} coins\")"
else
    echo "❌ Balance fetch failed"
    echo "$BALANCE"
    exit 1
fi
echo ""

# Test 4: Get BCH ticker (public endpoint)
echo "4️⃣  Fetching BCH ticker..."
TICKER=$(curl -s "$API_URL/api/bitvavo/ticker?market=BCH-EUR")
if echo "$TICKER" | grep -q '"success":true'; then
    echo "✅ Ticker retrieved successfully"
    echo "$TICKER" | python3 -c "import sys,json; data=json.load(sys.stdin); ticker=data.get('ticker',{}); print(f\"   BCH Price: €{ticker.get('last', 'N/A')}\"); print(f\"   24h Volume: {ticker.get('volume', 'N/A')}\")"
else
    echo "❌ Ticker fetch failed"
    echo "$TICKER"
    exit 1
fi
echo ""

# Test 5: Check current mode
echo "5️⃣  Checking trading mode..."
STATUS=$(curl -s "$API_URL/api/bitvavo/live-trading/status?user_id=$USER_ID")
MOCK_MODE=$(echo "$STATUS" | python3 -c "import sys,json; data=json.load(sys.stdin); print(str(data.get('mock_mode', 'unknown')).lower())")
if [ "$MOCK_MODE" = "true" ]; then
    echo "✅ Currently in MOCK mode (safe)"
elif [ "$MOCK_MODE" = "false" ]; then
    echo "⚠️  Currently in LIVE mode"
else
    echo "❌ Could not determine mode: $MOCK_MODE"
    echo "$STATUS"
    exit 1
fi
echo ""

# Summary
echo "======================================"
echo "✅ ALL PRE-FLIGHT CHECKS PASSED"
echo "======================================"
echo ""
echo "Ready for live trading test:"
echo "  • API connection: ✅ Working"
echo "  • Credentials: ✅ Valid"
echo "  • Balance access: ✅ OK"
echo "  • Market data: ✅ OK"
echo ""
echo "Next steps:"
echo "  1. Switch to live mode if ready"
echo "  2. Reset position for clean start"
echo "  3. Start monitoring with €5 trade size"
echo ""
