"""SavvyParking app router."""

from fastapi import APIRouter
from src.apps.parking.infrastructure.router import router as infra_router
from src.apps.parking.vehicles.router import router as vehicles_router
from src.apps.parking.pricing.router import router as pricing_router
from src.apps.parking.sessions.router import router as sessions_router
from src.apps.parking.services.router import router as services_router
from src.apps.parking.dashboard.router import router as dashboard_router

router = APIRouter(prefix="/parking", tags=["SavvyParking"])

router.include_router(dashboard_router)
router.include_router(infra_router)
router.include_router(vehicles_router)
router.include_router(pricing_router)
router.include_router(sessions_router)
router.include_router(services_router)
