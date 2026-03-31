"""
Mock Trading Service - Placeholder voor testing
Simuleert buy/sell zonder echte API calls
"""
import time
from datetime import datetime
from typing import Dict, Optional
from utils.logger import SparkLogger


class MockTradingService:
    """
    Mock trading voor testing - geen echte trades
    Replace later met echte Bitvavo API calls
    """
    
    # Simulated order counter
    _order_counter = 1000
    
    @staticmethod
    def mock_buy(
        user_id: str,
        market: str,
        amount: float,
        price: Optional[float] = None
    ) -> Dict:
        """
        MOCK: Simuleer BUY order
        
        Args:
            user_id: User ID
            market: Market (bijv. "BCH-EUR")
            amount: Amount in EUR
            price: Optional limit price (None = market order)
        
        Returns:
            {"success": True, "order_id": "...", "filled": amount}
        """
        MockTradingService._order_counter += 1
        order_id = f"MOCK-BUY-{MockTradingService._order_counter}"
        
        # Simulate small delay
        time.sleep(0.1)
        
        result = {
            "success": True,
            "order_id": order_id,
            "market": market,
            "side": "buy",
            "amount": amount,
            "filled": amount,
            "price": price if price else 0.0,
            "timestamp": datetime.now().isoformat(),
            "status": "filled",
            "mock": True,
            "fees": amount * 0.0025  # 0.25% mock fees
        }
        
        SparkLogger.log_system_event(
            f"[MOCK TRADE] BUY €{amount} on {market} @ €{price:.2f} | "
            f"Order: {order_id} | User: {user_id}"
        )
        
        return result
    
    @staticmethod
    def mock_sell(
        user_id: str,
        market: str,
        amount: float,
        price: Optional[float] = None
    ) -> Dict:
        """
        MOCK: Simuleer SELL order
        
        Args:
            user_id: User ID
            market: Market (bijv. "BCH-EUR")
            amount: Amount in coins/EUR
            price: Optional limit price (None = market order)
        
        Returns:
            {"success": True, "order_id": "...", "filled": amount}
        """
        MockTradingService._order_counter += 1
        order_id = f"MOCK-SELL-{MockTradingService._order_counter}"
        
        # Simulate small delay
        time.sleep(0.1)
        
        result = {
            "success": True,
            "order_id": order_id,
            "market": market,
            "side": "sell",
            "amount": amount,
            "filled": amount,
            "price": price if price else 0.0,
            "timestamp": datetime.now().isoformat(),
            "status": "filled",
            "mock": True,
            "fees": amount * 0.0025  # 0.25% mock fees
        }
        
        SparkLogger.log_system_event(
            f"[MOCK TRADE] SELL {amount:.6f} coins on {market} @ €{price:.2f} | "
            f"Order: {order_id} | User: {user_id}"
        )
        
        return result
    
    @staticmethod
    def get_mock_balance(user_id: str) -> Dict:
        """
        MOCK: Simuleer balance
        
        Returns:
            Fake balance voor testing
        """
        return {
            "success": True,
            "balance": {
                "EUR": {"available": "1000.00"},
                "BCH": {"available": "0.5"}
            },
            "mock": True
        }
    
    @staticmethod
    def check_order_status(user_id: str, order_id: str) -> Dict:
        """
        MOCK: Check order status
        
        Returns:
            Always returns "filled" voor mock orders
        """
        if order_id.startswith("MOCK-"):
            return {
                "success": True,
                "order_id": order_id,
                "status": "filled",
                "filled": 100.0,
                "mock": True
            }
        
        return {
            "success": False,
            "error": "Order not found",
            "mock": True
        }
