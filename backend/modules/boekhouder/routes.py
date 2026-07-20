"""v5_closing_flow_001 — Boekhouder closing-flow routes.

POST /api/boekhouder/close-cycle/{user_id}  — rollup + DM + audit
GET  /api/boekhouder/closings               — lijst (admin/user)
"""
from fastapi import APIRouter, HTTPException, Body
from typing import Optional
from . import service as boekhouder

router = APIRouter(prefix="/boekhouder", tags=["boekhouder"])


def _is_admin(user_id: str) -> bool:
    """Lazy admin check zonder cross-module gradatie-call (Willem of Spark)."""
    from pathlib import Path
    from modules.core.storage import load_json
    p = Path(__file__).parent.parent.parent / "data" / "system" / "users.json"
    data = load_json(p, default={"users": []})
    for u in data.get("users", []):
        if u.get("id") == user_id and (u.get("gradatie") or 7) <= 2:
            return True
    return False


@router.post("/close-cycle/{user_id}")
async def close_cycle(user_id: str, payload: Optional[dict] = Body(None)):
    """Sluit een trade-cyclus af voor user_id (terlens-terug-boek).

    Body (optioneel): {"viewer_id": "user-001", "note": "...optionele toelichting..."}
    Alleen admin (gradatie ≤ 2) mag closings triggeren.
    """
    viewer_id = (payload or {}).get("viewer_id")
    if not viewer_id or not _is_admin(viewer_id):
        raise HTTPException(status_code=403, detail="Alleen admin kan boekhouder afsluiten")
    note = (payload or {}).get("note", "")
    rollup = boekhouder.close_cycle(user_id, note=note)
    return {"success": True, "rollup": rollup}


@router.get("/closings")
async def list_closings(user_id: Optional[str] = None, limit: int = 20):
    return boekhouder.list_closings(user_id=user_id, limit=limit)



# ============================================================
# v10_finance_hub_001 — Finance Hub endpoints (single source of truth)
# ============================================================
from .finance_hub import get_hub


@router.get("/snapshot/{user_id}")
async def finance_snapshot(user_id: str):
    """Volledig financieel beeld — ÉÉN CALL: token, wallet, potjes, prijs, bitvavo, drift, sepa.

    Deze endpoint is de bron van waarheid voor alle UI's die financiële data tonen.
    """
    return {"success": True, **get_hub().get_snapshot(user_id)}


@router.get("/token/price")
async def finance_token_price():
    """Dynamische token-prijs — fresh berekend uit blueprint-formule."""
    return {"success": True, **get_hub().get_price()}


@router.get("/potjes/{user_id}")
async def finance_potjes(user_id: str):
    """Potjes met dynamische capital (hybride: capital = current token_price)."""
    return {"success": True, **get_hub().get_potjes(user_id)}


@router.get("/reconcile")
async def finance_reconcile(user_id: str = "user-001"):
    """Drift-detectie + ruis-berekening (systeem-breed)."""
    return {"success": True, **get_hub().reconcile(user_id)}


@router.get("/blueprint")
async def finance_blueprint():
    """Lees de volledige finance-hub blueprint (formules, hooks, chat_intents)."""
    return {"success": True, "blueprint": get_hub().token.full_blueprint()}


@router.get("/chat-snapshot/{user_id}")
async def finance_chat_snapshot(user_id: str):
    """Formatteert snapshot als NL chat-antwoord voor Spark's persona."""
    hub = get_hub()
    snap = hub.get_snapshot(user_id)
    # Lees user_naam
    from pathlib import Path
    from modules.core.storage import load_json
    users = load_json(Path(__file__).parent.parent.parent / "data" / "system" / "users.json",
                      default={"users": []})
    user_naam = "user"
    for u in users.get("users", []):
        if u.get("id") == user_id:
            user_naam = u.get("naam") or u.get("volledige_naam") or user_id
            break
    return {
        "success": True,
        "chat_message": hub.persona.format_snapshot_for_chat(snap, user_naam),
        "raw_snapshot": snap,
    }


# ============================================================
# v10_finance_hub_ops_001 — Muterende endpoints (sync, mint)
# ============================================================
from pydantic import BaseModel
from . import finance_ops


class SyncBody(BaseModel):
    dry_run: bool = True
    viewer_id: str = "user-001"


class MintBody(BaseModel):
    user_id: str
    n_tokens: int
    source: str = "manual"
    dry_run: bool = True
    viewer_id: str = "user-001"


@router.post("/admin/sync-wallet-mirror")
async def sync_wallet_mirror_endpoint(body: SyncBody):
    """Fix drift: sync user_wallets.spark_tokens ← roar_balances.balances."""
    if not _is_admin(body.viewer_id):
        raise HTTPException(status_code=403, detail="Alleen admin")
    return finance_ops.sync_wallet_mirror(dry_run=body.dry_run)


@router.post("/admin/mint")
async def mint_endpoint(body: MintBody):
    """Mint N tokens. 1 token = 1 pot (hybride Willem-regel).

    Bij dry_run=true: alleen preview. Bij dry_run=false: schrijft naar roar_balances,
    user_wallets en user_potjes files.
    """
    if not _is_admin(body.viewer_id):
        raise HTTPException(status_code=403, detail="Alleen admin")
    return finance_ops.mint_tokens(body.user_id, body.n_tokens, body.source, body.dry_run)


@router.post("/admin/check-auto-mint")
async def check_auto_mint_endpoint(body: SyncBody):
    """Trigger auto-mint hook: als Spark's overflow_pool ≥ MINT_THRESHOLD → mint."""
    if not _is_admin(body.viewer_id):
        raise HTTPException(status_code=403, detail="Alleen admin")
    return finance_ops.check_auto_mint_hook("user-000")
