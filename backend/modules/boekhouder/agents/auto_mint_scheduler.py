"""AutoMintScheduler — check elk uur of ruis stabiel is ≥ base_pot 24h → auto-mint.

Regel (Willem):
- Elk uur: check `ruis = bitvavo_free - sum(alle_potjes_capital)`
- Als ruis ≥ base_pot_size (€10):
    - Zet condition_met_since (als nog niet gezet)
    - Als condition_met_since ≥ 24h EN last_auto_mint ≥ 24h → MINT 1 pot
    - Reset condition_met_since, zet last_auto_mint = nu
- Als ruis wegvalt → reset condition_met_since
- Bij mint → notificatie (net als gift-flow) → user weet "Spark minted"
"""
from __future__ import annotations
from datetime import datetime, timezone, timedelta
from typing import Any, Dict
from modules.core.storage import load_json, save_json
from .base_agent import BaseFinanceAgent, DATA

STATE_FP = DATA / "boekhouder" / "auto_mint_state.json"
DEFAULT_STATE = {
    "condition_met_since": None, "last_auto_mint_at": None,
    "last_check_at": None, "check_count": 0, "mint_count": 0,
    "history": [],
}
COOLDOWN_H = 24
GRACE_H = 24


class AutoMintScheduler(BaseFinanceAgent):
    topic = "auto_mint_scheduler"

    def _load(self) -> Dict[str, Any]:
        STATE_FP.parent.mkdir(parents=True, exist_ok=True)
        return load_json(STATE_FP, default=DEFAULT_STATE) or DEFAULT_STATE

    def _save(self, s):
        save_json(STATE_FP, s)

    def _hours_ago(self, iso: str) -> float:
        if not iso: return 9999.0
        try:
            dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
            return (datetime.now(timezone.utc) - dt).total_seconds() / 3600.0
        except Exception:
            return 9999.0

    def check_and_maybe_mint(self, viewer_id: str = "user-001") -> Dict[str, Any]:
        """Roep elk uur (of via lazy check op snapshot)."""
        from .price_agent import PriceAgent
        from .bitvavo_agent import BitvavoAgent

        state = self._load()
        now = datetime.now(timezone.utc)
        state["last_check_at"] = now.isoformat()
        state["check_count"] = int(state.get("check_count", 0)) + 1

        pr = PriceAgent().compute_price()
        base = pr["base_pot_size_eur"]
        bitvavo = BitvavoAgent().live_free_eur()
        # potjes systeem-breed
        pots = load_json(DATA / "financial" / "user_potjes.json", default={"users": {}}) or {}
        total_potjes = sum(len((u or {}).get("potjes", []) or []) for u in (pots.get("users") or {}).values())
        total_potjes_value = total_potjes * pr["current_price_eur"]
        ruis = bitvavo - total_potjes_value

        result = {
            "check_at": now.isoformat(),
            "ruis_eur": round(ruis, 4),
            "threshold_base_eur": base,
            "condition_met": ruis >= base,
            "hours_since_condition_met": self._hours_ago(state.get("condition_met_since")),
            "hours_since_last_mint": self._hours_ago(state.get("last_auto_mint_at")),
            "action": "hold",
        }

        if ruis >= base:
            if not state.get("condition_met_since"):
                state["condition_met_since"] = now.isoformat()
                result["action"] = "condition_started"
            else:
                h = self._hours_ago(state["condition_met_since"])
                cooldown_ok = self._hours_ago(state.get("last_auto_mint_at")) >= COOLDOWN_H
                if h >= GRACE_H and cooldown_ok:
                    # → MINT!
                    from ..finance_ops import mint_tokens
                    mint_result = mint_tokens("user-000", 1, source="auto_mint_24h_ruis", dry_run=False)
                    state["last_auto_mint_at"] = now.isoformat()
                    state["condition_met_since"] = None
                    state["mint_count"] = int(state.get("mint_count", 0)) + 1
                    state.setdefault("history", []).append({
                        "at": now.isoformat(), "ruis_at_mint": ruis,
                        "mint_result_success": mint_result.get("success"),
                        "log_event_id": mint_result.get("preview", {}).get("log_event_id"),
                        "pot_ids": mint_result.get("minted_pot_ids", []),
                    })
                    result["action"] = "MINTED"
                    result["mint_result"] = mint_result
                    # Notificatie (gift-flow patroon)
                    self._notify_users_of_mint(mint_result)
                else:
                    result["action"] = "waiting_for_grace_or_cooldown"
        else:
            # ruis viel onder threshold — reset
            if state.get("condition_met_since"):
                state["condition_met_since"] = None
                result["action"] = "condition_lost_reset"

        self._save(state)
        result["state"] = state
        return result

    def _notify_users_of_mint(self, mint_result: Dict[str, Any]) -> None:
        """Stuur notificatie naar admin (Willem) + Spark eigenaar log."""
        try:
            from modules.notifications import notif_service  # bestaand
            preview = mint_result.get("preview", {})
            msg = (f"Spark minted automatisch 1 pot @ €{preview.get('token_price_at_mint', 0):.2f} "
                   f"uit stabiele ruis. Log: {preview.get('log_event_id', '?')[:8]}")
            for uid in ("user-001",):
                notif_service.notify(uid, "🪙 Auto-mint uitgevoerd", msg,
                                     icon="🪙", kind="auto_mint")
        except Exception as e:
            print(f"[auto_mint] notify failed (non-blocking): {e}")

    def snapshot(self, user_id: str) -> Dict[str, Any]:
        s = self._load()
        return {
            "condition_met_since": s.get("condition_met_since"),
            "last_auto_mint_at": s.get("last_auto_mint_at"),
            "last_check_at": s.get("last_check_at"),
            "check_count": s.get("check_count", 0),
            "mint_count": s.get("mint_count", 0),
            "cooldown_hours": COOLDOWN_H,
            "grace_hours": GRACE_H,
            "hours_since_condition_met": self._hours_ago(s.get("condition_met_since")),
            "hours_since_last_mint": self._hours_ago(s.get("last_auto_mint_at")),
            "recent_history": (s.get("history") or [])[-3:],
        }
