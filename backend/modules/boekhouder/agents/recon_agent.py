"""ReconAgent — drift-detectie + ruis-berekening.

Ruis = bitvavo_total - sum(alle_potjes_capital)  ← "extra vlees" volgens Willem
Drift = wallet_mirror != roar_authoritative
"""
from typing import Any, Dict, List
from modules.core.storage import load_json
from .base_agent import BaseFinanceAgent, DATA


class ReconAgent(BaseFinanceAgent):
    topic = "recon_agent"

    def snapshot(self, user_id: str) -> Dict[str, Any]:
        from .token_agent import TokenAgent
        from .price_agent import PriceAgent
        from .bitvavo_agent import BitvavoAgent

        # 1. Token drift (roar vs wallet mirror)
        t = TokenAgent().snapshot(user_id)
        token_drift = t.get("drift_detected", False)

        # 2. Ruis berekenen — SYSTEEM-breed
        potjes_file = load_json(DATA / "financial" / "user_potjes.json", default={"users": {}}) or {}
        price = PriceAgent().compute_price()["current_price_eur"]
        total_potjes_capital = 0.0
        total_potjes_count = 0
        for uid, udata in (potjes_file.get("users") or {}).items():
            n = len((udata or {}).get("potjes", []) or [])
            total_potjes_count += n
            total_potjes_capital += n * price
        bitvavo = BitvavoAgent().live_free_eur()
        # Ruis = bitvavo - som(alle potjes waarde)
        # Kan negatief zijn als potjes > bitvavo (dan is er "tekort", niet ruis)
        ruis = bitvavo - total_potjes_capital
        bp = self.blueprint()
        thresholds = bp.get("drift_thresholds", {})
        warnings: List[str] = []
        if token_drift:
            warnings.append(f"Token drift: wallet={t['user_tokens_wallet_mirror']} vs roar={t['user_tokens_roar_authoritative']}")
        if abs(ruis) > float(thresholds.get("ruis_warning_eur", 100)):
            warnings.append(f"Grote ruis: €{ruis:.2f} ({'surplus' if ruis > 0 else 'tekort'})")

        return {
            "system_wide": {
                "total_potjes_count": total_potjes_count,
                "total_potjes_capital_eur": round(total_potjes_capital, 2),
                "bitvavo_free_eur": round(bitvavo, 2),
                "ruis_eur": round(ruis, 2),
                "_ruis_note": "Positief = extra vlees op Bitvavo (niet aan potje gekoppeld). Negatief = potjes-waarde > Bitvavo (tekort).",
            },
            "user_drift": {
                "token_drift_detected": token_drift,
                "wallet_mirror": t["user_tokens_wallet_mirror"],
                "roar_authoritative": t["user_tokens_roar_authoritative"],
            },
            "warnings": warnings,
            "healthy": len(warnings) == 0,
        }
