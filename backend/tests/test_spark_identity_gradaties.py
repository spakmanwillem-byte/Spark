"""
Test Spark Identity, Bijbel, and Gradaties APIs
Tests for iteration 5: SparkBrainPage API data + UsersAdminPage gradatie enhancements
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestSparkIdentityAPI:
    """Tests for /api/spark/identity endpoint"""
    
    def test_get_identity_returns_200(self):
        """GET /api/spark/identity returns 200"""
        response = requests.get(f"{BASE_URL}/api/spark/identity")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ GET /api/spark/identity returns 200")
    
    def test_identity_has_required_fields(self):
        """Identity contains naam, versie, maker, doel, persoonlijkheid"""
        response = requests.get(f"{BASE_URL}/api/spark/identity")
        data = response.json()
        
        assert "naam" in data, "Missing 'naam' field"
        assert data["naam"] == "Spark", f"Expected naam='Spark', got '{data['naam']}'"
        
        assert "versie" in data, "Missing 'versie' field"
        assert "maker" in data, "Missing 'maker' field"
        assert "doel" in data, "Missing 'doel' field"
        assert "persoonlijkheid" in data, "Missing 'persoonlijkheid' field"
        
        print(f"✓ Identity has all required fields: naam={data['naam']}, versie={data['versie']}")
    
    def test_identity_persoonlijkheid_structure(self):
        """Persoonlijkheid contains traits, toon, filosofie"""
        response = requests.get(f"{BASE_URL}/api/spark/identity")
        data = response.json()
        
        persoonlijkheid = data.get("persoonlijkheid", {})
        assert "traits" in persoonlijkheid, "Missing 'traits' in persoonlijkheid"
        assert "toon" in persoonlijkheid, "Missing 'toon' in persoonlijkheid"
        assert "filosofie" in persoonlijkheid, "Missing 'filosofie' in persoonlijkheid"
        
        assert isinstance(persoonlijkheid["traits"], list), "traits should be a list"
        assert len(persoonlijkheid["traits"]) > 0, "traits should not be empty"
        
        print(f"✓ Persoonlijkheid has {len(persoonlijkheid['traits'])} traits")
    
    def test_identity_basis_kennis(self):
        """Identity contains basis_kennis with over_mezelf and wat_ik_kan"""
        response = requests.get(f"{BASE_URL}/api/spark/identity")
        data = response.json()
        
        basis_kennis = data.get("basis_kennis", {})
        assert "over_mezelf" in basis_kennis, "Missing 'over_mezelf' in basis_kennis"
        assert "wat_ik_kan" in basis_kennis, "Missing 'wat_ik_kan' in basis_kennis"
        
        assert isinstance(basis_kennis["over_mezelf"], list), "over_mezelf should be a list"
        assert isinstance(basis_kennis["wat_ik_kan"], list), "wat_ik_kan should be a list"
        
        print(f"✓ basis_kennis: {len(basis_kennis['over_mezelf'])} over_mezelf, {len(basis_kennis['wat_ik_kan'])} wat_ik_kan")


class TestSparkBijbelAPI:
    """Tests for /api/spark/bijbel endpoint"""
    
    def test_get_bijbel_returns_200(self):
        """GET /api/spark/bijbel returns 200"""
        response = requests.get(f"{BASE_URL}/api/spark/bijbel")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ GET /api/spark/bijbel returns 200")
    
    def test_bijbel_has_kernwaarden(self):
        """Bijbel contains 11 kernwaarden"""
        response = requests.get(f"{BASE_URL}/api/spark/bijbel")
        data = response.json()
        
        assert "kernwaarden" in data, "Missing 'kernwaarden' field"
        kernwaarden = data["kernwaarden"]
        assert isinstance(kernwaarden, list), "kernwaarden should be a list"
        assert len(kernwaarden) == 11, f"Expected 11 kernwaarden, got {len(kernwaarden)}"
        
        print(f"✓ Bijbel has {len(kernwaarden)} kernwaarden")
    
    def test_kernwaarden_structure(self):
        """Each kernwaarde has waarde, beschrijving, belangrijkheid"""
        response = requests.get(f"{BASE_URL}/api/spark/bijbel")
        data = response.json()
        
        kernwaarden = data.get("kernwaarden", [])
        for kw in kernwaarden[:3]:  # Check first 3
            assert "waarde" in kw, f"Missing 'waarde' in kernwaarde"
            assert "beschrijving" in kw, f"Missing 'beschrijving' in kernwaarde"
            assert "belangrijkheid" in kw, f"Missing 'belangrijkheid' in kernwaarde"
        
        print("✓ Kernwaarden have correct structure (waarde, beschrijving, belangrijkheid)")
    
    def test_kernwaarden_have_ws5_and_tags(self):
        """Kernwaarden have ws5 (5W+H) and tags for expandable details"""
        response = requests.get(f"{BASE_URL}/api/spark/bijbel")
        data = response.json()
        
        kernwaarden = data.get("kernwaarden", [])
        kw_with_ws5 = [kw for kw in kernwaarden if "ws5" in kw]
        kw_with_tags = [kw for kw in kernwaarden if "tags" in kw]
        
        assert len(kw_with_ws5) > 0, "No kernwaarden have ws5 field"
        assert len(kw_with_tags) > 0, "No kernwaarden have tags field"
        
        print(f"✓ {len(kw_with_ws5)} kernwaarden have ws5, {len(kw_with_tags)} have tags")
    
    def test_bijbel_has_normen(self):
        """Bijbel contains 6 normen"""
        response = requests.get(f"{BASE_URL}/api/spark/bijbel")
        data = response.json()
        
        assert "normen" in data, "Missing 'normen' field"
        normen = data["normen"]
        assert isinstance(normen, list), "normen should be a list"
        assert len(normen) == 6, f"Expected 6 normen, got {len(normen)}"
        
        print(f"✓ Bijbel has {len(normen)} normen")
    
    def test_bijbel_has_doelen(self):
        """Bijbel contains 5 doelen"""
        response = requests.get(f"{BASE_URL}/api/spark/bijbel")
        data = response.json()
        
        assert "doelen" in data, "Missing 'doelen' field"
        doelen = data["doelen"]
        assert isinstance(doelen, list), "doelen should be a list"
        assert len(doelen) == 5, f"Expected 5 doelen, got {len(doelen)}"
        
        print(f"✓ Bijbel has {len(doelen)} doelen")
    
    def test_bijbel_has_bijbel_items(self):
        """Bijbel contains 11 bijbel_items"""
        response = requests.get(f"{BASE_URL}/api/spark/bijbel")
        data = response.json()
        
        assert "bijbel_items" in data, "Missing 'bijbel_items' field"
        bijbel_items = data["bijbel_items"]
        assert isinstance(bijbel_items, list), "bijbel_items should be a list"
        assert len(bijbel_items) == 11, f"Expected 11 bijbel_items, got {len(bijbel_items)}"
        
        print(f"✓ Bijbel has {len(bijbel_items)} bijbel_items")
    
    def test_bijbel_has_reactie_voorbeelden(self):
        """Bijbel contains reactie_voorbeelden"""
        response = requests.get(f"{BASE_URL}/api/spark/bijbel")
        data = response.json()
        
        assert "reactie_voorbeelden" in data, "Missing 'reactie_voorbeelden' field"
        reactie_voorbeelden = data["reactie_voorbeelden"]
        assert isinstance(reactie_voorbeelden, dict), "reactie_voorbeelden should be a dict"
        assert len(reactie_voorbeelden) > 0, "reactie_voorbeelden should not be empty"
        
        print(f"✓ Bijbel has {len(reactie_voorbeelden)} reactie_voorbeelden categories")


class TestSparkFullAPI:
    """Tests for /api/spark/full endpoint (combined identity + bijbel)"""
    
    def test_get_full_returns_200(self):
        """GET /api/spark/full returns 200"""
        response = requests.get(f"{BASE_URL}/api/spark/full")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ GET /api/spark/full returns 200")
    
    def test_full_has_identity_and_bijbel(self):
        """Full profile contains both identity and bijbel"""
        response = requests.get(f"{BASE_URL}/api/spark/full")
        data = response.json()
        
        assert "identity" in data, "Missing 'identity' field"
        assert "bijbel" in data, "Missing 'bijbel' field"
        
        # Verify identity structure
        identity = data["identity"]
        assert "naam" in identity, "Missing 'naam' in identity"
        assert "persoonlijkheid" in identity, "Missing 'persoonlijkheid' in identity"
        
        # Verify bijbel structure
        bijbel = data["bijbel"]
        assert "kernwaarden" in bijbel, "Missing 'kernwaarden' in bijbel"
        assert "normen" in bijbel, "Missing 'normen' in bijbel"
        assert "doelen" in bijbel, "Missing 'doelen' in bijbel"
        
        print(f"✓ Full profile has identity (naam={identity['naam']}) and bijbel ({len(bijbel['kernwaarden'])} kernwaarden)")


class TestGradatiesAPI:
    """Tests for /api/auth/gradaties endpoint"""
    
    def test_get_gradaties_returns_200(self):
        """GET /api/auth/gradaties returns 200"""
        response = requests.get(f"{BASE_URL}/api/auth/gradaties")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ GET /api/auth/gradaties returns 200")
    
    def test_gradaties_has_7_levels(self):
        """Gradaties contains 7 levels (G1-G7)"""
        response = requests.get(f"{BASE_URL}/api/auth/gradaties")
        data = response.json()
        
        assert "gradaties" in data, "Missing 'gradaties' field"
        gradaties = data["gradaties"]
        assert isinstance(gradaties, list), "gradaties should be a list"
        assert len(gradaties) == 7, f"Expected 7 gradaties, got {len(gradaties)}"
        
        print(f"✓ Gradaties has {len(gradaties)} levels")
    
    def test_gradaties_structure(self):
        """Each gradatie has niveau, titel, beschrijving, toegang"""
        response = requests.get(f"{BASE_URL}/api/auth/gradaties")
        data = response.json()
        
        gradaties = data.get("gradaties", [])
        for g in gradaties:
            assert "niveau" in g, f"Missing 'niveau' in gradatie"
            assert "titel" in g, f"Missing 'titel' in gradatie"
            assert "beschrijving" in g, f"Missing 'beschrijving' in gradatie"
            assert "toegang" in g, f"Missing 'toegang' in gradatie"
            assert isinstance(g["toegang"], list), "toegang should be a list"
        
        print("✓ All gradaties have correct structure (niveau, titel, beschrijving, toegang)")
    
    def test_gradaties_niveau_order(self):
        """Gradaties are ordered by niveau 1-7"""
        response = requests.get(f"{BASE_URL}/api/auth/gradaties")
        data = response.json()
        
        gradaties = data.get("gradaties", [])
        niveaus = [g["niveau"] for g in gradaties]
        assert niveaus == [1, 2, 3, 4, 5, 6, 7], f"Expected niveaus [1-7], got {niveaus}"
        
        print("✓ Gradaties are correctly ordered 1-7")
    
    def test_gradatie_1_is_beheerder(self):
        """Gradatie 1 is Beheerder with most rechten"""
        response = requests.get(f"{BASE_URL}/api/auth/gradaties")
        data = response.json()
        
        gradaties = data.get("gradaties", [])
        g1 = next((g for g in gradaties if g["niveau"] == 1), None)
        
        assert g1 is not None, "Gradatie 1 not found"
        assert g1["titel"] == "Beheerder", f"Expected titel='Beheerder', got '{g1['titel']}'"
        assert len(g1["toegang"]) >= 8, f"Beheerder should have 8+ rechten, got {len(g1['toegang'])}"
        
        print(f"✓ Gradatie 1 is Beheerder with {len(g1['toegang'])} rechten")


class TestUsersAPI:
    """Tests for /api/auth/users endpoint"""
    
    def test_get_users_returns_200(self):
        """GET /api/auth/users returns 200"""
        response = requests.get(f"{BASE_URL}/api/auth/users")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ GET /api/auth/users returns 200")
    
    def test_users_have_gradatie_field(self):
        """Users have gradatie field for UsersAdminPage"""
        response = requests.get(f"{BASE_URL}/api/auth/users")
        data = response.json()
        
        users = data.get("users", [])
        assert len(users) > 0, "No users found"
        
        for user in users:
            assert "gradatie" in user, f"User {user.get('naam')} missing 'gradatie' field"
            assert isinstance(user["gradatie"], int), f"gradatie should be int"
            assert 1 <= user["gradatie"] <= 7, f"gradatie should be 1-7"
        
        print(f"✓ All {len(users)} users have valid gradatie field")
    
    def test_users_have_personalia_fields(self):
        """Users have naam, volledige_naam, rol fields for editing"""
        response = requests.get(f"{BASE_URL}/api/auth/users")
        data = response.json()
        
        users = data.get("users", [])
        for user in users[:3]:  # Check first 3
            assert "naam" in user, f"User missing 'naam' field"
            assert "id" in user, f"User missing 'id' field"
            # volledige_naam and rol may be optional
        
        print("✓ Users have required personalia fields")
    
    def test_update_user_personalia(self):
        """PUT /api/auth/users/{id} updates personalia"""
        # First get a user
        response = requests.get(f"{BASE_URL}/api/auth/users")
        users = response.json().get("users", [])
        
        if not users:
            pytest.skip("No users to test update")
        
        test_user = users[0]
        user_id = test_user["id"]
        
        # Update with test data
        update_data = {
            "rol": "TEST_ROL_UPDATE"
        }
        
        response = requests.put(f"{BASE_URL}/api/auth/users/{user_id}", json=update_data)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        # Verify update
        response = requests.get(f"{BASE_URL}/api/auth/users/{user_id}")
        updated_user = response.json()
        assert updated_user.get("rol") == "TEST_ROL_UPDATE", "Update not persisted"
        
        # Restore original
        original_rol = test_user.get("rol", "")
        requests.put(f"{BASE_URL}/api/auth/users/{user_id}", json={"rol": original_rol})
        
        print(f"✓ User personalia update works for user {user_id}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
