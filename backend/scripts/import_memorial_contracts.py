"""Importa contratos exequiales físicos (transcritos a JSON) a SavvyMemorial.

Pensado para migrar las libretas de contratos en papel de una funeraria:
cada hoja se transcribe a un objeto JSON y este script la registra con su
número físico como consecutivo (contrato 0084 -> EXQ-0084), de modo que los
contratos nuevos creados en la app continúan la numeración de la libreta.

Por defecto es un DRY-RUN: valida y muestra lo que haría. Con --commit escribe.
Idempotente: si el número de contrato ya existe en la org, se omite.

Uso:
    cd backend
    .venv/Scripts/python.exe scripts/import_memorial_contracts.py contratos.json \
        --org-email cliente@correo.com [--activate-app] [--commit]

Formato del JSON
----------------
{
  "plan": {                              # se crea si no existe (por code)
    "code": "PLAN-FAMILIAR", "name": "Plan Exequial Familiar",
    "monthly_fee": 14000, "max_beneficiaries": 15,
    "coverage_items": ["Cofre tipo plan", "..."]
  },
  "contracts": [
    {
      "numero": 84,                       # número impreso en la hoja
      "fecha_elaboracion": "2026-04-26",
      "mensualidad": 14000,
      "dia_cobro": 25,                    # null si no se lee
      "servicio_cobrador": true,          # true / false / null
      "observaciones": "texto libre de la hoja",
      "titular": {
        "nombres": "Benito Antonio", "apellidos": "López Conde",
        "documento": "78078800", "fecha_nacimiento": "1982-04-03",
        "direccion": "La Palma", "municipio": "La Palma",
        "telefonos": ["3008989582", "3205765620"]
      },
      "beneficiarios": [
        {"nombres": "José", "apellidos": "Padilla Conde", "documento": "11037587",
         "fecha_nacimiento": "1976-06-08",   # completa (AAAA-MM-DD), o
         "dia_mes": "08/06",                 # parcial: año se deriva de la edad
         "edad": 50, "parentesco": "Hermano"}
      ],
      "dudas": ["CC del titular poco legible"]   # quedan en las notas del contrato
    }
  ]
}

Reglas:
- Fecha completa + edad: se valida que la edad cuadre a la fecha del contrato.
- Solo dia_mes + edad: el año se deriva de la edad a la fecha del contrato.
- Solo edad: sin fecha de nacimiento; la edad queda en las notas.
- El titular se registra también como beneficiario (is_titular) para que
  aparezca en la búsqueda de cobertura por documento.
- Próximo cobro: la siguiente fecha con `dia_cobro` desde hoy (sin historial
  de pagos no se genera mora ficticia). Sin `dia_cobro` se usa el día de la firma.
- Todo lo dudoso (dudas + edades que no cuadran) queda en las notas como [Revisar].
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

from sqlalchemy import func, select  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from src.apps.memorial.models import (  # noqa: E402
    MemorialExequialBeneficiary,
    MemorialExequialContract,
    MemorialExequialPlan,
)
from src.core.database import async_session_factory, engine  # noqa: E402
from src.modules.apps.models import AppRegistry, OrganizationApp  # noqa: E402
from src.modules.auth.models import User  # noqa: E402
from src.modules.organization.models import Membership  # noqa: E402


# ---------------------------------------------------------------- Parsing


def _age_at(birth: date, ref: date) -> int:
    return ref.year - birth.year - ((ref.month, ref.day) < (birth.month, birth.day))


def _derive_birth(day_month: str, age: int, ref: date) -> date:
    """Año de nacimiento tal que la persona tenga `age` años en `ref`."""
    d, m = (int(x) for x in day_month.split("/"))
    year = ref.year - age - (1 if (m, d) > (ref.month, ref.day) else 0)
    return date(year, m, d)


def _next_collection(day: int | None, today: date) -> date | None:
    if not day:
        return None
    day = min(day, 28)
    candidate = today.replace(day=day)
    if candidate < today:
        y, m = (today.year + 1, 1) if today.month == 12 else (today.year, today.month + 1)
        candidate = date(y, m, day)
    return candidate


def _full_name(p: dict) -> str:
    return f"{p.get('nombres', '')} {p.get('apellidos') or ''}".strip()


def build_contract(raw: dict, today: date) -> tuple[dict, list[dict], list[str]]:
    """Normaliza una hoja. Devuelve (contrato, beneficiarios, advertencias)."""
    warnings: list[str] = []
    start = date.fromisoformat(raw["fecha_elaboracion"])
    tit = raw["titular"]
    phones = [p for p in tit.get("telefonos", []) if p]

    notes: list[str] = []
    if raw.get("observaciones"):
        notes.append(f"Observaciones: {raw['observaciones']}")
    if tit.get("municipio"):
        notes.append(f"Municipio: {tit['municipio']}")
    if raw.get("dia_cobro"):
        notes.append(f"Día de cobro: {raw['dia_cobro']} de cada mes")
    if raw.get("servicio_cobrador") is not None:
        notes.append(f"Servicio de cobrador: {'Sí' if raw['servicio_cobrador'] else 'No'}")

    beneficiaries: list[dict] = []
    tit_birth = date.fromisoformat(tit["fecha_nacimiento"]) if tit.get("fecha_nacimiento") else None
    beneficiaries.append({
        "first_name": tit["nombres"], "last_name": tit.get("apellidos"),
        "document_type": "CC" if tit.get("documento") else None,
        "document_number": tit.get("documento"),
        "birth_date": tit_birth, "relationship": "Titular", "is_titular": True,
    })

    age_only: list[str] = []
    for b in raw.get("beneficiarios", []):
        name = _full_name(b)
        age = b.get("edad")
        birth: date | None = None
        if b.get("fecha_nacimiento"):
            birth = date.fromisoformat(b["fecha_nacimiento"])
            if age is not None and _age_at(birth, start) != age:
                warnings.append(
                    f"{name}: nació {birth:%d/%m/%Y} → {_age_at(birth, start)} años a la fecha "
                    f"del contrato, pero la hoja dice {age}.",
                )
        elif b.get("dia_mes") and age is not None:
            birth = _derive_birth(b["dia_mes"], age, start)
            notes.append(f"{name}: año de nacimiento derivado de la edad ({age}).")
        elif age is not None:
            age_only.append(f"{name} ({age} años)")
        beneficiaries.append({
            "first_name": b["nombres"], "last_name": b.get("apellidos"),
            "document_type": "CC" if b.get("documento") else None,
            "document_number": b.get("documento"),
            "birth_date": birth, "relationship": b.get("parentesco"), "is_titular": False,
        })
    if age_only:
        notes.append(f"Edad a la firma sin fecha de nacimiento: {', '.join(age_only)}.")
    for w in warnings:
        notes.append(f"[Revisar] {w}")
    for d in raw.get("dudas", []):
        notes.append(f"[Revisar] {d}")
    collection_day = raw.get("dia_cobro")
    if not collection_day:
        collection_day = start.day
        notes.append(f"Día de cobro no indicado: se usa el día de la firma ({start.day}).")

    address = ", ".join(x for x in (tit.get("direccion"), tit.get("municipio")) if x) or None
    contract = {
        "consecutive": int(raw["numero"]),
        "code": f"EXQ-{int(raw['numero']):04d}",
        "affiliate_type": "familiar",
        "titular_first_name": tit["nombres"],
        "titular_last_name": tit.get("apellidos"),
        "titular_document_type": "CC" if tit.get("documento") else None,
        "titular_document_number": tit.get("documento"),
        "titular_mobile": phones[0] if phones else None,
        "titular_phone": phones[1] if len(phones) > 1 else None,
        "titular_address": address,
        "payment_frequency": "monthly",
        "fee_amount": Decimal(str(raw["mensualidad"])),
        "start_date": start,
        "next_payment_date": _next_collection(collection_day, today),
        "notes": "\n".join(notes) or None,
    }
    return contract, beneficiaries, warnings


# ---------------------------------------------------------------- DB steps


async def _resolve_org(db: AsyncSession, email: str) -> tuple[uuid.UUID, uuid.UUID]:
    row = (await db.execute(
        select(Membership.organization_id, User.id)
        .join(User, User.id == Membership.user_id)
        .where(func.lower(User.email) == email.lower(), Membership.role == "owner")
    )).first()
    if row is None:
        raise SystemExit(f"No hay organización cuyo owner sea {email}.")
    return row[0], row[1]


async def _activate_app(db: AsyncSession, org_id: uuid.UUID) -> str:
    app = await db.scalar(select(AppRegistry).where(AppRegistry.code == "memorial"))
    org_app = await db.scalar(select(OrganizationApp).where(
        OrganizationApp.organization_id == org_id, OrganizationApp.app_id == app.id,
    ))
    if org_app is None:
        db.add(OrganizationApp(
            organization_id=org_id, app_id=app.id, status="active",
            activated_at=datetime.now(UTC),
        ))
        return "memorial: activada (nueva)"
    if org_app.status == "active":
        return "memorial: ya estaba activa"
    prev = org_app.status
    org_app.status = "active"
    org_app.activated_at = datetime.now(UTC)
    org_app.trial_ends_at = None
    org_app.expires_at = None
    return f"memorial: {prev} → active"


async def _ensure_plan(
    db: AsyncSession, org_id: uuid.UUID, spec: dict, valid_from: date,
) -> tuple[MemorialExequialPlan, bool]:
    plan = await db.scalar(select(MemorialExequialPlan).where(
        MemorialExequialPlan.organization_id == org_id,
        MemorialExequialPlan.code == spec["code"],
    ))
    if plan is not None:
        return plan, False
    plan = MemorialExequialPlan(
        organization_id=org_id,
        code=spec["code"],
        name=spec["name"],
        description=spec.get("description"),
        plan_type="familiar",
        max_beneficiaries=spec.get("max_beneficiaries"),
        waiting_period_days=spec.get("waiting_period_days", 0),
        monthly_fee=Decimal(str(spec["monthly_fee"])),
        coverage_items=spec.get("coverage_items", []),
        is_active=True,
        valid_from=valid_from,
    )
    db.add(plan)
    await db.flush()
    return plan, True


async def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("json_file")
    ap.add_argument("--org-email", required=True, help="email del owner de la organización")
    ap.add_argument("--activate-app", action="store_true", help="deja la app memorial en estado active")
    ap.add_argument("--commit", action="store_true", help="escribe en la BD (sin esto es dry-run)")
    args = ap.parse_args()

    data = json.loads(Path(args.json_file).read_text(encoding="utf-8"))
    today = date.today()
    parsed = [(raw, *build_contract(raw, today)) for raw in data["contracts"]]

    async with async_session_factory() as db:
        org_id, owner_id = await _resolve_org(db, args.org_email)
        print(f"Org {org_id} (owner {args.org_email})")
        if args.activate_app:
            print(await _activate_app(db, org_id))

        valid_from = min(c["start_date"] for _, c, _, _ in parsed)
        plan, created = await _ensure_plan(db, org_id, data["plan"], valid_from)
        print(f"Plan {plan.code}: {'creado' if created else 'existente'}")

        existing = set((await db.scalars(select(MemorialExequialContract.consecutive).where(
            MemorialExequialContract.organization_id == org_id,
        ))).all())

        n_new = n_ben = 0
        for raw, c, bens, warns in parsed:
            label = f"{c['code']}  {c['titular_first_name']} {c['titular_last_name'] or ''}".strip()
            if c["consecutive"] in existing:
                print(f"  = {label}: ya existe, se omite")
                continue
            contract = MemorialExequialContract(
                organization_id=org_id, plan_id=plan.id, status="active",
                created_by=owner_id, **c,
            )
            db.add(contract)
            await db.flush()
            for b in bens:
                ben = MemorialExequialBeneficiary(
                    organization_id=org_id, contract_id=contract.id,
                    joined_at=c["start_date"],
                    **{k: v for k, v in b.items() if k != "relationship"},
                )
                ben.relationship_ = b["relationship"]
                db.add(ben)
            n_new += 1
            n_ben += len(bens)
            print(f"  + {label}: {len(bens)} personas (incl. titular), "
                  f"${c['fee_amount']:,.0f}/mes, desde {c['start_date']:%d/%m/%Y}, "
                  f"próximo cobro {c['next_payment_date'] or '—'}")
            for w in warns:
                print(f"      ! {w}")

        print(f"\n{n_new} contratos, {n_ben} personas.")
        if args.commit:
            await db.commit()
            print("OK — commit aplicado.")
        else:
            await db.rollback()
            print("DRY-RUN — nada escrito. Repite con --commit para guardar.")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
