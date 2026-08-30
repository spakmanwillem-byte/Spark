"""Move de 12 agent-layer kaarten van inbox → juiste lade + update index.

Regel: agents/architectuur-concepten → weten; handelings-fasen → doen.
"""
from __future__ import annotations

import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.core.storage import load_json, save_json  # noqa: E402

BASE = Path(__file__).parent.parent / "data" / "knowledge" / "v2"
INBOX = BASE / "knowledge_inbox.json"
WETEN = BASE / "knowledge_v2_weten.json"
DOEN = BASE / "knowledge_v2_doen.json"
INDEX = BASE / "knowledge_index.json"

# begrip → doel-lade
ASSIGNMENT = {
    # agents (concepten over systeem-modules) → weten
    "task_agent": "weten",
    "admin_command_agent": "weten",
    "personal_agent": "weten",
    "spark_pulse_agent": "weten",
    # architectuur-concepten & data-artefacten → weten
    "principe-8": "weten",
    "spark-architectuur": "weten",
    "command_registry": "weten",
    "privacy_matrix": "weten",
    "self_awareness": "weten",
    "observability": "weten",
    # handelings-fasen → doen
    "intent-uitvoering": "doen",
    "compose": "doen",
}


def _backup(p: Path, tag: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    bak = p.with_suffix(p.suffix + f".bak_{tag}_{ts}")
    shutil.copy2(p, bak)
    print(f"  backup: {bak.name}")


def main() -> None:
    now = datetime.now(timezone.utc).isoformat()

    print("Backups maken…")
    for p in (INBOX, WETEN, DOEN, INDEX):
        _backup(p, "agent_layer_move")

    inbox = load_json(INBOX, default={"kaarten": []})
    weten = load_json(WETEN, default={"kaarten": []})
    doen = load_json(DOEN, default={"kaarten": []})
    index = load_json(INDEX, default={"entries": {}})

    inbox_kaarten = inbox.get("kaarten", [])
    to_move: list = []
    keep: list = []
    for k in inbox_kaarten:
        b = (k.get("begrip") or "").lower().strip()
        if b in ASSIGNMENT:
            to_move.append((b, k))
        else:
            keep.append(k)

    moved_summary = []
    for begrip, k in to_move:
        target_lade = ASSIGNMENT[begrip]
        # Muteer kaart
        k["lade"] = target_lade
        k["status"] = "curated"
        fn = k.setdefault("footnote", {})
        fn["ingedeeld_door"] = "e1_agent_layer_move"
        fn["ingedeeld_op"] = now
        # inbox_reason is niet meer relevant zodra in lade
        k.pop("_inbox_reason", None)
        # Append naar juiste lade
        if target_lade == "weten":
            weten.setdefault("kaarten", []).append(k)
        else:
            doen.setdefault("kaarten", []).append(k)
        # Update index-entry
        entries = index.setdefault("entries", {})
        entries[begrip] = {
            "kaart_id": k.get("id"),
            "lade": target_lade,
            "has_lagen": [lk for lk, lv in (k.get("lagen") or {}).items() if lv],
            "last_updated": now,
        }
        moved_summary.append((begrip, target_lade, k.get("id")))

    inbox["kaarten"] = keep
    # Index-totalen bijwerken indien aanwezig
    if "total" in index:
        index["total"] = len(index.get("entries", {}))
    if "entry_count" in index:
        index["entry_count"] = len(index.get("entries", {}))
    index["rebuilt_at"] = now
    index["rebuilt_by"] = "e1_agent_layer_move"

    save_json(INBOX, inbox)
    save_json(WETEN, weten)
    save_json(DOEN, doen)
    save_json(INDEX, index)

    print("\n=== Verplaatst ===")
    for begrip, lade, kid in moved_summary:
        print(f"  {begrip:24s} → {lade:6s} ({kid})")
    print(f"\nTotaal: {len(moved_summary)} kaarten uit inbox verplaatst")
    print(f"Inbox rest: {len(keep)} kaarten")


if __name__ == "__main__":
    main()
