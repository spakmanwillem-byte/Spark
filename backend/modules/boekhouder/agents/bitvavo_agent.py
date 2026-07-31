"""BitvavoAgent — live saldo (cached)."""
from typing import Any, Dict
from modules.core.storage import load_json
from .base_agent import BaseFinanceAgent, DATA


class BitvavoAgent(BaseFinanceAgent):
    topic = "bitvavo_agent"

    def live_free_eur(self) -> float:
        """Probeer live via bitvavo_client, fallback naar cached market_stats."""
        try:
            from modules.trade.bitvavo_client import get_balance
            bal = get_balance() or {}
            for asset in bal if isinstance(bal, list) else []:
                if asset.get("symbol") == "EUR":
                    return float(asset.get("available", 0) or 0)
        except Exception:
            pass
        # Fallback: market_stats snapshot
        ms = load_json(DATA / "trade" / "market_stats.json", default={}) or {}
        return float((ms.get("bitvavo") or {}).get("free_eur", 0) or 0)

    def live_free_eur_after_reserve(self) -> float:
        """v11_reserve_lock_001 — vrij EUR NA aftrek van 2/2/1 reserve-kluis.
        Willems eis: reserve-kluis (dev/maint/buffer) moet apart blijven, mint/potjes
        mogen NIET aan dat bedrag komen. Gebruik dit ipv `live_free_eur` voor:
          - mint-check (spark_mint)
          - potje-availability (monitor.py)
          - Bitvavo balance display in Trader UI
        """
        raw = self.live_free_eur()
        try:
            from .reserve_kluis_agent import ReserveKluisAgent
            snap = ReserveKluisAgent().snapshot("system")
            reserved = float(snap.get("total_reserved_eur") or 0)
        except Exception:
            reserved = 0.0
        return max(0.0, raw - reserved)

    def snapshot(self, user_id: str) -> Dict[str, Any]:
        free = self.live_free_eur()
        after_reserve = self.live_free_eur_after_reserve()
        return {
            "bitvavo_free_eur": round(free, 2),
            "bitvavo_free_after_reserve_eur": round(after_reserve, 2),
            "reserve_locked_eur": round(free - after_reserve, 2),
            "source": "live" if free > 0 else "cached_fallback",
            "_note": "Shared account (Spark's Bitvavo). Reserve-kluis (2/2/1) gescheiden gehouden.",
        }
