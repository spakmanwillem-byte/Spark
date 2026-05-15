"""
Chat Log Service - archiveert gesprekken per user

Schema (per gesprek):
{
  "id": "conv-xxxxxxxx",
  "timestamp": "ISO-date",
  "user_id": "user-001",
  "user_naam": "Willem",
  "user_message": "Wat is fotosynthese?",
  "spark_response": "...",
  "channel": "spark|community|prive",
  "analysis": {
    "sentiment": "neutraal|positief|negatief",
    "emotion": {...},
    "is_question": bool,
    "trigger_type": "greeting|thanks|how_are_you|goodbye|null",
    "knowledge_matches": [...],
    "unknown_words": [...],
    "snap_suggestions": [...],
    "word_count": int,
    "has_entities": bool
  },
  "metadata": {
    "session_id": "...",
    "gesprek_nummer": int
  }
}
"""
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Optional
import uuid
from modules.core.storage import load_json, save_json

LOGS_DIR = Path(__file__).parent.parent.parent / "data" / "chat" / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)


def _log_file(user_id: str) -> Path:
    return LOGS_DIR / f"{user_id}.json"


def save_message(user_id: str, user_naam: str, user_message: str, spark_response: str,
                 analysis: Optional[Dict] = None, channel: str = "spark",
                 session_id: Optional[str] = None) -> Dict:
    """Save een gesprek-uitwisseling (user_msg + spark_response) naar user logs."""
    if not user_id:
        return {"saved": False, "reason": "Geen user_id"}

    file = _log_file(user_id)
    data = load_json(file, default={"user_id": user_id, "conversations": [], "metadata": {}})

    conv = {
        "id": f"conv-{uuid.uuid4().hex[:8]}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_id": user_id,
        "user_naam": user_naam,
        "user_message": user_message,
        "spark_response": spark_response,
        "channel": channel,
        "analysis": analysis or {},
        "metadata": {
            "session_id": session_id or "default",
            "gesprek_nummer": len(data.get("conversations", [])) + 1,
        },
    }
    data["conversations"].append(conv)
    data["metadata"] = {
        "user_id": user_id,
        "total_conversations": len(data["conversations"]),
        "last_updated": conv["timestamp"],
    }
    save_json(file, data)
    return {"saved": True, "id": conv["id"], "gesprek_nummer": conv["metadata"]["gesprek_nummer"]}


def get_logs(user_id: str, limit: int = 100, offset: int = 0,
             search: Optional[str] = None, channel: Optional[str] = None,
             has_trigger: Optional[bool] = None, has_snap: Optional[bool] = None) -> Dict:
    """Haal gesprekken op met filters."""
    data = load_json(_log_file(user_id), default={"user_id": user_id, "conversations": [], "metadata": {}})
    convs = data.get("conversations", [])

    # Filters
    if search:
        q = search.lower()
        convs = [c for c in convs if q in (c.get("user_message", "") + " " + c.get("spark_response", "")).lower()]
    if channel:
        convs = [c for c in convs if c.get("channel") == channel]
    if has_trigger is True:
        convs = [c for c in convs if c.get("analysis", {}).get("trigger_type")]
    if has_snap is True:
        convs = [c for c in convs if c.get("analysis", {}).get("snap_suggestions")]

    total_filtered = len(convs)
    # Nieuwste eerst
    convs = list(reversed(convs))[offset:offset + limit]

    return {
        "user_id": user_id,
        "conversations": convs,
        "total": data.get("metadata", {}).get("total_conversations", 0),
        "filtered_count": total_filtered,
        "offset": offset,
        "limit": limit,
    }


def get_last_conversation(user_id: str) -> Optional[Dict]:
    """Return de laatste conversatie van een user, of None."""
    data = load_json(_log_file(user_id), default={"conversations": []})
    convs = data.get("conversations", [])
    return convs[-1] if convs else None



def get_stats(user_id: str) -> Dict:
    data = load_json(_log_file(user_id), default={"conversations": []})
    convs = data.get("conversations", [])
    if not convs:
        return {"total": 0, "channels": {}, "triggers": {}, "snap_count": 0, "avg_words": 0}

    channels, triggers = {}, {}
    snap_count, total_words = 0, 0
    for c in convs:
        ch = c.get("channel", "unknown")
        channels[ch] = channels.get(ch, 0) + 1
        t = c.get("analysis", {}).get("trigger_type")
        if t:
            triggers[t] = triggers.get(t, 0) + 1
        if c.get("analysis", {}).get("snap_suggestions"):
            snap_count += 1
        total_words += c.get("analysis", {}).get("word_count", 0) or len(c.get("user_message", "").split())

    return {
        "total": len(convs),
        "channels": channels,
        "triggers": triggers,
        "snap_count": snap_count,
        "avg_words": round(total_words / len(convs), 1) if convs else 0,
        "first": convs[0]["timestamp"] if convs else None,
        "last": convs[-1]["timestamp"] if convs else None,
    }


def list_all_users_with_logs() -> list:
    """Lijst alle user_ids die logs hebben (admin)."""
    users = []
    for f in LOGS_DIR.glob("*.json"):
        data = load_json(f, default={})
        users.append({
            "user_id": data.get("user_id", f.stem),
            "total": data.get("metadata", {}).get("total_conversations", 0),
            "last_updated": data.get("metadata", {}).get("last_updated"),
        })
    return sorted(users, key=lambda u: u.get("last_updated") or "", reverse=True)


def delete_conversation(user_id: str, conv_id: str) -> bool:
    file = _log_file(user_id)
    data = load_json(file, default={"conversations": []})
    before = len(data["conversations"])
    data["conversations"] = [c for c in data["conversations"] if c["id"] != conv_id]
    if len(data["conversations"]) == before:
        return False
    data["metadata"]["total_conversations"] = len(data["conversations"])
    save_json(file, data)
    return True
