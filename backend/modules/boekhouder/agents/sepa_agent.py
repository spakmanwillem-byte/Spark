"""SepaAgent — PLACEHOLDER voor toekomstige SEPA/bankrekening-integratie.

Status: stub. Endpoints komen later.
"""
from typing import Any, Dict
from .base_agent import BaseFinanceAgent


class SepaAgent(BaseFinanceAgent):
    topic = "sepa_agent"

    def snapshot(self, user_id: str) -> Dict[str, Any]:
        return {
            "status": "placeholder",
            "coming_soon": True,
            "planned_features": [
                "SEPA-transactie import via bankstatement",
                "IBAN-koppeling per user (nu al zichtbaar in profile.json)",
                "Kruis-referentie met wallets.json Tikkie-deposits",
                "Boekhouden-tab met privé kasboek",
            ],
            "_note": "Stub-agent. Placeholder in UI 'Boekhouden' tab.",
        }
