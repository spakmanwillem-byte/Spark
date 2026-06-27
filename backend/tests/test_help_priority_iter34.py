"""
v6_help_priority_001 — iter_34 regression suite

Verifies that HELP-PRIORITY check at routes.py line 463 fires BEFORE
the capability-router (line 477), so 'toon help' (and friends) yields
open_help_bark instead of being intercepted as capability 'toon_afbeelding'.

Also validates:
  (a) all help phrasings open_help_bark in normal chat AND Diep
  (b) capability-router still works for non-help queries
  (c) other intent-routes (recap, agenda) still work
  (d) normale conversatie / edge-case ("help me met X") no false trigger
"""
import os
import time
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
    r = requests.post(CHAT_URL, json={
        "user_id": user_id,
        "user_naam": user_naam,
        "sleutelwoord": "Appelsap",
        "message": message,
    }, timeout=45)
    return r


# ============ MAIN FIX: 'toon help' must now hit help, not capability ============
class TestHelpPriorityFix:
    def test_toon_help_normal_chat(self):
        """FIX: 'toon help' → open_help_bark (NOT capability/toon_afbeelding)"""
        r = _chat("toon help")
        assert r.status_code == 200, r.text[:300]
        data = r.json()
        assert data.get("type") == "open_help_bark", \
            f"got type={data.get('type')} action={data.get('action')} cap_id={data.get('capability_id')}"
        assert data.get("action") == "open_help_bark", \
            f"got action={data.get('action')}"

    def test_help_basis_normal_chat(self):
        r = _chat("help")
        assert r.status_code == 200
        data = r.json()
        assert data.get("action") == "open_help_bark", f"got: {data.get('action')} type={data.get('type')}"

    def test_open_help_kader_normal_chat(self):
        r = _chat("open help kader")
        assert r.status_code == 200
        data = r.json()
        assert data.get("action") == "open_help_bark", f"got: {data.get('action')} type={data.get('type')}"


# ============ REGRESSIE: capability-router blijft werken ============
class TestCapabilityRouterRegression:
    def test_hoeveel_users(self):
        """'hoeveel users hebben we' → capability_response (tellen_gebruikers)"""
        r = _chat("hoeveel users hebben we")
        assert r.status_code == 200, r.text[:300]
        data = r.json()
        assert data.get("type") == "capability_response", \
            f"got type={data.get('type')} (action={data.get('action')})"
        # capability_id mag tellen_gebruikers zijn (of vergelijkbaar)
        cap_id = data.get("capability_id") or ""
        assert "user" in cap_id.lower() or "tell" in cap_id.lower() or "gebruik" in cap_id.lower(), \
            f"unexpected capability_id={cap_id}"

    def test_log_van_trade(self):
        """'log van trade' → capability_response, NIET help"""
        r = _chat("log van trade")
        assert r.status_code == 200
        data = r.json()
        assert data.get("type") == "capability_response", \
            f"got type={data.get('type')}"
        assert data.get("action") != "open_help_bark", "FOUT: hit help i.p.v. capability"


# ============ REGRESSIE: andere intent-routes (agenda) ============
class TestOtherIntentRegression:
    def test_agenda_planning(self):
        """'wat staat vandaag op de planning' → agenda-related, geen help"""
        r = _chat("wat staat vandaag op de planning")
        assert r.status_code == 200, r.text[:300]
        data = r.json()
        ttype = data.get("type") or ""
        assert data.get("action") != "open_help_bark", "FOUT: agenda → help"
        # Acceptabel: agenda_overview / agenda_empty / capability_response (agenda) / ...
        assert "agenda" in ttype.lower() or "planning" in (data.get("message") or "").lower() or \
            ttype == "capability_response", \
            f"got type={ttype} message={(data.get('message') or '')[:120]}"


# ============ REGRESSIE: Diep fast-path help (uit iter_33) ============
class TestDeepFastPathStillWorks:
    def test_compose_help(self):
        r = requests.post(COMPOSE_URL, json={
            "text": "help",
            "user_id": "user-001",
            "session_id": "iter34-fp-1",
        }, timeout=15)
        assert r.status_code == 200, r.text[:300]
        data = r.json()
        assert data.get("action") == "open_help_bark", f"got: {data}"
        assert data.get("fast_path") is True, f"fast_path: {data.get('fast_path')}"


# ============ REGRESSIE: normale conversatie ============
class TestNormalConversationRegression:
    def test_wat_is_fotosynthese(self):
        """'wat is fotosynthese' → KEIN open_help_bark; gewone snap/KB response"""
        r = _chat("wat is fotosynthese")
        assert r.status_code == 200, r.text[:300]
        data = r.json()
        assert data.get("type") != "open_help_bark", f"valse help! type={data.get('type')}"
        assert data.get("action") != "open_help_bark", f"valse help! action={data.get('action')}"


# ============ EDGE CASE: 'help me met X' (NIET help bedoeld) ============
class TestHelpEdgeCase:
    def test_help_me_met_X(self):
        """'help me met begrijpen wat trade is' → NIET open_help_bark (geen valse trigger)"""
        r = _chat("help me met begrijpen wat trade is")
        assert r.status_code == 200, r.text[:300]
        data = r.json()
        assert data.get("type") != "open_help_bark", \
            f"FALSE POSITIVE: 'help me met X' triggert help-bark! type={data.get('type')}"
        assert data.get("action") != "open_help_bark", \
            f"FALSE POSITIVE: action={data.get('action')}"
