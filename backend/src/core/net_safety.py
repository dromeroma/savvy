"""Validación de URLs salientes para prevenir SSRF.

Cuando el sistema hace una petición a una URL provista por el usuario (webhooks
de SavvyFlow), debe rechazar destinos internos: loopback, redes privadas,
link-local (metadata de la nube: 169.254.169.254), etc.
"""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse


class UnsafeUrlError(ValueError):
    pass


def validate_outbound_url(url: str, *, allow_http: bool = False) -> str:
    """Valida una URL saliente. Lanza UnsafeUrlError si es insegura.

    - Solo https (o http si allow_http).
    - Host debe resolver a una IP pública (no privada/loopback/link-local).
    """
    if not url or len(url) > 2048:
        raise UnsafeUrlError("URL vacía o demasiado larga.")
    parsed = urlparse(url)
    scheme = (parsed.scheme or "").lower()
    if scheme not in (("http", "https") if allow_http else ("https",)):
        raise UnsafeUrlError(f"Esquema no permitido: {scheme or '(vacío)'}. Usa https.")
    host = parsed.hostname
    if not host:
        raise UnsafeUrlError("URL sin host.")

    # Resolver todas las IPs del host y verificar que TODAS sean públicas.
    try:
        infos = socket.getaddrinfo(host, parsed.port or (443 if scheme == "https" else 80))
    except socket.gaierror as exc:
        raise UnsafeUrlError(f"No se pudo resolver el host: {host}") from exc

    for info in infos:
        ip_str = info[4][0]
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            raise UnsafeUrlError(f"IP inválida: {ip_str}")
        if (
            ip.is_private or ip.is_loopback or ip.is_link_local
            or ip.is_multicast or ip.is_reserved or ip.is_unspecified
        ):
            raise UnsafeUrlError(
                f"El destino {host} resuelve a una IP no pública ({ip_str})."
            )
    return url
