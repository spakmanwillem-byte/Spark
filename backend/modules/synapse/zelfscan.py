"""
v14_zelfscan_001 (Willem 20-10) — Zelfscan: kan Spark zijn eigen data zien?
Rapport per container (_meta.json): footnote? blueprint_ref? doel echt ingevuld? Blauwdruk meer dan stub?
Backfill (admin): lege footnote → "legacy_backfill" met bestandsdatum en vertrouwen 0.5; doel + blueprint_ref via
de bestaande enricher; blauwdruk-stubs krijgen het echte doel i.p.v. "(x — geen doel-omschrijving)".
Roadmap: P0 "metadata backfill" (sessie 55) + Emmy's "MetaAuditJob".
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from modules.core.storage import load_json, save_json
from .enricher import APP_ROOT, MEMORY_BLUEPRINTS, META_FILENAME, derive_doel, enrich_all
from .schema import now_iso

DATA_ROOT = APP_ROOT / "backend" / "data"
SKIP_PARTS = {"_backup", "_backups", "_archive", "_deleted", "_preview", "__pycache__", "node_modules", ".git"}


def _alle_metas() -> List[Path]:
    out = []
    for p in APP_ROOT.rglob(META_FILENAME):
        if any(part.startswith(tuple(SKIP_PARTS)) for part in p.parts):
            continue
        out.append(p)
    return sorted(out)


def _doel_leeg(doel: str) -> bool:
    d = (doel or "").strip()
    return not d or d.startswith("(") or d.startswith("Skelet — ") or d.startswith("Data-store voor ")


def _blueprint_is_stub(ref: str) -> bool:
    if not ref:
        return True
    p = APP_ROOT / ref.lstrip("/")
    if not p.is_file():
        return True
    txt = p.read_text(encoding="utf-8", errors="ignore")
    return "geen doel-omschrijving" in txt or ("_(vul aan)_" in txt and len(txt) < 1500)


def rapport() -> Dict[str, Any]:
    items, tel = [], {"totaal": 0, "code_modules": 0, "zonder_footnote": 0, "zonder_blueprint": 0, "doel_leeg": 0, "blueprint_stub": 0, "compleet": 0}
    for mp in _alle_metas():
        meta = load_json(mp, default={})
        rel = str(mp.parent).replace(str(APP_ROOT) + "/", "")
        fn_leeg = not (meta.get("footnote") or meta.get("footnote_meta"))
        bp = meta.get("blueprint_ref") or ""
        is_code = rel.startswith("backend/modules") or rel.startswith("frontend/src")
        doel_txt = (meta.get("doel") or "").strip()
        # data-containers: "Data-store voor …" is een prima doel; blauwdruk alleen voor code-modules
        doel_ok = (not _doel_leeg(doel_txt)) or (not is_code and doel_txt.startswith("Data-store voor "))
        row = {"pad": rel, "naam": meta.get("naam") or mp.parent.name, "container_type": meta.get("container_type"),
               "code": is_code, "footnote": not fn_leeg, "blueprint_ref": bool(bp), "doel": doel_ok,
               "blueprint_stub": _blueprint_is_stub(bp) if bp else None}
        tel["totaal"] += 1
        tel["code_modules"] += is_code
        tel["zonder_footnote"] += fn_leeg
        tel["zonder_blueprint"] += (is_code and not bp)
        tel["doel_leeg"] += not row["doel"]
        tel["blueprint_stub"] += bool(bp) and row["blueprint_stub"]
        bp_ok = (row["blueprint_ref"] and not row["blueprint_stub"]) if is_code else True
        if row["footnote"] and row["doel"] and bp_ok:
            tel["compleet"] += 1
        items.append(row)
    tel["pct_compleet"] = round(100 * tel["compleet"] / tel["totaal"]) if tel["totaal"] else 0
    return {"success": True, "generated_at": now_iso(), "tellers": tel, "containers": items}


def _refresh_blueprint_doel(ref: str, doel: str) -> bool:
    p = APP_ROOT / ref.lstrip("/")
    if not p.is_file() or _doel_leeg(doel):
        return False
    txt = p.read_text(encoding="utf-8", errors="ignore")
    nieuw = re.sub(r"## 🎯 Doel\n\(.*?\)\n", f"## 🎯 Doel\n{doel}\n", txt, count=1, flags=re.S)
    if nieuw == txt:
        nieuw = re.sub(r"## 🎯 Doel\n_\(nog niet beschreven\)_\n", f"## 🎯 Doel\n{doel}\n", txt, count=1)
    if nieuw != txt:
        p.write_text(nieuw, encoding="utf-8")
        return True
    return False


def backfill(door: str = "zelfscan") -> Dict[str, Any]:
    """Alleen lege velden; nooit bestaande tekst overschrijven. Backup per _meta in .bak_zelfscan."""
    stats = {"footnote_gevuld": 0, "blueprint_doel_ververst": 0}
    enrich_stats = enrich_all(write_blueprints=True, overwrite_existing_doel=False)
    for mp in _alle_metas():
        meta = load_json(mp, default={})
        gewijzigd = False
        if not (meta.get("footnote") or meta.get("footnote_meta")):
            try:
                mtime = datetime.fromtimestamp(mp.parent.stat().st_mtime, tz=timezone.utc).isoformat()
            except OSError:
                mtime = now_iso()
            meta["footnote_meta"] = {"bron": "legacy_backfill", "aangemaakt_door": door, "aangemaakt_op": mtime,
                                     "vertrouwen": 0.5, "backfill_op": now_iso()}
            meta["footnote"] = f"legacy_backfill · map bestond al op {mtime[:10]} · vertrouwen 0.5"
            gewijzigd = True
            stats["footnote_gevuld"] += 1
        if meta.get("blueprint_ref") and _refresh_blueprint_doel(meta["blueprint_ref"], meta.get("doel", "")):
            stats["blueprint_doel_ververst"] += 1
        if gewijzigd:
            bak = mp.with_suffix(".json.bak_zelfscan")
            if not bak.exists():
                bak.write_text(mp.read_text(encoding="utf-8"), encoding="utf-8")
            save_json(mp, meta)
    stats.update({f"enricher_{k}": v for k, v in enrich_stats.items()})
    return {"success": True, "stats": stats, "rapport": rapport()["tellers"]}
