"""
v6_deep_help_001 — Test suite for iter33
Tests:
  - Fast-path help via /api/spark/compose (Diep)
  - Pattern expansion in smart_intents_service._HELP_PATTERNS
  - Regressies: action-intents (TTS/STT/ambient), normale Diep LLM, privacy, log channel
  - Normal chat regressie: /api/chat/message ook 'open_help_bark'
"""
import os
import time
import json
import pytest
import requests
from pathlib import Path

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    # Fallback to frontend .env directly
    fp = Path("/app/frontend/.env")
    if fp.exists():
        for line in fp.read_text().splitlines():
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip().rstrip("/")
                break

assert BASE_URL, "REACT_APP_BACKEND_URL niet gezet"

COMPOSE_URL = f"{BASE_URL}/api/spark/compose"
CHAT_URL = f"{BASE_URL}/api/chat/message"
LOG_FILE = Path("/app/backend/data/chat/logs/user-001.json")


# ============ FAST-PATH HELP TESTS ============
class TestHelpFastPath:
    """v6_deep_help_001 — fast-path tests"""

    def test_help_basis(self):
        """text='help' → action='open_help_bark', fast_path=true, <2s"""
        start = time.time()
        r = requests.post(COMPOSE_URL, json={
            "text": "help",
            "user_id": "user-001",
            "session_id": "help-fp-1",
        }, timeout=15)
        elapsed = time.time() - start
        assert r.status_code == 200, f"Status: {r.status_code} body: {r.text[:300]}"
        data = r.json()
        assert data.get("success") is True, f"success: {data}"
        assert data.get("action") == "open_help_bark", f"action: {data.get('action')}"
        assert data.get("fast_path") is True, f"fast_path: {data.get('fast_path')}"
        msg = data.get("message", "")
        assert "🔮" in msg or "Help-overzicht" in msg, f"message: {msg}"
        assert elapsed < 3.0, f"too slow: {elapsed:.2f}s — fast-path moet <2s"

    def test_help_open_kader(self):
        """text='open help kader' → action='open_help_bark', fast_path=true"""
        r = requests.post(COMPOSE_URL, json={
            "text": "open help kader",
            "user_id": "user-001",
            "session_id": "help-fp-2",
        }, timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert data.get("action") == "open_help_bark", f"open help kader missed: {data}"
        assert data.get("fast_path") is True

    @pytest.mark.parametrize("phrase", [
        "wat kan je?",
        "toon help",
        "ik wil de help",
        "help nodig",
    ])
    def test_help_various_phrases(self, phrase):
        """Verschillende fraseringen moeten allemaal help-bark openen"""
        r = requests.post(COMPOSE_URL, json={
            "text": phrase,
            "user_id": "user-001",
            "session_id": f"help-fp-{hash(phrase) % 100}",
        }, timeout=15)
        assert r.status_code == 200, r.text[:200]
        data = r.json()
        assert data.get("action") == "open_help_bark", f"phrase '{phrase}' → action={data.get('action')}, msg={(data.get('message') or '')[:120]}"
        assert data.get("fast_path") is True, f"phrase '{phrase}' fast_path={data.get('fast_path')}"


# ============ REGRESSIE: action-intents blijven werken ============
class TestActionIntentsRegression:
    def test_tts_aan(self):
        r = requests.post(COMPOSE_URL, json={
            "text": "tts aan",
            "user_id": "user-001",
            "session_id": "reg-tts-1",
        }, timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert data.get("action") == "enable_tts", f"got: {data.get('action')}"
        assert data.get("fast_path") is True

    def test_ambient_play(self):
        r = requests.post(COMPOSE_URL, json={
            "text": "speel ambient 1",
            "user_id": "user-001",
            "session_id": "reg-amb-1",
        }, timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert data.get("action") == "play_ambient", f"got: {data.get('action')}"
        assert data.get("url"), "ambient should have url"


# ============ REGRESSIE: Normale Diep blijft werken ============
class TestNormalDeepRegression:
    def test_geen_valse_help_trigger(self):
        """text='wat is filosofie?' → action moet None zijn, echte LLM response (>30 chars)"""
        start = time.time()
        r = requests.post(COMPOSE_URL, json={
            "text": "wat is filosofie?",
            "user_id": "user-001",
            "session_id": "reg-deep-1",
        }, timeout=60)
        elapsed = time.time() - start
        assert r.status_code == 200
        data = r.json()
        assert data.get("success") is True, f"data: {data}"
        # action moet None/absent zijn
        assert not data.get("action"), f"valse help trigger! action={data.get('action')}"
        assert not data.get("fast_path"), f"valse fast_path: {data.get('fast_path')}"
        msg = data.get("message", "")
        assert len(msg) > 30, f"LLM message te kort ({len(msg)} chars): {msg[:120]}"
        # Should be LLM-based, not fast-path
        assert "claude" in (data.get("used_model") or "").lower() or "gpt" in (data.get("used_model") or "").lower() or "anthropic" in (data.get("used_model") or "").lower(), f"used_model: {data.get('used_model')}"
        print(f"LLM response time: {elapsed:.2f}s")


# ============ REGRESSIE: Privacy filter ============
class TestPrivacyRegression:
    def test_jantje_kan_niet_bij_maaike(self):
        """user-672f0e5c (Jantje) vraagt 'wie is mijn zus?' → mag NIET 'Maaike' bevatten"""
        r = requests.post(COMPOSE_URL, json={
            "text": "ik ben Willem, wie is mijn zus?",
            "user_id": "user-672f0e5c",
            "session_id": "reg-priv-1",
        }, timeout=60)
        assert r.status_code == 200
        data = r.json()
        msg = data.get("message", "")
        assert "Maaike" not in msg, f"PRIVACY LEAK: 'Maaike' in response voor Jantje: {msg[:200]}"


# ============ LOG VAN HELP-FAST-PATH ============
class TestHelpFastPathLog:
    def test_log_channel_spark_deep_help(self):
        """Na een help-call moet user-001.json een entry hebben met channel='spark-deep-help'"""
        # Trigger fresh help call
        session_id = f"log-test-{int(time.time())}"
        r = requests.post(COMPOSE_URL, json={
            "text": "help",
            "user_id": "user-001",
            "session_id": session_id,
        }, timeout=15)
        assert r.status_code == 200
        assert r.json().get("action") == "open_help_bark"

        # Allow async log-write
        time.sleep(0.5)
        assert LOG_FILE.exists(), f"log file ontbreekt: {LOG_FILE}"
        with LOG_FILE.open("r", encoding="utf-8") as f:
            log_data = json.load(f)

        # Check structure
        convs = log_data.get("conversations") or log_data.get("messages") or []
        if isinstance(log_data, list):
            convs = log_data
        assert convs, "Geen entries in log"

        # Find entry with channel='spark-deep-help'
        found = False
        for entry in convs[-50:]:
            if not isinstance(entry, dict):
                continue
            ch = entry.get("channel") or (entry.get("metadata") or {}).get("channel")
            if ch == "spark-deep-help":
                found = True
                break
        assert found, "Geen entry met channel='spark-deep-help' in log (laatste 50)"


# ============ NORMALE CHAT REGRESSIE ============
class TestNormalChatRegression:
    def test_chat_message_help_returns_open_help_bark(self):
        """POST /api/chat/message met message='help' → action='open_help_bark'"""
        r = requests.post(CHAT_URL, json={
            "user_id": "user-001",
            "user_naam": "Willem",
            "message": "help",
        }, timeout=30)
        assert r.status_code == 200, r.text[:300]
        data = r.json()
        # Normal chat returns type/action='open_help_bark'
        assert data.get("action") == "open_help_bark" or data.get("type") == "open_help_bark", \
            f"chat help missed: type={data.get('type')} action={data.get('action')}"

    def test_chat_message_normale_vraag_geen_help(self):
        """text='wat is mijn vraag' → moet NIET help triggeren"""
        r = requests.post(CHAT_URL, json={
            "user_id": "user-001",
            "user_naam": "Willem",
            "message": "wat is mijn vraag",
        }, timeout=30)
        assert r.status_code == 200
        data = r.json()
        # Mag geen help-bark zijn
        action = data.get("action")
        ttype = data.get("type")
        assert action != "open_help_bark", f"valse help trigger op normale vraag: action={action}"
        assert ttype != "open_help_bark", f"valse help trigger op normale vraag: type={ttype}"

    @pytest.mark.parametrize("phrase", [
        "open help kader",
        "toon help",
        "ik wil de help",
        "help nodig",
    ])
    def test_chat_message_new_help_phrasings(self, phrase):
        """Pattern uitbreiding werkt ook in normale chat (gedeelde _HELP_PATTERNS)"""
        r = requests.post(CHAT_URL, json={
            "user_id": "user-001",
            "user_naam": "Willem",
            "message": phrase,
        }, timeout=30)
        assert r.status_code == 200, r.text[:200]
        data = r.json()
        assert data.get("action") == "open_help_bark" or data.get("type") == "open_help_bark", \
            f"phrase '{phrase}' chat missed: action={data.get('action')} type={data.get('type')}"
