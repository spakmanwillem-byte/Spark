"""
Pre-Merge Diff Scan (v13_pre_merge_scan_001, sessie 54)

Doel: vóór elke ZIP-restore laten zien wat er OVERSCHREVEN zou worden
zodat Willem's werk op preview niet verloren gaat.

Los van backup/routes.py houden zodat een simpele `python -m modules.backup.pre_merge_scan <zip>`
óók vanaf CLI werkt, niet alleen via de UI.

Aanpak:
- Voor elk file in de ZIP:
   1. Check of het al bestaat in /app/backend/data/
   2. Zo ja: vergelijk (a) file-size, (b) voor JSON: aantal items in "kaarten"/"relationships"/etc.
   3. Markeer als: NEW (ZIP-only), IDENTICAL, ZIP_LARGER, ZIP_SMALLER (risico!), DIFFERENT
- Return summary + lijst van risico-files.

Willem's use-case: ZIP van productie mergen naar preview waar hij méér werk heeft gedaan.
"""
from __future__ import annotations

import json
import zipfile
from pathlib import Path
from modules.core.paths import SPARK_ROOT  # v14_spark_root_001
from typing import Any, Dict, List, Tuple

DATA_ROOT = Path(__file__).resolve().parent.parent.parent / "data"

# Files waarvoor we een item-count doen (i.p.v. alleen byte-size)
COUNTABLE = {
    "kaarten": ("kaarten",),
    "relationships": ("relationships",),
    "messages": ("messages",),
    "notes": ("notes",),
    "events": ("events",),
    "agenda": ("events",),
    "trades": ("trades",),
}


def _count_items(json_bytes: bytes) -> int | None:
    """Return aantal items in bekende collecties, of None."""
    try:
        d = json.loads(json_bytes.decode("utf-8"))
    except Exception:
        return None
    if not isinstance(d, dict):
        return None
    for k in ("kaarten", "relationships", "messages", "notes", "events", "trades"):
        if isinstance(d.get(k), list):
            return len(d[k])
    return None


def _count_ws5_full(json_bytes: bytes) -> int | None:
    """Voor KB-lades: hoeveel kaarten hebben volledig 5W (wie/wat/waar/wanneer/waarom)?"""
    try:
        d = json.loads(json_bytes.decode("utf-8"))
    except Exception:
        return None
    kaarten = d.get("kaarten") if isinstance(d, dict) else None
    if not isinstance(kaarten, list):
        return None
    full = 0
    for k in kaarten:
        ws5 = k.get("ws5") if isinstance(k, dict) else None
        if isinstance(ws5, dict) and all(ws5.get(x) for x in ("wie", "wat", "waar", "wanneer", "waarom")):
            full += 1
    return full


def scan_zip_vs_current(zip_path: str | Path) -> Dict[str, Any]:
    """Compare ZIP contents against current /data — return risico-report.

    Returns:
      {
        "ok": bool,
        "total_files": int,
        "risks": [
            {"file": "knowledge/v2/knowledge_v2_weten.json",
             "verdict": "ZIP_SMALLER",
             "current_items": 3787,
             "zip_items": 3762,
             "items_lost": 25,
             "current_ws5_full": 3787,
             "zip_ws5_full": 3669,
             "ws5_lost": 118},
            ...
        ],
        "safe": [...],  # NEW, IDENTICAL of ZIP_LARGER
        "summary": {"NEW": 4, "IDENTICAL": 20, "ZIP_LARGER": 1, "ZIP_SMALLER": 1, "DIFFERENT": 0}
      }
    """
    zip_path = Path(zip_path)
    if not zip_path.exists():
        return {"ok": False, "error": f"ZIP niet gevonden: {zip_path}"}

    risks: List[Dict[str, Any]] = []
    safe: List[Dict[str, Any]] = []
    summary: Dict[str, int] = {}

    with zipfile.ZipFile(zip_path) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            # Alleen data-files + memory-files bekijken (die worden echt gemerged)
            name = info.filename
            # ZIPs bevatten paden als `backend/data/...` of `memory/...`
            # Normaliseer naar het relatieve pad binnen /app
            if name.startswith("backend/data/"):
                rel = name[len("backend/data/"):]
                local_path = DATA_ROOT / rel
            elif name.startswith("data/"):
                rel = name[len("data/"):]
                local_path = DATA_ROOT / rel
            elif name.startswith("memory/"):
                local_path = SPARK_ROOT / name
            else:
                continue
            zip_size = info.file_size

            if not local_path.exists():
                verdict = "NEW"
                summary[verdict] = summary.get(verdict, 0) + 1
                safe.append({"file": name, "verdict": verdict, "zip_size": zip_size})
                continue

            local_size = local_path.stat().st_size

            # Voor JSON-files: item-based comparison
            entry: Dict[str, Any] = {"file": name, "zip_size": zip_size, "current_size": local_size}
            if name.endswith(".json"):
                try:
                    with zf.open(info) as zf_file:
                        zip_bytes = zf_file.read()
                    with local_path.open("rb") as f:
                        local_bytes = f.read()

                    if zip_bytes == local_bytes:
                        verdict = "IDENTICAL"
                    else:
                        zip_items = _count_items(zip_bytes)
                        loc_items = _count_items(local_bytes)
                        entry["zip_items"] = zip_items
                        entry["current_items"] = loc_items
                        # Voor KB-lades ook ws5-full check
                        if "knowledge_v2_" in name:
                            entry["zip_ws5_full"] = _count_ws5_full(zip_bytes)
                            entry["current_ws5_full"] = _count_ws5_full(local_bytes)

                        if zip_items is not None and loc_items is not None:
                            if zip_items < loc_items:
                                verdict = "ZIP_SMALLER"  # RISK: dataverlies
                                entry["items_lost"] = loc_items - zip_items
                                if entry.get("current_ws5_full") and entry.get("zip_ws5_full"):
                                    entry["ws5_lost"] = entry["current_ws5_full"] - entry["zip_ws5_full"]
                            elif zip_items > loc_items:
                                verdict = "ZIP_LARGER"  # veilig, wint
                                entry["items_gained"] = zip_items - loc_items
                            else:
                                verdict = "DIFFERENT_SAME_COUNT"  # zelfde aantal, andere inhoud
                        else:
                            # Kan niet tellen → val terug op byte-size
                            verdict = "ZIP_LARGER" if zip_size > local_size else ("ZIP_SMALLER" if zip_size < local_size else "DIFFERENT_SAME_SIZE")
                except Exception as e:
                    verdict = f"ERROR: {e}"
            else:
                # Niet-JSON → byte-diff
                if zip_size == local_size:
                    verdict = "IDENTICAL_SIZE"
                elif zip_size > local_size:
                    verdict = "ZIP_LARGER"
                else:
                    verdict = "ZIP_SMALLER"

            entry["verdict"] = verdict
            summary[verdict] = summary.get(verdict, 0) + 1

            if verdict in ("ZIP_SMALLER", "DIFFERENT_SAME_COUNT"):
                risks.append(entry)
            else:
                safe.append(entry)

    return {
        "ok": True,
        "zip_path": str(zip_path),
        "total_files": sum(summary.values()),
        "summary": summary,
        "risks": risks,
        "safe_count": len(safe),
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Gebruik: python -m modules.backup.pre_merge_scan <zip_path>")
        sys.exit(1)

    result = scan_zip_vs_current(sys.argv[1])
    print(json.dumps(result, indent=2, ensure_ascii=False))
