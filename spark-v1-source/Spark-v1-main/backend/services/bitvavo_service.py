"""
Bitvavo Integration Service
Read-only balance checking (later: trading)
"""
import os
import json
import hmac
import hashlib
import time
import requests
from typing import Dict, Optional, List
from utils.data_manager import DataManager
from utils.logger import SparkLogger

# Rate limiting & caching config
RATE_LIMIT_SECONDS = 2.0  # Minimum tijd tussen requests
CACHE_TTL_SECONDS = 30    # Cache geldigheid

# Cache TTL per endpoint type
CACHE_TTL_BALANCE = 60      # Balance: 60 seconden
CACHE_TTL_CANDLES = 3600    # Candles: 1 uur
CACHE_TTL_TICKER = 30       # Ticker prices: 30 seconden

# Global state voor rate limiting & caching
_request_lock = {}      # Voorkom concurrent requests per user
_last_request_time = {} # Track laatste request tijd per user
_response_cache = {}    # Cache voor GET responses met TTL


class BitvavoService:
    """
    Bitvavo API Integration
    Docs: https://docs.bitvavo.com/
    """
    
    BASE_URL = "https://api.bitvavo.com/v2"
    
    @staticmethod
    def _get_api_credentials(user_id: str) -> Optional[Dict]:
        """
        Haal Bitvavo API credentials op voor user
        
        Returns:
            {"api_key": "...", "api_secret": "..."} or None
        """
        try:
            # Load from user settings
            settings_path = f"users/{user_id}/settings.json"
            settings = DataManager.load_data(settings_path)
            
            bitvavo = settings.get("integrations", {}).get("bitvavo", {})
            
            if bitvavo.get("api_key") and bitvavo.get("api_secret"):
                return {
                    "api_key": bitvavo["api_key"],
                    "api_secret": bitvavo["api_secret"]
                }
            
            return None
        
        except Exception as e:
            print(f"[BITVAVO] Error loading credentials: {e}")
            return None
    
    @staticmethod
    def _create_signature(timestamp: int, method: str, endpoint: str, body: str, secret: str) -> str:
        """
        Create HMAC SHA256 signature for Bitvavo API
        Note: endpoint MUST include /v2 prefix!
        """
        # Ensure endpoint starts with /v2
        if not endpoint.startswith('/v2'):
            endpoint = f'/v2{endpoint}'
        
        message = str(timestamp) + method + endpoint + body
        signature = hmac.new(
            secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    @staticmethod
    def _make_request(
        user_id: str,
        endpoint: str,
        method: str = "GET",
        body: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Make authenticated request to Bitvavo API
        WITH rate limiting, caching, and better error handling
        """
        global _request_lock, _last_request_time, _response_cache
        
        # Prevent concurrent requests from same user
        if user_id in _request_lock:
            SparkLogger.log_system_event(f"[BITVAVO] Concurrent request blocked for {user_id}")
            return {"error": "Request already in progress - please wait"}
        
        try:
            _request_lock[user_id] = True
            
            # Check cache first (GET requests only)
            if method == "GET":
                cache_key = f"{user_id}:{endpoint}"
                cached = _response_cache.get(cache_key)
                
                if cached and (time.time() - cached['timestamp']) < CACHE_TTL_SECONDS:
                    SparkLogger.log_system_event(f"[BITVAVO] Cache HIT: {endpoint}")
                    return cached['data']
            
            # Rate limiting: enforce minimum time between requests
            last_time = _last_request_time.get(user_id, 0)
            time_since_last = time.time() - last_time
            
            if time_since_last < RATE_LIMIT_SECONDS:
                wait_time = RATE_LIMIT_SECONDS - time_since_last
                SparkLogger.log_system_event(f"[BITVAVO] Rate limit: waiting {wait_time:.1f}s")
                time.sleep(wait_time)
            
            # Update last request time
            _last_request_time[user_id] = time.time()
            
            # Get credentials
            credentials = BitvavoService._get_api_credentials(user_id)
            
            if not credentials:
                return {"error": "No Bitvavo API credentials found"}
            
            api_key = credentials["api_key"]
            api_secret = credentials["api_secret"]
            
            timestamp = int(time.time() * 1000)
            # Use compact JSON for signature (no spaces)
            body_str = json.dumps(body, separators=(',', ':')) if body else ""
            
            signature = BitvavoService._create_signature(
                timestamp, method, endpoint, body_str, api_secret
            )
            
            headers = {
                "Bitvavo-Access-Key": api_key,
                "Bitvavo-Access-Signature": signature,
                "Bitvavo-Access-Timestamp": str(timestamp),
                "Content-Type": "application/json"
            }
            
            url = f"{BitvavoService.BASE_URL}{endpoint}"
            
            # Make request with detailed error handling
            try:
                if method == "GET":
                    response = requests.get(url, headers=headers, timeout=10)
                elif method == "POST":
                    response = requests.post(url, headers=headers, json=body, timeout=10)
                else:
                    return {"error": f"Unsupported method: {method}"}
                
                # Log response for debugging
                SparkLogger.log_system_event(
                    f"[BITVAVO] {method} {endpoint} → {response.status_code}"
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Cache successful GET responses
                    if method == "GET":
                        cache_key = f"{user_id}:{endpoint}"
                        _response_cache[cache_key] = {
                            'data': result,
                            'timestamp': time.time()
                        }
                    
                    return result
                else:
                    # Log FULL error response
                    error_detail = f"Status {response.status_code}"
                    try:
                        error_json = response.json()
                        error_detail += f": {error_json}"
                        SparkLogger.log_system_event(f"[BITVAVO ERROR] {error_json}")
                    except Exception:
                        error_detail += f": {response.text}"
                        SparkLogger.log_system_event(f"[BITVAVO ERROR] {response.text}")
                    
                    return {
                        "error": error_detail,
                        "message": response.text
                    }
            
            except requests.Timeout:
                error = "Request timeout - Bitvavo API niet bereikbaar"
                SparkLogger.log_system_event(f"[BITVAVO TIMEOUT] {endpoint}")
                return {"error": error}
            
            except requests.ConnectionError:
                error = "Connection failed - Check internet verbinding"
                SparkLogger.log_system_event(f"[BITVAVO CONNECTION ERROR] {endpoint}")
                return {"error": error}
            
            except Exception as e:
                error = f"Unexpected error: {str(e)}"
                SparkLogger.log_system_event(f"[BITVAVO EXCEPTION] {str(e)}")
                return {"error": error}
        
        finally:
            # Always release lock
            if user_id in _request_lock:
                del _request_lock[user_id]
    
    @staticmethod
    def get_balance(user_id: str) -> Dict:
        """
        Haal wallet balance op + bereken CORRECTE total EUR waarde
        
        Returns:
            {
                "success": true,
                "balances": [
                    {
                        "symbol": "EUR", 
                        "available": "1000.00", 
                        "inOrder": "0.00",
                        "price_eur": "1.0",
                        "value_eur": "1000.00"
                    },
                    {
                        "symbol": "BTC", 
                        "available": "0.05", 
                        "inOrder": "0.00",
                        "price_eur": "50000.00",
                        "value_eur": "2500.00"
                    },
                    ...
                ],
                "total_eur": 3500.00
            }
        """
        # Get raw balance
        result = BitvavoService._make_request(user_id, "/balance", "GET")
        
        if "error" in result:
            return {"success": False, "error": result["error"], "total_eur": 0}
        
        # Filter out zero balances en bereken totaal MET PRICES
        balances = []
        total_eur = 0.0
        
        for item in result:
            available = float(item.get("available", 0))
            in_order = float(item.get("inOrder", 0))
            total_amount = available + in_order
            
            if total_amount > 0:
                symbol = item["symbol"]
                
                # Get price for this symbol
                if symbol == "EUR":
                    price_eur = 1.0
                    value_eur = total_amount
                else:
                    # Get ticker price (cached 30s)
                    ticker_result = BitvavoService.get_ticker(f"{symbol}-EUR")
                    # Check if ticker has price (not "success" key!)
                    if "price" in ticker_result:
                        price_eur = float(ticker_result.get("price", 0))
                        value_eur = total_amount * price_eur
                    else:
                        price_eur = 0.0
                        value_eur = 0.0
                
                balances.append({
                    "symbol": symbol,
                    "available": str(available),
                    "inOrder": str(in_order),
                    "total": str(total_amount),
                    "price_eur": str(price_eur),
                    "value_eur": str(round(value_eur, 2))
                })
                
                total_eur += value_eur
        
        SparkLogger.log_system_event(f"[BITVAVO] Balance calculated: €{total_eur:.2f} ({len(balances)} coins)")
        
        return {
            "success": True,
            "balances": balances,
            "total_eur": round(total_eur, 2),
            "last_updated": time.time()
        }
    
    @staticmethod
    def get_ticker(market: str = "BTC-EUR") -> Optional[Dict]:
        """
        Haal ticker info op voor een market
        
        Args:
            market: bijv "BTC-EUR", "ETH-EUR"
        
        Returns:
            {
                "market": "BTC-EUR",
                "price": "45000.00",
                "bid": "44995.00",
                "ask": "45005.00",
                ...
            }
        """
        try:
            url = f"{BitvavoService.BASE_URL}/ticker/price?market={market}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            
            return None
        
        except Exception as e:
            print(f"[BITVAVO] Ticker error: {e}")
            return None
    

    
    @staticmethod
    def get_portfolio_value(user_id: str, watchlist: List[str] = None) -> Dict:
        """
        Haal portfolio waarde op + coin prijzen
        
        Args:
            user_id: User ID
            watchlist: Optional list of coin symbols to track (e.g. ["BTC", "ETH"])
        
        Returns:
            {
                "success": true,
                "total_eur": 1234.56,
                "balances": [
                    {
                        "symbol": "BTC",
                        "amount": "0.05",
                        "price_eur": "45000.00",
                        "value_eur": "2250.00"
                    },
                    ...
                ],
                "watchlist_prices": {
                    "BTC": "45000.00",
                    "ETH": "3000.00",
                    ...
                }
            }
        """
        # Get balances
        balance_result = BitvavoService.get_balance(user_id)
        
        if not balance_result.get("success"):
            return balance_result
        
        balances = balance_result.get("balances", [])
        
        # Get prices for all coins in balance + watchlist
        coins_to_check = set()
        for b in balances:
            if b["symbol"] != "EUR":
                coins_to_check.add(b["symbol"])
        
        if watchlist:
            coins_to_check.update(watchlist)
        
        # Fetch ticker prices
        prices = {}
        for coin in coins_to_check:
            market = f"{coin}-EUR"
            ticker = BitvavoService.get_ticker(market)
            if ticker and "price" in ticker:
                prices[coin] = float(ticker["price"])
        
        # Calculate values
        total_eur = 0.0
        enriched_balances = []
        
        for b in balances:
            symbol = b["symbol"]
            amount = float(b["available"])
            
            if symbol == "EUR":
                # EUR is direct
                value_eur = amount
                price_eur = 1.0
            else:
                # Crypto coin
                price_eur = prices.get(symbol, 0.0)
                value_eur = amount * price_eur
            
            total_eur += value_eur
            
            enriched_balances.append({
                "symbol": symbol,
                "amount": str(amount),
                "price_eur": str(price_eur),
                "value_eur": str(round(value_eur, 2))
            })
        
        # Watchlist prices
        watchlist_prices = {coin: str(prices.get(coin, 0.0)) for coin in (watchlist or [])}
        
        return {
            "success": True,
            "total_eur": round(total_eur, 2),
            "balances": enriched_balances,
            "watchlist_prices": watchlist_prices,
            "last_updated": time.time()
        }

    @staticmethod
    def save_api_credentials(user_id: str, api_key: str, api_secret: str) -> bool:
        """
        Sla Bitvavo API credentials op
        
        Returns:
            Success boolean
        """
        try:
            settings_path = f"users/{user_id}/settings.json"
            settings = DataManager.load_data(settings_path)
            
            if "integrations" not in settings:
                settings["integrations"] = {}
            
            settings["integrations"]["bitvavo"] = {
                "api_key": api_key,
                "api_secret": api_secret,
                "enabled": True,
                "created_at": time.time()
            }
            
            DataManager.save_data(settings_path, settings)
            
            return True
        
        except Exception as e:
            print(f"[BITVAVO] Error saving credentials: {e}")
            return False
    
    @staticmethod
    def test_connection(user_id: str) -> Dict:
        """
        Test of API credentials werken
        
        Returns:
            {"success": true/false, "message": "..."}
        """
        result = BitvavoService._make_request(user_id, "/time", "GET")
        
        if "error" in result:
            return {
                "success": False,
                "message": f"Connection failed: {result['error']}"
            }
        
        return {
            "success": True,
            "message": "Connection successful",
            "server_time": result.get("time")
        }
    
    @staticmethod
    def get_trade_history(user_id: str, market: str = None, limit: int = 500) -> Dict:
        """
        Haal trade history op van Bitvavo
        
        Args:
            user_id: User ID
            market: Optional market filter (e.g. "BTC-EUR")
            limit: Max trades to fetch (default 500)
        
        Returns:
            {
                "success": true,
                "trades": [
                    {
                        "id": "...",
                        "market": "BTC-EUR",
                        "side": "buy",
                        "amount": "0.1",
                        "price": "50000",
                        "timestamp": 1234567890
                    },
                    ...
                ]
            }
        """
        # Build endpoint with query params
        endpoint = f"/trades?limit={limit}"
        if market:
            endpoint += f"&market={market}"
        
        result = BitvavoService._make_request(user_id, endpoint, "GET")
        
        # Check if result has error key
        if "error" in result:
            return {
                "success": False,
                "error": result["error"],
                "trades": []
            }
        
        # Result is directly the trades array from Bitvavo
        return {
            "success": True,
            "trades": result if isinstance(result, list) else []
        }
    
    @staticmethod
    def get_historical_coins(user_id: str) -> Dict:
        """
        Haal lijst op van alle coins die ooit in de wallet hebben gezeten
        
        NOTE: Bitvavo API vereist market parameter voor trades.
        Voor nu: alleen current coins tonen (historical trades vereist complexere query)
        
        Returns:
            {
                "success": true,
                "current_coins": ["BTC", "ETH", ...],  # Coins in wallet nu
                "historical_coins": [],  # TODO: Vereist market-specifieke queries
                "all_coins": ["BTC", "ETH", ...],
                "note": "Historical trades require market-specific queries"
            }
        """
        # Get current balance
        balance_result = BitvavoService.get_balance(user_id)
        
        if not balance_result.get("success"):
            return balance_result
        
        current_coins = []
        for b in balance_result.get("balances", []):
            if b["symbol"] != "EUR":
                current_coins.append(b["symbol"])
        
        # TODO: Historical coins vereist per-market trade queries
        # Voor nu: alleen huidige coins beschikbaar
        
        return {
            "success": True,
            "current_coins": sorted(current_coins),
            "historical_coins": [],  # Vereist complexere implementatie
            "all_coins": sorted(current_coins),
            "note": "Historical coins feature coming soon"
        }
    
    @staticmethod
    def get_candles(market: str, interval: str = "1d", limit: int = 30) -> Dict:
        """
        Haal historische candle data op voor een market
        
        Args:
            market: Market pair (e.g. "BTC-EUR", "ETH-EUR")
            interval: Candle interval - "1m", "5m", "15m", "1h", "4h", "1d", "1w"
            limit: Aantal candles (max 1440)
        
        Returns:
            {
                "success": true,
                "market": "BTC-EUR",
                "interval": "1d",
                "candles": [
                    {
                        "timestamp": 1234567890,
                        "open": "45000.00",
                        "high": "46000.00",
                        "low": "44500.00",
                        "close": "45500.00",
                        "volume": "123.45"
                    },
                    ...
                ]
            }
        """
        try:
            # Public endpoint - no auth needed!
            # Don't use BASE_URL since it already has /v2
            url = f"https://api.bitvavo.com/v2/{market}/candles?interval={interval}&limit={limit}"
            
            SparkLogger.log_system_event(f"[BITVAVO] Fetching candles: {market} {interval}")
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                raw_candles = response.json()
                
                # Transform Bitvavo format: [timestamp, open, high, low, close, volume]
                candles = []
                for candle in raw_candles:
                    if len(candle) >= 6:
                        candles.append({
                            "timestamp": candle[0],
                            "open": str(candle[1]),
                            "high": str(candle[2]),
                            "low": str(candle[3]),
                            "close": str(candle[4]),
                            "volume": str(candle[5])
                        })
                
                return {
                    "success": True,
                    "market": market,
                    "interval": interval,
                    "candles": candles
                }
            else:
                error = f"Status {response.status_code}: {response.text}"
                SparkLogger.log_system_event(f"[BITVAVO CANDLES ERROR] {error}")
                return {
                    "success": False,
                    "error": error
                }
        
        except Exception as e:
            error = f"Exception: {str(e)}"
            SparkLogger.log_system_event(f"[BITVAVO CANDLES ERROR] {error}")
            return {
                "success": False,
                "error": error
            }
    
    @staticmethod
    def place_market_order(
        user_id: str,
        market: str,
        side: str,
        amount: float
    ) -> Dict:
        """
        Plaats een market order (BUY/SELL) op Bitvavo
        
        Args:
            user_id: User ID
            market: Market pair (e.g. "BCH-EUR")
            side: "buy" or "sell"
            amount: Amount in base currency (EUR for buy, coins for sell)
        
        Returns:
            {
                "success": True/False,
                "order_id": "...",
                "market": "BCH-EUR",
                "side": "buy",
                "amount": "5.0",
                "filled": "5.0",
                "price": "410.50",
                "fees": "0.0125",
                "status": "filled",
                "timestamp": 1234567890
            }
        """
        try:
            SparkLogger.log_system_event(
                f"[BITVAVO] Placing MARKET order: {side.upper()} {amount} on {market}"
            )
            
            # Prepare order body
            # operatorId must be an integer for Bitvavo API v2.9.0+
            operator_id = hash(user_id) % 1000000  # Convert user_id to integer
            
            order_body = {
                "market": market,
                "side": side.lower(),
                "orderType": "market",
                "operatorId": operator_id
            }
            
            # Amount specification depends on side
            if side.lower() == "buy":
                # BUY: specify amount in quote currency (EUR) - max 8 decimals
                order_body["amountQuote"] = str(round(amount, 8))
            else:
                # SELL: specify amount in base currency (coins) - max 8 decimals
                order_body["amount"] = str(round(amount, 8))
            
            # Make authenticated POST request
            result = BitvavoService._make_request(
                user_id=user_id,
                endpoint="/order",  # _make_request adds /v2 prefix
                method="POST",
                body=order_body
            )
            
            # Check for errors
            if "error" in result or "errorCode" in result:
                error_msg = result.get("error") or result.get("errorCode")
                SparkLogger.log_system_event(f"[BITVAVO ORDER ERROR] {error_msg}")
                return {
                    "success": False,
                    "error": error_msg,
                    "details": result
                }
            
            # Success - parse Bitvavo response
            order_id = result.get("orderId")
            filled_amount = float(result.get("filledAmount", 0))
            filled_amount_quote = float(result.get("filledAmountQuote", 0))
            fee_paid = float(result.get("feePaid", 0))
            status = result.get("status", "unknown")
            
            # Calculate average price
            avg_price = 0.0
            if filled_amount > 0 and filled_amount_quote > 0:
                if side.lower() == "buy":
                    avg_price = filled_amount_quote / filled_amount
                else:
                    avg_price = filled_amount_quote / filled_amount
            
            SparkLogger.log_system_event(
                f"[BITVAVO] Order SUCCESS | "
                f"ID: {order_id} | "
                f"Filled: {filled_amount} | "
                f"Price: €{avg_price:.2f} | "
                f"Fee: €{fee_paid}"
            )
            
            return {
                "success": True,
                "order_id": order_id,
                "market": market,
                "side": side.lower(),
                "amount": filled_amount,
                "amount_quote": filled_amount_quote,
                "filled": filled_amount,
                "price": avg_price,
                "fees": fee_paid,
                "status": status,
                "timestamp": result.get("created", int(time.time() * 1000)),
                "raw_response": result
            }
            
        except Exception as e:
            error_msg = f"Exception placing order: {str(e)}"
            SparkLogger.log_system_event(f"[BITVAVO ORDER EXCEPTION] {error_msg}")
            return {
                "success": False,
                "error": error_msg
            }
    
    @staticmethod
    def place_limit_order(
        user_id: str,
        market: str,
        side: str,
        amount: float,
        price: float
    ) -> Dict:
        """
        Plaats een limit order op Bitvavo
        
        Args:
            user_id: User ID
            market: Market pair (e.g. "BCH-EUR")
            side: "buy" or "sell"
            amount: Amount in base currency (coins)
            price: Limit price
        
        Returns:
            Order result (similar to market order)
        """
        try:
            SparkLogger.log_system_event(
                f"[BITVAVO] Placing LIMIT order: {side.upper()} {amount} @ €{price} on {market}"
            )
            
            order_body = {
                "market": market,
                "side": side.lower(),
                "orderType": "limit",
                "amount": str(amount),
                "price": str(price)
            }
            
            result = BitvavoService._make_request(
                user_id=user_id,
                endpoint="/order",
                method="POST",
                body=order_body
            )
            
            if "error" in result or "errorCode" in result:
                error_msg = result.get("error") or result.get("errorCode")
                SparkLogger.log_system_event(f"[BITVAVO ORDER ERROR] {error_msg}")
                return {
                    "success": False,
                    "error": error_msg,
                    "details": result
                }
            
            return {
                "success": True,
                "order_id": result.get("orderId"),
                "market": market,
                "side": side.lower(),
                "amount": float(result.get("amount", 0)),
                "price": float(result.get("price", 0)),
                "status": result.get("status", "open"),
                "timestamp": result.get("created", int(time.time() * 1000)),
                "raw_response": result
            }
            
        except Exception as e:
            error_msg = f"Exception placing limit order: {str(e)}"
            SparkLogger.log_system_event(f"[BITVAVO ORDER EXCEPTION] {error_msg}")
            return {
                "success": False,
                "error": error_msg
            }
    
    @staticmethod
    def cancel_order(user_id: str, market: str, order_id: str) -> Dict:
        """
        Cancel een open order
        
        Returns:
            {"success": True/False, "order_id": "..."}
        """
        try:
            result = BitvavoService._make_request(
                user_id=user_id,
                endpoint=f"/order?market={market}&orderId={order_id}",
                method="DELETE"
            )
            
            if "error" in result or "errorCode" in result:
                return {
                    "success": False,
                    "error": result.get("error") or result.get("errorCode")
                }
            
            return {
                "success": True,
                "order_id": order_id,
                "cancelled": True
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def get_order_status(user_id: str, market: str, order_id: str) -> Dict:
        """
        Check status van een order
        
        Returns:
            Order details with status
        """
        try:
            result = BitvavoService._make_request(
                user_id=user_id,
                endpoint=f"/order?market={market}&orderId={order_id}",
                method="GET"
            )
            
            if "error" in result:
                return {
                    "success": False,
                    "error": result["error"]
                }
            
            return {
                "success": True,
                "order": result
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
