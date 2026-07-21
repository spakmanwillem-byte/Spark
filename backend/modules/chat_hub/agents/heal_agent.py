"""HealAgent — detecteert kapotte/drift-status, stelt backup-restore voor.

meta: leaf, guardrail-class (draait ook zonder trigger als proactive check).
Doet NIET auto-restore — Willem-in-the-loop.
"""
from __future__ import annotations
from typing import Any, Dict, List
from pathlib import Path
import json
from datetime import datetime, timezone
from ..base.agent_contract import AgentContract

DATA = Path(__file__).resolve().parent.parent.parent.parent / "data"


class HealAgent(AgentContract):
    naam: str = "heal"
    klasse: str = "guardrail"
    rol: str = "leaf"
    parent: str = "chat_hub_master"
    doel: str = "Detecteert drift/kapotte state, stelt restore uit backups voor."
    gradatie_min: int = 3
    kost_ms_estimate: int = 100
    triggers: List[str] = [
        r"\b(heal|zelf[- ]?herstel|self[- ]?heal)\b",
        r"\bhealth[- ]?check\b",
        r"\bben\s+je\s+ok\b",
        r"\balles\s+goed\b(?=.*(spark|systeem))",
        r"\bdrift[- ]?(detectie|check|status)\b",
        r"\bkan\s+je\s+jezelf\s+(herstellen|checken)\b",
    ]
    footnote: Dict[str, Any] = {
        "generated_by": "v10_chat_hub_fase1", "created": "2026-07-21",
        "note": "Detectie-only in Fase 1. Auto-restore = Fase 2.",
    }

    def run(self, text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        return self.health_check()

    def health_check(self) -> Dict[str, Any]:
        """Systematische check — retourneert status per categorie."""
        checks = []

        # 1. Boekhouder-drift
        try:
            from modules.boekhouder.finance_hub import get_hub
            circ = get_hub().get_circulation()
            checks.append({
                "check": "boekhouder_circulation",
                "status": circ.get("status"),
                "drift": circ.get("drift"),
                "ok": circ.get("status") == "OK",
            })
        except Exception as e:
            checks.append({"check": "boekhouder_circulation", "ok": False, "error": str(e)})

        # 2. Papertrail-integrity (laatste 5 events)
        try:
            from modules.boekhouder.agents.log_agent import LogAgent
            import hashlib
            evts = LogAgent().lookup(topic=None, limit=5)
            integrity_ok = True
            for e in evts or []:
                chain = f"{e['hash_prev']}|{e['event_id']}|{e['type']}|{e['timestamp']}|{json.dumps(e['data'], sort_keys=True)}"
                if hashlib.sha256(chain.encode()).hexdigest()[:16] != e.get("event_hash"):
                    integrity_ok = False; break
            checks.append({"check": "papertrail_integrity",
                           "ok": integrity_ok, "events_checked": len(evts or [])})
        except Exception as e:
            checks.append({"check": "papertrail_integrity", "ok": False, "error": str(e)})

        # 3. Beschikbare backups
        backup_dir = DATA / "_backups"
        recent_backups = []
        if backup_dir.exists():
            for p in sorted(backup_dir.iterdir(), key=lambda x: x.name, reverse=True)[:5]:
                if p.is_dir():
                    recent_backups.append({
                        "name": p.name,
                        "files": len(list(p.rglob("*.json"))),
                    })

        all_ok = all(c.get("ok") for c in checks)
        return {
            "overall_status": "HEALTHY" if all_ok else "DRIFT_DETECTED",
            "checks": checks,
            "recent_backups": recent_backups,
            "backup_count": len(list(backup_dir.iterdir())) if backup_dir.exists() else 0,
            "suggestion": None if all_ok else (
                "Overweeg restore uit meest recente backup: "
                + (recent_backups[0]["name"] if recent_backups else "geen backups gevonden")
            ),
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }
