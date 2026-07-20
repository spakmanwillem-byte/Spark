"""WalletAgent — EUR balance + deposits."""
from typing import Any, Dict
from modules.core.storage import load_json
from .base_agent import BaseFinanceAgent, DATA


class WalletAgent(BaseFinanceAgent):
    topic = "wallet_agent"

    def snapshot(self, user_id: str) -> Dict[str, Any]:
        w = load_json(DATA / "wallet" / "wallets.json", default={}) or {}
        wallets = (w.get("wallets") or {})
        user_w = wallets.get(user_id, {}) or {}
        transactions = w.get("transactions", []) or []
        recent = [t for t in transactions if t.get("user_id") == user_id][-5:]
        return {
            "balance_eur": float(user_w.get("balance", 0) or 0),
            "total_deposited_eur": float(user_w.get("total_deposited", 0) or 0),
            "total_withdrawn_eur": float(user_w.get("total_withdrawn", 0) or 0),
            "recent_transactions": recent,
            "transaction_count": sum(1 for t in transactions if t.get("user_id") == user_id),
        }
