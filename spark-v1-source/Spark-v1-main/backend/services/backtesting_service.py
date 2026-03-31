"""
Backtesting Service (Core)
===========================
Test trading strategieën met historische BCH data

Features:
- 2 jaar BCH candle data ophalen
- Versnelde replay (1 min, 15 min, 1 uur, instant)
- SparkDecisionEngine integration
- Patroon detectie (weekdag analyse)
- Rapportage + Knowledge Base updates

Willem's use case: Valideer zondag-dinsdag dip patroon
"""

import requests
import time
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
import json
import os

from services.spark_decision_engine import SparkDecisionEngine

logger = logging.getLogger(__name__)

# Cache folder voor historische data
CACHE_DIR = "/app/backend/data/backtesting/"
os.makedirs(CACHE_DIR, exist_ok=True)


class BacktestingService:
    """
    Backtesting service voor trading strategieën
    
    Gebruik:
    - backtest = BacktestingService()
    - backtest.load_historical_data("BCH-EUR", days=730)  # 2 jaar
    - results = backtest.run_backtest(speed="instant")
    - analysis = backtest.analyze_patterns(results)
    """
    
    def __init__(self):
        self.historical_data = []
        self.market = None
        self.interval = "1h"
        logger.info("🧪 Backtesting Service initialized")
    
    def load_historical_data(
        self, 
        market: str = "BCH-EUR", 
        days: int = 730,  # 2 jaar
        interval: str = "1h",
        use_cache: bool = True
    ) -> Dict:
        """
        Laad historische candle data van Bitvavo
        
        Args:
            market: Trading pair (BCH-EUR)
            days: Aantal dagen terug (730 = 2 jaar)
            interval: Candle interval (1h, 4h, 1d)
            use_cache: Gebruik gecachte data indien beschikbaar
        
        Returns:
            {
                "success": bool,
                "candles": int,
                "from": timestamp,
                "to": timestamp
            }
        """
        self.market = market
        self.interval = interval
        
        # Check cache
        cache_file = f"{CACHE_DIR}{market}_{interval}_{days}d.json"
        
        if use_cache and os.path.exists(cache_file):
            logger.info(f"📦 Loading from cache: {cache_file}")
            with open(cache_file, 'r') as f:
                cached = json.load(f)
                self.historical_data = cached['candles']
                return {
                    "success": True,
                    "candles": len(self.historical_data),
                    "from": self.historical_data[0]['timestamp'] if self.historical_data else None,
                    "to": self.historical_data[-1]['timestamp'] if self.historical_data else None,
                    "cached": True
                }
        
        # Calculate total candles needed
        if interval == "1h":
            total_candles = days * 24
        elif interval == "4h":
            total_candles = days * 6
        elif interval == "1d":
            total_candles = days
        else:
            total_candles = days * 24  # Default 1h
        
        logger.info(f"📥 Fetching {total_candles} candles for {market} ({interval})")
        
        # Bitvavo max: 1440 candles per request
        max_per_request = 1440
        num_requests = (total_candles // max_per_request) + 1
        
        all_candles = []
        
        for i in range(num_requests):
            limit = min(max_per_request, total_candles - (i * max_per_request))
            if limit <= 0:
                break
            
            try:
                url = f"https://api.bitvavo.com/v2/{market}/candles?interval={interval}&limit={limit}"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    raw_candles = response.json()
                    
                    # Transform format
                    for candle in raw_candles:
                        if len(candle) >= 6:
                            all_candles.append({
                                "timestamp": candle[0],
                                "open": float(candle[1]),
                                "high": float(candle[2]),
                                "low": float(candle[3]),
                                "close": float(candle[4]),
                                "volume": float(candle[5])
                            })
                    
                    logger.info(f"   ✅ Batch {i+1}/{num_requests}: {len(raw_candles)} candles")
                    
                    # Rate limiting (max 1000 weight/min)
                    if i < num_requests - 1:
                        time.sleep(0.5)
                else:
                    logger.error(f"❌ Bitvavo API error: {response.status_code}")
                    break
            
            except Exception as e:
                logger.error(f"❌ Error fetching candles: {e}")
                break
        
        # Sort by timestamp (oldest first)
        all_candles.sort(key=lambda x: x['timestamp'])
        
        self.historical_data = all_candles
        
        # Cache results
        with open(cache_file, 'w') as f:
            json.dump({
                "market": market,
                "interval": interval,
                "days": days,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "candles": all_candles
            }, f, indent=2)
        
        logger.info(f"✅ Loaded {len(all_candles)} candles, cached to {cache_file}")
        
        return {
            "success": True,
            "candles": len(all_candles),
            "from": all_candles[0]['timestamp'] if all_candles else None,
            "to": all_candles[-1]['timestamp'] if all_candles else None,
            "cached": False
        }
    
    def run_backtest(
        self,
        speed: str = "instant",  # instant, 1m, 15m, 1h, real-time
        trade_amount: float = 5.0,
        log_to_file: bool = True
    ) -> Dict:
        """
        Draai backtest met SparkDecisionEngine (ECHTE STRATEGIE)
        
        Args:
            speed: Replay snelheid
                - instant: Alle candles direct (seconden)
                - 1m: 1 candle per minuut (60x sneller)
                - 15m: 1 candle per 15 min (4x sneller)
                - 1h: 1 candle per uur (real-time simulatie)
            trade_amount: Trade size (€5 default)
            log_to_file: Log decisions naar file
        
        Returns:
            {
                "success": bool,
                "total_trades": int,
                "pnl_eur": float,
                "win_rate": float,
                "decisions": [...],
                "patterns": {...}
            }
        """
        if not self.historical_data:
            return {
                "success": False,
                "error": "No historical data loaded. Call load_historical_data() first."
            }
        
        logger.info(f"🚀 Starting backtest: {len(self.historical_data)} candles at {speed} speed")
        
        # Initialize SparkDecisionEngine
        from services.spark_decision_engine import PositionState
        
        position_state = PositionState()
        trading_locked = False
        
        decisions = []
        context_window = []  # Voor BB berekening
        start_time = time.time()
        
        # Speed delays (seconds per candle)
        speed_delays = {
            "instant": 0,
            "1m": 60,
            "15m": 900,
            "1h": 3600,
            "real-time": 3600
        }
        delay = speed_delays.get(speed, 0)
        
        # Process each candle met ECHTE engine
        for i, candle in enumerate(self.historical_data):
            # Build context window (laatste 50 candles voor indicators)
            if i > 0:
                context_window.append(self.historical_data[i - 1])
                if len(context_window) > 50:
                    context_window.pop(0)
            
            # Analyze candle met SparkDecisionEngine
            decision = SparkDecisionEngine.analyze_candle(
                candle=candle,
                context=context_window,
                config=None,  # Use defaults
                position_state=position_state,
                trading_locked=trading_locked
            )
            
            # Check for trading lock
            if decision.get("lock_triggered"):
                trading_locked = True
                logger.warning(f"⚠️ Trading locked at candle {i} due to loss > 3%")
            
            # Store decision (compact format)
            decisions.append({
                "timestamp": candle['timestamp'],
                "price": candle['close'],
                "action": decision['action'],
                "reason": decision['reason'],
                "confidence": decision['confidence'],
                "pnl_eur": decision['pnl']['pnl_eur'],
                "pnl_percent": decision['pnl']['pnl_percent'],
                "trade_amount": position_state.trade_amount,
                "current_pot": position_state.current_pot
            })
            
            # Log progress every 500 candles (for instant mode)
            if speed == "instant" and (i + 1) % 500 == 0:
                logger.info(f"   Progress: {i+1}/{len(self.historical_data)} candles")
            
            # Apply speed delay (skip for instant)
            if delay > 0 and i < len(self.historical_data) - 1:
                time.sleep(delay)
        
        elapsed = time.time() - start_time
        
        # Calculate stats
        trades = [d for d in decisions if d['action'] in ['BUY', 'SELL']]
        buys = [d for d in decisions if d['action'] == 'BUY']
        sells = [d for d in decisions if d['action'] == 'SELL']
        
        total_pnl = sum([s.get('pnl_eur', 0) for s in sells])
        wins = len([s for s in sells if s.get('pnl_eur', 0) > 0])
        losses = len([s for s in sells if s.get('pnl_eur', 0) < 0])
        win_rate = (wins / len(sells) * 100) if sells else 0
        
        # For large backtests, only keep sells (not all HOLD actions)
        decisions_to_save = trades if len(self.historical_data) > 1000 else decisions
        
        results = {
            "success": True,
            "market": self.market,
            "interval": self.interval,
            "candles_processed": len(self.historical_data),
            "elapsed_seconds": round(elapsed, 2),
            "total_trades": len(trades),
            "total_buys": len(buys),
            "total_sells": len(sells),
            "total_holds": len([d for d in decisions if d['action'] == 'HOLD']),
            "pnl_eur": round(total_pnl, 2),
            "wins": wins,
            "losses": losses,
            "win_rate": round(win_rate, 2),
            "decisions": decisions_to_save,
            "trading_locked": trading_locked
        }
        
        # Save log
        if log_to_file:
            log_file = f"{CACHE_DIR}backtest_{self.market}_{int(time.time())}.json"
            with open(log_file, 'w') as f:
                json.dump(results, f, indent=2)
            logger.info(f"💾 Backtest saved: {log_file}")
        
        logger.info(f"✅ Backtest complete: {len(trades)} trades ({len(buys)} buys, {len(sells)} sells), PnL: €{total_pnl:.2f}, Win rate: {win_rate:.1f}%")
        
        return results
    
    def analyze_patterns(self, backtest_results: Dict) -> Dict:
        """
        Analyseer patronen in backtest resultaten
        
        Focus: Weekdag analyse (Willem's zondag-dinsdag dip theorie)
        
        Returns:
            {
                "weekday_analysis": {...},
                "best_day": str,
                "worst_day": str,
                "insights": [...]
            }
        """
        decisions = backtest_results.get('decisions', [])
        
        if not decisions:
            return {"error": "No decisions to analyze"}
        
        # Group by weekday
        weekday_stats = {
            0: {"name": "Maandag", "trades": 0, "wins": 0, "pnl": 0.0},
            1: {"name": "Dinsdag", "trades": 0, "wins": 0, "pnl": 0.0},
            2: {"name": "Woensdag", "trades": 0, "wins": 0, "pnl": 0.0},
            3: {"name": "Donderdag", "trades": 0, "wins": 0, "pnl": 0.0},
            4: {"name": "Vrijdag", "trades": 0, "wins": 0, "pnl": 0.0},
            5: {"name": "Zaterdag", "trades": 0, "wins": 0, "pnl": 0.0},
            6: {"name": "Zondag", "trades": 0, "wins": 0, "pnl": 0.0}
        }
        
        # Analyze sells (completed trades)
        for d in decisions:
            if d['action'] == 'SELL':
                # Get weekday from timestamp
                dt = datetime.fromtimestamp(d['timestamp'] / 1000, tz=timezone.utc)
                weekday = dt.weekday()
                
                pnl = d.get('pnl_eur', 0)
                
                weekday_stats[weekday]['trades'] += 1
                weekday_stats[weekday]['pnl'] += pnl
                
                if pnl > 0:
                    weekday_stats[weekday]['wins'] += 1
        
        # Calculate win rates
        for day in weekday_stats.values():
            if day['trades'] > 0:
                day['win_rate'] = round((day['wins'] / day['trades']) * 100, 2)
                day['avg_pnl'] = round(day['pnl'] / day['trades'], 2)
            else:
                day['win_rate'] = 0
                day['avg_pnl'] = 0
        
        # Find best/worst
        best_day = max(weekday_stats.items(), key=lambda x: x[1]['pnl'])
        worst_day = min(weekday_stats.items(), key=lambda x: x[1]['pnl'])
        
        # Generate insights
        insights = []
        
        # Check Willem's theory: Zondag-dinsdag dip
        zo_di_pnl = sum([weekday_stats[i]['pnl'] for i in [6, 0, 1]])  # Zondag, Maandag, Dinsdag
        do_vr_pnl = sum([weekday_stats[i]['pnl'] for i in [3, 4]])  # Donderdag, Vrijdag
        
        if zo_di_pnl < do_vr_pnl:
            insights.append("✅ PATROON BEVESTIGD: Zondag-dinsdag lager PnL dan donderdag-vrijdag")
        else:
            insights.append("❌ PATROON NIET BEVESTIGD: Zondag-dinsdag heeft hoger PnL")
        
        # Best trading day
        insights.append(f"🏆 Beste dag: {best_day[1]['name']} (€{best_day[1]['pnl']:.2f})")
        insights.append(f"📉 Slechtste dag: {worst_day[1]['name']} (€{worst_day[1]['pnl']:.2f})")
        
        return {
            "weekday_analysis": weekday_stats,
            "best_day": best_day[1]['name'],
            "worst_day": worst_day[1]['name'],
            "zo_di_pnl": round(zo_di_pnl, 2),
            "do_vr_pnl": round(do_vr_pnl, 2),
            "pattern_confirmed": zo_di_pnl < do_vr_pnl,
            "insights": insights
        }


# Singleton
_backtesting_service = None

def get_backtesting_service() -> BacktestingService:
    """Get singleton backtesting service"""
    global _backtesting_service
    if _backtesting_service is None:
        _backtesting_service = BacktestingService()
    return _backtesting_service
