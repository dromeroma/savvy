"""SavvyChurch app router — assembles all church sub-module routers."""

from fastapi import APIRouter

from src.apps.church.members.router import router as members_router
from src.apps.church.finance.router import router as finance_router
from src.apps.church.reports.router import router as reports_router

router = APIRouter(prefix="/church", tags=["SavvyChurch"])

router.include_router(members_router)
router.include_router(finance_router)
router.include_router(reports_router)
