"""Finance Hub — dispatcher.

Central orchestrator. Delegeert naar sub-agents op basis van query-type.
Preserveert de bestaande boekhouder-service (weekly_report, close_cycle).
"""
from typing import Any, Dict
from .agents import (
    TokenAgent, PriceAgent, WalletAgent, PotjesAgent,
    BitvavoAgent, ReconAgent, SepaAgent, PersonaAgent,
    LogAgent, ReserveKluisAgent,
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
            "_generated_at": __import__("datetime").datetime.now(
                __import__("datetime").timezone.utc).isoformat(),
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
