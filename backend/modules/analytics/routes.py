"""
Analytics routes — storage breakdown (systeem vs user data)
"""
from pathlib import Path
from fastapi import APIRouter

router = APIRouter(prefix="/analytics", tags=["analytics"])

DATA_DIR = Path(__file__).parent.parent.parent / "data"


def _dir_size(path: Path) -> int:
    """Recursieve grootte van directory in bytes (volgt geen symlinks)."""
    if not path.exists():
        return 0
    total = 0
    try:
        if path.is_file():
            return path.stat().st_size
        for entry in path.rglob("*"):
            if entry.is_file():
                try:
                    total += entry.stat().st_size
                except OSError:
                    pass
    except OSError:
        pass
    return total


def _file_size(path: Path) -> int:
    if not path.exists() or not path.is_file():
        return 0
    try:
        return path.stat().st_size
    except OSError:
        return 0


# ============================================================
# Mapping: WELKE folder/file hoort bij WELKE categorie?
# ============================================================
# Twee hoofd-categorieën met sub-segmenten elk.
# Iedere sub-segment is een echte folder of file in /data.
SEGMENTS = {
    "system": {
        "label": "Systeem Data",
        "color": "#06b6d4",  # cyan
        "description": "Data die Spark zelf gebruikt om te functioneren",
        "segments": [
            {"id": "knowledge",    "label": "Kennisbank",        "path": "knowledge",                "color": "#3b82f6"},
            {"id": "graph",        "label": "Verbanden-graph",   "path": "graph",                    "color": "#6366f1"},
            {"id": "spark_bijbel", "label": "Spark Bijbel",      "path": "spark_bijbel.json",        "color": "#a855f7"},
            {"id": "personality",  "label": "Persoonlijkheid",   "path": "personality",              "color": "#ec4899"},
            {"id": "triggers",     "label": "Triggers",          "path": "triggers",                 "color": "#f59e0b"},
            {"id": "emotions",     "label": "Emoties",           "path": "emotions",                 "color": "#ef4444"},
            {"id": "system_cfg",   "label": "Systeem config",    "path": "system",                   "color": "#84cc16"},
            {"id": "trade",        "label": "Trade engine",      "path": "trade",                    "color": "#10b981"},
            {"id": "shop",         "label": "Shop catalog",      "path": "shop",                     "color": "#14b8a6"},
            {"id": "wallet",       "label": "Wallet/Trade hist", "path": "wallet",                   "color": "#0ea5e9"},
            {"id": "bots",         "label": "Community bots",    "path": "bots",                     "color": "#7c3aed"},
            {"id": "financial",    "label": "Financieel",        "path": "financial",                "color": "#22c55e"},
            {"id": "agenda",       "label": "Agenda (systeem)",  "path": "agenda",                   "color": "#f97316"},
            {"id": "notes",        "label": "Notities",          "path": "notes",                    "color": "#eab308"},
            {"id": "dagboek",      "label": "Dagboek",           "path": "dagboek",                  "color": "#d946ef"},
            {"id": "community",    "label": "Community",         "path": "community",                "color": "#06b6d4"},
            {"id": "roar",         "label": "ROAR Token",        "path": "roar",                     "color": "#fb923c"},
            {"id": "notifications","label": "Notificaties",      "path": "notifications",            "color": "#94a3b8"},
            {"id": "achievements", "label": "Achievements (data)","path": "achievements.json",        "color": "#fbbf24"},
            {"id": "keywords",     "label": "Keywords",           "path": "keywords.json",            "color": "#0891b2"},
            {"id": "conv_trig",    "label": "Chat triggers",      "path": "conversation_triggers.json","color": "#f59e0b"},
            {"id": "spark_id",     "label": "Spark identiteit",   "path": "spark_identity.json",      "color": "#8b5cf6"},
        ],
    },
    "user": {
        "label": "Gebruikers Data",
        "color": "#f59e0b",  # amber
        "description": "Persoonlijke data per gebruiker (archief + gesprekken + persoonskaarten)",
        "segments": [
            {"id": "user_archives", "label": "Persoonlijke archieven", "path": "users",       "color": "#f59e0b"},
            {"id": "chat_logs",     "label": "Gesprekslogs",           "path": "chat",        "color": "#22c55e"},
            {"id": "persons",       "label": "Persoonskaarten",        "path": "persons",     "color": "#ec4899"},
            {"id": "profile",       "label": "User profielen",         "path": "profile",     "color": "#a855f7"},
            {"id": "achievements",  "label": "Achievements/XP",        "path": "achievements","color": "#fbbf24"},
        ],
    },
}


def _human_bytes(n: int) -> str:
    if n < 1024: return f"{n} B"
    if n < 1024 ** 2: return f"{n / 1024:.1f} KB"
    if n < 1024 ** 3: return f"{n / (1024 ** 2):.1f} MB"
    return f"{n / (1024 ** 3):.2f} GB"


@router.get("/storage-breakdown")
def storage_breakdown():
    """
    Geeft volledige opsplitsing van data-gebruik in /backend/data:
    - per categorie (systeem vs user)
    - per sub-segment binnen elke categorie
    - met absolute bytes, human-readable size en percentage
    - inclusief 'andere' bucket voor folders die niet in mapping staan
    """
    total_data_bytes = _dir_size(DATA_DIR)

    # Bereken alle gemapte segmenten + verzamel paden
    categories = {}
    counted_paths = set()

    for cat_id, cat in SEGMENTS.items():
        cat_bytes = 0
        segs = []
        for s in cat["segments"]:
            p = DATA_DIR / s["path"]
            counted_paths.add(s["path"])
            size = _file_size(p) if p.is_file() else _dir_size(p)
            cat_bytes += size
            segs.append({
                "id": s["id"],
                "label": s["label"],
                "color": s["color"],
                "path": s["path"],
                "exists": p.exists(),
                "size_bytes": size,
                "size_human": _human_bytes(size),
            })
        # Sorteer segmenten groot → klein
        segs.sort(key=lambda x: x["size_bytes"], reverse=True)
        categories[cat_id] = {
            "id": cat_id,
            "label": cat["label"],
            "color": cat["color"],
            "description": cat["description"],
            "size_bytes": cat_bytes,
            "size_human": _human_bytes(cat_bytes),
            "segments": segs,
            "percent_of_total": round((cat_bytes / total_data_bytes * 100), 1) if total_data_bytes else 0,
        }

    # Wat zit er nog in /data dat niet gemapt is? = 'overig'
    overig_bytes = 0
    overig_items = []
    for entry in DATA_DIR.iterdir():
        rel = entry.name
        if rel in counted_paths:
            continue
        size = _file_size(entry) if entry.is_file() else _dir_size(entry)
        overig_bytes += size
        overig_items.append({
            "name": rel,
            "is_file": entry.is_file(),
            "size_bytes": size,
            "size_human": _human_bytes(size),
        })
    overig_items.sort(key=lambda x: x["size_bytes"], reverse=True)

    return {
        "total_bytes": total_data_bytes,
        "total_human": _human_bytes(total_data_bytes),
        "categories": list(categories.values()),
        "ongemapt": {
            "label": "Ongemapt (niet gecategoriseerd)",
            "size_bytes": overig_bytes,
            "size_human": _human_bytes(overig_bytes),
            "items": overig_items,
            "percent_of_total": round((overig_bytes / total_data_bytes * 100), 1) if total_data_bytes else 0,
            "color": "#475569",
        }
    }
