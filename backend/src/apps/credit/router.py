"""SavvyCredit app router — assembles all credit sub-module routers."""

from fastapi import APIRouter

from src.apps.credit.products.router import router as products_router
from src.apps.credit.borrowers.router import router as borrowers_router
from src.apps.credit.applications.router import router as applications_router
from src.apps.credit.loans.router import router as loans_router
from src.apps.credit.payments.router import router as payments_router
from src.apps.credit.restructuring.router import router as restructuring_router
from src.apps.credit.dashboard.router import router as dashboard_router

router = APIRouter(prefix="/credit", tags=["SavvyCredit"])

router.include_router(dashboard_router)
router.include_router(products_router)
router.include_router(borrowers_router)
router.include_router(applications_router)
router.include_router(loans_router)
router.include_router(payments_router)
router.include_router(restructuring_router)
