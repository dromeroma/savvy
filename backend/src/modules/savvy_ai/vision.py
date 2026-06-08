"""SavvyScan — extracción de documentos/imágenes a JSON estructurado.

Usa Claude Vision + tool-use para forzar la salida al schema del prompt. Cada
llamada se mide en ai_usage (vía service.py).
"""

from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Any

from src.modules.savvy_ai.client import ClaudeProvider, LLMResult
from src.modules.savvy_ai.prompts.registry import PromptSpec


@dataclass
class ExtractionOutput:
    data: dict[str, Any]
    confidence: float | None
    field_confidence: dict[str, Any] | None
    result: LLMResult


def _media_type(filename: str, content_type: str | None) -> str:
    if content_type and content_type.startswith(("image/", "application/pdf")):
        return content_type
    lower = (filename or "").lower()
    if lower.endswith(".png"):
        return "image/png"
    if lower.endswith((".jpg", ".jpeg")):
        return "image/jpeg"
    if lower.endswith(".webp"):
        return "image/webp"
    if lower.endswith(".pdf"):
        return "application/pdf"
    return "image/jpeg"


def _content_block(file_bytes: bytes, media_type: str) -> dict[str, Any]:
    b64 = base64.standard_b64encode(file_bytes).decode("ascii")
    if media_type == "application/pdf":
        return {"type": "document", "source": {"type": "base64", "media_type": media_type, "data": b64}}
    return {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": b64}}


async def extract_document(
    provider: ClaudeProvider,
    spec: PromptSpec,
    *,
    file_bytes: bytes,
    filename: str,
    content_type: str | None,
    instruction: str | None = None,
) -> ExtractionOutput:
    """Extrae datos estructurados de un documento según el prompt indicado."""
    media_type = _media_type(filename, content_type)
    tool = {
        "name": "extract",
        "description": "Devuelve los datos estructurados extraídos del documento.",
        "input_schema": spec.output_schema,
    }
    user_text = instruction or "Extrae los datos de este documento."
    messages = [{
        "role": "user",
        "content": [
            _content_block(file_bytes, media_type),
            {"type": "text", "text": user_text},
        ],
    }]

    result = await provider.complete(
        messages=messages,
        tier=spec.tier,
        system=spec.system,
        tools=[tool],
        tool_choice={"type": "tool", "name": "extract"},
        max_tokens=4096,
    )

    data = result.tool_input or {}
    confidence = data.pop("overall_confidence", None) if isinstance(data, dict) else None
    field_conf = data.get("field_confidence") if isinstance(data, dict) else None
    return ExtractionOutput(
        data=data,
        confidence=float(confidence) if confidence is not None else None,
        field_confidence=field_conf,
        result=result,
    )
