"""Iteration 48 — Spark Core 2.0
Tests for:
  * Bug A (v11_pot_registration_safety_001) — buy-flow safety wrapping + ui_refresh_trigger
  * Bug C (v11_adopt_manual_positions_001) — orphan positions adoption
  * Regression: /api/trade/monitor/status + /api/trade/potjes/{user}
"""
import os
import sys
import json
import inspect
from pathlib import Path

import pytest
import requests

sys.path.insert(0, "/app/backend")

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://question-hub-160.preview.emergentagent.com").rstrip("/")
DATA_DIR = Path("/app/backend/data")


# ---------------------- Regression: endpoints ----------------------

class TestEndpointsRegression:
    def test_monitor_status_200(self):
        r = requests.get(f"{BASE_URL}/api/trade/monitor/status", timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("success") is True
        assert "status" in d
        assert "markets" in d["status"]

    def test_potjes_user000_has_7(self):
        r = requests.get(f"{BASE_URL}/api/trade/potjes/user-000", timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        pots = d.get("potjes", [])
        assert len(pots) == 7, f"expected 7 potjes, got {len(pots)}"
        open_pots = [p for p in pots if p.get("position", {}).get("is_open")]
        markets = sorted(p.get("market") for p in open_pots)
        assert markets == ["ADA-EUR", "ETH-EUR", "SOL-EUR"], markets

    def test_potjes_user001_ok(self):
        r = requests.get(f"{BASE_URL}/api/trade/potjes/user-001", timeout=15)
        assert r.status_code == 200


# ---------------------- Bug A: buy-flow safety ----------------------

class TestBugAPotRegistrationSafety:
    def test_ui_refresh_trigger_dir_writable(self):
        """ui_refresh_trigger.json is written inside DATA_DIR/trade — must be writable."""
        target_dir = DATA_DIR / "trade"
        assert target_dir.exists() and target_dir.is_dir(), f"{target_dir} missing"
        assert os.access(target_dir, os.W_OK), "trade dir not writable"

    def test_event_notifications_dir_writable(self):
        target_dir = DATA_DIR / "trade"
        assert os.access(target_dir, os.W_OK)

    def test_monitor_source_has_safety_wrap(self):
        """Verify open_cluster is wrapped in try/except and fallback+notif code paths exist."""
        src = Path("/app/backend/modules/trade/monitor.py").read_text()
        assert "v11_pot_registration_safety_001" in src
        assert "open_cluster FAILED" in src
        assert "buy_registration_failure" in src
        assert "ui_refresh_trigger.json" in src
        # open_pot fallback loop
        assert "fallback open_pot" in src or "fallback_opened" in src


# ---------------------- Bug C: orphan adoption ----------------------

class TestBugCOrphanAdoption:
    def test_methods_exist(self):
        from modules.trade.monitor import MonitorService
        assert hasattr(MonitorService, "_adopt_orphan_positions")
        assert hasattr(MonitorService, "_process_trailing_for_market")

    def test_process_trailing_signature(self):
        from modules.trade.monitor import MonitorService
        sig = inspect.signature(MonitorService._process_trailing_for_market)
        params = list(sig.parameters.keys())
        # self, market, price, pots, adopted
        assert "market" in params
        assert "price" in params
        assert "pots" in params
        assert "adopted" in params

    def test_adopt_orphan_user000_detects_orphans(self, monkeypatch):
        """Simulate MonitorService(user-000) with _markets=['BTC-EUR'] and call
        _adopt_orphan_positions. Should detect 3 orphan pots (ADA/ETH/SOL) and
        process them without raising. We stub fetch_tickers to avoid network."""
        from modules.trade import monitor as mon_mod

        calls = {"processed": []}

        def fake_fetch_tickers(symbols):
            price_map = {"ADA": 0.4, "ETH": 3000.0, "SOL": 150.0}
            return [{"market": f"{s}-EUR", "last": price_map.get(s, 1.0)} for s in symbols]

        monkeypatch.setattr(mon_mod, "fetch_tickers", fake_fetch_tickers)

        # Stub _process_trailing_for_market to just record invocations
        def fake_process(self, market, price, pots, adopted=False):
            calls["processed"].append((market, price, len(pots), adopted))

        monkeypatch.setattr(mon_mod.MonitorService, "_process_trailing_for_market", fake_process)

        svc = mon_mod.MonitorService("user-000")
        svc._markets = ["BTC-EUR"]  # force ADA/ETH/SOL to become orphans
        svc._use_potjes = True

        # Should not raise
        svc._adopt_orphan_positions({})

        processed_markets = sorted(c[0] for c in calls["processed"])
        assert processed_markets == ["ADA-EUR", "ETH-EUR", "SOL-EUR"], processed_markets
        for m, price, n_pots, adopted in calls["processed"]:
            assert adopted is True
            assert n_pots >= 1
            assert price > 0

    def test_adopt_orphan_no_open_pots_noop(self, monkeypatch):
        """If user has no open pots, _adopt_orphan_positions returns quietly."""
        from modules.trade import monitor as mon_mod
        from modules.trade import potjes as potjes_svc

        monkeypatch.setattr(potjes_svc, "get_potjes", lambda uid: {"potjes": []})
        svc = mon_mod.MonitorService("user-999-noexist")
        svc._markets = ["BTC-EUR"]
        svc._use_potjes = True
        # No exception expected
        svc._adopt_orphan_positions({})
