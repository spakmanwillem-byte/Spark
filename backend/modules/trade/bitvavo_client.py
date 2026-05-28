"""
Bitvavo Client (v6_bitvavo_client_001 — 28 mei 2026)
=====================================================
Centralised Bitvavo API client met signed requests.
Werkt WEL vanaf preview environment (eerdere handoff dacht van niet).

Bron: https://docs.bitvavo.com/#tag/General
"""
import hmac
import hashlib
import json as _json
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, List, Optional

DATA_ROOT = Path(__file__).parent.parent.parent / "data"
BASE_URL = "https://api.bitvavo.com/v2"
_PRICE_CACHE = {}
_PRICE_TTL = 30  # 30s


def _load_credentials(user_id: str = "user-001") -> Optional[Dict]:
    """Lees Bitvavo API key + secret uit user settings."""
    settings_path = DATA_ROOT / "users" / user_id / "settings.json"
    if not settings_path.exists():
        return None
    try:
        s = _json.loads(settings_path.read_text())
        bv = s.get("integrations", {}).get("bitvavo", {})
        if bv.get("api_key") and bv.get("api_secret"):
            return {"api_key": bv["api_key"], "api_secret": bv["api_secret"]}
    except Exception:
        pass
    return None


def _signed_request(api_key: str, api_secret: str, method: str, path: str, body: str = "") -> Dict:
    """Voer signed Bitvavo request uit."""
    ts_ms = str(int(time.time() * 1000))
    sig_input = f"{ts_ms}{method.upper()}/v2{path}{body}"
    sig = hmac.new(api_secret.encode(), sig_input.encode(), hashlib.sha256).hexdigest()
    headers = {
        "Bitvavo-Access-Key": api_key,
        "Bitvavo-Access-Signature": sig,
        "Bitvavo-Access-Timestamp": ts_ms,
        "Bitvavo-Access-Window": "10000",
        "User-Agent": "curl/8.0",
        "Content-Type": "application/json",
    }
    url = f"{BASE_URL}{path}"
    data = body.encode() if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method.upper())
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return _json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"error": e.code, "detail": e.read().decode("utf-8", "ignore")[:300]}
    except Exception as e:
        return {"error": "network", "detail": str(e)[:200]}


def _public_get(path: str) -> Dict:
    """Public endpoint (no auth)."""
    try:
        req = urllib.request.Request(f"{BASE_URL}{path}", headers={"User-Agent": "curl/8.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            return _json.loads(r.read())
    except Exception as e:
        return {"error": "network", "detail": str(e)[:200]}


def get_price(market: str) -> Optional[float]:
    """Get spot-prijs voor market (cached 30s)."""
    now = time.time()
    if market in _PRICE_CACHE:
        ts, price = _PRICE_CACHE[market]
        if now - ts < _PRICE_TTL:
            return price
    res = _public_get(f"/ticker/price?market={market}")
    if isinstance(res, dict) and "price" in res:
        price = float(res["price"])
        _PRICE_CACHE[market] = (now, price)
        return price
    return None


def get_balance(user_id: str = "user-001") -> List[Dict]:
    """Returns list of {symbol, available, inOrder} dicts."""
    creds = _load_credentials(user_id)
    if not creds:
        return []
    res = _signed_request(creds["api_key"], creds["api_secret"], "GET", "/balance")
    if isinstance(res, list):
        return res
    return []


def get_balance_summary(user_id: str = "user-001") -> Dict:
    """Computes total EUR value across all holdings.
    Returns {total_eur, breakdown: {symbol: eur_value}, eur_cash, holdings: [...]}.
    """
    balances = get_balance(user_id)
    total = 0.0
    eur_cash = 0.0
    holdings = []
    breakdown = {}
    for b in balances:
        sym = b.get("symbol")
        try:
            avail = float(b.get("available", "0") or 0)
            inord = float(b.get("inOrder", "0") or 0)
        except (ValueError, TypeError):
            continue
        qty = avail + inord
        if qty <= 0:
            continue
        if sym == "EUR":
            eur_val = qty
            price = 1.0
        else:
            price = get_price(f"{sym}-EUR") or 0
            eur_val = qty * price
        if eur_val < 0.01:
            continue
        total += eur_val
        breakdown[sym] = round(eur_val, 2)
        holdings.append({
            "symbol": sym,
            "qty": qty,
            "available": avail,
            "in_order": inord,
            "price_eur": price,
            "eur_value": round(eur_val, 2),
        })
        if sym == "EUR":
            eur_cash = qty
    holdings.sort(key=lambda x: -x["eur_value"])
    return {
        "total_eur": round(total, 2),
        "eur_cash": round(eur_cash, 2),
        "crypto_value_eur": round(total - eur_cash, 2),
        "breakdown": breakdown,
        "holdings": holdings,
        "fetched_at": time.time(),
    }


def place_order(api_key: str, api_secret: str, market: str, side: str, amount: float, order_type: str = "market") -> Dict:
    """Plaats market order. side='buy' of 'sell'."""
    payload = {
        "market": market,
        "side": side,
        "orderType": order_type,
    }
    # amount in EUR voor buy, in coin voor sell
    if side == "buy":
        payload["amountQuote"] = str(round(amount, 2))
    else:
        payload["amount"] = str(amount)
    body = _json.dumps(payload, separators=(",", ":"))
    return _signed_request(api_key, api_secret, "POST", "/order", body)
