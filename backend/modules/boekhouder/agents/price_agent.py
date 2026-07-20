"""PriceAgent — dynamische token-prijs berekening.

Formule uit blueprint: `max(anchor, bitvavo_free_eur / minted_supply)`
"""
from typing import Any, Dict
from .base_agent import BaseFinanceAgent
from .token_agent import TokenAgent
from .bitvavo_agent import BitvavoAgent


class PriceAgent(BaseFinanceAgent):
    topic = "price_agent"

    def compute_price(self) -> Dict[str, Any]:
        bp = self.blueprint().get("formula_params", {}) or {}
        anchor = float(bp.get("anchor_price_eur", 5.08))
        token = TokenAgent()._load_roar()
        minted = token.get("total_supply", 1000000) - token.get("treasury_pool", 0)
        bitvavo_free = BitvavoAgent().live_free_eur()
        # Formule: max(anchor, bitvavo_free / minted)
        raw = (bitvavo_free / minted) if minted > 0 else 0
        price = max(anchor, raw)
        return {
            "current_price_eur": round(price, 4),
            "raw_calc_eur": round(raw, 4),
            "anchor_price_eur": anchor,
            "bitvavo_free_eur": bitvavo_free,
            "minted_supply": minted,
            "formula": "max(anchor, bitvavo_free_eur / minted_supply)",
            "at_floor": raw < anchor,
            "stale_dynamic_price_in_roar": token.get("current_dynamic_price_eur"),
            "_stale_note": "current_dynamic_price_eur in roar_balances.json is legacy (SOL min-trade artefact). PriceAgent berekent fresh.",
        }

    def snapshot(self, user_id: str) -> Dict[str, Any]:
        return self.compute_price()
