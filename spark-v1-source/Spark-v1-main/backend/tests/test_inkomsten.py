"""
Inkomsten (Income) API Tests
Tests for: GET /categories, POST /add, GET /list, GET /summary, DELETE /{id}
"""
import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://spark-foundation.preview.emergentagent.com')
API = f"{BASE_URL}/api"

# Test user ID for income tests
TEST_USER_ID = f"test_income_{uuid.uuid4().hex[:8]}"


class TestIncomeCategories:
    """Test GET /api/income/categories endpoint"""
    
    def test_get_categories_success(self):
        """Should return list of income categories"""
        response = requests.get(f"{API}/income/categories")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert "categories" in data
        assert isinstance(data["categories"], list)
        assert len(data["categories"]) == 6
        
        # Verify expected categories
        expected = ["Salaris", "Freelance", "Gift", "Verkoop", "Dividend", "Overig"]
        assert data["categories"] == expected
        print(f"✅ Categories returned: {data['categories']}")


class TestIncomeAdd:
    """Test POST /api/income/add endpoint"""
    
    def test_add_income_success(self):
        """Should add income entry with all fields"""
        payload = {
            "amount": 2500.00,
            "category": "Salaris",
            "description": "Maandelijks salaris",
            "date": "2026-01-15"
        }
        
        response = requests.post(
            f"{API}/income/add",
            json=payload,
            params={"user_id": TEST_USER_ID}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert "income" in data
        assert data["income"]["amount"] == 2500.00
        assert data["income"]["category"] == "Salaris"
        assert data["income"]["description"] == "Maandelijks salaris"
        assert "id" in data["income"]
        assert data["message"] == "Inkomst toegevoegd"
        print(f"✅ Income added with ID: {data['income']['id']}")
    
    def test_add_income_minimal_fields(self):
        """Should add income with only required fields"""
        payload = {
            "amount": 100.00,
            "category": "Gift",
            "description": ""
        }
        
        response = requests.post(
            f"{API}/income/add",
            json=payload,
            params={"user_id": TEST_USER_ID}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert data["income"]["amount"] == 100.00
        assert data["income"]["category"] == "Gift"
        print(f"✅ Minimal income added with ID: {data['income']['id']}")
    
    def test_add_income_decimal_amount(self):
        """Should handle decimal amounts correctly"""
        payload = {
            "amount": 450.75,
            "category": "Freelance",
            "description": "Project werk"
        }
        
        response = requests.post(
            f"{API}/income/add",
            json=payload,
            params={"user_id": TEST_USER_ID}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert data["income"]["amount"] == 450.75
        print(f"✅ Decimal amount income added: €{data['income']['amount']}")


class TestIncomeList:
    """Test GET /api/income/list endpoint"""
    
    def test_list_income_returns_entries(self):
        """Should return list of income entries"""
        # First add an income entry
        payload = {
            "amount": 500.00,
            "category": "Verkoop",
            "description": "Test verkoop"
        }
        requests.post(
            f"{API}/income/add",
            json=payload,
            params={"user_id": TEST_USER_ID}
        )
        
        # Now list
        response = requests.get(
            f"{API}/income/list",
            params={"user_id": TEST_USER_ID}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert "income" in data
        assert isinstance(data["income"], list)
        assert len(data["income"]) > 0
        assert "total_count" in data
        print(f"✅ Listed {len(data['income'])} income entries (total: {data['total_count']})")
    
    def test_list_income_with_limit(self):
        """Should respect limit parameter"""
        response = requests.get(
            f"{API}/income/list",
            params={"user_id": TEST_USER_ID, "limit": 2}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert len(data["income"]) <= 2
        print(f"✅ Limited list returned {len(data['income'])} entries")
    
    def test_list_income_empty_user(self):
        """Should return empty list for new user"""
        new_user = f"empty_user_{uuid.uuid4().hex[:8]}"
        
        response = requests.get(
            f"{API}/income/list",
            params={"user_id": new_user}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert data["income"] == []
        assert data["total_count"] == 0
        print("✅ Empty user returns empty list")


class TestIncomeSummary:
    """Test GET /api/income/summary endpoint"""
    
    def test_summary_returns_totals(self):
        """Should return summary with totals"""
        response = requests.get(
            f"{API}/income/summary",
            params={"user_id": TEST_USER_ID}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert "total" in data
        assert "count" in data
        assert "by_category" in data
        assert "month" in data
        assert isinstance(data["total"], (int, float))
        print(f"✅ Summary: €{data['total']} from {data['count']} entries in {data['month']}")
    
    def test_summary_with_specific_month(self):
        """Should filter by specific month"""
        # Add income for January 2026
        payload = {
            "amount": 1000.00,
            "category": "Dividend",
            "description": "Q4 dividend",
            "date": "2026-01-20"
        }
        requests.post(
            f"{API}/income/add",
            json=payload,
            params={"user_id": TEST_USER_ID}
        )
        
        response = requests.get(
            f"{API}/income/summary",
            params={"user_id": TEST_USER_ID, "month": "2026-01"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert data["month"] == "2026-01"
        assert data["total"] >= 1000.00  # At least our dividend
        print(f"✅ January 2026 summary: €{data['total']} from {data['count']} entries")
    
    def test_summary_empty_month(self):
        """Should return zero for month with no income"""
        response = requests.get(
            f"{API}/income/summary",
            params={"user_id": TEST_USER_ID, "month": "2020-01"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert data["total"] == 0
        assert data["count"] == 0
        print("✅ Empty month returns zero totals")


class TestIncomeDelete:
    """Test DELETE /api/income/{income_id} endpoint"""
    
    def test_delete_income_success(self):
        """Should delete income entry"""
        # First add an income to delete
        payload = {
            "amount": 50.00,
            "category": "Overig",
            "description": "To be deleted"
        }
        add_response = requests.post(
            f"{API}/income/add",
            json=payload,
            params={"user_id": TEST_USER_ID}
        )
        income_id = add_response.json()["income"]["id"]
        
        # Delete it
        response = requests.delete(
            f"{API}/income/{income_id}",
            params={"user_id": TEST_USER_ID}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert data["message"] == "Inkomst verwijderd"
        print(f"✅ Income {income_id} deleted successfully")
    
    def test_delete_nonexistent_income(self):
        """Should return 404 for non-existent income"""
        response = requests.delete(
            f"{API}/income/nonexistent123",
            params={"user_id": TEST_USER_ID}
        )
        
        assert response.status_code == 404
        print("✅ Non-existent income returns 404")


class TestIncomeIntegration:
    """Integration tests: Create → Read → Update → Delete flow"""
    
    def test_full_crud_flow(self):
        """Test complete CRUD flow for income"""
        user_id = f"crud_test_{uuid.uuid4().hex[:8]}"
        
        # 1. CREATE - Add income
        payload = {
            "amount": 3000.00,
            "category": "Salaris",
            "description": "Integration test salaris",
            "date": "2026-01-25"
        }
        create_response = requests.post(
            f"{API}/income/add",
            json=payload,
            params={"user_id": user_id}
        )
        assert create_response.status_code == 200
        income_id = create_response.json()["income"]["id"]
        print(f"✅ CREATE: Income {income_id} created")
        
        # 2. READ - Verify in list
        list_response = requests.get(
            f"{API}/income/list",
            params={"user_id": user_id}
        )
        assert list_response.status_code == 200
        income_list = list_response.json()["income"]
        assert any(i["id"] == income_id for i in income_list)
        print(f"✅ READ: Income {income_id} found in list")
        
        # 3. READ - Verify in summary
        summary_response = requests.get(
            f"{API}/income/summary",
            params={"user_id": user_id, "month": "2026-01"}
        )
        assert summary_response.status_code == 200
        assert summary_response.json()["total"] == 3000.00
        print(f"✅ READ: Summary shows €3000.00 total")
        
        # 4. DELETE - Remove income
        delete_response = requests.delete(
            f"{API}/income/{income_id}",
            params={"user_id": user_id}
        )
        assert delete_response.status_code == 200
        print(f"✅ DELETE: Income {income_id} deleted")
        
        # 5. VERIFY DELETE - Check list is empty
        verify_response = requests.get(
            f"{API}/income/list",
            params={"user_id": user_id}
        )
        assert verify_response.status_code == 200
        assert verify_response.json()["total_count"] == 0
        print("✅ VERIFY: List is empty after delete")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
