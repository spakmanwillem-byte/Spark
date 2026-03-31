"""
Backtesting API Routes (Core)
==============================
API endpoints voor backtesting service
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from services.backtesting_service import get_backtesting_service

router = APIRouter(prefix="/backtest", tags=["backtest"])


class BacktestRequest(BaseModel):
    market: Optional[str] = "BCH-EUR"
    days: Optional[int] = 730  # 2 jaar
    interval: Optional[str] = "1h"
    speed: Optional[str] = "instant"  # instant, 1m, 15m, 1h
    use_cache: Optional[bool] = True


@router.post("/run")
async def run_backtest(request: BacktestRequest):
    """
    Draai backtest met historische data
    
    Args:
        market: Trading pair (BCH-EUR)
        days: Aantal dagen terug (730 = 2 jaar)
        interval: Candle interval (1h, 4h, 1d)
        speed: Replay snelheid (instant, 1m, 15m, 1h)
        use_cache: Gebruik gecachte data
    
    Returns:
        Backtest resultaten + patroon analyse
    """
    service = get_backtesting_service()
    
    # Load historical data
    load_result = service.load_historical_data(
        market=request.market,
        days=request.days,
        interval=request.interval,
        use_cache=request.use_cache
    )
    
    if not load_result['success']:
        return {
            "success": False,
            "error": "Could not load historical data"
        }
    
    # Run backtest
    backtest_result = service.run_backtest(
        speed=request.speed
    )
    
    if not backtest_result['success']:
        return backtest_result
    
    # Analyze patterns
    pattern_analysis = service.analyze_patterns(backtest_result)
    
    return {
        "success": True,
        "backtest": backtest_result,
        "patterns": pattern_analysis
    }


@router.get("/patterns")
async def get_patterns():
    """
    Haal laatst geanalyseerde patronen op
    """
    # TODO: Load from cache/database
    return {
        "success": True,
        "message": "Run a backtest first with POST /backtest/run"
    }
