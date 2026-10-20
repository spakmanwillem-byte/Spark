"""
v11_spark_index_001 — Spark Self-Awareness Index (fundering voor 🟢)

Willems visie: Spark moet weten hoeveel mappen/bestanden/modules hij heeft
zonder telkens te scannen. Deze module bouwt een periodieke index en
aggregeert de bestaande `_meta.json` footnotes per module.

Endpoints:
  POST /api/spark-index/rebuild — scan alles opnieuw
  GET  /api/spark-index         — read-only index (fast)
  GET  /api/spark-index/module/{name} — details per module (footnote + counts)
"""
from modules.core.paths import SPARK_ROOT  # v14_spark_root_001
from fastapi import APIRouter
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List
import json
import os

router = APIRouter(prefix="/api/spark-index", tags=["spark-index"])

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "spark_index"
DATA_DIR.mkdir(parents=True, exist_ok=True)
INDEX_FILE = DATA_DIR / "index.json"
LOG_FILE = DATA_DIR / "rebuild_log.json"

SCAN_ROOTS = [f"{SPARK_ROOT}/backend", f"{SPARK_ROOT}/frontend/src", f"{SPARK_ROOT}/memory"]
SKIP_DIRS = {"__pycache__", "node_modules", ".git", "build", "dist", "sandbox", ".pytest_cache"}
CODE_EXTS = {".py", ".js", ".jsx", ".ts", ".tsx", ".json", ".css", ".html", ".md", ".txt", ".yaml", ".yml"}


def _scan_root(root: str) -> Dict:
    """Scan één root, return counts + per-directory summary."""
    if not os.path.exists(root):
        return {"exists": False, "root": root}
    total_dirs = 0
    total_files = 0
    per_ext: Dict[str, int] = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        total_dirs += 1
        for f in filenames:
            if f.startswith("."):
                continue
            ext = os.path.splitext(f)[1].lower()
            if ext in CODE_EXTS:
                total_files += 1
                per_ext[ext] = per_ext.get(ext, 0) + 1
    return {
        "exists": True, "root": root,
        "total_dirs": total_dirs, "total_files": total_files,
        "per_extension": per_ext,
    }


def _scan_modules() -> Dict[str, Dict]:
    """Scan /app/backend/modules/*/  — per module: bestand-count + footnote uit _meta.json."""
    mods_dir = Path(f"{SPARK_ROOT}/backend/modules")
    result: Dict[str, Dict] = {}
    if not mods_dir.exists():
        return result
    for mod_path in sorted(mods_dir.iterdir()):
        if not mod_path.is_dir() or mod_path.name.startswith((".", "_")):
            continue
        name = mod_path.name
        py_count = 0
        for f in mod_path.rglob("*.py"):
            if "__pycache__" not in str(f):
                py_count += 1
        # Footnote uit _meta.json
        footnote = None
        purpose = None
        meta_fp = mod_path / "_meta.json"
        if meta_fp.exists():
            try:
                m = json.loads(meta_fp.read_text())
                fn = m.get("footnote") or {}
                footnote = fn.get("wat_doet") or fn.get("purpose") or fn.get("beschrijving")
                purpose = m.get("purpose") or m.get("beschrijving")
            except Exception:
                pass
        result[name] = {
            "py_files": py_count,
            "footnote": footnote,
            "purpose": purpose,
            "has_meta": meta_fp.exists(),
        }
    return result


def build_index() -> Dict:
    """Volledige rebuild — persist naar INDEX_FILE + log."""
    ts = datetime.now(timezone.utc).isoformat()
    per_root: Dict[str, Dict] = {r: _scan_root(r) for r in SCAN_ROOTS}
    modules = _scan_modules()
    # Aggregate totals
    total_dirs = sum(r.get("total_dirs", 0) for r in per_root.values())
    total_files = sum(r.get("total_files", 0) for r in per_root.values())
    per_ext: Dict[str, int] = {}
    for r in per_root.values():
        for e, c in (r.get("per_extension") or {}).items():
            per_ext[e] = per_ext.get(e, 0) + c
    idx = {
        "version": "v11_spark_index_001",
        "rebuilt_at": ts,
        "totals": {
            "dirs": total_dirs,
            "files": total_files,
            "backend_modules": len(modules),
            "modules_with_meta": sum(1 for m in modules.values() if m["has_meta"]),
        },
        "per_extension": dict(sorted(per_ext.items(), key=lambda x: -x[1])),
        "per_root": per_root,
        "modules": modules,
    }
    INDEX_FILE.write_text(json.dumps(idx, indent=2, ensure_ascii=False))
    # Log entry
    log: List[Dict] = []
    if LOG_FILE.exists():
        try:
            log = json.loads(LOG_FILE.read_text())
        except Exception:
            log = []
    log.append({
        "ts": ts,
        "total_dirs": total_dirs,
        "total_files": total_files,
        "modules": len(modules),
    })
    LOG_FILE.write_text(json.dumps(log[-50:], indent=2))  # keep last 50
    return idx


def read_index() -> Dict:
    """Lees index van disk (fast). Als niet aanwezig → rebuild eenmalig."""
    if not INDEX_FILE.exists():
        return build_index()
    try:
        return json.loads(INDEX_FILE.read_text())
    except Exception:
        return build_index()


@router.post("/rebuild")
async def rebuild():
    idx = build_index()
    return {
        "success": True,
        "rebuilt_at": idx["rebuilt_at"],
        "totals": idx["totals"],
    }


@router.get("")
async def get_index():
    idx = read_index()
    return {"success": True, **idx}


@router.get("/module/{name}")
async def get_module(name: str):
    idx = read_index()
    mod = idx.get("modules", {}).get(name)
    if not mod:
        return {"success": False, "error": f"module '{name}' niet in index. Run /rebuild"}
    return {"success": True, "module": name, **mod}
