"""
Uitgaven (Expenses) Module - Backend API Tests
Tests for: categories, add, list, summary, delete endpoints
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = "https://spark-foundation.preview.emergentagent.com"

API = f"{BASE_URL}/api"

# Test user ID for isolation
TEST_USER_ID = f"test_uitgaven_{uuid.uuid4().hex[:8]}"


class TestUitgavenCategories:
    """Test /api/expenses/categories endpoint"""
    
    def test_get_categories_success(self):
        """Categories endpoint returns list of expense categories"""
        response = requests.get(f"{API}/expenses/categories")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "categories" in data
        assert isinstance(data["categories"], list)
        assert len(data["categories"]) == 9
        
        # Verify expected categories
        expected = ["Boodschappen", "Transport", "Zorg", "Hobby", "Kleding", 
                    "Huis", "Eten & Drinken", "Abonnementen", "Overig"]
        assert data["categories"] == expected


class TestUitgavenCRUD:
    """Test CRUD operations for expenses"""
    
    def test_add_expense_success(self):
        """Add expense with all fields"""
        payload = {
            "amount": 25.50,
            "category": "Boodschappen",
            "description": "Test expense from pytest",
            "date": "2026-03-21"
        }
        
        response = requests.post(
            f"{API}/expenses/add",
            params={"user_id": TEST_USER_ID},
            json=payload
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "expense" in data
        assert data["expense"]["amount"] == 25.50
        assert data["expense"]["category"] == "Boodschappen"
        assert data["expense"]["description"] == "Test expense from pytest"
        assert "id" in data["expense"]
        
        # Store for cleanup
        self.__class__.created_expense_id = data["expense"]["id"]
    
    def test_add_expense_minimal_fields(self):
        """Add expense with only required fields"""
        payload = {
            "amount": 10.00,
            "category": "Transport",
            "description": ""
        }
        
        response = requests.post(
            f"{API}/expenses/add",
            params={"user_id": TEST_USER_ID},
            json=payload
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["expense"]["amount"] == 10.00
        assert data["expense"]["category"] == "Transport"
        
        # Store for cleanup
        self.__class__.minimal_expense_id = data["expense"]["id"]
    
    def test_list_expenses_returns_created(self):
        """List expenses shows created expenses"""
        response = requests.get(
            f"{API}/expenses/list",
            params={"user_id": TEST_USER_ID}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "expenses" in data
        assert isinstance(data["expenses"], list)
        assert data["total_count"] >= 2  # At least our 2 created expenses
    
    def test_list_expenses_with_limit(self):
        """List expenses respects limit parameter"""
        response = requests.get(
            f"{API}/expenses/list",
            params={"user_id": TEST_USER_ID, "limit": 1}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["expenses"]) == 1
    
    def test_summary_returns_totals(self):
        """Summary endpoint returns correct totals"""
        response = requests.get(
            f"{API}/expenses/summary",
            params={"user_id": TEST_USER_ID}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "total" in data
        assert "count" in data
        assert "by_category" in data
        assert "month" in data
        assert isinstance(data["total"], (int, float))
        assert data["total"] >= 35.50  # At least our 25.50 + 10.00
    
    def test_summary_with_specific_month(self):
        """Summary endpoint filters by month"""
        response = requests.get(
            f"{API}/expenses/summary",
            params={"user_id": TEST_USER_ID, "month": "2026-03"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["month"] == "2026-03"
    
    def test_delete_expense_success(self):
        """Delete expense removes it from list"""
        expense_id = getattr(self.__class__, 'created_expense_id', None)
        if not expense_id:
            pytest.skip("No expense to delete")
        
        response = requests.delete(
            f"{API}/expenses/{expense_id}",
            params={"user_id": TEST_USER_ID}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Uitgave verwijderd"
        
        # Verify deletion via GET
        list_response = requests.get(
            f"{API}/expenses/list",
            params={"user_id": TEST_USER_ID}
        )
        expenses = list_response.json()["expenses"]
        expense_ids = [e["id"] for e in expenses]
        assert expense_id not in expense_ids
    
    def test_delete_nonexistent_expense(self):
        """Delete non-existent expense returns 404"""
        response = requests.delete(
            f"{API}/expenses/nonexistent123",
            params={"user_id": TEST_USER_ID}
        )
        
        assert response.status_code == 404


class TestUitgavenEdgeCases:
    """Edge case tests for expenses"""
    
    def test_empty_user_expenses(self):
        """New user has empty expenses list"""
        new_user_id = f"new_user_{uuid.uuid4().hex[:8]}"
        
        response = requests.get(
            f"{API}/expenses/list",
            params={"user_id": new_user_id}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["expenses"] == []
        assert data["total_count"] == 0
    
    def test_summary_empty_month(self):
        """Summary for month with no expenses"""
        response = requests.get(
            f"{API}/expenses/summary",
            params={"user_id": TEST_USER_ID, "month": "2020-01"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total"] == 0
        assert data["count"] == 0
    
    def test_add_expense_decimal_amount(self):
        """Add expense with decimal amount"""
        payload = {
            "amount": 12.99,
            "category": "Hobby",
            "description": "Decimal test"
        }
        
        response = requests.post(
            f"{API}/expenses/add",
            params={"user_id": TEST_USER_ID},
            json=payload
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["expense"]["amount"] == 12.99


# Cleanup fixture
@pytest.fixture(scope="module", autouse=True)
def cleanup_test_data():
    """Cleanup test data after all tests"""
    yield
    # Cleanup: Delete all expenses for test user
    try:
        response = requests.get(
            f"{API}/expenses/list",
            params={"user_id": TEST_USER_ID}
        )
        if response.status_code == 200:
            expenses = response.json().get("expenses", [])
            for expense in expenses:
                requests.delete(
                    f"{API}/expenses/{expense['id']}",
                    params={"user_id": TEST_USER_ID}
                )
    except Exception:
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
