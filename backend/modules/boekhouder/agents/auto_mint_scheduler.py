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

    def check_and_maybe_mint(self, viewer_id: str = "user-001", force: bool = False) -> Dict[str, Any]:
        """Roep elk uur (of via lazy check op snapshot).

        Ruis-definitie (Willem): bitvavo_free - (n_potjes * base_pot_size_eur).
        Als ruis >= base 24u aaneen → mint 1 pot (cooldown 24u tussen mints).
        `force=True` (admin) overslaat de 24u grace maar respecteert cooldown.
        """
        from .price_agent import PriceAgent
        from .bitvavo_agent import BitvavoAgent

        state = self._load()
        now = datetime.now(timezone.utc)
        state["last_check_at"] = now.isoformat()
        state["check_count"] = int(state.get("check_count", 0)) + 1

        pr = PriceAgent().compute_price()
        base = pr["base_pot_size_eur"]
        bitvavo = BitvavoAgent().live_free_eur()
        # potjes systeem-breed (n_potjes zoals prijs-berekening — Spark's shared trader)
        pots = load_json(DATA / "financial" / "user_potjes.json", default={"users": {}}) or {}
        total_potjes = sum(len((u or {}).get("potjes", []) or []) for u in (pots.get("users") or {}).values())
        # Ruis = surplus boven de baseline (n × base). NIET boven current_price (dat is ~bitvavo → altijd 0)
        baseline_eur = total_potjes * base
        ruis = bitvavo - baseline_eur

        result = {
            "check_at": now.isoformat(),
            "bitvavo_free_eur": round(bitvavo, 4),
            "n_potjes_total": total_potjes,
            "baseline_eur": round(baseline_eur, 4),
            "ruis_eur": round(ruis, 4),
            "threshold_base_eur": base,
            "condition_met": ruis >= base,
            "hours_since_condition_met": self._hours_ago(state.get("condition_met_since")),
            "hours_since_last_mint": self._hours_ago(state.get("last_auto_mint_at")),
            "forced": bool(force),
            "action": "hold",
        }

        if ruis >= base:
            cooldown_ok = self._hours_ago(state.get("last_auto_mint_at")) >= COOLDOWN_H
            if not state.get("condition_met_since"):
                state["condition_met_since"] = now.isoformat()
                result["action"] = "condition_started"
                if force and cooldown_ok:
                    # admin override — mint direct (val door naar mint-blok)
                    pass
                else:
                    self._save(state); result["state"] = state; return result

            h = self._hours_ago(state["condition_met_since"])
            grace_ok = h >= GRACE_H or force
            if grace_ok and cooldown_ok:
                # → MINT!
                from ..finance_ops import mint_tokens
                mint_result = mint_tokens("user-000", 1, source="auto_mint_24h_ruis", dry_run=False)
                state["last_auto_mint_at"] = now.isoformat()
                state["condition_met_since"] = None
                state["mint_count"] = int(state.get("mint_count", 0)) + 1
                state.setdefault("history", []).append({
                    "at": now.isoformat(),
                    "ruis_at_mint": round(ruis, 4),
                    "bitvavo_at_mint": round(bitvavo, 4),
                    "n_potjes_before": total_potjes,
                    "forced": bool(force),
                    "mint_result_success": mint_result.get("success"),
                    "log_event_id": mint_result.get("preview", {}).get("log_event_id"),
                    "pot_ids": mint_result.get("minted_pot_ids", []),
                })
                result["action"] = "MINTED"
                result["mint_result"] = mint_result
                # Notificatie (best-effort; module bestaat mogelijk niet)
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
        """Stuur DM via Boekhouder + community-post (papertrail-echo)."""
        try:
            from ..service import _send_dm, _post_community, ADMIN_ID
            preview = mint_result.get("preview", {})
            price = preview.get("token_price_at_mint", 0) or 0
            n = preview.get("n_tokens", 1) or 1
            log_id = (preview.get("log_event_id") or "?")[:8]
            pot_ids = mint_result.get("minted_pot_ids", []) or []
            dm_text = (
                f"🪙 **Auto-mint uitgevoerd**\n"
                f"Spark heeft {n} pot bijgemunt uit stabiele ruis.\n"
                f"• Token-prijs @ mint: €{price:.4f}\n"
                f"• Totaal: €{n * price:.2f}\n"
                f"• Nieuw pot-id(s): {', '.join(pot_ids) or '?'}\n"
                f"• Log-event: {log_id}\n"
                f"• 5% reserve-kluis (2/2/1) automatisch afgeboekt."
            )
            _send_dm(dm_text, kind="auto_mint", extra={
                "log_event_id": preview.get("log_event_id"),
                "pot_ids": pot_ids, "n_tokens": n, "price_eur": price,
            }, recipient_id=ADMIN_ID)
            _post_community(
                f"Spark heeft z'n eigen pot uitgebreid. De ruis was gewoon te stabiel om te negeren.",
                kind="auto_mint")
        except Exception as e:
            print(f"[auto_mint] notify failed (non-blocking): {e}")

    def snapshot(self, user_id: str) -> Dict[str, Any]:
        """Overview + live ruis/bitvavo/threshold (voor UI/admin)."""
        s = self._load()
        # Live cijfers meesturen zodat UI direct kan tonen zonder tick
        try:
            from .price_agent import PriceAgent
            from .bitvavo_agent import BitvavoAgent
            from modules.core.storage import load_json as _lj
            pr = PriceAgent().compute_price()
            base = float(pr.get("base_pot_size_eur", 10.0))
            bitvavo = BitvavoAgent().live_free_eur()
            pots = _lj(DATA / "financial" / "user_potjes.json", default={"users": {}}) or {}
            n = sum(len((u or {}).get("potjes", []) or []) for u in (pots.get("users") or {}).values())
            baseline = n * base
            ruis = bitvavo - baseline
            live = {
                "bitvavo_free_eur": round(bitvavo, 4),
                "n_potjes_total": n,
                "baseline_eur": round(baseline, 4),
                "ruis_eur": round(ruis, 4),
                "threshold_base_eur": base,
                "condition_met_now": ruis >= base,
                "next_mint_threshold_bitvavo_eur": round((n + 1) * base, 2),
            }
        except Exception as e:
            live = {"error": str(e)}
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
            "live": live,
        }
