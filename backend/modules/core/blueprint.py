"""v6_blueprint_loader_001 — laad module-config uit JSON in plaats van hard-coded Python.

Voordelen:
  - Modules zijn pure logica, basisinfo komt uit `blueprints/*.json`
  - Spark kan zichzelf updaten via een UI / endpoint
  - Versie-historie leesbaar (git diff op JSON)
  - Geen import-cycle nodig om constants te wijzigen

Conventie:
  /app/backend/modules/<container>/blueprints/<naam>.json

Pad-resolutie binnen blueprint:
  - "{DATA}" → /app/backend/data
  - "{MEMORY}" → /app/memory
  - "{MODULE}" → /app/backend/modules/<container>
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional
from functools import lru_cache

BACKEND_ROOT = Path(__file__).parent.parent.parent
DATA_ROOT = BACKEND_ROOT / "data"
MEMORY_ROOT = BACKEND_ROOT.parent / "memory"
MODULES_ROOT = BACKEND_ROOT / "modules"


def _resolve_path(value: str, module: str) -> str:
    """Resolve {DATA}, {MEMORY}, {MODULE} placeholders in path strings."""
    if not isinstance(value, str):
        return value
    return (value
            .replace("{DATA}", str(DATA_ROOT))
            .replace("{MEMORY}", str(MEMORY_ROOT))
            .replace("{MODULE}", str(MODULES_ROOT / module)))


def _walk_resolve(obj: Any, module: str) -> Any:
    """Recursief paths resolven in een dict/list structuur."""
    if isinstance(obj, dict):
        return {k: _walk_resolve(v, module) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_walk_resolve(i, module) for i in obj]
    if isinstance(obj, str) and "{" in obj:
        return _resolve_path(obj, module)
    return obj


def load_blueprint(module: str, naam: str, default: Optional[Dict] = None) -> Dict:
    """Laad blueprint voor `<module>/<naam>`. 
    
    Voorbeeld: load_blueprint("chat", "response_composer")
    Zoekt: /app/backend/modules/chat/blueprints/response_composer.json
    
    Geen caching — blueprints kunnen tijdens runtime geüpdatet worden.
    Voor performance: gebruik load_blueprint_cached als de waarden statisch zijn.
    """
    container = module.split("/")[0]
    fp = MODULES_ROOT / container / "blueprints" / f"{naam}.json"
    if not fp.exists():
        if default is not None:
            return default
        raise FileNotFoundError(f"Blueprint niet gevonden: {fp}")
    raw = json.loads(fp.read_text(encoding="utf-8"))
    return _walk_resolve(raw, container)


@lru_cache(maxsize=64)
def load_blueprint_cached(module: str, naam: str) -> Dict:
    """Gecached variant voor statische config (model namen, prompt templates).
    Gebruik clear_blueprint_cache() na een update."""
    return load_blueprint(module, naam)


def clear_blueprint_cache() -> None:
    """Reset blueprint cache (na update via endpoint)."""
    load_blueprint_cached.cache_clear()
