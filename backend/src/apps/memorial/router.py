"""Router padre de SavvyMemorial."""

from fastapi import APIRouter

from src.apps.memorial.services.router import dashboard_router, router as services_router

router = APIRouter(prefix="/memorial", tags=["SavvyMemorial"])

router.include_router(dashboard_router)
router.include_router(services_router)
