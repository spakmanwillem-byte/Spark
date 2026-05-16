"""
Bot & Community Routes - Bots met persoonlijkheden + community chat
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
from datetime import datetime, timezone
import secrets
import uuid
from modules.core.storage import load_json, save_json

router = APIRouter(prefix="/bots", tags=["bots"])
DATA_DIR = Path(__file__).parent.parent.parent / "data"
BOTS_FILE = DATA_DIR / "bots" / "bot_users.json"
COMMUNITY_FILE = DATA_DIR / "community" / "messages.json"


def get_bots():
    data = load_json(BOTS_FILE, default={"bots": []})
    return data.get("bots", [])


def get_bot_by_id(bot_id):
    return next((b for b in get_bots() if b["id"] == bot_id), None)


def check_bot_triggers(message_text):
    """Check alle bots voor keyword triggers, return responses"""
    responses = []
    msg_lower = message_text.lower()
    now = datetime.now(timezone.utc)

    for bot in get_bots():
        for trigger in bot.get("triggers", []):
            keywords = trigger.get("keywords", [])
            if trigger["type"] == "keyword" and any(kw in msg_lower for kw in keywords):
                resp_templates = trigger.get("responses", [])
                if resp_templates:
                    resp = secrets.choice(resp_templates)
                    resp = resp.replace("{current_time}", now.strftime("%H:%M"))
                    resp = resp.replace("{hour}", str(now.hour))
                    resp = resp.replace("{scan_result}", "Alles lijkt in orde!")
                    resp = resp.replace("{analysis}", "Geen issues gevonden.")
                    resp = resp.replace("{status}", "OPTIMAL")
                    responses.append({
                        "id": str(uuid.uuid4()),
                        "user_id": bot["id"],
                        "user_name": bot["naam"],
                        "message": resp,
                        "is_bot": True,
                        "timestamp": now.isoformat(),
                    })
            elif trigger["type"] == "greeting" and any(kw in msg_lower for kw in trigger.get("keywords", [])):
                resp_templates = trigger.get("responses", [])
                if resp_templates:
                    resp = secrets.choice(resp_templates)
                    responses.append({
                        "id": str(uuid.uuid4()),
                        "user_id": bot["id"],
                        "user_name": bot["naam"],
                        "message": resp,
                        "is_bot": True,
                        "timestamp": now.isoformat(),
                    })
    return responses


# ============================================================
# BOTS
# ============================================================

@router.get("/list")
async def list_bots():
    bots = get_bots()
    safe = [{
        "id": b["id"], "naam": b["naam"], "gradatie": b.get("gradatie", 3),
        "persoonlijkheid": b.get("persoonlijkheid", ""), "bio": b.get("bio", ""),
        "type": "bot",
    } for b in bots]
    return {"bots": safe, "count": len(safe)}


@router.get("/{bot_id}")
async def get_bot_info(bot_id: str):
    bot = get_bot_by_id(bot_id)
    if not bot:
        return {"success": False, "error": "Bot niet gevonden"}
    return {"success": True, "bot": {
        "id": bot["id"], "naam": bot["naam"], "gradatie": bot.get("gradatie"),
        "persoonlijkheid": bot.get("persoonlijkheid"), "bio": bot.get("bio"),
        "triggers": [{"type": t["type"], "keywords": t.get("keywords", [])} for t in bot.get("triggers", [])],
    }}


# ============================================================
# COMMUNITY CHAT
# ============================================================

class ChatMessage(BaseModel):
    message: str
    user_id: str = "user-001"
    user_name: str = "Willem"


@router.get("/community/messages")
async def get_community_messages(limit: int = 50):
    data = load_json(COMMUNITY_FILE, default={"messages": []})
    messages = data.get("messages", [])
    messages.sort(key=lambda m: m.get("timestamp", ""), reverse=True)
    return {"messages": messages[:limit], "total": len(messages)}


@router.post("/community/send")
async def send_community_message(msg: ChatMessage):
    data = load_json(COMMUNITY_FILE, default={"messages": []})
    now = datetime.now(timezone.utc).isoformat()

    # User message
    user_msg = {
        "id": str(uuid.uuid4()),
        "user_id": msg.user_id,
        "user_name": msg.user_name,
        "message": msg.message,
        "is_bot": False,
        "timestamp": now,
    }
    data["messages"].append(user_msg)

    # Check bot triggers
    bot_responses = check_bot_triggers(msg.message)

    # Replace {user} placeholder
    for resp in bot_responses:
        resp["message"] = resp["message"].replace("{user}", msg.user_name)

    data["messages"].extend(bot_responses)
    save_json(COMMUNITY_FILE, data)

    # Log naar user's gesprekslog
    try:
        from modules.chat import chat_log_service
        combined_bot_response = " | ".join(br.get("message", "") for br in bot_responses) if bot_responses else "(geen bot reactie)"
        chat_log_service.save_message(
            user_id=msg.user_id,
            user_naam=msg.user_name,
            user_message=msg.message,
            spark_response=combined_bot_response,
            analysis={
                "bots_reacted": [br.get("user_name") for br in bot_responses],
                "bot_count": len(bot_responses),
                "word_count": len(msg.message.split()),
            },
            channel="community",
        )
    except Exception:
        pass

    return {
        "success": True,
        "message": user_msg,
        "bot_responses": bot_responses,
    }
