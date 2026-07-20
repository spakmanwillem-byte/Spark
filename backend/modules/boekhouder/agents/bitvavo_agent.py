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

    def snapshot(self, user_id: str) -> Dict[str, Any]:
        free = self.live_free_eur()
        return {
            "bitvavo_free_eur": round(free, 2),
            "source": "live" if free > 0 else "cached_fallback",
            "_note": "Shared account (Spark's Bitvavo). Individueel niet af te leiden.",
        }
