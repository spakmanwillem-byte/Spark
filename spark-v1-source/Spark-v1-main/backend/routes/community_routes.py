from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import json
from pathlib import Path
from datetime import datetime
import uuid
from services.bot_engine import bot_engine

router = APIRouter()

COMMUNITY_CHAT_FILE = Path("/app/backend/data/community/messages.json")
COMMUNITY_CHAT_FILE.parent.mkdir(parents=True, exist_ok=True)

class CommunityMessage(BaseModel):
    user_id: str
    user_name: str
    message: str
    is_bot: bool = False

def load_messages():
    if not COMMUNITY_CHAT_FILE.exists():
        return {"messages": [], "active_users": []}
    with open(COMMUNITY_CHAT_FILE, 'r') as f:
        return json.load(f)

def save_messages(data):
    with open(COMMUNITY_CHAT_FILE, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

@router.get("/messages")
async def get_messages(limit: int = 50):
    """Get recent community messages"""
    data = load_messages()
    messages = data.get("messages", [])[-limit:]
    return {
        "success": True,
        "messages": messages,
        "count": len(messages)
    }

@router.post("/message")
async def post_message(msg: CommunityMessage):
    """Post message to community chat"""
    data = load_messages()
    
    # Add user message
    new_message = {
        "id": str(uuid.uuid4()),
        "user_id": msg.user_id,
        "user_name": msg.user_name,
        "message": msg.message,
        "is_bot": msg.is_bot,
        "timestamp": datetime.now().isoformat()
    }
    
    data["messages"].append(new_message)
    
    # Check if bots should respond
    bot_responses = []
    
    # Check all bots for keyword triggers
    for bot in bot_engine.get_all_bots():
        response = bot_engine.check_keyword_trigger(bot["id"], msg.message)
        if response:
            bot_message = {
                "id": str(uuid.uuid4()),
                "user_id": bot["id"],
                "user_name": bot["naam"],
                "message": response,
                "is_bot": True,
                "timestamp": datetime.now().isoformat()
            }
            data["messages"].append(bot_message)
            bot_responses.append(bot_message)
    
    save_messages(data)
    
    return {
        "success": True,
        "message": new_message,
        "bot_responses": bot_responses
    }

class JoinRequest(BaseModel):
    user_id: str
    user_name: str

@router.post("/join")
async def user_join(req: JoinRequest):
    """User joins community chat"""
    data = load_messages()
    
    # Add to active users
    if "active_users" not in data:
        data["active_users"] = []
    
    if req.user_id not in [u["user_id"] for u in data["active_users"]]:
        data["active_users"].append({
            "user_id": req.user_id,
            "user_name": req.user_name,
            "joined_at": datetime.now().isoformat()
        })
    
    # Trigger Madelief greeting
    madelief_response = bot_engine.get_bot_response(
        "bot-madelief",
        "user_join",
        {"user": req.user_name}
    )
    
    bot_messages = []
    if madelief_response:
        greeting = {
            "id": str(uuid.uuid4()),
            "user_id": "bot-madelief",
            "user_name": "Madelief Stouten",
            "message": madelief_response,
            "is_bot": True,
            "timestamp": datetime.now().isoformat()
        }
        data["messages"].append(greeting)
        bot_messages.append(greeting)
    
    save_messages(data)
    
    return {
        "success": True,
        "message": f"{req.user_name} joined the community",
        "greeting": bot_messages
    }

class LeaveRequest(BaseModel):
    user_id: str
    user_name: str

@router.post("/leave")
async def user_leave(req: LeaveRequest):
    """User leaves community chat"""
    data = load_messages()
    
    # Remove from active users
    data["active_users"] = [
        u for u in data.get("active_users", [])
        if u["user_id"] != req.user_id
    ]
    
    # Trigger Madelief goodbye
    madelief_response = bot_engine.get_bot_response(
        "bot-madelief",
        "user_leave",
        {"user": req.user_name}
    )
    
    if madelief_response:
        goodbye = {
            "id": str(uuid.uuid4()),
            "user_id": "bot-madelief",
            "user_name": "Madelief Stouten",
            "message": madelief_response,
            "is_bot": True,
            "timestamp": datetime.now().isoformat()
        }
        data["messages"].append(goodbye)
    
    save_messages(data)
    
    return {"success": True, "message": f"{req.user_name} left"}

@router.get("/active_users")
async def get_active_users():
    """Get list of active users"""
    data = load_messages()
    return {
        "success": True,
        "active_users": data.get("active_users", []),
        "count": len(data.get("active_users", []))
    }
