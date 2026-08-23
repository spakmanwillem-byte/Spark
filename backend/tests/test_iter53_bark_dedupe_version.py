"""
Iteration 53 — Bark dedupe + version reshow tests (v13 bug-report Willem).

Tests bark endpoints:
  - GET  /api/deploy/pending/{user_id}
  - POST /api/deploy/seen (with content_version)
  - POST /api/deploy/reset-seen/{user_id}?viewer_id=admin
  - Backwards-compat: old seen entries stored as `bark_id` (no :version)
  - Version-reshow: bumping content_version brings bark back into /pending
  - Data-file: verify only privacy_v1 + welcome_v1 remain in version_anchor.json
"""
import json
import os
import shutil
from pathlib import Path

import pytest
import requests

def _load_backend_url():
    v = os.environ.get("REACT_APP_BACKEND_URL")
    if not v:
        env = Path("/app/frontend/.env").read_text(encoding="utf-8")
        for ln in env.splitlines():
            if ln.startswith("REACT_APP_BACKEND_URL="):
                v = ln.split("=", 1)[1].strip()
                break
    if not v:
        raise RuntimeError("REACT_APP_BACKEND_URL not found")
    return v.rstrip("/")

BASE_URL = _load_backend_url()
API = f"{BASE_URL}/api"

DATA_ROOT = Path("/app/backend/data")
ANCHOR_FILE = DATA_ROOT / "system" / "version_anchor.json"
USER_001 = "user-001"
USER_ANNE = "user-83270eb1"


@pytest.fixture
def anchor_backup():
    """Backup + restore /data/system/version_anchor.json around each test."""
    original = ANCHOR_FILE.read_text(encoding="utf-8")
    yield
    ANCHOR_FILE.write_text(original, encoding="utf-8")


@pytest.fixture
def seen_backup_user001():
    fp = DATA_ROOT / "users" / USER_001 / "seen_barks.json"
    orig = fp.read_text(encoding="utf-8") if fp.exists() else None
    yield fp
    if orig is None:
        if fp.exists():
            fp.unlink()
    else:
        fp.write_text(orig, encoding="utf-8")


def _reset(user_id: str, viewer_id: str = USER_001):
    r = requests.post(f"{API}/deploy/reset-seen/{user_id}", params={"viewer_id": viewer_id})
    assert r.status_code == 200, r.text


# -------------------- Data-file guard --------------------
class TestVersionAnchorFile:
    def test_only_system_barks_remain(self):
        data = json.loads(ANCHOR_FILE.read_text(encoding="utf-8"))
        ids = [b.get("id") for b in data.get("barks", [])]
        assert "privacy_v1" in ids
        assert "welcome_v1" in ids
        # Verwijderde game-barks
        for removed in ("v0.6.4", "aspect_madelief_stouten", "aspect_de_boekhouder"):
            assert removed not in ids, f"{removed} should be removed from anchor file"


# -------------------- Pending + seen basics --------------------
class TestPendingSeen:
    def test_pending_returns_content_version_field(self, seen_backup_user001):
        _reset(USER_001)
        r = requests.get(f"{API}/deploy/pending/{USER_001}")
        assert r.status_code == 200, r.text
        data = r.json()
        pending = data.get("pending", [])
        assert len(pending) >= 2, f"expected >=2 pending after reset, got {pending}"
        for b in pending:
            assert "content_version" in b
            assert isinstance(b["content_version"], str)
        # Both system barks visible after reset
        ids = [b["id"] for b in pending]
        assert "privacy_v1" in ids and "welcome_v1" in ids

    def test_mark_seen_removes_from_pending(self, seen_backup_user001):
        _reset(USER_001)
        # See privacy_v1
        r = requests.post(f"{API}/deploy/seen", json={
            "user_id": USER_001, "bark_id": "privacy_v1", "content_version": "1",
        })
        assert r.status_code == 200, r.text
        # Verify persistence
        seen_data = json.loads((DATA_ROOT / "users" / USER_001 / "seen_barks.json").read_text())
        assert "privacy_v1:1" in seen_data["seen"]
        # Verify pending no longer contains privacy_v1
        pending = requests.get(f"{API}/deploy/pending/{USER_001}").json().get("pending", [])
        ids = [b["id"] for b in pending]
        assert "privacy_v1" not in ids
        assert "welcome_v1" in ids  # still pending


# -------------------- Backwards compat --------------------
class TestBackwardsCompat:
    def test_old_format_seen_entry_still_hides_bark(self, seen_backup_user001):
        """If seen contains only 'privacy_v1' (no :version), bark must stay out of pending."""
        fp = DATA_ROOT / "users" / USER_001 / "seen_barks.json"
        fp.write_text(json.dumps({"seen": ["privacy_v1"], "last_check": None}))
        pending = requests.get(f"{API}/deploy/pending/{USER_001}").json().get("pending", [])
        ids = [b["id"] for b in pending]
        assert "privacy_v1" not in ids, "old-format seen must be honoured"


# -------------------- Version reshow --------------------
class TestVersionReshow:
    def test_bumping_content_version_resurfaces_bark(self, anchor_backup, seen_backup_user001):
        # 1) Reset + mark privacy_v1 seen at version 1
        _reset(USER_001)
        r = requests.post(f"{API}/deploy/seen", json={
            "user_id": USER_001, "bark_id": "privacy_v1", "content_version": "1",
        })
        assert r.status_code == 200
        pending = requests.get(f"{API}/deploy/pending/{USER_001}").json().get("pending", [])
        assert "privacy_v1" not in [b["id"] for b in pending]

        # 2) Bump content_version in anchor file to "2"
        data = json.loads(ANCHOR_FILE.read_text(encoding="utf-8"))
        for b in data["barks"]:
            if b["id"] == "privacy_v1":
                b["content_version"] = "2"
        ANCHOR_FILE.write_text(json.dumps(data), encoding="utf-8")

        # 3) Bark must reappear
        pending = requests.get(f"{API}/deploy/pending/{USER_001}").json().get("pending", [])
        by_id = {b["id"]: b for b in pending}
        assert "privacy_v1" in by_id, f"privacy_v1 should re-appear after version bump; got {list(by_id)}"
        assert by_id["privacy_v1"]["content_version"] == "2"

        # 4) Mark it seen at v2 — no longer pending
        requests.post(f"{API}/deploy/seen", json={
            "user_id": USER_001, "bark_id": "privacy_v1", "content_version": "2",
        })
        pending = requests.get(f"{API}/deploy/pending/{USER_001}").json().get("pending", [])
        assert "privacy_v1" not in [b["id"] for b in pending]


# -------------------- Anne (non-admin) --------------------
class TestUserAnne:
    def test_pending_for_anne(self):
        r = requests.get(f"{API}/deploy/pending/{USER_ANNE}")
        assert r.status_code == 200
        pending = r.json().get("pending", [])
        # All returned barks must have content_version + not be admin-only
        for b in pending:
            assert "content_version" in b
            assert (b.get("audience") or "all") != "admins"
