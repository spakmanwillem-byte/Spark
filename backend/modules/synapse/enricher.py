"""
Synapse — Auto-enricher (v6_synapse_002)
==========================================
Vult automatisch het `doel` veld van een _meta.json door:
  1. Te lezen uit `__init__.py` docstring (eerste paragraaf na ===-banner)
  2. Bij geen Python: top JSDoc / comment-blok uit eerste .js/.jsx file
  3. Bij data-dirs: kijk in `_index.json` of typische `schema` key

Genereert ook blueprint-stubs in /app/memory/blueprints/{naam}.md
indien `blueprint_ref` leeg is.

Beschermt user-edits: vult alleen wanneer doel nog default/leeg is.
"""
import re
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

from modules.core.storage import load_json, save_json
from .schema import now_iso

APP_ROOT = Path("/app")
MEMORY_BLUEPRINTS = APP_ROOT / "memory" / "blueprints"
META_FILENAME = "_meta.json"


# ============================================================
# DOCSTRING EXTRACTIE
# ============================================================
def _extract_py_docstring(folder: Path) -> Optional[str]:
    """Lees module-level docstring uit __init__.py."""
    init = folder / "__init__.py"
    if not init.exists():
        # Probeer routes.py of <naam>.py
        for cand in (folder / "routes.py", folder / "service.py", folder / f"{folder.name}.py"):
            if cand.exists():
                init = cand
                break
        else:
            return None
    try:
        text = init.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None
    # Triple-quoted docstring eerst
    m = re.search(r'^"""(.*?)"""', text, re.DOTALL)
    if not m:
        m = re.search(r"^'''(.*?)'''", text, re.DOTALL)
    if not m:
        return None
    raw = m.group(1).strip()
    return raw


def _extract_js_topcomment(folder: Path) -> Optional[str]:
    """Lees JSDoc-blok uit eerste .js/.jsx file in de folder."""
    for ext in (".js", ".jsx"):
        for fp in sorted(folder.glob(f"*{ext}")):
            try:
                text = fp.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            # /** ... */ block aan begin
            m = re.search(r'/\*\*?(.*?)\*/', text, re.DOTALL)
            if m:
                raw = m.group(1).strip()
                # Strip leading * per regel
                lines = [re.sub(r"^\s*\*\s?", "", ln) for ln in raw.split("\n")]
                cleaned = "\n".join(lines).strip()
                if len(cleaned) >= 20:
                    return cleaned
    return None


def _first_meaningful_paragraph(text: str) -> str:
    """Pak de eerste paragraaf na de banner (lijntjes/== etc)."""
    if not text:
        return ""
    lines = text.split("\n")
    out = []
    started = False
    for ln in lines:
        s = ln.strip()
        # Skip banner-lijnen
        if re.match(r"^[=\-_*#]{5,}$", s):
            continue
        # Skip title-lines met allemaal capitals + ==
        if re.match(r"^.+?\s*\([^)]+\)\s*$", s) and "===" in (lines[lines.index(ln)+1] if lines.index(ln)+1 < len(lines) else ""):
            continue
        if not s:
            if started:
                break
            continue
        # Skip enkele technische headers
        if s.lower().startswith(("werking:", "concept (", "module:", "files in deze module:", "endpoints:", "routes:")):
            break
        if s.startswith(">"):
            continue  # blockquote
        if s.startswith(("- ", "* ", "•")):
            if not started:
                continue  # bullets vooraan negeren
            break  # bullets na alinea = einde
        out.append(s)
        started = True
        if len(" ".join(out)) > 220:
            break
    para = " ".join(out).strip()
    # Knip op eerste zin als hij erg lang is
    if len(para) > 240:
        sents = re.split(r"(?<=[.!?])\s+", para)
        para = sents[0] if sents else para[:240]
    return para


def derive_doel(folder: Path, container_type: str) -> Optional[str]:
    """Heuristiek: leid een goed 'doel'-veld af uit de bestanden in deze map."""
    if container_type == "dir":
        # Python eerst, dan JS
        ds = _extract_py_docstring(folder)
        if ds:
            return _first_meaningful_paragraph(ds)
        ds = _extract_js_topcomment(folder)
        if ds:
            return _first_meaningful_paragraph(ds)
    elif container_type == "data":
        # Voor data-mappen: kijk naar typische structuur
        items = list(folder.iterdir())
        json_files = [f for f in items if f.suffix == ".json" and f.name != META_FILENAME]
        if not json_files:
            return None
        # Beschrijf wat erin zit
        names = [f.stem for f in json_files[:3]]
        return f"Data-store voor {folder.name}: bevat {len(json_files)} JSON-bestanden ({', '.join(names)}{'…' if len(json_files) > 3 else ''})."
    return None


# ============================================================
# BLUEPRINT-STUB GENERATOR
# ============================================================
BLUEPRINT_TEMPLATE = """# Blueprint — {naam}

> Auto-gegenereerde stub door synapse v6_synapse_002.
> Pad: `{path}`
> Gegenereerd op: {ts}

## 🎯 Doel
{doel}

## ✅ Wat werkt al
- _(vul aan)_

## 🔌 Auto-gedetecteerde endpoints
{endpoints_block}

## 📝 TODO / open items
- [ ] _(vul aan)_

## ⚠️ Splitting-trigger
> Als deze map > 4 sub-mappen krijgt of > 10 endpoints, overweeg splitsen.
> Huidig: {file_count} files, {subdir_count} subdirs, {ep_count} endpoints.

## 🔐 Encryption-plan (F2F)
- Status nu: `{enc_status}`
- Wanneer aan: `algorithm = AES-256-GCM`, `key_holder = <owner>`
- Beschermt: _(welke velden zijn privacy-gevoelig?)_

## 🧬 Relaties
- Hangt af van: _(welke modules?)_
- Wordt gebruikt door: _(welke modules?)_
"""


def write_blueprint_stub(meta: Dict[str, Any], path_str: str) -> Optional[str]:
    """Schrijf een blueprint-stub als die nog niet bestaat. Returnt het pad."""
    naam = meta.get("naam") or "unknown"
    blueprint_path = MEMORY_BLUEPRINTS / f"{naam}.md"
    if blueprint_path.exists():
        return str(blueprint_path)
    MEMORY_BLUEPRINTS.mkdir(parents=True, exist_ok=True)
    endpoints = meta.get("endpoints") or []
    endpoints_block = "\n".join(f"- `{e}`" for e in endpoints[:15]) or "- _(geen)_"
    enc = meta.get("encryption") or {}
    enc_status = "🟢 actief" if enc.get("enabled") else "⚪ slot leeg (klaar voor activatie)"
    content = BLUEPRINT_TEMPLATE.format(
        naam=naam,
        path=path_str,
        ts=now_iso()[:19],
        doel=meta.get("doel") or "_(nog niet beschreven)_",
        endpoints_block=endpoints_block,
        file_count=meta.get("file_count", 0),
        subdir_count=meta.get("subdir_count", 0),
        ep_count=len(endpoints),
        enc_status=enc_status,
    )
    blueprint_path.write_text(content, encoding="utf-8")
    return str(blueprint_path)


# ============================================================
# MAIN ENRICH-LOOP
# ============================================================
def enrich_all(write_blueprints: bool = True, overwrite_existing_doel: bool = False) -> Dict[str, Any]:
    """Loop door alle bekende containers in SYNAPSE.json, vul doel + blueprint-stub."""
    from .aggregator import build_synapse, SYNAPSE_FILE
    if not SYNAPSE_FILE.exists():
        build_synapse()
    doc = load_json(SYNAPSE_FILE, default={})

    stats = {
        "doel_filled": 0,
        "doel_skipped_user_edited": 0,
        "doel_failed": 0,
        "blueprints_created": 0,
        "blueprints_skipped": 0,
    }

    for grp, items in doc.get("tree", {}).items():
        for path_str, meta in items.items():
            folder = APP_ROOT / path_str
            if not folder.exists():
                continue
            meta_path = folder / META_FILENAME
            if not meta_path.exists():
                continue
            on_disk = load_json(meta_path, default={})

            # Doel vullen
            current_doel = on_disk.get("doel") or ""
            is_default = (
                not current_doel.strip()
                or current_doel.startswith("(")  # bv "(naam — geen doel-omschrijving)"
                or current_doel.startswith("Skelet — ")
                or current_doel.startswith("Data-store voor ")
            )
            if is_default or overwrite_existing_doel:
                derived = derive_doel(folder, on_disk.get("container_type", "dir"))
                if derived:
                    on_disk["doel"] = derived
                    on_disk["last_touched"] = now_iso()
                    save_json(meta_path, on_disk)
                    meta = on_disk  # gebruik bijgewerkt voor blueprint
                    stats["doel_filled"] += 1
                else:
                    stats["doel_failed"] += 1
            else:
                stats["doel_skipped_user_edited"] += 1

            # Blueprint-stub
            if write_blueprints and not (on_disk.get("blueprint_ref") or "").strip():
                bp_path = write_blueprint_stub(meta, path_str)
                if bp_path:
                    # Link blueprint terug in meta
                    rel = bp_path.replace(str(APP_ROOT) + "/", "")
                    if not on_disk.get("blueprint_ref"):
                        on_disk["blueprint_ref"] = "/" + rel
                        save_json(meta_path, on_disk)
                    stats["blueprints_created"] += 1
                else:
                    stats["blueprints_skipped"] += 1

    # Rebuild aggregator
    build_synapse()
    return stats
