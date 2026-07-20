"""PriceAgent — dynamische token-prijs berekening.

Formule uit blueprint: `max(anchor, bitvavo_free_eur / minted_supply)`
"""
from typing import Any, Dict
from .base_agent import BaseFinanceAgent, DATA
from .bitvavo_agent import BitvavoAgent


class PriceAgent(BaseFinanceAgent):
    topic = "price_agent"

    def compute_price(self) -> Dict[str, Any]:
        """Hybride pot-waarde formule (Willem's voorbeeld):
        - base_pot_size = €10 (operationele basis)
        - anchor €5.08 = alleen ondergrens bij MINTEN (bescherming)
        - dynamic = max(base, bitvavo_balance / n_potjes)
        - Bij €60/5 = €12 per pot. Mint bij ≥ (n+1) × base → terug naar €10.
        """
        from modules.core.storage import load_json as _lj
        bp = self.blueprint().get("formula_params", {}) or {}
        base = float(bp.get("base_pot_size_eur", 10.0))
        anchor = float(bp.get("anchor_price_eur", 5.08))
        # Aantal potjes (systeem-breed, voor prijs-berekening — pak user-000 shared trader)
        pots_data = _lj(DATA / "financial" / "user_potjes.json", default={"users": {}}) or {}
        u0 = (pots_data.get("users") or {}).get("user-000", {}) or {}
        n_potjes = len(u0.get("potjes", []) or []) or 1
        bitvavo_free = BitvavoAgent().live_free_eur()
        # Formule: pot-waarde = max(base_pot_size, bitvavo_free / n_potjes)
        per_pot_ratio = bitvavo_free / n_potjes if n_potjes > 0 else 0
        price = max(base, per_pot_ratio)
        return {
            "current_price_eur": round(price, 4),
            "base_pot_size_eur": base,
            "anchor_price_eur": anchor,
            "mint_floor_eur": anchor,
            "raw_ratio_eur": round(per_pot_ratio, 4),
            "bitvavo_free_eur": bitvavo_free,
            "n_potjes": n_potjes,
            "formula": "max(base_pot_size, bitvavo_free_eur / n_potjes)",
            "at_base": price == base,
            "next_mint_threshold_eur": round((n_potjes + 1) * base, 2),
            "_note_anchor": "€5.08 = alleen mint-vloer, geen dagelijkse rol.",
            "_note_zelf_regulerend": f"Bij €{(n_potjes+1) * base:.0f} balance → mint pot #{n_potjes+1} → terug naar base €{base:.0f} per pot.",
        }

    def snapshot(self, user_id: str) -> Dict[str, Any]:
        return self.compute_price()
