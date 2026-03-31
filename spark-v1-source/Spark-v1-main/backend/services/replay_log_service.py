"""
Replay Log Service
Opslag en beheer van live trading runs voor replay functionaliteit
"""
import os
import json
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

REPLAY_LOGS_DIR = "/app/backend/data/wallet/replay_logs"


class ReplayLogService:
    """
    Beheert opslag van live runs en replay logs
    """
    
    @staticmethod
    def _ensure_directory():
        """Zorg dat replay logs directory bestaat"""
        os.makedirs(REPLAY_LOGS_DIR, exist_ok=True)
    
    @staticmethod
    def create_run(user_id: str, coin: str, config: Dict) -> str:
        """
        Start nieuwe live run
        
        Args:
            user_id: User ID
            coin: Crypto symbol (BTC, ETH, etc)
            config: Decision engine config
            
        Returns:
            run_id: Unique identifier voor deze run
        """
        ReplayLogService._ensure_directory()
        
        timestamp = int(datetime.now().timestamp())
        run_id = f"run_{user_id}_{coin}_{timestamp}"
        
        log_data = {
            "run_id": run_id,
            "user_id": user_id,
            "coin": coin,
            "start_time": datetime.now().isoformat(),
            "config": config,
            "candles": [],
            "decisions_v1": [],  # Live decisions
            "decisions_v2": [],  # Replay recalculation (leeg bij aanmaak)
            "position_state": {
                "position_type": "NONE",
                "entry_price": None,
                "entry_time": None,
                "highest_price": None,
                "trade_amount": config.get("trade_amount", 5.0),
                "trailing_stop_active": False
            },
            "trading_locked": False,
            "total_pnl": 0.0,
            "trade_history": [],
            "status": "active"
        }
        
        filepath = os.path.join(REPLAY_LOGS_DIR, f"{run_id}.json")
        with open(filepath, 'w') as f:
            json.dump(log_data, f, indent=2)
        
        logger.info(f"[REPLAY] Created new run: {run_id}")
        return run_id
    
    @staticmethod
    def append_candle_and_decision(
        run_id: str,
        candle: Dict,
        decision: Dict
    ) -> bool:
        """
        Voeg candle + decision toe aan active run
        + Update position state + trading lock
        
        Args:
            run_id: Run identifier
            candle: Candle data
            decision: Decision engine output
            
        Returns:
            Success boolean
        """
        try:
            filepath = os.path.join(REPLAY_LOGS_DIR, f"{run_id}.json")
            
            if not os.path.exists(filepath):
                logger.error(f"[REPLAY] Run not found: {run_id}")
                return False
            
            with open(filepath, 'r') as f:
                log_data = json.load(f)
            
            # Append nieuwe data
            log_data["candles"].append(candle)
            log_data["decisions_v1"].append({
                "timestamp": candle["timestamp"],
                **decision
            })
            
            # Update position state
            if "position_update" in decision:
                log_data["position_state"] = decision["position_update"]
            
            # Update trading lock
            if decision.get("lock_triggered", False):
                log_data["trading_locked"] = True
                logger.warning(f"[REPLAY] Trading lock activated for run {run_id}")
            
            # Track trade history (entry/exit)
            if decision["action"] == "BUY" and decision.get("position_update", {}).get("position_type") == "LONG":
                log_data["trade_history"].append({
                    "type": "ENTRY",
                    "timestamp": candle["timestamp"],
                    "price": candle["close"],
                    "reason": decision["reason"]
                })
            elif decision["action"] == "SELL":
                pnl = decision.get("pnl", {})
                log_data["trade_history"].append({
                    "type": "EXIT",
                    "timestamp": candle["timestamp"],
                    "price": candle["close"],
                    "pnl_eur": pnl.get("pnl_eur", 0),
                    "pnl_percent": pnl.get("pnl_percent", 0),
                    "reason": decision["reason"]
                })
                log_data["total_pnl"] += pnl.get("pnl_eur", 0)
            
            # Update timestamp
            log_data["last_update"] = datetime.now().isoformat()
            
            with open(filepath, 'w') as f:
                json.dump(log_data, f, indent=2)
            
            return True
        
        except Exception as e:
            logger.error(f"[REPLAY] Error appending to run {run_id}: {e}")
            return False
    
    @staticmethod
    def stop_run(run_id: str) -> bool:
        """
        Stop active run (mark as completed)
        
        Args:
            run_id: Run identifier
            
        Returns:
            Success boolean
        """
        try:
            filepath = os.path.join(REPLAY_LOGS_DIR, f"{run_id}.json")
            
            if not os.path.exists(filepath):
                return False
            
            with open(filepath, 'r') as f:
                log_data = json.load(f)
            
            log_data["status"] = "completed"
            log_data["end_time"] = datetime.now().isoformat()
            
            with open(filepath, 'w') as f:
                json.dump(log_data, f, indent=2)
            
            logger.info(f"[REPLAY] Stopped run: {run_id}")
            return True
        
        except Exception as e:
            logger.error(f"[REPLAY] Error stopping run {run_id}: {e}")
            return False
    
    @staticmethod
    def reset_trading_lock(run_id: str) -> bool:
        """
        Reset trading lock (handmatige actie)
        
        Args:
            run_id: Run identifier
            
        Returns:
            Success boolean
        """
        try:
            filepath = os.path.join(REPLAY_LOGS_DIR, f"{run_id}.json")
            
            if not os.path.exists(filepath):
                return False
            
            with open(filepath, 'r') as f:
                log_data = json.load(f)
            
            log_data["trading_locked"] = False
            log_data["lock_reset_time"] = datetime.now().isoformat()
            
            with open(filepath, 'w') as f:
                json.dump(log_data, f, indent=2)
            
            logger.info(f"[REPLAY] Trading lock reset for run: {run_id}")
            return True
        
        except Exception as e:
            logger.error(f"[REPLAY] Error resetting lock for run {run_id}: {e}")
            return False
    
    @staticmethod
    def load_run(run_id: str) -> Optional[Dict]:
        """
        Laad opgeslagen run
        
        Args:
            run_id: Run identifier
            
        Returns:
            Run data dict or None
        """
        try:
            filepath = os.path.join(REPLAY_LOGS_DIR, f"{run_id}.json")
            
            if not os.path.exists(filepath):
                logger.error(f"[REPLAY] Run not found: {run_id}")
                return None
            
            with open(filepath, 'r') as f:
                return json.load(f)
        
        except Exception as e:
            logger.error(f"[REPLAY] Error loading run {run_id}: {e}")
            return None
    
    @staticmethod
    def list_user_runs(user_id: str) -> List[Dict]:
        """
        Lijst alle runs voor een user
        
        Args:
            user_id: User ID
            
        Returns:
            List of run summaries
        """
        ReplayLogService._ensure_directory()
        
        runs = []
        for filename in os.listdir(REPLAY_LOGS_DIR):
            if filename.startswith(f"run_{user_id}_") and filename.endswith(".json"):
                filepath = os.path.join(REPLAY_LOGS_DIR, filename)
                try:
                    with open(filepath, 'r') as f:
                        log_data = json.load(f)
                        runs.append({
                            "run_id": log_data["run_id"],
                            "coin": log_data["coin"],
                            "start_time": log_data["start_time"],
                            "status": log_data.get("status", "unknown"),
                            "candle_count": len(log_data.get("candles", []))
                        })
                except Exception as e:
                    logger.error(f"[REPLAY] Error reading {filename}: {e}")
        
        # Sort by start_time (newest first)
        runs.sort(key=lambda x: x["start_time"], reverse=True)
        return runs
