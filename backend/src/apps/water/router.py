"""SavvyWater app router."""

from fastapi import APIRouter

from src.apps.water.cartera.router import router as cartera_router
from src.apps.water.cash_accounts.router import router as cash_accounts_router
from src.apps.water.consumptions.router import router as consumptions_router
from src.apps.water.dashboard.router import router as dashboard_router
from src.apps.water.invoices.router import router as invoices_router
from src.apps.water.meters.router import router as meters_router
from src.apps.water.payments.router import router as payments_router
from src.apps.water.portal.router import router as portal_router
from src.apps.water.pqrs.router import router as pqrs_router
from src.apps.water.routes.router import router as routes_router
from src.apps.water.subscribers.router import router as subscribers_router
from src.apps.water.tariffs.router import router as tariffs_router
from src.apps.water.treasury.router import router as treasury_router

router = APIRouter(prefix="/water", tags=["SavvyWater"])

router.include_router(dashboard_router)
router.include_router(subscribers_router)
router.include_router(meters_router)
router.include_router(tariffs_router)
router.include_router(consumptions_router)
router.include_router(invoices_router)
router.include_router(payments_router)
router.include_router(cartera_router)
router.include_router(routes_router)
router.include_router(cash_accounts_router)
router.include_router(treasury_router)
router.include_router(pqrs_router)
router.include_router(portal_router)
