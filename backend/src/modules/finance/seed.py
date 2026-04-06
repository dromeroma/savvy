"""Default seed data for the SavvyFinance module."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.accounting.models import ChartOfAccounts
from src.modules.finance.models import FinanceCategory, FinancePaymentAccount

# ---------------------------------------------------------------------------
# Church categories
# ---------------------------------------------------------------------------

CHURCH_INCOME_CATEGORIES = [
    {"code": "TITHE", "name": "Diezmo", "type": "income", "app_code": "church", "is_system": True},
    {"code": "OFFERING", "name": "Ofrenda", "type": "income", "app_code": "church", "is_system": True},
    {"code": "DONATION", "name": "Donación", "type": "income", "app_code": "church", "is_system": True},
    {"code": "COVENANT", "name": "Pacto", "type": "income", "app_code": "church", "is_system": True},
    {"code": "FIRSTFRUITS", "name": "Primicias", "type": "income", "app_code": "church", "is_system": True},
    {"code": "OTHER_INCOME", "name": "Otros Ingresos", "type": "income", "app_code": "church", "is_system": True},
]

CHURCH_EXPENSE_CATEGORIES = [
    {"code": "RENT", "name": "Arriendo", "type": "expense", "app_code": "church", "is_system": True},
    {"code": "UTILITIES", "name": "Servicios Públicos", "type": "expense", "app_code": "church", "is_system": True},
    {"code": "SALARIES", "name": "Salarios y Honorarios", "type": "expense", "app_code": "church", "is_system": True},
    {"code": "TITHE_OF_TITHE", "name": "Diezmo del Diezmo", "type": "expense", "app_code": "church", "is_system": True},
    {"code": "AID", "name": "Ayudas y Benevolencia", "type": "expense", "app_code": "church", "is_system": True},
    {"code": "TRANSPORT", "name": "Pasajes y Transporte", "type": "expense", "app_code": "church", "is_system": True},
    {"code": "MAINTENANCE", "name": "Mantenimiento", "type": "expense", "app_code": "church", "is_system": True},
    {"code": "SUPPLIES", "name": "Insumos y Materiales", "type": "expense", "app_code": "church", "is_system": True},
    {"code": "MINISTRY", "name": "Gastos Ministeriales", "type": "expense", "app_code": "church", "is_system": True},
    {"code": "INSURANCE", "name": "Seguros", "type": "expense", "app_code": "church", "is_system": True},
    {"code": "EQUIPMENT", "name": "Equipos y Tecnología", "type": "expense", "app_code": "church", "is_system": True},
    {"code": "FOOD", "name": "Alimentación", "type": "expense", "app_code": "church", "is_system": True},
    {"code": "EVENTS", "name": "Eventos y Actividades", "type": "expense", "app_code": "church", "is_system": True},
    {"code": "OTHER_EXPENSE", "name": "Otros Gastos", "type": "expense", "app_code": "church", "is_system": True},
]

DEFAULT_PAYMENT_ACCOUNTS = [
    {"payment_method": "cash", "account_code": "1.1.01"},
    {"payment_method": "transfer", "account_code": "1.1.02"},
    {"payment_method": "card", "account_code": "1.1.02"},
    {"payment_method": "check", "account_code": "1.1.02"},
]


async def seed_finance_categories(
    db: AsyncSession,
    org_id: uuid.UUID,
) -> list[FinanceCategory]:
    """Seed default church finance categories for an organization.

    Skips categories that already exist (idempotent).
    """
    all_categories = CHURCH_INCOME_CATEGORIES + CHURCH_EXPENSE_CATEGORIES
    created: list[FinanceCategory] = []

    for cat_data in all_categories:
        # Check if already exists
        result = await db.execute(
            select(FinanceCategory).where(
                FinanceCategory.organization_id == org_id,
                FinanceCategory.app_code == cat_data["app_code"],
                FinanceCategory.code == cat_data["code"],
            )
        )
        if result.scalar_one_or_none() is not None:
            continue

        category = FinanceCategory(
            organization_id=org_id,
            app_code=cat_data["app_code"],
            type=cat_data["type"],
            name=cat_data["name"],
            code=cat_data["code"],
            is_system=cat_data["is_system"],
        )
        db.add(category)
        created.append(category)

    if created:
        await db.flush()

    return created


async def seed_payment_accounts(
    db: AsyncSession,
    org_id: uuid.UUID,
) -> list[FinancePaymentAccount]:
    """Seed default payment-method-to-account mappings.

    Resolves account codes from the chart of accounts. Skips if already set.
    """
    created: list[FinancePaymentAccount] = []

    for pa_data in DEFAULT_PAYMENT_ACCOUNTS:
        # Check if already exists
        result = await db.execute(
            select(FinancePaymentAccount).where(
                FinancePaymentAccount.organization_id == org_id,
                FinancePaymentAccount.payment_method == pa_data["payment_method"],
            )
        )
        if result.scalar_one_or_none() is not None:
            continue

        # Resolve account code to ID
        acct_result = await db.execute(
            select(ChartOfAccounts).where(
                ChartOfAccounts.organization_id == org_id,
                ChartOfAccounts.code == pa_data["account_code"],
                ChartOfAccounts.is_active == True,  # noqa: E712
            )
        )
        account = acct_result.scalar_one_or_none()
        if account is None:
            # Skip if the chart of accounts hasn't been seeded yet
            continue

        mapping = FinancePaymentAccount(
            organization_id=org_id,
            payment_method=pa_data["payment_method"],
            account_id=account.id,
        )
        db.add(mapping)
        created.append(mapping)

    if created:
        await db.flush()

    return created
