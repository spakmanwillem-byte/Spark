"""v12_trader_strategy_cfg_001 — Data-driven trader-config service + endpoints.

Post trader-reset (2026-08-06): alle trader-parameters komen uit
/app/backend/data/trade/strategy_config.json i.p.v. hardcoded constants.

Willem kan tunen via PATCH zonder code-deploy. Elke wijziging wordt gelogd.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from modules.core.storage import load_json, save_json

router = APIRouter(prefix="/trader", tags=["trader-strategy-config"])

CONFIG_FILE = Path("/app/backend/data/trade/strategy_config.json")
HISTORY_FILE = Path("/app/backend/data/trade/strategy_config_history.json")

_DEFAULTS = {
    "buy": {
        "daily_drop_threshold_pct": 5.0,
        "gap_confirmation_required": False,
        "gap_confirmation_min_greens": 3,
        "cooldown_between_buys_sec": 3600,
        "min_position_eur": 5.0,
        "max_open_positions_per_market": 1,
    },
    "sell": {
        "loss_cut_pct": -1.0,
        "loss_cut_window_hours": 48,
        "take_profit_pct": 3.0,
        "trailing_active_above_pct": 2.0,
        "trailing_step_pct": 0.5,
        "fee_aware": True,
        "min_fee_buffer_pct": 0.4,
    },
    "risk": {
        "max_open_positions_global": 6,
        "daily_max_loss_eur": 5.0,
        "event_pause_on_drop_pct": 5.0,
        "event_pause_duration_hours": 24,
    },
    "pots": {
        "default_capital_eur": 10.0,
        "max_pot_size_ratio": 8.0,
        "overflow_to_pool_pct": 0.0,
    },
}


def get_strategy_config() -> Dict[str, Any]:
    """Read strategy config. Falls back to defaults if file missing/corrupt.

    Consumers in modules/trade gebruiken deze i.p.v. hardcoded constants.
    Voorbeeld:
        cfg = get_strategy_config()
        threshold = cfg["buy"]["daily_drop_threshold_pct"]
    """
    if not CONFIG_FILE.exists():
        return _DEFAULTS.copy()
    try:
        data = json.loads(CONFIG_FILE.read_text())
        # Merge met defaults zodat ontbrekende sections niet crashen
        merged = {}
        for section, defaults in _DEFAULTS.items():
            merged[section] = {**defaults, **(data.get(section) or {})}
        return merged
    except Exception:
        return _DEFAULTS.copy()


def get_strategy_value(section: str, key: str, fallback=None):
    """Convenience: pak 1 specifieke waarde met fallback."""
    cfg = get_strategy_config()
    return (cfg.get(section) or {}).get(key, fallback)


class PatchRequest(BaseModel):
    updates: Dict[str, Dict[str, Any]]  # {"buy": {"daily_drop_threshold_pct": 4.5}, ...}
    reason: Optional[str] = None
    by_user: Optional[str] = "willem"


@router.get("/strategy-config")
async def read_strategy_config():
    """Retourneer huidige strategy-config (samengevoegd met defaults)."""
    return {"success": True, "config": get_strategy_config(), "path": str(CONFIG_FILE)}


@router.patch("/strategy-config")
async def patch_strategy_config(req: PatchRequest):
    """Wijzig 1 of meer parameters. Elke wijziging gaat naar history log.

    Body:
      {
        "updates": {"buy": {"daily_drop_threshold_pct": 4.5}, "sell": {"loss_cut_pct": -1.5}},
        "reason": "Verlaag drempel voor meer entries",
        "by_user": "willem"
      }
    """
    if not req.updates:
        raise HTTPException(400, "Geen updates opgegeven")

    current = load_json(CONFIG_FILE, default=_DEFAULTS.copy())
    changed = []

    for section, params in req.updates.items():
        if section not in _DEFAULTS:
            raise HTTPException(400, f"Onbekende sectie '{section}'. Kies uit: {list(_DEFAULTS.keys())}")
        if not isinstance(params, dict):
            raise HTTPException(400, f"'{section}' updates moeten dict zijn")
        current.setdefault(section, {})
        for key, value in params.items():
            if key not in _DEFAULTS[section]:
                raise HTTPException(400, f"Onbekende key '{section}.{key}'. Bekend: {list(_DEFAULTS[section].keys())}")
            old = current[section].get(key)
            if old != value:
                changed.append({"section": section, "key": key, "old": old, "new": value})
                current[section][key] = value

    now = datetime.now(timezone.utc).isoformat()
    current["last_updated"] = now
    save_json(CONFIG_FILE, current)

    # History-log
    if changed:
        hist = load_json(HISTORY_FILE, default={"entries": []})
        hist.setdefault("entries", []).append({
            "ts": now,
            "by_user": req.by_user,
            "reason": req.reason,
            "changes": changed,
        })
        save_json(HISTORY_FILE, hist)

    return {
        "success": True,
        "changed_count": len(changed),
        "changed": changed,
        "config": current,
    }


@router.get("/strategy-config/history")
async def strategy_config_history(limit: int = 50):
    hist = load_json(HISTORY_FILE, default={"entries": []})
    entries = list(reversed(hist.get("entries", [])))[:limit]
    return {"success": True, "count": len(entries), "entries": entries}
