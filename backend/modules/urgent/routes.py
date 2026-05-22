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
URGENT_DIR = Path(__file__).parent.parent.parent / "data" / "urgent"
URGENT_DIR.mkdir(parents=True, exist_ok=True)
PRIVE_DIR = Path(__file__).parent.parent.parent / "data" / "chat" / "prive"
ADMIN_COLLECTIEF_FILE = Path(__file__).parent.parent.parent / "data" / "chat" / "admin-collectief.json"


def _ack_file(user_id: str) -> Path:
    return URGENT_DIR / f"acks_{user_id}.json"


def _load_acks(user_id: str) -> Dict[str, str]:
    """Map event_id -> until_iso (UTC). Ack geldig tot event_dt+10min."""
    return load_json(_ack_file(user_id), default={})


def _save_acks(user_id: str, acks: Dict[str, str]):
    from modules.core.storage import save_json
    # Prune expired
    now = datetime.now(timezone.utc)
    cleaned = {}
    for eid, until in acks.items():
        try:
            if datetime.fromisoformat(until.replace("Z", "+00:00")) > now:
                cleaned[eid] = until
        except Exception:
            pass
    save_json(_ack_file(user_id), cleaned)


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
    acks = _load_acks(user_id)

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
        # Skip als user dit event al heeft acknowledged
        eid = ev.get("id")
        if eid and eid in acks:
            continue
        severity = "red" if diff <= 15 else "amber"
        urgent.append({
            "kind": "agenda",
            "event_id": eid,
            "title": ev.get("titel") or ev.get("title") or "Afspraak",
            "minutes_until": round(diff),
            "severity": severity,
            "starts_at": ev_dt.isoformat(),
        })
    return urgent


def _prive_glow_for_user(user_id: str) -> List[Dict]:
    """v4_glow_notify_001 — Tel unread privé-DMs en geef glow severity.

    Logica:
      • 1-2 unread       → amber
      • ≥3 unread        → red
      • boekhouder-DM    → meteen red (financiële trade alert)

    v4_glow_skip_spark_001: gesprekken met Spark (user-000) tellen NIET
    voor de Privé-glow — die hebben hun eigen Spark AI tab.
    """
    if not PRIVE_DIR.exists():
        return []
    total_unread = 0
    from_boekhouder = 0
    senders: Dict[str, int] = {}
    for fp in PRIVE_DIR.glob("*.json"):
        # Filter: alleen conversaties waar user in betrokken is
        stem = fp.stem
        parts = stem.split("__")
        if user_id not in parts:
            continue
        # Skip Spark-conversaties (die horen bij Spark AI tab)
        if "user-000" in parts:
            continue
        data = load_json(fp, default={"messages": []})
        for m in data.get("messages", []):
            if user_id in (m.get("unread_by") or []):
                total_unread += 1
                fr = m.get("from_user_id") or ""
                senders[fr] = senders.get(fr, 0) + 1
                if fr == "bot-boekhouder":
                    from_boekhouder += 1
    if total_unread == 0:
        return []
    severity = "red" if (from_boekhouder > 0 or total_unread >= 3) else "amber"
    top_sender = max(senders.items(), key=lambda x: x[1])[0] if senders else None
    return [{
        "kind": "prive_dm",
        "severity": severity,
        "unread": total_unread,
        "from_boekhouder": from_boekhouder,
        "top_sender": top_sender,
    }]


def _admin_collectief_glow(user_id: str) -> List[Dict]:
    """v4_admin_collectief_001 — glow voor admin als er unread berichten in admin-collectief staan."""
    if not ADMIN_COLLECTIEF_FILE.exists():
        return []
    data = load_json(ADMIN_COLLECTIEF_FILE, default={"messages": []})
    unread = sum(1 for m in data.get("messages", []) if user_id in (m.get("unread_by") or []))
    if unread == 0:
        return []
    severity = "red" if unread >= 3 else "amber"
    return [{"kind": "admin_collectief", "severity": severity, "unread": unread}]


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
        items.extend(_prive_glow_for_user(user_id))
        # admin-collectief alleen voor gradatie ≤ 2 (admins)
        u = _get_user(user_id)
        if u and (u.get("gradatie") or 7) <= 2:
            items.extend(_admin_collectief_glow(user_id))

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
        elif it["kind"] == "prive_dm":
            _push("chat", it["severity"])
            _push("chat-prive", it["severity"])
        elif it["kind"] == "admin_collectief":
            _push("chat", it["severity"])
            _push("chat-prive", it["severity"])
            _push("chat-admin-collectief", it["severity"])

    return {"glow": glow, "items": items, "checked_at": datetime.now(timezone.utc).isoformat()}



@router.post("/acknowledge")
async def acknowledge(user_id: str, event_id: Optional[str] = None, all_agenda: bool = False):
    """
    Markeer een urgent agenda-event als 'gezien' zodat de glow uitgaat.
    - event_id: specifiek event acknowledgen
    - all_agenda=true: alle huidige urgente agenda-items in 1x stoppen met glowen
    Ack geldt tot event_dt+10min (daarna wordt de ack auto-pruned).
    """
    if not user_id:
        return {"success": False, "error": "user_id vereist"}
    acks = _load_acks(user_id)
    urgent_items = _agenda_glow_for_user(user_id) if all_agenda else []
    targets = []
    if all_agenda:
        targets = [it["event_id"] for it in urgent_items if it.get("event_id")]
    elif event_id:
        targets = [event_id]
    if not targets:
        return {"success": True, "acknowledged": [], "message": "Niets om te acknowledgen"}

    user = _get_user(user_id)
    tz_name = user_time_service.resolve_user_timezone(user)
    fpath = AGENDA_DIR / f"{user_id}.json"
    data = load_json(fpath, default={"events": []})
    ev_index = {ev.get("id"): ev for ev in data.get("events", []) if ev.get("id")}

    acknowledged = []
    for eid in targets:
        ev = ev_index.get(eid)
        if not ev:
            continue
        ev_dt = _parse_event_datetime(ev, tz_name)
        until = (ev_dt + timedelta(minutes=10)) if ev_dt else (datetime.now(timezone.utc) + timedelta(hours=2))
        acks[eid] = until.isoformat()
        acknowledged.append(eid)
    _save_acks(user_id, acks)
    return {"success": True, "acknowledged": acknowledged, "count": len(acknowledged)}


@router.get("/upcoming-spoken")
async def upcoming_spoken(user_id: str):
    """
    Geeft een door Spark uit te spreken zin voor de eerstvolgende afspraak (binnen 60min).
    Returnt {message, event_id, minutes_until, starts_at} of {} als geen.
    Gebruikt door chat/welcome en optioneel polled door frontend.
    """
    items = _agenda_glow_for_user(user_id)
    if not items:
        return {}
    # Eerste/dichtstbijzijnde
    items.sort(key=lambda x: x.get("minutes_until", 999))
    nxt = items[0]
    user = _get_user(user_id)
    tz_name = user_time_service.resolve_user_timezone(user)
    try:
        from zoneinfo import ZoneInfo
        dt_local = datetime.fromisoformat(nxt["starts_at"]).astimezone(ZoneInfo(tz_name))
        time_str = dt_local.strftime("%H:%M")
    except Exception:
        time_str = ""
    minutes = nxt["minutes_until"]
    title = nxt["title"]
    if minutes <= 0:
        msg = f"Je hebt nu een afspraak: **{title}**."
    elif minutes <= 15:
        msg = f"Let op — over {minutes} minuten heb je **{title}** om {time_str}."
    else:
        msg = f"Straks om {time_str} heb je een afspraak: **{title}** (over {minutes} min)."
    return {
        "message": msg,
        "event_id": nxt.get("event_id"),
        "minutes_until": minutes,
        "title": title,
        "starts_at": nxt["starts_at"],
    }
