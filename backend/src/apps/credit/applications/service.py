"""Business logic for SavvyCredit applications."""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundError, ValidationError
from src.apps.credit.applications.models import CreditApplication
from src.apps.credit.applications.schemas import ApplicationCreate, ApplicationDecision
from src.apps.credit.products.service import CreditProductService
from src.apps.credit.borrowers.models import CreditBorrower


class ApplicationService:

    @staticmethod
    async def list_applications(
        db: AsyncSession, org_id: uuid.UUID, status_filter: str | None = None,
    ) -> list[CreditApplication]:
        q = select(CreditApplication).where(CreditApplication.organization_id == org_id)
        if status_filter:
            q = q.where(CreditApplication.status == status_filter)
        q = q.order_by(CreditApplication.created_at.desc())
        result = await db.execute(q)
        return list(result.scalars().all())

    @staticmethod
    async def create_application(
        db: AsyncSession, org_id: uuid.UUID, data: ApplicationCreate,
    ) -> CreditApplication:
        # Validate product exists and amount/term within limits
        product = await CreditProductService.get_product(db, org_id, data.product_id)

        if data.requested_amount < float(product.amount_min) or data.requested_amount > float(product.amount_max):
            raise ValidationError(
                f"Amount must be between {product.amount_min} and {product.amount_max}."
            )
        if data.requested_term < product.term_min or data.requested_term > product.term_max:
            raise ValidationError(
                f"Term must be between {product.term_min} and {product.term_max} installments."
            )

        # Validate borrower exists and is active
        borrower_result = await db.execute(
            select(CreditBorrower).where(
                CreditBorrower.id == data.borrower_id,
                CreditBorrower.organization_id == org_id,
            )
        )
        borrower = borrower_result.scalar_one_or_none()
        if borrower is None:
            raise NotFoundError("Borrower not found.")
        if borrower.status != "active":
            raise ValidationError("Borrower is not active.")

        app = CreditApplication(
            organization_id=org_id,
            borrower_id=data.borrower_id,
            product_id=data.product_id,
            requested_amount=data.requested_amount,
            requested_term=data.requested_term,
            purpose=data.purpose,
            application_date=data.application_date or date.today(),
        )
        db.add(app)
        await db.flush()
        await db.refresh(app)
        return app

    @staticmethod
    async def get_application(
        db: AsyncSession, org_id: uuid.UUID, app_id: uuid.UUID,
    ) -> CreditApplication:
        result = await db.execute(
            select(CreditApplication).where(
                CreditApplication.id == app_id,
                CreditApplication.organization_id == org_id,
            )
        )
        app = result.scalar_one_or_none()
        if app is None:
            raise NotFoundError("Application not found.")
        return app

    @staticmethod
    async def decide_application(
        db: AsyncSession, org_id: uuid.UUID, app_id: uuid.UUID,
        decision: ApplicationDecision, reviewed_by: uuid.UUID | None = None,
    ) -> CreditApplication:
        app = await ApplicationService.get_application(db, org_id, app_id)
        if app.status not in ("pending", "under_review"):
            raise ValidationError("Application has already been decided.")

        app.status = decision.status
        app.decision_notes = decision.decision_notes
        app.reviewed_by = reviewed_by

        if decision.status == "approved":
            app.approved_amount = decision.approved_amount or app.requested_amount
            app.approved_term = decision.approved_term or app.requested_term

        await db.flush()
        await db.refresh(app)
        return app
