"""SavvyPOS app router."""

from fastapi import APIRouter
from src.apps.pos.catalog.router import router as catalog_router
from src.apps.pos.inventory.router import router as inventory_router
from src.apps.pos.sales.router import router as sales_router
from src.apps.pos.registers.router import router as registers_router
from src.apps.pos.config.router import router as config_router
from src.apps.pos.dashboard.router import router as dashboard_router

router = APIRouter(prefix="/pos", tags=["SavvyPOS"])

router.include_router(dashboard_router)
router.include_router(catalog_router)
router.include_router(inventory_router)
router.include_router(sales_router)
router.include_router(registers_router)
router.include_router(config_router)
