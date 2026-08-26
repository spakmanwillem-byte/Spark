"""
Agenda Routes - Events CRUD per user
Schema v1: {events: [{id, titel, beschrijving, date, reminder, status, created_at}]}

v13d_multi_module_privacy_001 (sessie 55) — Willem: "iedere user in eco-container".
GET/PATCH/DELETE endpoints eisen nu een `viewer_id` query-param die mag toegang
tot target user_id in de path. Owner en admin mogen; anders 403.
"""
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
from datetime import datetime, timezone
import uuid
from modules.core.storage import load_json, save_json
from modules.core.privacy import require_access

router = APIRouter(prefix="/agenda", tags=["agenda"])
DATA_DIR = Path(__file__).parent.parent.parent / "data" / "agenda"


# v13d_agenda_uren_registratie_001 (sessie 56b) — Willem: "kies privé/zakelijk,
# start/eind tijd, bij zakelijk pauze + opdrachtgever + onderwerp voor
# uren-registratie". Alle nieuwe velden optioneel voor backwards compat.
class EventCreate(BaseModel):
    titel: str
    beschrijving: Optional[str] = None
    date: str  # ISO datetime — geldt als start-tijd
    reminder: bool = False
    # Nieuwe velden (sessie 56b)
    scope: Optional[str] = "prive"  # 'prive' | 'zakelijk'
    end_date: Optional[str] = None  # ISO datetime — eind-tijd
    pauze_minuten: Optional[int] = None  # alleen bij zakelijk
    opdrachtgever: Optional[str] = None  # alleen bij zakelijk
    onderwerp: Optional[str] = None  # alleen bij zakelijk
    product_code: Optional[str] = None  # future-use bij zakelijk


class EventUpdate(BaseModel):
    titel: Optional[str] = None
    beschrijving: Optional[str] = None
    date: Optional[str] = None
    reminder: Optional[bool] = None
    status: Optional[str] = None
    scope: Optional[str] = None
    end_date: Optional[str] = None
    pauze_minuten: Optional[int] = None
    opdrachtgever: Optional[str] = None
    onderwerp: Optional[str] = None
    product_code: Optional[str] = None


def _compute_totaal_uren(start_iso: Optional[str], end_iso: Optional[str], pauze_min: Optional[int]) -> Optional[float]:
    """Bereken gewerkte uren = (end - start) - pauze. Return None als niet mogelijk."""
    if not start_iso or not end_iso:
        return None
    try:
        s = datetime.fromisoformat(start_iso.replace("Z", "+00:00"))
        e = datetime.fromisoformat(end_iso.replace("Z", "+00:00"))
        if e <= s:
            return None
        minuten = (e - s).total_seconds() / 60.0 - (pauze_min or 0)
        if minuten <= 0:
            return 0.0
        return round(minuten / 60.0, 2)
    except (ValueError, TypeError):
        return None


def _get_file(user_id: str) -> Path:
    return DATA_DIR / f"{user_id}.json"


@router.get("/events/{user_id}")
async def get_events(user_id: str, viewer_id: Optional[str] = Query(None)):
    # Backwards-compat: als viewer_id niet meegestuurd is, val terug op user_id
    # (zelfde user opvraag). Nieuwe frontends sturen viewer_id expliciet mee.
    require_access(viewer_id or user_id, user_id)
    data = load_json(_get_file(user_id), default={"events": []})
    return data


@router.post("/events/{user_id}")
async def create_event(user_id: str, event: EventCreate):
    filepath = _get_file(user_id)
    data = load_json(filepath, default={"events": []})
    scope = event.scope if event.scope in ("prive", "zakelijk") else "prive"
    totaal_uren = _compute_totaal_uren(event.date, event.end_date, event.pauze_minuten) if scope == "zakelijk" else None
    new_event = {
        "id": str(uuid.uuid4())[:8],
        "titel": event.titel,
        "beschrijving": event.beschrijving,
        "date": event.date,
        "reminder": event.reminder,
        "status": "upcoming",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "scope": scope,
        "end_date": event.end_date,
        "pauze_minuten": event.pauze_minuten if scope == "zakelijk" else None,
        "opdrachtgever": event.opdrachtgever if scope == "zakelijk" else None,
        "onderwerp": event.onderwerp if scope == "zakelijk" else None,
        "product_code": event.product_code if scope == "zakelijk" else None,
        "totaal_uren": totaal_uren,
    }
    data["events"].append(new_event)
    save_json(filepath, data)
    return {"success": True, "event": new_event}


@router.put("/events/{user_id}/{event_id}")
async def update_event(user_id: str, event_id: str, updates: EventUpdate):
    filepath = _get_file(user_id)
    data = load_json(filepath, default={"events": []})
    for ev in data["events"]:
        if ev["id"] == event_id:
            for k, v in updates.model_dump(exclude_none=True).items():
                ev[k] = v
            # Herbereken totaal_uren wanneer relevante velden zijn aangepast
            if ev.get("scope") == "zakelijk":
                ev["totaal_uren"] = _compute_totaal_uren(
                    ev.get("date"), ev.get("end_date"), ev.get("pauze_minuten")
                )
            save_json(filepath, data)
            return {"success": True, "event": ev}
    return {"success": False, "message": "Event niet gevonden"}


@router.delete("/events/{user_id}/{event_id}")
async def delete_event(user_id: str, event_id: str):
    filepath = _get_file(user_id)
    data = load_json(filepath, default={"events": []})
    before = len(data["events"])
    data["events"] = [e for e in data["events"] if e["id"] != event_id]
    if len(data["events"]) < before:
        save_json(filepath, data)
        return {"success": True}
    return {"success": False, "message": "Event niet gevonden"}



# v13_agenda_monthly_archive_001 (sessie 54) — Willem: op de 1e van elke maand
# oude events archiveren zodat de tab schoon blijft maar Spark de historie behoudt.
from . import archive_service as _archive


@router.get("/archive/{user_id}")
async def list_archive(user_id: str):
    """Lijst alle gearchiveerde maand-bestanden voor deze user. Elk bestand
    bevat de events van één afgelopen maand."""
    from pathlib import Path
    d = Path("/app/backend/data/users") / user_id / "archive" / "agenda_archief"
    if not d.exists():
        return {"user_id": user_id, "months": [], "total_events": 0}
    months = []
    total = 0
    for f in sorted(d.glob("agenda-*.json"), reverse=True):
        data = load_json(f, default={"events": []})
        n = len(data.get("events", []))
        total += n
        months.append({
            "month": data.get("month") or f.stem.replace("agenda-", ""),
            "filename": f.name,
            "event_count": n,
            "archived_at": data.get("archived_at"),
        })
    return {"user_id": user_id, "months": months, "total_events": total}


@router.get("/archive/{user_id}/{month}")
async def get_archived_month(user_id: str, month: str):
    """Alle events van een specifieke maand. `month` = YYYY-MM."""
    from pathlib import Path
    f = Path("/app/backend/data/users") / user_id / "archive" / "agenda_archief" / f"agenda-{month}.json"
    if not f.exists():
        return {"user_id": user_id, "month": month, "events": []}
    return load_json(f, default={"events": []})


@router.post("/archive-now")
async def archive_now_all():
    """Trigger handmatig het maand-archief voor alle users (override state).
    Normaal draait dit automatisch bij server-startup op de 1e van de maand."""
    return _archive.archive_now()


@router.post("/archive-now/{user_id}")
async def archive_now_user(user_id: str):
    """Trigger handmatig het maand-archief voor 1 user."""
    return _archive.archive_now(user_id)


# v13d_uren_rapport_001 (sessie 56b) — Willem: "uren-registratie formulier per
# dag/week/maand/jaar als bron waar wat we gemaakt hebben heen kan schrijven".
# Aggregeert alle zakelijke agenda-events per opdrachtgever per periode.
@router.get("/uren-rapport/{user_id}")
async def uren_rapport(
    user_id: str,
    period: str = Query("maand", pattern="^(dag|week|maand|jaar)$"),
    year: Optional[int] = None,
    month: Optional[int] = None,
    day: Optional[int] = None,
    viewer_id: Optional[str] = None,
):
    """Uren-rapport voor een user over een periode.
    - period=dag: geef year+month+day, of neem vandaag
    - period=week: geef year+month+day binnen die week, of neem huidige week
    - period=maand: geef year+month, of neem huidige maand
    - period=jaar: geef year, of neem huidige jaar
    """
    require_access(viewer_id or user_id, user_id)
    from datetime import datetime as _dt, timedelta as _td, timezone as _tz

    fpath = DATA_DIR / f"{user_id}.json"
    data = load_json(fpath, default={"events": []})
    events = data.get("events", []) or []

    # Bepaal periode-range
    today = _dt.now(_tz.utc).date()
    if period == "dag":
        target = _dt(year or today.year, month or today.month, day or today.day).date()
        start = end = target
        label = target.strftime("%A %d %b %Y")
    elif period == "week":
        anchor = _dt(year or today.year, month or today.month, day or today.day).date()
        start = anchor - _td(days=anchor.weekday())  # ma
        end = start + _td(days=6)  # zo
        label = f"Week {start.isocalendar()[1]} · {start.strftime('%d %b')} - {end.strftime('%d %b %Y')}"
    elif period == "jaar":
        j = year or today.year
        start = _dt(j, 1, 1).date(); end = _dt(j, 12, 31).date()
        label = f"Jaar {j}"
    else:  # maand
        j = year or today.year; m = month or today.month
        start = _dt(j, m, 1).date()
        if m == 12:
            end = _dt(j, 12, 31).date()
        else:
            end = (_dt(j, m + 1, 1) - _td(days=1)).date()
        maand_namen = ["januari", "februari", "maart", "april", "mei", "juni",
                       "juli", "augustus", "september", "oktober", "november", "december"]
        label = f"{maand_namen[m - 1].capitalize()} {j}"

    # Filter + aggregeer
    in_period = []
    for ev in events:
        if ev.get("scope") != "zakelijk":
            continue
        d = ev.get("date", "")
        if not d:
            continue
        try:
            ev_date = _dt.fromisoformat(d.replace("Z", "+00:00")).date()
        except Exception:
            continue
        if start <= ev_date <= end:
            in_period.append({
                "id": ev.get("id"),
                "titel": ev.get("titel"),
                "date": ev.get("date"),
                "end_date": ev.get("end_date"),
                "opdrachtgever": (ev.get("opdrachtgever") or "onbekend").strip(),
                "onderwerp": ev.get("onderwerp"),
                "pauze_minuten": ev.get("pauze_minuten") or 0,
                "totaal_uren": ev.get("totaal_uren") or 0,
            })

    in_period.sort(key=lambda x: x["date"])

    # Per opdrachtgever
    per_opdr = {}
    for ev in in_period:
        opd = ev["opdrachtgever"]
        per_opdr.setdefault(opd, {"opdrachtgever": opd, "uren": 0.0, "events": 0})
        per_opdr[opd]["uren"] += ev["totaal_uren"] or 0
        per_opdr[opd]["events"] += 1

    per_opdr_list = sorted(per_opdr.values(), key=lambda x: -x["uren"])
    for row in per_opdr_list:
        row["uren"] = round(row["uren"], 2)

    totaal_uren = round(sum(ev["totaal_uren"] or 0 for ev in in_period), 2)

    return {
        "period": period,
        "label": label,
        "start": str(start),
        "end": str(end),
        "totaal_uren": totaal_uren,
        "event_count": len(in_period),
        "per_opdrachtgever": per_opdr_list,
        "events": in_period,
    }

