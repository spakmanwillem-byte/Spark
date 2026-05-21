"""
Spark Core 2.0 - Ronde 1 features tests.
Covers:
  - Glow notifications (privé DM, admin-collectief)
  - Admin Collectief private channel (visibility, broadcast, 403 for non-admin)
  - Spark unstoppable bot (trade/bot/stop, trade/monitor/stop)
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://question-hub-160.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN_ID = "user-001"          # Willem (grad 1)
NON_ADMIN_ID = "user-c609d7d1"  # Marieke (grad 3)
SPARK_ID = "user-000"
ADMIN_COLLECTIEF_ID = "admin-collectief"


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# ---------- Module: Contacts (admin-collectief) ----------
class TestAdminCollectief:
    def test_admin_sees_admin_collectief_at_top(self, session):
        r = session.get(f"{API}/contacts/list", params={"user_id": ADMIN_ID})
        assert r.status_code == 200, r.text
        data = r.json()
        contacts = data.get("contacts") or data if isinstance(data, list) else data.get("contacts", [])
        # Try common shapes
        if isinstance(data, dict) and "contacts" in data:
            contacts = data["contacts"]
        assert len(contacts) > 0
        top = contacts[0]
        assert top.get("id") == ADMIN_COLLECTIEF_ID
        assert top.get("is_collective") is True
        assert top.get("naam") == "Admin Collectief"
        assert top.get("avatar") == "🛡️"

    def test_non_admin_does_not_see_admin_collectief(self, session):
        r = session.get(f"{API}/contacts/list", params={"user_id": NON_ADMIN_ID})
        assert r.status_code == 200, r.text
        data = r.json()
        contacts = data.get("contacts", []) if isinstance(data, dict) else data
        ids = [c.get("id") for c in contacts]
        assert ADMIN_COLLECTIEF_ID not in ids

    def test_admin_can_send_to_admin_collectief(self, session):
        payload = {
            "from_user_id": ADMIN_ID,
            "to_user_id": ADMIN_COLLECTIEF_ID,
            "text": "TEST_admin_broadcast_message",
        }
        r = session.post(f"{API}/contacts/send", json=payload)
        assert r.status_code == 200, r.text
        data = r.json()
        # success should be true-ish
        assert data.get("success") in (True, None) or data.get("message") or data.get("id")

    def test_non_admin_send_to_admin_collectief_forbidden(self, session):
        payload = {
            "from_user_id": NON_ADMIN_ID,
            "to_user_id": ADMIN_COLLECTIEF_ID,
            "text": "TEST_should_be_blocked",
        }
        r = session.post(f"{API}/contacts/send", json=payload)
        assert r.status_code == 403, f"Expected 403, got {r.status_code}: {r.text}"

    def test_get_messages_for_admin_collectief_marks_read(self, session):
        r = session.get(
            f"{API}/contacts/messages",
            params={"user_id": ADMIN_ID, "contact_id": ADMIN_COLLECTIEF_ID},
        )
        assert r.status_code == 200, r.text
        data = r.json()
        msgs = data.get("messages", []) if isinstance(data, dict) else data
        assert isinstance(msgs, list)
        # Test sent message above should be present
        texts = [m.get("text") for m in msgs]
        assert any("TEST_admin_broadcast_message" in (t or "") for t in texts)
        # After GET admin should be removed from unread_by
        for m in msgs:
            assert ADMIN_ID not in (m.get("unread_by") or [])


# ---------- Module: Urgent (glow) ----------
class TestUrgentGlow:
    def test_glow_payload_structure(self, session):
        r = session.get(f"{API}/urgent/notifications", params={"user_id": ADMIN_ID})
        assert r.status_code == 200, r.text
        data = r.json()
        glow = data.get("glow")
        assert isinstance(glow, dict), f"Missing glow object: {data}"
        # chat and chat-prive keys should be present (may be empty/null when nothing unread)
        assert "chat" in glow or "chat-prive" in glow
        items = data.get("items", [])
        assert isinstance(items, list)

    def test_glow_after_sending_prive_dm(self, session):
        # Admin sends a DM to non-admin, then non-admin's glow should mention prive_dm
        payload = {
            "from_user_id": ADMIN_ID,
            "to_user_id": NON_ADMIN_ID,
            "text": "TEST_glow_trigger_message",
        }
        s = session.post(f"{API}/contacts/send", json=payload)
        assert s.status_code == 200, s.text

        r = session.get(f"{API}/urgent/notifications", params={"user_id": NON_ADMIN_ID})
        assert r.status_code == 200, r.text
        data = r.json()
        items = data.get("items", [])
        kinds = [i.get("kind") for i in items]
        glow = data.get("glow", {})
        # Either an item with kind prive_dm exists OR glow chat/chat-prive set to amber/red
        has_dm_kind = "prive_dm" in kinds
        has_chat_glow = bool(glow.get("chat")) or bool(glow.get("chat-prive"))
        assert has_dm_kind or has_chat_glow, f"No prive_dm signal: items={items} glow={glow}"


# ---------- Module: Trade (Spark unstoppable) ----------
class TestSparkUnstoppable:
    def test_bot_stop_spark_blocked(self, session):
        r = session.post(f"{API}/trade/bot/stop/{SPARK_ID}")
        assert r.status_code in (200, 400, 403), r.status_code
        data = r.json()
        assert data.get("success") is False
        assert data.get("code") == "SPARK_UNSTOPPABLE", f"Got: {data}"

    def test_bot_stop_other_user_works(self, session):
        # Try to stop a non-Spark bot; should NOT return SPARK_UNSTOPPABLE
        r = session.post(f"{API}/trade/bot/stop/{ADMIN_ID}")
        # Either succeed (200) or fail for other reason but code must NOT be SPARK_UNSTOPPABLE
        data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
        assert data.get("code") != "SPARK_UNSTOPPABLE", f"Other user incorrectly blocked: {data}"

    def test_monitor_stop_mentions_spark_if_blocked(self, session):
        r = session.post(f"{API}/trade/monitor/stop")
        # We can't guarantee Spark monitor is running, so accept either success or blocked-with-Spark-mention
        assert r.status_code in (200, 400, 403), r.status_code
        data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
        if data.get("success") is False:
            payload_str = str(data).lower()
            assert "spark" in payload_str, f"monitor blocked but no Spark mention: {data}"
