"""
v6_staking_growth_engine_001 (sessie 14, 29 mei 2026)
Spark's anchors zijn nu statisch — dit module maakt ze actief:

  1. auto-rente   — maandelijks X% van overflow_pool → anchor.capital groei
  2. auto-mint    — bij overflow_pool >= MINT_THRESHOLD: nieuw trade-potje minten
  3. auto-anchor  — bij toevoegen nieuwe coin aan watch: auto-create base-anchor (Spark only)

Endpoints (admin-only):
  POST /api/trade/growth/run            — handmatig 1 cyclus draaien (test)
  GET  /api/trade/growth/status         — wanneer laatst, wat zou nu gebeuren
  POST /api/trade/growth/auto-anchor    — voeg coin toe + maak anchor

Scheduler-hook draait dit 1x per dag op 00:05.
"""
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List
import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from modules.core.storage import load_json, save_json

router = APIRouter(prefix="/trade/growth", tags=["staking-growth"])

# Tunables
RENTE_PCT_PER_MAAND = 1.5     # 1.5% per anchor per maand
MINT_THRESHOLD = 10.0          # bij €10 overflow → nieuw potje
RENTE_INTERVAL_HOURS = 720     # 30 dagen
SPARK_USER = "user-000"
ANCHOR_COINS_DEFAULT = ["ADA", "BCH", "BTC", "ETH", "SOL"]

DATA = Path(__file__).parent.parent.parent / "data"
POTJES_FILE = DATA / "financial" / "user_potjes.json"
GROWTH_STATE = DATA / "trade" / "growth_state.json"
USERS_FILE = DATA / "system" / "users.json"


def _is_admin(viewer_id: str) -> bool:
    users = load_json(USERS_FILE, default={"users": []})
    ulist = users.get("users", []) if isinstance(users, dict) else users
    u = next((x for x in ulist if x.get("id") == viewer_id), None)
    return bool(u and int(u.get("gradatie", 7) or 7) <= 2)


# ============================================================
# Core engine
# ============================================================
def run_growth_cycle(force: bool = False) -> Dict:
    """Hoofd-routine. Voert auto-rente + auto-mint uit voor Spark.
    Idempotent op rente (alleen 1× per RENTE_INTERVAL_HOURS).
    """
    now = datetime.now(timezone.utc)
    state = load_json(GROWTH_STATE, default={})
    last_rente_str = state.get("last_rente_run")
    actions = []

    # --- 1. AUTO-RENTE ---
    do_rente = force
    if not do_rente and last_rente_str:
        try:
            last = datetime.fromisoformat(last_rente_str.replace("Z", "+00:00"))
            if (now - last) >= timedelta(hours=RENTE_INTERVAL_HOURS):
                do_rente = True
        except Exception:
            do_rente = True
    elif not last_rente_str:
        do_rente = True

    data = load_json(POTJES_FILE, default={"users": {}})
    spark = data.get("users", {}).get(SPARK_USER)
    if not spark:
        return {"success": False, "error": "Spark user (user-000) niet gevonden"}

    overflow = float(spark.get("overflow_pool", 0))
    anchors = [p for p in spark.get("potjes", []) if p.get("pot_locked") and p.get("lock_reason") == "staking_anchor"]

    if do_rente and overflow > 0 and anchors:
        # Verdeel rente over anchors gelijkmatig
        total_rente_pct = RENTE_PCT_PER_MAAND / 100 * len(anchors)
        max_uit_overflow = round(overflow * total_rente_pct, 4)
        per_anchor = round(max_uit_overflow / len(anchors), 4)
        if per_anchor > 0:
            for a in anchors:
                a["capital"] = round((a.get("capital") or 10.0) + per_anchor, 4)
                a.setdefault("growth_log", []).append({
                    "ts": now.isoformat(), "type": "rente",
                    "amount": per_anchor, "source": "overflow_pool",
                })
                actions.append({
                    "type": "rente", "pot_id": a["id"],
                    "amount": per_anchor, "new_capital": a["capital"],
                })
            spark["overflow_pool"] = round(overflow - max_uit_overflow, 4)
            state["last_rente_run"] = now.isoformat()

    # --- 2. AUTO-MINT (overflow >= threshold) ---
    overflow = float(spark.get("overflow_pool", 0))
    minted = []
    while overflow >= MINT_THRESHOLD:
        # Maak nieuw trade-potje
        existing = spark.get("potjes", [])
        next_idx = max((p.get("index", 0) for p in existing), default=-1) + 1
        new_pot = {
            "id": f"pot-{next_idx + 1:03d}",
            "index": next_idx,
            "nummer": next_idx + 1,
            "capital": 10.0,
            "max_size": 50.0,
            "pot_locked": False,
            "lock_reason": None,
            "market": "EUR",  # nog niet toegewezen
            "position": {"is_open": False, "entry_price": None, "highest_price": None,
                         "trailing_active": False, "entry_time": None, "amount_eur": None},
            "stats": {"trades": 0, "wins": 0, "losses": 0, "total_pnl": 0.0},
            "trade_log": [],
            "minted_at": now.isoformat(),
            "minted_from": "overflow_auto_mint",
            "last_action": "Auto-minted from overflow_pool",
        }
        existing.append(new_pot)
        spark["overflow_pool"] = round(overflow - MINT_THRESHOLD, 4)
        overflow = spark["overflow_pool"]
        minted.append(new_pot["id"])
        actions.append({"type": "mint", "pot_id": new_pot["id"], "amount": MINT_THRESHOLD})

    save_json(POTJES_FILE, data)
    save_json(GROWTH_STATE, state)

    return {
        "success": True,
        "ran_at": now.isoformat(),
        "rente_applied": do_rente and bool(actions),
        "minted_pots": minted,
        "actions": actions,
        "overflow_after": spark.get("overflow_pool", 0),
        "anchors_count": len(anchors),
    }


def auto_create_anchor(coin: str) -> Optional[Dict]:
    """Maak een staking-anchor voor coin (alleen voor Spark).
    Hergebruikt een bestaand vrij EUR-potje als anchor of mint een nieuw potje.
    """
    coin = coin.upper().strip()
    if not coin:
        return None
    data = load_json(POTJES_FILE, default={"users": {}})
    spark = data.get("users", {}).get(SPARK_USER)
    if not spark:
        return None
    # Skip als anchor al bestaat
    for p in spark.get("potjes", []):
        if p.get("pot_locked") and p.get("market") == f"{coin}-EUR":
            return {"skipped": True, "reason": "anchor exists", "pot_id": p["id"]}
    # Vind eerste vrije EUR potje
    free = next((p for p in spark["potjes"]
                 if not p.get("pot_locked") and not p.get("position", {}).get("is_open")
                 and p.get("market") == "EUR"), None)
    now = datetime.now(timezone.utc).isoformat()
    if free:
        free["market"] = f"{coin}-EUR"
        free["pot_locked"] = True
        free["lock_reason"] = "staking_anchor"
        free["capital"] = 10.0
        free["last_action"] = f"Auto-anchored to {coin}"
        free["anchored_at"] = now
        save_json(POTJES_FILE, data)
        return {"created": True, "pot_id": free["id"], "market": f"{coin}-EUR", "source": "free_pot"}
    # Geen vrije EUR — mint nieuw potje als anchor
    existing = spark["potjes"]
    next_idx = max((p.get("index", 0) for p in existing), default=-1) + 1
    new_pot = {
        "id": f"pot-{next_idx + 1:03d}",
        "index": next_idx, "nummer": next_idx + 1,
        "capital": 10.0, "max_size": 50.0,
        "pot_locked": True, "lock_reason": "staking_anchor",
        "market": f"{coin}-EUR",
        "position": {"is_open": False, "entry_price": None, "highest_price": None,
                     "trailing_active": False, "entry_time": None, "amount_eur": None},
        "stats": {"trades": 0, "wins": 0, "losses": 0, "total_pnl": 0.0},
        "trade_log": [],
        "anchored_at": now,
        "last_action": f"Auto-minted as {coin} anchor",
    }
    existing.append(new_pot)
    save_json(POTJES_FILE, data)
    return {"created": True, "pot_id": new_pot["id"], "market": f"{coin}-EUR", "source": "newly_minted"}


# ============================================================
# Endpoints
# ============================================================
class RunRequest(BaseModel):
    viewer_id: str
    force: bool = False


class AnchorRequest(BaseModel):
    viewer_id: str
    coin: str


@router.post("/run")
async def run_endpoint(req: RunRequest):
    """Forceer 1 cyclus (admin-only). force=true negeert de 30-dag rente-interval."""
    if not _is_admin(req.viewer_id):
        raise HTTPException(403, "Alleen admin (gradatie ≤ 2)")
    return run_growth_cycle(force=req.force)


@router.get("/status")
async def status_endpoint():
    """Wanneer is laatste run geweest + huidige overflow + simulatie wat 'force run' zou doen."""
    state = load_json(GROWTH_STATE, default={})
    data = load_json(POTJES_FILE, default={"users": {}})
    spark = data.get("users", {}).get(SPARK_USER, {})
    anchors = [p for p in spark.get("potjes", []) if p.get("pot_locked")]
    return {
        "last_rente_run": state.get("last_rente_run"),
        "overflow_pool": spark.get("overflow_pool", 0),
        "anchors_count": len(anchors),
        "rente_pct_per_anchor": RENTE_PCT_PER_MAAND,
        "mint_threshold": MINT_THRESHOLD,
        "config": {
            "rente_interval_hours": RENTE_INTERVAL_HOURS,
            "spark_user_id": SPARK_USER,
        },
    }


@router.post("/auto-anchor")
async def auto_anchor_endpoint(req: AnchorRequest):
    """Maak staking-anchor voor coin (admin-only). Idempotent."""
    if not _is_admin(req.viewer_id):
        raise HTTPException(403, "Alleen admin (gradatie ≤ 2)")
    result = auto_create_anchor(req.coin)
    if not result:
        raise HTTPException(400, "Kon anchor niet maken")
    return {"success": True, **result}
