"""Tarifas de modelos para calcular el costo de cada llamada (USD por 1M tokens).

Editables desde el super admin (columna `pricing` en ai_provider_config); estos
son los valores por defecto. El costo se mide SIEMPRE — base del modelo de negocio.
"""

from __future__ import annotations

from decimal import Decimal

# USD por 1,000,000 tokens. (input, output, cached_input)
DEFAULT_PRICING: dict[str, dict[str, float]] = {
    "claude-haiku-4-5":  {"input": 1.00,  "output": 5.00,   "cached": 0.10},
    "claude-sonnet-4-6": {"input": 3.00,  "output": 15.00,  "cached": 0.30},
    "claude-opus-4-8":   {"input": 15.00, "output": 75.00,  "cached": 1.50},
}

TIER_TO_DEFAULT_MODEL = {
    "haiku": "claude-haiku-4-5",
    "sonnet": "claude-sonnet-4-6",
    "opus": "claude-opus-4-8",
}


def compute_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
    cached_tokens: int = 0,
    pricing_override: dict | None = None,
) -> Decimal:
    """Costo en USD de una llamada. Usa tarifa override (de la BD) si existe."""
    table = (pricing_override or {}).get(model) or DEFAULT_PRICING.get(model)
    if not table:
        # Modelo desconocido: no rompemos, costo 0 pero queda registrado el uso.
        return Decimal("0")
    inp = Decimal(str(table.get("input", 0))) * Decimal(input_tokens) / Decimal(1_000_000)
    out = Decimal(str(table.get("output", 0))) * Decimal(output_tokens) / Decimal(1_000_000)
    cac = Decimal(str(table.get("cached", 0))) * Decimal(cached_tokens) / Decimal(1_000_000)
    return (inp + out + cac).quantize(Decimal("0.000001"))
