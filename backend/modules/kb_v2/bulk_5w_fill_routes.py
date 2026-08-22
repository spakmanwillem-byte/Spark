"""v12_5w_bulk_fill_001 — Bulk 5W-Filler voor onvolledige kaarten in lades.

Willem's opdracht (sessie 56d):
> "Bekijk de 347 onvolledige kaarten. Vul per kaart de lege W/H-velden in op basis
>  van de bestaande content en tags. Geen nieuwe kaarten, geen UI. Alleen de
>  ontbrekende context aanvullen."

Verschil met bestaande /cards/{id}/llm-generate (llm_generate_routes.py):
  - Die werkt op INBOX-kaarten (nog niet gealloceerd) en verplaatst ze naar lade.
  - DEZE werkt op kaarten IN lades die al bestaan maar 5W/lagen missen.
  - DEZE vult ALLEEN ontbrekende velden — bestaande content blijft intact.

Autonomie-scheiding: Willem's expliciete goedkeuring: "LLM doet zware werk, ik scan
achteraf". Elke wijziging wordt gelogd in curation_history.json.

---

📌 STATUS SINDS SESSIE 53 (v13_semantic_lookup_001):

Deze bulk-filler is NIET meer de dagelijkse route voor gap-vulling.
Nieuwe standaard-flow: chat-retrieval met live gap-detectie.

  gebruiker vraagt Spark iets
      ↓
  semantic_lookup vindt relevante kaart
      ↓
  kaart heeft ws5-gap? → Spark meldt dat in antwoord + vraagt aanvulling
      ↓
  Willem antwoordt → PATCH /api/kb/v2/cards/{id} vult W in
      ↓
  volgende sessie: gap dicht

Voordelen chat-flow t.o.v. bulk-filler:
  ✓ Menselijke waarheid ipv LLM-gok
  ✓ Alleen kaarten die er nu toe doen krijgen aandacht
  ✓ Zelf-lerende loop (Emmy's punt): meer gesprek → meer kennis → betere vragen
  ✓ Verifieerbaar per veld

DEZE endpoint blijft actief als BATCH/IMPORT-TOOL:
  • bij massa-import van nieuwe kaarten (bv. via KB v2 migratie)
  • als eenmalige "eerste-boost" voordat chat-flow overneemt
  • als admin-fallback als retrieval te weinig gap-detectie doet

Niet meer scheduler-getriggerd. Niet meer default UI-knop.
Verwante shadow-vragen queue (personalia_intrek_service.py) doet vergelijkbare
gap-vulling maar voor kennis over ANDERE users — andere richting van
dezelfde motor (Willem sessie 53).
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel

from modules.core.storage import load_json, save_json

router = APIRouter(prefix="/kb/v2/curation", tags=["kb-v2-curation-5w-bulk"])

V2 = Path("/app/backend/data/knowledge/v2")
LADES = ["voelen", "spreken", "weten", "doen"]
REQUIRED_5W = ["wie", "wat", "wanneer", "waar", "waarom", "hoe"]
PLACEHOLDER = {"", "?", "nog te vullen", "onbekend", "n.v.t.", "n/a"}
HISTORY_FILE = V2 / "curation_history.json"


def _is_placeholder(v) -> bool:
    if not isinstance(v, str):
        return True
    return v.strip().lower() in PLACEHOLDER


def _missing_fields(card: Dict) -> Dict[str, List[str]]:
    """Return {'5w': [leeg-velden], 'lagen': [leeg-lagen]}."""
    ws = card.get("ws5", {}) or {}
    lagen = card.get("lagen", {}) or {}
    missing_5w = [k for k in REQUIRED_5W if _is_placeholder(ws.get(k))]
    missing_lagen = [f"laag{i}" for i in (1, 2, 3, 4)
                     if _is_placeholder(lagen.get(f"laag{i}"))
                     or len((lagen.get(f"laag{i}") or "").strip()) < 20]
    return {"5w": missing_5w, "lagen": missing_lagen}


def _build_fill_prompt(card: Dict, missing: Dict[str, List[str]]) -> list:
    """LLM krijgt alleen ontbrekende velden om in te vullen, met bestaande content
    als context. Volgt _meta.json v1.2 field-semantiek."""
    begrip = card.get("begrip", "")
    lade = card.get("lade", "")
    tags = card.get("tags", [])
    lagen = card.get("lagen", {}) or {}
    ws = card.get("ws5", {}) or {}

    # Alleen bestaande (niet-lege) velden meesturen als context
    existing_lagen = {k: v for k, v in lagen.items()
                      if isinstance(v, str) and len(v.strip()) >= 20 and not _is_placeholder(v)}
    existing_ws = {k: v for k, v in ws.items()
                   if isinstance(v, str) and not _is_placeholder(v)}

    sys = (
        "Je bent een Nederlandstalige KB-card curator voor Spark. "
        "Je taak: vul UITSLUITEND de aangewezen ontbrekende velden in op basis van de bestaande content. "
        "Wees consistent met bestaande lagen en tags. "
        "Geef ALLEEN geldig JSON terug, geen markdown, geen commentaar."
    )

    parts = [
        f'Begrip: "{begrip}"',
        f'Lade: {lade}',
        f'Tags: {tags}',
    ]
    if existing_lagen:
        parts.append("Bestaande lagen (BLIJVEN, niet aanpassen):")
        for k in sorted(existing_lagen.keys()):
            parts.append(f'  {k}: "{existing_lagen[k]}"')
    if existing_ws:
        parts.append("Bestaande 5W (BLIJVEN, niet aanpassen):")
        for k, v in existing_ws.items():
            parts.append(f'  {k}: "{v}"')

    parts.append("\nVul UITSLUITEND deze ontbrekende velden in:")
    schema = {}
    if missing.get("lagen"):
        parts.append("Lagen (schrijf inhoudelijk, geen ChatGPT-clichés):")
        for laag in missing["lagen"]:
            if laag == "laag1":
                parts.append('  - laag1: 1 krachtige zin, kernbetekenis (12-25 woorden)')
                schema["laag1"] = "..."
            elif laag == "laag2":
                parts.append('  - laag2: 3-4 zinnen, context + voorbeelden (50-90 woorden)')
                schema["laag2"] = "..."
            elif laag == "laag3":
                parts.append('  - laag3: uitgebreide achtergrond (150-220 woorden)')
                schema["laag3"] = "..."
            elif laag == "laag4":
                parts.append('  - laag4: diepere reflectie + nuances (220-320 woorden)')
                schema["laag4"] = "..."
    if missing.get("5w"):
        parts.append("5W-velden (concreet, geen abstracties):")
        hints = {
            "wie": "concreet subject/actor",
            "wat": "concrete actie of object",
            "wanneer": "moment, situatie, trigger",
            "waar": "plek, context, domein",
            "waarom": "beweegreden, doel",
            "hoe": "werkwijze, methode",
        }
        for k in missing["5w"]:
            parts.append(f'  - {k}: {hints.get(k, "beschrijf")}')
        schema["ws5"] = {k: "..." for k in missing["5w"]}

    parts.append(f"\nRetourneer alleen dit JSON-schema (met échte waardes):\n{json.dumps(schema, indent=2, ensure_ascii=False)}")

    return [
        {"role": "system", "content": sys},
        {"role": "user", "content": "\n".join(parts)},
    ]


def _append_history(entries: List[Dict]):
    hist = load_json(HISTORY_FILE, default={"entries": []})
    hist.setdefault("entries", []).extend(entries)
    save_json(HISTORY_FILE, hist)


class BulkFillResult(BaseModel):
    success: bool
    processed: int
    filled: int
    skipped: int
    errors: List[Dict]
    remaining_incomplete: int
    dry_run: bool


@router.post("/5w-fill-bulk")
async def bulk_5w_fill(limit: int = Query(20, ge=1, le=100),
                       dry_run: bool = False,
                       lade: str = Query("all", regex="^(all|voelen|spreken|weten|doen)$")):
    """v12_5w_bulk_fill_001 — Vul lege 5W/lagen op bestaande lade-kaarten via LLM.

    Params:
      - limit: max kaarten per call (1-100, default 20)
      - dry_run: alleen prompts genereren, niks opslaan
      - lade: filter op één lade of 'all'

    Werkwijze:
      1. Selecteer onvolledige kaarten (leeg 5W of laag <20 chars)
      2. Per kaart: identificeer ontbrekende velden
      3. LLM krijgt bestaande content + expliciete lijst wat te vullen
      4. Response wordt gemerged in kaart (bestaande velden BLIJVEN)
      5. Elke wijziging → curation_history.json
    """
    from modules.chat import llm_router

    lades_to_scan = [lade] if lade != "all" else LADES
    processed, filled, skipped = 0, 0, 0
    errors = []
    history_entries = []

    # Verzamel alle onvolledige kaarten (met lade-info)
    candidates = []
    for l in lades_to_scan:
        fp = V2 / f"knowledge_v2_{l}.json"
        d = load_json(fp, default={"kaarten": []})
        for idx, c in enumerate(d.get("kaarten", [])):
            miss = _missing_fields(c)
            if miss["5w"] or miss["lagen"]:
                candidates.append({"lade": l, "idx": idx, "card": c, "missing": miss, "fp": fp})
    total_incomplete = len(candidates)

    # Beperk tot limit
    batch = candidates[:limit]

    # Load-eens per lade voor efficiente saves
    lade_docs = {}

    for item in batch:
        processed += 1
        c = item["card"]
        miss = item["missing"]
        try:
            messages = _build_fill_prompt(c, miss)
            if dry_run:
                history_entries.append({
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "card_id": c.get("id"),
                    "begrip": c.get("begrip"),
                    "lade": item["lade"],
                    "action": "dry_run_prompt",
                    "missing": miss,
                })
                skipped += 1
                continue

            resp = await llm_router.chat_complete(messages, temperature=0.3, max_tokens=2400, timeout=45.0)
            if not resp.get("success"):
                errors.append({"card_id": c.get("id"), "error": resp.get("error", "unknown")})
                skipped += 1
                continue

            text = resp.get("text", "").strip()
            if text.startswith("```"):
                text = re.sub(r"^```(?:json)?\s*\n?", "", text)
                text = re.sub(r"\n?```\s*$", "", text)

            try:
                proposal = json.loads(text)
            except Exception as ex:
                errors.append({"card_id": c.get("id"), "error": f"json_parse: {ex}", "output": text[:200]})
                skipped += 1
                continue

            # Merge alleen ontbrekende velden — bestaande content blijft
            changed_fields = []
            for laag_key in ("laag1", "laag2", "laag3", "laag4"):
                if laag_key in miss.get("lagen", []) and proposal.get(laag_key):
                    c.setdefault("lagen", {})[laag_key] = proposal[laag_key]
                    changed_fields.append(laag_key)
            if proposal.get("ws5"):
                for k in miss.get("5w", []):
                    if proposal["ws5"].get(k):
                        c.setdefault("ws5", {})[k] = proposal["ws5"][k]
                        changed_fields.append(f"ws5.{k}")

            # Footnote
            c.setdefault("footnote", {})
            c["footnote"]["llm_5w_filled_at"] = datetime.now(timezone.utc).isoformat()
            c["footnote"]["llm_5w_provider"] = resp.get("provider")

            # Aggregeer in lade-doc voor save
            lade_docs.setdefault(item["lade"], load_json(item["fp"], default={"kaarten": []}))
            lade_docs[item["lade"]]["kaarten"][item["idx"]] = c

            history_entries.append({
                "ts": datetime.now(timezone.utc).isoformat(),
                "card_id": c.get("id"),
                "begrip": c.get("begrip"),
                "lade": item["lade"],
                "action": "5w_filled",
                "fields_filled": changed_fields,
                "provider": resp.get("provider"),
            })
            filled += 1
        except Exception as ex:
            errors.append({"card_id": c.get("id"), "error": f"exception: {ex}"})
            skipped += 1

    # Bulk save per lade
    if not dry_run:
        for l, doc in lade_docs.items():
            save_json(V2 / f"knowledge_v2_{l}.json", doc)
        if history_entries:
            _append_history(history_entries)

    return BulkFillResult(
        success=True,
        processed=processed,
        filled=filled,
        skipped=skipped,
        errors=errors[:10],
        remaining_incomplete=max(0, total_incomplete - filled),
        dry_run=dry_run,
    )


@router.get("/5w-fill-status")
async def bulk_5w_status():
    """Rapporteer hoeveel onvolledige kaarten er nog zijn + laatste 20 log-entries."""
    counts = {}
    total = 0
    for l in LADES:
        d = load_json(V2 / f"knowledge_v2_{l}.json", default={"kaarten": []})
        c = sum(1 for k in d.get("kaarten", []) if any(_missing_fields(k).values()))
        counts[l] = c
        total += c
    hist = load_json(HISTORY_FILE, default={"entries": []})
    recent = list(reversed(hist.get("entries", [])))[:20]
    return {
        "success": True,
        "total_incomplete": total,
        "per_lade": counts,
        "history_total": len(hist.get("entries", [])),
        "recent_entries": recent,
    }
