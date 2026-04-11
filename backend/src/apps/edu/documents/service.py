"""Business logic for SavvyEdu documents."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundError
from src.apps.edu.documents.models import EduDocumentTemplate, EduIssuedDocument
from src.apps.edu.documents.schemas import DocumentTemplateCreate, IssuedDocumentCreate


class EduDocumentService:

    @staticmethod
    async def list_templates(db: AsyncSession, org_id: uuid.UUID) -> list[EduDocumentTemplate]:
        result = await db.execute(
            select(EduDocumentTemplate).where(EduDocumentTemplate.organization_id == org_id)
            .order_by(EduDocumentTemplate.type, EduDocumentTemplate.name)
        )
        return list(result.scalars().all())

    @staticmethod
    async def create_template(db: AsyncSession, org_id: uuid.UUID, data: DocumentTemplateCreate) -> EduDocumentTemplate:
        tpl = EduDocumentTemplate(
            organization_id=org_id,
            type=data.type,
            name=data.name,
            template_html=data.template_html,
            variables=data.variables,
        )
        db.add(tpl)
        await db.flush()
        await db.refresh(tpl)
        return tpl

    @staticmethod
    async def issue_document(db: AsyncSession, org_id: uuid.UUID, data: IssuedDocumentCreate) -> EduIssuedDocument:
        doc = EduIssuedDocument(
            organization_id=org_id,
            student_id=data.student_id,
            template_id=data.template_id,
            data=data.data,
        )
        db.add(doc)
        await db.flush()
        await db.refresh(doc)
        return doc

    @staticmethod
    async def list_issued(db: AsyncSession, org_id: uuid.UUID, student_id: uuid.UUID | None = None) -> list[EduIssuedDocument]:
        q = select(EduIssuedDocument).where(EduIssuedDocument.organization_id == org_id)
        if student_id:
            q = q.where(EduIssuedDocument.student_id == student_id)
        q = q.order_by(EduIssuedDocument.issued_at.desc())
        result = await db.execute(q)
        return list(result.scalars().all())
