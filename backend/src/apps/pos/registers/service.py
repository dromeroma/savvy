"""Business logic for POS cash registers."""

from __future__ import annotations
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.exceptions import NotFoundError, ValidationError
from src.apps.pos.registers.models import PosCashRegister
from src.apps.pos.registers.schemas import RegisterClose, RegisterOpen
from src.apps.pos.sales.models import PosSale


class RegisterService:

    @staticmethod
    async def open_register(db: AsyncSession, org_id: uuid.UUID, data: RegisterOpen) -> PosCashRegister:
        reg = PosCashRegister(
            organization_id=org_id,
            location_id=data.location_id, register_name=data.register_name,
            opening_balance=data.opening_balance, opened_at=datetime.now(UTC),
            status="open",
        )
        db.add(reg); await db.flush(); await db.refresh(reg); return reg

    @staticmethod
    async def close_register(db: AsyncSession, org_id: uuid.UUID, reg_id: uuid.UUID, data: RegisterClose) -> PosCashRegister:
        result = await db.execute(select(PosCashRegister).where(PosCashRegister.id == reg_id, PosCashRegister.organization_id == org_id))
        reg = result.scalar_one_or_none()
        if reg is None: raise NotFoundError("Register not found.")
        if reg.status != "open": raise ValidationError("Register is already closed.")

        # Calculate expected balance: opening + cash sales
        sales_result = await db.execute(
            select(func.coalesce(func.sum(PosSale.total), 0))
            .where(PosSale.register_id == reg_id, PosSale.status == "completed", PosSale.payment_method == "cash")
        )
        cash_sales = float(sales_result.scalar() or 0)
        expected = float(Decimal(str(reg.opening_balance)) + Decimal(str(cash_sales)))
        diff = data.closing_balance - expected

        reg.closing_balance = data.closing_balance
        reg.expected_balance = expected
        reg.difference = diff
        reg.closed_at = datetime.now(UTC)
        reg.status = "closed"
        reg.notes = data.notes

        await db.flush(); await db.refresh(reg); return reg

    @staticmethod
    async def list_registers(db: AsyncSession, org_id: uuid.UUID, status_filter: str | None = None) -> list[PosCashRegister]:
        q = select(PosCashRegister).where(PosCashRegister.organization_id == org_id)
        if status_filter: q = q.where(PosCashRegister.status == status_filter)
        return list((await db.execute(q.order_by(PosCashRegister.created_at.desc()))).scalars().all())
