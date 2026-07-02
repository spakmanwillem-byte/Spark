"""
Iteration 44 — Cluster helpers + reconcile all-coins verificatie.

Test coverage:
  - GET /api/trade/reconcile/spark toont ALLE Bitvavo coins incl. orphans
  - potjes.get_next_buy_cluster returns cluster als Sigma capital >= min_order
  - potjes.open_cluster + close_cluster round-trip via test-user
  - Monitor _run_cycle BUY/SELL code paths bevatten cluster-based logica (code check)
  - GET /api/trade/delta consistency_ok, delta €11.36
  - GET /api/trade/potjes/user-001 & user-000 = 10 pots x EUR5.08
  - Regressie: bot/status endpoints en shadow endpoints
"""
import os
import sys
import json
import shutil
import pytest
import requests
from pathlib import Path

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    # fallback: read from /app/frontend/.env
    env_path = Path("/app/frontend/.env")
    for line in env_path.read_text().splitlines():
        if line.startswith("REACT_APP_BACKEND_URL="):
            BASE_URL = line.split("=", 1)[1].strip().rstrip("/")
            break

sys.path.insert(0, "/app/backend")

POTJES_FILE = Path("/app/backend/data/financial/user_potjes.json")


@pytest.fixture(scope="module")
def api():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# =============================================================================
# 1. Sanity: delta, pots per user, reconcile/spark
# =============================================================================
class TestBaseline:
    def test_delta_consistency(self, api):
        r = api.get(f"{BASE_URL}/api/trade/delta", timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert d.get("consistency_ok") is True
        assert d.get("total_pots") == 22
        assert d.get("total_roar_tokens") == 22
        assert d.get("circulating_tokens") == 22
        # delta ~ +11.36 (small drift ok since market moves)
        assert abs(d.get("delta_eur") - 11.36) < 5.0, f"delta_eur={d.get('delta_eur')}"
        assert d.get("pots_capital_eur") == 122.4

    def test_potjes_user_001(self, api):
        r = api.get(f"{BASE_URL}/api/trade/potjes/user-001", timeout=10)
        assert r.status_code == 200
        d = r.json()
        pots = d.get("potjes", [])
        assert len(pots) == 10
        for p in pots:
            assert p["capital"] == 5.08

    def test_potjes_user_000(self, api):
        r = api.get(f"{BASE_URL}/api/trade/potjes/user-000", timeout=10)
        assert r.status_code == 200
        d = r.json()
        pots = d.get("potjes", [])
        assert len(pots) == 10
        for p in pots:
            assert p["capital"] == 5.08


# =============================================================================
# 2. Reconcile all coins — orphan status voor coins zonder pot
# =============================================================================
class TestReconcileAllCoins:
    def test_reconcile_shows_all_coins(self, api):
        r = api.get(f"{BASE_URL}/api/trade/reconcile/spark", timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert d.get("success") is True
        rows = d.get("rows", [])
        assert len(rows) > 1, "expected multiple coins, got only " + str(len(rows))

        coins = [r["coin"] for r in rows]
        # BCH should exist (pot-based)
        assert "BCH" in coins

        # Er moet minimaal 1 orphan coin zijn (bv ADA, CSPR, ATOM)
        orphans = [r for r in rows if r["status"] == "orphan"]
        assert len(orphans) >= 1, f"no orphan coins in reconcile output; coins={coins}"
        for o in orphans:
            assert o["n_pots"] == 0
            assert o["actual_coin_amount"] > 0

    def test_reconcile_bch_matched(self, api):
        r = api.get(f"{BASE_URL}/api/trade/reconcile/spark", timeout=20)
        rows = r.json().get("rows", [])
        bch = next((r for r in rows if r["coin"] == "BCH"), None)
        assert bch is not None
        assert bch["n_pots"] == 10
        # status is exact, overschot, or tekort (NIET orphan)
        assert bch["status"] in ("exact", "overschot", "tekort")


# =============================================================================
# 3. Cluster helpers — direct Python-level testing
# =============================================================================
class TestClusterHelpers:
    def test_get_next_buy_cluster_returns_cluster_when_enough_capital(self):
        """10 pots × €5.08, min_order=€10 → cluster van 2 pots (Sigma=€10.16)."""
        from modules.trade.potjes import get_next_buy_cluster
        c = get_next_buy_cluster("user-001", "SOL-EUR", 10.0)
        assert c is not None, "expected cluster (10 pots x 5.08 = 50.8 >= 10)"
        assert c["n_pots"] == 2, f"expected 2 pots, got {c['n_pots']}"
        assert abs(c["total_capital"] - 10.16) < 0.01
        assert len(c["pot_ids"]) == 2
        assert c["cluster_id"] and len(c["cluster_id"]) >= 8
        assert c["primary_pot_id"] == c["pot_ids"][0]

    def test_get_next_buy_cluster_returns_none_when_insufficient(self):
        """min_order=€1000 → geen cluster want max €50.80."""
        from modules.trade.potjes import get_next_buy_cluster
        c = get_next_buy_cluster("user-001", "SOL-EUR", 1000.0)
        assert c is None

    def test_get_next_buy_cluster_three_pots_for_15eur(self):
        """min_order=€15 → cluster van 3 pots (Sigma=€15.24)."""
        from modules.trade.potjes import get_next_buy_cluster
        c = get_next_buy_cluster("user-000", "ETH-EUR", 15.0)
        assert c is not None
        assert c["n_pots"] == 3
        assert c["total_capital"] >= 15.0

    def test_open_close_cluster_roundtrip(self):
        """Open + close cluster op backup+restore van user_potjes.json."""
        from modules.trade.potjes import (
            get_next_buy_cluster, open_cluster, close_cluster, get_pots_by_cluster
        )
        # Backup
        backup = POTJES_FILE.read_text()
        try:
            # Use user-000 pots (safe: identiek aan user-001, we herstellen na)
            # Cluster van 2 pots @ €5.08
            cluster = get_next_buy_cluster("user-000", "SOL-EUR", 10.0)
            assert cluster is not None
            assert cluster["n_pots"] == 2
            cid = cluster["cluster_id"]

            # OPEN cluster @ entry €6.00
            open_res = open_cluster(
                "user-000", cluster["pot_ids"],
                entry_price=6.00, cluster_id=cid,
                current_cycle=1, trade_id="test_trade_iter44",
                market="SOL-EUR",
            )
            assert open_res["success"] is True
            assert len(open_res["opened_pot_ids"]) == 2

            # Verify pots hebben cluster_id + entry_price
            pots_in_cluster = get_pots_by_cluster("user-000", cid)
            assert len(pots_in_cluster) == 2
            for p in pots_in_cluster:
                assert p["position"]["is_open"] is True
                assert p["position"]["entry_price"] == 6.00
                assert p["position"]["cluster_id"] == cid
                assert p["position"]["cluster_size"] == 2
                assert p["market"] == "SOL-EUR"

            # CLOSE cluster @ exit €6.60 (10% winst)
            close_res = close_cluster("user-000", cid, 6.60)
            assert close_res["success"] is True
            assert close_res["n_pots_closed"] == 2
            assert len(close_res["closed_pot_ids"]) == 2
            # Netto: 2 pots x 5.08 = 10.16 capital, 10% winst - 2*0.25% fees
            # bruto ~ 10.16 * 0.10 = 1.016; fees = 10.16 * 0.0025 * 2 = 0.0508
            # netto ~ 0.965
            assert close_res["total_netto"] > 0.9, f"total_netto={close_res['total_netto']}"
            assert len(close_res["per_pot_netto"]) == 2
            # Pro-rata: gelijke capital → gelijke netto per pot (~0.4825 elk)
            netto_values = list(close_res["per_pot_netto"].values())
            assert abs(netto_values[0] - netto_values[1]) < 0.001

            # Verify pots weer gesloten
            after_close = get_pots_by_cluster("user-000", cid)
            assert len(after_close) == 0
        finally:
            # Restore
            POTJES_FILE.write_text(backup)

    def test_close_cluster_nonexistent(self):
        from modules.trade.potjes import close_cluster
        r = close_cluster("user-000", "nonexistent_cluster_id_xxx", 100.0)
        assert r["success"] is False
        assert "error" in r


# =============================================================================
# 4. Monitor code paths — static code inspection (geen execution)
# =============================================================================
class TestMonitorClusterCode:
    """Verify _run_market_cycle bevat cluster-aware BUY + SELL flows."""

    def test_monitor_buy_uses_cluster(self):
        code = Path("/app/backend/modules/trade/monitor.py").read_text()
        assert "get_next_buy_cluster" in code
        assert "open_cluster" in code
        # BUY-flow moet cluster-based zijn
        assert "cluster[\"pot_ids\"]" in code or "cluster['pot_ids']" in code

    def test_monitor_sell_uses_close_cluster(self):
        code = Path("/app/backend/modules/trade/monitor.py").read_text()
        assert "close_cluster" in code
        assert "processed_clusters" in code
        # Backwards-compat: pots zonder cluster_id → close_pot
        assert "close_pot" in code

    def test_monitor_processed_clusters_dedup(self):
        code = Path("/app/backend/modules/trade/monitor.py").read_text()
        # processed_clusters wordt gebruikt om dubbele cluster-close te voorkomen
        assert "processed_clusters.add" in code
        assert "cid in processed_clusters" in code or "in processed_clusters" in code


# =============================================================================
# 5. Regressie iter_43 fixes — shadow 404, bot/status, reconcile/orphans
# =============================================================================
class TestIter43Regression:
    def test_shadow_endpoints_404(self, api):
        for ep in ("/api/trade/shadow/user-001", "/api/trade/shadow"):
            r = api.get(f"{BASE_URL}{ep}", timeout=10)
            assert r.status_code == 404, f"{ep} should be 404, got {r.status_code}"

    def test_bot_status_user_001(self, api):
        r = api.get(f"{BASE_URL}/api/trade/bot/status/user-001", timeout=10)
        assert r.status_code == 200
        d = r.json()
        # Must return consistent status object under 'status' key
        assert d.get("success") is True
        status = d.get("status", {})
        assert "auto_trade" in status
        assert "cycles" in status

    def test_reconcile_orphans_dry_run(self, api):
        r = api.get(
            f"{BASE_URL}/api/trade/reconcile/orphans/user-001",
            params={"only_profit": True},
            timeout=15,
        )
        assert r.status_code == 200
        d = r.json()
        assert "orphans" in d or "success" in d
