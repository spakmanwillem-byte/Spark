"""
Iteration 43 — Spark Core 2.0 trader bugfix verificatie (pre-prod redeploy).

Test scope (uit review_request):
  1. Monitor instance singleton: /api/trade/bot/status/user-001 twee keer callen → identiek
  2. MonitorService __init__ laadt config uit monitor_state.json voor user-001
  3. execute_real_trade zero-filled guard — code-inspectie in test hieronder
  4. GET /api/trade/reconcile/orphans/user-001 — nieuwe endpoint, dry-run, geen exec
  5. POST /api/trade/reconcile/orphans/user-001 met only_profit — respecteert filter
     (we roepen 'm alleen met een lege coins-lijst en only_profit=true zodat er
     effectief niets verkocht kan worden — dit test enkel schema)
  6. GET /api/trade/potjes/user-001 → 10 pots, allemaal €5,08, 0 pot_locked
  7. GET /api/trade/potjes/user-000 → 10 pots, 0 pot_locked
  8. GET /api/trade/delta → consistency_ok=true, pots/roar in sync
  9. POST /api/trade/potjes/rebalance-from-bitvavo smart mode
 10. POST rebalance-from-bitvavo met onvoldoende saldo → success:false
 11. Shadow trader endpoints geven 404
 12. Backend logs schoon (import-check via /api/health)
"""

import os
import re
from pathlib import Path

import pytest
import requests

def _load_backend_url() -> str:
    url = os.environ.get("REACT_APP_BACKEND_URL", "").strip()
    if not url:
        env = Path("/app/frontend/.env")
        if env.exists():
            for line in env.read_text().splitlines():
                if line.startswith("REACT_APP_BACKEND_URL="):
                    url = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    return url.rstrip("/")


BASE_URL = _load_backend_url()
assert BASE_URL, "REACT_APP_BACKEND_URL must be set (env or frontend/.env)"

TIMEOUT = 30


@pytest.fixture(scope="session")
def api():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# ---------- 1. Health / clean startup ----------
class TestBackendHealth:
    def test_backend_alive(self, api):
        # Root or health endpoint
        r = api.get(f"{BASE_URL}/api/health", timeout=TIMEOUT)
        assert r.status_code in (200, 404)  # 404 acceptable als endpoint niet bestaat
        # Als er 500 komt of connection error → backend gebroken
        assert r.status_code < 500

    def test_backend_err_log_clean(self):
        """Check for tracebacks in most recent backend log."""
        p = Path("/var/log/supervisor/backend.err.log")
        if not p.exists():
            pytest.skip("no backend err log")
        tail = p.read_text(errors="ignore").splitlines()[-200:]
        joined = "\n".join(tail)
        # Filter uvicorn info; check for real python tracebacks
        bad_markers = ["Traceback (most recent call last)", "ImportError", "ModuleNotFoundError"]
        for m in bad_markers:
            assert m not in joined, f"Backend err log bevat '{m}':\n{joined[-2000:]}"


# ---------- 2. Bot status singleton consistency (v7_legacy_alias_001) ----------
class TestBotStatusSingleton:
    def test_status_consistent_two_calls(self, api):
        r1 = api.get(f"{BASE_URL}/api/trade/bot/status/user-001", timeout=TIMEOUT)
        r2 = api.get(f"{BASE_URL}/api/trade/bot/status/user-001", timeout=TIMEOUT)
        assert r1.status_code == 200
        assert r2.status_code == 200
        d1 = r1.json().get("status", r1.json())
        d2 = r2.json().get("status", r2.json())

        # Kritieke velden moeten identiek zijn (singleton)
        for key in ("running", "interval", "markets", "market", "use_potjes", "user_id"):
            assert d1.get(key) == d2.get(key), (
                f"Field '{key}' verschilt tussen 2 calls: {d1.get(key)!r} vs {d2.get(key)!r}. "
                f"→ MonitorService instance mismatch (registry singleton bug!)"
            )

    def test_status_reflects_state_file(self, api):
        """v7_config_persist_on_init_001 — status moet interval/markets uit state file laden."""
        import json
        state_fp = Path("/app/backend/data/trade/monitor_state.json")
        st = json.loads(state_fp.read_text())
        r = api.get(f"{BASE_URL}/api/trade/bot/status/user-001", timeout=TIMEOUT)
        assert r.status_code == 200
        d = r.json().get("status", r.json())
        assert d["interval"] == st["interval"], (
            f"Bot status interval={d['interval']} ≠ state file interval={st['interval']} "
            "→ __init__ laadt state niet"
        )
        assert d["markets"] == st["markets"], (
            f"Bot status markets={d['markets']} ≠ state file markets={st['markets']}"
        )
        assert d["use_potjes"] == st.get("use_potjes", False)


# ---------- 3. Zero-filled guard (code inspection) ----------
class TestZeroFilledGuard:
    def test_guard_present_in_monitor(self):
        src = Path("/app/backend/modules/trade/monitor.py").read_text()
        # Guard moet return success:False + error_code:ZERO_FILLED
        assert "ZERO_FILLED" in src, "v7_zero_filled_guard_001 code missing"
        # Check ordering: guard vóór trade-registration
        idx_guard = src.find('"error_code": "ZERO_FILLED"')
        idx_trade_id = src.find("trade_id = result.get(\"orderId\"")
        assert 0 < idx_guard < idx_trade_id, "ZERO_FILLED guard moet vóór trade registration staan"
        # Check condition: filled <= 0 or filled_quote <= 0
        assert re.search(r"if\s+filled\s*<=\s*0\s+or\s+filled_quote\s*<=\s*0", src), \
            "Guard condition (filled<=0 or filled_quote<=0) niet gevonden"


# ---------- 4/5. Reconcile orphans endpoints ----------
class TestReconcileOrphans:
    def test_get_scan(self, api):
        r = api.get(f"{BASE_URL}/api/trade/reconcile/orphans/user-001", timeout=TIMEOUT)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("success") is True
        assert d.get("user_id") == "user-001"
        assert "rows" in d and isinstance(d["rows"], list)
        assert "totals" in d and isinstance(d["totals"], dict)

        # Totals schema
        t = d["totals"]
        for k in ("potential_profit_eur", "underwater_positions_eur",
                  "coins_to_sell", "coins_to_reopen", "coins_skipped"):
            assert k in t, f"totals missing key: {k}"

        # Row schema (indien rows aanwezig)
        for row in d["rows"]:
            for k in ("coin", "market", "bv_amount", "bv_value_eur", "cur_price_eur",
                      "net_paid_eur", "pnl_after_fee_eur", "proposed_action",
                      "matching_closed_pot"):
                assert k in row, f"row missing key {k}: {row}"
            assert row["proposed_action"] in ("SELL_PROFIT", "REOPEN_POT", "SKIP_DUST")

    def test_post_only_profit_filter_skips_reopen(self, api):
        """POST met only_profit=true en coins=[] — mag GEEN REOPEN_POT uitvoeren.

        We beperken met coins=['NONEXISTENT'] zodat er zeker geen echte verkoop volgt,
        maar het endpoint moet wel netjes een gestructureerd antwoord geven.
        """
        payload = {"only_profit": True, "coins": ["NONEXISTENTCOIN"]}
        r = api.post(
            f"{BASE_URL}/api/trade/reconcile/orphans/user-001",
            json=payload,
            timeout=TIMEOUT,
        )
        assert r.status_code == 200, r.text
        d = r.json()
        # Response schema check
        for k in ("executed", "skipped", "errors"):
            assert k in d, f"response missing key: {k}"
        # Met NONEXISTENT filter → executed leeg
        assert d["executed"] == [] or all(
            e.get("action") != "REOPENED" for e in d["executed"]
        ), "only_profit=true moet REOPEN acties skippen"


# ---------- 6/7. Pots layout (user-001 / user-000) ----------
class TestPots:
    def test_user001_pots(self, api):
        r = api.get(f"{BASE_URL}/api/trade/potjes/user-001", timeout=TIMEOUT)
        assert r.status_code == 200
        d = r.json()
        pots = d.get("potjes") or d.get("pots") or []
        assert len(pots) == 10, f"user-001 heeft {len(pots)} pots (verwacht 10)"
        locked = [p for p in pots if p.get("pot_locked")]
        assert len(locked) == 0, f"user-001 heeft {len(locked)} pot_locked (verwacht 0)"
        # Alle capital = €5.08 (na anchor reset)
        for p in pots:
            cap = p.get("capital")
            assert abs(float(cap) - 5.08) < 0.01, f"pot {p.get('id')} capital={cap}, verwacht 5.08"
        # Markets varieert (minimaal 1, kan meer zijn)
        markets = {p.get("market") for p in pots}
        assert len(markets) >= 1

    def test_user000_pots_no_lock(self, api):
        r = api.get(f"{BASE_URL}/api/trade/potjes/user-000", timeout=TIMEOUT)
        assert r.status_code == 200
        d = r.json()
        pots = d.get("potjes") or d.get("pots") or []
        assert len(pots) == 10, f"user-000 heeft {len(pots)} pots (verwacht 10)"
        locked = [p for p in pots if p.get("pot_locked")]
        assert len(locked) == 0, f"user-000 heeft {len(locked)} pot_locked (verwacht 0, anchor removed)"


# ---------- 8. Delta consistency ----------
class TestDelta:
    def test_delta_consistency(self, api):
        r = api.get(f"{BASE_URL}/api/trade/delta", timeout=TIMEOUT)
        assert r.status_code == 200
        d = r.json()
        # Required keys
        for k in ("pots_capital_eur", "market_value_eur", "delta_eur",
                  "dynamic_price_eur", "consistency_ok"):
            assert k in d, f"delta response missing key: {k}"
        # Consistency should be true (22 = 22 = 22)
        assert d.get("consistency_ok") is True, f"consistency_ok=false: {d}"


# ---------- 9. Rebalance-from-bitvavo smart mode ----------
class TestRebalanceSmart:
    def test_smart_mode_success(self, api):
        payload = {
            "trader_user_id": "user-001",
            "target_pot_count": 10,
            "pot_size": 5.08,
            "include_eur_liquide": True,
        }
        r = api.post(
            f"{BASE_URL}/api/trade/potjes/rebalance-from-bitvavo",
            json=payload,
            timeout=TIMEOUT,
        )
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("success") is True, f"rebalance failed: {d}"
        assert d.get("mode") == "smart_token_count", f"mode={d.get('mode')}"
        assert "treasury_overschot_eur" in d
        assert "total_available_on_bitvavo" in d
        assert d.get("target_pot_count") == 10

    def test_smart_mode_insufficient_funds(self, api):
        payload = {
            "trader_user_id": "user-001",
            "target_pot_count": 10,
            "pot_size": 1000.0,   # onmogelijk saldo
            "include_eur_liquide": True,
        }
        r = api.post(
            f"{BASE_URL}/api/trade/potjes/rebalance-from-bitvavo",
            json=payload,
            timeout=TIMEOUT,
        )
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("success") is False, "Verwacht failure bij te hoog pot_size"
        assert "total_needed" in d
        assert "total_available" in d
        assert d["total_needed"] > d["total_available"]


# ---------- 11. Shadow trader removed ----------
class TestShadowRemoved:
    @pytest.mark.parametrize("path", [
        "/api/trade/shadow/user-001",
        "/api/trade/shadow/stats/user-001",
        "/api/trade/shadow/register",
    ])
    def test_shadow_404(self, api, path):
        r = api.get(f"{BASE_URL}{path}", timeout=TIMEOUT)
        assert r.status_code == 404, f"Shadow endpoint {path} still exists (status {r.status_code})"
