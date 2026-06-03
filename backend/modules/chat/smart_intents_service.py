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


# ============== PROFILE LOOKUP INTENT (v6_profile_lookup_001 - 28 mei) ==============
# ============== v6_my_relation_lookup_001 — "Wie is/zijn mijn X" ==============
# Vragen als "Wie is mijn zus?", "Wie zijn mijn dochters?", "Wie is mijn vader"
# Antwoorden direct vanuit /persons/{user_id}_relationships.json — geen KB-cards.

from .relation_extraction_service import REL_TYPES as _REL_TYPES, REL_KEYS_SORTED as _REL_KEYS

# Plural forms → singular relation key. NB: REL_TYPES heeft o.a. "zus", "broer", "neef" etc.
_REL_PLURALS = {
    "zussen": "zus", "broers": "broer", "broertjes": "broer", "zusjes": "zus",
    "moeders": "moeder", "vaders": "vader",
    "dochters": "dochter", "zonen": "zoon", "kinderen": "kind",
    "vrienden": "vriend", "vriendinnen": "vriendin",
    "collegas": "collega", "collega's": "collega",
    "neven": "neef", "nichten": "nicht", "neefjes": "neef", "nichtjes": "nicht",
    "tantes": "tante", "ooms": "oom",
    "schoonzussen": "schoonzus", "schoonbroers": "schoonbroer",
    "schoonzonen": "schoonzoon", "schoondochters": "schoondochter",
    "oma's": "oma", "opa's": "opa", "omas": "oma", "opas": "opa",
}

# Alle herkende termen (singular + plural)
_ALL_REL_TERMS = sorted(
    list(_REL_KEYS) + list(_REL_PLURALS.keys()),
    key=len, reverse=True
)
_MY_REL_PATTERN = re.compile(
    rf"\bwie\s+(?:is|zijn)\s+mijn\s+({'|'.join(re.escape(k) for k in _ALL_REL_TERMS)})\b",
    re.IGNORECASE,
)


def detect_my_relation_lookup(text: str) -> Optional[str]:
    """Returnt de relatie-term (genormaliseerd, lowercase, singular) als 'Wie is mijn X' matcht."""
    if not text:
        return None
    m = _MY_REL_PATTERN.search(text)
    if not m:
        return None
    term = m.group(1).lower()
    # Normalize plurals
    return _REL_PLURALS.get(term, term)


def handle_my_relation_lookup(user_id: str, rel_term: str) -> Dict:
    """Vraagt persons-graaf op en geeft alle personen terug die op deze relatie matchen."""
    rel_type = _REL_TYPES.get(rel_term, rel_term)
    # rel_type kan bv. "familie/zus" zijn
    base_type = rel_type.split("/")[-1]  # "zus", "moeder", etc.

    REL_FILE = DATA_ROOT / "persons" / f"{user_id}_relationships.json"
    if not REL_FILE.exists():
        return {
            "type": "my_relation_lookup",
            "message": f"Ik heb geen relaties van jou opgeslagen. Vertel me eens over je {rel_term}? Dan onthoud ik het.",
            "matched_rel": rel_term,
            "found": [],
        }

    rel_data = load_json(REL_FILE, default={"relationships": []})
    rels = rel_data.get("relationships", []) if isinstance(rel_data, dict) else rel_data

    matches = []
    for r in rels:
        rt = (r.get("relation_type") or "").lower()
        # Match: exact "familie/zus" of suffix-match (laatste deel = "zus")
        if rt == rel_type.lower() or rt.endswith(f"/{base_type}") or rt == base_type:
            matches.append(r)

    if not matches:
        return {
            "type": "my_relation_lookup",
            "message": f"Ik weet (nog) niet wie jouw {rel_term} is. Vertel het me — bv. '\\<naam\\> is mijn {rel_term}' — dan onthoud ik het.",
            "matched_rel": rel_term,
            "found": [],
        }

    namen = [r.get("person_name") for r in matches if r.get("person_name")]
    # Mooie taal
    if len(namen) == 1:
        n = namen[0]
        notes = (matches[0].get("notes") or "").strip()
        extra = f"\n\n_{notes}_" if notes and not notes.startswith("Auto-detected") else ""
        msg = f"Jouw **{rel_term}** is **{n}**.{extra}"
    else:
        bulleted = "\n".join(f"- **{n}**" for n in namen)
        msg = f"Jouw **{rel_term}**:\n{bulleted}"
    return {
        "type": "my_relation_lookup",
        "message": msg,
        "matched_rel": rel_term,
        "found": namen,
    }


# Spark beantwoordt vragen over personen: "wie is Marieke?", "wat is Willems achternaam?"
# Privacy-gate: alleen users in vriendelijke graaf van vrager, óf publieke users (gradatie ≤ 4).

_PROFILE_PATTERNS = [
    r"\bwie is\s+([A-ZÀ-ŸÄ-Üa-zà-ÿä-ü][\w\- ']{1,30})\??",
    # "wat is X achternaam" / "wat is Willems achternaam"
    r"\b(wat|hoe)(\s+is)?\s+([A-ZÀ-Ÿa-zà-ÿ][\w\- ']{1,30})['\u2019]?s?\s+(achternaam|email|telefoon|leeftijd|geboortedatum|rang|gradatie)\??",
    # "wat is de achternaam van X"
    r"\b(wat|hoe)(\s+is)?(\s+(?:de\s+|haar\s+|zijn\s+))?(achternaam|email|telefoon|leeftijd|geboortedatum|rang|gradatie)\s+van\s+([A-ZÀ-Ÿa-zà-ÿ][\w\- ']{1,30})\??",
    r"\bvertel\s+(eens\s+)?over\s+([A-ZÀ-Ÿa-zà-ÿ][\w\- ']{1,30})\b",
    r"\bken\s+je\s+([A-ZÀ-Ÿa-zà-ÿ][\w\- ']{1,30})\??",
]


def _users_data():
    USERS_FILE = DATA_ROOT / "system" / "users.json"
    d = load_json(USERS_FILE, default={"users": []})
    return d.get("users", []) if isinstance(d, dict) else d


def _resolve_person(name_query: str, viewer_id: str):
    """Find person by name. Privacy-rules:
    - Owner profielen (gradatie ≤ 2) altijd zichtbaar
    - Viewer's eigen profiel altijd zichtbaar
    - Andere users alleen als ze in viewer's relationships staan
    """
    q = (name_query or "").strip().lower()
    if not q:
        return None, "no_name"
    users = _users_data()
    matches = []
    for u in users:
        if not isinstance(u, dict):
            continue
        full = (u.get("naam") or u.get("name") or "").lower()
        if not full:
            continue
        # Match op exact, voornaam-only, of partial
        if q == full or q in full.split() or q in full:
            matches.append(u)
    if not matches:
        return None, "not_found"
    if len(matches) > 1:
        # Geef alleen voornamen terug voor disambiguatie
        return matches, "ambiguous"
    person = matches[0]
    grad = int(person.get("gradatie", 7) or 7)
    # Publieke profielen (admin/super gradatie) of self → altijd OK
    if grad <= 2 or person.get("id") == viewer_id:
        return person, "ok"
    # Anders: check viewer's relationships
    REL_FILE = DATA_ROOT / "persons" / f"{viewer_id}_relationships.json"
    if REL_FILE.exists():
        rel_data = load_json(REL_FILE, default={"relationships": []})
        rels = rel_data.get("relationships", []) if isinstance(rel_data, dict) else rel_data
        for r in rels:
            if r.get("user_id") == person.get("id") or r.get("naam","").lower() == (person.get("naam") or "").lower():
                return person, "ok"
    return person, "no_access"


def detect_profile_lookup(text: str, viewer_id: str = "") -> Optional[Dict]:
    """Detecteert vragen als 'wie is Marieke?' of 'wat is Willems achternaam?'.
    Returns dict {type, message, person?} of None.
    """
    if not text or len(text) < 6:
        return None
    t = text.strip()
    name_query = None
    field = None
    for pat in _PROFILE_PATTERNS:
        m = re.search(pat, t, re.IGNORECASE)
        if not m:
            continue
        groups = m.groups()
        # Patroon "wat is Willems achternaam" → groups = (wat, is, willems, achternaam)
        if len(groups) == 4 and groups[3] and groups[3].lower() in ("achternaam","email","telefoon","leeftijd","geboortedatum","rang","gradatie"):
            name_query = (groups[2] or "").strip().rstrip("'\u2019s")
            field = groups[3].lower()
        # Patroon "wat is de achternaam van X" (5 groups)
        elif len(groups) >= 5 and groups[3] and groups[4]:
            field = (groups[3] or "").strip().lower()
            name_query = (groups[4] or "").strip()
        else:
            name_query = (groups[-1] or "").strip()
        break
    if not name_query:
        return None

    # Cleanup: remove trailing ?, leading "een/de"
    name_query = re.sub(r"^(een|de|het|die|dat)\s+", "", name_query, flags=re.I).strip("?., ")
    if not name_query or name_query.lower() in ("dat", "die", "het", "ik", "jij", "je"):
        return None

    person, status = _resolve_person(name_query, viewer_id)
    if status == "not_found":
        return {"type": "profile_lookup", "message": f"Ik ken geen '{name_query}' in mijn registers. Ben je zeker van de naam?"}
    if status == "ambiguous":
        names = ", ".join(p.get("naam") or p.get("name") or "?" for p in person[:5])
        return {"type": "profile_lookup_ambiguous", "message": f"Welke '{name_query}' bedoel je? Ik vind: {names}."}
    if status == "no_access":
        return {"type": "profile_lookup_denied", "message": f"Ik weet wel wie {person.get('naam', name_query)} is, maar deze persoon staat niet in jouw vrienden-graaf. Ik deel hun info alleen met vrienden."}

    # status == ok → bouw antwoord
    naam = person.get("naam") or person.get("name") or "?"
    rang = person.get("rang") or person.get("rank") or "—"
    grad = person.get("gradatie", "?")
    if field:
        # Specifiek veld vragen
        value = None
        if field in ("achternaam",):
            parts = naam.split()
            value = parts[-1] if len(parts) > 1 else "(alleen voornaam bekend)"
        elif field in ("email",):
            value = person.get("email") or "(niet ingevuld)"
        elif field in ("telefoon",):
            value = person.get("telefoon") or person.get("phone") or "(niet ingevuld)"
        elif field in ("leeftijd", "geboortedatum"):
            value = person.get("geboortedatum") or person.get("leeftijd") or "(niet ingevuld)"
        else:
            value = person.get(field) or "(niet ingevuld)"
        return {
            "type": "profile_lookup",
            "person_id": person.get("id"),
            "message": f"**{naam}** — {field}: {value}",
        }

    # Algemeen profiel
    return {
        "type": "profile_lookup",
        "person_id": person.get("id"),
        "message": (
            f"**{naam}** (gradatie {grad}, rang {rang}). "
            f"{'Admin / oprichter.' if int(grad)<=2 else 'Lid van het Spark Core platform.'}"
        ),
    }

