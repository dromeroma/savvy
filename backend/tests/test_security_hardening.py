"""Tests unitarios de los hardening de seguridad (Fase 1). No requieren BD."""

import pytest

from src.core.net_safety import UnsafeUrlError, validate_outbound_url
from src.modules.savvy_ai.crypto import decrypt_secret, encrypt_secret, key_hint


# ---------------- Cifrado de secretos ----------------

def test_encrypt_decrypt_roundtrip():
    token = encrypt_secret("sk-ant-super-secret-123")
    assert token != "sk-ant-super-secret-123"
    assert decrypt_secret(token) == "sk-ant-super-secret-123"


def test_decrypt_garbage_returns_none():
    assert decrypt_secret("not-a-valid-fernet-token") is None
    assert decrypt_secret("") is None


def test_key_hint_is_not_sensitive():
    assert key_hint("sk-ant-abcd1234") == "...1234"
    assert key_hint("") == ""


# ---------------- Anti-SSRF en URLs salientes ----------------

@pytest.mark.parametrize("url", [
    "http://169.254.169.254/latest/meta-data/",  # metadata de la nube
    "http://localhost/admin",
    "http://127.0.0.1:8000/internal",
    "http://10.0.0.5/x",
    "http://192.168.1.1/x",
    "http://[::1]/x",
    "ftp://example.com/x",          # esquema no permitido
    "http://example.com/x",         # http no permitido por defecto
])
def test_ssrf_blocks_unsafe_urls(url):
    with pytest.raises(UnsafeUrlError):
        validate_outbound_url(url)


def test_ssrf_allows_public_https():
    # Host público real; debe pasar la validación de IP pública.
    assert validate_outbound_url("https://example.com/webhook") == "https://example.com/webhook"


def test_ssrf_rejects_oversized_url():
    with pytest.raises(UnsafeUrlError):
        validate_outbound_url("https://example.com/" + "a" * 3000)
