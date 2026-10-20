"""v6_namen_001 — Namen-lade service.

Spark's naam-classificatie. Blueprint-based (geen KB v2 lade) omdat namen
data zijn, geen gedrag.

Categorieen:
  voornaam_man / voornaam_vrouw / voornaam_unisex / achternaam /
  koosnaam / gamertag / onbekend
"""
from __future__ import annotations

from modules.core.paths import SPARK_ROOT  # v14_spark_root_001
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from modules.core.storage import load_json, save_json

BLUEPRINT_PATH = Path(f"{SPARK_ROOT}/backend/data/blueprints/namen.json")
VALID_CATEGORIES = {
    "voornaam_man", "voornaam_vrouw", "voornaam_unisex",
    "achternaam", "koosnaam", "gamertag", "onbekend",
}
_lock = threading.RLock()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load() -> Dict:
    data = load_json(BLUEPRINT_PATH, default={"_meta": {}, "namen": {}})
    if "namen" not in data:
        data["namen"] = {}
    return data


def get_all() -> Dict:
    """Return complete blueprint (meta + namen)."""
    return _load()


def list_names(categorie: Optional[str] = None) -> List[Dict]:
    """Lijst van alle namen, optioneel gefilterd op categorie."""
    data = _load()
    out = []
    for naam, meta in data.get("namen", {}).items():
        if categorie and meta.get("categorie") != categorie:
            continue
        out.append({"naam": naam, **meta})
    out.sort(key=lambda x: x["naam"].lower())
    return out


def get_name(naam: str) -> Optional[Dict]:
    """Case-insensitive lookup."""
    data = _load()
    for k, v in data.get("namen", {}).items():
        if k.lower() == naam.lower():
            return {"naam": k, **v}
    return None


def add_name(naam: str, categorie: str, bron: str = "manueel", notities: str = "") -> Dict:
    """Voeg naam toe of update bestaande."""
    naam = (naam or "").strip()
    if not naam:
        return {"success": False, "error": "Naam is leeg"}
    if categorie not in VALID_CATEGORIES:
        return {"success": False, "error": f"Ongeldige categorie: {categorie}", "valid": sorted(VALID_CATEGORIES)}

    with _lock:
        data = _load()
        # Normalise: titlecase
        key = naam[:1].upper() + naam[1:] if len(naam) > 1 else naam.upper()
        # Vind bestaande (case-insensitive)
        existing_key = None
        for k in data["namen"]:
            if k.lower() == key.lower():
                existing_key = k
                break
        if existing_key:
            data["namen"][existing_key].update({
                "categorie": categorie,
                "notities": notities or data["namen"][existing_key].get("notities", ""),
                "bijgewerkt": _now(),
            })
            action = "updated"
            saved_key = existing_key
        else:
            data["namen"][key] = {
                "categorie": categorie,
                "bron": bron,
                "toegevoegd": _now(),
                "notities": notities,
            }
            action = "created"
            saved_key = key
        save_json(BLUEPRINT_PATH, data)
    return {"success": True, "action": action, "naam": saved_key, "categorie": categorie}


def delete_name(naam: str) -> Dict:
    with _lock:
        data = _load()
        found_key = None
        for k in list(data.get("namen", {}).keys()):
            if k.lower() == naam.lower():
                found_key = k
                break
        if not found_key:
            return {"success": False, "error": f"Naam '{naam}' niet gevonden"}
        del data["namen"][found_key]
        save_json(BLUEPRINT_PATH, data)
    return {"success": True, "verwijderd": found_key}


def search_names(query: str, max_results: int = 10) -> List[Dict]:
    """Fuzzy-lite search op naam + categorie."""
    if not query:
        return []
    q = query.lower().strip()
    data = _load()
    hits = []
    for naam, meta in data.get("namen", {}).items():
        n_lower = naam.lower()
        score = 0
        if n_lower == q:
            score = 100
        elif n_lower.startswith(q):
            score = 80
        elif q in n_lower:
            score = 60
        elif q in (meta.get("categorie") or "").lower():
            score = 40
        elif q in (meta.get("notities") or "").lower():
            score = 30
        if score > 0:
            hits.append((score, {"naam": naam, **meta}))
    hits.sort(key=lambda x: -x[0])
    return [h[1] for h in hits[:max_results]]


def classify_via_llm(naam: str) -> Dict:
    """Vraag LLM om categorie te bepalen voor een onbekende naam.

    Retourneert {'success': bool, 'categorie': str, 'reasoning': str} maar
    schrijft NIET naar de lade — dat is aan de caller (avoid auto-pollution).
    """
    naam = (naam or "").strip()
    if not naam:
        return {"success": False, "error": "Naam is leeg"}
    if len(naam) > 40:
        return {"success": False, "error": "Naam te lang"}

    try:
        from modules.chat.llm_router import call_llm
    except Exception as e:
        return {"success": False, "error": f"LLM router niet beschikbaar: {e}"}

    prompt = (
        "Je bent een Nederlandse naamclassificatie-expert. Bepaal welke categorie het beste past "
        f"voor het woord '{naam}'.\n\n"
        "Kies EXACT één van:\n"
        "  voornaam_man, voornaam_vrouw, voornaam_unisex, achternaam, koosnaam, gamertag, onbekend\n\n"
        "Antwoord alleen met de categorie-naam, geen uitleg."
    )
    try:
        resp = call_llm(
            system="Antwoord altijd met exact één woord uit de gegeven categorie-lijst.",
            user=prompt,
            max_tokens=20,
            temperature=0.1,
        )
        # call_llm retour-structuur varieert; probeer bekende velden
        text = ""
        if isinstance(resp, dict):
            text = (resp.get("text") or resp.get("content") or resp.get("response") or "").strip()
        elif isinstance(resp, str):
            text = resp.strip()
        text_low = text.lower().replace(".", "").replace(",", "").strip()
        # Vind eerste matching categorie
        for cat in VALID_CATEGORIES:
            if cat in text_low:
                return {"success": True, "categorie": cat, "llm_raw": text}
        return {"success": False, "error": "Geen geldige categorie in LLM-antwoord", "llm_raw": text}
    except Exception as e:
        return {"success": False, "error": f"LLM-call mislukte: {e}"}


def stats() -> Dict:
    """Aantal namen per categorie."""
    data = _load()
    counts: Dict[str, int] = {c: 0 for c in VALID_CATEGORIES}
    for meta in data.get("namen", {}).values():
        c = meta.get("categorie", "onbekend")
        counts[c] = counts.get(c, 0) + 1
    return {"totaal": sum(counts.values()), "per_categorie": counts}
