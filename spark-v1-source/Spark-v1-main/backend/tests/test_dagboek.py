"""
Dagboek Module Backend Tests
Tests for: date filtering, CRUD operations, export functionality, tags support
"""
import pytest
import requests
import os
import uuid
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test user ID for isolation
TEST_USER_ID = f"test_dagboek_{uuid.uuid4().hex[:8]}"


class TestDagboekBasicCRUD:
    """Basic CRUD operations for dagboek entries"""
    
    def test_add_entry_success(self):
        """Test adding a new dagboek entry"""
        response = requests.post(f"{BASE_URL}/api/personal/dagboek", json={
            "user_id": TEST_USER_ID,
            "content": "Dit is een test entry voor mijn dagboek",
            "mood": "blij",
            "tags": ["test", "reflectie"]
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "entry" in data
        assert data["entry"]["content"] == "Dit is een test entry voor mijn dagboek"
        assert data["entry"]["mood"] == "blij"
        assert data["entry"]["tags"] == ["test", "reflectie"]
        assert "id" in data["entry"]
        assert "created_at" in data["entry"]
        assert "word_count" in data["entry"]
        
    def test_add_entry_minimal(self):
        """Test adding entry with only content (no mood/tags)"""
        response = requests.post(f"{BASE_URL}/api/personal/dagboek", json={
            "user_id": TEST_USER_ID,
            "content": "Minimale entry zonder mood of tags"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["entry"]["mood"] is None
        assert data["entry"]["tags"] == []
        
    def test_get_entries_returns_list(self):
        """Test getting dagboek entries returns list with stats"""
        response = requests.get(f"{BASE_URL}/api/personal/dagboek/{TEST_USER_ID}")
        
        assert response.status_code == 200
        data = response.json()
        assert "entries" in data
        assert "stats" in data
        assert isinstance(data["entries"], list)
        assert len(data["entries"]) >= 2  # From previous tests
        
    def test_get_entries_sorted_newest_first(self):
        """Test entries are sorted by date (newest first)"""
        response = requests.get(f"{BASE_URL}/api/personal/dagboek/{TEST_USER_ID}")
        
        assert response.status_code == 200
        entries = response.json()["entries"]
        
        if len(entries) >= 2:
            # Verify newest first
            first_date = entries[0]["created_at"]
            second_date = entries[1]["created_at"]
            assert first_date >= second_date


class TestDagboekDateFiltering:
    """Date range filtering tests"""
    
    def test_filter_by_start_date(self):
        """Test filtering entries by start_date"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        response = requests.get(
            f"{BASE_URL}/api/personal/dagboek/{TEST_USER_ID}",
            params={"start_date": today}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "entries" in data
        
        # All entries should be from today or later
        for entry in data["entries"]:
            entry_date = entry["created_at"][:10]
            assert entry_date >= today
            
    def test_filter_by_end_date(self):
        """Test filtering entries by end_date"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        response = requests.get(
            f"{BASE_URL}/api/personal/dagboek/{TEST_USER_ID}",
            params={"end_date": today}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "entries" in data
        
        # All entries should be from today or earlier
        for entry in data["entries"]:
            entry_date = entry["created_at"][:10]
            assert entry_date <= today
            
    def test_filter_by_date_range(self):
        """Test filtering entries by both start_date and end_date"""
        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        response = requests.get(
            f"{BASE_URL}/api/personal/dagboek/{TEST_USER_ID}",
            params={"start_date": yesterday, "end_date": today}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "entries" in data
        
    def test_filter_returns_empty_for_future_dates(self):
        """Test filtering with future dates returns empty"""
        future = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
        
        response = requests.get(
            f"{BASE_URL}/api/personal/dagboek/{TEST_USER_ID}",
            params={"start_date": future}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["entries"] == []


class TestDagboekUpdateEntry:
    """Update entry tests with timestamp tracking"""
    
    @pytest.fixture(autouse=True)
    def setup_entry(self):
        """Create an entry to update"""
        response = requests.post(f"{BASE_URL}/api/personal/dagboek", json={
            "user_id": TEST_USER_ID,
            "content": "Entry om te bewerken",
            "mood": "neutraal",
            "tags": ["origineel"]
        })
        self.entry_id = response.json()["entry"]["id"]
        
    def test_update_entry_content(self):
        """Test updating entry content"""
        response = requests.put(
            f"{BASE_URL}/api/personal/dagboek/{self.entry_id}",
            params={"user_id": TEST_USER_ID},
            json={
                "content": "Bijgewerkte content",
                "mood": "blij",
                "tags": ["bewerkt", "test"]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["entry"]["content"] == "Bijgewerkte content"
        assert data["entry"]["mood"] == "blij"
        assert data["entry"]["tags"] == ["bewerkt", "test"]
        
    def test_update_entry_adds_updated_at(self):
        """Test that updating adds updated_at timestamp"""
        response = requests.put(
            f"{BASE_URL}/api/personal/dagboek/{self.entry_id}",
            params={"user_id": TEST_USER_ID},
            json={
                "content": "Content met timestamp",
                "mood": "energiek",
                "tags": []
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "updated_at" in data["entry"]
        assert data["entry"]["updated_at"] is not None
        
    def test_update_nonexistent_entry(self):
        """Test updating non-existent entry returns failure"""
        response = requests.put(
            f"{BASE_URL}/api/personal/dagboek/nonexistent123",
            params={"user_id": TEST_USER_ID},
            json={
                "content": "Dit zou moeten falen",
                "mood": None,
                "tags": []
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == False


class TestDagboekDeleteEntry:
    """Delete entry tests"""
    
    def test_delete_entry_success(self):
        """Test deleting an entry"""
        # First create an entry
        create_response = requests.post(f"{BASE_URL}/api/personal/dagboek", json={
            "user_id": TEST_USER_ID,
            "content": "Entry om te verwijderen"
        })
        entry_id = create_response.json()["entry"]["id"]
        
        # Delete it
        response = requests.delete(
            f"{BASE_URL}/api/personal/dagboek/{entry_id}",
            params={"user_id": TEST_USER_ID}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "verwijderd" in data["message"].lower()
        
    def test_delete_entry_verify_removed(self):
        """Test that deleted entry is actually removed"""
        # Create entry
        create_response = requests.post(f"{BASE_URL}/api/personal/dagboek", json={
            "user_id": TEST_USER_ID,
            "content": "Entry voor delete verificatie"
        })
        entry_id = create_response.json()["entry"]["id"]
        
        # Get count before
        before = requests.get(f"{BASE_URL}/api/personal/dagboek/{TEST_USER_ID}")
        count_before = len(before.json()["entries"])
        
        # Delete
        requests.delete(
            f"{BASE_URL}/api/personal/dagboek/{entry_id}",
            params={"user_id": TEST_USER_ID}
        )
        
        # Get count after
        after = requests.get(f"{BASE_URL}/api/personal/dagboek/{TEST_USER_ID}")
        count_after = len(after.json()["entries"])
        
        assert count_after == count_before - 1
        
    def test_delete_nonexistent_entry(self):
        """Test deleting non-existent entry returns failure"""
        response = requests.delete(
            f"{BASE_URL}/api/personal/dagboek/nonexistent123",
            params={"user_id": TEST_USER_ID}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == False


class TestDagboekExport:
    """Export functionality tests"""
    
    def test_export_txt_format(self):
        """Test exporting entries as plain text"""
        response = requests.get(
            f"{BASE_URL}/api/personal/dagboek/{TEST_USER_ID}/export",
            params={"format": "txt"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["format"] == "txt"
        assert "content" in data
        assert "DAGBOEK EXPORT" in data["content"]
        
    def test_export_markdown_format(self):
        """Test exporting entries as markdown"""
        response = requests.get(
            f"{BASE_URL}/api/personal/dagboek/{TEST_USER_ID}/export",
            params={"format": "markdown"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["format"] == "markdown"
        assert "content" in data
        assert "# Dagboek Export" in data["content"]
        
    def test_export_with_date_filter(self):
        """Test export respects date filters"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        response = requests.get(
            f"{BASE_URL}/api/personal/dagboek/{TEST_USER_ID}/export",
            params={
                "format": "txt",
                "start_date": today,
                "end_date": today
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        
    def test_export_empty_user(self):
        """Test export for user with no entries"""
        empty_user = f"empty_user_{uuid.uuid4().hex[:8]}"
        
        response = requests.get(
            f"{BASE_URL}/api/personal/dagboek/{empty_user}/export",
            params={"format": "txt"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "Totaal aantal entries: 0" in data["content"]


class TestDagboekTags:
    """Tags functionality tests"""
    
    def test_tags_stored_as_array(self):
        """Test that tags are stored as array"""
        response = requests.post(f"{BASE_URL}/api/personal/dagboek", json={
            "user_id": TEST_USER_ID,
            "content": "Entry met meerdere tags",
            "tags": ["reflectie", "werk", "emotie"]
        })
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["entry"]["tags"], list)
        assert len(data["entry"]["tags"]) == 3
        assert "reflectie" in data["entry"]["tags"]
        
    def test_tags_in_export(self):
        """Test that tags appear in export"""
        # Create entry with tags
        requests.post(f"{BASE_URL}/api/personal/dagboek", json={
            "user_id": TEST_USER_ID,
            "content": "Entry voor export tag test",
            "tags": ["exporttest"]
        })
        
        # Export
        response = requests.get(
            f"{BASE_URL}/api/personal/dagboek/{TEST_USER_ID}/export",
            params={"format": "markdown"}
        )
        
        assert response.status_code == 200
        # Tags should appear with # prefix in markdown
        assert "#exporttest" in response.json()["content"]


class TestDagboekStats:
    """Statistics tests"""
    
    def test_stats_returned_with_entries(self):
        """Test that stats are returned with entries"""
        response = requests.get(f"{BASE_URL}/api/personal/dagboek/{TEST_USER_ID}")
        
        assert response.status_code == 200
        data = response.json()
        assert "stats" in data
        assert "total_entries" in data["stats"]
        assert "total_words" in data["stats"]
        assert "avg_words_per_entry" in data["stats"]
        
    def test_stats_values_correct(self):
        """Test that stats values are calculated correctly"""
        response = requests.get(f"{BASE_URL}/api/personal/dagboek/{TEST_USER_ID}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify total_entries matches actual count
        assert data["stats"]["total_entries"] == len(data["entries"])


class TestDagboekFullFlow:
    """Complete flow test: add → filter → edit → export → delete"""
    
    def test_complete_dagboek_flow(self):
        """Test complete dagboek workflow"""
        flow_user = f"flow_test_{uuid.uuid4().hex[:8]}"
        
        # 1. Add entry with tags
        add_response = requests.post(f"{BASE_URL}/api/personal/dagboek", json={
            "user_id": flow_user,
            "content": "Vandaag voel ik me goed. Dit is een test van de complete flow.",
            "mood": "blij",
            "tags": ["flow", "test"]
        })
        assert add_response.status_code == 200
        entry_id = add_response.json()["entry"]["id"]
        print(f"✓ Created entry: {entry_id}")
        
        # 2. Get entries with date filter
        today = datetime.now().strftime("%Y-%m-%d")
        filter_response = requests.get(
            f"{BASE_URL}/api/personal/dagboek/{flow_user}",
            params={"start_date": today}
        )
        assert filter_response.status_code == 200
        assert len(filter_response.json()["entries"]) == 1
        print("✓ Date filter works")
        
        # 3. Edit entry
        edit_response = requests.put(
            f"{BASE_URL}/api/personal/dagboek/{entry_id}",
            params={"user_id": flow_user},
            json={
                "content": "Bijgewerkte content na edit",
                "mood": "energiek",
                "tags": ["flow", "bewerkt"]
            }
        )
        assert edit_response.status_code == 200
        assert edit_response.json()["entry"]["updated_at"] is not None
        print("✓ Edit with timestamp works")
        
        # 4. Export
        export_response = requests.get(
            f"{BASE_URL}/api/personal/dagboek/{flow_user}/export",
            params={"format": "markdown"}
        )
        assert export_response.status_code == 200
        assert "Bijgewerkte content" in export_response.json()["content"]
        print("✓ Export works")
        
        # 5. Delete
        delete_response = requests.delete(
            f"{BASE_URL}/api/personal/dagboek/{entry_id}",
            params={"user_id": flow_user}
        )
        assert delete_response.status_code == 200
        assert delete_response.json()["success"] == True
        print("✓ Delete works")
        
        # 6. Verify deleted
        verify_response = requests.get(f"{BASE_URL}/api/personal/dagboek/{flow_user}")
        assert len(verify_response.json()["entries"]) == 0
        print("✓ Entry removed from list")
        
        print("\n✅ Complete dagboek flow test PASSED")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
