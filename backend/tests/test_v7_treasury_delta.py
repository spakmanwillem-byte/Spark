"""
Backend tests for Spark Core 2.0 refactor (v7_treasury_delta_001):
- Shadow trader completely removed
- Anchor lock removed (all pots unlocked)
- New /api/trade/delta endpoint (treasury view vs Bitvavo)
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://question-hub-160.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"


@pytest.fixture(scope="module")
def client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# ---------- Delta endpoint ----------
class TestTreasuryDelta:
    def test_delta_endpoint_shape(self, client):
        r = client.get(f"{API}/trade/delta", timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("success") is True
        for key in ["pots_capital_eur", "bitvavo_actual_eur", "delta_eur",
                    "status", "toelichting", "per_user", "spark_kasboek", "as_of"]:
            assert key in data, f"missing key {key}"
        # per_user must contain the 3 known users
        per_user = data["per_user"]
        for uid in ["user-000", "user-001", "user-a0ee2d7e"]:
            assert uid in per_user, f"per_user missing {uid}"
            u = per_user[uid]
            assert "pot_count" in u and "capital_eur" in u and "open_positions" in u

    def test_delta_status_and_dutch_toelichting(self, client):
        r = client.get(f"{API}/trade/delta", timeout=30)
        data = r.json()
        delta = float(data["delta_eur"])
        status = data["status"]
        if abs(delta) < 0.01:
            assert status == "in_sync"
        elif delta > 0.01:
            assert status == "zweeft_op_bitvavo"
        else:
            assert status == "tekort"
        # Toelichting is Dutch and descriptive
        toel = data["toelichting"]
        assert isinstance(toel, str) and len(toel) > 5


# ---------- Pot state (no anchor locked) ----------
class TestPotState:
    @pytest.mark.parametrize("user_id,expected", [
        ("user-000", 10),
        ("user-001", 10),
    ])
    def test_pot_count_and_no_locked(self, client, user_id, expected):
        r = client.get(f"{API}/trade/potjes/{user_id}", timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("success") is True
        pots = data.get("potjes", [])
        assert len(pots) == expected, f"expected {expected} pots for {user_id}, got {len(pots)}"
        locked = [p for p in pots if p.get("pot_locked")]
        assert len(locked) == 0, f"expected 0 locked pots, got {len(locked)}: {[p.get('id') for p in locked]}"


# ---------- Shadow trader removed ----------
class TestShadowRemoved:
    def test_shadow_pots_endpoint_gone(self, client):
        r = client.get(f"{API}/shadow-pots", timeout=15)
        assert r.status_code == 404

    def test_shadow_routes_gone(self, client):
        for path in ["/shadow-pots/user-000", "/shadow/pots"]:
            r = client.get(f"{API}{path}", timeout=15)
            assert r.status_code == 404, f"{path} returned {r.status_code}"


# ---------- Existing trader endpoints still work ----------
class TestExistingTraderEndpoints:
    def test_bitvavo_balance(self, client):
        r = client.get(f"{API}/trade/bitvavo/balance/user-001", timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert data.get("success") is True
        assert "balances" in data
        assert "total_eur" in data

    def test_trade_history(self, client):
        r = client.get(f"{API}/trade/history/user-001", timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert "trades" in data

    def test_trade_stats(self, client):
        r = client.get(f"{API}/trade/stats/user-001", timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert "total_trades" in data
        assert "buys" in data and "sells" in data

    def test_trade_settings(self, client):
        r = client.get(f"{API}/trade/settings/user-001", timeout=15)
        assert r.status_code == 200
        assert "settings" in r.json()

    def test_shop_token_price(self, client):
        r = client.get(f"{API}/shop/token/price", timeout=15)
        assert r.status_code == 200, r.text

    def test_roar_balance(self, client):
        # Actual endpoint is /api/shop/token/balance/{user_id}
        r = client.get(f"{API}/shop/token/balance/user-000", timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "roar_balance" in data
        assert data["user_id"] == "user-000"


# ---------- Monitor/bot endpoints still work (no shadow imports) ----------
class TestBotEndpoints:
    def test_monitor_status(self, client):
        r = client.get(f"{API}/trade/monitor/status", timeout=15)
        assert r.status_code == 200
        assert r.json().get("success") is True

    def test_bot_status_user001(self, client):
        r = client.get(f"{API}/trade/bot/status/user-001", timeout=15)
        assert r.status_code == 200
        assert r.json().get("success") is True

    def test_bot_register_status(self, client):
        r = client.get(f"{API}/trade/bot/register-status/user-001", timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert "registered" in data

    def test_bot_register_endpoint_works(self, client):
        # Ensure register endpoint (was previously auto-linked to shadow) still works
        r = client.post(f"{API}/trade/bot/register/user-001",
                        json={"viewer_id": "user-001"}, timeout=15)
        assert r.status_code == 200, r.text

    def test_admin_bots_listing(self, client):
        r = client.get(f"{API}/trade/admin/bots", timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert data.get("success") is True
        assert isinstance(data.get("bots"), list)
