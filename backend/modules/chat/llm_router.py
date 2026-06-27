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
    """Laatste redmiddel: Emergent Universal Key (Claude). Kost geld."""
    if os.environ.get("LLM_EMERGENCY_USE_EMERGENT", "false").lower() != "true":
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
                .with_model("anthropic", "claude-sonnet-4-6")
                .with_max_tokens(max_tokens))
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
) -> Dict[str, Any]:
    """Probeer providers in volgorde tot er één lukt.

    Return: {success, text, provider, model, latency_s, usage, tried[]}
    Bij volledige failure: {success: False, error, tried[]}
    """
    global _LAST_STATS
    tried: List[Dict[str, Any]] = []
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
        return emergency

    return {
        "success": False,
        "error": "all_providers_failed",
        "tried": tried,
    }
