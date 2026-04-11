"""Business logic for SavvyCredit loans + CreditEngine.

The CreditEngine handles amortization schedule generation, interest calculation,
and payment allocation. All financial math uses Decimal for precision.
"""

from __future__ import annotations

import uuid
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundError, ValidationError
from src.apps.credit.loans.models import CreditAmortization, CreditDisbursement, CreditLoan
from src.apps.credit.loans.schemas import DisburseLoan, LoanCreate
from src.apps.credit.products.models import CreditProduct
from src.apps.credit.borrowers.models import CreditBorrower


def _d(val: float | int | Decimal | None) -> Decimal:
    """Convert to Decimal for financial precision."""
    if val is None:
        return Decimal("0")
    return Decimal(str(val))


def _round2(val: Decimal) -> Decimal:
    return val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class CreditEngine:
    """Stateless credit calculation engine."""

    @staticmethod
    def generate_amortization(
        principal: Decimal,
        rate_per_period: Decimal,
        num_installments: int,
        method: str,
        start_date: date,
        frequency: str,
    ) -> list[dict]:
        """Generate amortization schedule.

        Returns list of dicts with: installment_number, due_date,
        principal_amount, interest_amount, total_amount, balance_after.
        """
        if method == "french":
            return CreditEngine._french(principal, rate_per_period, num_installments, start_date, frequency)
        elif method == "german":
            return CreditEngine._german(principal, rate_per_period, num_installments, start_date, frequency)
        elif method == "flat":
            return CreditEngine._flat(principal, rate_per_period, num_installments, start_date, frequency)
        elif method == "bullet":
            return CreditEngine._bullet(principal, rate_per_period, num_installments, start_date, frequency)
        else:
            raise ValidationError(f"Unknown amortization method: {method}")

    @staticmethod
    def _next_date(current: date, frequency: str, periods: int = 1) -> date:
        if frequency == "weekly":
            return current + timedelta(weeks=periods)
        elif frequency == "biweekly":
            return current + timedelta(weeks=2 * periods)
        elif frequency == "monthly":
            month = current.month + periods
            year = current.year + (month - 1) // 12
            month = (month - 1) % 12 + 1
            day = min(current.day, 28)  # Safe for all months
            return date(year, month, day)
        elif frequency == "quarterly":
            return CreditEngine._next_date(current, "monthly", periods * 3)
        return current + timedelta(days=30 * periods)

    @staticmethod
    def _french(P: Decimal, r: Decimal, n: int, start: date, freq: str) -> list[dict]:
        """French amortization: equal total payments."""
        schedule = []
        if r == 0:
            pmt = _round2(P / n)
            balance = P
            for i in range(1, n + 1):
                principal_part = pmt if i < n else balance
                due = CreditEngine._next_date(start, freq, i)
                balance -= principal_part
                schedule.append({
                    "installment_number": i,
                    "due_date": due,
                    "principal_amount": float(_round2(principal_part)),
                    "interest_amount": 0.0,
                    "total_amount": float(_round2(principal_part)),
                    "balance_after": float(_round2(balance)),
                })
            return schedule

        # PMT = P * [r(1+r)^n] / [(1+r)^n - 1]
        factor = (1 + r) ** n
        pmt = _round2(P * (r * factor) / (factor - 1))
        balance = P

        for i in range(1, n + 1):
            interest = _round2(balance * r)
            principal_part = pmt - interest
            if i == n:
                principal_part = balance
                interest = pmt - principal_part if pmt > principal_part else interest
            balance -= principal_part
            if balance < 0:
                balance = Decimal("0")

            due = CreditEngine._next_date(start, freq, i)
            schedule.append({
                "installment_number": i,
                "due_date": due,
                "principal_amount": float(_round2(principal_part)),
                "interest_amount": float(_round2(interest)),
                "total_amount": float(_round2(principal_part + interest)),
                "balance_after": float(_round2(balance)),
            })
        return schedule

    @staticmethod
    def _german(P: Decimal, r: Decimal, n: int, start: date, freq: str) -> list[dict]:
        """German amortization: equal principal payments, decreasing interest."""
        schedule = []
        fixed_principal = _round2(P / n)
        balance = P

        for i in range(1, n + 1):
            interest = _round2(balance * r)
            principal_part = fixed_principal if i < n else balance
            balance -= principal_part
            if balance < 0:
                balance = Decimal("0")

            due = CreditEngine._next_date(start, freq, i)
            schedule.append({
                "installment_number": i,
                "due_date": due,
                "principal_amount": float(_round2(principal_part)),
                "interest_amount": float(_round2(interest)),
                "total_amount": float(_round2(principal_part + interest)),
                "balance_after": float(_round2(balance)),
            })
        return schedule

    @staticmethod
    def _flat(P: Decimal, r: Decimal, n: int, start: date, freq: str) -> list[dict]:
        """Flat interest: interest calculated on original principal for all periods."""
        schedule = []
        total_interest = _round2(P * r * n)
        fixed_principal = _round2(P / n)
        fixed_interest = _round2(total_interest / n)
        balance = P

        for i in range(1, n + 1):
            principal_part = fixed_principal if i < n else balance
            balance -= principal_part
            if balance < 0:
                balance = Decimal("0")

            due = CreditEngine._next_date(start, freq, i)
            schedule.append({
                "installment_number": i,
                "due_date": due,
                "principal_amount": float(_round2(principal_part)),
                "interest_amount": float(_round2(fixed_interest)),
                "total_amount": float(_round2(principal_part + fixed_interest)),
                "balance_after": float(_round2(balance)),
            })
        return schedule

    @staticmethod
    def _bullet(P: Decimal, r: Decimal, n: int, start: date, freq: str) -> list[dict]:
        """Bullet: interest-only payments, principal at maturity."""
        schedule = []
        interest = _round2(P * r)

        for i in range(1, n + 1):
            is_last = i == n
            principal_part = P if is_last else Decimal("0")
            balance = Decimal("0") if is_last else P

            due = CreditEngine._next_date(start, freq, i)
            schedule.append({
                "installment_number": i,
                "due_date": due,
                "principal_amount": float(_round2(principal_part)),
                "interest_amount": float(_round2(interest)),
                "total_amount": float(_round2(principal_part + interest)),
                "balance_after": float(_round2(balance)),
            })
        return schedule

    @staticmethod
    def rate_to_period(rate: Decimal, rate_period: str, payment_frequency: str) -> Decimal:
        """Convert interest rate to the payment frequency period."""
        # Normalize to monthly first
        if rate_period == "annual":
            monthly = rate / 12
        elif rate_period == "daily":
            monthly = rate * 30
        else:
            monthly = rate

        # Convert monthly to target frequency
        if payment_frequency == "weekly":
            return _round2(monthly * 12 / 52) if monthly else Decimal("0")
        elif payment_frequency == "biweekly":
            return _round2(monthly * 12 / 26) if monthly else Decimal("0")
        elif payment_frequency == "quarterly":
            return monthly * 3
        return monthly  # monthly


class LoanService:

    @staticmethod
    async def _next_loan_number(db: AsyncSession, org_id: uuid.UUID) -> str:
        result = await db.execute(
            select(func.count()).where(CreditLoan.organization_id == org_id)
        )
        count = (result.scalar() or 0) + 1
        return f"LOAN-{count:06d}"

    @staticmethod
    async def create_loan(
        db: AsyncSession, org_id: uuid.UUID, data: LoanCreate,
    ) -> CreditLoan:
        """Create a loan, generate amortization schedule."""
        product_result = await db.execute(
            select(CreditProduct).where(
                CreditProduct.id == data.product_id,
                CreditProduct.organization_id == org_id,
            )
        )
        product = product_result.scalar_one_or_none()
        if product is None:
            raise NotFoundError("Credit product not found.")

        rate = _d(data.interest_rate_override) if data.interest_rate_override is not None else _d(product.interest_rate)
        rate_per_period = CreditEngine.rate_to_period(
            rate / 100,  # Convert percentage to decimal
            product.interest_rate_period,
            product.payment_frequency,
        )

        disb_date = data.disbursement_date or date.today()
        first_pay = data.first_payment_date or CreditEngine._next_date(disb_date, product.payment_frequency, 1)

        # Generate amortization
        schedule = CreditEngine.generate_amortization(
            principal=_d(data.principal),
            rate_per_period=rate_per_period,
            num_installments=data.term,
            method=product.amortization_method,
            start_date=disb_date,
            frequency=product.payment_frequency,
        )

        maturity = schedule[-1]["due_date"] if schedule else first_pay
        loan_number = await LoanService._next_loan_number(db, org_id)

        loan = CreditLoan(
            organization_id=org_id,
            borrower_id=data.borrower_id,
            product_id=data.product_id,
            application_id=data.application_id,
            loan_number=loan_number,
            principal=data.principal,
            interest_rate=float(rate),
            interest_type=product.interest_type,
            amortization_method=product.amortization_method,
            payment_frequency=product.payment_frequency,
            total_installments=data.term,
            payment_allocation=product.payment_allocation,
            disbursement_date=disb_date,
            first_payment_date=first_pay,
            maturity_date=maturity,
            next_payment_date=first_pay,
            balance_principal=data.principal,
            notes=data.notes,
            status="pending",
        )
        db.add(loan)
        await db.flush()

        # Save amortization schedule
        for entry in schedule:
            amort = CreditAmortization(
                loan_id=loan.id,
                installment_number=entry["installment_number"],
                due_date=entry["due_date"],
                principal_amount=entry["principal_amount"],
                interest_amount=entry["interest_amount"],
                total_amount=entry["total_amount"],
                balance_after=entry["balance_after"],
            )
            db.add(amort)

        # Update borrower stats
        borrower_result = await db.execute(
            select(CreditBorrower).where(CreditBorrower.id == data.borrower_id)
        )
        borrower = borrower_result.scalar_one()
        borrower.total_borrowed = float(_d(borrower.total_borrowed) + _d(data.principal))
        borrower.total_outstanding = float(_d(borrower.total_outstanding) + _d(data.principal))
        borrower.active_loans += 1

        await db.flush()
        await db.refresh(loan)
        return loan

    @staticmethod
    async def list_loans(
        db: AsyncSession, org_id: uuid.UUID,
        borrower_id: uuid.UUID | None = None,
        status_filter: str | None = None,
    ) -> list[CreditLoan]:
        q = select(CreditLoan).where(CreditLoan.organization_id == org_id)
        if borrower_id:
            q = q.where(CreditLoan.borrower_id == borrower_id)
        if status_filter:
            q = q.where(CreditLoan.status == status_filter)
        q = q.order_by(CreditLoan.created_at.desc())
        result = await db.execute(q)
        return list(result.scalars().all())

    @staticmethod
    async def get_loan(
        db: AsyncSession, org_id: uuid.UUID, loan_id: uuid.UUID,
    ) -> CreditLoan:
        result = await db.execute(
            select(CreditLoan).where(
                CreditLoan.id == loan_id,
                CreditLoan.organization_id == org_id,
            )
        )
        loan = result.scalar_one_or_none()
        if loan is None:
            raise NotFoundError("Loan not found.")
        return loan

    @staticmethod
    async def get_amortization(
        db: AsyncSession, loan_id: uuid.UUID,
    ) -> list[CreditAmortization]:
        result = await db.execute(
            select(CreditAmortization)
            .where(CreditAmortization.loan_id == loan_id)
            .order_by(CreditAmortization.installment_number)
        )
        return list(result.scalars().all())

    @staticmethod
    async def disburse_loan(
        db: AsyncSession, org_id: uuid.UUID, loan_id: uuid.UUID, data: DisburseLoan,
    ) -> CreditDisbursement:
        loan = await LoanService.get_loan(db, org_id, loan_id)
        if loan.status != "pending":
            raise ValidationError("Loan is not in pending status.")

        disb_date = data.disbursement_date or date.today()
        disbursement = CreditDisbursement(
            organization_id=org_id,
            loan_id=loan.id,
            amount=float(loan.principal),
            method=data.method,
            disbursement_date=disb_date,
            notes=data.notes,
        )
        db.add(disbursement)

        loan.status = "active"
        loan.disbursement_date = disb_date

        await db.flush()
        await db.refresh(disbursement)
        return disbursement
