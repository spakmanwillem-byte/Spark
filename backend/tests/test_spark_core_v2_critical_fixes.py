"""
Iteration 18: Spark Core 2.0 critical fixes batch
- Wallet reset (user-001=0, user-000=1, spark_system circulating=1)
- Trade bots filter (only running/with-tokens)
- Spark unstoppable
- Urgent glow skips user-000 prive
- Avatar fallback for user-000
- /bugs/mine for non-admin
- Inventory + backup regression
"""
import os
import io
import time
import zipfile
import requests
import pytest

BASE_URL = (os.environ.get("REACT_APP_BACKEND_URL") or "https://question-hub-160.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# ----- 1. WALLET FIX -----
class TestWallet:
    def test_wallet_overview_state(self, session):
        # /wallet/overview returns global system_wallet + current user's wallet
        # Defaults to user-001 (admin)
        r = session.get(f"{API}/wallet/overview")
        assert r.status_code == 200, r.text
        data = r.json()
        sys_w = data.get("system_wallet") or {}
        sys_circ = (sys_w.get("wallet") or {}).get("spark_tokens_circulating")
        assert sys_circ == 1, f"spark_system circulating expected 1, got {sys_circ}"

        # user-001 wallet check via dedicated endpoint
        r1 = session.get(f"{API}/wallet/user/user-001")
        assert r1.status_code == 200, r1.text
        u001 = r1.json()
        assert u001.get("spark_tokens") == 0, f"user-001 tokens expected 0: {u001}"

        # user-000 wallet check via dedicated endpoint
        r0 = session.get(f"{API}/wallet/user/user-000")
        assert r0.status_code == 200, r0.text
        u000 = r0.json()
        assert u000.get("spark_tokens") == 1, f"user-000 tokens expected 1: {u000}"


# ----- 2 & 3. TRADE BOT FILTER + SPARK UNSTOPPABLE -----
class TestTradeAdminBots:
    def test_admin_bots_filtered(self, session):
        r = session.get(f"{API}/trade/admin/bots")
        assert r.status_code == 200, r.text
        data = r.json()
        assert "bots" in data
        assert "total_unfiltered" in data
        bots = data["bots"]
        ids = [b.get("user_id") for b in bots]

        # user-000 (Spark) must always be in the visible list
        assert "user-000" in ids, f"Spark missing in bots: {ids}"
        # user-001 (0 tokens, not running) should be filtered out
        # unless explicitly running -- check if visible, ensure running is true
        for b in bots:
            if b.get("user_id") == "user-001":
                assert b.get("running") is True, (
                    "user-001 has 0 tokens and is in filtered list but not running"
                )
        # total_unfiltered >= len(bots)
        assert data["total_unfiltered"] >= len(bots)

    def test_spark_unstoppable(self, session):
        r = session.post(f"{API}/trade/bot/stop/user-000")
        assert r.status_code in (200, 400, 403), r.text
        data = r.json()
        assert data.get("success") is False, f"Spark should not be stoppable: {data}"
        assert data.get("code") == "SPARK_UNSTOPPABLE", f"Expected SPARK_UNSTOPPABLE code: {data}"


# ----- 4 & 5. URGENT GLOW -----
class TestUrgentGlow:
    def test_glow_skips_spark_dms(self, session):
        r = session.get(f"{API}/urgent/notifications", params={"user_id": "user-001"})
        assert r.status_code == 200, r.text
        data = r.json()
        glow = data.get("glow") or {}
        items = data.get("items") or []
        # Verify no items reference user-000 prive DMs
        prive_items = [i for i in items if i.get("type") == "prive_dm" or "prive" in str(i.get("type", ""))]
        for item in prive_items:
            partner = item.get("partner_id") or item.get("from_id") or item.get("with_user_id")
            assert partner != "user-000", f"prive item from user-000 leaked into glow: {item}"


# ----- 6. AVATAR FALLBACK -----
class TestAvatarFallback:
    def test_user000_avatar_fallback(self, session):
        r = session.get(f"{API}/avatar/current/user-000")
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("is_fallback") is True, f"user-000 should have is_fallback=true: {data}"
        fb = data.get("fallback_url") or ""
        assert "roadkill-logo" in fb, f"fallback_url should reference roadkill-logo: {data}"


# ----- 7 & 8. ROADMAP /bugs/mine -----
class TestBugsMine:
    def test_bugs_mine_user001(self, session):
        r = session.get(f"{API}/bugs/mine", params={"user_id": "user-001"})
        assert r.status_code == 200, r.text
        data = r.json()
        bugs = data.get("bugs") or []
        assert isinstance(bugs, list)
        # Each bug has required fields
        for b in bugs:
            assert "id" in b
            assert "description" in b
            assert "status" in b
            assert "created_at" in b
            assert b.get("created_by_id") == "user-001", f"bug not owned by user-001: {b}"

    def test_bugs_mine_non_admin_no_403(self, session):
        r = session.get(f"{API}/bugs/mine", params={"user_id": "user-c609d7d1"})
        assert r.status_code == 200, f"non-admin should not get 403: {r.status_code} {r.text}"
        data = r.json()
        bugs = data.get("bugs") or []
        for b in bugs:
            assert b.get("created_by_id") == "user-c609d7d1"


# ----- 9. INVENTORY REGRESSION -----
class TestInventoryRegression:
    def test_inventory_user001(self, session):
        r = session.get(f"{API}/inventory/user-001")
        assert r.status_code == 200, r.text
        data = r.json()
        assert isinstance(data, (dict, list))


# ----- 13. BACKUP REGRESSION -----
class TestBackupRegression:
    def test_backup_full_zip(self, session):
        t0 = time.time()
        r = session.get(f"{API}/backup/download/full", timeout=35, stream=True)
        assert r.status_code == 200, f"backup failed: {r.status_code}"
        content = r.content
        elapsed = time.time() - t0
        assert elapsed < 30, f"backup too slow: {elapsed:.2f}s"
        # validate zip
        zf = zipfile.ZipFile(io.BytesIO(content))
        assert len(zf.namelist()) > 0, "empty zip"
