#!/bin/bash
# BCH CYCLUS ANALYSE
# Hypothese: Ma/Di dip, Do/Vr/Za opbouw
# Methode: Data-driven - laat cijfers spreken

API_URL=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d '=' -f2)

echo "=========================================="
echo "📊 BCH CYCLUS ANALYSE"
echo "=========================================="
echo ""
echo "Hypothese te testen:"
echo "  - Ma/Di: Vaak dip?"
echo "  - Do/Vr/Za: Vaak opbouw?"
echo ""
echo "Methode: Analyse van historische data"
echo "=========================================="
echo ""

# Fetch verschillende periodes
echo "📍 Fetching historical BCH data..."
echo "  - 1 maand:  ~720 candles (1h)"
echo "  - 3 maanden: ~2160 candles (1h)"
echo ""

# We gaan 500 candles analyseren (3 weken)
# SCHRIJF DIRECT NAAR FILE (robuuster dan bash variable)
TEMP_FILE="/tmp/bch_candles.json"
curl -s "${API_URL}/api/bitvavo/candles?market=BCH-EUR&interval=1h&limit=500" > "$TEMP_FILE"

# Debug: check of file data bevat
if [ ! -s "$TEMP_FILE" ]; then
    echo "❌ Failed to fetch candles - empty response"
    echo "Checking API..."
    curl -s "${API_URL}/api/bitvavo/candles?market=BCH-EUR&interval=1h&limit=500"
    exit 1
fi

# Verify JSON is valid
CANDLE_COUNT=$(python3 -c "import sys,json; data=json.load(open('$TEMP_FILE')); print(len(data.get('candles', [])))" 2>&1)

if [ $? -ne 0 ]; then
    echo "❌ Invalid JSON response"
    echo "First 500 chars of response:"
    head -c 500 "$TEMP_FILE"
    exit 1
fi

if [ "$CANDLE_COUNT" -eq "0" ]; then
    echo "❌ Failed to fetch candles - got 0 candles"
    exit 1
fi

echo "✅ Fetched $CANDLE_COUNT candles"
echo ""

echo "📍 Analyzing patterns..."
echo ""

# Feed file to Python instead of piping variable
python3 << PYEOF
import json
import sys
from datetime import datetime
from collections import defaultdict
import statistics

# Load candles from file
with open('/tmp/bch_candles.json', 'r') as f:
    candles_data = json.load(f)

candles = candles_data.get('candles', [])

print(f"Analyzing {len(candles)} 1h candles...")
print("=" * 80)
print()

# Convert to analysis format
data_points = []
for candle in candles:
    timestamp = candle['timestamp'] / 1000  # Convert to seconds
    dt = datetime.fromtimestamp(timestamp)
    
    data_points.append({
        'timestamp': timestamp,
        'datetime': dt,
        'weekday': dt.weekday(),  # 0=Ma, 1=Di, 2=Wo, 3=Do, 4=Vr, 5=Za, 6=Zo
        'weekday_name': ['Ma', 'Di', 'Wo', 'Do', 'Vr', 'Za', 'Zo'][dt.weekday()],
        'hour': dt.hour,
        'open': float(candle['open']),
        'high': float(candle['high']),
        'low': float(candle['low']),
        'close': float(candle['close']),
        'volume': float(candle['volume'])
    })

# === 1. IDENTIFY LOCAL PEAKS & DIPS ===
print("1️⃣  PIEK & DAL DETECTIE")
print("-" * 80)
print()

peaks = []
dips = []

# Simple peak/dip detection: compare with neighbors (window = 12h)
window = 12

for i in range(window, len(data_points) - window):
    current = data_points[i]
    
    # Check if local peak
    left_prices = [data_points[j]['high'] for j in range(i - window, i)]
    right_prices = [data_points[j]['high'] for j in range(i + 1, i + window + 1)]
    
    if current['high'] >= max(left_prices) and current['high'] >= max(right_prices):
        peaks.append({
            'index': i,
            'weekday': current['weekday'],
            'weekday_name': current['weekday_name'],
            'price': current['high'],
            'datetime': current['datetime']
        })
    
    # Check if local dip
    left_prices_low = [data_points[j]['low'] for j in range(i - window, i)]
    right_prices_low = [data_points[j]['low'] for j in range(i + 1, i + window + 1)]
    
    if current['low'] <= min(left_prices_low) and current['low'] <= min(right_prices_low):
        dips.append({
            'index': i,
            'weekday': current['weekday'],
            'weekday_name': current['weekday_name'],
            'price': current['low'],
            'datetime': current['datetime']
        })

print(f"Detected Peaks (local highs): {len(peaks)}")
print(f"Detected Dips (local lows):   {len(dips)}")
print()

# === 2. DAY-OF-WEEK DISTRIBUTION ===
print("2️⃣  DAG-VAN-WEEK DISTRIBUTIE")
print("-" * 80)
print()

# Count peaks per day
peak_days = defaultdict(int)
for peak in peaks:
    peak_days[peak['weekday_name']] += 1

# Count dips per day
dip_days = defaultdict(int)
for dip in dips:
    dip_days[dip['weekday_name']] += 1

# Total observations per day (for normalization)
total_days = defaultdict(int)
for dp in data_points:
    total_days[dp['weekday_name']] += 1

print("PIEKEN (Highs) per dag:")
days = ['Ma', 'Di', 'Wo', 'Do', 'Vr', 'Za', 'Zo']
for day in days:
    count = peak_days[day]
    total = total_days[day]
    rate = (count / total * 100) if total > 0 else 0
    bar = '█' * int(rate * 2)
    print(f"  {day}: {count:2d} peaks ({rate:.1f}% rate) {bar}")

print()
print("DALEN (Lows) per dag:")
for day in days:
    count = dip_days[day]
    total = total_days[day]
    rate = (count / total * 100) if total > 0 else 0
    bar = '█' * int(rate * 2)
    print(f"  {day}: {count:2d} dips  ({rate:.1f}% rate) {bar}")

print()

# === 3. HYPOTHESIS TEST ===
print("3️⃣  HYPOTHESE TEST")
print("-" * 80)
print()

# Hypothesis: Ma/Di have more dips, Do/Vr/Za have more peaks
ma_di_dips = dip_days['Ma'] + dip_days['Di']
do_vr_za_peaks = peak_days['Do'] + peak_days['Vr'] + peak_days['Za']

total_ma_di_hours = total_days['Ma'] + total_days['Di']
total_do_vr_za_hours = total_days['Do'] + total_days['Vr'] + total_days['Za']

ma_di_dip_rate = (ma_di_dips / total_ma_di_hours * 100) if total_ma_di_hours > 0 else 0
do_vr_za_peak_rate = (do_vr_za_peaks / total_do_vr_za_hours * 100) if total_do_vr_za_hours > 0 else 0

print(f"Ma/Di Dip Rate:        {ma_di_dip_rate:.2f}%")
print(f"Do/Vr/Za Peak Rate:    {do_vr_za_peak_rate:.2f}%")
print()

# Compare with baseline
baseline_dip_rate = len(dips) / len(data_points) * 100
baseline_peak_rate = len(peaks) / len(data_points) * 100

print(f"Baseline Dip Rate:     {baseline_dip_rate:.2f}%")
print(f"Baseline Peak Rate:    {baseline_peak_rate:.2f}%")
print()

# Statistical significance (simple chi-square test approximation)
if ma_di_dip_rate > baseline_dip_rate * 1.2:
    print("✅ Ma/Di hebben SIGNIFICANT meer dips (+20%)")
elif ma_di_dip_rate > baseline_dip_rate * 1.1:
    print("⚠️  Ma/Di hebben licht meer dips (+10%)")
else:
    print("❌ Ma/Di patroon NIET bevestigd in deze data")

print()

if do_vr_za_peak_rate > baseline_peak_rate * 1.2:
    print("✅ Do/Vr/Za hebben SIGNIFICANT meer pieken (+20%)")
elif do_vr_za_peak_rate > baseline_peak_rate * 1.1:
    print("⚠️  Do/Vr/Za hebben licht meer pieken (+10%)")
else:
    print("❌ Do/Vr/Za patroon NIET bevestigd in deze data")

print()

# === 4. PRICE MOVEMENT ANALYSIS ===
print("4️⃣  GEMIDDELDE RETURNS PER DAG")
print("-" * 80)
print()

# Calculate daily returns
day_returns = defaultdict(list)

for i in range(24, len(data_points)):
    current = data_points[i]
    prev_24h = data_points[i - 24]
    
    daily_return = (current['close'] - prev_24h['close']) / prev_24h['close'] * 100
    day_returns[current['weekday_name']].append(daily_return)

print("Gemiddelde 24h return per dag:")
for day in days:
    if day_returns[day]:
        avg_return = statistics.mean(day_returns[day])
        std_return = statistics.stdev(day_returns[day]) if len(day_returns[day]) > 1 else 0
        
        emoji = "🟢" if avg_return > 0 else "🔴"
        print(f"  {emoji} {day}: {avg_return:+.2f}% (σ={std_return:.2f}%)")

print()

# === 5. CONCLUSIE ===
print("=" * 80)
print("📋 CONCLUSIE")
print("=" * 80)
print()

# Check if hypothesis is supported
ma_di_confirmed = ma_di_dip_rate > baseline_dip_rate * 1.1
do_vr_za_confirmed = do_vr_za_peak_rate > baseline_peak_rate * 1.1

if ma_di_confirmed and do_vr_za_confirmed:
    print("✅ HYPOTHESE BEVESTIGD:")
    print("   Ma/Di tonen verhoogde dip frequentie")
    print("   Do/Vr/Za tonen verhoogde piek frequentie")
    print()
    print("   → Cyclus patroon AANWEZIG in deze dataset")
elif ma_di_confirmed or do_vr_za_confirmed:
    print("⚠️  HYPOTHESE GEDEELTELIJK BEVESTIGD:")
    if ma_di_confirmed:
        print("   ✅ Ma/Di dip patroon aanwezig")
    if do_vr_za_confirmed:
        print("   ✅ Do/Vr/Za piek patroon aanwezig")
    print()
    print("   → Zwak signaal, meer data nodig")
else:
    print("❌ HYPOTHESE NIET BEVESTIGD:")
    print("   Geen significant dag-van-week patroon gevonden")
    print()
    print("   → BCH gedraagt zich RANDOM of heeft ander patroon")

print()
print("AANBEVELING:")
print("  - Analyse over langere periode (3-6 maanden)")
print("  - Check externe factoren (market events)")
print("  - Strategie NIET aanpassen op basis van deze data alleen")
print()

PYEOF

echo ""
echo "=========================================="
echo "Analyse Complete"
echo "=========================================="
