"""
LLM Router — v6_llm_router_001

Multi-provider OpenAI-compatible LLM router voor Spark's Diep-mode.
Doel: één code-pad voor Groq, Cerebras, OpenRouter, Ollama (lokaal),
of welke OpenAI-compatible API dan ook. Switchen = .env-vars wijzigen.

Architectuur (fallback-chain):
  1. PRIMARY  — LLM_PRIMARY_BASE_URL (bv. Groq)
  2. FALLBACK — LLM_FALLBACK_BASE_URL (bv. Cerebras) — optioneel
  3. EMERGENCY — Emergent Universal Key (Anthropic Claude) — alleen als
                 LLM_EMERGENCY_USE_EMERGENT=true. Kost geld, gebruik spaarzaam.
  4. TEMPLATE — laatste redmiddel, geen LLM-call, return Spark-template.

Bij rate-limit (429) of timeout op PRIMARY: probeer FALLBACK direct.
Bij beide down: korte retry (2s) op PRIMARY, dan EMERGENCY of TEMPLATE.

Op self-host (Odroid) wijzig je .env naar:
  LLM_PRIMARY_BASE_URL=http://localhost:11434/v1
  LLM_PRIMARY_API_KEY=ollama
  LLM_PRIMARY_MODEL=geitje-7b-ultra
en de code blijft identiek.
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Token-stats per call worden hier bijgehouden (admin kan ze later opvragen)
_LAST_STATS: Dict[str, Any] = {}


# =========================================================================
# v13_llm_usage_tracker_001 (sessie 53) — Willem's wens: widget moet
# vooraf zien welke provider bijna vol zit. Elke succesvolle LLM-call
# schrijft tokens weg naar /data/llm/usage_YYYY-MM-DD.json.
# Provider-limits komen uit env-vars zodat admin ze kan tunen (Groq
# on-demand = 100k, dev tier = 200k+).
# =========================================================================
from pathlib import Path as _Path
from datetime import datetime as _dt, timezone as _tz

_USAGE_DIR = _Path(__file__).resolve().parent.parent.parent / "data" / "llm"


def _usage_file_for_today() -> _Path:
    today = _dt.now(_tz.utc).strftime("%Y-%m-%d")
    _USAGE_DIR.mkdir(parents=True, exist_ok=True)
    return _USAGE_DIR / f"usage_{today}.json"


def _log_usage(provider: str, model: str, usage: Dict[str, Any]) -> None:
    """Append tokens naar dagelijkse usage-file. Non-fatal — faalt stil.
    v13: bij providers zonder usage-info (bv. Emergent SDK) wordt tenminste
    het aantal calls geteld zodat je activiteit ziet."""
    total = int((usage or {}).get("total_tokens") or 0)
    try:
        from modules.core.storage import load_json, save_json
        fp = _usage_file_for_today()
        today = _dt.now(_tz.utc).strftime("%Y-%m-%d")
        data = load_json(fp, default={"date": today, "providers": {}})
        p = data["providers"].setdefault(provider, {
            "tokens": 0, "calls": 0, "model": model, "last_call": None,
        })
        p["tokens"] += total  # 0 als provider geen tokens rapporteert
        p["calls"] += 1
        p["model"] = model
        p["last_call"] = _dt.now(_tz.utc).isoformat()
        # Reset error-state bij een succesvolle call
        p["last_error"] = None
        p["last_error_ts"] = None
        p["failed_calls"] = int(p.get("failed_calls", 0))
        save_json(fp, data)
    except Exception as e:
        logger.debug("[llm_usage] log failed: %s", e)


def _log_failure(provider: str, model: str, error: str) -> None:
    """v13c_llm_failure_log_001 (sessie 54) — log failed calls per provider
    zodat het widget kan tonen 'Cerebras: 402 quota op' i.p.v. 'geen data'
    als een provider vandaag alleen maar geweigerd heeft.
    """
    try:
        from modules.core.storage import load_json, save_json
        fp = _usage_file_for_today()
        today = _dt.now(_tz.utc).strftime("%Y-%m-%d")
        data = load_json(fp, default={"date": today, "providers": {}})
        p = data["providers"].setdefault(provider, {
            "tokens": 0, "calls": 0, "model": model, "last_call": None,
        })
        # Classificeer error kort
        err_str = (error or "")
        e_lc = err_str.lower()
        if "402" in err_str or "payment required" in e_lc or "quota" in e_lc:
            summary = "402 quota/betaling vereist"
        elif "429" in err_str or "rate_limit" in e_lc or "rate limit" in e_lc:
            summary = "429 tokens-per-day-limiet bereikt"
        elif "401" in err_str or "unauthorized" in e_lc or "invalid api key" in e_lc:
            summary = "401 ongeldige API-key"
        elif "timeout" in e_lc:
            summary = "timeout"
        else:
            summary = err_str[:120]
        p["last_error"] = summary
        p["last_error_ts"] = _dt.now(_tz.utc).isoformat()
        p["failed_calls"] = int(p.get("failed_calls", 0)) + 1
        p["model"] = model
        save_json(fp, data)
    except Exception as e:
        logger.debug("[llm_usage] failure log failed: %s", e)


def get_usage_today() -> Dict[str, Any]:
    """Return usage-snapshot van vandaag incl. limits + %-progressie.
    Publieke API voor /api/llm/usage/today endpoint."""
    from modules.core.storage import load_json
    today = _dt.now(_tz.utc).strftime("%Y-%m-%d")
    data = load_json(_usage_file_for_today(), default={"date": today, "providers": {}})

    # Provider-metadata + limits uit env of defaults
    def _limit(env_key: str, default: Optional[int]) -> Optional[int]:
        try:
            v = int(os.environ.get(env_key, "").strip() or 0)
            return v if v > 0 else default
        except (TypeError, ValueError):
            return default

    provider_meta = {
        "primary": {
            "naam": f"Groq ({os.environ.get('LLM_PRIMARY_MODEL', 'openai/gpt-oss-120b')})",
            # v13c_widget_limit_fix_001 (sessie 54) — Groq on_demand tier is
            # feitelijk 200k tokens/dag (bron: error-response 'Limit 200000').
            # De oude default (100k) toonde 140% terwijl echte usage <100% was.
            "limit": _limit("LLM_PRIMARY_TPD_LIMIT", 200000),
            "tier": os.environ.get("LLM_PRIMARY_TIER", "on_demand"),
        },
        "fallback": {
            "naam": f"Cerebras ({os.environ.get('LLM_FALLBACK_MODEL', 'gpt-oss-120b')})",
            "limit": _limit("LLM_FALLBACK_TPD_LIMIT", None),
            "tier": os.environ.get("LLM_FALLBACK_TIER", "quota"),
        },
        "emergent": {
            "naam": "Emergent LLM Key",
            "limit": None,
            "tier": "noodrem",
            "note": "activeert alleen bij écht nood (alle providers op quota)",
        },
    }

    providers = []
    for prov_id, meta in provider_meta.items():
        stats = data["providers"].get(prov_id, {})
        used = int(stats.get("tokens", 0))
        limit = meta["limit"]
        pct = (100.0 * used / limit) if (limit and used) else 0.0
        providers.append({
            "id": prov_id,
            "naam": meta["naam"],
            "used": used,
            "calls": int(stats.get("calls", 0)),
            "limit": limit,
            "pct": round(pct, 1),
            "tier": meta["tier"],
            "note": meta.get("note"),
            "last_call": stats.get("last_call"),
            # v13c_llm_failure_log_001 — toon last_error zodat widget "Cerebras:
            # 402 quota op" laat zien i.p.v. het cryptische "geen data".
            "last_error": stats.get("last_error"),
            "last_error_ts": stats.get("last_error_ts"),
            "failed_calls": int(stats.get("failed_calls", 0)),
        })

    return {
        "date": today,
        "providers": providers,
        "generated_at": _dt.now(_tz.utc).isoformat(),
    }


@dataclass
class ProviderConfig:
    name: str
    base_url: str
    api_key: str
    model: str

    @property
    def configured(self) -> bool:
        return bool(self.base_url and self.api_key and self.model)


# v13_model_alias_self_heal_001 (sessie 53) — Willem's productie had nog
# `llama-3.3-70b-versatile` in env, dat model is 16-aug 2025 door Groq
# gedeprecateerd → elke call gaf 404. Als code een gedeprecateerd model
# tegenkomt, swap 'em naar de vervanger. Productie werkt zo direct na
# redeploy zonder dat env-vars aangepast hoeven te worden.
_DEPRECATED_MODEL_ALIAS = {
    # Groq deprecations (bron: https://console.groq.com/docs/deprecations)
    "llama-3.3-70b-versatile": "openai/gpt-oss-120b",
    "llama-3.1-70b-versatile": "openai/gpt-oss-120b",
    "llama3-70b-8192": "openai/gpt-oss-120b",
    "mixtral-8x7b-32768": "openai/gpt-oss-120b",
}


def _resolve_model(model: str) -> str:
    """Vervang gedeprecateerde modelnamen automatisch door de current recommended.
    Logt bij eerste substitutie zodat admin het in de logs ziet."""
    if not model:
        return model
    replacement = _DEPRECATED_MODEL_ALIAS.get(model.strip())
    if replacement:
        logger.warning(
            "[llm_router] Model '%s' is deprecated → auto-swap naar '%s' "
            "(v13_model_alias_self_heal_001)", model, replacement,
        )
        return replacement
    return model


def _get_provider(prefix: str, default_name: str) -> ProviderConfig:
    return ProviderConfig(
        name=default_name,
        base_url=os.environ.get(f"LLM_{prefix}_BASE_URL", "").strip(),
        api_key=os.environ.get(f"LLM_{prefix}_API_KEY", "").strip(),
        model=_resolve_model(os.environ.get(f"LLM_{prefix}_MODEL", "").strip()),
    )


def list_providers() -> List[ProviderConfig]:
    """Geeft de actieve provider-chain terug (in volgorde)."""
    chain: List[ProviderConfig] = []
    primary = _get_provider("PRIMARY", "primary")
    fallback = _get_provider("FALLBACK", "fallback")
    if primary.configured:
        chain.append(primary)
    if fallback.configured:
        chain.append(fallback)
    return chain


def get_last_stats() -> Dict[str, Any]:
    return dict(_LAST_STATS)


# ============================================================
# v10_llm_response_cache_001 — Response cache (5 min TTL)
# ============================================================
import hashlib as _hashlib
from collections import OrderedDict as _OD

_CACHE: "_OD[str, Dict[str, Any]]" = _OD()
_CACHE_MAX = 200
_CACHE_TTL_SEC = 300  # 5 minuten
_CACHE_STATS = {"hits": 0, "misses": 0, "stores": 0}


def _cache_key(messages: List[Dict[str, str]], temperature: float) -> str:
    """Hash op system+last_user+temperature — identieke context = identiek antwoord."""
    sys_msg = next((m.get("content", "") for m in messages if m.get("role") == "system"), "")
    last_user = next((m.get("content", "") for m in reversed(messages) if m.get("role") == "user"), "")
    raw = f"{sys_msg}|{last_user}|{temperature:.2f}"
    return _hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _cache_lookup(messages: List[Dict[str, str]], temperature: float) -> Optional[Dict[str, Any]]:
    key = _cache_key(messages, temperature)
    entry = _CACHE.get(key)
    if not entry:
        return None
    if time.time() - entry["stored_at"] > _CACHE_TTL_SEC:
        _CACHE.pop(key, None)
        return None
    _CACHE.move_to_end(key)  # LRU touch
    return dict(entry["result"])


def _cache_store(messages: List[Dict[str, str]], temperature: float, result: Dict[str, Any]) -> None:
    if not result.get("success") or not result.get("text"):
        return
    key = _cache_key(messages, temperature)
    _CACHE[key] = {"stored_at": time.time(), "result": dict(result)}
    _CACHE_STATS["stores"] += 1
    _CACHE.move_to_end(key)
    while len(_CACHE) > _CACHE_MAX:
        _CACHE.popitem(last=False)


def get_cache_stats() -> Dict[str, Any]:
    """Voor Kladblok LLM Token widget — toont besparing."""
    tot = _CACHE_STATS["hits"] + _CACHE_STATS["misses"]
    return {
        "hits": _CACHE_STATS["hits"],
        "misses": _CACHE_STATS["misses"],
        "stores": _CACHE_STATS["stores"],
        "entries": len(_CACHE),
        "max_entries": _CACHE_MAX,
        "ttl_seconds": _CACHE_TTL_SEC,
        "hit_rate_pct": round((_CACHE_STATS["hits"] / tot * 100), 1) if tot else 0.0,
    }


def clear_cache() -> Dict[str, Any]:
    n = len(_CACHE)
    _CACHE.clear()
    return {"cleared": n}


async def _call_openai_compat(
    provider: ProviderConfig,
    messages: List[Dict[str, str]],
    *,
    temperature: float = 0.7,
    max_tokens: int = 1024,
    timeout: float = 30.0,
) -> Dict[str, Any]:
    """Doe één call naar een OpenAI-compatible endpoint."""
    from openai import AsyncOpenAI
    client = AsyncOpenAI(
        base_url=provider.base_url,
        api_key=provider.api_key,
        timeout=timeout,
    )
    t0 = time.time()
    try:
        resp = await client.chat.completions.create(
            model=provider.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        latency = time.time() - t0
        choice = resp.choices[0]
        text = (choice.message.content or "").strip()
        usage = getattr(resp, "usage", None)
        usage_dict = {}
        if usage is not None:
            usage_dict = {
                "prompt_tokens": getattr(usage, "prompt_tokens", None),
                "completion_tokens": getattr(usage, "completion_tokens", None),
                "total_tokens": getattr(usage, "total_tokens", None),
            }
        return {
            "success": True,
            "text": text,
            "provider": provider.name,
            "model": provider.model,
            "latency_s": round(latency, 3),
            "usage": usage_dict,
        }
    except Exception as ex:
        latency = time.time() - t0
        # Detecteer rate-limit voor sneller fallback
        is_rate_limit = "429" in str(ex) or "rate" in str(ex).lower()
        return {
            "success": False,
            "error": str(ex),
            "provider": provider.name,
            "model": provider.model,
            "latency_s": round(latency, 3),
            "rate_limited": is_rate_limit,
        }


async def _try_emergent_emergency(
    messages: List[Dict[str, str]],
    *,
    temperature: float,
    max_tokens: int,
    true_emergency: bool = False,
) -> Dict[str, Any]:
    """v13_emergent_nood_nood_001 (sessie 53) — Emergent Universal Key wordt gebruikt als:
       (A) admin heeft 'em expliciet aangezet (`LLM_EMERGENCY_USE_EMERGENT=true`), OF
       (B) `true_emergency=True` — d.w.z. álle andere providers faalden met
           quota/rate-limit/budget errors (echte nood-nood zoals Willem 't formuleerde).
    In alle andere gevallen: skip. Zo blijft de key veilig van dagelijkse calls
    maar vangt hij wél op als productie in code-rood staat.
    """
    forced_on = os.environ.get("LLM_EMERGENCY_USE_EMERGENT", "false").lower() == "true"
    if not (forced_on or true_emergency):
        return {"success": False, "error": "emergency_disabled", "provider": "emergent"}
    key = os.environ.get("EMERGENT_LLM_KEY", "").strip()
    if not key:
        return {"success": False, "error": "no_emergent_key", "provider": "emergent"}
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        # Bouw één UserMessage uit de laatste user-turn (Emergent SDK is iets minder flexibel)
        sys_msg = next((m["content"] for m in messages if m["role"] == "system"), "")
        last_user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        chat = (LlmChat(api_key=key, session_id=f"emergency-{int(time.time())}",
                        system_message=sys_msg)
                .with_model("anthropic", "claude-sonnet-4-6"))
        t0 = time.time()
        msg = UserMessage(text=last_user)
        text = await chat.send_message(msg)
        return {
            "success": True,
            "text": (text or "").strip(),
            "provider": "emergent",
            "model": "claude-sonnet-4-6",
            "latency_s": round(time.time() - t0, 3),
            "usage": {},
        }
    except Exception as ex:
        return {"success": False, "error": str(ex), "provider": "emergent"}


async def chat_complete(
    messages: List[Dict[str, str]],
    *,
    temperature: float = 0.7,
    max_tokens: int = 1024,
    timeout: float = 30.0,
    use_cache: bool = True,
) -> Dict[str, Any]:
    """Probeer providers in volgorde tot er één lukt.

    v10_llm_response_cache_001 — Zelfde-vraag-zelfde-antwoord cache (5 min TTL).
    Willem's idee sessie 47: bespaart tokens bij herhaalde vragen (dev-cycli,
    typo-retry, "wacht wat zei je ook alweer?").

    Cache-key = sha256(system_msg + last_user_msg + temperature).
    Cache-scope: globaal (niet per-user) omdat identieke system+user context per
    definitie tot zelfde antwoord leidt. TTL: 5 min. Max 200 entries (LRU-ish).

    Return: {success, text, provider, model, latency_s, usage, tried[], from_cache?}
    """
    global _LAST_STATS
    tried: List[Dict[str, Any]] = []

    # === CACHE-CHECK ===
    if use_cache:
        cache_hit = _cache_lookup(messages, temperature)
        if cache_hit:
            _CACHE_STATS["hits"] += 1
            cache_hit["from_cache"] = True
            cache_hit["tried"] = [{"provider": "cache", "ok": True, "latency_s": 0.0}]
            _LAST_STATS = cache_hit
            return cache_hit
        _CACHE_STATS["misses"] += 1

    chain = list_providers()

    if not chain:
        logger.warning("[llm_router] No providers configured — alleen emergency.")

    # Probeer elke provider in de chain
    for provider in chain:
        result = await _call_openai_compat(
            provider, messages,
            temperature=temperature, max_tokens=max_tokens, timeout=timeout,
        )
        # v13s_llm_tpm_auto_trim_001 — Bij 413 (Request too large / rate_limit_exceeded op
        # tokens per minute) probeer 1× opnieuw met de helft van de non-system messages
        # geknipt. Voorkomt all_providers_failed als de deep-history de prompt te groot maakt.
        if (not result["success"]) and ("413" in str(result.get("error", "")) or "rate_limit_exceeded" in str(result.get("error", "")).lower()):
            non_sys = [m for m in messages if m.get("role") != "system"]
            if len(non_sys) > 2:
                keep_n = max(1, len(non_sys) // 2)
                trimmed = [m for m in messages if m.get("role") == "system"] + non_sys[-keep_n:]
                logger.warning(
                    "[llm_router] %s 413/TPM overshoot — retry met getrimde context (%d → %d msgs)",
                    provider.name, len(messages), len(trimmed),
                )
                result = await _call_openai_compat(
                    provider, trimmed,
                    temperature=temperature, max_tokens=max_tokens, timeout=timeout,
                )
        tried.append({
            "provider": provider.name,
            "model": provider.model,
            "ok": result["success"],
            "latency_s": result.get("latency_s"),
            "error": result.get("error"),
        })
        if result["success"]:
            result["tried"] = tried
            _LAST_STATS = result
            _log_usage(provider.name, provider.model, result.get("usage") or {})
            if use_cache:
                _cache_store(messages, temperature, result)
            return result
        # v13c_llm_failure_log_001 — log de faal-status per provider zodat
        # widget kan tonen 'Cerebras: 402 quota op' i.p.v. 'geen data'.
        _log_failure(provider.name, provider.model, result.get("error") or "unknown")
        logger.warning("[llm_router] %s faalde: %s", provider.name, result.get("error"))

    # Alles gefaald → check of het écht nood-nood is (quota/rate-limit op alle providers).
    # v13_emergent_nood_nood_001: alleen dán mag Emergent invallen — anders niet.
    def _is_quota_error(err: str) -> bool:
        e = (err or "").lower()
        return any(x in e for x in [
            "429", "402", "quota", "rate_limit", "rate limit",
            "budget", "tokens per day", "tpd", "insufficient",
        ])
    all_quota = tried and all(_is_quota_error(t.get("error", "")) for t in tried if not t.get("ok"))

    emergency = await _try_emergent_emergency(
        messages, temperature=temperature, max_tokens=max_tokens,
        true_emergency=all_quota,
    )
    tried.append({
        "provider": "emergent",
        "model": emergency.get("model"),
        "ok": emergency["success"],
        "latency_s": emergency.get("latency_s"),
        "error": emergency.get("error"),
    })
    emergency["tried"] = tried
    _LAST_STATS = emergency
    if emergency["success"]:
        _log_usage("emergent", emergency.get("model") or "emergent", emergency.get("usage") or {})
        if use_cache:
            _cache_store(messages, temperature, emergency)
        return emergency

    return {
        "success": False,
        "error": "all_providers_failed",
        "tried": tried,
        # v13_llm_router_diagnostics_001 (sessie 53) — Willem: "all_providers_failed
        # zegt niks op productie". Bij falen: toon exact welke env-vars ontbreken
        # zodat admin direct weet wat te configureren. Preview vs productie
        # verschilt vaak alleen in .env → deze hint bespaart support-tickets.
        "hint": _diagnose_missing_keys(),
    }


def _diagnose_missing_keys() -> str:
    """Return mensen-leesbare hint over welke LLM-keys ontbreken."""
    import os as _os
    checks = [
        ("LLM_PRIMARY_API_KEY", "Primary LLM provider (Groq). Verkrijgbaar via https://console.groq.com/keys."),
        ("LLM_PRIMARY_BASE_URL", "Base URL voor primary (bv. https://api.groq.com/openai/v1)."),
        ("LLM_PRIMARY_MODEL", "Model-naam voor primary (bv. openai/gpt-oss-120b)."),
        ("LLM_FALLBACK_API_KEY", "Secondary LLM provider (Cerebras). Optioneel maar aangeraden."),
        ("EMERGENT_LLM_KEY", "Emergent Universal Key (emergency fallback). Alleen actief als LLM_EMERGENCY_USE_EMERGENT=true."),
    ]
    missing = []
    for env_name, desc in checks:
        if not _os.environ.get(env_name, "").strip():
            missing.append(f"{env_name}: {desc}")
    if not missing:
        return "Alle keys aanwezig — provider-call zelf faalde (netwerk, budget of rate-limit). Check LLM-router logs."
    return "Missende env-vars op deze omgeving: " + " | ".join(missing)
