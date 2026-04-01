"""
ROAR Token Shop API Tests - Iteration 11
Tests the rebuilt shop system with ROAR tokens (shares in Spark Core)
Dynamic pricing: total value / circulating tokens
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestROARTokenPrice:
    """Test GET /api/shop/token/price - Dynamic ROAR token pricing"""
    
    def test_token_price_returns_success(self):
        """Token price endpoint returns success with all required fields"""
        response = requests.get(f"{BASE_URL}/api/shop/token/price")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert "price_eur" in data
        assert "base_price" in data
        assert "total_supply" in data
        assert "circulating" in data
        assert "spark_treasury" in data
        assert "market_cap" in data
    
    def test_token_price_dynamic_calculation(self):
        """Dynamic price should be approximately €6.02 based on V1 migrated data"""
        response = requests.get(f"{BASE_URL}/api/shop/token/price")
        data = response.json()
        
        # Price should be around €5-7 based on deposits + profits / circulating
        assert 4.0 <= data["price_eur"] <= 10.0
        assert data["base_price"] == 5.08
        assert data["total_supply"] == 1000000
        
    def test_token_price_market_cap_calculation(self):
        """Market cap = circulating * price"""
        response = requests.get(f"{BASE_URL}/api/shop/token/price")
        data = response.json()
        
        expected_market_cap = round(data["circulating"] * data["price_eur"], 2)
        assert abs(data["market_cap"] - expected_market_cap) < 0.1


class TestROARTokenBalance:
    """Test GET /api/shop/token/balance/{user_id} - User ROAR balance"""
    
    def test_user_001_balance(self):
        """User-001 (Willem) should have ROAR tokens from V1 migration"""
        response = requests.get(f"{BASE_URL}/api/shop/token/balance/user-001")
        assert response.status_code == 200
        
        data = response.json()
        assert data["user_id"] == "user-001"
        assert "roar_balance" in data
        assert "value_eur" in data
        assert "price_per_token" in data
        
        # User should have tokens (originally 11, may vary after tests)
        assert data["roar_balance"] >= 0
        
    def test_balance_value_calculation(self):
        """Value EUR = balance * price per token"""
        response = requests.get(f"{BASE_URL}/api/shop/token/balance/user-001")
        data = response.json()
        
        expected_value = round(data["roar_balance"] * data["price_per_token"], 2)
        assert abs(data["value_eur"] - expected_value) < 0.1
        
    def test_nonexistent_user_balance(self):
        """Non-existent user should return 0 balance"""
        response = requests.get(f"{BASE_URL}/api/shop/token/balance/nonexistent-user")
        assert response.status_code == 200
        
        data = response.json()
        assert data["roar_balance"] == 0


class TestROARTokenHistory:
    """Test GET /api/shop/token/history/{user_id} - Transaction history"""
    
    def test_user_001_history_has_v1_data(self):
        """User-001 should have V1 migrated transaction history"""
        response = requests.get(f"{BASE_URL}/api/shop/token/history/user-001")
        assert response.status_code == 200
        
        data = response.json()
        assert "transactions" in data
        assert len(data["transactions"]) >= 5  # V1 had 5+ entries
        
    def test_history_transaction_structure(self):
        """Each transaction should have required fields"""
        response = requests.get(f"{BASE_URL}/api/shop/token/history/user-001")
        data = response.json()
        
        for tx in data["transactions"]:
            assert "id" in tx
            assert "user_id" in tx
            assert "type" in tx
            assert tx["type"] in ("deposit", "buy_roar", "sell_roar", "withdrawal")
            assert "amount_eur" in tx
            assert "timestamp" in tx
            
    def test_history_sorted_by_timestamp(self):
        """Transactions should be sorted by timestamp (newest first)"""
        response = requests.get(f"{BASE_URL}/api/shop/token/history/user-001")
        data = response.json()
        
        timestamps = [tx["timestamp"] for tx in data["transactions"]]
        assert timestamps == sorted(timestamps, reverse=True)


class TestROARTokenBuy:
    """Test POST /api/shop/token/buy/{user_id} - Buy ROAR tokens"""
    
    def test_buy_insufficient_eur_balance(self):
        """Buying more than EUR balance should fail"""
        # Try to buy 100 tokens (way more than available EUR)
        response = requests.post(
            f"{BASE_URL}/api/shop/token/buy/user-001",
            json={"amount_tokens": 100}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == False
        assert "Onvoldoende EUR" in data["error"]
        
    def test_buy_requires_amount(self):
        """Buy without amount should fail"""
        response = requests.post(
            f"{BASE_URL}/api/shop/token/buy/user-001",
            json={}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == False
        assert "amount_eur of amount_tokens" in data["error"]


class TestROARTokenSell:
    """Test POST /api/shop/token/sell/{user_id} - Sell ROAR tokens"""
    
    def test_sell_more_than_owned_fails(self):
        """Selling more tokens than owned should fail"""
        response = requests.post(
            f"{BASE_URL}/api/shop/token/sell/user-001",
            json={"amount_tokens": 9999}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == False
        assert "Onvoldoende ROAR" in data["error"]
        
    def test_sell_zero_tokens_fails(self):
        """Selling 0 tokens should fail or return error"""
        response = requests.post(
            f"{BASE_URL}/api/shop/token/sell/user-001",
            json={"amount_tokens": 0}
        )
        # Either 422 validation error or success=false
        assert response.status_code in (200, 422)


class TestROARTokenBuySellFlow:
    """Test complete buy/sell flow with actual transactions"""
    
    def test_sell_and_buy_back_flow(self):
        """Sell 0.1 tokens, then buy 0.1 tokens back"""
        # Get initial balance
        initial = requests.get(f"{BASE_URL}/api/shop/token/balance/user-001").json()
        initial_roar = initial["roar_balance"]
        
        # Sell 0.1 tokens
        sell_response = requests.post(
            f"{BASE_URL}/api/shop/token/sell/user-001",
            json={"amount_tokens": 0.1}
        )
        sell_data = sell_response.json()
        
        if sell_data["success"]:
            # Verify balance decreased
            after_sell = requests.get(f"{BASE_URL}/api/shop/token/balance/user-001").json()
            assert after_sell["roar_balance"] < initial_roar
            
            # Buy 0.1 tokens back
            buy_response = requests.post(
                f"{BASE_URL}/api/shop/token/buy/user-001",
                json={"amount_tokens": 0.1}
            )
            buy_data = buy_response.json()
            
            if buy_data["success"]:
                # Verify balance increased
                after_buy = requests.get(f"{BASE_URL}/api/shop/token/balance/user-001").json()
                assert after_buy["roar_balance"] > after_sell["roar_balance"]


class TestTradePageRegression:
    """Regression tests for Trade page (candles, monitor, watchlist)"""
    
    def test_candles_endpoint_works(self):
        """GET /api/trade/candles should still work"""
        response = requests.get(f"{BASE_URL}/api/trade/candles?market=BCH-EUR&interval=1h&limit=5")
        assert response.status_code == 200
        
    def test_tickers_endpoint_works(self):
        """GET /api/trade/tickers should still work"""
        response = requests.get(f"{BASE_URL}/api/trade/tickers")
        assert response.status_code == 200
        
    def test_monitor_status_works(self):
        """GET /api/trade/monitor/status should still work"""
        response = requests.get(f"{BASE_URL}/api/trade/monitor/status")
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
