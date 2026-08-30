"""v13c_apostrophe_normalizer_001 — normaliseer unicode-apostrofen in de KB.

Herbruikbare service-laag (was eerst scripts/normalize_apostrophes_in_kb.py).
Idempotent + backups. Consumers:
- Admin-route POST /api/kb/v2/admin/normalize-apostrophes
- Registry-entry cap_kb_normalize_apostrophes (admin_only)

Regel: rechte ASCII-apostrof (') is canoniek. Alle varianten (’ ‘ ´ ` ‛ ʼ) worden
vervangen in zowel tags als begrippen, index-keys mee-gemigreerd.
"""
from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

from modules.core.storage import load_json, save_json
from modules.kb_v2.tag_sanitizer import _normalize_apostrophes

BASE = Path(__file__).parent.parent.parent / "data" / "knowledge" / "v2"
KB_FILES = [
    BASE / "knowledge_inbox.json",
    BASE / "knowledge_v2_weten.json",
    BASE / "knowledge_v2_doen.json",
    BASE / "knowledge_v2_spreken.json",
    BASE / "knowledge_v2_voelen.json",
]
INDEX = BASE / "knowledge_index.json"


def _backup(p: Path, tag: str) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    bak = p.with_suffix(p.suffix + f".bak_{tag}_{ts}")
    shutil.copy2(p, bak)
    return bak.name


def normalize_apostrophes_in_kb(dry_run: bool = False) -> Dict:
    """Normaliseer unicode-apostrofen in alle KB-tags, begrippen en index-keys.

    Args:
        dry_run: True = alleen tellen wat er zou veranderen, geen writes.

    Returns:
        dict met tags_fixed, begrippen_renamed (lijst), index_keys (lijst),
        files_changed (lijst), backups (lijst), en dry_run flag.
    """
    now = datetime.now(timezone.utc).isoformat()

    tags_fixed = 0
    begrippen_renamed: List[Dict] = []
    files_changed: List[str] = []
    backups: List[str] = []

    # Backups alleen bij commit
    if not dry_run:
        for p in KB_FILES + [INDEX]:
            backups.append(_backup(p, "apostrof_normalize"))

    for p in KB_FILES:
        data = load_json(p, default={"kaarten": []})
        changed = False
        for k in data.get("kaarten", []):
            # 1) Tags
            tags_before = k.get("tags") or []
            new_tags: List = []
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
                # Dedupe na normalisatie
                seen = set()
                deduped = []
                for t in new_tags:
                    if not isinstance(t, str):
                        deduped.append(t)
                        continue
                    key = t.lower()
                    if key in seen:
                        continue
                    seen.add(key)
                    deduped.append(t)
                if not dry_run:
                    k["tags"] = deduped
                tags_fixed += fixed_here
                changed = True

            # 2) Begrip
            b = k.get("begrip") or ""
            b_norm = _normalize_apostrophes(b)
            if b_norm != b:
                begrippen_renamed.append({
                    "kaart_id": k.get("id"),
                    "from": b,
                    "to": b_norm,
                    "lade": k.get("lade"),
                })
                if not dry_run:
                    k["begrip"] = b_norm
                    fn = k.setdefault("footnote", {})
                    fn.setdefault("history", []).append({
                        "at": now,
                        "by": "kb_normalize_apostrophes",
                        "action": "begrip_rename",
                        "from": b,
                        "to": b_norm,
                    })
                changed = True
        if changed:
            if not dry_run:
                save_json(p, data)
            files_changed.append(p.name)

    # 3) Index-keys migreren
    index = load_json(INDEX, default={"entries": {}})
    entries = index.get("entries", {})
    index_renames: List[Dict] = []
    for key in list(entries.keys()):
        new_key = _normalize_apostrophes(key)
        if new_key == key:
            continue
        if new_key in entries:
            index_renames.append({"from": key, "to": new_key, "action": "merged_into_existing"})
            if not dry_run:
                del entries[key]
        else:
            index_renames.append({"from": key, "to": new_key, "action": "renamed"})
            if not dry_run:
                entries[new_key] = entries.pop(key)
    if index_renames and not dry_run:
        index["rebuilt_at"] = now
        index["rebuilt_by"] = "kb_normalize_apostrophes"
        save_json(INDEX, index)

    return {
        "dry_run": dry_run,
        "tags_fixed": tags_fixed,
        "begrippen_renamed": begrippen_renamed,
        "index_keys_updated": index_renames,
        "files_changed": files_changed,
        "backups": backups,
        "timestamp": now,
    }
