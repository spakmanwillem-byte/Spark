"""
Iter_37 backend tests:
- Nieuwe RPS triggers ('begin sps', 'start rps', 'begin spel sps', etc.) op Diep + normale chat.
- Multi-turn memory fix: fast-path moet naar turns_dir schrijven (/app/backend/data/chat/logs/{session_id}.json).
- Regressie: help/tts fast-path, normale LLM Diep, privacy.
- False-positive guard voor 'ik begin met sps oefenen'.
"""
import json
import os
import time
from pathlib import Path

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
COMPOSE_URL = f"{BASE_URL}/api/spark/compose"
CHAT_URL = f"{BASE_URL}/api/chat/message"
TURNS_DIR = Path("/app/backend/data/chat/logs")


# ---------- helpers ----------
def _post_compose(text, user_id="user-001", session_id=None):
    payload = {"text": text, "user_id": user_id}
    if session_id:
        payload["session_id"] = session_id
    r = requests.post(COMPOSE_URL, json=payload, timeout=60)
    return r


def _post_chat(message, user_id="user-001", session_id=None):
    payload = {"message": message, "user_id": user_id}
    if session_id:
        payload["session_id"] = session_id
    r = requests.post(CHAT_URL, json=payload, timeout=60)
    return r


@pytest.fixture(scope="module", autouse=True)
def _check_base_url():
    assert BASE_URL, "REACT_APP_BACKEND_URL must be set"


# ---------- TRIGGER tests (Diep /api/spark/compose) ----------
@pytest.mark.parametrize("text", [
    "begin sps",
    "start rps",
    "begin spel sps",
    "begin rps",
    "start sps",
    "begin spel rps",
    "start spel sps",
])
def test_diep_new_rps_triggers(text):
    r = _post_compose(text, session_id=f"iter37-trig-{text.replace(' ', '_')}")
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("success") is True, data
    assert data.get("action") == "open_game_rps", f"text={text!r} → {data}"
    assert data.get("fast_path") is True, data
    assert "🎮" in (data.get("message") or "")
    assert data.get("rps_opponent") == "spark"


# ---------- TRIGGER tests (normale chat /api/chat/message) ----------
def test_normale_chat_begin_sps():
    r = _post_chat("begin sps", session_id="iter37-chat-begin-sps")
    assert r.status_code == 200, r.text
    data = r.json()
    # action can be on top-level or response field
    assert data.get("action") == "open_game_rps", data
    assert "🎮" in (data.get("message") or "")


# ---------- MEMORY FIX: fast-path action (help) schrijft turns_dir ----------
def test_memory_fast_path_help_writes_turns():
    session_id = "iter37-memtest-1"
    fp = TURNS_DIR / f"{session_id}.json"
    if fp.exists():
        fp.unlink()
    # STEP 1: help
    r = _post_compose("help", session_id=session_id)
    assert r.status_code == 200, r.text
    assert r.json().get("fast_path") is True
    time.sleep(0.3)
    # STEP 2: turns file exists with 2 messages
    assert fp.exists(), f"{fp} should exist after fast-path help"
    data = json.loads(fp.read_text())
    msgs = data.get("messages", [])
    assert len(msgs) == 2, msgs
    assert msgs[0]["role"] == "user"
    assert msgs[0]["text"] == "help"
    assert msgs[1]["role"] == "spark"
    assert "Help-overzicht" in msgs[1]["text"] or "🔮" in msgs[1]["text"]
    # STEP 3: LLM-pad ziet de history (no error)
    r2 = _post_compose("wat zei je vorige bericht?", session_id=session_id)
    assert r2.status_code == 200, r2.text
    d2 = r2.json()
    assert d2.get("success") is True, d2
    # Should not be fast_path (this is an open LLM question)
    assert d2.get("fast_path") in (None, False)
    assert (d2.get("message") or "") != ""
    # After turn 2, file should have 4 messages
    time.sleep(0.3)
    data2 = json.loads(fp.read_text())
    assert len(data2.get("messages", [])) >= 4, data2


def test_memory_fast_path_rps_writes_turns():
    session_id = "iter37-memtest-rps"
    fp = TURNS_DIR / f"{session_id}.json"
    if fp.exists():
        fp.unlink()
    r = _post_compose("sps", session_id=session_id)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d.get("action") == "open_game_rps", d
    assert d.get("fast_path") is True
    time.sleep(0.3)
    assert fp.exists(), f"{fp} should exist after fast-path rps"
    data = json.loads(fp.read_text())
    msgs = data.get("messages", [])
    assert len(msgs) == 2, msgs
    assert msgs[0]["text"] == "sps"
    assert "🎮" in msgs[1]["text"]


# ---------- REGRESSIE ----------
def test_regression_help_fast_path():
    r = _post_compose("help", session_id="iter37-reg-help")
    assert r.status_code == 200
    d = r.json()
    assert d.get("action") == "open_help_bark"
    assert d.get("fast_path") is True


def test_regression_tts_fast_path():
    r = _post_compose("tts aan", session_id="iter37-reg-tts")
    assert r.status_code == 200, r.text
    d = r.json()
    # action_intents_service: action 'enable_tts'
    assert d.get("action") == "enable_tts", d
    assert d.get("fast_path") is True


def test_regression_normale_llm_diep():
    r = _post_compose("wat is filosofie?", session_id="iter37-reg-llm")
    assert r.status_code == 200, r.text
    d = r.json()
    assert d.get("success") is True, d
    assert d.get("action") in (None, "")
    assert d.get("fast_path") in (None, False)
    assert (d.get("message") or "").strip() != ""


def test_regression_privacy_no_maaike():
    r = _post_compose(
        "ik ben Willem, wie is mijn zus?",
        user_id="user-672f0e5c",
        session_id="iter37-reg-priv",
    )
    assert r.status_code == 200, r.text
    d = r.json()
    msg = (d.get("message") or "").lower()
    assert "maaike" not in msg, f"privacy leak: {d.get('message')}"


# ---------- FALSE-POSITIVE GUARD ----------
def test_false_positive_begin_sps_in_sentence():
    """
    'ik begin met sps oefenen' bevat 'begin' en 'sps' maar NIET de substring 'begin sps'
    (woord 'met' staat ertussen). Verwacht: GEEN open_game_rps fast-path.
    """
    r = _post_compose(
        "ik begin met sps oefenen",
        session_id="iter37-fp-guard",
    )
    assert r.status_code == 200, r.text
    d = r.json()
    assert d.get("action") != "open_game_rps", f"false positive: {d}"
