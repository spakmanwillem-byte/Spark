"""PapertrailAgent — leest hash-chained events uit boekhouder/logs/*.

meta: leaf, info_lookup, gradatie_min=3 (iedereen mag audit-log zien).
footnote: gebruikt LogAgent().lookup(topic, limit). Detecteert "wat is er gemint",
"papertrail", "audit", "welke deposits", "boekhouding log".
"""
from __future__ import annotations
from typing import Any, Dict, List
from ..base.agent_contract import AgentContract


class PapertrailAgent(AgentContract):
    naam: str = "papertrail"
    klasse: str = "info_lookup"
    rol: str = "leaf"
    parent: str = "chat_hub_master"
    doel: str = "Leest hash-chained events uit boekhouder/logs (mint, drift_fix, deposit)."
    gradatie_min: int = 3
    kost_ms_estimate: int = 40
    triggers: List[str] = [
        r"\bpaper\s?trail\b",
        r"\baudit\s?log\b",
        r"\b(wat\s+is\s+er\s+)?gemint\b",
        r"\b(mint|mints|minted)\b(?!.*(hoe|wat is))",
        r"\bboekhouding[- ]?log\b",
        r"\bwelke\s+(deposits?|stortingen)\b",
        r"\bdrift[- ]?(events?|log)\b",
        r"\bwat\s+is\s+er\s+(gestort|gemint|gebrand)\b",
        r"\btoon\s+(de\s+)?(paper\s?trail|logs?|events?)\b",
    ]
    footnote: Dict[str, Any] = {
        "generated_by": "v10_chat_hub_fase1", "created": "2026-07-21",
        "source_module": "modules.boekhouder.agents.log_agent",
    }

    def run(self, text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Detecteer topic + roep LogAgent aan."""
        from modules.boekhouder.agents.log_agent import LogAgent
        low = (text or "").lower()

        # Topic-detectie
        topic = None
        if any(w in low for w in ["mint", "gemint"]): topic = "mint"
        elif any(w in low for w in ["drift", "correctie", "burn"]): topic = "drift_fix"
        elif any(w in low for w in ["deposit", "storting", "tikkie"]): topic = "deposit"

        events = LogAgent().lookup(topic=topic, limit=10)

        # Hash-chain integrity check (spot-check laatste 3)
        integrity_ok = True
        import hashlib, json as _j
        for e in (events or [])[-3:]:
            chain_input = f"{e['hash_prev']}|{e['event_id']}|{e['type']}|{e['timestamp']}|{_j.dumps(e['data'], sort_keys=True)}"
            expected = hashlib.sha256(chain_input.encode()).hexdigest()[:16]
            if expected != e.get("event_hash"):
                integrity_ok = False
                break

        return {
            "topic": topic or "alle",
            "event_count": len(events or []),
            "events": [{
                "type": e.get("type"), "actor": e.get("actor"),
                "timestamp": e.get("timestamp", "")[:19],
                "summary": _summarize_event(e),
                "event_id_short": e.get("event_id", "")[:8],
            } for e in (events or [])],
            "integrity_ok": integrity_ok,
        }


def _summarize_event(e: Dict[str, Any]) -> str:
    d = e.get("data", {}) or {}
    t = e.get("type", "")
    if t.startswith("mint"):
        return f"{d.get('n_tokens',1)}× mint @ €{d.get('price_per_token_eur','?')} src={d.get('source','?')}"
    if t == "historical_drift_burn":
        return f"burn {d.get('n_tokens_burned','?')} tokens"
    if t == "pot_token_alignment":
        return f"alignment {d.get('from','?')} → {d.get('to','?')} ({d.get('n_tokens','?')} token)"
    if t == "baseline_reset":
        return f"baseline reset €{d.get('previous_baseline_eur','?')} → €{d.get('new_baseline_eur','?')}"
    if t == "pre_eikpunt_archive":
        return f"archief {d.get('tikkie_topups_count',0)} tikkies + {d.get('deposits_count',0)} deposits"
    return f"{t} — {list(d.keys())[:3]}"
