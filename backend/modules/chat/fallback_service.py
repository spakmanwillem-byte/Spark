"""
Fallback Service (v4_013c) — Lees random reacties uit system_fallback.json.
Strings die voorheen hard-coded in routes.py stonden zijn hier centraal beheerd.
"""
import secrets
from pathlib import Path
from modules.core.storage import load_json

DATA_DIR = Path(__file__).parent.parent.parent / "data"
FALLBACK_FILE = DATA_DIR / "triggers" / "system_fallback.json"


def pick(key: str, default: str = "", **format_kwargs) -> str:
    """Kies random tekst uit system_fallback.json[key]. Geeft `default` terug
    als de key niet bestaat of de lijst leeg is. Ondersteunt {placeholders}."""
    data = load_json(FALLBACK_FILE, default={})
    options = data.get(key, [])
    if not options:
        text = default
    else:
        text = secrets.choice(options)
    if format_kwargs and "{" in text:
        try:
            text = text.format(**format_kwargs)
        except (KeyError, IndexError):
            pass
    return text
