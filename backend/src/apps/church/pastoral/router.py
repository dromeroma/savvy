"""Pastoral REST endpoints: lifecycle, transfers, pastoral notes."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_db, get_org_id
from src.apps.church.pastoral.schemas import (
    LifecycleCreate,
    LifecycleResponse,
    PastoralNoteCreate,
    PastoralNoteResponse,
    PastoralNoteUpdate,
    TransferCreate,
    TransferResponse,
    TransferUpdate,
)
from src.apps.church.pastoral.service import (
    LifecycleService,
    PastoralNoteService,
    TransferService,
)

router = APIRouter(prefix="/pastoral", tags=["Church Pastoral"])


# ------------------------------------------------------------------
# Lifecycle
# ------------------------------------------------------------------

@router.get("/lifecycle/{congregant_id}", response_model=list[LifecycleResponse])
async def list_lifecycle(
    congregant_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await LifecycleService.list_for_congregant(db, org_id, congregant_id)


@router.post(
    "/lifecycle",
    response_model=LifecycleResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_lifecycle_event(
    data: LifecycleCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await LifecycleService.create_event(db, org_id, data)


# ------------------------------------------------------------------
# Transfers
# ------------------------------------------------------------------

@router.get("/transfers", response_model=list[TransferResponse])
async def list_transfers(
    person_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await TransferService.list_transfers(db, org_id, person_id)


@router.post(
    "/transfers",
    response_model=TransferResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_transfer(
    data: TransferCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await TransferService.create_transfer(db, org_id, data)


@router.patch("/transfers/{transfer_id}", response_model=TransferResponse)
async def update_transfer(
    transfer_id: uuid.UUID,
    data: TransferUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await TransferService.update_transfer(db, org_id, transfer_id, data)


# ------------------------------------------------------------------
# Pastoral notes
# ------------------------------------------------------------------

@router.get("/notes/{person_id}", response_model=list[PastoralNoteResponse])
async def list_notes(
    person_id: uuid.UUID,
    visibility: list[str] | None = Query(None),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await PastoralNoteService.list_notes_for_person(
        db, org_id, person_id, visibility,
    )


@router.post(
    "/notes",
    response_model=PastoralNoteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_note(
    data: PastoralNoteCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await PastoralNoteService.create_note(db, org_id, data)


@router.patch("/notes/{note_id}", response_model=PastoralNoteResponse)
async def update_note(
    note_id: uuid.UUID,
    data: PastoralNoteUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await PastoralNoteService.update_note(db, org_id, note_id, data)


@router.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    note_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> None:
    await PastoralNoteService.delete_note(db, org_id, note_id)
