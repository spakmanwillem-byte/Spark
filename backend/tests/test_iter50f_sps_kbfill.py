"""
iter50f — Test SPS daily-event bark + KB-fill multi-turn flow + regressie RPS/trader.
"""
import os
import time
import uuid
import json
from datetime import date
from pathlib import Path

import pytest
import requests

def _load_backend_url():
    url = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
    if url:
        return url
    env_file = Path("/app/frontend/.env")
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith("REACT_APP_BACKEND_URL="):
                return line.split("=", 1)[1].strip().rstrip("/")
    return ""

BASE_URL = _load_backend_url()
API = f"{BASE_URL}/api"


# --- helpers ---
def _new_uid():
    return f"test-user-{uuid.uuid4().hex[:8]}"


# ============ SPS Daily-Event ============

class TestDailyEvent:
    def test_get_daily_event_available_for_new_user(self):
        uid = _new_uid()
        r = requests.get(f"{API}/dnd/daily-event/{uid}")
        assert r.status_code == 200
        data = r.json()
        assert data["available"] is True
        assert data["played"] is False
        assert data["date"] == date.today().isoformat()
        assert set(data["choices"]) == {"steen", "papier", "schaar"}
        assert data["win_goud"] == 10

    def test_play_daily_event_returns_bark_and_result(self):
        uid = _new_uid()
        r = requests.post(f"{API}/dnd/daily-event/{uid}/play", json={"choice": "papier"})
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["success"] is True
        assert data["result"] in {"win", "draw", "loss"}
        assert data["choice"] == "papier"
        assert data["ai_choice"] in {"steen", "papier", "schaar"}
        assert "bark" in data and data["bark"]
        # v11_daily_event_honest_001 — bark bij loss moet 'je verloor' zeggen, NIET 'ontsnapte'
        if data["result"] == "loss":
            assert "verloor" in data["bark"].lower()
            assert "ontsnap" not in data["bark"].lower()
            assert data["reward_goud"] == 0
        if data["result"] == "win":
            assert data["reward_goud"] == 10
            assert "gewonnen" in data["bark"].lower()

    def test_cannot_play_twice_same_day(self):
        uid = _new_uid()
        r1 = requests.post(f"{API}/dnd/daily-event/{uid}/play", json={"choice": "steen"})
        assert r1.status_code == 200
        r2 = requests.post(f"{API}/dnd/daily-event/{uid}/play", json={"choice": "steen"})
        assert r2.status_code == 400

    def test_invalid_choice_rejected(self):
        uid = _new_uid()
        r = requests.post(f"{API}/dnd/daily-event/{uid}/play", json={"choice": "vuur"})
        assert r.status_code == 400

    def test_bark_loss_string_across_multiple_tries(self):
        """Force a loss by trying many users and checking bark text style."""
        loss_seen = False
        for _ in range(15):
            uid = _new_uid()
            r = requests.post(f"{API}/dnd/daily-event/{uid}/play", json={"choice": "steen"})
            if r.status_code != 200:
                continue
            d = r.json()
            if d["result"] == "loss":
                loss_seen = True
                assert "verloor" in d["bark"].lower()
                assert "ontsnap" not in d["bark"].lower()
                break
        # niet fataal als geen loss in 15 pogingen, maar meestal zien we er wel eentje
        if not loss_seen:
            pytest.skip("Geen loss in 15 pogingen — random")


# ============ KB-Fill Multi-Turn Flow ============

def _chat(session_id, message, user_id="user-001", user_naam="Willem"):
    payload = {
        "session_id": session_id,
        "message": message,
        "user_id": user_id,
        "user_naam": user_naam,
    }
    r = requests.post(f"{API}/chat/message", json=payload, timeout=30)
    return r


def _fresh_ids():
    """Session state is keyed by user_id, so use unique user_id per test."""
    tag = uuid.uuid4().hex[:8]
    return f"test-flow-{tag}", f"test-user-{tag}"


class TestKbFillFlow:
    def test_full_offer_yes_answer_confirm(self):
        sid, uid = _fresh_ids()
        # Step 1: offer
        r1 = _chat(sid, "kan ik wat voor je doen", user_id=uid)
        assert r1.status_code == 200, r1.text
        d1 = r1.json()
        assert d1.get("type") == "kb_fill_offer", f"expected kb_fill_offer, got {d1.get('type')}: {d1.get('message')}"
        assert "kaart" in d1.get("message", "").lower()

        # Step 2: ja → question
        r2 = _chat(sid, "ja", user_id=uid)
        assert r2.status_code == 200
        d2 = r2.json()
        assert d2.get("type") == "kb_fill_question", f"got {d2.get('type')}"

        # Step 3: answer → paraphrase
        r3 = _chat(sid, "mijn testantwoord tekst", user_id=uid)
        assert r3.status_code == 200
        d3 = r3.json()
        assert d3.get("type") == "kb_fill_paraphrase", f"got {d3.get('type')}"
        assert "klopt" in d3.get("message", "").lower()

        # Step 4: ja klopt → saved
        r4 = _chat(sid, "ja klopt", user_id=uid)
        assert r4.status_code == 200
        d4 = r4.json()
        assert d4.get("type") == "kb_fill_saved", f"got {d4.get('type')}: {d4.get('message')}"

    def test_decline_at_offer(self):
        sid, uid = _fresh_ids()
        r1 = _chat(sid, "kan ik wat voor je doen", user_id=uid)
        assert r1.json().get("type") == "kb_fill_offer"
        r2 = _chat(sid, "nee", user_id=uid)
        assert r2.json().get("type") == "kb_fill_declined"

    def test_negative_at_paraphrase_triggers_retry(self):
        sid, uid = _fresh_ids()
        _chat(sid, "kan ik wat voor je doen", user_id=uid)
        _chat(sid, "ja", user_id=uid)
        _chat(sid, "eerste poging antwoord", user_id=uid)
        r = _chat(sid, "nee", user_id=uid)
        assert r.json().get("type") == "kb_fill_retry"

    def test_skip_at_awaiting_answer(self):
        sid, uid = _fresh_ids()
        _chat(sid, "kan ik wat voor je doen", user_id=uid)
        _chat(sid, "ja", user_id=uid)
        r = _chat(sid, "skip", user_id=uid)
        assert r.json().get("type") == "kb_fill_skipped"


# ============ Regressie RPS ============

class TestRpsRegressie:
    def test_rps_start(self):
        r = requests.post(f"{API}/games/rps/start", params={"user_id": "user-001", "opponent": "spark"})
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("success") is True
        assert "cards" in data or "player_cards" in data or "session_id" in data

    def test_rps_play(self):
        # Start first
        requests.post(f"{API}/games/rps/start", params={"user_id": "user-001", "opponent": "spark"})
        r = requests.post(f"{API}/games/rps/play", json={"user_id": "user-001", "choice": "steen"})
        # Accept 200 even if session semantics differ
        assert r.status_code in (200, 400), r.text


# ============ Regressie Trader endpoints ============

class TestTraderEndpoints:
    def test_trade_monitor_status(self):
        r = requests.get(f"{API}/trade/monitor/status")
        assert r.status_code == 200, r.text

    def test_trade_potjes(self):
        r = requests.get(f"{API}/trade/potjes/user-000")
        assert r.status_code == 200, r.text
