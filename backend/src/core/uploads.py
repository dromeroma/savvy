"""Lectura segura de archivos subidos (límite de tamaño + tipo)."""

from __future__ import annotations

from fastapi import UploadFile

from src.core.exceptions import ValidationError

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED_IMAGE_PDF = ("image/", "application/pdf")


async def read_limited(
    file: UploadFile,
    *,
    max_bytes: int = MAX_UPLOAD_BYTES,
    allowed_prefixes: tuple[str, ...] | None = ALLOWED_IMAGE_PDF,
) -> bytes:
    """Lee el archivo respetando un tope de tamaño. Lanza ValidationError si excede."""
    if allowed_prefixes and file.content_type:
        if not any(file.content_type.startswith(p) for p in allowed_prefixes):
            raise ValidationError(
                f"Tipo de archivo no permitido: {file.content_type}. "
                "Sube una imagen o PDF."
            )
    data = await file.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise ValidationError(
            f"El archivo supera el máximo de {max_bytes // (1024 * 1024)} MB."
        )
    if not data:
        raise ValidationError("Archivo vacío.")
    return data
