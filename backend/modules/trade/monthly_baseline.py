"""v13_trader_monthly_baseline_001 — Maandelijkse baseline-snapshot.

Op de 1e van elke maand (of via handmatige call):
  1. Snapshot huidige baseline + live-balance → archief
  2. Reset baseline naar huidige balance
  3. Notitie in user's notes met resultaat vorige maand

Voordeel: users kunnen achteraf per maand precies zien wat hun trader-resultaat
was. Logs in `/data/trade/monthly_baselines/YYYY-MM/{user_id}.json`.
"""
from __future__ import annotations

import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from modules.core.storage import load_json, save_json

DATA_ROOT = Path(__file__).parent.parent.parent / "data"
BASELINE_FP = DATA_ROOT / "trade" / "capital_baseline.json"
MONTHLY_ROOT = DATA_ROOT / "trade" / "monthly_baselines"
MONTHLY_ROOT.mkdir(parents=True, exist_ok=True)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _month_str(dt: Optional[datetime] = None) -> str:
    dt = dt or _now()
    return dt.strftime("%Y-%m")


def _prev_month_str() -> str:
    now = _now()
    if now.month == 1:
        return f"{now.year - 1}-12"
    return f"{now.year}-{now.month - 1:02d}"


def snapshot_user(user_id: str, current_balance_eur: float) -> Dict:
    """Neem snapshot voor 1 user: log oude baseline + resultaat, reset naar huidige balance."""
    baseline_data = load_json(BASELINE_FP, default={})
    old_baseline = baseline_data.get(user_id, {})
    if isinstance(old_baseline, (int, float)):
        old_baseline = {"baseline_eur": float(old_baseline), "set_at": None}
    old_eur = float(old_baseline.get("baseline_eur", 0.0) or 0.0)
    old_set_at = old_baseline.get("set_at")

    month_key = _prev_month_str()  # afsluiting = vorige maand
    month_dir = MONTHLY_ROOT / month_key
    month_dir.mkdir(parents=True, exist_ok=True)

    resultaat = round(current_balance_eur - old_eur, 2)
    snapshot = {
        "id": "snap-" + secrets.token_hex(4),
        "user_id": user_id,
        "month": month_key,
        "closed_at": _now().isoformat(),
        "opening_baseline_eur": old_eur,
        "opening_set_at": old_set_at,
        "closing_balance_eur": round(current_balance_eur, 2),
        "resultaat_eur": resultaat,
        "resultaat_pct": round((resultaat / old_eur * 100.0) if old_eur > 0 else 0.0, 2),
    }
    save_json(month_dir / f"{user_id}.json", snapshot)

    # Nieuwe baseline = huidige balance
    baseline_data[user_id] = {
        "baseline_eur": round(current_balance_eur, 2),
        "set_at": _now().isoformat(),
        "note": f"Auto-snapshot maand-open {_month_str()} (na afsluiting {month_key})",
        "previous_month_result_eur": resultaat,
    }
    save_json(BASELINE_FP, baseline_data)

    # Notitie in user's notes
    try:
        notes_fp = DATA_ROOT / "users" / user_id / "notes.json"
        notes_fp.parent.mkdir(parents=True, exist_ok=True)
        ndata = load_json(notes_fp, default={"notes": []})
        arrow = "📈" if resultaat >= 0 else "📉"
        ndata.setdefault("notes", []).append({
            "id": "note-" + secrets.token_hex(4),
            "titel": f"{arrow} Trader-resultaat {month_key}: €{resultaat:+.2f}",
            "inhoud": f"Maand-afsluiting {month_key}\n"
                     f"Startsaldo: €{old_eur:.2f}\n"
                     f"Eindsaldo: €{current_balance_eur:.2f}\n"
                     f"Resultaat: €{resultaat:+.2f} ({snapshot['resultaat_pct']:+.2f}%)\n\n"
                     f"Nieuwe baseline per {_now().strftime('%Y-%m-%d')}: €{current_balance_eur:.2f}",
            "created_at": _now().isoformat(),
            "tags": ["trader", "maand-afsluiting", month_key],
            "source": "monthly_baseline_snapshot",
        })
        save_json(notes_fp, ndata)
    except Exception:
        pass

    return snapshot


def snapshot_all(get_balance_fn) -> List[Dict]:
    """Snapshot alle users met een baseline. `get_balance_fn(user_id) -> float`."""
    baseline_data = load_json(BASELINE_FP, default={})
    results = []
    for uid in baseline_data.keys():
        if not uid.startswith("user-"):
            continue
        try:
            bal = float(get_balance_fn(uid) or 0.0)
        except Exception:
            bal = 0.0
        results.append(snapshot_user(uid, bal))
    return results


def list_monthly_snapshots(user_id: Optional[str] = None, limit: int = 12) -> List[Dict]:
    """Historie: laatste N maanden. Optioneel gefilterd per user."""
    out = []
    for month_dir in sorted(MONTHLY_ROOT.glob("*"), reverse=True)[:limit]:
        if not month_dir.is_dir():
            continue
        if user_id:
            fp = month_dir / f"{user_id}.json"
            if fp.exists():
                out.append(load_json(fp, default=None))
        else:
            for fp in month_dir.glob("*.json"):
                out.append(load_json(fp, default=None))
    return [x for x in out if x]


def should_run_snapshot() -> bool:
    """Check: is het de 1e van de maand en is er nog geen snapshot voor deze maand?"""
    now = _now()
    if now.day != 1:
        return False
    prev_month = _prev_month_str()
    marker = MONTHLY_ROOT / prev_month / "_snapshot_done.marker"
    return not marker.exists()


def mark_snapshot_done():
    prev_month = _prev_month_str()
    d = MONTHLY_ROOT / prev_month
    d.mkdir(parents=True, exist_ok=True)
    (d / "_snapshot_done.marker").write_text(_now().isoformat())
