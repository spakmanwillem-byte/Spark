"""TokenAgent — ROAR balance, supply, mint/burn."""
from typing import Any, Dict
from modules.core.storage import load_json
from .base_agent import BaseFinanceAgent, DATA


class TokenAgent(BaseFinanceAgent):
    topic = "token_agent"

    def _load_roar(self) -> Dict[str, Any]:
        return load_json(DATA / "roar" / "roar_balances.json", default={}) or {}

    def snapshot(self, user_id: str) -> Dict[str, Any]:
        r = self._load_roar()
        balances = r.get("balances", {}) or {}
        # Fallback: user_wallets (display-mirror) — als roar leeg maar wallets vol → drift
        uw = load_json(DATA / "wallet" / "user_wallets.json",
                       default={"user_wallets": {}}) or {}
        wallets = uw.get("user_wallets", {})
        wallet_tokens = (wallets.get(user_id, {}) or {}).get("spark_tokens", 0)
        roar_tokens = balances.get(user_id, 0)
        spark_bonus = r.get("spark_bonus", {}).get("balance", 0) if user_id == "user-000" else 0
        return {
            "user_tokens_roar_authoritative": roar_tokens,
            "user_tokens_wallet_mirror": wallet_tokens,
            "spark_bonus": spark_bonus,
            "total_supply": r.get("total_supply", 1000000),
            "treasury_pool": r.get("treasury_pool", 0),
            "minted_total": r.get("total_supply", 1000000) - r.get("treasury_pool", 0),
            "drift_detected": roar_tokens != wallet_tokens,
        }
