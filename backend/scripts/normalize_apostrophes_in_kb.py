"""Dunne CLI-wrapper rond modules.kb_v2.apostrophe_normalizer.

De echte logica staat nu in de module zodat de admin-route én de CLI
dezelfde code gebruiken (v13c_apostrophe_normalizer_001).

Gebruik:
    python3 scripts/normalize_apostrophes_in_kb.py            # commit
    python3 scripts/normalize_apostrophes_in_kb.py --dry-run  # alleen tellen
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.kb_v2.apostrophe_normalizer import normalize_apostrophes_in_kb  # noqa: E402


def main() -> None:
    dry_run = "--dry-run" in sys.argv
    r = normalize_apostrophes_in_kb(dry_run=dry_run)
    print(f"dry_run: {r['dry_run']}")
    print(f"Tags met unicode-apostrof genormaliseerd: {r['tags_fixed']}")
    print(f"Begrippen hernoemd: {len(r['begrippen_renamed'])}")
    for b in r["begrippen_renamed"]:
        print(f"  [{b['kaart_id']}] {b['from']!r} → {b['to']!r}")
    print(f"Index-sleutels bijgewerkt: {len(r['index_keys_updated'])}")
    for k in r["index_keys_updated"]:
        print(f"  {k['from']!r} → {k['to']!r}  ({k['action']})")
    print(f"Files changed: {r['files_changed']}")
    if r["backups"]:
        print(f"Backups: {len(r['backups'])} bestanden")


if __name__ == "__main__":
    main()
