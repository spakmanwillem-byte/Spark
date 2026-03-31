"""
Spark Core 2.0 - Backend API Tests
Tests for Gesprekken, Kennisbank, and Integraties features
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHealthAndAuth:
    """Basic health and auth tests"""
    
    def test_health_check(self):
        """Test health endpoint"""
        response = requests.get(f"{BASE_URL}/api/system/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print(f"✅ Health check passed: {data}")
    
    def test_api_root(self):
        """Test API root endpoint"""
        response = requests.get(f"{BASE_URL}/api")
        assert response.status_code == 200
        data = response.json()
        assert "modules" in data
        assert data["name"] == "Spark Core"
        print(f"✅ API root passed: {data['name']} v{data['version']}")
    
    def test_login_valid_credentials(self):
        """Test login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "naam": "Willem",
            "sleutelwoord": "Appelsap"
        })
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "user" in data
        print(f"✅ Login passed: {data['user'].get('naam')}")


class TestKnowledgeAPI:
    """Knowledge base API tests"""
    
    def test_knowledge_stats(self):
        """Test GET /api/knowledge/stats returns correct stats"""
        response = requests.get(f"{BASE_URL}/api/knowledge/stats")
        assert response.status_code == 200
        data = response.json()
        
        # Verify stats structure
        assert "total" in data
        assert "answered" in data
        assert "unanswered" in data
        assert "te_herzien" in data
        
        # Verify expected values (2424 total, 31 onbeantwoord, 2393 beantwoord, 10 te herzien)
        assert data["total"] == 2424, f"Expected 2424 total, got {data['total']}"
        assert data["unanswered"] == 31, f"Expected 31 unanswered, got {data['unanswered']}"
        assert data["answered"] == 2393, f"Expected 2393 answered, got {data['answered']}"
        assert data["te_herzien"] == 10, f"Expected 10 te_herzien, got {data['te_herzien']}"
        
        print(f"✅ Knowledge stats: total={data['total']}, answered={data['answered']}, unanswered={data['unanswered']}, te_herzien={data['te_herzien']}")
    
    def test_knowledge_search_roadkill(self):
        """Test GET /api/knowledge/all?search=roadkill returns filtered results"""
        response = requests.get(f"{BASE_URL}/api/knowledge/all", params={
            "search": "roadkill",
            "per_page": 50
        })
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "entries" in data
        assert "total" in data
        assert "page" in data
        
        # Verify search results
        assert data["total"] >= 1, "Should find at least 1 roadkill entry"
        
        # Verify entries contain roadkill
        for entry in data["entries"]:
            begrip = entry.get("begrip", "").lower()
            assert "roadkill" in begrip, f"Entry '{begrip}' should contain 'roadkill'"
        
        print(f"✅ Knowledge search 'roadkill': found {data['total']} entries")
    
    def test_knowledge_all_pagination(self):
        """Test GET /api/knowledge/all with pagination"""
        response = requests.get(f"{BASE_URL}/api/knowledge/all", params={
            "page": 1,
            "per_page": 50
        })
        assert response.status_code == 200
        data = response.json()
        
        assert "entries" in data
        assert "total_pages" in data
        assert len(data["entries"]) <= 50
        assert data["page"] == 1
        
        print(f"✅ Knowledge pagination: page {data['page']} of {data['total_pages']}, {len(data['entries'])} entries")
    
    def test_knowledge_filter_unanswered(self):
        """Test GET /api/knowledge/all with unanswered filter"""
        response = requests.get(f"{BASE_URL}/api/knowledge/all", params={
            "status_filter": "unanswered",
            "per_page": 50
        })
        assert response.status_code == 200
        data = response.json()
        
        # All entries should be unanswered
        for entry in data["entries"]:
            assert entry.get("is_answered") == False, f"Entry should be unanswered"
        
        print(f"✅ Knowledge filter unanswered: {data['total']} entries")
    
    def test_knowledge_filter_answered(self):
        """Test GET /api/knowledge/all with answered filter"""
        response = requests.get(f"{BASE_URL}/api/knowledge/all", params={
            "status_filter": "answered",
            "per_page": 50
        })
        assert response.status_code == 200
        data = response.json()
        
        # All entries should be answered
        for entry in data["entries"]:
            assert entry.get("is_answered") == True, f"Entry should be answered"
        
        print(f"✅ Knowledge filter answered: {data['total']} entries")
    
    def test_knowledge_get_single_entry(self):
        """Test GET /api/knowledge/{id} returns single entry with full details"""
        # First get an entry ID
        list_response = requests.get(f"{BASE_URL}/api/knowledge/all", params={"per_page": 1})
        assert list_response.status_code == 200
        entries = list_response.json().get("entries", [])
        assert len(entries) > 0, "Should have at least one entry"
        
        entry_id = entries[0]["id"]
        
        # Get single entry
        response = requests.get(f"{BASE_URL}/api/knowledge/{entry_id}")
        assert response.status_code == 200
        data = response.json()
        
        # Verify full entry structure
        assert "id" in data
        assert "begrip" in data
        assert data["id"] == entry_id
        
        print(f"✅ Knowledge single entry: {data.get('begrip')}")
    
    def test_knowledge_get_tags(self):
        """Test GET /api/knowledge/tags returns all tags"""
        response = requests.get(f"{BASE_URL}/api/knowledge/tags")
        assert response.status_code == 200
        data = response.json()
        
        assert "tags" in data
        assert isinstance(data["tags"], list)
        
        print(f"✅ Knowledge tags: {len(data['tags'])} unique tags")


class TestFilesAPI:
    """Files browser API tests"""
    
    def test_files_tree(self):
        """Test GET /api/files/tree returns file tree with 100+ files"""
        response = requests.get(f"{BASE_URL}/api/files/tree")
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("success") == True
        assert "tree" in data
        assert "total_files" in data
        
        # Should have 100+ files
        assert data["total_files"] >= 100, f"Expected 100+ files, got {data['total_files']}"
        
        # Verify tree structure
        assert len(data["tree"]) >= 2, "Should have at least 2 directories (backend, frontend)"
        
        for dir_entry in data["tree"]:
            assert "name" in dir_entry
            assert "files" in dir_entry
            assert isinstance(dir_entry["files"], list)
        
        print(f"✅ Files tree: {data['total_files']} files in {len(data['tree'])} directories")
    
    def test_files_content(self):
        """Test GET /api/files/content returns file content"""
        # Get a file path first
        tree_response = requests.get(f"{BASE_URL}/api/files/tree")
        assert tree_response.status_code == 200
        tree_data = tree_response.json()
        
        # Find a Python file
        test_file = None
        for dir_entry in tree_data["tree"]:
            for f in dir_entry["files"]:
                if f["file_type"] == "python" and not f.get("protected"):
                    test_file = f["path"]
                    break
            if test_file:
                break
        
        if test_file:
            response = requests.get(f"{BASE_URL}/api/files/content", params={
                "file_path": test_file
            })
            assert response.status_code == 200
            data = response.json()
            
            assert data.get("success") == True
            assert "content" in data
            assert "file_type" in data
            assert len(data["content"]) > 0
            
            print(f"✅ Files content: {test_file} ({data['lines']} lines)")
        else:
            print("⚠️ No unprotected Python file found to test")


class TestModulesAPI:
    """Module sandbox API tests"""
    
    def test_modules_list(self):
        """Test GET /api/modules/list returns modules list"""
        response = requests.get(f"{BASE_URL}/api/modules/list")
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("success") == True
        assert "modules" in data
        assert isinstance(data["modules"], list)
        
        print(f"✅ Modules list: {len(data['modules'])} modules")
    
    def test_modules_create_and_delete(self):
        """Test POST /api/modules/create and DELETE /api/modules/delete"""
        # Create a test module
        create_response = requests.post(f"{BASE_URL}/api/modules/create", json={
            "name": "pytest_test_module",
            "type": "backend",
            "description": "Test module created by pytest"
        })
        assert create_response.status_code == 200
        create_data = create_response.json()
        
        assert create_data.get("success") == True
        assert "config" in create_data
        
        print(f"✅ Module created: {create_data['config']['name']}")
        
        # Verify module appears in list
        list_response = requests.get(f"{BASE_URL}/api/modules/list")
        list_data = list_response.json()
        module_names = [m["name"] for m in list_data["modules"]]
        assert "pytest_test_module" in module_names, "Created module should appear in list"
        
        # Delete the test module
        delete_response = requests.delete(f"{BASE_URL}/api/modules/delete/pytest_test_module")
        assert delete_response.status_code == 200
        delete_data = delete_response.json()
        
        assert delete_data.get("success") == True
        
        print(f"✅ Module deleted: pytest_test_module")
        
        # Verify module is removed from list
        list_response2 = requests.get(f"{BASE_URL}/api/modules/list")
        list_data2 = list_response2.json()
        module_names2 = [m["name"] for m in list_data2["modules"]]
        assert "pytest_test_module" not in module_names2, "Deleted module should not appear in list"


class TestSortingAndFiltering:
    """Test sorting and filtering options"""
    
    def test_knowledge_sort_alpha_asc(self):
        """Test sorting A-Z"""
        response = requests.get(f"{BASE_URL}/api/knowledge/all", params={
            "sort_by": "alpha-asc",
            "per_page": 10
        })
        assert response.status_code == 200
        data = response.json()
        
        entries = data["entries"]
        if len(entries) >= 2:
            begrippen = [e["begrip"].lower() for e in entries]
            assert begrippen == sorted(begrippen), "Entries should be sorted A-Z"
        
        print(f"✅ Knowledge sort A-Z working")
    
    def test_knowledge_sort_alpha_desc(self):
        """Test sorting Z-A"""
        response = requests.get(f"{BASE_URL}/api/knowledge/all", params={
            "sort_by": "alpha-desc",
            "per_page": 10
        })
        assert response.status_code == 200
        data = response.json()
        
        entries = data["entries"]
        if len(entries) >= 2:
            begrippen = [e["begrip"].lower() for e in entries]
            assert begrippen == sorted(begrippen, reverse=True), "Entries should be sorted Z-A"
        
        print(f"✅ Knowledge sort Z-A working")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
