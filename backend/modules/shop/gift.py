"""
v5_roar_gift_001 — ROAR token gift met paper-trail.

Flow:
  1. Sender klikt 🎁 Gift in wallet, kiest recipient + amount
  2. POST /api/shop/gift  → maakt 'pending' gift_request, neemt token NIET weg (escrow notie)
     • Notification naar recipient ("X wil je N token(s) sturen — accepteer of weiger")
  3. Recipient POST /api/shop/gift/{id}/accept → token wordt naar zijn wallet getransfereerd
     • OF /api/shop/gift/{id}/reject → status='rejected', sender's token blijft
  4. Na 24h zonder reactie → status='expired' (lazy-check bij elke list/get)

Audit-trail: roar_balances.transactions + audit_log entry per actie.
"""
import threading
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from modules.core.storage import load_json, save_json
from modules.core.spark_logger import traced

router = APIRouter(prefix="/shop", tags=["shop-gift"])

# v6_gift_idempotent_001 — global lock om race-conditions (dubbel accept/reject) te voorkomen
_gift_lock = threading.Lock()

DATA_DIR = Path(__file__).parent.parent.parent / "data"
GIFTS_FILE = DATA_DIR / "roar" / "gift_requests.json"
ROAR_FILE = DATA_DIR / "roar" / "roar_balances.json"
USER_WALLETS = DATA_DIR / "wallet" / "user_wallets.json"
NOTIF_FILE = DATA_DIR / "notifications" / "notifications.json"
USERS_FILE = DATA_DIR / "system" / "users.json"

EXPIRY_HOURS = 24


def _now():
    return datetime.now(timezone.utc)


def _iso():
    return _now().isoformat()


def _load_gifts() -> dict:
    return load_json(GIFTS_FILE, default={"gifts": []})


def _save_gifts(data: dict):
    GIFTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    save_json(GIFTS_FILE, data)


def _user_naam(uid: str) -> str:
    data = load_json(USERS_FILE, default={"users": []})
    for u in data.get("users", []):
        if u.get("id") == uid:
            return u.get("naam") or uid
    return uid


def _notify(user_id: str, title: str, message: str, icon: str = "🎁", kind: str = "gift"):
    NOTIF_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = load_json(NOTIF_FILE, default={"notifications": []})
    data.setdefault("notifications", []).append({
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "kind": kind,
        "icon": icon,
        "title": title,
        "message": message,
        "created_at": _iso(),
        "read": False,
    })
    save_json(NOTIF_FILE, data)


def _expire_overdue(gifts_data: dict) -> bool:
    """Markeer pending gifts ouder dan EXPIRY_HOURS als expired. Returns True if mutated."""
    changed = False
    cutoff = _now() - timedelta(hours=EXPIRY_HOURS)
    for g in gifts_data.get("gifts", []):
        if g.get("status") == "pending":
            try:
                created = datetime.fromisoformat(g.get("created_at", "").replace("Z", "+00:00"))
            except Exception:
                continue
            if created < cutoff:
                g["status"] = "expired"
                g["expired_at"] = _iso()
                changed = True
                _notify(
                    g.get("sender_id"),
                    "Gift verlopen", f"Je gift van {g.get('amount')} ROAR aan {_user_naam(g.get('recipient_id'))} is verlopen (24h zonder reactie). Je tokens zijn behouden.",
                    icon="⏰", kind="gift_expired",
                )
    return changed


# ============================================================
# MODELS
# ============================================================

class GiftCreate(BaseModel):
    sender_id: str
    recipient_id: str
    amount: int = Field(..., ge=1, le=100)
    note: Optional[str] = None


class GiftAction(BaseModel):
    actor_id: str


# ============================================================
# ENDPOINTS
# ============================================================

@router.post("/gift")
@traced(intent="ROAR gift initieren (sender → recipient pending)", module="shop_gift")
async def create_gift(req: GiftCreate):
    """Sender start een gift. Tokens worden NIET direct overgeboekt — escrow in 'pending'."""
    if req.sender_id == req.recipient_id:
        raise HTTPException(400, "Je kunt geen gift naar jezelf sturen")

    # Check sender balance
    roar = load_json(ROAR_FILE, default={"balances": {}, "transactions": []})
    sender_bal = int(roar.get("balances", {}).get(req.sender_id, 0))
    if sender_bal < req.amount:
        raise HTTPException(400, f"Onvoldoende ROAR. Heb {sender_bal}, wil {req.amount} versturen.")

    # Check pending van sender naar recipient bestaat al? Niet blokken, maar info
    gifts_data = _load_gifts()
    _expire_overdue(gifts_data)

    gift_id = str(uuid.uuid4())
    created = _iso()
    expires = (_now() + timedelta(hours=EXPIRY_HOURS)).isoformat()
    gift = {
        "id": gift_id,
        "sender_id": req.sender_id,
        "sender_naam": _user_naam(req.sender_id),
        "recipient_id": req.recipient_id,
        "recipient_naam": _user_naam(req.recipient_id),
        "amount": req.amount,
        "note": req.note or "",
        "status": "pending",
        "created_at": created,
        "expires_at": expires,
        "accepted_at": None,
        "rejected_at": None,
    }
    gifts_data.setdefault("gifts", []).append(gift)
    _save_gifts(gifts_data)

    # Notificatie naar recipient
    _notify(
        req.recipient_id,
        f"🎁 Gift van {gift['sender_naam']}: {req.amount} ROAR",
        f"{gift['sender_naam']} wil je {req.amount} ROAR token{'s' if req.amount > 1 else ''} sturen."
        + (f"\n\nNotitie: \"{req.note}\"" if req.note else "")
        + f"\n\nGa naar Wallet → Inkomende gifts om te accepteren of weigeren. Verloopt over 24 uur.",
        icon="🎁", kind="gift_incoming",
    )
    return {"success": True, "gift": gift}


@router.get("/gift/inbox/{user_id}")
async def list_inbox(user_id: str):
    """Pending gifts gericht aan user_id (incl. retroactieve expire-check)."""
    data = _load_gifts()
    if _expire_overdue(data):
        _save_gifts(data)
    inbox = [g for g in data.get("gifts", []) if g.get("recipient_id") == user_id and g.get("status") == "pending"]
    return {"success": True, "gifts": inbox, "count": len(inbox)}


@router.get("/gift/outbox/{user_id}")
async def list_outbox(user_id: str):
    """Alle gifts verstuurd door user (alle statussen) — paper trail voor sender."""
    data = _load_gifts()
    if _expire_overdue(data):
        _save_gifts(data)
    out = [g for g in data.get("gifts", []) if g.get("sender_id") == user_id]
    out.sort(key=lambda g: g.get("created_at", ""), reverse=True)
    return {"success": True, "gifts": out, "count": len(out)}


@router.post("/gift/{gift_id}/accept")
@traced(intent="ROAR gift accepteren (token-transfer recipient)", module="shop_gift")
async def accept_gift(gift_id: str, req: GiftAction):
    """Recipient accepteert: voer transfer uit, sluit gift."""
    # v6_gift_idempotent_001 — ALLE state-mutaties binnen 1 lock om dubbel-verwerken te voorkomen
    with _gift_lock:
        data = _load_gifts()
        _expire_overdue(data)
        gift = next((g for g in data.get("gifts", []) if g.get("id") == gift_id), None)
        if not gift:
            raise HTTPException(404, "Gift niet gevonden")
        if gift.get("recipient_id") != req.actor_id:
            raise HTTPException(403, "Alleen recipient kan accepteren")
        if gift.get("status") == "accepted":
            return {"success": True, "gift": gift, "already_accepted": True}
        if gift.get("status") != "pending":
            raise HTTPException(400, f"Gift heeft status '{gift.get('status')}', kan niet meer geaccepteerd worden")

        # Claim direct binnen lock: status → 'processing' zodat parallelle call afketst
        gift["status"] = "processing"
        _save_gifts(data)

        # Voer transfer uit (sender → recipient)
        roar = load_json(ROAR_FILE, default={"balances": {}, "transactions": []})
        sender = gift["sender_id"]
        recipient = gift["recipient_id"]
        amount = int(gift["amount"])
        sender_bal = int(roar["balances"].get(sender, 0))
        if sender_bal < amount:
            gift["status"] = "failed"
            gift["failed_at"] = _iso()
            gift["failed_reason"] = "Sender heeft niet genoeg tokens meer"
            _save_gifts(data)
            _notify(recipient, "Gift mislukt", f"De gift kon niet worden uitgevoerd: sender heeft niet genoeg tokens meer.", icon="⚠️", kind="gift_failed")
            return {"success": False, "error": "Sender heeft onvoldoende tokens", "gift": gift}

        prev_recipient = int(roar["balances"].get(recipient, 0))
        roar["balances"][sender] = sender_bal - amount
        roar["balances"][recipient] = prev_recipient + amount

        # Audit-trail
        tx = {
            "id": str(uuid.uuid4()),
            "ts": _iso(),
            "type": "gift",
            "from_user_id": sender,
            "to_user_id": recipient,
            "amount": amount,
            "gift_id": gift_id,
            "note": gift.get("note", ""),
            "status": "completed",
        }
        roar.setdefault("transactions", []).append(tx)
        roar.setdefault("admin_log", []).append({
            "ts": _iso(),
            "action": "gift_accepted",
            "from_user_id": sender,
            "to_user_id": recipient,
            "amount": amount,
            "gift_id": gift_id,
        })
        save_json(ROAR_FILE, roar)

        # Sync user_wallets
        try:
            uw = load_json(USER_WALLETS, default={"user_wallets": {}})
            for uid in (sender, recipient):
                e = uw.setdefault("user_wallets", {}).setdefault(uid, {"wallet": {}})
                e.setdefault("wallet", {})["spark_tokens"] = int(roar["balances"].get(uid, 0))
                e["wallet"]["last_sync"] = _iso()
            save_json(USER_WALLETS, uw)
        except Exception:
            pass

        # v6_potje_per_token_001 — sync recipient's potje count to new token balance
        try:
            from modules.trade.potjes import sync_potjes_to_tokens
            sync_potjes_to_tokens(recipient, int(roar["balances"].get(recipient, 0)))
        except Exception as _ex:
            print(f"[potje-sync gift] failed: {_ex}")

        # First-token achievement voor recipient
        try:
            if prev_recipient == 0 and amount > 0:
                from modules.achievements.service import unlock_milestone
                unlock_milestone(recipient, "milestone_first_roar_token")
                _notify(
                    recipient,
                    "Je eerste ROAR token is binnen",
                    "Welkom in de Spark-economie! Eén ROAR token = één bot-slot. "
                    "Met dit token kun je nu een eigen Trader monitor starten via de Trader-module.\n\n"
                    "• De monitor luistert naar 1 markt en analyseert de candles\n"
                    "• Bij auto-trade aan koopt en verkoopt hij automatisch\n"
                    "• Je kunt hem altijd pauzeren of stoppen",
                    icon="🪙", kind="first_roar_token",
                )
        except Exception:
            pass

        # Notificaties
        _notify(sender, f"Gift geaccepteerd door {gift['recipient_naam']}", f"{gift['recipient_naam']} heeft je gift van {amount} ROAR geaccepteerd.", icon="✅", kind="gift_accepted")
        _notify(recipient, f"Gift ontvangen van {gift['sender_naam']}", f"Je hebt {amount} ROAR ontvangen van {gift['sender_naam']}.", icon="🎁", kind="gift_received")

        gift["status"] = "accepted"
        gift["accepted_at"] = _iso()
        _save_gifts(data)

        return {"success": True, "gift": gift, "new_balance": roar["balances"][recipient]}


@router.post("/gift/{gift_id}/reject")
async def reject_gift(gift_id: str, req: GiftAction):
    """Recipient weigert. Geen token-mutatie."""
    with _gift_lock:
        data = _load_gifts()
        _expire_overdue(data)
        gift = next((g for g in data.get("gifts", []) if g.get("id") == gift_id), None)
        if not gift:
            raise HTTPException(404, "Gift niet gevonden")
        if gift.get("recipient_id") != req.actor_id:
            raise HTTPException(403, "Alleen recipient kan weigeren")
        if gift.get("status") == "rejected":
            return {"success": True, "gift": gift, "already_rejected": True}
        if gift.get("status") != "pending":
            raise HTTPException(400, f"Gift heeft status '{gift.get('status')}'")
        gift["status"] = "rejected"
        gift["rejected_at"] = _iso()
        _save_gifts(data)
    _notify(gift["sender_id"], f"Gift geweigerd door {gift['recipient_naam']}", f"{gift['recipient_naam']} heeft je gift van {gift['amount']} ROAR geweigerd. Je tokens zijn behouden.", icon="↩️", kind="gift_rejected")
    return {"success": True, "gift": gift}


@router.post("/gift/{gift_id}/cancel")
async def cancel_gift(gift_id: str, req: GiftAction):
    """Sender annuleert pending gift voordat recipient reageert."""
    with _gift_lock:
        data = _load_gifts()
        _expire_overdue(data)
        gift = next((g for g in data.get("gifts", []) if g.get("id") == gift_id), None)
        if not gift:
            raise HTTPException(404, "Gift niet gevonden")
        if gift.get("sender_id") != req.actor_id:
            raise HTTPException(403, "Alleen sender kan annuleren")
        if gift.get("status") == "cancelled":
            return {"success": True, "gift": gift, "already_cancelled": True}
        if gift.get("status") != "pending":
            raise HTTPException(400, f"Gift heeft status '{gift.get('status')}'")
        gift["status"] = "cancelled"
        gift["cancelled_at"] = _iso()
        _save_gifts(data)
    _notify(gift["recipient_id"], "Gift ingetrokken", f"{gift['sender_naam']} heeft de pending gift van {gift['amount']} ROAR ingetrokken.", icon="↩️", kind="gift_cancelled")
    return {"success": True, "gift": gift}
