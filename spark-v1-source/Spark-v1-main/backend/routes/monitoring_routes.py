"""
Monitoring API Routes (Core)
============================
API endpoints voor monitoring service

Endpoints:
- POST /api/monitoring/start
- POST /api/monitoring/stop
- POST /api/monitoring/pause
- GET /api/monitoring/status
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from services.monitoring_service import get_monitoring_service

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


class MonitorStartRequest(BaseModel):
    interval: Optional[int] = 10  # Default 10 seconds


@router.post("/start")
async def start_monitoring(request: MonitorStartRequest = MonitorStartRequest()):
    """
    Start background monitoring
    
    Args:
        interval: Check interval in seconds
            - 60 = 1 min candle
            - 300 = 5 min candle  
            - 900 = 15 min candle
            - 3600 = 1 uur candle
            - 14400 = 4 uur candle
    """
    service = get_monitoring_service()
    result = service.start(interval=request.interval)
    return result


@router.post("/stop")
async def stop_monitoring():
    """Stop monitoring"""
    service = get_monitoring_service()
    result = service.stop()
    return result


@router.post("/pause")
async def pause_monitoring():
    """Pause/Resume monitoring"""
    service = get_monitoring_service()
    result = service.pause()
    return result


@router.get("/status")
async def get_monitoring_status():
    """Get current monitoring status"""
    service = get_monitoring_service()
    status = service.get_status()
    return {
        "success": True,
        "status": status
    }



@router.get("/trades")
async def get_trades(
    user_id: str = "user-001",
    limit: int = 50,
    period: str = "today"  # today, week, month, all
):
    """
    📊 PLACEHOLDER: Trade Logs Endpoint
    
    Haalt trade history op voor monitoring dashboard
    
    Args:
        user_id: User ID (default: user-001)
        limit: Max aantal trades (default: 50)
        period: Filter periode (today/week/month/all)
    
    Returns:
        {
            "success": True,
            "trades": [...],
            "total": int,
            "period": str
        }
    """
    import json
    from pathlib import Path
    from datetime import datetime, timedelta
    
    try:
        # Load trade history
        trade_file = Path(f"/app/backend/data/wallet/trade_history/{user_id}.json")
        
        if not trade_file.exists():
            return {
                "success": True,
                "trades": [],
                "total": 0,
                "period": period,
                "message": "No trades found"
            }
        
        with open(trade_file, 'r') as f:
            data = json.load(f)
        
        all_trades = data.get('trades', [])
        
        # Filter by period
        now = datetime.now()
        filtered_trades = []
        
        for trade in all_trades:
            try:
                trade_time = datetime.fromisoformat(trade.get('timestamp', '').replace('Z', '+00:00'))
                
                if period == "today":
                    if trade_time.date() == now.date():
                        filtered_trades.append(trade)
                elif period == "week":
                    if trade_time >= now - timedelta(days=7):
                        filtered_trades.append(trade)
                elif period == "month":
                    if trade_time >= now - timedelta(days=30):
                        filtered_trades.append(trade)
                else:  # all
                    filtered_trades.append(trade)
            except ValueError:
                # Skip trades with invalid timestamps
                pass
        
        # Sort by timestamp (newest first)
        filtered_trades.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Limit
        limited_trades = filtered_trades[:limit]
        
        return {
            "success": True,
            "trades": limited_trades,
            "total": len(filtered_trades),
            "period": period
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "trades": [],
            "total": 0
        }



@router.get("/decisions")
async def get_decisions(limit: int = 50):
    """
    Haal laatste beslissingen op (BUY/SELL/HOLD)
    
    Args:
        limit: Max aantal decisions te returnen
    
    Returns:
        {
            "success": True,
            "decisions": [
                {
                    "timestamp": "2026-03-29T15:45:18Z",
                    "cycle": 47,
                    "action": "BUY",
                    "price": 408.20,
                    "reason": "Beneden lower band",
                    "executed": true,
                    "pnl": null,
                    "position": "NONE"
                }
            ],
            "total": 50
        }
    """
    service = get_monitoring_service()
    return service.get_decisions(limit=limit)
