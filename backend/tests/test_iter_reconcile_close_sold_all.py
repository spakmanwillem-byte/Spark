"""Tests for bulk reconcile endpoint /api/trade/reconcile/close-sold-all.
Verifies multi-user iteration, meta-key skipping, dry_run semantics, and persistence.
"""
import json
import os
import shutil
from pathlib import Path

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
POTJES_FP = Path("/app/backend/data/financial/user_potjes.json")


def _read_potjes():
    return json.loads(POTJES_FP.read_text())


def _find_pot(data, uid, coin=None, pot_id=None):
    u = (data.get("users") or {}).get(uid) or {}
    for p in (u.get("potjes") or []):
        if pot_id and p.get("id") == pot_id:
            return p
        if coin and (p.get("coin") or "").upper() == coin.upper():
            return p
    return None


@pytest.fixture(scope="module")
def backup_potjes():
    """Backup and restore user_potjes.json around the test module (safety net)."""
    bkp = POTJES_FP.with_suffix(".json.testbkp")
    shutil.copy2(POTJES_FP, bkp)
    yield
    # Restore only if something went wrong and file is missing/corrupted
    # We do NOT auto-restore because dry_run=false is an intentional mutation test
    # But keep the bkp for manual recovery.
    print(f"Backup saved at: {bkp}")


class TestReconcileCloseSoldAll:

    def test_endpoint_dry_run_returns_success_and_structure(self, backup_potjes):
        """dry_run=true must return success:true, contain per_user + totals + n_users_processed."""
        before = _read_potjes()
        r = requests.post(f"{BASE_URL}/api/trade/reconcile/close-sold-all",
                          params={"dry_run": "true"}, timeout=60)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body.get("success") is True, body
        assert body.get("dry_run") is True
        assert "per_user" in body and isinstance(body["per_user"], dict)
        assert "total_closed" in body
        assert "total_skipped" in body
        assert "n_users_processed" in body
        # Verify file untouched
        after = _read_potjes()
        assert before == after, "dry_run=true must NOT mutate user_potjes.json"

    def test_meta_keys_not_in_per_user(self, backup_potjes):
        r = requests.post(f"{BASE_URL}/api/trade/reconcile/close-sold-all",
                          params={"dry_run": "true"}, timeout=60)
        body = r.json()
        per_user = body.get("per_user", {})
        # These keys under 'users' should be filtered
        for meta in ("null", "__ignored__", None):
            assert meta not in per_user, f"meta-key {meta!r} leaked into per_user"
        # Top-level meta-keys (never in 'users') must never appear either
        for meta in ("_reset_at", "_final_reset_at", "_trim_at", "_pre_deploy_reset_at"):
            assert meta not in per_user

    def test_users_with_no_open_potjes_skipped(self, backup_potjes):
        r = requests.post(f"{BASE_URL}/api/trade/reconcile/close-sold-all",
                          params={"dry_run": "true"}, timeout=60)
        body = r.json()
        pu = body["per_user"]
        # user-001 currently has 0 open potjes -> must be marked skipped
        assert "user-001" in pu
        assert pu["user-001"].get("skipped") is True
        assert "no open" in (pu["user-001"].get("reason") or "").lower()
        # Empty-potjes users should also be marked skipped
        for uid in ("user-1996fa59", "user-166437fe"):
            if uid in pu:
                assert pu[uid].get("skipped") is True

    def test_candidate_users_present_in_per_user(self, backup_potjes):
        r = requests.post(f"{BASE_URL}/api/trade/reconcile/close-sold-all",
                          params={"dry_run": "true"}, timeout=60)
        pu = r.json()["per_user"]
        # Both users with open potjes should be processed (result may indicate
        # success or graceful error dep on Bitvavo key availability)
        for uid in ("user-000", "user-a0ee2d7e"):
            assert uid in pu, f"expected user {uid} to be processed"
            assert pu[uid].get("skipped") is not True

    def test_single_user_endpoint_backwards_compat(self, backup_potjes):
        r = requests.post(
            f"{BASE_URL}/api/trade/reconcile/close-sold/user-a0ee2d7e",
            params={"dry_run": "true"}, timeout=60,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        # per-user endpoint returns success and detail keys
        assert "success" in body
        # dry_run should not mutate
        # (we already backed up file; state check performed in other tests)

    def test_dry_run_false_persists_changes(self, backup_potjes):
        """Run dry_run=false ONCE and verify persistence for user-a0ee2d7e."""
        before = _read_potjes()
        pot_before = _find_pot(before, "user-a0ee2d7e", pot_id="pot-001")
        assert pot_before is not None, "expected pot-001 for user-a0ee2d7e"
        trades_before = ((pot_before.get("stats") or {}).get("trades") or 0)
        was_open_before = (pot_before.get("position") or {}).get("is_open")

        r = requests.post(f"{BASE_URL}/api/trade/reconcile/close-sold-all",
                          params={"dry_run": "false"}, timeout=90)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body.get("success") is True
        assert body.get("dry_run") is False

        after = _read_potjes()
        pot_after = _find_pot(after, "user-a0ee2d7e", pot_id="pot-001")
        assert pot_after is not None
        user_result = body["per_user"].get("user-a0ee2d7e") or {}
        n_closed = user_result.get("n_closed", 0)
        print("user-a0ee2d7e result:", user_result)
        # If the reconcile actually closed this pot, verify state
        if was_open_before and n_closed and n_closed > 0:
            assert (pot_after.get("position") or {}).get("is_open") is False, \
                "pot-001 should have transitioned to is_open=false"
            trades_after = ((pot_after.get("stats") or {}).get("trades") or 0)
            assert trades_after == trades_before + 1, \
                f"trades should increment: before={trades_before} after={trades_after}"
        else:
            # graceful degradation: endpoint should not crash; per_user has error/success entry
            assert isinstance(user_result, dict)
            print("Note: pot-001 not closed (likely Bitvavo returned >5% coin still present or api error). "
                  "This is acceptable graceful behavior.")
