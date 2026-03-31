"""
Trade History Service - Persistent trade logging
Tracks all executed trades for analysis and auditing
"""
from datetime import datetime
from typing import Dict, List, Optional
from utils.data_manager import DataManager
from utils.logger import SparkLogger


class TradeHistoryService:
    """
    Trade history tracking service
    - Logs all executed trades (mock + real)
    - Provides trade history and statistics
    - Enables auditing and performance analysis
    """
    
    @staticmethod
    def log_trade(
        user_id: str,
        run_id: str,
        trade_data: Dict
    ) -> bool:
        """
        Log een uitgevoerde trade
        
        Args:
            user_id: User ID
            run_id: Monitor run ID
            trade_data: Trade execution result
        
        Returns:
            Success boolean
        """
        try:
            # Load existing history
            history_path = f"wallet/trade_history/{user_id}.json"
            history = DataManager.load_json(history_path) or {
                "user_id": user_id,
                "trades": [],
                "created_at": datetime.now().isoformat()
            }
            
            # Add trade entry
            trade_entry = {
                "trade_id": len(history["trades"]) + 1,
                "run_id": run_id,
                "timestamp": datetime.now().isoformat(),
                "action": trade_data.get("action", "UNKNOWN"),
                "market": trade_data.get("market", "BCH-EUR"),
                "order_id": trade_data.get("order_id"),
                "amount": trade_data.get("amount", 0.0),
                "price": trade_data.get("price", 0.0),
                "filled": trade_data.get("filled", 0.0),
                "status": trade_data.get("status", "unknown"),
                "mock": trade_data.get("mock", False),
                "success": trade_data.get("success", False),
                "error": trade_data.get("error")
            }
            
            history["trades"].append(trade_entry)
            history["last_updated"] = datetime.now().isoformat()
            history["total_trades"] = len(history["trades"])
            
            # Save updated history
            success = DataManager.save_json(history_path, history)
            
            if success:
                SparkLogger.log_system_event(
                    f"[TRADE HISTORY] Trade logged | "
                    f"User: {user_id} | "
                    f"Action: {trade_entry['action']} | "
                    f"Trade ID: {trade_entry['trade_id']}"
                )
            
            return success
            
        except Exception as e:
            SparkLogger.log_system_event(f"[TRADE HISTORY ERROR] {e}")
            return False
    
    @staticmethod
    def get_trade_history(
        user_id: str,
        limit: Optional[int] = None,
        run_id: Optional[str] = None
    ) -> Dict:
        """
        Get trade history voor een user
        
        Args:
            user_id: User ID
            limit: Max aantal trades (newest first)
            run_id: Filter op specifieke run
        
        Returns:
            Trade history data
        """
        try:
            history_path = f"wallet/trade_history/{user_id}.json"
            history = DataManager.load_json(history_path)
            
            if not history:
                return {
                    "success": True,
                    "user_id": user_id,
                    "trades": [],
                    "total_trades": 0
                }
            
            trades = history.get("trades", [])
            
            # Filter by run_id if specified
            if run_id:
                trades = [t for t in trades if t.get("run_id") == run_id]
            
            # Sort by timestamp (newest first)
            trades.sort(key=lambda t: t.get("timestamp", ""), reverse=True)
            
            # Apply limit
            if limit:
                trades = trades[:limit]
            
            return {
                "success": True,
                "user_id": user_id,
                "trades": trades,
                "total_trades": len(history.get("trades", [])),
                "filtered_trades": len(trades)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def get_trade_statistics(user_id: str) -> Dict:
        """
        Get trade statistics voor een user
        
        Returns:
            Statistics (win rate, total PnL, etc.)
        """
        try:
            history_path = f"wallet/trade_history/{user_id}.json"
            history = DataManager.load_json(history_path)
            
            if not history:
                return {
                    "success": True,
                    "total_trades": 0,
                    "buy_count": 0,
                    "sell_count": 0
                }
            
            trades = history.get("trades", [])
            
            # Calculate stats
            buy_count = len([t for t in trades if t.get("action") == "BUY"])
            sell_count = len([t for t in trades if t.get("action") == "SELL"])
            success_count = len([t for t in trades if t.get("success")])
            failed_count = len([t for t in trades if not t.get("success")])
            mock_count = len([t for t in trades if t.get("mock")])
            real_count = len([t for t in trades if not t.get("mock")])
            
            return {
                "success": True,
                "user_id": user_id,
                "total_trades": len(trades),
                "buy_count": buy_count,
                "sell_count": sell_count,
                "success_count": success_count,
                "failed_count": failed_count,
                "mock_count": mock_count,
                "real_count": real_count,
                "success_rate": (success_count / len(trades) * 100) if trades else 0
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
