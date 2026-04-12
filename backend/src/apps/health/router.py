"""SavvyHealth app router."""

from fastapi import APIRouter
from src.apps.health.patients.router import router as patients_router
from src.apps.health.providers.router import router as providers_router
from src.apps.health.appointments.router import router as appointments_router
from src.apps.health.clinical.router import router as clinical_router
from src.apps.health.services.router import router as services_router
from src.apps.health.dashboard.router import router as dashboard_router

router = APIRouter(prefix="/health", tags=["SavvyHealth"])

router.include_router(dashboard_router)
router.include_router(patients_router)
router.include_router(providers_router)
router.include_router(appointments_router)
router.include_router(clinical_router)
router.include_router(services_router)
