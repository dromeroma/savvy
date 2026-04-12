"""SavvyCondo app router."""

from fastapi import APIRouter
from src.apps.condo.properties.router import router as properties_router
from src.apps.condo.residents.router import router as residents_router
from src.apps.condo.fees.router import router as fees_router
from src.apps.condo.areas.router import router as areas_router
from src.apps.condo.maintenance.router import router as maintenance_router
from src.apps.condo.governance.router import router as governance_router
from src.apps.condo.communication.router import router as communication_router
from src.apps.condo.dashboard.router import router as dashboard_router

router = APIRouter(prefix="/condo", tags=["SavvyCondo"])

router.include_router(dashboard_router)
router.include_router(properties_router)
router.include_router(residents_router)
router.include_router(fees_router)
router.include_router(areas_router)
router.include_router(maintenance_router)
router.include_router(governance_router)
router.include_router(communication_router)
