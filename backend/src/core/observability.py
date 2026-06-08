"""Observabilidad: Sentry (errores) + logging estructurado JSON.

Todo gated por configuración: sin `SENTRY_DSN` no se inicializa Sentry; con
`LOG_JSON=false` los logs siguen en texto. Cero impacto si no se configura.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime

from src.core.config import get_settings


class JsonFormatter(logging.Formatter):
    """Formatea cada log como una línea JSON (ideal para Loki/Better Stack)."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        # Campos extra (request_id, org_id, status, duration_ms, etc.).
        for key in (
            "request_id", "org_id", "method", "path", "status", "duration_ms",
        ):
            val = getattr(record, key, None)
            if val is not None:
                payload[key] = val
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def setup_logging() -> None:
    """Aplica el formato JSON a los handlers raíz si LOG_JSON está activo."""
    if not get_settings().LOG_JSON:
        return
    root = logging.getLogger()
    for handler in root.handlers:
        handler.setFormatter(JsonFormatter())


def init_sentry() -> bool:
    """Inicializa Sentry si hay DSN. Devuelve True si quedó activo."""
    s = get_settings()
    if not s.SENTRY_DSN:
        return False
    try:
        import sentry_sdk
    except ImportError:
        logging.getLogger("savvycore").warning("SENTRY_DSN configurado pero sentry_sdk no está instalado.")
        return False
    sentry_sdk.init(
        dsn=s.SENTRY_DSN,
        environment=s.APP_ENV,
        traces_sample_rate=s.SENTRY_TRACES_SAMPLE_RATE,
        send_default_pii=False,  # no enviar PII por defecto (multi-tenant)
        release=f"savvy@{s.APP_VERSION}",
    )
    logging.getLogger("savvycore").info("Sentry activo (env=%s).", s.APP_ENV)
    return True


def set_sentry_tenant(org_id: str | None, request_id: str | None) -> None:
    """Etiqueta el scope de Sentry con el tenant del request (si Sentry está activo)."""
    try:
        import sentry_sdk
    except ImportError:
        return
    if not sentry_sdk.Hub.current.client:
        return
    scope = sentry_sdk.get_current_scope()
    if org_id:
        scope.set_tag("org_id", org_id)
    if request_id:
        scope.set_tag("request_id", request_id)
