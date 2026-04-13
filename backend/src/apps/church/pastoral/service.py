"""Business logic for pastoral sub-module."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime as dt

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundError
from src.apps.church.congregants.models import ChurchCongregant
from src.apps.church.pastoral.models import (
    ChurchMemberLifecycle,
    ChurchPastoralNote,
    ChurchTransfer,
)
from src.apps.church.pastoral.schemas import (
    LifecycleCreate,
    PastoralNoteCreate,
    PastoralNoteUpdate,
    TransferCreate,
    TransferUpdate,
)


# -----------------------------------------------------------------
# Lifecycle (append-only)
# -----------------------------------------------------------------

class LifecycleService:

    @staticmethod
    async def list_for_congregant(
        db: AsyncSession, org_id: uuid.UUID, congregant_id: uuid.UUID,
    ) -> list[ChurchMemberLifecycle]:
        result = await db.execute(
            select(ChurchMemberLifecycle)
            .where(
                ChurchMemberLifecycle.organization_id == org_id,
                ChurchMemberLifecycle.congregant_id == congregant_id,
            )
            .order_by(ChurchMemberLifecycle.changed_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def create_event(
        db: AsyncSession, org_id: uuid.UUID, data: LifecycleCreate,
    ) -> ChurchMemberLifecycle:
        # Sync the current spiritual_status on the congregant record.
        congregant = await db.get(ChurchCongregant, data.congregant_id)
        if congregant is None or congregant.organization_id != org_id:
            raise NotFoundError("Congregant not found.")

        previous_status = congregant.spiritual_status
        congregant.spiritual_status = data.to_status

        event = ChurchMemberLifecycle(
            organization_id=org_id,
            congregant_id=data.congregant_id,
            person_id=data.person_id,
            from_status=data.from_status or previous_status,
            to_status=data.to_status,
            changed_at=data.changed_at or dt.now(UTC),
            changed_by=data.changed_by,
            reason=data.reason,
            notes=data.notes,
        )
        db.add(event)
        await db.flush()
        await db.refresh(event)
        return event


# -----------------------------------------------------------------
# Transfers
# -----------------------------------------------------------------

class TransferService:

    @staticmethod
    async def list_transfers(
        db: AsyncSession, org_id: uuid.UUID,
        person_id: uuid.UUID | None = None,
    ) -> list[ChurchTransfer]:
        stmt = (
            select(ChurchTransfer)
            .where(ChurchTransfer.organization_id == org_id)
            .order_by(ChurchTransfer.transfer_date.desc())
        )
        if person_id:
            stmt = stmt.where(ChurchTransfer.person_id == person_id)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def create_transfer(
        db: AsyncSession, org_id: uuid.UUID, data: TransferCreate,
    ) -> ChurchTransfer:
        transfer = ChurchTransfer(organization_id=org_id, **data.model_dump())
        db.add(transfer)

        # If completed, also move the congregant's scope pointer.
        if data.status == "completed":
            result = await db.execute(
                select(ChurchCongregant).where(
                    ChurchCongregant.organization_id == org_id,
                    ChurchCongregant.person_id == data.person_id,
                )
            )
            congregant = result.scalar_one_or_none()
            if congregant is not None:
                congregant.scope_id = data.to_scope_id

        await db.flush()
        await db.refresh(transfer)
        return transfer

    @staticmethod
    async def update_transfer(
        db: AsyncSession, org_id: uuid.UUID,
        transfer_id: uuid.UUID, data: TransferUpdate,
    ) -> ChurchTransfer:
        transfer = await db.get(ChurchTransfer, transfer_id)
        if transfer is None or transfer.organization_id != org_id:
            raise NotFoundError("Transfer not found.")
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(transfer, field, value)
        await db.flush()
        await db.refresh(transfer)
        return transfer


# -----------------------------------------------------------------
# Pastoral notes
# -----------------------------------------------------------------

class PastoralNoteService:

    @staticmethod
    async def list_notes_for_person(
        db: AsyncSession, org_id: uuid.UUID, person_id: uuid.UUID,
        visibility_filter: list[str] | None = None,
    ) -> list[ChurchPastoralNote]:
        stmt = (
            select(ChurchPastoralNote)
            .where(
                ChurchPastoralNote.organization_id == org_id,
                ChurchPastoralNote.person_id == person_id,
            )
            .order_by(ChurchPastoralNote.created_at.desc())
        )
        if visibility_filter:
            stmt = stmt.where(ChurchPastoralNote.visibility.in_(visibility_filter))
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def create_note(
        db: AsyncSession, org_id: uuid.UUID, data: PastoralNoteCreate,
    ) -> ChurchPastoralNote:
        note = ChurchPastoralNote(organization_id=org_id, **data.model_dump())
        db.add(note)
        await db.flush()
        await db.refresh(note)
        return note

    @staticmethod
    async def update_note(
        db: AsyncSession, org_id: uuid.UUID,
        note_id: uuid.UUID, data: PastoralNoteUpdate,
    ) -> ChurchPastoralNote:
        note = await db.get(ChurchPastoralNote, note_id)
        if note is None or note.organization_id != org_id:
            raise NotFoundError("Pastoral note not found.")
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(note, field, value)
        await db.flush()
        await db.refresh(note)
        return note

    @staticmethod
    async def delete_note(
        db: AsyncSession, org_id: uuid.UUID, note_id: uuid.UUID,
    ) -> None:
        note = await db.get(ChurchPastoralNote, note_id)
        if note is None or note.organization_id != org_id:
            raise NotFoundError("Pastoral note not found.")
        await db.delete(note)
        await db.flush()
