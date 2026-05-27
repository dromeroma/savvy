"""Router padre de SavvyMemorial."""

from fastapi import APIRouter

from src.apps.memorial.cartera.router import router as cartera_router
from src.apps.memorial.contracts.router import router as contracts_router
from src.apps.memorial.crm.router import router as crm_router
from src.apps.memorial.hr.router import router as hr_router
from src.apps.memorial.inventory.router import router as inventory_router
from src.apps.memorial.invoices.router import router as invoices_router
from src.apps.memorial.logistics.router import router as logistics_router
from src.apps.memorial.payments.router import router as payments_router
from src.apps.memorial.plans.router import router as plans_router
from src.apps.memorial.services.router import dashboard_router, router as services_router
from src.apps.memorial.transfers.router import router as transfers_router

router = APIRouter(prefix="/memorial", tags=["SavvyMemorial"])

router.include_router(dashboard_router)
router.include_router(services_router)
router.include_router(plans_router)
router.include_router(contracts_router)
router.include_router(invoices_router)
router.include_router(payments_router)
router.include_router(cartera_router)
router.include_router(logistics_router)
router.include_router(transfers_router)
router.include_router(inventory_router)
router.include_router(hr_router)
router.include_router(crm_router)
