#!/bin/bash
# Quick test script voor Willem
# Draai dit om de snap logging in actie te zien

echo "============================================================================"
echo "🔍 SNAP CREATION MONITORING"
echo "============================================================================"
echo ""
echo "Dit script toont real-time alle snap-gerelateerde events"
echo "Druk CTRL+C om te stoppen"
echo ""
echo "Start monitoring..."
echo "----------------------------------------------------------------------------"

# Volg beide backend logs en filter snap events
tail -f /var/log/supervisor/backend.out.log /var/log/supervisor/backend.err.log 2>/dev/null | \
  grep --line-buffered -E "(SNAP DEBUG|SNAP REJECTED|SNAP CREATED|Knowledge snap|duplicate|snap-)" | \
  while IFS= read -r line; do
    timestamp=$(date '+%H:%M:%S')
    
    # Color coding
    if [[ "$line" == *"REJECTED"* ]] || [[ "$line" == *"❌"* ]]; then
      echo -e "\033[91m[$timestamp] ❌ $line\033[0m"
    elif [[ "$line" == *"CREATED"* ]] || [[ "$line" == *"✅"* ]]; then
      echo -e "\033[92m[$timestamp] ✅ $line\033[0m"
    elif [[ "$line" == *"duplicate"* ]]; then
      echo -e "\033[93m[$timestamp] ⚠️  $line\033[0m"
    else
      echo -e "\033[96m[$timestamp] ℹ️  $line\033[0m"
    fi
  done
