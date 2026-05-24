"""Business logic for water cash accounts."""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import case, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.water.cash_accounts.schemas import (
    CashAccountCreate,
    CashAccountListItem,
    CashAccountUpdate,
)
from src.apps.water.models import WaterCashAccount, WaterTreasuryMovement
from src.core.exceptions import ConflictError, NotFoundError


class CashAccountsService:

    @staticmethod
    async def list_accounts(
        db: AsyncSession,
        org_id: uuid.UUID,
        active_only: bool = False,
    ) -> list[CashAccountListItem]:
        # Balance = initial_balance + sum(income) - sum(expense)
        balance_sq = (
            select(
                WaterTreasuryMovement.cash_account_id,
                func.coalesce(
                    func.sum(
                        case(
                            (WaterTreasuryMovement.type == "income", WaterTreasuryMovement.amount),
                            else_=-WaterTreasuryMovement.amount,
                        )
                    ),
                    0,
                ).label("delta"),
                func.count(WaterTreasuryMovement.id).label("n"),
            )
            .where(WaterTreasuryMovement.organization_id == org_id)
            .group_by(WaterTreasuryMovement.cash_account_id)
            .subquery()
        )
        stmt = (
            select(
                WaterCashAccount.id, WaterCashAccount.code, WaterCashAccount.name,
                WaterCashAccount.type, WaterCashAccount.is_default,
                WaterCashAccount.is_active, WaterCashAccount.initial_balance,
                (WaterCashAccount.initial_balance + func.coalesce(balance_sq.c.delta, 0)).label("bal"),
                func.coalesce(balance_sq.c.n, 0).label("n"),
            )
            .outerjoin(balance_sq, balance_sq.c.cash_account_id == WaterCashAccount.id)
            .where(WaterCashAccount.organization_id == org_id)
            .order_by(WaterCashAccount.is_default.desc(), WaterCashAccount.code)
        )
        if active_only:
            stmt = stmt.where(WaterCashAccount.is_active.is_(True))
        rows = await db.execute(stmt)
        return [
            CashAccountListItem(
                id=r[0], code=r[1], name=r[2], type=r[3], is_default=r[4],
                is_active=r[5], initial_balance=Decimal(str(r[6])),
                current_balance=Decimal(str(r[7])), movement_count=int(r[8]),
            )
            for r in rows.all()
        ]

    @staticmethod
    async def get_account(
        db: AsyncSession, org_id: uuid.UUID, account_id: uuid.UUID,
    ) -> WaterCashAccount:
        a = await db.scalar(
            select(WaterCashAccount).where(
                WaterCashAccount.id == account_id,
                WaterCashAccount.organization_id == org_id,
            )
        )
        if a is None:
            raise NotFoundError("Cash account not found.")
        return a

    @staticmethod
    async def get_default(
        db: AsyncSession, org_id: uuid.UUID,
    ) -> WaterCashAccount | None:
        return await db.scalar(
            select(WaterCashAccount).where(
                WaterCashAccount.organization_id == org_id,
                WaterCashAccount.is_default.is_(True),
                WaterCashAccount.is_active.is_(True),
            )
        )

    @staticmethod
    async def create_account(
        db: AsyncSession, org_id: uuid.UUID, data: CashAccountCreate,
    ) -> WaterCashAccount:
        existing = await db.scalar(
            select(WaterCashAccount).where(
                WaterCashAccount.organization_id == org_id,
                WaterCashAccount.code == data.code,
            )
        )
        if existing is not None:
            raise ConflictError(f"Already exists a cash account with code '{data.code}'.")
        if data.is_default:
            await CashAccountsService._unset_other_defaults(db, org_id)
        a = WaterCashAccount(organization_id=org_id, **data.model_dump())
        db.add(a)
        await db.flush()
        await db.refresh(a)
        return a

    @staticmethod
    async def update_account(
        db: AsyncSession, org_id: uuid.UUID, account_id: uuid.UUID, data: CashAccountUpdate,
    ) -> WaterCashAccount:
        a = await CashAccountsService.get_account(db, org_id, account_id)
        update_data = data.model_dump(exclude_unset=True)
        if update_data.get("is_default") is True:
            await CashAccountsService._unset_other_defaults(db, org_id, except_id=a.id)
        for k, v in update_data.items():
            setattr(a, k, v)
        await db.flush()
        await db.refresh(a)
        return a

    @staticmethod
    async def delete_account(
        db: AsyncSession, org_id: uuid.UUID, account_id: uuid.UUID,
    ) -> None:
        a = await CashAccountsService.get_account(db, org_id, account_id)
        # Block deletion if any movements reference it
        n = await db.scalar(
            select(func.count(WaterTreasuryMovement.id))
            .where(WaterTreasuryMovement.cash_account_id == a.id)
        )
        if n:
            raise ConflictError(
                "No se puede eliminar la cuenta: tiene movimientos. Desactívala.",
            )
        await db.delete(a)
        await db.flush()

    @staticmethod
    async def _unset_other_defaults(
        db: AsyncSession, org_id: uuid.UUID, except_id: uuid.UUID | None = None,
    ) -> None:
        stmt = (
            update(WaterCashAccount)
            .where(
                WaterCashAccount.organization_id == org_id,
                WaterCashAccount.is_default.is_(True),
            )
            .values(is_default=False)
        )
        if except_id is not None:
            stmt = stmt.where(WaterCashAccount.id != except_id)
        await db.execute(stmt)
