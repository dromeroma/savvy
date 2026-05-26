"""Router padre de SavvyMemorial."""

from fastapi import APIRouter

from src.apps.memorial.cartera.router import router as cartera_router
from src.apps.memorial.contracts.router import router as contracts_router
from src.apps.memorial.invoices.router import router as invoices_router
from src.apps.memorial.payments.router import router as payments_router
from src.apps.memorial.plans.router import router as plans_router
from src.apps.memorial.services.router import dashboard_router, router as services_router

router = APIRouter(prefix="/memorial", tags=["SavvyMemorial"])

router.include_router(dashboard_router)
router.include_router(services_router)
router.include_router(plans_router)
router.include_router(contracts_router)
router.include_router(invoices_router)
router.include_router(payments_router)
router.include_router(cartera_router)
