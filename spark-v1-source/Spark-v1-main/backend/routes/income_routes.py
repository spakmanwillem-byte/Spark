from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import json
from datetime import datetime
import uuid
from utils.paths import get_user_path

router = APIRouter()


class Income(BaseModel):
    id: Optional[str] = None
    amount: float
    source: str
    description: Optional[str] = None
    date: str


def load_income(user_id: str) -> List[dict]:
    """Load income from user file"""
    path = get_user_path(user_id, "income.json")
    
    if not path.exists():
        return []
    
    with open(path, 'r') as f:
        return json.load(f)


def save_income(user_id: str, income_list: List[dict]):
    """Save income to user file"""
    path = get_user_path(user_id, "income.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        json.dump(income_list, f, indent=2, ensure_ascii=False)


@router.get("/{user_id}")
async def get_income(user_id: str):
    """Get all income for user"""
    try:
        income = load_income(user_id)
        return {"success": True, "income": income}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{user_id}")
async def add_income(user_id: str, income: Income):
    """Add new income"""
    try:
        income_list = load_income(user_id)
        
        # Generate ID if not provided
        if not income.id:
            income.id = str(uuid.uuid4())
        
        # Add timestamp if not provided
        if not income.date:
            income.date = datetime.now().isoformat()
        
        income_list.append(income.dict())
        save_income(user_id, income_list)
        
        return {"success": True, "income": income}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{user_id}/{income_id}")
async def update_income(user_id: str, income_id: str, income: Income):
    """Update existing income"""
    try:
        income_list = load_income(user_id)
        
        # Find and update income
        for i, inc in enumerate(income_list):
            if inc["id"] == income_id:
                income.id = income_id
                income_list[i] = income.dict()
                save_income(user_id, income_list)
                return {"success": True, "income": income}
        
        raise HTTPException(status_code=404, detail="Income not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{user_id}/{income_id}")
async def delete_income(user_id: str, income_id: str):
    """Delete income"""
    try:
        income_list = load_income(user_id)
        
        # Filter out deleted income
        new_income = [inc for inc in income_list if inc["id"] != income_id]
        
        if len(new_income) == len(income_list):
            raise HTTPException(status_code=404, detail="Income not found")
        
        save_income(user_id, new_income)
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
