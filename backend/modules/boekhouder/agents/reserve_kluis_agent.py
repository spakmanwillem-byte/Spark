"""ReserveKluisAgent — 5% van elke mint gaat naar reserve-kluis.

Split: 2% dev / 2% maint / 1% buffer. Boekhoudkundige claim (niet fysieke transfer).
Storage: `data/boekhouder/reserve_kluis.json` (running balances).
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict
from modules.core.storage import load_json, save_json
from .base_agent import BaseFinanceAgent, DATA

KLUIS_FP = DATA / "boekhouder" / "reserve_kluis.json"

DEFAULT_KLUIS = {
    "dev_fund_eur": 0.0, "maint_fund_eur": 0.0, "buffer_eur": 0.0,
    "total_reserved_eur": 0.0, "mint_count": 0, "last_update": None,
    "history": [],
}


class ReserveKluisAgent(BaseFinanceAgent):
    topic = "reserve_kluis"

    def _load(self) -> Dict[str, Any]:
        KLUIS_FP.parent.mkdir(parents=True, exist_ok=True)
        return load_json(KLUIS_FP, default=DEFAULT_KLUIS) or DEFAULT_KLUIS

    def reserve_from_mint(self, mint_total_eur: float, mint_event_id: str,
                          source: str = "manual") -> Dict[str, Any]:
        """Reserveer 5% van mint-bedrag (2% dev / 2% maint / 1% buffer)."""
        k = self._load()
        pct = self.blueprint().get("reserve_percentages", {"dev": 2.0, "maint": 2.0, "buffer": 1.0})
        dev_amt = round(mint_total_eur * pct["dev"] / 100.0, 4)
        maint_amt = round(mint_total_eur * pct["maint"] / 100.0, 4)
        buffer_amt = round(mint_total_eur * pct["buffer"] / 100.0, 4)
        total = dev_amt + maint_amt + buffer_amt
        k["dev_fund_eur"] = round(k["dev_fund_eur"] + dev_amt, 4)
        k["maint_fund_eur"] = round(k["maint_fund_eur"] + maint_amt, 4)
        k["buffer_eur"] = round(k["buffer_eur"] + buffer_amt, 4)
        k["total_reserved_eur"] = round(k["total_reserved_eur"] + total, 4)
        k["mint_count"] = int(k.get("mint_count", 0)) + 1
        k["last_update"] = datetime.now(timezone.utc).isoformat()
        k.setdefault("history", []).append({
            "mint_event_id": mint_event_id, "source": source,
            "mint_total_eur": mint_total_eur,
            "dev": dev_amt, "maint": maint_amt, "buffer": buffer_amt,
            "timestamp": k["last_update"],
        })
        save_json(KLUIS_FP, k)
        return {
            "reserved": {"dev": dev_amt, "maint": maint_amt, "buffer": buffer_amt, "total": total},
            "current_kluis": {k2: v for k2, v in k.items() if k2 != "history"},
        }

    def snapshot(self, user_id: str) -> Dict[str, Any]:
        k = self._load()
        return {
            "dev_fund_eur": k["dev_fund_eur"], "maint_fund_eur": k["maint_fund_eur"],
            "buffer_eur": k["buffer_eur"], "total_reserved_eur": k["total_reserved_eur"],
            "mint_count": k["mint_count"], "last_update": k.get("last_update"),
            "recent_history": (k.get("history") or [])[-5:],
        }
