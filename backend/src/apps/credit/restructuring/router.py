"""SavvyCredit restructuring REST endpoints."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_db, get_org_id
from src.modules.apps.permissions import require_permission
from src.apps.credit.restructuring.schemas import RestructuringCreate, RestructuringResponse
from src.apps.credit.restructuring.service import RestructuringService

router = APIRouter(
    prefix="/restructuring",
    tags=["Credit Restructuring"],
    dependencies=[Depends(require_permission("credit", "loans.approve"))],
)


@router.post("", response_model=RestructuringResponse, status_code=status.HTTP_201_CREATED)
async def restructure_loan(
    data: RestructuringCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await RestructuringService.restructure(db, org_id, data)
