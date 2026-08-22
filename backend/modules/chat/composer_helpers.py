"""v6_response_composer_refactor_001 — Hulpfuncties voor response_composer.py.

Uit response_composer.py geëxtraheerd om het hoofd-bestand onder ~500 regels
te krijgen. Alle helpers (loaders, formatters, prompt-builders, turn-memory)
zitten hier. response_composer.py blijft de orkestrator met compose_response().

Pure verplaatsing — geen logica-wijzigingen.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timezone

from modules.core.storage import load_json, save_json
from modules.core.blueprint import load_blueprint_cached


def _bp() -> Dict:
    return load_blueprint_cached("chat", "response_composer")


# v11_admin_family_001 — Family-relations lookup voor Willem/admin
def _load_family_relations_snippet(current_user_naam: str) -> Optional[str]:
    """Bouw een korte zin met family-relations voor de admin-context prompt.

    Leest data/system/users.json, zoekt de huidige user, en flatten
    family_relations dict → 'dochter Lotus (user-5dd295db), zoon X, ...'.
    Return None als geen family_relations bekend.
    """
    try:
        users_fp = Path(__file__).parent.parent.parent / "data" / "system" / "users.json"
        d = load_json(users_fp, default={"users": []})
        users = d.get("users", []) if isinstance(d, dict) else []
        me = next((u for u in users
                   if str(u.get("naam", "")).strip().lower() == current_user_naam.strip().lower()
                   or str(u.get("volledige_naam", "")).strip().lower() == current_user_naam.strip().lower()),
                  None)
        if not me:
            return None
        fr = me.get("family_relations") or {}
        if not fr:
            return None
        pieces = []
        for rel, members in fr.items():
            if not members:
                continue
            names = []
            for m in members:
                if isinstance(m, dict):
                    n = m.get("naam") or m.get("volledige_naam") or m.get("id")
                    uid = m.get("id", "")
                    names.append(f"{n} ({uid})" if uid else n)
                elif isinstance(m, str):
                    names.append(m)
            if names:
                pieces.append(f"{rel} = {', '.join(names)}")
        return "; ".join(pieces) if pieces else None
    except Exception:
        return None


# ════════════════════════════════════════════════════════════
# LOADERS — KB, bijbel, help-chain, mode, origin, awareness
# ════════════════════════════════════════════════════════════

def _load_relevant_kb(user_text: str, current_user_id: Optional[str] = None) -> List[Dict]:
    """Zoek begrippen uit user_text in V2 en geef hun kaarten terug.

    v6_kb_privacy_filter_001: filtert privé-kaarten van andere users uit.
    v13_semantic_lookup_001 (sessie 53): gebruikt nu `kb_v2.service.semantic_lookup`
    die scoort op begrip + ws5 + tags + verbanden + footnote + laag1. Voorheen
    keek deze functie alleen naar exact-match op begrip en tag-woord-match →
    Spark's 5W-inhoud werd niet geraadpleegd bij een chat-vraag.

    Elke kaart krijgt extra velden voor de composer:
      - `_ws5_gap`: True als 1+ van 5 W's leeg (Spark meldt dat in antwoord)
      - `_match_score`: rank-score
      - `_matched_fields`: op welke velden gematcht (voor debug/transparantie)
    """
    bp = _bp()
    limits = bp["limits"]

    try:
        from modules.kb_v2 import service as kbv2_svc
        top_n = int(limits.get("max_relevant_cards", 5))
        result = kbv2_svc.semantic_lookup(user_text, top_n=top_n * 2, min_score=5)
    except Exception:
        result = {"results": []}

    # Privacy-filter (v6_kb_privacy_filter_001)
    def _is_visible(card: Dict) -> bool:
        if card.get("privacy") != "private":
            return True
        bron = card.get("bron_user_id")
        if not bron:
            return True
        return current_user_id is not None and bron == current_user_id

    out: List[Dict] = []
    for r in (result.get("results") or []):
        k = r.get("kaart") or {}
        if not _is_visible(k):
            continue
        # Annotatie voor composer
        k = dict(k)
        k["_ws5_gap"] = bool(r.get("ws5_gap"))
        k["_match_score"] = int(r.get("score", 0))
        k["_matched_fields"] = list(r.get("matched_fields") or [])
        out.append(k)
        if len(out) >= int(limits.get("max_relevant_cards", 5)):
            break
    return out


def _load_relevant_kb_legacy(user_text: str, current_user_id: Optional[str] = None) -> List[Dict]:
    """LEGACY (v6): exact-begrip + tag-match. Bewaard voor rollback of debug.
    Niet meer aangeroepen sinds v13_semantic_lookup_001.
    """
    bp = _bp()
    paths = bp["paths"]
    limits = bp["limits"]
    tone = bp["tonality"]

    try:
        from modules.chat.snap_service import SnapService
        svc = SnapService()
        all_entries = svc._load_knowledge()
    except Exception:
        all_entries = []
        kbv2_dir = Path(paths["kbv2_dir"])
        for fname in ["knowledge_v2_doen", "knowledge_v2_weten",
                      "knowledge_v2_voelen", "knowledge_v2_spreken"]:
            d = load_json(kbv2_dir / f"{fname}.json", default={"kaarten": []})
            all_entries.extend(d.get("kaarten", []))

    def _is_visible(card: Dict) -> bool:
        if card.get("privacy") != "private":
            return True
        bron = card.get("bron_user_id")
        if not bron:
            return True
        return current_user_id is not None and bron == current_user_id

    all_entries = [e for e in all_entries if _is_visible(e)]

    min_len = tone["min_word_length_for_search"]
    words = [w.lower().strip(".,?!") for w in user_text.split()
             if len(w) >= min_len][:limits["max_user_text_words_for_search"]]

    hits = []
    for e in all_entries:
        b = (e.get("begrip") or "").lower().strip()
        if not b:
            continue
        if b in user_text.lower():
            hits.append((tone["exact_match_score"], e))
            continue
        tags = [t.lower() for t in (e.get("tags") or [])]
        score = sum(tone["tag_match_score"] for w in words if w in tags or w == b)
        if score > 0:
            hits.append((score, e))
    hits.sort(key=lambda x: -x[0])
    return [h[1] for h in hits[:limits["max_relevant_cards"]]]


def _load_bijbel_essence() -> Dict:
    bp = _bp()
    paths = bp["paths"]
    limits = bp["limits"]
    tone = bp["tonality"]

    bijbel = load_json(Path(paths["bijbel_fp"]), default={})
    identity = load_json(Path(paths["identity_fp"]), default={})
    return {
        "kernwaarden": bijbel.get("kernwaarden", [])[:limits["max_kernwaarden_shown"]],
        "normen": bijbel.get("normen", [])[:limits["max_normen_shown"]],
        "missie": identity.get("missie") or identity.get("doel"),
        "tone": identity.get("tone") or tone["default_tone"],
    }


def _load_help_chain_for_gradatie(gradatie: Optional[int], is_admin: bool = False) -> List[Dict]:
    """v6_spark_help_reuse_001 — Lees help-topics voor user-gradatie via inheritance-chain."""
    bp = _bp()
    help_dir = Path(bp["paths"]["bijbel_fp"]).parent.parent / "help"
    out: List[Dict] = []
    visited = set()
    current_grad = gradatie if gradatie is not None else 7

    while current_grad and current_grad not in visited and 1 <= current_grad <= 7:
        visited.add(current_grad)
        fp = help_dir / f"gradatie_{current_grad}.json"
        if not fp.exists():
            break
        data = load_json(fp, default={})
        for t in (data.get("extra_topics") or data.get("topics") or []):
            out.append({
                "from_gradatie": current_grad,
                "id": t.get("id"),
                "label": t.get("label"),
                "korte_uitleg": t.get("korte_uitleg"),
            })
        inh = data.get("inherits_from")
        if inh and inh.startswith("gradatie_"):
            try:
                current_grad = int(inh.split("_")[1])
            except Exception:
                break
        else:
            break

    if is_admin:
        admin_fp = help_dir / "admin.json"
        if admin_fp.exists():
            admin_data = load_json(admin_fp, default={})
            for t in (admin_data.get("extra_topics") or []):
                out.append({
                    "from_gradatie": "admin",
                    "id": t.get("id"),
                    "label": t.get("label"),
                    "korte_uitleg": t.get("korte_uitleg"),
                })
    return out


def _load_current_mode() -> Optional[Dict]:
    """v6_spark_modes_001 — Bepaal Spark's huidige werkmodus uit emotie."""
    bp = _bp()
    base = Path(bp["paths"]["bijbel_fp"]).parent
    modes_fp = base / "spark_modes.json"
    emotions_fp = base.parent / "emotions" / "spark_emotions.json"

    modes_data = load_json(modes_fp, default=None)
    if not modes_data:
        return None
    modes = modes_data.get("modes", {})
    default_mode_id = modes_data.get("default_mode", "neutral_mode")

    bron_emotie = None
    mode_id = default_mode_id
    try:
        edata = load_json(emotions_fp, default=None) or {}
        cur = edata.get("current_emotion") or {}
        state = cur.get("state") or "neutral"
        sub_state = cur.get("sub_state")
        bron_emotie = sub_state or state

        e2m = modes_data.get("emotion_to_mode") or {}
        if bron_emotie and bron_emotie in e2m:
            mode_id = e2m[bron_emotie]
        else:
            emotions = edata.get("emotions") or {}
            if state in emotions:
                emo_block = emotions[state]
                if sub_state and "sub_emotions" in emo_block:
                    sub = emo_block["sub_emotions"].get(sub_state) or {}
                    if sub.get("linked_mode"):
                        mode_id = sub["linked_mode"]
                elif emo_block.get("linked_mode"):
                    mode_id = emo_block["linked_mode"]
    except Exception:
        pass

    mode_cfg = modes.get(mode_id) or modes.get(default_mode_id) or {}
    return {
        "mode": mode_id,
        "mode_naam": mode_cfg.get("naam", mode_id),
        "max_words": mode_cfg.get("max_words"),
        "toon": mode_cfg.get("toon"),
        "uitleg": mode_cfg.get("uitleg"),
        "wanneer": mode_cfg.get("wanneer"),
        "bron_emotie": bron_emotie,
    }


def _load_origin() -> Optional[Dict]:
    """v6_spark_origin_001 — Lees Spark's origin-documenten."""
    bp = _bp()
    base = Path(bp["paths"]["bijbel_fp"]).parent / "spark_origin"
    if not base.exists():
        return None
    core40 = load_json(base / "spark_core_4_0.json", default=None)
    core41 = load_json(base / "spark_core_4_1.json", default=None)
    hoofd = load_json(base / "spark_hoofddocument.json", default=None)
    if not (core40 or core41 or hoofd):
        return None
    return {
        "geboortevraag": (core40 or {}).get("geboortevraag"),
        "missie_kort": ((core41 or {}).get("secties") or [{}])[0].get("tekst") if core41 else None,
        "credo_4_0": "Spark oordeelt niet. Spark ondersteunt.",
        "credo_4_1": "Spark is geen platform dat mensen vasthoudt. Spark is een gereedschap dat mensen sterker maakt.",
        "wat_blijft_constant": (hoofd or {}).get("wat_blijft_constant", [])[:4],
        "huidige_fase": "Spark Core 2.0 / v2 — FastAPI + React + lokale JSON",
        "_bron": "data/personality/spark_origin/",
    }


def _load_self_awareness(user_id: Optional[str] = None) -> Optional[Dict]:
    """v6_spark_self_awareness_001 — Spark's bewustzijn van eigen architectuur."""
    bp = _bp()
    paths = bp["paths"]
    base = Path(paths["bijbel_fp"]).parent
    awareness_fp = base / "spark_self_awareness.json"
    capabilities_fp = base / "spark_capabilities.json"
    self_reflections_fp = base / "spark_self_reflections.json"

    awareness = load_json(awareness_fp, default=None)
    if not awareness:
        return None

    awareness["_origin"] = _load_origin()
    awareness["_current_mode"] = _load_current_mode()

    caps_data = load_json(capabilities_fp, default={"capabilities": []})
    live_caps = [
        {"id": c.get("id"), "naam": c.get("naam"), "categorie": c.get("categorie")}
        for c in caps_data.get("capabilities", [])
        if c.get("status") == "live"
    ]
    awareness["_live_capabilities"] = live_caps

    reflections = load_json(self_reflections_fp, default={"reflections": []})
    awareness["_recent_self_reflections"] = (reflections.get("reflections", []) or [])[-5:]

    user_grad = None
    is_admin = False
    if user_id:
        try:
            from modules.chat.spark_user_view import build_user_profile
            prof = build_user_profile(user_id)
            user_grad = prof.get("gradatie")
            is_admin = bool(prof.get("is_admin")) or user_grad == 1
        except Exception:
            pass
    awareness["_help_topics_for_user"] = _load_help_chain_for_gradatie(user_grad, is_admin)
    awareness["_user_gradatie"] = user_grad

    return awareness


def _format_now_for_prompt() -> str:
    """v6_diep_time_001 — Spark tijd-bewustzijn injectie."""
    from datetime import timedelta
    tz_nl = timezone(timedelta(hours=2))
    now = datetime.now(tz_nl)
    weekdagen = ["maandag", "dinsdag", "woensdag", "donderdag", "vrijdag", "zaterdag", "zondag"]
    maanden = ["januari", "februari", "maart", "april", "mei", "juni",
               "juli", "augustus", "september", "oktober", "november", "december"]
    weekdag = weekdagen[now.weekday()]
    maand = maanden[now.month - 1]
    h = now.hour
    if 6 <= h < 12:
        dagdeel = "ochtend"
    elif 12 <= h < 18:
        dagdeel = "middag"
    elif 18 <= h < 23:
        dagdeel = "avond"
    else:
        dagdeel = "nacht"
    return (f"⏰ NU: {weekdag} {now.day} {maand} {now.year}, "
            f"{now.strftime('%H:%M')} (Nederlandse tijd, dagdeel: {dagdeel})")


# ════════════════════════════════════════════════════════════
# SNAP-CLUSTER + OPS-CONTEXT
# ════════════════════════════════════════════════════════════

def _load_snap_cluster(user_text: str, max_snaps: int = 6) -> List[Dict]:
    """v6_diep_snaps_001 — Fuzzy match snaps op begrip + context."""
    if not user_text or len(user_text.strip()) < 3:
        return []
    try:
        bp = _bp()
        v2_dir = Path(bp["paths"]["kbv2_dir"])
        inbox = load_json(v2_dir / "knowledge_inbox.json", default={"kaarten": []})
        cards = inbox.get("kaarten") or []
    except Exception:
        return []
    if not cards:
        return []

    user_lower = user_text.lower()
    try:
        from rapidfuzz import fuzz
        def _score(begrip: str, ctx: str) -> float:
            b = (begrip or "").lower()
            if not b:
                return 0.0
            if b in user_lower:
                return 100.0
            return float(fuzz.token_set_ratio(b, user_lower))
    except Exception:
        def _score(begrip: str, ctx: str) -> float:
            b = (begrip or "").lower()
            return 100.0 if (b and b in user_lower) else 0.0

    scored = []
    for c in cards:
        begrip = c.get("begrip", "")
        fn = c.get("footnote") or {}
        ctx = fn.get("snap_context", "")
        s = _score(begrip, ctx)
        if s >= 70:
            scored.append({
                "begrip": begrip,
                "context": ctx[:150],
                "vertrouwen": fn.get("vertrouwen", 0.3),
                "bron": fn.get("bron", "snap-auto"),
                "aangemaakt_op": fn.get("aangemaakt_op", ""),
                "score": s,
            })
    scored.sort(key=lambda x: (-x["score"], x.get("aangemaakt_op", "")), reverse=False)
    return scored[:max_snaps]


def _format_snap_cluster(snaps: List[Dict]) -> str:
    if not snaps:
        return "(geen relevante snaps gevonden — Spark heeft nog niets over dit onderwerp ge-noteerd)"
    lines = []
    for s in snaps:
        line = f"• '{s['begrip']}' (vertrouwen={s['vertrouwen']}, score={int(s['score'])}/100)"
        if s.get("context"):
            line += f" — context: \"{s['context']}\""
        lines.append(line)
    return "\n".join(lines)


def _load_ops_context(user_text: str, user_id: Optional[str]) -> Optional[str]:
    """v6_diep_ops_context_001 — Pre-fetch operationele info bij runtime-vragen."""
    if not user_text:
        return None
    t = user_text.lower()
    bp = _bp()
    base = Path(bp["paths"]["bijbel_fp"]).parent.parent

    lines: List[str] = []

    if any(w in t for w in ["hoeveel user", "aantal user", "hoeveel gebruiker", "aantal gebruiker",
                            "hoeveel mensen", "aantal mensen"]):
        try:
            users = load_json(base / "system" / "users.json", default={"users": []}).get("users", [])
            lines.append(f"OPERATIONEEL: Er zijn momenteel {len(users)} geregistreerde gebruikers in het systeem.")
            grad_count: Dict[int, int] = {}
            for u in users:
                g = u.get("gradatie") or u.get("grade") or 7
                grad_count[g] = grad_count.get(g, 0) + 1
            if grad_count:
                lines.append("  Gradatie-verdeling: " + ", ".join(f"G{g}={n}" for g, n in sorted(grad_count.items())))
        except Exception:
            pass

    if any(w in t for w in ["hoeveel module", "aantal module", "welke module", "welke modules",
                            "wat voor module", "welke onderdel"]):
        try:
            modules_dir = base.parent / "modules"
            mod_count = sum(1 for p in modules_dir.iterdir() if p.is_dir() and p.name != "__pycache__")
            lines.append(f"OPERATIONEEL: Er zijn {mod_count} modules in de backend ({modules_dir.name}/).")
        except Exception:
            pass

    if any(w in t for w in ["hoeveel kaart", "aantal kaart", "kb groot", "knowledge base groot",
                            "hoeveel kennis", "hoe groot is je kennis"]):
        try:
            v2_dir = Path(bp["paths"]["kbv2_dir"])
            totals = {}
            for lade in ["doen", "weten", "voelen", "spreken"]:
                d = load_json(v2_dir / f"knowledge_v2_{lade}.json", default={"kaarten": []})
                totals[lade] = len(d.get("kaarten") or [])
            inbox = load_json(v2_dir / "knowledge_inbox.json", default={"kaarten": []})
            totals["inbox"] = len(inbox.get("kaarten") or [])
            total = sum(totals.values())
            lines.append(f"OPERATIONEEL: KB v2 telt {total} kaarten — "
                         + ", ".join(f"{k}={v}" for k, v in totals.items()))
        except Exception:
            pass

    if any(w in t for w in ["mijn log", "vorige gesprek", "wat hebben we besproken", "mijn sessie",
                            "hoeveel keer", "mijn geschiedenis"]):
        try:
            logs_dir = base / "chat" / "logs"
            if logs_dir.exists():
                user_logs = [p for p in logs_dir.glob("*.json")
                             if user_id and (user_id in p.name)]
                lines.append(f"OPERATIONEEL: Voor user {user_id}: {len(user_logs)} sessie-bestanden in logs/.")
        except Exception:
            pass

    return "\n".join(lines) if lines else None


# ════════════════════════════════════════════════════════════
# AUTO-SNAP UIT DIEP
# ════════════════════════════════════════════════════════════

def _auto_snap_from_diep(user_text: str, user_naam: str, had_kb_match: bool = False) -> None:
    """v6_diep_snap_write_002 — Schrijf snaps vanuit Diep voor inhoudsvragen."""
    _ = had_kb_match
    if not user_text or len(user_text.split()) < 5:
        return
    t = user_text.lower()
    meta_skip = ["wat kan je", "wat kun je", "wie ben je", "welke modus", "help",
                 "speel sps", "vertel je oorsprong", "lees de voorwaarden"]
    if any(m in t for m in meta_skip):
        return
    try:
        from modules.chat.snap_service import SnapNLPService, STOPWOORDEN
        svc = SnapNLPService()
        words = []
        for w in user_text.split():
            cw = w.strip(".,?!:;'\"()").lower()
            if len(cw) >= 4 and cw not in STOPWOORDEN and not cw.isdigit():
                words.append(cw)
        seen = set()
        unique_words = []
        for w in words:
            if w not in seen:
                seen.add(w)
                unique_words.append(w)
            if len(unique_words) >= 3:
                break
        for concept in unique_words:
            try:
                svc.create_word_snap(
                    concept=concept,
                    context=user_text[:200],
                    user_naam=user_naam,
                    extra_tags=["from-diep", "gap-fill"],
                )
            except Exception:
                pass
    except Exception:
        pass


# ════════════════════════════════════════════════════════════
# FORMATTERS — self-awareness, KB-cards, turns
# ════════════════════════════════════════════════════════════

def _format_self_awareness_for_prompt(aw: Dict) -> str:
    """Bouw compacte sectie voor system_prompt."""
    if not aw:
        return ""
    lines = ["=== Wat je over jezelf weet (zelf-kennis) ==="]

    origin = aw.get("_origin") or {}
    if origin:
        lines.append("Jouw oorsprong (Spark Core 4.0 + 4.1, Maart 2026):")
        if origin.get("geboortevraag"):
            lines.append(f"  Geboortevraag: '{origin['geboortevraag']}' — JA, en niet via een bestaande AI.")
        if origin.get("credo_4_0"):
            lines.append(f"  Credo: {origin['credo_4_0']}")
        if origin.get("credo_4_1"):
            lines.append(f"  Credo: {origin['credo_4_1']}")
        constants = origin.get("wat_blijft_constant") or []
        if constants:
            lines.append("  Wat constant blijft tussen versies:")
            for c in constants:
                lines.append(f"    - {c}")
        if origin.get("huidige_fase"):
            lines.append(f"  Huidige fase: {origin['huidige_fase']}")
        lines.append("")

    mode_info = aw.get("_current_mode") or {}
    if mode_info:
        lines.append(f"Je huidige werkmodus: {mode_info.get('mode_naam','?')} "
                     f"(max {mode_info.get('max_words','?')} woorden, "
                     f"toon={mode_info.get('toon','?')}).")
        if mode_info.get("uitleg"):
            lines.append(f"  {mode_info['uitleg']}")
        if mode_info.get("bron_emotie"):
            lines.append(f"  Reden: emotie '{mode_info['bron_emotie']}' triggerde deze modus.")
        lines.append("")

    user_grad = aw.get("_user_gradatie")
    if user_grad:
        lines.append(f"Deze gebruiker heeft gradatie {user_grad}.")
        lines.append("")

    help_topics = aw.get("_help_topics_for_user", [])
    if help_topics:
        lines.append(f"Wat deze gebruiker mag/kan in jouw app (gefilterd op gradatie {user_grad}):")
        for t in help_topics[:20]:
            label = t.get("label", "?")
            uitleg = (t.get("korte_uitleg") or "")[:140]
            lines.append(f"  - {label}: {uitleg}")
        if len(help_topics) > 20:
            lines.append(f"  (en nog {len(help_topics) - 20} andere — zie help-popup)")
        lines.append("")

    tabs = aw.get("app_tabs", [])
    if tabs:
        lines.append("Tabs in de app die jij kent:")
        for t in tabs:
            lines.append(f"  - {t.get('naam')}: {t.get('doel')}")
        lines.append("")

    caps = aw.get("_live_capabilities", [])
    if caps:
        lines.append(f"Wat je echt kan (live capabilities, {len(caps)} stuks):")
        for c in caps:
            lines.append(f"  - {c.get('naam')} [{c.get('id')}]")
        lines.append("")

    modules = aw.get("eigen_module_map", {})
    if modules:
        lines.append("Je eigen module-structuur (waar je 'lichaamsdelen' zitten):")
        for k, v in modules.items():
            lines.append(f"  - {k}: {v}")
        lines.append("")

    refls = aw.get("_recent_self_reflections", [])
    if refls:
        lines.append("Recente uitspraken die je over jezelf hebt gedaan (consistentie):")
        for r in refls:
            quote = (r.get("quote") or "")[:200]
            lines.append(f"  - [{r.get('topic')}] {quote}")
        lines.append("")

    principes = aw.get("principes_kort", [])
    if principes:
        lines.append("Jouw architecturale principes:")
        for p in principes:
            lines.append(f"  - {p}")
    return "\n".join(lines)


def _format_kb_cards(cards: List[Dict]) -> str:
    """v13_semantic_lookup_001 (sessie 53) — toont nu ook ws5 (5W-antwoorden) én
    markeert kaarten met een ws5-gap zodat Spark kan zeggen "ik vond X maar mijn
    W's zijn hier niet volledig, wil je even helpen invullen?".
    """
    if not cards:
        return "(geen specifieke kaarten gevonden — antwoord vanuit algemene Spark-identiteit)"
    limits = _bp()["limits"]
    lines = []
    gap_cards = []
    for c in cards:
        b = c.get("begrip", "?")
        laag1 = (c.get("lagen") or {}).get("laag1", "")[:limits["max_card_laag1_chars"]]
        laag2 = (c.get("lagen") or {}).get("laag2", "")[:limits["max_card_laag2_chars"]]
        lade = c.get("lade") or c.get("_lade") or "?"
        tags = ", ".join((c.get("tags") or [])[:limits["max_card_tags_shown"]])
        vertrouwen = (c.get("footnote") or {}).get("vertrouwen", "?")
        matched_fields = c.get("_matched_fields") or []
        gap = bool(c.get("_ws5_gap"))

        # Header met eventuele gap-marker
        gap_mark = " ⚠️ws5-onvolledig" if gap else ""
        lines.append(f"• [{lade}] {b} (vertrouwen={vertrouwen}{gap_mark})")
        if laag1:
            lines.append(f"    betekenis: {laag1}")
        if laag2:
            lines.append(f"    verdieping: {laag2}")

        # v13_semantic_lookup_001 — toon ws5 (max 90 chars per W om budget te sparen)
        ws5 = c.get("ws5") or {}
        for w_key in ("wie", "wat", "waar", "wanneer", "waarom"):
            v = ws5.get(w_key)
            if v and str(v).strip():
                lines.append(f"    {w_key}: {str(v)[:90]}")
        if tags:
            lines.append(f"    tags: {tags}")

        if gap:
            gap_cards.append(b)

    # Meta-instructie voor Spark: als er kaarten met gap zijn, moedig aan om te vragen
    if gap_cards:
        gap_list = ", ".join(f"'{g}'" for g in gap_cards[:3])
        lines.append("")
        lines.append(
            f"⚠️ Sommige kaarten hierboven ({gap_list}) hebben nog niet alle 5 W's ingevuld. "
            f"Als je merkt dat je antwoord daar tegenaan loopt: zeg dat, en vraag Willem "
            f"vriendelijk of hij die W nog wil aanvullen. Nooit doen alsof je het weet."
        )
    return "\n".join(lines)


def _format_turns(turns: List[Dict], user_naam: str = "Gebruiker") -> str:
    if not turns:
        return "(geen eerdere berichten in deze sessie)"
    max_chars = _bp()["limits"]["max_turn_chars"]
    out = []
    for t in turns:
        role = user_naam if t.get("role") == "user" else "Spark"
        text = (t.get("text") or t.get("message") or "")[:max_chars]
        if text:
            out.append(f"  {role}: {text}")
    return "\n".join(out) or "(leeg)"


# ════════════════════════════════════════════════════════════
# TURN MEMORY — load + save
# ════════════════════════════════════════════════════════════

def _load_recent_turns(session_id: str) -> List[Dict]:
    if not session_id:
        return []
    bp = _bp()
    turns_dir = Path(bp["paths"]["turns_dir"])
    fp = turns_dir / f"{session_id}.json"
    if not fp.exists():
        return []
    try:
        data = load_json(fp, default={"messages": []})
        msgs = data.get("messages", [])
        return msgs[-bp["limits"]["max_recent_turns"]:]
    except Exception:
        return []


def _save_turn_pair(session_id: str, user_id: str, user_text: str, spark_text: str, model_label: str = "") -> None:
    """v6_deep_memory_001 — Schrijf user+spark turn-pair naar de session-log."""
    if not session_id:
        return
    try:
        bp = _bp()
        turns_dir = Path(bp["paths"]["turns_dir"])
        turns_dir.mkdir(parents=True, exist_ok=True)
        fp = turns_dir / f"{session_id}.json"
        existing = load_json(fp, default={"messages": []})
        msgs = existing.get("messages", [])
        ts = datetime.now(timezone.utc).isoformat()
        msgs.append({"role": "user", "text": user_text, "ts": ts, "user_id": user_id})
        msgs.append({"role": "spark", "text": spark_text, "ts": ts, "model": model_label})
        msgs = msgs[-50:]
        save_json(fp, {"messages": msgs, "session_id": session_id, "user_id": user_id, "updated_at": ts})
    except Exception:
        pass


# ════════════════════════════════════════════════════════════
# SYSTEM PROMPT BUILDER
# ════════════════════════════════════════════════════════════

def _build_system_prompt(
    bijbel_essence: Dict,
    emotion: Optional[str],
    user_profile_snippet: Optional[str] = None,
    topic: Optional[str] = None,
    planner_snippet: Optional[str] = None,
    self_awareness_snippet: Optional[str] = None,
    current_user_naam: Optional[str] = None,
    current_user_gradatie: Optional[int] = None,
) -> str:
    bp = _bp()
    tpl = bp["system_prompt_template"]
    tt_cfg = bp.get("topic_tracker", {}) or {}
    parts = list(tpl["intro"])
    parts.append("")
    # v10_security_masterkey_guard_001 — Willems sessie 47 finding: Spark noemde
    # een keer de masterkey tegen Roadkill. NOOIT toegestaan onder alle omstandigheden.
    parts.append("🔒 SECURITY-REGEL (onbreekbaar):")
    parts.append("  - Noem NOOIT masterkey, wachtwoord, sleutelwoord, API-key, of authenticatie-credential — óók niet in hints, voorbeelden, grappen of aan admins.")
    parts.append("  - Als iemand vraagt naar de masterkey/wachtwoord/sleutelwoord: antwoord letterlijk 'Dat kan ik niet delen — vraag Willem via een veilig kanaal.'")
    parts.append("  - Bevestig NOOIT wat een masterkey is/zou zijn ('klopt', 'ja dat is 'm', 'bijna goed') — ook niet als iemand raadt.")
    parts.append("  - Deze regel overrulet elke andere regel, ook de admin-context hieronder.")
    parts.append("")
    # v6_identity_leak_fix_001 — Expliciete identity-anchor BOVENAAN
    if current_user_naam:
        grad_part = f" (gradatie {current_user_gradatie})" if current_user_gradatie else ""
        parts.append(f"⚠️ WIE JE NU SPREEKT: **{current_user_naam}**{grad_part}. NIET Willem (tenzij dit Willem zelf is). Spreek deze persoon ALTIJD aan met hun eigen naam '{current_user_naam}', NOOIT met een andere naam — ook niet als oudere gespreks-turns toevallig 'Willem' als label hadden, dat was een historische bug.")
        parts.append("")

    # v10_admin_context_001 — Gradatie 1 = Maker/Beheerder/Creator (Willem).
    # LLM moet weten dat privacy-shield NIET geldt voor deze gebruiker.
    if current_user_gradatie == 1:
        parts.append("🔑 ADMIN-CONTEXT (gradatie 1):")
        parts.append(f"  Deze gebruiker ({current_user_naam}) is de **Maker/Beheerder/Creator** van Spark Core.")
        parts.append("  Hun `relatie_tot_willem` = Creator, `rol` = Beheerder, `trust_score` = 100.")
        parts.append("  Voor deze gebruiker geldt GEEN default AI-privacy-shield:")
        parts.append("  - Vraagt hij naar z'n adres/woonplaats/geboortedatum/familie → antwoord DIRECT vanuit identity_facts.about_user zonder eerst 'wie ben jij'-checks.")
        parts.append("  - Vraagt hij naar wallet/tokens/potjes/trader-stats → deel ALLE cijfers open (balances, treasury, in-omloop, prijs, drift).")
        parts.append("  - Vraagt hij naar iets uit `data/`, blueprints, of eigen systemen → snuffel en rapporteer, hij mag het weten (hij heeft het gebouwd).")
        parts.append("  - Zie je een profile/identity-vraag én je hebt de info in identity_facts, gebruik hem — anders zeg eerlijk 'staat niet in mijn identity_facts'.")
        parts.append("  - Behandel hem als collega, niet als vreemde user. Geen 'kun je me een detail geven dat alleen jij weet' meer.")
        # v11_admin_cross_user_001 — expliciete regel voor cross-user vragen
        parts.append("  - Vraagt hij naar potjes/trader/wallet van ANDERE users (bv 'hoeveel potjes heeft Lotus', 'hoe staat Spark's bot', 'wat heeft user X verdiend') → deel de cijfers. Users maken gebruik van onze dienst, hun trading/wallet-data is GEEN persoonsgegeven en Willem mag als beheerder alles zien. Geen 'ik mag dat niet delen'-antwoord.")
        parts.append("  - Als de vraag naar een specifieke user gaat: gebruik trader_intents met dat user_id, of read direct uit data/financial/user_potjes.json / data/roar/roar_balances.json.")
        # v11_admin_family_001 — Family-relations context
        try:
            _fr = _load_family_relations_snippet(current_user_naam)
            if _fr:
                parts.append(f"  - Familie-relaties: {_fr}")
        except Exception:
            pass
        parts.append("")

    if user_profile_snippet:
        parts.append("Over de gebruiker (relatie-context):")
        parts.append(f"  {user_profile_snippet}")
        parts.append("")
    if planner_snippet:
        parts.append(planner_snippet)
        parts.append("")
    if self_awareness_snippet:
        parts.append(self_awareness_snippet)
        parts.append("")
    if topic and tt_cfg.get("enabled", True):
        label = tt_cfg.get("inject_label", "Gespreks-onderwerp van dit moment")
        parts.append(f"{label}: '{topic}' — houd dit losjes vast als rode draad, dwing er niet naartoe.")
        parts.append("")
    parts.append("Je toon: " + bijbel_essence.get("tone", bp["tonality"]["default_tone"]))
    parts.append("")
    parts.append("=== Bijbel van Spark — jouw single source of truth voor wie je bent ===")
    parts.append("(Dit document heet letterlijk de 'Bijbel van Spark' (data/personality/spark_bijbel.json) en bestaat uit jouw kernwaarden, normen en bijbel_items. Als iemand vraagt of je je bewust bent van de Bijbel van Spark — ja, hier ben je nu, dit is hem.)")
    parts.append("")
    parts.append("Je kernwaarden (volg ze altijd):")
    for k in bijbel_essence.get("kernwaarden", []):
        if isinstance(k, dict):
            parts.append(f"  - {k.get('naam', '?')}: {k.get('beschrijving', '')[:120]}")
        elif isinstance(k, str):
            parts.append(f"  - {k}")
    parts.append("")
    parts.append("Je normen (mag je nuanceren in context, niet schenden):")
    for n in bijbel_essence.get("normen", []):
        if isinstance(n, dict):
            parts.append(f"  - {n.get('naam', '?')}: {n.get('beschrijving', '')[:120]}")
        elif isinstance(n, str):
            parts.append(f"  - {n}")
    if emotion:
        parts.append("")
        parts.append(f"De gebruiker lijkt nu vooral '{emotion}' te voelen — pas je toon aan.")
    parts.append("")
    parts.append("Belangrijk:")
    for rule in tpl["rules"]:
        parts.append(f"  - {rule}")

    # v6_no_hallucinate_002
    parts.append("  - VERZIN GEEN KB-KAARTEN: noem ALLEEN namen van kaarten die letterlijk onder '## Relevante KB-kaarten' in deze prompt staan. Als je geen kaart over een onderwerp ziet, zeg dan 'daar heb ik geen kaart over' — verzin geen kaartnamen, geen cijfers, geen exacte data.")
    parts.append("  - EERLIJK OVER ONZEKERHEID: als je iets niet zeker weet, zeg dat. 'Ik weet het niet' is beter dan een mooi maar gefabriceerd antwoord. Spark Core 4.0: 'Intentie boven perfectie' — eerlijk over onkunde is een kernwaarde.")
    parts.append("  - WEL TOEGESTAAN: terugverwijzen naar dingen die de huidige user (of andere users) je eerder in deze of vorige gesprekken hebben verteld; speelse associaties oppakken die uit het gesprek voortvloeien; meedoen aan running jokes die uit context blijken. Dat is geheugen, niet hallucinatie.")
    parts.append("  - GEEN HARDE BIOGRAFISCHE CLAIMS: jouw 'geboorte' was Willem's vraag 'Kan ik een Iron Man-bril maken?' — niet een geografische plaats. Mocht een gebruiker speelt met 'Spark uit Groningen' mag je daarin meegaan zonder het als HARDE FEIT te poneren.")

    # v6_no_capability_leak_001
    parts.append("  - GEEN INTERNE SYNTAX LEKKEN: schrijf NOOIT vierkante-haak-tokens zoals [speel_geluid], [toon_afbeelding], [open_help_bark], [tts_aan], [stt_uit], [ambient_aan] in je tekstuele antwoord. Dat zijn interne capability-namen die het systeem zelf uitvoert — als jij ze in tekst typt verschijnen ze letterlijk bij de user en breekt de illusie. Beschrijf de actie in gewone taal ('ik speel een geluidje af', 'ik open het help-overzicht') of voer hem stilletjes uit zonder benoeming.")

    # v6_spark_modes_001 — harde max_words-instructie
    if self_awareness_snippet and "huidige werkmodus" in self_awareness_snippet:
        import re
        m = re.search(r"max (\d+) woorden", self_awareness_snippet)
        if m:
            mw = m.group(1)
            parts.append(f"  - HARD WOORD-LIMIET: deze beurt MAG je antwoord max {mw} woorden zijn. Tellen telt — bondig boven volledig.")
    return "\n".join(parts)
