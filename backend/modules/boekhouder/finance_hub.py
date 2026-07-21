"""Finance Hub — dispatcher.

Central orchestrator. Delegeert naar sub-agents op basis van query-type.
Preserveert de bestaande boekhouder-service (weekly_report, close_cycle).
"""
from typing import Any, Dict
from .agents import (
    TokenAgent, PriceAgent, WalletAgent, PotjesAgent,
    BitvavoAgent, ReconAgent, SepaAgent, PersonaAgent,
    LogAgent, ReserveKluisAgent, AutoMintScheduler,
)


class FinanceHub:
    def __init__(self):
        self.token = TokenAgent()
        self.price = PriceAgent()
        self.wallet = WalletAgent()
        self.potjes = PotjesAgent()
        self.bitvavo = BitvavoAgent()
        self.recon = ReconAgent()
        self.sepa = SepaAgent()
        self.persona = PersonaAgent()
        self.log = LogAgent()
        self.reserve = ReserveKluisAgent()
        self.auto_mint = AutoMintScheduler()

    def get_snapshot(self, user_id: str) -> Dict[str, Any]:
        """Volledig financieel beeld — ÉÉN CALL."""
        return {
            "user_id": user_id,
            "token": self.token.snapshot(user_id),
            "price": self.price.snapshot(user_id),
            "wallet": self.wallet.snapshot(user_id),
            "potjes": self.potjes.snapshot(user_id),
            "bitvavo": self.bitvavo.snapshot(user_id),
            "recon": self.recon.snapshot(user_id),
            "sepa": self.sepa.snapshot(user_id),
            "persona": self.persona.snapshot(user_id),
            "log": self.log.snapshot(user_id),
            "reserve_kluis": self.reserve.snapshot(user_id),
            "circulation": self.get_circulation(),
            "valuation": self.get_valuation(),
            "_generated_at": __import__("datetime").datetime.now(
                __import__("datetime").timezone.utc).isoformat(),
        }

    def get_circulation(self) -> Dict[str, Any]:
        """v10_central_bank_001 — Circulation-guard: token ↔ balance ↔ pot in lijn?

        Als drift ≠ 0 → status DRIFT_DETECTED (UI kan flag tonen).
        """
        from modules.core.storage import load_json
        from pathlib import Path
        DATA = Path(__file__).parent.parent.parent / "data"
        roar = load_json(DATA / "roar" / "roar_balances.json",
                         default={"total_supply": 1000000, "treasury_pool": 0, "balances": {}}) or {}
        pots = load_json(DATA / "financial" / "user_potjes.json", default={"users": {}}) or {}
        total_supply = int(roar.get("total_supply", 1000000) or 1000000)
        treasury = int(roar.get("treasury_pool", 0) or 0)
        balances = roar.get("balances", {}) or {}
        balances_sum = sum(int(v or 0) for v in balances.values())
        in_circulation = total_supply - treasury
        total_pots = sum(len((u or {}).get("potjes", []) or []) for u in (pots.get("users") or {}).values())
        circ_drift = in_circulation - balances_sum
        pot_drift = total_pots - balances_sum
        status = "OK" if (circ_drift == 0 and pot_drift == 0) else "DRIFT_DETECTED"
        return {
            "total_supply": total_supply,
            "treasury_pool": treasury,
            "in_circulation": in_circulation,
            "balances_sum": balances_sum,
            "fysieke_potjes": total_pots,
            "balances_per_user": balances,
            "drift": {
                "circulation_vs_balances": circ_drift,
                "potjes_vs_balances": pot_drift,
            },
            "status": status,
            "rule": "1 token = 1 pot; treasury + balances = total_supply",
        }

    def get_valuation(self) -> Dict[str, Any]:
        """v10_central_bank_002 — Live cap-berekening."""
        pr = self.price.compute_price()
        current = float(pr.get("current_price_eur", 10.0) or 10.0)
        base = float(pr.get("base_pot_size_eur", 10.0) or 10.0)
        circ = self.get_circulation()
        in_c = circ["in_circulation"]
        return {
            "pot_price_current_eur": round(current, 4),
            "pot_price_base_eur": base,
            "max_theoretical_cap_eur": round(circ["total_supply"] * base, 2),
            "max_theoretical_cap_dynamic_eur": round(circ["total_supply"] * current, 2),
            "in_circulation_cap_eur": round(in_c * current, 2),
            "in_circulation_baseline_eur": round(in_c * base, 2),
            "backing_ratio_pct": 100.0 if circ["status"] == "OK" else round(
                100.0 * circ["balances_sum"] / max(in_c, 1), 2),
        }

    def get_price(self) -> Dict[str, Any]:
        return self.price.compute_price()

    def get_potjes(self, user_id: str) -> Dict[str, Any]:
        return self.potjes.snapshot(user_id)

    def reconcile(self, user_id: str = "user-001") -> Dict[str, Any]:
        return self.recon.snapshot(user_id)


_hub = FinanceHub()


def get_hub() -> FinanceHub:
    return _hub
