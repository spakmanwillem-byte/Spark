"""Unit-test voor v6_resume_persist_merge_001 — registry-persist merge i.p.v. overwrite.

Bug die we fixen:
- Backend restart → `_registry` (in-memory) is leeg
- User stopt 1 bot via UI → `stop()` zet `running=False` → `_persist_registry()` schrijft
  bestand met ALLEEN die ene bot (anderen verdwijnen)
- Volgende restart → resume_registry_bots() vindt geen running bots → niks resumed

Fix: `_persist_registry()` mergt nu met bestaand bestand i.p.v. te overschrijven.
"""
import json
import sys
from pathlib import Path

# Zorg dat backend modules importable zijn
BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

from modules.trade import monitor as mon  # noqa: E402


def _reset_registry():
    """Helper: leeg de in-memory registry tussen tests."""
    with mon._registry_lock:
        mon._registry.clear()


def test_persist_merges_with_existing_file(tmp_path, monkeypatch):
    """Als er al 3 bots in het bestand staan en _registry heeft alleen bot A,
    moet het bestand na _persist_registry() nog steeds alle 3 bots bevatten."""
    fake_state = tmp_path / "bots_registry_state.json"
    monkeypatch.setattr(mon, "REGISTRY_STATE_FILE", fake_state)
    _reset_registry()

    # Setup: bestand bevat 3 bots (running)
    fake_state.write_text(json.dumps({
        "bots": [
            {"user_id": "user-A", "running": True, "interval": 30, "market": "BTC-EUR",
             "markets": ["BTC-EUR"], "candle_interval": "1h", "auto_trade": True,
             "trade_amount": 10.0, "use_mock": False, "use_potjes": True, "pot_count": 5},
            {"user_id": "user-B", "running": True, "interval": 30, "market": "ETH-EUR",
             "markets": ["ETH-EUR"], "candle_interval": "1h", "auto_trade": True,
             "trade_amount": 10.0, "use_mock": False, "use_potjes": True, "pot_count": 3},
            {"user_id": "user-C", "running": True, "interval": 30, "market": "ADA-EUR",
             "markets": ["ADA-EUR"], "candle_interval": "1h", "auto_trade": True,
             "trade_amount": 10.0, "use_mock": False, "use_potjes": True, "pot_count": 2},
        ]
    }))

    # Simuleer dat alleen user-A in-memory is en gestopt wordt
    m_a = mon.get_user_monitor("user-A")
    m_a._running = False
    m_a._markets = ["BTC-EUR"]
    m_a._market = "BTC-EUR"

    mon._persist_registry()

    data = json.loads(fake_state.read_text())
    uids = sorted(b["user_id"] for b in data["bots"])
    assert uids == ["user-A", "user-B", "user-C"], f"Expected all 3 bots preserved, got: {uids}"

    by_uid = {b["user_id"]: b for b in data["bots"]}
    assert by_uid["user-A"]["running"] is False, "user-A should be marked stopped"
    assert by_uid["user-B"]["running"] is True, "user-B should remain running"
    assert by_uid["user-C"]["running"] is True, "user-C should remain running"

    _reset_registry()


def test_resume_skips_stopped_bots(tmp_path, monkeypatch):
    """resume_registry_bots() moet bots met running:false skippen, andere starten."""
    fake_state = tmp_path / "bots_registry_state.json"
    monkeypatch.setattr(mon, "REGISTRY_STATE_FILE", fake_state)
    _reset_registry()

    fake_state.write_text(json.dumps({
        "bots": [
            {"user_id": "user-stopped", "running": False, "interval": 30,
             "market": "BTC-EUR", "markets": ["BTC-EUR"], "candle_interval": "1h",
             "auto_trade": True, "trade_amount": 10.0, "use_mock": False,
             "use_potjes": True, "pot_count": 1},
        ]
    }))

    # Mock m.start() zodat we geen echte thread starten
    started_calls = []
    orig_start = mon.MonitorService.start

    def fake_start(self, **kwargs):
        started_calls.append(self._user_id)
        self._running = True
        return {"success": True}

    monkeypatch.setattr(mon.MonitorService, "start", fake_start)

    try:
        result = mon.resume_registry_bots()
        assert result["resumed"] == 0
        assert "user-stopped" in result.get("skipped_user_stopped", [])
        assert started_calls == [], f"No bots should have started, got: {started_calls}"
    finally:
        monkeypatch.setattr(mon.MonitorService, "start", orig_start)
        _reset_registry()


def test_resume_starts_running_bots(tmp_path, monkeypatch):
    """Bots met running:true moeten m.start() krijgen."""
    fake_state = tmp_path / "bots_registry_state.json"
    monkeypatch.setattr(mon, "REGISTRY_STATE_FILE", fake_state)
    _reset_registry()

    fake_state.write_text(json.dumps({
        "bots": [
            {"user_id": "user-running-1", "running": True, "interval": 30,
             "market": "BTC-EUR", "markets": ["BTC-EUR"], "candle_interval": "1h",
             "auto_trade": True, "trade_amount": 10.0, "use_mock": False,
             "use_potjes": True, "pot_count": 1},
            {"user_id": "user-running-2", "running": True, "interval": 60,
             "market": "ETH-EUR", "markets": ["ETH-EUR"], "candle_interval": "15m",
             "auto_trade": True, "trade_amount": 10.0, "use_mock": False,
             "use_potjes": True, "pot_count": 2},
        ]
    }))

    started_calls = []

    def fake_start(self, **kwargs):
        started_calls.append(self._user_id)
        self._running = True
        return {"success": True}

    orig_start = mon.MonitorService.start
    monkeypatch.setattr(mon.MonitorService, "start", fake_start)

    try:
        result = mon.resume_registry_bots()
        assert result["resumed"] == 2, f"Expected 2 resumed, got: {result}"
        assert sorted(started_calls) == ["user-running-1", "user-running-2"]
    finally:
        monkeypatch.setattr(mon.MonitorService, "start", orig_start)
        _reset_registry()
