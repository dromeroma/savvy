"""SavvyCredit application model — loan origination."""

import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.core.models.base import BaseMixin, OrgMixin


class CreditApplication(BaseMixin, OrgMixin, Base):
    """Loan application with approval workflow."""

    __tablename__ = "credit_applications"

    borrower_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("credit_borrowers.id", ondelete="CASCADE"), nullable=False,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("credit_products.id", ondelete="RESTRICT"), nullable=False,
    )
    requested_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    requested_term: Mapped[int] = mapped_column(Integer, nullable=False)
    # Number of installments
    purpose: Mapped[str | None] = mapped_column(String(200), nullable=True)
    application_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Approval workflow
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    # pending, under_review, approved, rejected, cancelled
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    decision_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    approved_amount: Mapped[float | None] = mapped_column(Numeric(15, 2), nullable=True)
    approved_term: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Documents/attachments metadata
    documents: Mapped[dict] = mapped_column(JSONB, nullable=False, default=list)
    # [{"name": "cedula.pdf", "type": "identity", "url": "..."}, ...]
