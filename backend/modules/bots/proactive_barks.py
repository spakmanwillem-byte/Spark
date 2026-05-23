"""
Proactive Barks Service (v5_barks_001 — F1+F2+F3)
==================================================
Niet-trigger-gestuurde barks die proactief in de community-feed
verschijnen op specifieke momenten.

F1: Mr Smith bark na 3, 4, 5 logins van een user (reset bij 6)
F2: Harry tijd-barks op mirror-minuten (HH:MM waar H==M, bv 14:14, 21:21)
F3: Madelief wijst naar Bug-melder als user "bug/fout/werkt niet" zegt

Functies:
- handle_login_bark(user_id, user_name): wordt aangeroepen na auth.login
- inject_time_barks(): wordt aangeroepen bij elke GET /community/messages
- check_bug_pointer_bark(message): returnt bark-dict of None bij bug-keywords
"""
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Optional, List
import uuid

from modules.core.storage import load_json, save_json
from modules.core.spark_logger import log_event

DATA_ROOT = Path(__file__).parent.parent.parent / "data"
COUNTERS_FILE = DATA_ROOT / "system" / "login_counters.json"
COMMUNITY_FILE = DATA_ROOT / "community" / "messages.json"

# Mirror-minuten waarop Harry een tijd-bark plaatst (HH:MM met H==M)
MIRROR_TIMES = {
    "11:11", "12:12", "13:13", "14:14", "15:15",
    "16:16", "17:17", "18:18", "19:19", "20:20",
    "21:21", "22:22", "23:23",
}


def _append_community_message(msg: Dict) -> None:
    """Append een bark als community-bericht (geen duplicate via msg.id)."""
    data = load_json(COMMUNITY_FILE, default={"messages": []})
    data.setdefault("messages", []).append(msg)
    save_json(COMMUNITY_FILE, data)


# ============================================================
# F1 — Mr Smith login counter bark
# ============================================================

def handle_login_bark(user_id: str, user_name: str) -> Optional[Dict]:
    """Increment login counter; bij 3/4/5 → Mr Smith bark; bij 6 → reset naar 0."""
    if not user_id or user_id.startswith("bot-"):
        return None
    counters = load_json(COUNTERS_FILE, default={"counters": {}})
    cmap = counters.setdefault("counters", {})
    current = int(cmap.get(user_id, 0)) + 1

    bark = None
    if current >= 6:
        cmap[user_id] = 0  # reset
    else:
        cmap[user_id] = current
        if 3 <= current <= 5:
            now = datetime.now(timezone.utc).isoformat()
            phrases = {
                3: f"Ik zie je wel, {user_name}. 👀",
                4: f"{user_name} — nóg een keer, hè? Ik tel mee.",
                5: f"Vijf keer al. Welkom terug, {user_name}. *knipoog*",
            }
            bark = {
                "id": str(uuid.uuid4()),
                "user_id": "bot-smith",
                "user_name": "Mr Smith",
                "message": phrases.get(current, f"Ik zie je wel, {user_name}."),
                "is_bot": True,
                "timestamp": now,
                "bark_kind": "login_counter",
                "login_count": current,
            }
            _append_community_message(bark)
            log_event("barks", "f1_login_bark",
                      intent=f"Mr Smith bark count={current}",
                      detail={"user_id": user_id, "count": current})

    save_json(COUNTERS_FILE, counters)
    return bark


# ============================================================
# F2 — Harry mirror-time barks (lazy check, op messages-load)
# ============================================================

def inject_time_barks() -> List[Dict]:
    """Voeg een Harry-bark toe als HUIDIGE tijd een mirror-minuut is én
    nog geen bark voor dit moment vandaag is geplaatst.
    
    Wordt aangeroepen bij GET /api/bots/community/messages.
    Returnt de toegevoegde barks (meestal 0 of 1)."""
    now = datetime.now(timezone.utc)
    # Lokale Nederlandse tijd (CET/CEST) voor display — gebruik Europe/Amsterdam
    try:
        from zoneinfo import ZoneInfo
        local_now = now.astimezone(ZoneInfo("Europe/Amsterdam"))
    except Exception:
        local_now = now
    hhmm = local_now.strftime("%H:%M")
    if hhmm not in MIRROR_TIMES:
        return []

    # Check of we vandaag al een mirror-bark voor dit exacte HH:MM hebben gepost
    today = local_now.strftime("%Y-%m-%d")
    bark_key = f"harry_mirror_{today}_{hhmm}"
    data = load_json(COMMUNITY_FILE, default={"messages": []})
    msgs = data.get("messages", [])
    # Snel scan laatste 50 messages — mirror-barks zijn recent
    for m in reversed(msgs[-50:]):
        if m.get("bark_kind_id") == bark_key:
            return []  # al gepost

    bark = {
        "id": str(uuid.uuid4()),
        "user_id": "bot-harry",
        "user_name": "Harry Klokkenmaker",
        "message": f"⏰ {hhmm} — een spiegel-minuut. Even stilstaan?",
        "is_bot": True,
        "timestamp": now.isoformat(),
        "bark_kind": "mirror_time",
        "bark_kind_id": bark_key,
    }
    data.setdefault("messages", []).append(bark)
    save_json(COMMUNITY_FILE, data)
    log_event("barks", "f2_mirror_bark", intent=f"Harry mirror-time {hhmm}", detail={"hhmm": hhmm})
    return [bark]


# ============================================================
# F3 — Madelief bug-pointer bark
# ============================================================

_BUG_KEYWORDS = ["bug", "fout", "werkt niet", "kapot", "crash", "stuk"]


def check_bug_pointer_bark(user_message: str) -> Optional[Dict]:
    """Return Madelief bark als user iets over een bug zegt, anders None.
    Aanroeper (community/send) hangt de bark zelf in de feed."""
    if not user_message:
        return None
    text = user_message.lower()
    if not any(kw in text for kw in _BUG_KEYWORDS):
        return None
    now = datetime.now(timezone.utc).isoformat()
    bark = {
        "id": str(uuid.uuid4()),
        "user_id": "bot-madelief",
        "user_name": "Madelief Stouten",
        "message": (
            "Klinkt als iets dat misgaat — vervelend. 🌸\n"
            "Wil je 'm officieel melden? Ga naar **Notities & Taken → tab Bug-melder**. "
            "Dan komt 'ie op de roadmap en blijft 'ie niet alleen in deze chat hangen."
        ),
        "is_bot": True,
        "timestamp": now,
        "bark_kind": "bug_pointer",
    }
    log_event("barks", "f3_bug_pointer", intent="Madelief bug-pointer bark")
    return bark
