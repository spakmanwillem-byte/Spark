"""
Spark Core Logger (v5_spark_logger_001 — Willem's observability vereiste)
=========================================================================

Per-module trace-logger met intent + resultaat. Doelen:

  • Voor en na elke gemarkeerde functie: 1 log-regel met intentie en uitkomst
  • Per-py-module bestand
  • Datum-geïndexeerd: /data/system/logs/YYYY/MM/DD/{module}.jsonl
  • JSON Lines (1 record per regel) → makkelijk te tail-en en te indexeren
  • 28-dagen retentie (automatische opschoning bij startup)

Gebruik:

    from modules.core.spark_logger import traced, log_event

    @traced(intent="user inlog verifiëren")
    def login(user, pwd):
        ...

    log_event("auth", "manual_event", intent="reset wachtwoord", detail={"uid": "..."})

Records-schema:

    {
        "ts": "2026-05-23T12:34:56+00:00",
        "module": "auth",
        "fn": "login",
        "phase": "pre" | "post" | "error" | "event",
        "intent": "user inlog verifiëren",
        "args": {"naam": "Willem"},          # optioneel, getrunceerd
        "result": "ok | success=true",       # samenvatting, geen full payload
        "duration_ms": 12.4,                 # alleen op post/error
        "error": "ValueError: ..."           # alleen op error
    }
"""
from __future__ import annotations

import functools
import inspect
import json
import logging
import shutil
import threading
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, Optional

# Configuratie
LOGS_ROOT = Path(__file__).parent.parent.parent / "data" / "system" / "logs"
RETENTION_DAYS = 28
MAX_ARG_REPR = 80          # max chars per arg in args-summary
MAX_RESULT_REPR = 120      # max chars in result-summary

_file_lock = threading.Lock()
_stdlogger = logging.getLogger("spark_logger")


# ---------------------------------------------------------------------------
# Core write helper
# ---------------------------------------------------------------------------

def _path_for(module: str, when: Optional[datetime] = None) -> Path:
    dt = when or datetime.now(timezone.utc)
    return LOGS_ROOT / f"{dt.year:04d}" / f"{dt.month:02d}" / f"{dt.day:02d}" / f"{module}.jsonl"


def _safe_repr(val: Any, limit: int) -> str:
    try:
        if isinstance(val, (str, int, float, bool)) or val is None:
            s = str(val)
        else:
            s = repr(val)
    except Exception:
        s = "<unrepr>"
    if len(s) > limit:
        s = s[: limit - 1] + "…"
    return s


def _summarize_args(args: tuple, kwargs: dict) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for i, a in enumerate(args):
        out[f"a{i}"] = _safe_repr(a, MAX_ARG_REPR)
    for k, v in kwargs.items():
        out[k] = _safe_repr(v, MAX_ARG_REPR)
    return out


def _summarize_result(val: Any) -> str:
    if val is None:
        return "None"
    if isinstance(val, dict):
        ok = val.get("success")
        keys = ",".join(list(val.keys())[:6])
        if ok is not None:
            return f"dict(success={ok}, keys={keys})"
        return f"dict(keys={keys})"
    if isinstance(val, list):
        return f"list(len={len(val)})"
    return _safe_repr(val, MAX_RESULT_REPR)


def _write(record: Dict[str, Any]):
    """Append record als JSON-Line naar today's log-file."""
    try:
        path = _path_for(record["module"])
        with _file_lock:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
    except Exception as e:
        _stdlogger.warning(f"spark_logger write failed: {e}")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def log_event(module: str, name: str, intent: str = "", detail: Optional[Dict[str, Any]] = None):
    """Schrijf een handmatige event-log (niet via decorator)."""
    rec = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "module": module,
        "fn": name,
        "phase": "event",
        "intent": intent or name,
    }
    if detail:
        rec["detail"] = {k: _safe_repr(v, MAX_RESULT_REPR) for k, v in detail.items()}
    _write(rec)


def traced(intent: str = "", module: Optional[str] = None, log_args: bool = True):
    """
    Decorator: log voor + na elke function-call met intentie en uitkomst.

    Voorbeeld:
        @traced(intent="community bericht versturen", module="bots")
        async def send_message(...):
            ...

    Als module=None: gebruikt het laatste segment van het functie-module-pad
    (bv. `modules.bots.routes` → "bots").
    """
    def decorator(fn: Callable) -> Callable:
        mod_name = module
        if not mod_name:
            fn_module = getattr(fn, "__module__", "unknown")
            parts = [p for p in fn_module.split(".") if p and p != "modules"]
            mod_name = parts[0] if parts else "unknown"
        fn_name = fn.__name__

        is_coro = inspect.iscoroutinefunction(fn)

        if is_coro:
            @functools.wraps(fn)
            async def async_wrapper(*args, **kwargs):
                pre = {
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "module": mod_name, "fn": fn_name, "phase": "pre",
                    "intent": intent or fn_name,
                }
                if log_args:
                    pre["args"] = _summarize_args(args, kwargs)
                _write(pre)
                t0 = time.perf_counter()
                try:
                    result = await fn(*args, **kwargs)
                    _write({
                        "ts": datetime.now(timezone.utc).isoformat(),
                        "module": mod_name, "fn": fn_name, "phase": "post",
                        "intent": intent or fn_name,
                        "result": _summarize_result(result),
                        "duration_ms": round((time.perf_counter() - t0) * 1000, 2),
                    })
                    return result
                except Exception as e:
                    _write({
                        "ts": datetime.now(timezone.utc).isoformat(),
                        "module": mod_name, "fn": fn_name, "phase": "error",
                        "intent": intent or fn_name,
                        "error": f"{type(e).__name__}: {e}",
                        "duration_ms": round((time.perf_counter() - t0) * 1000, 2),
                    })
                    raise
            return async_wrapper

        @functools.wraps(fn)
        def sync_wrapper(*args, **kwargs):
            pre = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "module": mod_name, "fn": fn_name, "phase": "pre",
                "intent": intent or fn_name,
            }
            if log_args:
                pre["args"] = _summarize_args(args, kwargs)
            _write(pre)
            t0 = time.perf_counter()
            try:
                result = fn(*args, **kwargs)
                _write({
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "module": mod_name, "fn": fn_name, "phase": "post",
                    "intent": intent or fn_name,
                    "result": _summarize_result(result),
                    "duration_ms": round((time.perf_counter() - t0) * 1000, 2),
                })
                return result
            except Exception as e:
                _write({
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "module": mod_name, "fn": fn_name, "phase": "error",
                    "intent": intent or fn_name,
                    "error": f"{type(e).__name__}: {e}",
                    "duration_ms": round((time.perf_counter() - t0) * 1000, 2),
                })
                raise
        return sync_wrapper
    return decorator


# ---------------------------------------------------------------------------
# Retention / janitor
# ---------------------------------------------------------------------------

def purge_old_logs(retention_days: int = RETENTION_DAYS) -> Dict[str, Any]:
    """Verwijder log-directories ouder dan `retention_days` dagen.
    Logs zijn georganiseerd als YYYY/MM/DD/, dus we kunnen per-dag-folder opruimen."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=retention_days)).date()
    deleted_dirs = 0
    deleted_files = 0
    if not LOGS_ROOT.exists():
        return {"deleted_dirs": 0, "deleted_files": 0, "cutoff": cutoff.isoformat()}

    for year_dir in sorted(LOGS_ROOT.iterdir()):
        if not year_dir.is_dir() or not year_dir.name.isdigit():
            continue
        year = int(year_dir.name)
        for month_dir in sorted(year_dir.iterdir()):
            if not month_dir.is_dir() or not month_dir.name.isdigit():
                continue
            month = int(month_dir.name)
            for day_dir in sorted(month_dir.iterdir()):
                if not day_dir.is_dir() or not day_dir.name.isdigit():
                    continue
                day = int(day_dir.name)
                try:
                    folder_date = datetime(year, month, day, tzinfo=timezone.utc).date()
                except ValueError:
                    continue
                if folder_date < cutoff:
                    try:
                        deleted_files += len(list(day_dir.glob("*.jsonl")))
                        shutil.rmtree(day_dir)
                        deleted_dirs += 1
                    except Exception as e:
                        _stdlogger.warning(f"purge failed for {day_dir}: {e}")
            # Verwijder lege maand-folders
            try:
                if not any(month_dir.iterdir()):
                    month_dir.rmdir()
            except Exception:
                pass
        try:
            if not any(year_dir.iterdir()):
                year_dir.rmdir()
        except Exception:
            pass

    return {
        "deleted_dirs": deleted_dirs,
        "deleted_files": deleted_files,
        "cutoff": cutoff.isoformat(),
        "retention_days": retention_days,
    }


# ---------------------------------------------------------------------------
# Index / read helpers (gebruikt door admin route)
# ---------------------------------------------------------------------------

def index_tree() -> Dict[str, Any]:
    """Bouw boom: {YYYY: {MM: {DD: [module, ...]}}} van bestaande logs."""
    tree: Dict[str, Any] = {}
    if not LOGS_ROOT.exists():
        return tree
    for year_dir in sorted(LOGS_ROOT.iterdir()):
        if not year_dir.is_dir() or not year_dir.name.isdigit():
            continue
        tree.setdefault(year_dir.name, {})
        for month_dir in sorted(year_dir.iterdir()):
            if not month_dir.is_dir() or not month_dir.name.isdigit():
                continue
            tree[year_dir.name].setdefault(month_dir.name, {})
            for day_dir in sorted(month_dir.iterdir()):
                if not day_dir.is_dir() or not day_dir.name.isdigit():
                    continue
                modules = sorted(p.stem for p in day_dir.glob("*.jsonl"))
                tree[year_dir.name][month_dir.name][day_dir.name] = modules
    return tree


def read_logs(date_str: str, module: str, limit: int = 200, phase: Optional[str] = None) -> Dict[str, Any]:
    """Lees laatste `limit` records van die module op die datum (YYYY-MM-DD).
    Optioneel filteren op phase (pre/post/error/event)."""
    try:
        dt = datetime.fromisoformat(date_str)
    except ValueError:
        return {"records": [], "error": f"Ongeldige datum '{date_str}', verwacht YYYY-MM-DD"}
    fp = _path_for(module, dt)
    if not fp.exists():
        return {"records": [], "total": 0, "path": str(fp.relative_to(LOGS_ROOT.parent.parent.parent))}
    records = []
    try:
        with fp.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                if phase and rec.get("phase") != phase:
                    continue
                records.append(rec)
    except Exception as e:
        return {"records": [], "error": f"Read failed: {e}"}
    total = len(records)
    if limit and limit > 0:
        records = records[-limit:]
    return {"records": records, "total": total, "limit": limit, "phase": phase}
