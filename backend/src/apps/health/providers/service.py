"""Business logic for health providers."""

from __future__ import annotations
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.apps.health.providers.models import HealthProvider
from src.apps.health.providers.schemas import ProviderCreate, ProviderResponse
from src.modules.people.models import Person
from src.modules.people.schemas import PersonCreate
from src.modules.people.service import PeopleService


def _build(provider: HealthProvider, person: Person) -> ProviderResponse:
    return ProviderResponse(id=provider.id, organization_id=provider.organization_id, person_id=person.id,
        first_name=person.first_name, last_name=person.last_name, email=person.email, phone=person.phone,
        provider_code=provider.provider_code, specialty=provider.specialty, license_number=provider.license_number,
        consultation_duration=provider.consultation_duration, schedule=provider.schedule or {},
        status=provider.status, created_at=provider.created_at)


class ProviderService:
    @staticmethod
    async def list_providers(db: AsyncSession, org_id: uuid.UUID) -> list[ProviderResponse]:
        result = await db.execute(select(HealthProvider, Person).join(Person, Person.id == HealthProvider.person_id).where(HealthProvider.organization_id == org_id).order_by(Person.last_name))
        return [_build(p, pe) for p, pe in result.all()]

    @staticmethod
    async def create_provider(db: AsyncSession, org_id: uuid.UUID, data: ProviderCreate) -> ProviderResponse:
        person = await PeopleService.create_person(db, org_id, PersonCreate(
            first_name=data.first_name, last_name=data.last_name, email=data.email, phone=data.phone, document_number=data.document_number))
        provider = HealthProvider(organization_id=org_id, person_id=person.id, provider_code=data.provider_code,
            specialty=data.specialty, license_number=data.license_number, consultation_duration=data.consultation_duration)
        db.add(provider); await db.flush(); await db.refresh(provider)
        return _build(provider, person)
