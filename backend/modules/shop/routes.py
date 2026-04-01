"""
Shop Routes - ROAR Token Winkel
Token = product. Prijs dynamisch op basis van Bitvavo Spark Core trading pot waarde.
User koopt tokens met EUR uit wallet. Token = aandeel in Spark Core waarde.
"""
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
from datetime import datetime, timezone
import uuid
from modules.core.storage import load_json, save_json

router = APIRouter(prefix="/shop", tags=["shop"])
DATA_DIR = Path(__file__).parent.parent.parent / "data"
ROAR_FILE = DATA_DIR / "roar" / "roar_balances.json"
WALLET_FILE = DATA_DIR / "wallet" / "wallets.json"
FINANCIAL_FILE = DATA_DIR / "financial" / "transactions.json"
POTJES_FILE = DATA_DIR / "financial" / "user_potjes.json"

TOTAL_SUPPLY = 1_000_000
BASE_PRICE = 5.08  # Fallback prijs


def get_roar_data():
    return load_json(ROAR_FILE, default={"balances": {"user-000": TOTAL_SUPPLY}, "total_supply": TOTAL_SUPPLY})


def save_roar_data(data):
    save_json(ROAR_FILE, data)


def get_dynamic_price():
    """
    Dynamische ROAR prijs gebaseerd op Spark Core totale waarde / circulerende tokens.
    Fallback: €5.08. Stijgt naarmate Spark Core meer waard wordt door trading.
    """
    try:
        # Spark Core totale waarde = alle deposits + trading profits
        fin = load_json(FINANCIAL_FILE, default={"transactions": []})
        total_value = 0.0
        for tx in fin.get("transactions", []):
            if tx["type"] == "deposit":
                total_value += tx.get("amount_eur", 0)
            elif tx["type"] == "profit":
                total_value += tx.get("amount_eur", 0)
            elif tx["type"] == "withdrawal":
                total_value -= tx.get("amount_eur", 0)

        # Circulerende tokens (alles behalve user-000/spark)
        roar = get_roar_data()
        circulating = sum(
            bal for uid, bal in roar.get("balances", {}).items()
            if uid != "user-000"
        )

        if circulating > 0 and total_value > 0:
            return round(total_value / circulating, 2)
    except Exception:
        pass
    return BASE_PRICE


class BuyTokenRequest(BaseModel):
    amount_eur: Optional[float] = None
    amount_tokens: Optional[float] = None


class SellTokenRequest(BaseModel):
    amount_tokens: float


# ============================================================
# TOKEN INFO
# ============================================================

@router.get("/token/price")
async def get_token_price():
    """Huidige ROAR token prijs"""
    price = get_dynamic_price()
    roar = get_roar_data()
    circulating = sum(bal for uid, bal in roar.get("balances", {}).items() if uid != "user-000")
    spark_balance = roar.get("balances", {}).get("user-000", 0)

    return {
        "success": True,
        "price_eur": price,
        "base_price": BASE_PRICE,
        "total_supply": TOTAL_SUPPLY,
        "circulating": circulating,
        "spark_treasury": spark_balance,
        "market_cap": round(circulating * price, 2),
    }


@router.get("/token/balance/{user_id}")
async def get_token_balance(user_id: str):
    """ROAR token saldo van user"""
    roar = get_roar_data()
    balance = roar.get("balances", {}).get(user_id, 0)
    price = get_dynamic_price()
    return {
        "user_id": user_id,
        "roar_balance": balance,
        "value_eur": round(balance * price, 2),
        "price_per_token": price,
    }


@router.get("/token/history/{user_id}")
async def get_token_history(user_id: str):
    """Aankoop/verkoop geschiedenis"""
    fin = load_json(FINANCIAL_FILE, default={"transactions": []})
    user_txs = [
        tx for tx in fin.get("transactions", [])
        if tx.get("user_id") == user_id and tx.get("type") in ("buy_roar", "sell_roar", "deposit", "withdrawal")
    ]
    user_txs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return {"transactions": user_txs}


# ============================================================
# KOPEN / VERKOPEN
# ============================================================

@router.post("/token/buy/{user_id}")
async def buy_tokens(user_id: str, req: BuyTokenRequest):
    """Koop ROAR tokens met EUR uit wallet"""
    price = get_dynamic_price()

    # Bereken amounts
    if req.amount_eur and req.amount_eur > 0:
        amount_eur = round(req.amount_eur, 2)
        amount_tokens = round(amount_eur / price, 6)
    elif req.amount_tokens and req.amount_tokens > 0:
        amount_tokens = round(req.amount_tokens, 6)
        amount_eur = round(amount_tokens * price, 2)
    else:
        return {"success": False, "error": "Geef amount_eur of amount_tokens op"}

    # Check EUR wallet saldo
    wallets = load_json(WALLET_FILE, default={"wallets": {}, "transactions": []})
    user_wallet = wallets.get("wallets", {}).get(user_id, {"balance": 0})
    if user_wallet.get("balance", 0) < amount_eur:
        return {
            "success": False,
            "error": f"Onvoldoende EUR saldo. Heb €{user_wallet.get('balance', 0):.2f}, nodig €{amount_eur:.2f}",
        }

    # Check Spark ROAR supply
    roar = get_roar_data()
    spark_bal = roar.get("balances", {}).get("user-000", 0)
    if spark_bal < amount_tokens:
        return {"success": False, "error": "Onvoldoende ROAR supply"}

    # Execute
    # 1. Deduct EUR
    wallets["wallets"][user_id]["balance"] = round(user_wallet["balance"] - amount_eur, 2)

    # 2. Transfer ROAR
    roar["balances"]["user-000"] = round(spark_bal - amount_tokens, 6)
    roar["balances"][user_id] = round(roar.get("balances", {}).get(user_id, 0) + amount_tokens, 6)

    # 3. Log transaction
    tx = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "type": "buy_roar",
        "amount_eur": amount_eur,
        "token_amount": amount_tokens,
        "price_per_token": price,
        "description": f"{amount_tokens} ROAR gekocht @ €{price}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "completed",
    }

    fin = load_json(FINANCIAL_FILE, default={"transactions": [], "roar_config": {}})
    fin["transactions"].append(tx)
    save_json(FINANCIAL_FILE, fin)

    wallets["transactions"].append(tx)
    save_json(WALLET_FILE, wallets)
    save_roar_data(roar)

    return {
        "success": True,
        "message": f"{amount_tokens} ROAR gekocht voor €{amount_eur}",
        "transaction": tx,
        "new_roar_balance": roar["balances"][user_id],
        "new_eur_balance": wallets["wallets"][user_id]["balance"],
        "price_per_token": price,
    }


@router.post("/token/sell/{user_id}")
async def sell_tokens(user_id: str, req: SellTokenRequest):
    """Verkoop ROAR tokens terug naar Spark voor EUR"""
    price = get_dynamic_price()
    amount_tokens = round(req.amount_tokens, 6)
    amount_eur = round(amount_tokens * price, 2)

    # Check ROAR saldo
    roar = get_roar_data()
    user_roar = roar.get("balances", {}).get(user_id, 0)
    if user_roar < amount_tokens:
        return {"success": False, "error": f"Onvoldoende ROAR. Heb {user_roar}, wil {amount_tokens} verkopen"}

    # Execute
    roar["balances"][user_id] = round(user_roar - amount_tokens, 6)
    roar["balances"]["user-000"] = round(roar.get("balances", {}).get("user-000", 0) + amount_tokens, 6)

    wallets = load_json(WALLET_FILE, default={"wallets": {}, "transactions": []})
    if user_id not in wallets.get("wallets", {}):
        wallets["wallets"][user_id] = {"balance": 0}
    wallets["wallets"][user_id]["balance"] = round(wallets["wallets"][user_id].get("balance", 0) + amount_eur, 2)

    tx = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "type": "sell_roar",
        "amount_eur": amount_eur,
        "token_amount": amount_tokens,
        "price_per_token": price,
        "description": f"{amount_tokens} ROAR verkocht @ €{price}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "completed",
    }

    fin = load_json(FINANCIAL_FILE, default={"transactions": [], "roar_config": {}})
    fin["transactions"].append(tx)
    save_json(FINANCIAL_FILE, fin)
    wallets["transactions"].append(tx)
    save_json(WALLET_FILE, wallets)
    save_roar_data(roar)

    return {
        "success": True,
        "message": f"{amount_tokens} ROAR verkocht voor €{amount_eur}",
        "transaction": tx,
        "new_roar_balance": roar["balances"].get(user_id, 0),
        "new_eur_balance": wallets["wallets"][user_id]["balance"],
        "price_per_token": price,
    }


# ============================================================
# POTJES SYSTEEM
# ============================================================

@router.get("/potjes/{user_id}")
async def get_potjes(user_id: str):
    """Haal potjes status op"""
    data = load_json(POTJES_FILE, default={"users": {}})
    user_data = data.get("users", {}).get(user_id, {})
    return {"success": True, "user_id": user_id, "potjes": user_data}
