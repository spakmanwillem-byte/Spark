"""
Synapse — Touch helper (v6_synapse_001, F3)
=============================================
Wordt aangeroepen wanneer een file in een bekende container wordt aangepast.
Update `_meta.json::last_touched` + `activity_count`.

Gebruik:
  from modules.synapse.touch import touch_path
  touch_path(f"{SPARK_ROOT}/backend/data/notes/notes.json")  # vindt parent-meta en bumpt
"""
from modules.core.paths import SPARK_ROOT  # v14_spark_root_001
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from modules.core.storage import load_json, save_json
from .schema import now_iso

META_FILENAME = "_meta.json"
from modules.core.paths import SPARK_ROOT as APP_ROOT  # v14_spark_root_001


def find_container_for(file_path: Path) -> Optional[Path]:
    """Loop omhoog totdat we een _meta.json vinden (max 5 niveaus diep)."""
    p = file_path.parent if file_path.is_file() else file_path
    for _ in range(6):
        if (p / META_FILENAME).exists():
            return p
        if p == APP_ROOT or p == p.parent:
            return None
        p = p.parent
    return None


def touch_path(file_path) -> bool:
    """Markeer container van file_path als 'aangeraakt'. Stille fail bij errors."""
    try:
        fp = Path(file_path) if not isinstance(file_path, Path) else file_path
        # Skip meta zelf om infinite loops te vermijden
        if fp.name == META_FILENAME:
            return False
        container = find_container_for(fp)
        if not container:
            return False
        meta_path = container / META_FILENAME
        meta = load_json(meta_path, default={})
        if not meta:
            return False
        meta["last_touched"] = now_iso()
        meta["activity_count"] = int(meta.get("activity_count", 0)) + 1
        save_json(meta_path, meta)
        return True
    except Exception:
        return False
