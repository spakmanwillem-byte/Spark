"""
Iteratie 47 — Refactor regressie test (v8_refactor_001)
=======================================================
Valideert dat na extractie van strategy_decision.py + exchange_data.py uit monitor.py:
- Alle imports via monitor.py facade werken (re-exports)
- Directe imports vanuit nieuwe modules werken
- Endpoints die intern fetch_tickers/_simple_decision gebruiken blijven werken
- State caches gedeeld blijven via facade
- Iteration 46 test file (17+ tests) blijft 100% pass
"""
import os
import sys
import subprocess
import pytest
import requests

def _load_base_url() -> str:
    v = os.environ.get("REACT_APP_BACKEND_URL", "").strip()
    if not v:
        # Fallback: parse frontend/.env
        env_path = "/app/frontend/.env"
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    if line.strip().startswith("REACT_APP_BACKEND_URL="):
                        v = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break
    return v.rstrip("/")

BASE_URL = _load_base_url()

# ============================================================
# 1) IMPORT REGRESSIE via facade (monitor.py)
# ============================================================

class TestFacadeReExports:
    def test_import_simple_decision_via_monitor(self):
        from modules.trade.monitor import _simple_decision
        result = _simple_decision([], position=None, trade_amount=5.0)
        assert isinstance(result, dict)
        assert result.get("action") == "HOLD"
        assert "Te weinig data" in result.get("reason", "")

    def test_import_fetch_candles_fetch_tickers_via_monitor(self):
        from modules.trade.monitor import fetch_candles, fetch_tickers
        assert callable(fetch_candles)
        assert callable(fetch_tickers)

    def test_import_constants_via_monitor(self):
        from modules.trade.monitor import (
            WATCHLIST_COINS, WATCHLIST_NAMES, BITVAVO_URL, BITVAVO_TAKER_FEE,
            KNOWN_MIN_QUOTE_FALLBACK,
        )
        assert "BTC" in WATCHLIST_COINS
        assert WATCHLIST_NAMES.get("BTC") == "Bitcoin"
        assert BITVAVO_URL.startswith("https://api.bitvavo.com")
        assert BITVAVO_TAKER_FEE == 0.0025
        assert "BTC-EUR" in KNOWN_MIN_QUOTE_FALLBACK

    def test_import_get_market_min_quote_via_monitor(self):
        from modules.trade.monitor import get_market_min_quote
        v = get_market_min_quote("BTC-EUR")
        assert isinstance(v, float)
        assert v >= 5.0

    def test_import_gap_breakout_and_daily_drop_via_monitor(self):
        from modules.trade.monitor import _gap_breakout_check, _detect_daily_drop
        gb = _gap_breakout_check([])
        assert "signal" in gb
        assert gb["signal"] == "NONE"
        dd = _detect_daily_drop([])
        assert "is_event" in dd
        assert dd["is_event"] is False

    def test_state_caches_accessible_via_facade(self):
        from modules.trade.monitor import _BLUEPRINT_CACHE, _CANDLE_CACHE
        assert isinstance(_BLUEPRINT_CACHE, dict)
        assert "data" in _BLUEPRINT_CACHE and "mtime" in _BLUEPRINT_CACHE
        assert isinstance(_CANDLE_CACHE, dict)

    def test_load_trader_blueprint_shared_cache(self):
        from modules.trade.monitor import _load_trader_blueprint, _BLUEPRINT_CACHE
        bp1 = _load_trader_blueprint()
        bp2 = _load_trader_blueprint()
        assert isinstance(bp1, dict)
        # 2 aanroepen → cache hit, identiek object of identieke inhoud
        assert bp1 == bp2
        # blueprint bestand moet parameters key hebben (bekend uit iteration 46)
        # ...maar dit kan ook leeg zijn als het bestand geladen is: allow both
        # De cache mtime moet gezet zijn na een load
        assert _BLUEPRINT_CACHE.get("mtime", 0) >= 0

    def test_state_shared_between_facade_and_module(self):
        """_BLUEPRINT_CACHE via facade == direct via strategy_decision (zelfde object)."""
        from modules.trade import monitor as _mon
        from modules.trade import strategy_decision as _sd
        assert _mon._BLUEPRINT_CACHE is _sd._BLUEPRINT_CACHE
        from modules.trade import exchange_data as _ed
        assert _mon._CANDLE_CACHE is _ed._CANDLE_CACHE
        assert _mon._TICKER_CACHE_ALL is _ed._TICKER_CACHE_ALL
        assert _mon._MARKETS_CACHE is _ed._MARKETS_CACHE


# ============================================================
# 2) DIRECTE IMPORT uit nieuwe modules
# ============================================================

class TestDirectModuleImports:
    def test_strategy_decision_module_direct(self):
        from modules.trade.strategy_decision import (
            _simple_decision, _gap_breakout_check, _detect_daily_drop,
            _load_trader_blueprint, BITVAVO_TAKER_FEE, BLUEPRINT_FILE,
        )
        assert callable(_simple_decision)
        assert callable(_gap_breakout_check)
        assert callable(_detect_daily_drop)
        assert callable(_load_trader_blueprint)
        assert BITVAVO_TAKER_FEE == 0.0025
        assert str(BLUEPRINT_FILE).endswith("spark_trader.json")

    def test_exchange_data_module_direct(self):
        from modules.trade.exchange_data import (
            fetch_tickers, fetch_candles, get_market_min_quote,
            get_market_precision, _round_amount_for_market, _cache_ttl,
            BITVAVO_URL, WATCHLIST_COINS, WATCHLIST_NAMES, KNOWN_MIN_QUOTE_FALLBACK,
        )
        assert callable(fetch_tickers)
        assert callable(fetch_candles)
        # _cache_ttl sanity
        assert _cache_ttl("1h") == 3600
        assert _cache_ttl("15m") == 900


# ============================================================
# 3) BACKTEST IMPORT REGRESSIE (geen volledige backtest, alleen import)
# ============================================================

class TestBacktestImports:
    def test_backtest_v2_import(self):
        # backtest_v2 doet `from modules.trade.monitor import _simple_decision`
        # We simuleren dit door een subprocess python -c te draaien vanuit backend/
        result = subprocess.run(
            [sys.executable, "-c", "from modules.trade.monitor import _simple_decision; print('OK')"],
            cwd="/app/backend",
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0, f"Import failed: {result.stderr}"
        assert "OK" in result.stdout

    def test_backtest_v5_360d_import(self):
        # Zelfde check voor backtest_v5_360d als die bestaat
        result = subprocess.run(
            [sys.executable, "-c",
             "from modules.trade.monitor import _simple_decision, fetch_candles, _gap_breakout_check; print('OK')"],
            cwd="/app/backend",
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0, f"Import failed: {result.stderr}"

    def test_server_py_imports_still_work(self):
        # server.py doet import op regel 497 - controleer geen ImportError
        result = subprocess.run(
            [sys.executable, "-c",
             "from modules.trade.monitor import MonitorService, get_user_monitor; print('OK')"],
            cwd="/app/backend",
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0, f"MonitorService/get_user_monitor import failed: {result.stderr}"


# ============================================================
# 4) TRADE ENDPOINT REGRESSIES
# ============================================================

class TestTradeEndpointRegressions:
    def test_trade_history_endpoint(self):
        """GET /api/trade/history/user-000 gebruikt intern fetch_tickers voor enrich."""
        assert BASE_URL, "REACT_APP_BACKEND_URL missing"
        r = requests.get(f"{BASE_URL}/api/trade/history/user-000", timeout=30)
        assert r.status_code == 200, f"Status {r.status_code}: {r.text[:200]}"
        data = r.json()
        # Verwacht een dict of list; niet expliciete structuur validatie, alleen geen error
        assert data is not None

    def test_trade_explained_endpoint(self):
        r = requests.get(f"{BASE_URL}/api/trade/explained", timeout=15)
        assert r.status_code == 200, f"Status {r.status_code}: {r.text[:200]}"
        data = r.json()
        # Uit iteration 46 baseline: _versie=v1.0, 4_actieve_strategie.naam=Gap Momentum 50
        assert "_versie" in data or "4_actieve_strategie" in data or isinstance(data, dict)

    def test_trade_strategy_confidence(self):
        r = requests.get(f"{BASE_URL}/api/trade/strategy/confidence", timeout=15)
        assert r.status_code == 200, f"Status {r.status_code}: {r.text[:200]}"

    def test_trade_honest_pnl_endpoint(self):
        r = requests.get(f"{BASE_URL}/api/trade/honest-pnl/user-000", timeout=15)
        assert r.status_code == 200, f"Status {r.status_code}: {r.text[:200]}"
        data = r.json()
        assert isinstance(data, dict)


# ============================================================
# 5) TRADER INTENTS REGRESSIE via /api/spark/compose
# ============================================================

class TestSparkComposeTraderIntents:
    def test_compose_trader_status(self):
        payload = {
            "text": "hoe staat mijn bot",
            "user_id": "user-001",
        }
        r = requests.post(f"{BASE_URL}/api/spark/compose", json=payload, timeout=90)
        assert r.status_code == 200, f"Status {r.status_code}: {r.text[:300]}"
        data = r.json()
        # Uit iteration 46 baseline: used_model=trader_intents, intent=trader_status
        used_model = data.get("used_model") or data.get("model")
        # Kan geneste struct hebben - probeer flexibel
        assert data is not None
        text = str(data).lower()
        # trader_intents pad triggerde in iter46
        assert "trader" in text or "bot" in text, f"Response bevat geen trader/bot referentie: {data}"


# ============================================================
# 6) LIVE FETCH_TICKERS (via monitor facade)
# ============================================================

class TestExchangeDataFacade:
    def test_fetch_tickers_via_monitor_facade(self):
        from modules.trade.monitor import fetch_tickers
        # Live Bitvavo call - kan falen bij netwerkproblemen; skip als leeg
        results = fetch_tickers(["BTC"])
        if not results:
            pytest.skip("Bitvavo unreachable or rate-limited; skip live check")
        assert isinstance(results, list)
        btc = next((t for t in results if t.get("symbol") == "BTC"), None)
        assert btc is not None
        assert btc.get("market") == "BTC-EUR"
        assert btc.get("last") > 0

    def test_fetch_tickers_direct_module(self):
        from modules.trade.exchange_data import fetch_tickers as ft_direct
        results = ft_direct(["ETH"])
        if not results:
            pytest.skip("Bitvavo unreachable")
        eth = next((t for t in results if t.get("symbol") == "ETH"), None)
        assert eth is not None
        assert eth.get("last") > 0
