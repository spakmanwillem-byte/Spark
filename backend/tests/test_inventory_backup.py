"""Tests for Inventory module + backup speed fix (iteration 17)."""
import os
import io
import time
import zipfile
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://question-hub-160.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"


@pytest.fixture(scope="module")
def s():
    return requests.Session()


# ============== BACKUP ==============
class TestBackup:
    def test_full_backup_fast_and_valid(self, s):
        t0 = time.time()
        r = s.get(f"{API}/backup/download/full", timeout=60, stream=True)
        assert r.status_code == 200, r.text[:300]
        # Content-Length must be present
        cl = r.headers.get("Content-Length")
        assert cl is not None and int(cl) > 0
        content = r.content  # download fully
        elapsed = time.time() - t0
        print(f"Full backup: {len(content)} bytes in {elapsed:.1f}s, CL={cl}")
        assert elapsed < 30, f"Backup too slow: {elapsed:.1f}s"
        assert len(content) == int(cl), "Content size mismatch"
        # Validate ZIP
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            names = zf.namelist()
            assert "spark_backup_manifest.json" in names
            assert len(names) > 10

    def test_changes_backup_fast_and_valid(self, s):
        t0 = time.time()
        r = s.get(f"{API}/backup/download/changes", timeout=60)
        assert r.status_code == 200
        elapsed = time.time() - t0
        print(f"Changes backup: {len(r.content)} bytes in {elapsed:.1f}s")
        assert elapsed < 30
        # ZIP must be valid
        with zipfile.ZipFile(io.BytesIO(r.content)) as zf:
            assert "spark_backup_manifest.json" in zf.namelist()


# ============== INVENTORY ==============
class TestInventory:
    def test_get_willem_inventory(self, s):
        r = s.get(f"{API}/inventory/user-001")
        assert r.status_code == 200, r.text
        data = r.json()
        stats = data.get("stats", {})
        cap = data.get("capacity", {})
        assert stats.get("level") == 271, f"Expected level 271, got {stats.get('level')}"
        assert stats.get("rang") == "Generaal"
        assert stats.get("gradatie") == 1
        assert stats.get("is_bot") is False
        assert cap.get("slots_base") == 4
        assert "slots_used" in cap
        assert "slots_total" in cap
        assert "weight_used" in cap
        assert "weight_max" in cap
        assert isinstance(data.get("slots"), list)

    def test_marieke_auto_basis_rugzak(self, s):
        # Delete any existing inv to test first-time init
        inv_path = "/app/backend/data/users/user-c609d7d1/inventory.json"
        try:
            os.remove(inv_path)
        except FileNotFoundError:
            pass
        r = s.get(f"{API}/inventory/user-c609d7d1")
        assert r.status_code == 200
        data = r.json()
        slots = data.get("slots", [])
        # Find basis rugzak
        basis = [s for s in slots if s.get("item_id") == "backpack-basic"]
        assert len(basis) >= 1, f"Expected Basis Rugzak, got slots={slots}"
        assert basis[0].get("capacity_bonus") == 5
        assert basis[0].get("weight_bonus") == 10.0

    def test_bot_harry_inventory(self, s):
        r = s.get(f"{API}/inventory/bot-harry")
        assert r.status_code == 200
        data = r.json()
        stats = data.get("stats", {})
        assert stats.get("is_bot") is True
        assert stats.get("rang") == "Generaal"
        assert stats.get("level") == 277, f"Expected 277, got {stats.get('level')}"
        # Auto basis rugzak
        slots = data.get("slots", [])
        assert any(s.get("item_id") == "backpack-basic" for s in slots)

    def test_catalog(self, s):
        r = s.get(f"{API}/inventory/catalog/all")
        assert r.status_code == 200
        items = r.json().get("items", [])
        ids = {i["id"] for i in items}
        assert ids == {"backpack-basic", "backpack-large", "achievement-token", "auto-bark-pup"}

    def test_add_backpack_large_increases_slots(self, s):
        before = s.get(f"{API}/inventory/user-001").json()
        slots_total_before = before["capacity"]["slots_total"]
        r = s.post(f"{API}/inventory/user-001/items", json={"item_id": "backpack-large"})
        assert r.status_code == 200, r.text
        after = r.json()
        slots_total_after = after["capacity"]["slots_total"]
        assert slots_total_after == slots_total_before + 10, f"{slots_total_before} -> {slots_total_after}"

    def test_add_nonexistent_item(self, s):
        r = s.post(f"{API}/inventory/user-001/items", json={"item_id": "foobar"})
        assert r.status_code == 404

    def test_add_achievement_token(self, s):
        r = s.post(f"{API}/inventory/user-001/items", json={"item_id": "achievement-token"})
        assert r.status_code == 200
        data = r.json()
        assert any(s.get("item_id") == "achievement-token" for s in data["slots"])

    def test_inventory_full_returns_400(self, s):
        # Use a fresh test user. Use bot-smith for isolation; first reset its inventory
        uid = "bot-smith"
        inv_path = f"/app/backend/data/users/{uid}/inventory.json"
        try:
            os.remove(inv_path)
        except FileNotFoundError:
            pass
        # Load → basis rugzak auto-created → slots_total = 4+5=9, slots_used=1
        d = s.get(f"{API}/inventory/{uid}").json()
        cap = d["capacity"]
        to_fill = cap["slots_total"] - cap["slots_used"]
        # Fill with achievement tokens (weight 0.05 each, safe under weight_max)
        for _ in range(to_fill):
            rr = s.post(f"{API}/inventory/{uid}/items", json={"item_id": "achievement-token"})
            assert rr.status_code == 200, rr.text
        # Next add should fail
        r = s.post(f"{API}/inventory/{uid}/items", json={"item_id": "achievement-token"})
        assert r.status_code == 400
        assert "vol" in r.json().get("detail", "").lower()

    def test_delete_item(self, s):
        d = s.get(f"{API}/inventory/user-001").json()
        slots = d["slots"]
        # Find an achievement-token to delete (we added one earlier)
        tok = next((sl for sl in slots if sl.get("item_id") == "achievement-token"), None)
        assert tok is not None, "No achievement-token to delete"
        slot_id = tok["id"]
        before_used = d["capacity"]["slots_used"]
        r = s.delete(f"{API}/inventory/user-001/items/{slot_id}")
        assert r.status_code == 200
        after = r.json()
        assert after["capacity"]["slots_used"] == before_used - 1
        assert not any(sl["id"] == slot_id for sl in after["slots"])

    def test_add_achievement(self, s):
        body = {"code": "first_login_test", "naam": "Eerste Aanmelding"}
        r1 = s.post(f"{API}/inventory/user-001/achievement", json=body)
        assert r1.status_code == 200
        # Second time → already
        r2 = s.post(f"{API}/inventory/user-001/achievement", json=body)
        assert r2.status_code == 200
        assert r2.json().get("already") is True
