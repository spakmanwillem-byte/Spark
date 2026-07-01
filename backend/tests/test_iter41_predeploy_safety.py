"""
Iteration 41 — Pre-deploy safety check
Tests critical trader-monitor OFF-state after restart + reset regression checks.
"""
import json
import os
import subprocess
import time

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://question-hub-160.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"


@pytest.fixture(scope="module")
def client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# ---------- CRITICAL: Monitor OFF after restart ----------
class TestMonitorSafety:
    """Trader-monitor MUST stay off after backend restart."""

    def test_monitor_status_before_restart(self, client):
        r = client.get(f"{API}/trade/monitor/status", timeout=15)
        assert r.status_code == 200, r.text
        body = r.json()
        data = body.get("status", body)  # unwrap
        assert data.get("running") is False, f"Monitor is running BEFORE restart: {data}"
        assert data.get("auto_trade") is False, f"auto_trade True BEFORE restart: {data}"
        assert data.get("use_mock") is False, f"use_mock True BEFORE restart: {data}"
        assert data.get("thread_alive") is False, f"thread_alive True BEFORE restart: {data}"

    def test_monitor_state_file_persisted_false(self):
        with open("/app/backend/data/trade/monitor_state.json") as f:
            state = json.load(f)
        assert state["running"] is False
        assert state["auto_trade"] is False
        assert state["use_mock"] is False
        assert state["interval"] == 900
        assert state["market"] == "BCH-EUR"
        assert state["candle_interval"] == "1h"

    def test_monitor_off_after_supervisor_restart(self, client):
        # Restart backend
        result = subprocess.run(
            ["sudo", "supervisorctl", "restart", "backend"],
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0, f"Restart failed: {result.stderr}"
        # Wait for backend up (with retries)
        deadline = time.time() + 40
        last_err = None
        while time.time() < deadline:
            try:
                r = client.get(f"{API}/trade/monitor/status", timeout=8)
                if r.status_code == 200:
                    break
            except Exception as e:
                last_err = e
            time.sleep(1.5)
        else:
            pytest.fail(f"Backend never came back up: {last_err}")

        # KEY ASSERTION: monitor must still be OFF
        body = r.json()
        data = body.get("status", body)
        assert data.get("running") is False, f"CRITICAL: Monitor auto-started after restart: {data}"
        assert data.get("auto_trade") is False, f"CRITICAL: auto_trade True after restart: {data}"
        assert data.get("use_mock") is False
        assert data.get("thread_alive") is False, f"CRITICAL: thread alive after restart: {data}"


# ---------- Potjes reset ----------
class TestPotjesReset:
    def test_potjes_user_000(self, client):
        r = client.get(f"{API}/trade/potjes/user-000", timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        pots = data.get("potjes") or data.get("pots") or []
        # Endpoint may wrap differently — accept either shape
        if not pots and isinstance(data, dict) and "user_id" in data:
            pots = data.get("potjes", [])
        assert len(pots) == 10, f"Expected 10 pots, got {len(pots)}: {data}"
        total = sum(p.get("capital", 0) for p in pots)
        assert abs(total - 50.80) < 0.01, f"Expected 50.80, got {total}"
        # pot-001 or index 0 locked as staking_anchor
        locked = [p for p in pots if p.get("pot_locked")]
        assert len(locked) == 1
        assert locked[0].get("lock_reason") == "staking_anchor"
        # All BCH-EUR
        assert all(p.get("market") == "BCH-EUR" for p in pots)
        # Empty trade_log
        assert all(len(p.get("trade_log", [])) == 0 for p in pots)

    def test_potjes_user_001(self, client):
        r = client.get(f"{API}/trade/potjes/user-001", timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        pots = data.get("potjes") or data.get("pots") or []
        assert len(pots) == 10
        total = sum(p.get("capital", 0) for p in pots)
        assert abs(total - 50.80) < 0.01
        assert not any(p.get("pot_locked") for p in pots)
        assert all(p.get("market") == "BCH-EUR" for p in pots)
        assert all(len(p.get("trade_log", [])) == 0 for p in pots)

    def test_potjes_user_a0ee2d7e(self, client):
        r = client.get(f"{API}/trade/potjes/user-a0ee2d7e", timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        pots = data.get("potjes") or data.get("pots") or []
        assert len(pots) == 2
        total = sum(p.get("capital", 0) for p in pots)
        assert abs(total - 20.80) < 0.01
        assert not any(p.get("pot_locked") for p in pots)
        assert all(p.get("market") == "BCH-EUR" for p in pots)
        assert all(len(p.get("trade_log", [])) == 0 for p in pots)

    def test_legacy_users_removed_from_file(self):
        # NOTE: run BEFORE endpoint test — the GET endpoint auto-creates users
        with open("/app/backend/data/financial/user_potjes.json") as f:
            d = json.load(f)
        users = d.get("users", {})
        for legacy in ["user-1996fa59", "user-c609d7d1", "user-5dd295db", "user-4d9b59aa"]:
            assert legacy not in users, f"Legacy user {legacy} still in potjes file"

    def test_zzz_legacy_user_endpoint_returns_empty_or_zero(self, client):
        # This runs LAST (zzz prefix) because it may auto-create a user
        r = client.get(f"{API}/trade/potjes/user-1996fa59", timeout=15)
        # Accept 200 with 0 pots OR 404 OR empty response
        assert r.status_code in (200, 404)
        if r.status_code == 200:
            data = r.json()
            pots = data.get("potjes") or data.get("pots") or []
            assert len(pots) == 0, f"Legacy user still has pots: {data}"


# ---------- ROAR balances ----------
class TestRoarBalances:
    def test_roar_file_correct(self):
        with open("/app/backend/data/roar/roar_balances.json") as f:
            d = json.load(f)
        bals = d.get("balances", {})
        assert bals.get("user-000") == 10
        assert bals.get("user-001") == 10
        assert bals.get("user-a0ee2d7e") == 2
        # Legacy should be 0
        for legacy in ["user-c609d7d1", "user-1996fa59", "user-5dd295db", "user-4d9b59aa"]:
            assert bals.get(legacy, 0) == 0, f"{legacy} balance: {bals.get(legacy)}"

    def test_roar_supply_via_api(self, client):
        # Try common endpoints
        for path in ["/roar/supply", "/roar/stats", "/roar/balances", "/roar/info"]:
            r = client.get(f"{API}{path}", timeout=10)
            if r.status_code == 200:
                data = r.json()
                # Look for keys
                total = data.get("total_supply") or data.get("supply")
                treasury = data.get("treasury_pool") or data.get("treasury")
                circulating = data.get("circulating")
                if total is not None:
                    assert total == 1000000
                if treasury is not None:
                    assert treasury == 999978
                if circulating is not None:
                    assert circulating == 22
                return
        pytest.skip("No ROAR supply endpoint found; file check already passed")


# ---------- Bitvavo live ----------
class TestBitvavo:
    def test_bitvavo_balance_user_001(self, client):
        r = client.get(f"{API}/trade/bitvavo/balance/user-001", timeout=30)
        # Live API — 4xx/5xx acceptable but recorded
        if r.status_code != 200:
            pytest.skip(f"Bitvavo live API returned {r.status_code}: {r.text[:200]}")
        data = r.json()
        assert data.get("success") is True, f"Bitvavo returned success=false: {data}"
        # EUR balance ~ 122.40 (allow small delta due to live prices)
        balances = data.get("balances") or data.get("balance") or []
        # find EUR entry
        eur_val = None
        if isinstance(balances, list):
            for b in balances:
                sym = b.get("symbol") or b.get("currency") or b.get("asset")
                if sym == "EUR":
                    eur_val = float(b.get("available") or b.get("amount") or b.get("balance") or 0)
                    break
        elif isinstance(balances, dict):
            eur_val = float(balances.get("EUR", {}).get("available", 0) if isinstance(balances.get("EUR"), dict) else balances.get("EUR", 0))
        if eur_val is not None:
            assert eur_val > 0, f"EUR balance is 0: {data}"


# ---------- Daily event ----------
class TestDailyEvent:
    def test_daily_event_play(self, client):
        # Reset today entry
        try:
            with open("/app/backend/data/dnd/daily_events.json") as f:
                de = json.load(f)
            from datetime import date
            today = date.today().isoformat()
            # de may be nested; try both shapes
            if isinstance(de, dict):
                changed = False
                # remove any entry keyed by today for user-001
                for k in list(de.keys()):
                    if today in str(k) and "user-001" in str(k):
                        del de[k]
                        changed = True
                # or nested: de['user-001'][today]
                if "user-001" in de and isinstance(de["user-001"], dict) and today in de["user-001"]:
                    del de["user-001"][today]
                    changed = True
                if changed:
                    with open("/app/backend/data/dnd/daily_events.json", "w") as f:
                        json.dump(de, f, indent=2)
        except FileNotFoundError:
            pass

        r = client.post(f"{API}/dnd/daily-event/user-001/play", json={"choice": "steen"}, timeout=15)
        # 200 (played) OR 400 (already played) acceptable
        assert r.status_code in (200, 400), f"Unexpected status: {r.status_code} {r.text}"
        if r.status_code == 200:
            data = r.json()
            # Should contain outcome/result
            assert any(k in data for k in ["result", "outcome", "won", "success", "reward"])


# ---------- Chat routes refactor ----------
class TestChatRoutes:
    def test_chat_message(self, client):
        payload = {
            "user_id": "user-001",
            "user_naam": "Willem",
            "message": "test",
            "channel": "spark",
        }
        r = client.post(f"{API}/chat/message", json=payload, timeout=30)
        assert r.status_code == 200, f"Chat message failed: {r.status_code} {r.text[:500]}"
        data = r.json()
        # Response envelope check — must have message somewhere
        has_msg = (
            "message" in data
            or "response" in data
            or ("response" in data and isinstance(data.get("response"), dict) and "message" in data["response"])
        )
        assert has_msg, f"No message field in response: {data}"


# ---------- DnD character stats spend ----------
class TestDndStats:
    def test_stat_spend_kracht(self, client):
        # Get baseline first
        r0 = client.get(f"{API}/dnd/character/user-001", timeout=15)
        if r0.status_code != 200:
            pytest.skip(f"Cannot get baseline: {r0.status_code}")
        baseline = r0.json()
        stats_before = baseline.get("stats") or {}
        kracht_before = stats_before.get("Kracht", 0) if isinstance(stats_before, dict) else 0
        points_before = (baseline.get("stat_points") or {}).get("available", 0)

        r = client.post(f"{API}/dnd/character/user-001/stats/spend", json={"stat_name": "Kracht"}, timeout=15)
        if r.status_code == 400:
            # Maybe no points available
            pytest.skip(f"No points available: {r.text}")
        assert r.status_code == 200, f"Spend failed: {r.status_code} {r.text}"

        # Verify increment
        r2 = client.get(f"{API}/dnd/character/user-001", timeout=15)
        assert r2.status_code == 200
        after = r2.json()
        stats_after = after.get("stats") or {}
        kracht_after = stats_after.get("Kracht", 0) if isinstance(stats_after, dict) else 0
        points_after = (after.get("stat_points") or {}).get("available", 0)
        assert kracht_after == kracht_before + 1, f"Kracht not incremented: {kracht_before} -> {kracht_after}"
        assert points_after == points_before - 1, f"Points not decremented"

    def test_stat_spend_geluk_cap(self, client):
        # Try to spend on Geluk many times; should cap at 25 with 400
        for _ in range(30):
            r = client.post(f"{API}/dnd/character/user-001/stats/spend", json={"stat_name": "Geluk"}, timeout=10)
            if r.status_code == 400:
                # Cap or no points — acceptable
                body = r.text.lower()
                # Could be either cap or no-points; both are 400
                assert "geluk" in body or "cap" in body or "max" in body or "punt" in body or "point" in body or "beschikbaar" in body, f"400 without recognizable reason: {r.text}"
                return
            elif r.status_code != 200:
                pytest.fail(f"Unexpected status: {r.status_code} {r.text}")
        # If we never hit 400, that's a bug
        pytest.fail("Geluk cap never enforced after 30 spends")


# ---------- Items blueprint ----------
class TestItemsBlueprint:
    EXPECTED = {"brood", "koekje", "vlees", "worst", "appel", "vis", "kaas", "graan",
                "handzwaard", "schild", "helende_kruiden", "healing_potion",
                "kamer", "maaltijd", "recipe_vissen"}

    def test_items_blueprint_list(self, client):
        r = client.get(f"{API}/dnd/spark-world/items-blueprint", timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        # data could be list, dict of items, or wrapped
        items = data.get("items") if isinstance(data, dict) and "items" in data else data
        if isinstance(items, dict):
            ids = set(items.keys())
        elif isinstance(items, list):
            ids = {(i.get("id") or i.get("name") or i.get("key") or "").lower() for i in items}
        else:
            pytest.fail(f"Unexpected shape: {type(items)}")
        # Check all expected present
        missing = self.EXPECTED - ids
        assert len(ids) == 15, f"Expected 15 items, got {len(ids)}: {ids}"
        assert not missing, f"Missing items: {missing}"

    def test_items_blueprint_brood(self, client):
        r = client.get(f"{API}/dnd/spark-world/items-blueprint/brood", timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        # naam=Brood, weight_kg=0.3
        naam = data.get("naam") or data.get("name")
        assert naam == "Brood", f"Naam mismatch: {naam}"
        weight = data.get("weight_kg") or data.get("weight")
        assert abs(float(weight) - 0.3) < 0.001, f"weight_kg mismatch: {weight}"
