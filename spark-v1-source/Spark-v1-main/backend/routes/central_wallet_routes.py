"""
Central Transaction System - Single Source of Truth
All financial data calculated from transactions
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import json
import os
from datetime import datetime, timezone
from uuid import uuid4

# Import achievement service
import sys
sys.path.append('/app/backend')
from services.achievement_service import AchievementService

router = APIRouter()

TRANSACTIONS_FILE = "/app/backend/data/financial/transactions.json"
BITVAVO_STATE_FILE = "/app/backend/data/live_trading/position_state.json"
SPARK_CORE_BALANCE_FILE = "/app/backend/data/financial/spark_core_balance.json"

# ROAR Economic System - INTERNAL ONLY
ROAR_PRICE_FIXED = 5.08  # Fallback only


class Transaction(BaseModel):
    user_id: str
    type: str  # 'buy_roar', 'sell_roar', 'deposit', 'reward', 'admin_grant'
    amount_eur: float
    token_amount: float = 0
    price_per_token: float = 0
    description: Optional[str] = None


def load_transactions():
    """Load all transactions"""
    if os.path.exists(TRANSACTIONS_FILE):
        with open(TRANSACTIONS_FILE, 'r') as f:
            return json.load(f)
    
    # Initialize
    os.makedirs(os.path.dirname(TRANSACTIONS_FILE), exist_ok=True)
    data = {
        "transactions": [],
        "roar_config": {
            "description": "ROAR tokens are shares owned by USERS ONLY",
            "spark_core": "user-000 = total value, NO tokens",
            "ownership": "100% owned by users via their tokens"
        },
        "bitvavo_state": {
            "description": "External trading bot state - tracked separately"
        }
    }
    with open(TRANSACTIONS_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    return data


def save_transactions(data):
    """Save transactions"""
    with open(TRANSACTIONS_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def calculate_user_balance(user_id: str, transactions: list):
    """
    Calculate user balance from transactions
    
    EUR balance = deposits - buy_roar + sell_roar - withdrawals
    ROAR tokens = buy_roar + admin_grant - sell_roar
    
    Geld zit OF in EUR OF in tokens (geen dubbele waarde!)
    """
    eur_balance = 0
    roar_balance = 0
    
    for tx in transactions:
        if tx['user_id'] != user_id:
            continue
            
        tx_type = tx['type']
        
        # EUR balance
        if tx_type == 'deposit':
            eur_balance += tx['amount_eur']
        elif tx_type == 'buy_roar':
            eur_balance -= tx['amount_eur']  # EUR wordt omgezet naar tokens!
        elif tx_type == 'sell_roar':
            eur_balance += tx['amount_eur']
        elif tx_type == 'withdrawal':
            eur_balance -= tx['amount_eur']
        
        # ROAR tokens
        if tx_type in ['buy_roar', 'admin_grant']:
            roar_balance += tx['token_amount']
        elif tx_type == 'sell_roar':
            roar_balance -= tx['token_amount']
    
    return eur_balance, roar_balance


def calculate_spark_core_value(transactions: list):
    """
    Get REAL Spark Core value from external source (Bitvavo)
    NOT from internal transactions!
    
    This represents the ACTUAL value in the external trading wallet.
    """
    # Read REAL external balance
    if os.path.exists(SPARK_CORE_BALANCE_FILE):
        try:
            with open(SPARK_CORE_BALANCE_FILE, 'r') as f:
                config = json.load(f)
                return config['spark_core']['balance_eur']
        except Exception as e:
            print(f"⚠️ Warning: Could not read external balance: {e}")
    
    # Fallback: use deposits (for testing only)
    print("⚠️ Using fallback calculation - external balance file not found or invalid")
    total_value = 0
    for tx in transactions:
        if tx['type'] == 'deposit':
            total_value += tx['amount_eur']
        elif tx['type'] == 'withdrawal':
            total_value -= tx['amount_eur']
    return total_value


def get_current_roar_price():
    """
    DEPRECATED - Token price is now dynamic
    Based on: (total Spark Core value) / (total tokens distributed)
    """
    return ROAR_PRICE_FIXED  # Fallback only


def get_bitvavo_state():
    """Get Bitvavo trading bot state - SEPARATE from ROAR economy"""
    try:
        if os.path.exists(BITVAVO_STATE_FILE):
            with open(BITVAVO_STATE_FILE, 'r') as f:
                state = json.load(f)
                return {
                    "trade_amount": round(state.get('trade_amount', 0), 2),
                    "total_profit": round(state.get('total_profit', 0), 2),
                    "position": state.get('position', 'none'),
                    "description": "External Bitvavo trading - NOT part of ROAR economy"
                }
    except:
        pass
    return {
        "trade_amount": 0,
        "total_profit": 0,
        "position": "none",
        "description": "Bitvavo bot not active"
    }


@router.get("/wallet/{user_id}")
async def get_wallet(user_id: str):
    """
    Single source of truth - calculate everything from transactions
    ROAR tokens = shares in Spark Core value
    """
    try:
        data = load_transactions()
        transactions = data['transactions']
        
        # Calculate user balances
        eur_balance, roar_balance = calculate_user_balance(user_id, transactions)
        
        # Calculate total Spark Core value
        spark_core_value = calculate_spark_core_value(transactions)
        
        # Calculate total distributed ROAR tokens (ALL owned by users)
        # Spark Core (user-000) has NO tokens!
        total_user_tokens = 0
        for tx in transactions:
            if tx['user_id'] == 'user-000':
                continue  # Skip Spark Core transactions
            if tx['type'] in ['buy_roar', 'admin_grant']:
                total_user_tokens += tx['token_amount']
            elif tx['type'] == 'sell_roar':
                total_user_tokens -= tx['token_amount']
        
        # Dynamic token price = Spark Core value / total user tokens
        # Users OWN the entire system via their tokens
        if total_user_tokens > 0:
            current_price = spark_core_value / total_user_tokens
        else:
            current_price = 0  # No tokens = no price
        
        # User's ROAR value in EUR
        roar_value_eur = roar_balance * current_price
        
        # User transactions (last 10)
        user_txs = [tx for tx in transactions if tx['user_id'] == user_id]
        recent_txs = sorted(user_txs, key=lambda x: x['timestamp'], reverse=True)[:10]
        
        # Get achievements (based on ROAR token holdings, not word count)
        # Calculate achievement progress based on total ROAR tokens bought
        buy_roar_txs = [tx for tx in user_txs if tx['type'] == 'buy_roar']
        total_tokens_bought = sum(tx.get('token_amount', 0) for tx in buy_roar_txs)
        
        achievements = {
            "total_tokens_bought": round(total_tokens_bought, 2),
            "unlocked": []
        }
        
        # Check achievement thresholds
        if total_tokens_bought >= 1:
            achievements["unlocked"].append("Community Supporter")
        if total_tokens_bought >= 5:
            achievements["unlocked"].append("Core Supporter")
        if total_tokens_bought >= 10:
            achievements["unlocked"].append("ROARR Builder")
        
        # Get Bitvavo state (SEPARATE from ROAR economy)
        bitvavo_state = get_bitvavo_state()
        
        return {
            "success": True,
            "user_id": user_id,
            "balances": {
                "eur": round(eur_balance, 2),
                "roar": round(roar_balance, 6),
                "roar_value_eur": round(roar_value_eur, 2)
            },
            "roar_market": {
                "current_price": round(current_price, 2),
                "total_user_tokens": round(total_user_tokens, 6),
                "user_balance": round(roar_balance, 6),
                "user_percentage": round((roar_balance / total_user_tokens * 100) if total_user_tokens > 0 else 0, 2),
                "spark_core_value": round(spark_core_value, 2),
                "note": "Token price = Spark Core value / total user tokens. Users own 100% via tokens."
            },
            "bitvavo_trading": bitvavo_state,
            "achievements": achievements,
            "transactions": recent_txs,
            "transaction_count": len(user_txs)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transaction")
async def create_transaction(tx: Transaction):
    """
    Create a new transaction - this is the ONLY way to change balances
    """
    try:
        data = load_transactions()
        
        # Get current balances
        eur_balance, roar_balance = calculate_user_balance(tx.user_id, data['transactions'])
        
        # Validate transaction
        if tx.type == 'buy_roar':
            if eur_balance < tx.amount_eur:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient EUR balance. Have €{eur_balance}, need €{tx.amount_eur}"
                )
            
            # Check Spark has enough ROAR
            total_distributed = sum(
                t['token_amount'] for t in data['transactions'] 
                if t['type'] in ['buy_roar', 'admin_grant']
            )
            spark_balance = data['roar_config']['total_supply'] - total_distributed
            
            if spark_balance < tx.token_amount:
                raise HTTPException(status_code=400, detail="Insufficient ROAR supply")
        
        # Create transaction record
        transaction_record = {
            "id": str(uuid4()),
            "user_id": tx.user_id,
            "type": tx.type,
            "amount_eur": round(tx.amount_eur, 2),
            "token_amount": round(tx.token_amount, 6),
            "price_per_token": round(tx.price_per_token, 2),
            "description": tx.description or "",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        data['transactions'].append(transaction_record)
        save_transactions(data)
        
        # CHECK ACHIEVEMENTS (triggered by buy_roar transaction)
        newly_unlocked = []
        if tx.type == "buy_roar":
            # Calculate total tokens bought by user
            user_txs = [t for t in data['transactions'] if t['user_id'] == tx.user_id and t['type'] == 'buy_roar']
            total_bought = sum(t.get('token_amount', 0) for t in user_txs)
            
            # Check thresholds
            if total_bought >= 10 and not any(t.get('token_amount', 0) >= 10 for t in user_txs[:-1]):
                newly_unlocked.append("ROARR Builder")
            elif total_bought >= 5 and not any(t.get('token_amount', 0) >= 5 for t in user_txs[:-1]):
                newly_unlocked.append("Core Supporter")
            elif total_bought >= 1 and len(user_txs) == 1:
                newly_unlocked.append("Community Supporter")
        
        # Recalculate balances
        new_eur, new_roar = calculate_user_balance(tx.user_id, data['transactions'])
        
        return {
            "success": True,
            "message": f"Transaction created: {tx.type}",
            "transaction": transaction_record,
            "new_balances": {
                "eur": round(new_eur, 2),
                "roar": round(new_roar, 6)
            },
            "achievements_unlocked": newly_unlocked
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transactions/{user_id}")
async def get_user_transactions(user_id: str, limit: int = 50):
    """Get user transaction history"""
    try:
        data = load_transactions()
        user_txs = [tx for tx in data['transactions'] if tx['user_id'] == user_id]
        recent = sorted(user_txs, key=lambda x: x['timestamp'], reverse=True)[:limit]
        
        return {
            "success": True,
            "transactions": recent,
            "total_count": len(user_txs)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/roar/stats")
async def get_roar_stats():
    """Get ROAR market stats - calculated from transactions"""
    try:
        data = load_transactions()
        transactions = data['transactions']
        
        # Calculate total distributed
        total_distributed = sum(
            tx['token_amount'] for tx in transactions
            if tx['type'] in ['buy_roar', 'admin_grant']
        )
        
        total_supply = data['roar_config']['total_supply']
        spark_balance = total_supply - total_distributed
        current_price = get_current_roar_price()
        
        return {
            "success": True,
            "total_supply": total_supply,
            "circulating_supply": round(total_distributed, 2),
            "spark_balance": round(spark_balance, 2),
            "current_price": current_price,
            "market_cap": round(total_distributed * current_price, 2),
            "total_transactions": len([tx for tx in transactions if tx['type'] in ['buy_roar', 'sell_roar']])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
