"""
Synapse — Aggregator (v6_synapse_001)
======================================
Bundelt alle _meta.json in één SYNAPSE.json op /app/memory/SYNAPSE.json
zodat:
  - Spark hem snel kan lezen in chat ("wat hebben we?")
  - Jij hem kan openen voor één-blik-overzicht
  - UI Synapse-tab (F6) een snelle datasource heeft
"""
from modules.core.paths import SPARK_ROOT  # v14_spark_root_001
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

from modules.core.storage import save_json
from .scanner import scan_all

SYNAPSE_FILE = Path(f"{SPARK_ROOT}/memory/SYNAPSE.json")


def _summary(grouped: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    total = 0
    by_status: Dict[str, int] = {}
    by_type: Dict[str, int] = {}
    endpoints_total = 0
    for group_name, group in grouped.items():
        for path, meta in group.items():
            total += 1
            st = meta.get("status", "unknown")
            ct = meta.get("container_type", "unknown")
            by_status[st] = by_status.get(st, 0) + 1
            by_type[ct] = by_type.get(ct, 0) + 1
            endpoints_total += len(meta.get("endpoints") or [])
    return {
        "total_containers": total,
        "by_status": by_status,
        "by_container_type": by_type,
        "total_endpoints_detected": endpoints_total,
    }


def build_synapse() -> Dict[str, Any]:
    grouped = scan_all()
    summary = _summary(grouped)
    doc = {
        "_arch_ref": "v6_synapse_001",
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": summary,
        "tree": grouped,
    }
    save_json(SYNAPSE_FILE, doc)
    return doc
