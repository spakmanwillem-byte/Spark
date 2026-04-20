"""
Trade Routes - Trade history, positions, Bitvavo credentials, monitoring, candles, tickers
"""
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional, List
from pathlib import Path
from datetime import datetime, timezone
from modules.core.storage import load_json, save_json
from modules.trade.monitor import (
    get_monitor, fetch_candles, fetch_tickers,
    execute_mock_trade, execute_real_trade, WATCHLIST_COINS,
    fetch_bitvavo_balance, sync_bitvavo_orders,
)

router = APIRouter(prefix="/trade", tags=["trade"])
DATA_DIR = Path(__file__).parent.parent.parent / "data" / "wallet"
SETTINGS_DIR = Path(__file__).parent.parent.parent / "data" / "users"


class BitvavoCredentials(BaseModel):
    api_key: str
    api_secret: str


class TraderSettings(BaseModel):
    trade_amount: Optional[float] = 5.0
    market: Optional[str] = "BCH-EUR"
    use_mock: Optional[bool] = True
    auto_trade: Optional[bool] = False


class MonitorStartRequest(BaseModel):
    interval: Optional[int] = 60
    market: Optional[str] = "BCH-EUR"
    candle_interval: Optional[str] = "1h"
    user_id: Optional[str] = "user-001"
    auto_trade: Optional[bool] = False
    trade_amount: Optional[float] = 5.0
    use_mock: Optional[bool] = True


class QuickTradeRequest(BaseModel):
    market: str = "BCH-EUR"
    side: str = "buy"
    amount: float = 5.0
    use_mock: bool = True


@router.get("/history/{user_id}")
async def get_trade_history(user_id: str, limit: int = Query(50, ge=1, le=500), market: Optional[str] = None):
    data = load_json(DATA_DIR / "trade_history" / f"{user_id}.json", default={"trades": []})
    trades = data.get("trades", [])
    if market:
        trades = [t for t in trades if t.get("market") == market]
    trades.sort(key=lambda t: t.get("timestamp", ""), reverse=True)
    total = len(trades)
    return {"trades": trades[:limit], "total": total}


@router.get("/stats/{user_id}")
async def get_trade_stats(user_id: str):
    data = load_json(DATA_DIR / "trade_history" / f"{user_id}.json", default={"trades": []})
    trades = data.get("trades", [])
    buys = [t for t in trades if t.get("action") == "BUY" and t.get("success")]
    sells = [t for t in trades if t.get("action") == "SELL" and t.get("success")]
    markets = list(set(t.get("market", "?") for t in trades))
    total_buy_eur = sum(t.get("amount", 0) for t in buys)
    total_sell_eur = sum(t.get("amount", 0) for t in sells)
    avg_buy_price = sum(t.get("price", 0) for t in buys) / max(len(buys), 1)
    avg_sell_price = sum(t.get("price", 0) for t in sells) / max(len(sells), 1)
    # Fee-aware profit calculation
    total_fees = sum(float(t.get("fee", 0) or 0) for t in trades if (t.get("fee_currency") or "EUR") == "EUR")
    bruto_pnl = total_sell_eur - total_buy_eur
    netto_pnl = bruto_pnl - total_fees
    return {
        "total_trades": len(trades),
        "buys": len(buys),
        "sells": len(sells),
        "markets": markets,
        "total_buy_eur": round(total_buy_eur, 2),
        "total_sell_eur": round(total_sell_eur, 2),
        "avg_buy_price": round(avg_buy_price, 2),
        "avg_sell_price": round(avg_sell_price, 2),
        "total_fees_eur": round(total_fees, 2),
        "bruto_pnl": round(bruto_pnl, 2),
        "profit_loss": round(netto_pnl, 2),  # Netto na fees (backwards compat key)
        "netto_pnl": round(netto_pnl, 2),
        "mock_trades": sum(1 for t in trades if t.get("mock")),
        "real_trades": sum(1 for t in trades if not t.get("mock")),
    }


@router.get("/markets/{user_id}")
async def get_available_markets(user_id: str):
    data = load_json(DATA_DIR / "trade_history" / f"{user_id}.json", default={"trades": []})
    trades = data.get("trades", [])
    markets = {}
    for t in trades:
        m = t.get("market", "?")
        if m not in markets:
            markets[m] = {"total": 0, "buys": 0, "sells": 0}
        markets[m]["total"] += 1
        if t.get("action") == "BUY":
            markets[m]["buys"] += 1
        elif t.get("action") == "SELL":
            markets[m]["sells"] += 1
    return {"markets": markets}


@router.post("/bitvavo/credentials/{user_id}")
async def save_bitvavo_credentials(user_id: str, creds: BitvavoCredentials):
    settings_file = SETTINGS_DIR / user_id / "settings.json"
    settings = load_json(settings_file, default={"user_id": user_id, "integrations": {}})
    if "integrations" not in settings:
        settings["integrations"] = {}
    settings["integrations"]["bitvavo"] = {
        "api_key": creds.api_key,
        "api_secret": creds.api_secret,
        "connected_at": datetime.now(timezone.utc).isoformat(),
    }
    settings_file.parent.mkdir(parents=True, exist_ok=True)
    save_json(settings_file, settings)
    return {"success": True, "message": "Bitvavo credentials opgeslagen"}


@router.get("/bitvavo/status/{user_id}")
async def get_bitvavo_status(user_id: str):
    settings_file = SETTINGS_DIR / user_id / "settings.json"
    settings = load_json(settings_file, default={})
    bitvavo = settings.get("integrations", {}).get("bitvavo", {})
    api_key = bitvavo.get("api_key", "")
    return {
        "connected": bool(api_key) and not api_key.startswith("TEST_"),
        "placeholder": api_key.startswith("TEST_"),
        "connected_at": bitvavo.get("connected_at"),
    }


@router.get("/bitvavo/balance/{user_id}")
async def get_bitvavo_balance(user_id: str):
    """Live Bitvavo account balances (all coins + EUR) with current EUR values."""
    return fetch_bitvavo_balance(user_id)


@router.post("/bitvavo/sync/{user_id}")
async def sync_bitvavo(user_id: str, market: Optional[str] = None):
    """Importeer trade history vanuit Bitvavo naar lokale trade_history."""
    return sync_bitvavo_orders(user_id, market)


@router.get("/settings/{user_id}")
async def get_trader_settings(user_id: str):
    settings_file = SETTINGS_DIR / user_id / "settings.json"
    settings = load_json(settings_file, default={})
    trader = settings.get("trader", {
        "trade_amount": 5.0,
        "market": "BCH-EUR",
        "use_mock": True,
        "auto_trade": False,
    })
    return {"settings": trader}


@router.put("/settings/{user_id}")
async def update_trader_settings(user_id: str, updates: TraderSettings):
    settings_file = SETTINGS_DIR / user_id / "settings.json"
    settings = load_json(settings_file, default={"user_id": user_id})
    if "trader" not in settings:
        settings["trader"] = {}
    for k, v in updates.model_dump(exclude_none=True).items():
        settings["trader"][k] = v
    settings_file.parent.mkdir(parents=True, exist_ok=True)
    save_json(settings_file, settings)
    return {"success": True, "settings": settings["trader"]}


# ============================================================
# CANDLES & TICKERS (Bitvavo Public API - no auth needed)
# ============================================================

@router.get("/candles")
async def get_candles(
    market: str = Query("BCH-EUR"),
    interval: str = Query("1h"),
    limit: int = Query(30, ge=1, le=200),
):
    candles = fetch_candles(market, interval, limit)
    return {"success": len(candles) > 0, "market": market, "interval": interval, "candles": candles}


@router.get("/tickers")
async def get_tickers(coins: str = Query(None)):
    coin_list = coins.split(",") if coins else WATCHLIST_COINS
    tickers = fetch_tickers(coin_list)
    return {"success": len(tickers) > 0, "tickers": tickers}


# ============================================================
# QUICK TRADE (Execute buy/sell)
# ============================================================

@router.post("/execute/{user_id}")
async def execute_trade(user_id: str, req: QuickTradeRequest):
    if req.use_mock:
        result = execute_mock_trade(user_id, req.market, req.side, req.amount)
    else:
        result = execute_real_trade(user_id, req.market, req.side, req.amount)
    return result


# ============================================================
# MONITOR (Start/Stop/Pause background trading monitor)
# ============================================================

@router.post("/monitor/start")
async def monitor_start(req: MonitorStartRequest = MonitorStartRequest()):
    monitor = get_monitor()
    return monitor.start(
        interval=req.interval,
        market=req.market,
        candle_interval=req.candle_interval,
        user_id=req.user_id,
        auto_trade=req.auto_trade,
        trade_amount=req.trade_amount,
        use_mock=req.use_mock,
    )


@router.post("/monitor/stop")
async def monitor_stop():
    return get_monitor().stop()


@router.post("/monitor/pause")
async def monitor_pause():
    return get_monitor().pause()


@router.get("/monitor/status")
async def monitor_status():
    return {"success": True, "status": get_monitor().get_status()}


@router.get("/monitor/decisions")
async def monitor_decisions(limit: int = Query(50)):
    return {"success": True, "decisions": get_monitor().get_decisions(limit)}
