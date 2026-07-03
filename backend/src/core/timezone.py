"""Zona horaria de la aplicación (Colombia) para cálculos de "hoy".

El servidor corre en UTC; usar `now()::date` del servidor hace que en la noche
colombiana (UTC-5) "hoy" salte al día siguiente. Estos helpers calculan la
fecha/hora local para que métricas como "ventas de hoy" u "ocupación" coincidan
con el día real del usuario.
"""

from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

APP_TZ = ZoneInfo("America/Bogota")
APP_TZ_NAME = "America/Bogota"


def local_now() -> datetime:
    return datetime.now(APP_TZ)


def local_today() -> date:
    return datetime.now(APP_TZ).date()
