"""v6_snuffel_bestand_001 — Spark Internal File Search Capability.

Spark kan op verzoek zijn eigen JSON-data doorzoeken en gestructureerd terugmelden:
- KB v2 (alle 4 lades + inbox)
- Notes
- Personality (bijbel, self_awareness, origin, capabilities)
- Recente chat-logs (alleen van de huidige user — privacy)
- Tasks/agenda items
- Learned triggers

Triggers (fast-path):
  "snuffel [naar] X"
  "zoek in bestanden naar X"
  "doorzoek je geheugen op X"
  "waar staat info over X?"
  "vind X in je bestanden"

Privacy: chat-logs alleen voor opgevraagde user_id. KB-private kaarten alleen
van bron_user_id == viewer_id.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone

from modules.core.storage import load_json

DATA_ROOT = Path(__file__).parent.parent.parent / "data"

# v6_snuffel_code_001 — sandboxed roots voor source-file search
CODE_ROOTS = [
    Path("/app/backend/modules"),
    Path("/app/backend/config"),
    Path("/app/backend/data/blueprints"),
    Path("/app/backend/data/personality"),
    Path("/app/memory"),
]
CODE_EXTENSIONS = {".py", ".md", ".json", ".txt", ".yaml", ".yml"}
CODE_SKIP_DIRS = {"__pycache__", "node_modules", ".git", "build", "dist", "sandbox"}
CODE_MAX_FILE_BYTES = 200_000  # skip enorme bestanden

# ════════════════════════════════════════════════════════════
# TRIGGER DETECTIE
# ════════════════════════════════════════════════════════════

_SNUFFEL_PATTERNS = [
    r"\bsnuffel(?:\s+naar)?\s+(.+?)(?:\?|$|\.)",
    r"\bzoek\s+(?:in\s+(?:je\s+)?bestand(?:en)?|in\s+je\s+geheugen|in\s+je\s+kennis)\s+(?:naar\s+|op\s+)?(.+?)(?:\?|$|\.)",
    r"\bdoorzoek\s+(?:je\s+)?(?:geheugen|bestand(?:en)?|kennis|data)\s+(?:op\s+|naar\s+)?(.+?)(?:\?|$|\.)",
    r"\bwaar\s+(?:staat|heb\s+je|weet\s+je\s+iets)\s+(?:info|iets|data|kennis)?\s*(?:over\s+|van\s+)?(.+?)(?:\?|$|\.)",
    r"\bvind\s+(.+?)\s+in\s+(?:je\s+)?(?:bestand|kennis|geheugen|data)",
    r"\bkan\s+je\s+(?:eens\s+)?snuffelen\s+(?:naar\s+|op\s+)?(.+?)(?:\?|$|\.)",
]


def detect_snuffel_intent(text: str) -> Optional[str]:
    """Geeft de zoekterm terug als snuffel-intent gedetecteerd, anders None."""
    if not text or len(text.strip()) < 6:
        return None
    t = text.lower().strip()
    for pat in _SNUFFEL_PATTERNS:
        m = re.search(pat, t, re.IGNORECASE)
        if m:
            query = m.group(1).strip().strip('"\'`')
            # Strip filler-woorden
            query = re.sub(r"^(?:de|het|een|mijn|jouw|onze|wat|iets)\s+", "", query, flags=re.IGNORECASE)
            query = query.strip()
            if len(query) >= 2:
                return query
    return None


# ════════════════════════════════════════════════════════════
# ZOEKER PER BRON
# ════════════════════════════════════════════════════════════

def _score_match(query: str, text: str) -> int:
    """Eenvoudige scoring zonder rapidfuzz-dependency (sneller voor batch)."""
    if not text or not query:
        return 0
    q = query.lower().strip()
    t = text.lower()
    if q in t:
        # Exact substring match
        return 100 if t.startswith(q) or f" {q} " in t else 80
    # Token overlap
    q_tokens = set(re.findall(r"\w{3,}", q))
    t_tokens = set(re.findall(r"\w{3,}", t))
    if not q_tokens:
        return 0
    overlap = len(q_tokens & t_tokens)
    if overlap == 0:
        return 0
    return min(70, int(70 * overlap / len(q_tokens)))


def _search_kb_v2(query: str, viewer_id: Optional[str], max_results: int = 5) -> List[Dict]:
    """Doorzoek alle 4 lades + inbox."""
    hits: List[Tuple[int, Dict]] = []
    kbv2_dir = DATA_ROOT / "knowledge" / "v2"
    files = [
        ("doen",    "knowledge_v2_doen.json"),
        ("weten",   "knowledge_v2_weten.json"),
        ("voelen",  "knowledge_v2_voelen.json"),
        ("spreken", "knowledge_v2_spreken.json"),
        ("inbox",   "knowledge_inbox.json"),
    ]
    for lade_label, fname in files:
        data = load_json(kbv2_dir / fname, default={"kaarten": []})
        for card in data.get("kaarten", []):
            # Privacy filter
            if card.get("privacy") == "private":
                bron = card.get("bron_user_id")
                if bron and bron != viewer_id:
                    continue
            begrip = card.get("begrip", "")
            lagen = card.get("lagen", {}) or {}
            ws5 = card.get("ws5", {}) or {}
            tags = " ".join(card.get("tags", []) or [])
            haystack = " ".join([
                begrip,
                lagen.get("laag1", ""),
                lagen.get("laag2", ""),
                lagen.get("laag3", ""),
                lagen.get("laag4", ""),
                ws5.get("wat", ""),
                ws5.get("wie", ""),
                ws5.get("waarom", ""),
                tags,
            ])
            # Begrip krijgt boost
            begrip_score = _score_match(query, begrip)
            body_score = _score_match(query, haystack)
            score = max(begrip_score + 20, body_score) if begrip_score > 0 else body_score
            if score >= 50:
                snippet = lagen.get("laag1") or lagen.get("laag2") or begrip
                hits.append((score, {
                    "type": "kb-kaart",
                    "lade": lade_label,
                    "begrip": begrip,
                    "snippet": (snippet or "")[:180],
                    "id": card.get("id"),
                    "tags": (card.get("tags") or [])[:5],
                }))
    hits.sort(key=lambda x: -x[0])
    return [h[1] for h in hits[:max_results]]


def _search_notes(query: str, viewer_id: Optional[str], max_results: int = 3) -> List[Dict]:
    """Doorzoek notes.json — alleen notes van viewer of zonder owner."""
    notes_fp = DATA_ROOT / "notes" / "notes.json"
    if not notes_fp.exists():
        return []
    data = load_json(notes_fp, default=[])
    notes = data if isinstance(data, list) else data.get("notes", [])
    hits: List[Tuple[int, Dict]] = []
    for n in notes:
        owner = n.get("user_id") or n.get("owner")
        if owner and viewer_id and owner != viewer_id:
            continue
        text = " ".join([n.get("title", ""), n.get("content", ""), n.get("body", "")])
        score = _score_match(query, text)
        if score >= 50:
            snippet = (n.get("content") or n.get("body") or n.get("title") or "")[:180]
            hits.append((score, {
                "type": "note",
                "title": n.get("title", "(geen titel)"),
                "snippet": snippet,
                "id": n.get("id"),
                "created": n.get("created_at", ""),
            }))
    hits.sort(key=lambda x: -x[0])
    return [h[1] for h in hits[:max_results]]


def _search_personality(query: str, max_results: int = 3) -> List[Dict]:
    """Doorzoek bijbel + self_awareness + origin."""
    person_dir = DATA_ROOT / "personality"
    files = [
        ("bijbel",          person_dir / "spark_bijbel.json"),
        ("self_awareness",  person_dir / "spark_self_awareness.json"),
        ("capabilities",    person_dir / "spark_capabilities.json"),
        ("modes",           person_dir / "spark_modes.json"),
    ]
    # Origin docs
    origin_dir = person_dir / "spark_origin"
    if origin_dir.exists():
        for fp in origin_dir.glob("*.json"):
            files.append((f"origin/{fp.stem}", fp))

    hits: List[Tuple[int, Dict]] = []
    for label, fp in files:
        if not fp.exists():
            continue
        data = load_json(fp, default={})
        # Flatten to searchable string
        flat = json.dumps(data, ensure_ascii=False)
        score = _score_match(query, flat)
        if score >= 50:
            # Find best matching key
            best_key, best_snippet = _find_best_value_in_json(data, query)
            hits.append((score, {
                "type": "personality",
                "bron": label,
                "key": best_key,
                "snippet": (best_snippet or flat[:180])[:180],
            }))
    hits.sort(key=lambda x: -x[0])
    return [h[1] for h in hits[:max_results]]


def _find_best_value_in_json(data, query: str, path: str = "") -> Tuple[str, str]:
    """Recursief: vind value met hoogste match-score."""
    best_score = 0
    best_path = path
    best_val = ""
    q = query.lower()
    if isinstance(data, dict):
        for k, v in data.items():
            sub_path, sub_val = _find_best_value_in_json(v, query, f"{path}.{k}" if path else k)
            if sub_val:
                s = _score_match(query, sub_val)
                if s > best_score:
                    best_score = s
                    best_path = sub_path
                    best_val = sub_val
    elif isinstance(data, list):
        for i, v in enumerate(data):
            sub_path, sub_val = _find_best_value_in_json(v, query, f"{path}[{i}]")
            if sub_val:
                s = _score_match(query, sub_val)
                if s > best_score:
                    best_score = s
                    best_path = sub_path
                    best_val = sub_val
    elif isinstance(data, str):
        if q in data.lower() or _score_match(query, data) >= 50:
            return path, data
    return best_path, best_val


def _search_chat_logs(query: str, viewer_id: Optional[str], max_results: int = 3) -> List[Dict]:
    """Doorzoek chat-logs van viewer (privacy: alleen eigen logs)."""
    if not viewer_id:
        return []
    logs_dir = DATA_ROOT / "chat" / "logs"
    if not logs_dir.exists():
        return []
    # Probeer per-user file
    user_fp = logs_dir / f"{viewer_id}.json"
    if not user_fp.exists():
        return []
    data = load_json(user_fp, default={})
    convs = data.get("conversations", []) if isinstance(data, dict) else []
    hits: List[Tuple[int, Dict]] = []
    for conv in convs[-50:]:  # Laatste 50 conversaties
        msgs = conv.get("messages", []) or conv.get("turns", [])
        for m in msgs:
            text = m.get("text", "") or m.get("content", "")
            score = _score_match(query, text)
            if score >= 60:
                hits.append((score, {
                    "type": "chat-log",
                    "snippet": text[:180],
                    "role": m.get("role", "?"),
                    "ts": m.get("ts", "") or m.get("timestamp", ""),
                    "conv_id": conv.get("id", "?"),
                }))
                break  # 1 hit per conv genoeg
    hits.sort(key=lambda x: -x[0])
    return [h[1] for h in hits[:max_results]]


# ════════════════════════════════════════════════════════════
# HOOFD-FUNCTIE
# ════════════════════════════════════════════════════════════

def _search_code_files(query: str, max_results: int = 5) -> List[Dict]:
    """v6_snuffel_code_001 — grep-achtige zoek door Spark's eigen source/config files."""
    if not query or len(query) < 2:
        return []
    q_lower = query.lower()
    hits: List[Tuple[int, Dict]] = []
    for root in CODE_ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() not in CODE_EXTENSIONS:
                continue
            if any(p in CODE_SKIP_DIRS for p in path.parts):
                continue
            try:
                if path.stat().st_size > CODE_MAX_FILE_BYTES:
                    continue
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            t_lower = text.lower()
            if q_lower not in t_lower:
                continue
            # Score = aantal matches (capped) + bonus voor filename-match
            occur = t_lower.count(q_lower)
            score = min(100, occur * 10)
            if q_lower in path.name.lower():
                score += 30
            # Pak eerste match-regel als snippet
            idx = t_lower.find(q_lower)
            line_start = text.rfind("\n", 0, idx) + 1
            line_end = text.find("\n", idx)
            snippet = text[line_start:line_end if line_end != -1 else idx + 120].strip()
            hits.append((score, {
                "path": str(path),
                "rel_path": str(path.relative_to(Path("/app"))),
                "occurrences": occur,
                "snippet": snippet[:200],
            }))
    hits.sort(key=lambda x: -x[0])
    return [h[1] for h in hits[:max_results]]


def _search_namen(query: str, max_results: int = 5) -> List[Dict]:
    """v6_namen_001 — doorzoek namen-blueprint."""
    try:
        from modules.namen.service import search_names
        return search_names(query, max_results=max_results)
    except Exception:
        return []


def _search_bijbel(query: str, max_results: int = 5) -> List[Dict]:
    """v10_bijbel_semantic_layer_001 — doorzoek wijsheden/patronen/mentale modellen/ankers."""
    try:
        from modules.bijbel.service import search_entries
        return search_entries(query, max_results=max_results)
    except Exception:
        return []


def execute_snuffel(query: str, viewer_id: Optional[str] = None, scope: Optional[List[str]] = None) -> Dict:
    """Doorzoek alle bronnen voor query en geef gestructureerd resultaat.

    scope: optioneel subset van ['kb', 'notes', 'personality', 'chat']
    """
    if not query or len(query.strip()) < 2:
        return {"success": False, "error": "query te kort", "query": query}

    scope = scope or ["kb", "notes", "personality", "chat", "code", "namen", "wijsheden"]
    started = datetime.now(timezone.utc)
    results: Dict[str, List[Dict]] = {}
    if "kb" in scope:
        results["kb"] = _search_kb_v2(query, viewer_id, max_results=5)
    if "notes" in scope:
        results["notes"] = _search_notes(query, viewer_id, max_results=3)
    if "personality" in scope:
        results["personality"] = _search_personality(query, max_results=3)
    if "chat" in scope:
        results["chat"] = _search_chat_logs(query, viewer_id, max_results=3)
    if "code" in scope or "files" in scope or "bestanden" in scope:
        results["code"] = _search_code_files(query, max_results=5)
    if "namen" in scope or "names" in scope:
        results["namen"] = _search_namen(query, max_results=5)
    if "wijsheden" in scope or "bijbel" in scope:
        results["wijsheden"] = _search_bijbel(query, max_results=5)

    total = sum(len(v) for v in results.values())
    elapsed_ms = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)

    return {
        "success": True,
        "query": query,
        "viewer_id": viewer_id,
        "total_hits": total,
        "elapsed_ms": elapsed_ms,
        "scope": scope,
        "results": results,
    }


def format_snuffel_result_for_chat(result: Dict) -> str:
    """Pretty-format voor Spark's chat-reactie."""
    if not result.get("success"):
        return f"Snuffel mislukt: {result.get('error', 'onbekende fout')}"
    q = result["query"]
    total = result["total_hits"]
    if total == 0:
        return f"🔍 Ik heb gesnuffeld naar '{q}' maar niks gevonden in mijn bestanden. Misschien staat het ergens anders, of weet ik er nog niets over."

    lines = [f"🔍 **Snuffel-resultaat voor '{q}'** — {total} hits in {result['elapsed_ms']}ms\n"]

    kb_hits = result["results"].get("kb", [])
    if kb_hits:
        lines.append(f"**KB-kaarten ({len(kb_hits)}):**")
        for h in kb_hits:
            tags = f" `[{', '.join(h['tags'])}]`" if h.get('tags') else ""
            lines.append(f"  • [{h['lade']}] **{h['begrip']}**{tags}")
            if h.get('snippet'):
                lines.append(f"    {h['snippet'][:120]}")
        lines.append("")

    notes_hits = result["results"].get("notes", [])
    if notes_hits:
        lines.append(f"**Notes ({len(notes_hits)}):**")
        for h in notes_hits:
            lines.append(f"  • {h['title']}: {h.get('snippet', '')[:120]}")
        lines.append("")

    pers_hits = result["results"].get("personality", [])
    if pers_hits:
        lines.append(f"**Personality/Bijbel ({len(pers_hits)}):**")
        for h in pers_hits:
            lines.append(f"  • [{h['bron']}] {h['key']}: {h.get('snippet', '')[:120]}")
        lines.append("")

    chat_hits = result["results"].get("chat", [])
    if chat_hits:
        lines.append(f"**Eerdere gesprekken ({len(chat_hits)}):**")
        for h in chat_hits:
            ts = (h.get('ts') or '')[:10]
            lines.append(f"  • [{ts}] {h.get('role','?')}: \"{h['snippet'][:120]}\"")
        lines.append("")

    code_hits = result["results"].get("code", [])
    if code_hits:
        lines.append(f"**Bestanden/Code ({len(code_hits)}):**")
        for h in code_hits:
            lines.append(f"  • `{h['rel_path']}` ({h['occurrences']}× match)")
            if h.get('snippet'):
                lines.append(f"    {h['snippet'][:140]}")
        lines.append("")

    namen_hits = result["results"].get("namen", [])
    if namen_hits:
        lines.append(f"**Namen ({len(namen_hits)}):**")
        for h in namen_hits:
            lines.append(f"  • **{h['naam']}** — {h.get('categorie','?')}")
        lines.append("")

    wijs_hits = result["results"].get("wijsheden", [])
    if wijs_hits:
        lines.append(f"**Wijsheden/Bijbel ({len(wijs_hits)}):**")
        for h in wijs_hits:
            type_label = h.get("type", "?")
            begrippen = h.get("gerelateerde_begrippen", [])
            b_str = f" → {', '.join(begrippen[:4])}" if begrippen else ""
            lines.append(f"  • [{type_label}] \"{(h.get('tekst') or '')[:140]}\"{b_str}")

    return "\n".join(lines)
