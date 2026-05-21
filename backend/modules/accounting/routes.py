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
async def get_kasboeken(user_id: str = None):
    entities = load_json(ENTITIES_FILE, default={"entities": {}}).get("entities", {})
    data = load_json(TX_FILE, default={"transactions": []})
    kasboeken = []
    for eid, ent in entities.items():
        etxs = [t for t in data.get("transactions", []) if t.get("entity_id", "spark_core") == eid]
        # Persoonlijk kasboek: filter op user_id
        if eid == "personal_willem" and user_id:
            etxs = [t for t in etxs if t.get("user_id") == user_id]
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
        # Spark Core: saldo komt LIVE van Bitvavo
        if eid == "spark_core":
            try:
                from modules.shop.routes import get_bitvavo_balance_cached
                live = get_bitvavo_balance_cached()
                if live is not None:
                    saldo_override = live
                    if bank_info:
                        bank_info["balance"] = live
                else:
                    saldo_override = None
            except Exception:
                saldo_override = None
        else:
            saldo_override = None
        # Persoonlijk kasboek: haal IBAN uit user profiel
        if eid == "personal_willem" and user_id and not bank_info:
            profile_file = Path(__file__).parent.parent.parent / "data" / "users" / user_id / "profile.json"
            profile = load_json(profile_file, default={})
            if profile.get("iban"):
                bank_info = {"iban": profile["iban"], "provider": profile.get("bank_provider", "")}
        kasboeken.append({
            "id": eid,
            "name": ent.get("name", eid),
            "description": ent.get("description", ""),
            "type": ent.get("type", "system"),
            "color": ent.get("color", "blue"),
            "income": round(income, 2),
            "expenses": round(expenses, 2),
            "saldo": round(saldo_override if saldo_override is not None else (income - expenses), 2),
            "tx_count": len(etxs),
            "bank_info": bank_info,
            "live": saldo_override is not None,
        })
    return {"kasboeken": kasboeken}



# ============================================================
# v4_boekhouding_001 — Admin endpoints voor entiteit-IBAN & BTW
# ============================================================

class EntityUpdate(BaseModel):
    iban: Optional[str] = None
    bank_naam: Optional[str] = None
    btw_nummer: Optional[str] = None
    kvk_nummer: Optional[str] = None


@router.get("/entities")
async def list_entities():
    """Alle entiteiten met bank/btw/kvk velden."""
    d = load_json(ENTITIES_FILE, default={"entities": {}})
    return {"entities": d.get("entities", {}), "btw_tarieven": d.get("btw_tarieven", {}), "dagboeken": d.get("dagboeken", {})}


@router.patch("/entities/{entity_id}")
async def update_entity(entity_id: str, upd: EntityUpdate):
    """Admin update IBAN/BTW/KvK voor een entiteit."""
    d = load_json(ENTITIES_FILE, default={"entities": {}})
    ents = d.get("entities", {})
    if entity_id not in ents:
        return {"success": False, "error": f"Entiteit {entity_id} bestaat niet"}
    ent = ents[entity_id]
    ent.setdefault("bank", {})
    if upd.iban is not None:
        ent["bank"]["iban"] = upd.iban.strip() or None
    if upd.bank_naam is not None:
        ent["bank"]["naam"] = upd.bank_naam.strip()
    if upd.btw_nummer is not None:
        ent["btw_nummer"] = upd.btw_nummer.strip() or None
    if upd.kvk_nummer is not None:
        ent["kvk_nummer"] = upd.kvk_nummer.strip() or None
    ent["updated_at"] = datetime.now(timezone.utc).isoformat()
    save_json(ENTITIES_FILE, d)
    return {"success": True, "entity": ent}


@router.get("/btw-summary")
async def btw_summary(entity_id: str, year: Optional[int] = None):
    """BTW-overzicht per entiteit per tarief (21/9/0). Voor aangifte."""
    txs = load_json(TX_FILE, default={"transactions": []}).get("transactions", [])
    filtered = [t for t in txs if t.get("entity_id") == entity_id]
    if year:
        filtered = [t for t in filtered if t.get("date", "").startswith(str(year))]
    buckets = {21: {"income": 0.0, "expense": 0.0, "btw": 0.0},
               9: {"income": 0.0, "expense": 0.0, "btw": 0.0},
               0: {"income": 0.0, "expense": 0.0, "btw": 0.0}}
    for t in filtered:
        pct = int(t.get("btw_percentage", 21) or 0)
        if pct not in buckets:
            buckets[pct] = {"income": 0.0, "expense": 0.0, "btw": 0.0}
        amt = float(t.get("amount", 0) or 0)
        btw_amt = float(t.get("btw_amount", 0) or 0)
        bucket = buckets[pct]
        if t.get("type") == "income":
            bucket["income"] += amt
            bucket["btw"] += btw_amt
        else:
            bucket["expense"] += amt
            bucket["btw"] -= btw_amt
    return {
        "entity_id": entity_id,
        "year": year,
        "per_tarief": {str(k): {"income": round(v["income"], 2), "expense": round(v["expense"], 2), "btw_saldo": round(v["btw"], 2)} for k, v in buckets.items()},
        "totaal_btw_te_betalen": round(sum(v["btw"] for v in buckets.values()), 2),
    }
