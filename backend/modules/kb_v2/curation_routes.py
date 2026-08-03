"""v12_kb_curation_suite_001 — KB-Curatie Suite voor Sessie 55.

Drie samenhangende tools voor structurele KB-hygiëne:

1. **5W-Filler**: LLM-voorstel voor kaarten met lege ws5 (680 stuks).
2. **Duplicate-Merger**: samenvoegen van kaarten met identiek begrip (32 paren).
3. **Lade-Reclassificatie**: Regel 1/2 uit spark_tag_curatie_public.json toepassen
   op mis-geplaatste kaarten (~59 verdacht).

Alle endpoints admin-only (gradatie ≤ 2). Read-only tot admin klikt Accept.
Gebruikt bestaande llm_router (Groq/Cerebras) voor LLM-calls.

Blauwdruk-referentie: /data/knowledge/v2/spark_tag_curatie_public.json → sectie 8.
"""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Optional, Dict, Any, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from modules.core.storage import load_json, save_json
from modules.kb_v2.service import V2_DIR as _V2_DIR_PATH

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/kb/v2/curation", tags=["kb-curation"])

LADES = ["voelen", "spreken", "weten", "doen"]
REQUIRED_5W = {"wie", "wat", "wanneer", "waar", "waarom", "hoe"}

# Regel 1 detectie: infinitief NL werkwoord (min 4 chars, eindigt op -en).
# Uitgezonderd: bekende zn die toevallig op -en eindigen.
_ZN_OP_EN = {
    "leven", "wapen", "teken", "midden", "oosten", "westen", "zuiden", "noorden",
    "tuin", "trein", "begin", "kussen", "keten", "kraken", "zeven",
}
_INFINITIEF_RE = re.compile(r"^.{3,}en$")


def _lade_path(lade: str) -> Path:
    return _V2_DIR_PATH / f"knowledge_v2_{lade}.json"


def _load_all_cards():
    """Yield (lade, card_dict, lade_data_dict) voor alle kaarten."""
    out = []
    for lade in LADES:
        d = load_json(_lade_path(lade), default={"kaarten": []})
        for c in d.get("kaarten", []):
            out.append((lade, c, d))
    return out


def _missing_5w(card: Dict) -> List[str]:
    ws = card.get("ws5", {}) or {}
    filled = {k for k, v in ws.items() if isinstance(v, str) and v.strip()}
    return sorted(REQUIRED_5W - filled)


def _require_admin(viewer_id: str) -> None:
    USERS = Path(__file__).parent.parent.parent / "data" / "system" / "users.json"
    users = load_json(USERS, default={"users": []})
    ulist = users.get("users", []) if isinstance(users, dict) else users
    viewer = next((u for u in ulist if u.get("id") == viewer_id), None)
    if not viewer or int(viewer.get("gradatie", 7) or 7) > 2:
        raise HTTPException(403, "Alleen admin (gradatie ≤ 2)")


# ============================================================
# 1. 5W-FILLER
# ============================================================

class Suggest5WBody(BaseModel):
    viewer_id: str


class Apply5WBody(BaseModel):
    viewer_id: str
    ws5: Dict[str, str]  # de goedgekeurde/bewerkte 5W velden


@router.get("/empty-5w")
async def list_empty_5w(limit: int = 50, only_fully_empty: bool = False):
    """Lijst kaarten met (deels) leeg 5W, oplopend gesorteerd op begrip."""
    out = []
    for lade, c, _ in _load_all_cards():
        m = _missing_5w(c)
        if not m:
            continue
        if only_fully_empty and len(m) < 6:
            continue
        out.append({
            "id": c.get("id"),
            "begrip": c.get("begrip"),
            "lade": lade,
            "status": c.get("status"),
            "missing_fields": m,
            "filled_count": 6 - len(m),
            "laag1": (c.get("lagen") or {}).get("laag1", "")[:120],
            "tags_sample": (c.get("tags") or [])[:5],
        })
    out.sort(key=lambda x: (x["filled_count"], x["begrip"] or ""))
    return {
        "success": True,
        "total": len(out),
        "returned": min(limit, len(out)),
        "cards": out[:limit],
    }


@router.post("/5w-suggest/{card_id}")
async def suggest_5w(card_id: str, body: Suggest5WBody):
    """LLM-voorstel voor ws5 op basis van bestaande lagen + tags. Schrijft niks weg."""
    _require_admin(body.viewer_id)
    card = None
    for _, c, _ in _load_all_cards():
        if c.get("id") == card_id:
            card = c
            break
    if not card:
        raise HTTPException(404, f"Kaart {card_id} niet gevonden")

    lagen = card.get("lagen") or {}
    begrip = card.get("begrip", "")
    tags = card.get("tags") or []

    sys_prompt = (
        "Je bent een Nederlandstalige KB-editor voor Spark. Vul de 6 W's + Hoe in voor het "
        "gegeven begrip op basis van bestaande context. Wees concreet, feitelijk, geen 'persoon' "
        "of vage abstracties. Geen markdown, geen uitleg — alleen JSON."
    )
    user_prompt = (
        f"Begrip: '{begrip}'\n"
        f"Laag 1: {lagen.get('laag1', '')}\n"
        f"Laag 2: {lagen.get('laag2', '')}\n"
        f"Tags: {', '.join(tags[:15])}\n\n"
        "Geef JSON in EXACT dit formaat, verder niks:\n"
        "{\n"
        '  "wie": "concreet subject/actor",\n'
        '  "wat": "specifieke kerneigenschap",\n'
        '  "wanneer": "concrete tijd/situatie",\n'
        '  "waar": "concrete plaats/domein",\n'
        '  "waarom": "doel/motivatie/functie",\n'
        '  "hoe": "concrete werking/methode"\n'
        "}"
    )

    from modules.chat import llm_router
    resp = await llm_router.chat_complete(
        [{"role": "system", "content": sys_prompt}, {"role": "user", "content": user_prompt}],
        temperature=0.4, max_tokens=800, timeout=25.0,
    )
    if not resp.get("success"):
        raise HTTPException(503, f"LLM-call mislukt: {resp.get('error')}")

    text = resp.get("text", "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*\n?", "", text)
        text = re.sub(r"\n?```\s*$", "", text)
    try:
        proposal = json.loads(text)
    except Exception as ex:
        raise HTTPException(500, f"LLM gaf geen geldig JSON: {ex}. Output: {text[:200]}")

    return {
        "success": True,
        "card_id": card_id,
        "begrip": begrip,
        "current_ws5": card.get("ws5", {}),
        "proposal": proposal,
        "llm_provider": resp.get("provider"),
    }


@router.post("/5w-apply/{card_id}")
async def apply_5w(card_id: str, body: Apply5WBody):
    """Sla de goedgekeurde ws5 op de kaart op. Merge met bestaande, overschrijf lege slots."""
    _require_admin(body.viewer_id)
    for lade in LADES:
        p = _lade_path(lade)
        d = load_json(p, default={"kaarten": []})
        for c in d.get("kaarten", []):
            if c.get("id") == card_id:
                current = c.get("ws5", {}) or {}
                new = {**current}
                for k in REQUIRED_5W:
                    v = (body.ws5.get(k) or "").strip()
                    if v:
                        new[k] = v
                c["ws5"] = new
                # bookkeeping in footnote
                fn = c.setdefault("footnote", {})
                fn["laatst_bewerkt_door"] = body.viewer_id
                fn.setdefault("curation_history", []).append({
                    "action": "5w_fill",
                    "by": body.viewer_id,
                    "fields": list(body.ws5.keys()),
                })
                save_json(p, d)
                return {"success": True, "card_id": card_id, "lade": lade, "ws5": new}
    raise HTTPException(404, f"Kaart {card_id} niet gevonden")


# ============================================================
# 2. DUPLICATE-MERGER
# ============================================================

class DupeMergeBody(BaseModel):
    viewer_id: str
    keep_card_id: str
    drop_card_id: str


@router.get("/duplicates")
async def list_duplicates():
    """Zoek alle begrippen die 2+ keer voorkomen (in dezelfde of verschillende lades)."""
    by_begrip: Dict[str, List[Dict]] = {}
    for lade, c, _ in _load_all_cards():
        b = (c.get("begrip") or "").strip().lower()
        if not b:
            continue
        by_begrip.setdefault(b, []).append({
            "id": c.get("id"),
            "lade": lade,
            "status": c.get("status"),
            "filled_5w": 6 - len(_missing_5w(c)),
            "n_verbanden": len(c.get("verbanden") or []),
            "laag1": ((c.get("lagen") or {}).get("laag1") or "")[:100],
            "tags_count": len(c.get("tags") or []),
        })
    dupes = [
        {"begrip": b, "count": len(v), "same_lade": len({x["lade"] for x in v}) == 1, "cards": v}
        for b, v in by_begrip.items() if len(v) > 1
    ]
    dupes.sort(key=lambda x: (-x["count"], x["begrip"]))
    return {"success": True, "total": len(dupes), "duplicates": dupes}


@router.post("/duplicate-merge")
async def merge_duplicate(body: DupeMergeBody):
    """Merge twee kaarten: keep_card_id blijft, drop_card_id wordt verwijderd.

    Merge-strategie:
    - keep krijgt union van tags
    - keep krijgt ontbrekende ws5 velden aangevuld uit drop
    - keep krijgt union van verbanden
    - drop wordt verwijderd uit zijn lade
    """
    _require_admin(body.viewer_id)
    keep_ref = drop_ref = None
    for lade in LADES:
        p = _lade_path(lade)
        d = load_json(p, default={"kaarten": []})
        for c in d.get("kaarten", []):
            if c.get("id") == body.keep_card_id:
                keep_ref = (p, d, c, lade)
            if c.get("id") == body.drop_card_id:
                drop_ref = (p, d, c, lade)
    if not keep_ref:
        raise HTTPException(404, f"Keep-kaart {body.keep_card_id} niet gevonden")
    if not drop_ref:
        raise HTTPException(404, f"Drop-kaart {body.drop_card_id} niet gevonden")

    keep_path, keep_data, keep_card, keep_lade = keep_ref
    drop_path, drop_data, drop_card, drop_lade = drop_ref

    # Merge tags (union)
    ktags = keep_card.get("tags") or []
    dtags = drop_card.get("tags") or []
    keep_card["tags"] = sorted(set(ktags) | set(dtags))

    # Merge ws5: vul lege slots van keep uit drop
    k_ws5 = keep_card.get("ws5", {}) or {}
    d_ws5 = drop_card.get("ws5", {}) or {}
    for field in REQUIRED_5W:
        if not (k_ws5.get(field) or "").strip():
            v = (d_ws5.get(field) or "").strip()
            if v:
                k_ws5[field] = v
    keep_card["ws5"] = k_ws5

    # Merge verbanden (union op kaart_id)
    seen = {v.get("kaart_id") for v in (keep_card.get("verbanden") or [])}
    for v in drop_card.get("verbanden") or []:
        if v.get("kaart_id") not in seen and v.get("kaart_id") != body.keep_card_id:
            keep_card.setdefault("verbanden", []).append(v)
            seen.add(v.get("kaart_id"))

    # Footnote-audit
    fn = keep_card.setdefault("footnote", {})
    fn.setdefault("curation_history", []).append({
        "action": "duplicate_merge",
        "by": body.viewer_id,
        "merged_in": body.drop_card_id,
        "from_lade": drop_lade,
    })

    # Verwijder drop-kaart
    drop_data["kaarten"] = [c for c in drop_data.get("kaarten", []) if c.get("id") != body.drop_card_id]

    save_json(keep_path, keep_data)
    if drop_path != keep_path:
        save_json(drop_path, drop_data)

    return {
        "success": True,
        "kept": body.keep_card_id,
        "dropped": body.drop_card_id,
        "keep_lade": keep_lade,
        "drop_lade": drop_lade,
        "final_tags_count": len(keep_card["tags"]),
        "final_5w_filled": 6 - len(_missing_5w(keep_card)),
    }


# ============================================================
# 3. LADE-RECLASSIFICATIE (Regel 1 + 2 uit blauwdruk)
# ============================================================

class LadeMoveBody(BaseModel):
    viewer_id: str
    target_lade: str


def _regel_1_check(begrip: str) -> bool:
    """Regel 1: werkwoord in meervoud/infinitief (-en) → doen-lade."""
    b = begrip.lower().strip()
    if len(b) < 4:
        return False
    if not _INFINITIEF_RE.match(b):
        return False
    if b in _ZN_OP_EN:
        return False
    return True


# Regel 2: bekende proces-zn die volgens Willem's blauwdruk in doen horen.
_PROCES_ZN = {
    "onderhoud", "procedure", "keuze", "actie", "handeling", "reparatie",
    "operatie", "instructie", "beweging", "training", "installatie",
    "montage", "aanleg", "opbouw", "afbraak", "aanpassing", "uitvoering",
}


def _regel_2_check(begrip: str) -> bool:
    return (begrip or "").lower().strip() in _PROCES_ZN


@router.get("/lade-check")
async def lade_check(limit: int = 100):
    """Scan alle kaarten tegen Regel 1 + 2. Return voorstel-lijst voor verplaatsing."""
    proposals = []
    for lade, c, _ in _load_all_cards():
        b = c.get("begrip", "") or ""
        r1 = _regel_1_check(b)
        r2 = _regel_2_check(b)
        if (r1 or r2) and lade != "doen":
            reason = "Regel 1 (werkwoord meervoud → doen)" if r1 else "Regel 2 (proces-zn → doen)"
            proposals.append({
                "id": c.get("id"),
                "begrip": b,
                "current_lade": lade,
                "target_lade": "doen",
                "reason": reason,
                "rule": "regel_1" if r1 else "regel_2",
                "status": c.get("status"),
                "laag1_snippet": ((c.get("lagen") or {}).get("laag1") or "")[:100],
                "tags_sample": (c.get("tags") or [])[:5],
            })
    proposals.sort(key=lambda x: (x["current_lade"], x["begrip"]))
    return {
        "success": True,
        "total": len(proposals),
        "returned": min(limit, len(proposals)),
        "proposals": proposals[:limit],
    }


@router.post("/lade-move/{card_id}")
async def lade_move(card_id: str, body: LadeMoveBody):
    """Verplaats één kaart van huidige lade → target_lade."""
    _require_admin(body.viewer_id)
    if body.target_lade not in LADES:
        raise HTTPException(400, f"target_lade moet zijn: {LADES}")

    src_path = src_data = src_card = None
    for lade in LADES:
        p = _lade_path(lade)
        d = load_json(p, default={"kaarten": []})
        for c in d.get("kaarten", []):
            if c.get("id") == card_id:
                src_path = p
                src_data = d
                src_card = c
                if lade == body.target_lade:
                    return {"success": False, "error": "Kaart staat al in target-lade"}
                break
        if src_card:
            break
    if not src_card:
        raise HTTPException(404, f"Kaart {card_id} niet gevonden")

    # Update kaart-metadata
    src_card["lade"] = body.target_lade
    fn = src_card.setdefault("footnote", {})
    fn.setdefault("curation_history", []).append({
        "action": "lade_move",
        "by": body.viewer_id,
        "from": src_path.stem.replace("knowledge_v2_", ""),
        "to": body.target_lade,
    })

    # Verwijder uit src
    src_data["kaarten"] = [c for c in src_data.get("kaarten", []) if c.get("id") != card_id]
    save_json(src_path, src_data)

    # Voeg toe aan target
    tgt_path = _lade_path(body.target_lade)
    tgt_data = load_json(tgt_path, default={"kaarten": []})
    tgt_data.setdefault("kaarten", []).append(src_card)
    save_json(tgt_path, tgt_data)

    return {
        "success": True,
        "card_id": card_id,
        "moved_to": body.target_lade,
    }


# ============================================================
# GLOBAL SUMMARY (voor Spark Brain KB-Curatie tab)
# ============================================================

@router.get("/summary")
async def curation_summary():
    """Overzicht voor de UI-tab: hoeveel werk staat er?"""
    empty_5w = 0
    partial_5w = 0
    by_begrip: Dict[str, int] = {}
    lade_misplaced = 0

    for lade, c, _ in _load_all_cards():
        m = _missing_5w(c)
        if len(m) == 6:
            empty_5w += 1
        elif m:
            partial_5w += 1
        b = (c.get("begrip") or "").strip().lower()
        if b:
            by_begrip[b] = by_begrip.get(b, 0) + 1
        # lade-check
        if lade != "doen" and (_regel_1_check(c.get("begrip", "")) or _regel_2_check(c.get("begrip", ""))):
            lade_misplaced += 1

    dupe_count = sum(1 for v in by_begrip.values() if v > 1)

    return {
        "success": True,
        "empty_5w": empty_5w,
        "partial_5w": partial_5w,
        "duplicates": dupe_count,
        "lade_misplaced": lade_misplaced,
        "blauwdruk_ref": "/data/knowledge/v2/spark_tag_curatie_public.json § 8_lade_toewijzing_regels",
    }
