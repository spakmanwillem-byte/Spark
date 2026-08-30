"""Normaliseer unicode-apostrofen in bestaande KB-data.

Toepassing:
- Tags: elke tag met unicode-apostrof (’‘´`) wordt vervangen door rechte '.
- Begrippen: kaarten waarvan het begrip een unicode-apostrof bevat worden
  hernoemd (rechte apostrof).
- Index-entries mee updaten.

Idempotent + backups.
"""
from __future__ import annotations

import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.core.storage import load_json, save_json  # noqa: E402
from modules.kb_v2.tag_sanitizer import _normalize_apostrophes, sanitize_tag_list  # noqa: E402

BASE = Path(__file__).parent.parent / "data" / "knowledge" / "v2"
KB_FILES = [
    BASE / "knowledge_inbox.json",
    BASE / "knowledge_v2_weten.json",
    BASE / "knowledge_v2_doen.json",
    BASE / "knowledge_v2_spreken.json",
    BASE / "knowledge_v2_voelen.json",
]
INDEX = BASE / "knowledge_index.json"


def _backup(p: Path, tag: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    bak = p.with_suffix(p.suffix + f".bak_{tag}_{ts}")
    shutil.copy2(p, bak)


def main() -> None:
    now = datetime.now(timezone.utc).isoformat()

    print("Backups…")
    for p in KB_FILES + [INDEX]:
        _backup(p, "apostrof_normalize")

    total_tags_fixed = 0
    total_begrippen_fixed = 0
    renamed_pairs: list[tuple[str, str, str]] = []  # (old, new, id)

    for p in KB_FILES:
        data = load_json(p, default={"kaarten": []})
        changed = False
        for k in data.get("kaarten", []):
            # 1) Tags
            tags_before = k.get("tags") or []
            new_tags = []
            fixed_here = 0
            for t in tags_before:
                if not isinstance(t, str):
                    new_tags.append(t)
                    continue
                normalized = _normalize_apostrophes(t)
                if normalized != t:
                    fixed_here += 1
                new_tags.append(normalized)
            if fixed_here:
                # Dedupe na normalisatie (misschien staat nu 'foto's' 2x)
                seen = set()
                deduped = []
                for t in new_tags:
                    key = t.lower()
                    if key in seen:
                        continue
                    seen.add(key)
                    deduped.append(t)
                k["tags"] = deduped
                total_tags_fixed += fixed_here
                changed = True

            # 2) Begrip
            b = k.get("begrip") or ""
            b_norm = _normalize_apostrophes(b)
            if b_norm != b:
                renamed_pairs.append((b, b_norm, k.get("id", "?")))
                k["begrip"] = b_norm
                fn = k.setdefault("footnote", {})
                fn.setdefault("history", []).append({
                    "at": now,
                    "by": "e1_apostrof_normalize",
                    "action": "begrip_rename",
                    "from": b,
                    "to": b_norm,
                })
                total_begrippen_fixed += 1
                changed = True
        if changed:
            save_json(p, data)
            print(f"  updated {p.name}")

    # 3) Index bijwerken: sleutels met unicode-apostrof migreren
    index = load_json(INDEX, default={"entries": {}})
    entries = index.get("entries", {})
    key_renames = []
    for key in list(entries.keys()):
        new_key = _normalize_apostrophes(key)
        if new_key != key:
            # Merge: als new_key al bestaat, prefereer de bestaande maar log
            if new_key in entries:
                key_renames.append((key, new_key, "MERGED_INTO_EXISTING"))
                del entries[key]
            else:
                entries[new_key] = entries.pop(key)
                key_renames.append((key, new_key, "RENAMED"))
    if key_renames:
        index["rebuilt_at"] = now
        index["rebuilt_by"] = "e1_apostrof_normalize"
        save_json(INDEX, index)

    print()
    print("=== Resultaat ===")
    print(f"Tags met unicode-apostrof genormaliseerd: {total_tags_fixed}")
    print(f"Begrippen hernoemd: {total_begrippen_fixed}")
    for old, new, kid in renamed_pairs:
        print(f"  [{kid}]  {old!r} → {new!r}")
    print(f"Index-sleutels bijgewerkt: {len(key_renames)}")
    for old, new, action in key_renames:
        print(f"  {old!r} → {new!r}  ({action})")


if __name__ == "__main__":
    main()
