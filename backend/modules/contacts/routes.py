"""
Contacts Module (v4_contacts_001) — Privé-gesprekken tussen users en bots.

Gradatie-zichtbaarheidsregels:
  Grad 1-3 (admin tier):       Zien ALLE users met echte naam + alle bots.
  Grad 4-7 (gewone users):     Zien admin-users (grad 1-3) anoniem als "Admin" + bots met echte naam.
                                Andere gewone users (grad 4-7) zijn niet zichtbaar onderling.

Online status:
  • Bots: altijd "online"
  • Users: online als last_active < 5 min geleden

Storage:
  Privé-berichten → /data/chat/prive/<conv_key>.json
  conv_key = sorted([user_a, user_b]).join("__")
"""
import json
import uuid
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from modules.core.storage import load_json, save_json

router = APIRouter(prefix="/contacts", tags=["contacts"])

DATA_ROOT = Path(__file__).parent.parent.parent / "data"
USERS_FILE = DATA_ROOT / "system" / "users.json"
PRIVE_DIR = DATA_ROOT / "chat" / "prive"
PRIVE_DIR.mkdir(parents=True, exist_ok=True)
ADMIN_COLLECTIEF_ID = "admin-collectief"
ADMIN_COLLECTIEF_FILE = DATA_ROOT / "chat" / "admin-collectief.json"

ONLINE_WINDOW_MIN = 5  # last_active < 5 min = online
ADMIN_GRADATIE_MAX = 3  # 1, 2, 3 zijn admin tier
ADMIN_COLLECTIEF_MAX = 2  # alleen gradatie 1+2 mogen in admin-collectief
COLORS = ["#f59e0b", "#3b82f6", "#22c55e", "#a855f7", "#ec4899", "#06b6d4", "#84cc16"]


def _admin_collectief_members() -> List[dict]:
    """Alle users met gradatie ≤ 2 die niet bot/Spark zijn."""
    data = load_json(USERS_FILE, default={"users": []})
    out = []
    for u in data.get("users", []):
        if (u.get("gradatie") or 7) > ADMIN_COLLECTIEF_MAX:
            continue
        if _is_bot(u):
            continue
        if u.get("id") == "user-000":
            continue
        out.append(u)
    return out


# ============== HELPERS ==============
def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_iso(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _is_online(user: dict) -> bool:
    if user.get("type") == "bot" or user.get("rol") == "AI Assistant & Digital Companion":
        return True
    la = _parse_iso(user.get("last_active"))
    if not la:
        return False
    return (_now() - la) <= timedelta(minutes=ONLINE_WINDOW_MIN)


def _is_bot(user: dict) -> bool:
    return user.get("type") == "bot" or str(user.get("id", "")).startswith("bot-")


def _get_user(user_id: str) -> Optional[dict]:
    data = load_json(USERS_FILE, default={"users": []})
    for u in data.get("users", []):
        if u.get("id") == user_id:
            return u
    return None


def _conv_key(a: str, b: str) -> str:
    return "__".join(sorted([a, b]))


def _conv_file(a: str, b: str) -> Path:
    return PRIVE_DIR / f"{_conv_key(a, b)}.json"


def _color_for(idx: int) -> str:
    return COLORS[idx % len(COLORS)]


def _avatar(naam: str) -> str:
    return (naam or "?")[0].upper()


def _last_message_for(a: str, b: str) -> Optional[dict]:
    fp = _conv_file(a, b)
    if not fp.exists():
        return None
    data = load_json(fp, default={"messages": []})
    msgs = data.get("messages", [])
    return msgs[-1] if msgs else None


def _unread_for(a: str, b: str, viewer: str) -> int:
    """Aantal berichten in conv waarvoor viewer in 'unread_by' staat."""
    fp = _conv_file(a, b)
    if not fp.exists():
        return 0
    data = load_json(fp, default={"messages": []})
    return sum(1 for m in data.get("messages", []) if viewer in m.get("unread_by", []))


# ============== MODELS ==============
class SendMessage(BaseModel):
    from_user_id: str
    to_user_id: str
    text: str


# ============== ROUTES ==============
@router.get("/list")
async def list_contacts(user_id: str) -> Dict:
    """Geef gradatie-gefilterde contactenlijst voor deze viewer."""
    viewer = _get_user(user_id)
    if not viewer:
        raise HTTPException(status_code=404, detail="User niet gevonden")
    data = load_json(USERS_FILE, default={"users": []})
    viewer_grad = viewer.get("gradatie", 7) or 7
    viewer_is_admin = viewer_grad <= ADMIN_GRADATIE_MAX

    # Helpdesk-modus: gewone users zien admins gegroepeerd tot 1 enkele "Admin" contact
    # dat naar de PRIMARY admin (laagste gradatie, eerst gevonden) routeert.
    primary_admin = None
    if not viewer_is_admin:
        for u in data.get("users", []):
            ug = u.get("gradatie", 7) or 7
            if ug <= ADMIN_GRADATIE_MAX and not _is_bot(u) and u.get("id") != user_id:
                if primary_admin is None or ug < (primary_admin.get("gradatie") or 7):
                    primary_admin = u

    contacts: List[Dict] = []
    admin_grouped_added = False

    # v4_admin_collectief_001: virtueel "Admin Collectief" contact bovenaan voor admins (grad ≤ 2)
    if viewer_grad <= ADMIN_COLLECTIEF_MAX:
        ac_data = load_json(ADMIN_COLLECTIEF_FILE, default={"messages": []})
        ac_msgs = ac_data.get("messages", [])
        ac_last = ac_msgs[-1] if ac_msgs else None
        ac_unread = sum(1 for m in ac_msgs if user_id in (m.get("unread_by") or []))
        ac_last_time = ""
        if ac_last:
            try:
                t = _parse_iso(ac_last.get("ts"))
                if t:
                    delta = _now() - t
                    if delta < timedelta(minutes=1):
                        ac_last_time = "nu"
                    elif delta < timedelta(hours=1):
                        ac_last_time = f"{int(delta.total_seconds() / 60)}m"
                    elif delta < timedelta(days=1):
                        ac_last_time = t.astimezone().strftime("%H:%M")
                    else:
                        ac_last_time = t.astimezone().strftime("%d/%m")
            except Exception:
                pass
        members = _admin_collectief_members()
        contacts.append({
            "id": ADMIN_COLLECTIEF_ID,
            "naam": "Admin Collectief",
            "avatar": "🛡️",
            "color": "#f59e0b",
            "online": True,
            "is_bot": False,
            "is_admin_contact": False,
            "is_collective": True,
            "rol": f"{len(members)} leden",
            "gradatie": None,
            "last_message": (ac_last.get("text") or "")[:80] if ac_last else "Privé kanaal voor alle admins",
            "last_time": ac_last_time,
            "unread": ac_unread,
        })

    for idx, u in enumerate(data.get("users", [])):
        uid = u.get("id")
        if not uid or uid == user_id:
            continue  # niet zichzelf
        # Spark AI niet als prive-contact tonen (heeft eigen tab "Spark AI")
        if uid == "user-000" or (u.get("rol") or "").startswith("AI Assistant"):
            continue

        is_bot = _is_bot(u)
        target_grad = u.get("gradatie", 7) or 7
        target_is_admin = target_grad <= ADMIN_GRADATIE_MAX

        # Zichtbaarheidsregels
        if viewer_is_admin:
            # Admin ziet iedereen met echte naam
            display_name = u.get("naam") or "Onbekend"
            display_role = u.get("rol") or f"Gradatie {target_grad}"
            anonymized = False
            actual_id = uid
        else:
            # Gewone user
            if is_bot:
                display_name = u.get("naam") or "Bot"
                display_role = "Bot"
                anonymized = False
                actual_id = uid
            elif target_is_admin:
                # Helpdesk-modus: groepeer alle admins tot 1 contact
                if admin_grouped_added or not primary_admin:
                    continue
                admin_grouped_added = True
                display_name = "Admin"
                display_role = "Spark Team"
                anonymized = True
                actual_id = primary_admin.get("id")
                # Online als ENIGE admin online is
                u = primary_admin  # voor _is_online check hieronder
            else:
                # Andere gewone users → niet zichtbaar onderling
                continue

        last = _last_message_for(user_id, actual_id)
        unread = _unread_for(user_id, actual_id, user_id)
        last_time = ""
        if last:
            try:
                t = _parse_iso(last.get("ts"))
                if t:
                    delta = _now() - t
                    if delta < timedelta(minutes=1):
                        last_time = "nu"
                    elif delta < timedelta(hours=1):
                        last_time = f"{int(delta.total_seconds() / 60)}m"
                    elif delta < timedelta(days=1):
                        last_time = t.astimezone().strftime("%H:%M")
                    else:
                        last_time = t.astimezone().strftime("%d/%m")
            except Exception:
                last_time = ""

        contacts.append({
            "id": actual_id,
            "naam": display_name,
            "avatar": _avatar(display_name),
            "color": _color_for(idx),
            "online": _is_online(u),
            "is_bot": is_bot,
            "is_admin_contact": anonymized,
            "rol": display_role,
            "gradatie": None if anonymized else target_grad,
            "last_message": (last.get("text") or "")[:80] if last else "",
            "last_time": last_time,
            "unread": unread,
        })

    # Sorteer: ongelezen eerst, dan online, dan op laatste activiteit
    contacts.sort(key=lambda c: (-c["unread"], not c["online"], -(len(c["last_message"]))))
    return {"contacts": contacts, "viewer": {"id": user_id, "gradatie": viewer_grad, "is_admin": viewer_is_admin}}


@router.get("/messages")
async def get_messages(user_id: str, contact_id: str, mark_read: bool = True) -> Dict:
    """Haal alle berichten op tussen user_id en contact_id (oplopend op tijd)."""
    # v4_admin_collectief_001: speciaal kanaal
    if contact_id == ADMIN_COLLECTIEF_ID:
        viewer = _get_user(user_id)
        if not viewer or (viewer.get("gradatie") or 7) > ADMIN_COLLECTIEF_MAX:
            raise HTTPException(403, "Alleen admins (gradatie ≤ 2) hebben toegang")
        data = load_json(ADMIN_COLLECTIEF_FILE, default={"messages": []})
        msgs = data.get("messages", [])
        if mark_read and msgs:
            changed = False
            for m in msgs:
                if user_id in (m.get("unread_by") or []):
                    m["unread_by"] = [x for x in m["unread_by"] if x != user_id]
                    changed = True
            if changed:
                save_json(ADMIN_COLLECTIEF_FILE, data)
        return {"conv_key": ADMIN_COLLECTIEF_ID, "messages": msgs, "count": len(msgs)}

    fp = _conv_file(user_id, contact_id)
    data = load_json(fp, default={"messages": []})
    msgs = data.get("messages", [])

    if mark_read and msgs:
        changed = False
        for m in msgs:
            if user_id in m.get("unread_by", []):
                m["unread_by"] = [x for x in m["unread_by"] if x != user_id]
                changed = True
        if changed:
            save_json(fp, data)

    return {
        "conv_key": _conv_key(user_id, contact_id),
        "messages": msgs,
        "count": len(msgs),
    }


@router.post("/send")
async def send_message(req: SendMessage) -> Dict:
    """Stuur een privé-bericht."""
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Leeg bericht")
    sender = _get_user(req.from_user_id)
    if not sender:
        raise HTTPException(status_code=404, detail="Sender niet gevonden")

    # v4_admin_collectief_001: broadcast naar gedeelde admin-collectief
    if req.to_user_id == ADMIN_COLLECTIEF_ID:
        if (sender.get("gradatie") or 7) > ADMIN_COLLECTIEF_MAX:
            raise HTTPException(403, "Alleen admins (gradatie ≤ 2) mogen posten in admin-collectief")
        data = load_json(ADMIN_COLLECTIEF_FILE, default={"messages": []})
        members = _admin_collectief_members()
        unread_for = [m["id"] for m in members if m.get("id") and m.get("id") != req.from_user_id]
        msg = {
            "id": f"ac-{uuid.uuid4().hex[:8]}",
            "from_user_id": req.from_user_id,
            "from_naam": sender.get("naam") or "Admin",
            "to_user_id": ADMIN_COLLECTIEF_ID,
            "text": req.text.strip(),
            "ts": _now().isoformat(),
            "unread_by": unread_for,
            "channel": "admin-collectief",
        }
        data["messages"] = data.get("messages", []) + [msg]
        if len(data["messages"]) > 500:
            data["messages"] = data["messages"][-500:]
        save_json(ADMIN_COLLECTIEF_FILE, data)
        return {"ok": True, "message": msg, "total": len(data["messages"]), "broadcast_to": len(unread_for)}

    recipient = _get_user(req.to_user_id)
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient niet gevonden")

    fp = _conv_file(req.from_user_id, req.to_user_id)
    data = load_json(fp, default={"messages": []})

    msg = {
        "id": f"pm-{uuid.uuid4().hex[:8]}",
        "from_user_id": req.from_user_id,
        "from_naam": sender.get("naam") or "Onbekend",
        "to_user_id": req.to_user_id,
        "text": req.text.strip(),
        "ts": _now().isoformat(),
        "unread_by": [req.to_user_id],  # recipient ziet 'm als unread tot hij opent
    }
    data["messages"] = data.get("messages", []) + [msg]
    save_json(fp, data)

    # Snap-systeem + Shadow Observer (v4_contacts_002) — leer ook uit privé-gesprekken
    # Niet-blokkerend: chat mag nooit breken door snap/shadow
    try:
        from modules.chat.snap_service import SnapNLPService
        from modules.chat import shadow_observer
        snap = SnapNLPService()
        sentiment = snap.detect_sentiment(req.text)
        meaningful = snap._extract_meaningful_words(req.text) if hasattr(snap, "_extract_meaningful_words") else []
        shadow_response = {
            "type": "prive_message",
            "message": req.text[:200],
            "sentiment": sentiment,
            "unknown_words": [],
            "knowledge_matches": [],
            "channel": "prive",
            "to_user_id": req.to_user_id,
            "is_bot_target": _is_bot(recipient),
            "meaningful_words": meaningful[:15],
        }
        shadow_observer.record(req.from_user_id, req.text, shadow_response, "prive")
    except Exception:
        pass

    # Bot auto-reply (eenvoudig: vraag aan chat-route met channel=prive zou kunnen,
    # nu simpel: bot stuurt directe acknowledgement)
    if _is_bot(recipient):
        bot_reply = _bot_auto_reply(recipient, sender, req.text)
        if bot_reply:
            reply_msg = {
                "id": f"pm-{uuid.uuid4().hex[:8]}",
                "from_user_id": req.to_user_id,
                "from_naam": recipient.get("naam") or "Bot",
                "to_user_id": req.from_user_id,
                "text": bot_reply,
                "ts": _now().isoformat(),
                "unread_by": [req.from_user_id],
                "is_bot": True,
            }
            data["messages"].append(reply_msg)
            save_json(fp, data)

    return {"ok": True, "message": msg, "total": len(data["messages"])}


def _bot_auto_reply(bot: dict, sender: dict, text: str) -> Optional[str]:
    """Eenvoudige bot-reply op basis van bot persoonlijkheid.
    Houd het simpel — voor volwaardige NLP kan user later via Spark AI tab praten."""
    naam = sender.get("naam") or "vriend"
    bot_naam = bot.get("naam") or "Bot"
    pi = bot.get("persoonlijke_info") or {}
    persona = (bot.get("persoonlijkheid") or pi.get("persoonlijkheid") or "").lower()
    bio = (bot.get("bio") or pi.get("bio") or "").lower()
    t = (text or "").lower()

    # Tijd-vraag (Harry) — eerst, voor groet, want "hey hoe laat" zou anders als groet eindigen
    if ("klok" in bio or "tijd" in bio) and any(w in t for w in ["hoe laat", "tijd", "wanneer", "klok", "uur"]):
        from datetime import datetime as _dt
        return f"Het is nu {_dt.now().strftime('%H:%M')}. ⏰"

    # Basis groet-detectie
    if any(g in t for g in ["hallo", "hoi", "hey", "goedemorgen", "goedemiddag", "goedenavond"]):
        if "sociaal" in persona or "vriendelijk" in persona:
            return f"Hoi {naam}! Wat fijn dat je me prive een berichtje stuurt. Wat is er aan de hand? 😊"
        if "punctueel" in persona:
            return f"Hallo {naam}. Stipt op tijd ben je. Wat kan ik voor je doen?"
        if "security" in persona or "analytisch" in persona:
            return f"Bericht ontvangen, {naam}. Status: alles ok. Wat is je vraag?"
        return f"Hallo {naam}, met {bot_naam}."

    # Default per persoonlijkheid
    if "sociaal" in persona or "vriendelijk" in persona:
        return f"Ik snap je, {naam}. Vertel eens meer? 💚"
    if "punctueel" in persona:
        return "Genoteerd. Wil je dat ik een herinnering inplan?"
    if "security" in persona or "analytisch" in persona:
        return f"Ik analyseer wat je zegt, {naam}. Geef me wat meer context?"
    return f"Hoi {naam}, ik ben {bot_naam}. Bedankt voor je bericht."
