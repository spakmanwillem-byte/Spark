"""
Behavior Tracker Helper (v4_dnd_001)

Lichte wrapper rond /api/dnd/track die direct counters increment zonder HTTP-call.
Gebruikt door andere modules (chat, kb, agenda, trade) om gedrag te tellen.
"""
from pathlib import Path
from typing import Optional
from datetime import datetime, timezone
import re

from .core.storage import load_json, save_json

DATA_ROOT = Path(__file__).parent.parent / "data"
USERS_DIR = DATA_ROOT / "users"

# Heuristics: woorden die wijzen op "helpen" gedrag
_HELP_PATTERNS = re.compile(
    r"\b(help|helpen|helper|geholpen|tip|advies|samen|fijn|bedankt|"
    r"graag gedaan|natuurlijk|prima|leuk|kan ik|laat me|zal ik)\b",
    re.IGNORECASE,
)
# Manipulatie / leugen heuristics (strikt)
_LIE_PATTERNS = re.compile(
    r"\b(leugen|liegen|nep|fake|bedrog|manipuleer|manipuleren|chantage|dreig|dreigen)\b",
    re.IGNORECASE,
)


def _path(user_id: str) -> Path:
    d = USERS_DIR / user_id
    d.mkdir(parents=True, exist_ok=True)
    return d / "behavior.json"


def track(user_id: Optional[str], counter_key: str, delta: int = 1) -> None:
    """Veilige no-throw counter increment."""
    if not user_id or not counter_key:
        return
    try:
        fp = _path(user_id)
        data = load_json(fp, default={"counters": {}, "started_at": datetime.now(timezone.utc).isoformat()})
        counters = data.get("counters", {})
        counters[counter_key] = max(0, counters.get(counter_key, 0) + delta)
        data["counters"] = counters
        data["last_updated"] = datetime.now(timezone.utc).isoformat()
        save_json(fp, data)
    except Exception:
        pass  # nooit blokkeren op tracking


def track_chat_message(user_id: Optional[str], text: str) -> None:
    """Detecteer helpen/manipulatie in chat tekst en tel."""
    if not user_id:
        return
    track(user_id, "msg_received", 1)
    t = (text or "").lower()
    if not t.strip():
        return
    if len(t) > 80:  # langer bericht = meer "lezen"
        track(user_id, "long_read", 1)
    if _HELP_PATTERNS.search(t):
        track(user_id, "help_msg", 1)
    if _LIE_PATTERNS.search(t):
        track(user_id, "lie_detected", 1)
