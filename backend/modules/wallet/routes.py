"""
Wallet Routes - User wallets, entities, transactions
Schema v1:
  user_wallets.json: {user_wallets: {user-001: {wallet: {spark_tokens, credits, balance_eur, ...}}}}
  entities.json: {entities: {spark_core, spark_your_life, roadkill_merch, personal_willem}}
  wallets.json: {wallets: {user-001: {balance, total_deposited, total_withdrawn}}, transactions: [...]}
"""
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
from datetime import datetime, timezone
import uuid
from modules.core.storage import load_json, save_json

router = APIRouter(prefix="/wallet", tags=["wallet"])
DATA_DIR = Path(__file__).parent.parent.parent / "data" / "wallet"
ROAR_FILE = Path(__file__).parent.parent.parent / "data" / "roar" / "roar_balances.json"
USERS_FILE = Path(__file__).parent.parent.parent / "data" / "system" / "users.json"


# ============================================================
# v4_wallet_per_user_001 — Ensure wallet per user (idempotent).
# Wallet-id = user-id (klaar voor latere bank-koppeling).
# ============================================================
def ensure_wallet(user_id: str) -> dict:
    """Maak wallet aan voor user als die nog niet bestaat. Idempotent.
    v11_unique_wallet_ids_001 — wallet_id = UUID (`wal-xxxxxxxx`), NIET user_id.
    Anti-fraude: user_id kan gepubliceerd zijn, wallet_id blijft privé/bank-koppeling.
    """
    from uuid import uuid4
    wallets = load_json(DATA_DIR / "wallets.json", default={"wallets": {}, "transactions": []})
    if user_id not in wallets.get("wallets", {}):
        wallets.setdefault("wallets", {})[user_id] = {
            "wallet_id": f"wal-{uuid4().hex[:8]}",
            "balance": 0.0,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "total_deposited": 0,
            "total_withdrawn": 0,
            "total_donated": 0,
            "iban": None,  # voor latere bank-koppeling
        }
        save_json(DATA_DIR / "wallets.json", wallets)
    return wallets["wallets"][user_id]


@router.post("/ensure/{user_id}")
async def ensure_wallet_endpoint(user_id: str):
    """Maak wallet als die er nog niet is. Wordt aangeroepen bij login."""
    w = ensure_wallet(user_id)
    return {"success": True, "wallet": w}


@router.post("/backfill-all")
async def backfill_all_wallets():
    """Eenmalige backfill: maak wallets voor alle bestaande users zonder wallet."""
    users_data = load_json(USERS_FILE, default={})
    users_list = users_data.get("users", []) if isinstance(users_data, dict) else []
    created = []
    for u in users_list:
        uid = u.get("id") or u.get("user_id")
        if not uid:
            continue
        wallets = load_json(DATA_DIR / "wallets.json", default={"wallets": {}, "transactions": []})
        if uid not in wallets.get("wallets", {}):
            ensure_wallet(uid)
            created.append(uid)
    return {"success": True, "created": created, "total_now": len(load_json(DATA_DIR / "wallets.json").get("wallets", {}))}


# ============================================================
# v4_token_admin_001 — Admin: token grant + revoke per user
# ============================================================
class TokenAdminRequest(BaseModel):
    amount: int = 1
    reason: Optional[str] = None


@router.post("/admin/token/grant/{user_id}")
async def admin_grant_token(user_id: str, req: TokenAdminRequest):
    """Admin geeft N tokens aan user vanuit treasury_pool (NIET Spark's balance).

    v11_treasury_pool_fix_001 — Was: haalde uit balances[user-000] (Spark's persoonlijke
    tokens). Fout: verwarring tussen treasury en Spark-balance. Nu: correct uit
    treasury_pool → 1M supply consistent (treasury + som(balances) = 1.000.000).
    """
    n = max(1, int(req.amount))
    roar = load_json(ROAR_FILE, default={"balances": {}, "treasury_pool": 999973, "total_supply": 1000000})
    treasury = int(roar.get("treasury_pool", 0))
    if treasury < n:
        return {"success": False, "error": f"Treasury heeft maar {treasury} tokens, je vroeg {n}"}
    # 51%-garantie: treasury moet ≥510k blijven (governance)
    if treasury - n < 510000:
        return {"success": False, "error": "Mag niet onder 51% governance-garantie (510.000 tokens)"}
    roar["treasury_pool"] = treasury - n
    roar["balances"][user_id] = int(roar.get("balances", {}).get(user_id, 0)) + n
    now = datetime.now(timezone.utc).isoformat()
    roar.setdefault("transactions", []).append({
        "type": "admin_grant", "user_id": user_id, "n_tokens": n,
        "source": "wallet_admin_grant_button", "reason": req.reason,
        "timestamp": now,
    })
    roar.setdefault("admin_log", []).append({
        "ts": now, "action": "grant", "user_id": user_id, "amount": n, "reason": req.reason,
    })
    save_json(ROAR_FILE, roar)
    # Sync user_wallets mirror
    try:
        uw_fp = DATA_DIR / "user_wallets.json"
        uw = load_json(uw_fp, default={"user_wallets": {}})
        entry = uw.setdefault("user_wallets", {}).setdefault(user_id, {})
        entry["spark_tokens"] = roar["balances"][user_id]  # top-level master
        entry.setdefault("wallet", {})["spark_tokens"] = roar["balances"][user_id]  # nested mirror
        save_json(uw_fp, uw)
    except Exception:
        pass
    # Sync potjes-slot (1 token = 1 pot)
    try:
        from modules.trade.potjes import sync_potjes_to_tokens
        sync_potjes_to_tokens(user_id, roar["balances"][user_id])
    except Exception:
        pass
    return {"success": True, "user_id": user_id,
            "new_balance": roar["balances"][user_id],
            "treasury_left": roar["treasury_pool"]}


@router.post("/admin/token/revoke/{user_id}")
async def admin_revoke_token(user_id: str, req: TokenAdminRequest):
    """Admin neemt N tokens terug van user → treasury_pool (v11_treasury_pool_fix_001)."""
    n = max(1, int(req.amount))
    roar = load_json(ROAR_FILE, default={"balances": {}, "treasury_pool": 999973, "total_supply": 1000000})
    user_bal = int(roar.get("balances", {}).get(user_id, 0))
    if user_bal < n:
        return {"success": False, "error": f"User heeft maar {user_bal} tokens"}
    roar["balances"][user_id] = user_bal - n
    roar["treasury_pool"] = int(roar.get("treasury_pool", 0)) + n
    now = datetime.now(timezone.utc).isoformat()
    roar.setdefault("transactions", []).append({
        "type": "admin_revoke", "user_id": user_id, "n_tokens": n,
        "source": "wallet_admin_revoke_button", "reason": req.reason,
        "timestamp": now,
    })
    roar.setdefault("admin_log", []).append({
        "ts": now, "action": "revoke", "user_id": user_id, "amount": n, "reason": req.reason,
    })
    save_json(ROAR_FILE, roar)
    # Sync mirror + potjes
    try:
        uw_fp = DATA_DIR / "user_wallets.json"
        uw = load_json(uw_fp, default={"user_wallets": {}})
        entry = uw.setdefault("user_wallets", {}).setdefault(user_id, {})
        entry["spark_tokens"] = roar["balances"][user_id]  # top-level master
        entry.setdefault("wallet", {})["spark_tokens"] = roar["balances"][user_id]  # nested mirror
        save_json(uw_fp, uw)
    except Exception:
        pass
    try:
        from modules.trade.potjes import sync_potjes_to_tokens
        sync_potjes_to_tokens(user_id, roar["balances"][user_id])
    except Exception:
        pass
    return {"success": True, "user_id": user_id, "new_balance": roar["balances"][user_id],
            "treasury_left": roar["treasury_pool"]}


@router.get("/admin/overview")
async def admin_wallet_overview():
    """Per-user overzicht: wallet €, tokens, gradatie. Voor admin UI."""
    users_data = load_json(USERS_FILE, default={})
    users_list = users_data.get("users", []) if isinstance(users_data, dict) else []
    wallets = load_json(DATA_DIR / "wallets.json", default={"wallets": {}})
    roar = load_json(ROAR_FILE, default={"balances": {}})
    rows = []
    for u in users_list:
        uid = u.get("id") or u.get("user_id")
        if not uid:
            continue
        w = wallets.get("wallets", {}).get(uid, {})
        rows.append({
            "user_id": uid,
            "naam": u.get("voornaam") or u.get("naam") or u.get("volledige_naam") or uid,
            "gradatie": u.get("gradatie", 7),
            "wallet_id": w.get("wallet_id"),
            "balance_eur": round(float(w.get("balance", 0) or 0), 2),
            "iban": w.get("iban"),
            "tokens": int(roar.get("balances", {}).get(uid, 0)),
        })
    rows.sort(key=lambda r: (r["gradatie"], r["naam"].lower()))
    return {"success": True, "rows": rows}


class DepositRequest(BaseModel):
    amount: float
    message: Optional[str] = None


class WithdrawRequest(BaseModel):
    amount: float
    message: Optional[str] = None


@router.get("/user/{user_id}")
async def get_user_wallet(user_id: str):
    user_wallets = load_json(DATA_DIR / "user_wallets.json", default={"user_wallets": {}})
    wallets = load_json(DATA_DIR / "wallets.json", default={"wallets": {}, "transactions": []})
    uw = user_wallets.get("user_wallets", {}).get(user_id, {})
    w = wallets.get("wallets", {}).get(user_id, {})

    # v10_finance_hub_wallet_sync — hybride Willem-regel: 1 pot = 1 token.
    # De ROAR-count in wallet = potjes-count (via finance_hub, fallback naar user-000).
    # De stale user_wallets.spark_tokens is legacy en wordt genegeerd voor display.
    spark_tokens_stored = uw.get("wallet", {}).get("spark_tokens", 0)
    hybrid_token_count = spark_tokens_stored
    try:
        from modules.boekhouder.finance_hub import get_hub
        potjes_snap = get_hub().get_potjes(user_id)
        potjes_count = potjes_snap.get("potjes_count", 0) or 0
        # Willem-regel: token-count = potjes-count. Volgt hybride direct.
        hybrid_token_count = potjes_count
    except Exception as ex:
        print(f"[wallet] finance_hub overlay failed: {ex}")

    return {
        "user_id": user_id,
        # v11_wallet_fields_001 — wallet_id + created_at nodig voor Spark Card UI
        "wallet_id": w.get("wallet_id", user_id),
        "created_at": w.get("created_at"),
        "geblokkeerd": bool(uw.get("geblokkeerd", False)),
        "name": uw.get("name", "Onbekend"),
        "spark_tokens": hybrid_token_count,
        "spark_tokens_stored": spark_tokens_stored,
        "spark_tokens_from_potjes": hybrid_token_count,
        "credits": uw.get("wallet", {}).get("credits", 0),
        "balance_eur": w.get("balance", uw.get("wallet", {}).get("balance_eur", 0)),
        # v10_earned_fix_001 — "earned_total" moet echt earned zijn (trade P&L),
        # NIET total_deposited. Legacy-bug hield deze twee bij elkaar geveegd.
        "earned_total": float(uw.get("wallet", {}).get("earned_total", 0) or 0),
        "total_deposited": float(w.get("total_deposited", 0) or 0),
        "activity_score": uw.get("wallet", {}).get("activity_score", 0),
        "total_withdrawn": w.get("total_withdrawn", 0),
        "total_donated": w.get("total_donated", 0),
    }


@router.get("/transactions/{user_id}")
async def get_transactions(user_id: str, limit: int = Query(50, ge=1, le=200)):
    wallets = load_json(DATA_DIR / "wallets.json", default={"transactions": []})
    txs = [t for t in wallets.get("transactions", []) if t.get("user_id") == user_id]
    txs.sort(key=lambda t: t.get("created_at", ""), reverse=True)
    return {"transactions": txs[:limit], "total": len(txs)}


@router.post("/deposit/{user_id}")
async def create_deposit(user_id: str, req: DepositRequest):
    wallets = load_json(DATA_DIR / "wallets.json", default={"wallets": {}, "transactions": []})
    tx = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "type": "deposit",
        "amount": req.amount,
        "status": "pending",
        "message": req.message,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "payment_info": {
            "method": "bank_transfer",
            "iban": "NL12 ABCD 1234 5678 90",
            "reference": f"SPARK-{user_id.upper()}-{datetime.now(timezone.utc).strftime('%Y%m%d')}",
        },
    }
    wallets["transactions"].append(tx)
    save_json(DATA_DIR / "wallets.json", wallets)
    return {"success": True, "transaction": tx}


@router.post("/withdraw/{user_id}")
async def create_withdrawal(user_id: str, req: WithdrawRequest):
    wallets = load_json(DATA_DIR / "wallets.json", default={"wallets": {}, "transactions": []})
    user_w = wallets.get("wallets", {}).get(user_id, {"balance": 0})
    if req.amount > user_w.get("balance", 0):
        return {"success": False, "error": "Onvoldoende saldo"}
    tx = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "type": "withdrawal",
        "amount": req.amount,
        "status": "completed",
        "message": req.message or "Opname",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    wallets["transactions"].append(tx)
    if user_id not in wallets["wallets"]:
        wallets["wallets"][user_id] = {"balance": 0, "total_deposited": 0, "total_withdrawn": 0, "total_donated": 0}
    wallets["wallets"][user_id]["balance"] = round(user_w.get("balance", 0) - req.amount, 2)
    wallets["wallets"][user_id]["total_withdrawn"] = round(user_w.get("total_withdrawn", 0) + req.amount, 2)
    # Also reduce spark tokens proportionally
    user_wallets = load_json(DATA_DIR / "user_wallets.json", default={"user_wallets": {}})
    uw = user_wallets.get("user_wallets", {}).get(user_id, {})
    if uw.get("wallet"):
        token_reduction = int(req.amount * 10)
        uw["wallet"]["spark_tokens"] = max(0, uw["wallet"].get("spark_tokens", 0) - token_reduction)
        user_wallets["user_wallets"][user_id] = uw
        save_json(DATA_DIR / "user_wallets.json", user_wallets)
    save_json(DATA_DIR / "wallets.json", wallets)
    return {"success": True, "transaction": tx, "new_balance": wallets["wallets"][user_id]["balance"]}


@router.get("/entities")
async def get_entities():
    data = load_json(DATA_DIR / "entities.json", default={"entities": {}})
    return {"entities": data.get("entities", {})}


@router.get("/entities/{entity_id}")
async def get_entity(entity_id: str):
    data = load_json(DATA_DIR / "entities.json", default={"entities": {}})
    entity = data.get("entities", {}).get(entity_id)
    if entity:
        return {"success": True, "entity": entity}
    return {"success": False, "error": "Entity niet gevonden"}


@router.get("/overview")
async def get_overview(user_id: str = Query("user-001")):
    entities = load_json(DATA_DIR / "entities.json", default={"entities": {}}).get("entities", {})
    user_wallets = load_json(DATA_DIR / "user_wallets.json", default={"user_wallets": {}})
    wallets = load_json(DATA_DIR / "wallets.json", default={"wallets": {}, "transactions": []})
    uw = user_wallets.get("user_wallets", {}).get(user_id, {})
    w = wallets.get("wallets", {}).get(user_id, {})

    # v11_week_boekhoud_link_001 — Bereken week-in/out uit boekhoud-log (audit_log.json).
    # In = deposits + sell-opbrengsten; Out = withdrawals + gifts uitgaand.
    week_in_eur = 0.0
    week_out_eur = 0.0
    week_in_count = 0
    week_out_count = 0
    try:
        from datetime import datetime, timezone, timedelta
        audit_fp = Path(__file__).parent.parent.parent / "data" / "system" / "audit_log.json"
        audit = load_json(audit_fp, default={"entries": []})
        cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        for e in audit.get("entries", []):
            if e.get("user_id") != user_id:
                continue
            if e.get("ts", "") < cutoff:
                continue
            amt = e.get("amount_eur")
            if amt is None:
                continue
            typ = e.get("type", "")
            if typ in ("deposit", "trade_sell", "gift_received", "topup"):
                week_in_eur += float(amt) if amt > 0 else 0
                week_in_count += 1
            elif typ in ("withdraw", "trade_buy", "gift_sent", "purchase"):
                week_out_eur += abs(float(amt))
                week_out_count += 1
    except Exception:
        pass

    return {
        "entities": entities,
        "user_wallet": {
            # v11_toplevel_master_001 — top-level spark_tokens is master
            # (mint/grant/revoke muteren die), nested wallet.spark_tokens = mirror.
            "spark_tokens": uw.get("spark_tokens", uw.get("wallet", {}).get("spark_tokens", 0)),
            "credits": uw.get("wallet", {}).get("credits", 0),
            "balance_eur": w.get("balance", 0),
            "wallet_id": w.get("wallet_id"),
            "created_at": w.get("created_at"),
            "week_in_eur": round(week_in_eur, 2),
            "week_out_eur": round(week_out_eur, 2),
            "week_in_count": week_in_count,
            "week_out_count": week_out_count,
        },
        "system_wallet": user_wallets.get("user_wallets", {}).get("spark_system", {}),
    }



@router.get("/papertrail-overview")
async def papertrail_overview():
    """v11_papertrail_widget_001 — Compleet overzicht: treasury + alle holders +
    laatste 15 papertrail-transacties. Bewijs dat 1M pool klopt."""
    roar = load_json(ROAR_FILE, default={})
    users = load_json(USERS_FILE, default={"users": []}).get("users", [])
    wallets = load_json(DATA_DIR / "wallets.json", default={"wallets": {}}).get("wallets", {})

    treasury = int(roar.get("treasury_pool", 0))
    balances = roar.get("balances", {})
    circulating = sum(int(v) for v in balances.values())
    total_supply = int(roar.get("total_supply", 1000000))

    # Current price (voor value-per-holder)
    current_price = 0.0
    try:
        from modules.shop.routes import get_dynamic_price
        current_price = get_dynamic_price() or 0.0
    except Exception:
        pass

    # Bouw holders-lijst
    holders = []
    users_by_id = {u.get("id"): u for u in users}
    for uid, amount in balances.items():
        if int(amount) <= 0:
            continue
        u = users_by_id.get(uid) or {}
        w = wallets.get(uid) or {}
        holders.append({
            "user_id": uid,
            "naam": u.get("naam") or u.get("volledige_naam") or uid,
            "wallet_id": w.get("wallet_id") or uid,
            "tokens": int(amount),
        })
    holders.sort(key=lambda h: -h["tokens"])

    # Recent transacties (laatste 15) — v11_papertrail_names_001 (31 jul):
    # Verrijk elke tx met 'user_naam' zodat de widget "→ Spark" kan tonen ipv "user-000".
    txs = roar.get("transactions", [])
    if not isinstance(txs, list):
        txs = []
    recent = []
    for t in list(reversed(txs))[:15]:
        t2 = dict(t)
        uid = t.get("user_id") or t.get("to_user") or t.get("actor")
        from_uid = t.get("from_user")
        to_uid = t.get("to_user")
        if uid:
            u = users_by_id.get(uid) or {}
            t2["user_naam"] = u.get("naam") or u.get("volledige_naam") or uid
        if from_uid:
            u = users_by_id.get(from_uid) or {}
            t2["from_naam"] = u.get("naam") or from_uid
        if to_uid:
            u = users_by_id.get(to_uid) or {}
            t2["to_naam"] = u.get("naam") or to_uid
        recent.append(t2)

    return {
        "success": True,
        "total_supply": total_supply,
        "treasury_pool": treasury,
        "circulating": circulating,
        "current_price": round(current_price, 4),
        "supply_check_ok": (treasury + circulating) == total_supply,
        "holders": holders,
        "transactions": recent,
    }
