"""
Live Trader Service - Executes trading decisions
Integrates decision engine met trade execution
"""
import os
import logging
from datetime import datetime
from typing import Dict, Optional
from services.spark_decision_engine import SparkDecisionEngine, PositionState
from services.mock_trading_service import MockTradingService
from services.replay_log_service import ReplayLogService
from services.trade_history_service import TradeHistoryService
from utils.logger import SparkLogger
from utils.data_manager import DataManager

# Setup logger
logger = logging.getLogger(__name__)


# TOGGLE: Use mock trading (True) or real API (False)
USE_MOCK_TRADING = os.environ.get("USE_MOCK_TRADING", "true").lower() == "true"


class LiveTraderService:
    """
    Live Trading Service
    - Executes BUY/SELL decisions from engine
    - Tracks open positions
    - Safety checks
    - Reset functionality
    """
    
    @staticmethod
    def execute_decision(
        decision: Dict,
        user_id: str,
        run_id: str,
        market: str = "BCH-EUR",
        config: Optional[Dict] = None
    ) -> Dict:
        """
        Execute een trading decision (BUY/SELL)
        
        Args:
            decision: Decision van SparkDecisionEngine
            user_id: User ID
            run_id: Monitor run ID
            market: Trading market
            config: Trading config
        
        Returns:
            Execution result
        """
        action = decision.get("action")
        
        if action not in ["BUY", "SELL"]:
            return {
                "success": False,
                "action": action,
                "reason": "No trade action (HOLD)"
            }
        
        # Get trade amount from config or decision
        if not config:
            config = SparkDecisionEngine.DEFAULT_CONFIG
        
        trade_amount_eur = config.get("trade_amount", 5.0)
        
        # Extract price from decision (can be in root or indicators)
        price = decision.get("price", 0.0)
        if price == 0.0 and "indicators" in decision:
            price = decision["indicators"].get("price", 0.0)
        
        # LOG EXACT TRADE DETAILS
        logger.info("=" * 60)
        logger.info(f"[TRADE PREP] Preparing {action} order")
        logger.info(f"  Price from decision: €{price:.2f}")
        logger.info(f"  Trade amount: €{trade_amount_eur}")
        logger.info(f"  Decision keys: {list(decision.keys())}")
        if "indicators" in decision:
            logger.info(f"  Indicators: {decision['indicators'].keys()}")
        logger.info("=" * 60)
        
        # For SELL, we need BCH amount, not EUR
        if action == "SELL":
            # Check if position_update has the BCH amount
            position_update = decision.get("position_update", {})
            if position_update and "trade_amount" in position_update:
                # trade_amount in position is in BCH for sells
                trade_amount = position_update.get("trade_amount", 0)
                if trade_amount == 0:
                    # Fallback: calculate from EUR amount
                    trade_amount = trade_amount_eur / price if price > 0 else 0
            else:
                # Calculate BCH amount from EUR
                trade_amount = trade_amount_eur / price if price > 0 else 0
        else:
            # For BUY, use EUR amount
            trade_amount = trade_amount_eur
        
        # Safety checks before execution
        safety_check = LiveTraderService._pre_trade_safety_check(
            user_id=user_id,
            action=action,
            amount=trade_amount,
            price=price
        )
        
        if not safety_check.get("safe"):
            SparkLogger.log_system_event(
                f"[TRADE BLOCKED] Safety check failed | "
                f"User: {user_id} | Action: {action} | "
                f"Reason: {safety_check.get('reason')}"
            )
            return {
                "success": False,
                "action": action,
                "error": f"Safety check failed: {safety_check.get('reason')}"
            }
        
        # Execute trade (mock or real)
        try:
            if USE_MOCK_TRADING:
                result = LiveTraderService._execute_mock_trade(
                    action=action,
                    user_id=user_id,
                    market=market,
                    amount=trade_amount,
                    price=price
                )
            else:
                result = LiveTraderService._execute_real_trade(
                    action=action,
                    user_id=user_id,
                    market=market,
                    amount=trade_amount,
                    price=price
                )
            
            # Add metadata to result
            result["action"] = action
            result["user_id"] = user_id
            result["run_id"] = run_id
            
            # Log result
            if result.get("success"):
                SparkLogger.log_system_event(
                    f"[LIVE TRADE] {action} executed | "
                    f"Order: {result.get('order_id')} | "
                    f"Amount: €{trade_amount} | "
                    f"Price: €{price:.2f} | "
                    f"Mock: {result.get('mock', False)}"
                )
                
                # Log to trade history
                TradeHistoryService.log_trade(
                    user_id=user_id,
                    run_id=run_id,
                    trade_data=result
                )
            else:
                SparkLogger.log_system_event(
                    f"[LIVE TRADE ERROR] {action} failed | "
                    f"Error: {result.get('error')}"
                )
            
            return result
            
        except Exception as e:
            error_msg = f"Trade execution exception: {str(e)}"
            SparkLogger.log_system_event(f"[TRADE EXCEPTION] {error_msg}")
            return {
                "success": False,
                "action": action,
                "error": error_msg
            }
    
    @staticmethod
    def _execute_mock_trade(
        action: str,
        user_id: str,
        market: str,
        amount: float,
        price: float
    ) -> Dict:
        """Execute mock trade (for testing)"""
        if action == "BUY":
            return MockTradingService.mock_buy(
                user_id=user_id,
                market=market,
                amount=amount,
                price=price
            )
        elif action == "SELL":
            return MockTradingService.mock_sell(
                user_id=user_id,
                market=market,
                amount=amount,
                price=price
            )
        
        return {"success": False, "error": "Unknown action"}
    
    @staticmethod
    def _execute_real_trade(
        action: str,
        user_id: str,
        market: str,
        amount: float,
        price: float
    ) -> Dict:
        """
        Execute REAL trade via Bitvavo API
        
        Args:
            action: "BUY" or "SELL"
            user_id: User ID
            market: Trading market (e.g. "BCH-EUR")
            amount: Trade amount in EUR
            price: Current price (for logging only, market order used)
        
        Returns:
            Trade execution result
        """
        from services.bitvavo_service import BitvavoService
        
        try:
            # Use market order for immediate execution
            result = BitvavoService.place_market_order(
                user_id=user_id,
                market=market,
                side=action.lower(),  # "buy" or "sell"
                amount=amount
            )
            
            # Add metadata
            if result.get("success"):
                result["mock"] = False
                result["market"] = market
            
            return result
            
        except Exception as e:
            error_msg = f"Real trade execution failed: {str(e)}"
            SparkLogger.log_system_event(f"[REAL TRADE ERROR] {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "action": action,
                "mock": False
            }
    
    @staticmethod
    def sync_position_with_exchange(
        user_id: str,
        run_id: str,
        market: str = "BCH-EUR"
    ) -> Dict:
        """
        Synchroniseer interne position state met echte exchange balance
        
        Gebruik bij:
        - Start van monitoring (automatisch)
        - Na manual trades buiten de bot
        - Na crashes/restarts
        
        Returns:
            {
                "success": True,
                "synced": True/False,
                "exchange_balance": 0.048,
                "position_initialized": True/False
            }
        """
        from services.bitvavo_service import BitvavoService
        from services.spark_decision_engine import SparkDecisionEngine
        
        try:
            # Get current exchange balance
            balance_result = BitvavoService.get_balance(user_id)
            
            if not balance_result.get("success"):
                return {
                    "success": False,
                    "error": "Failed to fetch exchange balance"
                }
            
            # Find BCH balance
            coin = market.split("-")[0]  # "BCH-EUR" -> "BCH"
            bch_balance = 0.0
            
            for bal in balance_result.get("balances", []):
                if bal["symbol"] == coin:
                    # Balance is string, convert to float
                    bch_balance = float(bal.get("available", 0))
                    break
            
            SparkLogger.log_system_event(
                f"[SYNC] Exchange balance: {bch_balance} {coin}"
            )
            
            # Check if we have a position on exchange
            if bch_balance > 0.001:  # Minimum 0.001 BCH threshold
                # We have a position! Initialize state
                # Get current price for entry price estimate
                ticker = BitvavoService.get_ticker(market)
                current_price = float(ticker.get("price", 0))  # Direct price field
                
                if current_price > 0:
                    # Save position state directly (PositionState is dataclass, not used here)
                    state_path = f"live_trading/{user_id}/runs/{run_id}/position_state.json"
                    DataManager.save_json(state_path, {
                        "is_open": True,
                        "entry_price": current_price,
                        "entry_amount": bch_balance,
                        "entry_time": datetime.now().isoformat(),
                        "synced_from_exchange": True,
                        "note": "Position synced from exchange balance"
                    })
                    
                    SparkLogger.log_system_event(
                        f"[SYNC] Position initialized from exchange | "
                        f"{bch_balance} {coin} @ €{current_price:.2f}"
                    )
                    
                    return {
                        "success": True,
                        "synced": True,
                        "exchange_balance": bch_balance,
                        "position_initialized": True,
                        "entry_price": current_price,
                        "message": f"Position synced: {bch_balance} {coin} @ €{current_price:.2f}"
                    }
            
            # No position on exchange - state is correct
            SparkLogger.log_system_event("[SYNC] No exchange position - state OK")
            
            return {
                "success": True,
                "synced": True,
                "exchange_balance": 0.0,
                "position_initialized": False,
                "message": "No position on exchange"
            }
            
        except Exception as e:
            error_msg = f"Position sync failed: {str(e)}"
            SparkLogger.log_system_event(f"[SYNC ERROR] {error_msg}")
            return {
                "success": False,
                "error": error_msg
            }
    
    @staticmethod
    def reset_position(
        user_id: str,
        run_id: str,
        reason: str = "manual_reset",
        force_sell: bool = False,
        market: str = "BCH-EUR"
    ) -> Dict:
        """
        Reset position state
        
        Args:
            user_id: User ID
            run_id: Monitor run ID
            reason: Reset reason (manual_reset, crash_recovery, etc.)
            force_sell: If True, sell any existing exchange position FIRST
            market: Trading market
        
        Returns:
            Reset result with optional sell execution
        """
        from services.bitvavo_service import BitvavoService
        
        try:
            SparkLogger.log_system_event(
                f"[RESET] Position reset requested | "
                f"User: {user_id} | Run: {run_id} | "
                f"Reason: {reason} | Force sell: {force_sell}"
            )
            
            sold_position = None
            
            # STEP 1: Force sell existing position if requested
            if force_sell:
                # Get exchange balance
                balance_result = BitvavoService.get_balance(user_id)
                
                if balance_result.get("success"):
                    coin = market.split("-")[0]
                    bch_balance = 0.0
                    
                    for bal in balance_result.get("balances", []):
                        if bal["symbol"] == coin:
                            # Balance is string, convert to float
                            bch_balance = float(bal.get("available", 0))
                            break
                    
                    # Sell if we have a position
                    if bch_balance > 0.001:
                        SparkLogger.log_system_event(
                            f"[RESET] Selling existing position: {bch_balance} {coin}"
                        )
                        
                        # Check if mock or live mode
                        if USE_MOCK_TRADING:
                            from services.mock_trading_service import MockTradingService
                            sell_result = MockTradingService.mock_sell(
                                user_id=user_id,
                                market=market,
                                amount=bch_balance,
                                price=0.0  # Market price
                            )
                        else:
                            # Real sell
                            sell_result = BitvavoService.place_market_order(
                                user_id=user_id,
                                market=market,
                                side="sell",
                                amount=bch_balance
                            )
                        
                        if sell_result.get("success"):
                            sold_position = {
                                "amount": bch_balance,
                                "order_id": sell_result.get("order_id"),
                                "price": sell_result.get("price", 0)
                            }
                            
                            SparkLogger.log_system_event(
                                f"[RESET] Position sold: {bch_balance} {coin} | "
                                f"Order: {sell_result.get('order_id')}"
                            )
                            
                            # Log to trade history
                            from services.trade_history_service import TradeHistoryService
                            TradeHistoryService.log_trade(
                                user_id=user_id,
                                run_id=run_id,
                                trade_data={
                                    **sell_result,
                                    "action": "SELL",
                                    "reason": f"Reset with force_sell ({reason})",
                                    "market": market
                                }
                            )
                        else:
                            SparkLogger.log_system_event(
                                f"[RESET ERROR] Failed to sell position: {sell_result.get('error')}"
                            )
                    else:
                        SparkLogger.log_system_event(
                            "[RESET] No position to sell on exchange"
                        )
            
            # STEP 2: Reset internal state
            # Log reset
            SparkLogger.log_system_event(
                f"[POSITION RESET] User: {user_id} | "
                f"Run: {run_id} | "
                f"Reason: {reason}"
            )
            
            # Load current run
            log_path = f"wallet/replay_logs/{run_id}.json"
            run_data = DataManager.load_json(log_path)
            
            if not run_data:
                return {
                    "success": False,
                    "error": "Run not found"
                }
            
            # Mark position as reset
            run_data["position_reset"] = {
                "timestamp": datetime.now().isoformat(),
                "reason": reason
            }
            
            # Clear position state in last decision
            if run_data.get("decisions_v1"):
                last_decision = run_data["decisions_v1"][-1]
                last_decision["position_reset"] = True
                last_decision["reset_reason"] = reason
            
            # Save updated run
            DataManager.save_json(log_path, run_data)
            
            return {
                "success": True,
                "reset": True,
                "reason": reason,
                "force_sell_executed": force_sell,
                "sold_position": sold_position,
                "message": f"Position reset complete ({reason})",
                "run_id": run_id,
                "timestamp": datetime.now().isoformat()
            }
        
        except Exception as e:
            SparkLogger.log_system_event(f"[POSITION RESET ERROR] {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def get_trading_status(user_id: str) -> Dict:
        """
        Get current trading status
        
        Returns:
            Status info (mock mode, active positions, etc.)
        """
        return {
            "success": True,
            "mock_mode": USE_MOCK_TRADING,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def _pre_trade_safety_check(
        user_id: str,
        action: str,
        amount: float,
        price: float
    ) -> Dict:
        """
        Pre-trade safety checks
        
        Returns:
            {"safe": True/False, "reason": "..."}
        """
        # Check minimum trade amount
        if amount <= 0:
            return {
                "safe": False,
                "reason": "Invalid trade amount (must be > 0)"
            }
        
        # Check minimum price
        if price <= 0:
            return {
                "safe": False,
                "reason": "Invalid price (must be > 0)"
            }
        
        # Check maximum single trade amount (safety limit)
        MAX_SINGLE_TRADE = 100.0  # €100 max per trade
        if amount > MAX_SINGLE_TRADE:
            return {
                "safe": False,
                "reason": f"Trade amount exceeds limit: €{amount} > €{MAX_SINGLE_TRADE}"
            }
        
        # All checks passed
        return {
            "safe": True,
            "reason": "Pre-trade safety checks passed"
        }
    
    @staticmethod
    def check_safety_limits(
        user_id: str,
        position_state: PositionState,
        config: Dict
    ) -> Dict:
        """
        Check safety limits (max loss, balance, etc.)
        
        Returns:
            {"safe": True/False, "reason": "..."}
        """
        # Check max loss
        max_loss = config.get("max_loss_percent", 3.0)
        
        if position_state.entry_price > 0:
            current_loss = position_state.unrealized_loss_percent
            
            if abs(current_loss) > max_loss:
                return {
                    "safe": False,
                    "reason": f"Max loss exceeded: {current_loss:.2f}% > {max_loss}%"
                }
        
        # TODO: Check balance (when real API is used)
        
        return {
            "safe": True,
            "reason": "All safety checks passed"
        }
