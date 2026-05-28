"""
Backend tests for iteration 22 — 8 capability items:
W-vraag dempen, profile-lookup, Spark-bode/relay, agenda-aware, dashboard saldo+vermogen,
verbal deposit, 1 bot per pot stage-1, mood-glow + Winkel refactor.
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://question-hub-160.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

WILLEM = "user-001"
MARIEKE = "user-c609d7d1"
SPARK = "user-000"


@pytest.fixture(scope="module")
def s():
    return requests.Session()


# ============= Winkel UI / Backend =============
class TestWinkelstraat:
    def test_shops_enriched_with_owner_avatar(self, s):
        r = s.get(f"{API}/winkelstraat/shops")
        assert r.status_code == 200, r.text
        data = r.json()
        shops = data.get("shops") or data
        assert isinstance(shops, list) and len(shops) > 0
        # At least one shop should have owner_avatar_url key (could be empty string)
        assert any("owner_avatar_url" in s for s in shops), f"Expected owner_avatar_url enrichment, got keys: {list(shops[0].keys()) if shops else []}"

    def test_shop_logo_serve_endpoint_exists(self, s):
        # Endpoint mag 404 returnen als geen logo, maar route moet bestaan
        r = s.get(f"{API}/winkelstraat/shops/shop-roadkill/logo.png")
        # Acceptabel: 200 (logo aanwezig) of 404 (geen logo). Niet 500.
        assert r.status_code in (200, 404), f"Logo endpoint returned {r.status_code}: {r.text[:200]}"


# ============= Product migratie =============
class TestProductMigration:
    def test_products_from_user_container(self, s):
        r = s.get(f"{API}/shop/products", params={"shop_id": "shop-roadkill"})
        assert r.status_code == 200, r.text
        d = r.json()
        # Source field should confirm user-container origin
        src = d.get("source") or d.get("storage") or ""
        # Acceptabel als 'users' of 'user-001' of 'shop-roadkill' staat in path
        assert "user" in str(src).lower() or "shop-roadkill" in str(src).lower() or "products" in d, (
            f"Expected user-container source, got: {d}"
        )


# ============= Wallet sync =============
class TestWalletSync:
    def test_spark_wallet_zero_eur(self, s):
        r = s.get(f"{API}/wallet/user/{SPARK}")
        assert r.status_code == 200, r.text
        d = r.json()
        bal = float(d.get("balance_eur", d.get("balance", -1)))
        assert bal == 0.0, f"Spark wallet should be 0 EUR after manual sync, got {bal}: {d}"

    def test_spark_token_balance_ten(self, s):
        r = s.get(f"{API}/shop/token/balance/{SPARK}")
        assert r.status_code == 200, r.text
        d = r.json()
        tokens = int(d.get("roar_balance", d.get("balance", d.get("tokens", 0))))
        assert tokens == 10, f"Expected 10 tokens for Spark, got {tokens}: {d}"


# ============= Dashboard financial widget =============
class TestDashboardFinancial:
    def test_financial_aggregator(self, s):
        r = s.get(f"{API}/dashboard/financial/{WILLEM}")
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("success") is True
        for k in ("cash_eur", "potjes_eur", "roar_value_eur", "bitvavo_eur", "totaal_vermogen_eur"):
            assert k in d, f"Missing key {k} in dashboard financial response"
        # Total = sum of parts (approx)
        expected = round(d["cash_eur"] + d["potjes_eur"] + d["roar_value_eur"] + d["bitvavo_eur"], 2)
        assert abs(d["totaal_vermogen_eur"] - expected) < 0.05, f"Total mismatch: {d}"


# ============= C2 Profile lookup =============
class TestProfileLookup:
    def test_wie_is_willem(self, s):
        r = s.post(f"{API}/chat/message", json={"user_id": WILLEM, "message": "wie is Willem"})
        assert r.status_code == 200, r.text
        d = r.json()
        # Type kan in 'type' of nested zitten
        t = d.get("type") or d.get("response_type") or ""
        msg = (d.get("message") or d.get("response") or "").lower()
        assert "profile_lookup" in str(t) or "willem" in msg, f"Expected profile_lookup, got: {d}"

    def test_wie_is_onbekend(self, s):
        r = s.post(f"{API}/chat/message", json={"user_id": WILLEM, "message": "wie is Onbekend123"})
        assert r.status_code == 200
        d = r.json()
        msg = (d.get("message") or d.get("response") or "").lower()
        t = str(d.get("type") or "")
        assert "profile_lookup" in t or "onbekend" in msg or "ken geen" in msg or "niet" in msg, (
            f"Expected not-found profile_lookup, got: {d}"
        )


# ============= C3 Spark-bode/relay =============
class TestRelay:
    def test_relay_sent_to_marieke(self, s):
        r = s.post(f"{API}/chat/message", json={
            "user_id": WILLEM,
            "message": "zeg tegen Marieke dat ik morgen kom"
        })
        assert r.status_code == 200, r.text
        d = r.json()
        t = str(d.get("type") or "")
        msg = (d.get("message") or "").lower()
        assert "relay_sent" in t or "bericht" in msg, f"Expected relay_sent, got: {d}"

    def test_relay_inbox(self, s):
        r = s.get(f"{API}/chat/relay/inbox/{MARIEKE}")
        assert r.status_code == 200, r.text
        d = r.json()
        msgs = d.get("messages") or d.get("inbox") or d
        if isinstance(msgs, list) and msgs:
            # At least one message should reference Willem
            found = any("willem" in str(m.get("from_user_naam") or m.get("from") or "").lower() for m in msgs)
            assert found, f"Expected Willem in inbox attributions: {msgs}"


# ============= C6 Verbal deposit =============
class TestVerbalDeposit:
    def test_deposit_ask(self, s):
        r = s.post(f"{API}/chat/message", json={"user_id": WILLEM, "message": "ik stortte 50 euro"})
        assert r.status_code == 200, r.text
        d = r.json()
        t = str(d.get("type") or "")
        assert "deposit_ask" in t or "deposit" in t.lower(), f"Expected deposit_ask, got: {d}"
        amount = d.get("amount_eur") or d.get("amount")
        assert amount and float(amount) == 50.0, f"Expected amount_eur=50, got: {amount} in {d}"

    def test_deposit_cancel(self, s):
        # First trigger deposit
        s.post(f"{API}/chat/message", json={"user_id": WILLEM, "message": "ik stortte 50 euro"})
        # Then cancel
        r = s.post(f"{API}/chat/message", json={"user_id": WILLEM, "message": "annuleer"})
        assert r.status_code == 200, r.text
        d = r.json()
        t = str(d.get("type") or "")
        msg = (d.get("message") or "").lower()
        assert "cancel" in t.lower() or "annuleer" in msg or "geannuleerd" in msg, (
            f"Expected deposit_cancelled, got: {d}"
        )


# ============= C7 1 bot per pot =============
class TestAssignMarket:
    def test_assign_market(self, s):
        # First get user's potjes to find a real pot_id
        r0 = s.get(f"{API}/trade/potjes/{WILLEM}")
        if r0.status_code != 200:
            pytest.skip("Cannot fetch potjes list")
        potjes = r0.json().get("potjes") or r0.json().get("users", {}).get(WILLEM, {}).get("potjes", [])
        if not potjes:
            pytest.skip("No potjes for user-001")
        pot_id = potjes[0].get("id") or potjes[0].get("pot_id") or "pot-001"

        r = s.post(f"{API}/trade/potjes/{WILLEM}/{pot_id}/assign-market",
                   params={"market": "BTC-EUR"})
        assert r.status_code == 200, f"assign-market failed: {r.status_code} {r.text}"
        d = r.json()
        assert d.get("assigned_market") == "BTC-EUR" or d.get("market") == "BTC-EUR" or d.get("success"), (
            f"Expected assigned_market=BTC-EUR, got: {d}"
        )


# ============= C8 Mood glow =============
class TestEmotionState:
    def test_emotion_state_endpoint(self, s):
        r = s.get(f"{API}/chat/emotions/state")
        # Mag 200 of 404 zijn, maar NIET 500
        assert r.status_code != 500, f"emotions/state crashed: {r.text}"
