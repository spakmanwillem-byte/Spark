"""
v6_mint_from_wallet_001 — Spark "Maak Token" flow.

POST /api/spark/mint-from-wallet
Spark gebruikt zijn EUR-wallet om 1 token uit treasury naar zijn eigen balance te minten.
Effect: circulating +1, treasury -1, Spark EUR-wallet -price, audit + Boekhouder DM.

Conceptueel vastgelegd in /app/memory/MONEY_MODEL.md.
"""
from fastapi import APIRouter, HTTPException, Body
from pathlib import Path
from datetime import datetime, timezone
import uuid

from modules.core.storage import load_json, save_json

router = APIRouter(prefix="/spark/mint", tags=["spark-mint"])

DATA = Path(__file__).parent.parent.parent / "data"
ROAR_FILE = DATA / "roar" / "roar_balances.json"
WALLET_FILE = DATA / "wallet" / "wallets.json"
KASBOEK_FILE = DATA / "system" / "spark_kasboek.json"
AUDIT_FILE = DATA / "system" / "audit_log.json"


def _is_admin(user_id: str) -> bool:
    u = load_json(DATA / "system" / "users.json", default={"users": []})
    for x in u.get("users", []):
        if x.get("id") == user_id and (x.get("gradatie") or 7) <= 2:
            return True
    return False


@router.post("/from-wallet")
async def mint_from_wallet(payload: dict = Body(...)):
    """v6_mint_from_wallet_001 — Spark mint 1 token uit eigen EUR-wallet.

    Body: {"viewer_id": "user-001", "amount_tokens": 1}
    Alleen admin (gradatie ≤ 2) mag triggeren.
    """
    viewer_id = payload.get("viewer_id")
    if not viewer_id or not _is_admin(viewer_id):
        raise HTTPException(403, "Alleen admin kan Spark laten minten")
    n = max(1, int(payload.get("amount_tokens") or 1))

    # Price + Spark wallet
    from modules.shop.routes import get_dynamic_price
    price = get_dynamic_price()
    cost = round(price * n, 4)

    wallets = load_json(WALLET_FILE, default={"wallets": {}, "transactions": []})
    spark_w = wallets.get("wallets", {}).get("user-000", {"balance": 0, "tokens": 0})
    if spark_w.get("balance", 0) < cost:
        raise HTTPException(400, f"Onvoldoende Spark EUR-wallet (€{spark_w.get('balance',0):.2f}, nodig €{cost:.2f})")

    roar = load_json(ROAR_FILE, default={})
    treasury = roar.get("treasury_pool", 0)
    if treasury < n:
        raise HTTPException(400, f"Onvoldoende treasury (slechts {treasury} tokens)")

    # 51%-garantie check: Spark moet altijd ≥510k in treasury houden
    if treasury - n < 510000:
        raise HTTPException(400, "Mag niet onder 51% governance-garantie (510.000 tokens)")

    now = datetime.now(timezone.utc).isoformat()
    tx_id = uuid.uuid4().hex[:12]

    # 1. Treasury -n, Spark balance +n
    roar["treasury_pool"] = treasury - n
    roar["balances"]["user-000"] = roar.get("balances", {}).get("user-000", 0) + n
    roar.setdefault("transactions", []).append({
        "id": tx_id, "ts": now, "type": "spark_self_mint",
        "user_id": "user-000", "amount": n, "cost_eur": cost,
        "price_per_token": price,
        "description": f"Spark mint {n} ROAR uit eigen EUR-wallet @ €{price:.2f}",
    })
    save_json(ROAR_FILE, roar)

    # 2. Spark EUR-wallet -cost
    wallets["wallets"]["user-000"]["balance"] = round(spark_w["balance"] - cost, 4)
    wallets["wallets"]["user-000"]["tokens"] = roar["balances"]["user-000"]
    wallets.setdefault("transactions", []).append({
        "id": tx_id, "ts": now, "type": "spark_self_mint",
        "user_id": "user-000", "amount_eur": -cost, "tokens": n,
    })
    save_json(WALLET_FILE, wallets)

    # 3. Kasboek: outflow
    kb = load_json(KASBOEK_FILE, default={"entries": [], "totals": {"btw_in": 0, "winst_in": 0, "uit": 0}})
    kb["entries"].append({
        "id": uuid.uuid4().hex[:12], "ts": now,
        "type": "spark_self_mint", "bron_tx": tx_id,
        "bedrag_eur": -cost, "n_tokens": n,
        "omschrijving": f"Spark heeft {n} ROAR voor zichzelf gemint (@€{price:.2f}/stuk) — circulating +{n}",
    })
    kb["totals"]["uit"] = round(kb["totals"].get("uit", 0) + cost, 4)
    save_json(KASBOEK_FILE, kb)

    # 4. Audit
    audit = load_json(AUDIT_FILE, default={"entries": []})
    audit["entries"].append({
        "ts": now, "id": tx_id, "type": "spark_self_mint",
        "n_tokens": n, "cost_eur": cost, "price_per_token": price,
        "new_treasury": roar["treasury_pool"],
        "new_spark_balance": roar["balances"]["user-000"],
    })
    save_json(AUDIT_FILE, audit)

    # v6_mint_creates_potje_001 (28 mei) — Spark krijgt extra trade-slot potje per mint
    try:
        from modules.trade.potjes import sync_potjes_to_tokens, _load as _potjes_load
        # Spark heeft target_count = 5 + 10 = 15 (base + slots). Bij elke mint expanden we de slots-pool met n.
        # Direct expand: voeg n nieuwe pots toe aan Spark's pool
        data = _potjes_load("user-000")
        spark_data = data["users"]["user-000"]
        existing = spark_data.get("potjes", [])
        next_idx = max((p.get("index", i) for i, p in enumerate(existing)), default=-1) + 1
        for _ in range(n):
            existing.append({
                "id": f"pot-{next_idx+1:03d}",
                "index": next_idx,
                "capital": 10.0,
                "max_size": 50.0,
                "pot_locked": False,
                "lock_reason": None,
                "position": {"is_open": False, "entry_price": None, "highest_price": None,
                             "trailing_active": False, "entry_time": None},
                "market": "EUR",
                "assigned_market": None,
                "stats": {"trades": 0, "wins": 0, "losses": 0, "total_pnl": 0.0},
                "created_at": now,
                "last_action": None,
                "source": "spark_mint_bonus",
                "slot_type": "trade_slot_from_mint",
                "origin_tx": tx_id,
            })
            next_idx += 1
        spark_data["potjes"] = existing
        from modules.core.storage import save_json as _save
        _save(Path(__file__).parent.parent.parent / "data" / "financial" / "user_potjes.json", data)
        print(f"[mint] Spark kreeg {n} extra trade-slot potjes (totaal nu: {len(existing)})")
    except Exception as ex:
        print(f"[mint→potje] failed: {ex}")

    # 5. Boekhouder DM
    try:
        from modules.boekhouder import service as bh
        bh._send_dm(
            text=(
                f"🪙 **Spark heeft {n} ROAR gemaakt** uit eigen wallet.\n"
                f"• Kosten: €{cost:.2f}\n"
                f"• Treasury: {roar['treasury_pool']:,} (≥510k governance OK)\n"
                f"• Circulating +{n} → prijs stijgt voor alle holders\n"
                f"_Conceptueel vastgelegd in MONEY_MODEL.md_"
            ),
            kind="spark_self_mint",
            extra={"tx_id": tx_id, "n": n, "cost": cost},
            recipient_id="user-001",  # admin
        )
    except Exception as ex:
        print(f"[mint] Boekhouder DM failed: {ex}")

    return {
        "success": True,
        "tx_id": tx_id,
        "n_tokens": n,
        "cost_eur": cost,
        "price_per_token": price,
        "new_treasury": roar["treasury_pool"],
        "new_spark_balance": roar["balances"]["user-000"],
        "new_spark_eur_wallet": wallets["wallets"]["user-000"]["balance"],
    }
