"""Auto-scanner voor command_registry (Principe #8 — dekking richting 100%).

Doorzoekt /app/backend/modules/**/*.py naar @router-decorators en produceert
per gevonden endpoint een concept-registry-entry. Vergelijkt met de bestaande
registry en print alleen entries die MISSEN.

Output: schrijft naar /tmp/registry_scan_YYYYmmdd.json met concept-entries
die je vervolgens kunt reviewen en (na aanvulling van intent_tags/gradatie)
via registry_batch1_add-achtige script kunt inzetten.

Gebruik:
    python3 scripts/scan_routes_for_registry.py             # samenvatting + JSON
    python3 scripts/scan_routes_for_registry.py --module agenda   # één module
    python3 scripts/scan_routes_for_registry.py --write     # commit conceptbestand
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

MODULES_DIR = Path(__file__).parent.parent / "modules"
REGISTRY_PATH = Path(__file__).parent.parent / "data" / "system" / "command_registry.json"
OUT_DIR = Path("/tmp")

ROUTE_RE = re.compile(r'@router\.(get|post|put|patch|delete)\(\s*["\']([^"\']+)["\']')
PREFIX_RE = re.compile(r'APIRouter\(\s*prefix\s*=\s*["\']([^"\']+)["\']')
FUNC_RE = re.compile(r'@router\.[a-z]+\([^\)]*\)\s*(?:async\s+)?def\s+([a-zA-Z_][a-zA-Z0-9_]*)')

# Heuristiek: welke behavior_class hoort bij welke methode?
BEHAVIOR_HINTS = {
    "GET": "informatief-functioneel",
    "POST": "exploreren-uitbreiden",
    "PUT": "exploreren-uitbreiden",
    "PATCH": "exploreren-uitbreiden",
    "DELETE": "vertragen-ondersteunen",
}

# Modules die als admin gemarkeerd worden bij POST/DELETE/PATCH/PUT
ADMIN_LIKELY_MODULES = {"admin", "bugs", "triggers", "container", "deploy", "backup", "audit"}


def _extract_module(pyfile: Path) -> str:
    """Return module-naam (eerste subdir onder modules/)."""
    rel = pyfile.relative_to(MODULES_DIR)
    return rel.parts[0] if rel.parts else pyfile.stem


def _slugify_id(module: str, method: str, path: str) -> str:
    """cap_<module>_<method>_<hint> — heuristisch id-voorstel."""
    # laatste segment zonder placeholders
    parts = [p for p in path.strip("/").split("/") if not p.startswith("{")]
    tail = "_".join(parts[-2:]) if parts else "root"
    tail = re.sub(r"[^a-z0-9_]", "_", tail.lower())
    tail = re.sub(r"_+", "_", tail).strip("_")
    return f"cap_{module}_{method.lower()}_{tail}"


def _extract_required(path: str) -> list[str]:
    return re.findall(r"\{([^}]+)\}", path)


def scan_all() -> list[dict]:
    """Scan alle module-files en return concept-entries."""
    entries: list[dict] = []
    for py in sorted(MODULES_DIR.rglob("*.py")):
        try:
            text = py.read_text(errors="ignore")
        except Exception:
            continue
        prefix_m = PREFIX_RE.search(text)
        prefix = prefix_m.group(1) if prefix_m else ""

        # Route-decorators + functienamen paren
        route_positions = [(m.start(), m.group(1).upper(), m.group(2)) for m in ROUTE_RE.finditer(text)]
        func_positions = [(m.start(), m.group(1)) for m in FUNC_RE.finditer(text)]
        func_after = {}
        for r_pos, method, path in route_positions:
            best = None
            for f_pos, fname in func_positions:
                if f_pos > r_pos and (best is None or f_pos < best[0]):
                    best = (f_pos, fname)
            func_after[(r_pos, method, path)] = best[1] if best else "?"

        module = _extract_module(py)
        for r_pos, method, path in route_positions:
            full_path = f"/api{prefix}{path}".replace("//", "/")
            method_upper = method
            admin_hint = (module in ADMIN_LIKELY_MODULES and method_upper != "GET") or "/admin/" in path
            entry = {
                "id": _slugify_id(module, method_upper, path),
                "path": full_path,
                "method": method_upper,
                "intent_tags": [module],  # BEWUST leeg — jij vult aan
                "required_params": _extract_required(path),
                "gradatie_min": 4 if admin_hint else 2,
                "admin_only": admin_hint,
                "behavior_class_hint": BEHAVIOR_HINTS.get(method_upper, "informatief-functioneel"),
                "source": f"{module}.{py.stem}.{func_after[(r_pos, method, path)]}",
                "_scan": {"file": str(py.relative_to(MODULES_DIR.parent)), "auto_generated": True},
            }
            entries.append(entry)
    return entries


def main() -> None:
    args = sys.argv[1:]
    module_filter = None
    write = False
    for i, a in enumerate(args):
        if a == "--module" and i + 1 < len(args):
            module_filter = args[i + 1]
        if a == "--write":
            write = True

    registry = json.loads(REGISTRY_PATH.read_text())
    registered_paths = {(c.get("path"), c.get("method")) for c in registry.get("commands", [])}

    all_entries = scan_all()
    missing = [e for e in all_entries if (e["path"], e["method"]) not in registered_paths]
    if module_filter:
        missing = [e for e in missing if e["source"].startswith(module_filter + ".")]

    # Groepeer per module voor overzicht
    per_module: dict[str, int] = {}
    for e in missing:
        mod = e["source"].split(".")[0]
        per_module[mod] = per_module.get(mod, 0) + 1

    print(f"Totaal routes gescanned: {len(all_entries)}")
    print(f"Reeds in registry: {len(all_entries) - len([e for e in all_entries if (e['path'], e['method']) not in registered_paths])}")
    print(f"Concept-entries voor MISSENDE routes: {len(missing)}")
    print()
    print("=== Per module (top 20) ===")
    for mod, cnt in sorted(per_module.items(), key=lambda x: -x[1])[:20]:
        print(f"  {mod:<25s} {cnt:>4d}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    fn = OUT_DIR / f"registry_scan_{ts}.json"
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_scanned": len(all_entries),
        "missing_count": len(missing),
        "module_filter": module_filter,
        "concept_entries": missing,
        "notes": [
            "intent_tags bevat nu alleen module-naam — vul aan met echte NL-woorden voordat je toevoegt aan registry",
            "gradatie_min is heuristisch: 4 voor admin-achtig, 2 voor rest — corrigeer waar nodig",
            "admin_only is heuristisch — verifieer per entry",
            "id is auto-gegenereerd (cap_<module>_<method>_<tail>) — mag je hernoemen",
        ],
    }
    if write:
        fn.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
        print(f"\nGeschreven naar: {fn}")
    else:
        print(f"\n(dry-run — gebruik --write om {fn.name} te schrijven)")


if __name__ == "__main__":
    main()
