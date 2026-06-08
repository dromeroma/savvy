"""Cliente LLM de SavvyAI.

Interfaz abstracta `LLMProvider` + implementación `ClaudeProvider` que llama la
API REST de Anthropic vía httpx (sin SDK extra). La API key se lee CIFRADA desde
`ai_provider_config` (la configura el super admin), nunca de variables de entorno.

Toda llamada devuelve `LLMResult` con uso de tokens para que `usage.py` mida el costo.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.savvy_ai.crypto import decrypt_secret
from src.modules.savvy_ai.models import AiProviderConfig
from src.modules.savvy_ai.pricing import TIER_TO_DEFAULT_MODEL

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"


async def _sleep_backoff(attempt: int, resp: httpx.Response | None) -> None:
    """Espera con backoff exponencial; respeta el header Retry-After si viene."""
    delay = min(2.0 ** attempt, 8.0)  # 1, 2, 4, 8s máx
    if resp is not None:
        ra = resp.headers.get("retry-after")
        if ra:
            try:
                delay = max(delay, float(ra))
            except ValueError:
                pass
    await asyncio.sleep(delay)
ANTHROPIC_VERSION = "2023-06-01"


class AiNotConfiguredError(Exception):
    """El super admin aún no configuró/activó la API key del proveedor."""


@dataclass
class LLMResult:
    text: str
    tool_input: dict[str, Any] | None = None
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    cached_tokens: int = 0
    latency_ms: int = 0
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class LoadedConfig:
    api_key: str
    is_enabled: bool
    models: dict[str, str]
    default_tier: str
    pricing: dict[str, Any]


async def load_provider_config(db: AsyncSession) -> AiProviderConfig | None:
    row = (await db.execute(select(AiProviderConfig).limit(1))).scalar_one_or_none()
    return row


async def resolve_config(db: AsyncSession) -> LoadedConfig:
    cfg = await load_provider_config(db)
    if cfg is None or not cfg.is_enabled or not cfg.api_key_encrypted:
        raise AiNotConfiguredError(
            "La IA no está configurada. El super administrador debe agregar y "
            "activar la API key del proveedor en el panel de plataforma.",
        )
    api_key = decrypt_secret(cfg.api_key_encrypted)
    if not api_key:
        raise AiNotConfiguredError("La API key almacenada no se pudo descifrar.")
    return LoadedConfig(
        api_key=api_key,
        is_enabled=cfg.is_enabled,
        models={
            "haiku": cfg.model_haiku,
            "sonnet": cfg.model_sonnet,
            "opus": cfg.model_opus,
        },
        default_tier=cfg.default_tier,
        pricing=cfg.pricing or {},
    )


class LLMProvider:
    """Interfaz. Cambiar de proveedor = nueva implementación, sin tocar el resto."""

    async def complete(self, *args: Any, **kwargs: Any) -> LLMResult:  # pragma: no cover
        raise NotImplementedError


class ClaudeProvider(LLMProvider):
    def __init__(self, cfg: LoadedConfig):
        self.cfg = cfg

    def model_for_tier(self, tier: str) -> str:
        return self.cfg.models.get(tier) or TIER_TO_DEFAULT_MODEL.get(tier, "claude-sonnet-4-6")

    async def complete(
        self,
        *,
        messages: list[dict[str, Any]],
        tier: str = "sonnet",
        system: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: dict[str, Any] | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.0,
        timeout: float = 60.0,
    ) -> LLMResult:
        model = self.model_for_tier(tier)
        payload: dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }
        if system:
            # Prompt caching: el system prompt (estable y largo) se cachea →
            # baja costo y latencia en llamadas repetidas (~90% en input cacheado).
            payload["system"] = [
                {"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}
            ]
        if tools:
            payload["tools"] = tools
        if tool_choice:
            payload["tool_choice"] = tool_choice

        headers = {
            "x-api-key": self.cfg.api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        }

        # Retries con backoff exponencial para errores transitorios.
        RETRYABLE = {408, 409, 429, 500, 502, 503, 504}
        max_attempts = 4
        started = time.perf_counter()
        last_err: str | None = None
        resp = None
        for attempt in range(max_attempts):
            try:
                async with httpx.AsyncClient(timeout=timeout) as http:
                    resp = await http.post(ANTHROPIC_URL, headers=headers, json=payload)
                if resp.status_code < 400:
                    break
                if resp.status_code in RETRYABLE and attempt < max_attempts - 1:
                    last_err = f"{resp.status_code}: {resp.text[:200]}"
                    await _sleep_backoff(attempt, resp)
                    continue
                raise RuntimeError(f"Anthropic API {resp.status_code}: {resp.text[:500]}")
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                last_err = str(exc)[:200]
                if attempt < max_attempts - 1:
                    await _sleep_backoff(attempt, None)
                    continue
                raise RuntimeError(f"Anthropic API inalcanzable tras {max_attempts} intentos: {last_err}")
        latency_ms = int((time.perf_counter() - started) * 1000)
        if resp is None:
            raise RuntimeError(f"Anthropic API sin respuesta: {last_err}")

        data = resp.json()
        usage = data.get("usage", {}) or {}
        text_parts: list[str] = []
        tool_input: dict[str, Any] | None = None
        for block in data.get("content", []) or []:
            if block.get("type") == "text":
                text_parts.append(block.get("text", ""))
            elif block.get("type") == "tool_use":
                tool_input = block.get("input")

        return LLMResult(
            text="".join(text_parts).strip(),
            tool_input=tool_input,
            model=model,
            input_tokens=int(usage.get("input_tokens", 0)),
            output_tokens=int(usage.get("output_tokens", 0)),
            cached_tokens=int(usage.get("cache_read_input_tokens", 0)),
            latency_ms=latency_ms,
            raw=data,
        )


async def get_provider(db: AsyncSession) -> ClaudeProvider:
    cfg = await resolve_config(db)
    return ClaudeProvider(cfg)
