"""Application configuration loaded from environment variables."""

from functools import lru_cache
from typing import Literal

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for the SavvyCore application."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="SAVVY_",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "SavvyCore"
    APP_VERSION: str = "0.1.0"
    APP_ENV: Literal["dev", "staging", "prod"] = "dev"
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://savvy:savvy_secret@localhost:5432/savvycore"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    JWT_SECRET_KEY: str = "change-me-to-a-random-256-bit-secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Cifrado de secretos en reposo (API keys de IA, tokens de WhatsApp).
    # Clave dedicada e independiente del JWT_SECRET_KEY: rotar el JWT no debe
    # destruir los secretos cifrados. Si está vacía, se cae a JWT_SECRET_KEY
    # (compatibilidad con secretos ya cifrados). MIGRAR a una clave propia en prod.
    ENCRYPTION_KEY: str = ""

    # RLS — enforcement por `SET LOCAL ROLE` + GUC por transacción.
    # OFF por defecto: la app corre como owner (RLS bypassada, comportamiento
    # actual). ON: cada transacción de un request con org corre como RLS_APP_ROLE
    # (no propietario) → la RLS aísla a nivel de BD. Activar primero en staging.
    RLS_ENFORCE: bool = False
    RLS_APP_ROLE: str = "savvy_app"

    # Kill-switch de gasto de IA (USD/día). 0 = sin límite. Protege contra
    # loops/abuso antes de que la cuota mensual por org reaccione.
    AI_DAILY_USD_LIMIT_GLOBAL: float = 50.0
    AI_DAILY_USD_LIMIT_ORG: float = 10.0

    # Secreto para que un cron externo dispare /automations/evaluate-all.
    CRON_SECRET: str = ""

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def DATABASE_URL_SYNC(self) -> str:
        """Synchronous database URL for Alembic migrations."""
        return self.DATABASE_URL.replace("+asyncpg", "+psycopg2")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "prod"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "dev"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached singleton of the application settings."""
    return Settings()
