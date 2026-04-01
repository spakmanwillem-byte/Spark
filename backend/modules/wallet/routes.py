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


class DepositRequest(BaseModel):
    amount: float
    message: Optional[str] = None


@router.get("/user/{user_id}")
async def get_user_wallet(user_id: str):
    user_wallets = load_json(DATA_DIR / "user_wallets.json", default={"user_wallets": {}})
    wallets = load_json(DATA_DIR / "wallets.json", default={"wallets": {}, "transactions": []})
    uw = user_wallets.get("user_wallets", {}).get(user_id, {})
    w = wallets.get("wallets", {}).get(user_id, {})
    return {
        "user_id": user_id,
        "name": uw.get("name", "Onbekend"),
        "spark_tokens": uw.get("wallet", {}).get("spark_tokens", 0),
        "credits": uw.get("wallet", {}).get("credits", 0),
        "balance_eur": w.get("balance", uw.get("wallet", {}).get("balance_eur", 0)),
        "earned_total": w.get("total_deposited", uw.get("wallet", {}).get("earned_total", 0)),
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
    return {
        "entities": entities,
        "user_wallet": {
            "spark_tokens": uw.get("wallet", {}).get("spark_tokens", 0),
            "credits": uw.get("wallet", {}).get("credits", 0),
            "balance_eur": w.get("balance", 0),
        },
        "system_wallet": user_wallets.get("user_wallets", {}).get("spark_system", {}),
    }
