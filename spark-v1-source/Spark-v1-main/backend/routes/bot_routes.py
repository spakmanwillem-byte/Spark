from fastapi import APIRouter, HTTPException
from services.bot_engine import bot_engine
from datetime import datetime

router = APIRouter()

@router.get("/")
async def get_all_bots():
    """Get all bot users"""
    bots = bot_engine.get_all_bots()
    return {
        "success": True,
        "bots": bots,
        "count": len(bots)
    }

@router.get("/{bot_id}")
async def get_bot(bot_id: str):
    """Get specific bot"""
    bot = bot_engine.get_bot_by_id(bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    return {"success": True, "bot": bot}

@router.post("/trigger/{bot_id}")
async def trigger_bot(bot_id: str, trigger_type: str, user_name: str = None):
    """Manually trigger bot response"""
    context = {}
    if user_name:
        context["user"] = user_name
    
    response = bot_engine.get_bot_response(bot_id, trigger_type, context)
    
    if not response:
        return {"success": False, "message": "No response for this trigger"}
    
    return {
        "success": True,
        "bot_id": bot_id,
        "response": response,
        "timestamp": datetime.now().isoformat()
    }

@router.post("/check_keyword/{bot_id}")
async def check_keyword(bot_id: str, message: str):
    """Check if message triggers bot"""
    response = bot_engine.check_keyword_trigger(bot_id, message)
    
    if not response:
        return {"success": False, "message": "No trigger found"}
    
    return {
        "success": True,
        "bot_id": bot_id,
        "triggered": True,
        "response": response
    }

@router.get("/simulate/activity")
async def simulate_activity():
    """Simulate bot activities (for testing)"""
    activities = bot_engine.simulate_bot_activity()
    return {
        "success": True,
        "activities": activities,
        "count": len(activities)
    }

@router.post("/hourly_announcement")
async def hourly_announcement():
    """Harry's hourly time announcement"""
    hour = datetime.now().hour
    response = f"🕐 Het is nu {hour}:00 uur!"
    
    return {
        "success": True,
        "bot_id": "bot-harry",
        "bot_name": "Harry Klokkenmaker",
        "announcement": response,
        "timestamp": datetime.now().isoformat()
    }
