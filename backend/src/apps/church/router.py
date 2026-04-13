"""SavvyChurch app router — assembles all church sub-module routers."""

from fastapi import APIRouter

from src.apps.church.attendance.router import router as attendance_router
from src.apps.church.congregants.router import router as congregants_router
from src.apps.church.dashboard.router import router as dashboard_router
from src.apps.church.doctrine.router import router as doctrine_router
from src.apps.church.events.router import router as events_router
from src.apps.church.finance.router import router as finance_router
from src.apps.church.pastoral.router import router as pastoral_router
from src.apps.church.reports.router import router as reports_router
from src.apps.church.rotations.router import router as rotations_router
from src.apps.church.social_aid.router import router as social_aid_router
from src.apps.church.visitors.router import router as visitors_router

router = APIRouter(prefix="/church", tags=["SavvyChurch"])

router.include_router(dashboard_router)
router.include_router(congregants_router)
router.include_router(finance_router)
router.include_router(reports_router)
router.include_router(visitors_router)
router.include_router(events_router)
router.include_router(attendance_router)
router.include_router(pastoral_router)
router.include_router(doctrine_router)
router.include_router(social_aid_router)
router.include_router(rotations_router)
