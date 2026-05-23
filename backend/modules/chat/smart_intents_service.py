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

DATA_ROOT = Path(__file__).parent.parent.parent / "data"
AGENDA_DIR = DATA_ROOT / "agenda"
NOTES_FILE = DATA_ROOT / "notes" / "notes.json"
TRIGGERS_FILE = DATA_ROOT / "triggers" / "conversation_triggers.json"
ROADMAP_FILE = DATA_ROOT / "system" / "roadmap.json"


# ============== AGENDA INTENT ==============
_AGENDA_PATTERNS = [
    r"\bwat staat\b.*\b(agenda|planning|gepland)\b",
    r"\bwat staat (er|op (de )?planning)\b",
    r"\bwat (staat|heb ik) (er )?(vandaag|morgen|overmorgen|deze week)\b",
    r"\b(heb|hebben) ik\b.*\b(afspraken|afspraak|in (de )?agenda)\b",
    r"\bagenda\b.*\b(vandaag|morgen|overmorgen|deze week)\b",
    r"\bwelke afspraken\b",
    r"\b(mijn |de )?planning\b.*\b(vandaag|morgen)\b",
]


def detect_agenda_intent(text: str) -> bool:
    t = (text or "").lower()
    return any(re.search(p, t) for p in _AGENDA_PATTERNS)


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
_NOTE_PATTERNS = [
    r"^\s*(maak |voeg )?(notitie|note)\s*[:\-]\s*(.+)$",
    r"^\s*(noteer|onthoud)\s*[:\-]?\s*(.+)$",
]


def detect_note_intent(text: str):
    """Return (matched: bool, content: str|None)"""
    if not text:
        return False, None
    t = text.strip()
    for pat in _NOTE_PATTERNS:
        m = re.match(pat, t, re.IGNORECASE)
        if m:
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


# ============== HELP / WAT KAN JE ==============
_HELP_PATTERNS = [
    r"\bwat kan je\b",
    r"\bwat kun je\b",
    r"\bhoe werk je\b",
    r"\bhelp\b\s*$",
    r"^/?help\b",
    r"\bwelke (commands|opdrachten|functies)\b",
    r"\bwat zijn je (mogelijkheden|capaciteiten)\b",
]


def detect_help_intent(text: str) -> bool:
    t = (text or "").lower().strip()
    return any(re.search(p, t) for p in _HELP_PATTERNS)


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
_SUGGEST_PATTERNS = [
    r"\bwat zullen we\b",
    r"\bwat (kunnen|gaan) we (gaan )?doen\b",
    r"\b(geef me|heb je) (een )?(idee|voorstel|suggestie)\b",
    r"\bwaar (moet|zou) ik aan werken\b",
    r"\bwat is (er )?(belangrijk|urgent)\b",
]


def detect_suggest_intent(text: str) -> bool:
    t = (text or "").lower().strip()
    return any(re.search(p, t) for p in _SUGGEST_PATTERNS)


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
_CLARIFY_PATTERNS = [
    r"\bnee\b.*\b(bedoel|bedoelde)\b",
    r"\b(bedoel|bedoelde) ik niet\b",
    r"\bdat (bedoel|bedoelde) ik niet\b",
    r"\b(verkeerd|fout)\b.*(begrepen|begrip|woord)\b",
]


def detect_clarify_intent(text: str) -> bool:
    t = (text or "").lower().strip()
    return any(re.search(p, t) for p in _CLARIFY_PATTERNS)


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
# "vertel me over X" / "wat heb je over X" / "alles over X"
_TOPIC_PATTERNS = [
    r"\bvertel (me |mij )?(eens )?over\s+(.+)$",
    r"\bwat heb je (allemaal )?over\s+(.+)\?",
    r"\balles over\s+(.+)$",
    r"\bwat weet je over\s+(.+)\?",
    r"\boverzicht\s+(van )?(.+)$",
]
KB_FILE = DATA_ROOT / "knowledge" / "learned_knowledge" / "knowledge_base.json"


def detect_topic_intent(text: str):
    """Return (matched, topic_query) tuple."""
    if not text:
        return False, None
    t = text.strip()
    for pat in _TOPIC_PATTERNS:
        m = re.search(pat, t, re.IGNORECASE)
        if m:
            topic = m.group(m.lastindex).strip().rstrip("?.! ")
            if topic and len(topic) >= 3:
                return True, topic
    return False, None


def handle_topic_overview(topic_query: str) -> Dict:
    """Zoek kaarten met topic of tag matching topic_query. Case-insensitive."""
    kb = load_json(KB_FILE, default={"knowledge_entries": []})
    entries = kb.get("knowledge_entries") or kb.get("entries") or []
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
_DELETE_PATTERNS = [
    r"\b(verwijder|wis|delete|sluit|stop)\s+(mijn|m'n|me)\s+account\b",
    r"\b(ik wil|wil)\s+mijn\s+account\s+(verwijder|wissen|opzeggen|deleten|kwijt|weg)",
    r"\bmijn\s+account\s+(verwijder|wissen|deleten|opzeggen)",
    r"\b(deactiveer|opheffen|opzeggen)\s+(mijn|m'n|me)\s+account\b",
    r"\baccount\s+(verwijder|opzeggen|sluiten)\b",
]
_YES_PATTERNS = [r"^\s*(ja|yes|jawel|zeker|inderdaad|akkoord|bevestig|ok|oké|prima|doe maar|graag)\b"]
_NO_PATTERNS = [r"^\s*(nee|nope|niet doen|stop|annuleer|annuleren|cancel|laat maar|nvm)\b"]


def detect_account_delete_intent(text: str) -> bool:
    t = (text or "").lower().strip()
    return any(re.search(p, t) for p in _DELETE_PATTERNS)


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
_COMMUNITY_RECAP_PATTERNS = [
    r"\bwat (is|was|werd) (er )?(gisteren|vandaag|eergisteren).{0,40}(besproken|gezegd|gepraat|gepost)\b",
    r"\bwat (is|was) er (gisteren|vandaag|eergisteren).{0,30}(community|chat)\b",
    r"\bcommunity (recap|samenvatting|overzicht)\b",
    r"\b(samenvatting|recap) (van )?(de )?community\b",
    r"\bwat heeft (de )?community (gisteren|vandaag|eergisteren) (gezegd|besproken)\b",
    r"\bwat (is|was) er (gisteren|vandaag|eergisteren) (besproken|gezegd|gepraat)\b",
]


def detect_community_recap_intent(text: str) -> Optional[int]:
    """Returnt offset_days (0=vandaag, 1=gisteren, 2=eergisteren) of None."""
    t = (text or "").lower()
    matched = any(re.search(p, t) for p in _COMMUNITY_RECAP_PATTERNS)
    if not matched:
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
_DND_HELP_PATTERNS = [
    r"\bd\&?d (help|uitleg|wat is)\b",
    r"\bhelp.{0,10}d\&?d\b",
    r"\bwat (is|zijn) d\&?d\b",
    r"\bhoe werkt d\&?d\b",
    r"\bspark world (uitleg|help)\b",
    r"\bbase line (uitleg|wat)\b",
    r"\bpersoonskaart (help|uitleg)\b",
    r"\brugzak (help|uitleg)\b",
    r"\binventory (help|uitleg)\b",
    r"\bbark (help|uitleg|wat is)\b",
]


def detect_dnd_help_intent(text: str) -> bool:
    t = (text or "").lower()
    return any(re.search(p, t) for p in _DND_HELP_PATTERNS)


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

