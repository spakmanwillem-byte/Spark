"""
Trade Routes - Trade history, positions, Bitvavo credentials
Schema v1:
  trade_history/user-001.json: {trades: [{trade_id, run_id, timestamp, action, market, amount, price, filled, status, mock, success}]}
"""
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
from datetime import datetime, timezone
from modules.core.storage import load_json, save_json

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
    return {
        "total_trades": len(trades),
        "buys": len(buys),
        "sells": len(sells),
        "markets": markets,
        "total_buy_eur": round(total_buy_eur, 2),
        "total_sell_eur": round(total_sell_eur, 2),
        "avg_buy_price": round(avg_buy_price, 2),
        "avg_sell_price": round(avg_sell_price, 2),
        "profit_loss": round(total_sell_eur - total_buy_eur, 2),
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
    return {
        "connected": bool(bitvavo.get("api_key")),
        "connected_at": bitvavo.get("connected_at"),
    }


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
