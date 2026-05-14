"""
Chat Recap Service (v4_recap_001) — "Wat hebben we gisteren middag besproken?"
-----------------------------------------------------------------------------
Spark kan op vraag een korte samenvatting geven van een eerder tijdvenster.
Gebruikt user_time_service voor timezone-aware datum/dagdeel resolving.

Dagdelen (lokaal):
  ochtend: 05:00-12:00
  middag:  12:00-18:00
  avond:   18:00-23:00
  nacht:   23:00-05:00
"""
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from modules.core.storage import load_json
from . import user_time_service

LOGS_DIR = Path(__file__).parent.parent.parent / "data" / "chat" / "logs"

# ============== INTENT DETECTION ==============
# Triggers voor "wat hebben we besproken"
_RECAP_PATTERNS = [
    r"\bwat hebben we\b.*\b(besproken|gehad|geleerd|gezegd)\b",
    r"\bwaar hadden we\b.*\b(over|het over)\b",
    r"\b(samenvatting|recap|overzicht)\b.*\b(gesprek|chat|gisteren|vandaag|vanochtend|vanmiddag|vanavond)\b",
    r"\bwat (zei|zeiden|hebben) (jij|je|wij|we)\b.*\b(gisteren|vandaag|vanochtend|vanmiddag|vanavond|eerder)\b",
    r"\bbespraken we\b",
    r"\bonderwerpen\b.*\b(gisteren|vandaag|vanochtend|vanmiddag|vanavond|gesprek)\b",
]

_DAYNAMES = {
    "maandag": 0, "dinsdag": 1, "woensdag": 2, "donderdag": 3,
    "vrijdag": 4, "zaterdag": 5, "zondag": 6,
}

_DAYPARTS = {
    "ochtend": (5, 12),
    "vanochtend": (5, 12),
    "morgen": (5, 12),
    "voormiddag": (5, 12),
    "middag": (12, 18),
    "vanmiddag": (12, 18),
    "namiddag": (12, 18),
    "avond": (18, 23),
    "vanavond": (18, 23),
    "nacht": (23, 5),
    "vannacht": (23, 5),
}


def detect_recap_intent(text: str) -> bool:
    if not text:
        return False
    t = text.lower().strip()
    return any(re.search(p, t) for p in _RECAP_PATTERNS)


def _resolve_window(text: str, user: Optional[dict]) -> Tuple[datetime, datetime, str]:
    """
    Parse user-text → return (start_utc, end_utc, label_nl) als 2 UTC datetimes.
    Bijv. "gisteren middag" bij user in NL → 12:00-18:00 lokale tijd van gisteren.
    Default: vandaag totnu.
    """
    now_local = user_time_service.now_for_user(user)
    t = (text or "").lower()

    # Bepaal dag
    offset_days = 0
    daylabel = "vandaag"
    if "eergisteren" in t:
        offset_days = -2
        daylabel = "eergisteren"
    elif "gisteren" in t:
        offset_days = -1
        daylabel = "gisteren"
    elif "vandaag" in t or "vanochtend" in t or "vanmiddag" in t or "vanavond" in t or "vannacht" in t:
        offset_days = 0
        daylabel = "vandaag"
    else:
        # Weekdag genoemd? "afgelopen maandag", "maandag"
        for name, wd in _DAYNAMES.items():
            if re.search(rf"\b{name}\b", t):
                today_wd = now_local.weekday()
                diff = (today_wd - wd) % 7
                if diff == 0:
                    diff = 7  # 'afgelopen' interpretatie
                offset_days = -diff
                daylabel = name
                break

    # Bepaal dagdeel
    dp_start, dp_end = 0, 24
    dpartlabel = ""
    for name, (s, e) in _DAYPARTS.items():
        if re.search(rf"\b{name}\b", t):
            dp_start, dp_end = s, e
            dpartlabel = name.replace("van", "")
            break

    base = now_local + timedelta(days=offset_days)
    start_local = base.replace(hour=dp_start if dp_start < 24 else 0, minute=0, second=0, microsecond=0)
    if dp_end > dp_start:
        end_local = base.replace(hour=dp_end - 1, minute=59, second=59, microsecond=0)
    else:
        # nacht: 23:00-05:00 → strekt over twee dagen, hou simpel: nacht van base
        end_local = (base + timedelta(days=1)).replace(hour=dp_end - 1 if dp_end > 0 else 4, minute=59, second=59, microsecond=0)

    # Convert naar UTC (timestamps in log files staan in UTC ISO)
    if start_local.tzinfo is None:
        start_local = start_local.replace(tzinfo=timezone.utc)
        end_local = end_local.replace(tzinfo=timezone.utc)
    start_utc = start_local.astimezone(timezone.utc)
    end_utc = end_local.astimezone(timezone.utc)

    label = (daylabel + (" " + dpartlabel if dpartlabel else "")).strip()
    return start_utc, end_utc, label


def _parse_iso(s: str) -> Optional[datetime]:
    if not s:
        return None
    try:
        # support both Z and +00:00
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _conversations_in_window(user_id: str, start_utc: datetime, end_utc: datetime) -> List[Dict]:
    if not user_id:
        return []
    f = LOGS_DIR / f"{user_id}.json"
    data = load_json(f, default={"conversations": []})
    out = []
    for conv in data.get("conversations", []):
        ts = _parse_iso(conv.get("timestamp"))
        if not ts:
            continue
        if start_utc <= ts <= end_utc:
            out.append(conv)
    return out


def _extract_topics(conversations: List[Dict]) -> List[Tuple[str, int]]:
    """Tel begrip-frequencies uit knowledge_matches. Top-N onderwerpen."""
    counts: Dict[str, int] = {}
    for conv in conversations:
        analysis = conv.get("analysis") or {}
        for m in analysis.get("knowledge_matches") or []:
            if isinstance(m, dict):
                b = (m.get("begrip") or "").strip()
                if b and len(b) >= 2:
                    counts[b] = counts.get(b, 0) + 1
    # Sorteer
    return sorted(counts.items(), key=lambda x: -x[1])


def _extract_keywords_from_messages(conversations: List[Dict], max_words: int = 5) -> List[str]:
    """Fallback wanneer geen knowledge matches: pak content-words uit user messages."""
    STOP = {
        "de", "het", "een", "en", "ik", "je", "jij", "u", "we", "wij", "is", "zijn",
        "was", "waren", "wat", "hoe", "dat", "die", "deze", "dit", "in", "op", "aan",
        "van", "voor", "met", "naar", "om", "te", "of", "als", "ook", "maar", "dus",
        "nog", "wel", "niet", "geen", "kan", "kun", "kunt", "moet", "wil", "zou", "ja",
        "nee", "even", "heel", "veel", "weinig", "echt", "gaan", "zien", "hebben",
    }
    counts: Dict[str, int] = {}
    for conv in conversations:
        msg = (conv.get("user_message") or "").lower()
        for w in re.findall(r"[a-zà-ÿ]{3,}", msg):
            if w in STOP:
                continue
            counts[w] = counts.get(w, 0) + 1
    return [w for w, _ in sorted(counts.items(), key=lambda x: -x[1])[:max_words]]


def build_recap(user: Optional[dict], user_id: Optional[str], text: str) -> Dict:
    """Hoofd-API. Return dict met message + structuur."""
    start_utc, end_utc, label = _resolve_window(text, user)
    convs = _conversations_in_window(user_id or "", start_utc, end_utc)

    # Lokale tijdwindow strings voor user-facing
    tz_name = user_time_service.resolve_user_timezone(user)
    try:
        from zoneinfo import ZoneInfo
        sl = start_utc.astimezone(ZoneInfo(tz_name)).strftime("%H:%M")
        el = end_utc.astimezone(ZoneInfo(tz_name)).strftime("%H:%M")
    except Exception:
        sl, el = start_utc.strftime("%H:%M"), end_utc.strftime("%H:%M")

    if not convs:
        return {
            "type": "recap",
            "message": f"Ik kan voor {label} (tussen {sl} en {el}) geen gesprekken terugvinden in de logs.",
            "window": {"label": label, "start": start_utc.isoformat(), "end": end_utc.isoformat()},
            "count": 0,
            "topics": [],
        }

    topics = _extract_topics(convs)[:5]
    if not topics:
        kws = _extract_keywords_from_messages(convs, max_words=5)
        topics = [(kw, 1) for kw in kws]

    if topics:
        joined = ", ".join(f"**{t}**" for t, _ in topics[:-1])
        last = f"**{topics[-1][0]}**" if topics else ""
        topics_str = f"{joined} en {last}" if joined else last
    else:
        topics_str = "geen specifiek onderwerp"

    # Mooie zin bouwen
    if label == "vandaag":
        when_str = "vandaag"
    elif label == "gisteren":
        when_str = "gisteren"
    elif label == "eergisteren":
        when_str = "eergisteren"
    elif " " in label:
        when_str = label  # bv "gisteren middag"
    else:
        when_str = f"op {label}"

    msg = (
        f"In de gesprekken van {when_str} (tussen {sl} en {el}) "
        f"hebben we **{len(convs)}** "
        f"{'berichten' if len(convs) != 1 else 'bericht'} uitgewisseld. "
        f"Onderwerpen: {topics_str}. "
        f"Wil je dat ik op één daarvan dieper inga?"
    )
    return {
        "type": "recap",
        "message": msg,
        "window": {"label": label, "start": start_utc.isoformat(), "end": end_utc.isoformat()},
        "count": len(convs),
        "topics": [{"naam": t, "frequentie": c} for t, c in topics],
    }
