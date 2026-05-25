"""CSV import logic for water subscribers and meters."""

from __future__ import annotations

import csv
import io
import re
import uuid
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.water.imports.schemas import (
    ImportCommitResponse,
    ImportCommitRow,
    ImportPreviewResponse,
    ImportRowError,
    ImportRowPreview,
)
from src.apps.water.models import WaterMeter, WaterSubscriber


SUBSCRIBER_TYPES = {"residential", "commercial", "industrial", "official"}
SUBSCRIBER_STATUSES = {"active", "suspended", "overdue", "retired"}
METER_STATUSES = {"active", "replaced", "damaged", "inactive"}
DOCUMENT_TYPES = {"CC", "NIT", "CE", "TI", "PP", "RC", "PA"}

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

SUBSCRIBER_COLUMNS = [
    "code", "subscriber_type", "first_name", "last_name", "business_name",
    "document_type", "document_number", "email", "phone", "mobile",
    "address", "neighborhood", "stratum", "status", "latitude", "longitude",
    "notes", "registered_at",
]

METER_COLUMNS = [
    "serial_number", "subscriber_code", "brand", "model", "diameter",
    "install_date", "initial_reading", "last_reading", "status",
    "location_notes",
]


def _clean(v: Any) -> str | None:
    if v is None:
        return None
    s = str(v).strip()
    return s if s else None


def _parse_int(v: Any) -> int | None:
    s = _clean(v)
    if s is None:
        return None
    try:
        return int(s)
    except ValueError:
        raise ValueError(f"'{s}' no es un entero válido")


def _parse_decimal(v: Any) -> Decimal | None:
    s = _clean(v)
    if s is None:
        return None
    try:
        return Decimal(s.replace(",", "."))
    except InvalidOperation:
        raise ValueError(f"'{s}' no es un número válido")


def _parse_date(v: Any) -> date | None:
    s = _clean(v)
    if s is None:
        return None
    try:
        return date.fromisoformat(s)
    except ValueError:
        raise ValueError(f"'{s}' no es una fecha válida (usa YYYY-MM-DD)")


def _decode_csv(raw: bytes) -> list[dict[str, str]]:
    """Decode bytes (utf-8 with optional BOM) and return list of dicts."""
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            text = raw.decode("latin-1")
        except UnicodeDecodeError as e:
            raise ValueError(f"No se pudo decodificar el archivo CSV: {e}") from e
    reader = csv.DictReader(io.StringIO(text))
    return list(reader)


class ImportsService:

    # ------------------------------------------------------------------
    # Subscribers
    # ------------------------------------------------------------------
    @staticmethod
    async def preview_subscribers(
        db: AsyncSession, org_id: uuid.UUID, raw: bytes,
    ) -> ImportPreviewResponse:
        rows_raw = _decode_csv(raw)
        if not rows_raw:
            return ImportPreviewResponse(
                rows=[], total_rows=0, total_valid=0, total_errors=0,
                total_create=0, total_update=0,
            )

        # Index existing subscribers by code for upsert lookup
        existing = await db.execute(
            select(WaterSubscriber.id, WaterSubscriber.code)
            .where(WaterSubscriber.organization_id == org_id)
        )
        by_code: dict[str, uuid.UUID] = {r[1]: r[0] for r in existing.all()}

        previews: list[ImportRowPreview] = []
        seen_codes: dict[str, int] = {}

        for idx, raw_row in enumerate(rows_raw, start=2):  # row 1 is header
            errors: list[ImportRowError] = []
            data: dict[str, Any] = {}

            # code
            code = _clean(raw_row.get("code"))
            if not code:
                errors.append(ImportRowError(field="code", message="Obligatorio"))
            elif len(code) > 40:
                errors.append(ImportRowError(field="code", message="Máx 40 caracteres"))
            else:
                if code in seen_codes:
                    errors.append(ImportRowError(
                        field="code",
                        message=f"Duplicado en el CSV (también está en la fila {seen_codes[code]})",
                    ))
                else:
                    seen_codes[code] = idx
                data["code"] = code

            # first_name
            first_name = _clean(raw_row.get("first_name"))
            if not first_name:
                errors.append(ImportRowError(field="first_name", message="Obligatorio"))
            else:
                data["first_name"] = first_name[:100]

            # subscriber_type
            stype = (_clean(raw_row.get("subscriber_type")) or "residential").lower()
            if stype not in SUBSCRIBER_TYPES:
                errors.append(ImportRowError(
                    field="subscriber_type",
                    message=f"Debe ser uno de: {', '.join(sorted(SUBSCRIBER_TYPES))}",
                ))
            else:
                data["subscriber_type"] = stype

            # status
            status = (_clean(raw_row.get("status")) or "active").lower()
            if status not in SUBSCRIBER_STATUSES:
                errors.append(ImportRowError(
                    field="status",
                    message=f"Debe ser uno de: {', '.join(sorted(SUBSCRIBER_STATUSES))}",
                ))
            else:
                data["status"] = status

            # optional text fields
            data["last_name"] = _clean(raw_row.get("last_name"))
            data["business_name"] = _clean(raw_row.get("business_name"))
            data["phone"] = _clean(raw_row.get("phone"))
            data["mobile"] = _clean(raw_row.get("mobile"))
            data["address"] = _clean(raw_row.get("address"))
            data["neighborhood"] = _clean(raw_row.get("neighborhood"))
            data["document_number"] = _clean(raw_row.get("document_number"))
            data["notes"] = _clean(raw_row.get("notes"))

            # document_type
            dt = _clean(raw_row.get("document_type"))
            if dt is not None:
                if dt.upper() not in DOCUMENT_TYPES:
                    errors.append(ImportRowError(
                        field="document_type",
                        message=f"Debe ser uno de: {', '.join(sorted(DOCUMENT_TYPES))}",
                    ))
                else:
                    data["document_type"] = dt.upper()

            # email
            email = _clean(raw_row.get("email"))
            if email is not None:
                if not EMAIL_RE.match(email):
                    errors.append(ImportRowError(field="email", message="Formato inválido"))
                else:
                    data["email"] = email.lower()

            # stratum
            try:
                stratum = _parse_int(raw_row.get("stratum"))
                if stratum is not None:
                    if stratum < 1 or stratum > 6:
                        errors.append(ImportRowError(
                            field="stratum", message="Debe estar entre 1 y 6",
                        ))
                    else:
                        data["stratum"] = stratum
            except ValueError as e:
                errors.append(ImportRowError(field="stratum", message=str(e)))

            # latitude / longitude
            for field in ("latitude", "longitude"):
                try:
                    val = _parse_decimal(raw_row.get(field))
                    if val is not None:
                        data[field] = str(val)
                except ValueError as e:
                    errors.append(ImportRowError(field=field, message=str(e)))

            # registered_at
            try:
                rd = _parse_date(raw_row.get("registered_at"))
                if rd is not None:
                    data["registered_at"] = rd.isoformat()
            except ValueError as e:
                errors.append(ImportRowError(field="registered_at", message=str(e)))

            # Drop None values from data — we only send populated fields to commit
            data = {k: v for k, v in data.items() if v is not None}

            existing_id = by_code.get(code) if code else None
            if errors:
                action = "error"
            elif existing_id is not None:
                action = "update"
            else:
                action = "create"

            previews.append(ImportRowPreview(
                row_number=idx, action=action, data=data, errors=errors,
                existing_id=existing_id,
            ))

        return ImportPreviewResponse(
            rows=previews,
            total_rows=len(previews),
            total_valid=sum(1 for r in previews if r.action != "error"),
            total_errors=sum(1 for r in previews if r.action == "error"),
            total_create=sum(1 for r in previews if r.action == "create"),
            total_update=sum(1 for r in previews if r.action == "update"),
        )

    @staticmethod
    async def commit_subscribers(
        db: AsyncSession, org_id: uuid.UUID, rows: list[ImportCommitRow],
    ) -> ImportCommitResponse:
        created = 0
        updated = 0
        failed = 0
        errors: list[ImportRowError] = []

        for row in rows:
            try:
                data = row.data
                # Coerce decimal/date strings back to native types
                if "latitude" in data:
                    data["latitude"] = Decimal(str(data["latitude"]))
                if "longitude" in data:
                    data["longitude"] = Decimal(str(data["longitude"]))
                if "registered_at" in data:
                    data["registered_at"] = date.fromisoformat(str(data["registered_at"]))

                if row.action == "create":
                    sub = WaterSubscriber(organization_id=org_id, **data)
                    db.add(sub)
                    created += 1
                else:  # update
                    if row.existing_id is None:
                        raise ValueError("existing_id requerido para update")
                    sub = await db.scalar(
                        select(WaterSubscriber).where(
                            WaterSubscriber.id == row.existing_id,
                            WaterSubscriber.organization_id == org_id,
                        )
                    )
                    if sub is None:
                        raise ValueError("Suscriptor no encontrado (¿fue eliminado?)")
                    # Don't change the code on update
                    data.pop("code", None)
                    for k, v in data.items():
                        setattr(sub, k, v)
                    updated += 1
            except Exception as e:
                failed += 1
                errors.append(ImportRowError(
                    field=f"row_{row.row_number}",
                    message=str(e),
                ))

        if failed > 0:
            # Rollback the whole batch on any failure to keep state consistent
            await db.rollback()
            return ImportCommitResponse(
                created=0, updated=0, failed=failed, errors=errors,
            )

        await db.flush()
        return ImportCommitResponse(
            created=created, updated=updated, failed=0, errors=[],
        )

    # ------------------------------------------------------------------
    # Meters
    # ------------------------------------------------------------------
    @staticmethod
    async def preview_meters(
        db: AsyncSession, org_id: uuid.UUID, raw: bytes,
    ) -> ImportPreviewResponse:
        rows_raw = _decode_csv(raw)
        if not rows_raw:
            return ImportPreviewResponse(
                rows=[], total_rows=0, total_valid=0, total_errors=0,
                total_create=0, total_update=0,
            )

        # Index subscribers by code (to resolve subscriber_code → subscriber_id)
        sub_rows = await db.execute(
            select(WaterSubscriber.id, WaterSubscriber.code)
            .where(WaterSubscriber.organization_id == org_id)
        )
        sub_by_code: dict[str, uuid.UUID] = {r[1]: r[0] for r in sub_rows.all()}

        # Index existing meters by serial for upsert
        meter_rows = await db.execute(
            select(WaterMeter.id, WaterMeter.serial_number)
            .where(WaterMeter.organization_id == org_id)
        )
        meter_by_serial: dict[str, uuid.UUID] = {r[1]: r[0] for r in meter_rows.all()}

        previews: list[ImportRowPreview] = []
        seen_serials: dict[str, int] = {}

        for idx, raw_row in enumerate(rows_raw, start=2):
            errors: list[ImportRowError] = []
            data: dict[str, Any] = {}

            # serial_number
            serial = _clean(raw_row.get("serial_number"))
            if not serial:
                errors.append(ImportRowError(field="serial_number", message="Obligatorio"))
            elif len(serial) > 60:
                errors.append(ImportRowError(field="serial_number", message="Máx 60 caracteres"))
            else:
                if serial in seen_serials:
                    errors.append(ImportRowError(
                        field="serial_number",
                        message=f"Duplicado en el CSV (también está en la fila {seen_serials[serial]})",
                    ))
                else:
                    seen_serials[serial] = idx
                data["serial_number"] = serial

            # subscriber_code → subscriber_id
            sub_code = _clean(raw_row.get("subscriber_code"))
            if not sub_code:
                errors.append(ImportRowError(
                    field="subscriber_code", message="Obligatorio",
                ))
            else:
                sub_id = sub_by_code.get(sub_code)
                if sub_id is None:
                    errors.append(ImportRowError(
                        field="subscriber_code",
                        message=f"No existe suscriptor con código '{sub_code}'. Importa primero los suscriptores.",
                    ))
                else:
                    data["subscriber_id"] = str(sub_id)

            # status
            status = (_clean(raw_row.get("status")) or "active").lower()
            if status not in METER_STATUSES:
                errors.append(ImportRowError(
                    field="status",
                    message=f"Debe ser uno de: {', '.join(sorted(METER_STATUSES))}",
                ))
            else:
                data["status"] = status

            # optional text
            data["brand"] = _clean(raw_row.get("brand"))
            data["model"] = _clean(raw_row.get("model"))
            data["diameter"] = _clean(raw_row.get("diameter"))
            data["location_notes"] = _clean(raw_row.get("location_notes"))

            # install_date
            try:
                d = _parse_date(raw_row.get("install_date"))
                if d is not None:
                    data["install_date"] = d.isoformat()
            except ValueError as e:
                errors.append(ImportRowError(field="install_date", message=str(e)))

            # initial_reading / last_reading
            for field in ("initial_reading", "last_reading"):
                try:
                    val = _parse_decimal(raw_row.get(field))
                    if val is not None:
                        if val < 0:
                            errors.append(ImportRowError(
                                field=field, message="No puede ser negativo",
                            ))
                        else:
                            data[field] = str(val)
                except ValueError as e:
                    errors.append(ImportRowError(field=field, message=str(e)))

            data = {k: v for k, v in data.items() if v is not None}

            existing_id = meter_by_serial.get(serial) if serial else None
            if errors:
                action = "error"
            elif existing_id is not None:
                action = "update"
            else:
                action = "create"

            previews.append(ImportRowPreview(
                row_number=idx, action=action, data=data, errors=errors,
                existing_id=existing_id,
            ))

        return ImportPreviewResponse(
            rows=previews,
            total_rows=len(previews),
            total_valid=sum(1 for r in previews if r.action != "error"),
            total_errors=sum(1 for r in previews if r.action == "error"),
            total_create=sum(1 for r in previews if r.action == "create"),
            total_update=sum(1 for r in previews if r.action == "update"),
        )

    @staticmethod
    async def commit_meters(
        db: AsyncSession, org_id: uuid.UUID, rows: list[ImportCommitRow],
    ) -> ImportCommitResponse:
        created = 0
        updated = 0
        failed = 0
        errors: list[ImportRowError] = []

        for row in rows:
            try:
                data = dict(row.data)
                if "subscriber_id" in data:
                    data["subscriber_id"] = uuid.UUID(str(data["subscriber_id"]))
                if "install_date" in data:
                    data["install_date"] = date.fromisoformat(str(data["install_date"]))
                if "initial_reading" in data:
                    data["initial_reading"] = Decimal(str(data["initial_reading"]))
                if "last_reading" in data:
                    data["last_reading"] = Decimal(str(data["last_reading"]))

                if row.action == "create":
                    meter = WaterMeter(organization_id=org_id, **data)
                    db.add(meter)
                    created += 1
                else:
                    if row.existing_id is None:
                        raise ValueError("existing_id requerido para update")
                    meter = await db.scalar(
                        select(WaterMeter).where(
                            WaterMeter.id == row.existing_id,
                            WaterMeter.organization_id == org_id,
                        )
                    )
                    if meter is None:
                        raise ValueError("Medidor no encontrado (¿fue eliminado?)")
                    data.pop("serial_number", None)
                    for k, v in data.items():
                        setattr(meter, k, v)
                    updated += 1
            except Exception as e:
                failed += 1
                errors.append(ImportRowError(
                    field=f"row_{row.row_number}",
                    message=str(e),
                ))

        if failed > 0:
            await db.rollback()
            return ImportCommitResponse(
                created=0, updated=0, failed=failed, errors=errors,
            )

        await db.flush()
        return ImportCommitResponse(
            created=created, updated=updated, failed=0, errors=[],
        )

    # ------------------------------------------------------------------
    # Templates
    # ------------------------------------------------------------------
    @staticmethod
    def subscribers_template() -> str:
        return ",".join(SUBSCRIBER_COLUMNS) + "\n"

    @staticmethod
    def meters_template() -> str:
        return ",".join(METER_COLUMNS) + "\n"
