"""PersonaAgent — de 'Boekhouder' chat-persona.

Data komt uit andere sub-agents. Deze agent formuleert alleen NL-teksten
en voert de weekly_report / close_cycle uit (bestaande logica in service.py).
"""
from typing import Any, Dict
from .base_agent import BaseFinanceAgent


class PersonaAgent(BaseFinanceAgent):
    topic = "persona_agent"

    def snapshot(self, user_id: str) -> Dict[str, Any]:
        bp = self.blueprint()
        return {
            "chat_style": bp.get("chat_style", "warm, precies, cijfergericht in NL"),
            "topic_ownership": "boekhouden, financieel overzicht, weekrapporten",
            "delegates_to": ["token_agent", "wallet_agent", "potjes_agent", "recon_agent"],
        }

    def format_snapshot_for_chat(self, snapshot: Dict[str, Any], user_naam: str) -> str:
        """Format de volledige hub-snapshot als NL chat-antwoord."""
        t = snapshot.get("token", {})
        w = snapshot.get("wallet", {})
        p = snapshot.get("potjes", {})
        pr = snapshot.get("price", {})
        r = snapshot.get("recon", {})

        lines = [f"📊 **Financieel overzicht — {user_naam}**", ""]
        lines.append(f"💰 EUR-saldo: **€{w.get('balance_eur', 0):.2f}**")
        lines.append(f"📥 Ooit gestort: €{w.get('total_deposited_eur', 0):.2f}")
        lines.append("")
        lines.append(f"🪙 ROAR tokens: **{t.get('user_tokens_roar_authoritative', 0)}** (autoritatief)")
        if t.get("drift_detected"):
            lines.append(f"⚠️ Drift: wallet-mirror toont {t.get('user_tokens_wallet_mirror')} — moet ge-synct")
        lines.append(f"📈 Token-prijs (live): €{pr.get('current_price_eur', 0):.2f}"
                     + (" (floor)" if pr.get("at_floor") else ""))
        lines.append("")
        lines.append(f"🏺 Potjes: **{p.get('potjes_count', 0)}** × €{pr.get('current_price_eur', 0):.2f} "
                     f"= €{p.get('total_capital_dynamic_eur', 0):.2f}")
        lines.append(f"💵 Bitvavo saldo: €{snapshot.get('bitvavo', {}).get('bitvavo_free_eur', 0):.2f}")
        ruis = r.get("system_wide", {}).get("ruis_eur", 0)
        lines.append(f"🍖 Ruis (extra vlees): €{ruis:+.2f}")
        if r.get("warnings"):
            lines.append("")
            lines.append("⚠️ Waarschuwingen:")
            for wrn in r.get("warnings", []):
                lines.append(f"  • {wrn}")
        return "\n".join(lines)
