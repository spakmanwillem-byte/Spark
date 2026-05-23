"""
v6_tijdelijke_lening_001 — Auto-resolve voor tijdelijke uithaal-leningen.

Wanneer Bitvavo-balance + winst genoeg is om de openstaande lening te dekken
(plus eventueel het verschil tussen verkoop en boekwaarde), wordt de lening
automatisch gesloten en potjes hersteld.

Endpoint:
  GET  /api/spark/leningen/open       — open leningen overzicht
  POST /api/spark/leningen/check      — handmatig check trigger (admin)
"""
from fastapi import APIRouter, HTTPException, Body
from pathlib import Path
from datetime import datetime, timezone
import uuid

from modules.core.storage import load_json, save_json

router = APIRouter(prefix="/spark/leningen", tags=["spark-leningen"])

DATA = Path(__file__).parent.parent.parent / "data"


def _check_and_resolve(viewer_id: str = "user-001") -> dict:
    """Check Bitvavo balance vs open leningen. Sluit als mogelijk."""
    kb = load_json(DATA / "system" / "spark_kasboek.json", default={"entries": [], "totals": {}})
    open_loans = [e for e in kb.get("entries", []) if e.get("type") == "tijdelijke_lening" and not e.get("resolved_at")]
    if not open_loans:
        return {"success": True, "resolved": 0, "message": "Geen openstaande leningen"}

    # Lees live Bitvavo balance
    try:
        from modules.trade.monitor import fetch_bitvavo_balance
        bv = fetch_bitvavo_balance(viewer_id)
        total_eur = bv.get("total_eur", 0) if bv.get("success") else 0
    except Exception:
        total_eur = 0

    # Lees pre-lening baseline (= deposits totaal voor user-001)
    deps = load_json(DATA / "trade" / "deposits.json", default={})
    baseline_eur = sum(d.get("amount_eur", 0) for d in deps.get("user-001", []))

    resolved = []
    for loan in open_loans:
        loan_eur = abs(loan.get("bedrag_eur", 0))
        n_potjes = abs(loan.get("n_tokens", 0))
        # Sluit als balance ≥ baseline (lening teruggestort)
        if total_eur >= baseline_eur - 5:  # 5 euro speling
            now = datetime.now(timezone.utc).isoformat()
            loan["resolved_at"] = now
            loan["resolved_balance_eur"] = total_eur
            loan["resolved_by"] = "auto_check"
            # Herstel potjes
            pots = load_json(DATA / "financial" / "user_potjes.json", default={"users": {}})
            user_id = loan.get("bron_user", "user-001")
            user_pots = pots.get("users", {}).get(user_id, {})
            for p in user_pots.get("potjes", []):
                if p.get("lening_id") == loan["id"]:
                    p["status"] = "open"
                    capital = p.get("capital", 5.08)
                    p["live_value"] = capital
                    p.pop("uitgehaald_op", None)
                    p.pop("uitgehaald_voor_eur", None)
                    p.pop("lening_id", None)
            user_pots["baseline_eur"] = sum(p.get("capital", 0) for p in user_pots.get("potjes", []))
            save_json(DATA / "financial" / "user_potjes.json", pots)
            # Kasboek totalen aanpassen
            kb["totals"]["open_leningen"] = round(kb["totals"].get("open_leningen", 0) - loan_eur, 4)
            kb["entries"].append({
                "id": uuid.uuid4().hex[:12],
                "ts": now,
                "type": "lening_resolved",
                "loan_id": loan["id"],
                "bron_user": user_id,
                "bedrag_eur": loan_eur,
                "n_tokens": n_potjes,
                "omschrijving": f"Lening €{loan_eur} gesloten — {n_potjes} potjes hersteld (Bitvavo balance €{total_eur:.2f} ≥ baseline €{baseline_eur:.2f})",
            })
            # v6_lening_resolve_accounting_001 — Accounting tegenboekingen
            try:
                tx_path = DATA / "accounting" / "transactions.json"
                acc = load_json(tx_path, default={"transactions": []})
                resolved_ref = f"lening-resolved-{loan['id']}"
                acc["transactions"].extend([
                    {"id": uuid.uuid4().hex[:12], "entity_id": "spark_core", "type": "expense", "category": "lening_voldaan", "amount": loan_eur, "description": "Vordering op Willem voldaan (terugstorting)", "date": now[:10], "reference": resolved_ref, "created_at": now},
                    {"id": uuid.uuid4().hex[:12], "entity_id": "spark_core", "type": "income", "category": "bitvavo_terug", "amount": loan_eur, "description": "Bitvavo balance hersteld door terugstorting", "date": now[:10], "reference": resolved_ref, "created_at": now},
                    {"id": uuid.uuid4().hex[:12], "entity_id": "personal_willem", "user_id": user_id, "type": "expense", "category": "schuld_voldaan", "amount": loan_eur, "description": "Schuld aan Spark voldaan", "date": now[:10], "reference": resolved_ref, "created_at": now},
                    {"id": uuid.uuid4().hex[:12], "entity_id": "personal_willem", "user_id": user_id, "type": "income", "category": "lening_terug", "amount": loan_eur, "description": "Lening teruggegeven aan Spark/Bitvavo", "date": now[:10], "reference": resolved_ref, "created_at": now},
                ])
                save_json(tx_path, acc)
            except Exception as ex:
                print(f"[lening-resolve-accounting] failed: {ex}")
            resolved.append({"loan_id": loan["id"], "eur": loan_eur, "potjes_hersteld": n_potjes})

    save_json(DATA / "system" / "spark_kasboek.json", kb)
    return {
        "success": True,
        "resolved": len(resolved),
        "open_loans_remaining": len([e for e in kb["entries"] if e.get("type") == "tijdelijke_lening" and not e.get("resolved_at")]),
        "live_bitvavo_eur": total_eur,
        "baseline_eur": baseline_eur,
        "details": resolved,
    }


@router.get("/open")
async def open_loans():
    kb = load_json(DATA / "system" / "spark_kasboek.json", default={"entries": []})
    open_l = [e for e in kb.get("entries", []) if e.get("type") == "tijdelijke_lening" and not e.get("resolved_at")]
    totaal = sum(abs(e.get("bedrag_eur", 0)) for e in open_l)
    return {"open_leningen": open_l, "totaal_eur": round(totaal, 4), "n": len(open_l)}


@router.post("/check")
async def check(payload: dict = Body(default={})):
    viewer_id = payload.get("viewer_id", "user-001")
    return _check_and_resolve(viewer_id)
