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
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

# v8_odroid_portability_001 — Portable path: gebruik SPARK_DATA_DIR env-var,
# fallback op relatieve pad t.o.v. deze file (backend/modules/scheduler/ → backend/data)
DATA = Path(os.environ.get("SPARK_DATA_DIR") or (Path(__file__).parent.parent.parent / "data"))
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
    v6_price_chart_density_001 (sessie 15) — interval verlaagd naar 5 minuten
    zodat fluctuaties in de Bitvavo-balance zichtbaar worden in de grafiek.
    """
    now = datetime.now(timezone.utc)
    state = _load_state()
    last_str = state.get("roar_price_snapshot_last")
    if last_str:
        try:
            last = datetime.fromisoformat(last_str.replace("Z", "+00:00"))
            if (now - last).total_seconds() < 300:  # < 5 min geleden
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


async def _maybe_staking_growth():
    """v6_staking_growth_engine_001 — eens per 24 uur staking growth cycle draaien.
    Auto-rente check is intern op 30-dag interval, dus dagelijkse trigger is safe.
    """
    now = datetime.now(timezone.utc)
    state = _load_state()
    last_str = state.get("staking_growth_last")
    if last_str:
        try:
            last = datetime.fromisoformat(last_str.replace("Z", "+00:00"))
            if (now - last).total_seconds() < 86400:  # < 24h geleden
                return
        except Exception:
            pass
    try:
        from modules.trade.staking_growth import run_growth_cycle
        result = run_growth_cycle(force=False)
        state["staking_growth_last"] = now.isoformat()
        _save_state(state)
        actions = result.get("actions", [])
        if actions:
            print(f"[scheduler] staking growth: {len(actions)} acties ({len(result.get('minted_pots', []))} mints)")
    except Exception as ex:
        print(f"[scheduler] staking growth failed: {ex}")


async def _maybe_weekly_report():
    """v6_boekhouder_weekrapport_001 (sessie 14) — Zondagavond rond 20:00 het
    wekelijks Boekhouder-rapport sturen. Idempotent: 1 keer per 6+ dagen.
    """
    now = datetime.now(timezone.utc)
    # Trigger-window: zondag (weekday=6) tussen 20:00 en 22:00 UTC
    if now.weekday() != 6 or now.hour < 20 or now.hour >= 22:
        return
    state = _load_state()
    last_str = state.get("weekly_report_last")
    if last_str:
        try:
            last = datetime.fromisoformat(last_str.replace("Z", "+00:00"))
            if (now - last).total_seconds() < 6 * 86400:  # < 6 dagen geleden
                return
        except Exception:
            pass
    try:
        from modules.boekhouder.weekly_report import send_weekly_report
        send_weekly_report(also_community=False)
        state["weekly_report_last"] = now.isoformat()
        _save_state(state)
        print("[scheduler] weekly boekhouder report sent")
    except Exception as ex:
        print(f"[scheduler] weekly report failed: {ex}")


async def _maybe_daily_brief():
    """v6_daily_brief_scheduler_001 — 1× per dag een Daagse Brief genereren voor
    elke user die vandaag activiteit had (>= 3 chat-turns). Trigger om 03:00 UTC
    (rustige uren). Idempotent: state-file voorkomt dubbele run.
    """
    now = datetime.now(timezone.utc)
    # Trigger alleen tussen 02:00-04:00 UTC (rustige uren)
    if now.hour not in (2, 3):
        return
    today = now.date().isoformat()
    state = _load_state()
    if state.get("daily_brief_date") == today:
        return  # al gedraaid vandaag

    try:
        from modules.spark_planner.brief_builder import build_daily_brief
        # Vind users met activiteit vandaag
        chat_logs_dir = DATA / "chat" / "logs"
        if not chat_logs_dir.exists():
            return

        # Bron 1: per-user JSON files (user-001.json bv.)
        active_users = set()
        for fp in chat_logs_dir.glob("user-*.json"):
            try:
                user_id = fp.stem
                with open(fp, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # Tel turns van vandaag (ruwe heuristiek: laatste mtime <= 1 dag)
                mtime = datetime.fromtimestamp(fp.stat().st_mtime, tz=timezone.utc)
                if (now - mtime).total_seconds() < 86400:
                    convs = data.get("conversations", []) if isinstance(data, dict) else []
                    if len(convs) >= 3:
                        active_users.add(user_id)
            except Exception:
                continue

        if not active_users:
            state["daily_brief_date"] = today
            state["daily_brief_users"] = 0
            _save_state(state)
            return

        # Genereer briefs (max 30 users/dag om budget te bewaken)
        results = {"success": 0, "skipped": 0, "errors": 0}
        for user_id in list(active_users)[:30]:
            try:
                r = await build_daily_brief(user_id)
                if r.get("success"):
                    results["success"] += 1
                else:
                    results["skipped"] += 1
            except Exception as ex:
                results["errors"] += 1
                print(f"[scheduler] daily-brief {user_id} failed: {ex}")

        state["daily_brief_date"] = today
        state["daily_brief_users"] = results["success"]
        state["daily_brief_results"] = results
        _save_state(state)
        print(f"[scheduler] daily briefs: {results}")
    except Exception as ex:
        print(f"[scheduler] daily-brief loop failed: {ex}")


async def scheduler_loop():
    """Hoofdloop — draait elke 5 minuten."""
    print("[scheduler] v6_scheduler_001 gestart (interval 5min)")
    while True:
        try:
            await _maybe_boekhouder_roundup()
            await _maybe_error_bark()
            await _maybe_roar_price_snapshot()
            await _maybe_staking_growth()
            await _maybe_weekly_report()
            await _maybe_daily_brief()
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
