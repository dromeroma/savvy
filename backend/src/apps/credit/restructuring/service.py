"""Business logic for SavvyCredit restructuring."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundError, ValidationError
from src.apps.credit.restructuring.models import CreditRestructuring
from src.apps.credit.restructuring.schemas import RestructuringCreate
from src.apps.credit.loans.models import CreditLoan
from src.apps.credit.loans.service import LoanService
from src.apps.credit.loans.schemas import LoanCreate


class RestructuringService:

    @staticmethod
    async def restructure(
        db: AsyncSession, org_id: uuid.UUID, data: RestructuringCreate,
    ) -> CreditRestructuring:
        loan = await LoanService.get_loan(db, org_id, data.original_loan_id)
        if loan.status in ("paid_off", "written_off"):
            raise ValidationError("Cannot restructure a closed loan.")

        original_balance = float(Decimal(str(loan.balance_principal)) + Decimal(str(loan.balance_interest)))
        effective = data.effective_date or date.today()
        terms: dict = {}

        if data.type == "write_off":
            loan.status = "written_off"
            restructuring = CreditRestructuring(
                organization_id=org_id,
                original_loan_id=loan.id,
                type="write_off",
                reason=data.reason,
                original_balance=original_balance,
                new_balance=0,
                effective_date=effective,
                terms={"written_off_amount": original_balance},
            )
            db.add(restructuring)
            await db.flush()
            await db.refresh(restructuring)
            return restructuring

        if data.type == "settlement":
            discount = data.discount_amount or 0
            new_balance = max(0, original_balance - discount)
            loan.balance_principal = new_balance
            loan.balance_interest = 0
            loan.balance_penalties = 0
            loan.status = "active"
            terms = {"discount_amount": discount, "settled_balance": new_balance}

            restructuring = CreditRestructuring(
                organization_id=org_id,
                original_loan_id=loan.id,
                type="settlement",
                reason=data.reason,
                original_balance=original_balance,
                new_balance=new_balance,
                effective_date=effective,
                terms=terms,
            )
            db.add(restructuring)
            await db.flush()
            await db.refresh(restructuring)
            return restructuring

        # refinancing or rescheduling: close old loan, create new one
        loan.status = "restructured"

        new_rate = data.new_rate if data.new_rate is not None else float(loan.interest_rate)
        new_term = data.new_term if data.new_term is not None else loan.total_installments
        new_principal = original_balance

        new_loan_data = LoanCreate(
            borrower_id=loan.borrower_id,
            product_id=loan.product_id,
            principal=new_principal,
            term=new_term,
            interest_rate_override=new_rate,
            disbursement_date=effective,
            notes=f"Restructured from {loan.loan_number}: {data.reason or data.type}",
        )
        new_loan = await LoanService.create_loan(db, org_id, new_loan_data)
        new_loan.status = "active"

        terms = {
            "original_rate": float(loan.interest_rate),
            "new_rate": new_rate,
            "original_term": loan.total_installments,
            "new_term": new_term,
        }

        restructuring = CreditRestructuring(
            organization_id=org_id,
            original_loan_id=loan.id,
            new_loan_id=new_loan.id,
            type=data.type,
            reason=data.reason,
            original_balance=original_balance,
            new_balance=new_principal,
            effective_date=effective,
            terms=terms,
        )
        db.add(restructuring)
        await db.flush()
        await db.refresh(restructuring)
        return restructuring
