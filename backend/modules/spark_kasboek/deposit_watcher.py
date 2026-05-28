"""
Deposit Watcher (v6_deposit_watcher_001 — 28 mei 2026)
==========================================================
Polls Bitvavo EUR-balance + compares with last_known. Als delta positief is
= storting binnen. Auto-update kasboek + verlaag open_commitment.

Triggers:
  • GET /api/spark/deposit-watcher/check (on-demand check)
  • Cron: 1× per uur (TODO: scheduler-koppeling)

State file: /data/system/deposit_watcher_state.json
"""
import json
from pathlib import Path
from datetime import datetime, timezone
from fastapi import APIRouter

from modules.core.storage import load_json, save_json

router = APIRouter(prefix="/spark/deposit-watcher", tags=["deposit-watcher"])

DATA = Path(__file__).parent.parent.parent / "data"
STATE_FILE = DATA / "system" / "deposit_watcher_state.json"
KASBOEK = DATA / "system" / "spark_kasboek.json"


def _get_current_bitvavo_eur(user_id: str = "user-001") -> float:
    """Lees actuele EUR-cash op Bitvavo via bitvavo_client."""
    try:
        from modules.trade.bitvavo_client import get_balance_summary
        s = get_balance_summary(user_id)
        return float(s.get("eur_cash", 0) or 0)
    except Exception as ex:
        print(f"[deposit-watcher] bitvavo fetch failed: {ex}")
        return 0.0


@router.get("/check")
async def check_deposits(user_id: str = "user-001"):
    """Vergelijk huidige Bitvavo EUR-cash met laatst gezien.
    Als hoger → storting → log in kasboek + return event.
    """
    now = datetime.now(timezone.utc).isoformat()
    current_eur = _get_current_bitvavo_eur(user_id)

    state = load_json(STATE_FILE, default={"last_known_eur": None, "history": []})
    last_known = state.get("last_known_eur")
    delta = 0.0
    event = None

    if last_known is not None:
        delta = round(current_eur - last_known, 2)
        if delta > 0.50:  # threshold: kleinere bewegingen = trade-resultaat
            # Storting gedetecteerd → log in echte accounting kasboek (spark_core)
            event = {
                "ts": now,
                "type": "deposit_detected",
                "delta_eur": delta,
                "previous_eur": last_known,
                "current_eur": current_eur,
                "user_id": user_id,
            }
            state.setdefault("history", []).append(event)
            # Voeg toe aan /api/accounting/transactions in spark_core kasboek
            try:
                from modules.accounting.routes import TX_FILE as ACC_TX
                import uuid
                acc_data = load_json(ACC_TX, default={"transactions": []})
                acc_data["transactions"].append({
                    "id": str(uuid.uuid4()),
                    "type": "income",
                    "category": "Donations",
                    "amount": delta,
                    "description": f"Storting auto-detect via deposit_watcher (Bitvavo EUR €{last_known:.2f}→€{current_eur:.2f})",
                    "entity_id": "spark_core",
                    "date": now,
                    "btw_percentage": 0,
                    "btw_amount": 0,
                    "created_at": now,
                    "source": "deposit_watcher",
                })
                save_json(ACC_TX, acc_data)
            except Exception as ex:
                print(f"[deposit-watcher] kasboek-log failed: {ex}")
        elif delta < -0.50:
            # Mogelijk uitname of trade
            event = {
                "ts": now,
                "type": "decrease_detected",
                "delta_eur": delta,
                "previous_eur": last_known,
                "current_eur": current_eur,
            }
            state.setdefault("history", []).append(event)

    state["last_known_eur"] = current_eur
    state["last_check_at"] = now
    save_json(STATE_FILE, state)

    # Recompute commitment-status
    try:
        from modules.spark_kasboek import _build_reconcile_report
        report = _build_reconcile_report()
        commitments = report.get("commitments", {})
    except Exception:
        commitments = {}

    return {
        "success": True,
        "current_bitvavo_eur": current_eur,
        "last_known_eur": last_known,
        "delta_eur": delta,
        "event": event,
        "commitments": commitments,
    }


@router.get("/state")
async def get_state():
    state = load_json(STATE_FILE, default={"last_known_eur": None, "history": []})
    return {"success": True, **state}
