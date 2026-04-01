"""
Test Trader Page Features - Iteration 9
Tests: Candles, Tickers, Monitor (start/stop/pause), Quick Trade, Decisions
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestCandlesAPI:
    """Test candle data from Bitvavo public API"""
    
    def test_candles_bch_eur_1h(self):
        """GET /api/trade/candles?market=BCH-EUR&interval=1h&limit=10"""
        response = requests.get(f"{BASE_URL}/api/trade/candles?market=BCH-EUR&interval=1h&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["market"] == "BCH-EUR"
        assert data["interval"] == "1h"
        assert len(data["candles"]) > 0
        # Verify candle structure
        candle = data["candles"][0]
        assert "timestamp" in candle
        assert "open" in candle
        assert "high" in candle
        assert "low" in candle
        assert "close" in candle
        assert "volume" in candle
        assert isinstance(candle["open"], (int, float))
        assert isinstance(candle["close"], (int, float))
        print(f"✓ BCH-EUR 1h candles: {len(data['candles'])} candles, latest close: €{candle['close']}")
    
    def test_candles_btc_eur_4h(self):
        """GET /api/trade/candles?market=BTC-EUR&interval=4h&limit=5"""
        response = requests.get(f"{BASE_URL}/api/trade/candles?market=BTC-EUR&interval=4h&limit=5")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["market"] == "BTC-EUR"
        assert data["interval"] == "4h"
        assert len(data["candles"]) >= 1
        candle = data["candles"][0]
        assert candle["close"] > 10000  # BTC should be > €10k
        print(f"✓ BTC-EUR 4h candles: {len(data['candles'])} candles, latest close: €{candle['close']}")
    
    def test_candles_eth_eur_1d(self):
        """GET /api/trade/candles?market=ETH-EUR&interval=1d&limit=5"""
        response = requests.get(f"{BASE_URL}/api/trade/candles?market=ETH-EUR&interval=1d&limit=5")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["market"] == "ETH-EUR"
        assert data["interval"] == "1d"
        assert len(data["candles"]) >= 1
        print(f"✓ ETH-EUR 1d candles: {len(data['candles'])} candles")


class TestTickersAPI:
    """Test live ticker prices from Bitvavo"""
    
    def test_tickers_watchlist(self):
        """GET /api/trade/tickers returns BCH, BTC, ETH, SOL, ADA"""
        response = requests.get(f"{BASE_URL}/api/trade/tickers")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert len(data["tickers"]) == 5
        
        symbols = [t["symbol"] for t in data["tickers"]]
        assert "BCH" in symbols
        assert "BTC" in symbols
        assert "ETH" in symbols
        assert "SOL" in symbols
        assert "ADA" in symbols
        
        # Verify ticker structure
        for ticker in data["tickers"]:
            assert "market" in ticker
            assert "symbol" in ticker
            assert "name" in ticker
            assert "last" in ticker
            assert "open" in ticker
            assert "high" in ticker
            assert "low" in ticker
            assert "bid" in ticker
            assert "ask" in ticker
            assert isinstance(ticker["last"], (int, float))
            assert ticker["last"] > 0
        
        ticker_str = ', '.join([f"{t['symbol']}=€{t['last']}" for t in data['tickers']])
        print(f"✓ Tickers: {ticker_str}")


class TestMonitorAPI:
    """Test monitor start/stop/pause functionality"""
    
    def test_monitor_status_initial(self):
        """GET /api/trade/monitor/status returns status object"""
        response = requests.get(f"{BASE_URL}/api/trade/monitor/status")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "status" in data
        status = data["status"]
        assert "running" in status
        assert "paused" in status
        assert "cycles" in status
        print(f"✓ Monitor status: running={status['running']}, cycles={status['cycles']}")
    
    def test_monitor_start_stop_cycle(self):
        """POST /api/trade/monitor/start, wait, check status, stop"""
        # Start monitor
        start_response = requests.post(
            f"{BASE_URL}/api/trade/monitor/start",
            json={
                "interval": 10,
                "market": "BCH-EUR",
                "candle_interval": "1h",
                "user_id": "user-001",
                "auto_trade": False,
                "trade_amount": 5,
                "use_mock": True
            }
        )
        assert start_response.status_code == 200
        start_data = start_response.json()
        assert start_data["success"] == True
        assert "Monitor gestart" in start_data["message"]
        print(f"✓ Monitor started: {start_data['message']}")
        
        # Wait for first cycle
        time.sleep(3)
        
        # Check status
        status_response = requests.get(f"{BASE_URL}/api/trade/monitor/status")
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["status"]["running"] == True
        assert status_data["status"]["cycles"] >= 1
        assert status_data["status"]["last_price"] > 0
        print(f"✓ Monitor running: cycles={status_data['status']['cycles']}, price=€{status_data['status']['last_price']}")
        
        # Check decisions
        decisions_response = requests.get(f"{BASE_URL}/api/trade/monitor/decisions?limit=10")
        assert decisions_response.status_code == 200
        decisions_data = decisions_response.json()
        assert decisions_data["success"] == True
        assert len(decisions_data["decisions"]) >= 1
        decision = decisions_data["decisions"][0]
        assert "action" in decision
        assert "price" in decision
        assert "reason" in decision
        assert decision["action"] in ["BUY", "SELL", "HOLD"]
        print(f"✓ Decision: {decision['action']} @ €{decision['price']} - {decision['reason']}")
        
        # Stop monitor
        stop_response = requests.post(f"{BASE_URL}/api/trade/monitor/stop")
        assert stop_response.status_code == 200
        stop_data = stop_response.json()
        assert stop_data["success"] == True
        assert "gestopt" in stop_data["message"]
        print(f"✓ Monitor stopped: {stop_data['message']}")
    
    def test_monitor_pause_toggle(self):
        """POST /api/trade/monitor/start, pause, resume, stop"""
        # Start
        requests.post(f"{BASE_URL}/api/trade/monitor/start", json={"interval": 10})
        time.sleep(1)
        
        # Pause
        pause_response = requests.post(f"{BASE_URL}/api/trade/monitor/pause")
        assert pause_response.status_code == 200
        pause_data = pause_response.json()
        assert pause_data["success"] == True
        assert pause_data["status"]["paused"] == True
        print(f"✓ Monitor paused")
        
        # Resume (toggle pause again)
        resume_response = requests.post(f"{BASE_URL}/api/trade/monitor/pause")
        assert resume_response.status_code == 200
        resume_data = resume_response.json()
        assert resume_data["status"]["paused"] == False
        print(f"✓ Monitor resumed")
        
        # Stop
        requests.post(f"{BASE_URL}/api/trade/monitor/stop")
        print(f"✓ Monitor stopped after pause test")


class TestQuickTradeAPI:
    """Test quick trade execution"""
    
    def test_execute_mock_buy(self):
        """POST /api/trade/execute/user-001 with mock buy"""
        response = requests.post(
            f"{BASE_URL}/api/trade/execute/user-001",
            json={
                "market": "BCH-EUR",
                "side": "buy",
                "amount": 5,
                "use_mock": True
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "trade" in data
        trade = data["trade"]
        assert trade["action"] == "BUY"
        assert trade["market"] == "BCH-EUR"
        assert trade["amount"] == 5.0
        assert trade["mock"] == True
        assert trade["success"] == True
        assert trade["price"] > 0
        print(f"✓ Mock BUY executed: €{trade['amount']} @ €{trade['price']}")
    
    def test_execute_mock_sell(self):
        """POST /api/trade/execute/user-001 with mock sell"""
        response = requests.post(
            f"{BASE_URL}/api/trade/execute/user-001",
            json={
                "market": "ETH-EUR",
                "side": "sell",
                "amount": 10,
                "use_mock": True
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        trade = data["trade"]
        assert trade["action"] == "SELL"
        assert trade["market"] == "ETH-EUR"
        assert trade["amount"] == 10.0
        assert trade["mock"] == True
        print(f"✓ Mock SELL executed: €{trade['amount']} @ €{trade['price']}")


class TestTradeHistoryIntegration:
    """Verify trades appear in history after execution"""
    
    def test_trade_appears_in_history(self):
        """Execute trade and verify it appears in history"""
        # Execute a trade
        trade_response = requests.post(
            f"{BASE_URL}/api/trade/execute/user-001",
            json={
                "market": "SOL-EUR",
                "side": "buy",
                "amount": 3,
                "use_mock": True
            }
        )
        assert trade_response.status_code == 200
        trade_id = trade_response.json()["trade"]["trade_id"]
        
        # Check history
        history_response = requests.get(f"{BASE_URL}/api/trade/history/user-001?limit=10")
        assert history_response.status_code == 200
        trades = history_response.json()["trades"]
        
        # Find our trade
        found = any(t["trade_id"] == trade_id for t in trades)
        assert found, f"Trade {trade_id} not found in history"
        print(f"✓ Trade {trade_id} found in history")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
