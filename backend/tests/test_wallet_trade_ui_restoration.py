"""
Test Wallet and Trade Module UI Restoration
Tests for iteration 8 - UI restoration of Wallet and Trader pages
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestWalletEndpoints:
    """Wallet API endpoint tests"""
    
    def test_get_user_wallet(self):
        """Test GET /api/wallet/user/{user_id} returns wallet data"""
        response = requests.get(f"{BASE_URL}/api/wallet/user/user-001")
        assert response.status_code == 200
        data = response.json()
        
        # Verify required fields
        assert "user_id" in data
        assert "spark_tokens" in data
        assert "credits" in data
        assert "balance_eur" in data
        assert "earned_total" in data
        assert "activity_score" in data
        assert "total_withdrawn" in data
        
        # Verify data types
        assert isinstance(data["spark_tokens"], (int, float))
        assert isinstance(data["credits"], (int, float))
        assert isinstance(data["balance_eur"], (int, float))
        print(f"Wallet data: tokens={data['spark_tokens']}, credits={data['credits']}, balance=€{data['balance_eur']}")
    
    def test_get_transactions(self):
        """Test GET /api/wallet/transactions/{user_id} returns transaction list"""
        response = requests.get(f"{BASE_URL}/api/wallet/transactions/user-001?limit=10")
        assert response.status_code == 200
        data = response.json()
        
        assert "transactions" in data
        assert "total" in data
        assert isinstance(data["transactions"], list)
        
        if len(data["transactions"]) > 0:
            tx = data["transactions"][0]
            assert "id" in tx
            assert "type" in tx
            assert "amount" in tx
            assert tx["type"] in ["deposit", "withdrawal"]
        print(f"Found {data['total']} transactions")
    
    def test_withdrawal_endpoint(self):
        """Test POST /api/wallet/withdraw/{user_id} creates withdrawal"""
        # Get initial balance
        wallet_response = requests.get(f"{BASE_URL}/api/wallet/user/user-001")
        initial_balance = wallet_response.json().get("balance_eur", 0)
        
        # Create withdrawal
        response = requests.post(
            f"{BASE_URL}/api/wallet/withdraw/user-001",
            json={"amount": 0.10, "message": "TEST_withdrawal"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert "transaction" in data
        assert "new_balance" in data
        assert data["transaction"]["type"] == "withdrawal"
        assert data["transaction"]["amount"] == 0.10
        assert data["new_balance"] < initial_balance
        print(f"Withdrawal successful: new_balance=€{data['new_balance']}")
    
    def test_withdrawal_insufficient_funds(self):
        """Test withdrawal with amount exceeding balance fails"""
        response = requests.post(
            f"{BASE_URL}/api/wallet/withdraw/user-001",
            json={"amount": 99999.99, "message": "TEST_large_withdrawal"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == False
        assert "error" in data
        print(f"Insufficient funds error: {data['error']}")
    
    def test_entities_not_in_wallet_response(self):
        """Verify entities are NOT returned in wallet user endpoint (moved to Boekhouding)"""
        response = requests.get(f"{BASE_URL}/api/wallet/user/user-001")
        assert response.status_code == 200
        data = response.json()
        
        # Entities should NOT be in the wallet user response
        assert "entities" not in data
        print("Confirmed: entities not in wallet user response")


class TestTradeEndpoints:
    """Trade API endpoint tests"""
    
    def test_get_trade_stats(self):
        """Test GET /api/trade/stats/{user_id} returns trade statistics"""
        response = requests.get(f"{BASE_URL}/api/trade/stats/user-001")
        assert response.status_code == 200
        data = response.json()
        
        # Verify required fields
        assert "total_trades" in data
        assert "buys" in data
        assert "sells" in data
        assert "markets" in data
        assert "total_buy_eur" in data
        assert "total_sell_eur" in data
        assert "profit_loss" in data
        assert "mock_trades" in data
        assert "real_trades" in data
        
        # Verify data
        assert data["total_trades"] == 287
        assert "BCH-EUR" in data["markets"]
        print(f"Trade stats: {data['total_trades']} trades, P/L=€{data['profit_loss']}")
    
    def test_get_trade_history(self):
        """Test GET /api/trade/history/{user_id} returns trade list"""
        response = requests.get(f"{BASE_URL}/api/trade/history/user-001?limit=10")
        assert response.status_code == 200
        data = response.json()
        
        assert "trades" in data
        assert "total" in data
        assert isinstance(data["trades"], list)
        assert data["total"] == 287
        
        if len(data["trades"]) > 0:
            trade = data["trades"][0]
            assert "trade_id" in trade
            assert "action" in trade
            assert "market" in trade
            assert "amount" in trade
            assert trade["action"] in ["BUY", "SELL"]
        print(f"Found {data['total']} trades")
    
    def test_get_markets(self):
        """Test GET /api/trade/markets/{user_id} returns market breakdown"""
        response = requests.get(f"{BASE_URL}/api/trade/markets/user-001")
        assert response.status_code == 200
        data = response.json()
        
        assert "markets" in data
        assert "BCH-EUR" in data["markets"]
        
        bch_market = data["markets"]["BCH-EUR"]
        assert "total" in bch_market
        assert "buys" in bch_market
        assert "sells" in bch_market
        print(f"BCH-EUR market: {bch_market['total']} trades ({bch_market['buys']} buys, {bch_market['sells']} sells)")
    
    def test_bitvavo_status(self):
        """Test GET /api/trade/bitvavo/status/{user_id} returns connection status"""
        response = requests.get(f"{BASE_URL}/api/trade/bitvavo/status/user-001")
        assert response.status_code == 200
        data = response.json()
        
        assert "connected" in data
        assert isinstance(data["connected"], bool)
        print(f"Bitvavo connected: {data['connected']}")
    
    def test_trader_settings(self):
        """Test GET /api/trade/settings/{user_id} returns trader settings"""
        response = requests.get(f"{BASE_URL}/api/trade/settings/user-001")
        assert response.status_code == 200
        data = response.json()
        
        assert "settings" in data
        settings = data["settings"]
        assert "trade_amount" in settings
        assert "market" in settings
        assert "use_mock" in settings
        print(f"Trader settings: market={settings['market']}, amount=€{settings['trade_amount']}, mock={settings['use_mock']}")


class TestNavigation:
    """Test navigation between modules"""
    
    def test_wallet_endpoint_accessible(self):
        """Verify wallet endpoint is accessible"""
        response = requests.get(f"{BASE_URL}/api/wallet/user/user-001")
        assert response.status_code == 200
    
    def test_trade_endpoint_accessible(self):
        """Verify trade endpoint is accessible"""
        response = requests.get(f"{BASE_URL}/api/trade/stats/user-001")
        assert response.status_code == 200
