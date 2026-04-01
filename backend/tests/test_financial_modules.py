"""
Financial Modules API Tests - Trade, Wallet, Accounting
Tests for Spark Core 2.0 Dutch dashboard financial modules
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestTradeModule:
    """Trade module API tests - BCH-EUR trade history, stats, Bitvavo integration"""
    
    def test_trade_stats_returns_correct_totals(self):
        """GET /api/trade/stats/user-001 returns total_trades (287), buys, sells, markets, profit_loss"""
        response = requests.get(f"{BASE_URL}/api/trade/stats/user-001")
        assert response.status_code == 200
        data = response.json()
        
        # Verify expected fields
        assert "total_trades" in data
        assert data["total_trades"] == 287
        assert "buys" in data
        assert "sells" in data
        assert "markets" in data
        assert "BCH-EUR" in data["markets"]
        assert "profit_loss" in data
        assert "total_buy_eur" in data
        assert "total_sell_eur" in data
        assert "avg_buy_price" in data
        assert "avg_sell_price" in data
        assert "mock_trades" in data
        assert "real_trades" in data
        print(f"Trade stats: {data['total_trades']} trades, {data['buys']} buys, {data['sells']} sells, P/L: {data['profit_loss']}")
    
    def test_trade_history_returns_trades_array(self):
        """GET /api/trade/history/user-001 returns trades array with BCH-EUR trades"""
        response = requests.get(f"{BASE_URL}/api/trade/history/user-001?limit=100")
        assert response.status_code == 200
        data = response.json()
        
        assert "trades" in data
        assert "total" in data
        assert data["total"] == 287
        assert len(data["trades"]) <= 100  # Respects limit
        
        # Verify trade structure
        if data["trades"]:
            trade = data["trades"][0]
            assert "trade_id" in trade
            assert "action" in trade
            assert trade["action"] in ["BUY", "SELL"]
            assert "market" in trade
            assert trade["market"] == "BCH-EUR"
            assert "amount" in trade
            assert "price" in trade
            assert "status" in trade
            assert "mock" in trade
        print(f"Trade history: {data['total']} total trades, returned {len(data['trades'])}")
    
    def test_trade_history_respects_limit(self):
        """GET /api/trade/history with limit parameter"""
        response = requests.get(f"{BASE_URL}/api/trade/history/user-001?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["trades"]) == 10
    
    def test_trade_markets_returns_bch_eur(self):
        """GET /api/trade/markets/user-001 returns BCH-EUR market data"""
        response = requests.get(f"{BASE_URL}/api/trade/markets/user-001")
        assert response.status_code == 200
        data = response.json()
        
        assert "markets" in data
        assert "BCH-EUR" in data["markets"]
        
        bch_eur = data["markets"]["BCH-EUR"]
        assert "total" in bch_eur
        assert "buys" in bch_eur
        assert "sells" in bch_eur
        assert bch_eur["total"] == 287
        print(f"BCH-EUR market: {bch_eur['total']} trades, {bch_eur['buys']} buys, {bch_eur['sells']} sells")
    
    def test_bitvavo_status_returns_connected_status(self):
        """GET /api/trade/bitvavo/status/user-001 returns connected status"""
        response = requests.get(f"{BASE_URL}/api/trade/bitvavo/status/user-001")
        assert response.status_code == 200
        data = response.json()
        
        assert "connected" in data
        assert isinstance(data["connected"], bool)
        print(f"Bitvavo status: connected={data['connected']}")
    
    def test_trader_settings_returns_defaults(self):
        """GET /api/trade/settings/user-001 returns trader settings"""
        response = requests.get(f"{BASE_URL}/api/trade/settings/user-001")
        assert response.status_code == 200
        data = response.json()
        
        assert "settings" in data
        settings = data["settings"]
        assert "trade_amount" in settings
        assert "market" in settings
        assert "use_mock" in settings
        assert "auto_trade" in settings
        print(f"Trader settings: amount={settings['trade_amount']}, market={settings['market']}, mock={settings['use_mock']}")
    
    def test_save_bitvavo_credentials(self):
        """POST /api/trade/bitvavo/credentials/user-001 saves API credentials"""
        payload = {
            "api_key": "TEST_API_KEY_12345",
            "api_secret": "TEST_API_SECRET_67890"
        }
        response = requests.post(
            f"{BASE_URL}/api/trade/bitvavo/credentials/user-001",
            json=payload
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert "message" in data
        
        # Verify credentials were saved by checking status
        status_response = requests.get(f"{BASE_URL}/api/trade/bitvavo/status/user-001")
        status_data = status_response.json()
        assert status_data["connected"] == True
        print("Bitvavo credentials saved successfully")


class TestWalletModule:
    """Wallet module API tests - User wallets, entities, transactions"""
    
    def test_user_wallet_returns_correct_balances(self):
        """GET /api/wallet/user/user-001 returns spark_tokens (1000), credits (250), balance_eur (15.4)"""
        response = requests.get(f"{BASE_URL}/api/wallet/user/user-001")
        assert response.status_code == 200
        data = response.json()
        
        assert data["user_id"] == "user-001"
        assert data["name"] == "De Willem"
        assert data["spark_tokens"] == 1000
        assert data["credits"] == 250
        assert data["balance_eur"] == 15.4
        assert "earned_total" in data
        assert "activity_score" in data
        print(f"Wallet: {data['spark_tokens']} tokens, {data['credits']} credits, €{data['balance_eur']}")
    
    def test_wallet_transactions_returns_history(self):
        """GET /api/wallet/transactions/user-001 returns transaction history"""
        response = requests.get(f"{BASE_URL}/api/wallet/transactions/user-001")
        assert response.status_code == 200
        data = response.json()
        
        assert "transactions" in data
        assert "total" in data
        
        if data["transactions"]:
            tx = data["transactions"][0]
            assert "id" in tx
            assert "user_id" in tx
            assert "type" in tx
            assert "amount" in tx
            assert "status" in tx
        print(f"Wallet transactions: {data['total']} total")
    
    def test_entities_returns_four_entities(self):
        """GET /api/wallet/entities returns 4 entities (spark_core, spark_your_life, roadkill_merch, personal_willem)"""
        response = requests.get(f"{BASE_URL}/api/wallet/entities")
        assert response.status_code == 200
        data = response.json()
        
        assert "entities" in data
        entities = data["entities"]
        
        # Verify all 4 entities exist
        expected_entities = ["spark_core", "spark_your_life", "roadkill_merch", "personal_willem"]
        for entity_id in expected_entities:
            assert entity_id in entities, f"Missing entity: {entity_id}"
            entity = entities[entity_id]
            assert "name" in entity
            assert "type" in entity
            assert "description" in entity
            assert "color" in entity
        
        print(f"Entities: {list(entities.keys())}")
    
    def test_single_entity_returns_details(self):
        """GET /api/wallet/entities/spark_core returns entity details"""
        response = requests.get(f"{BASE_URL}/api/wallet/entities/spark_core")
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert "entity" in data
        entity = data["entity"]
        assert entity["name"] == "Spark Core"
        assert entity["type"] == "system"
    
    def test_wallet_overview_returns_combined_data(self):
        """GET /api/wallet/overview returns entities and user wallet"""
        response = requests.get(f"{BASE_URL}/api/wallet/overview?user_id=user-001")
        assert response.status_code == 200
        data = response.json()
        
        assert "entities" in data
        assert "user_wallet" in data
        assert "spark_tokens" in data["user_wallet"]
        assert "credits" in data["user_wallet"]


class TestAccountingModule:
    """Accounting module API tests - Kasboeken, transactions, summary"""
    
    def test_kasboeken_returns_four_kasboeken(self):
        """GET /api/accounting/kasboeken returns 4 kasboeken with income/expenses/saldo"""
        response = requests.get(f"{BASE_URL}/api/accounting/kasboeken")
        assert response.status_code == 200
        data = response.json()
        
        assert "kasboeken" in data
        kasboeken = data["kasboeken"]
        assert len(kasboeken) == 4
        
        # Verify kasboek structure
        for kb in kasboeken:
            assert "id" in kb
            assert "name" in kb
            assert "income" in kb
            assert "expenses" in kb
            assert "saldo" in kb
            assert "tx_count" in kb
        
        # Verify all 4 entities are represented
        kb_ids = [kb["id"] for kb in kasboeken]
        assert "spark_core" in kb_ids
        assert "spark_your_life" in kb_ids
        assert "roadkill_merch" in kb_ids
        assert "personal_willem" in kb_ids
        print(f"Kasboeken: {[kb['name'] for kb in kasboeken]}")
    
    def test_accounting_summary_returns_totals(self):
        """GET /api/accounting/summary returns total income/expenses/profit"""
        response = requests.get(f"{BASE_URL}/api/accounting/summary")
        assert response.status_code == 200
        data = response.json()
        
        assert "income" in data
        assert "expenses" in data
        assert "profit" in data
        assert "btw_total" in data
        assert "transaction_count" in data
        assert "per_entity" in data
        
        # Verify per_entity breakdown
        assert len(data["per_entity"]) == 4
        print(f"Summary: income={data['income']}, expenses={data['expenses']}, profit={data['profit']}")
    
    def test_transactions_returns_list(self):
        """GET /api/accounting/transactions returns 7 transactions"""
        response = requests.get(f"{BASE_URL}/api/accounting/transactions")
        assert response.status_code == 200
        data = response.json()
        
        assert "transactions" in data
        assert "total" in data
        assert data["total"] >= 7  # At least 7 from seed data
        
        # Verify transaction structure
        if data["transactions"]:
            tx = data["transactions"][0]
            assert "id" in tx
            assert "type" in tx
            assert tx["type"] in ["income", "expense"]
            assert "category" in tx
            assert "amount" in tx
            assert "description" in tx
        print(f"Transactions: {data['total']} total")
    
    def test_transactions_filter_by_entity(self):
        """GET /api/accounting/transactions?entity_id=spark_core filters by entity"""
        response = requests.get(f"{BASE_URL}/api/accounting/transactions?entity_id=spark_core")
        assert response.status_code == 200
        data = response.json()
        
        # All returned transactions should be for spark_core
        for tx in data["transactions"]:
            assert tx.get("entity_id", "spark_core") == "spark_core"
    
    def test_transactions_filter_by_type(self):
        """GET /api/accounting/transactions?type=income filters by type"""
        response = requests.get(f"{BASE_URL}/api/accounting/transactions?type=income")
        assert response.status_code == 200
        data = response.json()
        
        for tx in data["transactions"]:
            assert tx["type"] == "income"
    
    def test_create_transaction(self):
        """POST /api/accounting/transactions creates new transaction"""
        payload = {
            "type": "income",
            "category": "Donations",
            "amount": 75.0,
            "description": "TEST_pytest_donation",
            "entity_id": "spark_core",
            "btw_percentage": 21.0
        }
        response = requests.post(
            f"{BASE_URL}/api/accounting/transactions",
            json=payload
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert "transaction" in data
        tx = data["transaction"]
        assert tx["type"] == "income"
        assert tx["category"] == "Donations"
        assert tx["amount"] == 75.0
        assert tx["description"] == "TEST_pytest_donation"
        assert tx["btw_amount"] == 15.75  # 21% of 75
        
        # Store ID for cleanup
        self.created_tx_id = tx["id"]
        print(f"Created transaction: {tx['id']}")
        
        # Verify it appears in list
        list_response = requests.get(f"{BASE_URL}/api/accounting/transactions")
        list_data = list_response.json()
        tx_ids = [t["id"] for t in list_data["transactions"]]
        assert tx["id"] in tx_ids
    
    def test_delete_transaction(self):
        """DELETE /api/accounting/transactions/{id} deletes transaction"""
        # First create a transaction to delete
        payload = {
            "type": "expense",
            "category": "Hosting",
            "amount": 25.0,
            "description": "TEST_to_delete",
            "entity_id": "spark_core"
        }
        create_response = requests.post(
            f"{BASE_URL}/api/accounting/transactions",
            json=payload
        )
        tx_id = create_response.json()["transaction"]["id"]
        
        # Delete it
        delete_response = requests.delete(f"{BASE_URL}/api/accounting/transactions/{tx_id}")
        assert delete_response.status_code == 200
        data = delete_response.json()
        assert data["success"] == True
        
        # Verify it's gone
        list_response = requests.get(f"{BASE_URL}/api/accounting/transactions")
        list_data = list_response.json()
        tx_ids = [t["id"] for t in list_data["transactions"]]
        assert tx_id not in tx_ids
        print(f"Deleted transaction: {tx_id}")
    
    def test_categories_returns_income_and_expense(self):
        """GET /api/accounting/categories returns income and expense categories"""
        response = requests.get(f"{BASE_URL}/api/accounting/categories")
        assert response.status_code == 200
        data = response.json()
        
        assert "income" in data
        assert "expense" in data
        assert len(data["income"]) > 0
        assert len(data["expense"]) > 0
        assert "Donations" in data["income"]
        assert "Hosting" in data["expense"]
        print(f"Categories: {len(data['income'])} income, {len(data['expense'])} expense")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
