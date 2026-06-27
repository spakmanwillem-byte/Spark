"""Tests for Spark Core 2.0 topic_tracker + disclaimer/intent_matcher blueprints.

Validates:
1. /api/spark/compose works without IndentationError (3 sequential calls)
2. topic_tracker exposes `topic` and `blueprint_version` in response
3. /api/spark/disclaimer returns expected leidende_lagen_counts + blueprint_version
4. /api/chat/message routes via intent_matcher (no 500)
5. /api/spark/compose/blueprint/reload + /api/spark/compose/blueprint topic_tracker config
"""
import os
import time
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/") or \
    open("/app/frontend/.env").read().split("REACT_APP_BACKEND_URL=")[1].split("\n")[0].strip()

SESSION_ID = "test-fork-topic"
TIMEOUT = 90  # LLM calls can be slow


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# -------- BUG FIX VALIDATIE: 3 sequential compose calls --------
class TestComposeNoIndentError:
    """POST /api/spark/compose works without IndentationError after the fix."""

    USER_TEXTS = [
        "Wat is filosofie volgens jou?",
        "Vertel meer over Spinoza",
        "En wat met bewustzijn?",
    ]
    responses = []  # capture for next test class

    def test_compose_three_sequential_calls(self, session):
        for i, txt in enumerate(self.USER_TEXTS):
            payload = {
                "text": txt,
                "user_id": "user-001",
                "session_id": SESSION_ID,
            }
            r = session.post(f"{BASE_URL}/api/spark/compose", json=payload, timeout=TIMEOUT)
            assert r.status_code == 200, f"turn {i+1}: HTTP {r.status_code} — body={r.text[:400]}"
            data = r.json()
            assert data.get("success") is True, f"turn {i+1}: success != true — {data}"
            assert data.get("message"), f"turn {i+1}: empty message — {data}"
            TestComposeNoIndentError.responses.append(data)
            time.sleep(0.5)


# -------- TOPIC TRACKER --------
class TestTopicTrackerFeature:
    def test_topic_present_in_last_response(self, session):
        assert TestComposeNoIndentError.responses, "previous compose tests didn't run"
        last = TestComposeNoIndentError.responses[-1]
        topic = last.get("topic")
        assert topic, f"response.topic empty: {last}"
        assert isinstance(topic, str)
        assert len(topic) > 0

    def test_blueprint_version_present(self, session):
        last = TestComposeNoIndentError.responses[-1]
        assert "blueprint_version" in last, f"blueprint_version missing: {last.keys()}"
        assert last["blueprint_version"]


# -------- DISCLAIMER BLUEPRINT --------
class TestDisclaimerBlueprint:
    def test_disclaimer_endpoint(self, session):
        r = session.get(f"{BASE_URL}/api/spark/disclaimer", timeout=30)
        assert r.status_code == 200, r.text[:400]
        data = r.json()
        assert data.get("success") is True
        assert "disclaimer" in data and isinstance(data["disclaimer"], dict)
        assert "leidende_lagen_counts" in data
        counts = data["leidende_lagen_counts"]
        for key in ("kernwaarden", "normen", "bijbel_items", "bijbel",
                    "capabilities", "capabilities_total"):
            assert key in counts, f"missing key '{key}' in leidende_lagen_counts: {counts}"
            assert isinstance(counts[key], int), f"{key} not int: {counts[key]}"
            assert counts[key] >= 0
        assert "blueprint_version" in data, f"blueprint_version missing in disclaimer response: {data.keys()}"


# -------- INTENT MATCHER (via /api/chat/message) --------
class TestIntentMatcher:
    def test_chat_message_no_500(self, session):
        payload = {
            "user_id": "user-001",
            "sleutelwoord": "Appelsap",
            "message": "hoeveel gebruikers hebben we?",
        }
        r = session.post(f"{BASE_URL}/api/chat/message", json=payload, timeout=30)
        assert r.status_code == 200, f"HTTP {r.status_code}: {r.text[:400]}"
        data = r.json()
        # intent-routing actief: accept either "reply" or "message" (capability_response)
        text_field = data.get("reply") or data.get("message")
        assert text_field, f"no reply/message in response: {data}"
        assert isinstance(text_field, str)


# -------- BLUEPRINT RELOAD --------
class TestBlueprintReload:
    def test_reload(self, session):
        r = session.post(f"{BASE_URL}/api/spark/compose/blueprint/reload", timeout=30)
        assert r.status_code == 200, r.text[:400]
        d = r.json()
        assert d.get("success") is True

    def test_get_blueprint_has_topic_tracker(self, session):
        r = session.get(f"{BASE_URL}/api/spark/compose/blueprint", timeout=30)
        assert r.status_code == 200
        bp = r.json()
        # response may wrap blueprint inside a "blueprint" key
        body = bp.get("blueprint", bp)
        assert "topic_tracker" in body, f"topic_tracker missing in blueprint: {list(body.keys())}"
        assert body["topic_tracker"].get("enabled") is True
