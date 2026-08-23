"""
Smart Intents Service (v4_intents_001)
--------------------------------------
Een handvol high-value chat intents die Spark slimmer maken:

  • agenda_today   "wat staat in agenda vandaag?"
  • make_note      "maak notitie: <inhoud>"
  • help_overview  "wat kan je allemaal?"
  • suggest_action "wat zullen we doen?"
  • clarify_intent "nee dat bedoel ik niet" (loopt door als correction)

Elke detector retourneert (matched: bool, response_dict | None).
Hooked vanuit chat/routes.py voordat de fallback-flow start.
"""
import re
import json
import uuid
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

from modules.core.storage import load_json, save_json
from . import user_time_service
from . import intent_pattern_store as _patterns  # v13d_intent_patterns_json_001

DATA_ROOT = Path(__file__).parent.parent.parent / "data"
AGENDA_DIR = DATA_ROOT / "agenda"
NOTES_FILE = DATA_ROOT / "notes" / "notes.json"
TRIGGERS_FILE = DATA_ROOT / "triggers" / "conversation_triggers.json"
ROADMAP_FILE = DATA_ROOT / "system" / "roadmap.json"


# ============== AGENDA INTENT ==============
# v13d_intent_patterns_json_001 — patronen leven nu in intent_pattern_store
# (BASELINE + /data/triggers/intent_patterns.json). Nieuwe patronen kunnen
# live via Triggers-UI worden toegevoegd zonder redeploy.

# v13c_agenda_weekdays_001 — day-focus regex nu ook weekdagen + prefix
_AGENDA_DAY_RX = re.compile(
    r"\b(?:aanstaande\s+|volgende\s+|komende\s+)?(vandaag|morgen|overmorgen|deze week|"
    r"maandag|dinsdag|woensdag|donderdag|vrijdag|zaterdag|zondag)\b",
    re.IGNORECASE,
)
_WEEKDAY_INDEX = {"maandag": 0, "dinsdag": 1, "woensdag": 2, "donderdag": 3,
                  "vrijdag": 4, "zaterdag": 5, "zondag": 6}


def detect_agenda_intent(text: str) -> bool:
    return _patterns.match_any("agenda_read", text or "")


def detect_agenda_delete_intent(text: str) -> bool:
    """v13d_agenda_delete_001 — Willem: 'haal aanstaande dinsdag uit de agenda'
    moet DELETE-flow triggeren (met bevestiging), niet 'doe dat via de UI'."""
    return _patterns.match_any("agenda_delete", text or "")


def _parse_event_dt(ev: dict) -> Optional[datetime]:
    raw = ev.get("date") or ev.get("datetime") or ev.get("start")
    if not raw or not isinstance(raw, str):
        return None
    try:
        s = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
        dt = datetime.fromisoformat(s)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def handle_agenda(user_id: str, user: Optional[dict], text: str) -> Dict:
    fpath = AGENDA_DIR / f"{user_id}.json"
    data = load_json(fpath, default={"events": []})
    events = data.get("events", []) or []

    now_utc = datetime.now(timezone.utc)
    tz = user_time_service.resolve_user_timezone(user)
    try:
        from zoneinfo import ZoneInfo
        local_now = now_utc.astimezone(ZoneInfo(tz))
    except Exception:
        local_now = now_utc

    today = local_now.date()
    horizon_end = local_now + timedelta(days=7)

    # v6_agenda_dayfocus_001 — Detecteer dag-focus (morgen/overmorgen) uit user-tekst
    # v13c_agenda_weekdays_001 — nu ook weekdagen (dinsdag, aanstaande dinsdag, …)
    day_focus = None  # None = standaard (vandaag + komende week)
    day_match = _AGENDA_DAY_RX.search(text or "")
    if day_match:
        word = day_match.group(1).lower()
        if word == "morgen":
            day_focus = today + timedelta(days=1)
        elif word == "overmorgen":
            day_focus = today + timedelta(days=2)
        elif word == "vandaag":
            day_focus = today
        elif word in _WEEKDAY_INDEX:
            # Volgende voorkomen van deze weekdag (of vandaag als het al is)
            target_dow = _WEEKDAY_INDEX[word]
            today_dow = today.weekday()
            delta = (target_dow - today_dow) % 7
            if delta == 0:
                delta = 7  # "aanstaande dinsdag" op een dinsdag = volgende week
            day_focus = today + timedelta(days=delta)
        # "deze week" laat focus op None (alles toont)

    # Sorteer + filter toekomstige
    upcoming = []
    for ev in events:
        if ev.get("status") in ("done", "completed", "cancelled"):
            continue
        dt = _parse_event_dt(ev)
        if not dt or dt < now_utc - timedelta(hours=1):
            continue
        try:
            local_dt = dt.astimezone(ZoneInfo(tz))
        except Exception:
            local_dt = dt
        upcoming.append((local_dt, ev))
    upcoming.sort(key=lambda x: x[0])

    today_evs = [(d, e) for d, e in upcoming if d.date() == today]
    later_evs = [(d, e) for d, e in upcoming if d.date() > today and d <= horizon_end]

    # v6_agenda_dayfocus_001 — Antwoord toespitsen als user expliciet een dag noemde
    if day_focus is not None:
        focused = [(d, e) for d, e in upcoming if d.date() == day_focus]
        day_label = "vandaag" if day_focus == today else (
            "morgen" if day_focus == today + timedelta(days=1) else (
            "overmorgen" if day_focus == today + timedelta(days=2) else day_focus.strftime('%A %d %b')))
        if not focused:
            msg = f"📅 Geen afspraken {day_label}."
            # Toon eerstvolgende daarna als hint
            future = [(d, e) for d, e in upcoming if d.date() > day_focus]
            if future:
                nxt = future[0]
                nxt_label = "morgen" if nxt[0].date() == today + timedelta(days=1) else (
                    "overmorgen" if nxt[0].date() == today + timedelta(days=2) else nxt[0].strftime('%A %d %b'))
                msg += f" Wel daarna: **{nxt[1].get('titel') or nxt[1].get('title') or 'afspraak'}** ({nxt_label} om {nxt[0].strftime('%H:%M')})."
        else:
            first = focused[0]
            rest = focused[1:]
            msg = f"📅 {day_label.capitalize()}: **{first[1].get('titel') or first[1].get('title') or 'afspraak'}** om {first[0].strftime('%H:%M')}."
            if rest:
                extra = ", ".join(f"{r[1].get('titel') or 'afspraak'} ({r[0].strftime('%H:%M')})" for r in rest[:3])
                msg += f" Verder: {extra}."
        return {
            "type": "agenda_overview",
            "message": msg,
            "day_focus": str(day_focus),
            "focused_count": len(focused),
            "events_preview": [{"titel": e.get("titel") or e.get("title"), "tijd": d.strftime("%a %d %b %H:%M")} for d, e in focused[:5]],
        }

    if not upcoming:
        msg = "Je agenda is helemaal leeg voor de komende week. Vrij speelveld dus 🙂"
    elif today_evs:
        first = today_evs[0]
        rest = today_evs[1:]
        msg = f"Vandaag staat **{first[1].get('titel') or first[1].get('title') or 'een afspraak'}** om {first[0].strftime('%H:%M')} op de planning."
        if rest:
            extra = ", ".join(f"{r[1].get('titel') or 'afspraak'} ({r[0].strftime('%H:%M')})" for r in rest[:3])
            msg += f" Daarna nog: {extra}."
        if later_evs:
            nxt = later_evs[0]
            day_label = "morgen" if nxt[0].date() == today + timedelta(days=1) else nxt[0].strftime('%A %d %b')
            msg += f" {day_label.capitalize()} heb je **{nxt[1].get('titel') or 'een afspraak'}** om {nxt[0].strftime('%H:%M')}."
    else:
        # Vandaag niks, eerstvolgende noemen
        nxt = later_evs[0] if later_evs else upcoming[0]
        day_label = "morgen" if nxt[0].date() == today + timedelta(days=1) else (
            "overmorgen" if nxt[0].date() == today + timedelta(days=2) else nxt[0].strftime('%A %d %b')
        )
        msg = (
            f"Vandaag staat er **niks** in je agenda. "
            f"{day_label.capitalize()} heb je je eerste afspraak: **{nxt[1].get('titel') or 'afspraak'}** om {nxt[0].strftime('%H:%M')}."
        )

    return {
        "type": "agenda_overview",
        "message": msg,
        "today_count": len(today_evs),
        "upcoming_count": len(later_evs),
        "events_preview": [{"titel": e.get("titel") or e.get("title"), "tijd": d.strftime("%a %d %b %H:%M")} for d, e in upcoming[:5]],
    }


# ============== NOTE INTENT ==============
# v13d_intent_patterns_json_001 — patronen zitten nu in intent_pattern_store
# (BASELINE + JSON). Deze lokale lijsten zijn nog nodig omdat we `.match()`
# doen om de content-group te extracten. Ze worden bij runtime samengevoegd
# met de JSON-additions.


def _note_pattern_strs():
    return _patterns.get_raw_patterns("note_create")


def _bug_pattern_strs():
    return _patterns.get_raw_patterns("bug_report")


def detect_note_intent(text: str):
    """Return (matched: bool, content: str|None)"""
    if not text:
        return False, None
    t = text.strip()
    for pat in _note_pattern_strs():
        try:
            m = re.match(pat, t, re.IGNORECASE)
        except re.error:
            continue
        if m and m.lastindex:
            content = m.group(m.lastindex).strip()
            if content:
                return True, content
    return False, None


def handle_note(user: Optional[dict], user_id: Optional[str], content: str) -> Dict:
    NOTES_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = load_json(NOTES_FILE, default={"notes": [], "metadata": {}})
    note = {
        "id": str(uuid.uuid4()),
        "title": content[:60],
        "content": content,
        "tags": ["chat-aangemaakt"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "user_id": user_id,
        "user_naam": (user or {}).get("naam") if user else None,
    }
    data.setdefault("notes", []).append(note)
    data.setdefault("metadata", {})["total_notes"] = len(data["notes"])
    save_json(NOTES_FILE, data)
    return {
        "type": "note_created",
        "message": f"📝 Notitie opgeslagen: **{content[:80]}**. Je kan 'm zien in 'Notities & Taken'.",
        "note_id": note["id"],
    }

# ---------------------------------------------------------------------------
# v13_user_lookup_intent_001 (sessie 54) — Willem's GPT-conversatie showed
# Spark said "Nee ik zie geen gebruiker Anne" en zoekt "Maaike" in KB i.p.v.
# in users.json. Nu: admin (én normale users) kunnen naar bestaande users
# vragen — Spark leest /data/system/users.json en antwoordt op naam/user_id.
# ---------------------------------------------------------------------------
USER_LOOKUP_PATTERNS = [
    # "zie je gebruiker anne", "ken je user maaike", "heb jij een gebruiker anne"
    re.compile(r"\b(zie|ken|heb|hebben|kent|heeft)\s+(je|jij|spark)\s+(?:al\s+)?(?:een\s+|de\s+)?(user|gebruiker|account)\s+([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9_\-]{1,30})\b", re.IGNORECASE),
    # "welke users zijn er", "toon me alle gebruikers"
    re.compile(r"\b(welke|hoeveel|toon|noem|lijst|list)\s+(users?|gebruikers?|accounts?)\b", re.IGNORECASE),
    # "user X bestaat?"
    re.compile(r"\b(user|gebruiker)\s+([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ0-9_\-]{1,30})\s+bestaat", re.IGNORECASE),
]


def detect_user_lookup_intent(text: str):
    """Return dict {mode: 'single'|'list', name: str|None} of None."""
    if not text:
        return None
    for pat in USER_LOOKUP_PATTERNS:
        m = pat.search(text)
        if not m:
            continue
        # Groep 4 (single) of geen (list)
        groups = m.groups()
        if len(groups) >= 4 and groups[3]:
            return {"mode": "single", "name": groups[3].strip()}
        if len(groups) >= 2 and groups[1] and groups[1].lower().startswith(("user", "gebruiker", "account")):
            return {"mode": "list", "name": None}
        return {"mode": "list", "name": None}
    return None


def handle_user_lookup(intent: dict, requester_is_admin: bool = False) -> Dict:
    """Zoek in users.json en bouw antwoord. Voor niet-admins alleen naam+gradatie tonen,
    voor admins ook user_id + admin-vlaggen."""
    users_file = DATA_ROOT / "system" / "users.json"
    users_data = load_json(users_file, default={"users": []})
    users = users_data.get("users", []) if isinstance(users_data, dict) else users_data
    if not isinstance(users, list):
        users = []

    if intent["mode"] == "list":
        # Toon alle users compact
        if not users:
            return {"type": "user_lookup", "message": "Er zijn nog geen users in het systeem."}
        lines = [f"Er zijn **{len(users)} users** in het systeem:"]
        for u in users:
            nm = u.get("naam") or u.get("username") or "?"
            gr = u.get("gradatie") or "?"
            uid = u.get("id") or "?"
            adm = " (admin)" if u.get("admin") or u.get("admin_capable") else ""
            if requester_is_admin:
                lines.append(f"- **{nm}** ({gr}){adm} — `{uid}`")
            else:
                lines.append(f"- **{nm}** ({gr}){adm}")
        return {"type": "user_lookup", "message": "\n".join(lines)}

    # Single-mode: zoek op naam (case-insensitive, ook via username/email)
    needle = intent["name"].lower()
    match = None
    for u in users:
        candidates = [
            str(u.get("naam", "")).lower(),
            str(u.get("username", "")).lower(),
            str(u.get("email", "")).lower().split("@")[0],
        ]
        if any(needle == c or (len(needle) >= 3 and needle in c) for c in candidates if c):
            match = u
            break

    if not match:
        # Niet gevonden — meld hoeveel wél bestaan
        return {
            "type": "user_lookup",
            "message": f"Nee, ik zie geen user met de naam '**{intent['name']}**' in het systeem. "
                       f"Er staan {len(users)} users geregistreerd. Wil je de volledige lijst zien?",
        }

    nm = match.get("naam") or match.get("username") or "?"
    gr = match.get("gradatie") or "?"
    uid = match.get("id") or "?"
    adm = " (admin)" if match.get("admin") or match.get("admin_capable") else ""
    created = (match.get("created_at") or match.get("aangemaakt_op") or "")[:10]

    lines = [f"Ja, **{nm}** bestaat als user."]
    lines.append(f"- Gradatie: {gr}{adm}")
    if created:
        lines.append(f"- Aangemaakt: {created}")
    if requester_is_admin:
        lines.append(f"- User-ID: `{uid}`")
    return {"type": "user_lookup", "message": "\n".join(lines)}





# v13_write_intent_patterns_001 — bug-detectie + write (analoog aan note-flow).
def detect_bug_intent(text: str):
    """Return (matched: bool, content: str|None)"""
    if not text:
        return False, None
    t = text.strip()
    for pat in _bug_pattern_strs():
        try:
            m = re.match(pat, t, re.IGNORECASE)
        except re.error:
            continue
        if m and m.lastindex:
            content = m.group(m.lastindex).strip()
            if content and len(content) >= 5:
                return True, content
    return False, None


def handle_bug(user: Optional[dict], user_id: Optional[str], content: str) -> Dict:
    """Schrijf bug naar /data/bugs/bugs.json — zelfde bestand als bugs-module."""
    bugs_fp = NOTES_FILE.parent.parent / "bugs" / "bugs.json"
    bugs_fp.parent.mkdir(parents=True, exist_ok=True)
    data = load_json(bugs_fp, default={"bugs": []})
    bug = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "titel": content[:80],
        "beschrijving": content,
        "status": "open",
        "severity": "medium",
        "created": datetime.now(timezone.utc).isoformat(),
        "created_by": (user or {}).get("naam") if user else user_id,
        "source": "chat-intent",
    }
    data.setdefault("bugs", []).insert(0, bug)
    save_json(bugs_fp, data)
    return {
        "type": "bug_created",
        "message": (
            f"🐛 Bug-melding opgeslagen: **{bug['titel']}**. "
            f"Admin ziet 'm in de Bugs-tab (status: open)."
        ),
        "bug_id": bug["id"],
    }


# ============== HELP / WAT KAN JE ==============
# v13d_intent_patterns_json_001 — patronen in intent_pattern_store


def detect_help_intent(text: str) -> bool:
    return _patterns.match_any("help_overview", (text or "").strip())


def handle_help(is_admin: bool = False) -> Dict:
    # Lees triggers + voeg vaste commands toe
    triggers = load_json(TRIGGERS_FILE, default={})
    trigger_keys = list(triggers.keys()) if isinstance(triggers, dict) else []

    # Basis commands voor iedereen
    user_commands = [
        ("Vraag iets over een onderwerp", "bv. 'wat is fotosynthese?'"),
        ("Leer me een nieuw woord", "bv. 'voetenbank'"),
        ("Plan een afspraak", "bv. 'maak afspraak vrijdag 14:00 lunch met Tineke'"),
        ("Wat staat er in mijn agenda?", "bv. 'wat staat vandaag op de planning'"),
        ("Maak een notitie", "bv. 'notitie: bel monteur over verwarming'"),
        ("Wat zullen we doen?", "bv. 'wat zullen we doen?' — ik kijk in agenda + roadmap"),
        ("Recap van eerder gesprek", "bv. 'wat hebben we gisteren middag besproken?'"),
        ("Mijn tijd / dagdeel", "bv. 'hoe laat is het?' of 'welk tijdstip is het?'"),
        ("Wie ben ik / wat is Spark", "bv. 'wie ben jij?', 'jouw missie', 'wat kan je?'"),
        ("Speech-to-Text (jij spreekt)", "bv. '(stt aan)' / '(stt uit)' of 'spraak naar text aan/uit'"),
        ("Text-to-Speech (Spark spreekt)", "bv. '(tts aan)' / '(tts uit)' of 'text naar spraak aan/uit'"),
        ("Achtergrondgeluid", "bv. 'ambient 1 aan', 'ambient 2 aan', 'ambient 3 aan', 'stilte' — blijft door na F5"),
        ("Stop een lopend proces", "bv. 'stop' of 'klaar' — beëindigt actieve sessie (W-woord card, kennis-leer, etc.)"),
        ("Spark's eigen anker", "bv. 'onthoud voor jezelf: ...' (parkeert in Spark's user-000 scratch) of 'wat heb je vandaag geleerd?'"),
        ("Relaties noteren", "bv. 'mijn moeder Anneke is jarig', 'Ron is mijn vriend'"),
        ("Testament aanmaken", "bv. 'maak testament aan' → 'voeg toe aan testament: <tekst>' → 'bekijk testament'"),
        ("Survivalgids aanmaken", "bv. 'maak survivalgids aan' → 'voeg toe aan survivalgids: <tekst>'"),
        ("Documenten bekijken", "via Mijn Archief → tab Documenten (JSON download mogelijk)"),
        ("Account verwijderen", "bv. 'verwijder mijn account' — 2× bevestiging, backup 30 dagen"),
        ("Privacy / Cookies / Voorwaarden", "bv. 'wat is de privacy beschrijving?' / 'cookies' / 'voorwaarden'"),
        ("Credits", "bv. 'credits' — wie heeft Spark mogelijk gemaakt"),
        # v5_help_refresh_001 — nieuwe v5 features
        ("Kennisbank v2 — audit", "bv. 'audit kennis' / 'wat mist' — samenvatting van lege/lage-vertrouwen kaarten"),
        ("Kennisbank v2 — inbox", "bv. 'hoeveel onbeantwoord' / 'wat staat in inbox' — telling per reden"),
        ("Kennisbank v2 — leren", "bv. 'leer woord: pareltje' / 'voeg toe aan kennis: hartslag' — direct in inbox"),
        ("D&D-kaart maken", "bv. 'maak een d&d kaart Het Eerste Licht' — draft kaart die je in UI invult"),
        ("Event-kaart maken", "bv. 'maak een event kaart Roadkill Borrel' — Boekhouder kondigt 'm aan in community"),
        ("Bark-template maken", "bv. 'maak een bark kaart morgenavond' — template voor bot-trigger later"),
        ("ROAR Gift", "via Winkel → ROAR Token tab → 🎁 ROAR Gift sturen (24h escrow met accept/weiger)"),
        ("Spark World D&D", "bv. '[start verhaal]' in community, 'd&d help', 'rugzak uitleg', 'persoonskaart help'"),
        ("Recap community", "bv. 'wat is gisteren in de community besproken?'"),
        ("Trader / Wallet", "via Trader & Wallet tabs (ROAR-tokens = potjes-slots, monitor cycle aanpasbaar)"),
    ]

    # Admin-extra (gradatie ≤ 2)
    admin_commands = [
        ("Beheer credits-lijst via chat", "bv. 'voeg Nick Teeuwen toe aan de credits', 'verander Nick naar Nick Teeuwen in credits', 'verwijder X uit credits'"),
        ("Beheer credits-lijst via UI", "Spark AI → Triggers → zoek op 'Credits' (Voornamen + Extra dank)"),
        ("Credits-bonus matching", "Namen met voor+achternaam matchen autom. met users (grad ≤4) — +10 trust + ×1.2 multiplier"),
        ("Wat zullen we doen? (admin)", "bv. 'wat zou jij willen doen?' — bekijkt roadmap-bugs + open items"),
        ("Bugs beheren", "via Beheer → Bug-melder; chat-meldingen lopen via Spark"),
        ("Trigger/Vocab beheer", "via Spark AI → Triggers; alles editable"),
        ("Avatar Galerij beheer", "via Beheer → Instellingen → Beeld → Avatar Galerij"),
        ("Backup/Restore", "via Beheer → Back-up (ZIP export/import, incl. cache flush)"),
        ("Gradatie-upgrades", "automatisch (7→6 profiel, 6→5 gedrag) of admin handmatig (4→3)"),
        ("Storage cache stats", "via Beheer dashboard 'Performance' kaart"),
        # v5_help_refresh_001 — admin v5 features
        ("Logs browser", "via Beheer → Instellingen → Archief → Logs (per dag, per module, filter op pre/post/error/event)"),
        ("Deploy-anker + Update Bark", "via Notities → Deploy (versie + bericht; iedereen ziet bark bij volgende login)"),
        ("Trader hot coin-swap / cycle", "TraderPage: coin-picker en cycle (15m/1h/4h/1d) live aanpasbaar zonder bot-stop"),
        ("Force-sell potje (admin)", "Admin Analytics → Trade → bot-kaart uitklappen → force-sell + reden (audit-trail)"),
        ("Bot-kleurschema's", "via Beheer → Instellingen → Beeld → BOT-ACCENT KLEUREN (5 bots, hex-pickers)"),
        ("App-kleurenschema", "via Beheer → Instellingen → Beeld → App Kleurenschema (6 presets + 3 custom-pickers)"),
        ("Boekhouding entiteiten", "via Beheer → Boekhouding: 4 entiteiten (Spark Core / Spark Your Life / Roadkill Merch / Privé)"),
        ("Graph rebuild", "POST /api/graph/rebuild — herbouwt nodes+edges incl. KB v2 (zie Verbanden tab)"),
    ]

    if is_admin:
        lines = ["**Help voor jou (admin)**", "", "_Iedereen kan dit:_"]
        for label, hint in user_commands:
            lines.append(f"  • **{label}** — _{hint}_")
        lines.append("")
        lines.append("_Admin-extra:_")
        for label, hint in admin_commands:
            lines.append(f"  • **{label}** — _{hint}_")
    else:
        lines = ["Hier is wat ik kan:"]
        for label, hint in user_commands:
            lines.append(f"  • **{label}** — _{hint}_")

    if trigger_keys:
        sample = ", ".join(trigger_keys[:8])
        lines.append("")
        lines.append(f"_Daarnaast reageer ik op {len(trigger_keys)} trigger-types: {sample}{'...' if len(trigger_keys) > 8 else ''}._")
    lines.append("")
    lines.append("Vraag gerust dieper door bij wat dan ook — ik leer van elk gesprek.")
    return {"type": "help_overview", "message": "\n".join(lines)}


# ============== WAT ZULLEN WE DOEN ==============

def detect_suggest_intent(text: str) -> bool:
    return _patterns.match_any("suggest_action", (text or "").strip())


def handle_suggest(user_id: str, user: Optional[dict]) -> Dict:
    # 1) Agenda voor vandaag
    fpath = AGENDA_DIR / f"{user_id}.json"
    agenda = load_json(fpath, default={"events": []}).get("events", [])
    tz = user_time_service.resolve_user_timezone(user)
    now_utc = datetime.now(timezone.utc)
    try:
        from zoneinfo import ZoneInfo
        local_now = now_utc.astimezone(ZoneInfo(tz))
    except Exception:
        local_now = now_utc
    today = local_now.date()

    today_evs = []
    for ev in agenda:
        if ev.get("status") in ("done", "completed", "cancelled"):
            continue
        dt = _parse_event_dt(ev)
        if dt and dt >= now_utc:
            try:
                ld = dt.astimezone(ZoneInfo(tz))
            except Exception:
                ld = dt
            if ld.date() == today:
                today_evs.append((ld, ev))
    today_evs.sort(key=lambda x: x[0])

    # 2) Roadmap urgent items
    roadmap = load_json(ROADMAP_FILE, default={})
    v4 = roadmap.get("v4.0", {}) if isinstance(roadmap, dict) else {}
    items = v4.get("items", []) if isinstance(v4, dict) else []
    todo = [
        it for it in items
        if isinstance(it, dict)
        and (it.get("status") or "").lower() in ("todo", "planned", "in_progress", "")
        and it.get("priority") in (None, "high", "medium")
    ]
    # Sorteer high → medium → low
    prio_rank = {"high": 0, "medium": 1, "low": 2}
    todo.sort(key=lambda x: prio_rank.get(x.get("priority"), 3))

    lines = []
    if today_evs:
        first = today_evs[0]
        lines.append(f"📅 Vandaag staat **{first[1].get('titel') or 'afspraak'}** om {first[0].strftime('%H:%M')} op de planning.")
        if len(today_evs) > 1:
            lines.append(f"   (en nog {len(today_evs)-1} afspra{'ken' if len(today_evs)>2 else 'ak'})")
    else:
        lines.append("📅 Vandaag heb je geen afspraken in de agenda.")

    if todo:
        lines.append("")
        lines.append("🎯 Op de roadmap staan deze open items (prioriteit eerst):")
        for it in todo[:3]:
            t = it.get("titel") or it.get("naam") or it.get("title") or "—"
            prio = it.get("priority") or "?"
            lines.append(f"   • **{t}** _({prio})_")
        if len(todo) > 3:
            lines.append(f"   _...en {len(todo)-3} meer in de roadmap-tab._")
    else:
        lines.append("")
        lines.append("🎯 Roadmap is helemaal afgewerkt — vrij om iets nieuws te kiezen!")

    lines.append("")
    lines.append("Welke voelt het meest urgent voor jou nu?")
    return {"type": "suggest_action", "message": "\n".join(lines), "todo_count": len(todo), "today_events": len(today_evs)}


# ============== CLARIFY INTENT (loopt door als correction) ==============

def detect_clarify_intent(text: str) -> bool:
    return _patterns.match_any("clarify", (text or "").strip())


def handle_clarify(last_begrip: Optional[str]) -> Dict:
    if last_begrip:
        msg = (
            f"Oké — bedoelde je iets anders met **{last_begrip}**, of bedoelde je een heel ander woord? "
            f"Geef het andere woord dan typ ik 'm in dezelfde context."
        )
    else:
        msg = "Sorry, wat bedoelde je dan? Type het andere woord of de juiste zin — ik leer ervan."
    return {
        "type": "clarify_question",
        "message": msg,
        "expects": "alternative_word_or_phrase",
    }



# ============== TOPIC OVERVIEW INTENT (v4_topic_001) ==============
# v13d_intent_patterns_json_001 — patronen in intent_pattern_store
KB_FILE = DATA_ROOT / "knowledge" / "learned_knowledge" / "knowledge_base.json"  # V1 legacy
KBV2_DIR = DATA_ROOT / "knowledge" / "v2"


def _load_kbv2_entries() -> list:
    """v6_v2_first_001 — alle V2 kaarten (4 lades + inbox) als platte lijst."""
    out = []
    for fname in ["knowledge_v2_doen", "knowledge_v2_weten",
                  "knowledge_v2_voelen", "knowledge_v2_spreken",
                  "knowledge_inbox"]:
        d = load_json(KBV2_DIR / f"{fname}.json", default={"kaarten": []})
        out.extend(d.get("kaarten", []) or [])
    return out


def detect_topic_intent(text: str):
    """Return (matched, topic_query) tuple."""
    if not text:
        return False, None
    t = text.strip()
    for pat in _patterns.get_raw_patterns("topic_overview"):
        try:
            m = re.search(pat, t, re.IGNORECASE)
        except re.error:
            continue
        if m and m.lastindex:
            topic = m.group(m.lastindex).strip().rstrip("?.! ")
            if topic and len(topic) >= 3:
                return True, topic
    return False, None


def handle_topic_overview(topic_query: str) -> Dict:
    """Zoek kaarten met topic of tag matching topic_query. Case-insensitive."""
    # v6_v2_first_001 — V2 is bron; V1 wordt overgeslagen (archief)
    entries = _load_kbv2_entries()
    q = topic_query.lower().strip()

    # Match op topic OR tag
    hits = []
    for e in entries:
        topic = (e.get("topic") or "").lower().strip()
        tags = [t.lower().strip() for t in (e.get("tags") or [])]
        if topic == q or q in tags:
            hits.append(e)

    if not hits:
        # Soft match: substring in topic
        for e in entries:
            topic = (e.get("topic") or "").lower().strip()
            if q in topic and len(topic) > 0:
                hits.append(e)

    if not hits:
        # v5_kbv2_001 — #DeWillem Graceful Fallback: probeer v2 buur-kaart
        try:
            from modules.kb_v2 import service as kbv2
            fb = kbv2.graceful_fallback(topic_query)
            if fb and fb.get("type") == "direct":
                kaart = fb["kaart"]
                laag1 = (kaart.get("lagen") or {}).get("laag1") or ""
                if laag1:
                    return {
                        "type": "kbv2_direct",
                        "message": f"**{kaart['begrip']}** _(lade: {fb['lade']})_: {laag1}",
                        "topic": topic_query,
                        "kbv2_card_id": kaart["id"],
                    }
            if fb and fb.get("type") == "neighbor":
                kaart = fb["kaart"]
                laag1 = (kaart.get("lagen") or {}).get("laag1") or ""
                return {
                    "type": "kbv2_neighbor",
                    "message": (
                        f"Ik ken **{topic_query}** nog niet specifiek, maar in mijn **{fb['lade']}**-lade "
                        f"vind ik wel iets over **{kaart['begrip']}**: {laag1}\n\n"
                        f"_Wil je dat ik **{topic_query}** apart leer?_"
                    ),
                    "topic": topic_query,
                    "kbv2_card_id": kaart["id"],
                }
        except Exception:
            pass

        return {
            "type": "topic_overview",
            "message": f"Ik heb nog niets in mijn kennisbank over **{topic_query}**. Wil je dat ik iets nieuws leer over dit onderwerp?",
            "topic": topic_query,
            "count": 0,
            "begrippen": [],
        }

    # Sorteer op kwaliteit: status active + ws5 gevuld eerst
    def _score(e):
        score = 0
        if e.get("status") == "active":
            score += 10
        if e.get("ws5") and any((e.get("ws5") or {}).values()):
            score += 5
        if e.get("lagen") and any((e.get("lagen") or {}).values()):
            score += 3
        return -score
    hits.sort(key=_score)

    # Geef top 5 begrippen
    sample = hits[:5]
    begrippen = [e.get("begrip") for e in sample if e.get("begrip")]
    begrip_str = ", ".join(f"**{b}**" for b in begrippen)

    msg = f"Ik heb **{len(hits)}** kaarten over **{topic_query}** in mijn kennisbank. "
    if begrippen:
        msg += f"Een paar: {begrip_str}. Welke wil je dat ik uitleg?"
    return {
        "type": "topic_overview",
        "message": msg,
        "topic": topic_query,
        "count": len(hits),
        "begrippen": begrippen,
        "preview_ids": [e.get("id") for e in sample],
    }


# ============== ACCOUNT DELETE (v4_self_delete_001) ==============
# v13d_intent_patterns_json_001 — patronen in intent_pattern_store
_YES_PATTERNS = [r"^\s*(ja|yes|jawel|zeker|inderdaad|akkoord|bevestig|ok|oké|prima|doe maar|graag)\b"]
_NO_PATTERNS = [r"^\s*(nee|nope|niet doen|stop|annuleer|annuleren|cancel|laat maar|nvm)\b"]


def detect_account_delete_intent(text: str) -> bool:
    return _patterns.match_any("account_delete", (text or "").strip())


def is_yes(text: str) -> bool:
    t = (text or "").lower().strip()
    return any(re.search(p, t) for p in _YES_PATTERNS)


def is_no(text: str) -> bool:
    t = (text or "").lower().strip()
    return any(re.search(p, t) for p in _NO_PATTERNS)


def handle_account_delete_start(user_naam: str = "") -> Dict:
    """Stap 1: vraag eerste bevestiging."""
    naam = user_naam or "jij"
    return {
        "type": "account_delete_confirm_1",
        "message": (
            f"Even checken, {naam}: wil jij echt je **account verwijderen**? Ik vraag het straks nóg een keer "
            f"om zeker te zijn. Een backup van je data blijft 30 dagen bewaard — daarna is het écht weg.\n\n"
            f"_Antwoord met **ja** om door te gaan, of **nee** om te annuleren._"
        ),
        "pending_state": {"flow": "account_delete", "step": 1},
    }


def handle_account_delete_confirm() -> Dict:
    """Stap 2: tweede bevestiging."""
    return {
        "type": "account_delete_confirm_2",
        "message": (
            "Laatste kans — **weet je het zeker**? Je wordt direct uitgelogd zodra ik op de knop druk.\n\n"
            "_Antwoord met **ja** om te verwijderen, of **nee** om te stoppen._"
        ),
        "pending_state": {"flow": "account_delete", "step": 2},
    }


def handle_account_delete_cancel() -> Dict:
    return {
        "type": "account_delete_cancelled",
        "message": "Goed, ik laat je account staan. Niks veranderd.",
    }


# ============== COMMUNITY RECAP INTENT (v4_community_recap_001) ==============
# v13d_intent_patterns_json_001 — patronen in intent_pattern_store


def detect_community_recap_intent(text: str) -> Optional[int]:
    """Returnt offset_days (0=vandaag, 1=gisteren, 2=eergisteren) of None."""
    t = (text or "").lower()
    if not _patterns.match_any("community_recap", t):
        return None
    if "eergisteren" in t:
        return 2
    if "gisteren" in t:
        return 1
    return 0


def handle_community_recap(offset_days: int = 1) -> Dict:
    """Roep community recap aan en formatteer voor chat-respons."""
    from datetime import timedelta
    target_dt = datetime.now(timezone.utc) - timedelta(days=offset_days)
    target = target_dt.strftime("%Y-%m-%d")

    community_file = DATA_ROOT / "community" / "messages.json"
    data = load_json(community_file, default={"messages": []})
    messages = data.get("messages", [])
    day_msgs = [m for m in messages if (m.get("timestamp") or "").startswith(target)]
    day_msgs.sort(key=lambda m: m.get("timestamp", ""))

    label = {0: "vandaag", 1: "gisteren", 2: "eergisteren"}.get(offset_days, target)

    if not day_msgs:
        return {
            "type": "community_recap",
            "message": f"In de community is **{label}** ({target}) niets besproken. Stilte!",
            "date": target,
            "total": 0,
        }

    user_counts: Dict[str, int] = {}
    bot_count = 0
    for m in day_msgs:
        if m.get("is_bot"):
            bot_count += 1
        else:
            name = m.get("user_name") or "Onbekend"
            user_counts[name] = user_counts.get(name, 0) + 1

    STOP = {"weer", "wordt", "worden", "kunnen", "moeten", "willen", "zullen",
            "echter", "daarom", "natuurlijk", "iemand", "iedereen", "alleen",
            "samen", "geweest", "geleden", "tijdens", "vooral"}
    word_counts: Dict[str, int] = {}
    for m in day_msgs:
        if m.get("is_bot"):
            continue
        for w in re.findall(r"\b[a-zà-ÿ]{5,}\b", (m.get("message") or "").lower()):
            if w in STOP:
                continue
            word_counts[w] = word_counts.get(w, 0) + 1
    top_topics = sorted(word_counts.items(), key=lambda x: -x[1])[:5]

    lines = [f"📋 **Community-recap {label}** ({target})"]
    lines.append(f"• {len(day_msgs)} berichten totaal ({sum(user_counts.values())} van mensen, {bot_count} van bots)")
    if user_counts:
        top = sorted(user_counts.items(), key=lambda x: -x[1])[:3]
        lines.append("• Actief: " + ", ".join(f"{n} ({c})" for n, c in top))
    if top_topics:
        lines.append("• Onderwerpen: " + ", ".join(w for w, _ in top_topics))
    # Voorbeeld-snippet (eerste niet-bot bericht)
    first_user = next((m for m in day_msgs if not m.get("is_bot")), None)
    if first_user:
        snippet = (first_user.get("message") or "")[:120]
        lines.append(f"• Eerste bericht: _{first_user.get('user_name')}: \"{snippet}\"_")
    return {
        "type": "community_recap",
        "message": "\n".join(lines),
        "date": target,
        "total": len(day_msgs),
        "users": user_counts,
        "top_topics": [{"word": w, "count": c} for w, c in top_topics],
    }


# ============== D&D HELP INTENT (v4_dnd_help_001) ==============
# v13d_intent_patterns_json_001 — patronen in intent_pattern_store


def detect_dnd_help_intent(text: str) -> bool:
    return _patterns.match_any("dnd_help", text or "")


def handle_dnd_help() -> Dict:
    """v4_dnd_help_001 — Korte uitleg D&D laag in Spark World."""
    msg = (
        "🎲 **Spark World D&D — Korte uitleg**\n\n"
        "**Base Line** is de oorsprong van Spark World (X=0, Y=0, Z=0). "
        "Vanuit een puls in de leegte groeit alles. Fracties: Spark, Players, "
        "Licht, Schaduw — elk met 2 kinderen uit de 4 elementen.\n\n"
        "**Persoonskaart** (Profiel → Avatar-tab) toont je stats: rang, level, "
        "XP, gradatie. Daaronder zit je inventory met slots en gewichts-mechaniek.\n\n"
        "**Rugzak** (eerste body-slot) bepaalt hoeveel slots én kg je kunt dragen. "
        "Trade-off: basis-rugzak (+5 slots / +10kg) vs grote trekrugzak "
        "(+10 slots / +25kg, weegt zelf 2.5kg).\n\n"
        "**Avatars** in galerij hebben 2 tabs: Persoonlijk en D&D Archief "
        "(bot/Spark-claimed of unlock-required).\n\n"
        "**Barks** zijn sensory-overlays (geluid + beeld) die getriggerd worden "
        "door events. Bij elke deploy zie je 1x een update-bark.\n\n"
        "Vraag ook 'wat is Base Line', 'rugzak uitleg' of 'persoonskaart help' "
        "voor diepere lagen."
    )
    return {"type": "dnd_help", "message": msg}


# ============== AGENDA DELETE (v13d_agenda_delete_001) ==============
# Willem, sessie 55: "als ik in chat zeg 'haal aanstaande dinsdag uit de
# agenda' dan moet Spark dat doen, niet zeggen 'via de agenda-tab'." Flow:
#  1. Detect delete-intent + parse dag-focus.
#  2. Zoek matchende events; als 0 → melden. Als 1 → bevestiging vragen.
#     Als >1 → lijstje met numers, gebruiker mag "1" typen of "alle".
#  3. Bij bevestiging → verwijder event(s) uit /data/agenda/{uid}.json.
#
# Gebruikt bestaande handle_agenda-logica voor dag-focus (weekdag / morgen / …).


def _parse_delete_day_focus(text: str, user: Optional[dict]):
    """Return (day_focus_date, day_label) of (None, None)."""
    day_match = _AGENDA_DAY_RX.search(text or "")
    if not day_match:
        return None, None
    now_utc = datetime.now(timezone.utc)
    tz = user_time_service.resolve_user_timezone(user)
    try:
        from zoneinfo import ZoneInfo
        local_now = now_utc.astimezone(ZoneInfo(tz))
    except Exception:
        local_now = now_utc
    today = local_now.date()
    word = day_match.group(1).lower()
    if word == "vandaag":
        return today, "vandaag"
    if word == "morgen":
        return today + timedelta(days=1), "morgen"
    if word == "overmorgen":
        return today + timedelta(days=2), "overmorgen"
    if word in _WEEKDAY_INDEX:
        target_dow = _WEEKDAY_INDEX[word]
        today_dow = today.weekday()
        delta = (target_dow - today_dow) % 7
        if delta == 0:
            delta = 7
        return today + timedelta(days=delta), word
    return None, None


def _matching_events(user_id: str, day_focus, text: str) -> list:
    """Return list of (event_dict, local_dt) for events matching day/text."""
    fpath = AGENDA_DIR / f"{user_id}.json"
    data = load_json(fpath, default={"events": []})
    events = data.get("events", []) or []
    now_utc = datetime.now(timezone.utc)
    from zoneinfo import ZoneInfo
    matches = []
    text_lower = (text or "").lower()
    for ev in events:
        if ev.get("status") in ("done", "completed", "cancelled"):
            continue
        dt = _parse_event_dt(ev)
        if not dt:
            continue
        # Alleen toekomstige (of vandaag)
        if dt < now_utc - timedelta(hours=1):
            continue
        # Match op day_focus als gegeven
        if day_focus is not None:
            try:
                # gebruik user-tz om date te vergelijken
                local_dt = dt.astimezone(ZoneInfo("Europe/Amsterdam"))
            except Exception:
                local_dt = dt
            if local_dt.date() != day_focus:
                continue
            matches.append((ev, local_dt))
        else:
            # Geen day_focus: probeer op titel-substring te matchen (bv "haal Tineke afspraak weg")
            titel = (ev.get("titel") or ev.get("title") or "").lower()
            loc = (ev.get("location") or "").lower()
            # Neem alleen mee als text expliciet iets van titel/location noemt
            for token in re.findall(r"[a-zà-ÿ]{4,}", text_lower):
                if token in ("agenda", "afspraak", "afspraken", "event", "haal", "verwijder", "schrap",
                             "cancel", "delete", "annuleer", "weghalen", "leegmaken", "morgen",
                             "vandaag", "aanstaande", "volgende", "komende"):
                    continue
                if token and (token in titel or token in loc):
                    try:
                        local_dt = dt.astimezone(ZoneInfo("Europe/Amsterdam"))
                    except Exception:
                        local_dt = dt
                    matches.append((ev, local_dt))
                    break
    matches.sort(key=lambda x: x[1])
    return matches


def handle_agenda_delete_start(user_id: str, user: Optional[dict], text: str) -> Dict:
    """Stap 1: vind matchende events + vraag bevestiging."""
    day_focus, day_label = _parse_delete_day_focus(text, user)
    matches = _matching_events(user_id, day_focus, text)

    if not matches:
        if day_focus:
            return {
                "type": "agenda_delete_none",
                "message": f"📅 Ik zie geen afspraken op **{day_label}** om te verwijderen. "
                           "Wil je 'wat staat er op {day_label}?' vragen om te kijken wat er wel staat?",
            }
        return {
            "type": "agenda_delete_none",
            "message": "Ik weet niet precies welke afspraak je bedoelt. Noem een dag "
                       "(bv. 'haal dinsdag uit de agenda') of een titel-woord (bv. 'verwijder tandarts uit agenda').",
        }

    if len(matches) == 1:
        ev, local_dt = matches[0]
        titel = ev.get("titel") or ev.get("title") or "afspraak"
        when_str = local_dt.strftime("%A %d %b om %H:%M")
        pending = {
            "flow": "agenda_delete",
            "step": 1,
            "event_ids": [ev.get("id")],
            "summary": f"{titel} ({when_str})",
        }
        return {
            "type": "agenda_delete_confirm",
            "message": f"Wil je **{titel}** op {when_str} verwijderen? _Zeg **ja** om te bevestigen, **nee** om te annuleren._",
            "pending_state": pending,
        }

    # >1 matches → toon lijst
    lines = [f"Ik vond **{len(matches)}** afspraken die daarbij passen:"]
    for i, (ev, local_dt) in enumerate(matches[:8], start=1):
        titel = ev.get("titel") or ev.get("title") or "afspraak"
        when_str = local_dt.strftime("%A %d %b om %H:%M")
        lines.append(f"  {i}. **{titel}** — {when_str}")
    lines.append("")
    lines.append("_Typ het nummer (bv. **1**) om er één te verwijderen, of **alle** om alles te wissen._")
    pending = {
        "flow": "agenda_delete",
        "step": "choose",
        "event_ids": [ev.get("id") for ev, _ in matches[:8]],
        "summaries": [
            f"{(ev.get('titel') or ev.get('title') or 'afspraak')} ({local_dt.strftime('%A %d %b %H:%M')})"
            for ev, local_dt in matches[:8]
        ],
    }
    return {
        "type": "agenda_delete_choose",
        "message": "\n".join(lines),
        "pending_state": pending,
    }


def handle_agenda_delete_choose(pending: dict, text: str) -> Dict:
    """Verwerk keuze bij multi-match. Return dict met of nieuwe pending (voor confirm)
    of directe delete."""
    t = (text or "").strip().lower()
    ids = pending.get("event_ids") or []
    summaries = pending.get("summaries") or []
    if re.match(r"^\s*(alle|allemaal|alle afspraken|all)\b", t):
        new_pending = {
            "flow": "agenda_delete",
            "step": 1,
            "event_ids": list(ids),
            "summary": f"{len(ids)} afspraken",
        }
        return {
            "type": "agenda_delete_confirm",
            "message": f"Weet je zeker dat je **alle {len(ids)}** afspraken wilt verwijderen? _Zeg **ja** of **nee**._",
            "pending_state": new_pending,
        }
    m = re.match(r"^\s*(\d+)\s*$", t)
    if m:
        idx = int(m.group(1)) - 1
        if 0 <= idx < len(ids):
            new_pending = {
                "flow": "agenda_delete",
                "step": 1,
                "event_ids": [ids[idx]],
                "summary": summaries[idx] if idx < len(summaries) else "afspraak",
            }
            return {
                "type": "agenda_delete_confirm",
                "message": f"Wil je **{new_pending['summary']}** verwijderen? _Zeg **ja** of **nee**._",
                "pending_state": new_pending,
            }
    return {
        "type": "agenda_delete_repeat",
        "message": "Ik snap 'm niet — typ een nummer (bv. **1**), **alle**, of **nee** om te annuleren.",
        "pending_state": pending,
    }


def execute_agenda_delete(user_id: str, event_ids: list) -> Dict:
    """Verwijder events uit de user-agenda file. Return dict met resultaat."""
    fpath = AGENDA_DIR / f"{user_id}.json"
    data = load_json(fpath, default={"events": []})
    events = data.get("events", []) or []
    kept = [ev for ev in events if ev.get("id") not in event_ids]
    removed_count = len(events) - len(kept)
    if removed_count == 0:
        return {
            "type": "agenda_delete_failed",
            "message": "Hmm, die afspraken waren al weg. Niks veranderd.",
        }
    data["events"] = kept
    save_json(fpath, data)
    return {
        "type": "agenda_deleted",
        "message": f"Klaar — **{removed_count}** afspra{'ken' if removed_count > 1 else 'ak'} uit je agenda verwijderd.",
        "removed_count": removed_count,
    }


def handle_agenda_delete_cancel() -> Dict:
    return {
        "type": "agenda_delete_cancelled",
        "message": "Oké, ik laat de agenda staan zoals hij is.",
    }


# ============== SHOP DELETE (v13d_shop_owner_delete_001, sessie 55) ==============
# Willem's logica: "gebruiker die een winkel heeft is admin over zijn winkel"
# → owner mag eigen shops verwijderen via chat, ook zonder globaal admin-recht.
# Flow: detect → find shop by name → check ownership → confirm → delete.

SHOPS_FILE = DATA_ROOT.parent / "backend" / "data" / "shop" / "shops.json"
# Fallback: DATA_ROOT / "shop" / "shops.json"
_SHOPS_FP = Path("/app/backend/data/shop/shops.json")


def detect_shop_delete_intent(text: str) -> bool:
    """Match delete-intent voor winkels."""
    return _patterns.match_any("shop_delete", text or "")


def _extract_shop_name_from_text(text: str) -> Optional[str]:
    """Probeer shop-naam te vinden in de gebruikers-tekst.
    Zoekt naar tokens die er als shop-naam uitzien: CamelCase, ALL_CAPS_underscore,
    of tussen quotes."""
    t = text or ""
    # 1) Tussen quotes: "TEST_PatchShop"
    m = re.search(r'["\']([^"\']{3,40})["\']', t)
    if m:
        return m.group(1).strip()
    # 2) Ondersteun ALL_CAPS_MIXED tokens (met underscore) of CamelCaseTokens
    # Zoek tokens van 3+ chars die minimaal 1 hoofdletter hebben
    tokens = re.findall(r'\b([A-Z][A-Za-z0-9_-]{2,39})\b', t)
    # Skip generieke woorden
    skip = {"TEST", "SHOP", "WINKEL", "DE", "EEN", "MIJN", "DIT", "DEZE", "DIE"}
    for tok in tokens:
        if tok.upper() not in skip and len(tok) >= 3:
            return tok
    # 3) "shop met naam X"-patroon
    m = re.search(r"\b(?:shop|winkel)\s+(?:met naam |genaamd |heet )?(\S+)", t, re.IGNORECASE)
    if m:
        cand = m.group(1).strip().strip(".,!?;:")
        if cand.lower() not in ("de", "een", "mijn", "deze", "die", "wil", "wilt", "zou", "je"):
            return cand
    return None


def _find_shops_by_name(query: str) -> list:
    """Zoek shops op naam-substring (case-insensitive)."""
    if not _SHOPS_FP.exists() or not query:
        return []
    data = load_json(_SHOPS_FP, default={"shops": []})
    shops = data.get("shops", []) if isinstance(data, dict) else data
    q = query.lower().strip()
    matches = []
    for s in shops:
        naam = (s.get("naam") or s.get("name") or "").lower()
        sid = (s.get("id") or "").lower()
        if q in naam or q in sid or q == naam:
            matches.append(s)
    return matches


def _user_can_delete_shop(user_id: str, shop: dict) -> bool:
    """Owner mag eigen shop verwijderen. Admin mag alle shops verwijderen."""
    if not user_id:
        return False
    if shop.get("owner_user_id") == user_id:
        return True
    # Check admin-status via users.json
    users = load_json(DATA_ROOT / "system" / "users.json", default={"users": []}).get("users", [])
    me = next((u for u in users if u.get("id") == user_id), None) or {}
    return bool(me.get("admin") or me.get("admin_capable"))


def handle_shop_delete_start(user_id: str, text: str) -> Dict:
    """Detecteer shop-naam, check ownership, vraag bevestiging."""
    shop_name = _extract_shop_name_from_text(text)
    if not shop_name:
        return {
            "type": "shop_delete_none",
            "message": (
                "Ik snap dat je een winkel wilt verwijderen, maar ik heb de naam nodig. "
                "Zeg bv. **'verwijder winkel TEST_PatchShop'** of gebruik quotes rond de naam."
            ),
        }
    matches = _find_shops_by_name(shop_name)
    if not matches:
        return {
            "type": "shop_delete_none",
            "message": f"Ik kan geen winkel vinden met '{shop_name}' in de naam. Check even de spelling?",
        }
    # System-default shop niet toestaan
    matches = [s for s in matches if s.get("id") != "shop-roadkill"]
    if not matches:
        return {
            "type": "shop_delete_none",
            "message": "De system-default winkel (Roadkillshop) mag niet verwijderd worden. Andere winkels wel.",
        }
    # Filter op permissie
    allowed = [s for s in matches if _user_can_delete_shop(user_id, s)]
    if not allowed:
        return {
            "type": "shop_delete_denied",
            "message": (
                f"Ik vond **{len(matches)}** winkel(s) met '{shop_name}', maar je bent geen eigenaar "
                "en geen admin — ik mag deze niet verwijderen. Vraag de eigenaar of een admin."
            ),
        }
    if len(allowed) == 1:
        s = allowed[0]
        pending = {
            "flow": "shop_delete",
            "step": 1,
            "shop_ids": [s.get("id")],
            "summary": s.get("naam") or s.get("name") or s.get("id"),
        }
        return {
            "type": "shop_delete_confirm",
            "message": (
                f"Wil je **{pending['summary']}** definitief verwijderen? "
                f"_Alle producten in die winkel worden ook weggegooid._ "
                f"Zeg **ja** om te bevestigen, **nee** om te annuleren."
            ),
            "pending_state": pending,
        }
    # >1 matches
    lines = [f"Ik vond **{len(allowed)}** winkels met '{shop_name}':"]
    for i, s in enumerate(allowed[:8], start=1):
        naam = s.get("naam") or s.get("name") or s.get("id")
        lines.append(f"  {i}. **{naam}** ({s.get('id')})")
    lines.append("")
    lines.append("_Typ het nummer (bv. **1**) om er één te verwijderen, of **alle** om alle te wissen._")
    pending = {
        "flow": "shop_delete",
        "step": "choose",
        "shop_ids": [s.get("id") for s in allowed[:8]],
        "summaries": [s.get("naam") or s.get("name") or s.get("id") for s in allowed[:8]],
    }
    return {
        "type": "shop_delete_choose",
        "message": "\n".join(lines),
        "pending_state": pending,
    }


def handle_shop_delete_choose(pending: dict, text: str) -> Dict:
    t = (text or "").strip().lower()
    ids = pending.get("shop_ids") or []
    summaries = pending.get("summaries") or []
    if re.match(r"^\s*(alle|allemaal|all)\b", t):
        return {
            "type": "shop_delete_confirm",
            "message": f"Weet je zeker dat je **alle {len(ids)}** winkels wilt verwijderen? _Zeg **ja** of **nee**._",
            "pending_state": {
                "flow": "shop_delete", "step": 1,
                "shop_ids": list(ids),
                "summary": f"{len(ids)} winkels",
            },
        }
    m = re.match(r"^\s*(\d+)\s*$", t)
    if m:
        idx = int(m.group(1)) - 1
        if 0 <= idx < len(ids):
            return {
                "type": "shop_delete_confirm",
                "message": f"Wil je **{summaries[idx]}** verwijderen? _Zeg **ja** of **nee**._",
                "pending_state": {
                    "flow": "shop_delete", "step": 1,
                    "shop_ids": [ids[idx]],
                    "summary": summaries[idx],
                },
            }
    return {
        "type": "shop_delete_repeat",
        "message": "Typ een nummer (bv. **1**), **alle**, of **nee** om te annuleren.",
        "pending_state": pending,
    }


def execute_shop_delete(user_id: str, shop_ids: list) -> Dict:
    """Verwijder shops. Dubbele permissie-check per shop."""
    if not _SHOPS_FP.exists():
        return {"type": "shop_delete_failed", "message": "Shops-bestand niet gevonden."}
    data = load_json(_SHOPS_FP, default={"shops": []})
    shops = data.get("shops", [])
    kept = []
    removed = []
    denied = []
    for s in shops:
        if s.get("id") in shop_ids:
            if s.get("id") == "shop-roadkill":
                kept.append(s)  # system-default nooit weg
                continue
            if _user_can_delete_shop(user_id, s):
                removed.append(s.get("naam") or s.get("id"))
                continue
            denied.append(s.get("naam") or s.get("id"))
            kept.append(s)
        else:
            kept.append(s)
    if not removed:
        if denied:
            return {
                "type": "shop_delete_denied",
                "message": f"Ik mag deze winkels niet verwijderen: {', '.join(denied)}.",
            }
        return {"type": "shop_delete_failed", "message": "Geen winkels verwijderd."}
    data["shops"] = kept
    save_json(_SHOPS_FP, data)
    msg = f"Klaar — **{len(removed)}** winkel{'s' if len(removed) > 1 else ''} verwijderd: {', '.join(removed)}."
    if denied:
        msg += f" _{len(denied)} zonder rechten overgeslagen: {', '.join(denied)}._"
    return {
        "type": "shop_deleted",
        "message": msg,
        "removed_count": len(removed),
    }


def handle_shop_delete_cancel() -> Dict:
    return {"type": "shop_delete_cancelled", "message": "Oké, ik laat de winkels staan."}


# v6_smart_intents_split_001 — Re-export profile/relation/age intents voor backwards-compat
from modules.chat.smart_intents_profile import (  # noqa: E402
    detect_my_relation_lookup,
    handle_my_relation_lookup,
    detect_age_lookup,
    _users_data,
    _resolve_person,
    detect_profile_lookup,
)
