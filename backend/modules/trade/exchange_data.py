"""
Exchange Data Layer (v8_refactor_001)
=====================================
Bitvavo public-API wrappers: candles, tickers, market metadata.

Geëxtraheerd uit monitor.py. Alle functies stateless behalve gedeelde caches
(_CANDLE_CACHE, _TICKER_CACHE_ALL, _MARKETS_CACHE). Deze zijn thread-local safe
omdat GIL sequenceert dict-writes van kleine payloads.

Re-exported vanuit monitor.py voor backwards compat.
"""
from __future__ import annotations

import time
import logging
import requests
from typing import Dict, List

logger = logging.getLogger("spark_monitor")

# ============================================================
# Constanten
# ============================================================

BITVAVO_URL = "https://api.bitvavo.com/v2"

WATCHLIST_COINS = ["BCH", "BTC", "ETH", "SOL", "ADA", "ATOM"]
WATCHLIST_NAMES = {
    "BCH": "Bitcoin Cash",
    "BTC": "Bitcoin",
    "ETH": "Ethereum",
    "SOL": "Solana",
    "ADA": "Cardano",
    "ATOM": "Cosmos",
}

# v4_multi_market_001: candle cache → vermijdt Bitvavo rate-limit bij multi-coin monitoring.
_CANDLE_CACHE: Dict[str, Dict] = {}
_INTERVAL_SECONDS = {"1m": 60, "5m": 300, "15m": 900, "30m": 1800, "1h": 3600, "4h": 14400, "1d": 86400}

# v6_trade_minorder_001: market-info cache (minimumOrderInQuoteAsset per markt).
_MARKETS_CACHE: Dict[str, Dict] = {"data": None, "ts": 0}
_MARKETS_TTL = 3600

# Ticker cache (12s TTL, gedeeld door alle users)
_TICKER_CACHE_ALL: Dict = {"data": None, "ts": 0}

# Fallback-minimums bij offline/cache-miss (EUR).
KNOWN_MIN_QUOTE_FALLBACK = {
    "BTC-EUR": 5.0, "ETH-EUR": 5.0, "SOL-EUR": 5.0,
    "BCH-EUR": 5.0, "ADA-EUR": 5.0, "XRP-EUR": 5.0,
}


# ============================================================
# Market metadata
# ============================================================

def get_market_min_quote(market: str) -> float:
    """v6_trade_minorder_001 — Returnt minimumOrderInQuoteAsset voor een markt.
    Cache → fetch /markets → fallback op KNOWN_MIN_QUOTE_FALLBACK of 5.0 EUR.
    """
    now = time.time()
    cached = _MARKETS_CACHE.get("data")
    if not cached or (now - _MARKETS_CACHE.get("ts", 0)) > _MARKETS_TTL:
        try:
            resp = requests.get(f"{BITVAVO_URL}/markets", timeout=8)
            if resp.status_code == 200:
                arr = resp.json()
                if isinstance(arr, list):
                    cached = {m.get("market"): m for m in arr if m.get("market")}
                    _MARKETS_CACHE["data"] = cached
                    _MARKETS_CACHE["ts"] = now
        except Exception as e:
            logger.warning(f"markets fetch faalde: {e}")
    if cached and market in cached:
        info = cached[market]
        try:
            return float(info.get("minOrderInQuoteAsset") or info.get("minimumOrderInQuoteAsset") or KNOWN_MIN_QUOTE_FALLBACK.get(market, 5.0))
        except Exception:
            pass
    return KNOWN_MIN_QUOTE_FALLBACK.get(market, 5.0)


def get_market_precision(market: str) -> Dict[str, int]:
    """v7_market_precision_001 — Bitvavo precisie-instellingen per markt.

    v13_atom_sell_precision_fix_001 (sessie 54): ATOM-EUR heeft `quantityDecimals=6`
    terwijl code hardcoded 8 gebruikte. Bitvavo weigert dan met errorCode 429
    ("too many decimal digits"). Nu leest hij het echte veld uit de markets-response.
    """
    now = time.time()
    cached = _MARKETS_CACHE.get("data")
    if not cached or (now - _MARKETS_CACHE.get("ts", 0)) > _MARKETS_TTL:
        get_market_min_quote(market)  # herbruik fetch
        cached = _MARKETS_CACHE.get("data")
    if cached and market in cached:
        info = cached[market]
        try:
            # amount-precision uit Bitvavo `quantityDecimals` (aanwezig sinds 2024).
            # Fallback naar 8 als het veld ontbreekt.
            amount_prec = int(info.get("quantityDecimals") or 8)
            price_prec = int(info.get("pricePrecision") or 8)
            return {"amount": amount_prec, "price": price_prec}
        except Exception:
            pass
    return {"amount": 8, "price": 8}


def _round_amount_for_market(amount: float, market: str) -> float:
    """Round coin amount naar market-specifieke precisie (voorkomt errorCode 429)."""
    prec = get_market_precision(market)
    dec = int(prec.get("amount", 8))
    factor = 10 ** dec
    return int(amount * factor) / factor


def _cache_ttl(interval: str) -> int:
    """Cache TTL = candle-interval in seconden."""
    return _INTERVAL_SECONDS.get(interval, 300)


# ============================================================
# Candles + tickers (public)
# ============================================================

def fetch_candles(market: str, interval: str = "1h", limit: int = 30) -> List[Dict]:
    """Fetch candles from Bitvavo public API met TTL-cache."""
    cache_key = f"{market}:{interval}:{limit}"
    now = time.time()
    cached = _CANDLE_CACHE.get(cache_key)
    if cached and (now - cached["ts"]) < _cache_ttl(interval):
        return cached["candles"]
    try:
        url = f"{BITVAVO_URL}/{market}/candles?interval={interval}&limit={limit}"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            raw = resp.json()
            candles = []
            for c in raw:
                if len(c) >= 6:
                    candles.append({
                        "timestamp": c[0],
                        "open": float(c[1]),
                        "high": float(c[2]),
                        "low": float(c[3]),
                        "close": float(c[4]),
                        "volume": float(c[5]),
                    })
            _CANDLE_CACHE[cache_key] = {"candles": candles, "ts": now}
            return candles
        if cached:
            logger.warning(f"Candle fetch HTTP {resp.status_code} voor {market}, gebruik cache ({len(cached['candles'])} candles)")
            return cached["candles"]
    except Exception as e:
        logger.error(f"Candle fetch error {market}: {e}")
        if cached:
            return cached["candles"]
    return []


def fetch_tickers(coins: List[str] = None) -> List[Dict]:
    """v6_ticker_cache_001 — 12s TTL cache voor Bitvavo ticker/24h endpoint."""
    if coins is None:
        coins = WATCHLIST_COINS
    normalized = []
    for c in coins:
        if isinstance(c, str) and "-" in c:
            normalized.append(c.split("-")[0])
        else:
            normalized.append(c)
    coins = normalized

    now = time.time()
    data = None
    if _TICKER_CACHE_ALL.get("data") and (now - _TICKER_CACHE_ALL["ts"]) < 12:
        data = _TICKER_CACHE_ALL["data"]
    if data is None:
        try:
            url = f"{BITVAVO_URL}/ticker/24h"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                _TICKER_CACHE_ALL["data"] = data
                _TICKER_CACHE_ALL["ts"] = now
            elif _TICKER_CACHE_ALL.get("data"):
                data = _TICKER_CACHE_ALL["data"]
        except Exception as e:
            logger.error(f"Ticker fetch error: {e}")
            if _TICKER_CACHE_ALL.get("data"):
                data = _TICKER_CACHE_ALL["data"]

    results = []
    if data:
        wanted = {f"{c}-EUR" for c in coins}
        for t in data:
            if t.get("market") in wanted:
                results.append({
                    "market": t["market"],
                    "symbol": t["market"].split("-")[0],
                    "name": WATCHLIST_NAMES.get(t["market"].split("-")[0], t["market"].split("-")[0]),
                    "last": float(t.get("last", 0)),
                    "open": float(t.get("open", 0)),
                    "high": float(t.get("high", 0)),
                    "low": float(t.get("low", 0)),
                    "volume": float(t.get("volume", 0)),
                    "volumeQuote": float(t.get("volumeQuote", 0)),
                    "bid": float(t.get("bid", 0)),
                    "ask": float(t.get("ask", 0)),
                })
    order = {c: i for i, c in enumerate(coins)}
    results.sort(key=lambda x: order.get(x["symbol"], 99))
    return results


# Alias voor backwards-compat (compileerbaar synoniem)
def get_price(market: str) -> float:
    """Convenience: last-price van een markt via fetch_tickers."""
    base = market.split("-")[0] if "-" in market else market
    for t in fetch_tickers([base]):
        if t.get("market") == market:
            return float(t.get("last") or 0)
    return 0.0
