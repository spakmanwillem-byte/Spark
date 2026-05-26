"""
Spark Core - JSON Storage Layer
Centrale laag voor alle JSON operaties.

v4_storage_cache_001 (20/05): mtime-based in-memory cache.
Doel: vermijden dat we 8 MB knowledge_base.json + 7 MB graph/edges.json bij elke API-call
opnieuw parsen. Cache wordt automatisch ververst wanneer de file op disk gewijzigd is
(via mtime+size check, ook bestand-bestendig over processen heen).

Veiligheid:
- Callers mogen de teruggegeven dict/list muteren EN dan save_json aanroepen — dat patroon
  blijft werken want save_json invalidateert + bevoorraadt de cache opnieuw.
- Lees-only consumers worden ook bediend uit dezelfde reference (geen deepcopy = snel).
- Bij file-write door externe processen (bv. backup-restore, handmatige edits) wordt
  de cache automatisch ververst dankzij mtime-check.
"""
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Optional, Tuple
from datetime import datetime
import threading

# Thread-safe lock voor file operaties
_file_locks = {}
_lock_manager = threading.Lock()

# v4_storage_cache_001 — in-memory cache: {filepath_str: (mtime_ns, size, parsed_obj)}
_cache: dict = {}
_cache_lock = threading.Lock()

# Drempel: alleen files boven deze grootte cachen. Kleinere files zijn al snel genoeg
# en cachen kost daar meer dan het oplevert (overhead van mtime stat).
_CACHE_MIN_SIZE = 50 * 1024  # 50 KB


def _get_lock(filepath: str) -> threading.Lock:
    """Get or create lock for specific file"""
    with _lock_manager:
        if filepath not in _file_locks:
            _file_locks[filepath] = threading.Lock()
        return _file_locks[filepath]


def _cache_key_stats(filepath: Path) -> Optional[Tuple[int, int]]:
    """Return (mtime_ns, size) tuple voor cache-key, of None als file niet bestaat."""
    try:
        st = filepath.stat()
        return (st.st_mtime_ns, st.st_size)
    except OSError:
        return None


def load_json(filepath: Path, default: Any = None, fresh: bool = False) -> Any:
    """Load JSON file safely (met mtime-based cache voor grote files).

    Args:
        filepath: Path to JSON file
        default: Default value als file niet bestaat of invalid is
        fresh: True = forceer disk-read, skip cache (gebruik bij twijfel over staleness)
    """
    fp_str = str(filepath)
    lock = _get_lock(fp_str)

    with lock:
        try:
            stats = _cache_key_stats(filepath)
            if stats is None:
                return default if default is not None else {}

            # Cache hit? (mtime + size identiek aan opgeslagen versie)
            if not fresh:
                with _cache_lock:
                    cached = _cache.get(fp_str)
                if cached and cached[0] == stats[0] and cached[1] == stats[1]:
                    return cached[2]

            with open(filepath, 'r', encoding='utf-8') as f:
                parsed = json.load(f)

            # Cache alleen grote files (KB, graph nodes/edges, chat logs)
            if stats[1] >= _CACHE_MIN_SIZE:
                with _cache_lock:
                    _cache[fp_str] = (stats[0], stats[1], parsed)
            return parsed
        except (json.JSONDecodeError, IOError) as e:
            print(f"[STORAGE ERROR] Failed to load {filepath}: {e}")
            return default if default is not None else {}


def save_json(filepath: Path, data: Any, backup: bool = False) -> bool:
    """
    Save data to JSON file safely (atomic + cache invalidation).
    
    Args:
        filepath: Path to JSON file
        data: Data to save
        backup: Create backup before saving
    """
    fp_str = str(filepath)
    lock = _get_lock(fp_str)

    with lock:
        try:
            # Ensure directory exists
            filepath.parent.mkdir(parents=True, exist_ok=True)

            # Create backup if requested
            if backup and filepath.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = filepath.with_suffix(f".backup_{timestamp}.json")
                with open(filepath, 'r', encoding='utf-8') as f:
                    backup_data = f.read()
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(backup_data)

            # Write new data ATOMIC: schrijf eerst naar tmp file, dan rename.
            tmp_fd, tmp_path = tempfile.mkstemp(
                dir=filepath.parent,
                prefix=f".{filepath.name}.",
                suffix=".tmp",
            )
            try:
                with os.fdopen(tmp_fd, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                    f.flush()
                    try: os.fsync(f.fileno())
                    except OSError: pass
                os.replace(tmp_path, filepath)
            except Exception:
                try: os.unlink(tmp_path)
                except OSError: pass
                raise

            # v4_storage_cache_001: update cache met nieuwe mtime + size + data
            stats = _cache_key_stats(filepath)
            if stats and stats[1] >= _CACHE_MIN_SIZE:
                with _cache_lock:
                    _cache[fp_str] = (stats[0], stats[1], data)
            elif stats:
                # File werd kleiner → invalidate
                with _cache_lock:
                    _cache.pop(fp_str, None)

            # v6_synapse_001 F3: auto-touch parent-container _meta.json (best-effort)
            # Skipt _meta.json zelf (anders infinite loop). Lazy import om circulair te vermijden.
            try:
                if filepath.name != "_meta.json":
                    from modules.synapse.touch import touch_path as _touch
                    _touch(filepath)
            except Exception:
                pass  # touch is bonus, mag nooit save breken

            return True
        except IOError as e:
            print(f"[STORAGE ERROR] Failed to save {filepath}: {e}")
            return False


def append_to_json_list(filepath: Path, item: Any) -> bool:
    """Append item to JSON list file."""
    data = load_json(filepath, default=[])
    if not isinstance(data, list):
        data = []
    data.append(item)
    return save_json(filepath, data)


def update_json_item(filepath: Path, key_field: str, key_value: Any, updates: dict) -> bool:
    """Update item in JSON list by key field."""
    data = load_json(filepath, default=[])
    if not isinstance(data, list):
        return False
    for item in data:
        if isinstance(item, dict) and item.get(key_field) == key_value:
            item.update(updates)
            return save_json(filepath, data)
    return False


# v4_storage_cache_001 — Diagnostics endpoint helper
def get_cache_stats() -> dict:
    """Geeft cache-info voor debug/admin endpoint."""
    with _cache_lock:
        return {
            "cached_files": len(_cache),
            "files": [
                {
                    "path": k,
                    "size_kb": round(v[1] / 1024, 1),
                    "mtime_iso": datetime.fromtimestamp(v[0] / 1e9).isoformat(),
                }
                for k, v in _cache.items()
            ],
            "total_cached_mb": round(sum(v[1] for v in _cache.values()) / 1024 / 1024, 2),
        }


def clear_cache():
    """Forceer cache leeg (admin gebruik / na bulk-restore)."""
    with _cache_lock:
        _cache.clear()
