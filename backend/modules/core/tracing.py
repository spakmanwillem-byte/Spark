"""
v7_function_tracing_001 — Function-call logger voor observability.

Purpose:
    Bij elke gedecoreerde functie schrijven we entry/exit + timing + result-hash
    naar een dagelijks log-bestand. Zo weet Spark (en de main agent bij een handoff)
    exact wat er is gebeurd zonder de hele code te hoeven lezen.

Metadata pattern:
    Elke log-entry heeft: timestamp | function | args (redacted) | duration_ms | status

Log location:
    /app/backend/data/trade/logs/trace_YYYY-MM-DD.jsonl  (JSONL, 1 entry per regel)

Usage:
    from modules.core.tracing import trace_call

    @trace_call(category="trade.buy")
    def open_cluster(user_id, pot_ids, entry_price, ...):
        ...

Best-practice:
    - Redact PII / secrets in args (api_key, password, private_key)
    - Log alleen return-shape (keys + success), niet volledige payload
    - Sample high-frequency calls (bv. 1/10) via `sample_rate` param
"""
from functools import wraps
from pathlib import Path
from datetime import datetime, timezone
import json
import time
import threading

_LOG_DIR = Path(__file__).parent.parent.parent / "data" / "trade" / "logs"
_LOG_DIR.mkdir(parents=True, exist_ok=True)
_LOG_LOCK = threading.Lock()

REDACT_KEYS = {"api_key", "apikey", "secret", "password", "private_key", "token"}


def _redact(v):
    """Beperk args-log tot type + lengte om PII/secrets/kilobytes JSON te vermijden."""
    if isinstance(v, (int, float, bool, type(None))):
        return v
    if isinstance(v, str):
        return v if len(v) <= 40 else f"<str len={len(v)}>"
    if isinstance(v, dict):
        return {k: ("<REDACTED>" if k.lower() in REDACT_KEYS else _redact(v[k])) for k in list(v.keys())[:8]}
    if isinstance(v, (list, tuple)):
        return f"<{type(v).__name__} len={len(v)}>"
    return f"<{type(v).__name__}>"


def _log_line(entry: dict):
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    fp = _LOG_DIR / f"trace_{day}.jsonl"
    line = json.dumps(entry, default=str) + "\n"
    with _LOG_LOCK:
        with open(fp, "a", encoding="utf-8") as f:
            f.write(line)


def trace_call(category: str = "general", sample_rate: float = 1.0):
    """Decorator: log entry + exit + timing van functie.

    Args:
        category: label voor filtering ("trade.buy", "trade.sell", "kb.write" etc.)
        sample_rate: 0.0-1.0 fraction om te loggen (voor high-freq calls)
    """
    def deco(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            import random
            do_log = random.random() < sample_rate
            start = time.time()
            fn_name = f"{fn.__module__}.{fn.__name__}"
            if do_log:
                try:
                    _log_line({
                        "ts": datetime.now(timezone.utc).isoformat(),
                        "cat": category,
                        "fn": fn_name,
                        "phase": "enter",
                        "args": [_redact(a) for a in args[:5]],
                        "kwargs": {k: _redact(v) for k, v in list(kwargs.items())[:8]},
                    })
                except Exception:
                    pass
            try:
                result = fn(*args, **kwargs)
                if do_log:
                    dur_ms = int((time.time() - start) * 1000)
                    _log_line({
                        "ts": datetime.now(timezone.utc).isoformat(),
                        "cat": category,
                        "fn": fn_name,
                        "phase": "exit",
                        "duration_ms": dur_ms,
                        "status": "ok",
                        "result_shape": _redact(result),
                    })
                return result
            except Exception as e:
                if do_log:
                    dur_ms = int((time.time() - start) * 1000)
                    _log_line({
                        "ts": datetime.now(timezone.utc).isoformat(),
                        "cat": category,
                        "fn": fn_name,
                        "phase": "error",
                        "duration_ms": dur_ms,
                        "error_type": type(e).__name__,
                        "error_msg": str(e)[:200],
                    })
                raise
        return wrapper
    return deco
