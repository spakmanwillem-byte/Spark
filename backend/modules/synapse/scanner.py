"""
Synapse — Scanner (v6_synapse_001)
====================================
Walkt door alle relevante boom-takken en zorgt dat elke map een _meta.json heeft.
Bestaande _meta.json wordt gemerged (user-edits beschermd).

Bronnen:
  - /app/backend/modules/*/        → CONTAINER_DIR (Python module)
  - /app/frontend/src/components/* → CONTAINER_DIR (React component-folder)
  - /app/backend/data/*/           → CONTAINER_DATA (json-store)

Skipt:
  - __pycache__, .git, .emergent, node_modules
  - _backups, _deleted_users, system_archive (te groot voor meta-per-map)
  - bestanden direct in /data (gebruikt root-meta)
"""
import re
import json
from pathlib import Path
from typing import Dict, List, Any

from modules.core.storage import load_json, save_json
from .schema import (
    new_meta, merge_meta,
    CONTAINER_DIR, CONTAINER_DATA,
    STATUS_ACTIVE, STATUS_SKELETON,
)


# Project roots
APP_ROOT = Path("/app")
BACKEND_MODULES = APP_ROOT / "backend" / "modules"
FRONTEND_COMPONENTS = APP_ROOT / "frontend" / "src" / "components"
BACKEND_DATA = APP_ROOT / "backend" / "data"

# Skip-lijst
SKIP_DIRS = {
    "__pycache__", ".git", ".emergent", "node_modules", ".pytest_cache",
    "_backups", "_deleted_users",
}
# Mappen die we wel scannen maar zonder de zware sub-tree (alleen meta op root-level)
SHALLOW_DIRS = {
    "system_archive",  # foto/geluid/film — tienduizenden bestanden
    "graph",           # 7MB edges-file
    "knowledge",       # large
}

META_FILENAME = "_meta.json"


# ============================================================
# ROUTE-EXTRACTIE uit Python module
# ============================================================
ROUTE_PATTERN = re.compile(
    r"@router\.(get|post|put|delete|patch)\s*\(\s*['\"]([^'\"]+)['\"]",
    re.IGNORECASE,
)
PREFIX_PATTERN = re.compile(
    r"APIRouter\s*\(\s*[^)]*prefix\s*=\s*['\"]([^'\"]+)['\"]",
    re.IGNORECASE | re.DOTALL,
)


def extract_endpoints_from_py(folder: Path) -> List[str]:
    """Scan alle .py files in folder voor @router.<verb>(...) declaraties."""
    endpoints: List[str] = []
    prefix = ""
    for py in folder.glob("*.py"):
        try:
            text = py.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if not prefix:
            m = PREFIX_PATTERN.search(text)
            if m:
                prefix = m.group(1).rstrip("/")
        for match in ROUTE_PATTERN.finditer(text):
            verb = match.group(1).upper()
            path = match.group(2)
            full = f"{prefix}{path}" if prefix else path
            endpoints.append(f"{verb} {full}")
    return sorted(set(endpoints))


# ============================================================
# CORE SCAN per map
# ============================================================
def _count_files_and_dirs(folder: Path, shallow: bool = False) -> tuple:
    """Tel files en subdirs. Bij shallow: alleen direct."""
    files = 0
    subdirs = 0
    try:
        for entry in folder.iterdir():
            if entry.name == META_FILENAME:
                continue
            if entry.is_dir():
                if entry.name in SKIP_DIRS:
                    continue
                subdirs += 1
            elif entry.is_file():
                files += 1
        if not shallow:
            # Diepe telling van files
            for entry in folder.rglob("*"):
                if entry.is_file() and entry.name != META_FILENAME:
                    # Skip in pycache/backups
                    parts = set(entry.parts)
                    if SKIP_DIRS & parts:
                        continue
                    pass  # files al via top-level
    except Exception:
        pass
    return files, subdirs


def _deep_file_count(folder: Path, max_depth: int = 5) -> int:
    """Tel alle non-meta files tot max_depth."""
    if max_depth < 0:
        return 0
    cnt = 0
    try:
        for entry in folder.iterdir():
            if entry.name in SKIP_DIRS or entry.name == META_FILENAME:
                continue
            if entry.is_file():
                cnt += 1
            elif entry.is_dir():
                cnt += _deep_file_count(entry, max_depth - 1)
    except Exception:
        pass
    return cnt


def scan_one_folder(folder: Path, container_type: str = CONTAINER_DIR) -> Dict[str, Any]:
    """Scan één folder, return (en schrijf) _meta.json record."""
    if not folder.exists() or not folder.is_dir():
        return {}
    meta_path = folder / META_FILENAME
    existing = {}
    if meta_path.exists():
        try:
            existing = load_json(meta_path, default={})
        except Exception:
            existing = {}

    shallow = folder.name in SHALLOW_DIRS
    file_count = _deep_file_count(folder, max_depth=2 if shallow else 5)
    direct_subdirs = sum(
        1 for e in folder.iterdir()
        if e.is_dir() and e.name not in SKIP_DIRS and e.name != META_FILENAME
    )

    endpoints: List[str] = []
    if container_type == CONTAINER_DIR and (folder / "__init__.py").exists() or any(folder.glob("*.py")):
        endpoints = extract_endpoints_from_py(folder)

    # Initial doel/status heuristiek
    naam = folder.name
    auto_doel = ""
    auto_status = STATUS_ACTIVE
    # Frontend skeleton-heuristiek: tel ook .js/.jsx/.ts/.tsx als "code"
    code_files = 0
    try:
        for ext in (".py", ".js", ".jsx", ".ts", ".tsx"):
            code_files += sum(1 for _ in folder.rglob(f"*{ext}"))
    except Exception:
        pass
    is_likely_skeleton = (
        file_count <= 1
        and not endpoints
        and code_files <= 1
        and direct_subdirs == 0
    )
    if is_likely_skeleton:
        auto_status = STATUS_SKELETON
        auto_doel = f"Skelet — {naam} module nog leeg of placeholder"

    fresh = new_meta(
        naam=naam,
        doel=auto_doel,
        container_type=container_type,
        status=auto_status,
        endpoints=endpoints,
    )
    fresh["file_count"] = file_count
    fresh["subdir_count"] = direct_subdirs

    merged = merge_meta(existing, fresh)
    # Schrijf alleen als gewijzigd
    if existing != merged:
        save_json(meta_path, merged)
    return merged


# ============================================================
# WALK-FUNCTIES voor elke boom
# ============================================================
def scan_backend_modules() -> Dict[str, Dict[str, Any]]:
    out = {}
    if not BACKEND_MODULES.exists():
        return out
    for sub in sorted(BACKEND_MODULES.iterdir()):
        if not sub.is_dir() or sub.name in SKIP_DIRS:
            continue
        meta = scan_one_folder(sub, container_type=CONTAINER_DIR)
        if meta:
            out[f"backend/modules/{sub.name}"] = meta
    return out


def scan_frontend_components() -> Dict[str, Dict[str, Any]]:
    out = {}
    if not FRONTEND_COMPONENTS.exists():
        return out
    for sub in sorted(FRONTEND_COMPONENTS.iterdir()):
        if not sub.is_dir() or sub.name in SKIP_DIRS:
            continue
        meta = scan_one_folder(sub, container_type=CONTAINER_DIR)
        if meta:
            out[f"frontend/components/{sub.name}"] = meta
    return out


def scan_backend_data() -> Dict[str, Dict[str, Any]]:
    out = {}
    if not BACKEND_DATA.exists():
        return out
    for sub in sorted(BACKEND_DATA.iterdir()):
        if not sub.is_dir() or sub.name in SKIP_DIRS:
            continue
        meta = scan_one_folder(sub, container_type=CONTAINER_DATA)
        if meta:
            out[f"backend/data/{sub.name}"] = meta
    return out


def scan_all() -> Dict[str, Dict[str, Dict[str, Any]]]:
    """Full scan. Returnt grouped dict voor aggregator."""
    return {
        "backend_modules": scan_backend_modules(),
        "frontend_components": scan_frontend_components(),
        "backend_data": scan_backend_data(),
    }
