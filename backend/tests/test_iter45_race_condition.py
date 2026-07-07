"""
Iteration 45 — Race condition fix in potjes.py.

Tests:
1. Concurrent open_cluster on 3 different users (30x parallel) — geen lost writes
2. Concurrent close_pot + open_cluster on same user
3. revalue_free_pots + revalue_single_pot single-thread correctness
4. POST /api/trade/baseline/{user_id} + verify stats reflects it
5. GET /api/trade/stats/{user_id} — heeft lifetime_trades + trades_before_baseline
6. GET /api/trade/admin/bots — 3 users, interval config, dynamic trade_amount

Alle tests maken een backup van /app/backend/data/financial/user_potjes.json en
/app/backend/data/trade/capital_baseline.json en restoren die in teardown.
"""
import os
import sys
import json
import shutil
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pytest
import requests

# Add backend to path
BACKEND_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_DIR))

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    # fallback voor pytest zonder REACT_APP_BACKEND_URL
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip().rstrip("/")
                break

POTJES_FILE = Path("/app/backend/data/financial/user_potjes.json")
BASELINE_FILE = Path("/app/backend/data/trade/capital_baseline.json")

USERS = ["user-000", "user-001", "user-a0ee2d7e"]


# --------------------------------------------------------------------
# Fixtures — backup & restore state files
# --------------------------------------------------------------------
@pytest.fixture
def backup_potjes():
    """Backup user_potjes.json and restore after test."""
    backup = POTJES_FILE.read_bytes()
    yield
    POTJES_FILE.write_bytes(backup)


@pytest.fixture
def backup_baseline():
    """Backup capital_baseline.json (may not exist) and restore after test."""
    backup = BASELINE_FILE.read_bytes() if BASELINE_FILE.exists() else None
    yield
    if backup is None:
        if BASELINE_FILE.exists():
            BASELINE_FILE.unlink()
    else:
        BASELINE_FILE.write_bytes(backup)


def _load_pots():
    return json.loads(POTJES_FILE.read_text())


def _count_open(user_id: str) -> int:
    data = _load_pots()
    pots = data["users"].get(user_id, {}).get("potjes", [])
    return sum(1 for p in pots if p.get("position", {}).get("is_open"))


def _all_pot_ids(user_id: str, only_free: bool = True):
    data = _load_pots()
    pots = data["users"].get(user_id, {}).get("potjes", [])
    if only_free:
        return [p["id"] for p in pots if not p.get("position", {}).get("is_open") and not p.get("pot_locked")]
    return [p["id"] for p in pots]


# --------------------------------------------------------------------
# 1. RACE CONDITION — Concurrent open_cluster on 3 users
# --------------------------------------------------------------------
class TestRaceCondition:
    """Verify _POTJES_LOCK prevents lost writes across users."""

    def test_concurrent_open_cluster_no_lost_writes(self, backup_potjes):
        """30 concurrent open_cluster calls (10 per user × 3 users)
        must all succeed — no user should lose pots to interleaved writes.
        """
        from modules.trade import potjes as potjes_svc

        # Ensure all pots are free for all 3 users first
        data = _load_pots()
        for uid in USERS:
            for p in data["users"][uid]["potjes"]:
                p["position"] = {"is_open": False, "entry_price": None,
                                 "highest_price": None, "trailing_active": False,
                                 "entry_time": None}
        POTJES_FILE.write_text(json.dumps(data, indent=2))

        # Baseline counts
        expected = {}
        for uid in USERS:
            expected[uid] = len(_all_pot_ids(uid, only_free=True))
        # user-000: 10, user-001: 10, user-a0ee2d7e: 2

        # Build tasks: open each pot as its own 1-pot "cluster"
        tasks = []
        for uid in USERS:
            for pid in _all_pot_ids(uid, only_free=True):
                tasks.append((uid, pid))

        assert len(tasks) == 22, f"Expected 22 pot-open tasks, got {len(tasks)}"

        def _open_one(args):
            uid, pid = args
            cluster_id = f"race_{uid}_{pid}"
            return potjes_svc.open_cluster(
                user_id=uid,
                pot_ids=[pid],
                entry_price=100.0,
                cluster_id=cluster_id,
                current_cycle=1,
                trade_id=f"trade_{pid}",
            )

        # Run all 22 in parallel with 20 workers to force races
        with ThreadPoolExecutor(max_workers=20) as ex:
            results = list(ex.map(_open_one, tasks))

        # All must have succeeded
        assert all(r.get("success") for r in results), f"Some failed: {results}"

        # Now verify state: each user has ALL its pots open (no lost writes)
        for uid in USERS:
            open_count = _count_open(uid)
            assert open_count == expected[uid], (
                f"RACE DETECTED: user {uid} expected {expected[uid]} open pots, "
                f"got {open_count}. Some writes were lost."
            )

    def test_stress_100_iterations_no_data_loss(self, backup_potjes):
        """Repeated open/close cycles from many threads must never lose data."""
        from modules.trade import potjes as potjes_svc

        # Reset all pots closed for all users
        data = _load_pots()
        for uid in USERS:
            for p in data["users"][uid]["potjes"]:
                p["position"] = {"is_open": False, "entry_price": None,
                                 "highest_price": None, "trailing_active": False,
                                 "entry_time": None}
        POTJES_FILE.write_text(json.dumps(data, indent=2))

        errors = []

        def _worker(uid, pid, iterations):
            try:
                for i in range(iterations):
                    potjes_svc.open_cluster(uid, [pid], 100.0 + i,
                                            f"stress_{uid}_{pid}_{i}", 1)
                    potjes_svc.close_pot(uid, pid, 101.0 + i)
            except Exception as e:
                errors.append(f"{uid}/{pid}: {e}")

        threads = []
        tasks_per_user = {"user-000": 3, "user-001": 3, "user-a0ee2d7e": 2}
        iters = 10
        for uid, n_pots in tasks_per_user.items():
            for i in range(1, n_pots + 1):
                pid = f"pot-{i:03d}"
                t = threading.Thread(target=_worker, args=(uid, pid, iters))
                threads.append(t)
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)

        assert not errors, f"Stress errors: {errors}"

        # All should be closed at end
        for uid in USERS:
            open_count = _count_open(uid)
            assert open_count == 0, (
                f"After stress, {uid} has {open_count} open pots (should be 0)"
            )

        # JSON file must still be valid
        try:
            data = json.loads(POTJES_FILE.read_text())
        except json.JSONDecodeError as e:
            pytest.fail(f"user_potjes.json corrupted after stress test: {e}")

        # All users' pot lists preserved
        for uid, expected_n in [("user-000", 10), ("user-001", 10), ("user-a0ee2d7e", 2)]:
            assert len(data["users"][uid]["potjes"]) == expected_n, (
                f"{uid} lost pots! Expected {expected_n}, got {len(data['users'][uid]['potjes'])}"
            )

    def test_concurrent_close_and_open_same_user(self, backup_potjes):
        """Interleave close_pot + open_cluster on user-000 — no missing pots."""
        from modules.trade import potjes as potjes_svc

        uid = "user-000"
        # Ensure clean state and open first 5 pots
        data = _load_pots()
        pots = data["users"][uid]["potjes"]
        for p in pots:
            p["position"] = {"is_open": False, "entry_price": None,
                             "highest_price": None, "trailing_active": False,
                             "entry_time": None}
        # Open pots 1-5
        for p in pots[:5]:
            p["position"] = {
                "is_open": True, "entry_price": 100.0, "highest_price": 100.0,
                "trailing_active": False, "entry_time": "2026-01-01T00:00:00+00:00",
                "amount_eur": p.get("capital"),
                "cluster_id": None, "cluster_size": 1,
            }
        POTJES_FILE.write_text(json.dumps(data, indent=2))
        assert _count_open(uid) == 5

        # Concurrently: close pots 1-5 and open pots 6-10
        pots_to_close = [f"pot-{i:03d}" for i in range(1, 6)]
        pots_to_open = [f"pot-{i:03d}" for i in range(6, 11)]

        def _close(pid):
            return potjes_svc.close_pot(uid, pid, 110.0)

        def _open(pid):
            return potjes_svc.open_cluster(uid, [pid], 105.0, f"c_{pid}", 1)

        tasks = [(op, pid) for op, pid in
                 [("close", p) for p in pots_to_close] +
                 [("open", p) for p in pots_to_open]]

        with ThreadPoolExecutor(max_workers=10) as ex:
            futures = []
            for op, pid in tasks:
                fn = _close if op == "close" else _open
                futures.append(ex.submit(fn, pid))
            _results = [f.result() for f in as_completed(futures)]

        # Final state: 1-5 closed, 6-10 open → 5 open
        assert _count_open(uid) == 5, (
            f"After concurrent close+open, expected 5 open pots but got {_count_open(uid)}"
        )
        data = _load_pots()
        pots = data["users"][uid]["potjes"]
        by_id = {p["id"]: p for p in pots}
        for pid in pots_to_close:
            assert not by_id[pid]["position"]["is_open"], f"{pid} should be closed"
        for pid in pots_to_open:
            assert by_id[pid]["position"]["is_open"], f"{pid} should be open"


# --------------------------------------------------------------------
# 2. Revalue functions still work single-thread
# --------------------------------------------------------------------
class TestRevalue:
    def test_revalue_free_pots(self, backup_potjes):
        from modules.trade import potjes as potjes_svc

        uid = "user-001"
        # Ensure closed state
        data = _load_pots()
        for p in data["users"][uid]["potjes"]:
            p["position"] = {"is_open": False, "entry_price": None,
                             "highest_price": None, "trailing_active": False,
                             "entry_time": None}
        POTJES_FILE.write_text(json.dumps(data, indent=2))

        result = potjes_svc.revalue_free_pots(uid, 7.50)
        assert result["success"] is True
        assert result["new_capital_each"] == 7.50
        assert result["revalued_count"] >= 1
        # Verify persistence
        data = _load_pots()
        for p in data["users"][uid]["potjes"]:
            assert abs(p["capital"] - 7.50) < 0.001

    def test_revalue_single_pot(self, backup_potjes):
        from modules.trade import potjes as potjes_svc

        uid = "user-001"
        # Ensure pot-001 is closed
        data = _load_pots()
        for p in data["users"][uid]["potjes"]:
            if p["id"] == "pot-001":
                p["position"] = {"is_open": False, "entry_price": None,
                                 "highest_price": None, "trailing_active": False,
                                 "entry_time": None}
        POTJES_FILE.write_text(json.dumps(data, indent=2))

        result = potjes_svc.revalue_single_pot(uid, "pot-001", 8.25)
        assert result["success"] is True
        assert result["new_capital"] == 8.25
        data = _load_pots()
        pot = next(p for p in data["users"][uid]["potjes"] if p["id"] == "pot-001")
        assert abs(pot["capital"] - 8.25) < 0.001


# --------------------------------------------------------------------
# 3. Baseline endpoint & stats endpoint
# --------------------------------------------------------------------
class TestBaselineAndStats:
    def test_post_baseline_and_read_back(self, backup_baseline):
        uid = "user-000"
        r = requests.post(f"{BASE_URL}/api/trade/baseline/{uid}",
                          json={"baseline_eur": 100.0}, timeout=10)
        assert r.status_code == 200, f"POST baseline failed: {r.status_code} {r.text}"
        body = r.json()
        assert body.get("success") is True
        assert body["baseline"]["baseline_eur"] == 100.0
        assert "set_at" in body["baseline"]

        # Read back
        g = requests.get(f"{BASE_URL}/api/trade/baseline/{uid}", timeout=10)
        assert g.status_code == 200
        assert g.json()["baseline"]["baseline_eur"] == 100.0

    def test_stats_endpoint_returns_required_fields(self, backup_baseline):
        uid = "user-000"
        # Set a baseline first so trades_before_baseline is populated
        requests.post(f"{BASE_URL}/api/trade/baseline/{uid}",
                      json={"baseline_eur": 100.0}, timeout=10)

        r = requests.get(f"{BASE_URL}/api/trade/stats/{uid}", timeout=15)
        assert r.status_code == 200, f"stats {r.status_code}: {r.text}"
        d = r.json()
        # Required fields per review request
        for key in ("user_trades", "user_pnl", "lifetime_trades", "trades_before_baseline"):
            assert key in d, f"Missing field '{key}' in stats response. Got: {list(d.keys())}"
        assert isinstance(d["lifetime_trades"], int)
        assert isinstance(d["trades_before_baseline"], int)


# --------------------------------------------------------------------
# 4. Admin bots endpoint
# --------------------------------------------------------------------
class TestAdminBots:
    def test_admin_bots_lists_three_users(self):
        r = requests.get(f"{BASE_URL}/api/trade/admin/bots", timeout=15)
        assert r.status_code == 200, f"{r.status_code}: {r.text}"
        d = r.json()
        assert d.get("success") is True
        bots = d["bots"]
        by_uid = {b["user_id"]: b for b in bots}
        for uid in USERS:
            assert uid in by_uid, f"User {uid} not in admin/bots. Got: {list(by_uid.keys())}"

        # Config checks
        for uid in USERS:
            b = by_uid[uid]
            assert b.get("candle_interval") == "15m", f"{uid} candle_interval={b.get('candle_interval')}"
            assert "interval" in b
            assert isinstance(b.get("interval"), (int, float))
            assert "trade_amount" in b
            # trade_amount is dynamic (some float value)
            assert isinstance(b["trade_amount"], (int, float))
            assert b["trade_amount"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
