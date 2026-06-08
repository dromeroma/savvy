"""Rate limiting en memoria (ventana fija), sin dependencias externas.

Suficiente para una sola instancia pre-lanzamiento. Para multi-worker/instancia,
migrar el contador a Redis (ya hay REDIS_URL configurado).

Uso:
    @router.post("/login", dependencies=[Depends(rate_limit("auth", 10, 60))])
"""

from __future__ import annotations

import time

from fastapi import Request

from src.core.exceptions import SavvyException


class RateLimitError(SavvyException):
    status_code = 429
    code = "RATE_LIMITED"
    detail = "Demasiadas solicitudes. Intenta de nuevo en unos segundos."


# bucket_key -> (window_start_epoch, count)
_BUCKETS: dict[str, tuple[float, int]] = {}


def rate_limit(scope: str, max_requests: int, window_seconds: int):
    """Devuelve una dependencia que limita por IP del cliente y ventana."""

    async def _dep(request: Request) -> None:
        ident = request.client.host if request.client else "anon"
        key = f"{scope}:{ident}"
        now = time.time()
        window_start, count = _BUCKETS.get(key, (0.0, 0))
        if now - window_start >= window_seconds:
            _BUCKETS[key] = (now, 1)
            return
        if count >= max_requests:
            retry = int(window_seconds - (now - window_start)) or 1
            raise RateLimitError(f"Demasiadas solicitudes. Intenta de nuevo en {retry}s.")
        _BUCKETS[key] = (window_start, count + 1)

    return _dep
