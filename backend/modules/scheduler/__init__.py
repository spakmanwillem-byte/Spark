"""
Scheduler service (v6_scheduler_001)
======================================
Achtergrond-loop die periodieke taken uitvoert:
  1. Boekhouder 21:00 roundup-bark in community (1x/dag)
  2. Spark "merkt eigen errors" — scant log-files elke 5 min,
     bij nieuwe `phase=error` records → Madelief-bark in community

Gestart vanuit server.py startup-event. Stille fail.
"""
import asyncio
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

DATA = Path("/app/backend/data")
LOG_ROOT = DATA / "system" / "logs"
STATE_FILE = DATA / "system" / "scheduler_state.json"

# ============================================================
# STATE (persistent — laatste run-times)
# ============================================================
def _load_state() -> dict:
    if not STATE_FILE.exists():
        return {}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_state(s: dict):
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(s, f, indent=2)
    except Exception:
        pass


# ============================================================
# 1. BOEKHOUDER 21:00 ROUNDUP BARK
# ============================================================
async def _maybe_boekhouder_roundup():
    """Eens per dag rond 21:00 NL een bark posten met dag-summary."""
    now = datetime.now(timezone.utc)
    # 21:00 NL = 19:00 UTC (winter) of 20:00 UTC (zomer). We trigger als hour == 19 of 20.
    if now.hour not in (19, 20):
        return
    state = _load_state()
    last = state.get("boekhouder_last_roundup")
    today_str = now.strftime("%Y-%m-%d")
    if last == today_str:
        return  # al gedraaid vandaag

    # Bouw bark-tekst uit boekhouder.list_closings + audit
    try:
        from modules.boekhouder import service as boekhouder
        closings = boekhouder.list_closings(limit=5).get("closings", [])
    except Exception:
        closings = []

    try:
        from modules.audit import weak_trigger_scan
        wt = weak_trigger_scan()
        weak_pct = wt.get("weak_pct", 0)
    except Exception:
        weak_pct = None

    parts = ["📋 **Boekhouder dagelijkse roundup** — 21:00", ""]
    if closings:
        parts.append(f"💼 {len(closings)} recente closings; laatste: {closings[0].get('user_id','?')} op {closings[0].get('closed_at','?')[:16]}")
    else:
        parts.append("💼 Geen closings vandaag.")
    if weak_pct is not None:
        parts.append(f"🧠 Kennisbank-gezondheid: {100 - weak_pct:.0f}% kaarten met laag1.")
    parts.append("")
    parts.append("_Slaap zacht — Spark blijft wakker._")
    msg = "\n".join(parts)

    # Stuur via bots community-route
    try:
        from modules.core.storage import load_json, save_json
        comm_file = DATA / "community" / "messages.json"
        comm = load_json(comm_file, default={"messages": []})
        comm.setdefault("messages", []).append({
            "id": f"bark-roundup-{today_str}",
            "user_id": "bot-boekhouder",
            "user_name": "De Boekhouder",
            "message": msg,
            "ts": now.isoformat(),
            "kind": "boekhouder_roundup",
            "source": "scheduler_v6",
        })
        save_json(comm_file, comm)
        state["boekhouder_last_roundup"] = today_str
        _save_state(state)
        print(f"[scheduler] boekhouder roundup posted for {today_str}")
    except Exception as ex:
        print(f"[scheduler] boekhouder roundup failed: {ex}")


# ============================================================
# 2. SPARK MERKT EIGEN ERRORS — log-watcher
# ============================================================
async def _maybe_error_bark():
    """Scan log-files vanaf last_checked_ts. Bij nieuwe error-records → Madelief bark."""
    state = _load_state()
    last_iso = state.get("error_scan_last_ts")
    if last_iso:
        try:
            last_dt = datetime.fromisoformat(last_iso)
        except Exception:
            last_dt = datetime.now(timezone.utc) - timedelta(minutes=10)
    else:
        last_dt = datetime.now(timezone.utc) - timedelta(minutes=10)

    today = datetime.now(timezone.utc)
    new_errors = []
    # Check vandaag + gisteren (in geval van middernacht-overgang)
    for offset in (0, 1):
        check_day = today - timedelta(days=offset)
        day_dir = LOG_ROOT / check_day.strftime("%Y") / check_day.strftime("%m") / check_day.strftime("%d")
        if not day_dir.exists():
            continue
        for fp in day_dir.glob("*.jsonl"):
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    for ln in f:
                        ln = ln.strip()
                        if not ln:
                            continue
                        try:
                            ev = json.loads(ln)
                        except Exception:
                            continue
                        if ev.get("phase") != "error":
                            continue
                        ts = ev.get("ts") or ev.get("timestamp")
                        if not ts:
                            continue
                        try:
                            ev_dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                        except Exception:
                            continue
                        if ev_dt > last_dt:
                            new_errors.append({
                                "module": ev.get("module", "?"),
                                "intent": ev.get("intent", "?"),
                                "err": (ev.get("error") or ev.get("err") or "?")[:160],
                                "ts": ts,
                            })
            except Exception:
                continue

    state["error_scan_last_ts"] = today.isoformat()
    _save_state(state)

    if not new_errors:
        return

    # Beperken tot 3 om community niet te overspoelen
    new_errors = new_errors[:3]
    parts = ["🐛 **Madelief heeft iets opgevangen**", ""]
    for e in new_errors:
        parts.append(f"• `{e['module']}` — {e['intent']}: {e['err']}")
    parts.append("")
    parts.append("_Spark gaat er mee aan de slag._")
    msg = "\n".join(parts)
    try:
        from modules.core.storage import load_json, save_json
        comm_file = DATA / "community" / "messages.json"
        comm = load_json(comm_file, default={"messages": []})
        comm.setdefault("messages", []).append({
            "id": f"bark-err-{today.strftime('%Y%m%dT%H%M%S')}",
            "user_id": "bot-madelief",
            "user_name": "Madelief Stouten",
            "message": msg,
            "ts": today.isoformat(),
            "kind": "self_error_bark",
            "source": "scheduler_v6",
            "errors": new_errors,
        })
        save_json(comm_file, comm)
        print(f"[scheduler] madelief error-bark posted ({len(new_errors)} errors)")
    except Exception as ex:
        print(f"[scheduler] error-bark failed: {ex}")


# ============================================================
# MAIN LOOP
# ============================================================
async def _maybe_roar_price_snapshot():
    """v6_price_history_snapshots_002 (sessie 14) — eens per uur ROAR-prijs
    vastleggen in roar/price_snapshots.json zodat de grafiek altijd data heeft,
    ook na een clean_slate of in lage-activiteit periodes.
    """
    now = datetime.now(timezone.utc)
    state = _load_state()
    last_str = state.get("roar_price_snapshot_last")
    if last_str:
        try:
            last = datetime.fromisoformat(last_str.replace("Z", "+00:00"))
            if (now - last).total_seconds() < 3600:  # < 1 uur geleden
                return
        except Exception:
            pass
    try:
        from modules.shop.routes import get_dynamic_price
        from modules.core.storage import load_json, save_json
        SNAPS = DATA / "roar" / "price_snapshots.json"
        price = float(get_dynamic_price() or 0)
        if price <= 0:
            return
        d = load_json(SNAPS, default={"snapshots": []})
        d["snapshots"].append({"ts": now.isoformat(), "price_eur": round(price, 4)})
        if len(d["snapshots"]) > 5000:
            d["snapshots"] = d["snapshots"][-5000:]
        save_json(SNAPS, d)
        state["roar_price_snapshot_last"] = now.isoformat()
        _save_state(state)
        print(f"[scheduler] roar price-snapshot saved: €{price:.2f}")
    except Exception as ex:
        print(f"[scheduler] roar price-snapshot failed: {ex}")


async def scheduler_loop():
    """Hoofdloop — draait elke 5 minuten."""
    print("[scheduler] v6_scheduler_001 gestart (interval 5min)")
    while True:
        try:
            await _maybe_boekhouder_roundup()
            await _maybe_error_bark()
            await _maybe_roar_price_snapshot()
        except Exception as ex:
            print(f"[scheduler] loop iteration error: {ex}")
        await asyncio.sleep(300)  # 5 min


def start_scheduler_in_background():
    """Aanroep vanuit FastAPI startup-event."""
    try:
        loop = asyncio.get_event_loop()
        loop.create_task(scheduler_loop())
        print("[scheduler] v6_scheduler_001 task scheduled in background")
    except RuntimeError:
        # Geen running loop yet — wordt later via on_event("startup") opnieuw geprobeerd
        pass
