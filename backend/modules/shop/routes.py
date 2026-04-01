"""
Shop Routes - Winkel items + token aankopen
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
from datetime import datetime, timezone
import uuid
from modules.core.storage import load_json, save_json

router = APIRouter(prefix="/shop", tags=["shop"])
DATA_DIR = Path(__file__).parent.parent.parent / "data"
WALLET_DIR = DATA_DIR / "wallet"

SHOP_ITEMS = [
    {"id": "custom-emoji", "naam": "Custom Emoji Slot", "prijs": 5, "type": "tokens", "categorie": "Personalisatie", "beschrijving": "Voeg een eigen emoji toe aan Spark", "beschikbaar": True},
    {"id": "kleur-thema", "naam": "Kleur Thema Pakket", "prijs": 8, "type": "tokens", "categorie": "Personalisatie", "beschrijving": "Unlock extra kleurthemas voor je dashboard", "beschikbaar": True},
    {"id": "priority-support", "naam": "Priority Support", "prijs": 3, "type": "tokens", "categorie": "Service", "beschrijving": "1 maand priority support van Spark", "beschikbaar": True},
    {"id": "extra-storage", "naam": "Extra Opslag (1GB)", "prijs": 4, "type": "tokens", "categorie": "Uitbreiding", "beschrijving": "Extra opslagruimte voor bestanden en data", "beschikbaar": True},
    {"id": "ai-boost", "naam": "AI Boost Module", "prijs": 15, "type": "tokens", "categorie": "Modules", "beschrijving": "Geavanceerde AI functies voor 30 dagen", "beschikbaar": False},
    {"id": "gift-card", "naam": "Gift Card (50 Credits)", "prijs": 2, "type": "tokens", "categorie": "Cadeau", "beschrijving": "Geef credits cadeau aan een andere gebruiker", "beschikbaar": True},
]


@router.get("/items")
async def get_shop_items():
    return {"items": SHOP_ITEMS}


@router.get("/balance/{user_id}")
async def get_token_balance(user_id: str):
    wallets = load_json(WALLET_DIR / "user_wallets.json", default={"user_wallets": {}})
    uw = wallets.get("user_wallets", {}).get(user_id, {})
    tokens = uw.get("wallet", {}).get("spark_tokens", 0)
    credits = uw.get("wallet", {}).get("credits", 0)
    return {"user_id": user_id, "spark_tokens": tokens, "credits": credits}


class PurchaseRequest(BaseModel):
    item_id: str


@router.post("/buy/{user_id}")
async def buy_item(user_id: str, req: PurchaseRequest):
    # Find item
    item = next((i for i in SHOP_ITEMS if i["id"] == req.item_id), None)
    if not item:
        return {"success": False, "error": "Item niet gevonden"}
    if not item["beschikbaar"]:
        return {"success": False, "error": "Item niet beschikbaar"}

    # Check balance
    wallets = load_json(WALLET_DIR / "user_wallets.json", default={"user_wallets": {}})
    uw = wallets.get("user_wallets", {}).get(user_id, {})
    wallet = uw.get("wallet", {})
    tokens = wallet.get("spark_tokens", 0)

    if tokens < item["prijs"]:
        return {"success": False, "error": f"Onvoldoende tokens. Je hebt {tokens}, nodig: {item['prijs']}"}

    # Deduct tokens
    wallet["spark_tokens"] = tokens - item["prijs"]
    uw["wallet"] = wallet
    wallets["user_wallets"][user_id] = uw

    # Add tokens back to Spark treasury
    spark = wallets.get("user_wallets", {}).get("spark_system", {})
    if spark.get("wallet"):
        spark["wallet"]["treasury_reserves"] = spark["wallet"].get("treasury_reserves", 0) + item["prijs"]
        spark["wallet"]["spark_tokens_circulating"] = max(0, spark["wallet"].get("spark_tokens_circulating", 0) - item["prijs"])
        wallets["user_wallets"]["spark_system"] = spark

    save_json(WALLET_DIR / "user_wallets.json", wallets)

    # Log purchase
    purchases_file = DATA_DIR / "shop" / "purchases.json"
    purchases_file.parent.mkdir(parents=True, exist_ok=True)
    purchases = load_json(purchases_file, default={"purchases": []})
    purchases["purchases"].append({
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "item_id": item["id"],
        "item_naam": item["naam"],
        "prijs": item["prijs"],
        "type": item["type"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    save_json(purchases_file, purchases)

    return {
        "success": True,
        "message": f"{item['naam']} gekocht voor {item['prijs']} tokens!",
        "new_balance": wallet["spark_tokens"],
        "item": item,
    }


@router.get("/purchases/{user_id}")
async def get_purchases(user_id: str):
    purchases = load_json(DATA_DIR / "shop" / "purchases.json", default={"purchases": []})
    user_purchases = [p for p in purchases["purchases"] if p["user_id"] == user_id]
    return {"purchases": user_purchases}
