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
    kb = load_json(KB_PATH, default={"entries": [], "totals": {}})
    totals = kb.get("totals", {})
    gift_in = totals.get("gift_in", 0)
    omzet_in = totals.get("omzet_in", 0)
    btw_reserve = totals.get("btw_reserve", 0)
    winst_in = totals.get("winst_in", 0)
    uit = totals.get("uit", 0)
    saldo_total = round(gift_in + omzet_in + winst_in - uit, 4)
    vrij = round(saldo_total - btw_reserve, 4)
    # Lees huidige fase
    from pathlib import Path as _P
    phase_path = _P(__file__).parent.parent.parent / "data" / "system" / "money_phase.json"
    phase_data = load_json(phase_path, default={"phase": "build"})
    w = load_json(WALLET_PATH, default={"wallets": {}})
    spark_w = w.get("wallets", {}).get("user-000", {})
    return {
        "spark_kasboek_saldo_eur": saldo_total,
        "vrij_te_besteden_eur": vrij,
        "gift_in_eur": gift_in,
        "omzet_in_eur": omzet_in,
        "btw_reserve_eur": btw_reserve,
        "spark_wallet_balance_eur": round(spark_w.get("balance", 0), 4),
        "totals": totals,
        "money_phase": phase_data.get("phase", "build"),
        "n_entries": len(kb.get("entries", [])),
        "last_entry": (kb.get("entries") or [])[-1] if kb.get("entries") else None,
    }


@router.get("/price-history")
async def price_history(interval: str = "1h", limit: int = 50):
    """v6_price_history_001 — bucket prijs uit alle buy_roar transactions.
    Returns 2 lines: price_incl (klant-prijs) + price_netto (Spark's deel zonder BTW).
    interval: 15m / 1h / 4h / 1d
    """
    from pathlib import Path as _P
    from datetime import datetime, timezone, timedelta
    ROAR = _P(__file__).parent.parent.parent / "data" / "roar" / "roar_balances.json"
    roar = load_json(ROAR, default={"transactions": []})

    minutes = {"15m": 15, "1h": 60, "4h": 240, "1d": 1440}.get(interval, 60)
    buckets = {}
    ANCHOR = {"user-000", "user-001"}
    for t in roar.get("transactions", []):
        if t.get("type") != "buy_roar":
            continue
        ts_str = t.get("ts") or t.get("timestamp")
        if not ts_str:
            continue
        try:
            dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        except Exception:
            continue
        # Round down to bucket
        epoch_min = int(dt.timestamp() / 60)
        bucket_min = (epoch_min // minutes) * minutes
        bucket_ts = datetime.fromtimestamp(bucket_min * 60, tz=timezone.utc).isoformat()
        price_incl = t.get("price_per_token") or 0
        is_klant = t.get("user_id") not in ANCHOR
        # Anker-aankoop: incl == netto (geen BTW). Klant: netto = incl * 100/121
        price_netto = round(price_incl * 100 / 121, 4) if is_klant else price_incl
        b = buckets.setdefault(bucket_ts, {"ts": bucket_ts, "price_incl": price_incl, "price_netto": price_netto, "n": 0})
        b["price_incl"] = max(b["price_incl"], price_incl)
        b["price_netto"] = max(b["price_netto"], price_netto)
        b["n"] += 1
    series = sorted(buckets.values(), key=lambda x: x["ts"])[-limit:]
    return {"interval": interval, "points": series, "total": len(series)}


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
        etype = e.get("type")
        label = (
            "💚 Gift binnen" if etype == "gift_in"
            else "💰 Klant-omzet" if etype == "klant_omzet"
            else "📥 BTW binnen" if etype == "btw_afroming"  # legacy
            else "💚 Winst trade" if etype == "trade_winst"
            else "📒 BTW reservering" if etype == "btw_reserve"
            else "🪙 Token gemaakt" if etype == "spark_self_mint"
            else etype or "?"
        )
        items.append({
            "ts": e.get("ts"),
            "type": etype,
            "label": label,
            "amount_eur": e.get("bedrag_eur"),
            "n_tokens": e.get("n_tokens", 0),
            "description": e.get("omschrijving"),
            "bron_user": e.get("bron_user"),
            "source": "kasboek",
        })
    # ROAR transactions die Spark raken (verkopen uit treasury, mint, etc.)
    # v6_dedup_treasury_001 — skip treasury_sale als ook getoond als gift_in/klant_omzet (zelfde tx)
    seen_tx_ids = {e.get("bron_tx") for e in kb.get("entries", []) if e.get("bron_tx")}
    for t in roar.get("transactions", []):
        ttype = t.get("type")
        if ttype == "buy_roar":
            if t.get("id") in seen_tx_ids:
                continue
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
        elif ttype == "anchor_mint":
            items.append({
                "ts": t.get("ts") or t.get("timestamp"),
                "type": "anchor_mint",
                "label": "⚓ Anker-mint",
                "amount_eur": t.get("total_eur") or t.get("amount_eur"),
                "n_tokens": t.get("token_amount", 0),
                "description": t.get("description") or f"Anker {t.get('user_id')} kreeg {t.get('token_amount')} ROAR @ €{t.get('price_per_token')}",
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
