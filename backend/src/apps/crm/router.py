"""SavvyCRM app router — assembles all CRM sub-module routers."""

from fastapi import APIRouter

from src.apps.crm.contacts.router import router as contacts_router
from src.apps.crm.leads.router import router as leads_router
from src.apps.crm.pipelines.router import router as pipelines_router
from src.apps.crm.deals.router import router as deals_router
from src.apps.crm.activities.router import router as activities_router
from src.apps.crm.dashboard.router import router as dashboard_router

router = APIRouter(prefix="/crm", tags=["SavvyCRM"])

router.include_router(dashboard_router)
router.include_router(contacts_router)
router.include_router(leads_router)
router.include_router(pipelines_router)
router.include_router(deals_router)
router.include_router(activities_router)
