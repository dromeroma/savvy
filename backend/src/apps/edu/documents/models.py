"""SavvyEdu document models — templates and issued documents."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.core.models.base import BaseMixin, OrgMixin


class EduDocumentTemplate(BaseMixin, OrgMixin, Base):
    """Template for certificates, transcripts, report cards."""

    __tablename__ = "edu_document_templates"

    type: Mapped[str] = mapped_column(String(30), nullable=False)  # certificate, transcript, report_card, paz_y_salvo
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    template_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    variables: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # ["student_name", "program", "date", ...]


class EduIssuedDocument(BaseMixin, OrgMixin, Base):
    """A document issued to a student."""

    __tablename__ = "edu_issued_documents"

    student_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("edu_students.id", ondelete="CASCADE"), nullable=False,
    )
    template_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("edu_document_templates.id", ondelete="CASCADE"), nullable=False,
    )
    data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default="now()")
    issued_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
