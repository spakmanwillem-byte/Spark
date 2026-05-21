"""Tests for Avatar Gallery edit + Spark (user-000) avatar handling.

Covers tests 1-9 of iteration 15:
- PATCH /api/avatar/gallery/{avatar_id} (admin can edit title/bot_owner)
- non-admin gets 403
- claim via bot_owner=user-000 (Spark) propagates to GET /gallery and avatar/select guard
- user-000 fallback URL
- /api/auth/users includes Spark
"""
import os
import pytest
import requests

BASE_URL = (os.environ.get("REACT_APP_BACKEND_URL") or "https://question-hub-160.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN_ID = "user-001"
NON_ADMIN_ID = "user-c609d7d1"
SPARK_ID = "user-000"
TARGET_AVATAR = "0ef0b726773e"  # "De Trader" per request


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module", autouse=True)
def restore_state(session):
    """Snapshot the target avatar entry + Spark's avatar ref, restore after module."""
    # Snapshot gallery entry
    r = session.get(f"{API}/avatar/gallery")
    avatars = r.json().get("avatars", [])
    original = next((a for a in avatars if a.get("id") == TARGET_AVATAR), None)
    # Snapshot Spark current
    cur = session.get(f"{API}/avatar/current/{SPARK_ID}").json()
    spark_ref = cur.get("avatar_ref")

    yield

    # Restore avatar entry to title='De Trader' bot_owner=''
    payload = {"viewer_id": ADMIN_ID, "title": "De Trader", "bot_owner": ""}
    if original is not None and original.get("tags") is not None:
        payload["tags"] = original.get("tags", [])
    session.patch(f"{API}/avatar/gallery/{TARGET_AVATAR}", json=payload)

    # Restore Spark avatar ref
    session.put(f"{API}/avatar/select/{SPARK_ID}", json={"avatar_ref": spark_ref})


# Test 1
def test_patch_title_as_admin(session):
    r = session.patch(
        f"{API}/avatar/gallery/{TARGET_AVATAR}",
        json={"viewer_id": ADMIN_ID, "title": "De Joker"},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("success") is True
    assert data["avatar"]["title"] == "De Joker"

    # Verify via GET
    g = session.get(f"{API}/avatar/gallery").json()
    entry = next((a for a in g["avatars"] if a["id"] == TARGET_AVATAR), None)
    assert entry is not None
    assert entry["title"] == "De Joker"


# Test 2
def test_patch_bot_owner_user000(session):
    r = session.patch(
        f"{API}/avatar/gallery/{TARGET_AVATAR}",
        json={"viewer_id": ADMIN_ID, "bot_owner": "user-000"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["avatar"]["bot_owner"] == "user-000"


# Test 5 (depends on test 2 having claimed)
def test_gallery_shows_locked_owner_user000(session):
    g = session.get(f"{API}/avatar/gallery").json()
    entry = next((a for a in g["avatars"] if a["id"] == TARGET_AVATAR), None)
    assert entry is not None
    assert entry.get("locked") is True
    assert entry.get("bot_owner") == "user-000"


# Test 6 (depends on test 2)
def test_non_admin_cannot_select_claimed_avatar(session):
    r = session.put(
        f"{API}/avatar/select/{NON_ADMIN_ID}",
        json={"avatar_ref": f"gallery:{TARGET_AVATAR}"},
    )
    assert r.status_code == 403
    assert "user-000" in r.text


# Test 7
def test_spark_can_use_own_claimed_avatar(session):
    r = session.put(
        f"{API}/avatar/select/{SPARK_ID}",
        json={"avatar_ref": f"gallery:{TARGET_AVATAR}"},
    )
    assert r.status_code == 200, r.text
    # Reset Spark to None right after so test 8 passes
    session.put(f"{API}/avatar/select/{SPARK_ID}", json={"avatar_ref": None})


# Test 3
def test_patch_clear_bot_owner(session):
    r = session.patch(
        f"{API}/avatar/gallery/{TARGET_AVATAR}",
        json={"viewer_id": ADMIN_ID, "bot_owner": ""},
    )
    assert r.status_code == 200, r.text
    assert "bot_owner" not in r.json()["avatar"] or not r.json()["avatar"].get("bot_owner")

    g = session.get(f"{API}/avatar/gallery").json()
    entry = next((a for a in g["avatars"] if a["id"] == TARGET_AVATAR), None)
    # After clear, "De Joker" title -> no title-based bot match, so no owner
    assert entry.get("locked") is not True or not entry.get("bot_owner")


# Test 4
def test_patch_as_non_admin_forbidden(session):
    r = session.patch(
        f"{API}/avatar/gallery/{TARGET_AVATAR}",
        json={"viewer_id": NON_ADMIN_ID, "title": "Hack"},
    )
    assert r.status_code == 403


# Test 8
def test_spark_current_avatar_fallback(session):
    # Ensure Spark has no avatar set
    session.put(f"{API}/avatar/select/{SPARK_ID}", json={"avatar_ref": None})
    r = session.get(f"{API}/avatar/current/{SPARK_ID}")
    assert r.status_code == 200
    data = r.json()
    assert data["is_fallback"] is True
    assert data.get("fallback_url") is not None
    assert "roadkill-logo" in data["fallback_url"]


# Test 9
def test_auth_users_includes_spark(session):
    r = session.get(f"{API}/auth/users")
    assert r.status_code == 200
    users = r.json().get("users", [])
    spark = next((u for u in users if u.get("id") == SPARK_ID), None)
    assert spark is not None, "user-000 (Spark) not in /api/auth/users"
    assert spark.get("naam") == "Spark"
    assert spark.get("gradatie") == 1
