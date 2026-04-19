"""
Accounting Routes - Kasboeken (4 entities) + transacties
Schema v1: {transactions: [{id, type, category, amount, description, date, btw_percentage, btw_amount, created_at}]}
Kasboeken: spark_core, spark_your_life, roadkill_merch, personal_willem
"""
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
from datetime import datetime, timezone
import uuid
from modules.core.storage import load_json, save_json

router = APIRouter(prefix="/accounting", tags=["accounting"])
DATA_DIR = Path(__file__).parent.parent.parent / "data" / "accounting"
ENTITIES_FILE = Path(__file__).parent.parent.parent / "data" / "wallet" / "entities.json"
TX_FILE = DATA_DIR / "transactions.json"

INCOME_CATEGORIES = ["Donations", "Sales", "Crypto Profit", "Consulting", "Freelance", "Refunds", "Overig"]
EXPENSE_CATEGORIES = ["Hosting", "Software", "Hardware", "Marketing", "Verzekering", "Materiaal", "Verzending", "BTW", "Overig"]


class TransactionCreate(BaseModel):
    type: str  # income, expense
    category: str
    amount: float
    description: str
    entity_id: Optional[str] = "spark_core"
    date: Optional[str] = None
    btw_percentage: Optional[float] = 21.0


@router.get("/transactions")
async def get_transactions(
    entity_id: Optional[str] = None,
    type: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
):
    data = load_json(TX_FILE, default={"transactions": []})
    txs = data.get("transactions", [])
    if entity_id:
        txs = [t for t in txs if t.get("entity_id", "spark_core") == entity_id]
    if type:
        txs = [t for t in txs if t.get("type") == type]
    txs.sort(key=lambda t: t.get("date", ""), reverse=True)
    return {"transactions": txs[:limit], "total": len(txs)}


@router.post("/transactions")
async def create_transaction(tx: TransactionCreate):
    data = load_json(TX_FILE, default={"transactions": []})
    btw_amount = round(tx.amount * (tx.btw_percentage / 100), 2) if tx.btw_percentage else 0
    new_tx = {
        "id": str(uuid.uuid4()),
        "type": tx.type,
        "category": tx.category,
        "amount": tx.amount,
        "description": tx.description,
        "entity_id": tx.entity_id or "spark_core",
        "date": tx.date or datetime.now(timezone.utc).isoformat(),
        "btw_percentage": tx.btw_percentage,
        "btw_amount": btw_amount,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    data["transactions"].append(new_tx)
    save_json(TX_FILE, data)
    return {"success": True, "transaction": new_tx}


@router.delete("/transactions/{tx_id}")
async def delete_transaction(tx_id: str):
    data = load_json(TX_FILE, default={"transactions": []})
    before = len(data["transactions"])
    data["transactions"] = [t for t in data["transactions"] if t.get("id") != tx_id]
    if len(data["transactions"]) < before:
        save_json(TX_FILE, data)
        return {"success": True}
    return {"success": False, "message": "Transactie niet gevonden"}


@router.get("/summary")
async def get_summary(entity_id: Optional[str] = None):
    data = load_json(TX_FILE, default={"transactions": []})
    entities = load_json(ENTITIES_FILE, default={"entities": {}}).get("entities", {})
    txs = data.get("transactions", [])
    if entity_id:
        txs = [t for t in txs if t.get("entity_id", "spark_core") == entity_id]

    income = sum(t["amount"] for t in txs if t["type"] == "income")
    expenses = sum(t["amount"] for t in txs if t["type"] == "expense")
    btw = sum(t.get("btw_amount", 0) for t in txs)

    # Per entity breakdown
    per_entity = {}
    for eid, ent in entities.items():
        etxs = [t for t in data.get("transactions", []) if t.get("entity_id", "spark_core") == eid]
        eincome = sum(t["amount"] for t in etxs if t["type"] == "income")
        eexpenses = sum(t["amount"] for t in etxs if t["type"] == "expense")
        per_entity[eid] = {
            "name": ent.get("name", eid),
            "income": round(eincome, 2),
            "expenses": round(eexpenses, 2),
            "profit": round(eincome - eexpenses, 2),
            "tx_count": len(etxs),
        }

    return {
        "income": round(income, 2),
        "expenses": round(expenses, 2),
        "profit": round(income - expenses, 2),
        "btw_total": round(btw, 2),
        "transaction_count": len(txs),
        "per_entity": per_entity,
    }


@router.get("/categories")
async def get_categories():
    return {"income": INCOME_CATEGORIES, "expense": EXPENSE_CATEGORIES}


@router.get("/kasboeken")
async def get_kasboeken():
    entities = load_json(ENTITIES_FILE, default={"entities": {}}).get("entities", {})
    data = load_json(TX_FILE, default={"transactions": []})
    kasboeken = []
    for eid, ent in entities.items():
        etxs = [t for t in data.get("transactions", []) if t.get("entity_id", "spark_core") == eid]
        income = sum(t["amount"] for t in etxs if t["type"] == "income")
        expenses = sum(t["amount"] for t in etxs if t["type"] == "expense")
        # Wallet/bank info
        wallets = ent.get("wallets", {})
        bank_info = None
        for wkey, wval in wallets.items():
            if isinstance(wval, dict) and wval.get("iban"):
                bank_info = {"iban": wval["iban"], "provider": wval.get("provider", "")}
                break
            if isinstance(wval, dict) and wval.get("provider") == "bitvavo":
                bank_info = {"provider": "Bitvavo", "balance": wval.get("balance_eur", 0)}
                break
        kasboeken.append({
            "id": eid,
            "name": ent.get("name", eid),
            "description": ent.get("description", ""),
            "type": ent.get("type", "system"),
            "color": ent.get("color", "blue"),
            "income": round(income, 2),
            "expenses": round(expenses, 2),
            "saldo": round(income - expenses, 2),
            "tx_count": len(etxs),
            "bank_info": bank_info,
        })
    return {"kasboeken": kasboeken}
