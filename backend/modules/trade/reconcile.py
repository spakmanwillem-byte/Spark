"""
v6_reconcile_001 — Reconciliation: vergelijk potje-saldo met echte Bitvavo-balance.

Alleen voor Spark (user-000) — community-pool met 1 Bitvavo-account.
Andere users traden via Spark's proxy, dus hun potjes zijn virtueel — geen reconciliatie nodig.

Endpoints:
  GET  /api/trade/reconcile/spark        — toon per coin: potje vs Bitvavo, diff
  POST /api/trade/reconcile/spark/fix    — body {pot_id, new_capital, new_position_size?}
                                            past potje aan om bij Bitvavo te kloppen
"""
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..core.storage import load_json, save_json
from .monitor import fetch_bitvavo_balance

router = APIRouter(prefix="/trade/reconcile", tags=["trade-reconcile"])

DATA_ROOT = Path(__file__).parent.parent.parent / "data"
POTJES_FILE = DATA_ROOT / "financial" / "user_potjes.json"
SPARK_USER = "user-000"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _base_coin(market: str) -> str:
    """BCH-EUR → BCH."""
    return (market or "").split("-")[0].upper()


@router.get("/spark")
async def reconcile_spark():
    """
    Voor Spark (user-000): per coin → potje-totaal vs werkelijke Bitvavo-balance.
    Resultaat: per coin een rij met expected/actual/diff/status.
    """
    # 1. Spark's potjes ophalen
    pot_data = load_json(POTJES_FILE, default={"users": {}})
    spark = pot_data.get("users", {}).get(SPARK_USER, {})
    pots = spark.get("potjes", [])

    # 2. Bitvavo live balance
    bv_result = fetch_bitvavo_balance(SPARK_USER)
    if not bv_result.get("success"):
        raise HTTPException(502, f"Bitvavo: {bv_result.get('error', 'onbekend')}")

    # bal: list of {symbol, available, in_order, eur_value, price, ...}
    bv_balances = {b.get("symbol", "").upper(): b for b in bv_result.get("balances", bv_result.get("data", []))}

    # 3. Groepeer potjes per coin
    per_coin: Dict[str, List[Dict]] = {}
    for p in pots:
        coin = _base_coin(p.get("market", ""))
        if not coin:
            continue
        per_coin.setdefault(coin, []).append(p)

    rows = []
    for coin, lst in sorted(per_coin.items()):
        # Expected: som van capital (free) + open posities (size × price)
        expected_eur_free = 0.0
        expected_coin_amount = 0.0
        n_locked = 0
        n_open = 0
        for p in lst:
            pos = p.get("position") or {}
            if pos.get("is_open"):
                size = float(pos.get("size", 0) or 0)
                expected_coin_amount += size
                n_open += 1
            else:
                # Vrij potje = EUR die niet in coin zit
                expected_eur_free += float(p.get("capital", 0) or 0)
            if p.get("pot_locked"):
                n_locked += 1

        # Actual Bitvavo
        bv = bv_balances.get(coin) or {}
        actual_coin_amount = float(bv.get("available", 0) or 0) + float(bv.get("in_order", 0) or 0)
        bv_price = float(bv.get("price", 0) or 0)
        actual_eur_value = actual_coin_amount * bv_price

        # Diff
        diff_coin = actual_coin_amount - expected_coin_amount
        diff_eur = actual_eur_value - (expected_coin_amount * bv_price)

        # Status
        if abs(diff_coin) < 1e-8:
            status = "exact"
        elif diff_coin > 0:
            status = "overschot"   # meer op Bitvavo dan potjes denken
        else:
            status = "tekort"      # potjes denken meer te hebben dan werkelijk

        rows.append({
            "coin": coin,
            "n_pots": len(lst),
            "n_open": n_open,
            "n_locked": n_locked,
            "expected_eur_free": round(expected_eur_free, 2),
            "expected_coin_amount": round(expected_coin_amount, 8),
            "actual_coin_amount": round(actual_coin_amount, 8),
            "bv_price_eur": round(bv_price, 6),
            "actual_eur_value": round(actual_eur_value, 2),
            "diff_coin": round(diff_coin, 8),
            "diff_eur": round(diff_eur, 2),
            "status": status,
        })

    return {"success": True, "user_id": SPARK_USER, "rows": rows, "ts": _now()}


class FixPotReq(BaseModel):
    pot_id: str
    new_capital: Optional[float] = None
    new_position_size: Optional[float] = None
    new_entry_price: Optional[float] = None
    note: Optional[str] = ""


@router.post("/spark/fix")
async def fix_spark_pot(req: FixPotReq):
    """
    Handmatig potje-saldo aanpassen om overeen te komen met Bitvavo-werkelijkheid.
    Audit-log per fix: wie/wanneer/wat veranderd is.
    """
    pot_data = load_json(POTJES_FILE, default={"users": {}})
    spark = pot_data.get("users", {}).get(SPARK_USER)
    if not spark:
        raise HTTPException(404, "Spark gebruiker niet gevonden")
    pots = spark.get("potjes", [])
    target = next((p for p in pots if p.get("id") == req.pot_id), None)
    if not target:
        raise HTTPException(404, f"Pot {req.pot_id} niet gevonden")

    before = {
        "capital": target.get("capital"),
        "position": dict(target.get("position") or {}),
    }
    if req.new_capital is not None:
        target["capital"] = float(req.new_capital)
    if req.new_position_size is not None:
        target.setdefault("position", {})
        target["position"]["size"] = float(req.new_position_size)
        target["position"]["is_open"] = float(req.new_position_size) > 0
    if req.new_entry_price is not None:
        target.setdefault("position", {})
        target["position"]["entry_price"] = float(req.new_entry_price)

    # Audit
    audit = target.setdefault("reconcile_audit", [])
    audit.append({
        "ts": _now(),
        "before": before,
        "after": {
            "capital": target.get("capital"),
            "position": dict(target.get("position") or {}),
        },
        "note": req.note or "",
    })

    save_json(POTJES_FILE, pot_data)
    return {"success": True, "pot_id": req.pot_id, "after": {
        "capital": target.get("capital"),
        "position": target.get("position"),
    }}
