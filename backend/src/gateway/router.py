"""Central API router that assembles all module and app routers under /api/v1."""

from fastapi import APIRouter

# Core modules
from src.modules.auth.router import router as auth_router
from src.modules.organization.router import router as organization_router

# Shared modules
from src.modules.apps.router import router as apps_router
from src.modules.accounting.router import router as accounting_router

# Apps
from src.apps.church.router import router as church_router

api_router = APIRouter(prefix="/api/v1")

# Core modules
api_router.include_router(auth_router)
api_router.include_router(organization_router)

# Shared modules
api_router.include_router(apps_router)
api_router.include_router(accounting_router)

# Vertical apps
api_router.include_router(church_router)
