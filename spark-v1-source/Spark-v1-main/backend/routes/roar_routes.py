"""
ROAR Token Routes
Dynamic pricing based on trading pot value
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import json
import os
from datetime import datetime, timezone
from uuid import uuid4

router = APIRouter()

# Data paths
ROAR_DATA = "/app/backend/data/roar/roar_balances.json"
WALLETS_FILE = "/app/backend/data/wallets/wallets.json"

# ROAR Token Supply
TOTAL_ROAR_SUPPLY = 1_000_000
SPARK_ROAR_BALANCE = TOTAL_ROAR_SUPPLY  # Spark owns all initially


class BuyROARRequest(BaseModel):
    user_id: str
    amount_eur: float = None
    amount_roar: float = None


def get_current_roar_price():
    """
    Get current ROAR price from trading pot value
    Default: €5.08, grows to €10.16 over 10 pots
    """
    try:
        # Read current pot value from decision engine state
        state_file = "/app/backend/data/live_trading/position_state.json"
        if os.path.exists(state_file):
            with open(state_file, 'r') as f:
                state = json.load(f)
                trade_amount = state.get('trade_amount', 5.08)
                return round(trade_amount, 2)
    except Exception as e:
        print(f"Error reading pot value: {e}")
    
    # Default fallback
    return 5.08


def load_roar_data():
    """Load ROAR balances"""
    if os.path.exists(ROAR_DATA):
        with open(ROAR_DATA, 'r') as f:
            return json.load(f)
    
    # Initialize
    os.makedirs(os.path.dirname(ROAR_DATA), exist_ok=True)
    data = {
        "balances": {
            "user-000": TOTAL_ROAR_SUPPLY  # Spark owns all
        },
        "transactions": []
    }
    with open(ROAR_DATA, 'w') as f:
        json.dump(data, f, indent=2)
    return data


def save_roar_data(data):
    """Save ROAR balances"""
    with open(ROAR_DATA, 'w') as f:
        json.dump(data, f, indent=2)


def load_wallets():
    """Load user wallets"""
    if os.path.exists(WALLETS_FILE):
        with open(WALLETS_FILE, 'r') as f:
            return json.load(f)
    return {"wallets": {}, "transactions": []}


def save_wallets(data):
    """Save wallets"""
    with open(WALLETS_FILE, 'w') as f:
        json.dump(data, f, indent=2)


@router.get("/roar/price")
async def get_roar_price():
    """
    Get current ROAR token price
    Price is dynamic based on trading pot value
    """
    try:
        current_price = get_current_roar_price()
        
        return {
            "success": True,
            "price_eur": current_price,
            "total_supply": TOTAL_ROAR_SUPPLY,
            "note": f"1 ROAR = €{current_price} (dynamic pricing)"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/roar/balance/{user_id}")
async def get_roar_balance(user_id: str):
    """Get user's ROAR token balance"""
    try:
        data = load_roar_data()
        balance = data["balances"].get(user_id, 0)
        current_price = get_current_roar_price()
        
        return {
            "success": True,
            "user_id": user_id,
            "roar_balance": balance,
            "value_eur": round(balance * current_price, 2),
            "current_price": current_price
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/roar/buy")
async def buy_roar(request: BuyROARRequest):
    """
    Buy ROAR tokens with EUR from wallet
    Can specify either amount_eur or amount_roar
    """
    try:
        user_id = request.user_id
        current_price = get_current_roar_price()
        
        # Calculate amounts
        if request.amount_eur:
            amount_eur = round(request.amount_eur, 2)
            amount_roar = round(amount_eur / current_price, 6)
        elif request.amount_roar:
            amount_roar = round(request.amount_roar, 6)
            amount_eur = round(amount_roar * current_price, 2)
        else:
            raise HTTPException(status_code=400, detail="Specify amount_eur or amount_roar")
        
        # Check user wallet balance
        wallets_data = load_wallets()
        user_wallet = wallets_data["wallets"].get(user_id)
        
        if not user_wallet:
            raise HTTPException(status_code=404, detail="Wallet not found")
        
        if user_wallet["balance"] < amount_eur:
            raise HTTPException(
                status_code=400, 
                detail=f"Insufficient balance. Need €{amount_eur}, have €{user_wallet['balance']}"
            )
        
        # Check Spark has enough ROAR
        roar_data = load_roar_data()
        spark_balance = roar_data["balances"].get("user-000", 0)
        
        if spark_balance < amount_roar:
            raise HTTPException(status_code=400, detail="Insufficient ROAR supply")
        
        # Execute transaction
        # 1. Deduct EUR from user wallet
        user_wallet["balance"] = round(user_wallet["balance"] - amount_eur, 2)
        
        # 2. Transfer ROAR from Spark to user
        roar_data["balances"]["user-000"] = round(spark_balance - amount_roar, 6)
        roar_data["balances"][user_id] = round(
            roar_data["balances"].get(user_id, 0) + amount_roar, 6
        )
        
        # 3. Log transaction
        transaction = {
            "id": str(uuid4()),
            "user_id": user_id,
            "type": "buy_roar",
            "amount_eur": amount_eur,
            "amount_roar": amount_roar,
            "price_per_roar": current_price,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        roar_data["transactions"].append(transaction)
        wallets_data["transactions"].append({
            **transaction,
            "status": "completed",
            "message": f"Bought {amount_roar} ROAR tokens"
        })
        
        # Save
        save_roar_data(roar_data)
        save_wallets(wallets_data)
        
        return {
            "success": True,
            "message": f"Successfully bought {amount_roar} ROAR for €{amount_eur}",
            "transaction": transaction,
            "new_roar_balance": roar_data["balances"][user_id],
            "new_wallet_balance": user_wallet["balance"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/roar/stats")
async def get_roar_stats():
    """Get ROAR token statistics"""
    try:
        roar_data = load_roar_data()
        current_price = get_current_roar_price()
        
        # Calculate circulating supply (owned by users, not Spark)
        total_user_roar = sum(
            balance for user_id, balance in roar_data["balances"].items()
            if user_id != "user-000"
        )
        
        spark_balance = roar_data["balances"].get("user-000", 0)
        
        return {
            "success": True,
            "total_supply": TOTAL_ROAR_SUPPLY,
            "circulating_supply": round(total_user_roar, 2),
            "spark_balance": round(spark_balance, 2),
            "current_price": current_price,
            "market_cap": round(total_user_roar * current_price, 2),
            "total_transactions": len(roar_data["transactions"])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
