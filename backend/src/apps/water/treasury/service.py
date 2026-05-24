"""Business logic for water treasury (movements + closings + dashboard)."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.water.cash_accounts.service import CashAccountsService
from src.apps.water.models import (
    WaterCashAccount,
    WaterCashClosing,
    WaterPayment,
    WaterTreasuryMovement,
)
from src.apps.water.treasury.schemas import (
    CashAccountBalance,
    ClosingCreate,
    ClosingPreview,
    ClosingResponse,
    MovementCreate,
    MovementListItem,
    TreasuryDashboard,
)
from src.core.exceptions import NotFoundError, ValidationError


class TreasuryService:

    # ------------------------------------------------------------------
    # Movements
    # ------------------------------------------------------------------
    @staticmethod
    async def list_movements(
        db: AsyncSession,
        org_id: uuid.UUID,
        cash_account_id: uuid.UUID | None = None,
        type_: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        limit: int = 200,
        offset: int = 0,
    ) -> list[MovementListItem]:
        stmt = (
            select(
                WaterTreasuryMovement.id, WaterTreasuryMovement.movement_date,
                WaterTreasuryMovement.type, WaterTreasuryMovement.category,
                WaterTreasuryMovement.amount, WaterTreasuryMovement.description,
                WaterTreasuryMovement.reference, WaterTreasuryMovement.cash_account_id,
                WaterCashAccount.name.label("acc_name"),
                WaterTreasuryMovement.payment_id,
            )
            .join(WaterCashAccount, WaterCashAccount.id == WaterTreasuryMovement.cash_account_id)
            .where(WaterTreasuryMovement.organization_id == org_id)
            .order_by(WaterTreasuryMovement.movement_date.desc(), WaterTreasuryMovement.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if cash_account_id is not None:
            stmt = stmt.where(WaterTreasuryMovement.cash_account_id == cash_account_id)
        if type_:
            stmt = stmt.where(WaterTreasuryMovement.type == type_)
        if date_from:
            stmt = stmt.where(WaterTreasuryMovement.movement_date >= date_from)
        if date_to:
            stmt = stmt.where(WaterTreasuryMovement.movement_date <= date_to)
        rows = await db.execute(stmt)
        return [
            MovementListItem(
                id=r[0], movement_date=r[1], type=r[2], category=r[3], amount=r[4],
                description=r[5], reference=r[6], cash_account_id=r[7],
                cash_account_name=r[8], payment_id=r[9],
            )
            for r in rows.all()
        ]

    @staticmethod
    async def create_movement(
        db: AsyncSession,
        org_id: uuid.UUID,
        data: MovementCreate,
        recorded_by: uuid.UUID | None,
    ) -> WaterTreasuryMovement:
        # Validate cash account belongs to org
        acc = await db.scalar(
            select(WaterCashAccount).where(
                WaterCashAccount.id == data.cash_account_id,
                WaterCashAccount.organization_id == org_id,
            )
        )
        if acc is None:
            raise NotFoundError("Cash account not found.")
        if not acc.is_active:
            raise ValidationError("Esta cuenta está inactiva.")
        m = WaterTreasuryMovement(
            organization_id=org_id,
            recorded_by=recorded_by,
            **data.model_dump(),
        )
        db.add(m)
        await db.flush()
        await db.refresh(m)
        return m

    @staticmethod
    async def delete_movement(
        db: AsyncSession, org_id: uuid.UUID, movement_id: uuid.UUID,
    ) -> None:
        m = await db.scalar(
            select(WaterTreasuryMovement).where(
                WaterTreasuryMovement.id == movement_id,
                WaterTreasuryMovement.organization_id == org_id,
            )
        )
        if m is None:
            raise NotFoundError("Movement not found.")
        if m.payment_id is not None:
            raise ValidationError(
                "Este movimiento fue generado por un pago. Anula el pago en su lugar.",
            )
        await db.delete(m)
        await db.flush()

    # ------------------------------------------------------------------
    # Closings (arqueos)
    # ------------------------------------------------------------------
    @staticmethod
    async def closing_preview(
        db: AsyncSession,
        org_id: uuid.UUID,
        cash_account_id: uuid.UUID,
        closing_date: date,
    ) -> ClosingPreview:
        acc = await db.scalar(
            select(WaterCashAccount).where(
                WaterCashAccount.id == cash_account_id,
                WaterCashAccount.organization_id == org_id,
            )
        )
        if acc is None:
            raise NotFoundError("Cash account not found.")

        # Sum movements UP TO AND INCLUDING closing_date
        sums = await db.execute(
            select(
                WaterTreasuryMovement.type,
                func.coalesce(func.sum(WaterTreasuryMovement.amount), 0),
            )
            .where(
                WaterTreasuryMovement.organization_id == org_id,
                WaterTreasuryMovement.cash_account_id == cash_account_id,
                WaterTreasuryMovement.movement_date <= closing_date,
            )
            .group_by(WaterTreasuryMovement.type)
        )
        by_type = {r[0]: Decimal(str(r[1])) for r in sums.all()}
        income = by_type.get("income", Decimal("0"))
        expense = by_type.get("expense", Decimal("0"))
        expected = Decimal(acc.initial_balance) + income - expense
        return ClosingPreview(
            cash_account_id=acc.id,
            closing_date=closing_date,
            initial_balance=Decimal(acc.initial_balance),
            movements_income=income,
            movements_expense=expense,
            expected_balance=expected,
        )

    @staticmethod
    async def list_closings(
        db: AsyncSession,
        org_id: uuid.UUID,
        cash_account_id: uuid.UUID | None = None,
        limit: int = 100,
    ) -> list[ClosingResponse]:
        stmt = (
            select(
                WaterCashClosing.id, WaterCashClosing.organization_id,
                WaterCashClosing.cash_account_id, WaterCashAccount.name.label("acc_name"),
                WaterCashClosing.closing_date, WaterCashClosing.expected_balance,
                WaterCashClosing.counted_balance, WaterCashClosing.difference,
                WaterCashClosing.notes, WaterCashClosing.closed_by, WaterCashClosing.closed_at,
            )
            .join(WaterCashAccount, WaterCashAccount.id == WaterCashClosing.cash_account_id)
            .where(WaterCashClosing.organization_id == org_id)
            .order_by(WaterCashClosing.closing_date.desc(), WaterCashClosing.closed_at.desc())
            .limit(limit)
        )
        if cash_account_id is not None:
            stmt = stmt.where(WaterCashClosing.cash_account_id == cash_account_id)
        rows = await db.execute(stmt)
        return [
            ClosingResponse(
                id=r[0], organization_id=r[1], cash_account_id=r[2],
                cash_account_name=r[3], closing_date=r[4],
                expected_balance=r[5], counted_balance=r[6], difference=r[7],
                notes=r[8], closed_by=r[9], closed_at=r[10],
            )
            for r in rows.all()
        ]

    @staticmethod
    async def create_closing(
        db: AsyncSession,
        org_id: uuid.UUID,
        data: ClosingCreate,
        closed_by: uuid.UUID | None,
    ) -> ClosingResponse:
        preview = await TreasuryService.closing_preview(
            db, org_id, data.cash_account_id, data.closing_date,
        )
        difference = Decimal(data.counted_balance) - preview.expected_balance
        closing = WaterCashClosing(
            organization_id=org_id,
            cash_account_id=data.cash_account_id,
            closing_date=data.closing_date,
            expected_balance=preview.expected_balance,
            counted_balance=Decimal(data.counted_balance),
            difference=difference,
            notes=data.notes,
            closed_by=closed_by,
        )
        db.add(closing)
        await db.flush()
        # Fetch the account name to return ClosingResponse cleanly
        acc = await db.scalar(
            select(WaterCashAccount).where(WaterCashAccount.id == data.cash_account_id),
        )
        return ClosingResponse(
            id=closing.id, organization_id=org_id, cash_account_id=data.cash_account_id,
            cash_account_name=acc.name if acc else "",
            closing_date=data.closing_date,
            expected_balance=preview.expected_balance,
            counted_balance=Decimal(data.counted_balance),
            difference=difference,
            notes=data.notes, closed_by=closed_by, closed_at=closing.closed_at,
        )

    # ------------------------------------------------------------------
    # Treasury dashboard
    # ------------------------------------------------------------------
    @staticmethod
    async def dashboard(
        db: AsyncSession, org_id: uuid.UUID,
    ) -> TreasuryDashboard:
        today = date.today()
        first = today.replace(day=1)

        # Balances per account
        accs = await CashAccountsService.list_accounts(db, org_id, active_only=False)
        total = sum((a.current_balance for a in accs), start=Decimal("0"))
        balances = [
            CashAccountBalance(
                cash_account_id=a.id, code=a.code, name=a.name,
                type=a.type, current_balance=a.current_balance,
            )
            for a in accs
        ]

        # Today / month income & expense
        def _agg(stmt):
            return db.scalar(stmt)

        income_today = await db.scalar(
            select(func.coalesce(func.sum(WaterTreasuryMovement.amount), 0))
            .where(
                WaterTreasuryMovement.organization_id == org_id,
                WaterTreasuryMovement.type == "income",
                WaterTreasuryMovement.movement_date == today,
            )
        ) or 0
        expense_today = await db.scalar(
            select(func.coalesce(func.sum(WaterTreasuryMovement.amount), 0))
            .where(
                WaterTreasuryMovement.organization_id == org_id,
                WaterTreasuryMovement.type == "expense",
                WaterTreasuryMovement.movement_date == today,
            )
        ) or 0
        income_month = await db.scalar(
            select(func.coalesce(func.sum(WaterTreasuryMovement.amount), 0))
            .where(
                WaterTreasuryMovement.organization_id == org_id,
                WaterTreasuryMovement.type == "income",
                WaterTreasuryMovement.movement_date >= first,
            )
        ) or 0
        expense_month = await db.scalar(
            select(func.coalesce(func.sum(WaterTreasuryMovement.amount), 0))
            .where(
                WaterTreasuryMovement.organization_id == org_id,
                WaterTreasuryMovement.type == "expense",
                WaterTreasuryMovement.movement_date >= first,
            )
        ) or 0

        return TreasuryDashboard(
            total_balance=total,
            income_today=Decimal(str(income_today)),
            expense_today=Decimal(str(expense_today)),
            income_this_month=Decimal(str(income_month)),
            expense_this_month=Decimal(str(expense_month)),
            net_this_month=Decimal(str(income_month)) - Decimal(str(expense_month)),
            balances=balances,
        )
