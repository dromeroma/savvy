"""Business logic for SavvyCredit payments — applies payments to loans using
the configured allocation method, updates balances and amortization status."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundError, ValidationError
from src.apps.credit.payments.models import CreditPayment, CreditPenalty
from src.apps.credit.payments.schemas import PaymentCreate
from src.apps.credit.loans.models import CreditAmortization, CreditLoan
from src.apps.credit.borrowers.models import CreditBorrower


def _d(val) -> Decimal:
    return Decimal(str(val)) if val else Decimal("0")


def _r2(val: Decimal) -> float:
    return float(val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


class PaymentService:

    @staticmethod
    async def record_payment(
        db: AsyncSession, org_id: uuid.UUID, data: PaymentCreate,
    ) -> CreditPayment:
        """Record a payment and apply it to the loan using the product's allocation method."""
        # Get loan
        loan_result = await db.execute(
            select(CreditLoan).where(
                CreditLoan.id == data.loan_id,
                CreditLoan.organization_id == org_id,
            )
        )
        loan = loan_result.scalar_one_or_none()
        if loan is None:
            raise NotFoundError("Loan not found.")
        if loan.status not in ("active", "current", "delinquent"):
            raise ValidationError("Loan is not in a payable status.")

        amount = _d(data.amount)
        remaining = amount
        penalty_applied = Decimal("0")
        interest_applied = Decimal("0")
        principal_applied = Decimal("0")

        allocation = loan.payment_allocation

        # 1. Apply to pending penalties first (always)
        penalty_balance = _d(loan.balance_penalties)
        if penalty_balance > 0 and remaining > 0:
            apply = min(remaining, penalty_balance)
            penalty_applied = apply
            remaining -= apply

        # 2. Apply to interest and principal based on allocation method
        interest_balance = _d(loan.balance_interest)

        if allocation == "interest_first":
            # Pay all interest first, then principal
            if interest_balance > 0 and remaining > 0:
                apply = min(remaining, interest_balance)
                interest_applied = apply
                remaining -= apply
            principal_applied = remaining
        elif allocation == "principal_first":
            # Pay principal first, then interest
            principal_balance = _d(loan.balance_principal)
            if principal_balance > 0 and remaining > 0:
                apply = min(remaining, principal_balance)
                principal_applied = apply
                remaining -= apply
            interest_applied = remaining
        else:  # proportional
            total_due = _d(loan.balance_principal) + interest_balance
            if total_due > 0 and remaining > 0:
                apply = min(remaining, total_due)
                ratio = _d(loan.balance_principal) / total_due if total_due > 0 else Decimal("0.5")
                principal_applied = apply * ratio
                interest_applied = apply - principal_applied

        # Create payment record
        payment = CreditPayment(
            organization_id=org_id,
            loan_id=loan.id,
            amount=float(amount),
            principal_applied=_r2(principal_applied),
            interest_applied=_r2(interest_applied),
            penalty_applied=_r2(penalty_applied),
            payment_date=data.payment_date or date.today(),
            method=data.method,
            notes=data.notes,
        )
        db.add(payment)

        # Update loan balances
        loan.balance_principal = _r2(_d(loan.balance_principal) - principal_applied)
        loan.balance_interest = _r2(_d(loan.balance_interest) - interest_applied)
        loan.balance_penalties = _r2(_d(loan.balance_penalties) - penalty_applied)
        loan.total_paid = _r2(_d(loan.total_paid) + amount)
        loan.total_interest_paid = _r2(_d(loan.total_interest_paid) + interest_applied)

        # Update amortization entries
        remaining_principal = principal_applied + interest_applied  # total to mark in schedule
        amort_result = await db.execute(
            select(CreditAmortization)
            .where(
                CreditAmortization.loan_id == loan.id,
                CreditAmortization.status.in_(["pending", "partial", "overdue"]),
            )
            .order_by(CreditAmortization.installment_number)
        )
        for amort in amort_result.scalars().all():
            if remaining_principal <= 0:
                break
            due = _d(amort.total_amount) - _d(amort.paid_amount)
            if due <= 0:
                continue
            apply = min(remaining_principal, due)
            amort.paid_amount = _r2(_d(amort.paid_amount) + apply)
            if _d(amort.paid_amount) >= _d(amort.total_amount):
                amort.status = "paid"
                amort.paid_date = data.payment_date or date.today()
            else:
                amort.status = "partial"
            remaining_principal -= apply

        # Check if loan is fully paid
        if _d(loan.balance_principal) <= 0:
            loan.status = "paid_off"
            loan.balance_principal = 0
            # Update borrower stats
            borrower_result = await db.execute(
                select(CreditBorrower).where(CreditBorrower.id == loan.borrower_id)
            )
            borrower = borrower_result.scalar_one()
            borrower.active_loans = max(0, borrower.active_loans - 1)
            borrower.completed_loans += 1
            borrower.total_outstanding = _r2(_d(borrower.total_outstanding) - _d(loan.principal))
            borrower.total_paid = _r2(_d(borrower.total_paid) + amount)
        else:
            # Update next payment date
            next_amort = await db.execute(
                select(CreditAmortization)
                .where(
                    CreditAmortization.loan_id == loan.id,
                    CreditAmortization.status.in_(["pending", "partial"]),
                )
                .order_by(CreditAmortization.installment_number)
                .limit(1)
            )
            next_entry = next_amort.scalar_one_or_none()
            if next_entry:
                loan.next_payment_date = next_entry.due_date
            loan.status = "current" if loan.days_overdue == 0 else "delinquent"

            # Update borrower total_paid
            borrower_result = await db.execute(
                select(CreditBorrower).where(CreditBorrower.id == loan.borrower_id)
            )
            borrower = borrower_result.scalar_one()
            borrower.total_paid = _r2(_d(borrower.total_paid) + amount)
            borrower.total_outstanding = _r2(_d(borrower.total_outstanding) - principal_applied)

        await db.flush()
        await db.refresh(payment)
        return payment

    @staticmethod
    async def list_payments(
        db: AsyncSession, org_id: uuid.UUID, loan_id: uuid.UUID,
    ) -> list[CreditPayment]:
        result = await db.execute(
            select(CreditPayment)
            .where(CreditPayment.organization_id == org_id, CreditPayment.loan_id == loan_id)
            .order_by(CreditPayment.payment_date.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def list_penalties(
        db: AsyncSession, org_id: uuid.UUID, loan_id: uuid.UUID,
    ) -> list[CreditPenalty]:
        result = await db.execute(
            select(CreditPenalty)
            .where(CreditPenalty.organization_id == org_id, CreditPenalty.loan_id == loan_id)
            .order_by(CreditPenalty.applied_date.desc())
        )
        return list(result.scalars().all())
