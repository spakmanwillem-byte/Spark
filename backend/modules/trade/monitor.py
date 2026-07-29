"""
Monitor Service - Background trading monitor met Bitvavo candles
Singleton pattern, thread-safe, start/stop/pause
"""
import threading
import time
import logging
import json
import uuid
import hmac
import hashlib
import requests
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, List
from pathlib import Path
from modules.core.storage import load_json, save_json
from modules.core.tracing import trace_call  # v7_function_tracing_001

logger = logging.getLogger("spark_monitor")


def _read_pot_count(user_id: str) -> int:
    """v6_potje_per_token_001 — lees aantal potjes uit user_potjes.json (geen hardcoded 10)."""
    try:
        path = Path(__file__).parent.parent.parent / "data" / "financial" / "user_potjes.json"
        if not path.exists():
            return 0
        data = json.loads(path.read_text())
        return len(data.get("users", {}).get(user_id, {}).get("potjes", []))
    except Exception:
        return 0


# Bitvavo public API
# v8_refactor_001 — Exchange data (candles, tickers, market metadata)
# verhuisd naar exchange_data.py. Re-export voor externe consumers.
from .exchange_data import (  # noqa: E402
    BITVAVO_URL,
    WATCHLIST_COINS,
    WATCHLIST_NAMES,
    KNOWN_MIN_QUOTE_FALLBACK,
    _CANDLE_CACHE,
    _INTERVAL_SECONDS,
    _MARKETS_CACHE,
    _MARKETS_TTL,
    _TICKER_CACHE_ALL,
    get_market_min_quote,
    get_market_precision,
    _round_amount_for_market,
    _cache_ttl,
    fetch_candles,
    fetch_tickers,
)


DATA_DIR = Path(__file__).parent.parent.parent / "data"

# v8_refactor_001 — strategy-decision-logica verhuisd naar strategy_decision.py
# Re-export voor externe consumers die `from .monitor import X` doen.
from .strategy_decision import (  # noqa: E402
    BLUEPRINT_FILE,
    BITVAVO_TAKER_FEE,
    _BLUEPRINT_CACHE,
    _load_trader_blueprint,
    _simple_decision as _simple_decision_v1,
    _gap_breakout_check as _gap_breakout_check_v1,
    _detect_daily_drop as _detect_daily_drop_v1,
)
# v8_engine_switch_001 — A/B: kies decision-engine op basis van blueprint config
from .strategy_decision_v2 import (  # noqa: E402
    _simple_decision as _simple_decision_v2,
    _gap_breakout_check as _gap_breakout_check_v2,
    _detect_daily_drop as _detect_daily_drop_v2,
)


def _active_engine() -> str:
    """Return 'v1' (default) of 'v2' op basis van blueprint config."""
    try:
        bp = _load_trader_blueprint()
        return str(bp.get("active_decision_engine", "v1"))
    except Exception:
        return "v1"


def _simple_decision(candles, position=None, trade_amount=5.0):
    """Dispatcher: routes naar v1 of v2 op basis van blueprint config."""
    if _active_engine() == "v2":
        return _simple_decision_v2(candles, position, trade_amount)
    return _simple_decision_v1(candles, position, trade_amount)


def _gap_breakout_check(candles):
    if _active_engine() == "v2":
        return _gap_breakout_check_v2(candles)
    return _gap_breakout_check_v1(candles)


def _detect_daily_drop(candles, threshold_pct=5.0):
    if _active_engine() == "v2":
        return _detect_daily_drop_v2(candles, threshold_pct)
    return _detect_daily_drop_v1(candles, threshold_pct)
SETTINGS_DIR = DATA_DIR / "users"
MONITOR_STATE_FILE = DATA_DIR / "trade" / "monitor_state.json"

# v4_multi_market_001: candle cache → vermijdt Bitvavo rate-limit bij multi-coin monitoring.
# Per (market, interval, limit) bewaar laatst-opgehaalde candles + timestamp.
# Cache wordt vers gehouden door candle-interval seconden te respecteren.


def execute_mock_trade(user_id: str, market: str, side: str, amount_eur: float) -> Dict:
    """Execute a mock trade and log it"""
    # Fetch current price
    tickers = fetch_tickers([market.split("-")[0]])
    price = tickers[0]["last"] if tickers else 400.0

    trade_id = str(uuid.uuid4())[:8]
    now = datetime.now(timezone.utc).isoformat()
    trade = {
        "trade_id": trade_id,
        "run_id": "manual",
        "timestamp": now,
        "action": side.upper(),
        "market": market,
        "order_id": f"MOCK-{side.upper()}-{trade_id}",
        "amount": amount_eur,
        "price": price,
        "filled": amount_eur,
        "status": "filled",
        "mock": True,
        "success": True,
        "error": None,
    }

    # Save to trade history
    history_file = DATA_DIR / "wallet" / "trade_history" / f"{user_id}.json"
    data = load_json(history_file, default={"trades": []})
    data["trades"].append(trade)
    save_json(history_file, data)

    return {"success": True, "trade": trade, "message": f"Mock {side.upper()} uitgevoerd @ €{price:.2f}"}


@trace_call(category="trade.bitvavo.execute")
def execute_real_trade(user_id: str, market: str, side: str, amount_eur: float) -> Dict:
    """Execute a real trade via Bitvavo authenticated API.

    v6_trade_minorder_001: pre-check minimumOrderInQuoteAsset bij BUY.
    v6_trade_sell_balance_001: bij SELL eerst actuele balance ophalen en clamp om
      'insufficient balance'/dust-rounding fouten te voorkomen.
    v6_bitvavo_proxy_via_spark_001 (sessie 16): non-Spark users zonder eigen
      Bitvavo keys → trade gaat via Spark's (user-000) keys. Logisch consistent:
      ROAR-aankopen kwamen via Spark op Bitvavo terecht. `proxied=True` in trade-log.
    """
    settings_file = SETTINGS_DIR / user_id / "settings.json"
    settings = load_json(settings_file, default={})
    bitvavo = settings.get("integrations", {}).get("bitvavo", {})

    api_key = bitvavo.get("api_key")
    api_secret = bitvavo.get("api_secret")
    proxied = False
    if not api_key or not api_secret:
        spark_settings = load_json(SETTINGS_DIR / "user-000" / "settings.json", default={})
        spark_bv = spark_settings.get("integrations", {}).get("bitvavo", {})
        if spark_bv.get("api_key") and spark_bv.get("api_secret"):
            api_key = spark_bv["api_key"]
            api_secret = spark_bv["api_secret"]
            bitvavo = spark_bv
            proxied = True
            logger.info(f"[trade] {user_id} → via Spark's Bitvavo keys (proxy)")
        else:
            return {"success": False, "error": "Geen Bitvavo API credentials gevonden (ook niet bij Spark)"}

    side_l = side.lower()

    # v6_trade_minorder_001 — BUY min-order check
    if side_l == "buy":
        try:
            min_quote = get_market_min_quote(market)
            if amount_eur < min_quote:
                return {
                    "success": False,
                    "error": f"Te laag bedrag voor {market}: €{amount_eur:.2f} < minimum €{min_quote:.2f} (Bitvavo). Tip: kies een potje met meer kapitaal of een lagere min-coin (BTC/ETH werken vanaf €5).",
                    "error_code": "MIN_QUOTE",
                    "market": market,
                    "min_quote": min_quote,
                    "requested_amount": amount_eur,
                }
        except Exception as e:
            logger.warning(f"min-order check faalde voor {market}: {e}")

        # v6_buy_balance_check_001 (28 mei) — EUR-saldo check vóór BUY
        try:
            bal_resp = fetch_bitvavo_balance(user_id)
            balances = (bal_resp or {}).get("balances") or []
            eur_avail = 0.0
            for b in balances:
                if str(b.get("symbol")) == "EUR":
                    try:
                        eur_avail = float(b.get("available") or 0)
                    except Exception:
                        eur_avail = 0.0
                    break
            if eur_avail < amount_eur:
                logger.warning(f"[buy] geen saldo: €{eur_avail:.2f} < gevraagd €{amount_eur:.2f}")
                return {
                    "success": False,
                    "error": f"Geen saldo — aankoop niet gelukt. EUR beschikbaar: €{eur_avail:.2f}, gevraagd: €{amount_eur:.2f} voor {market}.",
                    "error_code": "INSUFFICIENT_EUR_BALANCE",
                    "market": market,
                    "eur_available": round(eur_avail, 2),
                    "requested_amount": amount_eur,
                    "tip": "Stort EUR op Bitvavo of wacht tot deposit-watcher een storting detecteert.",
                }
        except Exception as e:
            logger.warning(f"EUR-balance check faalde voor {market}: {e} — door met buy")

    # v6_trade_sell_balance_001 + v7_sell_units_fix_001 — SELL balance pre-check
    # Fix: amount_eur is EUR-bedrag, actual_avail is coin count → mixen unit was fout.
    # Nu: coin_target = amount_eur / price, clamp = min(coin_target, actual_avail),
    # round naar market-specifieke precisie, check dat resulterende quote-value >= min_quote.
    final_amount = amount_eur
    if side_l == "sell":
        try:
            base_asset = market.split("-")[0]  # bv. SOL-EUR → SOL
            bal_resp = fetch_bitvavo_balance(user_id)
            balances = (bal_resp or {}).get("balances") or []
            actual_avail = 0.0
            for b in balances:
                if str(b.get("symbol")) == base_asset:
                    try:
                        actual_avail = float(b.get("available") or 0)
                    except Exception:
                        actual_avail = 0.0
                    break
            if actual_avail <= 0:
                return {
                    "success": False,
                    "error": f"Geen {base_asset} balance op Bitvavo om te verkopen. Mogelijk al verkocht of niet binnengekomen.",
                    "error_code": "NO_BALANCE",
                    "market": market,
                    "base_asset": base_asset,
                    "actual_balance": actual_avail,
                }

            # v7_sell_units_fix_001 — bereken huidige prijs om EUR → coin te converteren
            current_price = 0.0
            try:
                tickers = fetch_tickers([base_asset])
                tk = next((t for t in tickers if t.get("market") == market), None)
                if tk:
                    current_price = float(tk.get("last") or 0)
            except Exception:
                pass
            if current_price <= 0:
                logger.warning(f"[sell] geen live prijs voor {market}, val terug op oude clamp-logica")
                clamped = min(amount_eur, actual_avail) * 0.999
            else:
                # Converteer EUR-bedrag naar coin count
                coin_target = amount_eur / current_price
                # Clamp naar wat we werkelijk hebben, minus 0.1% dust-buffer
                clamped = min(coin_target, actual_avail) * 0.999

            # v7_market_precision_001 — round naar market-specifieke decimals
            final_amount = _round_amount_for_market(clamped, market)

            if final_amount <= 0:
                return {
                    "success": False,
                    "error": f"Effectief sell-amount is 0 na precision-truncatie ({base_asset}: coin_target={coin_target if current_price>0 else 'n/a'}, actueel={actual_avail}).",
                    "error_code": "ZERO_AFTER_CLAMP",
                    "market": market,
                }

            # v7_sell_min_quote_check_001 — verify dat we boven Bitvavo min-quote zitten
            if current_price > 0:
                expected_quote = final_amount * current_price
                min_quote = get_market_min_quote(market)
                if expected_quote < min_quote:
                    return {
                        "success": False,
                        "error": (
                            f"Sell zou €{expected_quote:.3f} opleveren, onder Bitvavo minimum €{min_quote:.2f} "
                            f"voor {market}. Balance ({actual_avail} {base_asset}) is te klein om te verkopen."
                        ),
                        "error_code": "BELOW_MIN_QUOTE",
                        "market": market,
                        "expected_quote_eur": round(expected_quote, 4),
                        "min_quote_eur": min_quote,
                        "actual_balance": actual_avail,
                        "hint": "Deze coin is nu 'restwaarde' — verkoop is niet mogelijk. Gebruik sync-with-bitvavo om restwaarde-pot te sluiten zonder PnL.",
                    }

            logger.info(f"[sell] {market}: EUR gevraagd €{amount_eur} → coin_target {coin_target if current_price>0 else 'legacy'} → clamped {final_amount} (bal={actual_avail}, prec-adj)")
        except Exception as e:
            logger.warning(f"balance pre-check faalde voor {market}: {e} — val terug op gevraagd bedrag")
            final_amount = amount_eur

    try:
        timestamp = int(time.time() * 1000)
        body = {
            "market": market,
            "side": side_l,
            "orderType": "market",
            # v4_trade_operator_id_001: Bitvavo verplicht sinds 2025 operatorId (int) bij order endpoints (errorCode 203)
            "operatorId": int(bitvavo.get("operator_id") or 1001),
        }
        if side_l == "buy":
            body["amountQuote"] = str(round(final_amount, 2))  # EUR: 2 decimalen
        else:
            # v6_sell_amount_decimals_001 — coin-amount: max 8 decimals, geen
            # wetenschappelijke notatie. Bitvavo weigert anders met errorCode 429.
            body["amount"] = f"{final_amount:.8f}".rstrip("0").rstrip(".")

        # CRITICAL: signature moet over EXACT dezelfde body string als verzonden.
        # We sturen `data=body_str` om dubbele serialisatie te voorkomen.
        body_str = json.dumps(body, separators=(",", ":"))
        endpoint = "/v2/order"
        msg = str(timestamp) + "POST" + endpoint + body_str
        sig = hmac.new(api_secret.encode(), msg.encode(), hashlib.sha256).hexdigest()

        headers = {
            "Bitvavo-Access-Key": api_key,
            "Bitvavo-Access-Signature": sig,
            "Bitvavo-Access-Timestamp": str(timestamp),
            "Content-Type": "application/json",
        }

        resp = requests.post(f"{BITVAVO_URL}/order", headers=headers, data=body_str, timeout=10)
        if resp.status_code == 200:
            result = resp.json()
            filled = float(result.get("filledAmount", 0))
            filled_quote = float(result.get("filledAmountQuote", 0))
            avg_price = filled_quote / filled if filled > 0 else 0
            fee_paid = float(result.get("feePaid", 0))
            fee_currency = result.get("feeCurrency", "EUR")

            # v7_zero_filled_guard_001 — Bitvavo kan 200 OK teruggeven met
            # filledAmount=0 (bijv. bij te kleine sell-amount na clamp, of
            # market-condition rejection). Zonder guard sluiten we het potje
            # alsof er verkocht is, terwijl de crypto nog op Bitvavo staat.
            # → Interpreteer 0-fill expliciet als failure.
            if filled <= 0 or filled_quote <= 0:
                logger.warning(
                    f"[{side_l}] {market} Bitvavo 200 OK maar filled=0 → geen crypto verplaatst. "
                    f"raw={result}"
                )
                return {
                    "success": False,
                    "error": (
                        f"Bitvavo accepteerde de {side.upper()} maar er is niets verplaatst "
                        f"(filled=0). Order geweigerd door markt of amount te klein. "
                        f"{'Pot blijft open — trader probeert volgende cycle opnieuw.' if side_l == 'sell' else ''}"
                    ),
                    "error_code": "ZERO_FILLED",
                    "market": market,
                    "requested_amount": amount_eur,
                    "effective_amount": final_amount,
                    "bitvavo_status": result.get("status"),
                    "bitvavo_order_id": result.get("orderId"),
                }

            trade_id = result.get("orderId", str(uuid.uuid4())[:8])
            now = datetime.now(timezone.utc).isoformat()
            trade = {
                "trade_id": trade_id,
                "run_id": "manual",
                "timestamp": now,
                "action": side.upper(),
                "market": market,
                "order_id": trade_id,
                "amount": filled_quote if side_l == "buy" else filled,
                "price": avg_price,
                "filled": filled,
                "status": result.get("status", "filled"),
                "mock": False,
                "success": True,
                "error": None,
                "fee": fee_paid,
                "fee_currency": fee_currency,
                # v6_trade_sell_balance_001 — traceability
                "requested_amount": amount_eur,
                "effective_amount": final_amount,
                # v6_bitvavo_proxy_via_spark_001 — audit trail
                "proxied_via_spark": proxied,
            }

            history_file = DATA_DIR / "wallet" / "trade_history" / f"{user_id}.json"
            data = load_json(history_file, default={"trades": []})
            data["trades"].append(trade)
            save_json(history_file, data)

            return {"success": True, "trade": trade, "message": f"LIVE {side.upper()} uitgevoerd @ €{avg_price:.2f} (fee €{fee_paid:.4f})"}
        else:
            # Detail-error voor debugging
            err_body = resp.text
            return {
                "success": False,
                "error": f"Bitvavo API error: {resp.status_code} - {err_body}",
                "error_code": "BITVAVO_HTTP_ERROR",
                "http_status": resp.status_code,
                "requested_amount": amount_eur,
                "effective_amount": final_amount,
            }
    except Exception as e:
        return {"success": False, "error": str(e), "error_code": "EXCEPTION",
                "requested_amount": amount_eur, "effective_amount": final_amount}


def _bitvavo_signed_get(api_key: str, api_secret: str, endpoint: str, params: str = "") -> Dict:
    """Helper: signed GET request to Bitvavo API."""
    timestamp = int(time.time() * 1000)
    full_endpoint = endpoint + (f"?{params}" if params else "")
    msg = str(timestamp) + "GET" + full_endpoint
    sig = hmac.new(api_secret.encode(), msg.encode(), hashlib.sha256).hexdigest()
    headers = {
        "Bitvavo-Access-Key": api_key,
        "Bitvavo-Access-Signature": sig,
        "Bitvavo-Access-Timestamp": str(timestamp),
    }
    url = f"https://api.bitvavo.com{full_endpoint}"
    resp = requests.get(url, headers=headers, timeout=10)
    if resp.status_code == 200:
        return {"success": True, "data": resp.json()}
    return {"success": False, "error": f"Bitvavo {resp.status_code}: {resp.text}"}


def fetch_bitvavo_balance(user_id: str) -> Dict:
    """Fetch live Bitvavo account balances (all coins).
    v6_bitvavo_proxy_via_spark_001 (sessie 16): non-Spark users zonder keys →
    val terug op Spark's keys. Resultaat: één gedeelde Bitvavo-balance die alle
    user-bots zien (logisch want het is fysiek 1 Bitvavo-account)."""
    settings = load_json(SETTINGS_DIR / user_id / "settings.json", default={})
    bitvavo = settings.get("integrations", {}).get("bitvavo", {})
    api_key = bitvavo.get("api_key")
    api_secret = bitvavo.get("api_secret")
    proxied = False
    if not api_key or not api_secret:
        spark_settings = load_json(SETTINGS_DIR / "user-000" / "settings.json", default={})
        spark_bv = spark_settings.get("integrations", {}).get("bitvavo", {})
        if spark_bv.get("api_key") and spark_bv.get("api_secret"):
            api_key = spark_bv["api_key"]
            api_secret = spark_bv["api_secret"]
            proxied = True
        else:
            return {"success": False, "error": "Geen Bitvavo API credentials"}
    if api_key.startswith("TEST_"):
        return {"success": False, "error": "Placeholder API keys gedetecteerd - voer echte Bitvavo keys in via Trader → Settings"}

    result = _bitvavo_signed_get(api_key, api_secret, "/v2/balance")
    if not result.get("success"):
        return result

    balances = result["data"]
    # Enrich with EUR value using tickers
    non_zero = [b for b in balances if float(b.get("available", 0)) + float(b.get("inOrder", 0)) > 0]
    symbols = [b["symbol"] for b in non_zero if b["symbol"] != "EUR"]
    price_map = {}
    if symbols:
        tickers = fetch_tickers(symbols)
        price_map = {t["symbol"]: t["last"] for t in tickers}

    enriched = []
    total_eur = 0.0
    for b in non_zero:
        sym = b["symbol"]
        available = float(b.get("available", 0))
        in_order = float(b.get("inOrder", 0))
        total_amount = available + in_order
        if sym == "EUR":
            eur_value = total_amount
        else:
            eur_value = total_amount * price_map.get(sym, 0)
        total_eur += eur_value
        enriched.append({
            "symbol": sym,
            "available": available,
            "in_order": in_order,
            "total": total_amount,
            "price_eur": price_map.get(sym, 1.0 if sym == "EUR" else 0),
            "value_eur": round(eur_value, 2),
        })
    enriched.sort(key=lambda x: x["value_eur"], reverse=True)
    return {"success": True, "balances": enriched, "total_eur": round(total_eur, 2),
            "proxied_via_spark": proxied}


def sync_bitvavo_orders(user_id: str, market: Optional[str] = None) -> Dict:
    """
    Fetch executed trades from Bitvavo and add missing ones to local trade history.
    Uses the /v2/trades endpoint which lists all fills per market.
    """
    settings = load_json(SETTINGS_DIR / user_id / "settings.json", default={})
    bitvavo = settings.get("integrations", {}).get("bitvavo", {})
    api_key = bitvavo.get("api_key")
    api_secret = bitvavo.get("api_secret")
    if not api_key or not api_secret:
        return {"success": False, "error": "Geen Bitvavo API credentials"}
    if api_key.startswith("TEST_"):
        return {"success": False, "error": "Placeholder API keys gedetecteerd"}

    # Determine markets to sync: explicit, or all markets where user holds a balance
    markets_to_sync = [market] if market else []
    if not markets_to_sync:
        bal = fetch_bitvavo_balance(user_id)
        if bal.get("success"):
            markets_to_sync = [f"{b['symbol']}-EUR" for b in bal["balances"] if b["symbol"] != "EUR"]
        if not markets_to_sync:
            markets_to_sync = ["BCH-EUR"]

    history_file = DATA_DIR / "wallet" / "trade_history" / f"{user_id}.json"
    history = load_json(history_file, default={"trades": []})
    existing_ids = {t.get("order_id") or t.get("trade_id") for t in history["trades"]}

    imported = 0
    errors = []
    for m in markets_to_sync:
        result = _bitvavo_signed_get(api_key, api_secret, "/v2/trades", f"market={m}&limit=500")
        if not result.get("success"):
            errors.append(f"{m}: {result.get('error')}")
            continue
        for fill in result["data"]:
            fill_id = fill.get("id")
            if fill_id in existing_ids:
                continue
            amount = float(fill.get("amount", 0))
            price = float(fill.get("price", 0))
            side = fill.get("side", "buy").upper()
            trade = {
                "trade_id": fill_id,
                "run_id": "bitvavo_sync",
                "timestamp": datetime.fromtimestamp(fill.get("timestamp", 0) / 1000, tz=timezone.utc).isoformat(),
                "action": side,
                "market": m,
                "order_id": fill.get("orderId", fill_id),
                "amount": round(amount * price, 8),  # EUR quote value
                "price": price,
                "filled": amount,
                "status": "filled",
                "mock": False,
                "success": True,
                "error": None,
                "fee": float(fill.get("fee", 0)),
                "fee_currency": fill.get("feeCurrency", "EUR"),
            }
            history["trades"].append(trade)
            existing_ids.add(fill_id)
            imported += 1

    save_json(history_file, history)
    return {
        "success": True,
        "imported": imported,
        "total_trades": len(history["trades"]),
        "markets_synced": markets_to_sync,
        "errors": errors,
    }


# v8_refactor_001 — _simple_decision / _gap_breakout_check / _detect_daily_drop
# + BITVAVO_TAKER_FEE verhuisd naar strategy_decision.py.
# Re-exported bovenaan deze file via `from .strategy_decision import ...`.


class MonitorService:
    """v4_per_user_bot_001: per-user trade bot.
    Was singleton, nu instantieerbaar per user-id via MonitorRegistry."""

    def __init__(self, user_id: str = "user-001"):
        self._lock = threading.Lock()
        self._running = False
        self._paused = False
        self._thread = None
        self._stop_event = threading.Event()
        self._start_time = None
        self._cycles = 0
        self._interval = 60
        self._market = "BCH-EUR"
        self._markets = ["BCH-EUR"]
        # v7_candle_15m_default_001 — 15m is reactiever bij dalende/volatiele markten.
        # 1h heeft 20u rollende window → mist intra-day turnarounds. 15m heeft 5u window.
        self._candle_interval = "15m"
        self._user_id = user_id
        self._decisions = []
        self._last_price = 0
        self._last_prices = {}
        self._auto_trade = False
        self._trade_amount = 5.0
        # v6_mock_default_off_001 — default REAL voor nieuwe MonitorService-instanties
        self._use_mock = False
        self._position = {"is_open": False, "entry_price": None, "highest_price": None, "trailing_active": False}
        self._use_potjes = False
        # v6_buy_cooldown_001 — tijdstempel laatste BUY per markt (voor 5-min cooldown)
        self._last_buy_per_market: Dict[str, datetime] = {}
        # v7_eur_cooldown_001 — als Bitvavo INSUFFICIENT_EUR_BALANCE geeft, wacht N min
        # voor we opnieuw proberen te kopen (voorkomt loop-spam op alle markets).
        self._last_insufficient_eur_ts: Optional[datetime] = None
        # v8_event_protection_001 — bij >5% daily drop pauzeert de bot en waarschuwt de user.
        # Data-driven: backtest v3 detecteerde 185 shock-events over 6 markten × 6 maanden.
        # Config uit blueprints/spark_trader.json.event_protection.
        self._event_pause_until: Dict[str, datetime] = {}
        self._event_notifications: List[Dict] = []

        # v7_config_persist_on_init_001 — laad config uit state file bij creatie zodat
        # UI /bot/status altijd de laatste user-configuratie toont (interval, markets,
        # auto_trade, use_potjes), OOK als de bot momenteel niet draait.
        # _running blijft False — alleen expliciet start()/resume_if_was_running() zet 'm aan.
        if user_id == "user-001":
            try:
                if MONITOR_STATE_FILE.exists():
                    with open(MONITOR_STATE_FILE) as f:
                        st = json.load(f)
                    self._interval = int(st.get("interval") or self._interval)
                    self._market = st.get("market") or self._market
                    self._markets = list(st.get("markets") or [self._market])
                    self._candle_interval = st.get("candle_interval") or self._candle_interval
                    self._auto_trade = bool(st.get("auto_trade", self._auto_trade))
                    self._trade_amount = float(st.get("trade_amount") or self._trade_amount)
                    self._use_mock = bool(st.get("use_mock", self._use_mock))
                    self._use_potjes = bool(st.get("use_potjes", self._use_potjes))
                    # v10_buy_cooldown_persist_001 — laad per-markt buy-cooldown timestamps
                    # zodat cooldown herstart-safe is. Voorheen was dit in-memory dict,
                    # bij monitor-restart werd cooldown gereset → spam-buys mogelijk.
                    _cd = st.get("last_buy_per_market") or {}
                    for _m, _iso in _cd.items():
                        try:
                            self._last_buy_per_market[_m] = datetime.fromisoformat(_iso.replace("Z", "+00:00"))
                        except Exception:
                            pass
            except Exception as _ex:
                logger.warning(f"Config init-load faalde voor {user_id}: {_ex}")

    def start(self, interval: int = 60, market: str = "BCH-EUR",
              candle_interval: str = "1h", user_id: Optional[str] = None,
              auto_trade: bool = False, trade_amount: float = 5.0, use_mock: bool = False,
              use_potjes: bool = False, markets: Optional[List[str]] = None) -> Dict:
        # user_id wordt vastgezet bij instantiatie; argument blijft voor back-compat
        if user_id and user_id != self._user_id:
            self._user_id = user_id

        # v6_pot_required_001 — geen potje = geen monitor/bot
        # Monitor en bot mogen ALLEEN starten als de user-id minstens 1 potje bezit.
        # Dit voorkomt idle bots/monitor zonder capital na deploy-reset.
        effective_uid = user_id or self._user_id
        owned_pot_count = _read_pot_count(effective_uid)
        if owned_pot_count <= 0:
            return {
                "success": False,
                "message": f"Geen potjes voor {effective_uid} — koop/ontvang eerst een potje voor je een bot/monitor start.",
                "owned_pot_count": 0,
            }
        # Monitor gebruikt strikt het aantal potjes dat de user bezit (niet meer dan dat).
        # use_potjes wordt geforceerd op True zodat er geen single-mode bot draait
        # die de pot-economie omzeilt.
        use_potjes = True

        with self._lock:
            if self._running:
                return {"success": False, "message": "Monitor draait al", "status": self.get_status()}
            self._interval = max(10, min(interval, 86400))
            # v4_multi_market_001: `markets` (lijst) heeft voorrang op `market` (string)
            if markets:
                clean = [m.strip().upper() for m in markets if isinstance(m, str) and m.strip()]
                self._markets = clean if clean else [market]
            else:
                self._markets = [market]
            self._market = self._markets[0]   # primair = eerste voor status display
            self._candle_interval = candle_interval
            self._user_id = user_id
            self._auto_trade = auto_trade
            self._trade_amount = trade_amount
            # v6_bitvavo_proxy_via_spark_001 — non-Spark users gebruiken Spark's keys
            # via execute_real_trade fallback. Mock-mode wordt niet meer geforceerd
            # zodat álle user-bots echt kunnen handelen.
            self._use_mock = use_mock
            self._use_potjes = use_potjes
            self._stop_event.clear()
            self._running = True
            self._paused = False
            self._start_time = datetime.now(timezone.utc)
            self._cycles = 0
            self._decisions = []
            self._last_prices = {}
            self._thread = threading.Thread(target=self._loop, daemon=True)
            self._thread.start()
            self._persist_state()
            # v4_registry_persist_001: ook registry-state voor non-legacy bots
            if self._user_id != "user-001":
                try:
                    _persist_registry()
                except Exception:
                    pass
            # v6_clean_slate_28mei — toon actuele potje-count uit data
            from modules.trade.potjes import _load as _potjes_load
            try:
                n_pots = len(_potjes_load(user_id or self._user_id).get("users", {}).get(self._user_id, {}).get("potjes", []))
                mode = f"{n_pots}-potjes" if use_potjes else "single"
            except Exception:
                mode = "potjes" if use_potjes else "single"
            coin_label = ", ".join(self._markets) if len(self._markets) > 1 else self._markets[0]
            return {"success": True, "message": f"Monitor gestart ({candle_interval} candles, {mode} mode, {coin_label})", "status": self.get_status()}

    def _persist_state(self):
        """Save monitor config to disk for auto-resume after restart.
        v4_registry_persist_001: Alleen LEGACY monitor (user-001) persisteert
        naar globale state. Registry-bots (user-000 enz) krijgen eigen file later."""
        if self._user_id != "user-001":
            return  # registry-bots niet in globale state
        try:
            MONITOR_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
            state = {
                "running": self._running,
                "interval": self._interval,
                "market": self._market,
                "markets": self._markets,
                "candle_interval": self._candle_interval,
                "user_id": self._user_id,
                "auto_trade": self._auto_trade,
                "trade_amount": self._trade_amount,
                "use_mock": self._use_mock,
                "use_potjes": self._use_potjes,
                # v10_buy_cooldown_persist_001 — persist per-markt buy-timestamps
                "last_buy_per_market": {
                    m: ts.isoformat() for m, ts in self._last_buy_per_market.items()
                },
                "last_persisted": datetime.now(timezone.utc).isoformat(),
            }
            with open(MONITOR_STATE_FILE, "w") as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.warning(f"Monitor state persist failed: {e}")

    def resume_if_was_running(self) -> Dict:
        """v7_no_auto_resume_001 — auto-resume UITGESCHAKELD (default).

        Reden: state-mismatches (restwaarde-pots, potjes-desync) na deploy/redeploy zijn
        veroorzaakt door de trader die automatisch herstart met oude state terwijl
        de actual Bitvavo saldo intussen veranderd is. User moet expliciet trader
        starten via UI na deploy, ná restwaarde-sync via
        POST /api/trade/reconcile/potjes/user-001/sync-with-bitvavo.

        State-file wordt WEL naar `running: false` gezet zodat de UI zichtbaar toont
        dat de trader inactief is na restart.
        """
        if MONITOR_STATE_FILE.exists():
            try:
                with open(MONITOR_STATE_FILE) as f:
                    state = json.load(f)
                if state.get("running"):
                    state["running"] = False
                    state["_auto_stopped_at"] = datetime.now(timezone.utc).isoformat()
                    state["_auto_stop_reason"] = "v7_no_auto_resume — safety after (re)deploy"
                    with open(MONITOR_STATE_FILE, "w") as f:
                        json.dump(state, f, indent=2)
                    logger.info("Monitor NIET automatisch geresumeerd (v7_no_auto_resume_001). User moet expliciet starten.")
            except Exception as e:
                logger.warning(f"resume_if_was_running state-reset failed: {e}")
        return {"resumed": False, "reason": "v7_no_auto_resume_001 — trader moet expliciet gestart worden na (re)deploy"}

    def stop(self) -> Dict:
        with self._lock:
            if not self._running:
                return {"success": False, "message": "Monitor draait niet"}
            self._stop_event.set()
            self._running = False
            self._paused = False
            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=5)
            self._thread = None
            self._persist_state()  # Save: running=false so auto-resume skips
            if self._user_id != "user-001":
                try:
                    _persist_registry()
                except Exception:
                    pass
            return {"success": True, "message": "Monitor gestopt", "status": self.get_status()}

    def pause(self) -> Dict:
        with self._lock:
            if not self._running:
                return {"success": False, "message": "Monitor draait niet"}
            self._paused = not self._paused
            state = "gepauzeerd" if self._paused else "hervat"
            return {"success": True, "message": f"Monitor {state}", "status": self.get_status()}

    # v5_hot_market_swap_001 — markets hot-aanpassen zonder bot te stoppen
    def update_markets(self, markets: List[str]) -> Dict:
        with self._lock:
            clean = [m.strip().upper() for m in markets if isinstance(m, str) and m.strip()]
            if not clean:
                return {"success": False, "message": "Geen geldige markets opgegeven"}
            self._markets = clean
            self._market = clean[0]
            if self._running:
                try:
                    self._persist_state()
                    if self._user_id != "user-001":
                        _persist_registry()
                except Exception:
                    pass
            # v7_anchor_removed_001 — ensure_anchors_for_markets is nu een no-op stub.
            # Geen locked pots meer aangemaakt bij nieuwe coins. Pots blijven 1-op-1
            # met ROAR-tokens; verdeling over markten via round-robin in sync_potjes_to_tokens.
            logger.info(f"Markets hot-updated voor {self._user_id}: {clean}")
            return {"success": True, "markets": clean, "running": self._running}

    # v5_candle_hotswap_001 — wissel candle_interval (15m / 1h / 4h / 1d) zonder restart
    def update_candle_interval(self, candle_interval: str) -> Dict:
        VALID = {"1m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d"}
        ci = (candle_interval or "").strip()
        if ci not in VALID:
            return {"success": False, "message": f"Ongeldige candle_interval '{ci}'. Geldig: {sorted(VALID)}"}
        with self._lock:
            self._candle_interval = ci
            if self._running:
                try:
                    self._persist_state()
                    if self._user_id != "user-001":
                        _persist_registry()
                except Exception:
                    pass
            logger.info(f"Candle interval hot-updated voor {self._user_id}: {ci}")
            return {"success": True, "candle_interval": ci, "running": self._running}

    # v5_autotrade_hotswap_001 — toggle auto_trade aan/uit zonder restart en persisteer
    def update_auto_trade(self, auto_trade: bool) -> Dict:
        with self._lock:
            self._auto_trade = bool(auto_trade)
            try:
                self._persist_state()
                if self._user_id != "user-001":
                    _persist_registry()
            except Exception:
                pass
            logger.info(f"Auto-trade hot-updated voor {self._user_id}: {self._auto_trade}")
            return {"success": True, "auto_trade": self._auto_trade, "running": self._running}

    def get_status(self) -> Dict:
        uptime = None
        if self._start_time and self._running:
            uptime = (datetime.now(timezone.utc) - self._start_time).total_seconds()
        return {
            "running": self._running,
            "paused": self._paused,
            "cycles": self._cycles,
            "interval": self._interval,
            "candle_interval": self._candle_interval,
            "market": self._market,
            "markets": list(self._markets),
            "user_id": self._user_id,
            "auto_trade": self._auto_trade,
            "trade_amount": self._trade_amount,
            "use_mock": self._use_mock,
            "last_price": self._last_price,
            "last_prices": dict(self._last_prices),
            "start_time": self._start_time.isoformat() if self._start_time else None,
            "uptime_seconds": uptime,
            "thread_alive": self._thread.is_alive() if self._thread else False,
            "position": self._position,
            "use_potjes": self._use_potjes,
            "pot_count": _read_pot_count(self._user_id) if self._use_potjes else None,
        }

    def get_decisions(self, limit: int = 50) -> List[Dict]:
        return list(reversed(self._decisions[-limit:]))

    def _loop(self):
        logger.info(f"Monitor loop started: markets={self._markets} ({self._candle_interval})")
        # v4_multi_market_001: context-candles per market apart bijhouden (TTL-cache in fetch_candles)
        context_per_market: Dict[str, List[Dict]] = {}
        for mkt in self._markets:
            try:
                context_per_market[mkt] = fetch_candles(mkt, self._candle_interval, 50)
                logger.info(f"Pre-loaded {len(context_per_market[mkt])} candles for {mkt}")
            except Exception as e:
                logger.error(f"Initial candle fetch failed for {mkt}: {e}")
                context_per_market[mkt] = []

        while not self._stop_event.is_set():
            if self._paused:
                time.sleep(1)
                continue

            self._cycles += 1

            # v7_pot_revalue_001 — Sync vrije pots met huidige token-prijs (1 keer per tick).
            # Reden: pot capital moet meebewegen met dynamische ROAR-prijs (die stijgt door
            # Bitvavo groei / stortingen). Open pots blijven locked op buy-price.
            try:
                from modules.shop.routes import get_dynamic_price
                from modules.trade import potjes as potjes_svc
                token_price = float(get_dynamic_price())
                if token_price > 0:
                    rv = potjes_svc.revalue_free_pots(self._user_id, token_price)
                    if rv.get("revalued_count", 0) > 0:
                        logger.info(f"[revalue] user={self._user_id} synced {rv['revalued_count']} free pots to €{token_price:.4f}")
            except Exception as e:
                logger.warning(f"pot revalue skipped: {e}")

            # v4_multi_market_001: één ticker-call voor ALLE markten samen (anti-rate-limit)
            try:
                base_symbols = [m.split("-")[0] for m in self._markets]
                ticker_data = fetch_tickers(base_symbols)
                price_by_market = {t["market"]: t["last"] for t in ticker_data}
            except Exception as e:
                logger.error(f"Ticker fetch error: {e}")
                price_by_market = {}

            for mkt in list(self._markets):
                try:
                    self._run_market_cycle(mkt, context_per_market, price_by_market.get(mkt))
                except ZeroDivisionError as e:
                    # v6_zerodiv_guard_001 — log met user-id en stack-trace voor diagnose
                    import traceback as _tb
                    logger.error(f"Monitor cycle ZeroDivision ({mkt}) user={self._user_id}: {e}\n{_tb.format_exc()[:800]}")
                except Exception as e:
                    logger.error(f"Monitor cycle error ({mkt}) user={self._user_id}: {e}")

            # v11_adopt_manual_positions_001 — Bug C fix.
            # Bot draaide alleen over markten in `self._markets`. Handmatige BUYs van
            # Willem op andere markten werden compleet genegeerd → geen trailing stop.
            # Nu: detecteer open potjes op markten BUITEN self._markets en pas ook
            # daar trailing-stop toe (loss-cut + trailing SELL) alsof ze bij ons hoorden.
            if self._use_potjes:
                try:
                    self._adopt_orphan_positions(context_per_market)
                except Exception as e:
                    logger.error(f"Orphan adoption error user={self._user_id}: {e}")

            elapsed = 0
            while elapsed < self._interval and not self._stop_event.is_set():
                time.sleep(1)
                elapsed += 1

        logger.info("Monitor loop stopped")

    def _adopt_orphan_positions(self, context_per_market: Dict[str, List[Dict]]):
        """v11_adopt_manual_positions_001 — Detecteer open potjes op markten buiten
        self._markets (bijv. handmatige BUYs door Willem) en apply trailing-stop check.

        Werkwijze:
          1. Verzamel unique markets van alle open pots die NIET in self._markets zitten
          2. Voor elke orphan market: fetch live price + candles
          3. Voor elke open pot op die market: doe dezelfde trailing-stop check als
             _run_market_cycle regel 989-1046 (loss-cut + trailing SELL)
        """
        from modules.trade import potjes as potjes_svc

        user_potjes = potjes_svc.get_potjes(self._user_id)
        open_pots = [p for p in user_potjes.get("potjes", [])
                     if p.get("position", {}).get("is_open")]
        if not open_pots:
            return

        orphan_markets: Dict[str, List[Dict]] = {}
        for p in open_pots:
            mkt = p.get("market")
            if not mkt or mkt in self._markets:
                continue
            orphan_markets.setdefault(mkt, []).append(p)

        if not orphan_markets:
            return

        # Batch ticker-call voor alle orphan markets
        base_symbols = [m.split("-")[0] for m in orphan_markets.keys()]
        try:
            ticker_data = fetch_tickers(base_symbols)
            price_by_market = {t["market"]: float(t.get("last") or 0) for t in ticker_data}
        except Exception as e:
            logger.warning(f"[adopt] ticker fetch failed: {e}")
            price_by_market = {}

        for mkt, pots_on_mkt in orphan_markets.items():
            price = price_by_market.get(mkt)
            if not price or price <= 0:
                continue
            self._process_trailing_for_market(mkt, price, pots_on_mkt, adopted=True)

    def _process_trailing_for_market(self, market: str, price: float,
                                     pots: List[Dict], adopted: bool = False):
        """v11_adopt_manual_positions_001 — Gedeelde trailing-stop logica voor
        `_run_market_cycle` én `_adopt_orphan_positions`. Loss-cut + trailing SELL check.

        Wordt in Fase 1 alleen aangeroepen door orphan-adoption (Bug C fix).
        In een latere refactor kan _run_market_cycle regel 989-1046 hier naartoe worden
        gerefactored zodat er 1 pad is voor trailing-stop logic.
        """
        from modules.trade import potjes as potjes_svc

        processed_clusters: set = set()
        for pot in pots:
            if not pot["position"]["is_open"]:
                continue
            cid = pot["position"].get("cluster_id")
            if cid and cid in processed_clusters:
                continue
            potjes_svc.update_pot_tracking(self._user_id, pot["id"], price)
            pos = pot["position"]
            entry = pos.get("entry_price")
            if not entry or entry <= 0:
                continue
            if cid:
                cluster_pots = potjes_svc.get_pots_by_cluster(self._user_id, cid)
                cluster_capital = sum(float(cp.get("capital", 0) or 0) for cp in cluster_pots)
            else:
                cluster_pots = [pot]
                cluster_capital = float(pot.get("capital", 0) or 0)
            highest = max(pos.get("highest_price", entry) or entry, price)
            profit_pct = (price - entry) / entry
            bruto = cluster_capital * profit_pct
            fees = cluster_capital * BITVAVO_TAKER_FEE * 2
            netto = bruto - fees
            trail_threshold = round(fees * 2, 6)
            exit_min_netto = round(fees * 1, 6)
            netto_r = round(netto, 6)
            trailing_active = pos.get("trailing_active", False) or netto_r >= trail_threshold

            # Loss-cut check (Willems -8% noodstop op adopted positions ook)
            loss_pct = profit_pct * 100
            try:
                bp = _load_trader_blueprint()
                loss_cut_pct = float(bp.get("parameters", {}).get("loss_cut_pct", -0.08)) * 100
            except Exception:
                loss_cut_pct = -8.0
            hit_loss_cut = loss_pct <= loss_cut_pct

            should_sell = False
            reason = ""
            if hit_loss_cut:
                should_sell = True
                reason = f"Loss-cut {loss_pct:.2f}% ≤ {loss_cut_pct:.1f}%"
            elif trailing_active and price < highest and netto_r >= exit_min_netto:
                should_sell = True
                reason = f"Trailing SELL netto €{netto_r:.4f}"

            if should_sell and self._auto_trade:
                tag = "[adopted]" if adopted else "[trailing]"
                logger.info(f"{tag} SELL trigger {market} pot={pot['id']} — {reason}")
                if self._use_mock:
                    result = execute_mock_trade(self._user_id, market, "SELL", cluster_capital)
                else:
                    result = execute_real_trade(self._user_id, market, "SELL", cluster_capital)
                if result.get("success"):
                    real_price = result.get("trade", {}).get("price") or price
                    if cid:
                        potjes_svc.close_cluster(self._user_id, cid, real_price)
                        processed_clusters.add(cid)
                    else:
                        potjes_svc.close_pot(self._user_id, pot["id"], real_price)

    def _run_market_cycle(self, market: str, context_per_market: Dict[str, List[Dict]], live_price: Optional[float] = None):
        """v4_multi_market_001: één cycle voor één market. Live prijs uit gedeelde ticker-call.
        Candles enkel ververst als TTL verstreken (zie fetch_candles cache)."""
        # Context candles: gebruik cache uit fetch_candles (TTL = candle-interval seconden)
        context_candles = fetch_candles(market, self._candle_interval, 50)
        context_per_market[market] = context_candles
        if not context_candles:
            return

        # v8_event_protection_001 — check op shock-event (>5% drop 24u)
        # Als event actief én we zijn in pause-window: skip deze market.
        now_utc = datetime.now(timezone.utc)
        paused_until = self._event_pause_until.get(market)
        if paused_until and now_utc < paused_until:
            remaining_min = int((paused_until - now_utc).total_seconds() / 60)
            logger.info(f"[event-pause] {market}: nog {remaining_min}min gepauzeerd vanwege eerdere shock-event")
            return
        # Fetch 96 15m-candles voor event-detectie (24u window)
        event_candles = context_candles if self._candle_interval == "15m" else fetch_candles(market, "15m", 96)
        event = _detect_daily_drop(event_candles, threshold_pct=5.0) if event_candles else {"is_event": False}
        if event.get("is_event"):
            # Pauzeer 24u + log notification
            pause_hours = 24
            self._event_pause_until[market] = now_utc + timedelta(hours=pause_hours)
            notif = {
                "ts": now_utc.isoformat(),
                "user_id": self._user_id,
                "market": market,
                "drop_pct": event["drop_pct"],
                "peak_price": event["peak_price"],
                "trough_price": event["trough_price"],
                "pause_hours": pause_hours,
                "message": (
                    f"🚨 Ik zag {event['drop_pct']}% drop op {market} in de laatste 24u "
                    f"(€{event['peak_price']} → €{event['trough_price']}). Ik pauzeer je bot {pause_hours}u "
                    f"om je kapitaal te beschermen."
                ),
            }
            self._event_notifications.append(notif)
            # Persist naar file (max 200 recent)
            try:
                notif_file = DATA_DIR / "trade" / "event_notifications.json"
                existing = []
                if notif_file.exists():
                    existing = json.loads(notif_file.read_text())
                existing.append(notif)
                notif_file.write_text(json.dumps(existing[-200:], indent=2, ensure_ascii=False))
            except Exception as _e:
                logger.warning(f"event_notifications write error: {_e}")
            logger.warning(f"[event-pause] {market} — {notif['message']}")
            return

        price = live_price if live_price is not None else context_candles[-1]["close"]
        self._last_price = price
        self._last_prices[market] = price

        if self._use_potjes:
            from modules.trade import potjes as potjes_svc
            from modules.trade import context_service
            market_context = context_service.get_cached(market)
            user_potjes = potjes_svc.get_potjes(self._user_id)
            actions_this_cycle = []

            # 1. Voor elke open positie OP DEZE MARKET: check trailing-stop SELL.
            #    v7_pot_cluster_001 — Pots die tot dezelfde cluster behoren delen entry/highest.
            #    We processen per uniek cluster_id (of per losse pot als cluster_id=None) om
            #    te voorkomen dat we 5× dezelfde exit check doen voor 1 cluster.
            processed_clusters: set = set()
            for pot in user_potjes["potjes"]:
                if not pot["position"]["is_open"]:
                    continue
                if pot.get("market") != market:
                    continue
                cid = pot["position"].get("cluster_id")
                if cid and cid in processed_clusters:
                    continue  # cluster al gecheckt/gesloten in deze cycle
                potjes_svc.update_pot_tracking(self._user_id, pot["id"], price)
                pos = pot["position"]
                entry = pos["entry_price"]
                if not entry or entry <= 0:
                    continue
                # Cluster-aware: aggregate capital voor trailing thresholds
                if cid:
                    cluster_pots = potjes_svc.get_pots_by_cluster(self._user_id, cid)
                    cluster_capital = sum(float(cp.get("capital", 0) or 0) for cp in cluster_pots)
                else:
                    cluster_pots = [pot]
                    cluster_capital = pot["capital"]
                highest = max(pos.get("highest_price", entry) or entry, price)
                profit_pct = (price - entry) / entry
                bruto = cluster_capital * profit_pct
                fees = cluster_capital * BITVAVO_TAKER_FEE * 2
                netto = bruto - fees
                trail_threshold = round(fees * 2, 6)
                exit_min_netto = round(fees * 1, 6)
                netto_r = round(netto, 6)
                trailing_active = pos.get("trailing_active", False) or netto_r >= trail_threshold

                if trailing_active and price < highest and netto_r >= exit_min_netto:
                    if self._auto_trade:
                        if self._use_mock:
                            result = execute_mock_trade(self._user_id, market, "SELL", cluster_capital)
                        else:
                            result = execute_real_trade(self._user_id, market, "SELL", cluster_capital)
                        if result.get("success"):
                            real_price = result.get("trade", {}).get("price") or price
                            if cid:
                                close_result = potjes_svc.close_cluster(self._user_id, cid, real_price)
                                actions_this_cycle.append(
                                    f"SELL cluster {cid[:6]} ({close_result.get('n_pots_closed',0)} pots, {market}) "
                                    f"@ €{real_price:.4f} netto €{close_result.get('total_netto', 0):+.4f}"
                                )
                                processed_clusters.add(cid)
                            else:
                                close_result = potjes_svc.close_pot(self._user_id, pot["id"], real_price)
                                actions_this_cycle.append(
                                    f"SELL {pot['id']} ({market}) @ €{real_price:.4f} netto €{close_result.get('netto', 0):+.4f}"
                                )
                            # v7_shadow_removed_001 — Shadow-close block removed.

                # v7_shadow_removed_001 — Shadow-activatie block removed (dead code cleanup).

            # 2. BUY check op deze market — max 1 potje per cycle GLOBAAL (over alle coins)
            #    v6_buy_cooldown_001 — Plus: minimaal cooldown per markt tussen 2 BUYs
            #    v7_buy_cooldown_15min_001 — verhoogd van 5 min → 15 min matching candle.
            #    Voorheen: trader kocht binnen 1 kwartier meerdere pots van dezelfde coin
            #    bij drop → volgende (grotere) dip werd niet benut. 15 min = 1 candle-cycle
            #    per markt per user (users kopen wel onafhankelijk op zelfde trigger).
            #    v10_buy_cooldown_blueprint_001 — cooldown-waarde nu uit blueprint
            #    zodat Willem het kan tweaken via de admin-UI zonder code-change.
            _bp_cd = None
            try:
                from pathlib import Path as _P
                import json as _j
                _bp_fp = _P(__file__).parent / "blueprints" / "spark_trader.json"
                if _bp_fp.exists():
                    _bp = _j.load(open(_bp_fp))
                    _bp_cd = _bp.get("buy_cooldown_sec_per_market")
            except Exception:
                pass
            BUY_COOLDOWN_SEC = int(_bp_cd) if _bp_cd else 900  # default 15 min (per markt per user)
            EUR_COOLDOWN_SEC = 1800
            last_buy_ts = self._last_buy_per_market.get(market)
            now = datetime.now(timezone.utc)
            in_cooldown = False
            cooldown_left = 0
            if last_buy_ts:
                elapsed = (now - last_buy_ts).total_seconds()
                if elapsed < BUY_COOLDOWN_SEC:
                    in_cooldown = True
                    cooldown_left = int(BUY_COOLDOWN_SEC - elapsed)

            # v7_eur_cooldown_001 — globale EUR-cooldown na eerdere INSUFFICIENT_EUR_BALANCE
            in_eur_cooldown = False
            eur_cooldown_left = 0
            if self._last_insufficient_eur_ts:
                eur_elapsed = (now - self._last_insufficient_eur_ts).total_seconds()
                if eur_elapsed < EUR_COOLDOWN_SEC:
                    in_eur_cooldown = True
                    eur_cooldown_left = int(EUR_COOLDOWN_SEC - eur_elapsed)

            buy_decision = _simple_decision(context_candles, position=None, trade_amount=self._trade_amount)
            # v7_gap_merge_001 — bevestigings-filter: Bollinger BUY alleen doorlaten als
            # laatste candle een structuur-omslag toont (groene candle volledig boven
            # vorige rode). Voorkomt 'kopen op piek' in dalende markt zoals Willem meldde.
            gap_check = _gap_breakout_check(context_candles)
            # v11_gap_filter_conditional_001 — Filter alleen blokkerend bij ondiepe dips.
            # Bij grote dips (>= threshold uit blueprint) mag Bollinger-BUY door zonder
            # gap-bevestiging. Backtest 10d juli 2026: 3.0% gaf 6x meer trades met 75%
            # win-rate. Overwrite via blueprint zonder code-change.
            _gap_override_pct = 999.0
            try:
                from pathlib import Path as _P
                import json as _j
                _bp_fp = _P(__file__).parent / "blueprints" / "spark_trader.json"
                if _bp_fp.exists():
                    _bp = _j.load(open(_bp_fp))
                    _gap_override_pct = float(_bp.get("gap_filter_dip_override_pct", 999.0))
            except Exception:
                pass
            _dip_pct = buy_decision.get("drop_from_high_pct", 0)
            if buy_decision.get("action") == "BUY" and gap_check["signal"] != "BUY" and _dip_pct < _gap_override_pct:
                buy_decision["action"] = "HOLD"
                buy_decision["reason"] += f" | Wacht op gap-bevestiging ({gap_check['reason']}, dip {_dip_pct:.1f}% < {_gap_override_pct:.1f}%)"
                buy_decision["gap_filter_blocked"] = True
            elif buy_decision.get("action") == "BUY" and gap_check["signal"] != "BUY" and _dip_pct >= _gap_override_pct:
                buy_decision["reason"] += f" | Gap-filter overruled: dip {_dip_pct:.1f}% \u2265 {_gap_override_pct:.1f}% (echte dip)"
                buy_decision["gap_filter_overruled"] = True
            elif buy_decision.get("action") == "BUY" and gap_check["signal"] == "BUY":
                buy_decision["reason"] += f" | \u2713 gap-bevestigd: {gap_check['reason']}"
                buy_decision["gap_confirmed"] = True
            buy_decision["gap_check"] = gap_check
            if market_context:
                buy_decision = context_service.apply_context_to_decision(buy_decision, market_context, price, user_id=self._user_id)
            if buy_decision["action"] == "BUY" and in_cooldown:
                buy_decision["reason"] += f" | Skipped: BUY-cooldown {cooldown_left}s op {market}"
                buy_decision["action"] = "HOLD"
            if buy_decision["action"] == "BUY" and in_eur_cooldown:
                buy_decision["reason"] += f" | Skipped: EUR-cooldown {eur_cooldown_left}s (eerder onvoldoende EUR)"
                buy_decision["action"] = "HOLD"
            # v10_anker_hook_001 — Gap-up guard. Log-only als flag off/log_only,
            # skip als action=skip. Elke check gaat via LogAgent (topic=anker_check).
            if buy_decision["action"] == "BUY":
                try:
                    from .anker_service import check_gap_up, log_anker_event
                    anker_dec = check_gap_up(market, price)
                    if anker_dec.get("enabled"):
                        log_anker_event(market, anker_dec, user_id=self._user_id or "system")
                    buy_decision["anker_check"] = {
                        "enabled": anker_dec.get("enabled"),
                        "anker": anker_dec.get("anker"),
                        "delta_pct": anker_dec.get("delta_pct"),
                        "action": anker_dec.get("action"),
                        "above_threshold": anker_dec.get("above_threshold", False),
                    }
                    if not anker_dec.get("allow"):
                        buy_decision["reason"] += f" | Skipped: anker-guard ({anker_dec.get('reason')})"
                        buy_decision["action"] = "HOLD"
                        buy_decision["anker_blocked"] = True
                except Exception as _ae:
                    # Anker mag NOOIT de trader blokkeren als hij zelf crasht (fail-open)
                    logger.warning(f"anker check failed for {market}: {_ae}")
            if buy_decision["action"] == "BUY":
                # v7_pot_cluster_001 — Cluster pots samen tot Bitvavo min-order gehaald
                # is. Voorheen: 1 pot × €5,08 = Bitvavo weigert SOL/ADA orders (min €5-7).
                # Nu: neem meerdere pots samen zodat Σcapital ≥ min_order.
                try:
                    min_order = get_market_min_quote(market)
                except Exception:
                    min_order = 5.0
                cluster = potjes_svc.get_next_buy_cluster(self._user_id, market, min_order)
                if cluster and self._auto_trade:
                    if self._use_mock:
                        result = execute_mock_trade(self._user_id, market, "BUY", cluster["total_capital"])
                    else:
                        result = execute_real_trade(self._user_id, market, "BUY", cluster["total_capital"])
                    if result.get("success"):
                        real_entry = result.get("trade", {}).get("price") or price
                        # v11_pot_registration_safety_001 — Bug A fix.
                        # Bitvavo BUY is geslaagd — potjes registratie MOET slagen anders
                        # coin gekocht zonder pot-tracking (silent loss). Wrap in try/except,
                        # log kritisch bij faal, en persist direct zodat frontend het ziet.
                        cluster_opened = False
                        try:
                            open_result = potjes_svc.open_cluster(
                                self._user_id, cluster["pot_ids"], real_entry,
                                cluster["cluster_id"], self._cycles,
                                trade_id=result.get("trade", {}).get("trade_id"),
                                market=market,
                            )
                            cluster_opened = bool(open_result.get("success"))
                        except Exception as _oe:
                            logger.error(
                                f"[CRITICAL] open_cluster FAILED na Bitvavo BUY success! "
                                f"user={self._user_id} market={market} entry=€{real_entry} "
                                f"pot_ids={cluster['pot_ids']} err={_oe}"
                            )
                        if not cluster_opened:
                            # Fallback: probeer per potje open_pot zodat er tenminste
                            # registratie is (voorkomt "coin gekocht maar geen pot"-scenario).
                            fallback_opened = []
                            for pid in cluster["pot_ids"]:
                                try:
                                    p_capital_share = float(cluster["total_capital"]) / max(len(cluster["pot_ids"]), 1)
                                    r = potjes_svc.open_pot(
                                        self._user_id, pid, real_entry, self._cycles,
                                        trade_id=result.get("trade", {}).get("trade_id"),
                                        amount_eur=p_capital_share,
                                        market=market,
                                    )
                                    if r:
                                        fallback_opened.append(pid)
                                except Exception as _fe:
                                    logger.error(f"[CRITICAL] fallback open_pot faalde voor {pid}: {_fe}")
                            # Publiceer event zodat frontend & Willem direct zien dat er iets fout ging
                            try:
                                notif_file = DATA_DIR / "trade" / "event_notifications.json"
                                existing = []
                                if notif_file.exists():
                                    existing = json.loads(notif_file.read_text())
                                existing.append({
                                    "type": "buy_registration_failure",
                                    "severity": "CRITICAL" if not fallback_opened else "WARN",
                                    "user_id": self._user_id,
                                    "market": market,
                                    "entry_price": real_entry,
                                    "total_capital": cluster["total_capital"],
                                    "cluster_id": cluster["cluster_id"],
                                    "requested_pot_ids": cluster["pot_ids"],
                                    "fallback_opened_pot_ids": fallback_opened,
                                    "trade_id": result.get("trade", {}).get("trade_id"),
                                    "timestamp": datetime.now(timezone.utc).isoformat(),
                                    "message": (
                                        f"Bitvavo BUY €{cluster['total_capital']:.2f} {market} @ €{real_entry:.4f} "
                                        f"is geslaagd, maar open_cluster faalde. "
                                        f"{len(fallback_opened)}/{len(cluster['pot_ids'])} potjes via fallback geopend."
                                    ),
                                })
                                notif_file.write_text(json.dumps(existing[-200:], indent=2, ensure_ascii=False))
                            except Exception as _ne:
                                logger.error(f"kon buy_registration_failure notif niet schrijven: {_ne}")
                            cluster_opened = bool(fallback_opened)
                        self._last_buy_per_market[market] = now
                        # v10_buy_cooldown_persist_001 — direct persisteren na BUY
                        # zodat cooldown herstart-safe is (was voorheen alleen in-memory).
                        try:
                            self._persist_state()
                        except Exception:
                            pass
                        # v11_pot_registration_safety_001 — signaal aan frontend polling
                        # zodat UI direct kan verversen na een succesvolle BUY (was: alleen
                        # zichtbaar na volgende poll-cycle, kon 30s+ vertraging geven).
                        try:
                            trigger_file = DATA_DIR / "trade" / "ui_refresh_trigger.json"
                            trigger_file.write_text(json.dumps({
                                "user_id": self._user_id,
                                "market": market,
                                "action": "BUY",
                                "cluster_id": cluster["cluster_id"],
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                            }))
                        except Exception:
                            pass
                        actions_this_cycle.append(
                            f"BUY cluster {cluster['cluster_id'][:6]} ({cluster['n_pots']} pots, "
                            f"€{cluster['total_capital']:.2f}) {market} @ €{real_entry:.4f}"
                            + ("" if cluster_opened else " [WARN: pot-registratie faalde]")
                        )
                    else:
                        # v7_eur_cooldown_001 — bij INSUFFICIENT_EUR_BALANCE: activeer 30-min cooldown
                        if result.get("error_code") == "INSUFFICIENT_EUR_BALANCE":
                            self._last_insufficient_eur_ts = now
                            logger.warning(
                                f"[buy] EUR-cooldown 30min actief voor {self._user_id} — "
                                f"€{result.get('eur_available',0):.2f} < €{cluster['total_capital']:.2f}"
                            )
                        buy_decision["reason"] += f" | BUY faalde: {result.get('error','?')[:80]}"
                elif not cluster:
                    buy_decision["reason"] += (
                        f" | Skipped: geen cluster met ≥€{min_order:.2f} voor {market} "
                        f"(geen vrije pots of te weinig volume)"
                    )

            decision = buy_decision
            decision["market"] = market
            decision["cycle"] = self._cycles
            decision["timestamp"] = datetime.now(timezone.utc).isoformat()
            decision["executed"] = len(actions_this_cycle) > 0
            decision["execution"] = " | ".join(actions_this_cycle) if actions_this_cycle else ""
            decision["potjes_summary"] = potjes_svc.get_summary(self._user_id)
        else:
            from modules.trade import context_service
            market_context = context_service.get_cached(market)
            decision = _simple_decision(context_candles, position=self._position, trade_amount=self._trade_amount)
            if market_context:
                decision = context_service.apply_context_to_decision(decision, market_context, price, user_id=self._user_id)
            decision["market"] = market
            decision["cycle"] = self._cycles
            decision["timestamp"] = datetime.now(timezone.utc).isoformat()
            decision["executed"] = False

            # Apply position state updates from decision
            pos_update = decision.get("position_update", {})
            if pos_update.get("close"):
                pass
            elif pos_update.get("highest_price") is not None:
                self._position["highest_price"] = pos_update["highest_price"]
                self._position["trailing_active"] = pos_update.get("trailing_active", self._position.get("trailing_active", False))

            # Auto trade (single-position mode) — alleen primaire market
            if self._auto_trade and decision["action"] in ("BUY", "SELL") and market == self._market:
                can_execute = (decision["action"] == "BUY" and not self._position["is_open"]) or \
                              (decision["action"] == "SELL" and self._position["is_open"])
                if can_execute:
                    if self._use_mock:
                        result = execute_mock_trade(self._user_id, market, decision["action"], self._trade_amount)
                    else:
                        result = execute_real_trade(self._user_id, market, decision["action"], self._trade_amount)
                    decision["executed"] = result.get("success", False)
                    decision["execution"] = result.get("message", "")
                    if decision["executed"]:
                        if decision["action"] == "BUY":
                            self._position = {"is_open": True, "entry_price": price, "highest_price": price, "trailing_active": False}
                        else:
                            self._position = {"is_open": False, "entry_price": None, "highest_price": None, "trailing_active": False}
                else:
                    decision["execution"] = f"Skipped: {'al in positie' if decision['action'] == 'BUY' else 'geen open positie'}"

        self._decisions.append(decision)
        if len(self._decisions) > 200:
            self._decisions.pop(0)

        logger.info(f"Cycle #{self._cycles} | {market} €{price:.2f} | {decision['action']}")


_monitor = MonitorService(user_id="user-001")

# v4_per_user_bot_001 — Registry van per-user bots
_registry: Dict[str, MonitorService] = {}
_registry_lock = threading.Lock()


def get_monitor() -> MonitorService:
    """Back-compat: legacy single-monitor (user-001)"""
    return _monitor


def get_user_monitor(user_id: str) -> MonitorService:
    """v4_per_user_bot_001: haal of maak monitor voor specifieke user.

    v7_legacy_alias_001 — user-001 is de legacy singleton (`_monitor`). Return altijd
    dezelfde instance zodat status-endpoints en de echt-draaiende thread consistent zijn.
    Voorheen: get_user_monitor("user-001") maakte een 2e instance in _registry met
    defaults → UI zag "running:false" terwijl de echte monitor draaide.
    """
    if user_id == "user-001":
        return _monitor
    with _registry_lock:
        if user_id not in _registry:
            _registry[user_id] = MonitorService(user_id=user_id)
        return _registry[user_id]


# v4_registry_persist_001 — persist per-user bots zodat ze auto-resumen na restart
REGISTRY_STATE_FILE = DATA_DIR / "trade" / "bots_registry_state.json"

# v5_bot_proactive_register_001 — users die proactief zichtbaar willen zijn in Analytics
# (bot komt in _registry zonder te starten zodat admin de slot ziet)
REGISTERED_USERS_FILE = DATA_DIR / "trade" / "registered_users.json"


def _load_registered_users() -> list:
    data = load_json(REGISTERED_USERS_FILE, default={"users": []})
    return data.get("users", [])


def _save_registered_users(users: list):
    REGISTERED_USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    save_json(REGISTERED_USERS_FILE, {"users": sorted(set(users))})


def register_user_bot(user_id: str) -> dict:
    """Proactief: voeg bot toe aan _registry zonder te starten. Persistent."""
    get_user_monitor(user_id)  # zorgt voor instance in _registry
    users = _load_registered_users()
    if user_id not in users:
        users.append(user_id)
        _save_registered_users(users)
    return {"success": True, "registered": True, "user_id": user_id}


def unregister_user_bot(user_id: str) -> dict:
    """Verwijder bot uit visibility-lijst (bot zelf blijft bestaan in registry tot stop)."""
    users = _load_registered_users()
    if user_id in users:
        users = [u for u in users if u != user_id]
        _save_registered_users(users)
    return {"success": True, "unregistered": True, "user_id": user_id}


def is_registered(user_id: str) -> bool:
    return user_id in _load_registered_users()


# v6_auto_provision_001 — Wanneer een user een token koopt of ontvangt,
# moet hij direct kunnen handelen. Deze helper doet alles in 1 call:
#   1. register_user_bot (proactief zichtbaar in admin Analytics)
#   2. monitor-instance aanmaken met defaults (markets, trade_amount=10, auto_trade=True)
#   3. use_mock standaard FALSE (zelfde als de 5 live-bots) — token-holder mag echt handelen
#   4. NIET autostart: bot staat klaar maar wacht op user "start"-knop in UI
def auto_provision_bot_for_token_holder(
    user_id: str,
    use_mock: bool = False,
    auto_trade: bool = True,
    autostart: bool = False,
    force_reconfigure: bool = False,
) -> dict:
    """Idempotent: meerdere calls voor dezelfde user veranderen niets als hij al heeft.

    force_reconfigure=True → overschrijft interval/candle/markets/trade_amount met
    huidige defaults (voor migratie na code-updates).
    """
    # 1. Register (idempotent)
    register_user_bot(user_id)

    # 2. Monitor instance (idempotent — get_user_monitor maakt aan als niet bestaat)
    m = get_user_monitor(user_id)

    # 3. Defaults voor nieuwe bot — alleen toepassen als nog niet expliciet ingesteld
    already_running = bool(getattr(m, "_running", False))
    has_been_configured = bool(getattr(m, "_user_configured", False)) and not force_reconfigure

    if not has_been_configured:
        try:
            # v7_bot_defaults_align_001 — alle nieuwe bots identiek geconfigureerd:
            # - markets: met -EUR suffix (anders vindt Bitvavo ze niet)
            # - interval: 300s (5 min tick — snel genoeg maar niet spammy)
            # - candle_interval: 15m (consistent met Willem)
            # - trade_amount: dynamisch = huidige token-prijs (fallback €6.32)
            if "WATCHLIST_COINS" in globals():
                m._markets = [f"{c}-EUR" for c in WATCHLIST_COINS]
                m._market = m._markets[0] if m._markets else m._market
            m._interval = 300
            m._candle_interval = "15m"
            m._auto_trade = bool(auto_trade)
            m._use_mock = bool(use_mock)
            # v7_dynamic_defaults_001 — trade_amount = altijd huidige token-prijs
            try:
                from modules.shop.routes import get_dynamic_price
                _p = float(get_dynamic_price())
                m._trade_amount = _p if _p > 0 else 5.08
            except Exception:
                m._trade_amount = float(getattr(m, "_trade_amount", 5.08) or 5.08)
            m._use_potjes = True
            m._user_configured = True
        except Exception as e:
            logger.warning(f"auto-provision config-set failed for {user_id}: {e}")

    # 4. Optioneel autostart
    started = False
    if autostart and not already_running:
        try:
            m.start()
            started = True
        except Exception as e:
            logger.warning(f"auto-provision autostart failed for {user_id}: {e}")

    # Persist registry
    try:
        _persist_registry()
    except Exception:
        pass

    # v7_shadow_removed_001 — Shadow auto-ensure block removed.

    return {
        "success": True,
        "user_id": user_id,
        "registered": True,
        "auto_trade": getattr(m, "_auto_trade", None),
        "use_mock": getattr(m, "_use_mock", None),
        "configured": getattr(m, "_user_configured", False),
        "started": started,
        "running": bool(getattr(m, "_running", False)),
    }


def resume_registered_users():
    """Bij backend startup: ensure registered users hebben monitor-instance (niet running)."""
    for uid in _load_registered_users():
        try:
            get_user_monitor(uid)
        except Exception as e:
            logger.warning(f"Registered user {uid} ensure failed: {e}")


def _persist_registry():
    """Sla alle registry-bots op (running EN stopped) zodat:
    - running bots auto-resumen bij restart
    - stopped bots herkenbaar blijven (running:false) → niet auto-restarted

    v6_resume_persist_merge_001 — MERGE met bestaand bestand i.p.v. overschrijven.
    Plus file-level lock zodat parallelle stop/start calls niet elkaars writes
    overschrijven (read-modify-write race).
    """
    from modules.core.storage import _get_lock
    file_lock = _get_lock(str(REGISTRY_STATE_FILE))
    try:
        REGISTRY_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with file_lock:
            # 1. Lees bestaand bestand (kan bots bevatten die nog niet in-memory zijn)
            existing_by_uid: Dict[str, Dict] = {}
            if REGISTRY_STATE_FILE.exists():
                try:
                    with open(REGISTRY_STATE_FILE) as f:
                        data = json.load(f)
                    for b in data.get("bots", []):
                        uid = b.get("user_id")
                        if uid:
                            existing_by_uid[uid] = b
                except Exception as e:
                    logger.warning(f"Registry read-before-merge failed: {e}")

            # 2. Overschrijf/voeg toe met in-memory state
            with _registry_lock:
                for uid, m in _registry.items():
                    if uid == "user-001":
                        continue  # legacy heeft eigen state file
                    existing_by_uid[uid] = {
                        "user_id": uid,
                        "running": bool(m._running),
                        "interval": m._interval,
                        "market": m._market,
                        "markets": list(m._markets),
                        "candle_interval": m._candle_interval,
                        "auto_trade": m._auto_trade,
                        "trade_amount": m._trade_amount,
                        "use_mock": m._use_mock,
                        "use_potjes": m._use_potjes,
                        "pot_count": _read_pot_count(uid) if m._use_potjes else None,
                    }

            # 3. Schrijf merged lijst terug
            bots = list(existing_by_uid.values())
            with open(REGISTRY_STATE_FILE, "w") as f:
                json.dump({"bots": bots, "saved_at": datetime.now(timezone.utc).isoformat()}, f, indent=2)
    except Exception as e:
        logger.warning(f"Registry persist failed: {e}")


def resume_registry_bots():
    """Bij backend startup: hervat alle eerder-running registry-bots.

    v6_resume_respect_stop_001 — Respecteer expliciet als user de bot gestopt heeft:
    de stop() flow verwijdert de bot uit `bots` (via _persist_registry die alleen
    running bots opslaat). Als een bot toch in de file staat met `running: false`,
    skippen we 'm ook. Anders zou een eerdere bug die `running:false` schrijft een
    eindeloze auto-restart loop veroorzaken.
    """
    if not REGISTRY_STATE_FILE.exists():
        return {"resumed": 0, "reason": "no state"}
    try:
        with open(REGISTRY_STATE_FILE) as f:
            data = json.load(f)
        resumed = 0
        skipped = []
        for b in data.get("bots", []):
            uid = b.get("user_id")
            if not uid:
                continue
            # NIEUW: respect "running: false" als expliciet aanwezig
            if b.get("running") is False:
                skipped.append(uid)
                continue
            m = get_user_monitor(uid)
            m.start(
                interval=b["interval"], market=b["market"], markets=b.get("markets"),
                candle_interval=b["candle_interval"], user_id=uid,
                auto_trade=b["auto_trade"], trade_amount=b["trade_amount"],
                use_mock=b["use_mock"], use_potjes=b["use_potjes"],
            )
            resumed += 1
        logger.info(f"Registry resume: {resumed} resumed, {len(skipped)} skipped (user-stopped): {skipped}")
        return {"resumed": resumed, "skipped_user_stopped": skipped}
    except Exception as e:
        logger.error(f"Registry resume failed: {e}")
        return {"resumed": 0, "error": str(e)}


def list_running_bots() -> List[Dict]:
    """Status van alle actieve bots — voor admin Trade Analytics."""
    out = []
    with _registry_lock:
        bots = list(_registry.values())
    # Legacy monitor altijd toevoegen indien niet al in registry
    if _monitor._user_id not in _registry:
        bots.insert(0, _monitor)
    for m in bots:
        try:
            out.append(m.get_status())
        except Exception:
            pass
    return out
