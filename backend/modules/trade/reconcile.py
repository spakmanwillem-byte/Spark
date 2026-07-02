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


@router.post("/spark/sync-anchor/{coin}")
async def sync_anchor_to_bitvavo(coin: str):
    """
    Eén-klik-sync: pak de anchor-pot (pot_locked=True) voor deze coin en zet diens
    position.size + entry_price gelijk aan de echte Bitvavo-balance.
    Capital → 0 (geld zit in coin, niet meer cash).
    Audit-log per sync.
    """
    coin = coin.upper()
    pot_data = load_json(POTJES_FILE, default={"users": {}})
    spark = pot_data.get("users", {}).get(SPARK_USER)
    if not spark:
        raise HTTPException(404, "Spark gebruiker niet gevonden")

    # Vind anchor-pot voor deze coin (locked + matchende market)
    target = None
    for p in spark.get("potjes", []):
        market_coin = (p.get("market") or "").split("-")[0].upper()
        if market_coin == coin and p.get("pot_locked"):
            target = p
            break
    if not target:
        raise HTTPException(404, f"Geen anchor-pot (locked) gevonden voor {coin}")

    # Haal echte Bitvavo
    bv_result = fetch_bitvavo_balance(SPARK_USER)
    if not bv_result.get("success"):
        raise HTTPException(502, f"Bitvavo: {bv_result.get('error')}")
    bv_balances = {b.get("symbol", "").upper(): b for b in bv_result.get("balances", bv_result.get("data", []))}
    bv = bv_balances.get(coin) or {}
    actual_amount = float(bv.get("available", 0) or 0) + float(bv.get("in_order", 0) or 0)
    bv_price = float(bv.get("price", 0) or 0)
    if actual_amount <= 0:
        raise HTTPException(400, f"Bitvavo balance voor {coin} is 0 — niets te syncen")

    before = {"capital": target.get("capital"), "position": dict(target.get("position") or {})}
    target["capital"] = 0.0
    target["position"] = {
        "is_open": True,
        "entry_price": bv_price,
        "size": actual_amount,
        "highest_price": bv_price,
        "trailing_active": False,
    }
    audit = target.setdefault("reconcile_audit", [])
    audit.append({
        "ts": _now(),
        "action": "sync-anchor",
        "before": before,
        "after": {"capital": 0.0, "position": dict(target["position"])},
        "bv_price": bv_price,
        "actual_amount": actual_amount,
    })
    save_json(POTJES_FILE, pot_data)
    return {
        "success": True,
        "coin": coin,
        "pot_id": target.get("id"),
        "synced": {"size": actual_amount, "entry_price": bv_price, "eur_value": round(actual_amount * bv_price, 2)},
    }


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


# =============================================================================
# v7_reconcile_orphans_001 — Recover coins die op Bitvavo staan maar niet in pots.
#
# Achtergrond: fixed sell-bug (v7_zero_filled_guard_001) gaf ooit filled=0 als
# success terug, waardoor pots gesloten werden terwijl de crypto nog op Bitvavo
# stond. Dit endpoint scant per user het verschil en repareert:
#   - PnL positief   → SELL nu + registreer als winst in pot-stats en spark_kasboek
#   - PnL negatief   → heropen closed pot met correct entry-prijs zodat trader
#                      volgende cycle opnieuw kan proberen
#   - PnL ≈ 0 (dust) → skip; te klein om zinvol te reconciliëren
# =============================================================================
BITVAVO_FEE_RATE = 0.0025          # Bitvavo taker fee 0.25%
DUST_THRESHOLD_EUR = 0.10          # onder deze value: skip
TRADE_HISTORY_DIR = DATA_ROOT / "wallet" / "trade_history"


def _compute_net_paid_per_market(user_id: str) -> Dict[str, Dict[str, float]]:
    """Bereken per market: som(BUY.amount) - som(SELL.effective_amount * price).

    Returns: {market: {"total_buy_eur": X, "total_sell_eur": Y, "net_paid_eur": X-Y}}
    """
    fp = TRADE_HISTORY_DIR / f"{user_id}.json"
    if not fp.exists():
        return {}
    data = load_json(fp, default={"trades": []})
    per_market: Dict[str, Dict[str, float]] = {}
    for t in data.get("trades", []):
        if t.get("status") != "filled":
            continue
        m = t.get("market")
        if not m:
            continue
        row = per_market.setdefault(m, {"total_buy_eur": 0.0, "total_sell_eur": 0.0, "buys": 0, "sells": 0})
        action = (t.get("action") or "").upper()
        if action == "BUY":
            # amount voor BUY is in EUR (filled_quote)
            eur = float(t.get("amount", 0) or 0)
            row["total_buy_eur"] += eur
            row["buys"] += 1
        elif action == "SELL":
            # amount voor SELL is in coin (filled); waarde = filled × price
            coin_amount = float(t.get("amount", 0) or 0)
            px = float(t.get("price", 0) or 0)
            row["total_sell_eur"] += coin_amount * px
            row["sells"] += 1
    for m in per_market:
        per_market[m]["net_paid_eur"] = round(
            per_market[m]["total_buy_eur"] - per_market[m]["total_sell_eur"], 4
        )
    return per_market


@router.get("/orphans/{user_id}")
async def scan_orphans(user_id: str):
    """Dry-run: toon welke coins op Bitvavo geen matching open pot hebben en of
    verkopen winst zou opleveren.

    Response.rows[] bevat per coin:
      coin, bv_amount, bv_value_eur, cur_price_eur
      net_paid_eur      — historisch EUR uitgegeven aan deze market
      pnl_eur           — bv_value - net_paid
      pnl_after_fee_eur — bv_value × (1-fee) - net_paid
      proposed_action   — "SELL_PROFIT" | "REOPEN_POT" | "SKIP_DUST"
      matching_closed_pot — pot_id die vrij is voor dit coin
    """
    # 1. Bitvavo balance
    bv_result = fetch_bitvavo_balance(user_id)
    if not bv_result.get("success"):
        raise HTTPException(502, f"Bitvavo: {bv_result.get('error', 'onbekend')}")
    bv_balances = {b.get("symbol", "").upper(): b for b in bv_result.get("balances", [])}

    # 2. Per-market betaalgeschiedenis
    paid_per_market = _compute_net_paid_per_market(user_id)

    # 3. User's pots (om closed pot te matchen)
    pot_data = load_json(POTJES_FILE, default={"users": {}})
    user_pots = pot_data.get("users", {}).get(user_id, {}).get("potjes", [])
    closed_pots_by_market: Dict[str, List[str]] = {}
    for p in user_pots:
        if not p.get("position", {}).get("is_open"):
            m = p.get("market", "")
            closed_pots_by_market.setdefault(m, []).append(p.get("id"))

    rows = []
    for coin, b in bv_balances.items():
        if coin == "EUR":
            continue
        avail = float(b.get("available", 0) or 0)
        cur_val = float(b.get("value_eur", 0) or 0)
        cur_price = float(b.get("price", 0) or 0)
        if avail <= 0 or cur_val < DUST_THRESHOLD_EUR:
            continue
        market = f"{coin}-EUR"
        paid = paid_per_market.get(market, {})
        net_paid = paid.get("net_paid_eur", 0.0)
        pnl = round(cur_val - net_paid, 4)
        pnl_after_fee = round(cur_val * (1 - BITVAVO_FEE_RATE) - net_paid, 4)

        # Bepaal actie
        if pnl_after_fee >= 0.01:
            action = "SELL_PROFIT"
        elif abs(pnl_after_fee) < 0.02:  # binnen 2 cent → dust
            action = "SKIP_DUST"
        else:
            action = "REOPEN_POT"

        matching = closed_pots_by_market.get(market, [])
        rows.append({
            "coin": coin,
            "market": market,
            "bv_amount": round(avail, 8),
            "bv_value_eur": round(cur_val, 2),
            "cur_price_eur": round(cur_price, 6),
            "total_buy_eur": round(paid.get("total_buy_eur", 0), 2),
            "total_sell_eur": round(paid.get("total_sell_eur", 0), 2),
            "net_paid_eur": round(net_paid, 2),
            "pnl_eur": pnl,
            "pnl_after_fee_eur": pnl_after_fee,
            "proposed_action": action,
            "matching_closed_pot": matching[0] if matching else None,
            "closed_pots_available": len(matching),
        })

    return {
        "success": True,
        "user_id": user_id,
        "rows": sorted(rows, key=lambda r: -r["pnl_after_fee_eur"]),
        "totals": {
            "potential_profit_eur": round(sum(r["pnl_after_fee_eur"] for r in rows if r["proposed_action"] == "SELL_PROFIT"), 2),
            "underwater_positions_eur": round(sum(r["pnl_after_fee_eur"] for r in rows if r["proposed_action"] == "REOPEN_POT"), 2),
            "coins_to_sell": sum(1 for r in rows if r["proposed_action"] == "SELL_PROFIT"),
            "coins_to_reopen": sum(1 for r in rows if r["proposed_action"] == "REOPEN_POT"),
            "coins_skipped": sum(1 for r in rows if r["proposed_action"] == "SKIP_DUST"),
        },
        "note": "Dry-run — geen wijzigingen doorgevoerd. Gebruik POST om uit te voeren.",
        "ts": _now(),
    }


class RecoverOrphansRequest(BaseModel):
    only_profit: bool = False   # als true: alleen SELL_PROFIT acties uitvoeren, geen REOPEN
    coins: Optional[List[str]] = None  # subset, bijv. ["BCH","ETH"] — None = alle


@router.post("/orphans/{user_id}")
async def recover_orphans(user_id: str, req: RecoverOrphansRequest):
    """Execute reconcile: verkoop coins met winst, heropen pots voor coins met verlies.

    Body:
      only_profit: bool — als true, alleen verkopen bij winst (skip REOPEN acties)
      coins: List[str] — beperk tot deze coins, of leeg voor alle
    """
    from .monitor import execute_real_trade
    from . import potjes as potjes_svc

    # Doe eerst scan
    scan = await scan_orphans(user_id)
    rows = scan["rows"]

    if req.coins:
        want = {c.upper() for c in req.coins}
        rows = [r for r in rows if r["coin"] in want]

    executed = []
    skipped = []
    errors = []

    for r in rows:
        coin = r["coin"]
        market = r["market"]
        action = r["proposed_action"]

        if action == "SKIP_DUST":
            skipped.append({"coin": coin, "reason": "dust (<€0.10 PnL)"})
            continue

        if action == "REOPEN_POT":
            if req.only_profit:
                skipped.append({"coin": coin, "reason": "only_profit=True, verlies-pot skipped"})
                continue
            # Heropen matching closed pot met historische entry
            pot_id = r["matching_closed_pot"]
            if not pot_id:
                errors.append({"coin": coin, "error": "geen closed pot beschikbaar om te heropen"})
                continue
            pot_data = load_json(POTJES_FILE, default={"users": {}})
            target = None
            for p in pot_data.get("users", {}).get(user_id, {}).get("potjes", []):
                if p.get("id") == pot_id:
                    target = p
                    break
            if not target:
                errors.append({"coin": coin, "error": f"pot {pot_id} niet gevonden"})
                continue
            avg_entry = round(r["net_paid_eur"] / r["bv_amount"], 6) if r["bv_amount"] > 0 else r["cur_price_eur"]
            target["market"] = market
            target["position"] = {
                "is_open": True,
                "entry_price": avg_entry,
                "size": r["bv_amount"],
                "highest_price": max(avg_entry, r["cur_price_eur"]),
                "trailing_active": False,
                "entry_time": _now(),
            }
            audit = target.setdefault("reconcile_audit", [])
            audit.append({
                "ts": _now(),
                "action": "reopen_orphan",
                "reason": f"Orphaned {coin} balance reconciled — trader neemt over",
                "avg_entry_price": avg_entry,
                "size": r["bv_amount"],
                "net_paid_eur": r["net_paid_eur"],
            })
            save_json(POTJES_FILE, pot_data)
            executed.append({"coin": coin, "action": "REOPENED", "pot_id": pot_id,
                             "entry_price": avg_entry, "size": r["bv_amount"]})
            continue

        # SELL_PROFIT — verkoop nu, registreer als winst
        if action == "SELL_PROFIT":
            # 1. Bepaal target pot om winst in te boeken (matching closed pot of eerste vrije)
            pot_id = r["matching_closed_pot"]
            pot_data = load_json(POTJES_FILE, default={"users": {}})
            user_pots_list = pot_data.get("users", {}).get(user_id, {}).get("potjes", [])
            target = None
            for p in user_pots_list:
                if p.get("id") == pot_id:
                    target = p
                    break
            if not target:
                # Fallback: pak eerste closed pot
                for p in user_pots_list:
                    if not p.get("position", {}).get("is_open"):
                        target = p
                        break
            if not target:
                errors.append({"coin": coin, "error": "geen pot beschikbaar om winst in te boeken"})
                continue

            # 2. Tijdelijk pot als "open" markeren met de historische entry, dan close_pot() aanroepen
            #    Dit zorgt dat close_pot de netto-berekening + stats + kasboek-update correct doet.
            avg_entry = round(r["net_paid_eur"] / r["bv_amount"], 6) if r["bv_amount"] > 0 else r["cur_price_eur"]
            target["market"] = market
            target["capital"] = round(r["net_paid_eur"], 4)  # correcte inleg voor P&L
            target["position"] = {
                "is_open": True,
                "entry_price": avg_entry,
                "size": r["bv_amount"],
                "highest_price": max(avg_entry, r["cur_price_eur"]),
                "trailing_active": True,
                "entry_time": _now(),
            }
            save_json(POTJES_FILE, pot_data)

            # 3. Execute REAL sell op Bitvavo — met de nieuwe ZERO_FILLED guard
            #    execute_real_trade verwacht amount_eur (voor SELL wordt dit intern
            #    geclamped naar coin balance). We geven de coin-value in EUR mee.
            sell_result = execute_real_trade(user_id, market, "SELL", r["bv_value_eur"])
            if not sell_result.get("success"):
                # Sell mislukt — laat pot open zodat trader het volgende cycle probeert
                errors.append({
                    "coin": coin, "error": sell_result.get("error"),
                    "error_code": sell_result.get("error_code"),
                    "action": "pot blijft open voor trader-retry",
                })
                continue

            # 4. Success — call close_pot voor nette registratie in stats + kasboek
            real_price = sell_result.get("trade", {}).get("price") or r["cur_price_eur"]
            close_result = potjes_svc.close_pot(user_id, target["id"], real_price)
            executed.append({
                "coin": coin, "action": "SOLD",
                "pot_id": target["id"],
                "sold_at_price": real_price,
                "netto_profit_eur": close_result.get("netto", 0),
                "trade_id": sell_result.get("trade", {}).get("trade_id"),
            })

    return {
        "success": True,
        "user_id": user_id,
        "executed": executed,
        "skipped": skipped,
        "errors": errors,
        "summary": {
            "sold": sum(1 for e in executed if e["action"] == "SOLD"),
            "reopened": sum(1 for e in executed if e["action"] == "REOPENED"),
            "total_netto_profit_eur": round(sum(e.get("netto_profit_eur", 0) for e in executed if e["action"] == "SOLD"), 2),
        },
        "ts": _now(),
    }
