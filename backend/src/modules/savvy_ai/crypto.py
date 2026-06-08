"""Cifrado simétrico de secretos (API keys) en reposo.

Deriva una clave Fernet del JWT_SECRET_KEY de la app — no agrega config nueva.
La API key del proveedor de IA nunca se guarda en texto plano en la BD.
"""

from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from src.core.config import get_settings


def _fernet() -> Fernet:
    # Deriva 32 bytes estables del secreto JWT y los codifica urlsafe-base64.
    digest = hashlib.sha256(get_settings().JWT_SECRET_KEY.encode("utf-8")).digest()
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


def encrypt_secret(plaintext: str) -> str:
    """Cifra un secreto. Devuelve token urlsafe almacenable como TEXT."""
    return _fernet().encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_secret(token: str) -> str | None:
    """Descifra. Devuelve None si el token es inválido o la clave cambió."""
    try:
        return _fernet().decrypt(token.encode("utf-8")).decode("utf-8")
    except (InvalidToken, ValueError, TypeError):
        return None


def key_hint(plaintext: str) -> str:
    """Pista no sensible para mostrar en UI (p.ej. '...Ab12')."""
    if not plaintext:
        return ""
    tail = plaintext[-4:]
    return f"...{tail}"
