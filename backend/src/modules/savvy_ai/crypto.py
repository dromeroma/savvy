"""Cifrado simétrico de secretos (API keys, tokens) en reposo.

Usa una clave DEDICADA (`SAVVY_ENCRYPTION_KEY`) independiente del JWT secret:
rotar el JWT no debe destruir los secretos cifrados. Para compatibilidad con
secretos ya cifrados con el JWT secret, el descifrado prueba ambas claves
(MultiFernet) y el cifrado usa siempre la clave dedicada.
"""

from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken, MultiFernet

from src.core.config import get_settings


def _fernet_from(secret: str) -> Fernet:
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def _primary() -> Fernet:
    """Clave de cifrado primaria: la dedicada si existe, si no el JWT secret."""
    s = get_settings()
    secret = s.ENCRYPTION_KEY or s.JWT_SECRET_KEY
    return _fernet_from(secret)


def _multi() -> MultiFernet:
    """Para descifrar: prueba la dedicada y luego el JWT secret (compat)."""
    s = get_settings()
    keys: list[Fernet] = []
    if s.ENCRYPTION_KEY:
        keys.append(_fernet_from(s.ENCRYPTION_KEY))
    keys.append(_fernet_from(s.JWT_SECRET_KEY))
    return MultiFernet(keys)


def encrypt_secret(plaintext: str) -> str:
    """Cifra un secreto con la clave primaria. Devuelve token urlsafe (TEXT)."""
    return _primary().encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_secret(token: str) -> str | None:
    """Descifra probando todas las claves. None si ninguna funciona."""
    try:
        return _multi().decrypt(token.encode("utf-8")).decode("utf-8")
    except (InvalidToken, ValueError, TypeError):
        return None


def key_hint(plaintext: str) -> str:
    """Pista no sensible para mostrar en UI (p.ej. '...Ab12')."""
    if not plaintext:
        return ""
    return f"...{plaintext[-4:]}"
