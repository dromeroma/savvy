"""SavvyCore application entry point."""

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import get_settings
from src.core.exceptions import register_exception_handlers
from src.core.middleware.logging import LoggingMiddleware
from src.core.middleware.tenant import TenantMiddleware
from src.gateway.router import api_router

settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown lifecycle."""
    logging.getLogger("savvycore").info(
        "Starting %s v%s [%s]",
        settings.APP_NAME,
        settings.APP_VERSION,
        settings.APP_ENV,
    )
    yield
    logging.getLogger("savvycore").info("Shutting down %s", settings.APP_NAME)


def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    # --- Exception handlers ---
    register_exception_handlers(app)

    # --- Middleware (order matters: last added = first executed) ---
    app.add_middleware(TenantMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Routers ---
    app.include_router(api_router)

    # --- Health check ---
    @app.get("/health", tags=["System"])
    async def health_check() -> dict[str, str]:
        return {"status": "healthy", "version": settings.APP_VERSION}

    return app


app = create_app()
