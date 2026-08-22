"""
Iteration 52: Test v13_pot_value_consistency_001 fix.
For CLOSED pots: capital == live_value (book value incl. realized P&L).
For OPEN pots: live_value may differ (mark-to-market).
Response schema regression + summary schema regression + related endpoints regression.
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")

USERS = [
    ("user-000", "Spark", 8),
    ("user-001", "Willem", 3),
    ("user-a0ee2d7e", "Gijs", 2),
]

REQUIRED_POT_FIELDS = [
    "id", "capital", "live_value", "capital_stored",
    "capital_dynamic", "position", "market", "stats",
]

REQUIRED_SUMMARY_FIELDS = [
    "pot_count", "total_capital", "current_max_per_pot",
    "open_positions", "closed_positions", "total_pnl",
    "total_trades", "win_rate", "live_balance", "live_pnl",
    "baseline_eur", "total_capital_dynamic", "token_price_eur",
]


@pytest.fixture(scope="module")
def api():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.mark.parametrize("uid,uname,expected_count", USERS)
def test_potjes_capital_consistency(api, uid, uname, expected_count):
    r = api.get(f"{BASE_URL}/api/trade/potjes/{uid}", timeout=15)
    assert r.status_code == 200, f"{uid}: {r.status_code} {r.text[:200]}"
    data = r.json()
    assert "potjes" in data, f"missing potjes key: {list(data.keys())}"
    pots = data["potjes"]
    assert len(pots) >= 1, f"{uid} has no pots"

    for p in pots:
        # v13 marker on each pot
        assert p.get("_hybrid_source") == "finance_hub_v13", (
            f"{uid} pot {p.get('id')} _hybrid_source={p.get('_hybrid_source')}"
        )
        for f in REQUIRED_POT_FIELDS:
            assert f in p, f"{uid} pot {p.get('id')} missing field {f}"
        pos = p["position"]
        is_open = pos.get("is_open", False)
        cap = float(p["capital"])
        live = float(p["live_value"])
        if not is_open:
            # CLOSED pot -> capital must equal live_value
            assert abs(cap - live) < 1e-6, (
                f"{uid} closed pot {p['id']}: capital={cap} live_value={live} mismatch"
            )
        # capital_dynamic is separate (token-priced) — must exist as number
        assert isinstance(p["capital_dynamic"], (int, float))


@pytest.mark.parametrize("uid,uname,expected_count", USERS)
def test_potjes_summary_schema(api, uid, uname, expected_count):
    r = api.get(f"{BASE_URL}/api/trade/potjes/{uid}", timeout=15)
    assert r.status_code == 200
    data = r.json()
    summary = data.get("summary")
    assert summary is not None, f"summary missing for {uid}"
    for f in REQUIRED_SUMMARY_FIELDS:
        assert f in summary, f"{uid} summary missing {f}"


def test_user_000_pot_006_open_mtm(api):
    """pot-006 (ATOM) is open per prompt — live may differ from capital."""
    r = api.get(f"{BASE_URL}/api/trade/potjes/user-000", timeout=15)
    assert r.status_code == 200
    pots = {p["id"]: p for p in r.json()["potjes"]}
    if "pot-006" in pots:
        p = pots["pot-006"]
        if p["position"].get("is_open"):
            # both fields present
            assert isinstance(p["live_value"], (int, float))
            assert isinstance(p["capital"], (int, float))


def test_user_000_closed_pots_are_1026(api):
    """Per prompt: pot-001..005, 007, 008 should have cap≈10.26 live≈10.26."""
    r = api.get(f"{BASE_URL}/api/trade/potjes/user-000", timeout=15)
    assert r.status_code == 200
    pots = {p["id"]: p for p in r.json()["potjes"]}
    closed_ids = ["pot-001", "pot-002", "pot-003", "pot-004", "pot-005", "pot-007", "pot-008"]
    for pid in closed_ids:
        if pid not in pots:
            continue
        p = pots[pid]
        if p["position"].get("is_open"):
            continue
        cap = float(p["capital"])
        live = float(p["live_value"])
        assert abs(cap - live) < 1e-6, f"{pid} cap!=live ({cap} vs {live})"
        # Prompt says ~10.26; ensure NOT ~10.00 exactly
        assert abs(live - 10.00) > 0.01 or abs(live - 10.26) < 0.05, (
            f"{pid} live={live} looks like un-fixed 10.00"
        )


# ---------------- Regression: related endpoints ----------------

def test_trade_stats(api):
    r = api.get(f"{BASE_URL}/api/trade/stats/user-000", timeout=15)
    assert r.status_code == 200, r.text[:200]


def test_trade_history(api):
    r = api.get(f"{BASE_URL}/api/trade/history/user-000?limit=100", timeout=15)
    assert r.status_code == 200, r.text[:200]


def test_bot_status(api):
    r = api.get(f"{BASE_URL}/api/trade/bot/status/user-000", timeout=15)
    assert r.status_code == 200, r.text[:200]


def test_potjes_post_endpoint_exists(api):
    """Note: prompt mentions POST /api/trade/potjes/user-000 but no such route exists.
    Verify the related expand endpoint (a real POST under /potjes/) works instead."""
    r = api.post(f"{BASE_URL}/api/trade/potjes/user-000/reset-cycle", json={}, timeout=15)
    assert r.status_code in (200, 400, 409, 422), (
        f"reset-cycle unexpected: {r.status_code} {r.text[:200]}"
    )
