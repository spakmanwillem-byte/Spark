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


# ============================================================================
# v6_kasboek_reconcile_001 — discrepanties tussen ROAR-tx, wallets en kasboek
# ============================================================================

def _build_reconcile_report():
    """Vergelijk 3 bronnen:
      1. ROAR transactions (anchor_mint + buy_roar) → wat Spark MOET hebben ontvangen
      2. Spark kasboek totals.gift_in + omzet_in → wat geboekt is
      3. Wallets (Spark EUR-balance) → wat fysiek aanwezig is
    Spark zelf-mints/anchor van Spark (user-000) tellen NIET als gift binnen.
    """
    from pathlib import Path as _P
    ROAR = _P(__file__).parent.parent.parent / "data" / "roar" / "roar_balances.json"
    roar = load_json(ROAR, default={"transactions": []})
    kb = load_json(KB_PATH, default={"entries": [], "totals": {}})
    w = load_json(WALLET_PATH, default={"wallets": {}})

    # v6_commitments_001 (28 mei) — bereken Spark's openstaande potje-commitments
    # 15 potjes × €10 = €150 totaal toegezegd capital
    # 5 base bezet door Bitvavo (€50 al gedekt)
    # 10 trade-slots = €100 te storten/aanvullen
    pot_path = _P(__file__).parent.parent.parent / "data" / "financial" / "user_potjes.json"
    potjes = load_json(pot_path, default={"users": {}})
    spark_pots = potjes.get("users", {}).get("user-000", {}).get("potjes", [])
    commitments_total = sum(float(p.get("capital", 0) or 0) for p in spark_pots)
    bitvavo_covered = sum(float(p.get("capital", 0) or 0) for p in spark_pots if p.get("linked_bitvavo"))
    open_commitment = round(commitments_total - bitvavo_covered, 2)

    # 1. Som inkomsten uit ROAR transactions (anchor_mint + buy_roar) — exclusief Spark zelf
    expected_in = 0.0
    tx_records = []
    for t in roar.get("transactions", []):
        ttype = t.get("type")
        if ttype not in ("anchor_mint", "buy_roar"):
            continue
        user_id = t.get("user_id")
        if user_id == "user-000":  # Spark zelf-mint telt niet
            continue
        amt = t.get("amount_eur") or t.get("total_eur") or 0
        if not amt:
            continue
        expected_in += amt
        tx_records.append({
            "ts": t.get("ts") or t.get("timestamp"),
            "type": ttype,
            "user_id": user_id,
            "amount_eur": amt,
            "tokens": t.get("amount_tokens") or t.get("token_amount"),
            "tx_id": t.get("id"),
        })

    # 2. Som uitgaven uit ROAR (sell_back = users die tokens terug verkochten → uit kasboek)
    expected_out = 0.0
    out_records = []
    for t in roar.get("transactions", []):
        if t.get("type") in ("sell_back", "gift_refund_to_eur"):
            amt = t.get("amount_eur") or 0
            if amt:
                expected_out += amt
                out_records.append({
                    "ts": t.get("ts"),
                    "type": t.get("type"),
                    "amount_eur": amt,
                    "tokens": t.get("amount_tokens") or t.get("token_amount"),
                    "user_id": t.get("user_id"),
                    "tx_id": t.get("id"),
                    "note": t.get("note", ""),
                })

    # 3. Wat staat geboekt in kasboek
    totals = kb.get("totals", {})
    booked_in = (totals.get("gift_in", 0) or 0) + (totals.get("omzet_in", 0) or 0)
    booked_out = totals.get("uit", 0) or 0

    # 4. Welke ROAR-tx IDs zijn al in kasboek geboekt (via bron_tx)
    booked_tx_ids = {e.get("bron_tx") for e in kb.get("entries", []) if e.get("bron_tx")}
    unbooked = [r for r in tx_records if r["tx_id"] not in booked_tx_ids]
    unbooked_out = [r for r in out_records if r.get("tx_id") and r["tx_id"] not in booked_tx_ids]

    # 5. Spark EUR-wallet
    spark_w_eur = round(w.get("wallets", {}).get("user-000", {}).get("balance_eur",
                       w.get("wallets", {}).get("user-000", {}).get("balance", 0)) or 0, 2)

    return {
        "expected_in_eur": round(expected_in, 2),
        "expected_out_eur": round(expected_out, 2),
        "expected_net_eur": round(expected_in - expected_out, 2),
        "booked_in_eur": round(booked_in, 2),
        "booked_out_eur": round(booked_out, 2),
        "booked_net_eur": round(booked_in - booked_out, 2),
        "spark_wallet_eur": spark_w_eur,
        "discrepancy_in_eur": round(expected_in - booked_in, 2),
        "discrepancy_out_eur": round(expected_out - booked_out, 2),
        # Alleen positieve discrepanties zijn een probleem (missing booking).
        # Negative discrepancy_out = extra "uit" entries (loans, self-mint costs) — OK.
        "in_balance": (expected_in - booked_in) < 0.01 and len([r for r in tx_records if r["tx_id"] not in {e.get("bron_tx") for e in kb.get("entries", []) if e.get("bron_tx")}]) == 0,
        "unbooked_transactions": unbooked,
        "unbooked_out_transactions": unbooked_out,
        "out_transactions": out_records,
        "kasboek_totals": totals,
        # v6_commitments_001
        "commitments": {
            "spark_potjes_total_eur": round(commitments_total, 2),
            "bitvavo_covered_eur": round(bitvavo_covered, 2),
            "open_commitment_eur": open_commitment,
            "status": "rood" if open_commitment > 0 else "ok",
            "note": f"Spark heeft {len(spark_pots)} potjes (€{commitments_total:.2f} totaal). €{bitvavo_covered:.2f} gedekt door Bitvavo. €{open_commitment:.2f} nog te storten.",
        },
    }


@router.get("/reconcile")
async def kasboek_reconcile():
    """Toon discrepanties tussen ROAR-tx en kasboek."""
    return {"success": True, **_build_reconcile_report()}


@router.post("/reconcile/fix")
async def kasboek_reconcile_fix(viewer_id: str):
    """Retroactief alle unbooked ROAR-tx als gift_in/omzet_in toevoegen aan kasboek.
    Admin-only (gradatie ≤ 2). Idempotent — gebruikt bron_tx voor dedup.
    """
    from fastapi import HTTPException
    from datetime import datetime, timezone
    from modules.core.storage import save_json

    # Admin check
    USERS = Path(__file__).parent.parent.parent / "data" / "system" / "users.json"
    users = load_json(USERS, default={"users": []})
    ulist = users.get("users", []) if isinstance(users, dict) else users
    viewer = next((u for u in ulist if u.get("id") == viewer_id), None)
    if not viewer or int(viewer.get("gradatie", 7) or 7) > 2:
        raise HTTPException(403, "Alleen admin (gradatie ≤ 2) mag kasboek reconciliëren.")

    report = _build_reconcile_report()
    unbooked = report["unbooked_transactions"]
    unbooked_out = report.get("unbooked_out_transactions", [])
    if not unbooked and not unbooked_out:
        return {"success": True, "added": 0, "message": "Kasboek is al in balans.", "report": report}

    # Lees money phase
    phase_path = Path(__file__).parent.parent.parent / "data" / "system" / "money_phase.json"
    phase_data = load_json(phase_path, default={"phase": "build"})
    phase = phase_data.get("phase", "build")
    bucket = "gift_in" if phase == "build" else "omzet_in"

    kb = load_json(KB_PATH, default={"entries": [], "totals": {}})
    kb.setdefault("entries", [])
    kb.setdefault("totals", {})
    kb["totals"].setdefault(bucket, 0)
    kb["totals"].setdefault("uit", 0)

    added = 0
    total_added = 0.0
    total_uit = 0.0
    now = datetime.now(timezone.utc).isoformat()

    # Inboekingen
    for r in unbooked:
        amt = r["amount_eur"]
        entry = {
            "ts": r["ts"] or now,
            "type": bucket,
            "bedrag_eur": amt,
            "n_tokens": r.get("tokens"),
            "bron_user": r["user_id"],
            "bron_tx": r["tx_id"],
            "omschrijving": f"Reconcile: {r['type']} retroactief — {r.get('tokens','?')} ROAR voor €{amt} (user {r['user_id']})",
            "reconciled_by": viewer_id,
            "reconciled_at": now,
        }
        kb["entries"].append(entry)
        kb["totals"][bucket] = round(kb["totals"].get(bucket, 0) + amt, 4)
        added += 1
        total_added += amt

    # Uitboekingen (sell_back / refund)
    for r in unbooked_out:
        amt = r["amount_eur"]
        entry = {
            "ts": r["ts"] or now,
            "type": "uit_sell_back" if r["type"] == "sell_back" else "uit_refund",
            "bedrag_eur": amt,
            "n_tokens": r.get("tokens"),
            "bron_user": r.get("user_id"),
            "bron_tx": r["tx_id"],
            "omschrijving": f"Reconcile: {r['type']} retroactief — €{amt} uit ({r.get('note','')[:60]})",
            "reconciled_by": viewer_id,
            "reconciled_at": now,
        }
        kb["entries"].append(entry)
        kb["totals"]["uit"] = round(kb["totals"].get("uit", 0) + amt, 4)
        added += 1
        total_uit += amt

    save_json(KB_PATH, kb)
    new_report = _build_reconcile_report()
    return {
        "success": True,
        "added": added,
        "total_added_in_eur": round(total_added, 2),
        "total_added_uit_eur": round(total_uit, 2),
        "bucket": bucket,
        "phase": phase,
        "message": f"{added} transacties retroactief geboekt — €{total_added:.2f} {bucket} + €{total_uit:.2f} uit",
        "report": new_report,
    }



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
