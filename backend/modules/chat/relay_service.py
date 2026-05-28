"""
Relay Service (v6_spark_relay_001 — 28 mei 2026)
=====================================================
Spark als bode: user A vraagt Spark om bericht door te geven aan user B.
Bericht krijgt attributie ("Willem zegt: ...") en wordt opgeslagen in
de inbox van de ontvanger.

Triggers (NL):
  - "zeg tegen Marieke dat ..."
  - "vraag aan Gijs of ..."
  - "geef Anneke door dat ..."
  - "laat Marieke weten dat ..."
  - "stuur Marieke een bericht: ..."

Privacy-regels:
  - Sender moet bestaan
  - Recipient moet gevonden worden via name resolution (zelfde regels als profile_lookup)
  - Recipient moet in vrienden-graaf van sender óf admin (gradatie ≤ 2)
"""
import re
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict

from modules.core.storage import load_json, save_json

DATA_ROOT = Path(__file__).parent.parent.parent / "data"
INBOX_DIR = DATA_ROOT / "users"  # per-user inbox in /users/{user_id}/spark_inbox.json


# Patronen — vangt naam + payload
_RELAY_PATTERNS = [
    # "zeg tegen X dat ..." / "zeg X dat ..."
    r"^(?:zeg|geef door|laat (?:weten)?)\s+(?:tegen\s+|aan\s+)?([A-ZÀ-Ÿa-zà-ÿ][\w\- ']{1,30})\s+(?:dat|of)\s+(.+)$",
    # "vraag aan X of ..."
    r"^vraag\s+(?:aan\s+|de\s+)?([A-ZÀ-Ÿa-zà-ÿ][\w\- ']{1,30})\s+(?:of|dat)\s+(.+)$",
    # "stuur X een bericht: ..."
    r"^stuur\s+(?:aan\s+)?([A-ZÀ-Ÿa-zà-ÿ][\w\- ']{1,30})\s+(?:een\s+)?bericht[:\s]+(.+)$",
    # "laat X weten dat ..."
    r"^laat\s+([A-ZÀ-Ÿa-zà-ÿ][\w\- ']{1,30})\s+weten\s+dat\s+(.+)$",
]


def _users():
    d = load_json(DATA_ROOT / "system" / "users.json", default={"users": []})
    return d.get("users", []) if isinstance(d, dict) else d


def _agenda_busy_now(user_id: str) -> Optional[dict]:
    """v6_voicemail_agenda_001 (28 mei) — check of user nu een agenda-event heeft.
    Returns dict {titel, start, eind} of None.
    """
    AGENDA_DIR = DATA_ROOT / "agenda"
    user_agenda = AGENDA_DIR / f"{user_id}.json"
    if not user_agenda.exists():
        return None
    d = load_json(user_agenda, default={"events": []})
    events = d.get("events", []) if isinstance(d, dict) else d
    now = datetime.now(timezone.utc)
    for ev in events:
        try:
            start = datetime.fromisoformat(ev.get("start", "").replace("Z", "+00:00"))
            end_str = ev.get("eind") or ev.get("end")
            if end_str:
                end = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
            else:
                # default duur 1 uur
                end = start.replace(hour=start.hour+1) if start.hour < 23 else start
            if start.tzinfo is None:
                start = start.replace(tzinfo=timezone.utc)
                end = end.replace(tzinfo=timezone.utc)
            if start <= now <= end:
                return {"titel": ev.get("titel") or ev.get("title", "afspraak"),
                        "start": start.isoformat(), "eind": end.isoformat()}
        except Exception:
            continue
    return None


def _find_recipient(name_query: str):
    """Resolve recipient by partial match op naam."""
    q = (name_query or "").strip().lower()
    if not q:
        return None
    for u in _users():
        full = (u.get("naam") or u.get("name") or "").lower()
        if q == full or q in full.split() or q in full:
            return u
    return None


def _has_friendship(sender_id: str, recipient_id: str) -> bool:
    """Check of recipient in vrienden-graaf van sender staat."""
    rel = DATA_ROOT / "persons" / f"{sender_id}_relationships.json"
    if not rel.exists():
        return False
    d = load_json(rel, default={"relationships": []})
    rels = d.get("relationships", []) if isinstance(d, dict) else d
    for r in rels:
        if r.get("user_id") == recipient_id:
            return True
    return False


def _push_inbox(recipient_id: str, msg_record: dict):
    """Append message to recipient's spark_inbox.json."""
    inbox_path = INBOX_DIR / recipient_id / "spark_inbox.json"
    inbox_path.parent.mkdir(parents=True, exist_ok=True)
    d = load_json(inbox_path, default={"messages": []})
    d.setdefault("messages", []).append(msg_record)
    d["last_updated"] = datetime.now(timezone.utc).isoformat()
    save_json(inbox_path, d)


def detect_relay(text: str, sender_id: str, sender_naam: str = "") -> Optional[Dict]:
    """Detecteert relay-intent. Returns response-dict of None."""
    if not text or len(text) < 8:
        return None
    t = text.strip()
    name_q = None
    payload = None
    for pat in _RELAY_PATTERNS:
        m = re.match(pat, t, re.IGNORECASE)
        if not m:
            continue
        name_q = m.group(1).strip().rstrip(",.")
        payload = m.group(2).strip().rstrip(".")
        break
    if not name_q or not payload:
        return None

    # Resolve recipient
    recipient = _find_recipient(name_q)
    if not recipient:
        return {
            "type": "relay_no_recipient",
            "message": f"Ik ken geen '{name_q}'. Geef je de juiste naam?",
        }
    rid = recipient.get("id")
    if rid == sender_id:
        return {"type": "relay_self", "message": "Dat ben jij zelf — geen bode nodig 😄"}

    # Privacy: alleen admin (≤2) of vrienden
    sender_users = [u for u in _users() if u.get("id") == sender_id]
    sender_grad = int(sender_users[0].get("gradatie", 7) or 7) if sender_users else 7
    if sender_grad > 2 and not _has_friendship(sender_id, rid):
        return {
            "type": "relay_denied",
            "message": f"Ik kan {recipient.get('naam')} alleen een bericht sturen als jullie vrienden zijn.",
        }

    # Persist message
    msg = {
        "id": f"relay-{uuid.uuid4().hex[:8]}",
        "from_user_id": sender_id,
        "from_user_naam": sender_naam or sender_users[0].get("naam", "?") if sender_users else "?",
        "via": "Spark (bode)",
        "text": payload,
        "ts": datetime.now(timezone.utc).isoformat(),
        "read": False,
    }
    _push_inbox(rid, msg)

    # v6_voicemail_agenda_001 — als recipient nu een agenda-event heeft, meld dat
    busy = _agenda_busy_now(rid)
    extra = ""
    if busy:
        from datetime import datetime as _dt
        try:
            end_dt = _dt.fromisoformat(busy["eind"].replace("Z", "+00:00"))
            tijd_klaar = end_dt.strftime("%H:%M")
            extra = f"\n\n_Heads-up: {recipient.get('naam')} is nu bezig met '{busy['titel']}' tot {tijd_klaar} — antwoord komt dus mogelijk later._"
        except Exception:
            pass

    return {
        "type": "relay_sent",
        "recipient_id": rid,
        "recipient_naam": recipient.get("naam"),
        "message_id": msg["id"],
        "recipient_busy": busy,
        "message": f"📨 Bericht voor **{recipient.get('naam')}** in hun Spark-inbox gezet:\n\n> \"{payload}\"\n\n_Komt door als ze inloggen. Attributie: {msg['from_user_naam']} (via Spark)._{extra}",
    }


def get_inbox(user_id: str, limit: int = 50):
    inbox_path = INBOX_DIR / user_id / "spark_inbox.json"
    d = load_json(inbox_path, default={"messages": []})
    msgs = d.get("messages", [])[-limit:]
    return list(reversed(msgs))


def mark_read(user_id: str, message_id: str) -> bool:
    inbox_path = INBOX_DIR / user_id / "spark_inbox.json"
    d = load_json(inbox_path, default={"messages": []})
    changed = False
    for m in d.get("messages", []):
        if m.get("id") == message_id:
            m["read"] = True
            m["read_at"] = datetime.now(timezone.utc).isoformat()
            changed = True
            break
    if changed:
        save_json(inbox_path, d)
    return changed
