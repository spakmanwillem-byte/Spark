"""
v4_user_avatar_helper_001 — Backend tests for contacts /list avatar_ref field.

Tests:
  10. GET /api/contacts/list?user_id=user-001 includes avatar_ref per contact;
      admin-collectief has avatar_ref='emoji:🛡️'.
  11. For non-admin viewer (user-c609d7d1), admin contacts are anonymized AND
      avatar_ref is null (no leak).
"""
import os
import pytest
import requests

_RAW_URL = os.environ.get("REACT_APP_BACKEND_URL")
if not _RAW_URL:
    # Read from frontend/.env as fallback (test env doesn't auto-load it)
    try:
        with open("/app/frontend/.env") as _f:
            for _ln in _f:
                if _ln.startswith("REACT_APP_BACKEND_URL="):
                    _RAW_URL = _ln.split("=", 1)[1].strip()
                    break
    except Exception:
        pass
assert _RAW_URL, "REACT_APP_BACKEND_URL not set"
BASE_URL = _RAW_URL.rstrip("/")
API = f"{BASE_URL}/api"


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# ------------------- Test 10 -------------------
def test_contacts_list_has_avatar_ref_admin_viewer(session):
    """Admin viewer (Willem) sees all contacts including avatar_ref field."""
    r = session.get(f"{API}/contacts/list", params={"user_id": "user-001"})
    assert r.status_code == 200, r.text
    body = r.json()
    contacts = body.get("contacts", [])
    assert len(contacts) > 0, "Expected at least one contact"

    # Every contact must have the avatar_ref key (value may be None)
    for c in contacts:
        assert "avatar_ref" in c, f"Contact {c.get('id')} missing avatar_ref"

    # admin-collectief must be present with emoji shield avatar_ref
    ac = next((c for c in contacts if c["id"] == "admin-collectief"), None)
    assert ac is not None, "Admin Collectief virtual contact missing"
    assert ac["avatar_ref"] == "emoji:🛡️", f"Got: {ac['avatar_ref']!r}"

    # Bots should have avatar_ref pointing at gallery (or at least non-null)
    bots = [c for c in contacts if c.get("is_bot")]
    assert len(bots) >= 3, "Expected ≥3 bot contacts for admin viewer"
    bot_with_gallery = [b for b in bots if isinstance(b.get("avatar_ref"), str) and b["avatar_ref"].startswith("gallery:")]
    assert len(bot_with_gallery) >= 3, (
        f"Expected ≥3 bots with gallery:* avatar_ref. Got: "
        f"{[(b['naam'], b['avatar_ref']) for b in bots]}"
    )


# ------------------- Test 11 -------------------
def test_contacts_list_anonymizes_admin_for_non_admin_viewer(session):
    """Non-admin viewer (gradatie ≥ 4) — admin contacts grouped & avatar_ref=null.

    Creates a temp user with gradatie 5, verifies behaviour, then deletes.
    Marieke (user-c609d7d1) is gradatie 3 which is admin-tier in contacts module,
    so we need a true non-admin to exercise the anonymization branch.
    """
    # Create temp user via auth API
    create_resp = session.post(
        f"{API}/auth/users",
        json={"naam": "TEST_NonAdmin", "sleutelwoord": "TestPass01", "gradatie": 5},
    )
    if create_resp.status_code not in (200, 201):
        pytest.skip(f"Could not create temp non-admin user: {create_resp.status_code} {create_resp.text}")
    temp_user = create_resp.json()
    temp_id = temp_user.get("id") or temp_user.get("user", {}).get("id")
    assert temp_id, f"No id in create resp: {temp_user}"

    try:
        r = session.get(f"{API}/contacts/list", params={"user_id": temp_id})
        assert r.status_code == 200, r.text
        body = r.json()
        assert body.get("viewer", {}).get("is_admin") is False, (
            f"viewer.is_admin should be False for grad-5 user, got {body.get('viewer')}"
        )
        contacts = body.get("contacts", [])

        # Find anonymized admin contact (helpdesk-grouped)
        admin_contacts = [c for c in contacts if c.get("is_admin_contact")]
        assert len(admin_contacts) == 1, (
            f"Non-admin should see exactly 1 grouped 'Admin' contact, got {len(admin_contacts)}: "
            f"{[c['naam'] for c in admin_contacts]}"
        )
        ac = admin_contacts[0]
        assert ac["naam"] == "Admin"
        assert ac["avatar_ref"] is None, (
            f"Admin avatar must NOT leak to non-admin. Got: {ac['avatar_ref']!r}"
        )
        assert ac.get("gradatie") is None, "Gradatie must be hidden for anonymized admin"

        # Non-admin should NOT see admin-collectief
        assert not any(c["id"] == "admin-collectief" for c in contacts)

        # Bots still visible with avatar_ref intact
        bots = [c for c in contacts if c.get("is_bot")]
        assert len(bots) >= 3
        gallery_bots = [b for b in bots if isinstance(b.get("avatar_ref"), str) and b["avatar_ref"].startswith("gallery:")]
        assert len(gallery_bots) >= 3, f"Bots should retain gallery avatar_ref: {[(b['naam'], b['avatar_ref']) for b in bots]}"
    finally:
        # Cleanup
        session.delete(f"{API}/auth/users/{temp_id}")
