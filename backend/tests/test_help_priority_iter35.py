"""
v6_help_patterns_strict_001 — iter_35 regression suite

Verifies that the _HELP_PATTERNS regex in smart_intents_service.py:227 is now
STRICT (`^\\s*/?help[\\s.!?]*$`), removing the false-positive that triggered
open_help_bark for phrases starting with "help " followed by a word.

Required to PASS in this iteration:
  (A) False-positives WEG:
       1. "help me met begrijpen wat trade is" → NIET open_help_bark
       2. "help haar even met de auto"        → NIET open_help_bark
       3. "help mij Spark, ik snap dit niet"  → NIET open_help_bark
  (B) Positives BEHOUDEN:
       4. "help" / "help." / "help!" / "Help?" / "/help" → open_help_bark
       5. Natural phrasings: "open help kader", "ik wil de help",
          "wat kan je?", "toon help", "help nodig" → open_help_bark
  (C) Regressies:
       6. /api/spark/compose with text="help" → action=open_help_bark fast_path=true
       7. /api/chat/message "hoeveel users hebben we" → capability_response
"""
import os
import pytest
import requests
from pathlib import Path

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    fp = Path("/app/frontend/.env")
    if fp.exists():
        for line in fp.read_text().splitlines():
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip().rstrip("/")
                break
assert BASE_URL, "REACT_APP_BACKEND_URL niet gezet"

CHAT_URL = f"{BASE_URL}/api/chat/message"
COMPOSE_URL = f"{BASE_URL}/api/spark/compose"


def _chat(message, user_id="user-001", user_naam="Willem"):
    return requests.post(CHAT_URL, json={
        "user_id": user_id,
        "user_naam": user_naam,
        "sleutelwoord": "Appelsap",
        "message": message,
    }, timeout=45)


def _is_help_response(data: dict) -> bool:
    return data.get("type") == "open_help_bark" or data.get("action") == "open_help_bark"


# ============ (A) FALSE-POSITIVES WEG — MAIN FIX ============
class TestFalsePositivesGone:
    def test_help_me_met_X(self):
        """'help me met begrijpen wat trade is' → NIET open_help_bark"""
        r = _chat("help me met begrijpen wat trade is")
        assert r.status_code == 200, r.text[:300]
        data = r.json()
        assert not _is_help_response(data), \
            f"FALSE POSITIVE: type={data.get('type')} action={data.get('action')}"

    def test_help_haar_even(self):
        """'help haar even met de auto' → NIET open_help_bark"""
        r = _chat("help haar even met de auto")
        assert r.status_code == 200, r.text[:300]
        data = r.json()
        assert not _is_help_response(data), \
            f"FALSE POSITIVE: type={data.get('type')} action={data.get('action')}"

    def test_help_mij_spark(self):
        """'help mij Spark, ik snap dit niet' → NIET open_help_bark"""
        r = _chat("help mij Spark, ik snap dit niet")
        assert r.status_code == 200, r.text[:300]
        data = r.json()
        assert not _is_help_response(data), \
            f"FALSE POSITIVE: type={data.get('type')} action={data.get('action')}"


# ============ (B) POSITIVES BEHOUDEN — exact 'help' + leestekens ============
class TestExactHelpPositives:
    def test_help_basis(self):
        r = _chat("help")
        assert r.status_code == 200, r.text[:300]
        data = r.json()
        assert _is_help_response(data), \
            f"missed positive: type={data.get('type')} action={data.get('action')}"

    def test_help_dot(self):
        r = _chat("help.")
        data = r.json()
        assert _is_help_response(data), f"missed: {data.get('type')} / {data.get('action')}"

    def test_help_exclaim(self):
        r = _chat("help!")
        data = r.json()
        assert _is_help_response(data), f"missed: {data.get('type')} / {data.get('action')}"

    def test_help_question(self):
        r = _chat("Help?")
        data = r.json()
        assert _is_help_response(data), f"missed: {data.get('type')} / {data.get('action')}"

    def test_slash_help(self):
        r = _chat("/help")
        data = r.json()
        assert _is_help_response(data), f"missed: {data.get('type')} / {data.get('action')}"


# ============ (B) POSITIVES BEHOUDEN — natuurlijke fraseringen ============
class TestNaturalPhrasingPositives:
    def test_open_help_kader(self):
        r = _chat("open help kader")
        data = r.json()
        assert _is_help_response(data), f"missed: {data.get('type')} / {data.get('action')}"

    def test_ik_wil_de_help(self):
        r = _chat("ik wil de help")
        data = r.json()
        assert _is_help_response(data), f"missed: {data.get('type')} / {data.get('action')}"

    def test_wat_kan_je(self):
        r = _chat("wat kan je?")
        data = r.json()
        assert _is_help_response(data), f"missed: {data.get('type')} / {data.get('action')}"

    def test_toon_help(self):
        r = _chat("toon help")
        data = r.json()
        assert _is_help_response(data), f"missed: {data.get('type')} / {data.get('action')}"

    def test_help_nodig(self):
        r = _chat("help nodig")
        data = r.json()
        assert _is_help_response(data), f"missed: {data.get('type')} / {data.get('action')}"


# ============ (C) REGRESSIE: Diep fast-path en capability-router ============
class TestRegressions:
    def test_compose_help_fastpath(self):
        r = requests.post(COMPOSE_URL, json={
            "text": "help",
            "user_id": "user-001",
            "session_id": "iter35-fp-1",
        }, timeout=15)
        assert r.status_code == 200, r.text[:300]
        data = r.json()
        assert data.get("action") == "open_help_bark", f"got: {data}"
        assert data.get("fast_path") is True, f"fast_path: {data.get('fast_path')}"

    def test_capability_hoeveel_users(self):
        r = _chat("hoeveel users hebben we")
        assert r.status_code == 200, r.text[:300]
        data = r.json()
        # NIET help
        assert not _is_help_response(data), \
            f"FOUT: capability vraag triggert help; type={data.get('type')} action={data.get('action')}"
        # Capability response (placeholder of response allebei OK)
        ttype = data.get("type") or ""
        assert ttype in ("capability_response", "capability_placeholder"), \
            f"got type={ttype} message={(data.get('message') or '')[:120]}"
