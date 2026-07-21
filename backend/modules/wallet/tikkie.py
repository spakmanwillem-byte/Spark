"""
Tikkie Topup Module (v5_tikkie_topup_001) — Wallet opwaarderen via Tikkie.

Flow:
  1. User vult bedrag + naam in, drukt 'Verzenden'
  2. Pending topup wordt opgeslagen
  3. Bot-boekhouder stuurt privé-bericht naar admin (user-001) met details
  4. Admin opent admin-overzicht, ziet pending lijst, na ontvangst Tikkie:
       - Klikt 'Bevestigen' → bedrag wordt op user-wallet bijgeboekt
       - Eventueel: kan saldo verdelen (potje vs vrij saldo)

Storage:
  /data/wallet/tikkie_topups.json:
    {
      "config": { "tikkie_url": "" },
      "topups": [
        { "id", "user_id", "user_naam", "amount_eur", "naam_invoer",
          "status": "pending|confirmed|cancelled",
          "created_at", "confirmed_at", "confirmed_by",
          "potje_amount", "free_amount", "note" }
      ]
    }
"""
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from modules.core.storage import load_json, save_json

router = APIRouter(prefix="/wallet/tikkie", tags=["wallet-tikkie"])

DATA_ROOT = Path(__file__).parent.parent.parent / "data"
TIKKIE_FILE = DATA_ROOT / "wallet" / "tikkie_topups.json"
WALLETS_FILE = DATA_ROOT / "wallet" / "wallets.json"
USERS_FILE = DATA_ROOT / "system" / "users.json"
PRIVE_DIR = DATA_ROOT / "chat" / "prive"
QR_IMAGE = DATA_ROOT / "system" / "assets" / "tikkie_qr.jpg"

ADMIN_USER_ID = "user-001"
BOEKHOUDER_BOT_ID = "bot-boekhouder"
ADMIN_GRADATIE_MAX = 2


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_user(user_id: str) -> Optional[dict]:
    data = load_json(USERS_FILE, default={"users": []})
    for u in data.get("users", []):
        if u.get("id") == user_id:
            return u
    return None


def _is_admin(user_id: str) -> bool:
    u = _get_user(user_id)
    if not u:
        return False
    return (u.get("gradatie") or 7) <= ADMIN_GRADATIE_MAX


def _send_admin_pm(topup: dict) -> None:
    """Stuur privé-bericht van bot-boekhouder naar admin (user-001) + archiveer als bestand."""
    pair = sorted([BOEKHOUDER_BOT_ID, ADMIN_USER_ID])
    fp = PRIVE_DIR / f"{pair[0]}__{pair[1]}.json"
    fp.parent.mkdir(parents=True, exist_ok=True)
    data = load_json(fp, default={"messages": []})
    ref = f"#{topup['id'][:8]}"
    lines = [
        f"💰 Nieuwe Tikkie-aanvraag {ref}",
        "",
        f"👤 User: {topup['user_naam']} ({topup['user_id']})",
        f"✏️  Naam ingevoerd: {topup['naam_invoer']}",
        f"💶 Bedrag: €{topup['amount_eur']:.2f}",
        "",
        "Check Tikkie-app of het bedrag binnen is en bevestig in Wallet → 📥 (admin Tikkie-aanvragen).",
    ]
    msg = {
        "id": f"pm-{uuid.uuid4().hex[:8]}",
        "from_user_id": BOEKHOUDER_BOT_ID,
        "from_naam": "De Boekhouder 🎩",
        "to_user_id": ADMIN_USER_ID,
        "text": "\n".join(lines),
        "ts": _now(),
        "unread_by": [ADMIN_USER_ID],
        "system": True,
        "kind": "tikkie_request",
        "topup_id": topup["id"],
        "topup_ref": ref,
        "is_bot": True,
    }
    data["messages"] = data.get("messages", []) + [msg]
    save_json(fp, data)
    # Archiveer ook als bestand in admin's persoonlijk archief (categorie: bestanden)
    try:
        _archive_tikkie_doc(topup, "aanvraag")
    except Exception as e:
        print(f"[tikkie] archiveer aanvraag gefaald: {e}")


def _archive_tikkie_doc(topup: dict, soort: str) -> None:
    """Schrijf een tekstdocument met Tikkie-details naar admin's archief.
    soort: 'aanvraag' bij nieuwe Tikkie, 'bevestigd' bij confirm.
    """
    admin_archive = DATA_ROOT / "users" / ADMIN_USER_ID / "archive" / "bestanden"
    admin_archive.mkdir(parents=True, exist_ok=True)
    index_file = DATA_ROOT / "users" / ADMIN_USER_ID / "archive" / "_index.json"
    idx_data = load_json(index_file, default={"files": []})
    files_list = idx_data.get("files", []) if isinstance(idx_data, dict) else (idx_data if isinstance(idx_data, list) else [])
    file_id = f"tikkie-{topup['id'][:10]}-{soort}"
    fname = f"{file_id}.txt"
    dest = admin_archive / fname
    lines = [
        f"# Tikkie {soort.title()} — {topup['id']}",
        "",
        f"Aangevraagd: {topup.get('created_at','')}",
        f"User: {topup['user_naam']} ({topup['user_id']})",
        f"Naam-invoer (bij betaling): {topup['naam_invoer']}",
        f"Bedrag: €{topup['amount_eur']:.2f}",
        f"Status: {topup.get('status','pending')}",
    ]
    if soort == "bevestigd":
        lines += [
            f"Bevestigd: {topup.get('confirmed_at','')}",
            f"Door: {topup.get('confirmed_by','')}",
            f"Verdeling: €{topup.get('free_amount',0):.2f} vrij + €{topup.get('potje_amount',0):.2f} potje",
        ]
        if topup.get("note"):
            lines += ["", f"Notitie: {topup['note']}"]
    content = "\n".join(lines).encode("utf-8")
    dest.write_bytes(content)
    # Update index (vervang als al bestaat)
    files_list = [f for f in files_list if f.get("id") != file_id]
    entry = {
        "id": file_id,
        "filename": fname,
        "original_name": f"Tikkie {soort} {topup['id'][:8]}.txt",
        "category": "bestanden",
        "extension": ".txt",
        "mime_type": "text/plain",
        "size_bytes": len(content),
        "description": f"Tikkie {soort} van {topup['user_naam']} — €{topup['amount_eur']:.2f}",
        "tags": ["tikkie", soort, topup["user_id"]],
        "uploaded_at": _now(),
        "uploaded_by": ADMIN_USER_ID,
        "path": str(dest),
        "auto_generated": True,
        "source": "tikkie_topup",
        "topup_id": topup["id"],
    }
    files_list.append(entry)
    save_json(index_file, {
        "user_id": ADMIN_USER_ID,
        "files": files_list,
        "updated_at": _now(),
    })


def _send_user_confirmation_pm(topup: dict) -> None:
    """Stuur privé-bericht naar user dat zijn Tikkie-bedrag is bevestigd."""
    user_id = topup["user_id"]
    pair = sorted([BOEKHOUDER_BOT_ID, user_id])
    fp = PRIVE_DIR / f"{pair[0]}__{pair[1]}.json"
    fp.parent.mkdir(parents=True, exist_ok=True)
    data = load_json(fp, default={"messages": []})
    ref = f"#{topup['id'][:8]}"
    free = topup.get("free_amount") or topup["amount_eur"]
    potje = topup.get("potje_amount") or 0
    lines = [
        f"✅ Je Tikkie-storting {ref} is bevestigd.",
        "",
        f"💶 Bedrag: €{topup['amount_eur']:.2f}",
    ]
    if potje > 0:
        lines.append(f"🍯 In potje: €{potje:.2f}")
    if free > 0:
        lines.append(f"💳 Vrij saldo: €{free:.2f}")
    note = topup.get("note")
    if note:
        lines.append("")
        lines.append(f"💬 {note}")
    msg = {
        "id": f"pm-{uuid.uuid4().hex[:8]}",
        "from_user_id": BOEKHOUDER_BOT_ID,
        "from_naam": "De Boekhouder 🎩",
        "to_user_id": user_id,
        "text": "\n".join(lines),
        "ts": _now(),
        "unread_by": [user_id],
        "system": True,
        "kind": "tikkie_confirmed",
        "topup_id": topup["id"],
        "topup_ref": ref,
        "is_bot": True,
    }
    data["messages"] = data.get("messages", []) + [msg]
    save_json(fp, data)


# ============== MODELS ==============
class CreateTopup(BaseModel):
    user_id: str
    naam_invoer: str
    amount_eur: float


class ConfirmTopup(BaseModel):
    viewer_id: str
    free_amount: Optional[float] = None
    potje_amount: Optional[float] = 0
    note: Optional[str] = None


class CancelTopup(BaseModel):
    viewer_id: str
    reason: Optional[str] = None


class TikkieConfig(BaseModel):
    viewer_id: str
    tikkie_url: str


# ============== ENDPOINTS ==============
@router.get("/qr")
async def get_qr():
    """Serve de Tikkie QR afbeelding."""
    if not QR_IMAGE.exists():
        raise HTTPException(404, "QR afbeelding niet gevonden")
    return FileResponse(QR_IMAGE, media_type="image/jpeg")


@router.get("/config")
async def get_config():
    data = load_json(TIKKIE_FILE, default={"config": {}, "topups": []})
    cfg = data.get("config", {})
    return {
        "tikkie_url": cfg.get("tikkie_url", ""),
        "qr_available": QR_IMAGE.exists(),
    }


@router.put("/config")
async def update_config(req: TikkieConfig):
    if not _is_admin(req.viewer_id):
        raise HTTPException(403, "Alleen admins mogen de Tikkie-config wijzigen")
    data = load_json(TIKKIE_FILE, default={"config": {}, "topups": []})
    data["config"] = {"tikkie_url": req.tikkie_url.strip()}
    save_json(TIKKIE_FILE, data)
    return {"success": True, "config": data["config"]}


@router.post("/request")
async def create_topup(req: CreateTopup):
    """User dient een Tikkie-storting in. Bot-boekhouder stuurt PM naar admin."""
    if req.amount_eur <= 0:
        raise HTTPException(400, "Bedrag moet > 0 zijn")
    if not req.naam_invoer.strip():
        raise HTTPException(400, "Naam is verplicht")
    user = _get_user(req.user_id)
    if not user:
        raise HTTPException(404, "User niet gevonden")
    data = load_json(TIKKIE_FILE, default={"config": {}, "topups": []})
    topup = {
        "id": f"tk-{uuid.uuid4().hex[:10]}",
        "user_id": req.user_id,
        "user_naam": user.get("naam") or user.get("volledige_naam") or req.user_id,
        "naam_invoer": req.naam_invoer.strip(),
        "amount_eur": round(float(req.amount_eur), 2),
        "status": "pending",
        "created_at": _now(),
        "confirmed_at": None,
        "confirmed_by": None,
        "potje_amount": 0,
        "free_amount": 0,
        "note": None,
    }
    data.setdefault("topups", []).append(topup)
    save_json(TIKKIE_FILE, data)
    try:
        _send_admin_pm(topup)
    except Exception as e:
        # niet blokkerend — PM-fout mag aanvraag niet stoppen
        print(f"[tikkie] PM naar admin gefaald: {e}")
    return {"success": True, "topup": topup}


@router.get("/list")
async def list_topups(viewer_id: str, status: Optional[str] = None):
    """Admin-only: alle Tikkie-aanvragen."""
    if not _is_admin(viewer_id):
        raise HTTPException(403, "Alleen admins (gradatie ≤ 2)")
    data = load_json(TIKKIE_FILE, default={"config": {}, "topups": []})
    topups = data.get("topups", [])
    if status:
        topups = [t for t in topups if t.get("status") == status]
    topups = sorted(topups, key=lambda t: t.get("created_at", ""), reverse=True)
    counts = {"pending": 0, "confirmed": 0, "cancelled": 0}
    for t in data.get("topups", []):
        s = t.get("status", "pending")
        counts[s] = counts.get(s, 0) + 1
    return {"topups": topups, "counts": counts}


@router.get("/mine")
async def my_topups(user_id: str):
    """User ziet eigen Tikkie-aanvragen + statussen."""
    data = load_json(TIKKIE_FILE, default={"config": {}, "topups": []})
    mine = [t for t in data.get("topups", []) if t.get("user_id") == user_id]
    mine = sorted(mine, key=lambda t: t.get("created_at", ""), reverse=True)
    return {"topups": mine, "total": len(mine)}


@router.post("/{topup_id}/confirm")
async def confirm_topup(topup_id: str, req: ConfirmTopup):
    """Admin bevestigt Tikkie ontvangen → boekt bedrag bij in user-wallet."""
    if not _is_admin(req.viewer_id):
        raise HTTPException(403, "Alleen admins (gradatie ≤ 2)")
    data = load_json(TIKKIE_FILE, default={"config": {}, "topups": []})
    topup = None
    for t in data.get("topups", []):
        if t.get("id") == topup_id:
            topup = t
            break
    if not topup:
        raise HTTPException(404, "Tikkie-aanvraag niet gevonden")
    if topup.get("status") != "pending":
        raise HTTPException(400, f"Aanvraag heeft status '{topup.get('status')}' (niet pending)")

    amount = float(topup["amount_eur"])
    potje = round(float(req.potje_amount or 0), 2)
    free = req.free_amount
    if free is None:
        free = round(amount - potje, 2)
    else:
        free = round(float(free), 2)
    if round(potje + free, 2) != round(amount, 2):
        raise HTTPException(400, f"Verdeling klopt niet: €{potje:.2f} potje + €{free:.2f} vrij ≠ €{amount:.2f}")

    # Boek bij in wallet
    wallets = load_json(WALLETS_FILE, default={"wallets": {}, "transactions": []})
    user_id = topup["user_id"]
    if user_id not in wallets.get("wallets", {}):
        wallets.setdefault("wallets", {})[user_id] = {
            "wallet_id": user_id, "balance": 0, "total_deposited": 0,
            "total_withdrawn": 0, "total_donated": 0,
        }
    w = wallets["wallets"][user_id]
    w["balance"] = round(float(w.get("balance", 0)) + free, 2)
    w["total_deposited"] = round(float(w.get("total_deposited", 0)) + amount, 2)
    if potje > 0:
        w["potje_balance"] = round(float(w.get("potje_balance", 0)) + potje, 2)
    tx = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "type": "deposit",
        "amount": amount,
        "status": "completed",
        "message": f"Tikkie {topup['id'][:8]} — naam: {topup['naam_invoer']}",
        "created_at": _now(),
        "payment_info": {"method": "tikkie", "topup_id": topup["id"]},
        "split": {"free": free, "potje": potje},
    }
    wallets["transactions"].append(tx)
    save_json(WALLETS_FILE, wallets)

    # Update topup
    topup["status"] = "confirmed"
    topup["confirmed_at"] = _now()
    topup["confirmed_by"] = req.viewer_id
    topup["free_amount"] = free
    topup["potje_amount"] = potje
    topup["note"] = (req.note or "").strip() or None
    save_json(TIKKIE_FILE, data)

    try:
        _send_user_confirmation_pm(topup)
    except Exception as e:
        print(f"[tikkie] PM naar user gefaald: {e}")
    try:
        _archive_tikkie_doc(topup, "bevestigd")
    except Exception as e:
        print(f"[tikkie] archiveer bevestigd gefaald: {e}")

    # v10_tikkie_papertrail_001 — Bevestigde Tikkie → boekhouder log-agent
    # (topic="deposit"). Hash-chained paper trail voor centrale bank guard.
    try:
        from modules.boekhouder.agents.log_agent import LogAgent
        LogAgent().record(
            topic="deposit",
            event_type="tikkie_confirmed",
            actor=topup.get("user_id"),
            data={
                "topup_id": topup["id"],
                "amount_eur": float(topup.get("amount_eur") or 0),
                "free_eur": free,
                "potje_eur": potje,
                "confirmed_by": req.viewer_id,
                "source": "Tikkie",
                "note": topup.get("note"),
            }
        )
    except Exception as e:
        print(f"[tikkie] papertrail log failed (non-blocking): {e}")

    # v6_accounting_hooks_001 — Tikkie storting → income personal_<user>
    try:
        from modules.accounting.hooks import on_deposit
        on_deposit(
            user_id=topup.get("user_id"),
            user_naam=topup.get("naam_invoer") or topup.get("user_id"),
            amount=float(topup.get("amount") or 0),
            source="Tikkie",
            ref_id=topup["id"],
        )
    except Exception as e:
        print(f"[tikkie] accounting-hook failed (non-blocking): {e}")

    return {"success": True, "topup": topup, "wallet": w, "transaction": tx}


@router.post("/{topup_id}/cancel")
async def cancel_topup(topup_id: str, req: CancelTopup):
    """Admin annuleert een pending aanvraag (bv. duplicaat / niet ontvangen)."""
    if not _is_admin(req.viewer_id):
        raise HTTPException(403, "Alleen admins (gradatie ≤ 2)")
    data = load_json(TIKKIE_FILE, default={"config": {}, "topups": []})
    for t in data.get("topups", []):
        if t.get("id") == topup_id:
            if t.get("status") != "pending":
                raise HTTPException(400, f"Status is '{t.get('status')}'")
            t["status"] = "cancelled"
            t["confirmed_at"] = _now()
            t["confirmed_by"] = req.viewer_id
            t["note"] = (req.reason or "").strip() or None
            save_json(TIKKIE_FILE, data)
            return {"success": True, "topup": t}
    raise HTTPException(404, "Niet gevonden")
