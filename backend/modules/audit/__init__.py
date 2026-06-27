"""
Audit Service (v6_audit_001) — Maintenance scans voor Spark Core
==================================================================
Twee scans (uit v1 backlog terug):
  1. weak_trigger_scan() → vind KB-triggers met <10-char of generieke responses
  2. self_learning_audit() → verifieer dat shadow-observer events correct loggen

Endpoints:
  GET  /api/audit/weak-triggers
  GET  /api/audit/self-learning
  GET  /api/audit/summary

Resultaten worden ook gepersisteerd in:
  /data/system/audit_reports/{type}_{timestamp}.json
"""
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any
from collections import Counter

from fastapi import APIRouter
from modules.core.storage import load_json, save_json

router = APIRouter(prefix="/audit", tags=["audit"])

DATA = Path("/app/backend/data")
KNOWLEDGE_FILE = DATA / "knowledge" / "learned_knowledge" / "knowledge_base.json"  # V1 legacy
KBV2_DIR = DATA / "knowledge" / "v2"
SHADOW_OBSERVATIONS = DATA / "system" / "shadow_observations.jsonl"
AUDIT_REPORTS = DATA / "system" / "audit_reports"

MIN_RESPONSE_LEN = 10
GENERIC_PATTERNS = ["weet ik niet", "geen idee", "hmm", "uhh", "...", "ja", "nee", "ok"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_kbv2_entries():
    """v6_v2_first_001 — V2 lades + inbox als platte lijst."""
    out = []
    for fname in ["knowledge_v2_doen", "knowledge_v2_weten",
                  "knowledge_v2_voelen", "knowledge_v2_spreken",
                  "knowledge_inbox"]:
        d = load_json(KBV2_DIR / f"{fname}.json", default={"kaarten": []})
        out.extend(d.get("kaarten", []) or [])
    return out


# ============================================================
# WEAK TRIGGER SCAN
# ============================================================
def weak_trigger_scan() -> Dict[str, Any]:
    """Scan KB v2 entries voor zwakke responses (< MIN_RESPONSE_LEN of generiek).

    v6_v2_first_001 — V2 is bron. Kaart-structuur: {begrip, lade, lagen, tags, ...}
    "Response" = lagen.laag1 (de korte uitleg).
    """
    entries = _load_kbv2_entries()
    if not entries:
        return {"error": "V2 kennisbank leeg/niet gevonden", "scanned": 0}
    weak: List[Dict[str, Any]] = []
    generic: List[Dict[str, Any]] = []
    no_tags: List[str] = []
    total = 0
    for data in entries:
        if not isinstance(data, dict):
            continue
        total += 1
        begrip = (data.get("begrip") or "").strip() or "(geen begrip)"
        lagen = data.get("lagen") or {}
        resp = (lagen.get("laag1") or "").strip()
        if not resp:
            weak.append({"begrip": begrip, "reason": "geen laag1"})
            continue
        if len(resp) < MIN_RESPONSE_LEN:
            weak.append({"begrip": begrip, "reason": f"te kort ({len(resp)} chars)", "response": resp})
            continue
        if resp.lower().strip(" .!?") in GENERIC_PATTERNS:
            generic.append({"begrip": begrip, "response": resp})
        # Bonus: kaarten zonder tags
        tags = data.get("tags") or []
        if not tags:
            no_tags.append(begrip)

    report = {
        "type": "weak_trigger_scan",
        "scanned_at": _now(),
        "total_entries": total,
        "weak_count": len(weak),
        "generic_count": len(generic),
        "no_tags_count": len(no_tags),
        "weak_pct": round(len(weak) * 100 / max(1, total), 2),
        "weak_top_25": weak[:25],
        "generic_top_25": generic[:25],
        "no_tags_top_25": no_tags[:25],
    }
    _save_report("weak_triggers", report)
    return report


# ============================================================
# SELF-LEARNING AUDIT
# ============================================================
def self_learning_audit() -> Dict[str, Any]:
    """Check dat shadow observer recent events heeft + variatie qua kind."""
    report = {
        "type": "self_learning_audit",
        "scanned_at": _now(),
        "shadow_observations_exists": SHADOW_OBSERVATIONS.exists(),
    }
    if not SHADOW_OBSERVATIONS.exists():
        report["status"] = "geen-observations-file"
        report["warnings"] = ["Shadow observer heeft nog geen events geschreven."]
        _save_report("self_learning", report)
        return report

    # Lees laatste N regels van JSONL
    try:
        with open(SHADOW_OBSERVATIONS, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        report["status"] = "read-error"
        report["error"] = str(e)
        _save_report("self_learning", report)
        return report

    last_lines = lines[-500:]  # laatste 500 events
    import json as _json
    kinds = Counter()
    parsed_count = 0
    parse_errors = 0
    latest_ts = None
    for ln in last_lines:
        ln = ln.strip()
        if not ln:
            continue
        try:
            ev = _json.loads(ln)
            parsed_count += 1
            kinds[ev.get("kind") or ev.get("type") or "unknown"] += 1
            ts = ev.get("ts") or ev.get("timestamp")
            if ts and (latest_ts is None or ts > latest_ts):
                latest_ts = ts
        except Exception:
            parse_errors += 1

    # Verifieer recentheid
    is_recent = False
    if latest_ts:
        try:
            latest_dt = datetime.fromisoformat(latest_ts.replace("Z", "+00:00"))
            age_h = (datetime.now(timezone.utc) - latest_dt).total_seconds() / 3600
            is_recent = age_h < 48
            report["last_event_age_hours"] = round(age_h, 1)
        except Exception:
            pass

    report.update({
        "total_lines": len(lines),
        "scanned_lines": len(last_lines),
        "parsed_count": parsed_count,
        "parse_errors": parse_errors,
        "latest_ts": latest_ts,
        "is_recent_48h": is_recent,
        "kind_counts": dict(kinds.most_common(15)),
        "unique_kinds": len(kinds),
    })

    warnings = []
    if parse_errors > 0:
        warnings.append(f"{parse_errors} JSONL-regels niet parseerbaar")
    if not is_recent:
        warnings.append("Geen events in laatste 48 uur — shadow observer mogelijk uitgevallen")
    if len(kinds) < 3:
        warnings.append(f"Weinig event-variatie ({len(kinds)} unique kinds) — modules loggen mogelijk niet")
    report["warnings"] = warnings
    report["status"] = "healthy" if not warnings else "warning"
    _save_report("self_learning", report)
    return report


# ============================================================
# REPORTS
# ============================================================
def _save_report(name: str, report: dict):
    AUDIT_REPORTS.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    save_json(AUDIT_REPORTS / f"{name}_{ts}.json", report)


@router.get("/weak-triggers")
async def get_weak_triggers():
    return weak_trigger_scan()


@router.get("/self-learning")
async def get_self_learning_audit():
    return self_learning_audit()


@router.get("/summary")
async def get_summary():
    """Snelle gecombineerde summary (geen volle scan, alleen aantallen)."""
    wt = weak_trigger_scan()
    sl = self_learning_audit()
    return {
        "weak_triggers": {
            "total": wt.get("total_entries"),
            "weak": wt.get("weak_count"),
            "generic": wt.get("generic_count"),
            "weak_pct": wt.get("weak_pct"),
        },
        "self_learning": {
            "status": sl.get("status"),
            "warnings": sl.get("warnings", []),
            "unique_kinds": sl.get("unique_kinds"),
            "last_event_age_hours": sl.get("last_event_age_hours"),
        },
    }
