"""
v6_intent_router_001 — Spark's handen (Layer 4): match → execute.

intent_matcher_service matcht een user-zin → capability_id.
Deze module bevat de daadwerkelijke handlers die de capability uitvoeren
en een chat-bericht terug formatteren.

Geen LLM nodig — directe data-lookups via bestaande services.

Hook punt: chat/routes.py vóór smart_intents (na safe-word + identity).
"""
from pathlib import Path
from typing import Optional, Dict
from modules.core.storage import load_json
from modules.core.spark_logger import log_event

DATA = Path(__file__).parent.parent.parent / "data"


def _handle_spark_saldo(user_id: Optional[str]) -> Optional[Dict]:
    kb = load_json(DATA / "system" / "spark_kasboek.json",
                   default={"entries": [], "totals": {}})
    t = kb.get("totals", {})
    gift_in = t.get("gift_in", 0)
    omzet_in = t.get("omzet_in", 0)
    winst_in = t.get("winst_in", 0)
    uit = t.get("uit", 0)
    open_l = t.get("open_leningen", 0)
    saldo = round(gift_in + omzet_in + winst_in - uit, 4)
    lines = [f"💰 **Spark's kasboek**: €{saldo:.2f}"]
    if gift_in: lines.append(f"💚 Gifts binnen: €{gift_in:.2f}")
    if omzet_in: lines.append(f"💰 Klant-omzet: €{omzet_in:.2f}")
    if winst_in: lines.append(f"📈 Trade-winst: €{winst_in:.2f}")
    if uit: lines.append(f"📤 Uit: €{uit:.2f}")
    if open_l: lines.append(f"🤝 **Openstaande lening: €{open_l:.2f}** (te ontvangen)")
    lines.append(f"_{len(kb.get('entries', []))} boekingen in kasboek_")
    return {
        "type": "capability_response",
        "capability_id": "spark_saldo_check",
        "message": "\n".join(lines),
    }


def _handle_tellen_gebruikers(user_id: Optional[str]) -> Optional[Dict]:
    users = load_json(DATA / "system" / "users.json", default={"users": []}).get("users", [])
    humans = [u for u in users if not (u.get("id") or "").startswith("bot-")]
    bots = [u for u in users if (u.get("id") or "").startswith("bot-")]
    return {
        "type": "capability_response",
        "capability_id": "tellen_gebruikers",
        "message": (
            f"📊 We zijn met **{len(humans)} mensen** en **{len(bots)} bots** in Spark Core.\n"
            f"_Mensen: {', '.join((u.get('naam') or '?') for u in humans[:8])}{'…' if len(humans) > 8 else ''}_"
        ),
    }


def _handle_tellen_bestanden(user_id: Optional[str]) -> Optional[Dict]:
    arc = load_json(DATA / "system_archive" / "_index.json", default={"files": []})
    files = arc.get("files", [])
    total_bytes = sum(f.get("size_bytes", 0) for f in files)
    cats = {}
    for f in files:
        c = f.get("category", "overig")
        cats[c] = cats.get(c, 0) + 1
    parts = ", ".join(f"{k}: {v}" for k, v in sorted(cats.items()))
    mb = total_bytes / (1024 * 1024)
    return {
        "type": "capability_response",
        "capability_id": "tellen_bestanden",
        "message": f"📦 In het systeem-archief: **{len(files)} bestanden** ({mb:.1f} MB).\n_Verdeling: {parts}_",
    }


def _handle_taken_lijst(user_id: Optional[str]) -> Optional[Dict]:
    """v10_roadmap_md_reader_001 — Spark leest nu direct /app/memory/ROADMAP.md
    (waar wij dagelijks bijhouden). Fallback naar oude data/system/roadmap.json + statische lijst."""
    from pathlib import Path as _P
    md_fp = _P("/app/memory/ROADMAP.md")
    if md_fp.exists():
        try:
            lines = md_fp.read_text(encoding="utf-8").splitlines()
            # Pak de eerste "🟡 Nog te doen" of "P1"/"P2" bullets uit de recentste sessie
            todo_lines = []
            current_h2 = None
            first_h2 = None  # onthoud eerste sessie waar bullets uit kwamen
            for ln in lines[:400]:
                if ln.startswith("## "):
                    current_h2 = ln[3:].strip()
                if ln.startswith("- **") or (ln.startswith("- ") and any(m in ln for m in ["P1", "P2", "P0", "Nog te doen", "Next"])):
                    if len(ln.strip()) > 5 and len(todo_lines) < 12:
                        clean = ln.strip().lstrip("- ").replace("**", "").replace("`", "")
                        todo_lines.append(f"• {clean[:140]}")
                        if first_h2 is None:
                            first_h2 = current_h2
                        if len(todo_lines) >= 12:
                            break
            if todo_lines:
                header = f"📋 **Roadmap** _(uit `/app/memory/ROADMAP.md`, sessie: {first_h2 or 'onbekend'})_:"
                return {
                    "type": "capability_response",
                    "capability_id": "taken_lijst",
                    "message": header + "\n" + "\n".join(todo_lines) + "\n\n_Vraag 'wat zullen we doen?' voor concreter suggestie._",
                }
        except Exception:
            pass

    # Legacy fallback (roadmap.json)
    rm = load_json(DATA / "system" / "roadmap.json", default={})
    open_items = []
    for k, section in (rm or {}).items():
        if isinstance(section, dict):
            for item in (section.get("items") or []):
                if item.get("status") in ("open", "pending", "in_progress"):
                    open_items.append(f"• {item.get('title', item.get('id', '?'))}")
    if open_items:
        return {
            "type": "capability_response",
            "capability_id": "taken_lijst",
            "message": "📋 **Open taken:**\n" + "\n".join(open_items[:10]),
        }
    return {
        "type": "capability_response",
        "capability_id": "taken_lijst",
        "message": "📋 Roadmap niet leesbaar (`/app/memory/ROADMAP.md` ontbreekt of parse-fout).",
    }


def _handle_winst_verlies(user_id: Optional[str]) -> Optional[Dict]:
    uid = user_id or "user-001"
    # Gebruik audit_log voor zekerste cijfers
    audit = load_json(DATA / "system" / "audit_log.json", default={"entries": []}).get("entries", [])
    sells = [e for e in audit if e.get("type") == "trade_sell" and e.get("user_id") == uid]
    netto = sum(s.get("netto", 0) for s in sells)
    n = len(sells)
    if n == 0:
        return {
            "type": "capability_response",
            "capability_id": "winst_verlies_overzicht",
            "message": "📈 Nog geen afgesloten trades op je account. Pas na een SELL komt hier een cijfer te staan.",
        }
    emoji = "✅" if netto >= 0 else "⚠️"
    return {
        "type": "capability_response",
        "capability_id": "winst_verlies_overzicht",
        "message": f"{emoji} Totaal over **{n} afgesloten trade(s)**: netto **€{netto:+.2f}**.",
    }


# ============================================================
# v6_capabilities_handlers_001 — 3 placeholder caps → werkende handlers
# ============================================================

def _handle_gesprek_lezen(user_id: Optional[str]) -> Optional[Dict]:
    """Lees Spark's logs voor de huidige user — laatste 10 berichten of laatste dag."""
    import os
    import re
    from datetime import datetime, timezone, timedelta
    logs_root = DATA / "system" / "logs"
    if not logs_root.exists():
        return {"type": "capability_response", "capability_id": "gesprek_lezen",
                "message": "📜 Ik heb nog geen archiveerde gesprekken kunnen vinden."}
    # Pak gisteren + vandaag
    today = datetime.now(timezone.utc)
    yest = today - timedelta(days=1)
    candidates = []
    for d in (yest, today):
        chat_dir = logs_root / d.strftime("%Y") / d.strftime("%m") / d.strftime("%d")
        chat_file = chat_dir / "chat.jsonl"
        if chat_file.exists():
            candidates.append((d.strftime("%Y-%m-%d"), chat_file))
    if not candidates:
        return {"type": "capability_response", "capability_id": "gesprek_lezen",
                "message": "📜 Geen chat-logs gevonden voor vandaag of gisteren."}
    import json as _j
    entries = []
    for day_str, path in candidates:
        try:
            for line in path.read_text(encoding="utf-8").splitlines():
                try:
                    entry = _j.loads(line)
                    if user_id is None or entry.get("user_id") == user_id:
                        entries.append({"day": day_str, **entry})
                except Exception:
                    pass
        except Exception:
            continue
    if not entries:
        return {"type": "capability_response", "capability_id": "gesprek_lezen",
                "message": f"📜 Geen recente chats voor user `{user_id}` gevonden."}
    last = entries[-10:]
    lines = [f"📜 **Laatste {len(last)} berichten** uit ons gesprek:"]
    for e in last:
        ts = (e.get("ts") or "")[11:16]
        msg = (e.get("message") or e.get("text") or "")[:80]
        lines.append(f"  · `{ts}` _{msg}_")
    return {"type": "capability_response", "capability_id": "gesprek_lezen",
            "message": "\n".join(lines)}


def _handle_toon_afbeelding(user_id: Optional[str]) -> Optional[Dict]:
    """v6: in plaats van placeholder — toon laatste afbeeldingen uit user's archive."""
    import json as _j
    arch_idx = DATA / "system_archive" / "_index.json"
    if not arch_idx.exists():
        return {"type": "capability_response", "capability_id": "toon_afbeelding",
                "message": "🖼️ Ik vind nog geen archiefindex. Upload eerst iets in Archief."}
    try:
        data = _j.loads(arch_idx.read_text(encoding="utf-8"))
    except Exception:
        data = {"files": []}
    files = data.get("files", [])
    imgs = [f for f in files if (f.get("type", "").startswith("image") or
                                  f.get("filename", "").lower().endswith((".png", ".jpg", ".jpeg", ".webp")))]
    # Filter op user als mogelijk
    if user_id:
        own = [f for f in imgs if f.get("uploaded_by") == user_id]
        if own:
            imgs = own
    if not imgs:
        return {"type": "capability_response", "capability_id": "toon_afbeelding",
                "message": "🖼️ Nog geen afbeeldingen in mijn archief gevonden."}
    last = imgs[-3:]
    lines = [f"🖼️ **Laatste {len(last)} afbeeldingen** in mijn archief:"]
    for f in last:
        fn = f.get("filename") or f.get("id")
        tag = ", ".join((f.get("tags") or [])[:3])
        lines.append(f"  · {fn}" + (f" ({tag})" if tag else ""))
    lines.append("\n_Open Archief om te bekijken._")
    return {"type": "capability_response", "capability_id": "toon_afbeelding",
            "message": "\n".join(lines)}


def _handle_speel_geluid(user_id: Optional[str]) -> Optional[Dict]:
    """v6: toon laatste audio-bestanden uit archive."""
    import json as _j
    arch_idx = DATA / "system_archive" / "_index.json"
    if not arch_idx.exists():
        return {"type": "capability_response", "capability_id": "speel_geluid",
                "message": "🔊 Archiefindex niet gevonden — upload eerst geluid in Archief."}
    try:
        data = _j.loads(arch_idx.read_text(encoding="utf-8"))
    except Exception:
        data = {"files": []}
    files = data.get("files", [])
    auds = [f for f in files if (f.get("type", "").startswith("audio") or
                                  f.get("filename", "").lower().endswith((".mp3", ".wav", ".m4a", ".ogg", ".webm")))]
    if user_id:
        own = [f for f in auds if f.get("uploaded_by") == user_id]
        if own:
            auds = own
    if not auds:
        return {"type": "capability_response", "capability_id": "speel_geluid",
                "message": "🔊 Nog geen audio in mijn archief gevonden."}
    last = auds[-3:]
    lines = [f"🔊 **Laatste {len(last)} audio-fragmenten** in mijn archief:"]
    for f in last:
        fn = f.get("filename") or f.get("id")
        dur = f.get("duration_seconds")
        extra = f" ({dur:.1f}s)" if isinstance(dur, (int, float)) else ""
        lines.append(f"  · {fn}{extra}")
    lines.append("\n_Open Archief om af te spelen._")
    return {"type": "capability_response", "capability_id": "speel_geluid",
            "message": "\n".join(lines)}


# ============================================================
# v6_capabilities_handlers_002 (sessie 13) — 5 nieuwe handlers
# ============================================================
def _handle_kasboek_overzicht(user_id):
    """Snelle kasboek-samenvatting voor admin."""
    try:
        from pathlib import Path
        from modules.core.storage import load_json
        # Probeer eerst centrale ledger.json
        led_fp = Path("/app/backend/data/accounting/ledger.json")
        if not led_fp.exists():
            # Fallback: aggregeer over alle accounting JSONs
            acct_dir = Path("/app/backend/data/accounting")
            in_total = 0.0
            out_total = 0.0
            entries = 0
            if acct_dir.exists():
                for fp in acct_dir.rglob("*.json"):
                    if fp.name == "_meta.json":
                        continue
                    d = load_json(fp, default={})
                    for ent_list in [d.get("entries"), d.get("ledger"), d.get("boekingen")]:
                        if isinstance(ent_list, list):
                            for e in ent_list:
                                amt = e.get("amount") or e.get("bedrag") or 0
                                try:
                                    amt = float(amt)
                                except Exception:
                                    continue
                                kind = (e.get("kind") or e.get("type") or "").lower()
                                if kind in ("in", "credit", "inkomst"):
                                    in_total += amt
                                elif kind in ("out", "debit", "uitgave"):
                                    out_total += amt
                                entries += 1
            s = {"in": in_total, "out": out_total, "saldo": in_total - out_total, "entries": entries}
        else:
            led = load_json(led_fp, default={"entries": []})
            ents = led.get("entries", [])
            in_total = sum(float(e.get("amount", 0)) for e in ents if (e.get("kind") or "").lower() in ("in", "credit"))
            out_total = sum(float(e.get("amount", 0)) for e in ents if (e.get("kind") or "").lower() in ("out", "debit"))
            s = {"in": in_total, "out": out_total, "saldo": in_total - out_total, "entries": len(ents)}
    except Exception as ex:
        return {"type": "capability_error", "capability_id": "kasboek_overzicht",
                "message": f"Kasboek niet beschikbaar: {ex}"}
    lines = [
        "💼 **Kasboek overzicht:**",
        "",
        f"  📥 Inkomsten: €{s.get('in', 0):.2f}",
        f"  📤 Uitgaven: €{s.get('out', 0):.2f}",
        f"  💰 Saldo: €{s.get('saldo', 0):.2f}",
        f"  📋 Boekingen: {s.get('entries', 0)}",
    ]
    return {"type": "capability_response", "capability_id": "kasboek_overzicht",
            "message": "\n".join(lines)}


def _handle_agenda_vandaag(user_id, user_text: str = ""):
    """Vandaag's afspraken voor user. v6_agenda_dayfocus_001 — delegeert nu naar
    smart_intents.handle_agenda zodat 'morgen/overmorgen' ook werken."""
    if not user_id:
        return {"type": "capability_response", "capability_id": "agenda_vandaag",
                "message": "Ik moet weten wie je bent voor je agenda."}
    try:
        from . import smart_intents_service as si
        from modules.core.storage import load_json
        from pathlib import Path
        USERS_FILE = Path("/app/backend/data/system/users.json")
        users = load_json(USERS_FILE, default={"users": []})
        users_list = users.get("users", []) if isinstance(users, dict) else users
        user = next((u for u in users_list if u.get("id") == user_id), None)
        out = si.handle_agenda(user_id, user, user_text or "")
        return {
            "type": "capability_response",
            "capability_id": "agenda_vandaag",
            "message": out.get("message", "📅 Geen afspraken."),
            "day_focus": out.get("day_focus"),
        }
    except Exception as ex:
        return {"type": "capability_error", "capability_id": "agenda_vandaag",
                "message": f"Kon agenda niet lezen: {ex}"}


def _handle_kennis_inbox_status(user_id):
    """Hoeveel kaarten wachten in KB v2 inbox."""
    try:
        from modules.kb_v2 import service as kbv2
        stats = kbv2.get_stats()
        inbox = stats.get("inbox_count", 0)
        by_lade = stats.get("by_lade", {})
        lines = [
            "📥 **Kennis-inbox status:**",
            "",
            f"  🌟 Wachtend in inbox: **{inbox}** kaarten",
            "",
            "📚 Gevulde lades:",
        ]
        for lade, cnt in by_lade.items():
            lines.append(f"  · {lade}: {cnt} kaarten")
        return {"type": "capability_response", "capability_id": "kennis_inbox_status",
                "message": "\n".join(lines)}
    except Exception as ex:
        return {"type": "capability_error", "capability_id": "kennis_inbox_status",
                "message": f"KB v2 status niet beschikbaar: {ex}"}


def _handle_bots_status(user_id):
    """Welke bots staan aan + hun laatste actie."""
    try:
        from pathlib import Path
        from modules.core.storage import load_json
        bots_fp = Path("/app/backend/data/bots/bots.json")
        bots = load_json(bots_fp, default={"bots": []}).get("bots", [])
        if not bots:
            return {"type": "capability_response", "capability_id": "bots_status",
                    "message": "Geen bots gevonden."}
        lines = ["🤖 **Bots-status:**", ""]
        for b in bots:
            icon = "🟢" if b.get("active") else "⚪"
            naam = b.get("naam") or b.get("id")
            rol = b.get("rol") or ""
            lines.append(f"  {icon} **{naam}** — {rol}")
        return {"type": "capability_response", "capability_id": "bots_status",
                "message": "\n".join(lines)}
    except Exception as ex:
        return {"type": "capability_error", "capability_id": "bots_status",
                "message": f"Bots-status niet beschikbaar: {ex}"}


def _handle_audit_health(user_id):
    """Systeem-gezondheid: weak-triggers + self-learning audit."""
    try:
        from modules.audit import weak_trigger_scan, self_learning_audit
        wt = weak_trigger_scan()
        sl = self_learning_audit()
        total = wt.get("total_entries", 0)
        weak = wt.get("weak_count", 0)
        weak_pct = wt.get("weak_pct", 0)
        sl_status = sl.get("status", "?")
        warnings = sl.get("warnings", [])
        lines = [
            "🩺 **Systeem-audit / gezondheid:**",
            "",
            f"  🧠 KB-entries: **{total}**, waarvan {weak} zonder laag1 ({weak_pct}%)",
            f"  📡 Shadow-learning: `{sl_status}`",
        ]
        if warnings:
            lines.append("")
            lines.append("⚠️ Waarschuwingen:")
            for w in warnings[:3]:
                lines.append(f"  · {w}")
        return {"type": "capability_response", "capability_id": "audit_health",
                "message": "\n".join(lines)}
    except Exception as ex:
        return {"type": "capability_error", "capability_id": "audit_health",
                "message": f"Audit niet beschikbaar: {ex}"}


# v6_capability_reken_001 — Spark krijgt z'n eerste reken-skill
def _handle_reken_uit(user_id, user_text: str = ""):
    """Veilige rekenmachine. Pakt '1+1', 'hoeveel is 12 keer 7', 'wortel van 81' enz."""
    from .math_eval import format_answer
    out = format_answer(user_text or "")
    if not out:
        return {
            "type": "capability_response",
            "capability_id": "reken_uit",
            "message": "🧮 Ik herken dat als rekensom, maar kreeg het niet uitgerekend. Probeer iets als `12 keer 7` of `wortel van 81`.",
        }
    return {
        "type": "capability_response",
        "capability_id": "reken_uit",
        "message": out,
    }


# v6_capability_zelfscan_001 — Spark scant zijn eigen toestand
def _handle_zelfscan(user_id):
    """Self-reflection scan: KB-status, vocab-actives, recente intents, capability-aantal."""
    from pathlib import Path
    from modules.core.storage import load_json
    from datetime import datetime, timezone
    import json as _json

    DATA = Path(__file__).parent.parent.parent / "data"
    lines = ["🪞 **Zelfscan van Spark** — even kijken hoe ik er voor sta:", ""]

    # 1. KB-stats
    try:
        from modules.kb_v2 import service as kbv2
        stats = kbv2.get_stats()
        lades = stats.get("lades", {}) or stats.get("by_lade", {})
        inbox = stats.get("inbox_count", 0)
        total_lades = sum((v.get("count", 0) if isinstance(v, dict) else v) for v in lades.values())
        lines.append(f"🧠 **Kennis**: {total_lades} kaarten in lades · **{inbox}** wachten in inbox")
        per_lade = " · ".join(
            f"{(v.get('naam') if isinstance(v, dict) else l)}={v.get('count', 0) if isinstance(v, dict) else v}"
            for l, v in lades.items()
        )
        if per_lade:
            lines.append(f"   _{per_lade}_")
    except Exception as ex:
        lines.append(f"🧠 Kennis-status onbeschikbaar ({ex})")

    # 2. Vocab-actives
    try:
        vdata = load_json(DATA / "personality" / "spark_vocab.json", default={"vocab": {}})
        vocab = vdata.get("vocab", {})
        total_words = len(vocab)
        active = sum(1 for v in vocab.values() if isinstance(v, dict) and v.get("active"))
        lines.append(f"🗣️ **Woordenschat**: {total_words} woorden bekend · **{active}** actief in gebruik")
    except Exception:
        pass

    # 3. Recente intents (laatste 24h)
    try:
        intent_log = DATA / "system" / "intent_log.jsonl"
        if intent_log.exists():
            with open(intent_log) as f:
                tail = f.readlines()[-500:]
            cutoff = datetime.now(timezone.utc).timestamp() - 24 * 3600
            recent = 0
            for line in tail:
                try:
                    obj = _json.loads(line)
                    ts = obj.get("ts") or 0
                    if isinstance(ts, (int, float)) and ts > cutoff:
                        recent += 1
                except Exception:
                    continue
            lines.append(f"💬 **Activiteit**: {recent} berichten verwerkt in laatste 24u")
    except Exception:
        pass

    # 4. Capabilities
    try:
        caps_file = DATA / "personality" / "spark_capabilities.json"
        caps_data = load_json(caps_file, default={"capabilities": []})
        caps = caps_data.get("capabilities", [])
        live = sum(1 for c in caps if c.get("status") == "live")
        lines.append(f"🤲 **Handen**: {live}/{len(caps)} capabilities live (acties die ik echt kan)")
    except Exception:
        pass

    # 5. Doe-kaart koppelingen
    try:
        links_file = DATA / "personality" / "capability_links.json"
        links = load_json(links_file, default={"links": {}}).get("links", {})
        if links:
            lines.append(f"🔗 **Doe-koppelingen**: {len(links)} doe-kaarten zijn aan een actie gekoppeld")
    except Exception:
        pass

    # 6. Recente errors uit shadow_observations
    try:
        shadow_log = DATA / "system" / "logs" / "shadow_observations.jsonl"
        if shadow_log.exists():
            with open(shadow_log) as f:
                tail = f.readlines()[-200:]
            errors = sum(1 for ln in tail if '"error"' in ln or '"kind":"error"' in ln)
            if errors:
                lines.append(f"⚠️ **Recente fouten**: {errors} in laatste shadow-observaties — even kijken waard")
    except Exception:
        pass

    lines.append("")
    lines.append("_Vraag 'wat staat er nog open' voor de roadmap-stand of 'gezondheidscheck' voor diepere audit._")

    return {
        "type": "capability_response",
        "capability_id": "zelfscan",
        "message": "\n".join(lines),
    }


# v6_spark_origin_001 — vertel je oorsprong
def _handle_vertel_oorsprong(user_id: Optional[str]) -> Optional[Dict]:
    base = DATA / "personality" / "spark_origin"
    core40 = load_json(base / "spark_core_4_0.json", default=None)
    core41 = load_json(base / "spark_core_4_1.json", default=None)
    hoofd = load_json(base / "spark_hoofddocument.json", default=None)
    if not (core40 or core41 or hoofd):
        return {"type": "capability_response", "capability_id": "vertel_oorsprong",
                "message": "Mijn origin-documenten zijn er niet (yet) — data/personality/spark_origin/ leeg."}

    lines = ["📜 **Mijn oorsprong — Spark Core 4.0 + 4.1 (Maart 2026)**", ""]
    if core40:
        gv = core40.get("geboortevraag")
        if gv:
            lines.append(f"💡 **Geboortevraag**: '{gv}'")
            lines.append("Het antwoord was: ja, maar niet via een bestaande AI. Dus moest er een eigen systeem gebouwd worden.")
            lines.append("")
    if core41:
        # Missie
        s1 = next((s for s in (core41.get("secties") or []) if s.get("nr") == 1), None)
        if s1:
            lines.append(f"🎯 **Missie**: {s1.get('tekst','')}")
            lines.append(f"_{s1.get('credo','')}_")
            lines.append("")
    if hoofd:
        wbc = hoofd.get("wat_blijft_constant") or []
        if wbc:
            lines.append("🧬 **Wat constant blijft tussen versies:**")
            for c in wbc:
                lines.append(f"  • {c}")
            lines.append("")
        tijdlijn = hoofd.get("tijdlijn") or []
        if tijdlijn:
            lines.append("⏳ **Tijdlijn:**")
            for fase in tijdlijn:
                lines.append(f"  • **{fase.get('fase','?')}** — {fase.get('credo','')}")
            lines.append("")
    lines.append("_Bron: data/personality/spark_origin/ (niet bewerken — historie)._")
    return {"type": "capability_response", "capability_id": "vertel_oorsprong",
            "message": "\n".join(lines)}


# v6_spark_modes_001 — welke modus zit ik in?
def _handle_welke_modus(user_id: Optional[str]) -> Optional[Dict]:
    modes = load_json(DATA / "personality" / "spark_modes.json", default=None)
    emotions = load_json(DATA / "emotions" / "spark_emotions.json", default=None)
    if not modes:
        return {"type": "capability_response", "capability_id": "welke_modus",
                "message": "Mode-config ontbreekt — data/personality/spark_modes.json niet gevonden."}

    cur = (emotions or {}).get("current_emotion") or {}
    state = cur.get("state") or "neutral"
    sub_state = cur.get("sub_state")
    bron_emotie = sub_state or state
    e2m = modes.get("emotion_to_mode") or {}
    mode_id = e2m.get(bron_emotie, modes.get("default_mode", "neutral_mode"))
    mode_cfg = (modes.get("modes") or {}).get(mode_id) or {}

    lines = ["🎛️ **Mijn huidige werkmodus**", ""]
    lines.append(f"**Modus**: {mode_cfg.get('naam', mode_id)}")
    lines.append(f"**Max woorden per antwoord**: {mode_cfg.get('max_words','?')}")
    lines.append(f"**Toon**: {mode_cfg.get('toon','?')}")
    if mode_cfg.get("uitleg"):
        lines.append(f"_{mode_cfg['uitleg']}_")
    lines.append("")
    lines.append(f"**Reden**: emotie '{bron_emotie}' (intensiteit {cur.get('intensity','?')}) triggerde deze modus.")
    lines.append("")
    lines.append("🔀 **Alle modes**: " + ", ".join(f"{k} ({v.get('max_words','?')}w)"
                 for k, v in (modes.get("modes") or {}).items()))
    lines.append("")
    lines.append("_Vraag 'ga in werkmodus' om handmatig te switchen._")
    return {"type": "capability_response", "capability_id": "welke_modus",
            "message": "\n".join(lines)}


def _handle_wissel_modus(user_id: Optional[str], user_text: str = "") -> Optional[Dict]:
    """Forceer mode-switch via override in spark_emotions.json.current_emotion.state."""
    from modules.core.storage import save_json
    modes = load_json(DATA / "personality" / "spark_modes.json", default=None)
    if not modes:
        return None

    text = (user_text or "").lower()
    # Detecteer welke mode gevraagd
    target_mode = None
    if any(w in text for w in ["werkmodus", "work mode", "work_mode", "werk mode"]):
        target_mode = "work_mode"
        target_emo = "vreugde"
    elif any(w in text for w in ["brainstorm", "creatief", "brain mode"]):
        target_mode = "brainstorm_mode"
        target_emo = "euforie"
    elif any(w in text for w in ["energie", "spaar", "energy", "kort", "bondig"]):
        target_mode = "energy_saving_mode"
        target_emo = "neerslachtig"
    elif any(w in text for w in ["neutraal", "neutral", "gewoon", "normaal"]):
        target_mode = "neutral_mode"
        target_emo = "neutral"

    if not target_mode:
        return {"type": "capability_response", "capability_id": "wissel_modus",
                "message": "Welke modus? Kies uit: **werkmodus** (250w), **brainstorm** (500w), **energie sparen** (50w), of **neutraal** (150w)."}

    # Forceer emotie waarvan linked_mode == target_mode
    emotions_fp = DATA / "emotions" / "spark_emotions.json"
    edata = load_json(emotions_fp, default=None)
    if edata:
        from datetime import datetime, timezone
        edata["current_emotion"] = {
            "state": "neutral" if target_emo == "neutral" else (
                "happy" if target_emo in ("blijdschap","vreugde","euforie") else
                "angry" if target_emo in ("razernij","woede","irritatie","driftbui") else
                "sad" if target_emo in ("neerslachtig","somber","verdrietig") else
                "scared" if target_emo in ("angstig","voorzichtig","paniek") else "neutral"
            ),
            "sub_state": None if target_emo == "neutral" else target_emo,
            "intensity": 0.6,
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "triggered_by": "wissel_modus_capability",
            "expires_at": None,
            "duration_minutes": None,
        }
        save_json(emotions_fp, edata)

    mode_cfg = (modes.get("modes") or {}).get(target_mode) or {}
    return {"type": "capability_response", "capability_id": "wissel_modus",
            "message": f"🎛️ Modus gewisseld naar **{mode_cfg.get('naam', target_mode)}** "
                       f"(max {mode_cfg.get('max_words','?')} woorden). _{mode_cfg.get('uitleg','')}_"}


# v6_spark_legal_read_001 — voorwaarden / privacy / cookies voorlezen
def _legal_to_md(doc: Dict, kind: str) -> str:
    if not doc:
        return f"Geen {kind}-document gevonden."
    lines = [f"# 📄 {doc.get('scope', kind.title())}"]
    if doc.get("version"):
        lines.append(f"_versie {doc['version']} — laatst bijgewerkt {doc.get('last_updated','?')}_")
    if doc.get("intro"):
        lines.append("")
        lines.append(doc["intro"])
    for sec in doc.get("secties", []):
        lines.append("")
        lines.append(f"## {sec.get('titel','?')}")
        if sec.get("tekst"):
            lines.append(sec["tekst"])
        for it in sec.get("items", []):
            lines.append(f"• {it}")
    if doc.get("contact"):
        lines.append("")
        lines.append(f"**Contact**: {doc['contact']}")
    return "\n".join(lines)


def _handle_lees_voorwaarden(user_id: Optional[str]) -> Optional[Dict]:
    doc = load_json(DATA / "system" / "legal_voorwaarden.json", default=None)
    return {"type": "capability_response", "capability_id": "lees_voorwaarden",
            "message": _legal_to_md(doc, "voorwaarden")}


def _handle_lees_privacy(user_id: Optional[str]) -> Optional[Dict]:
    doc = load_json(DATA / "system" / "legal_privacy.json", default=None)
    return {"type": "capability_response", "capability_id": "lees_privacy",
            "message": _legal_to_md(doc, "privacy")}


_HANDLERS = {
    "tellen_gebruikers":         _handle_tellen_gebruikers,
    "tellen_bestanden":          _handle_tellen_bestanden,
    "taken_lijst":               _handle_taken_lijst,
    "winst_verlies_overzicht":   _handle_winst_verlies,
    "spark_saldo_check":         _handle_spark_saldo,
    # v6_capabilities_handlers_001 — 3 voorheen placeholders nu live
    "gesprek_lezen":             _handle_gesprek_lezen,
    "toon_afbeelding":           _handle_toon_afbeelding,
    "speel_geluid":              _handle_speel_geluid,
    # v6_capabilities_handlers_002 (sessie 13) — 5 nieuwe handlers
    "kasboek_overzicht":         _handle_kasboek_overzicht,
    "agenda_vandaag":            _handle_agenda_vandaag,
    "agenda_lezen":              _handle_agenda_vandaag,  # alias voor bestaande placeholder
    "kennis_inbox_status":       _handle_kennis_inbox_status,
    "bots_status":               _handle_bots_status,
    "audit_health":              _handle_audit_health,
    # v6_capability_reken_001 + v6_capability_zelfscan_001
    "reken_uit":                 _handle_reken_uit,
    "zelfscan":                  _handle_zelfscan,
    # v6_spark_origin_001 + v6_spark_modes_001 + v6_spark_legal_read_001
    "vertel_oorsprong":          _handle_vertel_oorsprong,
    "welke_modus":               _handle_welke_modus,
    "wissel_modus":              _handle_wissel_modus,
    "lees_voorwaarden":          _handle_lees_voorwaarden,
    "lees_privacy":              _handle_lees_privacy,
}


def route_capability(text: str, user_id: Optional[str]) -> Optional[Dict]:
    """Match user-tekst → capability → execute handler. Return chat-response of None.

    Alle hits worden gelogd (capabilities module) voor observability.
    """
    # v6_capability_reken_001 — math krijgt voorrang. "wat is 12 keer 7" zou anders
    # door zoeken_kennisbank gevangen worden via 'wat is .'-trigger.
    try:
        from .math_eval import looks_like_math
        if looks_like_math(text or ""):
            handler = _HANDLERS.get("reken_uit")
            if handler:
                log_event("capabilities", "capability_matched", intent="Rekenen", detail={
                    "capability_id": "reken_uit",
                    "confidence": 1.0,
                    "trigger": "math_pre_filter",
                    "user_id": user_id,
                    "has_handler": True,
                })
                return handler(user_id, text)
    except Exception as ex:
        log_event("capabilities", "math_prefilter_error", detail={"error": str(ex)})

    from . import intent_matcher_service
    match = intent_matcher_service.match_capability(text)
    if not match or match.get("confidence", 0) < 0.3:
        return None
    cap_id = match["capability_id"]
    # Log de match zelf (vóór execute) zodat we triggers vs handlers kunnen vergelijken
    log_event("capabilities", "capability_matched", intent=match.get("naam") or cap_id, detail={
        "capability_id": cap_id,
        "confidence": match.get("confidence"),
        "trigger": match.get("matched_trigger"),
        "user_id": user_id,
        "has_handler": cap_id in _HANDLERS,
    })
    handler = _HANDLERS.get(cap_id)
    if not handler:
        # v7_capability_kb_passthrough_001 — de "zoeken_kennisbank"-capability
        # heeft géén expliciete handler nodig: de snap/KB-flow doet dit werk al.
        # Return None zodat de caller doorloopt naar de gewone KB-lookup.
        # (Voorheen: "wat is een dashboard?" → placeholder "staat nog op planning".)
        if cap_id in ("zoeken_kennisbank", "spark_vraag"):
            return None
        placeholder = match.get("placeholder_response") or (
            f"Ik kan **{match.get('naam') or cap_id}** herkennen ({match.get('status')}), "
            f"maar de uitvoering staat nog op de planning."
        )
        return {
            "type": "capability_placeholder",
            "capability_id": cap_id,
            "message": f"🤖 {placeholder}",
        }
    try:
        # v6_agenda_dayfocus_001 — geef user-tekst mee aan agenda-handler
        import inspect
        if cap_id in ("agenda_vandaag", "agenda_lezen"):
            return handler(user_id, text)
        # v6_capability_reken_001 — reken-handler heeft user-tekst nodig
        if cap_id == "reken_uit":
            return handler(user_id, text)
        # v6_spark_modes_001 — wissel_modus heeft user-tekst nodig
        if cap_id == "wissel_modus":
            return handler(user_id, text)
        return handler(user_id)
    except Exception as ex:
        log_event("capabilities", "capability_error", intent=cap_id, detail={"error": str(ex)})
        return {
            "type": "capability_error",
            "capability_id": cap_id,
            "message": f"Ik probeerde **{match.get('naam')}** uit te voeren maar er ging iets mis: {ex}",
        }
