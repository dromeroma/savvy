"""POS cash registers REST endpoints."""

import uuid
from typing import Any
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.dependencies import get_db, get_org_id
from src.apps.pos.registers.schemas import RegisterClose, RegisterOpen, RegisterResponse
from src.apps.pos.registers.service import RegisterService

router = APIRouter(prefix="/registers", tags=["POS Registers"])

@router.get("", response_model=list[RegisterResponse])
async def list_registers(status_filter: str | None = Query(None, alias="status"), db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await RegisterService.list_registers(db, org_id, status_filter)

@router.post("/open", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def open_register(data: RegisterOpen, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await RegisterService.open_register(db, org_id, data)

@router.post("/{reg_id}/close", response_model=RegisterResponse)
async def close_register(reg_id: uuid.UUID, data: RegisterClose, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await RegisterService.close_register(db, org_id, reg_id, data)
