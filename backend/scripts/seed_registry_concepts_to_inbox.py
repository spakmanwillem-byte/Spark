"""Seed alle concept-entries uit de auto-scanner als KB-inbox skeletons.

Gebruikt de meest recente /tmp/registry_scan_*.json en maakt voor elke missende
route een KB-inbox-kaart aan. Idempotent — bestaande begrippen worden
overgeslagen (deep-scan dedupe in kb_service.add_to_inbox).

Elke kaart krijgt duidelijke filter-metadata:
- footnote.bron: "registry_scan_v13"
- footnote.registry_path: "/api/..."
- footnote.registry_method: GET/POST/...
- footnote.registry_module: agenda/notes/...
- _inbox_reason: "registry_missing_kb_card"
- tags: [module, "command", "principe-8"]

Zo kan je in de KB-UI filteren op bron=registry_scan_v13 om exact deze
617 kaarten module-per-module te verwerken.
"""
from __future__ import annotations

import glob
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.core.storage import load_json, save_json  # noqa: E402
from modules.kb_v2 import service as kb_service  # noqa: E402

BASE = Path(__file__).parent.parent / "data" / "knowledge" / "v2"
INBOX = BASE / "knowledge_inbox.json"


def _latest_scan_file() -> Path:
    files = sorted(glob.glob("/tmp/registry_scan_*.json"))
    if not files:
        raise SystemExit("Geen /tmp/registry_scan_*.json gevonden — draai eerst scan_routes_for_registry.py --write")
    return Path(files[-1])


def main() -> None:
    scan_file = _latest_scan_file()
    print(f"Bron: {scan_file}")
    payload = json.loads(scan_file.read_text())
    entries = payload.get("concept_entries", [])
    print(f"Concept-entries: {len(entries)}")

    now = datetime.now(timezone.utc).isoformat()

    # Backup
    from shutil import copy2
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    bak = INBOX.with_suffix(INBOX.suffix + f".bak_registry_seed_{ts}")
    copy2(INBOX, bak)
    print(f"Backup: {bak.name}")

    created = 0
    existing = 0
    skipped = 0

    for entry in entries:
        cmd_id = entry.get("id")
        if not cmd_id:
            skipped += 1
            continue

        # Add via kb_service — deep-scan dedupe zorgt dat we niks dubbelen
        r = kb_service.add_to_inbox(
            begrip=cmd_id,
            source="registry_scan_v13",
            user_id="user-000",
        )
        if not r.get("success"):
            skipped += 1
            continue
        if r.get("existing"):
            existing += 1
            continue

        # Verrijk footnote/tags/_inbox_reason op de vers-aangemaakte kaart
        kaart = r.get("kaart") or {}
        kaart_id = kaart.get("id")
        if not kaart_id:
            continue

        # Direct in-place mutatie in inbox-file (kb_service heeft geen partial-edit API)
        data = load_json(INBOX, default={"kaarten": []})
        module = (entry.get("source") or "unknown").split(".")[0]
        for k in data.get("kaarten", []):
            if k.get("id") == kaart_id:
                # Footnote
                fn = k.setdefault("footnote", {})
                fn["bron"] = "registry_scan_v13"
                fn["aangemaakt_door"] = "registry_seed_script"
                fn["aangemaakt_op"] = now
                fn["registry_path"] = entry.get("path")
                fn["registry_method"] = entry.get("method")
                fn["registry_module"] = module
                fn["registry_admin_only"] = entry.get("admin_only", False)
                fn["registry_gradatie_min"] = entry.get("gradatie_min", 2)
                fn["registry_source"] = entry.get("source")
                fn["vertrouwen"] = 0.2  # laag — nog niet ingevuld
                fn["needs_kb_fill"] = True
                # Reason waarom deze in inbox staat
                k["_inbox_reason"] = "registry_missing_kb_card"
                # Tags
                base_tags = [module, "command", "principe-8"]
                if entry.get("admin_only"):
                    base_tags.append("admin_only")
                existing_tags = set(k.get("tags") or [])
                k["tags"] = sorted(existing_tags | set(base_tags))
                break
        save_json(INBOX, data)
        created += 1

        if created % 50 == 0:
            print(f"  … {created} aangemaakt")

    print()
    print("=== Resultaat ===")
    print(f"Nieuw aangemaakt: {created}")
    print(f"Reeds aanwezig (skipped): {existing}")
    print(f"Skipped (overig): {skipped}")

    # Herbereken inbox-totaal
    data = load_json(INBOX, default={"kaarten": []})
    print(f"Inbox totaal na seed: {len(data.get('kaarten', []))}")


if __name__ == "__main__":
    main()
