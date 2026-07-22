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


@dataclass
class ProviderConfig:
    name: str
    base_url: str
    api_key: str
    model: str

    @property
    def configured(self) -> bool:
        return bool(self.base_url and self.api_key and self.model)


def _get_provider(prefix: str, default_name: str) -> ProviderConfig:
    return ProviderConfig(
        name=default_name,
        base_url=os.environ.get(f"LLM_{prefix}_BASE_URL", "").strip(),
        api_key=os.environ.get(f"LLM_{prefix}_API_KEY", "").strip(),
        model=os.environ.get(f"LLM_{prefix}_MODEL", "").strip(),
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
) -> Dict[str, Any]:
    """v10_llm_emergency_default_on_001 — Laatste redmiddel: Emergent Universal Key (Claude).
    Default AAN sinds sessie 47 (Groq TPD-limit haalde Spark vandaag onderuit).
    Kost credits van Emergent LLM key. Uit te zetten via env: LLM_EMERGENCY_USE_EMERGENT=false.
    """
    if os.environ.get("LLM_EMERGENCY_USE_EMERGENT", "true").lower() != "true":
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
            if use_cache:
                _cache_store(messages, temperature, result)
            return result
        logger.warning("[llm_router] %s faalde: %s", provider.name, result.get("error"))

    # Alles gefaald → emergency
    emergency = await _try_emergent_emergency(
        messages, temperature=temperature, max_tokens=max_tokens,
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
        if use_cache:
            _cache_store(messages, temperature, emergency)
        return emergency

    return {
        "success": False,
        "error": "all_providers_failed",
        "tried": tried,
    }
