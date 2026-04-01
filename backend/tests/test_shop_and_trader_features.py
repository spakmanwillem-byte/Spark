"""
Test Shop (Winkel) Token System and Trader Page New Features
- Shop items API
- Token balance API
- Token purchase (buy) API
- Purchase history API
- 15-minute candle interval
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestShopItems:
    """Shop items endpoint tests"""
    
    def test_get_shop_items_returns_6_items(self):
        """GET /api/shop/items returns 6 shop items with token prices"""
        response = requests.get(f"{BASE_URL}/api/shop/items")
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        items = data["items"]
        assert len(items) == 6, f"Expected 6 items, got {len(items)}"
        
        # Verify item structure
        for item in items:
            assert "id" in item
            assert "naam" in item
            assert "prijs" in item
            assert "beschikbaar" in item
            assert isinstance(item["prijs"], int)
        
        # Verify specific items exist
        item_ids = [i["id"] for i in items]
        expected_ids = ["custom-emoji", "kleur-thema", "priority-support", "extra-storage", "ai-boost", "gift-card"]
        for expected_id in expected_ids:
            assert expected_id in item_ids, f"Missing item: {expected_id}"
        
        print(f"✓ Shop items: {len(items)} items returned")
        for item in items:
            print(f"  - {item['id']}: {item['naam']} ({item['prijs']} tokens, beschikbaar={item['beschikbaar']})")


class TestTokenBalance:
    """Token balance endpoint tests"""
    
    def test_get_token_balance_user_001(self):
        """GET /api/shop/balance/user-001 returns current token balance"""
        response = requests.get(f"{BASE_URL}/api/shop/balance/user-001")
        assert response.status_code == 200
        
        data = response.json()
        assert "user_id" in data
        assert data["user_id"] == "user-001"
        assert "spark_tokens" in data
        assert isinstance(data["spark_tokens"], int)
        
        # User started with 11 tokens, bought gift-card for 2, should have 9
        # But may have changed if more purchases were made
        print(f"✓ Token balance for user-001: {data['spark_tokens']} tokens")
        return data["spark_tokens"]


class TestTokenPurchase:
    """Token purchase (buy) endpoint tests"""
    
    def test_buy_priority_support_deducts_3_tokens(self):
        """POST /api/shop/buy/user-001 with priority-support deducts 3 tokens"""
        # First get current balance
        balance_response = requests.get(f"{BASE_URL}/api/shop/balance/user-001")
        initial_balance = balance_response.json()["spark_tokens"]
        print(f"  Initial balance: {initial_balance} tokens")
        
        # Skip if not enough tokens
        if initial_balance < 3:
            pytest.skip(f"Not enough tokens ({initial_balance}) to buy priority-support (3)")
        
        # Buy priority-support (3 tokens)
        response = requests.post(
            f"{BASE_URL}/api/shop/buy/user-001",
            json={"item_id": "priority-support"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True, f"Purchase failed: {data.get('error')}"
        assert "new_balance" in data
        assert data["new_balance"] == initial_balance - 3, f"Expected {initial_balance - 3}, got {data['new_balance']}"
        assert "message" in data
        assert "Priority Support" in data["message"]
        
        print(f"✓ Bought priority-support: {data['message']}")
        print(f"  New balance: {data['new_balance']} tokens")
    
    def test_buy_unavailable_item_returns_error(self):
        """POST /api/shop/buy/user-001 with ai-boost returns error (item not available)"""
        response = requests.post(
            f"{BASE_URL}/api/shop/buy/user-001",
            json={"item_id": "ai-boost"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == False
        assert "error" in data
        assert "niet beschikbaar" in data["error"].lower()
        
        print(f"✓ Unavailable item error: {data['error']}")
    
    def test_buy_with_insufficient_tokens_returns_error(self):
        """POST /api/shop/buy/user-001 with expensive item returns 'Onvoldoende tokens' error"""
        # First get current balance
        balance_response = requests.get(f"{BASE_URL}/api/shop/balance/user-001")
        current_balance = balance_response.json()["spark_tokens"]
        
        # Try to buy ai-boost (15 tokens) - but it's unavailable
        # So let's try to buy multiple items to exhaust tokens first
        # Or just check if balance is less than 15 and try to buy kleur-thema (8 tokens)
        
        if current_balance < 8:
            # Try to buy kleur-thema (8 tokens) with insufficient balance
            response = requests.post(
                f"{BASE_URL}/api/shop/buy/user-001",
                json={"item_id": "kleur-thema"}
            )
            assert response.status_code == 200
            
            data = response.json()
            assert data["success"] == False
            assert "error" in data
            assert "onvoldoende" in data["error"].lower() or "tokens" in data["error"].lower()
            
            print(f"✓ Insufficient tokens error: {data['error']}")
        else:
            # We have enough tokens, so let's verify the error message format
            # by checking the shop items endpoint for an expensive item
            print(f"  Current balance ({current_balance}) is sufficient for most items")
            print(f"  Skipping insufficient tokens test - would need to exhaust balance first")
            pytest.skip("Balance is sufficient for available items")


class TestPurchaseHistory:
    """Purchase history endpoint tests"""
    
    def test_get_purchase_history_user_001(self):
        """GET /api/shop/purchases/user-001 returns purchase history"""
        response = requests.get(f"{BASE_URL}/api/shop/purchases/user-001")
        assert response.status_code == 200
        
        data = response.json()
        assert "purchases" in data
        purchases = data["purchases"]
        assert isinstance(purchases, list)
        
        # Should have at least 1 purchase (gift-card from previous test)
        if len(purchases) > 0:
            purchase = purchases[0]
            assert "id" in purchase
            assert "user_id" in purchase
            assert "item_id" in purchase
            assert "prijs" in purchase
            assert "timestamp" in purchase
            
            print(f"✓ Purchase history: {len(purchases)} purchases")
            for p in purchases[-5:]:  # Show last 5
                print(f"  - {p['item_id']}: {p.get('item_naam', 'N/A')} ({p['prijs']} tokens)")
        else:
            print(f"✓ Purchase history: empty (no purchases yet)")


class TestCandleIntervals:
    """Candle interval tests including new 15m interval"""
    
    def test_15m_candle_interval(self):
        """GET /api/trade/candles?market=BCH-EUR&interval=15m&limit=10 returns 15-minute candle data"""
        response = requests.get(
            f"{BASE_URL}/api/trade/candles",
            params={"market": "BCH-EUR", "interval": "15m", "limit": 10}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "candles" in data
        assert data["interval"] == "15m"
        assert data["market"] == "BCH-EUR"
        
        candles = data["candles"]
        assert len(candles) > 0, "No candles returned for 15m interval"
        
        # Verify candle structure
        candle = candles[0]
        assert "timestamp" in candle
        assert "open" in candle
        assert "high" in candle
        assert "low" in candle
        assert "close" in candle
        
        print(f"✓ 15m candles: {len(candles)} candles returned")
        print(f"  Latest: O={candle['open']}, H={candle['high']}, L={candle['low']}, C={candle['close']}")
    
    def test_1h_candle_interval(self):
        """GET /api/trade/candles?market=BCH-EUR&interval=1h&limit=10 returns 1-hour candle data"""
        response = requests.get(
            f"{BASE_URL}/api/trade/candles",
            params={"market": "BCH-EUR", "interval": "1h", "limit": 10}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["interval"] == "1h"
        assert len(data["candles"]) > 0
        
        print(f"✓ 1h candles: {len(data['candles'])} candles returned")
    
    def test_4h_candle_interval(self):
        """GET /api/trade/candles?market=BCH-EUR&interval=4h&limit=10 returns 4-hour candle data"""
        response = requests.get(
            f"{BASE_URL}/api/trade/candles",
            params={"market": "BCH-EUR", "interval": "4h", "limit": 10}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["interval"] == "4h"
        assert len(data["candles"]) > 0
        
        print(f"✓ 4h candles: {len(data['candles'])} candles returned")
    
    def test_1d_candle_interval(self):
        """GET /api/trade/candles?market=BCH-EUR&interval=1d&limit=10 returns daily candle data"""
        response = requests.get(
            f"{BASE_URL}/api/trade/candles",
            params={"market": "BCH-EUR", "interval": "1d", "limit": 10}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["interval"] == "1d"
        assert len(data["candles"]) > 0
        
        print(f"✓ 1d candles: {len(data['candles'])} candles returned")


class TestRegressionChecks:
    """Regression tests for existing features"""
    
    def test_trade_stats_still_works(self):
        """GET /api/trade/stats/user-001 still returns trade statistics"""
        response = requests.get(f"{BASE_URL}/api/trade/stats/user-001")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_trades" in data
        assert "buys" in data
        assert "sells" in data
        
        print(f"✓ Trade stats: {data['total_trades']} trades ({data['buys']} buys, {data['sells']} sells)")
    
    def test_tickers_still_works(self):
        """GET /api/trade/tickers still returns live prices"""
        response = requests.get(f"{BASE_URL}/api/trade/tickers")
        assert response.status_code == 200
        
        data = response.json()
        assert "tickers" in data
        tickers = data["tickers"]
        assert len(tickers) > 0
        
        print(f"✓ Tickers: {len(tickers)} coins")
        for t in tickers[:3]:
            print(f"  - {t['symbol']}: €{t['last']}")
    
    def test_monitor_status_still_works(self):
        """GET /api/trade/monitor/status still returns monitor status"""
        response = requests.get(f"{BASE_URL}/api/trade/monitor/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        
        print(f"✓ Monitor status: running={data['status'].get('running', False) if data['status'] else False}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
