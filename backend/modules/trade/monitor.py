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
from datetime import datetime, timezone
from typing import Dict, Optional, List
from pathlib import Path
from modules.core.storage import load_json, save_json

logger = logging.getLogger("spark_monitor")

# Bitvavo public API
BITVAVO_URL = "https://api.bitvavo.com/v2"

# Watchlist coins
WATCHLIST_COINS = ["BCH", "BTC", "ETH", "SOL", "ADA"]
WATCHLIST_NAMES = {
    "BCH": "Bitcoin Cash",
    "BTC": "Bitcoin",
    "ETH": "Ethereum",
    "SOL": "Solana",
    "ADA": "Cardano",
}

DATA_DIR = Path(__file__).parent.parent.parent / "data"
SETTINGS_DIR = DATA_DIR / "users"


def fetch_candles(market: str, interval: str = "1h", limit: int = 30) -> List[Dict]:
    """Fetch candles from Bitvavo public API (no auth needed)"""
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
            return candles
    except Exception as e:
        logger.error(f"Candle fetch error: {e}")
    return []


def fetch_tickers(coins: List[str] = None) -> List[Dict]:
    """Fetch live ticker prices from Bitvavo (public, no auth)"""
    if coins is None:
        coins = WATCHLIST_COINS
    results = []
    try:
        url = f"{BITVAVO_URL}/ticker/24h"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
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
    except Exception as e:
        logger.error(f"Ticker fetch error: {e}")
    # Sort: BCH first, then by market cap (BTC, ETH, SOL, ADA)
    order = {c: i for i, c in enumerate(coins)}
    results.sort(key=lambda x: order.get(x["symbol"], 99))
    return results


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


def execute_real_trade(user_id: str, market: str, side: str, amount_eur: float) -> Dict:
    """Execute a real trade via Bitvavo authenticated API"""
    settings_file = SETTINGS_DIR / user_id / "settings.json"
    settings = load_json(settings_file, default={})
    bitvavo = settings.get("integrations", {}).get("bitvavo", {})

    api_key = bitvavo.get("api_key")
    api_secret = bitvavo.get("api_secret")
    if not api_key or not api_secret:
        return {"success": False, "error": "Geen Bitvavo API credentials gevonden"}

    try:
        timestamp = int(time.time() * 1000)
        body = {
            "market": market,
            "side": side.lower(),
            "orderType": "market",
        }
        if side.lower() == "buy":
            body["amountQuote"] = str(round(amount_eur, 8))
        else:
            body["amount"] = str(round(amount_eur, 8))

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

        resp = requests.post(f"{BITVAVO_URL}/order", headers=headers, json=body, timeout=10)
        if resp.status_code == 200:
            result = resp.json()
            filled = float(result.get("filledAmount", 0))
            filled_quote = float(result.get("filledAmountQuote", 0))
            avg_price = filled_quote / filled if filled > 0 else 0
            fee_paid = float(result.get("feePaid", 0))
            fee_currency = result.get("feeCurrency", "EUR")

            trade_id = result.get("orderId", str(uuid.uuid4())[:8])
            now = datetime.now(timezone.utc).isoformat()
            trade = {
                "trade_id": trade_id,
                "run_id": "manual",
                "timestamp": now,
                "action": side.upper(),
                "market": market,
                "order_id": trade_id,
                "amount": filled_quote if side.lower() == "buy" else filled,
                "price": avg_price,
                "filled": filled,
                "status": result.get("status", "filled"),
                "mock": False,
                "success": True,
                "error": None,
                "fee": fee_paid,
                "fee_currency": fee_currency,
            }

            history_file = DATA_DIR / "wallet" / "trade_history" / f"{user_id}.json"
            data = load_json(history_file, default={"trades": []})
            data["trades"].append(trade)
            save_json(history_file, data)

            return {"success": True, "trade": trade, "message": f"LIVE {side.upper()} uitgevoerd @ €{avg_price:.2f} (fee €{fee_paid:.4f})"}
        else:
            return {"success": False, "error": f"Bitvavo API error: {resp.status_code} - {resp.text}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


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
    """Fetch live Bitvavo account balances (all coins)."""
    settings = load_json(SETTINGS_DIR / user_id / "settings.json", default={})
    bitvavo = settings.get("integrations", {}).get("bitvavo", {})
    api_key = bitvavo.get("api_key")
    api_secret = bitvavo.get("api_secret")
    if not api_key or not api_secret:
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
    return {"success": True, "balances": enriched, "total_eur": round(total_eur, 2)}


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


# Bitvavo taker fee (market orders)
BITVAVO_TAKER_FEE = 0.0025  # 0.25%


def _simple_decision(candles: List[Dict], position: Optional[Dict] = None, trade_amount: float = 5.0) -> Dict:
    """
    Decision engine with trailing stop + fee-aware profit guard.
    - Enters LONG bij prijs onder lower Bollinger band (2σ)
    - Activeert trailing stop bij +1% winst
    - Verkoopt bij -0.4% drop vanaf hoogste punt, MITS netto winst na fees > €0.01
    - NOOIT verkopen met verlies (Willem's regel)

    Args:
        candles: Laatste N candles (min 5)
        position: Huidige positie state (None = geen positie)
        trade_amount: EUR bedrag per trade
    """
    if len(candles) < 5:
        return {"action": "HOLD", "reason": "Te weinig data", "confidence": 0}

    closes = [c["close"] for c in candles[-20:]]
    mean = sum(closes) / len(closes)
    variance = sum((x - mean) ** 2 for x in closes) / len(closes)
    std = variance ** 0.5 if variance > 0 else 0.001
    price = candles[-1]["close"]
    lower = mean - 2 * std
    upper = mean + 2 * std

    base = {
        "price": price,
        "mean": round(mean, 2),
        "lower": round(lower, 2),
        "upper": round(upper, 2),
    }

    # ========== HEBBEN WE EEN POSITIE? ==========
    if position and position.get("is_open"):
        entry = position["entry_price"]
        highest = max(position.get("highest_price", entry), price)
        profit_pct = (price - entry) / entry
        # Absolute winst in EUR (bruto)
        bruto_profit = trade_amount * profit_pct
        # Fees: 0.25% buy + 0.25% sell = 0.5% van trade amount
        total_fees = trade_amount * BITVAVO_TAKER_FEE * 2
        netto_profit = bruto_profit - total_fees

        # Trailing stop activation: +1%
        trailing_active = position.get("trailing_active", False) or profit_pct >= 0.01
        # Trailing stop trigger: -0.4% from high
        drop_from_high = (highest - price) / highest if highest else 0

        if trailing_active and drop_from_high >= 0.004:
            # Guard: nooit verkopen bij verlies na fees
            if netto_profit >= 0.01:
                return {
                    **base,
                    "action": "SELL",
                    "reason": f"Trailing stop @ €{price:.2f} (drop -{drop_from_high*100:.2f}% van €{highest:.2f}). Netto: €{netto_profit:.3f}",
                    "confidence": 0.95,
                    "netto_profit": round(netto_profit, 3),
                    "bruto_profit": round(bruto_profit, 3),
                    "fees": round(total_fees, 4),
                    "position_update": {"close": True, "highest_price": highest, "trailing_active": trailing_active},
                }
            else:
                # Winst te klein voor fees, reset trailing en wacht opnieuw
                return {
                    **base,
                    "action": "HOLD",
                    "reason": f"Drop -{drop_from_high*100:.2f}% maar netto €{netto_profit:.3f} <€0.01. Reset trailing.",
                    "confidence": 0.2,
                    "netto_profit": round(netto_profit, 3),
                    "position_update": {"highest_price": highest, "trailing_active": False},
                }

        # Nog in positie, nog geen exit signaal
        return {
            **base,
            "action": "HOLD",
            "reason": f"In positie @ €{entry:.2f}. Nu €{price:.2f} ({profit_pct*100:+.2f}%). Netto €{netto_profit:+.3f}. Trailing: {'AAN' if trailing_active else 'wacht op +1%'}",
            "confidence": 0.5,
            "netto_profit": round(netto_profit, 3),
            "position_update": {"highest_price": highest, "trailing_active": trailing_active},
        }

    # ========== GEEN POSITIE: ZOEK BUY SIGNAAL ==========
    if price <= lower:
        # Te dicht bij upper? Geen ruimte voor winst
        distance_from_upper = (upper - price) / upper if upper > 0 else 1
        if distance_from_upper < 0.015:  # Minder dan 1.5% ruimte tot upper
            return {
                **base,
                "action": "HOLD",
                "reason": f"Lower band geraakt maar te dicht bij upper ({distance_from_upper*100:.1f}% ruimte) — geen winstpotentieel",
                "confidence": 0.2,
            }
        return {
            **base,
            "action": "BUY",
            "reason": f"Prijs €{price:.2f} onder lower band €{lower:.2f}. Ruimte tot upper: {distance_from_upper*100:.1f}%",
            "confidence": min(0.9, (lower - price) / std + 0.5),
            "position_update": {"open": True, "entry_price": price},
        }

    band_pos = (price - lower) / (upper - lower) if (upper - lower) > 0 else 0.5
    return {
        **base,
        "action": "HOLD",
        "reason": f"Prijs €{price:.2f} in band ({band_pos:.0%}). Wacht op lower band.",
        "confidence": 0.3,
        "band_position": round(band_pos, 2),
    }


class MonitorService:
    """Singleton background monitoring service"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        self._initialized = True
        self._running = False
        self._paused = False
        self._thread = None
        self._stop_event = threading.Event()
        self._start_time = None
        self._cycles = 0
        self._interval = 60
        self._market = "BCH-EUR"
        self._candle_interval = "1h"
        self._user_id = "user-001"
        self._decisions = []
        self._last_price = 0
        self._auto_trade = False
        self._trade_amount = 5.0
        self._use_mock = True
        # Position state for trailing stop
        self._position = {"is_open": False, "entry_price": None, "highest_price": None, "trailing_active": False}

    def start(self, interval: int = 60, market: str = "BCH-EUR",
              candle_interval: str = "1h", user_id: str = "user-001",
              auto_trade: bool = False, trade_amount: float = 5.0, use_mock: bool = True) -> Dict:
        with self._lock:
            if self._running:
                return {"success": False, "message": "Monitor draait al", "status": self.get_status()}
            self._interval = max(10, min(interval, 86400))
            self._market = market
            self._candle_interval = candle_interval
            self._user_id = user_id
            self._auto_trade = auto_trade
            self._trade_amount = trade_amount
            self._use_mock = use_mock
            self._stop_event.clear()
            self._running = True
            self._paused = False
            self._start_time = datetime.now(timezone.utc)
            self._cycles = 0
            self._decisions = []
            self._thread = threading.Thread(target=self._loop, daemon=True)
            self._thread.start()
            return {"success": True, "message": f"Monitor gestart ({candle_interval} candles)", "status": self.get_status()}

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
            return {"success": True, "message": "Monitor gestopt", "status": self.get_status()}

    def pause(self) -> Dict:
        with self._lock:
            if not self._running:
                return {"success": False, "message": "Monitor draait niet"}
            self._paused = not self._paused
            state = "gepauzeerd" if self._paused else "hervat"
            return {"success": True, "message": f"Monitor {state}", "status": self.get_status()}

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
            "user_id": self._user_id,
            "auto_trade": self._auto_trade,
            "trade_amount": self._trade_amount,
            "use_mock": self._use_mock,
            "last_price": self._last_price,
            "start_time": self._start_time.isoformat() if self._start_time else None,
            "uptime_seconds": uptime,
            "thread_alive": self._thread.is_alive() if self._thread else False,
            "position": self._position,
        }

    def get_decisions(self, limit: int = 50) -> List[Dict]:
        return list(reversed(self._decisions[-limit:]))

    def _loop(self):
        logger.info(f"Monitor loop started: {self._market} ({self._candle_interval})")
        context_candles = fetch_candles(self._market, self._candle_interval, 50)
        logger.info(f"Pre-loaded {len(context_candles)} context candles")

        while not self._stop_event.is_set():
            if self._paused:
                time.sleep(1)
                continue

            self._cycles += 1
            try:
                new_candles = fetch_candles(self._market, self._candle_interval, 1)
                if new_candles:
                    latest = new_candles[0]
                    self._last_price = latest["close"]

                    if context_candles and context_candles[-1]["timestamp"] != latest["timestamp"]:
                        context_candles.append(latest)
                        if len(context_candles) > 50:
                            context_candles.pop(0)

                    decision = _simple_decision(context_candles, position=self._position, trade_amount=self._trade_amount)
                    decision["cycle"] = self._cycles
                    decision["timestamp"] = datetime.now(timezone.utc).isoformat()
                    decision["executed"] = False

                    # Apply position state updates from decision
                    pos_update = decision.get("position_update", {})
                    if pos_update.get("close"):
                        # We gaan verkopen; sluit de positie na uitvoering
                        pass  # position wordt na SELL exec gereset
                    elif pos_update.get("highest_price") is not None:
                        self._position["highest_price"] = pos_update["highest_price"]
                        self._position["trailing_active"] = pos_update.get("trailing_active", self._position.get("trailing_active", False))

                    # Auto trade
                    if self._auto_trade and decision["action"] in ("BUY", "SELL"):
                        # Extra guard: BUY alleen als geen positie, SELL alleen als positie open
                        can_execute = (decision["action"] == "BUY" and not self._position["is_open"]) or \
                                      (decision["action"] == "SELL" and self._position["is_open"])
                        if can_execute:
                            if self._use_mock:
                                result = execute_mock_trade(self._user_id, self._market, decision["action"], self._trade_amount)
                            else:
                                result = execute_real_trade(self._user_id, self._market, decision["action"], self._trade_amount)
                            decision["executed"] = result.get("success", False)
                            decision["execution"] = result.get("message", "")

                            # Update position na succesvolle trade
                            if decision["executed"]:
                                if decision["action"] == "BUY":
                                    self._position = {
                                        "is_open": True,
                                        "entry_price": decision.get("price", self._last_price),
                                        "highest_price": decision.get("price", self._last_price),
                                        "trailing_active": False,
                                    }
                                else:  # SELL
                                    self._position = {"is_open": False, "entry_price": None, "highest_price": None, "trailing_active": False}
                        else:
                            decision["execution"] = f"Skipped: {'al in positie' if decision['action'] == 'BUY' else 'geen open positie'}"

                    self._decisions.append(decision)
                    if len(self._decisions) > 200:
                        self._decisions.pop(0)

                    logger.info(f"Cycle #{self._cycles} | {self._market} €{self._last_price:.2f} | {decision['action']}")

            except Exception as e:
                logger.error(f"Monitor cycle error: {e}")

            elapsed = 0
            while elapsed < self._interval and not self._stop_event.is_set():
                time.sleep(1)
                elapsed += 1

        logger.info("Monitor loop stopped")


_monitor = MonitorService()


def get_monitor() -> MonitorService:
    return _monitor
