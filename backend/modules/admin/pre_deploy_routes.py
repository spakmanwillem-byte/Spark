"""
v6_pre_deploy_reset_001 — Admin endpoint voor pre/post-deploy schoonmaak.
v6_pre_deploy_reset_002 — Uitgebreid met potjes-reset, baseline-wipe, accounting-clear,
                          shadow-pots-leeg, en optioneel ROAR-balances naar 0.

Eén knop die:
  1. Shadow-cascade UIT zet (data/trade/shadow_flag.json)
  2. ROAR balances reset (geheel-0 of custom mapping)
  3. Potjes per user op 12 lege idle pots (capital 10.0, geen positie)
  4. capital_baseline.json leegmaken (geen base)
  5. accounting/transactions.json leegmaken
  6. shadow_pots.json clean (lege array)

Vereist: admin-rol (user.admin == True).
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional
from pathlib import Path
from datetime import datetime, timezone
from modules.core.storage import load_json, save_json
from modules.admin.admin_service import is_admin

router = APIRouter(prefix="/admin/system", tags=["admin-system"])

DATA = Path(__file__).parent.parent.parent / "data"
ROAR_FILE = DATA / "roar" / "roar_balances.json"
SHADOW_FLAG_FILE = DATA / "trade" / "shadow_flag.json"
USER_POTJES_FILE = DATA / "financial" / "user_potjes.json"
CAPITAL_BASELINE_FILE = DATA / "trade" / "capital_baseline.json"
ACCOUNTING_FILE = DATA / "accounting" / "transactions.json"
SHADOW_POTS_FILE = DATA / "trade" / "shadow_pots.json"

DEFAULT_POTS_COUNT = 12
DEFAULT_POT_CAPITAL = 10.0
DEFAULT_POT_MAX = 50.0


class ResetBody(BaseModel):
    by_user: str  # admin user_id die de actie uitvoert
    balances: Optional[Dict[str, int]] = None  # {user_id: nieuwe_balance}
    disable_shadow: bool = True
    # v6_pre_deploy_reset_002 — nieuwe vlaggen, default OFF om bestaande UI te respecteren
    reset_pots: bool = False           # 12 lege pots per user
    clear_baseline: bool = False       # capital_baseline.json leeg
    clear_accounting: bool = False     # accounting/transactions.json leeg
    clear_shadow_pots: bool = False    # shadow_pots.json clean
    zero_all_roar: bool = False        # alle ROAR balances → 0


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _make_empty_pot(idx: int) -> dict:
    return {
        "id": f"pot-{idx:03d}",
        "index": idx - 1,
        "capital": DEFAULT_POT_CAPITAL,
        "max_size": DEFAULT_POT_MAX,
        "pot_locked": False,
        "lock_reason": None,
        "position": {
            "is_open": False,
            "entry_price": None,
            "highest_price": None,
            "trailing_active": False,
            "entry_time": None,
        },
        "market": None,
        "stats": {"trades": 0, "wins": 0, "losses": 0, "total_pnl": 0.0},
        "created_at": _now(),
        "trade_log": [],
        "last_action": "",
        "live_value": DEFAULT_POT_CAPITAL,
    }


@router.post("/pre-deploy-reset")
def pre_deploy_reset(body: ResetBody):
    """
    Pre/post-deploy schoonmaak. Admin-only.

    Vlaggen (alle default behavior behouden):
      - balances: optionele dict {user_id: nieuw_saldo} → vervangt ALLE balances
      - disable_shadow: True (default) → zet shadow-cascade UIT
      - reset_pots: True → elke user krijgt 12 lege idle potjes
      - clear_baseline: True → capital_baseline.json wordt {}
      - clear_accounting: True → accounting/transactions.json transactions=[]
      - clear_shadow_pots: True → shadow_pots.json {shadows:[]}
      - zero_all_roar: True → alle ROAR balances → 0
    """
    if not is_admin(body.by_user):
        raise HTTPException(403, "Alleen admins mogen pre-deploy reset uitvoeren.")

    result = {"success": True, "ts": _now(), "by": body.by_user}

    # 1. Shadow flag UIT
    if body.disable_shadow:
        sf = load_json(SHADOW_FLAG_FILE, default={})
        prev = sf.get("enabled")
        sf.update({
            "enabled": False,
            "updated_at": _now(),
            "updated_by": body.by_user,
            "note": "pre_deploy_reset endpoint",
        })
        save_json(SHADOW_FLAG_FILE, sf)
        result["shadow_flag"] = {"was": prev, "now": False}

    # 2. ROAR balances reset (expliciete mapping wint van zero_all_roar)
    if body.balances is not None or body.zero_all_roar:
        roar = load_json(ROAR_FILE, default={"balances": {}})
        prev_balances = dict(roar.get("balances", {}))
        if body.balances is not None:
            new_balances = {k: int(v) for k, v in body.balances.items()}
        else:
            new_balances = {k: 0 for k in prev_balances.keys()}
        roar["balances"] = new_balances
        roar.setdefault("admin_log", []).append({
            "ts": _now(),
            "action": "pre_deploy_reset_balances",
            "by": body.by_user,
            "previous": prev_balances,
            "new": new_balances,
        })
        save_json(ROAR_FILE, roar)
        result["balances"] = {"previous": prev_balances, "new": new_balances}

    # 3. Potjes-reset: elke user krijgt 12 lege idle pots
    if body.reset_pots:
        up = load_json(USER_POTJES_FILE, default={"users": {}})
        users = up.get("users", {})
        summary = {}
        for uid, info in users.items():
            old_count = len(info.get("potjes", []))
            new_pots = [_make_empty_pot(i) for i in range(1, DEFAULT_POTS_COUNT + 1)]
            info["potjes"] = new_pots
            info["overflow_pool"] = 0.0
            info["last_buy_cycle"] = None
            info.pop("baseline_eur", None)  # geen base
            summary[uid] = {"old_pot_count": old_count, "new_pot_count": DEFAULT_POTS_COUNT}
        up["users"] = users
        up["_pre_deploy_reset_at"] = _now()
        save_json(USER_POTJES_FILE, up)
        result["pots_reset"] = summary

    # 4. Baseline leeg
    if body.clear_baseline:
        prev_bl = load_json(CAPITAL_BASELINE_FILE, default={})
        save_json(CAPITAL_BASELINE_FILE, {})
        result["baseline_cleared"] = {"previous_keys": list(prev_bl.keys())}

    # 5. Accounting transactions wissen
    if body.clear_accounting:
        prev_acc = load_json(ACCOUNTING_FILE, default={"transactions": []})
        prev_count = len(prev_acc.get("transactions", []))
        save_json(ACCOUNTING_FILE, {"transactions": [], "_cleared_at": _now(), "_cleared_by": body.by_user})
        result["accounting_cleared"] = {"previous_tx_count": prev_count}

    # 6. Shadow pots clean
    if body.clear_shadow_pots:
        prev_sp = load_json(SHADOW_POTS_FILE, default={"shadows": []})
        prev_count = len(prev_sp.get("shadows", []))
        save_json(SHADOW_POTS_FILE, {"shadows": [], "_cleared_at": _now(), "_cleared_by": body.by_user})
        result["shadow_pots_cleared"] = {"previous_shadows": prev_count}

    return result


@router.get("/health-status")
def health_status():
    """Snelle check: huidige shadow-flag + ROAR-balances + pots-overzicht voor admin-UI."""
    sf = load_json(SHADOW_FLAG_FILE, default={"enabled": False})
    roar = load_json(ROAR_FILE, default={"balances": {}})
    up = load_json(USER_POTJES_FILE, default={"users": {}})
    bl = load_json(CAPITAL_BASELINE_FILE, default={})
    acc = load_json(ACCOUNTING_FILE, default={"transactions": []})

    pots_summary = {}
    for uid, info in up.get("users", {}).items():
        pots = info.get("potjes", [])
        open_count = sum(1 for p in pots if p.get("position", {}).get("is_open"))
        pots_summary[uid] = {"count": len(pots), "open_positions": open_count}

    return {
        "shadow_enabled": bool(sf.get("enabled")),
        "shadow_updated_at": sf.get("updated_at"),
        "roar_balances": roar.get("balances", {}),
        "pots_per_user": pots_summary,
        "baseline_users": list(bl.keys()),
        "accounting_tx_count": len(acc.get("transactions", [])),
    }
