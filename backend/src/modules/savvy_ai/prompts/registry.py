"""Registro de prompts versionados.

Cada prompt tiene una `key` y `version` que se registran en ai_usage, para que
el super admin sepa "qué prompts son caros". Cambiar un prompt = nueva versión.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PromptSpec:
    key: str
    version: str
    tier: str
    system: str
    # JSON Schema del tool que fuerza la salida estructurada (structured output)
    output_schema: dict[str, Any]


# ---------------- Extracción de factura de compra (POS) ----------------

INVOICE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "supplier_name": {"type": "string", "description": "Nombre o razón social del proveedor"},
        "supplier_tax_id": {"type": ["string", "null"], "description": "NIT / identificación fiscal"},
        "invoice_number": {"type": ["string", "null"]},
        "invoice_date": {"type": ["string", "null"], "description": "YYYY-MM-DD"},
        "currency": {"type": "string", "default": "COP"},
        "subtotal": {"type": ["number", "null"]},
        "tax": {"type": ["number", "null"]},
        "total": {"type": ["number", "null"]},
        "line_items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "description": {"type": "string"},
                    "sku": {"type": ["string", "null"]},
                    "quantity": {"type": "number"},
                    "unit_cost": {"type": ["number", "null"]},
                    "line_total": {"type": ["number", "null"]},
                },
                "required": ["description", "quantity"],
            },
        },
        "field_confidence": {
            "type": "object",
            "description": "Confianza 0-100 por campo principal",
            "additionalProperties": {"type": "number"},
        },
        "overall_confidence": {"type": "number", "description": "Confianza global 0-100"},
    },
    "required": ["supplier_name", "line_items", "overall_confidence"],
}

INVOICE_PROMPT = PromptSpec(
    key="extraction.purchase_invoice",
    version="v1",
    tier="sonnet",
    system=(
        "Eres un asistente experto en leer facturas de compra de proveedores en "
        "Colombia y Latinoamérica. Extrae los datos con precisión. Si un dato no "
        "aparece, déjalo en null — nunca inventes. Devuelve montos como números sin "
        "separadores de miles. Para cada campo principal estima una confianza 0-100. "
        "Responde SOLO llamando la herramienta de extracción."
    ),
    output_schema=INVOICE_SCHEMA,
)


PROMPTS: dict[str, PromptSpec] = {
    INVOICE_PROMPT.key: INVOICE_PROMPT,
}


def get_prompt(key: str) -> PromptSpec:
    spec = PROMPTS.get(key)
    if spec is None:
        raise KeyError(f"Prompt '{key}' no registrado")
    return spec
