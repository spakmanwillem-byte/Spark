"""
Chat Session State — lichte staat per user in JSON.

Houdt bij:
- laatste begrip dat Spark gaf (voor rejection-flow)
- of user awaiting confirmation is voor homoniem-creatie
- v6_conv_state_001: last_question + last_question_ts (2-min context window)
"""
from pathlib import Path
from datetime import datetime, timezone
from modules.core.storage import load_json, save_json

STATE_FILE = Path(__file__).parent.parent.parent / "data" / "chat_sessions.json"

# Session timeout — na 10 min is context vergeten
SESSION_TIMEOUT_SEC = 600
# v6_conv_state_001 — last_question heeft een kortere window (2 min)
LAST_QUESTION_WINDOW_SEC = 120


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _parse_iso(ts: str):
    try:
        return datetime.fromisoformat(ts)
    except Exception:
        return None


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
    # v6_conv_state_001 — last_question expires veel sneller (2 min) zodat
    # follow-up vragen niet dagen-oud zijn.
    lq_ts = s.get("last_question_ts")
    if lq_ts:
        try:
            lq_age = (datetime.now(timezone.utc) - datetime.fromisoformat(lq_ts)).total_seconds()
            if lq_age > LAST_QUESTION_WINDOW_SEC:
                s = dict(s)
                s.pop("last_question", None)
                s.pop("last_question_ts", None)
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


def set_last_question(user_id: str, question: str, intent: str = ""):
    """v6_conv_state_001 — markeer dat Spark net een vraag stelde aan de user.

    Bij next user-message kunnen we in chat-router checken of die als antwoord
    op deze vraag bedoeld is (bv. yes/no resolutie).
    """
    if not user_id or not question:
        return
    set_state(
        user_id,
        last_question=question,
        last_question_ts=_now_iso(),
        last_question_intent=intent or "",
    )


def get_last_question(user_id: str) -> dict:
    """v6_conv_state_001 — returnt {question, intent, age_sec} of {} als verlopen/geen."""
    if not user_id:
        return {}
    s = get_state(user_id)
    q = s.get("last_question")
    if not q:
        return {}
    ts = s.get("last_question_ts")
    age_sec = None
    if ts:
        dt = _parse_iso(ts)
        if dt:
            age_sec = (datetime.now(timezone.utc) - dt).total_seconds()
    return {
        "question": q,
        "intent": s.get("last_question_intent") or "",
        "age_sec": age_sec,
    }


def clear_state(user_id: str):
    """Reset user staat."""
    if not user_id:
        return
    data = load_json(STATE_FILE, default={})
    if user_id in data:
        del data[user_id]
        save_json(STATE_FILE, data)
