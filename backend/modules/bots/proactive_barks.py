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
    """Increment login counter; bij 3/4/5 → Mr Smith bark; bij 6 → reset naar 0.

    v13c_bots_consolidatie_001 (sessie 54) — KOELKAST. Mr Smith is inactief;
    login-counter barks zijn puur ruis zonder inhoudelijke waarde. Counter-file
    blijft tikken zodat data intact is voor als 'ie later terugkeert.
    """
    if not user_id or user_id.startswith("bot-"):
        return None
    counters = load_json(COUNTERS_FILE, default={"counters": {}})
    cmap = counters.setdefault("counters", {})
    current = int(cmap.get(user_id, 0)) + 1
    if current >= 6:
        cmap[user_id] = 0
    else:
        cmap[user_id] = current
    save_json(COUNTERS_FILE, counters)
    return None  # geen bark meer


# ============================================================
# F2 — Harry mirror-time barks (lazy check, op messages-load)
# ============================================================

def inject_time_barks() -> List[Dict]:
    """Harry mirror-time barks.

    v13c_bots_consolidatie_001 (sessie 54) — KOELKAST. Harry Klokkenmaker
    inactief; mirror-time barks waren puur cosmetische ruis. Aanroepers
    krijgen lege lijst, verder gedrag ongewijzigd.
    """
    return []


# ============================================================
# F3 — Madelief bug-pointer bark
# ============================================================

_BUG_KEYWORDS = ["bug", "fout", "werkt niet", "kapot", "crash", "stuk"]


def check_bug_pointer_bark(user_message: str) -> Optional[Dict]:
    """Return Boekhouder bark als user iets over een bug zegt, anders None.
    Aanroeper (community/send) hangt de bark zelf in de feed.

    v13c_bots_consolidatie_001 (sessie 54) — was Madelief; nu De Boekhouder
    (die alle system-error/health meldingen doet)."""
    if not user_message:
        return None
    text = user_message.lower()
    if not any(kw in text for kw in _BUG_KEYWORDS):
        return None
    now = datetime.now(timezone.utc).isoformat()
    bark = {
        "id": str(uuid.uuid4()),
        "user_id": "bot-boekhouder",
        "user_name": "De Boekhouder",
        "message": (
            "Klinkt als iets dat misgaat — genoteerd.\n"
            "Wil je 'm officieel melden? Ga naar **Notities & Taken → tab Bug-melder**. "
            "Dan komt 'ie op de roadmap en blijft 'ie niet alleen in deze chat hangen."
        ),
        "is_bot": True,
        "timestamp": now,
        "bark_kind": "bug_pointer",
    }
    log_event("barks", "f3_bug_pointer", intent="Boekhouder bug-pointer bark")
    return bark
