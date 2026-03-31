"""
Monitoring Service (Core)
=========================
Background monitoring service die autonoom kan draaien

Features:
- Start/Stop/Pause monitoring
- Background thread (blijft draaien na UI sluiten)
- Singleton pattern (voorkomt dubbele instances)
- Thread-safe
- Logging

Willem's use case: Trading alerts, automated tasks
"""

import threading
import time
import logging
from datetime import datetime, timezone
from typing import Dict, Optional
import json
from pathlib import Path

# Setup logger voor monitoring
monitor_logger = logging.getLogger("spark_monitor")
monitor_logger.setLevel(logging.INFO)

# File handler voor monitoring logs
monitor_handler = logging.FileHandler("/var/log/spark_monitor.log")
monitor_handler.setFormatter(logging.Formatter(
    '%(asctime)s - MONITOR - %(levelname)s - %(message)s'
))
monitor_logger.addHandler(monitor_handler)


from services.bitvavo_service import BitvavoService
from services.spark_decision_engine import SparkDecisionEngine, PositionState
from services.live_trader_service import LiveTraderService
from services.notification_service import NotificationService
from services.trading_context_service import get_trading_context


class MonitoringService:
    """
    Singleton monitoring service
    
    Draait in background thread
    Thread-safe met locks
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern - alleen 1 instance"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize monitoring service"""
        # Prevent re-initialization
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self._running = False
        self._paused = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        
        # Stats
        self._start_time = None
        self._cycles_completed = 0
        self._interval = 10  # Default 10 seconds (voor heartbeat)
        
        # Decision log
        self._decision_log_file = Path("/app/backend/data/system/decision_log.json")
        self._decision_log_file.parent.mkdir(parents=True, exist_ok=True)
        
        monitor_logger.info("🎯 Monitoring Service initialized")
    
    def start(self, interval: int = 10) -> Dict:
        """
        Start monitoring in background
        
        Args:
            interval: Check interval in seconds
                - 60 = 1 min candle
                - 300 = 5 min candle
                - 900 = 15 min candle
                - 3600 = 1 uur candle
                - 14400 = 4 uur candle
        """
        with self._lock:
            if self._running:
                monitor_logger.warning("⚠️ Monitor already running")
                return {
                    "success": False,
                    "message": "Monitor draait al",
                    "status": self.get_status()
                }
            
            # Validate interval (min 10 sec, max 24 hours)
            if interval < 10 or interval > 86400:
                return {
                    "success": False,
                    "message": "Interval moet tussen 10 seconden en 24 uur zijn",
                    "status": self.get_status()
                }
            
            # Set interval
            self._interval = interval
            
            # Reset events
            self._stop_event.clear()
            self._pause_event.clear()
            
            # Start background thread
            self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self._thread.start()
            
            self._running = True
            self._paused = False
            self._start_time = datetime.now(timezone.utc)
            self._cycles_completed = 0
            
            # Get interval label for logging
            interval_label = self._get_interval_label(interval)
            
            monitor_logger.info(f"▶️ Monitor STARTED (interval: {interval_label})")
            
            return {
                "success": True,
                "message": f"▶️ Monitor gestart (interval: {interval_label})",
                "status": self.get_status()
            }
    
    def stop(self) -> Dict:
        """Stop monitoring - FORCE STOP"""
        with self._lock:
            if not self._running:
                monitor_logger.warning("⚠️ Monitor is not running")
                return {
                    "success": False,
                    "message": "Monitor draait niet",
                    "status": self.get_status()
                }
            
            # Signal stop
            self._stop_event.set()
            self._running = False
            self._paused = False
            
            # Wait for thread to finish (max 5 sec)
            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=5)
            
            # FORCE RESET ALL STATE
            self._thread = None
            self._start_time = None
            self._cycles_completed = 0
            self._interval = 3600  # Reset to default
            
            monitor_logger.info(f"⏹️ Monitor STOPPED - COMPLETE RESET")
            
            return {
                "success": True,
                "message": f"⏹️ Monitor gestopt (complete reset)",
                "status": self.get_status()
            }
    
    def pause(self) -> Dict:
        """Pause monitoring (kan resumed worden)"""
        with self._lock:
            if not self._running:
                return {
                    "success": False,
                    "message": "Monitor draait niet",
                    "status": self.get_status()
                }
            
            if self._paused:
                # Resume
                self._pause_event.clear()
                self._paused = False
                monitor_logger.info("▶️ Monitor RESUMED")
                return {
                    "success": True,
                    "message": "▶️ Monitor hervat",
                    "status": self.get_status()
                }
            else:
                # Pause
                self._pause_event.set()
                self._paused = True
                monitor_logger.info("⏸️ Monitor PAUSED")
                return {
                    "success": True,
                    "message": "⏸️ Monitor gepauzeerd",
                    "status": self.get_status()
                }
    
    def get_status(self) -> Dict:
        """Get current monitoring status"""
        uptime = None
        if self._start_time and self._running:
            uptime = (datetime.now(timezone.utc) - self._start_time).total_seconds()
        
        return {
            "running": self._running,
            "paused": self._paused,
            "cycles_completed": self._cycles_completed,
            "start_time": self._start_time.isoformat() if self._start_time else None,
            "uptime_seconds": uptime,
            "thread_alive": self._thread.is_alive() if self._thread else False,
            "interval_seconds": self._interval,
            "interval_label": self._get_interval_label(self._interval) if self._running else None
        }
    
    def _log_decision(self, decision: Dict, cycle: int, price: float, executed: bool = False):
        """Log een beslissing naar JSON file"""
        try:
            # Load existing log
            if self._decision_log_file.exists():
                with open(self._decision_log_file, 'r') as f:
                    log_data = json.load(f)
            else:
                log_data = {"decisions": []}
            
            # Add new decision
            log_entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "cycle": cycle,
                "action": decision['action'],
                "price": price,
                "reason": decision['reason'],
                "executed": executed,
                "pnl": decision.get('pnl'),
                "position": decision.get('position_state', {}).get('position_type', 'NONE')
            }
            
            log_data["decisions"].insert(0, log_entry)  # Newest first
            
            # Keep only last 100
            log_data["decisions"] = log_data["decisions"][:100]
            
            # Save
            with open(self._decision_log_file, 'w') as f:
                json.dump(log_data, f, indent=2)
                
        except Exception as e:
            monitor_logger.error(f"Error logging decision: {e}")
    
    def get_decisions(self, limit: int = 50) -> Dict:
        """Haal laatste decisions op"""
        try:
            if not self._decision_log_file.exists():
                return {"success": True, "decisions": []}
            
            with open(self._decision_log_file, 'r') as f:
                log_data = json.load(f)
            
            decisions = log_data.get("decisions", [])[:limit]
            
            return {
                "success": True,
                "decisions": decisions,
                "total": len(decisions)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "decisions": []
            }
    
    def _get_interval_label(self, seconds: int) -> str:
        """Convert seconds to readable label"""
        if seconds == 60:
            return "1 min candle"
        elif seconds == 300:
            return "5 min candle"
        elif seconds == 900:
            return "15 min candle"
        elif seconds == 3600:
            return "1 uur candle"
        elif seconds == 14400:
            return "4 uur candle"
        elif seconds == 86400:
            return "1 dag candle"
        elif seconds < 60:
            return f"{seconds} sec"
        elif seconds < 3600:
            return f"{seconds // 60} min"
        else:
            return f"{seconds // 3600} uur"
    
    def _monitor_loop(self):
        """
        Main monitoring loop (runs in background thread)
        
        Voor trading:
        - 1 min candle: Check elke 60 sec
        - 5 min candle: Check elke 300 sec
        - 15 min candle: Check elke 900 sec
        - 1 uur candle: Check elke 3600 sec
        
        LIVE TRADING INTEGRATIE:
        - Fetch BCH candles van Bitvavo
        - Run SparkDecisionEngine
        - Execute trades via LiveTraderService
        - Send notifications
        """
        monitor_logger.info(f"🔄 Monitor loop started (interval: {self._interval}s)")
        
        # Import trading services
        from services.bitvavo_service import BitvavoService
        from services.spark_decision_engine import SparkDecisionEngine, PositionState
        from services.live_trader_service import LiveTraderService
        from services.notification_service import NotificationService
        
        # Trading state
        position_state = PositionState()
        trading_locked = False
        # Pre-load context candles (100 stuks voor Bollinger Bands)
        try:
            interval_map = {
                60: '1m',
                300: '5m',
                900: '15m',
                3600: '1h',
                14400: '4h',
                86400: '1d'
            }
            bitvavo_interval = interval_map.get(self._interval, '1h')
            
            monitor_logger.info(f"📚 Pre-loading context: Fetching 100 candles ({bitvavo_interval})...")
            
            context_result = BitvavoService.get_candles(
                market="BCH-EUR",
                interval=bitvavo_interval,
                limit=100
            )
            
            if context_result and context_result.get('success'):
                context_candles = context_result.get('candles', [])
                monitor_logger.info(f"✅ Pre-loaded {len(context_candles)} candles for context")
            else:
                monitor_logger.warning("⚠️ Failed to pre-load context, starting with empty")
                context_candles = []
        except Exception as e:
            monitor_logger.error(f"Error pre-loading context: {e}")
            context_candles = []
        
        # Load historical trading context (support/resistance/trend)
        monitor_logger.info("🧠 Loading historical trading context...")
        try:
            historical_context = get_trading_context(context_candles, use_cache=True)
            
            # LOG CONTEXT DETAILS
            if historical_context:
                monitor_logger.info("=" * 60)
                monitor_logger.info("📊 HISTORICAL CONTEXT LOADED:")
                monitor_logger.info(f"   Market State: {historical_context['market_state']['trend'].upper()} (confidence: {historical_context['market_state']['confidence']:.2f})")
                monitor_logger.info(f"   Duration: {historical_context['market_state']['duration_days']} days")
                
                if historical_context['support_levels']:
                    monitor_logger.info(f"   Support Levels ({len(historical_context['support_levels'])}):")
                    for sup in historical_context['support_levels'][:3]:
                        monitor_logger.info(f"     • €{sup['price']} (strength: {sup['strength']:.2f}, {sup['bounces']} bounces, {sup['days_ago']:.0f}d ago)")
                
                if historical_context['resistance_levels']:
                    monitor_logger.info(f"   Resistance Levels ({len(historical_context['resistance_levels'])}):")
                    for res in historical_context['resistance_levels'][:3]:
                        monitor_logger.info(f"     • €{res['price']} (strength: {res['strength']:.2f}, {res['tests']} tests, {res['days_ago']:.0f}d ago)")
                
                monitor_logger.info("=" * 60)
            else:
                monitor_logger.warning("⚠️ No historical context available")
                
        except Exception as e:
            monitor_logger.error(f"⚠️ Failed to load historical context: {e}")
            historical_context = None
        
        while not self._stop_event.is_set():
            # Check if paused
            if self._pause_event.is_set():
                monitor_logger.debug("⏸️ Monitor paused, waiting...")
                time.sleep(1)
                continue
            
            # === LIVE TRADING LOGIC ===
            self._cycles_completed += 1
            
            try:
                # 1. Fetch latest BCH candle
                # Map seconds to Bitvavo interval format
                interval_map = {
                    60: '1m',
                    300: '5m',
                    900: '15m',
                    3600: '1h',
                    14400: '4h',
                    86400: '1d'
                }
                bitvavo_interval = interval_map.get(self._interval, '1h')  # Default 1h
                
                candle_result = BitvavoService.get_candles(
                    market="BCH-EUR",
                    interval=bitvavo_interval,
                    limit=1
                )
                
                if not candle_result or not candle_result.get('success'):
                    monitor_logger.warning("⚠️ Failed to fetch candles, skipping cycle")
                    time.sleep(self._interval)
                    continue
                
                candle_data = candle_result.get('candles', [])
                if len(candle_data) == 0:
                    monitor_logger.warning("⚠️ No candle data received, skipping cycle")
                    time.sleep(self._interval)
                    continue
                
                latest_candle = candle_data[0]
                current_price = float(latest_candle['close'])
                
                monitor_logger.info(
                    f"💓 Cycle #{self._cycles_completed} | "
                    f"BCH: €{current_price:.2f} | "
                    f"Position: {position_state.position_type}"
                )
                
                # 2. Build context (keep last 50 candles)
                if len(context_candles) >= 50:
                    context_candles.pop(0)
                context_candles.append(latest_candle)
                
                # 3. Run decision engine (MET historical context)
                decision = SparkDecisionEngine.analyze_candle(
                    candle={
                        "timestamp": latest_candle['timestamp'],
                        "open": float(latest_candle['open']),
                        "high": float(latest_candle['high']),
                        "low": float(latest_candle['low']),
                        "close": float(latest_candle['close']),
                        "volume": float(latest_candle['volume'])
                    },
                    context=context_candles,
                    position_state=position_state,
                    trading_locked=trading_locked,
                    historical_context=historical_context  # ← Context weging!
                )
                
                # Calculate support/resistance proximity
                support_near = None
                resistance_near = None
                
                if historical_context and historical_context.get('support_levels'):
                    for sup in historical_context['support_levels']:
                        distance_pct = abs(current_price - sup['price']) / sup['price'] * 100
                        if distance_pct < 2:  # Within 2%
                            support_near = {"price": sup['price'], "strength": sup['strength'], "distance_pct": round(distance_pct, 2)}
                            break
                
                if historical_context and historical_context.get('resistance_levels'):
                    for res in historical_context['resistance_levels']:
                        distance_pct = abs(current_price - res['price']) / res['price'] * 100
                        if distance_pct < 2:  # Within 2%
                            resistance_near = {"price": res['price'], "strength": res['strength'], "distance_pct": round(distance_pct, 2)}
                            break
                
                # LOG PER CANDLE: price, signal, confidence, support_near, trend
                trend = historical_context['market_state']['trend'] if historical_context else "unknown"
                trend_conf = historical_context['market_state']['confidence'] if historical_context else 0
                
                monitor_logger.info("─" * 60)
                monitor_logger.info(f"💓 Cycle #{self._cycles_completed}")
                monitor_logger.info(f"   Price: €{current_price:.2f}")
                monitor_logger.info(f"   Signal: {decision['action']}")
                monitor_logger.info(f"   Reason: {decision['reason']}")
                monitor_logger.info(f"   Trend: {trend.upper()} ({trend_conf:.2f})")
                if support_near:
                    monitor_logger.info(f"   Support Near: €{support_near['price']} (strength {support_near['strength']:.2f}, {support_near['distance_pct']}% away)")
                if resistance_near:
                    monitor_logger.info(f"   Resistance Near: €{resistance_near['price']} (strength {resistance_near['strength']:.2f}, {resistance_near['distance_pct']}% away)")
                monitor_logger.info("─" * 60)
                
                # Log decision (ALTIJD, ook bij HOLD)
                executed = False
                
                # 4. Execute trade if BUY/SELL
                if decision['action'] in ['BUY', 'SELL']:
                    monitor_logger.info(f"🎯 {decision['action']} signal detected!")
                    monitor_logger.info(f"   Reason: {decision['reason']}")
                    
                    # Execute via LiveTraderService
                    execution = LiveTraderService.execute_decision(
                        decision=decision,
                        user_id="user-001",
                        run_id="monitor-001",
                        market="BCH-EUR"
                    )
                    
                    if execution.get('success'):
                        monitor_logger.info(f"✅ Trade executed: {decision['action']}")
                        executed = True
                        
                        # Send notification
                        if decision['action'] == 'SELL':
                            pnl = decision.get('pnl', {})
                            profit = pnl.get('pnl_eur', 0)
                            
                            if profit > 0:
                                NotificationService.send_trade_profit_alert(
                                    profit_eur=profit,
                                    trade_data={
                                        'price': current_price,
                                        'pot': position_state.current_pot
                                    }
                                )
                            else:
                                NotificationService.send_trade_loss_alert(
                                    loss_eur=abs(profit),
                                    trade_data={
                                        'price': current_price,
                                        'pot': position_state.current_pot
                                    }
                                )
                    else:
                        monitor_logger.error(f"❌ Trade failed: {execution.get('error')}")
                
                # Check for trading lock
                if decision.get('lock_triggered'):
                    trading_locked = True
                    monitor_logger.warning("🔒 Trading locked (loss > 3%)")
                
                # Log decision to file (ALTIJD)
                self._log_decision(decision, self._cycles_completed, current_price, executed)
                
            except Exception as e:
                monitor_logger.error(f"❌ Error in trading cycle: {e}")
            
            # Sleep voor interval tijd
            elapsed = 0
            while elapsed < self._interval and not self._stop_event.is_set():
                time.sleep(1)
                elapsed += 1
        
        monitor_logger.info("🔄 Monitor loop stopped")


# Singleton instance
_monitoring_service = MonitoringService()


def get_monitoring_service() -> MonitoringService:
    """Get singleton monitoring service"""
    return _monitoring_service


# Quick test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    service = get_monitoring_service()
    
    print("Testing Monitoring Service...")
    print("\n1. Start monitor")
    print(service.start())
    
    time.sleep(5)
    
    print("\n2. Status check")
    print(service.get_status())
    
    print("\n3. Pause monitor")
    print(service.pause())
    
    time.sleep(3)
    
    print("\n4. Resume monitor")
    print(service.pause())
    
    time.sleep(3)
    
    print("\n5. Stop monitor")
    print(service.stop())
    
    print("\n6. Final status")
    print(service.get_status())
