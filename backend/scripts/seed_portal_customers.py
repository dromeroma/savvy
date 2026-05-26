"""Seed portal customer users on top of the existing demo (run after
`seed_water_demo.py`).

Picks 5 representative subscribers from the demo org and turns each into
a portal user (Savvy User + Membership(customer) + AppUserRole(customer)
+ links WaterSubscriber.user_id). Idempotent — re-running just resets
the password without duplicating rows.

Usage:
    cd backend
    .venv/Scripts/python.exe scripts/seed_portal_customers.py
"""

from __future__ import annotations

import asyncio
import logging
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

from sqlalchemy import select  # noqa: E402

from src.apps.water.models import WaterSubscriber  # noqa: E402
from src.core.database import async_session_factory, engine  # noqa: E402
from src.core.security import hash_password  # noqa: E402
from src.main import app  # noqa: E402, F401
from src.modules.apps.models import AppRegistry, AppUserRole  # noqa: E402
from src.modules.auth.models import User  # noqa: E402
from src.modules.organization.models import Membership, Organization  # noqa: E402


DEMO_ORG_SLUG = "acueducto-demo"
DEMO_PASSWORD = "Demo1234!"

# 5 subscriber codes covering the 4 subscriber types. The seed script
# is deterministic (random.seed(42)), so these codes always exist and
# have 3 months of invoices + payments.
CUSTOMERS = [
    {
        "code": "SUB-0001",
        "email": "juan.demo@acueducto.com",
        "name": "Cliente Demo Juan",
        "label": "Residencial estrato 3",
    },
    {
        "code": "SUB-0050",
        "email": "maria.demo@acueducto.com",
        "name": "Cliente Demo María",
        "label": "Residencial (mezcla de estratos)",
    },
    {
        "code": "SUB-0080",
        "email": "panaderia.demo@acueducto.com",
        "name": "Cliente Demo Panadería",
        "label": "Comercial",
    },
    {
        "code": "SUB-0091",
        "email": "escuela.demo@acueducto.com",
        "name": "Cliente Demo Escuela",
        "label": "Oficial",
    },
    {
        "code": "SUB-0098",
        "email": "lacteos.demo@acueducto.com",
        "name": "Cliente Demo Lácteos",
        "label": "Industrial",
    },
]


async def main() -> None:
    print("=" * 70)
    print("SavvyWater · Seed Portal Customers")
    print("=" * 70)

    async with async_session_factory() as session:
        try:
            # Locate the demo org
            org = await session.scalar(
                select(Organization).where(Organization.slug == DEMO_ORG_SLUG)
            )
            if org is None:
                raise SystemExit(
                    f"Demo org '{DEMO_ORG_SLUG}' no encontrada. "
                    f"Corre primero `python scripts/seed_water_demo.py`."
                )

            # Locate water app
            water_app = await session.scalar(
                select(AppRegistry).where(AppRegistry.code == "water")
            )
            if water_app is None:
                raise SystemExit("App 'water' no registrada en app_registry.")

            results: list[tuple[dict, str]] = []  # (customer cfg, action)

            for cfg in CUSTOMERS:
                # Locate subscriber
                sub = await session.scalar(
                    select(WaterSubscriber).where(
                        WaterSubscriber.organization_id == org.id,
                        WaterSubscriber.code == cfg["code"],
                    )
                )
                if sub is None:
                    print(f"  ! WARN: subscriber {cfg['code']} no existe — saltando")
                    continue

                # Create or reuse user
                user = await session.scalar(
                    select(User).where(User.email == cfg["email"])
                )
                action = ""
                if user is None:
                    user = User(
                        id=uuid.uuid4(),
                        name=cfg["name"],
                        email=cfg["email"],
                        password_hash=hash_password(DEMO_PASSWORD),
                    )
                    session.add(user)
                    await session.flush()
                    action = "creado"
                else:
                    user.password_hash = hash_password(DEMO_PASSWORD)
                    user.name = cfg["name"]
                    action = "reseteado"

                # Membership (role=customer drives portal redirect after login)
                membership = await session.scalar(
                    select(Membership).where(
                        Membership.organization_id == org.id,
                        Membership.user_id == user.id,
                    )
                )
                if membership is None:
                    session.add(Membership(
                        id=uuid.uuid4(),
                        organization_id=org.id,
                        user_id=user.id,
                        role="customer",
                    ))
                elif membership.role != "customer":
                    membership.role = "customer"

                # App role on water (defensive — the bypass for owners
                # doesn't help here since role=customer is not owner)
                app_role = await session.scalar(
                    select(AppUserRole).where(
                        AppUserRole.organization_id == org.id,
                        AppUserRole.user_id == user.id,
                        AppUserRole.app_id == water_app.id,
                    )
                )
                if app_role is None:
                    session.add(AppUserRole(
                        id=uuid.uuid4(),
                        organization_id=org.id,
                        user_id=user.id,
                        app_id=water_app.id,
                        role="customer",
                    ))
                elif app_role.role != "customer":
                    app_role.role = "customer"

                # Link subscriber → user (one direction only — multiple subs
                # could not be linked to the same user, but it's fine here)
                sub.user_id = user.id
                if not sub.email:
                    sub.email = cfg["email"]
                await session.flush()
                results.append((cfg, action))

            await session.commit()

            print("\n" + "=" * 70)
            print("USUARIOS DEL PORTAL LISTOS")
            print("=" * 70)
            print(f"  URL portal:  /portal/water/dashboard")
            print(f"  (redirige automáticamente desde /auth/login)")
            print()
            print(f"  Contraseña común:  {DEMO_PASSWORD}")
            print()
            print(f"  {'Email':<35}  {'Suscriptor':<12}  Tipo")
            print(f"  {'-' * 35}  {'-' * 12}  {'-' * 30}")
            for cfg, action in results:
                print(f"  {cfg['email']:<35}  {cfg['code']:<12}  {cfg['label']} [{action}]")
            print("=" * 70)
        except Exception:
            await session.rollback()
            raise
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
