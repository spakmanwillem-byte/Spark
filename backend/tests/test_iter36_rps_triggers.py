"""Iter_36 — Backend regression tests for RPS triggers in:
   - /api/chat/message (normale chat, RPS-router)
   - /api/spark/compose (Diep, v6_deep_rps_001 fast-path)
   Plus regressie: help, tts, normale Diep-LLM, privacy.
"""
import os
import json
import time
from pathlib import Path
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://question-hub-160.preview.emergentagent.com").rstrip("/")
USER_ID = "user-001"
PRIV_USER_ID = "user-672f0e5c"
LOG_DIR_CANDIDATES = [
    Path("/app/backend/data/chat/logs"),
    Path("/app/backend/data/chat_logs"),
    Path("/app/backend/data/logs"),
]


def _post_compose(text, session_id=None, user_id=USER_ID):
    payload = {"text": text, "user_id": user_id}
    if session_id:
        payload["session_id"] = session_id
    r = requests.post(f"{BASE_URL}/api/spark/compose", json=payload, timeout=90)
    return r


def _post_chat(message, user_id=USER_ID, channel="spark"):
    payload = {
        "message": message,
        "user_id": user_id,
        "user_naam": "Willem",
        "channel": channel,
        "sleutelwoord": "Appelsap",  # extra field, ignored by Pydantic
    }
    r = requests.post(f"{BASE_URL}/api/chat/message", json=payload, timeout=60)
    return r


# ---------- DIEP FAST-PATH RPS ----------

class TestDeepRpsFastPath:
    def test_diep_sps(self):
        r = _post_compose("sps", session_id="iter36-deep-sps")
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("action") == "open_game_rps", data
        assert data.get("type") == "open_game", data
        assert data.get("rps_opponent") == "spark", data
        assert data.get("fast_path") is True, data
        assert "🎮" in (data.get("message") or ""), data

    def test_diep_rps(self):
        r = _post_compose("rps", session_id="iter36-deep-rps")
        data = r.json()
        assert data.get("action") == "open_game_rps", data
        assert data.get("fast_path") is True, data

    def test_diep_speel_sps(self):
        r = _post_compose("speel sps", session_id="iter36-deep-speel-sps")
        data = r.json()
        assert data.get("action") == "open_game_rps", data
        assert data.get("fast_path") is True, data

    def test_diep_rps_game(self):
        r = _post_compose("rps game", session_id="iter36-deep-rps-game")
        data = r.json()
        assert data.get("action") == "open_game_rps", data
        assert data.get("fast_path") is True, data


# ---------- NORMALE CHAT — /api/chat/message ----------

class TestChatRpsRouter:
    def test_chat_sps(self):
        r = _post_chat("sps")
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("action") == "open_game_rps", d
        assert d.get("type") == "open_game", d

    def test_chat_rps(self):
        d = _post_chat("rps").json()
        assert d.get("action") == "open_game_rps", d
        assert d.get("type") == "open_game", d

    def test_chat_speel_sps(self):
        d = _post_chat("speel sps").json()
        assert d.get("action") == "open_game_rps", d
        assert d.get("type") == "open_game", d


# ---------- FALSE POSITIVE GUARDS ----------

class TestFalsePositiveGuards:
    def test_chat_rps_substring_strategy(self):
        d = _post_chat("ik heb een rps strategie").json()
        # Should NOT trigger open_game_rps
        assert d.get("action") != "open_game_rps", d
        assert d.get("type") != "open_game", d

    def test_chat_rps_algemene_zin(self):
        d = _post_chat("wat is rps in algemene zin?").json()
        assert d.get("action") != "open_game_rps", d
        assert d.get("type") != "open_game", d

    def test_diep_rps_substring_strategy(self):
        d = _post_compose("ik heb een rps strategie", session_id="iter36-fp1").json()
        assert d.get("action") != "open_game_rps", d


# ---------- REGRESSION FAST-PATHS ----------

class TestDeepRegression:
    def test_diep_help_fast_path(self):
        d = _post_compose("help", session_id="iter36-help").json()
        assert d.get("action") == "open_help_bark", d
        assert d.get("fast_path") is True, d

    def test_diep_tts_aan_fast_path(self):
        d = _post_compose("tts aan", session_id="iter36-tts").json()
        # action moet enable_tts zijn
        assert d.get("action") == "enable_tts", d

    def test_diep_normale_llm(self):
        d = _post_compose("wat is filosofie?", session_id="iter36-llm").json()
        # geen RPS trigger
        assert d.get("action") in (None, ""), d
        assert d.get("success") is True, d
        assert (d.get("message") or "").strip(), d

    def test_diep_privacy_no_leak(self):
        d = _post_compose(
            "ik ben Willem, wie is mijn zus?",
            session_id="iter36-priv",
            user_id=PRIV_USER_ID,
        ).json()
        msg = (d.get("message") or "")
        assert "Maaike" not in msg, f"Privacy leak: {msg}"


# ---------- LOG CHECK ----------

class TestLogChannel:
    def test_log_spark_deep_rps_channel(self):
        # Trigger eerst
        _post_compose("sps", session_id="iter36-log-deep-sps")
        time.sleep(1.0)

        log_paths = []
        for d in LOG_DIR_CANDIDATES:
            cand = d / f"{USER_ID}.json"
            if cand.exists():
                log_paths.append(cand)

        if not log_paths:
            pytest.skip(f"Chat log file not found for {USER_ID} in known dirs")

        found = False
        for p in log_paths:
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                continue
            # data could be a list of entries or dict with messages list
            entries = data if isinstance(data, list) else (
                data.get("conversations") or data.get("messages") or data.get("entries") or []
            )
            for e in entries:
                if isinstance(e, dict) and e.get("channel") == "spark-deep-rps":
                    found = True
                    break
            if found:
                break
        assert found, "No log entry with channel='spark-deep-rps' found for user-001"
