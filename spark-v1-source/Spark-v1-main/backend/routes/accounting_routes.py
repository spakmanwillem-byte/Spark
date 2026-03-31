from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import json
from pathlib import Path
from datetime import datetime, timedelta
import uuid

router = APIRouter()

ACCOUNTING_FILE = Path("/app/backend/data/accounting/transactions.json")
ACCOUNTING_FILE.parent.mkdir(parents=True, exist_ok=True)

class AccountingTransaction(BaseModel):
    type: str  # 'income', 'expense'
    category: str
    amount: float
    description: str
    date: Optional[str] = None
    btw_percentage: Optional[float] = 21.0

def load_transactions():
    if not ACCOUNTING_FILE.exists():
        return {"transactions": []}
    with open(ACCOUNTING_FILE, 'r') as f:
        return json.load(f)

def save_transactions(data):
    with open(ACCOUNTING_FILE, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

@router.post("/transaction")
async def add_transaction(transaction: AccountingTransaction):
    """Add accounting transaction"""
    data = load_transactions()
    
    new_transaction = {
        "id": str(uuid.uuid4()),
        "type": transaction.type,
        "category": transaction.category,
        "amount": transaction.amount,
        "description": transaction.description,
        "date": transaction.date or datetime.now().isoformat(),
        "btw_percentage": transaction.btw_percentage,
        "btw_amount": round(transaction.amount * (transaction.btw_percentage / 100), 2) if transaction.btw_percentage else 0,
        "created_at": datetime.now().isoformat()
    }
    
    data["transactions"].append(new_transaction)
    save_transactions(data)
    
    return {"success": True, "transaction": new_transaction}

@router.get("/summary")
async def get_accounting_summary(start_date: Optional[str] = None, end_date: Optional[str] = None):
    """Get accounting summary"""
    data = load_transactions()
    
    # Default to current month
    if not start_date:
        start_date = datetime.now().replace(day=1).isoformat()
    if not end_date:
        end_date = datetime.now().isoformat()
    
    # Filter transactions
    filtered = [
        t for t in data["transactions"]
        if start_date <= t["date"] <= end_date
    ]
    
    # Calculate totals
    income = sum(t["amount"] for t in filtered if t["type"] == "income")
    expenses = sum(t["amount"] for t in filtered if t["type"] == "expense")
    btw_total = sum(t.get("btw_amount", 0) for t in filtered)
    
    return {
        "success": True,
        "period": {"start": start_date, "end": end_date},
        "summary": {
            "income": round(income, 2),
            "expenses": round(expenses, 2),
            "profit": round(income - expenses, 2),
            "btw_total": round(btw_total, 2),
            "transaction_count": len(filtered)
        },
        "transactions": filtered
    }

@router.get("/categories")
async def get_categories():
    """Get suggested categories"""
    return {
        "success": True,
        "income_categories": [
            "Wallet Deposits",
            "Donations",
            "Spark Shares Sale",
            "Services",
            "Other Income"
        ],
        "expense_categories": [
            "Hosting",
            "Domain Names",
            "Development Tools",
            "Marketing",
            "Legal/Admin",
            "Hardware",
            "Electricity (Odroid)",
            "Other Expenses"
        ]
    }
