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


@router.get("/history")
async def history(limit: int = 100):
    """v6_spark_history_001 — Spark's complete transactie-papier:
    kasboek + ROAR transactions waar Spark bij betrokken is (mint/sale/btw)
    in chronologische volgorde met heldere labels.
    """
    from pathlib import Path as _P
    ROAR = _P(__file__).parent.parent.parent / "data" / "roar" / "roar_balances.json"
    kb = load_json(KB_PATH, default={"entries": []})
    roar = load_json(ROAR, default={"transactions": []})
    items = []
    # Kasboek
    for e in kb.get("entries", []):
        items.append({
            "ts": e.get("ts"),
            "type": e.get("type"),  # btw_afroming / spark_self_mint
            "label": ("📥 BTW binnen" if e.get("type") == "btw_afroming"
                      else "🪙 Token gemaakt" if e.get("type") == "spark_self_mint"
                      else e.get("type")),
            "amount_eur": e.get("bedrag_eur"),
            "n_tokens": e.get("n_tokens", 0),
            "description": e.get("omschrijving"),
            "bron_user": e.get("bron_user"),
            "source": "kasboek",
        })
    # ROAR transactions die Spark raken (verkopen uit treasury, mint, etc.)
    for t in roar.get("transactions", []):
        ttype = t.get("type")
        if ttype == "buy_roar":
            # Iemand kocht uit treasury → Spark "verkoopt" virtueel
            items.append({
                "ts": t.get("ts") or t.get("timestamp"),
                "type": "treasury_sale",
                "label": "🛒 Treasury verkoop",
                "amount_eur": t.get("total_eur") or t.get("amount_eur"),
                "n_tokens": -t.get("token_amount", 0),
                "description": f"{t.get('token_amount')} ROAR verkocht aan {t.get('user_id')} @ €{t.get('price_per_token')}",
                "bron_user": t.get("user_id"),
                "source": "roar",
            })
        elif ttype == "spark_self_mint":
            items.append({
                "ts": t.get("ts"),
                "type": "spark_self_mint",
                "label": "🪙 Self-mint",
                "amount_eur": -(t.get("cost_eur") or 0),
                "n_tokens": t.get("amount", 0),
                "description": t.get("description"),
                "bron_user": "user-000",
                "source": "roar",
            })
    # Sorteer nieuwste eerst
    items.sort(key=lambda x: x.get("ts") or "", reverse=True)
    return {"history": items[:limit], "total": len(items)}
