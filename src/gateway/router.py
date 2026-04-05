"""Central API router that assembles all module routers under /api/v1."""

from fastapi import APIRouter

from src.modules.auth.router import router as auth_router
from src.modules.organization.router import router as organization_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(organization_router)
