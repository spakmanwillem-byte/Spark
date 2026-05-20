"""
Personal Documents Service — testament, survivalgids, etc.
Generiek patroon voor 'persoonlijke documenten' die de user via chat opbouwt.

Storage: /app/backend/data/users/{user_id}/documents/{doc_type}.json
Structuur (uniform voor alle doc-types):
{
  "type": "testament",
  "user_id": "user-001",
  "version": 1,
  "created": "...",
  "last_updated": "...",
  "title": "Mijn Testament",
  "secties": [{"titel": str, "tekst": str, "notitie": str?}],
  "notitie_globaal": str?
}

Doc types kunnen later worden uitgebreid (zorgvolmacht, wensen, levensoverzicht).
Templates komen later — nu kale skelet bij create.
"""
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from modules.core.storage import load_json, save_json

DATA_DIR = Path(__file__).parent.parent.parent / "data"


# ============================================================
# DOC TYPES — uitbreidbaar
# ============================================================

DOC_TYPES: Dict[str, Dict] = {
    "testament": {
        "label": "Testament",
        "emoji": "📜",
        "default_title": "Mijn Testament",
        "default_secties": [
            {"titel": "Persoonsgegevens", "tekst": ""},
            {"titel": "Erfgenamen", "tekst": ""},
            {"titel": "Specifieke wensen (legaten)", "tekst": ""},
            {"titel": "Executeur", "tekst": ""},
            {"titel": "Uitvaart wensen", "tekst": ""},
            {"titel": "Overige opmerkingen", "tekst": ""},
        ],
        "triggers_create": [
            r"\b(maak|creëer|start|begin) (een )?(mijn )?testament( aan)?\b",
            r"\btestament aanmaken\b",
            r"\bnieuw testament\b",
        ],
        "triggers_show": [
            r"\b(toon|laat zien|bekijk|lees) (mijn )?testament\b",
            r"\bwat staat (er )?in mijn testament\b",
            r"\bmijn testament\b",
        ],
        "triggers_append": [
            r"\b(voeg toe|noteer|schrijf op) (aan|in|bij) (mijn )?testament[:\s]+(.+)",
            r"\bin (mijn )?testament[:\s]+(.+)",
            r"\btestament[:\s]+(.+)",
        ],
        "triggers_delete": [
            r"\b(verwijder|wis) (mijn )?testament\b",
        ],
    },
    "survivalgids": {
        "label": "Survivalgids",
        "emoji": "🧭",
        "default_title": "Mijn Survivalgids",
        "default_secties": [
            {"titel": "Belangrijke contacten", "tekst": ""},
            {"titel": "Belangrijke documenten (waar te vinden)", "tekst": ""},
            {"titel": "Wachtwoorden / sleutels (locatie, niet inhoud)", "tekst": ""},
            {"titel": "Verzekeringen", "tekst": ""},
            {"titel": "Bankzaken & abonnementen", "tekst": ""},
            {"titel": "Praktische instructies (huis, dieren, etc.)", "tekst": ""},
            {"titel": "Persoonlijke boodschap", "tekst": ""},
        ],
        "triggers_create": [
            r"\b(maak|creëer|start|begin) (een )?(mijn )?survivalgids( aan)?\b",
            r"\bsurvivalgids aanmaken\b",
            r"\bnieuwe survivalgids\b",
        ],
        "triggers_show": [
            r"\b(toon|laat zien|bekijk|lees) (mijn )?survivalgids\b",
            r"\bwat staat (er )?in mijn survivalgids\b",
            r"\bmijn survivalgids\b",
        ],
        "triggers_append": [
            r"\b(voeg toe|noteer|schrijf op) (aan|in|bij) (mijn )?survivalgids[:\s]+(.+)",
            r"\bin (mijn )?survivalgids[:\s]+(.+)",
            r"\bsurvivalgids[:\s]+(.+)",
        ],
        "triggers_delete": [
            r"\b(verwijder|wis) (mijn )?survivalgids\b",
        ],
    },
}


# ============================================================
# DETECTOR
# ============================================================

def detect_personal_doc_intent(text: str) -> Optional[Dict]:
    """Return {doc_type, action, content?} of None.
    Actions: create | show | append | delete"""
    if not text:
        return None
    t = text.lower().strip()
    for doc_type, cfg in DOC_TYPES.items():
        for pat in cfg["triggers_create"]:
            if re.search(pat, t):
                return {"doc_type": doc_type, "action": "create"}
        for pat in cfg["triggers_delete"]:
            if re.search(pat, t):
                return {"doc_type": doc_type, "action": "delete"}
        for pat in cfg["triggers_append"]:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                content = m.groups()[-1].strip()
                if content and len(content) > 2:
                    return {"doc_type": doc_type, "action": "append", "content": content}
        for pat in cfg["triggers_show"]:
            if re.search(pat, t):
                return {"doc_type": doc_type, "action": "show"}
    return None


# ============================================================
# HELPERS
# ============================================================

def _doc_file(user_id: str, doc_type: str) -> Path:
    d = DATA_DIR / "users" / user_id / "documents"
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{doc_type}.json"


def _build_template(user_id: str, doc_type: str) -> Dict:
    cfg = DOC_TYPES[doc_type]
    now = datetime.now(timezone.utc).isoformat()
    return {
        "id": f"{doc_type}-{uuid.uuid4().hex[:8]}",
        "type": doc_type,
        "user_id": user_id,
        "version": 1,
        "title": cfg["default_title"],
        "secties": [{**s, "id": f"sec-{uuid.uuid4().hex[:6]}"} for s in cfg["default_secties"]],
        "notitie_globaal": "",
        "created": now,
        "last_updated": now,
    }


def _format_doc(doc: Dict) -> str:
    cfg = DOC_TYPES.get(doc["type"], {})
    emoji = cfg.get("emoji", "📄")
    label = cfg.get("label", doc["type"].title())
    lines = [f"{emoji} **{doc.get('title', label)}** _(v{doc.get('version', 1)})_", ""]
    for sec in doc.get("secties", []):
        lines.append(f"**{sec['titel']}**")
        if sec.get("tekst"):
            lines.append(sec["tekst"])
        else:
            lines.append("_(nog leeg)_")
        if sec.get("notitie"):
            lines.append(f"  _📝 {sec['notitie']}_")
        lines.append("")
    if doc.get("notitie_globaal"):
        lines.append(f"_📝 Algemene notitie:_ {doc['notitie_globaal']}")
        lines.append("")
    lines.append(f"_Laatst bewerkt: {doc.get('last_updated','?')[:16].replace('T',' ')}_")
    return "\n".join(lines)


# ============================================================
# HANDLERS
# ============================================================

def handle_create(user_id: str, doc_type: str) -> Dict:
    fp = _doc_file(user_id, doc_type)
    cfg = DOC_TYPES[doc_type]
    if fp.exists():
        existing = load_json(fp, default={})
        return {
            "type": f"doc_{doc_type}_exists",
            "message": f"{cfg['emoji']} Je hebt al een **{cfg['label']}** (aangemaakt {existing.get('created','?')[:10]}). Wil je hem bekijken of verwijderen?\n\nZeg: _\"bekijk {doc_type}\"_ of _\"verwijder {doc_type}\"_.",
            "response_type": "doc_exists",
        }
    doc = _build_template(user_id, doc_type)
    save_json(fp, doc)
    return {
        "type": f"doc_{doc_type}_created",
        "message": (
            f"{cfg['emoji']} **{cfg['label']}** aangemaakt en opgeslagen.\n\n"
            f"Skelet bevat {len(doc['secties'])} secties. Vul ze één voor één in via:\n"
            f"_\"voeg toe aan {doc_type}: <jouw tekst>\"_\n\n"
            f"Bekijk altijd met _\"bekijk {doc_type}\"_."
        ),
        "response_type": "doc_created",
        "doc_id": doc["id"],
    }


def handle_show(user_id: str, doc_type: str) -> Dict:
    fp = _doc_file(user_id, doc_type)
    cfg = DOC_TYPES[doc_type]
    if not fp.exists():
        return {
            "type": f"doc_{doc_type}_missing",
            "message": f"Je hebt nog geen **{cfg['label']}**. Zeg _\"maak {doc_type} aan\"_ om te starten.",
            "response_type": "doc_missing",
        }
    doc = load_json(fp, default={})
    return {"type": f"doc_{doc_type}_view", "message": _format_doc(doc), "response_type": "doc_view"}


def handle_append(user_id: str, doc_type: str, content: str) -> Dict:
    fp = _doc_file(user_id, doc_type)
    cfg = DOC_TYPES[doc_type]
    if not fp.exists():
        return {
            "type": f"doc_{doc_type}_missing",
            "message": f"Eerst aanmaken: zeg _\"maak {doc_type} aan\"_, dan kun je toevoegen.",
            "response_type": "doc_missing",
        }
    doc = load_json(fp, default={})
    # Append als een notitie-sectie (gedateerd) → user kan later herorganiseren
    secties = doc.setdefault("secties", [])
    secties.append({
        "id": f"sec-{uuid.uuid4().hex[:6]}",
        "titel": f"Aanvulling {datetime.now(timezone.utc).strftime('%d-%m-%Y %H:%M')}",
        "tekst": content,
    })
    doc["last_updated"] = datetime.now(timezone.utc).isoformat()
    doc["version"] = (doc.get("version", 1) or 1) + 1
    save_json(fp, doc)
    return {
        "type": f"doc_{doc_type}_appended",
        "message": f"{cfg['emoji']} Opgeslagen in **{cfg['label']}** (v{doc['version']}):\n\n_\"{content[:150]}{'...' if len(content)>150 else ''}\"_\n\nBekijk met _\"bekijk {doc_type}\"_.",
        "response_type": "doc_appended",
    }


def handle_delete(user_id: str, doc_type: str) -> Dict:
    fp = _doc_file(user_id, doc_type)
    cfg = DOC_TYPES[doc_type]
    if not fp.exists():
        return {
            "type": f"doc_{doc_type}_missing",
            "message": f"Je hebt geen **{cfg['label']}** om te verwijderen.",
            "response_type": "doc_missing",
        }
    # Soft-delete: rename naar .deleted-{ts}
    backup = fp.with_suffix(f".deleted-{int(datetime.now(timezone.utc).timestamp())}.json")
    fp.rename(backup)
    return {
        "type": f"doc_{doc_type}_deleted",
        "message": f"{cfg['emoji']} **{cfg['label']}** verwijderd. Backup bewaard in `{backup.name}` (handmatig terug te zetten indien nodig).",
        "response_type": "doc_deleted",
    }


# ============================================================
# DISPATCHER (1 entry point voor routes.py)
# ============================================================

def handle_personal_doc(user_id: str, intent: Dict) -> Dict:
    action = intent["action"]
    doc_type = intent["doc_type"]
    if action == "create":
        return handle_create(user_id, doc_type)
    if action == "show":
        return handle_show(user_id, doc_type)
    if action == "append":
        return handle_append(user_id, doc_type, intent.get("content", ""))
    if action == "delete":
        return handle_delete(user_id, doc_type)
    return {"type": "doc_unknown", "message": "Ik begrijp die documentactie niet.", "response_type": "doc_unknown"}


# ============================================================
# LIST + ARCHIVE INTEGRATION
# ============================================================

def list_user_docs(user_id: str) -> List[Dict]:
    """Lijst van persoonlijke documenten van user — voor weergave in Archief."""
    docs_dir = DATA_DIR / "users" / user_id / "documents"
    if not docs_dir.exists():
        return []
    out = []
    for fp in sorted(docs_dir.glob("*.json")):
        if fp.name.endswith(".deleted.json") or ".deleted-" in fp.name:
            continue
        try:
            d = load_json(fp, default={})
            cfg = DOC_TYPES.get(d.get("type", ""), {})
            out.append({
                "doc_type": d.get("type"),
                "label": cfg.get("label", d.get("type", "?").title()),
                "emoji": cfg.get("emoji", "📄"),
                "title": d.get("title"),
                "version": d.get("version"),
                "secties_count": len(d.get("secties", [])),
                "created": d.get("created"),
                "last_updated": d.get("last_updated"),
                "size_bytes": fp.stat().st_size,
                "filename": fp.name,
            })
        except Exception:
            continue
    return out
