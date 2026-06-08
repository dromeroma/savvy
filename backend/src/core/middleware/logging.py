"""Request logging middleware (tenant-aware).

Genera un ``request_id`` por request, mide duración, y emite una línea de log
estructurada con el ``org_id`` (cuando está resuelto). Loguea como WARNING los
requests lentos o con error 5xx, y etiqueta el scope de Sentry con el tenant.
"""

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from src.core.config import get_settings
from src.core.observability import set_sentry_tenant

logger = logging.getLogger("savvycore.access")


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        slow_ms = get_settings().SLOW_REQUEST_MS

        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            org_id = getattr(request.state, "org_id", None)
            set_sentry_tenant(str(org_id) if org_id else None, request_id)
            logger.exception(
                "unhandled error",
                extra={"request_id": request_id, "org_id": str(org_id) if org_id else None,
                       "method": request.method, "path": request.url.path,
                       "status": 500, "duration_ms": duration_ms},
            )
            raise

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        org_id = getattr(request.state, "org_id", None)
        response.headers["X-Request-ID"] = request_id

        # Etiqueta el tenant en Sentry para correlacionar errores por organización.
        set_sentry_tenant(str(org_id) if org_id else None, request_id)

        level = logging.INFO
        if response.status_code >= 500 or duration_ms >= slow_ms:
            level = logging.WARNING
        logger.log(
            level,
            "method=%s path=%s status=%s duration_ms=%s org=%s request_id=%s",
            request.method, request.url.path, response.status_code,
            duration_ms, org_id, request_id,
            extra={"request_id": request_id, "org_id": str(org_id) if org_id else None,
                   "method": request.method, "path": request.url.path,
                   "status": response.status_code, "duration_ms": duration_ms},
        )
        return response
