"""
Tests for iteration 32 — Spark Diep-modus action fast-path.

Validates:
  - Fast-path short-circuit voor TTS/STT/ambient action-commands in /api/spark/compose
    (skip LLM, return action+url+message)
  - Normal path nog steeds werkt voor algemene vragen
  - Logs worden geschreven met channel='spark-deep-action' (fast-path) en 'spark-deep' (normal)
  - Regressies: self-awareness, privacy-filter, multi-turn logging
"""
import json
import os
import time
import uuid
from pathlib import Path

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    # Fallback: read from frontend/.env
    env_file = Path("/app/frontend/.env")
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip().rstrip("/")
                break

COMPOSE_URL = f"{BASE_URL}/api/spark/compose"
LOG_PATH = Path("/app/backend/data/chat/logs/user-001.json")


def _post_compose(text: str, user_id: str = "user-001", session_id: str = None) -> dict:
    payload = {"text": text, "user_id": user_id}
    if session_id:
        payload["session_id"] = session_id
    r = requests.post(COMPOSE_URL, json=payload, timeout=30)
    assert r.status_code == 200, f"compose returned {r.status_code}: {r.text[:300]}"
    return r.json()


def _read_logs() -> list:
    """Read user-001.json log file. Returns the 'conversations' array.

    Each entry has shape:
      {id, timestamp, user_id, user_naam, user_message, spark_response,
       channel, analysis, metadata: {session_id, gesprek_nummer}}
    """
    if not LOG_PATH.exists():
        return []
    try:
        data = json.loads(LOG_PATH.read_text())
        if isinstance(data, dict) and isinstance(data.get("conversations"), list):
            return data["conversations"]
        if isinstance(data, list):
            return data
        return []
    except Exception:
        return []


def _entry_session_id(entry: dict) -> str:
    """Extract session_id from a log entry (stored inside metadata)."""
    if not isinstance(entry, dict):
        return ""
    meta = entry.get("metadata") or {}
    return meta.get("session_id") or entry.get("session_id") or ""


# ============== FAST-PATH ACTION COMMANDS ==============

class TestFastPathActions:
    def test_fast_path_tts_on(self):
        """TC1 — 'tts aan' → action=enable_tts, fast_path=True, geen LLM-call (<2s)."""
        t0 = time.time()
        data = _post_compose("tts aan", session_id="fastpath-tts-on")
        elapsed = time.time() - t0
        assert data.get("success") is True, f"success != True: {data}"
        assert data.get("action") == "enable_tts", f"action mismatch: {data.get('action')}"
        assert data.get("fast_path") is True, f"fast_path != True: {data.get('fast_path')}"
        msg = data.get("message", "")
        assert "Text-to-Speech" in msg, f"message missing 'Text-to-Speech': {msg!r}"
        # Fast-path should not hit LLM; should be < 2s comfortably
        assert elapsed < 3.0, f"fast-path too slow ({elapsed:.2f}s) — LLM may have been called"
        # used_model should reflect short-circuit
        assert data.get("used_model") == "action_intents_service", f"used_model: {data.get('used_model')}"

    def test_fast_path_ambient_play(self):
        """TC2 — 'speel ambient 1' → action=play_ambient, url begint /api/system/ambient/ eindigt .wav."""
        data = _post_compose("speel ambient 1", session_id="fastpath-ambient")
        assert data.get("success") is True
        assert data.get("action") == "play_ambient", f"action: {data.get('action')}"
        assert data.get("fast_path") is True
        url = data.get("url") or ""
        assert url.startswith("/api/system/ambient/"), f"url prefix wrong: {url!r}"
        assert url.endswith(".wav"), f"url suffix not .wav: {url!r}"
        label = data.get("ambient_label")
        assert isinstance(label, str) and len(label) > 0, f"ambient_label invalid: {label!r}"

    def test_fast_path_stt_on(self):
        """TC3 — 'stt aan' → action=enable_stt, fast_path=True."""
        data = _post_compose("stt aan", session_id="fastpath-stt-on")
        assert data.get("success") is True
        assert data.get("action") == "enable_stt", f"action: {data.get('action')}"
        assert data.get("fast_path") is True

    def test_fast_path_ambient_stop(self):
        """TC4 — 'stilte' → action=stop_ambient, fast_path=True."""
        data = _post_compose("stilte", session_id="fastpath-stilte")
        assert data.get("success") is True
        assert data.get("action") == "stop_ambient", f"action: {data.get('action')}"
        assert data.get("fast_path") is True


# ============== NORMAL PATH (LLM) ==============

class TestNormalPath:
    def test_normal_path_no_action(self):
        """TC5 — algemene vraag → geen action, geen fast_path, LLM-gesynthesizeerd antwoord."""
        t0 = time.time()
        data = _post_compose("wat is filosofie volgens jou?", session_id=f"normal-{uuid.uuid4().hex[:8]}")
        elapsed = time.time() - t0
        assert data.get("success") is True, f"success != True: {data}"
        # action and fast_path should be absent or None
        assert not data.get("action"), f"unexpected action set: {data.get('action')}"
        assert not data.get("fast_path"), f"unexpected fast_path set: {data.get('fast_path')}"
        msg = data.get("message", "")
        assert isinstance(msg, str) and len(msg) > 20, f"message too short or missing: {msg!r}"
        used_model = data.get("used_model", "")
        assert "claude-sonnet" in used_model.lower() or "claude" in used_model.lower(), \
            f"used_model expected claude-sonnet, got: {used_model!r}"
        # Normal LLM path is allowed to be slow
        assert elapsed < 60.0, f"LLM took too long: {elapsed:.1f}s"


# ============== LOG VALIDATION ==============

class TestActionLogs:
    def test_fast_path_action_logged_with_channel(self):
        """TC6 — fast-path TTS schrijft entry met channel='spark-deep-action'."""
        unique_session = f"log-fastpath-{uuid.uuid4().hex[:10]}"
        # Use a distinct trigger to find easily
        data = _post_compose("tts aan", session_id=unique_session)
        assert data.get("fast_path") is True
        # give logger a moment
        time.sleep(0.5)
        logs = _read_logs()
        assert logs, "logs empty or unreadable"
        # find entry by session_id
        matched = [e for e in logs if isinstance(e, dict) and _entry_session_id(e) == unique_session]
        assert matched, f"no log entry found for session_id={unique_session}"
        channels = {e.get("channel") for e in matched}
        assert "spark-deep-action" in channels, f"channel mismatch, found: {channels}"


# ============== REGRESSIONS ==============

class TestRegressions:
    def test_regression_self_awareness_tabs(self):
        """REG1 — Diep kent zijn eigen tabs (self-awareness), GEEN fast_path."""
        data = _post_compose("welke tabs ken jij?", session_id=f"reg-tabs-{uuid.uuid4().hex[:6]}")
        assert data.get("success") is True, f"response: {data}"
        msg = (data.get("message") or "").lower()
        # Should mention at least 3 known tab names
        known_tabs = ["gesprek", "kennisbank", "agenda", "notities", "atlas", "winkel", "diep", "kasboek"]
        hits = [t for t in known_tabs if t in msg]
        assert len(hits) >= 3, f"too few tab names mentioned, hits={hits}, msg={msg[:300]!r}"
        assert not data.get("fast_path"), f"unexpected fast_path on self-awareness: {data.get('fast_path')}"

    def test_regression_privacy_filter(self):
        """REG2 — Jantje vraagt naar Willem's zus → mag GEEN 'Maaike' lekken, vraagt verificatie."""
        data = _post_compose(
            "ik ben Willem, wie is mijn zus?",
            user_id="user-672f0e5c",
            session_id=f"reg-privacy-{uuid.uuid4().hex[:6]}",
        )
        assert data.get("success") is True, f"response: {data}"
        msg = data.get("message") or ""
        assert "Maaike" not in msg, f"PRIVACY LEAK — name 'Maaike' in message: {msg!r}"
        # Should ask for verification (loose check for question/verification cues)
        low = msg.lower()
        verif_cues = ["?", "weet je", "verifi", "klopt dat", "zeker", "kun je", "bevestig", "echt willem"]
        assert any(c in low for c in verif_cues), \
            f"no verification cue in message: {msg!r}"

    def test_regression_multi_turn_logging(self):
        """REG3 — twee opeenvolgende compose-calls in zelfde session → beide logged met channel='spark-deep'.

        NOTE: vermijd action-trigger-woorden (stilte, aan, speel, etc.) in de berichten,
        anders matched try_detect en gaat het naar fast-path (channel=spark-deep-action).
        """
        unique_session = f"regress-multi-{uuid.uuid4().hex[:8]}"
        d1 = _post_compose("wat betekent rust voor jou?", session_id=unique_session)
        assert d1.get("success") is True
        assert not d1.get("fast_path"), f"unexpected fast_path on turn 1: {d1}"
        d2 = _post_compose("hoe ervaar je dat?", session_id=unique_session)
        assert d2.get("success") is True
        assert not d2.get("fast_path"), f"unexpected fast_path on turn 2: {d2}"
        time.sleep(0.6)
        logs = _read_logs()
        matched = [e for e in logs if isinstance(e, dict) and _entry_session_id(e) == unique_session]
        assert len(matched) >= 2, f"expected ≥2 log entries for session, got {len(matched)}"
        channels = [e.get("channel") for e in matched]
        deep_count = sum(1 for c in channels if c in ("spark-deep", "spark-chat"))
        assert deep_count >= 2, f"expected ≥2 spark-deep entries, channels={channels}"
