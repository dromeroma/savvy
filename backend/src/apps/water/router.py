"""SavvyWater app router — assembles dashboard + subscribers + meters."""

from fastapi import APIRouter

from src.apps.water.dashboard.router import router as dashboard_router
from src.apps.water.meters.router import router as meters_router
from src.apps.water.subscribers.router import router as subscribers_router

router = APIRouter(prefix="/water", tags=["SavvyWater"])

router.include_router(dashboard_router)
router.include_router(subscribers_router)
router.include_router(meters_router)
