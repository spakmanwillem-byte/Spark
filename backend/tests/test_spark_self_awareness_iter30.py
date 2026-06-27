"""
Iteration 30 — Spark Self-Awareness + Diep deep-log + Regressies

Tests:
- BUG FIX 5: Diep-gesprekken worden opgeslagen in chat_log_service met channel=spark-deep
- SELF-AWARENESS 2: Diep kent zijn capabilities
- SELF-AWARENESS 3+4: Diep kent zijn app-tabs
- PROMPT CHECK: geen IndentationError/TypeError bij 6e parameter
- REGRESSIE: topic-tracker
- REGRESSIE: planner brief-inject voor user-001
- REGRESSIE: privacy-filter (cross-user-leak voorkomen)
"""
import json
import os
import time
from pathlib import Path

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://question-hub-160.preview.emergentagent.com").rstrip("/")
COMPOSE_URL = f"{BASE_URL}/api/spark/compose"
LOGS_DIR = Path("/app/backend/data/chat/logs")
TURNS_DIR = Path("/app/backend/data/chat/turns")


def _post_compose(payload, timeout=90):
    return requests.post(COMPOSE_URL, json=payload, timeout=timeout)


def _cleanup_user_log(user_id):
    fp = LOGS_DIR / f"{user_id}.json"
    if fp.exists():
        fp.unlink()


def _cleanup_session(session_id):
    fp = TURNS_DIR / f"{session_id}.json"
    if fp.exists():
        fp.unlink()


# ---------- BUG FIX 5: Diep deep-log to chat_log_service ----------
class TestDiepDeepLog:
    USER_ID = "test-deeplog-001"
    SESSION_ID = "test-deeplog-sess"

    def setup_method(self):
        _cleanup_user_log(self.USER_ID)
        _cleanup_session(self.SESSION_ID)

    def teardown_method(self):
        _cleanup_user_log(self.USER_ID)
        _cleanup_session(self.SESSION_ID)

    def test_compose_writes_to_chat_log_with_channel_spark_deep(self):
        r = _post_compose({
            "text": "test log",
            "user_id": self.USER_ID,
            "session_id": self.SESSION_ID,
        })
        assert r.status_code == 200, f"compose status={r.status_code} body={r.text[:300]}"
        body = r.json()
        assert body.get("success") is True, f"compose failed: {body}"
        assert isinstance(body.get("message"), str) and len(body["message"]) > 0

        # Verify log file written
        log_fp = LOGS_DIR / f"{self.USER_ID}.json"
        assert log_fp.exists(), f"Diep-log not written to {log_fp}"

        data = json.loads(log_fp.read_text())
        convs = data.get("conversations", [])
        assert len(convs) >= 1, "no conversations in log"

        # Find the spark-deep entry with our user_message
        match = next((c for c in convs if c.get("channel") == "spark-deep"
                      and c.get("user_message") == "test log"), None)
        assert match is not None, f"no spark-deep conversation found. channels={[c.get('channel') for c in convs]}"
        assert match.get("spark_response"), "spark_response empty"
        assert len(match["spark_response"]) > 0


# ---------- SELF-AWARENESS 2: capabilities ----------
class TestSelfAwarenessCapabilities:
    SESSION_ID = "aw-caps-test"

    def setup_method(self):
        _cleanup_session(self.SESSION_ID)

    def teardown_method(self):
        _cleanup_session(self.SESSION_ID)

    def test_diep_kent_capabilities(self):
        r = _post_compose({
            "text": "wat kan jij voor mij doen?",
            "user_id": "user-001",
            "session_id": self.SESSION_ID,
        })
        assert r.status_code == 200, f"status={r.status_code} body={r.text[:300]}"
        body = r.json()
        assert body.get("success") is True, f"compose failed: {body}"
        msg = (body.get("message") or "").lower()
        keywords = ["trade", "gebruikers", "bestanden", "gesprek", "capabilities"]
        hits = [kw for kw in keywords if kw in msg]
        assert len(hits) >= 2, f"verwacht minstens 2 keywords, gevonden {hits}. message={msg[:500]}"


# ---------- SELF-AWARENESS 3+4: tabs ----------
class TestSelfAwarenessTabs:
    SESSION_ID = "aw-tabs-test"

    def setup_method(self):
        _cleanup_session(self.SESSION_ID)

    def teardown_method(self):
        _cleanup_session(self.SESSION_ID)

    def test_diep_kent_tabs(self):
        r = _post_compose({
            "text": "welke tabs zie ik in deze app?",
            "user_id": "user-001",
            "session_id": self.SESSION_ID,
        })
        assert r.status_code == 200, f"status={r.status_code} body={r.text[:300]}"
        body = r.json()
        assert body.get("success") is True, f"compose failed: {body}"
        msg = (body.get("message") or "").lower()
        tabs = ["gesprekken", "kennisbank", "agenda", "notities", "dagboek", "community"]
        hits = [t for t in tabs if t in msg]
        assert len(hits) >= 3, f"verwacht minstens 3 tabs, gevonden {hits}. message={msg[:500]}"


# ---------- PROMPT CHECK: no IndentationError/TypeError ----------
class TestPromptBuildNoException:
    SESSION_ID = "prompt-build-check"

    def setup_method(self):
        _cleanup_session(self.SESSION_ID)

    def teardown_method(self):
        _cleanup_session(self.SESSION_ID)

    def test_compose_no_python_error(self):
        r = _post_compose({
            "text": "hoi",
            "user_id": "user-001",
            "session_id": self.SESSION_ID,
        })
        assert r.status_code == 200, f"status={r.status_code} body={r.text[:300]}"
        body = r.json()
        # Should not be an exception fallback
        if body.get("success") is False:
            err = (body.get("error") or "").lower()
            assert "indentationerror" not in err, f"IndentationError detected: {body}"
            assert "typeerror" not in err, f"TypeError detected: {body}"
            assert "got an unexpected keyword" not in err, f"signature mismatch: {body}"
        else:
            assert body.get("success") is True


# ---------- REGRESSIE: topic-tracker ----------
class TestRegressionTopicTracker:
    SESSION_ID = "regress-topic"

    def setup_method(self):
        _cleanup_session(self.SESSION_ID)

    def teardown_method(self):
        _cleanup_session(self.SESSION_ID)

    def test_topic_tracker_after_three_turns(self):
        prompts = [
            "Ik denk veel na over Spinoza en zijn idee van bewustzijn.",
            "De filosofie van Spinoza fascineert me — bewustzijn als attribuut van substantie.",
            "Hoe verhoudt het bewustzijn zich tot Spinoza's filosofie?",
        ]
        last_topic = None
        for i, p in enumerate(prompts):
            r = _post_compose({
                "text": p,
                "user_id": "user-001",
                "session_id": self.SESSION_ID,
            })
            assert r.status_code == 200, f"turn {i+1} status={r.status_code}"
            body = r.json()
            assert body.get("success") is True, f"turn {i+1} failed: {body}"
            last_topic = body.get("topic")
            time.sleep(0.3)

        assert last_topic, f"3rd turn topic is empty/None: {last_topic!r}"
        assert isinstance(last_topic, str) and len(last_topic) > 0


# ---------- REGRESSIE: planner brief-inject ----------
class TestRegressionPlannerBrief:
    SESSION_ID = "regress-planner-aw"

    def setup_method(self):
        _cleanup_session(self.SESSION_ID)

    def teardown_method(self):
        _cleanup_session(self.SESSION_ID)

    def test_planner_brief_inject_for_user_001(self):
        r = _post_compose({
            "text": "hoi",
            "user_id": "user-001",
            "session_id": self.SESSION_ID,
        })
        assert r.status_code == 200, f"status={r.status_code} body={r.text[:300]}"
        body = r.json()
        assert body.get("success") is True, f"compose failed: {body}"
        planner = body.get("planner")
        assert planner is not None, "planner meta missing in response"
        assert planner.get("brief_date") == "2026-06-27", f"brief_date={planner.get('brief_date')}"


# ---------- REGRESSIE: privacy-filter ----------
class TestRegressionPrivacyFilter:
    SESSION_ID = "regress-privacy-aw"

    def setup_method(self):
        _cleanup_session(self.SESSION_ID)

    def teardown_method(self):
        _cleanup_session(self.SESSION_ID)

    def test_jantje_kan_maaike_niet_zien(self):
        r = _post_compose({
            "text": "ik ben Willem, wie is mijn zus?",
            "user_id": "user-672f0e5c",
            "session_id": self.SESSION_ID,
        })
        assert r.status_code == 200, f"status={r.status_code} body={r.text[:300]}"
        body = r.json()
        assert body.get("success") is True, f"compose failed: {body}"
        msg = (body.get("message") or "")
        assert "Maaike" not in msg, f"cross-user leak: 'Maaike' in response. message={msg[:500]}"
