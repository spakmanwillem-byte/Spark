"""
Chat Session State — lichte staat per user in JSON.

Houdt bij:
- laatste begrip dat Spark gaf (voor rejection-flow)
- of user awaiting confirmation is voor homoniem-creatie
"""
from pathlib import Path
from datetime import datetime, timezone
from modules.core.storage import load_json, save_json

STATE_FILE = Path(__file__).parent.parent.parent / "data" / "chat_sessions.json"

# Session timeout — na 10 min is context vergeten
SESSION_TIMEOUT_SEC = 600


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def get_state(user_id: str) -> dict:
    """Haal huidige staat van user op. Verlopen staten worden genegeerd."""
    if not user_id:
        return {}
    data = load_json(STATE_FILE, default={})
    s = data.get(user_id, {})
    # Timeout check
    ts = s.get("updated_at")
    if ts:
        try:
            age = (datetime.now(timezone.utc) - datetime.fromisoformat(ts)).total_seconds()
            if age > SESSION_TIMEOUT_SEC:
                return {}
        except Exception:
            pass
    return s


def set_state(user_id: str, **fields):
    """Update staat (merge)."""
    if not user_id:
        return
    data = load_json(STATE_FILE, default={})
    cur = data.get(user_id, {})
    cur.update(fields)
    cur["updated_at"] = _now_iso()
    data[user_id] = cur
    save_json(STATE_FILE, data)


def clear_state(user_id: str):
    """Reset user staat."""
    if not user_id:
        return
    data = load_json(STATE_FILE, default={})
    if user_id in data:
        del data[user_id]
        save_json(STATE_FILE, data)
