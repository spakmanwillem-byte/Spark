"""
Bitvavo API Routes - Crypto wallet integration
"""
from fastapi import APIRouter, Query, Body
from services.bitvavo_service import BitvavoService
from services.spark_decision_engine import SparkDecisionEngine
from services.replay_log_service import ReplayLogService
from typing import Dict
from datetime import datetime
import json

router = APIRouter()


@router.get("/balance")
async def get_balance(user_id: str = Query(...)):
    """
    Haal Bitvavo wallet balance op
    """
    result = BitvavoService.get_balance(user_id)
    return result


@router.get("/ticker")
async def get_ticker(market: str = Query("BTC-EUR")):
    """
    Haal ticker info op voor een market
    """
    result = BitvavoService.get_ticker(market)
    
    if result:
        return {"success": True, "ticker": result}
    else:
        return {"success": False, "error": "Could not fetch ticker"}


@router.post("/credentials")
async def save_credentials(
    user_id: str = Query(...),
    credentials: Dict = Body(...)
):
    """
    Sla Bitvavo API credentials op
    
    Body:
        {
            "api_key": "...",
            "api_secret": "..."
        }
    """
    api_key = credentials.get("api_key")
    api_secret = credentials.get("api_secret")
    
    if not api_key or not api_secret:
        return {
            "success": False,
            "message": "Missing api_key or api_secret"
        }
    
    success = BitvavoService.save_api_credentials(user_id, api_key, api_secret)
    
    if success:
        return {
            "success": True,
            "message": "Credentials saved successfully"
        }
    else:
        return {
            "success": False,
            "message": "Failed to save credentials"
        }


@router.post("/test")
async def test_connection(user_id: str = Query(...)):
    """
    Test of API credentials werken
    """
    result = BitvavoService.test_connection(user_id)
    return result



@router.get("/portfolio")
async def get_portfolio(
    user_id: str = Query(...),
    watchlist: str = Query(None)
):
    """
    Haal portfolio waarde + coin prijzen op
    
    Args:
        user_id: User ID
        watchlist: Comma-separated coin symbols (e.g. "BTC,ETH,ADA")
    """
    watchlist_coins = watchlist.split(",") if watchlist else None
    result = BitvavoService.get_portfolio_value(user_id, watchlist_coins)
    return result


@router.get("/history/coins")
async def get_historical_coins(user_id: str = Query(...)):
    """
    Haal lijst op van coins die ooit in de wallet hebben gezeten
    """
    result = BitvavoService.get_historical_coins(user_id)
    return result


@router.get("/candles")
async def get_candles(
    market: str = Query(..., description="Market pair (e.g. BTC-EUR)"),
    interval: str = Query("1d", description="Candle interval: 1m, 5m, 15m, 1h, 4h, 1d, 1w"),
    limit: int = Query(30, description="Number of candles (max 1440)")
):
    """
    Haal historische candle data op voor een market
    Public endpoint - geen auth vereist
    """
    result = BitvavoService.get_candles(market, interval, limit)
    return result



# ============================================================================
# LIVE MONITORING & REPLAY ENDPOINTS
# ============================================================================

@router.post("/live-monitor/start")
async def start_live_monitor(
    user_id: str = Query(...),
    coin: str = Query(..., description="Crypto symbol (BTC, ETH, etc)"),
    interval: str = Query("1h", description="Candle interval: 5m, 15m, 30m, 1h"),
    config: Dict = Body(None, description="Decision engine config (optional)")
):
    """
    Start nieuwe live monitoring run
    Creëert log en returnt run_id
    """
    if config is None:
        config = SparkDecisionEngine.DEFAULT_CONFIG
    
    # Store interval in config voor later gebruik
    config["interval"] = interval
    
    run_id = ReplayLogService.create_run(user_id, coin, config)
    
    return {
        "success": True,
        "run_id": run_id,
        "config": config,
        "interval": interval
    }


@router.get("/live-monitor/candle")
async def process_live_candle(
    run_id: str = Query(...),
    user_id: str = Query(...)
):
    """
    Verwerk ALLEEN de laatste candle met decision engine
    GEEN full recalculation - incrementeel!
    
    Flow:
    1. Haal laatste candle van Bitvavo (gebruik interval uit run config)
    2. Load context + position state from run log
    3. Run decision engine (met position state + trading lock)
    4. Append naar log
    5. Return decision + candle + position state
    """
    # Load run log voor context + state
    run_log = ReplayLogService.load_run(run_id)
    if not run_log:
        return {"success": False, "error": "Run not found"}
    
    coin = run_log["coin"]
    config = run_log["config"]
    interval = config.get("interval", "1h")  # Default naar 1h als niet gespecificeerd
    
    # Haal laatste candle van Bitvavo (met correct interval)
    market = f"{coin}-EUR"
    candles_result = BitvavoService.get_candles(market, interval, 1)
    
    if not candles_result.get("success"):
        return {"success": False, "error": "Could not fetch latest candle"}
    
    latest_candle = candles_result["candles"][0]
    
    # Context = previous candles from log
    context_candles = run_log.get("candles", [])
    
    # Reconstruct position state
    from services.spark_decision_engine import PositionState
    position_state = PositionState()
    saved_state = run_log.get("position_state", {})
    if saved_state.get("position_type") != "NONE":
        position_state.position_type = saved_state["position_type"]
        position_state.entry_price = saved_state["entry_price"]
        position_state.entry_time = saved_state["entry_time"]
        position_state.highest_price = saved_state["highest_price"]
        position_state.trailing_stop_active = saved_state.get("trailing_stop_active", False)
    
    trading_locked = run_log.get("trading_locked", False)
    
    # Run decision engine (IDENTIEKE logica als replay!)
    decision = SparkDecisionEngine.analyze_candle(
        candle=latest_candle,
        context=context_candles,
        config=config,
        position_state=position_state,
        trading_locked=trading_locked
    )
    
    # Append to log
    success = ReplayLogService.append_candle_and_decision(
        run_id=run_id,
        candle=latest_candle,
        decision=decision
    )
    
    if not success:
        return {"success": False, "error": "Failed to append to log"}
    
    # EXECUTE TRADE if BUY or SELL decision
    execution_result = None
    if decision.get("action") in ["BUY", "SELL"]:
        from services.live_trader_service import LiveTraderService
        
        # Add price from latest candle to decision
        decision["price"] = float(latest_candle["close"])
        
        execution_result = LiveTraderService.execute_decision(
            decision=decision,
            user_id=user_id,
            run_id=run_id,
            market=market,
            config=config
        )
        
        # Log execution result
        if execution_result.get("success"):
            from utils.logger import SparkLogger
            SparkLogger.log_system_event(
                f"[LIVE MONITOR] {decision['action']} executed | "
                f"Run: {run_id} | "
                f"Order: {execution_result.get('order_id')}"
            )
        else:
            from utils.logger import SparkLogger
            SparkLogger.log_system_event(
                f"[LIVE MONITOR ERROR] {decision['action']} execution failed | "
                f"Error: {execution_result.get('error')}"
            )
    
    return {
        "success": True,
        "run_id": run_id,
        "candle": latest_candle,
        "decision": decision,
        "execution": execution_result,  # Added
        "position_state": decision.get("position_update", {}),
        "pnl": decision.get("pnl", {}),
        "trading_locked": decision.get("lock_triggered", False) or trading_locked,
        "total_pnl": run_log.get("total_pnl", 0) + decision.get("pnl", {}).get("pnl_eur", 0),
        "candle_count": len(context_candles) + 1,
        "trade_amount_eur": config.get("trade_amount", 5.0)  # Potje waarde
    }



@router.post("/replay/run")
async def replay_run(run_id: str = Query(...)):
    """
    Replay een opgeslagen run - herbereken alle beslissingen
    Dit is de KERN van het systeem: moet 100% reproduceerbaar zijn
    
    Flow:
    1. Load run log (candles + config + decisions_v1)
    2. Herbereken decisions met IDENTIEKE logica
    3. Sla op als decisions_v2
    4. Return comparison
    """
    # Load run
    run_log = ReplayLogService.load_run(run_id)
    if not run_log:
        return {"success": False, "error": "Run not found"}
    
    candles = run_log.get("candles", [])
    config = run_log.get("config", {})
    
    if not candles:
        return {"success": False, "error": "No candles in run"}
    
    # Herbereken alle beslissingen (IDENTIEKE LOGICA als live!)
    from services.spark_decision_engine import PositionState, SparkDecisionEngine
    
    decisions_v2 = []
    position_state = PositionState()
    trading_locked = False
    
    for i, candle in enumerate(candles):
        # Context = alle vorige candles
        context = candles[:i]
        
        # Run decision engine (EXACT SAME as live!)
        decision = SparkDecisionEngine.analyze_candle(
            candle=candle,
            context=context,
            config=config,
            position_state=position_state,
            trading_locked=trading_locked
        )
        
        # Update position state (simuleer state changes)
        if decision.get("position_update"):
            saved_state = decision["position_update"]
            if saved_state.get("position_type") != "NONE":
                position_state.position_type = saved_state["position_type"]
                position_state.entry_price = saved_state["entry_price"]
                position_state.entry_time = saved_state["entry_time"]
                position_state.highest_price = saved_state["highest_price"]
                position_state.trailing_stop_active = saved_state.get("trailing_stop_active", False)
            else:
                # Position closed
                position_state.exit_position()
        
        # Update trading lock
        if decision.get("lock_triggered"):
            trading_locked = True
        
        decisions_v2.append({
            "timestamp": candle["timestamp"],
            **decision
        })
    
    # Save decisions_v2 to run log
    try:
        filepath = f"/app/backend/data/wallet/replay_logs/{run_id}.json"
        with open(filepath, 'r') as f:
            log_data = json.load(f)
        
        log_data["decisions_v2"] = decisions_v2
        log_data["replay_timestamp"] = datetime.now().isoformat()
        
        with open(filepath, 'w') as f:
            json.dump(log_data, f, indent=2)
    except Exception as e:
        return {"success": False, "error": f"Failed to save replay: {str(e)}"}
    
    # Compare v1 vs v2 (ONLY for candles that have v1 decisions)
    decisions_v1 = run_log.get("decisions_v1", [])
    
    # Find which candle indices have v1 decisions
    v1_timestamps = [d["timestamp"] for d in decisions_v1]
    
    # Filter v2 to only include matching timestamps
    decisions_v2_filtered = [
        d for d in decisions_v2 
        if d["timestamp"] in v1_timestamps
    ]
    
    matches = 0
    mismatches = 0
    differences = []
    
    for i, (d1, d2) in enumerate(zip(decisions_v1, decisions_v2_filtered)):
        if d1["action"] == d2["action"] and abs(d1.get("confidence", 0) - d2.get("confidence", 0)) < 0.01:
            matches += 1
        else:
            mismatches += 1
            differences.append({
                "candle_timestamp": d1["timestamp"],
                "live_action": d1["action"],
                "live_confidence": d1.get("confidence", 0),
                "replay_action": d2["action"],
                "replay_confidence": d2.get("confidence", 0),
                "live_reason": d1.get("reason", ""),
                "replay_reason": d2.get("reason", "")
            })
    
    return {
        "success": True,
        "run_id": run_id,
        "total_candles": len(candles),
        "candles_with_live_decisions": len(decisions_v1),
        "matches": matches,
        "mismatches": mismatches,
        "reproducibility_percent": (matches / len(decisions_v1) * 100) if decisions_v1 else 0,
        "differences": differences
    }


@router.get("/live-monitor/run-data")
async def get_run_data(run_id: str = Query(...)):
    """
    Haal volledige run data op (voor testing/analysis)
    """
    run_log = ReplayLogService.load_run(run_id)
    
    if not run_log:
        return {"success": False, "error": "Run not found"}
    
    return run_log



@router.post("/live-monitor/reset-lock")
async def reset_trading_lock(run_id: str = Query(...)):
    """
    Reset trading lock (handmatige reset na slechte trade)
    """
    success = ReplayLogService.reset_trading_lock(run_id)
    
    return {
        "success": success,
        "run_id": run_id,
        "message": "Trading lock reset" if success else "Failed to reset lock"
    }


@router.post("/live-monitor/stop")
async def stop_live_monitor(
    run_id: str = Query(...)
):
    """
    Stop active live monitoring run
    """
    success = ReplayLogService.stop_run(run_id)
    
    return {
        "success": success,
        "run_id": run_id,
        "status": "stopped" if success else "error"
    }


@router.get("/live-monitor/runs")
async def list_runs(user_id: str = Query(...)):
    """
    List alle runs voor een user
    """
    runs = ReplayLogService.list_user_runs(user_id)
    
    return {
        "success": True,
        "runs": runs
    }



# ============================================================================
# LIVE TRADING ENDPOINTS
# ============================================================================

@router.post("/live-trading/execute")
async def execute_trade(
    user_id: str = Query(...),
    run_id: str = Query(...),
    decision: dict = Body(...)
):
    """
    Execute een trading decision (BUY/SELL)
    
    Body:
        {
            "action": "BUY" | "SELL",
            "price": 408.50,
            "reason": "lower band",
            ...
        }
    """
    from services.live_trader_service import LiveTraderService
    
    result = LiveTraderService.execute_decision(
        decision=decision,
        user_id=user_id,
        run_id=run_id,
        market="BCH-EUR"
    )
    
    return result


@router.post("/live-trading/reset-position")
async def reset_position(
    user_id: str = Query(...),
    run_id: str = Query(...),
    reason: str = Query("manual_reset"),
    force_sell: bool = Query(False, description="Sell existing exchange position before reset")
):
    """
    Reset huidige position (voor gemiste trades, offline, edge cases)
    
    Args:
        reason: manual_reset | offline | edge_case | other
        force_sell: Als True, verkoopt bestaande BCH positie VOOR reset
                    Als False, alleen internal state reset (jij verkoopt handmatig)
    
    force_sell=True gebruiken wanneer:
    - Je wilt een complete clean slate
    - Bot moet automatisch orphaned positions sluiten
    
    force_sell=False gebruiken wanneer:
    - Je wilt de positie open houden
    - Je verkoopt handmatig
    """
    from services.live_trader_service import LiveTraderService
    
    result = LiveTraderService.reset_position(
        user_id=user_id,
        run_id=run_id,
        reason=reason,
        force_sell=force_sell,
        market="BCH-EUR"
    )
    
    return result


@router.post("/live-trading/sync-position")
async def sync_position_with_exchange(
    user_id: str = Query(...),
    run_id: str = Query(...)
):
    """
    Sync internal position state met echte exchange balance
    
    Gebruik bij:
    - Start monitoring na crash/restart
    - Na manual trades buiten bot om
    - Bot state lijkt out of sync
    
    Checkt BCH balance op Bitvavo en initialiseert position state
    """
    from services.live_trader_service import LiveTraderService
    
    result = LiveTraderService.sync_position_with_exchange(
        user_id=user_id,
        run_id=run_id,
        market="BCH-EUR"
    )
    
    return result


@router.get("/live-trading/status")
async def get_trading_status(user_id: str = Query(...)):
    """
    Get current trading status (mock mode, positions, etc.)
    """
    from services.live_trader_service import LiveTraderService
    
    status = LiveTraderService.get_trading_status(user_id)
    
    return status


# ============================================================================
# TRADE HISTORY ENDPOINTS
# ============================================================================

@router.get("/trade-history")
async def get_trade_history(
    user_id: str = Query(...),
    limit: int = Query(50, description="Max aantal trades"),
    run_id: str = Query(None, description="Filter op run ID")
):
    """
    Haal trade history op voor een user
    """
    from services.trade_history_service import TradeHistoryService
    
    result = TradeHistoryService.get_trade_history(
        user_id=user_id,
        limit=limit,
        run_id=run_id
    )
    
    return result


@router.get("/trade-statistics")
async def get_trade_statistics(user_id: str = Query(...)):
    """
    Get trade statistics (win rate, counts, etc.)
    """
    from services.trade_history_service import TradeHistoryService
    
    result = TradeHistoryService.get_trade_statistics(user_id)
    
    return result
