import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import httpx

from modules.core.storage import load_json, save_json

DATA_ROOT = Path(os.environ.get("SPARK_DATA_DIR") or Path(__file__).resolve().parents[2] / "data")
CONN_FILE = DATA_ROOT / "system" / "connections.json"

# Definitie van elke verbinding: velden + welke env-var erachter zit.
# secret=True → gemaskeerd in GET, password-veld in UI.
CONNECTION_DEFS: List[Dict] = [
    {
        "id": "llm_primary", "naam": "Primaire LLM (Groq)", "type": "llm",
        "doel": "Spark's hoofd-taalmodel voor Diep/compose. OpenAI-compatibel endpoint.",
        "velden": [
            {"key": "base_url", "label": "Base URL", "env": "LLM_PRIMARY_BASE_URL", "secret": False, "hint": "https://api.groq.com/openai/v1"},
            {"key": "api_key", "label": "API key", "env": "LLM_PRIMARY_API_KEY", "secret": True},
            {"key": "model", "label": "Model", "env": "LLM_PRIMARY_MODEL", "secret": False, "hint": "openai/gpt-oss-120b"},
        ],
        "test": "openai_models",
    },
    {
        "id": "llm_fallback", "naam": "Reserve-LLM (bv. Ollama lokaal)", "type": "llm",
        "doel": "Tweede taalmodel als de primaire op quota zit. Ollama: http://localhost:11434/v1, key mag 'ollama' zijn.",
        "velden": [
            {"key": "base_url", "label": "Base URL", "env": "LLM_FALLBACK_BASE_URL", "secret": False, "hint": "http://localhost:11434/v1"},
            {"key": "api_key", "label": "API key", "env": "LLM_FALLBACK_API_KEY", "secret": True},
            {"key": "model", "label": "Model", "env": "LLM_FALLBACK_MODEL", "secret": False, "hint": "llama3.1:8b"},
        ],
        "test": "openai_models",
    },
    {
        "id": "emergent_key", "naam": "Emergent Universal Key", "type": "llm",
        "doel": "TTS, STT (Whisper), foto-analyse en LLM-noodrem. Werkt ook buiten Emergent (betaald plan).",
        "velden": [
            {"key": "api_key", "label": "Universal key", "env": "EMERGENT_LLM_KEY", "secret": True, "hint": "sk-emergent-…"},
        ],
        "test": "key_present",
    },
    {
        "id": "bitvavo", "naam": "Bitvavo (per gebruiker)", "type": "exchange",
        "doel": "Trader-koppeling. Sleutels staan per gebruiker in users/<id>/settings.json → Profiel → Instellingen. Hier alleen testen.",
        "velden": [],
        "per_user": True,
        "test": "bitvavo_balance",
    },
    {
        "id": "ports", "naam": "Poorten & adressen", "type": "system",
        "doel": "Backend 8001, frontend 3000. Frontend praat via REACT_APP_BACKEND_URL (frontend/.env). Alleen ter info — wijzigen vraagt herstart.",
        "velden": [
            {"key": "cors_origins", "label": "CORS origins", "env": "CORS_ORIGINS", "secret": False, "hint": "*"},
        ],
        "readonly_info": {"backend_port": 8001, "frontend_port": 3000},
        "test": None,
    },
]

_DEF_BY_ID = {d["id"]: d for d in CONNECTION_DEFS}
# Originele .env-waarden bij opstart, zodat "leegmaken in JSON" netjes terugvalt op .env.
_ENV_BASELINE = {f["env"]: os.environ.get(f["env"]) for d in CONNECTION_DEFS for f in d["velden"]}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load() -> Dict:
    return load_json(CONN_FILE, default={"connections": {}, "updated_at": None})


def _mask(v: str) -> str:
    if not v:
        return ""
    return ("•" * 6) + v[-4:] if len(v) > 4 else "•" * len(v)


def effective_value(conn_id: str, key: str) -> str:
    """JSON-waarde wint; leeg → .env."""
    stored = (_load().get("connections", {}).get(conn_id) or {}).get(key)
    if stored:
        return str(stored)
    env = next((f["env"] for f in _DEF_BY_ID[conn_id]["velden"] if f["key"] == key), None)
    return (os.environ.get(env, "") if env else "").strip()


def apply_to_env() -> int:
    """JSON-waarde → os.environ (override .env); leeg → terug naar .env-baseline. Return aantal overrides."""
    n = 0
    data = _load().get("connections", {})
    for d in CONNECTION_DEFS:
        vals = data.get(d["id"]) or {}
        for f in d["velden"]:
            v = vals.get(f["key"])
            if v:
                os.environ[f["env"]] = str(v)
                n += 1
            else:
                base = _ENV_BASELINE.get(f["env"])
                if base is None:
                    os.environ.pop(f["env"], None)
                else:
                    os.environ[f["env"]] = base
    return n


def list_connections() -> List[Dict]:
    data = _load()
    stored_all = data.get("connections", {})
    out = []
    for d in CONNECTION_DEFS:
        stored = stored_all.get(d["id"]) or {}
        velden = []
        for f in d["velden"]:
            in_json = bool(stored.get(f["key"]))
            val = effective_value(d["id"], f["key"])
            velden.append({
                "key": f["key"], "label": f["label"], "secret": f["secret"], "hint": f.get("hint", ""),
                "env": f["env"], "value": _mask(val) if f["secret"] else val,
                "filled": bool(val), "source": "json" if in_json else ("env" if val else "leeg"),
            })
        out.append({
            "id": d["id"], "naam": d["naam"], "type": d["type"], "doel": d["doel"],
            "velden": velden, "per_user": d.get("per_user", False),
            "readonly_info": d.get("readonly_info"), "testable": bool(d.get("test")),
            "updated_at": stored.get("_updated_at"), "last_test": stored.get("_last_test"),
        })
    return out


def save_values(conn_id: str, values: Dict[str, str], user_id: str) -> Dict:
    d = _DEF_BY_ID.get(conn_id)
    if not d:
        raise KeyError(conn_id)
    allowed = {f["key"] for f in d["velden"]}
    data = _load()
    cur = data.setdefault("connections", {}).setdefault(conn_id, {})
    for k, v in values.items():
        if k not in allowed:
            continue
        v = (v or "").strip()
        if v == "":
            cur.pop(k, None)  # leeg = terug naar .env
        else:
            cur[k] = v
    cur["_updated_at"] = _now()
    cur["_updated_by"] = user_id
    data["updated_at"] = _now()
    save_json(CONN_FILE, data)
    apply_to_env()
    return cur


def _record_test(conn_id: str, result: Dict) -> None:
    data = _load()
    cur = data.setdefault("connections", {}).setdefault(conn_id, {})
    cur["_last_test"] = {"ok": result.get("ok"), "at": _now(), "detail": result.get("detail")}
    save_json(CONN_FILE, data)


def test_connection(conn_id: str, user_id: str = "user-001") -> Dict:
    d = _DEF_BY_ID.get(conn_id)
    if not d:
        raise KeyError(conn_id)
    kind = d.get("test")
    try:
        if kind == "openai_models":
            base = effective_value(conn_id, "base_url").rstrip("/")
            key = effective_value(conn_id, "api_key")
            if not base:
                res = {"ok": False, "detail": "Geen base URL ingevuld"}
            else:
                r = httpx.get(f"{base}/models", headers={"Authorization": f"Bearer {key or 'none'}"}, timeout=8)
                if r.status_code == 200:
                    models = [m.get("id") for m in (r.json().get("data") or [])]
                    want = effective_value(conn_id, "model")
                    res = {"ok": True, "detail": f"{len(models)} modellen bereikbaar" + ("" if not want or want in models or not models else f" — let op: '{want}' niet in lijst"), "models": models[:12]}
                else:
                    res = {"ok": False, "detail": f"HTTP {r.status_code}: {r.text[:120]}"}
        elif kind == "key_present":
            key = effective_value(conn_id, "api_key")
            res = {"ok": bool(key), "detail": "Key aanwezig" if key else "Geen key ingevuld"}
        elif kind == "bitvavo_balance":
            from modules.trade.bitvavo_client import _load_credentials, get_balance
            if not _load_credentials(user_id):
                res = {"ok": False, "detail": f"Geen Bitvavo-sleutels voor {user_id} (Profiel → Instellingen)"}
            else:
                bal = get_balance(user_id)
                res = {"ok": isinstance(bal, list), "detail": f"{len(bal)} assets op balans" if isinstance(bal, list) else str(bal)[:120]}
        else:
            res = {"ok": None, "detail": "Niet testbaar (alleen informatie)"}
    except Exception as ex:
        res = {"ok": False, "detail": f"{type(ex).__name__}: {str(ex)[:140]}"}
    _record_test(conn_id, res)
    return res


# ---------- v14_connections_keyfile_001 — sleutelbestand (.env) export/import ----------
_ENV_TO_FIELD = {f["env"]: (d["id"], f["key"]) for d in CONNECTION_DEFS for f in d["velden"]}


def export_env_text() -> str:
    """Alle verbindingen als .env-tekst (huidige effectieve waarden). Bewaar veilig."""
    lines = ["# Spark sleutelbestand — gegenereerd " + _now(), "# Upload dit in Widget Kladblok → Verbindingen op een nieuwe Spark-installatie.", ""]
    for d in CONNECTION_DEFS:
        if not d["velden"]:
            continue
        lines.append(f"# {d['naam']}")
        for f in d["velden"]:
            lines.append(f"{f['env']}={effective_value(d['id'], f['key'])}")
        lines.append("")
    return "\n".join(lines)


def import_env_text(content: str, user_id: str) -> Dict:
    """Parse KEY=WAARDE regels; bekende keys → connections.json. Onbekende keys worden genoemd, niet opgeslagen."""
    per_conn: Dict[str, Dict[str, str]] = {}
    unknown, skipped = [], 0
    for raw in (content or "").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip().removeprefix("export ").strip()
        val = val.strip().strip('"').strip("'")
        if key not in _ENV_TO_FIELD:
            unknown.append(key)
            continue
        if not val:
            skipped += 1
            continue
        conn_id, fkey = _ENV_TO_FIELD[key]
        per_conn.setdefault(conn_id, {})[fkey] = val
    for conn_id, vals in per_conn.items():
        save_values(conn_id, vals, user_id)
    return {"filled": sum(len(v) for v in per_conn.values()), "connections": sorted(per_conn), "unknown_keys": unknown, "empty_skipped": skipped}
