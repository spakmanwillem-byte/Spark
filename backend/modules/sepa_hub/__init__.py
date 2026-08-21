"""v13_sepa_hub_001 — SEPA Hub (bank-formaat ↔ intern).

Aparte hub omdat SEPA een universele vertaler is die niet aan boekhouder-
module vast hoeft te zitten. Ook bruikbaar voor wallet-topups, shop-payouts,
of toekomstige modules zonder boekhouder-dependency.

Publieke API:
    SepaHub.parse_camt053(xml_text) -> {transactions, statements}
    SepaHub.parse_mt940(text)       -> {transactions, iban}
    SepaHub.generate_pain001(...)   -> XML str
    SepaHub.reconcile(book_id, imported_tx) -> {matched, unmatched, added}

Data-root (voor toekomstige logs/reconciliaties):
    /data/sepa/imports/<iso-date>_<sha>.jsonl
    /data/sepa/exports/<msg_id>.xml
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from . import parsers as _parsers

DATA_ROOT = Path(__file__).parent.parent.parent / "data" / "sepa"
DATA_ROOT.mkdir(parents=True, exist_ok=True)
(DATA_ROOT / "imports").mkdir(parents=True, exist_ok=True)
(DATA_ROOT / "exports").mkdir(parents=True, exist_ok=True)


class SepaHub:
    """Centrale SEPA-vertaler. Stateless voor parsing/generatie; kan later
    stateful worden (reconcile-cache, batch-log)."""

    @staticmethod
    def parse_camt053(xml_text: str) -> Dict:
        return _parsers.parse_camt053(xml_text)

    @staticmethod
    def parse_mt940(text: str) -> Dict:
        return _parsers.parse_mt940(text)

    @staticmethod
    def generate_pain001(
        debtor_naam: str,
        debtor_iban: str,
        payments: List[Dict],
        message_id: Optional[str] = None,
        initiator_naam: Optional[str] = None,
    ) -> str:
        return _parsers.generate_pain001(
            debtor_naam=debtor_naam,
            debtor_iban=debtor_iban,
            payments=payments,
            message_id=message_id,
            initiator_naam=initiator_naam,
        )

    @staticmethod
    def reconcile(book_id: str, imported_transactions: List[Dict]) -> Dict:
        """Match geïmporteerde bank-tx met bestaande boek-entries op
        datum+bedrag+iban. Returnt aantallen; consumers voegen zelf toe.
        (Skeleton — echte matching-heuristics komen in fase 6.)
        """
        # Import hier ipv top-level om circular imports te vermijden
        from modules.boekhouder import books as book_svc
        existing = book_svc.list_entries(book_id, limit=100_000)
        matched, unmatched = [], []
        for tx in imported_transactions:
            key = (
                round(float(tx.get("amount_eur", 0)), 2),
                (tx.get("ts") or "")[:10],
                (tx.get("tegenrekening_iban") or "").replace(" ", "").upper(),
            )
            hit = None
            for e in existing:
                ekey = (
                    round(float(e.get("amount_eur", 0)), 2),
                    (e.get("ts") or "")[:10],
                    (e.get("tegenrekening_iban") or "").replace(" ", "").upper(),
                )
                if ekey == key:
                    hit = e
                    break
            (matched if hit else unmatched).append(tx)
        return {
            "matched": len(matched),
            "unmatched": len(unmatched),
            "unmatched_tx": unmatched,
        }


_hub_singleton: Optional[SepaHub] = None


def get_hub() -> SepaHub:
    global _hub_singleton
    if _hub_singleton is None:
        _hub_singleton = SepaHub()
    return _hub_singleton
