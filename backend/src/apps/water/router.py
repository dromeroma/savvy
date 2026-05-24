"""SavvyWater app router — assembles dashboard + subscribers + meters
+ tariffs + consumptions + invoices + payments."""

from fastapi import APIRouter

from src.apps.water.consumptions.router import router as consumptions_router
from src.apps.water.dashboard.router import router as dashboard_router
from src.apps.water.invoices.router import router as invoices_router
from src.apps.water.meters.router import router as meters_router
from src.apps.water.payments.router import router as payments_router
from src.apps.water.subscribers.router import router as subscribers_router
from src.apps.water.tariffs.router import router as tariffs_router

router = APIRouter(prefix="/water", tags=["SavvyWater"])

router.include_router(dashboard_router)
router.include_router(subscribers_router)
router.include_router(meters_router)
router.include_router(tariffs_router)
router.include_router(consumptions_router)
router.include_router(invoices_router)
router.include_router(payments_router)
