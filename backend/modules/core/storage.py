"""
Spark Core - JSON Storage Layer
Centrale laag voor alle JSON operaties
"""
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Optional
from datetime import datetime
import threading

# Thread-safe lock voor file operaties
_file_locks = {}
_lock_manager = threading.Lock()


def _get_lock(filepath: str) -> threading.Lock:
    """Get or create lock for specific file"""
    with _lock_manager:
        if filepath not in _file_locks:
            _file_locks[filepath] = threading.Lock()
        return _file_locks[filepath]


def load_json(filepath: Path, default: Any = None) -> Any:
    """
    Load JSON file safely
    
    Args:
        filepath: Path to JSON file
        default: Default value if file doesn't exist or is invalid
        
    Returns:
        Parsed JSON data or default value
    """
    lock = _get_lock(str(filepath))
    
    with lock:
        try:
            if not filepath.exists():
                return default if default is not None else {}
            
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"[STORAGE ERROR] Failed to load {filepath}: {e}")
            return default if default is not None else {}


def save_json(filepath: Path, data: Any, backup: bool = False) -> bool:
    """
    Save data to JSON file safely
    
    Args:
        filepath: Path to JSON file
        data: Data to save
        backup: Create backup before saving
        
    Returns:
        True if successful, False otherwise
    """
    lock = _get_lock(str(filepath))
    
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
            # Voorkomt half-geschreven files bij crash/SIGTERM/disk-error.
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
                # os.replace is atomic op POSIX (en Windows ≥3.3)
                os.replace(tmp_path, filepath)
            except Exception:
                # Clean up tmp on failure
                try: os.unlink(tmp_path)
                except OSError: pass
                raise

            return True
            
        except IOError as e:
            print(f"[STORAGE ERROR] Failed to save {filepath}: {e}")
            return False


def append_to_json_list(filepath: Path, item: Any) -> bool:
    """
    Append item to JSON list file
    
    Args:
        filepath: Path to JSON file containing a list
        item: Item to append
        
    Returns:
        True if successful
    """
    data = load_json(filepath, default=[])
    if not isinstance(data, list):
        data = []
    data.append(item)
    return save_json(filepath, data)


def update_json_item(filepath: Path, key_field: str, key_value: Any, updates: dict) -> bool:
    """
    Update item in JSON list by key field
    
    Args:
        filepath: Path to JSON file containing a list
        key_field: Field to match (e.g., 'id')
        key_value: Value to match
        updates: Dict of fields to update
        
    Returns:
        True if item was found and updated
    """
    data = load_json(filepath, default=[])
    if not isinstance(data, list):
        return False
    
    for item in data:
        if isinstance(item, dict) and item.get(key_field) == key_value:
            item.update(updates)
            return save_json(filepath, data)
    
    return False
