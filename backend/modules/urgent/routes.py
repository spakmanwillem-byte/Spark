"""
Urgent Notifications (v4_glow_001) — Welke sidebar-tabs moeten "glowen"?

Doel:
  Een lichte poll-endpoint die de frontend elke ~60s kan aanroepen.
  Returnt een lijst van urgent items, gegroepeerd per nav-id, met severity.

Severities:
  • "amber"  → komt eraan (< 60 min)
  • "red"    → nu (< 15 min)

Eerste implementatie: agenda-events → glow op 'chat' (en optioneel sub-tabs).
Modulair zodat trade/wallet/etc. later eigen producers kunnen toevoegen.
"""
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import APIRouter

from modules.core.storage import load_json
from modules.chat import user_time_service

router = APIRouter(prefix="/urgent", tags=["urgent"])

AGENDA_DIR = Path(__file__).parent.parent.parent / "data" / "agenda"
USERS_FILE = Path(__file__).parent.parent.parent / "data" / "system" / "users.json"


def _get_user(user_id: str) -> Optional[dict]:
    if not user_id:
        return None
    data = load_json(USERS_FILE, default={"users": []})
    for u in data.get("users", []):
        if u.get("id") == user_id:
            return u
    return None


def _parse_event_datetime(ev: dict, tz_name: str) -> Optional[datetime]:
    """Probeer event-datum/tijd te parsen naar timezone-aware UTC datetime."""
    raw = ev.get("date") or ev.get("datetime") or ev.get("start") or ev.get("when")
    if not raw:
        return None
    if isinstance(raw, str):
        s = raw.strip()
        try:
            if s.endswith("Z"):
                s = s[:-1] + "+00:00"
            dt = datetime.fromisoformat(s)
            if dt.tzinfo is None:
                # Aanname: lokaal in user-tz
                try:
                    from zoneinfo import ZoneInfo
                    dt = dt.replace(tzinfo=ZoneInfo(tz_name))
                except Exception:
                    dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            return None
    return None


def _agenda_glow_for_user(user_id: str) -> List[Dict]:
    """Lees agenda en bepaal welke events urgent zijn voor de glow."""
    user = _get_user(user_id)
    tz_name = user_time_service.resolve_user_timezone(user)
    now_utc = datetime.now(timezone.utc)

    fpath = AGENDA_DIR / f"{user_id}.json"
    data = load_json(fpath, default={"events": []})

    urgent: List[Dict] = []
    for ev in data.get("events", []):
        # Skip done/cancelled
        if ev.get("status") in ("done", "completed", "cancelled"):
            continue
        ev_dt = _parse_event_datetime(ev, tz_name)
        if not ev_dt:
            continue
        diff = (ev_dt - now_utc).total_seconds() / 60.0  # minuten tot event
        if diff < -5:  # >5 min geleden = al voorbij
            continue
        if diff > 60:  # te ver weg
            continue
        severity = "red" if diff <= 15 else "amber"
        urgent.append({
            "kind": "agenda",
            "event_id": ev.get("id"),
            "title": ev.get("titel") or ev.get("title") or "Afspraak",
            "minutes_until": round(diff),
            "severity": severity,
            "starts_at": ev_dt.isoformat(),
        })
    return urgent


@router.get("/notifications")
async def get_urgent(user_id: Optional[str] = None) -> Dict:
    """
    Poll-endpoint. Frontend roept elke ~60s aan met ?user_id=...
    Return:
      {
        "glow": {
          "chat": "amber",        # hoogste severity per nav-id
          "chat-spark": "red",    # optionele sub-tab keys
          ...
        },
        "items": [ {...}, ... ]   # gedetailleerde lijst voor tooltips/badges
      }
    """
    items: List[Dict] = []
    if user_id:
        items.extend(_agenda_glow_for_user(user_id))

    # Aggregeer severity per nav-id (red wint van amber)
    glow: Dict[str, str] = {}

    def _push(nav_id: str, sev: str):
        cur = glow.get(nav_id)
        if cur == "red":
            return
        if sev == "red" or cur is None:
            glow[nav_id] = sev

    for it in items:
        if it["kind"] == "agenda":
            _push("chat", it["severity"])
            _push("chat-spark", it["severity"])  # sub-tab hint
            _push("calendar", it["severity"])

    return {"glow": glow, "items": items, "checked_at": datetime.now(timezone.utc).isoformat()}
