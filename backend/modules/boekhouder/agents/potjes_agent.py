"""PotjesAgent — trader potjes met dynamische capital = token_price."""
from typing import Any, Dict, List
from modules.core.storage import load_json
from .base_agent import BaseFinanceAgent, DATA


class PotjesAgent(BaseFinanceAgent):
    topic = "potjes_agent"

    def _resolve_source(self, user_id: str):
        """Trader-potjes zitten historisch onder user-000 (Spark). Fallback als user leeg."""
        p = load_json(DATA / "financial" / "user_potjes.json", default={"users": {}}) or {}
        users = p.get("users", {}) or {}
        u = users.get(user_id, {}) or {}
        potjes = u.get("potjes", []) or []
        source = user_id
        if not potjes and user_id != "user-000":
            u0 = users.get("user-000", {}) or {}
            potjes = u0.get("potjes", []) or []
            source = "user-000"
        return source, potjes, u.get("overflow_pool", 0.0)

    def snapshot(self, user_id: str) -> Dict[str, Any]:
        from .price_agent import PriceAgent
        source, potjes, overflow = self._resolve_source(user_id)
        price = PriceAgent().compute_price()["current_price_eur"]
        # Hybride: pot.capital = current token_price (leeft mee)
        listing: List[Dict[str, Any]] = []
        for pot in potjes:
            stored_capital = float(pot.get("capital", 0) or 0)
            dynamic_capital = price  # HYBRIDE regel
            listing.append({
                "id": pot.get("id"),
                "market": pot.get("market") or pot.get("last_market"),
                "capital_stored_eur": stored_capital,
                "capital_dynamic_eur": round(dynamic_capital, 2),
                "max_size_eur": float(pot.get("max_size", 0) or 0),
                "pot_locked": pot.get("pot_locked", False),
                "drift_eur": round(dynamic_capital - stored_capital, 2),
            })
        return {
            "source_user_id": source,
            "potjes_count": len(potjes),
            "current_token_price_eur": price,
            "total_capital_dynamic_eur": round(len(potjes) * price, 2),
            "total_capital_stored_eur": round(sum(p["capital_stored_eur"] for p in listing), 2),
            "overflow_pool_eur": float(overflow or 0),
            "potjes": listing,
        }
