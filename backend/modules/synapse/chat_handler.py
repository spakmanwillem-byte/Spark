"""
Synapse chat-handler (v6_synapse_001, F2)
==========================================
Voegt natuurlijke chat-intenties toe waarmee Spark zichzelf kan lezen:
  - "wat hebben we?"          → high-level summary
  - "wat zit er in jou?"      → same
  - "is X af?"                → status van module X
  - "waar woont X?"           → path + endpoints van X
  - "wat doet X?"             → doel + footnote van X
  - "lijst skeletons"         → alle status=skeleton modules
  - "lijst verouderd"         → alle status=deprecated/tagged_for_deletion

Hookt vóór capability-router in chat/routes.py.
"""
import re
from typing import Optional, Dict, List
from pathlib import Path
from modules.core.storage import load_json

SYNAPSE_FILE = Path("/app/memory/SYNAPSE.json")


# ============================================================
# INTENT-DETECTIE
# ============================================================
def detect_synapse_intent(text: str) -> Optional[Dict]:
    """Return dict met {action, query?} of None als geen match."""
    if not text:
        return None
    t = text.lower().strip().rstrip("?.! ")

    # High-level overview
    overview_patterns = (
        "wat hebben we", "wat heb je", "wat zit er in jou", "wat zit er in je",
        "spark wat heb je", "synapse overzicht", "synapslaag",
        "wat is er allemaal", "geef me overzicht", "wat is jouw structuur",
    )
    for p in overview_patterns:
        if p in t:
            return {"action": "overview"}

    # Lijst-vragen
    if any(p in t for p in ("lijst skeletons", "welke skeletons", "wat is nog skelet", "welke modules zijn skelet")):
        return {"action": "list_status", "status": "skeleton"}
    if any(p in t for p in ("lijst verouderd", "wat is verouderd", "wat is deprecated", "wat staat te verwijderen", "tagged for deletion")):
        return {"action": "list_status", "status": "deprecated_or_deletion"}

    # "Is X af?" / "Is X klaar?" / "Status van X"
    m = re.search(r"^(is|als)\s+(?:de\s+|het\s+)?(.+?)\s+(?:al\s+)?(?:af|klaar|gereed)$", t)
    if m:
        return {"action": "status_of", "query": m.group(2).strip()}
    m = re.search(r"status\s+(?:van\s+)?(.+)$", t)
    if m:
        return {"action": "status_of", "query": m.group(1).strip()}

    # "Waar woont X?" / "Waar zit X?" / "Waar staat X?"
    m = re.search(r"waar\s+(?:woont|zit|staat|leeft)\s+(?:de\s+|het\s+)?(.+)$", t)
    if m:
        return {"action": "where_is", "query": m.group(1).strip()}

    # "Wat doet X?" / "Wat is X?"
    m = re.search(r"wat\s+(?:doet|is|deed)\s+(?:de\s+|het\s+)?(.+)$", t)
    if m and len(m.group(1).strip()) >= 3:
        return {"action": "what_does", "query": m.group(1).strip()}

    return None


# ============================================================
# HANDLERS
# ============================================================
def _load_synapse() -> dict:
    if not SYNAPSE_FILE.exists():
        try:
            from .aggregator import build_synapse
            build_synapse()
        except Exception:
            return {}
    return load_json(SYNAPSE_FILE, default={})


def _all_records() -> List[tuple]:
    """Returnt [(path, group, meta), ...] voor alle records."""
    doc = _load_synapse()
    out = []
    for grp, items in doc.get("tree", {}).items():
        for path, meta in items.items():
            out.append((path, grp, meta))
    return out


def _find_by_name(query: str) -> List[tuple]:
    """Match op naam (exact, dan substring)."""
    q = (query or "").lower().strip()
    if not q:
        return []
    records = _all_records()
    # Exact match
    exact = [r for r in records if (r[2].get("naam") or "").lower() == q]
    if exact:
        return exact
    # Substring
    return [r for r in records if q in (r[2].get("naam") or "").lower()][:5]


def _handle_overview() -> Dict:
    doc = _load_synapse()
    s = doc.get("summary", {})
    if not s:
        return {
            "type": "synapse_overview",
            "message": "🧬 Mijn synapslaag is nog niet gescand. Vraag een admin: `GET /api/synapse/scan`.",
        }
    by_status = s.get("by_status", {})
    by_type = s.get("by_container_type", {})
    lines = [
        "🧬 **Mijn synapslaag — wat zit er in mij:**",
        "",
        f"📦 **{s.get('total_containers', 0)} containers** in totaal:",
        f"  • {by_type.get('dir', 0)} code-modules",
        f"  • {by_type.get('data', 0)} data-stores",
        f"  • {by_type.get('user', 0)} user-containers" if by_type.get('user') else None,
        f"  • {by_type.get('shop', 0)} shop-containers" if by_type.get('shop') else None,
        "",
        "📊 **Status verdeling:**",
        f"  • ✅ {by_status.get('active', 0)} actief",
        f"  • 🚧 {by_status.get('wip', 0)} in opbouw (wip)" if by_status.get('wip') else None,
        f"  • 🌱 {by_status.get('skeleton', 0)} skeletons",
        f"  • 🍂 {by_status.get('deprecated', 0)} verouderd" if by_status.get('deprecated') else None,
        f"  • 🗑️ {by_status.get('tagged_for_deletion', 0)} klaar voor verwijdering" if by_status.get('tagged_for_deletion') else None,
        "",
        f"🔌 **{s.get('total_endpoints_detected', 0)} endpoints** zelf-gedetecteerd",
        "",
        "_Vraag me: 'is winkelstraat af?', 'waar woont wallet?', 'wat doet glow_nav?', 'lijst skeletons'._",
    ]
    return {
        "type": "synapse_overview",
        "message": "\n".join(line for line in lines if line is not None),
    }


def _handle_list_status(status: str) -> Dict:
    records = _all_records()
    if status == "deprecated_or_deletion":
        hits = [r for r in records if r[2].get("status") in ("deprecated", "tagged_for_deletion")]
        title = "🍂 **Verouderd / klaar voor verwijdering**"
    else:
        hits = [r for r in records if r[2].get("status") == status]
        title = f"🌱 **Modules met status `{status}`**"
    if not hits:
        return {
            "type": "synapse_list",
            "message": f"{title}\n\n_Geen items gevonden. ✨_",
        }
    lines = [title, ""]
    for path, grp, meta in hits[:25]:
        naam = meta.get("naam")
        doel = meta.get("doel") or ""
        lines.append(f"  • **{naam}** ({grp}) — {doel}")
    if len(hits) > 25:
        lines.append(f"\n_+ {len(hits) - 25} meer…_")
    return {"type": "synapse_list", "message": "\n".join(lines)}


def _handle_status_of(query: str) -> Dict:
    hits = _find_by_name(query)
    if not hits:
        return {
            "type": "synapse_status",
            "message": f"🤔 Ik vind geen module met de naam **{query}** in mijn synapslaag.",
        }
    path, grp, meta = hits[0]
    status = meta.get("status", "unknown")
    icon = {"active": "✅", "wip": "🚧", "skeleton": "🌱",
            "deprecated": "🍂", "tagged_for_deletion": "🗑️", "deleted": "❌"}.get(status, "❓")
    lines = [
        f"{icon} **{meta.get('naam')}** — status: `{status}`",
        "",
        f"📂 Locatie: `{path}`",
        f"🎯 Doel: {meta.get('doel') or '_geen omschrijving_'}",
    ]
    fn = meta.get("footnote")
    fn_text = fn if isinstance(fn, str) else ((fn or {}).get("spark_note") or "")
    if fn_text:
        lines.append(f"📝 Footnote: {fn_text}")
    bp = meta.get("blueprint_ref")
    if bp:
        lines.append(f"📘 Blueprint: `{bp}`")
    ep_count = len(meta.get("endpoints") or [])
    if ep_count:
        lines.append(f"🔌 {ep_count} endpoints")
    fc = meta.get("file_count", 0)
    if fc:
        lines.append(f"📁 {fc} bestanden")
    if len(hits) > 1:
        lines.append(f"\n_(Ook gevonden: {', '.join(h[2].get('naam') for h in hits[1:5])})_")
    return {"type": "synapse_status", "message": "\n".join(lines)}


def _handle_where_is(query: str) -> Dict:
    hits = _find_by_name(query)
    if not hits:
        return {
            "type": "synapse_where",
            "message": f"🤔 Ik vind geen module met de naam **{query}** in mijn synapslaag.",
        }
    path, grp, meta = hits[0]
    lines = [
        f"📍 **{meta.get('naam')}** woont op:",
        f"`{path}`",
        "",
        f"({grp}, status: `{meta.get('status')}`)",
    ]
    ep = meta.get("endpoints") or []
    if ep:
        lines.append("")
        lines.append("🔌 Eigen endpoints:")
        for e in ep[:6]:
            lines.append(f"  · {e}")
        if len(ep) > 6:
            lines.append(f"  _… + {len(ep) - 6} meer_")
    return {"type": "synapse_where", "message": "\n".join(lines)}


def _handle_what_does(query: str) -> Dict:
    hits = _find_by_name(query)
    if not hits:
        return None  # Laat door naar normaal kennis-flow
    path, grp, meta = hits[0]
    naam = meta.get("naam")
    doel = meta.get("doel") or "_geen doel-omschrijving (admin kan toevoegen via /api/synapse/tag)_"
    lines = [
        f"🎯 **{naam}** — {doel}",
    ]
    fn = meta.get("footnote")
    fn_text = fn if isinstance(fn, str) else ((fn or {}).get("spark_note") or "")
    if fn_text:
        lines.append("")
        lines.append(f"📝 Notitie: {fn_text}")
    lines.append("")
    lines.append(f"📂 `{path}` · status `{meta.get('status')}`")
    return {"type": "synapse_what", "message": "\n".join(lines)}


# ============================================================
# ROUTE
# ============================================================
def route_synapse_intent(text: str, user_id: Optional[str] = None) -> Optional[Dict]:
    """Probeer een synapse-intent op de tekst te matchen + uit te voeren."""
    intent = detect_synapse_intent(text)
    if not intent:
        return None
    action = intent.get("action")
    try:
        if action == "overview":
            return _handle_overview()
        if action == "list_status":
            return _handle_list_status(intent.get("status"))
        if action == "status_of":
            return _handle_status_of(intent.get("query", ""))
        if action == "where_is":
            return _handle_where_is(intent.get("query", ""))
        if action == "what_does":
            return _handle_what_does(intent.get("query", ""))
    except Exception:
        return None
    return None
