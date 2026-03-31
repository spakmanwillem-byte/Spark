"""
Wallet API Routes - Multi-entity wallet system + Legacy wallet support
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
import json
from pathlib import Path
from datetime import datetime
import uuid
from services.wallet_service import WalletService

router = APIRouter()

# ============================================
# NEW: Multi-Entity Wallet System
# ============================================

@router.get("/entities")
async def get_entities():
    """
    Haal alle wallet entities op (Spark Core, Spark Your Life, etc)
    """
    entities = WalletService.get_entities()
    return {"success": True, "entities": entities}


@router.get("/entities/{entity_id}")
async def get_entity(entity_id: str):
    """
    Haal 1 specifieke entity op
    """
    entity = WalletService.get_entity(entity_id)
    
    if entity:
        return {"success": True, "entity": entity}
    else:
        return {"success": False, "error": "Entity not found"}


@router.get("/entities/{entity_id}/balance")
async def get_entity_balance(
    entity_id: str,
    user_id: str = Query(None, description="User ID voor Bitvavo balance")
):
    """
    Haal balance op van een entity
    Voor Spark Core crypto: live Bitvavo data
    """
    result = WalletService.get_entity_balance(entity_id, user_id)
    return result


@router.get("/overview")
async def get_overview(
    user_id: str = Query(None, description="User ID (optioneel)"),
    owner: str = Query(None, description="Filter: 'spark' | 'willem' | null")
):
    """
    Totaal overzicht van alle entities + optioneel user wallet
    
    Query params:
        user_id: Voor crypto balance + user wallet data
        owner: Filter entities op owner ('spark', 'willem', of null voor alles)
    """
    result = WalletService.get_overview(user_id, owner)
    return result


@router.get("/user/{user_id}/wallet")
async def get_user_wallet_tokens(user_id: str):
    """
    Haal user wallet op (tokens, credits, balance)
    """
    wallet = WalletService.get_user_wallet(user_id)
    
    if wallet:
        return {"success": True, "wallet": wallet}
    else:
        return {"success": False, "error": "User wallet not found"}


@router.post("/entities/{entity_id}/transaction")
async def add_transaction(
    entity_id: str,
    amount: float = Query(..., description="Bedrag in EUR (positief)"),
    type: str = Query(..., description="Type: donation | income | expense"),
    description: str = Query(..., description="Korte beschrijving"),
    user_id: str = Query(None, description="User ID (optioneel)")
):
    """
    Voeg handmatige transaction toe aan entity
    
    Voor donaties (Spark Your Life), inkomsten (Roadkill Merch), kosten, etc.
    """
    result = WalletService.add_transaction(entity_id, amount, type, description, user_id)
    return result


@router.get("/entities/{entity_id}/transactions")
async def get_entity_transactions(
    entity_id: str,
    limit: int = Query(100, description="Max aantal transactions")
):
    """
    Haal transactions op voor een entity
    """
    result = WalletService.get_transactions(entity_id, limit)
    return result


@router.get("/transactions")
async def get_all_transactions(
    limit: int = Query(100, description="Max aantal transactions")
):
    """
    Haal alle transactions op (over alle entities)
    """
    result = WalletService.get_transactions(None, limit)
    return result


# ============================================
# LEGACY: Old Wallet System (Deposits/Withdrawals)
# ============================================

WALLETS_FILE = Path("/app/backend/data/wallets/wallets.json")
WALLETS_FILE.parent.mkdir(parents=True, exist_ok=True)

class DepositRequest(BaseModel):
    user_id: str
    amount: float
    message: Optional[str] = None

class WithdrawalRequest(BaseModel):
    user_id: str
    amount: float
    iban: str
    iban_name: str

class Transaction(BaseModel):
    user_id: str
    type: str  # 'deposit', 'withdrawal', 'donation', 'reward'
    amount: float
    status: str  # 'pending', 'approved', 'rejected', 'completed'
    notes: Optional[str] = None

def load_wallets():
    if not WALLETS_FILE.exists():
        return {"wallets": {}, "transactions": []}
    with open(WALLETS_FILE, 'r') as f:
        return json.load(f)

def save_wallets(data):
    with open(WALLETS_FILE, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

@router.get("/{user_id}")
async def get_wallet(user_id: str):
    """Get user's wallet balance and info"""
    data = load_wallets()
    
    if user_id not in data["wallets"]:
        # Initialize wallet
        data["wallets"][user_id] = {
            "balance": 0.0,
            "created_at": datetime.now().isoformat(),
            "total_deposited": 0.0,
            "total_withdrawn": 0.0,
            "total_donated": 0.0
        }
        save_wallets(data)
    
    wallet = data["wallets"][user_id]
    
    # Get recent transactions
    user_transactions = [
        t for t in data["transactions"] 
        if t.get("user_id") == user_id
    ][-10:]  # Last 10
    
    return {
        "success": True,
        "wallet": wallet,
        "recent_transactions": user_transactions
    }

@router.post("/deposit/request")
async def request_deposit(request: DepositRequest):
    """User requests to deposit money"""
    data = load_wallets()
    
    transaction = {
        "id": str(uuid.uuid4()),
        "user_id": request.user_id,
        "type": "deposit",
        "amount": request.amount,
        "status": "pending",
        "message": request.message,
        "created_at": datetime.now().isoformat(),
        "payment_info": {
            "method": "bank_transfer",
            "iban": "NL12 ABCD 1234 5678 90",  # PLACEHOLDER
            "reference": f"SPARK-{request.user_id[:8].upper()}-{datetime.now().strftime('%Y%m%d')}"
        }
    }
    
    data["transactions"].append(transaction)
    save_wallets(data)
    
    return {
        "success": True,
        "message": "Deposit request created. Please transfer money to the provided IBAN.",
        "transaction": transaction
    }

@router.post("/withdrawal/request")
async def request_withdrawal(request: WithdrawalRequest):
    """User requests to withdraw money"""
    data = load_wallets()
    
    # Check balance
    wallet = data["wallets"].get(request.user_id)
    if not wallet or wallet["balance"] < request.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    
    transaction = {
        "id": str(uuid.uuid4()),
        "user_id": request.user_id,
        "type": "withdrawal",
        "amount": request.amount,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "withdrawal_info": {
            "iban": request.iban,
            "iban_name": request.iban_name
        }
    }
    
    data["transactions"].append(transaction)
    save_wallets(data)
    
    return {
        "success": True,
        "message": "Withdrawal request submitted. Willem will process it soon.",
        "transaction": transaction
    }

@router.post("/donation")
async def make_donation(user_id: str, amount: float, recurring: bool = False):
    """User makes a donation to Spark"""
    data = load_wallets()
    
    transaction = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "type": "donation",
        "amount": amount,
        "status": "pending",
        "recurring": recurring,
        "created_at": datetime.now().isoformat(),
        "payment_info": {
            "method": "bank_transfer",
            "iban": "NL12 ABCD 1234 5678 90",  # PLACEHOLDER
            "reference": f"SPARK-DONATIE-{user_id[:8].upper()}"
        }
    }
    
    data["transactions"].append(transaction)
    save_wallets(data)
    
    return {
        "success": True,
        "message": "Thank you for supporting Spark! 💚",
        "transaction": transaction
    }

@router.get("/admin/pending")
async def get_pending_transactions():
    """Admin: Get all pending transactions"""
    data = load_wallets()
    pending = [t for t in data["transactions"] if t.get("status") == "pending"]
    return {"success": True, "pending_transactions": pending}

@router.put("/admin/approve/{transaction_id}")
async def approve_transaction(transaction_id: str):
    """Admin: Approve a transaction"""
    data = load_wallets()
    
    # Find transaction
    transaction = next((t for t in data["transactions"] if t["id"] == transaction_id), None)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Update status
    transaction["status"] = "approved"
    transaction["approved_at"] = datetime.now().isoformat()
    
    # Update wallet balance
    user_id = transaction["user_id"]
    if user_id not in data["wallets"]:
        data["wallets"][user_id] = {"balance": 0.0, "created_at": datetime.now().isoformat()}
    
    if transaction["type"] == "deposit" or transaction["type"] == "donation":
        data["wallets"][user_id]["balance"] += transaction["amount"]
        if transaction["type"] == "deposit":
            data["wallets"][user_id]["total_deposited"] = data["wallets"][user_id].get("total_deposited", 0) + transaction["amount"]
        else:
            data["wallets"][user_id]["total_donated"] = data["wallets"][user_id].get("total_donated", 0) + transaction["amount"]
    
    elif transaction["type"] == "withdrawal":
        data["wallets"][user_id]["balance"] -= transaction["amount"]
        data["wallets"][user_id]["total_withdrawn"] = data["wallets"][user_id].get("total_withdrawn", 0) + transaction["amount"]
        transaction["status"] = "completed"
    
    save_wallets(data)
    
    return {"success": True, "message": "Transaction approved", "transaction": transaction}

@router.get("/spark/balance")
async def get_spark_balance():
    """Get Spark's total balance (PLACEHOLDER)"""
    # PLACEHOLDER: Mock data until Bitvavo API
    return {
        "success": True,
        "note": "⚠️ PLACEHOLDER DATA - Real data via Bitvavo API later",
        "balance": {
            "total_eur": 12458.32,
            "bitcoin": 0.2847,
            "bitcoin_price_eur": 43750.50,
            "change_24h": 2.4,
            "change_30d": 8.7
        },
        "last_updated": datetime.now().isoformat()
    }
