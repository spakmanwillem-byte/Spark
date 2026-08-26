"""
Iteration 21 — P1-P4 plan: Winkelstraat backend + Kasboek reconcile + 1-token-1-potje +
Chat capability-routing for 5 intents.
"""
import os
import pytest
import requests
from pathlib import Path

# Load REACT_APP_BACKEND_URL from frontend/.env
def _load_backend_url():
    if os.environ.get("REACT_APP_BACKEND_URL"):
        return os.environ["REACT_APP_BACKEND_URL"]
    env_path = Path("/app/frontend/.env")
    for line in env_path.read_text().splitlines():
        if line.startswith("REACT_APP_BACKEND_URL="):
            return line.split("=", 1)[1].strip()
    raise RuntimeError("REACT_APP_BACKEND_URL not set")

BASE_URL = _load_backend_url().rstrip("/")
API = f"{BASE_URL}/api"

ADMIN = "user-001"          # Willem gradatie 1
MARIEKE = "user-c609d7d1"   # Marieke gradatie 3
GIJS = "user-a0ee2d7e"      # Gijs gradatie 3, 2 ROAR



# v13d_pytest_book_teardown_001 (sessie 56b) — Willem: "je pytest laat TEST_
# books achter in mijn boekhouding-tab". Shop-close markeert alleen status
# 'closing', linked book blijft staan. Deze module-teardown ruimt alle
# book-folders op die als naam met 'TEST_' beginnen.
@pytest.fixture(scope="module", autouse=True)
def _cleanup_test_books():
    yield
    import shutil, json
    books_dir = Path("/app/backend/data/boekhouding/books")
    if not books_dir.exists():
        return
    removed = []
    for entry in books_dir.iterdir():
        if not entry.is_dir():
            continue
        meta = entry / "_meta.json"
        if not meta.exists():
            continue
        try:
            m = json.loads(meta.read_text())
            if (m.get("naam") or "").startswith("TEST_"):
                shutil.rmtree(entry)
                removed.append(m["naam"])
        except Exception:
            pass
    if removed:
        print(f"\n[cleanup] {len(removed)} TEST_ books opgeruimd: {removed}")



# --------- Winkelstraat ---------
class TestWinkelstraat:
    def test_list_shops(self):
        r = requests.get(f"{API}/winkelstraat/shops")
        assert r.status_code == 200
        d = r.json()
        assert d["success"] is True
        assert d["min_gradatie_to_open"] == 4
        # Roadkillshop should exist
        ids = [s["id"] for s in d["shops"]]
        assert any("roadkill" in i.lower() for i in ids), f"shops: {ids}"

    def test_admin_can_create_shop_bypass(self):
        body = {
            "naam": "TEST_AdminShop",
            "type": "digitaal",
            "owner_user_id": ADMIN,
            "owner_naam": "Willem",
            "voorwaarden_geaccepteerd": True,
        }
        r = requests.post(f"{API}/winkelstraat/shops", json=body)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["success"] is True
        shop_id = d["shop"]["id"]
        # Persist verify
        g = requests.get(f"{API}/winkelstraat/shops/{shop_id}").json()
        assert g["shop"]["naam"] == "TEST_AdminShop"
        # Cleanup via close
        requests.post(f"{API}/winkelstraat/shops/{shop_id}/close",
                      json={"actor_user_id": ADMIN, "reden": "cleanup"})

    def test_non_admin_low_grad_blocked(self):
        body = {
            "naam": "TEST_MariekeShop",
            "type": "merch",
            "owner_user_id": MARIEKE,
            "voorwaarden_geaccepteerd": True,
        }
        r = requests.post(f"{API}/winkelstraat/shops", json=body)
        assert r.status_code == 403, f"expected 403, got {r.status_code}: {r.text}"

    def test_terms_must_be_accepted(self):
        body = {
            "naam": "TEST_NoTerms",
            "owner_user_id": ADMIN,
            "voorwaarden_geaccepteerd": False,
        }
        r = requests.post(f"{API}/winkelstraat/shops", json=body)
        assert r.status_code == 400

    def test_patch_owner_only(self):
        # Create as admin
        body = {
            "naam": "TEST_PatchShop",
            "owner_user_id": ADMIN,
            "voorwaarden_geaccepteerd": True,
        }
        c = requests.post(f"{API}/winkelstraat/shops", json=body)
        assert c.status_code == 200
        sid = c.json()["shop"]["id"]
        try:
            # Non-owner Marieke -> 403
            r = requests.patch(f"{API}/winkelstraat/shops/{sid}",
                               json={"actor_user_id": MARIEKE, "patch": {"tagline": "evil"}})
            assert r.status_code == 403
            # Owner -> 200
            r2 = requests.patch(f"{API}/winkelstraat/shops/{sid}",
                                json={"actor_user_id": ADMIN, "patch": {"tagline": "ok"}})
            assert r2.status_code == 200
            assert r2.json()["shop"]["tagline"] == "ok"
        finally:
            requests.post(f"{API}/winkelstraat/shops/{sid}/close",
                          json={"actor_user_id": ADMIN, "reden": "cleanup"})

    def test_close_sets_closing_status(self):
        # Use a fresh test shop
        body = {"naam": "TEST_CloseMe", "owner_user_id": ADMIN, "voorwaarden_geaccepteerd": True}
        c = requests.post(f"{API}/winkelstraat/shops", json=body).json()
        sid = c["shop"]["id"]
        r = requests.post(f"{API}/winkelstraat/shops/{sid}/close",
                          json={"actor_user_id": ADMIN, "reden": "test"})
        assert r.status_code == 200
        assert r.json()["shop"]["status"] == "closing"


# --------- Spark Kasboek Reconcile ---------
class TestKasboekReconcile:
    def test_reconcile_in_balance(self):
        r = requests.get(f"{API}/spark/kasboek/reconcile")
        assert r.status_code == 200
        d = r.json()
        assert d["success"] is True
        # Spec: expected_in_eur=71.6, booked_in_eur=71.6, in_balance=true, no unbooked
        assert d["expected_in_eur"] == pytest.approx(71.6, abs=0.05), d
        assert d["booked_in_eur"] == pytest.approx(71.6, abs=0.05), d
        assert d["in_balance"] is True, d
        assert d["unbooked_transactions"] == [], d


# --------- Potjes 1-token-1-potje ---------
class TestPotjesSync:
    def test_admin_sync_all(self):
        r = requests.post(f"{API}/trade/potjes/sync-all-to-tokens",
                          params={"viewer_id": ADMIN})
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["success"] is True

    def test_non_admin_blocked(self):
        r = requests.post(f"{API}/trade/potjes/sync-all-to-tokens",
                          params={"viewer_id": MARIEKE})
        assert r.status_code == 403

    def test_gijs_has_potjes_matching_tokens(self):
        # Gijs has 2 ROAR tokens per spec. Verify via shop/token/balance and potjes count.
        roar = requests.get(f"{API}/shop/token/balance/{GIJS}").json()
        tokens = int(roar.get("roar_balance", roar.get("balance", 0)))
        p = requests.get(f"{API}/trade/potjes/{GIJS}").json()
        count = len(p.get("potjes", []))
        assert tokens == 2, f"Gijs spec=2 tokens, got {tokens}"
        assert count == tokens, f"Gijs tokens={tokens}, potjes={count}"

    def test_marieke_zero_tokens_zero_potjes(self):
        r = requests.get(f"{API}/trade/potjes/{MARIEKE}").json()
        # Marieke has 0 tokens -> 0 potjes
        assert len(r.get("potjes", [])) == 0

    def test_spark_keeps_10_base_potjes(self):
        r = requests.get(f"{API}/trade/potjes/user-000").json()
        # Spark base = 10
        assert len(r.get("potjes", [])) >= 10


# --------- Chat capability-routing ---------
INTENT_CASES = [
    ("wat is spark saldo", "spark_saldo_check"),
    ("wat staat morgen op mijn agenda", "agenda_vandaag"),
    ("hoeveel kaarten wachten op classificatie", "kennis_inbox_status"),
    ("welke bots draaien", "bots_status"),
    ("audit gezondheid", "audit_health"),
]


class TestChatCapabilityRouting:
    @pytest.mark.parametrize("text,expected_cap", INTENT_CASES)
    def test_intent_to_capability(self, text, expected_cap):
        body = {"user_id": ADMIN, "text": text, "message": text}
        r = requests.post(f"{API}/chat/message", json=body, timeout=30)
        assert r.status_code == 200, f"[{text}] {r.status_code}: {r.text[:300]}"
        d = r.json()
        # type can be in 'type' or nested
        resp_type = d.get("type") or (d.get("response") or {}).get("type")
        cap_id = d.get("capability_id") or (d.get("response") or {}).get("capability_id")
        assert resp_type == "capability_response", \
            f"[{text}] expected capability_response, got type={resp_type}, cap={cap_id}, body={str(d)[:300]}"
        assert cap_id == expected_cap, \
            f"[{text}] expected cap_id={expected_cap}, got {cap_id}"
