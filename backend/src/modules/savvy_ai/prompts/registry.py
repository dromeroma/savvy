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


# ---------------- Reconocimiento de placa de vehículo (Parking) ----------------

PLATE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "plate": {"type": ["string", "null"], "description": "Placa del vehículo, sin espacios, mayúsculas"},
        "vehicle_type": {"type": ["string", "null"], "enum": ["car", "motorcycle", "truck", "van", "other", None],
                         "description": "Tipo de vehículo"},
        "color": {"type": ["string", "null"]},
        "brand": {"type": ["string", "null"]},
        "looks_dirty": {"type": "boolean", "description": "¿El vehículo se ve sucio (candidato a lavado)?"},
        "plate_confidence": {"type": "number", "description": "Confianza 0-100 en la lectura de la placa"},
    },
    "required": ["plate", "looks_dirty", "plate_confidence"],
}

PLATE_PROMPT = PromptSpec(
    key="extraction.vehicle_plate",
    version="v1",
    tier="sonnet",
    system=(
        "Eres un sistema de visión para un parqueadero. Lee la placa del vehículo "
        "de la imagen con la mayor precisión posible (mayúsculas, sin espacios). "
        "Identifica tipo, color y marca si son visibles. Evalúa si el vehículo se ve "
        "sucio (candidato a lavado). Si no puedes leer la placa, déjala en null. "
        "Responde SOLO llamando la herramienta de extracción."
    ),
    output_schema=PLATE_SCHEMA,
)


PROMPTS: dict[str, PromptSpec] = {
    INVOICE_PROMPT.key: INVOICE_PROMPT,
    PLATE_PROMPT.key: PLATE_PROMPT,
}


def get_prompt(key: str) -> PromptSpec:
    spec = PROMPTS.get(key)
    if spec is None:
        raise KeyError(f"Prompt '{key}' no registrado")
    return spec
