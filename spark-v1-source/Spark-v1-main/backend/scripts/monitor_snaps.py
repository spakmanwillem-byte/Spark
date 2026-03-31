#!/usr/bin/env python3
"""
Real-time Snap Creation Monitor
Willem kan dit draaien in een terminal terwijl hij test
"""

import sys
import time
import subprocess
from datetime import datetime

def print_header():
    print("\n" + "="*80)
    print("🔍 SNAP CREATION LIVE MONITOR")
    print("="*80)
    print("Monitoring snap creation, rejections en ja/nee systeem...")
    print("Druk CTRL+C om te stoppen\n")
    print("-"*80)

def monitor_logs():
    """Monitor backend logs in real-time voor snap events"""
    print_header()
    
    # Volg backend logs
    cmd = "tail -f /var/log/supervisor/backend.out.log /var/log/supervisor/backend.err.log 2>/dev/null"
    
    try:
        process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1
        )
        
        for line in iter(process.stdout.readline, ''):
            line = line.strip()
            
            # Filter relevante snap events
            if any(keyword in line for keyword in [
                'SNAP DEBUG',
                'SNAP REJECTED',
                'SNAP CREATED',
                'Knowledge snap',
                'duplicate',
                'ja/nee',
                'snap-'
            ]):
                timestamp = datetime.now().strftime("%H:%M:%S")
                
                # Color coding
                if 'REJECTED' in line or '❌' in line:
                    color = '\033[91m'  # Rood
                    symbol = "❌"
                elif 'CREATED' in line or '✅' in line:
                    color = '\033[92m'  # Groen
                    symbol = "✅"
                elif 'duplicate' in line.lower():
                    color = '\033[93m'  # Geel
                    symbol = "⚠️"
                else:
                    color = '\033[96m'  # Cyan
                    symbol = "ℹ️"
                
                reset = '\033[0m'
                
                print(f"{color}[{timestamp}] {symbol} {line}{reset}")
                sys.stdout.flush()
    
    except KeyboardInterrupt:
        print("\n\n⏹️  Monitor gestopt")
        process.terminate()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(monitor_logs())
