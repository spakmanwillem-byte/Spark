"""
Spark Core Sync Routes - Configure and monitor Bitvavo balance sync
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from services.spark_core_sync_service import SparkCoreSyncService
from typing import Optional

router = APIRouter()


class SyncConfig(BaseModel):
    """Configuration for auto-sync"""
    auto_sync: bool
    interval_minutes: Optional[int] = 30
    spark_user_id: Optional[str] = 'user-000'


@router.get("/sync/status")
async def get_sync_status():
    """
    Get current sync status and configuration
    
    Returns:
        {
            "auto_sync": bool,
            "interval_minutes": int,
            "spark_user_id": str,
            "last_sync_success": str,
            "last_sync_status": str,
            "current_balance": float,
            "last_updated": str
        }
    """
    try:
        status = SparkCoreSyncService.get_sync_status()
        return {
            "success": True,
            **status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/enable")
async def enable_sync(
    interval_minutes: int = Query(30, ge=5, le=1440),
    spark_user_id: str = Query('user-000')
):
    """
    Enable automatic Bitvavo balance syncing
    
    Args:
        interval_minutes: Sync interval (5-1440 minutes, default: 30)
        spark_user_id: User ID for Spark Core Bitvavo account (default: user-000)
    
    Returns:
        Updated configuration
    """
    try:
        config = SparkCoreSyncService.enable_auto_sync(
            interval_minutes=interval_minutes,
            spark_user_id=spark_user_id
        )
        
        # Restart scheduler with new interval
        from server import app
        if hasattr(app.state, 'scheduler'):
            scheduler = app.state.scheduler
            
            # Remove existing sync job if exists
            try:
                scheduler.remove_job('spark_core_sync')
            except Exception:
                pass
            
            # Add new job with updated interval
            from server import sync_spark_core_balance
            scheduler.add_job(
                sync_spark_core_balance,
                'interval',
                minutes=interval_minutes,
                id='spark_core_sync',
                replace_existing=True
            )
        
        return {
            "success": True,
            "message": f"Auto-sync enabled: {interval_minutes} min interval",
            "config": config
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/disable")
async def disable_sync():
    """
    Disable automatic Bitvavo balance syncing
    
    Returns:
        Updated configuration
    """
    try:
        config = SparkCoreSyncService.disable_auto_sync()
        
        # Remove scheduler job
        from server import app
        if hasattr(app.state, 'scheduler'):
            scheduler = app.state.scheduler
            try:
                scheduler.remove_job('spark_core_sync')
            except Exception:
                pass
        
        return {
            "success": True,
            "message": "Auto-sync disabled",
            "config": config
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/now")
async def sync_now():
    """
    Manually trigger a sync immediately (works even if auto_sync is disabled)
    
    Returns:
        Sync result with balance info
    """
    try:
        result = SparkCoreSyncService.manual_sync()
        
        if result.get('success'):
            return {
                "success": True,
                "message": result.get('message'),
                "balance_eur": result.get('balance_eur'),
                "old_balance": result.get('old_balance'),
                "change": result.get('change'),
                "timestamp": result.get('timestamp')
            }
        else:
            return {
                "success": False,
                "message": result.get('message'),
                "timestamp": result.get('timestamp')
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/balance")
async def get_spark_core_balance():
    """
    Get current Spark Core balance (from cache)
    
    Returns:
        {
            "balance_eur": float,
            "last_updated": str,
            "source": str,
            "sync_enabled": bool
        }
    """
    try:
        status = SparkCoreSyncService.get_sync_status()
        
        return {
            "success": True,
            "balance_eur": status.get('current_balance'),
            "last_updated": status.get('last_updated'),
            "source": status.get('source'),
            "sync_enabled": status.get('auto_sync'),
            "interval_minutes": status.get('interval_minutes')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
