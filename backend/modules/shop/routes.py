"""
Shop Routes - Roadkill Winkel + ROAR Token
Producten: Merch (caps, hoodies) + ROAR tokens (dynamische prijs).
Winkelwagen + bestellingen. Kasboek koppeling per entity.
"""
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional, List
from pathlib import Path
from datetime import datetime, timezone
import time
import uuid
from modules.core.storage import load_json, save_json

router = APIRouter(prefix="/shop", tags=["shop"])
DATA_DIR = Path(__file__).parent.parent.parent / "data"
ROAR_FILE = DATA_DIR / "roar" / "roar_balances.json"
WALLET_FILE = DATA_DIR / "wallet" / "wallets.json"
FINANCIAL_FILE = DATA_DIR / "financial" / "transactions.json"
POTJES_FILE = DATA_DIR / "financial" / "user_potjes.json"
PRODUCTS_FILE = DATA_DIR / "shop" / "products.json"
ACCOUNTING_FILE = DATA_DIR / "accounting" / "transactions.json"

TOTAL_SUPPLY = 1_000_000
BASE_PRICE = 5.08  # Vaste prijs voor eerste 10 tokens
FIXED_PRICE_LIMIT = 10  # Na 10 tokens: dynamische prijs

# Cache voor live Bitvavo balance (30s)
_bitvavo_cache = {"value": None, "timestamp": 0}


def get_roar_data():
    return load_json(ROAR_FILE, default={"balances": {"user-000": TOTAL_SUPPLY}, "total_supply": TOTAL_SUPPLY})


def save_roar_data(data):
    save_json(ROAR_FILE, data)


def get_circulating():
    """Bereken circulerende tokens (alles behalve user-000/spark treasury)"""
    roar = get_roar_data()
    return sum(
        bal for uid, bal in roar.get("balances", {}).items()
        if uid != "user-000"
    )


def get_bitvavo_balance_cached(user_id: str = "user-001") -> Optional[float]:
    """Haal live Bitvavo balance op met 30s cache. Returns None bij fout."""
    now = time.time()
    if _bitvavo_cache["value"] is not None and (now - _bitvavo_cache["timestamp"]) < 30:
        return _bitvavo_cache["value"]
    try:
        from modules.trade.monitor import fetch_bitvavo_balance
        result = fetch_bitvavo_balance(user_id)
        if result.get("success"):
            total = result.get("total_eur", 0)
            _bitvavo_cache["value"] = total
            _bitvavo_cache["timestamp"] = now
            return total
    except Exception:
        pass
    return None


def get_spark_core_value():
    """
    Spark Core totale waarde = LIVE Bitvavo balance (primair) OF
    deposits + trading profits - withdrawals uit financial file (fallback).
    """
    # PRIMAIR: Live Bitvavo balance
    live = get_bitvavo_balance_cached()
    if live is not None and live > 0:
        return live

    # FALLBACK: Bereken uit financial transactions
    fin = load_json(FINANCIAL_FILE, default={"transactions": []})
    total_value = 0.0
    for tx in fin.get("transactions", []):
        if tx["type"] == "deposit":
            total_value += tx.get("amount_eur", 0)
        elif tx["type"] == "profit":
            total_value += tx.get("amount_eur", 0)
        elif tx["type"] == "withdrawal":
            total_value -= tx.get("amount_eur", 0)
    return total_value


def get_dynamic_price():
    """
    ROAR prijs model:
    - Tot en met 10 tokens: bodemprijs €5.08 (starterprijs)
    - Boven dat: dynamisch = Spark Core (Bitvavo) waarde / circulerende tokens
    - Als Bitvavo stijgt door trading → token prijs stijgt mee
    """
    circulating = get_circulating()

    # Altijd dynamische berekening als Spark Core waarde bekend is
    try:
        total_value = get_spark_core_value()
        if circulating > 0 and total_value > 0:
            dynamic = round(total_value / circulating, 2)
            # Bodem op BASE_PRICE zolang nog weinig tokens uitstaan
            if circulating <= FIXED_PRICE_LIMIT:
                return max(dynamic, BASE_PRICE)
            return dynamic
    except Exception:
        pass
    return BASE_PRICE


class BuyTokenRequest(BaseModel):
    amount_eur: Optional[float] = None
    amount_tokens: Optional[int] = None  # Alleen hele tokens


class SellTokenRequest(BaseModel):
    amount_tokens: int  # Alleen hele tokens


# ============================================================
# TOKEN INFO
# ============================================================

@router.get("/token/price")
async def get_token_price():
    """Huidige ROAR token prijs"""
    price = get_dynamic_price()
    circulating = get_circulating()
    roar = get_roar_data()
    spark_balance = roar.get("balances", {}).get("user-000", 0)
    spark_core_value = get_spark_core_value()
    is_fixed = circulating < FIXED_PRICE_LIMIT

    return {
        "success": True,
        "price_eur": price,
        "base_price": BASE_PRICE,
        "total_supply": TOTAL_SUPPLY,
        "circulating": circulating,
        "spark_treasury": spark_balance,
        "spark_core_value": round(spark_core_value, 2),
        "market_cap": round(circulating * price, 2),
        "price_model": "fixed" if is_fixed else "dynamic",
        "fixed_price_limit": FIXED_PRICE_LIMIT,
        "tokens_until_dynamic": max(0, FIXED_PRICE_LIMIT - circulating),
        "bitvavo_balance": round(spark_core_value, 2),
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
    """Koop ROAR tokens met EUR uit wallet - alleen hele tokens"""
    price = get_dynamic_price()

    # Bereken amounts - alleen hele tokens
    if req.amount_tokens and req.amount_tokens > 0:
        amount_tokens = int(req.amount_tokens)
        amount_eur = round(amount_tokens * price, 2)
    elif req.amount_eur and req.amount_eur > 0:
        amount_tokens = int(req.amount_eur / price)  # Afronden naar beneden
        if amount_tokens < 1:
            return {"success": False, "error": f"Minimaal 1 token nodig. Prijs: {price}"}
        amount_eur = round(amount_tokens * price, 2)
    else:
        return {"success": False, "error": "Geef amount_eur of amount_tokens op"}

    # Check EUR wallet saldo
    wallets = load_json(WALLET_FILE, default={"wallets": {}, "transactions": []})
    user_wallet = wallets.get("wallets", {}).get(user_id, {"balance": 0})
    if user_wallet.get("balance", 0) < amount_eur:
        return {
            "success": False,
            "error": f"Onvoldoende EUR saldo. Heb {user_wallet.get('balance', 0):.2f}, nodig {amount_eur:.2f}",
        }

    # Check Spark ROAR supply
    roar = get_roar_data()
    spark_bal = roar.get("balances", {}).get("user-000", 0)
    if spark_bal < amount_tokens:
        return {"success": False, "error": "Onvoldoende ROAR supply"}

    # Execute
    # 1. Deduct EUR
    wallets["wallets"][user_id]["balance"] = round(user_wallet["balance"] - amount_eur, 2)

    # 2. Transfer ROAR (hele tokens)
    roar["balances"]["user-000"] = spark_bal - amount_tokens
    roar["balances"][user_id] = roar.get("balances", {}).get(user_id, 0) + amount_tokens

    # 3. Log transaction
    tx = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "type": "buy_roar",
        "amount_eur": amount_eur,
        "token_amount": amount_tokens,
        "price_per_token": price,
        "description": f"{amount_tokens} ROAR gekocht @ {price}",
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
        "message": f"{amount_tokens} ROAR gekocht voor {amount_eur}",
        "transaction": tx,
        "new_roar_balance": roar["balances"][user_id],
        "new_eur_balance": wallets["wallets"][user_id]["balance"],
        "price_per_token": price,
    }


@router.post("/token/sell/{user_id}")
async def sell_tokens(user_id: str, req: SellTokenRequest):
    """Verkoop ROAR tokens terug naar Spark voor EUR - alleen hele tokens"""
    price = get_dynamic_price()
    amount_tokens = int(req.amount_tokens)
    if amount_tokens < 1:
        return {"success": False, "error": "Minimaal 1 token verkopen"}
    amount_eur = round(amount_tokens * price, 2)

    # Check ROAR saldo
    roar = get_roar_data()
    user_roar = roar.get("balances", {}).get(user_id, 0)
    if user_roar < amount_tokens:
        return {"success": False, "error": f"Onvoldoende ROAR. Heb {user_roar}, wil {amount_tokens} verkopen"}

    # Execute
    roar["balances"][user_id] = user_roar - amount_tokens
    roar["balances"]["user-000"] = roar.get("balances", {}).get("user-000", 0) + amount_tokens

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
        "description": f"{amount_tokens} ROAR verkocht @ {price}",
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
        "message": f"{amount_tokens} ROAR verkocht voor {amount_eur}",
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



# ============================================================
# PRODUCTEN CATALOG
# ============================================================

@router.get("/products")
async def get_products():
    """Alle winkel producten ophalen"""
    data = load_json(PRODUCTS_FILE, default={"products": []})
    products = data.get("products", [])
    # ROAR token prijs dynamisch updaten
    price = get_dynamic_price()
    for p in products:
        if p.get("dynamic_price"):
            p["price"] = price
    return {"success": True, "products": products}


@router.get("/products/{product_id}")
async def get_product(product_id: str):
    """Enkel product ophalen"""
    data = load_json(PRODUCTS_FILE, default={"products": []})
    for p in data.get("products", []):
        if p["id"] == product_id:
            if p.get("dynamic_price"):
                p["price"] = get_dynamic_price()
            return {"success": True, "product": p}
    return {"success": False, "error": "Product niet gevonden"}


# ============================================================
# BESTELLINGEN (Merch)
# ============================================================

class OrderItem(BaseModel):
    product_id: str
    quantity: int = 1


class CreateOrderRequest(BaseModel):
    items: List[OrderItem]
    shipping_name: Optional[str] = None
    shipping_address: Optional[str] = None
    notes: Optional[str] = None


@router.post("/orders/{user_id}")
async def create_order(user_id: str, req: CreateOrderRequest):
    """Bestelling plaatsen - trekt af van wallet, boekt in kasboek"""
    data = load_json(PRODUCTS_FILE, default={"products": [], "orders": []})
    products = {p["id"]: p for p in data.get("products", [])}

    # Bouw order items
    order_items = []
    total = 0.0
    for item in req.items:
        prod = products.get(item.product_id)
        if not prod:
            return {"success": False, "error": f"Product {item.product_id} niet gevonden"}
        if not prod.get("in_stock", True):
            return {"success": False, "error": f"{prod['name']} is niet op voorraad"}
        if prod.get("category") == "token":
            return {"success": False, "error": "ROAR tokens koop je via de Token sectie"}

        price = prod["price"]
        line_total = round(price * item.quantity, 2)
        total += line_total
        order_items.append({
            "product_id": item.product_id,
            "name": prod["name"],
            "price": price,
            "quantity": item.quantity,
            "line_total": line_total,
            "entity_id": prod.get("entity_id", "roadkill_merch"),
        })

    total = round(total, 2)

    # Check wallet saldo
    wallets = load_json(WALLET_FILE, default={"wallets": {}, "transactions": []})
    user_wallet = wallets.get("wallets", {}).get(user_id, {"balance": 0})
    if user_wallet.get("balance", 0) < total:
        return {
            "success": False,
            "error": f"Onvoldoende saldo. Heb {user_wallet.get('balance', 0):.2f}, nodig {total:.2f}",
        }

    # Maak order aan
    order_id = str(uuid.uuid4())[:8]
    now = datetime.now(timezone.utc).isoformat()
    order = {
        "id": order_id,
        "user_id": user_id,
        "items": order_items,
        "total": total,
        "status": "besteld",
        "shipping_name": req.shipping_name,
        "shipping_address": req.shipping_address,
        "notes": req.notes,
        "created_at": now,
    }

    # Trek af van wallet
    wallets["wallets"][user_id]["balance"] = round(user_wallet["balance"] - total, 2)
    wallet_tx = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "type": "purchase",
        "amount": total,
        "message": f"Bestelling #{order_id}: {', '.join(i['name'] for i in order_items)}",
        "created_at": now,
        "status": "completed",
    }
    wallets["transactions"].append(wallet_tx)
    save_json(WALLET_FILE, wallets)

    # Boek in kasboek per entity
    accounting = load_json(ACCOUNTING_FILE, default={"transactions": []})
    for item in order_items:
        acc_tx = {
            "id": str(uuid.uuid4()),
            "type": "income",
            "category": "Sales",
            "amount": item["line_total"],
            "description": f"Verkoop: {item['quantity']}x {item['name']} (order #{order_id})",
            "entity_id": item["entity_id"],
            "date": now,
            "btw_percentage": 21,
            "btw_amount": round(item["line_total"] * 0.21, 2),
            "created_at": now,
        }
        accounting["transactions"].append(acc_tx)
    save_json(ACCOUNTING_FILE, accounting)

    # Sla order op
    if "orders" not in data:
        data["orders"] = []
    data["orders"].append(order)
    save_json(PRODUCTS_FILE, data)

    return {
        "success": True,
        "message": f"Bestelling #{order_id} geplaatst!",
        "order": order,
        "new_balance": wallets["wallets"][user_id]["balance"],
    }


@router.get("/orders/{user_id}")
async def get_orders(user_id: str):
    """Bestellingen van gebruiker ophalen"""
    data = load_json(PRODUCTS_FILE, default={"orders": []})
    orders = [o for o in data.get("orders", []) if o.get("user_id") == user_id]
    orders.sort(key=lambda o: o.get("created_at", ""), reverse=True)
    return {"success": True, "orders": orders}
