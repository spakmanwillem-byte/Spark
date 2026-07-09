"""
Iteration 46 — Spark Core 2.0 backend regression + new-feature tests.

Covers 4 features added:
  1. Trader-glow (event dispatch, backend regression only — no UI test)
  2. Strategy Synthesizer (/api/trade/strategy/properties, /synthesize, /confidence)
  3. Chat → KB suggestions (/api/kb/v2/suggest-from-chat/{uid}, /suggest-accept)
  4. Odroid portability (SPARK_DATA_DIR env var in scheduler/__init__.py)

Focus: geen regressies in trader-intents, honest-pnl, chat compose, trade/explained.
"""
import json
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL")
if not BASE_URL:
    # Fallback: read frontend/.env directly
    env_file = Path("/app/frontend/.env")
    if env_file.exists():
        for ln in env_file.read_text().splitlines():
            if ln.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = ln.split("=", 1)[1].strip()
                break
BASE_URL = BASE_URL.rstrip("/")
API = f"{BASE_URL}/api"

TIMEOUT = 30


# ============================================================
# FEATURE 2: Strategy Synthesizer
# ============================================================

class TestStrategyProperties:
    """GET /api/trade/strategy/properties → 13 items met categorieën."""

    def test_properties_returns_catalog(self):
        r = requests.get(f"{API}/trade/strategy/properties", timeout=TIMEOUT)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("success") is True
        props = data.get("properties", {})
        assert isinstance(props, dict)
        # Should have 13 items per requirement
        assert len(props) == 13, f"Expected 13 property-catalog items, got {len(props)}: {list(props.keys())}"
        # Check categorieën diversity
        cats = {v.get("categorie") for v in props.values()}
        expected_cats = {"signaal", "filosofie", "confirmatie", "bescherming", "exit", "meta"}
        assert expected_cats.issubset(cats), f"Missing categorieën: {expected_cats - cats}"
        # Each item has description
        for key, val in props.items():
            assert "beschrijving" in val and val["beschrijving"]
            assert "categorie" in val
            assert "conflicts_with" in val


class TestStrategySynthesize:
    """POST /api/trade/strategy/synthesize — happy path + conflict + unknown."""

    def test_synthesize_valid_properties(self):
        unique = f"TEST_synth_{uuid.uuid4().hex[:8]}"
        payload = {
            "display_name": unique,
            "properties": ["bollinger_2sigma", "mean_reversion", "loss_cut_48h_3pct", "trailing_stop"],
            "author": "spark",
            "notes": "iter46 test",
        }
        r = requests.post(f"{API}/trade/strategy/synthesize", json=payload, timeout=TIMEOUT)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("success") is True, data
        assert "strategy_id" in data
        strat = data.get("strategy") or {}
        assert strat.get("status") == "draft_synthesized"
        assert strat.get("beschrijving")
        assert "hypothese_lineage" in strat
        assert "spark_alignment" in strat
        assert "backtest_plan" in strat
        assert strat.get("backtest_plan", {}).get("test_periode_dagen") == 360

        # Verify persisted in blueprint
        bp_path = Path("/app/backend/modules/trade/blueprints/spark_trader.json")
        bp = json.loads(bp_path.read_text(encoding="utf-8"))
        assert data["strategy_id"] in bp.get("strategieën", {})

        # Cleanup: remove draft to keep blueprint clean
        try:
            del bp["strategieën"][data["strategy_id"]]
            bp_path.write_text(json.dumps(bp, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    def test_synthesize_conflict(self):
        payload = {
            "display_name": f"TEST_conflict_{uuid.uuid4().hex[:6]}",
            "properties": ["mean_reversion", "trend_following"],
        }
        r = requests.post(f"{API}/trade/strategy/synthesize", json=payload, timeout=TIMEOUT)
        assert r.status_code == 200
        data = r.json()
        assert data.get("success") is False
        assert "conflicterende" in (data.get("error") or "").lower()
        assert isinstance(data.get("conflicts"), list) and len(data["conflicts"]) > 0

    def test_synthesize_unknown_property(self):
        payload = {
            "display_name": f"TEST_unknown_{uuid.uuid4().hex[:6]}",
            "properties": ["bogus_prop_xyz"],
        }
        r = requests.post(f"{API}/trade/strategy/synthesize", json=payload, timeout=TIMEOUT)
        assert r.status_code == 200
        data = r.json()
        assert data.get("success") is False
        assert "onbekende properties" in (data.get("error") or "").lower()
        assert isinstance(data.get("beschikbaar"), list)
        assert len(data["beschikbaar"]) >= 13

    def test_synthesize_empty_properties(self):
        r = requests.post(f"{API}/trade/strategy/synthesize", json={"properties": []}, timeout=TIMEOUT)
        assert r.status_code == 200
        data = r.json()
        assert data.get("success") is False
        assert data.get("error")


class TestStrategyConfidence:
    """GET /api/trade/strategy/confidence — all + single."""

    def test_confidence_all(self):
        r = requests.get(f"{API}/trade/strategy/confidence", timeout=TIMEOUT)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("success") is True
        strategies = data.get("strategies", {})
        # Original 3 strategieën must be present
        assert len(strategies) >= 3, f"Expected >=3 strategies, got {len(strategies)}: {list(strategies.keys())}"
        # gap_momentum_50 moet actief=true zijn
        gm = strategies.get("gap_momentum_50")
        assert gm is not None, "gap_momentum_50 missing"
        assert gm.get("actief") is True

    def test_confidence_single_gap_momentum_50(self):
        r = requests.get(
            f"{API}/trade/strategy/confidence",
            params={"strategy_id": "gap_momentum_50"},
            timeout=TIMEOUT,
        )
        assert r.status_code == 200
        data = r.json()
        assert data.get("success") is True
        strat = data.get("strategy")
        assert strat is not None
        assert strat.get("strategy_id") == "gap_momentum_50"
        assert "breakdown" in strat
        assert "hypothese_lineage" in strat
        assert "spark_alignment" in strat

    def test_confidence_unknown_strategy(self):
        r = requests.get(
            f"{API}/trade/strategy/confidence",
            params={"strategy_id": "does_not_exist_xyz"},
            timeout=TIMEOUT,
        )
        assert r.status_code == 200
        data = r.json()
        assert data.get("success") is False


# ============================================================
# FEATURE 3: Chat → KB suggestions
# ============================================================

class TestKbChatSuggest:
    """GET /api/kb/v2/suggest-from-chat/{user_id} + POST /suggest-accept."""

    def test_suggest_from_chat_user_001(self):
        r = requests.get(f"{API}/kb/v2/suggest-from-chat/user-001", timeout=TIMEOUT)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("success") is True
        assert data.get("turns_analyzed", 0) > 0
        assert data.get("unique_words_seen", 0) > 0
        sugs = data.get("suggestions", [])
        assert isinstance(sugs, list)
        if sugs:
            first = sugs[0]
            assert "begrip" in first
            assert "mention_count" in first
            assert "example_snippet" in first
            assert "confidence" in first
            assert 0 <= first["confidence"] <= 100

    def test_suggest_from_chat_filtered(self):
        r = requests.get(
            f"{API}/kb/v2/suggest-from-chat/user-001",
            params={"min_mentions": 10, "top_n": 5},
            timeout=TIMEOUT,
        )
        assert r.status_code == 200
        data = r.json()
        assert data.get("success") is True
        sugs = data.get("suggestions", [])
        assert len(sugs) <= 5
        for s in sugs:
            assert s.get("mention_count", 0) >= 10

    def test_suggest_accept_valid(self):
        # Use fake begrip to avoid colliding with real cards
        fake = f"test-begrip-{uuid.uuid4().hex[:8]}"
        payload = {"begrip": fake, "user_id": "user-001", "source": "chat_suggestion"}
        r = requests.post(f"{API}/kb/v2/suggest-accept", json=payload, timeout=TIMEOUT)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("success") is True, data
        # add_to_inbox returns 'existing' key or 'kaart' key
        # For a truly new begrip, existing should be False (or absent → we accept both)
        # Cleanup: try to delete the created inbox card so we don't pollute
        kaart = data.get("kaart") or {}
        card_id = kaart.get("id")
        if card_id:
            requests.post(
                f"{API}/kb/v2/delete",
                json={"card_id": card_id, "lade": "inbox", "user_id": "user-001", "reason": "iter46_test_cleanup"},
                timeout=TIMEOUT,
            )

    def test_suggest_accept_empty_begrip(self):
        payload = {"begrip": "   ", "user_id": "user-001"}
        r = requests.post(f"{API}/kb/v2/suggest-accept", json=payload, timeout=TIMEOUT)
        assert r.status_code == 200
        data = r.json()
        assert data.get("success") is False
        assert "begrip" in (data.get("error") or "").lower()


# ============================================================
# REGRESSIONS: trader-intents fast-path, LLM fallback, trade/explained, honest-pnl
# ============================================================

class TestChatComposeRegression:
    """POST /api/spark/compose — trader-intents fast path + LLM fallback."""

    def test_compose_trader_status(self):
        payload = {"text": "hoe staat mijn bot", "user_id": "user-001"}
        r = requests.post(f"{API}/spark/compose", json=payload, timeout=60)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("used_model") == "trader_intents", f"Expected trader_intents, got {data.get('used_model')}"
        assert data.get("intent") == "trader_status"
        assert data.get("fast_path") is True

    def test_compose_trader_explain(self):
        payload = {"text": "leg de trader uit", "user_id": "user-001"}
        r = requests.post(f"{API}/spark/compose", json=payload, timeout=60)
        assert r.status_code == 200
        data = r.json()
        assert data.get("intent") == "trader_explain", data
        msg = data.get("message") or ""
        assert "Gap Momentum 50" in msg, f"Message missing 'Gap Momentum 50': {msg[:200]}"

    def test_compose_llm_fallback_non_trader(self):
        payload = {"text": "wat vind je van muziek", "user_id": "user-001"}
        r = requests.post(f"{API}/spark/compose", json=payload, timeout=90)
        assert r.status_code == 200
        data = r.json()
        used = data.get("used_model") or ""
        assert used.startswith("primary/"), f"Expected 'primary/*' fallback, got '{used}'"
        assert data.get("intent") is None or data.get("intent") != "trader_status"


class TestTradeExplainedRegression:
    def test_explained_v1(self):
        r = requests.get(f"{API}/trade/explained", timeout=TIMEOUT)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("_versie") == "v1.0", data.get("_versie")
        s4 = data.get("4_actieve_strategie") or {}
        assert s4.get("naam") == "Gap Momentum 50", f"Expected 'Gap Momentum 50', got {s4.get('naam')}"


class TestHonestPnlRegression:
    def test_honest_pnl_user000(self):
        r = requests.get(f"{API}/trade/honest-pnl/user-000", timeout=TIMEOUT)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("success") is True
        for key in ("realized", "open", "echt_netto_eur", "honesty_ratio"):
            assert key in data, f"Missing key '{key}': {list(data.keys())}"


# ============================================================
# FEATURE 4: Odroid portability — SPARK_DATA_DIR env var
# ============================================================

class TestPortability:
    def test_spark_data_dir_env_var(self):
        """Run child python process with SPARK_DATA_DIR set → scheduler.DATA reflects it."""
        script = (
            "import os; os.environ['SPARK_DATA_DIR']='/tmp/spark-portable'; "
            "import sys; sys.path.insert(0,'/app/backend'); "
            "from modules.scheduler import DATA; print(DATA)"
        )
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        out = result.stdout.strip()
        assert out == "/tmp/spark-portable", f"Expected /tmp/spark-portable, got: {out!r}\nstderr: {result.stderr}"

    def test_scheduler_default_fallback(self):
        """Without SPARK_DATA_DIR → should fallback to /app/backend/data."""
        script = (
            "import os; os.environ.pop('SPARK_DATA_DIR', None); "
            "import sys; sys.path.insert(0,'/app/backend'); "
            "from modules.scheduler import DATA; print(DATA)"
        )
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        out = result.stdout.strip()
        # Fallback resolves to backend/data (may be normalized path)
        assert out.endswith("/backend/data"), f"Expected fallback path ending in /backend/data, got: {out!r}"
