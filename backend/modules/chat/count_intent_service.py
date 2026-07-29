"""
v11_spark_index_001 — Count-intent detector voor Spark Self-Awareness.

Detecteert "hoeveel bestanden/mappen/modules" e.d. en beantwoordt uit
de spark_index (fastpath, geen live scan nodig).
"""
import re
from typing import Optional, Dict, Any
from modules.spark_index import read_index

_COUNT_PATTERNS = [
    # Bestanden/files
    (r"\bhoe\s*veel\s+(bestand(?:en)?|files?)\b", "files"),
    (r"\b(aantal|totaal)\s+bestand(?:en)?\b", "files"),
    # Mappen/folders/directories
    (r"\bhoe\s*veel\s+(mapp?en|folders?|directories?|dirs?)\b", "dirs"),
    (r"\b(aantal|totaal)\s+mapp?en\b", "dirs"),
    # Modules
    (r"\bhoe\s*veel\s+modules?\b", "modules"),
    (r"\b(aantal|totaal)\s+modules?\b", "modules"),
    (r"\bwelke\s+modules?\s+(heb|zijn)\b", "modules_list"),
    # Per file-type
    (r"\bhoe\s*veel\s+(python|py)[-\s]?(bestanden|files)?\b", "ext:.py"),
    (r"\bhoe\s*veel\s+(js|javascript|react)[-\s]?(bestanden|files)?\b", "ext:.js"),
    (r"\bhoe\s*veel\s+json[-\s]?(bestanden|files)?\b", "ext:.json"),
    (r"\bhoe\s*veel\s+markdown\b|hoe\s*veel\s+md\b", "ext:.md"),
]


def detect_count_intent(text: str) -> Optional[str]:
    """Return count-target ('files' | 'dirs' | 'modules' | 'ext:.py' | ...) or None."""
    if not text:
        return None
    t = text.lower().strip()
    for pat, target in _COUNT_PATTERNS:
        if re.search(pat, t):
            return target
    return None


def answer_count(target: str) -> Optional[Dict[str, Any]]:
    """Bouw Sparks antwoord voor de count-vraag."""
    idx = read_index()
    totals = idx.get("totals", {})
    ts = idx.get("rebuilt_at", "onbekend")[:19]  # kort ISO

    if target == "files":
        msg = (
            f"Ik heb **{totals.get('files', 0)} code-bestanden** verspreid over "
            f"{totals.get('dirs', 0)} mappen (backend + frontend + memory). "
            f"Laatste index: {ts}."
        )
    elif target == "dirs":
        msg = f"Ik heb **{totals.get('dirs', 0)} mappen** in totaal. Laatste index: {ts}."
    elif target == "modules":
        msg = (
            f"Ik heb **{totals.get('backend_modules', 0)} backend-modules**, "
            f"waarvan **{totals.get('modules_with_meta', 0)} met een `_meta.json`-footnote** "
            f"(die vertelt wat de module doet). Laatste index: {ts}."
        )
    elif target == "modules_list":
        mods = list(idx.get("modules", {}).keys())
        preview = ", ".join(mods[:15])
        rest = len(mods) - 15
        tail = f" en nog {rest} andere" if rest > 0 else ""
        msg = f"Ik heb **{len(mods)} modules**: {preview}{tail}. Vraag `/api/spark-index` voor de volledige lijst."
    elif target.startswith("ext:"):
        ext = target[4:]
        count = idx.get("per_extension", {}).get(ext, 0)
        ext_label = ext.lstrip(".") if ext else ""
        msg = f"Ik heb **{count} `{ext_label}`-bestanden**. Laatste index: {ts}."
    else:
        return None

    return {
        "message": msg,
        "intent": "spark_index_count",
        "target": target,
        "totals": totals,
        "used_model": "spark_index_fastpath",
        "fast_path": True,
    }
