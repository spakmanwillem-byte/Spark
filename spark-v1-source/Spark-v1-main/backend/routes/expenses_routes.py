from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import json
from datetime import datetime
import uuid
from utils.paths import get_user_path

router = APIRouter()


class Expense(BaseModel):
    id: Optional[str] = None
    amount: float
    category: str
    description: Optional[str] = None
    date: str


def load_expenses(user_id: str) -> List[dict]:
    """Load expenses from user file"""
    path = get_user_path(user_id, "expenses.json")
    
    if not path.exists():
        return []
    
    with open(path, 'r') as f:
        return json.load(f)


def save_expenses(user_id: str, expenses: List[dict]):
    """Save expenses to user file"""
    path = get_user_path(user_id, "expenses.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        json.dump(expenses, f, indent=2, ensure_ascii=False)


@router.get("/{user_id}")
async def get_expenses(user_id: str):
    """Get all expenses for user"""
    try:
        expenses = load_expenses(user_id)
        return {"success": True, "expenses": expenses}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{user_id}")
async def add_expense(user_id: str, expense: Expense):
    """Add new expense"""
    try:
        expenses = load_expenses(user_id)
        
        # Generate ID if not provided
        if not expense.id:
            expense.id = str(uuid.uuid4())
        
        # Add timestamp if not provided
        if not expense.date:
            expense.date = datetime.now().isoformat()
        
        expenses.append(expense.dict())
        save_expenses(user_id, expenses)
        
        return {"success": True, "expense": expense}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{user_id}/{expense_id}")
async def update_expense(user_id: str, expense_id: str, expense: Expense):
    """Update existing expense"""
    try:
        expenses = load_expenses(user_id)
        
        # Find and update expense
        for i, exp in enumerate(expenses):
            if exp["id"] == expense_id:
                expense.id = expense_id
                expenses[i] = expense.dict()
                save_expenses(user_id, expenses)
                return {"success": True, "expense": expense}
        
        raise HTTPException(status_code=404, detail="Expense not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{user_id}/{expense_id}")
async def delete_expense(user_id: str, expense_id: str):
    """Delete expense"""
    try:
        expenses = load_expenses(user_id)
        
        # Filter out deleted expense
        new_expenses = [exp for exp in expenses if exp["id"] != expense_id]
        
        if len(new_expenses) == len(expenses):
            raise HTTPException(status_code=404, detail="Expense not found")
        
        save_expenses(user_id, new_expenses)
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
