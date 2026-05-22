"""
Spark Core 2.0 - Update Bark / Deploy Anchor + Avatar Gallery 2-tab + D&D help intent
Iteration 19 backend regression tests
"""
import os
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://question-hub-160.preview.emergentagent.com").rstrip("/")
ADMIN_ID = "user-001"
NON_ADMIN_ID = "user-c609d7d1"
TEST_VERSION = "v0.6.5-test"


@pytest.fixture(scope="module", autouse=True)
def cleanup_test_anchor():
    # pre-clean
    requests.delete(f"{BASE_URL}/api/deploy/anchor/{TEST_VERSION}", params={"viewer_id": ADMIN_ID})
    yield
    # post-clean
    requests.delete(f"{BASE_URL}/api/deploy/anchor/{TEST_VERSION}", params={"viewer_id": ADMIN_ID})
    requests.delete(f"{BASE_URL}/api/deploy/anchor/v0.6.6-fronttest", params={"viewer_id": ADMIN_ID})


# ============== DEPLOY ANCHOR TESTS ==============

class TestDeployAnchors:

    def test_01_list_anchors_has_privacy_and_064(self):
        r = requests.get(f"{BASE_URL}/api/deploy/anchors")
        assert r.status_code == 200
        data = r.json()
        assert "barks" in data
        ids = [b["id"] for b in data["barks"]]
        assert "privacy_v1" in ids, f"privacy_v1 missing from {ids}"
        # find privacy
        p = next(b for b in data["barks"] if b["id"] == "privacy_v1")
        assert p["kind"] == "privacy"
        assert p["audience"] == "all"
        # v0.6.4 may or may not exist; warn but don't fail
        if "v0.6.4" not in ids:
            pytest.skip(f"v0.6.4 anchor not seeded; got {ids}")

    def test_02_pending_marieke_includes_privacy_first(self):
        # Reset marieke seen to guarantee fresh state
        requests.post(f"{BASE_URL}/api/deploy/reset-seen/{NON_ADMIN_ID}", params={"viewer_id": ADMIN_ID})
        r = requests.get(f"{BASE_URL}/api/deploy/pending/{NON_ADMIN_ID}")
        assert r.status_code == 200
        data = r.json()
        assert data["count"] >= 1
        assert data["pending"][0]["id"] == "privacy_v1"

    def test_03_create_anchor_admin(self):
        body = {
            "version": TEST_VERSION,
            "title": "Test anchor",
            "message": "Pytest test anchor",
            "viewer_id": ADMIN_ID,
        }
        r = requests.post(f"{BASE_URL}/api/deploy/anchor", json=body)
        assert r.status_code == 200, r.text
        assert r.json()["success"] is True
        assert r.json()["bark"]["id"] == TEST_VERSION

    def test_04_create_anchor_non_admin_forbidden(self):
        body = {"version": "v-should-fail", "viewer_id": NON_ADMIN_ID}
        r = requests.post(f"{BASE_URL}/api/deploy/anchor", json=body)
        assert r.status_code == 403, r.text

    def test_05_create_duplicate_returns_400(self):
        body = {"version": TEST_VERSION, "viewer_id": ADMIN_ID}
        r = requests.post(f"{BASE_URL}/api/deploy/anchor", json=body)
        assert r.status_code == 400, r.text

    def test_06_delete_test_anchor(self):
        r = requests.delete(f"{BASE_URL}/api/deploy/anchor/{TEST_VERSION}", params={"viewer_id": ADMIN_ID})
        assert r.status_code == 200, r.text
        assert r.json()["removed"] >= 1

    def test_07_delete_privacy_forbidden(self):
        r = requests.delete(f"{BASE_URL}/api/deploy/anchor/privacy_v1", params={"viewer_id": ADMIN_ID})
        assert r.status_code == 400, r.text

    def test_08_mark_seen_and_pending_excludes(self):
        # Reset first
        requests.post(f"{BASE_URL}/api/deploy/reset-seen/{NON_ADMIN_ID}", params={"viewer_id": ADMIN_ID})
        pre = requests.get(f"{BASE_URL}/api/deploy/pending/{NON_ADMIN_ID}").json()
        assert pre["count"] >= 1
        # mark privacy_v1 seen
        r = requests.post(f"{BASE_URL}/api/deploy/seen", json={"user_id": NON_ADMIN_ID, "bark_id": "privacy_v1"})
        assert r.status_code == 200
        post = requests.get(f"{BASE_URL}/api/deploy/pending/{NON_ADMIN_ID}").json()
        ids_post = [b["id"] for b in post["pending"]]
        assert "privacy_v1" not in ids_post

    def test_09_reset_seen_admin(self):
        r = requests.post(f"{BASE_URL}/api/deploy/reset-seen/{ADMIN_ID}", params={"viewer_id": ADMIN_ID})
        assert r.status_code == 200
        # pending should include privacy_v1 again
        p = requests.get(f"{BASE_URL}/api/deploy/pending/{ADMIN_ID}").json()
        ids = [b["id"] for b in p["pending"]]
        assert "privacy_v1" in ids


# ============== AVATAR GALLERY 2-TAB ==============

class TestAvatarGallery:

    def test_10_gallery_user_category(self):
        r = requests.get(f"{BASE_URL}/api/avatar/gallery", params={"category": "user"})
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True
        for a in data["avatars"]:
            assert a.get("category") == "user"

    def test_11_gallery_dnd_category(self):
        r = requests.get(f"{BASE_URL}/api/avatar/gallery", params={"category": "dnd"})
        assert r.status_code == 200
        data = r.json()
        for a in data["avatars"]:
            assert a.get("category") == "dnd"

    def test_12_patch_category_to_dnd(self):
        # Pick any non-locked user avatar
        all_avatars = requests.get(f"{BASE_URL}/api/avatar/gallery", params={"category": "user"}).json()["avatars"]
        if not all_avatars:
            pytest.skip("No 'user' category avatars to patch")
        target = all_avatars[0]
        avatar_id = target["id"]
        original_cat = target.get("category", "user")
        # Patch to dnd
        r = requests.patch(
            f"{BASE_URL}/api/avatar/gallery/{avatar_id}",
            json={"viewer_id": ADMIN_ID, "category": "dnd"},
        )
        assert r.status_code == 200, r.text
        assert r.json()["avatar"]["category"] == "dnd"
        # Restore
        requests.patch(
            f"{BASE_URL}/api/avatar/gallery/{avatar_id}",
            json={"viewer_id": ADMIN_ID, "category": original_cat},
        )


# ============== D&D CHAT INTENT ==============

class TestDnDHelpIntent:

    @pytest.mark.parametrize("msg", [
        "D&D help",
        "wat is d&d",
        "hoe werkt d&d",
        "spark world help",
    ])
    def test_13_dnd_help_intent_triggers(self, msg):
        payload = {"message": msg, "user_id": ADMIN_ID}
        r = requests.post(f"{BASE_URL}/api/chat/message", json=payload, timeout=30)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("type") == "dnd_help", f"Got type={data.get('type')} for msg={msg!r}: {data.get('message','')[:200]}"
        assert "🎲" in data.get("message", "")
        assert "Spark World" in data.get("message", "")
