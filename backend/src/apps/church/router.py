"""SavvyChurch app router — assembles all church sub-module routers."""

from fastapi import APIRouter

from src.apps.church.attendance.router import router as attendance_router
from src.apps.church.congregants.router import router as congregants_router
from src.apps.church.dashboard.router import router as dashboard_router
from src.apps.church.events.router import router as events_router
from src.apps.church.finance.router import router as finance_router
from src.apps.church.reports.router import router as reports_router
from src.apps.church.visitors.router import router as visitors_router

router = APIRouter(prefix="/church", tags=["SavvyChurch"])

router.include_router(dashboard_router)
router.include_router(congregants_router)
router.include_router(finance_router)
router.include_router(reports_router)
router.include_router(visitors_router)
router.include_router(events_router)
router.include_router(attendance_router)
