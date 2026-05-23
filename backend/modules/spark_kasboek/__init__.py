"""
v5_spark_kasboek_001 — Spark's eigen kasboek (geen bank, alleen afroming via shop).

Endpoints:
  GET /api/spark/kasboek/saldo      — huidig totaal + breakdown (btw_in/winst_in/uit)
  GET /api/spark/kasboek/entries    — laatste N entries
"""
from fastapi import APIRouter
from pathlib import Path
from modules.core.storage import load_json

router = APIRouter(prefix="/spark/kasboek", tags=["spark-kasboek"])

KB_PATH = Path(__file__).parent.parent.parent / "data" / "system" / "spark_kasboek.json"
WALLET_PATH = Path(__file__).parent.parent.parent / "data" / "wallet" / "wallets.json"


@router.get("/saldo")
async def saldo():
    kb = load_json(KB_PATH, default={"entries": [], "totals": {"btw_in": 0, "winst_in": 0, "uit": 0}})
    totals = kb.get("totals", {})
    saldo_total = round(totals.get("btw_in", 0) + totals.get("winst_in", 0) - totals.get("uit", 0), 4)
    # Tegelijkertijd huidige Spark EUR-wallet (voor cross-check)
    w = load_json(WALLET_PATH, default={"wallets": {}})
    spark_w = w.get("wallets", {}).get("user-000", {})
    return {
        "spark_kasboek_saldo_eur": saldo_total,
        "spark_wallet_balance_eur": round(spark_w.get("balance", 0), 4),
        "totals": totals,
        "n_entries": len(kb.get("entries", [])),
        "last_entry": (kb.get("entries") or [])[-1] if kb.get("entries") else None,
    }


@router.get("/entries")
async def entries(limit: int = 50):
    kb = load_json(KB_PATH, default={"entries": []})
    items = list(reversed(kb.get("entries", [])))[:limit]
    return {"entries": items, "total": len(kb.get("entries", []))}
