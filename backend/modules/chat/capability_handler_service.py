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
    # Pak open backlog uit ROADMAP-JSON als die bestaat, anders een statisch overzicht
    rm = load_json(DATA / "system" / "roadmap.json", default={})
    open_items = []
    for k, section in (rm or {}).items():
        if isinstance(section, dict):
            for item in (section.get("items") or []):
                if item.get("status") in ("open", "pending", "in_progress"):
                    open_items.append(f"• {item.get('title', item.get('id', '?'))}")
    if not open_items:
        return {
            "type": "capability_response",
            "capability_id": "taken_lijst",
            "message": (
                "📋 **Open taken** (uit `/app/memory/ROADMAP.md`):\n"
                "• P0: Spark's hands — generic intent-router (deze laag nu live!)\n"
                "• P1: D&D Perks & Unlocks enforcement\n"
                "• P1: KB v2 hooks (Vocab/Graph/D&D/Voice-snippet)\n"
                "• P2: Frontend-knop boekhouder closing\n"
                "• P2: Closing-flow auto-trigger 21:00\n"
                "_Vraag 'wat zullen we doen?' voor concreter suggestie._"
            ),
        }
    return {
        "type": "capability_response",
        "capability_id": "taken_lijst",
        "message": "📋 **Open taken:**\n" + "\n".join(open_items[:10]),
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


def _handle_agenda_vandaag(user_id):
    """Vandaag's afspraken voor user."""
    if not user_id:
        return {"type": "capability_response", "capability_id": "agenda_vandaag",
                "message": "Ik moet weten wie je bent voor je agenda."}
    try:
        from pathlib import Path
        from modules.core.storage import load_json
        from datetime import datetime, timezone
        fp = Path(f"/app/backend/data/agenda/{user_id}.json")
        if not fp.exists():
            return {"type": "capability_response", "capability_id": "agenda_vandaag",
                    "message": "📅 Je agenda is nog leeg vandaag."}
        d = load_json(fp, default={"items": []})
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        items = [i for i in d.get("items", []) if (i.get("datum") or "").startswith(today)]
        if not items:
            return {"type": "capability_response", "capability_id": "agenda_vandaag",
                    "message": "📅 Geen afspraken vandaag."}
        lines = [f"📅 **Vandaag ({today}):**", ""]
        for i in items[:10]:
            t = i.get("tijd") or ""
            titel = i.get("titel") or i.get("event") or "(geen titel)"
            lines.append(f"  · {t} — {titel}")
        return {"type": "capability_response", "capability_id": "agenda_vandaag",
                "message": "\n".join(lines)}
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
}


def route_capability(text: str, user_id: Optional[str]) -> Optional[Dict]:
    """Match user-tekst → capability → execute handler. Return chat-response of None.

    Alle hits worden gelogd (capabilities module) voor observability.
    """
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
        return handler(user_id)
    except Exception as ex:
        log_event("capabilities", "capability_error", intent=cap_id, detail={"error": str(ex)})
        return {
            "type": "capability_error",
            "capability_id": cap_id,
            "message": f"Ik probeerde **{match.get('naam')}** uit te voeren maar er ging iets mis: {ex}",
        }
