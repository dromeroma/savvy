"""SavvyParking app router."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.parking.infrastructure.router import router as infra_router
from src.apps.parking.vehicles.router import router as vehicles_router
from src.apps.parking.pricing.router import router as pricing_router
from src.apps.parking.sessions.router import router as sessions_router
from src.apps.parking.services.router import router as services_router
from src.apps.parking.dashboard.router import router as dashboard_router
from src.core.dependencies import get_current_user, get_db, get_org_id
from src.core.exceptions import ValidationError
from src.modules.savvy_ai.client import AiNotConfiguredError
from src.modules.savvy_ai.usage import QuotaExceededError

router = APIRouter(prefix="/parking", tags=["SavvyParking"])

router.include_router(dashboard_router)
router.include_router(infra_router)
router.include_router(vehicles_router)
router.include_router(pricing_router)
router.include_router(sessions_router)
router.include_router(services_router)


@router.post("/scan-plate")
async def scan_plate_endpoint(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    user: dict[str, Any] = Depends(get_current_user),
) -> Any:
    """SavvyVision: lee la placa de una foto y sugiere entrada/salida/lavado."""
    from src.apps.parking.ai_scan import scan_plate
    from src.core.uploads import read_limited
    data = await read_limited(file, allowed_prefixes=("image/",))
    try:
        return await scan_plate(
            db, org_id, file_bytes=data, filename=file.filename or "placa.jpg",
            content_type=file.content_type, user_id=uuid.UUID(user["sub"]),
        )
    except AiNotConfiguredError as exc:
        raise ValidationError(str(exc))
    except QuotaExceededError as exc:
        raise ValidationError(str(exc))
