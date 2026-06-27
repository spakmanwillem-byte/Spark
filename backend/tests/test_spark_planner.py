"""Backend tests for Spark Planner (v6_spark_planner_001).
Tests Laag A (Brief), Laag B (Threads), Blueprint & Compose integration.
"""
import os
import json
import time
import pytest
import requests
from pathlib import Path

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://question-hub-160.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

TEST_USER = "test-planner-001"
REAL_USER = "user-001"
TEST_DATE = "2026-06-26"


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# ----------------------- BRIEF -----------------------

class TestBrief:
    def test_build_brief_too_few_turns(self, session):
        """Date with no chat logs for test user → expect success=false / error."""
        r = session.post(f"{API}/spark/planner/brief/build",
                         json={"user_id": TEST_USER, "date": "2025-01-01"})
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("success") is False
        assert "error" in data
        assert "weinig" in data["error"].lower() or "turns" in data["error"].lower()
        print(f"[OK] empty-date build returns: {data.get('error')}")

    def test_build_brief_with_seeded_logs(self, session):
        """Build brief on 2026-06-26 from seeded chat log."""
        r = session.post(f"{API}/spark/planner/brief/build",
                         json={"user_id": TEST_USER, "date": TEST_DATE},
                         timeout=120)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("success") is True, f"Brief build failed: {data}"
        brief = data["brief"]
        assert isinstance(brief.get("summary"), str) and brief["summary"].strip(), "summary leeg"
        assert isinstance(brief.get("themes"), list)
        assert isinstance(brief.get("open_questions"), list)
        assert isinstance(brief.get("emotional_tone"), str) and brief["emotional_tone"]
        assert brief.get("n_user_turns", 0) >= 3
        assert brief.get("date") == TEST_DATE
        print(f"[OK] brief built: themes={brief.get('themes')}, tone={brief.get('emotional_tone')}")

    def test_brief_latest(self, session):
        r = session.get(f"{API}/spark/planner/brief/latest", params={"user_id": TEST_USER})
        assert r.status_code == 200
        data = r.json()
        assert data.get("success") is True
        assert data["brief"]["user_id"] == TEST_USER
        assert data["brief"]["date"] == TEST_DATE

    def test_brief_list(self, session):
        r = session.get(f"{API}/spark/planner/brief/list", params={"user_id": TEST_USER})
        assert r.status_code == 200
        data = r.json()
        assert data.get("success") is True
        assert isinstance(data.get("briefs"), list) and len(data["briefs"]) >= 1
        first = data["briefs"][0]
        assert "date" in first and "summary" in first and "themes" in first


# ----------------------- THREADS -----------------------

class TestThreads:
    created_thread_id = None

    def test_threads_auto_created_from_brief(self, session):
        """After brief build, threads should be auto-synced from brief.themes."""
        r = session.get(f"{API}/spark/planner/threads", params={"user_id": TEST_USER})
        assert r.status_code == 200
        data = r.json()
        assert data.get("success") is True
        threads = data.get("threads", [])
        assert len(threads) >= 1, f"Expected at least 1 auto-thread, got: {threads}"
        print(f"[OK] auto-synced {len(threads)} threads from brief")

    def test_create_thread(self, session):
        r = session.post(f"{API}/spark/planner/threads",
                         json={"user_id": TEST_USER, "topic": "nieuw onderwerp", "intensity": 3})
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("success") is True
        t = data.get("thread")
        assert t.get("topic") == "nieuw onderwerp"
        assert t.get("intensity") == 3
        TestThreads.created_thread_id = t.get("id")

    def test_bump_thread(self, session):
        """Second POST with same topic should bump intensity, same id."""
        r = session.post(f"{API}/spark/planner/threads",
                         json={"user_id": TEST_USER, "topic": "nieuw onderwerp", "intensity": 2})
        assert r.status_code == 200
        data = r.json()
        assert data.get("success") is True
        t = data["thread"]
        assert t.get("id") == TestThreads.created_thread_id, "id should be same (bump)"
        assert t.get("intensity") >= 5  # was 3, bumped +2 → 5

    def test_patch_thread_status(self, session):
        assert TestThreads.created_thread_id is not None
        r = session.patch(f"{API}/spark/planner/threads/{TestThreads.created_thread_id}/status",
                          params={"user_id": TEST_USER},
                          json={"status": "sluimerend"})
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("success") is True
        assert data["thread"]["status"] == "sluimerend"

    def test_delete_thread(self, session):
        assert TestThreads.created_thread_id is not None
        r = session.delete(f"{API}/spark/planner/threads/{TestThreads.created_thread_id}",
                           params={"user_id": TEST_USER})
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("success") is True

    def test_decay(self, session):
        r = session.post(f"{API}/spark/planner/threads/decay", params={"user_id": TEST_USER})
        assert r.status_code == 200, r.text
        data = r.json()
        assert "demoted_to_sluimerend" in data
        assert "closed" in data


# ----------------------- BLUEPRINT -----------------------

class TestBlueprint:
    def test_get_blueprint(self, session):
        r = session.get(f"{API}/spark/planner/blueprint")
        assert r.status_code == 200
        data = r.json()
        assert data.get("success") is True
        bp = data.get("blueprint", {})
        assert "brief" in bp
        assert "threads" in bp
        assert "paths" in bp

    def test_blueprint_reload(self, session):
        r = session.post(f"{API}/spark/planner/blueprint/reload")
        assert r.status_code == 200
        data = r.json()
        assert data.get("success") is True


# ----------------------- COMPOSE INTEGRATION -----------------------

class TestComposeIntegration:
    def test_compose_injects_brief_and_threads(self, session):
        """For real user-001 (has brief on 2026-06-27 + threads), compose should
        return planner.brief_date + planner.active_threads."""
        r = session.post(f"{API}/spark/compose",
                         json={"text": "hoi Spark", "user_id": REAL_USER,
                               "session_id": "test-planner-compose"},
                         timeout=120)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("success") is True, f"Compose failed: {data}"
        planner_meta = data.get("planner")
        assert planner_meta is not None, f"Missing 'planner' in compose response: {list(data.keys())}"
        bd = planner_meta.get("brief_date")
        assert isinstance(bd, str) and len(bd) == 10 and bd[4] == "-" and bd[7] == "-", \
            f"brief_date not YYYY-MM-DD: {bd}"
        active = planner_meta.get("active_threads")
        assert isinstance(active, list) and len(active) >= 1, \
            f"active_threads should be non-empty list, got: {active}"
        print(f"[OK] compose planner meta: brief_date={bd}, active_threads={len(active)}")
