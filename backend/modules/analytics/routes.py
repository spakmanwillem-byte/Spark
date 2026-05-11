"""
Analytics routes — storage breakdown (systeem vs user data)
+ live system info (CPU, geheugen, schijf, netwerk, OS, Python)
"""
import os
import platform
import socket
import sys
import time
from pathlib import Path
from fastapi import APIRouter

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

router = APIRouter(prefix="/analytics", tags=["analytics"])

DATA_DIR = Path(__file__).parent.parent.parent / "data"
APP_ROOT = Path(__file__).parent.parent.parent

# Process-start timestamp voor uptime
_START_TIME = time.time()

# In-memory recent requests tracker (laatste 50)
_RECENT_REQUESTS: list = []
_MAX_RECENT = 50


def track_request(ip: str, method: str, path: str, status: int, duration_ms: float):
    """Aangeroepen vanuit middleware om recente requests te tonen."""
    _RECENT_REQUESTS.append({
        "ip": ip,
        "method": method,
        "path": path,
        "status": status,
        "duration_ms": round(duration_ms, 1),
        "ts": time.time(),
    })
    if len(_RECENT_REQUESTS) > _MAX_RECENT:
        del _RECENT_REQUESTS[:-_MAX_RECENT]


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


# ============================================================
# LIVE SYSTEM INFO (psutil-based, dynamisch — werkt overal)
# ============================================================

def _format_uptime(seconds: float) -> str:
    seconds = int(seconds)
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    parts = []
    if days: parts.append(f"{days}d")
    if hours: parts.append(f"{hours}u")
    if minutes or not parts: parts.append(f"{minutes}m")
    return " ".join(parts)


@router.get("/system-info")
def get_system_info():
    """
    Live runtime info van het systeem waar Spark op draait.
    Volledig dynamisch — werkt op elke machine, ook na verplaatsing via zip.
    """
    info = {
        "host": {
            "hostname": socket.gethostname(),
            "platform": platform.system(),
            "platform_release": platform.release(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor() or platform.machine(),
            "python_version": sys.version.split()[0],
            "python_implementation": platform.python_implementation(),
        },
        "app": {
            "root": str(APP_ROOT),
            "uptime_seconds": int(time.time() - _START_TIME),
            "uptime_human": _format_uptime(time.time() - _START_TIME),
        },
        "psutil_available": HAS_PSUTIL,
    }

    if not HAS_PSUTIL:
        return info

    # CPU
    cpu_freq = psutil.cpu_freq()
    info["cpu"] = {
        "percent": psutil.cpu_percent(interval=0.3),
        "count_logical": psutil.cpu_count(logical=True),
        "count_physical": psutil.cpu_count(logical=False),
        "freq_current_mhz": round(cpu_freq.current, 1) if cpu_freq else None,
        "freq_max_mhz": round(cpu_freq.max, 1) if cpu_freq and cpu_freq.max else None,
        "per_core_percent": psutil.cpu_percent(interval=0, percpu=True),
    }

    # Geheugen
    mem = psutil.virtual_memory()
    info["memory"] = {
        "total_bytes": mem.total,
        "available_bytes": mem.available,
        "used_bytes": mem.used,
        "percent": mem.percent,
        "total_human": _human_bytes(mem.total),
        "used_human": _human_bytes(mem.used),
        "available_human": _human_bytes(mem.available),
    }

    # Schijf — uitlezen van waar Spark daadwerkelijk staat
    disk = psutil.disk_usage(str(APP_ROOT))
    # Probeer fstype/device te detecteren
    disk_type = "unknown"
    disk_device = "unknown"
    try:
        partitions = psutil.disk_partitions(all=False)
        app_path = str(APP_ROOT.resolve())
        # Match longest mountpoint prefix
        best = None
        for p in partitions:
            if app_path.startswith(p.mountpoint):
                if best is None or len(p.mountpoint) > len(best.mountpoint):
                    best = p
        if best:
            disk_type = best.fstype or "unknown"
            disk_device = best.device
    except (PermissionError, OSError):
        pass

    info["disk"] = {
        "mount": str(APP_ROOT),
        "device": disk_device,
        "fs_type": disk_type,
        "total_bytes": disk.total,
        "used_bytes": disk.used,
        "free_bytes": disk.free,
        "percent": disk.percent,
        "total_human": _human_bytes(disk.total),
        "used_human": _human_bytes(disk.used),
        "free_human": _human_bytes(disk.free),
    }

    # Netwerk
    net = psutil.net_io_counters()
    info["network"] = {
        "bytes_sent": net.bytes_sent,
        "bytes_recv": net.bytes_recv,
        "sent_human": _human_bytes(net.bytes_sent),
        "recv_human": _human_bytes(net.bytes_recv),
        "packets_sent": net.packets_sent,
        "packets_recv": net.packets_recv,
        "interfaces": list(psutil.net_if_addrs().keys()),
    }

    # Process info (deze Spark process zelf)
    try:
        proc = psutil.Process(os.getpid())
        info["process"] = {
            "pid": proc.pid,
            "name": proc.name(),
            "memory_used_bytes": proc.memory_info().rss,
            "memory_used_human": _human_bytes(proc.memory_info().rss),
            "cpu_percent": proc.cpu_percent(interval=0.1),
            "threads": proc.num_threads(),
            "create_time": proc.create_time(),
        }
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass

    return info


# ============================================================
# LIVE NETWORK INFO
# ============================================================

# Bewaar vorige meting voor delta-rate berekening
_PREV_NET = {"ts": None, "sent": 0, "recv": 0}


@router.get("/network-info")
def get_network_info():
    """
    Live netwerk-info: interfaces, IPs, counters, throughput rate, recente requests.
    """
    if not HAS_PSUTIL:
        return {"error": "psutil niet beschikbaar"}

    # Interfaces met adressen
    interfaces = []
    addrs = psutil.net_if_addrs()
    stats = psutil.net_if_stats()
    for ifname, addr_list in addrs.items():
        ipv4 = None
        ipv6 = None
        mac = None
        for a in addr_list:
            if a.family == socket.AF_INET:
                ipv4 = a.address
            elif a.family == socket.AF_INET6:
                ipv6 = a.address
            elif a.family == psutil.AF_LINK:
                mac = a.address
        st = stats.get(ifname)
        interfaces.append({
            "name": ifname,
            "ipv4": ipv4,
            "ipv6": ipv6 if ipv6 and not ipv6.startswith("fe80") else None,
            "mac": mac,
            "is_up": st.isup if st else None,
            "speed_mbps": st.speed if st and st.speed > 0 else None,
            "mtu": st.mtu if st else None,
        })

    # Totale counters
    net = psutil.net_io_counters()
    total = {
        "bytes_sent": net.bytes_sent,
        "bytes_recv": net.bytes_recv,
        "sent_human": _human_bytes(net.bytes_sent),
        "recv_human": _human_bytes(net.bytes_recv),
        "packets_sent": net.packets_sent,
        "packets_recv": net.packets_recv,
        "errin": net.errin,
        "errout": net.errout,
        "dropin": net.dropin,
        "dropout": net.dropout,
    }

    # Rate (bytes/sec sinds vorige call)
    now = time.time()
    rate_sent_bps = 0
    rate_recv_bps = 0
    if _PREV_NET["ts"] is not None:
        elapsed = now - _PREV_NET["ts"]
        if elapsed > 0:
            rate_sent_bps = max(0, (net.bytes_sent - _PREV_NET["sent"]) / elapsed)
            rate_recv_bps = max(0, (net.bytes_recv - _PREV_NET["recv"]) / elapsed)
    _PREV_NET["ts"] = now
    _PREV_NET["sent"] = net.bytes_sent
    _PREV_NET["recv"] = net.bytes_recv

    # Per-interface counters
    per_if = []
    if_counters = psutil.net_io_counters(pernic=True)
    for ifname, c in if_counters.items():
        per_if.append({
            "name": ifname,
            "sent_human": _human_bytes(c.bytes_sent),
            "recv_human": _human_bytes(c.bytes_recv),
            "bytes_sent": c.bytes_sent,
            "bytes_recv": c.bytes_recv,
        })

    # Connections (kan permission denied geven in container — vang af)
    conn_counts = {"ESTABLISHED": 0, "LISTEN": 0, "TIME_WAIT": 0, "OTHER": 0}
    try:
        for c in psutil.net_connections(kind="inet"):
            s = c.status
            if s in conn_counts:
                conn_counts[s] += 1
            else:
                conn_counts["OTHER"] += 1
    except (psutil.AccessDenied, PermissionError):
        conn_counts = None  # niet beschikbaar in container

    # Recente requests (laatste 20)
    recent = sorted(_RECENT_REQUESTS[-20:], key=lambda r: r["ts"], reverse=True)
    recent_formatted = []
    for r in recent:
        age = now - r["ts"]
        if age < 60:
            age_str = f"{int(age)}s geleden"
        elif age < 3600:
            age_str = f"{int(age // 60)}m geleden"
        else:
            age_str = f"{int(age // 3600)}u geleden"
        recent_formatted.append({**r, "age_str": age_str})

    return {
        "interfaces": interfaces,
        "total": total,
        "throughput": {
            "sent_bps": rate_sent_bps,
            "recv_bps": rate_recv_bps,
            "sent_human": _human_bytes(rate_sent_bps) + "/s",
            "recv_human": _human_bytes(rate_recv_bps) + "/s",
        },
        "per_interface": per_if,
        "connections": conn_counts,
        "recent_requests": recent_formatted,
        "recent_count": len(_RECENT_REQUESTS),
    }
