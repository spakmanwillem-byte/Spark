"""
Time Intent Service (v4_time_001) — Spark beantwoordt "hoe laat is het?" vragen
in de tijdzone van de user.
"""
import re
from datetime import datetime, timezone
from typing import Optional, Dict
from . import user_time_service

PATTERNS = [
    r"\bhoe\s+laat\s+is\s+het\b",
    r"\bwelk\s+tijdstip\s+is\s+het\b",
    r"\bwat\s+is\s+(de\s+tijd|het\s+tijdstip)\b",
    r"\bwhat\s+time\s+is\s+it\b",
    r"\bhuidige\s+tijd\b",
    r"\btijd\s+(nu|alstublieft|aub|aub\?)\b",
    r"\bklokt?ijd\b",
]


def detect(text: str) -> bool:
    if not text:
        return False
    t = text.lower()
    return any(re.search(p, t) for p in PATTERNS)


def build_answer(user: Optional[dict]) -> Dict:
    now_utc = datetime.now(timezone.utc)
    tz = user_time_service.resolve_user_timezone(user)
    try:
        from zoneinfo import ZoneInfo
        local = now_utc.astimezone(ZoneInfo(tz))
        tz_label = tz
    except Exception:
        local = now_utc
        tz_label = "UTC"
    time_str = local.strftime("%H:%M")
    date_str = local.strftime("%A %-d %B %Y").lower()
    # NL-vertaling van weekdagen
    NL_DAYS = {"monday":"maandag","tuesday":"dinsdag","wednesday":"woensdag","thursday":"donderdag","friday":"vrijdag","saturday":"zaterdag","sunday":"zondag"}
    NL_MONTHS = {"january":"januari","february":"februari","march":"maart","april":"april","may":"mei","june":"juni","july":"juli","august":"augustus","september":"september","october":"oktober","november":"november","december":"december"}
    for en, nl in NL_DAYS.items(): date_str = date_str.replace(en, nl)
    for en, nl in NL_MONTHS.items(): date_str = date_str.replace(en, nl)
    return {
        "message": f"Het is **{time_str}** ({date_str}) — tijdzone {tz_label}.",
        "type": "time_now",
    }
