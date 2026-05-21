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
    # v4_community_avatar_001: verrijk elke message met avatar_url van de afzender
    users_file = Path(__file__).parent.parent.parent / "data" / "system" / "users.json"
    udata = load_json(users_file, default={})
    users_list = udata.get("users", []) if isinstance(udata, dict) else []
    avatar_map = {}
    ROADKILL_FALLBACK = {"kind": "image", "url": "/api/avatar/gallery/roadkill-logo/image", "is_fallback": True}
    for u in users_list:
        uid = u.get("id") or u.get("user_id")
        av = u.get("avatar") or u.get("avatar_ref")
        if not uid:
            continue
        if av and isinstance(av, str):
            if av.startswith("gallery:"):
                gid = av.split(":", 1)[1]
                avatar_map[uid] = {"kind": "image", "url": f"/api/avatar/gallery/{gid}/image"}
            elif av.startswith("emoji:"):
                avatar_map[uid] = {"kind": "emoji", "emoji": av.split(":", 1)[1]}
            elif av.startswith("upload:"):
                avatar_map[uid] = {"kind": "image", "url": f"/api/avatar/user/{uid}/image"}
            else:
                # Onbekend formaat → fallback
                avatar_map[uid] = dict(ROADKILL_FALLBACK)
        else:
            # Geen avatar veld → check user-upload anders roadkill fallback
            user_img = Path(__file__).parent.parent.parent / "data" / "users" / uid / "avatar.jpg"
            if user_img.exists():
                avatar_map[uid] = {"kind": "image", "url": f"/api/avatar/user/{uid}/image"}
            else:
                avatar_map[uid] = dict(ROADKILL_FALLBACK)
    enriched = []
    for m in messages[:limit]:
        m = dict(m)
        m["avatar"] = avatar_map.get(m.get("user_id")) or dict(ROADKILL_FALLBACK)
        enriched.append(m)
    return {"messages": enriched, "total": len(messages)}


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

    # v4_community_snap_001 — Detecteer onbekende woorden in user-bericht
    # Lichte heuristiek: woorden met >5 letters die NIET in KB staan + niet bot-namen
    snap_candidates = []
    try:
        from modules.core.storage import load_json as _lj
        from pathlib import Path as _P
        kb_path = _P("/app/backend/data/knowledge/learned_knowledge/knowledge_base.json")
        kb = _lj(kb_path, default={})
        known_concepts = {k.lower() for k in kb.keys()} if isinstance(kb, dict) else set()
        import re as _re
        words = _re.findall(r"\b[a-zà-ÿ]{6,}\b", msg.message.lower())
        # Filter stopwoorden/algemene woorden
        STOP = {"hebben", "worden", "kunnen", "moeten", "willen", "zullen", "gaan",
                "vandaag", "morgen", "gister", "altijd", "soms", "eigenlijk", "natuurlijk",
                "misschien", "waarschijnlijk", "echter", "hierdoor", "daarom"}
        snap_candidates = list({w for w in words if w not in STOP and w not in known_concepts})[:5]
    except Exception:
        snap_candidates = []

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
        "snap_candidates": snap_candidates,
    }


# ============================================================
# v4_community_archive_001 — Community chat archief per dag/maand/jaar
# ============================================================
def _group_by_date(messages):
    """Groepeer messages in jaar→maand→dag boom met counts en first/last ts."""
    tree = {}
    for m in messages:
        ts = m.get("timestamp") or ""
        if not ts or len(ts) < 10:
            continue
        try:
            year = ts[0:4]
            month = ts[5:7]
            day = ts[8:10]
            int(year)
            int(month)
            int(day)
        except Exception:
            continue
        tree.setdefault(year, {}).setdefault(month, {}).setdefault(day, {"count": 0, "first": ts, "last": ts})
        node = tree[year][month][day]
        node["count"] += 1
        if ts < node["first"]:
            node["first"] = ts
        if ts > node["last"]:
            node["last"] = ts
    return tree


@router.get("/community/archive")
async def community_archive(year: Optional[str] = None, month: Optional[str] = None, day: Optional[str] = None):
    """
    Returnt jaar→maand→dag-tree van community-berichten.
    - Geen params: alleen boom-counts
    - year+month+day: berichten van die dag (chronologisch)
    """
    data = load_json(COMMUNITY_FILE, default={"messages": []})
    messages = data.get("messages", [])
    tree = _group_by_date(messages)
    if year and month and day:
        prefix = f"{year}-{month}-{day}"
        day_msgs = [m for m in messages if (m.get("timestamp") or "").startswith(prefix)]
        day_msgs.sort(key=lambda m: m.get("timestamp", ""))
        return {
            "tree": tree,
            "day": prefix,
            "messages": day_msgs,
            "count": len(day_msgs),
        }
    return {"tree": tree, "total": len(messages)}


@router.get("/community/recap")
async def community_recap(date: Optional[str] = None, offset_days: int = 0):
    """v4_community_recap_001 — Samenvatting van community-chat op een dag.

    - `date=YYYY-MM-DD` voor expliciete datum
    - `offset_days=1` voor gisteren (default 0 = vandaag)
    Returnt human-readable recap + topic-counts + actieve users.
    """
    from datetime import timedelta
    if date:
        target = date
    else:
        target_dt = datetime.now(timezone.utc) - timedelta(days=offset_days)
        target = target_dt.strftime("%Y-%m-%d")

    data = load_json(COMMUNITY_FILE, default={"messages": []})
    messages = data.get("messages", [])
    day_msgs = [m for m in messages if (m.get("timestamp") or "").startswith(target)]
    day_msgs.sort(key=lambda m: m.get("timestamp", ""))

    user_counts = {}
    bot_counts = {}
    for m in day_msgs:
        name = m.get("user_name") or "Onbekend"
        if m.get("is_bot"):
            bot_counts[name] = bot_counts.get(name, 0) + 1
        else:
            user_counts[name] = user_counts.get(name, 0) + 1

    # Topic woordtelling (basic): woorden ≥5 letters die niet stopwoord zijn
    import re
    STOP = {"weer", "wordt", "worden", "kunnen", "moeten", "willen", "zullen",
            "vandaag", "morgen", "gister", "echter", "daarom", "natuurlijk",
            "iemand", "iedereen", "alleen", "samen", "geweest", "geleden",
            "tijdens", "doorheen", "vooral", "ondanks", "tegelijk"}
    word_counts = {}
    for m in day_msgs:
        if m.get("is_bot"):
            continue  # focus op user-content
        for w in re.findall(r"\b[a-zà-ÿ]{5,}\b", (m.get("message") or "").lower()):
            if w in STOP:
                continue
            word_counts[w] = word_counts.get(w, 0) + 1
    top_topics = sorted(word_counts.items(), key=lambda x: -x[1])[:8]

    # Recap-tekst (Dutch, friendly)
    if not day_msgs:
        recap = f"Op {target} is er niets in de community besproken."
    else:
        bits = [f"Op {target} zijn er {len(day_msgs)} berichten in de community geplaatst"]
        if user_counts:
            top_user = max(user_counts.items(), key=lambda x: x[1])
            bits.append(f"door {len(user_counts)} mensen (meest: **{top_user[0]}** met {top_user[1]})")
        if bot_counts:
            bits.append(f"+ {sum(bot_counts.values())} bot-reacties")
        if top_topics:
            bits.append("Onderwerpen: " + ", ".join(t[0] for t in top_topics[:5]))
        recap = ". ".join(bits) + "."

    return {
        "date": target,
        "recap": recap,
        "total": len(day_msgs),
        "users": user_counts,
        "bots": bot_counts,
        "top_topics": [{"word": w, "count": c} for w, c in top_topics],
        "messages_preview": [
            {"user_name": m.get("user_name"), "message": (m.get("message") or "")[:140], "timestamp": m.get("timestamp"), "is_bot": m.get("is_bot", False)}
            for m in day_msgs[:30]
        ],
    }
